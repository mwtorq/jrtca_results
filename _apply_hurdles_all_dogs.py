#!/usr/bin/env python3
"""Insert/remount missing steeple-hurdles for ALL dogs from each trial source.

Yearbook/site: parse_all_slots. Trial Vault: parse_tv Rank/Nbr/Name only.
Does not create dogs or trials. Does not use parse_all_slots on vault files.
"""
from __future__ import annotations

import os
import re
import sys
from pathlib import Path

print("imports", flush=True)
import pyodbc
from populate_trialresults_fixed import normalize_placement_label
from _remount_source_divisions import (
    CONN,
    class_key,
    classes_ok,
    dogs_ok,
    ensure_tc,
    fam,
    res_key,
    resolve_path,
)
from _remount_midwest_2026_tv import DOG_RE, PLACE_RE, SKIP_PLACE, looks_div
from fix_racing_steeplechase_class_collapse import parse_all_slots

SKIP_RES = {x.upper() for x in SKIP_PLACE} | {"-- SCR --", "DQ", "F", "NP", "ABS", "SCR", "DNP"}


def is_vault(path: str) -> bool:
    p = (path or "").lower()
    return "vault" in p or "trialvault" in p


def is_champ(res: str, cls: str) -> bool:
    u = f"{res or ''} {cls or ''}".upper()
    return bool(re.search(r"\b(CHAMPION|RESERVE)\b", u))


def session_of(tname: str, cls: str, day: str | None, div: str = "") -> str:
    blob = f"{tname or ''} {cls or ''} {div or ''}".upper()
    moe = "MOE" in blob or "EARTHDOG" in blob or "MEMORIAL DAY BASH" in blob
    if day == "fri" or "FRIDAY" in blob:
        return "FRI"
    if day == "sun" or "SUNDAY" in blob:
        return "SUN"
    if day == "sat" or "SATURDAY" in blob:
        return "SAT"
    if not moe:
        return "ALL"
    return "ALL"


def src_dog(line: str) -> str:
    head = re.split(r"owned\s*by", line or "", maxsplit=1, flags=re.I)[0]
    head = re.sub(r"^#\d+:\s*", "", head).strip(" ,")
    return head


def resolve_src(path: str) -> str | None:
    rp = resolve_path(path)
    if not rp:
        return None
    if is_vault(rp) and rp.lower().endswith(".html"):
        raw = rp[:-5] + "_raw.txt"
        if os.path.isfile(raw):
            return raw
        alt = rp.replace(".html", "_raw.txt")
        if os.path.isfile(alt):
            return alt
    return rp


def file_has_hurdles(path: str) -> bool:
    try:
        with open(path, "rb") as f:
            data = f.read(4_000_000)
    except OSError:
        return False
    low = data.lower()
    return b"steeple" in low or b"hurdle" in low


def parse_tv_lines(lines: list[str]):
    day = "all"
    division = None
    friday_night = False
    out = []
    i = 0
    n = len(lines)

    def raw(j):
        return lines[j].strip() if 0 <= j < n else ""

    while i < n:
        s = raw(i)
        sl = s.lower()
        if sl in ("saturday", "saturday events") or s == "Saturday":
            day = "sat"
            division = None
            friday_night = False
        elif sl in ("sunday", "sunday events") or s == "Sunday":
            day = "sun"
            division = None
            friday_night = False
        elif sl in ("friday", "friday events"):
            day = "fri"
            division = None
            friday_night = False
        elif s.startswith("Friday Night"):
            day = "fri"
            friday_night = True
            division = looks_div(s) or "FRIDAY NIGHT RACING UNDER THE LIGHTS!"
            i += 1
            continue
        d = looks_div(s)
        if d:
            if day == "fri" and friday_night:
                df = fam(d)
                if df == "HURDLES":
                    d = "FRIDAY NIGHT STEEPLECHASE RACES"
                elif df == "RACING":
                    d = "FRIDAY NIGHT RACING UNDER THE LIGHTS!"
            division = d
            i += 1
            continue
        if s == "Rank" and raw(i + 1) == "Nbr" and raw(i + 2) == "Name":
            cls = raw(i - 1)
            if cls.isdigit():
                cls = raw(i - 2)
            prev = raw(i - 2) if not raw(i - 1).isdigit() else raw(i - 3)
            pd = looks_div(prev)
            if pd:
                if day == "fri" and friday_night:
                    df = fam(pd)
                    if df == "HURDLES":
                        pd = "FRIDAY NIGHT STEEPLECHASE RACES"
                    elif df == "RACING":
                        pd = "FRIDAY NIGHT RACING UNDER THE LIGHTS!"
                division = pd
            metric = raw(i + 4).lower()
            j = i + 5
            while j < n:
                place = raw(j)
                if place == "Rank" and raw(j + 1) == "Nbr":
                    break
                if looks_div(place) or place in (
                    "Saturday",
                    "Sunday",
                    "Friday Events",
                    "Legend",
                    "Friday",
                ):
                    break
                if not PLACE_RE.match(place) and place not in ("-- SCR --", "---"):
                    if place.isdigit() and len(place) <= 3:
                        j += 1
                        continue
                    break
                dog_line = raw(j + 2)
                m = DOG_RE.match(dog_line)
                if not m:
                    j += 1
                    continue
                dog = m.group(1).strip()
                label = normalize_placement_label(place.replace("-- SCR --", "SCR"), cls)
                step = 5 if metric in ("position", "time") else 4
                nxt_head = None
                for k in range(1, step + 1):
                    cand = raw(j + k)
                    if looks_div(cand) or cand in (
                        "Saturday",
                        "Sunday",
                        "Friday",
                        "Friday Events",
                        "Legend",
                    ) or cand.startswith("Friday Night"):
                        nxt_head = j + k
                        break
                if label.upper() in SKIP_RES or place in ("---", "-- SCR --"):
                    if nxt_head is not None:
                        j = nxt_head
                        break
                    j += step
                    continue
                if division and cls:
                    out.append((day, division, cls, label, dog))
                if nxt_head is not None:
                    j = nxt_head
                    break
                j += step
            i = j
            continue
        i += 1
    return out


