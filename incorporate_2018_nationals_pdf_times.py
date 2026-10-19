#!/usr/bin/env python3
"""
Incorporate 2018 Nationals PDF times into TrialPlacements_Times for
2018 JRTCA National Trial WITHOUT duplicating placements or times.

Matching cascade:
  1) existing placement by trial + class + dog (+ result when placed)
  2) catalog EntryNumber (dog_id from PDF) -> DogID/DogName
  3) create DNP/DQ placement only when no matching placement exists
  4) insert time only when TrialPlacementsID has no Times row yet
"""
from __future__ import annotations

import csv
import re
import sys
from collections import defaultdict
from pathlib import Path

import pyodbc
from normalize_trialresults_data import (
    normalize_class_name_full,
    normalize_division_name_full,
    normalize_dog_name,
)
from parse_catalog import names_are_similar

sys.stdout.reconfigure(encoding="utf-8", errors="replace")

ROOT = Path(r"c:\Users\mw\OneDrive - timberwilde.net\repos\jrtca_results")
CSV_PATH = ROOT / "_extracted_2018_nationals_times" / "all_entries_ready_to_insert.csv"

DRIVERS = [
    "ODBC Driver 17 for SQL Server",
    "ODBC Driver 18 for SQL Server",
    "SQL Server",
]


def connect():
    last = None
    for d in DRIVERS:
        try:
            return pyodbc.connect(
                f"DRIVER={{{d}}};SERVER=Ldahsar\\SQLEXPRESS;"
                f"DATABASE=TrialResults;Trusted_Connection=yes;",
                timeout=15,
            )
        except Exception as e:
            last = e
    raise SystemExit(f"DB connect failed: {last}")


def scrub(s):
    if s is None:
        return ""
    s = str(s).replace("\ufffd", "½").replace("�", "½")
    return re.sub(r"\s+", " ", s).strip()


def dog_key(name: str) -> str:
    name = scrub(name)
    name = re.split(r",\s*owned\b", name, flags=re.I)[0]
    return normalize_dog_name(name) or name


def dog_compact(name: str) -> str:
    return re.sub(r"[^A-Z0-9]", "", (name or "").upper())


def dogs_match(a: str, b: str) -> bool:
    if not a or not b:
        return False
    if a == b or dog_compact(a) == dog_compact(b):
        return True
    return names_are_similar(a, b)


def result_key(r: str) -> str:
    r = scrub(r).upper()
    aliases = {
        "1": "1ST", "2": "2ND", "3": "3RD", "4": "4TH", "5": "5TH", "6": "6TH",
        "CH": "CHAMPION", "CHAMP": "CHAMPION", "RES": "RESERVE",
        "RESERVE CHAMPION": "RESERVE", "D/Q": "DQ", "DISQ": "DQ",
    }
    return aliases.get(r, r)


ORDINAL_MAP = {
    "1ST": "1st", "2ND": "2nd", "3RD": "3rd", "4TH": "4th", "5TH": "5th", "6TH": "6th",
    "CHAMPION": "Champion", "RESERVE": "Reserve", "DNP": "DNP", "DQ": "DQ",
}


def canonical_result(r: str) -> str:
    return ORDINAL_MAP.get(result_key(r), scrub(r) or "DNP")


