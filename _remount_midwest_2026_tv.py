#!/usr/bin/env python3
"""Remount 2026 Midwest Summer I & II from the Trial Vault Rank/Nbr/Name file.

Does not use parse_all_slots. Does not delete placements. Does not create dogs.
"""
from __future__ import annotations

import re
import sys

import pyodbc
from populate_trialresults_fixed import normalize_placement_label
from _remount_source_divisions import CONN, dogs_ok, ensure_tc, fam

SRC = r"2026\debug_trialvault_Midwest_Summer_Celebration_I_and_II_raw.txt"

DIV_HEADS = {
    "CONFORMATION",
    "YOUTH",
    "RACING",
    "GO-TO-GROUND",
    "GO TO GROUND",
    "SUPER EARTH",
    "AGILITY",
    "NOSE WORK",
    "BRUSH HUNT",
    "LURE COURSING",
    "HAY STACK HUNT",
    "TRAIL & LOCATE OBSTACLE COURSE",
    "MW MAYHEM",
    "EARTHDOG STEEPLECHASE RACES",
    "HURDLES",
    "HURDLE RACES",
    "HURDLE RACE",
    "FRIDAY NIGHT RACING",
    "FRIDAY NIGHT STEEPLE",
}

SKIP_PLACE = {"SCR", "DNP", "DQ", "F", "NP", "ABS", "---", "--", ""}
PLACE_RE = re.compile(
    r"^(1st|2nd|3rd|4th|5th|6th|Champion|Reserve|Best|-- SCR --|---)$",
    re.I,
)
DOG_RE = re.compile(r"^#\d+:\s*(.+)$")


def canon_div(name: str) -> str:
    u = (name or "").strip()
    ul = u.upper()
    if ul.startswith("GO-TO-GROUND") or ul.startswith("GO TO GROUND"):
        return "GO-TO-GROUND"
    if ul.startswith("SUPER EARTH"):
        return "SUPER EARTH"
    if "FRIDAY NIGHT" in ul and ("STEEPLE" in ul or "HURDLE" in ul):
        return "FRIDAY NIGHT STEEPLECHASE RACES"
    if "FRIDAY NIGHT RACING" in ul or ("FRIDAY NIGHT" in ul and "LIGHTS" in ul):
        return "FRIDAY NIGHT RACING UNDER THE LIGHTS!"
    if ul in ("RACING", "FLAT RACES", "FLAT RACE") or ul.startswith("FLAT RACE"):
        return "RACING DIVISION - FLAT RACES"
    if ul.startswith("RACING") and "CHAMPION" not in ul and "STEEPLE" not in ul:
        return "RACING DIVISION - FLAT RACES"
    if "STEEPLE" in ul or "HURDLE" in ul:
        return "STEEPLECHASE RACES"
    if ul.startswith("EARTHDOG STEEPLE"):
        return "EARTHDOG STEEPLECHASE RACES"
    if ul.startswith("NOSE"):
        return "NOSE WORK"
    if ul.startswith("CONFORMATION"):
        return "CONFORMATION"
    if ul.startswith("YOUTH"):
        return "YOUTH"
    if ul.startswith("AGILITY"):
        return "AGILITY"
    if "BRUSH" in ul:
        return "BRUSH HUNT"
    if "LURE" in ul:
        return "LURE COURSING"
    if "HAY STACK" in ul:
        return "HAY STACK HUNT"
    if "MAYHEM" in ul or "THUNDER" in ul:
        return "MW MAYHEM"
    if "TRAIL" in ul and "LOCATE" in ul:
        return "TRAIL & LOCATE OBSTACLE COURSE"
    return u


def looks_div(line: str) -> str | None:
    u = line.strip()
    if not u or len(u) > 80:
        return None
    ul = u.upper()
    for h in DIV_HEADS:
        if ul == h or ul.startswith(h):
            return canon_div(u)
    if "STEEPLECHASE" in ul and "RACE" in ul:
        return canon_div(u)
    if ul in ("FLAT RACES", "FLAT RACE"):
        return "RACING DIVISION - FLAT RACES"
    if ul in ("HURDLES", "HURDLE", "HURDLE RACES", "HURDLE RACE"):
        return "STEEPLECHASE RACES"
    return None


