#!/usr/bin/env python3
"""Restore missing flats/hurdles/champs for ALL dogs from trial sources.

Also: Best->Champion on racing champs; drop extra FLAT-division Champion when
a steeple champ already exists; drop Olson's JR from 2005 Gold Rush;
copy Wilderness site flats onto TV twins. No new dogs/trials.
"""
from __future__ import annotations

import os
import re
import sys
from pathlib import Path

print("imports", flush=True)
import pyodbc
from populate_trialresults_fixed import normalize_placement_label
from fix_racing_steeplechase_class_collapse import parse_all_slots
from _apply_hurdles_all_dogs import (
    SKIP_RES,
    day_for_trial,
    file_has_hurdles,
    find_dog,
    is_champ,
    is_vault,
    parse_tv_file,
    resolve_src,
    session_of,
    src_dog,
    wanted_hurdle,
)
from _remount_source_divisions import CONN, class_key, classes_ok, ensure_tc, fam, res_key

_BAD = re.compile(
    r"AGILITY|JUMPER|ON\s+LEAD|OFF\s+LEAD|OBEDIENCE|SUB\s+NOVICE|"
    r"GO[\s\-]?TO[\s\-]?GROUND|\bGTG\b|SUPER\s*EARTH|NOSE|"
    r"CONFORMATION|BRUSH|LURE|CERTIFICATE|EARTHDOG|STARTERS|HAY|MAYHEM|"
    r"BARN|RAT|TUNNEL|TRAIL",
    re.I,
)
_RACE = re.compile(
    r"\b(?:DOGS?|BITCHES|VETERAN|SENIOR|PUPP(?:Y|IES)|ADULT|"
    r"CHAMPION|CHALLENGE|HURDLE|STEEPLE|FLAT|RACING)\b",
    re.I,
)


def wanted_flat(div, cls):
    u = f"{div or ''} {cls or ''}"
    if _BAD.search(u) or wanted_hurdle(div, cls):
        return False
    if is_champ("", cls) and "FLAT" not in u:
        return False
    if "FLAT" in u.upper() or "FRIDAY NIGHT RACING" in u.upper():
        return bool(_RACE.search(u))
    if fam(div) == "RACING" and not re.search(r"STEEPLE|HURDLE|CHAMPION", u, re.I):
        return bool(_RACE.search(cls or "") or _RACE.search(div or ""))
    return False


def wanted_champ(div, cls, res=""):
    u = f"{div or ''} {cls or ''} {res or ''}"
    if _BAD.search(f"{div or ''} {cls or ''}"):
        return False
    if not re.search(r"CHAMPION|RESERVE|\bBEST\b", u, re.I):
        return False
    return bool(re.search(r"RACING|STEEPLE|HURDLE|FLAT", u, re.I))


def kind(div, cls, res=""):
    if wanted_hurdle(div, cls):
        return "HURDLES" if not is_champ(res, cls) else "HCHAMP"
    if wanted_champ(div, cls, res):
        return "HCHAMP"
    if wanted_flat(div, cls):
        return "FLAT"
    return None


def dest_for(k, div, cls):
    if k == "FLAT":
        if "FRIDAY" in (div or "").upper():
            return div
        if fam(div) == "RACING" and "FLAT" in (div or "").upper():
            return div
        return "RACING DIVISION - FLAT RACES"
    if k in ("HURDLES", "HCHAMP"):
        if "FRIDAY" in (div or "").upper() and fam(div) in ("HURDLES", "RACING"):
            return div
        if fam(div) == "HURDLES" and "STEEPLE" in (div or "").upper():
            return div
        return "STEEPLECHASE RACES"
    return div


