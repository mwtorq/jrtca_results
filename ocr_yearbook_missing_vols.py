#!/usr/bin/env python3
"""OCR Updated Yearbook vol PDFs missing hqmax text (initial page-audit gap)."""
from __future__ import annotations

import argparse
from pathlib import Path

from yearbook_ocr import ocr_pdf_hq

ROOT = Path(r"c:\Users\mw\OneDrive - timberwilde.net\repos\jrtca_results")
LIST = ROOT / "_yearbook_ocr_needed.txt"


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--limit", type=int, default=None)
    ap.add_argument("--force", action="store_true")
    args = ap.parse_args()
    paths = [
        Path(ln.strip())
        for ln in LIST.read_text(encoding="utf-8").splitlines()
        if ln.strip()
    ]
    if args.limit:
        paths = paths[: args.limit]
    print(f"ocr_queue={len(paths)}", flush=True)
    ok = fail = skip = 0
    for i, p in enumerate(paths, 1):
        if not p.is_file():
            print(f"MISSING {p}", flush=True)
            fail += 1
            continue
        hq = p.with_name(p.stem + "_ocr_hqmax.txt")
        if hq.is_file() and hq.stat().st_size > 200 and not args.force:
            print(f"SKIP {i}/{len(paths)} {p.relative_to(ROOT)}", flush=True)
            skip += 1
            continue
        print(f"OCR {i}/{len(paths)} {p.relative_to(ROOT)}", flush=True)
        try:
            text, year = ocr_pdf_hq(p, force=True)
            out = p.with_name(p.stem + "_ocr_hqmax.txt")
            out.write_text(text or "", encoding="utf-8")
            print(f"  year={year} chars={len(text or '')} -> {out.name}", flush=True)
            ok += 1
        except Exception as e:
            print(f"  FAIL {e}", flush=True)
            fail += 1
    print(f"DONE ok={ok} skip={skip} fail={fail}", flush=True)
    return 0 if fail == 0 else 1


if __name__ == "__main__":
    raise SystemExit(main())
