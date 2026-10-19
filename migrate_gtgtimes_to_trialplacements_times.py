#!/usr/bin/env python3
"""
Migrate GTG/Super Earth times from TrialData.sJRTCA.TrialPlacements_GTGTimes
into TrialResults.sResults.TrialPlacements_Times.

Matching cascade:
  1) year/trial + normalized division/class + dog (+ result)
  2) same class bucket, placement/result only (when dog names diverge)
  3) loose class key (punctuation/encoding tolerant)
  4) cross-division within trial using class-token similarity + dog/result
  5) raw trial file bridge: locate dog/result under original class header,
     then map to TrialResults placement (handles post-load division/class
     normalization in TrialResults)
"""

from __future__ import annotations

import argparse
import os
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

REPO_ROOT = Path(__file__).resolve().parent

DRIVERS = [
    "ODBC Driver 17 for SQL Server",
    "ODBC Driver 18 for SQL Server",
    "SQL Server",
]

# Local raw result files used when TrialResults class/division were normalized.
RAW_FILE_MAP: dict[tuple[int, str], list[str]] = {
    (2008, "JRTCA"): [
        "2008/jrtca_national_trial.txt",
        "2008/jrtca_national_trial.html",
    ],
    (2014, "JRTCA"): [
        "2014/2014 JRTCA National Trial.txt",
        "2014/2014 JRTCA National Trial.htm",
    ],
    (2015, "JRTCA"): [
        "2015/2015 National Trial.txt",
        "2015/JRTCA National Trial.txt",
        "2015/JRTCA National Trial.html",
        "2015/2015 National Trial.htm",
    ],
    (2016, "JRTCA"): [
        "2016/JRTCA National Trial.txt",
        "2016/JRTCA National Trial.html",
        "2016/2016 JRTCA National Trial.html",
        "2016/debug_trial_2016_JRTCA_National_Trial_raw.txt",
    ],
    (2017, "JRTCA"): [
        "2017/jrtca nationals.txt",
        "2017/2017 JRTCA National Trial.html",
        "2017/debug_trial_2017_JRTCA_National_Trial_raw.txt",
    ],
    (2017, "JRTCC"): [
        "2017/jrtcc nationals.txt",
        "JRTCC/2017 JRTCC National Trial Results.txt",
        "JRTCC/2017 JRTCC National Trial.txt",
    ],
    (2018, "JRTCA"): [
        "2018/JRTCA National Trial.txt",
        "2018/2018 JRTCA National Trial.html",
        "2018/debug_trial_2018_JRTCA_National_Trial_raw.txt",
    ],
}


def connect(database: str) -> pyodbc.Connection:
    last = None
    for driver in DRIVERS:
        try:
            return pyodbc.connect(
                f"DRIVER={{{driver}}};SERVER=localhost\\SQLEXPRESS;"
                f"DATABASE={database};Trusted_Connection=yes;",
                timeout=15,
            )
        except Exception as exc:  # noqa: BLE001
            last = exc
    raise SystemExit(f"Could not connect to {database}: {last}")


def scrub(text: str | None) -> str:
    if not text:
        return ""
    text = str(text)
    text = text.replace("\ufffd", "½").replace("�", "½")
    text = text.replace("\x9d", "").replace("\x9c", "").replace("\x81", "")
    text = text.replace("Â", "")
    text = re.sub(r"[“”„″]", '"', text)
    text = re.sub(r"[‘’]", "'", text)
    return text


def trial_org(name: str) -> str:
    n = (name or "").upper()
    if "JRTCC" in n:
        return "JRTCC"
    return "JRTCA"


def trial_key(year: int, name: str) -> tuple[int, str]:
    org = trial_org(name)
    return (int(year), f"{org} NATIONAL TRIAL")


def clean_dog(name: str) -> str:
    name = scrub(name)
    name = re.split(r",\s*owned\b", name, flags=re.IGNORECASE)[0]
    name = re.sub(r"\s+", " ", name).strip()
    return normalize_dog_name(name) or name


def dog_compact(name: str) -> str:
    return re.sub(r"[^A-Z0-9]", "", (name or "").upper())