def process_trial(cur, tid, tname, path, apply, stats):
    rp = resolve_src(path)
    if not rp or not os.path.isfile(rp):
        stats["skip_nosource"] += 1
        return
    try:
        if os.path.getsize(rp) > 3_000_000:
            stats["skip_nosource"] += 1
            return
    except OSError:
        stats["skip_nosource"] += 1
        return

    vault = is_vault(rp) or is_vault(path)
    try:
        if vault:
            tv = parse_tv_file(rp)
            want_day = day_for_trial(tname)
            slots = []
            for day, div, cls, place, dog in tv:
                if want_day and day not in ("all", want_day):
                    continue
                slots.append((div, cls, place, dog, day))
        else:
            if not file_has_hurdles(rp) and b"flat" not in open(rp, "rb").read(4_000_000).lower() and b"racing" not in open(rp, "rb").read(4_000_000).lower():
                stats["skip_norace"] += 1
                return
            raw_slots = parse_all_slots(Path(rp))
            slots = [(d, c, p, src_dog(line), None) for d, c, p, line in raw_slots]
    except Exception as e:
        print(f"  parse-fail {tid} {e}", flush=True)
        stats["skip_nosource"] += 1
        return

    want = []
    for sdiv, scls, sres, sdog, day in slots:
        if (sres or "").upper() in SKIP_RES:
            continue
        k = kind(sdiv, scls, sres)
        if k:
            want.append((k, sdiv, scls, sres, sdog, day))
    if not want:
        stats["skip_norace"] += 1
        return

    cur.execute(
        """
        SELECT p.TrialPlacementsID, p.DogID, dog.DogName, p.Result,
               div.DivisionName, c.ClassName, p.TrialClassID
        FROM sResults.TrialPlacements p
        JOIN sResults.Dog dog ON dog.DogID=p.DogID
        JOIN sResults.TrialClass tc ON tc.TrialClassID=p.TrialClassID
        JOIN sResults.Class c ON c.ClassID=tc.ClassID
        JOIN sResults.Division div ON div.DivisionID=c.DivisionID
        WHERE tc.TrialListID=?
        """,
        tid,
    )
    db = [list(r) for r in cur.fetchall()]
    trial_dogs = list({(int(r[1]), r[2]) for r in db})
    cache = {}
    stats["processed"] += 1

    def has_kind(dog_id, sess, k):
        for row in db:
            if int(row[1]) != int(dog_id):
                continue
            if sess != "ALL" and session_of(tname, row[5], None) != sess:
                continue
            if kind(row[4], row[5], row[3]) == k:
                return True
        return False

    for k, sdiv, scls, sres, sdog, day in want:
        dog_id = find_dog(sdog, trial_dogs, cache, cur)
        if dog_id is None:
            stats["skip_nodog"] += 1
            continue
        sess = session_of(tname, scls, day)
        sr = res_key(sres)
        already = False
        remount = None
        for row in db:
            if int(row[1]) != int(dog_id) or res_key(row[3]) != sr:
                continue
            dk = kind(row[4], row[5], row[3])
            if dk == k:
                already = True
                break
            if dk is None and (
                fam(row[4]) in ("CONFORMATION", "UNKNOWN")
                or (fam(row[4]) == "RACING" and k != "FLAT")
            ):
                remount = row
        if already:
            stats["already"] += 1
            continue
        if remount is None and has_kind(dog_id, sess, k):
            stats["already"] += 1
            continue
        dest = dest_for(k, sdiv, scls)
        new_tc = ensure_tc(cur, tid, dest, scls)
        if remount is not None:
            if apply and int(new_tc) != int(remount[6]):
                cur.execute(
                    "UPDATE sResults.TrialPlacements SET TrialClassID=? WHERE TrialPlacementsID=?",
                    new_tc,
                    remount[0],
                )
            remount[4], remount[5], remount[6] = dest, scls, new_tc
            stats["remounted"] += 1
            continue
        if apply:
            cur.execute("SELECT ISNULL(MAX(TrialPlacementsID),0)+1 FROM sResults.TrialPlacements")
            new_pid = int(cur.fetchone()[0])
            cur.execute(
                """
                INSERT INTO sResults.TrialPlacements
                    (TrialPlacementsID, TrialClassID, DogID, Result, TrialListID)
                VALUES (?, ?, ?, ?, ?)
                """,
                new_pid,
                new_tc,
                dog_id,
                sres,
                tid,
            )
            db.append([new_pid, dog_id, sdog, sres, dest, scls, new_tc])
        stats["inserted"] += 1


