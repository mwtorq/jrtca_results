#!/usr/bin/env python3
"""Year completeness + manifest for 1997–2001 remediation pipeline.

Uses the same PDF queue as ``ocr_yearbook_baseline_v2.queue``. Marks A1 complete
when every queued PDF has ``*_ocr_hqmax.txt`` with size > 500.

Writes/updates ``_pipeline_year_manifest.json``.

Usage:
  python -u pipeline_year_status.py
  python -u pipeline_year_status.py --years 1997 1998 1999 2000 2001
"""
from __future__ import annotations

import argparse
import json
from datetime import datetime, timezone
from pathlib import Path

from ocr_yearbook_baseline_v2 import queue

ROOT = Path(r"c:\Users\mw\OneDrive - timberwilde.net\repos\jrtca_results")
MANIFEST = ROOT / "_pipeline_year_manifest.json"
DEFAULT_YEARS = list(range(1997, 2002))
HQ_MIN_BYTES = 500


def _now() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def load_manifest() -> dict:
    if MANIFEST.is_file():
        try:
            return json.loads(MANIFEST.read_text(encoding="utf-8"))
        except Exception:
            pass
    return {"updated": None, "years": {}}


def save_manifest(data: dict) -> None:
    data["updated"] = _now()
    MANIFEST.write_text(json.dumps(data, indent=2) + "\n", encoding="utf-8")


def a1_status_for_year(year: int) -> dict:
    items = queue([year])
    jobs = len(items)
    done_paths: list[str] = []
    missing: list[str] = []
    for _y, pdf, dest in items:
        ok = dest.is_file() and dest.stat().st_size > HQ_MIN_BYTES
        rel = str(pdf.relative_to(ROOT))
        if ok:
            done_paths.append(rel)
        else:
            missing.append(rel)
    complete = jobs > 0 and len(missing) == 0
    return {
        "a1": "done" if complete else ("pending" if jobs else "no_jobs"),
        "a1_jobs": jobs,
        "a1_done": len(done_paths),
        "a1_missing": missing,
        "a1_complete": complete,
    }


def merge_year_entry(existing: dict | None, a1: dict) -> dict:
    base = {
        "a1": "pending",
        "a1_jobs": 0,
        "a1_done": 0,
        "a1_missing": [],
        "a1_complete": False,
        "a2": "pending",
        "a2_pass": 0,
        "a2_warn": 0,
        "a2_fail": 0,
        "a2_unlocked": False,
        "a3": "n/a",
        "a3_fail_vols": [],
        "b6": "pending",
        "b6_sections": 0,
        "c10": "pending",
        "timestamps": {},
    }
    if existing:
        for k, v in existing.items():
            if k.startswith("a1"):
                continue
            base[k] = v
    base.update(a1)
    ts = dict(base.get("timestamps") or {})
    if a1.get("a1_complete") and not (existing or {}).get("a1_complete"):
        ts["a1_done"] = _now()
    elif a1.get("a1_complete") and not ts.get("a1_done"):
        ts["a1_done"] = _now()
    base["timestamps"] = ts
    return base


def refresh_years(years: list[int]) -> dict:
    data = load_manifest()
    ymap: dict = dict(data.get("years") or {})
    for year in years:
        key = str(year)
        a1 = a1_status_for_year(year)
        ymap[key] = merge_year_entry(ymap.get(key), a1)
        print(
            f"y={year} a1={ymap[key]['a1']} "
            f"{ymap[key]['a1_done']}/{ymap[key]['a1_jobs']} "
            f"a2={ymap[key].get('a2')} unlocked={ymap[key].get('a2_unlocked')} "
            f"b6={ymap[key].get('b6')}",
            flush=True,
        )
    data["years"] = ymap
    save_manifest(data)
    print(f"Wrote {MANIFEST}", flush=True)
    return data


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument(
        "--years",
        type=int,
        nargs="*",
        default=DEFAULT_YEARS,
        help="Years to refresh (default 1997-2001)",
    )
    args = ap.parse_args()
    refresh_years(list(args.years))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