def dogs_match(a: str, b: str, *, fuzzy: bool = True) -> bool:
    if not a or not b:
        return False
    if a == b:
        return True
    if dog_compact(a) == dog_compact(b):
        return True
    return bool(fuzzy and names_are_similar(a, b))


def result_key(result: str) -> str:
    r = scrub(result).strip().upper()
    aliases = {
        "CH": "CHAMPION",
        "CHAMP": "CHAMPION",
        "RES": "RESERVE",
        "RESERVE CHAMPION": "RESERVE",
    }
    return aliases.get(r, r)


def class_key(class_name: str, division: str) -> str:
    return normalize_class_name_full(scrub(class_name), scrub(division)) or scrub(class_name)


def loose_class_key(class_name: str, division: str) -> str:
    n = class_key(class_name, division)
    n = n.upper().replace("½", "HALF")
    n = re.sub(r"[^A-Z0-9]+", " ", n)
    n = re.sub(r"\s+", " ", n).strip()
    n = n.replace("CHAMPIONSHIP CERTIFICATE", "CERT")
    n = n.replace("CERTIFICATE", "CERT")
    n = n.replace("CHAMPION AND RESERVE", "CHAMP RESERVE")
    n = n.replace("CHAMPION & RESERVE", "CHAMP RESERVE")
    n = n.replace("AND RESERVE", "RESERVE")
    n = n.replace("& RESERVE", "RESERVE")
    return n


def class_tokens(class_name: str, division: str = "") -> set[str]:
    stop = {
        "THE",
        "AND",
        "TO",
        "UP",
        "OF",
        "A",
        "AN",
        "CLASS",
        "ENTRIES",
        "MONTH",
        "MONTHS",
        "YEAR",
        "YEARS",
        "OLDER",
    }
    tokens = set(loose_class_key(class_name, division).split()) - stop
    return tokens


def class_similarity(a_class: str, a_div: str, b_class: str, b_div: str) -> float:
    a = class_tokens(a_class, a_div)
    b = class_tokens(b_class, b_div)
    if not a or not b:
        return 0.0
    return len(a & b) / len(a | b)


def is_timed_event_class(division: str, class_name: str) -> bool:
    blob = f"{division} {class_name}".upper()
    markers = (
        "GO-TO-GROUND",
        "GO TO GROUND",
        "GTG",
        "SUPER EARTH",
        "SUPEREARTH",
        "MASTER'S DEN",
        "MASTERS DEN",
        "STAKES GTG",
        "THUNDER TUNNEL",
    )
    return any(m in blob for m in markers)


def resolve_raw_file(year: int, trial_name: str) -> Path | None:
    org = trial_org(trial_name)
    for rel in RAW_FILE_MAP.get((year, org), []):
        path = REPO_ROOT / rel
        if path.is_file():
            return path
    # Generic discovery under year folder / JRTCC
    patterns = []
    if org == "JRTCC":
        patterns = [
            REPO_ROOT / "JRTCC" / f"{year} JRTCC National*",
            REPO_ROOT / str(year) / f"*JRTCC*",
        ]
    else:
        patterns = [
            REPO_ROOT / str(year) / f"*{year}*JRTCA*National*",
            REPO_ROOT / str(year) / "*JRTCA*National*",
            REPO_ROOT / str(year) / f"*{year}*National*",
        ]
    candidates: list[Path] = []
    for pattern in patterns:
        candidates.extend(Path(pattern.parent).glob(pattern.name))
    # Prefer .txt over .html; skip catalog/entry files
    scored = []
    for path in candidates:
        name = path.name.lower()
        if "catalog" in name or "entries" in name or name.startswith("debug_"):
            continue
        score = 0
        if path.suffix.lower() in {".txt", ".raw.txt"}:
            score += 3
        if "jrtca" in name and org == "JRTCA":
            score += 2
        if "jrtcc" in name and org == "JRTCC":
            score += 2
        if "national" in name:
            score += 1
        scored.append((score, path))
    if not scored:
        return None
    scored.sort(key=lambda x: (-x[0], len(str(x[1]))))
    return scored[0][1]


