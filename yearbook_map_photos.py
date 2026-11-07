#!/usr/bin/env python3
"""Map Yearbook Photos OCR onto TrialList rows and rematch placements.

Year and trial identity come from OCR content, not folder names.
"""
from __future__ import annotations

import os
import re
from collections import defaultdict
from pathlib import Path

import pyodbc

from fill_from_parse import build_catalog_index, process_trial
from ocr_yearbook_source import derive_year_from_text, write_ocr_sibling
from remount_source_divisions import CONN

ROOT = Path(r"c:\Users\mw\OneDrive - timberwilde.net\repos\jrtca_results")
PHOTOS = ROOT / "Yearbook Photos"
OUT_DIR = ROOT / "Yearbook Photos" / "_mapped_ocr"

# Content patterns → logical trial key (year filled later from DerivedYear/content)
RULES = [
    # (key_suffix, regex) — key is f"{year}:{suffix}"
    ("national", re.compile(r"JRTCA\s+19\d{2}\s+NATIONAL|J\.?R\.?T\.?C\.?A\.?\s+NATIONAL\s+TRIAL|19\d{2}\s+JRTCA\s+National", re.I)),
    ("old_north_bridge", re.compile(r"OLD\s+NORTH\s+BRIDGE", re.I)),
    ("frederick_pony", re.compile(r"FREDERICK\s+PONY\s+CLUB", re.I)),
    ("windy_hill", re.compile(r"WINDY\s+HILL\s+TERRIER\s+TRIAL", re.I)),
    ("litchfield", re.compile(r"LITCHFIELD\s+COUNTY\s+HOUNDS", re.I)),
    ("saratoga", re.compile(r"SARATOGA\s+(JRT|TERRIER)\s+TRIAL", re.I)),
    ("genessee", re.compile(r"GENESSEE\s+VALLEY", re.I)),
    ("south_coast", re.compile(r"SOUTH\s+COAST\s+JRT\s+TRIAL", re.I)),
]

# Existing / to-create TrialList targets by (year, suffix)
# create=True → insert shell if missing
TARGETS = {
    # year-specific nationals use shells we already created where possible
    "national": {
        # year -> preferred existing name pattern; create if absent
        "create_name": "{year} JRTCA National Trial",
    },
    "old_north_bridge": {"create_name": "{year} Old North Bridge Hounds Terrier Trial"},
    "frederick_pony": {"create_name": "{year} Frederick Pony Club JRT Trial"},
    "windy_hill": {"create_name": "{year} Windy Hill Terrier Trial"},
    "litchfield": {"create_name": "{year} Litchfield County Hounds Terrier Trial"},
    "saratoga": {"create_name": "{year} Saratoga JRT Trial"},
    "genessee": {"create_name": "{year} Genessee Valley Terrier Trial"},
    "south_coast": {"create_name": "{year} South Coast JRT Trial"},
}

SKIP_IF = re.compile(
    r"BOARD\s+OF\s+DIRECTORS|BOARD\s+MEMBERS\s+&\s+COMMITTEES|"
    r"TRIAL\s+CERTIFICATES|SANCTIONED\s+TRIAL\s+OR\s+SHOW|"
    r"BREEDER\s+DIRECTORY|DISPLAY\s+ADS|LETTERS\s+TO\s+THE\s+EDITOR",
    re.I,
)


def ensure_ocr(path: Path) -> Path:
    if path.suffix.lower() == ".txt" and path.name.lower().endswith("_ocr.txt"):
        return path
    out, _, _ = write_ocr_sibling(str(path))
    return Path(out)


def read_ocr(path: Path) -> tuple[int | None, str]:
    text = path.read_text(encoding="utf-8", errors="ignore")
    m = re.search(r"DerivedYear:\s*(\d{4})", text)
    year = int(m.group(1)) if m else derive_year_from_text(text)
    return year, text


def classify(text: str, year: int | None) -> list[str]:
    """Return list of 'year:suffix' keys this page belongs to."""
    # Skip pure meta/instruction pages unless they also clearly name a results trial
    head = text[:1200]
    if SKIP_IF.search(head) and not re.search(r"NATIONAL\s+TRIAL|1st:|1st\b.*owned", head, re.I):
        # allow national results pages that mention board elsewhere
        if not re.search(r"NATIONAL\s+TRIAL|DIVISION\s+[A-D]\s*[-–].*RACING|DIVISION\s+[A-D].*CONFORMATION", text[:2000], re.I):
            return []
    keys = []
    for suffix, rx in RULES:
        if rx.search(text):
            y = year
            if suffix == "national":
                # prefer year in "JRTCA 1988 NATIONAL" / "1989 National"
                ym = re.search(r"JRTCA\s+(19\d{2})\s+NATIONAL|(19\d{2})\s+JRTCA\s+National|NATIONAL\s+TRIAL[^\n]{0,40}(19\d{2})", text, re.I)
                if ym:
                    y = int(next(g for g in ym.groups() if g))
            if y and 1983 <= y <= 1995:
                keys.append(f"{y}:{suffix}")
    return keys