def parse_tv_file(path: str):
    raw = open(path, encoding="utf-8", errors="replace").read()
    if "<" in raw[:2000] and "Rank" not in raw[:4000]:
        raw = re.sub(r"(?i)<br\s*/?>", "\n", raw)
        raw = re.sub(r"(?i)</p>", "\n", raw)
        raw = re.sub(r"<[^>]+>", "\n", raw)
        raw = raw.replace("&nbsp;", " ")
    lines = [ln.rstrip("\n") for ln in raw.splitlines()]
    return parse_tv_lines(lines)


def day_for_trial(tname: str) -> str | None:
    u = (tname or "").upper()
    if "SATURDAY" in u or re.search(r"\bSAT\b", u):
        return "sat"
    if "SUNDAY" in u or re.search(r"\bSUN\b", u):
        return "sun"
    if "FRIDAY" in u or re.search(r"\bFRI\b", u):
        return "fri"
    return None


_BAD_HURDLE = re.compile(
    r"AGILITY|JUMPER|ON\s+LEAD|OFF\s+LEAD|OBEDIENCE|SUB\s+NOVICE|"
    r"GO[\s\-]?TO[\s\-]?GROUND|\bGTG\b|SUPER\s*EARTH|NOSE|"
    r"CONFORMATION|BRUSH|LURE|CERTIFICATE|EARTHDOG|STARTERS|HAY|MAYHEM",
    re.I,
)
_RACE_CLASS = re.compile(
    r"\b(?:DOGS?|BITCHES|VETERAN|SENIOR|PUPP(?:Y|IES)|ADULT|"
    r"CHAMPION|CHALLENGE|HURDLE|STEEPLE|FLAT)\b",
    re.I,
)


def wanted_hurdle(div: str, cls: str) -> bool:
    u = f"{div or ''} {cls or ''}"
    if _BAD_HURDLE.search(u):
        return False
    if not (fam(div) == "HURDLES" or re.search(r"STEEPLE|HURDLE", u, re.I)):
        return False
    return bool(_RACE_CLASS.search(cls or "") or _RACE_CLASS.search(div or ""))


def map_div(div: str, cls: str) -> str:
    if wanted_hurdle(div, cls):
        if fam(div) == "HURDLES" and div and "STEEPLE" in (div or "").upper():
            return div
        return "STEEPLECHASE RACES"
    return div


def find_dog(sdog: str, trial_dogs: list[tuple[int, str]], cache: dict, cur) -> int | None:
    key = (sdog or "").strip().lower()
    if key in cache:
        return cache[key]
    hits = [did for did, nm in trial_dogs if dogs_ok(sdog, nm)]
    if len(hits) == 1:
        cache[key] = hits[0]
        return hits[0]
    if len(hits) > 1:
        cache[key] = None
        return None
    token = re.sub(r"[^A-Za-z0-9 ]", " ", sdog or "").split()
    if not token:
        cache[key] = None
        return None
    like = token[0] if len(token[0]) >= 4 else (sdog[:16] if sdog else "")
    if len(like) < 3:
        cache[key] = None
        return None
    cur.execute(
        "SELECT TOP 25 DogID, DogName FROM sResults.Dog WHERE DogName LIKE ?",
        f"%{like}%",
    )
    glob = [int(a) for a, b in cur.fetchall() if dogs_ok(sdog, b)]
    if len(glob) == 1:
        cache[key] = glob[0]
        return glob[0]
    cache[key] = None
    return None


