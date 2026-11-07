#!/usr/bin/env python3
"""Export yearbook meta + photo index by dog name.

- Board/Committee/StateRep CSVs for work years
- Photo index from jrtcabreeders.com/photos (Yearbook Photos is OneDrive-empty here)
"""
from __future__ import annotations

import csv
import os
import re
from pathlib import Path

import pyodbc

from remount_source_divisions import CONN

ROOT = Path(r"c:\Users\mw\OneDrive - timberwilde.net\repos\jrtca_results")
OUT = ROOT / "_yearbook_export"
PHOTOS_YB = ROOT / "Yearbook Photos"
PHOTOS_WEB = ROOT / "jrtcabreeders.com" / "photos"
YEARS = list(range(1984, 1991))


def export_table(cur, table: str, path: Path) -> int:
    cur.execute(
        f"""
        SELECT * FROM sResults.[{table}]
        WHERE Year BETWEEN ? AND ?
        ORDER BY Year, MemberName
        """,
        YEARS[0],
        YEARS[-1],
    )
    cols = [d[0] for d in cur.description]
    rows = cur.fetchall()
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="") as f:
        w = csv.writer(f)
        w.writerow(cols)
        for r in rows:
            w.writerow(list(r))
    return len(rows)


def dog_key_from_filename(name: str) -> str:
    stem = Path(name).stem
    # Kennel__Dog-Owner / Kennel__DOG__Owner patterns
    stem = stem.replace("__", " ").replace("_", " ").replace("-", " ")
    stem = re.sub(r"\s+", " ", stem).strip()
    return stem


def index_photos(folder: Path, out_csv: Path) -> int:
    if not folder.is_dir():
        out_csv.write_text("path,filename,dog_key\n", encoding="utf-8")
        return 0
    rows = []
    try:
        names = os.listdir(folder)
    except OSError:
        names = []
    for fn in names:
        low = fn.lower()
        if not low.endswith((".jpg", ".jpeg", ".png", ".gif", ".webp", ".tif", ".tiff", ".bmp")):
            continue
        rows.append(
            {
                "path": str((folder / fn).relative_to(ROOT)),
                "filename": fn,
                "dog_key": dog_key_from_filename(fn),
            }
        )
    rows.sort(key=lambda r: r["dog_key"].lower())
    out_csv.parent.mkdir(parents=True, exist_ok=True)
    with out_csv.open("w", encoding="utf-8", newline="") as f:
        w = csv.DictWriter(f, fieldnames=["path", "filename", "dog_key"])
        w.writeheader()
        w.writerows(rows)
    return len(rows)


def main() -> int:
    OUT.mkdir(parents=True, exist_ok=True)
    cn = pyodbc.connect(CONN, timeout=60)
    cur = cn.cursor()
    for t in ("Board", "Committee", "StateRepresentative"):
        n = export_table(cur, t, OUT / f"{t}_1984_1990.csv")
        print(f"{t}: {n} rows -> {OUT / (t + '_1984_1990.csv')}", flush=True)
    cn.close()

    yb_attrs = ""
    try:
        yb_attrs = oct(PHOTOS_YB.stat().st_file_attributes) if PHOTOS_YB.exists() else "missing"
    except Exception as e:
        yb_attrs = str(e)
    print(f"Yearbook Photos exists={PHOTOS_YB.exists()} attrs={yb_attrs}", flush=True)
    n_yb = index_photos(PHOTOS_YB, OUT / "photos_yearbook_index.csv")
    n_web = index_photos(PHOTOS_WEB, OUT / "photos_breeders_web_index.csv")
    print(f"Yearbook Photos images indexed: {n_yb}", flush=True)
    print(f"jrtcabreeders.com/photos indexed: {n_web}", flush=True)
    print(f"Export dir: {OUT}", flush=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