def find_or_create_trial(cur, year: int, suffix: str, next_tid: list[int]) -> int | None:
    name_tmpl = TARGETS[suffix]["create_name"]
    want = name_tmpl.format(year=year)
    # match existing
    if suffix == "national":
        cur.execute(
            """
            SELECT TrialListID, TrialName FROM sResults.TrialList
            WHERE Year=? AND TrialName LIKE '%National%' AND (TrialName LIKE '%JRTCA%' OR TrialName NOT LIKE '%JRTCC%')
            """,
            year,
        )
    else:
        # token match on distinctive words
        token = {
            "old_north_bridge": "%North Bridge%",
            "frederick_pony": "%Frederick%Pony%",
            "windy_hill": "%Windy Hill%",
            "litchfield": "%Litchfield%",
            "saratoga": "%Saratoga%",
            "genessee": "%Genessee%",
            "south_coast": "%South Coast%",
        }[suffix]
        cur.execute(
            "SELECT TrialListID, TrialName FROM sResults.TrialList WHERE Year=? AND TrialName LIKE ?",
            year,
            token,
        )
    rows = cur.fetchall()
    if rows:
        return int(rows[0][0])
    # create shell
    tid = next_tid[0]
    next_tid[0] += 1
    start = f"{year}-01-01"
    cur.execute(
        """
        INSERT INTO sResults.TrialList
        (TrialListID, Year, TrialName, StartDate, EndDate, TrialResultFilePath, CreateUser)
        VALUES (?,?,?,?,?,?,?)
        """,
        tid,
        year,
        want,
        start,
        start,
        None,
        "yearbook_photo_map",
    )
    print(f"  CREATED tid={tid} {want}", flush=True)
    return tid


def main() -> None:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    # Ensure OCR siblings for all JPGs (reuse existing)
    jpg_paths = []
    for dp, _, fns in os.walk(PHOTOS):
        if "_mapped_ocr" in dp:
            continue
        for fn in fns:
            if fn.lower().endswith((".jpg", ".jpeg", ".png")):
                jpg_paths.append(Path(dp) / fn)

    buckets: dict[str, list[tuple[Path, str]]] = defaultdict(list)
    for jp in sorted(jpg_paths):
        ocr = ensure_ocr(jp)
        year, text = read_ocr(ocr)
        keys = classify(text, year)
        for k in keys:
            buckets[k].append((ocr, text))

    print("mapped buckets:", {k: len(v) for k, v in sorted(buckets.items())}, flush=True)

    cn = pyodbc.connect(CONN, timeout=120)
    cur = cn.cursor()
    cur.execute("SET LOCK_TIMEOUT 20000")
    cur.execute("SELECT ISNULL(MAX(TrialListID),0)+1 FROM sResults.TrialList")
    next_tid = [int(cur.fetchone()[0])]

    catalog_idx, _ = build_catalog_index(cur)
    stats_keys = (
        "insert", "remount", "ok", "skip_nodog", "skip_junk", "skip_nonplace",
        "skip_2011", "skip_nopath", "skip_err", "new_cumberland", "skip_under", "catalog_hit",
    )
    totals = {k: 0 for k in stats_keys}

    for key in sorted(buckets):
        year_s, suffix = key.split(":", 1)
        year = int(year_s)
        pages = buckets[key]
        # dedupe by path, preserve order
        seen = set()
        uniq = []
        for p, t in pages:
            if str(p) in seen:
                continue
            seen.add(str(p))
            uniq.append((p, t))
        combined = f"Source: Yearbook Photos mapped {key}\nDerivedYear: {year}\n\n"
        combined += "\n\n".join(
            f"--- {p.name} ---\n{t}" for p, t in uniq
        )
        out = OUT_DIR / f"{year}_{suffix}_combined_ocr.txt"
        out.write_text(combined, encoding="utf-8")

        tid = find_or_create_trial(cur, year, suffix, next_tid)
        if not tid:
            print(f"SKIP no trial for {key}")
            continue
        cur.execute(
            "UPDATE sResults.TrialList SET TrialResultFilePath=? WHERE TrialListID=?",
            str(out),
            tid,
        )
        # quality: parse count
        from populate_trialresults_fixed import parse_trial_source_file

        info, placements, err = parse_trial_source_file(str(out), year, quiet=True)
        n = len(placements or [])
        ok_dogs = sum(1 for p in (placements or []) if p.dog_name and len(p.dog_name) >= 3)
        print(f"{key} tid={tid} pages={len(uniq)} parse={n} ok_dogs={ok_dogs} err={err}", flush=True)
        if ok_dogs < 8:
            print(f"  quality FAIL — path set, skip fill", flush=True)
            continue
        st = {k: 0 for k in stats_keys}
        cur.execute(
            "SELECT TrialListID, Year, TrialName, TrialResultFilePath FROM sResults.TrialList WHERE TrialListID=?",
            tid,
        )
        row = cur.fetchone()
        process_trial(cur, row[0], row[1], row[2], row[3], True, st, catalog_idx)
        print(f"  fill { {k: st[k] for k in ('insert','remount','ok','skip_nodog','skip_err') if st[k]} }", flush=True)
        for k in totals:
            totals[k] += st[k]
        cn.commit()

    cn.commit()
    print("COMMITTED", totals, flush=True)
    cn.close()


if __name__ == "__main__":
    main()
