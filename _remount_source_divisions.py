#!/usr/bin/env python3
"""Remount placements whose division/class disagrees with the trial source.

Fixes hurdles/steeplechase parked in conformation or flats, leftover
Nose Work/Agility/UNKNOWN generic classes, and age/height class drift.
"""
from __future__ import annotations

import argparse
import contextlib
import io
import os
import re
import sys
from concurrent.futures import ThreadPoolExecutor, TimeoutError as FuturesTimeout

import pyodbc
from parse_catalog import distinct_registered_names, names_are_similar
from fix_racing_steeplechase_class_collapse import parse_all_slots
from populate_trialresults_fixed import (
    get_or_create_class,
    get_or_create_division,
)

CONN = (
    r"DRIVER={SQL Server};SERVER=Ldahsar\SQLEXPRESS;"
    r"DATABASE=TrialResults;Trusted_Connection=yes"
)

RACING = {"RACING", "FLAT", "HURDLE", "STEEPLE", "STEEPLECHASE"}
LEFTOVER = {"NOSE WORK", "AGILITY", "UNKNOWN"}


def fam(div: str) -> str:
    u = re.sub(r"[^A-Z]", "", (div or "").upper())
    if any(x in u for x in ("HURDLE", "STEEPLE")):
        return "HURDLES"
    if (
        "FLAT" in u
        or u.startswith("RACING")
        or u == "RACING"
        or "FRIDAYNIGHTRACING" in u
    ):
        return "RACING"
    if "CONFORMATION" in u:
        return "CONFORMATION"
    if "NOSE" in u:
        return "NOSE"
    if "AGILITY" in u:
        return "AGILITY"
    if "UNKNOWN" in u:
        return "UNKNOWN"
    if "BRUSH" in u:
        return "BRUSH"
    if "BARN" in u:
        return "BARN"
    if "LURE" in u:
        return "LURE"
    if "THUNDER" in u or "SEEJACK" in u:
        return "TUNNEL"
    if "GOTOGROUND" in u or u.endswith("GTG"):
        return "GTG"
    if "SUPEREARTH" in u or "MASTERSDEN" in u:
        return "SE"
    return u[:20] or "OTHER"


def class_key(name: str) -> str:
    n = (name or "").upper()
    n = n.replace("½", "1/2")
    n = re.sub(r"\bYEARS?\b", "YR", n)
    n = re.sub(r"\bAND\b", " ", n)
    n = re.sub(r"^(FLAT|HURDLES?|STEEPLECHASE)\s+RACING\s*-?\s*", "", n)
    n = re.sub(r"\b(?:JRT|TALL|JACK\s+RUSSELL(?:\s+TERRIERS?)?)\b", " ", n)
    n = re.sub(r"12\s*1/2|12\s*½|12\.5", "12", n)
    n = re.sub(r"[^A-Z0-9]+", "", n)
    n = re.sub(r"OVER12\d*UPTO15|OVER12\d*15|OVER12TO15", "OVER12TO15", n)
    n = re.sub(r"10\d*UPTO12|10UPTO12|10TO12", "10TO12", n)
    return n


def res_key(r: str) -> str:
    r = (r or "").strip().lower()
    r = r.replace("–", "-").replace("—", "-")
    return r


def dog_key(n: str) -> str:
    return re.sub(r"[^a-z0-9]", "", (n or "").lower())


def dogs_ok(a: str, b: str) -> bool:
    if not a or not b:
        return False
    if distinct_registered_names(a, b):
        return False
    ta, tb = dog_key(a), dog_key(b)
    if ta == tb:
        return True
    if min(len(ta), len(tb)) < 10:
        return False
    return ta in tb or tb in ta


def classes_ok(a: str, b: str) -> bool:
    ka, kb = class_key(a), class_key(b)
    if not ka or not kb or min(len(ka), len(kb)) < 8:
        return ka == kb and len(ka) >= 8
    return ka == kb or ka in kb or kb in ka


