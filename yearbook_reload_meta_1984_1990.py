#!/usr/bin/env python3
"""Clear Board/Committee/StateRepresentative and reload from Updated Yearbook Scans 1984-1990.

Prefer reoriented PDFs; OCR all pages (not just first 2). Year from content.
"""
from __future__ import annotations

import os
import sys
from pathlib import Path

import pyodbc

from ocr_yearbook_source import write_ocr_sibling, derive_year_from_text
from remount_source_divisions import CONN
from yearbook_meta_ingest import parse_meta_text, apply_bundle
from yearbook_meta_schema import ensure

ROOT = Path(r"c:\Users\mw\OneDrive - timberwilde.net\repos\jrtca_results")
UPDATED = ROOT / "Updated Yearbook Scans"

# Folders that hold early BOD/committee/state-rep yearbook pages
EARLY_FOLDERS = [
    "1984 & 1985",
    "1986",
    "1987",
    "1988",
    "1989",
    "1990",
]


def clear_meta(cur) -> None:
    for t in ("Board", "Committee", "StateRepresentative"):
        cur.execute(f"DELETE FROM sResults.[{t}]")
        print(f"cleared {t} rowcount={cur.rowcount}", flush=True)


def pdfs_in_early() -> list[Path]:
    out = []
    for folder in EARLY_FOLDERS:
        d = UPDATED / folder
        if not d.is_dir():
            continue
        for fn in sorted(os.listdir(d)):
            if not fn.lower().endswith(".pdf"):
                continue
            if fn.endswith(".pre_rotate.pdf"):
                continue
            out.append(d / fn)
    return out


def main() -> int:
    apply = "--apply" in sys.argv
    cn = pyodbc.connect(CONN, timeout=120, autocommit=False)
    cur = cn.cursor()
    cur.execute("SET LOCK_TIMEOUT 30000")
    ensure(cur)

    if apply:
        clear_meta(cur)
        cn.commit()
    else:
        print("DRY-RUN (pass --apply to clear+reload)", flush=True)

    totals = {
        "board": 0,
        "committee": 0,
        "state_rep": 0,
        "owner_aug": 0,
        "files": 0,
        "skip_noyear": 0,
    }
    pdfs = pdfs_in_early()
    print(f"pdfs={len(pdfs)}", flush=True)
    for path in pdfs:
        rel = path.relative_to(ROOT)
        print(f"OCR {rel}", flush=True)
        try:
            ocr_path, year, text = write_ocr_sibling(str(path), force=True, max_pages=None)
        except Exception as e:
            print(f"  ERR OCR {e}", flush=True)
            continue
        if not year:
            year = derive_year_from_text(text)
        bundle = parse_meta_text(text, str(rel))
        if not bundle.year and year:
            bundle.year = year
        st = apply_bundle(cur, bundle, apply=apply)
        totals["files"] += 1
        for k in ("board", "committee", "state_rep", "owner_aug", "skip_noyear"):
            totals[k] += st.get(k, 0)
        print(
            f"  year={bundle.year} board={st.get('board',0)} committee={st.get('committee',0)} "
            f"state_rep={st.get('state_rep',0)} owner_aug={st.get('owner_aug',0)}",
            flush=True,
        )
        if apply:
            cn.commit()

    if apply:
        cn.commit()
        print("COMMITTED", totals, flush=True)
    else:
        cn.rollback()
        print("DRY-RUN", totals, flush=True)

    # final counts
    for t in ("Board", "Committee", "StateRepresentative"):
        cur.execute(f"SELECT COUNT(*), MIN(Year), MAX(Year) FROM sResults.[{t}]")
        print(t, cur.fetchone(), flush=True)
    cn.close()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