def find_tc(db_classes, sdiv, scls):
    sf = fam(sdiv) if fam(sdiv) == "HURDLES" else (
        "HURDLES" if wanted_hurdle(sdiv, scls) else fam(sdiv)
    )
    for tcid, ddiv, dcls in db_classes:
        df = fam(ddiv)
        if df != "HURDLES" and not wanted_hurdle(ddiv, dcls):
            continue
        if classes_ok(scls, dcls) or class_key(scls) == class_key(dcls):
            return tcid
    return None


def process_trial(cur, tid, year, tname, path, apply, stats):
    rp = resolve_src(path)
    if not rp or not os.path.isfile(rp):
        stats["skip_nosource"] += 1
        print(f"  skip {tid} no-source {path}", flush=True)
        return
    try:
        if os.path.getsize(rp) > 3_000_000:
            stats["skip_nosource"] += 1
            print(f"  skip {tid} huge {rp}", flush=True)
            return
    except OSError:
        stats["skip_nosource"] += 1
        print(f"  skip {tid} size-fail", flush=True)
        return
    if not file_has_hurdles(rp):
        stats["skip_nohurdle_src"] += 1
        print(f"  skip {tid} no-hurdle-text", flush=True)
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
            raw_slots = parse_all_slots(Path(rp))
            slots = [(d, c, p, src_dog(line), None) for d, c, p, line in raw_slots]
    except Exception as e:
        stats["skip_nosource"] += 1
        print(f"  skip {tid} parse {e}", flush=True)
        return

    hslots = [
        s
        for s in slots
        if wanted_hurdle(s[0], s[1]) and (s[2] or "").upper() not in SKIP_RES
    ]
    print(f"  parse {tid} {year} vault={vault} slots={len(slots)} hurdles={len(hslots)}", flush=True)
    if not hslots:
        stats["skip_nohurdle_src"] += 1
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
    db = cur.fetchall()
    trial_dogs = list({(int(r[1]), r[2]) for r in db})
    db_classes = list({(int(r[6]), r[4], r[5]) for r in db})
    cache = {}
    stats["processed"] += 1

    def caps(dog_id, sess):
        has_h_non = has_h_ch = False
        for pid, did, dname, res, ddiv, dcls, tcid in db:
            if int(did) != int(dog_id):
                continue
            if session_of(tname, dcls, None) != sess and sess != "ALL":
                if session_of(tname, dcls, None) != sess:
                    continue
            f = fam(ddiv)
            if f != "HURDLES" and not wanted_hurdle(ddiv, dcls):
                continue
            if is_champ(res, dcls):
                has_h_ch = True
            else:
                has_h_non = True
        return has_h_non, has_h_ch

    for sdiv, scls, sres, sdog, day in hslots:
        dog_id = find_dog(sdog, trial_dogs, cache, cur)
        if dog_id is None:
            stats["skip_nodog"] += 1
            continue
        sess = session_of(tname, scls, day)
        champ = is_champ(sres, scls)
        sr = res_key(sres)

        already = False
        remount = None
        for row in db:
            pid, did, dname, res, ddiv, dcls, tcid = row
            if int(did) != int(dog_id):
                continue
            if res_key(res) != sr:
                continue
            df = fam(ddiv)
            hurdle_db = df == "HURDLES" or wanted_hurdle(ddiv, dcls)
            if hurdle_db:
                already = True
                break
            if not hurdle_db:
                # wrong-division twin: conformation / leftover / generic racing
                du = (ddiv or "").upper()
                leftover = df in ("UNKNOWN",) or "NOSE" in du or du == "UNKNOWN"
                conf = df == "CONFORMATION"
                generic_r = df == "RACING" and not re.search(r"FLAT|STEEPLE|HURDLE", du)
                if conf or leftover or generic_r:
                    remount = row
        if already:
            stats["already"] += 1
            continue

        dest_div = map_div(sdiv, scls)
        dest_tc = find_tc(db_classes, dest_div, scls)
        if dest_tc is None:
            dest_tc = ensure_tc(cur, tid, dest_div, scls)
            db_classes.append((int(dest_tc), dest_div, scls))

        if remount is not None:
            pid, did, dname, res, ddiv, dcls, tcid = remount
            if apply and int(dest_tc) != int(tcid):
                cur.execute(
                    "UPDATE sResults.TrialPlacements SET TrialClassID=? WHERE TrialPlacementsID=?",
                    dest_tc,
                    pid,
                )
            db[:] = [
                (pid, did, dname, res, dest_div, scls, dest_tc) if r[0] == pid else r
                for r in db
            ]
            stats["remounted"] += 1
            continue

        has_h_non, has_h_ch = caps(dog_id, sess)
        if champ and has_h_ch:
            stats["already"] += 1
            continue
        if (not champ) and has_h_non:
            stats["already"] += 1
            continue

        new_pid = -1
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
                dest_tc,
                dog_id,
                sres,
                tid,
            )
        db.append((new_pid, dog_id, sdog, sres, dest_div, scls, dest_tc))
        if (dog_id, sdog) not in trial_dogs:
            trial_dogs.append((dog_id, sdog))
        stats["inserted"] += 1