def map_pdf_class_to_db(class_name: str) -> tuple[str, str]:
    """Return (division_hint, class_name_for_match)."""
    c = scrub(class_name)
    low = c.lower()

    # Strip leading "Class NNN: "
    c2 = re.sub(r"^Class\s+\d+\s*:\s*", "", c, flags=re.I).strip()

    if "stakes" in low:
        return ("THUNDER TUNNEL", "STAKES GTG")

    if "super earth" in low:
        div = "SUPER EARTH"
        # normalize common SE names toward DB forms
        name = c2
        name = re.sub(r"^Super Earth,\s*", "", name, flags=re.I)
        if re.search(r"6[- ]?12\s*month\s*puppies", name, re.I):
            name = "6 up to 12 month Puppy Super Earth"
        elif re.search(r"open super earth", name, re.I) and "veteran" not in name.lower():
            name = "Open Super Earth"
        elif re.search(r"veteran open super earth", name, re.I):
            name = "Veteran Open Super Earth"
        elif re.search(r"puppy super earth championship", name, re.I):
            name = "6 up to 12 month Puppy Certificate Super Earth"
        elif re.search(r'10".*12.*super earth championship', name, re.I) and "veteran" not in name.lower() and "senior" not in name.lower():
            name = 'Adult Certificate Super Earth, 10" up to 12½"'
        elif re.search(r'over 12.*15".*super earth championship', name, re.I) and "veteran" not in name.lower() and "senior" not in name.lower():
            name = 'Adult Certificate Super Earth, Over 12½" up to 15"'
        elif re.search(r'veteran.*10".*12', name, re.I) and "super earth" in name.lower():
            name = 'Veteran Certificate Super Earth, 10" up to 12½"'
        elif re.search(r'veteran.*over 12', name, re.I) and "super earth" in name.lower():
            name = 'Veteran Certificate Super Earth, Over 12½" up to 15"'
        elif re.search(r'senior.*10".*12', name, re.I) and "super earth" in name.lower():
            name = 'Senior Certificate Super Earth, 10" up to 12½"'
        elif re.search(r'senior.*over 12', name, re.I) and "super earth" in name.lower():
            name = 'Senior Certificate Super Earth, Over 12½" up to 15"'
        return (div, name)

    # GTG
    div = "GO-TO-GROUND"
    name = c2
    name = re.sub(r"^Go-To-Ground,\s*", "", name, flags=re.I)
    name = re.sub(r"^GTG,\s*", "", name, flags=re.I)
    if re.search(r"open puppy", name, re.I):
        name = "Open Puppy"
    elif re.search(r"open adult", name, re.I):
        name = "Open Adult"
    elif re.search(r"novice puppy", name, re.I):
        name = "Novice Puppy"
    elif re.search(r"novice adult", name, re.I):
        name = "Novice Adult"
    elif re.search(r"puppy championship", name, re.I):
        name = "PUPPY CHAMPIONSHIP"
    elif re.search(r'10".*12.*champion certificate', name, re.I) and "veteran" not in name.lower() and "senior" not in name.lower():
        name = 'Championship Certificate, 10" up to 12½"'
    elif re.search(r'over 12.*15".*champion certificate', name, re.I) and "veteran" not in name.lower() and "senior" not in name.lower():
        name = 'Championship Certificate, Over 12½" up to 15"'
    elif re.search(r'veteran.*10".*12', name, re.I):
        name = 'Veteran Championship Certificate, 10" up to 12½"'
    elif re.search(r'veteran.*over 12', name, re.I):
        name = 'Veteran Championship Certificate, Over 12½" up to 15"'
    elif re.search(r'senior.*10".*12', name, re.I):
        name = 'Senior Championship Certificate, 10" up to 12½"'
    elif re.search(r'senior.*over 12', name, re.I):
        name = 'Senior Championship Certificate, Over 12½" up to 15"'
    return (div, name)


def class_tokens(name: str) -> set[str]:
    n = normalize_class_name_full(name) or name
    n = n.upper().replace("½", "HALF")
    n = re.sub(r"[^A-Z0-9]+", " ", n)
    stop = {"THE", "AND", "TO", "UP", "OF", "A", "AN", "CLASS", "GTG", "GO"}
    return set(n.split()) - stop


def class_sim(a: str, b: str) -> float:
    ta, tb = class_tokens(a), class_tokens(b)
    if not ta or not tb:
        return 0.0
    return len(ta & tb) / len(ta | tb)


def load_csv() -> list[dict]:
    rows = []
    with CSV_PATH.open(encoding="utf-8") as f:
        for r in csv.DictReader(f):
            time = scrub(r.get("time"))
            place = canonical_result(r.get("insert_result") or r.get("placement") or "DNP")
            # Skip empty useless rows
            if not scrub(r.get("dog_name")) and not scrub(r.get("dog_id")):
                continue
            # DQ without time is still insertable as placement; time optional
            if not time and place != "DQ":
                # nothing to store in Times and not a DQ marker
                continue
            if time.upper() in {"N/T", "NT", "—", "-", "UNKNOWN"}:
                # still create DNP placement? User asked for times; skip time insert but keep if DQ
                if place != "DQ":
                    # store literal N/T as time for DNP correlation if desired
                    pass
            div, cls = map_pdf_class_to_db(r["class_name"])
            rows.append(
                {
                    "source_pdf": r["source_pdf"],
                    "page": r["page"],
                    "pdf_class": scrub(r["class_name"]),
                    "division_hint": div,
                    "class_hint": cls,
                    "entry_number": scrub(r.get("dog_id")),
                    "dog_name": scrub(r.get("dog_name")),
                    "owner_name": scrub(r.get("owner_name")),
                    "time": time or None,
                    "result": place,
                }
            )
    return rows