def load_raw_placements(year: int, trial_name: str) -> list[dict]:
    path = resolve_raw_file(year, trial_name)
    if not path:
        return []
    try:
        from populate_trialresults_fixed import parse_trial_source_file
    except Exception as exc:  # noqa: BLE001
        print(f"  [WARN] could not import parser for {path.name}: {exc}")
        return []

    trial_info, placements, err = parse_trial_source_file(str(path), year, quiet=True)
    if err or not placements:
        print(f"  [WARN] raw parse failed for {path}: {err}")
        return []
    rows = []
    for p in placements:
        rows.append(
            {
                "division": scrub(getattr(p, "division", "") or ""),
                "class_name": scrub(getattr(p, "class_name", "") or ""),
                "result": scrub(getattr(p, "placement", "") or getattr(p, "result", "") or ""),
                "dog": scrub(getattr(p, "dog_name", "") or ""),
                "time": scrub(getattr(p, "time", "") or ""),
                "source_file": str(path),
            }
        )
    print(f"  Raw file {path.relative_to(REPO_ROOT)}: {len(rows)} placements")
    return rows


def load_source_rows(conn: pyodbc.Connection) -> list[dict]:
    cur = conn.cursor()
    cur.execute(
        """
        SELECT
            g.TrialPlacements_GTGTimesID,
            g.Time,
            l.Year,
            l.TrialName,
            dv.DivisionName,
            cl.ClassName,
            p.Result,
            d.DogName
        FROM [sJRTCA].[TrialPlacements_GTGTimes] g
        JOIN [sJRTCA].[TrialPlacements] p ON p.TrialPlacementsID = g.TrialPlacementsID
        JOIN [sJRTCA].[TrialList] l ON l.TrialListID = p.TrialListID
        JOIN [sJRTCA].[TrialClass] tc ON tc.TrialClassID = p.TrialClassID
        JOIN [sJRTCA].[Class] cl ON cl.ClassID = tc.ClassID
        JOIN [sJRTCA].[Division] dv ON dv.DivisionID = cl.DivisionID
        JOIN [sAll].[Dog] d ON d.DogID = p.DogID
        ORDER BY l.Year, l.TrialName, dv.DivisionName, cl.ClassName, p.Result
        """
    )
    rows = []
    for r in cur.fetchall():
        rows.append(
            {
                "gtg_id": int(r[0]),
                "time": scrub(r[1]),
                "year": int(r[2]),
                "trial": scrub(r[3]),
                "division": scrub(r[4]),
                "class_name": scrub(r[5]),
                "result": scrub(r[6]),
                "dog": scrub(r[7]),
                "trial_key": trial_key(int(r[2]), r[3]),
            }
        )
    return rows


def load_target_rows(conn: pyodbc.Connection, years: list[int]) -> list[dict]:
    cur = conn.cursor()
    cur.execute(
        f"""
        SELECT
            p.TrialPlacementsID,
            l.Year,
            l.TrialName,
            dv.DivisionName,
            cl.ClassName,
            p.Result,
            d.DogName,
            pt.TrialPlacements_TimesID,
            pt.Time
        FROM [sResults].[TrialPlacements] p
        JOIN [sResults].[TrialList] l ON l.TrialListID = p.TrialListID
        JOIN [sResults].[TrialClass] tc ON tc.TrialClassID = p.TrialClassID
        JOIN [sResults].[Class] cl ON cl.ClassID = tc.ClassID
        JOIN [sResults].[Division] dv ON dv.DivisionID = cl.DivisionID
        JOIN [sResults].[Dog] d ON d.DogID = p.DogID
        LEFT JOIN [sResults].[TrialPlacements_Times] pt
            ON pt.TrialPlacementsID = p.TrialPlacementsID
        WHERE l.Year IN ({",".join("?" for _ in years)})
          AND l.TrialName LIKE '%National%'
        """,
        years,
    )
    rows = []
    for r in cur.fetchall():
        year = int(r[1])
        division = scrub(r[3])
        class_name = scrub(r[4])
        rows.append(
            {
                "placement_id": int(r[0]),
                "year": year,
                "trial": scrub(r[2]),
                "trial_key": trial_key(year, r[2]),
                "division": division,
                "class_name": class_name,
                "division_key": normalize_division_name_full(division),
                "class_key": class_key(class_name, division),
                "loose_class": loose_class_key(class_name, division),
                "result_key": result_key(r[5]),
                "dog_key": clean_dog(r[6]),
                "times_id": r[7],
                "existing_time": scrub(r[8]) if r[8] is not None else None,
            }
        )
    return rows