def is_generic_leftover_class(cls: str) -> bool:
    u = (cls or "").upper()
    if re.search(r"\b(?:AGILITY|JUMPERS?|NOSE)\b", u):
        return False
    return bool(
        re.search(
            r"VETERANS?.{0,20}SIX|ADULTS?.{0,20}ONE YEAR|JRT VETERANS|JRT ADULTS|THUNDER TUNNEL",
            u,
        )
    )


_NON_RACING_CLASS = re.compile(
    r"AGILITY|JUMPER|GO[\s\-]?TO[\s\-]?GROUND|OBEDIENCE|TRAILING|"
    r"SUPER\s*EARTH|BARN\s*HUNT|LURE|NOSE|CONFORMATION|THUNDER\s*TUNNEL",
    re.I,
)
_RACING_CLASS = re.compile(
    r"\b(?:DOGS?|BITCHES|VETERAN|PUPP(?:Y|IES)|ADULT|SENIOR|GRAND\s+PRIX|"
    r"CHALLENGE|FLAT|HURDLE|STEEPLE)",
    re.I,
)


def slot_usable(div: str, cls: str) -> bool:
    sf = fam(div)
    if _NON_RACING_CLASS.search(cls or "") and sf in ("RACING", "HURDLES"):
        return False
    if sf in ("RACING", "HURDLES"):
        return bool(_RACING_CLASS.search(cls or ""))
    if sf in ("BRUSH", "BARN", "LURE", "TUNNEL"):
        return True
    return False


def should_move(src_div: str, src_cls: str, db_div: str, db_cls: str) -> bool:
    if not slot_usable(src_div, src_cls):
        return False
    sf, df = fam(src_div), fam(db_div)
    if sf == df:
        return False
    leftover = df in LEFTOVER or df == "UNKNOWN"
    racing_src = sf in ("RACING", "HURDLES")
    conf_db = df == "CONFORMATION"
    racing_db = df in ("RACING", "HURDLES")
    if leftover and is_generic_leftover_class(db_cls) and sf in ("BRUSH", "BARN", "LURE", "TUNNEL"):
        return True
    if racing_src and conf_db and classes_ok(src_cls, db_cls):
        return True
    if racing_src and racing_db and sf != df and classes_ok(src_cls, db_cls):
        if re.search(r"CHAMPION", (src_cls or "") + (db_cls or ""), re.I):
            return False
        # Already labeled Flat or Hurdles — do not steal one for the other.
        if re.search(r"FLAT|HURDLE|STEEPLE", (db_div or "").upper()):
            return False
        return True
    return False


def ensure_tc(cur, trial_id: int, division: str, class_name: str) -> int:
    last_err = None
    for _ in range(4):
        try:
            div_id = get_or_create_division(cur, division)
            class_id = get_or_create_class(cur, class_name, div_id)
            cur.execute(
                "SELECT TrialClassID FROM sResults.TrialClass WHERE TrialListID=? AND ClassID=?",
                trial_id,
                class_id,
            )
            row = cur.fetchone()
            if row:
                return int(row[0])
            cur.execute("SELECT ISNULL(MAX(TrialClassID),0)+1 FROM sResults.TrialClass")
            tcid = int(cur.fetchone()[0])
            cur.execute(
                """
                INSERT INTO sResults.TrialClass (TrialClassID, TrialListID, ClassID, EntryCount)
                VALUES (?, ?, ?, 0)
                """,
                tcid,
                trial_id,
                class_id,
            )
            return tcid
        except Exception as e:
            last_err = e
            if "40001" not in str(e) and "deadlock" not in str(e).lower():
                raise
            import time

            time.sleep(0.4)
    raise last_err


def connect():
    return pyodbc.connect(CONN, timeout=60)


def fetch_trials(cur, trial_id: int | None):
    extra = "AND l.TrialListID=?" if trial_id else ""
    params = (trial_id,) if trial_id else ()
    cur.execute(
        f"""
        SELECT l.TrialListID, l.Year, l.TrialName, l.TrialResultFilePath
        FROM sResults.TrialList l
        WHERE l.TrialResultFilePath IS NOT NULL AND LTRIM(RTRIM(l.TrialResultFilePath)) <> ''
        {extra}
        ORDER BY l.Year, l.TrialListID
        """,
        params,
    )
    return cur.fetchall()