def parse_tv(path: str):
    lines = [ln.rstrip("\n") for ln in open(path, encoding="utf-8", errors="replace")]
    day = None
    division = None
    out = []
    i = 0
    n = len(lines)

    def raw(j):
        return lines[j].strip() if 0 <= j < n else ""

    while i < n:
        s = raw(i)
        if s == "Saturday" or (
            "Summer Celebration I" in s and "II" not in s.replace("I & II", "")
        ):
            if s == "Saturday" or s.startswith("Midwest Jack Russell"):
                day = "sat"
                division = None
        if s == "Sunday" or (
            s.startswith("Midwest Jack Russell") and "Celebration II" in s
        ):
            day = "sun"
            division = None
        d = looks_div(s)
        if d:
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
                division = pd
            metric = raw(i + 4).lower()
            j = i + 5
            while j < n:
                place = raw(j)
                if place == "Rank" and raw(j + 1) == "Nbr":
                    break
                if looks_div(place) or place in ("Saturday", "Sunday", "Friday Events", "Legend"):
                    break
                if place.startswith("Midwest Jack Russell"):
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
                if label.upper() in SKIP_PLACE or place in ("---", "-- SCR --"):
                    step = 5 if metric in ("position", "time") else 4
                    j += step
                    continue
                if day and division and cls:
                    out.append((day, division, cls, label, dog))
                j += 5 if metric in ("position", "time") else 4
            i = j
            continue
        i += 1
    return out


def main():
    print("parse", SRC, flush=True)
    src = parse_tv(SRC)
    by_day = {"sat": 0, "sun": 0}
    for d, *_ in src:
        by_day[d] = by_day.get(d, 0) + 1
    print(f"source_rows={len(src)} sat={by_day.get('sat')} sun={by_day.get('sun')}", flush=True)

    conn = pyodbc.connect(CONN, timeout=8)
    conn.timeout = 20
    cur = conn.cursor()
    cur.execute(
        """
        SELECT TrialListID, TrialName
        FROM sResults.TrialList
        WHERE Year=2026 AND TrialName LIKE '%Midwest%Summer%'
        ORDER BY TrialListID
        """
    )
    trials = cur.fetchall()
    print("trials", [(r[0], r[1]) for r in trials], flush=True)
    if len(trials) < 2:
        sys.exit("expected Midwest Summer I and II")
    id_sat, id_sun = int(trials[0][0]), int(trials[1][0])
    day_tid = {"sat": id_sat, "sun": id_sun}

    moved = 0
    inserted = 0
    skipped_nodog = 0
    already = 0

    for day, tid in day_tid.items():
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
        used = set()
        day_src = [r for r in src if r[0] == day]
        print(f"tid={tid} db={len(db)} src={len(day_src)}", flush=True)

        dogs_on_trial = {int(r[1]): r[2] for r in db}

        for _day, sdiv, scls, sres, sdog in day_src:
            match = None
            for row in db:
                pid, dog_id, dname, res, ddiv, dcls, tcid = row
                if pid in used:
                    continue
                if (res or "").strip().lower() != sres.strip().lower():
                    continue
                if not dogs_ok(sdog, dname):
                    continue
                match = row
                if fam(ddiv) == fam(sdiv):
                    break
            if match:
                pid, dog_id, dname, res, ddiv, dcls, tcid = match
                used.add(pid)
                if fam(ddiv) == fam(sdiv) and dcls.strip().lower() == scls.strip().lower():
                    already += 1
                    continue
                new_tc = ensure_tc(cur, tid, sdiv, scls)
                if int(new_tc) != int(tcid):
                    cur.execute(
                        "UPDATE sResults.TrialPlacements SET TrialClassID=? WHERE TrialPlacementsID=?",
                        new_tc,
                        pid,
                    )
                    moved += 1
                else:
                    already += 1
                continue

            dog_id = None
            for did, dname in dogs_on_trial.items():
                if dogs_ok(sdog, dname):
                    dog_id = did
                    break
            if dog_id is None:
                cur.execute(
                    "SELECT TOP 5 DogID, DogName FROM sResults.Dog WHERE DogName LIKE ?",
                    f"%{sdog[:20]}%",
                )
                for did, dname in cur.fetchall():
                    if dogs_ok(sdog, dname):
                        dog_id = int(did)
                        break
            if dog_id is None:
                skipped_nodog += 1
                continue
            new_tc = ensure_tc(cur, tid, sdiv, scls)
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
            inserted += 1

    conn.commit()
    print(
        f"moved={moved} inserted={inserted} already={already} skipped_nodog={skipped_nodog}",
        flush=True,
    )


if __name__ == "__main__":
    main()
