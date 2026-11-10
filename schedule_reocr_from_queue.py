#!/usr/bin/env python3
"""Force re-OCR HQ volumes listed in ``_reocr_queue.json``.

Maps each ``*_ocr_hqmax.txt`` back to its source PDF (Yearbook Scans /
Updated Yearbook Scans) via ``ocr_yearbook_baseline_v2.queue``, then runs
``ocr_pdf_hq(..., force=True)`` into the same baseline dest.

Usage:
  python -u schedule_reocr_from_queue.py --years 1997
  python -u schedule_reocr_from_queue.py --years 1997 --limit 2
  python -u schedule_reocr_from_queue.py --dry-run
"""
from __future__ import annotations

import argparse
import json
import os
import sys
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(r"c:\Users\mw\OneDrive - timberwilde.net\repos\jrtca_results")
QUEUE = ROOT / "_reocr_queue.json"
LOG = ROOT / "_reocr_queue_run.log"


def _now() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def log(msg: str) -> None:
    line = f"[{_now()}] {msg}"
    print(line, flush=True)
    with LOG.open("a", encoding="utf-8") as f:
        f.write(line + "\n")


def load_queue() -> list[dict]:
    if not QUEUE.is_file():
        return []
    data = json.loads(QUEUE.read_text(encoding="utf-8"))
    return data if isinstance(data, list) else []


def hq_to_pdf_jobs(years: set[int] | None) -> dict[str, tuple[int, Path, Path]]:
    """Map relative hqmax path -> (year, pdf, dest)."""
    sys.path.insert(0, str(ROOT))
    from ocr_yearbook_baseline_v2 import queue

    year_list = sorted(years) if years else list(range(1984, 2002))
    out: dict[str, tuple[int, Path, Path]] = {}
    for year, pdf, dest in queue(year_list):
        try:
            rel = str(dest.relative_to(ROOT)).replace("\\", "/")
        except ValueError:
            rel = str(dest).replace("\\", "/")
        # also key by basename for looser match
        out[rel] = (year, pdf, dest)
        out[dest.name] = (year, pdf, dest)
    return out


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--years", type=int, nargs="*", default=None)
    ap.add_argument("--limit", type=int, default=None)
    ap.add_argument("--workers", type=int, default=10)
    ap.add_argument("--page-workers", type=int, default=2)
    ap.add_argument("--dry-run", action="store_true")
    args = ap.parse_args()

    years = set(args.years) if args.years else None
    entries = load_queue()
    if years:
        entries = [e for e in entries if e.get("year") in years]
    if not entries:
        log("queue empty — nothing to re-OCR")
        return 0

    jobs = hq_to_pdf_jobs(years)
    os.environ["JRTCA_OCR_WORKERS"] = str(args.workers)
    os.environ["JRTCA_OCR_PAGE_WORKERS"] = str(args.page_workers)

    from yearbook_ocr import ocr_pdf_hq

    ok = fail = skip = 0
    for i, e in enumerate(entries, 1):
        if args.limit is not None and i > args.limit:
            break
        hq = str(e.get("hqmax") or "").replace("\\", "/")
        key = hq if hq in jobs else Path(hq).name
        if key not in jobs:
            log(f"SKIP no PDF map for {hq}")
            skip += 1
            continue
        year, pdf, dest = jobs[key]
        codes = ",".join(e.get("codes") or [])
        log(
            f"REOCR {i}/{len(entries)} y={year} codes={codes} "
            f"{pdf.relative_to(ROOT)} -> {dest.relative_to(ROOT)}"
        )
        if args.dry_run:
            continue
        try:
            text, y = ocr_pdf_hq(pdf, force=True, dest_path=dest)
            log(f"  ok year_guess={y} chars={len(text or '')}")
            ok += 1
        except Exception as ex:
            log(f"  FAIL {ex}")
            fail += 1

    log(f"DONE ok={ok} skip={skip} fail={fail}")
    return 0 if fail == 0 else 1


if __name__ == "__main__":
    raise SystemExit(main())