def fetch_db_rows(cur, trial_id: int):
    cur.execute(
        """
        SELECT p.TrialPlacementsID, dog.DogName, p.Result, div.DivisionName,
               c.ClassName, p.TrialClassID
        FROM sResults.TrialPlacements p
        JOIN sResults.Dog dog ON dog.DogID=p.DogID
        JOIN sResults.TrialClass tc ON tc.TrialClassID=p.TrialClassID
        JOIN sResults.Class c ON c.ClassID=tc.ClassID
        JOIN sResults.Division div ON div.DivisionID=c.DivisionID
        WHERE tc.TrialListID=?
        """,
        trial_id,
    )
    return cur.fetchall()


def resolve_path(path: str) -> str | None:
    if path and os.path.isfile(path):
        return path
    root = r"c:\Users\mw\OneDrive - timberwilde.net\repos\jrtca_results"
    if not path:
        return None
    name = os.path.basename(path.replace("/", os.sep))
    for folder in (root, os.path.join(root, str(os.path.basename(os.path.dirname(path))))):
        cand = os.path.join(folder, name)
        if os.path.isfile(cand):
            return cand
    # year folder
    m = re.search(r"(\d{4})", path)
    if m:
        cand = os.path.join(root, m.group(1), name)
        if os.path.isfile(cand):
            return cand
    return None