def willie_flat_no_h(cur):
    cur.execute(
        """
        SELECT l.Year, l.TrialListID, l.TrialName, div.DivisionName, c.ClassName, p.Result
        FROM sResults.TrialPlacements p
        JOIN sResults.TrialClass tc ON tc.TrialClassID=p.TrialClassID
        JOIN sResults.TrialList l ON l.TrialListID=tc.TrialListID
        JOIN sResults.Class c ON c.ClassID=tc.ClassID
        JOIN sResults.Division div ON div.DivisionID=c.DivisionID
        WHERE p.DogID=1062796
        ORDER BY l.Year, l.TrialListID
        """
    )
    rows = cur.fetchall()
    by = {}
    for y, tid, name, div, cls, res in rows:
        by.setdefault(tid, {"y": y, "name": name, "fams": set(), "rows": []})
        f = fam(div)
        if wanted_hurdle(div, cls):
            f = "HURDLES"
        by[tid]["fams"].add(f)
        by[tid]["rows"].append((f, div, cls, res))
    gaps = []
    for tid, info in sorted(by.items()):
        if "RACING" in info["fams"] and "HURDLES" not in info["fams"]:
            gaps.append((info["y"], tid, info["name"], info["rows"]))
    return gaps


def twin_counts(cur):
    out = []
    for tid in (1863, 1864, 1865, 1873, 1874, 1880, 1949, 1950):
        cur.execute("SELECT TrialName FROM sResults.TrialList WHERE TrialListID=?", tid)
        nm = cur.fetchone()
        if not nm:
            out.append((tid, 0, "GONE"))
            continue
        cur.execute(
            """
            SELECT COUNT(*) FROM sResults.TrialPlacements p
            JOIN sResults.TrialClass tc ON tc.TrialClassID=p.TrialClassID
            WHERE tc.TrialListID=?
            """,
            tid,
        )
        n = int(cur.fetchone()[0])
        out.append((tid, n, nm[0]))
    return out


def main():
    apply = "--apply" in sys.argv
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    print("connecting", flush=True)
    cn = pyodbc.connect(CONN, timeout=8)
    cn.timeout = 40
    cur = cn.cursor()
    print("connected apply=" + str(apply), flush=True)
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
    stats = {
        "processed": 0,
        "remounted": 0,
        "inserted": 0,
        "already": 0,
        "skip_nosource": 0,
        "skip_nodog": 0,
        "skip_nohurdle_src": 0,
    }
    for i, (tid, year, tname, path) in enumerate(trials, 1):
        print(f"[{i}/{len(trials)}] start {tid} {year} {str(tname)[:50]}", flush=True)
        try:
            process_trial(cur, int(tid), year, tname or "", path or "", apply, stats)
            if apply:
                cn.commit()
        except Exception as e:
            print(f"  FAIL {tid} {e}", flush=True)
            try:
                cn.rollback()
            except Exception:
                pass
            stats["skip_nosource"] += 1
        if i % 25 == 0:
            print(f"progress {stats}", flush=True)

    print(
        f"DONE processed={stats['processed']} remounted={stats['remounted']} "
        f"inserted={stats['inserted']} already={stats['already']} "
        f"skip_nosource={stats['skip_nosource']} skip_nodog={stats['skip_nodog']} "
        f"skip_nohurdle_src={stats['skip_nohurdle_src']}",
        flush=True,
    )
    print("==== Willie flat-without-hurdles ====", flush=True)
    gaps = willie_flat_no_h(cur)
    print(f"flat_no_hurdles={len(gaps)}", flush=True)
    for y, tid, name, rows in gaps:
        print(f"  {y} tid={tid} {name}", flush=True)
        for f, div, cls, res in rows:
            if f == "RACING":
                print(f"    {res:10} {div} / {cls}", flush=True)
    print("==== twin counts ====", flush=True)
    for tid, n, name in twin_counts(cur):
        print(f"  tid={tid} n={n} | {name}", flush=True)
    cn.close()
    print("done", flush=True)


if __name__ == "__main__":
    main()