def fix_best_and_extra_flat_champ(cur, apply, stats):
    cur.execute(
        """
        SELECT p.TrialPlacementsID, p.DogID, tc.TrialListID, p.Result,
               div.DivisionName, c.ClassName
        FROM sResults.TrialPlacements p
        JOIN sResults.TrialClass tc ON tc.TrialClassID=p.TrialClassID
        JOIN sResults.Class c ON c.ClassID=tc.ClassID
        JOIN sResults.Division div ON div.DivisionID=c.DivisionID
        WHERE (p.Result LIKE 'Best%' OR c.ClassName LIKE '%CHAMPION%RESERVE%'
               OR c.ClassName LIKE '%Racing Champion%')
        """
    )
    rows = cur.fetchall()
    for pid, dog_id, tid, res, div, cls in rows:
        if (res or "").strip().lower() == "best" and wanted_champ(div, cls, res):
            if apply:
                cur.execute(
                    "UPDATE sResults.TrialPlacements SET Result='Champion' WHERE TrialPlacementsID=?",
                    pid,
                )
            stats["best_to_champ"] += 1

    cur.execute(
        """
        SELECT p.TrialPlacementsID, p.DogID, tc.TrialListID, p.Result,
               div.DivisionName, c.ClassName
        FROM sResults.TrialPlacements p
        JOIN sResults.TrialClass tc ON tc.TrialClassID=p.TrialClassID
        JOIN sResults.Class c ON c.ClassID=tc.ClassID
        JOIN sResults.Division div ON div.DivisionID=c.DivisionID
        WHERE (p.Result LIKE 'Champion%' OR p.Result LIKE 'Reserve%' OR p.Result LIKE 'Best%')
          AND div.DivisionName LIKE '%FLAT%'
          AND (c.ClassName LIKE '%CHAMPION%' OR c.ClassName LIKE '%RESERVE%')
        """
    )
    extras = cur.fetchall()
    for pid, dog_id, tid, res, div, cls in extras:
        cur.execute(
            """
            SELECT COUNT(*)
            FROM sResults.TrialPlacements p
            JOIN sResults.TrialClass tc ON tc.TrialClassID=p.TrialClassID
            JOIN sResults.Class c ON c.ClassID=tc.ClassID
            JOIN sResults.Division div ON div.DivisionID=c.DivisionID
            WHERE p.DogID=? AND tc.TrialListID=? AND p.TrialPlacementsID<>?
              AND (div.DivisionName LIKE '%STEEPLE%' OR div.DivisionName LIKE '%HURDLE%')
              AND (p.Result LIKE 'Champion%' OR p.Result LIKE 'Reserve%' OR p.Result LIKE 'Best%')
            """,
            dog_id,
            tid,
            pid,
        )
        if int(cur.fetchone()[0]) > 0:
            if apply:
                cur.execute(
                    "DELETE FROM sResults.TrialPlacements_Times WHERE TrialPlacementsID=?",
                    pid,
                )
                cur.execute(
                    "DELETE FROM sResults.TrialPlacements WHERE TrialPlacementsID=?",
                    pid,
                )
            stats["drop_flat_champ"] += 1


def drop_gold_rush_jr(cur, apply, stats):
    cur.execute(
        """
        SELECT p.TrialPlacementsID
        FROM sResults.TrialPlacements p
        JOIN sResults.TrialClass tc ON tc.TrialClassID=p.TrialClassID
        JOIN sResults.TrialList l ON l.TrialListID=tc.TrialListID
        WHERE p.DogID=1255818 AND l.Year=2005 AND l.TrialName LIKE '%Gold Rush%'
        """
    )
    ids = [int(r[0]) for r in cur.fetchall()]
    for pid in ids:
        if apply:
            cur.execute("DELETE FROM sResults.TrialPlacements_Times WHERE TrialPlacementsID=?", pid)
            cur.execute("DELETE FROM sResults.TrialPlacements WHERE TrialPlacementsID=?", pid)
        stats["drop_jr_goldrush"] += 1