def choose_from_bucket(bucket: list[dict], dog: str, rk: str):
    if not bucket:
        return None, None

    dog_result = [
        t for t in filter_dog_candidates(bucket, dog) if t["result_key"] == rk
    ]
    if dog_result:
        return dog_result[0], "dog+result" if len(dog_result) == 1 else "dog+result_multi"

    dog_only = filter_dog_candidates(bucket, dog)
    if len(dog_only) == 1:
        return dog_only[0], "dog"
    if len(dog_only) > 1:
        prefer = [t for t in dog_only if t["result_key"] == rk]
        return (prefer or dog_only)[0], "dog_multi"

    by_result = [t for t in bucket if t["result_key"] == rk]
    if len(by_result) == 1:
        return by_result[0], "placement"
    if len(by_result) > 1:
        return by_result[0], "placement_multi"
    return None, None


def filter_dog_candidates(candidates: list[dict], dog: str) -> list[dict]:
    """Prefer exact/compact dog matches; only fuzzy-compare a small remainder."""
    if not candidates or not dog:
        return []
    compact = dog_compact(dog)
    exact = [
        t
        for t in candidates
        if t["dog_key"] == dog or t.get("dog_compact") == compact
    ]
    if exact:
        return exact
    fuzzy = []
    for t in candidates:
        if dogs_match(dog, t["dog_key"], fuzzy=True):
            fuzzy.append(t)
            if len(fuzzy) >= 8:
                break
    return fuzzy


def best_cross_division_match(
    by_trial_result: dict[tuple, list],
    by_trial_dog: dict[tuple, list],
    src: dict,
    dog: str,
    rk: str,
):
    tk = src["trial_key"]
    # Narrow by result first, then dog
    result_bucket = by_trial_result.get((tk, rk), [])
    dog_hits = filter_dog_candidates(result_bucket, dog)
    if not dog_hits:
        # dog anywhere in trial, then require result
        dog_hits = [
            t
            for t in filter_dog_candidates(by_trial_dog.get((tk, dog_compact(dog)), [])
                                           or by_trial_result.get((tk, rk), []), dog)
            if t["result_key"] == rk
        ]

    timed_hits = [
        t
        for t in dog_hits
        if is_timed_event_class(t["division"], t["class_name"])
        or is_timed_event_class(src["division"], src["class_name"])
    ]
    pool = timed_hits or dog_hits
    if not pool:
        return None, None

    if len(pool) == 1:
        return pool[0], "cross_dog+result"

    pool.sort(
        key=lambda t: (
            -class_similarity(
                src["class_name"], src["division"], t["class_name"], t["division"]
            ),
            t["placement_id"],
        )
    )
    return pool[0], "cross_dog+result_best"


def raw_file_match(
    src: dict,
    dog: str,
    rk: str,
    raw_by_trial: dict[tuple[int, str], list[dict]],
    by_trial_result: dict[tuple, list],
):
    raw_rows = raw_by_trial.get(src["trial_key"])
    if raw_rows is None:
        # Lazy-load only when needed
        raw_rows = load_raw_placements(src["year"], src["trial"])
        raw_by_trial[src["trial_key"]] = raw_rows
    if not raw_rows:
        return None, None

    raw_hits = []
    for raw in raw_rows:
        raw_dog = clean_dog(raw["dog"])
        if not dogs_match(dog, raw_dog, fuzzy=False) and not dogs_match(dog, raw_dog):
            continue
        raw_rk = result_key(raw["result"])
        sim = class_similarity(
            src["class_name"], src["division"], raw["class_name"], raw["division"]
        )
        if raw_rk == rk:
            raw_hits.append((sim + 1.0, raw, raw_dog, raw_rk))
        elif sim >= 0.45:
            raw_hits.append((sim, raw, raw_dog, raw_rk))
    if not raw_hits:
        return None, None

    raw_hits.sort(key=lambda x: -x[0])
    _, raw, raw_dog, raw_rk = raw_hits[0]

    # Map onto TrialResults using result index, ignore division mismatches
    candidates = list(by_trial_result.get((src["trial_key"], raw_rk), []))
    if rk != raw_rk:
        candidates.extend(by_trial_result.get((src["trial_key"], rk), []))
    dog_hits = filter_dog_candidates(candidates, raw_dog or dog)
    if not dog_hits:
        return None, None

    dog_hits.sort(
        key=lambda t: (
            -class_similarity(
                raw["class_name"], raw["division"], t["class_name"], t["division"]
            )
            - (0.15 if is_timed_event_class(t["division"], t["class_name"]) else 0.0),
            t["placement_id"],
        )
    )
    return dog_hits[0], "raw_file"