def main():
    print("=" * 80)
    print("Incorporate 2018 Nationals PDF times (no duplicate placements/times)")
    print("=" * 80)

    entries = load_csv()
    print(f"CSV entries usable: {len(entries)}")

    conn = connect()
    cur = conn.cursor()
    print("Connected")

    # Resolve trial
    cur.execute(
        """
        SELECT TrialListID, TrialName
        FROM [sResults].[TrialList]
        WHERE Year = 2018 AND TrialName LIKE '%JRTCA National%'
        ORDER BY TrialListID
        """
    )
    trials = cur.fetchall()
    if not trials:
        raise SystemExit("2018 JRTCA National Trial not found")
    trial_id, trial_name = trials[0]
    print(f"Trial: {trial_id} {trial_name}")
    if len(trials) > 1:
        print(f"  NOTE: {len(trials)} matching trials; using first: {trials}")

    # Catalog entry number -> dog
    cur.execute(
        """
        SELECT EntryNumber, DogID, DogName, OwnerID
        FROM [sResults].[CatalogEntry]
        WHERE Year = '2018' OR Year = 2018
        """
    )
    catalog_by_entry: dict[str, tuple] = {}
    for entry_no, dog_id, dog_name, owner_id in cur.fetchall():
        key = scrub(entry_no)
        if key:
            catalog_by_entry[key] = (dog_id, scrub(dog_name), owner_id)
    print(f"Catalog entries for 2018: {len(catalog_by_entry)}")

    # Existing placements for this trial
    cur.execute(
        """
        SELECT
            p.TrialPlacementsID,
            p.TrialClassID,
            p.DogID,
            p.Result,
            d.DogName,
            o.OwnerName,
            dv.DivisionName,
            c.ClassName,
            pt.TrialPlacements_TimesID,
            pt.Time
        FROM [sResults].[TrialPlacements] p
        JOIN [sResults].[TrialClass] tc ON tc.TrialClassID = p.TrialClassID
        JOIN [sResults].[Class] c ON c.ClassID = tc.ClassID
        JOIN [sResults].[Division] dv ON dv.DivisionID = c.DivisionID
        JOIN [sResults].[Dog] d ON d.DogID = p.DogID
        LEFT JOIN [sResults].[Owner] o ON o.OwnerID = d.OwnerID
        LEFT JOIN [sResults].[TrialPlacements_Times] pt
            ON pt.TrialPlacementsID = p.TrialPlacementsID
        WHERE p.TrialListID = ?
        """,
        trial_id,
    )
    placements = []
    for r in cur.fetchall():
        placements.append(
            {
                "placement_id": r[0],
                "trialclass_id": r[1],
                "dog_id": r[2],
                "result": scrub(r[3]),
                "result_key": result_key(r[3] or ""),
                "dog_name": scrub(r[4]),
                "dog_key": dog_key(r[4] or ""),
                "dog_compact": dog_compact(r[4] or ""),
                "owner_name": scrub(r[5]),
                "division": scrub(r[6]),
                "division_key": normalize_division_name_full(r[6] or ""),
                "class_name": scrub(r[7]),
                "class_key": normalize_class_name_full(r[7] or "", r[6] or ""),
                "times_id": r[8],
                "existing_time": scrub(r[9]) if r[9] is not None else None,
            }
        )
    print(f"Existing placements: {len(placements)}")
    print(f"Already have times: {sum(1 for p in placements if p['times_id'] is not None)}")

    # Index trial classes
    cur.execute(
        """
        SELECT tc.TrialClassID, tc.ClassID, c.ClassName, dv.DivisionName, dv.DivisionID
        FROM [sResults].[TrialClass] tc
        JOIN [sResults].[Class] c ON c.ClassID = tc.ClassID
        JOIN [sResults].[Division] dv ON dv.DivisionID = c.DivisionID
        WHERE tc.TrialListID = ?
        """,
        trial_id,
    )
    trial_classes = []
    for r in cur.fetchall():
        trial_classes.append(
            {
                "trialclass_id": r[0],
                "class_id": r[1],
                "class_name": scrub(r[2]),
                "class_key": normalize_class_name_full(r[2] or "", r[3] or ""),
                "division": scrub(r[3]),
                "division_key": normalize_division_name_full(r[3] or ""),
                "division_id": r[4],
            }
        )

    by_dog_id = defaultdict(list)
    by_dog_compact = defaultdict(list)
    for p in placements:
        by_dog_id[p["dog_id"]].append(p)
        by_dog_compact[p["dog_compact"]].append(p)

    def find_trial_class(div_hint: str, class_hint: str):
        div_key = normalize_division_name_full(div_hint)
        class_key = normalize_class_name_full(class_hint, div_hint)
        # exact
        for tc in trial_classes:
            if tc["division_key"] == div_key and tc["class_key"] == class_key:
                return tc
        # same division, best class similarity
        scored = []
        for tc in trial_classes:
            if tc["division_key"] != div_key and not (
                "STAKES" in div_hint.upper() and "THUNDER" in tc["division_key"].upper()
            ) and not (
                "SUPER EARTH" in div_hint.upper() and "GO-TO-GROUND" in tc["division_key"].upper()
                and "SUPER EARTH" in tc["class_name"].upper()
            ):
                # allow SE classes that were normalized under GTG
                if "SUPER EARTH" in div_hint.upper() and "SUPER EARTH" in (tc["class_name"] + " " + tc["division"]).upper():
                    pass
                elif "STAKES" in div_hint.upper() and "STAKES" in (tc["class_name"] + " " + tc["division"]).upper():
                    pass
                else:
                    continue
            sim = class_sim(class_hint, tc["class_name"])
            scored.append((sim, tc))
        if not scored:
            # any class similarity in trial
            for tc in trial_classes:
                sim = class_sim(class_hint, tc["class_name"])
                if sim >= 0.45:
                    scored.append((sim, tc))
        if not scored:
            return None
        scored.sort(key=lambda x: -x[0])
        if scored[0][0] < 0.35:
            return None
        return scored[0][1]

    def resolve_dog(entry: dict):
        # catalog by entry number
        if entry["entry_number"] and entry["entry_number"] in catalog_by_entry:
            dog_id, cat_name, owner_id = catalog_by_entry[entry["entry_number"]]
            return dog_id, cat_name or entry["dog_name"], owner_id, "catalog_entry"
        # existing dog by name within trial placements
        dk = dog_key(entry["dog_name"])
        dc = dog_compact(entry["dog_name"])
        hits = by_dog_compact.get(dc, [])
        if not hits and dk:
            for p in placements:
                if dogs_match(dk, p["dog_key"]):
                    hits.append(p)
                    break
        if hits:
            return hits[0]["dog_id"], hits[0]["dog_name"], None, "trial_dog_name"
        # global dog table by name
        if entry["dog_name"]:
            cur.execute(
                "SELECT TOP 5 DogID, DogName, OwnerID FROM [sResults].[Dog] WHERE DogName = ?",
                entry["dog_name"],
            )
            exact = cur.fetchall()
            if len(exact) == 1:
                return exact[0][0], exact[0][1], exact[0][2], "global_dog_exact"
        return None, entry["dog_name"], None, None

    def find_existing_placement(entry, dog_id, tc):
        candidates = []
        pool = []
        if dog_id:
            pool.extend(by_dog_id.get(dog_id, []))
        dc = dog_compact(entry["dog_name"])
        if dc:
            pool.extend(by_dog_compact.get(dc, []))
        # unique by placement_id
        seen = set()
        uniq = []
        for p in pool:
            if p["placement_id"] in seen:
                continue
            seen.add(p["placement_id"])
            uniq.append(p)

        rk = result_key(entry["result"])
        for p in uniq:
            # prefer same trial class
            class_ok = True
            if tc:
                class_ok = p["trialclass_id"] == tc["trialclass_id"] or class_sim(
                    entry["class_hint"], p["class_name"]
                ) >= 0.45
            if not class_ok and tc:
                # still allow if dog unique in timed class family
                if class_sim(entry["class_hint"], p["class_name"]) < 0.3:
                    continue
            score = class_sim(entry["class_hint"], p["class_name"])
            if p["result_key"] == rk:
                score += 2
            elif rk in {"DNP", "DQ"} and p["result_key"] in {"DNP", "DQ", "0", ""}:
                score += 1.5
            elif rk in {"DNP", "DQ"}:
                # PDF DNP/DQ may match an existing placed row for same dog/class
                # Prefer exact result; otherwise allow same class+dog for time attach
                # only when existing has no conflicting place? Attach time to placed row if same dog/class
                score += 0.5
            candidates.append((score, p))

        if not candidates and tc:
            # search all placements in that trial class by dog name
            for p in placements:
                if p["trialclass_id"] != tc["trialclass_id"]:
                    continue
                if dog_id and p["dog_id"] == dog_id:
                    score = 2
                elif dogs_match(dog_key(entry["dog_name"]), p["dog_key"]):
                    score = 1.5
                else:
                    continue
                if p["result_key"] == rk:
                    score += 2
                candidates.append((score, p))

        if not candidates:
            return None
        candidates.sort(key=lambda x: (-x[0], x[1]["placement_id"]))
        return candidates[0][1]

    def get_or_create_dog(dog_name: str, owner_name: str):
        from populate_trialresults_fixed import get_or_create_dog as gcd, get_or_create_owner

        owner_id = get_or_create_owner(cur, owner_name) if owner_name else None
        dog_id = gcd(cur, dog_name, owner_id)
        return dog_id, owner_id

    def next_placement_id():
        cur.execute("SELECT ISNULL(MAX(TrialPlacementsID),0)+1 FROM [sResults].[TrialPlacements]")
        return int(cur.fetchone()[0])

    def next_times_id():
        cur.execute("SELECT ISNULL(MAX(TrialPlacements_TimesID),0)+1 FROM [sResults].[TrialPlacements_Times]")
        return int(cur.fetchone()[0])

    stats = defaultdict(int)
    miss_examples = []
    next_pid = next_placement_id()
    next_tid = next_times_id()

    # Track newly created so we don't duplicate within this run
    created_keys = set()  # (trialclass_id, dog_id, result_key)

    for entry in entries:
        stats["input"] += 1
        tc = find_trial_class(entry["division_hint"], entry["class_hint"])
        dog_id, resolved_name, owner_id, dog_how = resolve_dog(entry)

        if not dog_id and entry["dog_name"]:
            # will create if needed for DNP/DQ
            pass

        existing = find_existing_placement(entry, dog_id, tc) if (dog_id or entry["dog_name"]) else None

        if existing:
            stats["matched_placement"] += 1
            # If existing already has a time, skip (no duplicate times)
            if existing["times_id"] is not None:
                stats["skipped_existing_time"] += 1
                continue
            if not entry["time"]:
                # DQ without time: placement exists, nothing to insert into Times
                stats["skipped_no_time"] += 1
                continue
            # Insert time only
            cur.execute(
                """
                IF NOT EXISTS (
                    SELECT 1 FROM [sResults].[TrialPlacements_Times]
                    WHERE TrialPlacementsID = ?
                )
                INSERT INTO [sResults].[TrialPlacements_Times]
                    (TrialPlacements_TimesID, TrialPlacementsID, Time)
                VALUES (?, ?, ?)
                """,
                existing["placement_id"],
                next_tid,
                existing["placement_id"],
                entry["time"],
            )
            if cur.rowcount:
                stats["times_inserted"] += 1
                next_tid += 1
                existing["times_id"] = next_tid - 1
                existing["existing_time"] = entry["time"]
            else:
                stats["skipped_existing_time"] += 1
            continue

        # No existing placement — only create for DNP/DQ (or any result if class found)
        if not tc:
            stats["unmatched_class"] += 1
            if len(miss_examples) < 25:
                miss_examples.append(("no_class", entry))
            continue

        if not entry["dog_name"] and not dog_id:
            stats["unmatched_dog"] += 1
            if len(miss_examples) < 25:
                miss_examples.append(("no_dog", entry))
            continue

        if not dog_id:
            dog_id, owner_id = get_or_create_dog(entry["dog_name"], entry["owner_name"])
            stats["dogs_created"] += 1
            dog_how = "created"

        result_text = entry["result"]
        ck = (tc["trialclass_id"], dog_id, result_key(result_text))
        if ck in created_keys:
            stats["skipped_dup_in_batch"] += 1
            continue

        # Final safety: does placement already exist for this class/dog/result?
        cur.execute(
            """
            SELECT p.TrialPlacementsID, pt.TrialPlacements_TimesID
            FROM [sResults].[TrialPlacements] p
            LEFT JOIN [sResults].[TrialPlacements_Times] pt
                ON pt.TrialPlacementsID = p.TrialPlacementsID
            WHERE p.TrialListID = ? AND p.TrialClassID = ? AND p.DogID = ?
              AND ISNULL(p.Result,'') = ?
            """,
            trial_id,
            tc["trialclass_id"],
            dog_id,
            result_text,
        )
        exists_row = cur.fetchone()
        if exists_row:
            pid, tid = exists_row
            stats["matched_placement"] += 1
            if tid is not None:
                stats["skipped_existing_time"] += 1
            elif entry["time"]:
                cur.execute(
                    """
                    IF NOT EXISTS (
                        SELECT 1 FROM [sResults].[TrialPlacements_Times]
                        WHERE TrialPlacementsID = ?
                    )
                    INSERT INTO [sResults].[TrialPlacements_Times]
                        (TrialPlacements_TimesID, TrialPlacementsID, Time)
                    VALUES (?, ?, ?)
                    """,
                    pid,
                    next_tid,
                    pid,
                    entry["time"],
                )
                if cur.rowcount:
                    stats["times_inserted"] += 1
                    next_tid += 1
                else:
                    stats["skipped_existing_time"] += 1
            else:
                stats["skipped_no_time"] += 1
            continue

        # Create placement (DNP/DQ/etc.) then optional time
        cur.execute(
            """
            INSERT INTO [sResults].[TrialPlacements]
                (TrialPlacementsID, TrialListID, TrialClassID, DogID, Result)
            VALUES (?, ?, ?, ?, ?)
            """,
            next_pid,
            trial_id,
            tc["trialclass_id"],
            dog_id,
            result_text,
        )
        stats["placements_created"] += 1
        created_keys.add(ck)
        pid = next_pid
        next_pid += 1

        # track in memory indexes
        newp = {
            "placement_id": pid,
            "trialclass_id": tc["trialclass_id"],
            "dog_id": dog_id,
            "result": result_text,
            "result_key": result_key(result_text),
            "dog_name": resolved_name or entry["dog_name"],
            "dog_key": dog_key(resolved_name or entry["dog_name"]),
            "dog_compact": dog_compact(resolved_name or entry["dog_name"]),
            "owner_name": entry["owner_name"],
            "division": tc["division"],
            "division_key": tc["division_key"],
            "class_name": tc["class_name"],
            "class_key": tc["class_key"],
            "times_id": None,
            "existing_time": None,
        }
        placements.append(newp)
        by_dog_id[dog_id].append(newp)
        by_dog_compact[newp["dog_compact"]].append(newp)

        if entry["time"]:
            cur.execute(
                """
                INSERT INTO [sResults].[TrialPlacements_Times]
                    (TrialPlacements_TimesID, TrialPlacementsID, Time)
                VALUES (?, ?, ?)
                """,
                next_tid,
                pid,
                entry["time"],
            )
            stats["times_inserted"] += 1
            next_tid += 1
        else:
            stats["placement_without_time"] += 1

    conn.commit()
    conn.close()

    print("\n=== RESULTS ===")
    for k in sorted(stats.keys()):
        print(f"  {k}: {stats[k]}")
    if miss_examples:
        print("\n=== miss examples ===")
        for kind, e in miss_examples[:15]:
            print(f"  [{kind}] {e['pdf_class']} | #{e['entry_number']} {e['dog_name']} | {e['result']} | {e['time']}")


if __name__ == "__main__":
    main()