def copy_wilderness_flats(cur, apply, stats):
    pairs = ((1863, 1873), (1864, 1874))
    for src, dst in pairs:
        cur.execute(
            """
            SELECT p.DogID, p.Result, div.DivisionName, c.ClassName
            FROM sResults.TrialPlacements p
            JOIN sResults.TrialClass tc ON tc.TrialClassID=p.TrialClassID
            JOIN sResults.Class c ON c.ClassID=tc.ClassID
            JOIN sResults.Division div ON div.DivisionID=c.DivisionID
            WHERE tc.TrialListID=?
            """,
            src,
        )
        src_rows = cur.fetchall()
        cur.execute(
            """
            SELECT p.DogID, p.Result, div.DivisionName, c.ClassName
            FROM sResults.TrialPlacements p
            JOIN sResults.TrialClass tc ON tc.TrialClassID=p.TrialClassID
            JOIN sResults.Class c ON c.ClassID=tc.ClassID
            JOIN sResults.Division div ON div.DivisionID=c.DivisionID
            WHERE tc.TrialListID=?
            """,
            dst,
        )
        dst_have = {(int(d), res_key(r), kind(dv, cl, r)) for d, r, dv, cl in cur.fetchall()}
        for dog_id, res, div, cls in src_rows:
            k = kind(div, cls, res)
            if k != "FLAT":
                continue
            if (int(dog_id), res_key(res), "FLAT") in dst_have:
                continue
            dest = dest_for("FLAT", div, cls)
            if apply:
                tcid = ensure_tc(cur, dst, dest, cls)
                cur.execute("SELECT ISNULL(MAX(TrialPlacementsID),0)+1 FROM sResults.TrialPlacements")
                new_pid = int(cur.fetchone()[0])
                cur.execute(
                    """
                    INSERT INTO sResults.TrialPlacements
                        (TrialPlacementsID, TrialClassID, DogID, Result, TrialListID)
                    VALUES (?, ?, ?, ?, ?)
                    """,
                    new_pid,
                    tcid,
                    dog_id,
                    res,
                    dst,
                )
            stats["copy_wild_flat"] += 1
            dst_have.add((int(dog_id), res_key(res), "FLAT"))


def main():
    apply = "--apply" in sys.argv
    print("connecting", flush=True)
    cn = pyodbc.connect(CONN, timeout=8)
    cn.timeout = 40
    cur = cn.cursor()
    print("connected apply=" + str(apply), flush=True)
    stats = {
        "processed": 0,
        "remounted": 0,
        "inserted": 0,
        "already": 0,
        "skip_nosource": 0,
        "skip_nodog": 0,
        "skip_norace": 0,
        "best_to_champ": 0,
        "drop_flat_champ": 0,
        "drop_jr_goldrush": 0,
        "copy_wild_flat": 0,
    }
    fix_best_and_extra_flat_champ(cur, apply, stats)
    drop_gold_rush_jr(cur, apply, stats)
    copy_wilderness_flats(cur, apply, stats)
    if apply:
        cn.commit()
    print(f"specials { {k: stats[k] for k in ('best_to_champ','drop_flat_champ','drop_jr_goldrush','copy_wild_flat')} }", flush=True)

    cur.execute(
        """
        SELECT TrialListID, Year, TrialName, TrialResultFilePath
        FROM sResults.TrialList
        WHERE TrialResultFilePath IS NOT NULL AND LTRIM(RTRIM(TrialResultFilePath)) <> ''
        ORDER BY Year, TrialListID
        """
    )
    trials = cur.fetchall()
    print(f"trials_with_path={len(trials)}", flush=True)
    for i, (tid, year, tname, path) in enumerate(trials, 1):
        print(f"[{i}/{len(trials)}] {tid} {year}", flush=True)
        try:
            process_trial(cur, int(tid), tname or "", path or "", apply, stats)
            if apply:
                cn.commit()
        except Exception as e:
            print(f"  FAIL {tid} {e}", flush=True)
            try:
                cn.rollback()
            except Exception:
                pass
        if i % 50 == 0:
            print(f"progress {stats}", flush=True)
    print(f"DONE {stats}", flush=True)
    cn.close()


if __name__ == "__main__":
    main()