def match_all(source_rows: list[dict], target_rows: list[dict]):
    by_class: dict[tuple, list] = defaultdict(list)
    by_loose: dict[tuple, list] = defaultdict(list)
    by_trial_result: dict[tuple, list] = defaultdict(list)
    by_trial_dog: dict[tuple, list] = defaultdict(list)

    for row in target_rows:
        row["dog_compact"] = dog_compact(row["dog_key"])
        by_class[(row["trial_key"], row["division_key"], row["class_key"])].append(row)
        by_loose[(row["trial_key"], row["division_key"], row["loose_class"])].append(row)
        by_trial_result[(row["trial_key"], row["result_key"])].append(row)
        by_trial_dog[(row["trial_key"], row["dog_compact"])].append(row)

    raw_by_trial: dict[tuple, list | None] = {}
    # Eager-load raw files once (parsing is the expensive part; do it up front)
    print("\nLoading raw trial files for fallback...")
    for year, trial, tk in sorted({(r["year"], r["trial"], r["trial_key"]) for r in source_rows}):
        raw_by_trial[tk] = load_raw_placements(year, trial)

    matches = []
    method_counts = defaultdict(int)
    trial_stats = defaultdict(lambda: defaultdict(int))

    for src in source_rows:
        tk = src["trial_key"]
        dk = normalize_division_name_full(src["division"])
        ck = class_key(src["class_name"], src["division"])
        lk = loose_class_key(src["class_name"], src["division"])
        rk = result_key(src["result"])
        dog = clean_dog(src["dog"])
        trial_label = f"{tk[0]} {tk[1]}"

        chosen = None
        method = None

        # 1) exact normalized division/class
        bucket = list(by_class.get((tk, dk, ck), []))
        if not bucket and "STAKES" in src["division"].upper():
            alt = normalize_division_name_full("THUNDER TUNNEL")
            bucket = list(by_class.get((tk, alt, ck), []))
        chosen, method = choose_from_bucket(bucket, dog, rk)

        # 2) loose class key
        if chosen is None:
            bucket = list(by_loose.get((tk, dk, lk), []))
            if not bucket and "STAKES" in src["division"].upper():
                alt = normalize_division_name_full("THUNDER TUNNEL")
                bucket = list(by_loose.get((tk, alt, lk), []))
            chosen, method = choose_from_bucket(bucket, dog, rk)
            if chosen is not None:
                method = f"loose:{method}"

        # 3) cross-division within trial (handles SUPER EARTH -> GO-TO-GROUND moves)
        if chosen is None:
            chosen, method = best_cross_division_match(
                by_trial_result, by_trial_dog, src, dog, rk
            )

        # 4) raw file bridge for remaining class/division normalization gaps
        if chosen is None:
            chosen, method = raw_file_match(src, dog, rk, raw_by_trial, by_trial_result)

        if chosen is None:
            method_counts["miss"] += 1
            trial_stats[trial_label]["miss"] += 1
            matches.append(
                {**src, "placement_id": None, "method": "miss", "existing_time": None}
            )
            continue

        method_counts[method] += 1
        trial_stats[trial_label]["matched"] += 1
        if chosen["existing_time"] is not None:
            trial_stats[trial_label]["already"] += 1
            method_counts["already"] += 1
        else:
            trial_stats[trial_label]["insert"] += 1

        matches.append(
            {
                **src,
                "placement_id": chosen["placement_id"],
                "method": method,
                "existing_time": chosen["existing_time"],
                "target_division": chosen["division"],
                "target_class": chosen["class_name"],
                "target_dog": chosen["dog_key"],
            }
        )
        chosen["existing_time"] = chosen["existing_time"] or src["time"]

    return matches, method_counts, trial_stats