def remount_trial(cur, tid, year, tname, placements, db, apply, samples, moved, deleted):
    used_db = set()
    db_idx = []
    dest_keys = set()
    for row in db:
        pid, dname, result, ddiv, dcls, tcid = row
        rk = res_key(result)
        dk = dog_key(dname)
        df = fam(ddiv)
        ck = class_key(dcls)
        db_idx.append((pid, dname, result, ddiv, dcls, tcid, rk, dk, df, ck))
        dest_keys.add((dk, rk, df, ck))
    for src in placements:
        if not slot_usable(src.division or "", src.class_name or ""):
            continue
        sdiv = src.division or ""
        scls = src.class_name or ""
        sres = res_key(src.placement)
        sdk = dog_key(src.dog_name)
        sck = class_key(scls)
        cands = []
        for row in db_idx:
            pid, dname, result, ddiv, dcls, tcid, rk, dk, df, ck = row
            if pid in used_db or rk != sres:
                continue
            if not (sdk == dk or (min(len(sdk), len(dk)) >= 10 and (sdk in dk or dk in sdk))):
                continue
            cands.append(row)
        if not cands:
            continue

        def score(row):
            pid, dname, result, ddiv, dcls, tcid, rk, dk, df, ck = row
            cok = (sck == ck) or (sck and ck and min(len(sck), len(ck)) >= 8 and (sck in ck or ck in sck))
            return (
                2 if cok else 0,
                1 if should_move(sdiv, scls, ddiv, dcls) else 0,
                -abs(len(ck) - len(sck)),
            )

        best = max(cands, key=score)
        pid, dname, result, ddiv, dcls, tcid, rk, dk, df, ck = best
        if not should_move(sdiv, scls, ddiv, dcls):
            continue
        new_div = sdiv
        new_cls = scls
        new_fam = fam(new_div)
        new_ck = class_key(new_cls)
        dest_exists = False
        for opid, oname, ores, odiv, ocls, otc, ork, odk, odf, ock in db_idx:
            if opid == pid or ork != rk or odk != dk or odf != new_fam:
                continue
            if ock == new_ck or (
                new_ck and ock and min(len(new_ck), len(ock)) >= 8
                and (new_ck in ock or ock in new_ck)
            ):
                dest_exists = True
                break
        new_tc = ensure_tc(cur, tid, new_div, new_cls)
        if new_tc == tcid:
            used_db.add(pid)
            continue
        if dest_exists:
            if apply:
                cur.execute(
                    "DELETE FROM sResults.TrialPlacements_Times WHERE TrialPlacementsID=?",
                    pid,
                )
                cur.execute(
                    "DELETE FROM sResults.TrialPlacements WHERE TrialPlacementsID=?",
                    pid,
                )
            deleted += 1
            used_db.add(pid)
            continue
        if apply:
            cur.execute(
                "UPDATE sResults.TrialPlacements SET TrialClassID=? WHERE TrialPlacementsID=?",
                new_tc,
                pid,
            )
        dest_keys.add((dk, rk, new_fam, new_ck))
        moved += 1
        used_db.add(pid)
        if len(samples) < 40:
            samples.append(
                f"{year} {tname[:28]} | {dname[:22]} {result} | {ddiv[:22]}/{dcls[:28]} -> {new_div[:18]}/{new_cls[:28]}"
            )
        for row in db_idx:
            opid, oname, ores, odiv, ocls, otc, ork, odk, odf, ock = row
            if opid == pid or opid in used_db or ork != sres:
                continue
            if not (sdk == odk or (min(len(sdk), len(odk)) >= 10 and (sdk in odk or odk in sdk))):
                continue
            if not (
                (sck == ock or (sck and ock and min(len(sck), len(ock)) >= 8 and (sck in ock or ock in sck)))
                or (ck == ock or (ck and ock and min(len(ck), len(ock)) >= 8 and (ck in ock or ock in ck)))
            ):
                continue
            if odf in ("CONFORMATION", "UNKNOWN") or odf in LEFTOVER:
                if apply:
                    cur.execute(
                        "DELETE FROM sResults.TrialPlacements_Times WHERE TrialPlacementsID=?",
                        opid,
                    )
                    cur.execute(
                        "DELETE FROM sResults.TrialPlacements WHERE TrialPlacementsID=?",
                        opid,
                    )
                deleted += 1
                used_db.add(opid)
    return moved, deleted


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--apply", action="store_true")
    ap.add_argument("--trial-id", type=int)
    ap.add_argument("--limit", type=int, default=0)
    args = ap.parse_args()
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")

    conn = connect()
    cur = conn.cursor()
    trials = fetch_trials(cur, args.trial_id)
    if args.limit:
        trials = trials[: args.limit]
    print(f"trials={len(trials)}")

    moved = 0
    deleted = 0
    parsed = 0
    skipped = 0
    samples = []

    class Src:
        __slots__ = ("division", "class_name", "placement", "dog_name")

        def __init__(self, d, c, p, line):
            self.division = d
            self.class_name = c
            self.placement = p
            head = re.split(r"owned\s*by", line, maxsplit=1, flags=re.I)[0]
            self.dog_name = head.strip(" ,")

    from pathlib import Path as _P

    for tid, year, tname, path in trials:
        print(f"  start {tid} {year} {str(tname)[:40]}", flush=True)
        rp = resolve_path(path)
        if not rp:
            skipped += 1
            continue
        try:
            if os.path.getsize(rp) > 3_000_000:
                skipped += 1
                continue
        except OSError:
            skipped += 1
            continue
        try:
            slots = parse_all_slots(_P(rp))
        except Exception:
            skipped += 1
            continue
        print(f"    slots={len(slots)}", flush=True)
        if not slots:
            skipped += 1
            continue
        placements = [Src(d, c, p, line) for d, c, p, line in slots]
        parsed += 1
        try:
            db = fetch_db_rows(cur, tid)
            print(f"    db={len(db)}", flush=True)
            moved, deleted = remount_trial(
                cur, tid, year, tname, placements, db, args.apply, samples, moved, deleted
            )
            if args.apply:
                conn.commit()
        except Exception as e:
            print(f"    fail {tid} {e}", flush=True)
            with contextlib.suppress(Exception):
                conn.rollback()
            skipped += 1
            continue
        print(f"    done moved={moved} deleted={deleted}", flush=True)

    if args.apply:
        print("committed")
    else:
        conn.rollback()
        print("dry-run")
    print(f"parsed={parsed} skipped={skipped} remounted={moved} twins_deleted={deleted}")
    for s in samples:
        print(" ", s)


if __name__ == "__main__":
    main()
