#!/usr/bin/env python3
"""Split multi-trial Yearbook OCR into per-trial text and rematch each TrialList row.

Year from OCR content. Does not invent trials — only remaps existing TrialList IDs.
"""
from __future__ import annotations

import os
import re
from pathlib import Path

import pyodbc

from fill_from_parse import build_catalog_index, process_trial
from ocr_yearbook_source import write_ocr_sibling
from remount_source_divisions import CONN

ROOT = Path(r"c:\Users\mw\OneDrive - timberwilde.net\repos\jrtca_results")

# Multi-trial PDFs → ordered (trial_list_id, header_regex)
SPLITS = [
    {
        "pdf": "Yearbook Scans/2001 Vol II/2001 Paumanok Farmstead Dutchess County.pdf",
        "parts": [
            (301, r"PAUMANOK"),
            (302, r"FARMSTEAD"),
            (303, r"DUTCHESS"),
        ],
    },
    {
        "pdf": "Yearbook Scans/2001 Vol I/2001 Troon Quarry.pdf",
        "parts": [
            (277, r"TROON\s+QUARRY.*\bI\b|TERRIER\s+TRIAL\s+I"),
            (278, r"TROON\s+QUARRY.*\bII\b|TERRIER\s+TRIAL\s+II"),
        ],
    },
    {
        "pdf": "Yearbook Scans/2001 Vol II/2001 Summer Celebration.pdf",
        "parts": [
            (297, r"SUMMER\s+CELEBRATION\s+I\b"),
            (1312, r"SUMMER\s+CELEBRATION\s+II\b"),
        ],
    },
    {
        "pdf": "Yearbook Scans/2001 Vol II/2001 Yankee.pdf",
        "parts": [
            (293, r"YANKEE\s+CHALLENGE"),
            (1314, r"YANKEE\s+CLASSIC"),
        ],
    },
    {
        "pdf": "Yearbook Scans/2001 Vol II/2001 MWJRTC II Wheatland I & II.pdf",
        "parts": [
            (306, r"MWJRTC.*\bII\b|MIDWEST.*\bII\b"),
            (305, r"WHEATLAND.*\bI\b"),
            (307, r"WHEATLAND.*\bII\b"),
        ],
    },
]


def split_text(text: str, parts: list[tuple[int, str]]) -> dict[int, str]:
    """Find earliest header match for each part; slice text between ordered starts."""
    hits = []
    for tid, pat in parts:
        m = re.search(pat, text, re.I)
        if m:
            hits.append((m.start(), tid, m.group(0)))
    if not hits:
        return {}
    hits.sort()
    out = {}
    for i, (start, tid, _lbl) in enumerate(hits):
        end = hits[i + 1][0] if i + 1 < len(hits) else len(text)
        out[tid] = text[start:end]
    return out


def main() -> None:
    cn = pyodbc.connect(CONN, timeout=120)
    cur = cn.cursor()
    catalog_idx, _ = build_catalog_index(cur)
    stats_keys = (
        "insert",
        "remount",
        "ok",
        "skip_nodog",
        "skip_junk",
        "skip_nonplace",
        "skip_2011",
        "skip_nopath",
        "skip_err",
        "new_cumberland",
        "skip_under",
        "catalog_hit",
    )
    totals = {k: 0 for k in stats_keys}

    for spec in SPLITS:
        pdf = ROOT / spec["pdf"].replace("/", os.sep)
        if not pdf.is_file():
            print("MISSING", spec["pdf"])
            continue
        print("OCR", spec["pdf"], flush=True)
        ocr_path, year, text = write_ocr_sibling(str(pdf), max_pages=12)
        print(f"  year={year} chars={len(text)}", flush=True)
        sections = split_text(text, spec["parts"])
        print(f"  sections={list(sections.keys())}", flush=True)
        for tid, body in sections.items():
            out = pdf.with_name(f"{pdf.stem}_tid{tid}_ocr.txt")
            out.write_text(
                f"Source: {pdf.name}\nDerivedYear: {year or 2001}\nTrialListID: {tid}\n\n{body}",
                encoding="utf-8",
            )
            cur.execute(
                "UPDATE sResults.TrialList SET TrialResultFilePath=? WHERE TrialListID=?",
                str(out),
                tid,
            )
            cur.execute(
                "SELECT TrialListID, Year, TrialName, TrialResultFilePath FROM sResults.TrialList WHERE TrialListID=?",
                tid,
            )
            row = cur.fetchone()
            if not row:
                print(f"  no trial {tid}")
                continue
            st = {k: 0 for k in stats_keys}
            process_trial(cur, row[0], row[1], row[2], row[3], True, st, catalog_idx)
            print(f"  fill tid={tid} { {k:st[k] for k in ('insert','remount','ok','skip_err','skip_nodog') if st[k]} }", flush=True)
            for k in totals:
                totals[k] += st[k]
        cn.commit()

    print("COMMITTED", totals, flush=True)
    cn.close()


if __name__ == "__main__":
    main()