def insert_times(conn: pyodbc.Connection, matches: list[dict], dry_run: bool) -> dict:
    to_insert = [
        m
        for m in matches
        if m["placement_id"] is not None and m["existing_time"] is None and m["time"]
    ]
    # Deduplicate by placement_id (keep first)
    seen = set()
    unique = []
    for m in to_insert:
        if m["placement_id"] in seen:
            continue
        seen.add(m["placement_id"])
        unique.append(m)

    stats = {"would_insert": len(unique), "inserted": 0}
    if dry_run or not unique:
        return stats

    cur = conn.cursor()
    cur.execute(
        "SELECT ISNULL(MAX(TrialPlacements_TimesID), 0) + 1 FROM [sResults].[TrialPlacements_Times]"
    )
    next_id = int(cur.fetchone()[0])
    for m in unique:
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
            m["placement_id"],
            next_id,
            m["placement_id"],
            m["time"],
        )
        if cur.rowcount:
            stats["inserted"] += 1
            next_id += 1
    conn.commit()
    return stats


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--apply",
        action="store_true",
        help="Write matched times into TrialResults (default is dry-run)",
    )
    parser.add_argument(
        "--show-misses",
        type=int,
        default=25,
        help="How many miss examples to print",
    )
    args = parser.parse_args()
    dry_run = not args.apply

    print("=" * 80)
    print("Migrate TrialData GTGTimes -> TrialResults TrialPlacements_Times")
    print(f"Mode: {'APPLY' if args.apply else 'DRY-RUN'}")
    print("=" * 80)

    src_conn = connect("TrialData")
    source_rows = load_source_rows(src_conn)
    src_conn.close()
    print(f"Source GTG times: {len(source_rows)}")

    years = sorted({r["year"] for r in source_rows})
    tgt_conn = connect("TrialResults")
    target_rows = load_target_rows(tgt_conn, years)
    print(f"Target National placements in years {years}: {len(target_rows)}")

    matches, method_counts, trial_stats = match_all(source_rows, target_rows)

    print("\n=== match methods ===")
    for k, v in sorted(method_counts.items(), key=lambda x: (-x[1], x[0])):
        print(f"  {k}: {v}")

    print("\n=== by year/trial ===")
    migrated_trials = []
    for trial, s in sorted(trial_stats.items()):
        print(f"  {trial}: {dict(s)}")
        if s.get("matched") or s.get("insert") or s.get("already"):
            migrated_trials.append((trial, dict(s)))

    insert_stats = insert_times(tgt_conn, matches, dry_run=dry_run)
    tgt_conn.close()

    print("\n=== write ===")
    if dry_run:
        print(f"  Dry-run: would insert {insert_stats['would_insert']} times")
        print("  Re-run with --apply to write.")
    else:
        print(f"  Inserted {insert_stats['inserted']} times "
              f"(candidates {insert_stats['would_insert']})")

    misses = [m for m in matches if m["method"] == "miss"]
    if misses and args.show_misses:
        print(f"\n=== miss examples ({min(args.show_misses, len(misses))} of {len(misses)}) ===")
        for m in misses[: args.show_misses]:
            print(
                f"  {m['year']} {m['trial']} | {m['division']} | {m['class_name']} | "
                f"{m['result']} | {m['dog']} | time={m['time']}"
            )

    print("\n=== trials with migrated/matched times ===")
    for trial, s in migrated_trials:
        print(
            f"  {trial}: matched={s.get('matched', 0)}, "
            f"insert={s.get('insert', 0)}, already={s.get('already', 0)}, "
            f"miss={s.get('miss', 0)}"
        )


if __name__ == "__main__":
    main()
