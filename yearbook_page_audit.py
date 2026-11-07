#!/usr/bin/env python3
"""Audit printed page numbers at bottom of yearbook OCR; report gaps.

Prefer Updated Yearbook Scans for 1984-1996 (incl. Vol folders);
Yearbook Scans for 1997-2001. No recursive repo search — listdir only.
"""
from __future__ import annotations

import csv
import os
import re
from pathlib import Path

ROOT = Path(r"c:\Users\mw\OneDrive - timberwilde.net\repos\jrtca_results")
UPDATED = ROOT / "Updated Yearbook Scans"
SCANS = ROOT / "Yearbook Scans"
OUT = ROOT / "_yearbook_page_audit.csv"

YEARS = list(range(1984, 2002))
_PAGE_HEADER = re.compile(r"(?im)^---\s*page\s+(\d+)\s*---\s*$")


def folders_for_year(year: int) -> list[Path]:
    """Return preferred OCR folders for a yearbook year."""
    out: list[Path] = []
    if year <= 1996 and UPDATED.is_dir():
        for name in sorted(os.listdir(UPDATED)):
            p = UPDATED / name
            if not p.is_dir():
                continue
            if year in (1984, 1985) and name.startswith("1984"):
                out.append(p)
            elif name == str(year) or name.startswith(f"{year} "):
                out.append(p)
    if year >= 1997 and SCANS.is_dir():
        for name in sorted(os.listdir(SCANS)):
            if "entries catalog" in name.lower():
                continue
            p = SCANS / name
            if not p.is_dir():
                continue
            if name.startswith(str(year)):
                out.append(p)
    # Fallback: Yearbook Scans vols for pre-1997 if Updated missing
    if not out and SCANS.is_dir():
        for name in sorted(os.listdir(SCANS)):
            if "entries catalog" in name.lower():
                continue
            p = SCANS / name
            if p.is_dir() and name.startswith(str(year)):
                out.append(p)
    return out


def best_ocr_text(folder: Path) -> Path | None:
    cands: list[tuple[int, Path]] = []
    try:
        names = os.listdir(folder)
    except OSError:
        return None
    for fn in names:
        low = fn.lower()
        if not low.endswith(".txt"):
            continue
        path = folder / fn
        if "hqmax" in low:
            cands.append((0, path))
        elif "_hq.txt" in low or low.endswith("hq.txt"):
            cands.append((1, path))
        elif "ocr" in low:
            cands.append((2, path))
        else:
            cands.append((5, path))
    if not cands:
        return None
    cands.sort(key=lambda x: (x[0], -x[1].stat().st_size))
    return cands[0][1]


def split_pages(text: str) -> list[tuple[int, str]]:
    marks = list(_PAGE_HEADER.finditer(text))
    if not marks:
        return [(1, text)]
    out = []
    for i, m in enumerate(marks):
        end = marks[i + 1].start() if i + 1 < len(marks) else len(text)
        out.append((int(m.group(1)), text[m.end() : end]))
    return out


def printed_page_number(page_text: str) -> int | None:
    tail = page_text[-500:] if len(page_text) > 500 else page_text
    lines = [ln.strip() for ln in tail.splitlines() if ln.strip()]
    candidates = []
    for ln in lines[-12:]:
        if re.fullmatch(r"\d{1,3}", ln):
            n = int(ln)
            if 1 <= n <= 500:
                candidates.append(n)
        m = re.fullmatch(r"(?:page\s*)?[-–—]?\s*(\d{1,3})\s*[-–—]?", ln, re.I)
        if m:
            n = int(m.group(1))
            if 1 <= n <= 500:
                candidates.append(n)
    return candidates[-1] if candidates else None


def gaps(nums: list[int]) -> list[int]:
    clean = sorted(set(nums))
    if len(clean) < 2:
        return []
    missing = []
    for a, b in zip(clean, clean[1:]):
        if b - a > 1 and b - a < 80:  # ignore huge leaps between volumes
            missing.extend(range(a + 1, b))
    return missing


def main() -> int:
    rows = []
    print(
        "year\tfolder\tocr_file\tocr_pages\tprinted_min\tprinted_max\tmissing_n\tmissing",
        flush=True,
    )
    for year in YEARS:
        folders = folders_for_year(year)
        if not folders:
            rows.append(
                {
                    "Year": year,
                    "Folder": "",
                    "OcrFile": "",
                    "OcrPages": 0,
                    "PrintedMin": "",
                    "PrintedMax": "",
                    "PrintedCount": 0,
                    "MissingCount": 0,
                    "Missing": "NO_FOLDER",
                }
            )
            print(f"{year}\tNO_FOLDER", flush=True)
            continue
        year_printed: list[int] = []
        for folder in folders:
            ocr = best_ocr_text(folder)
            if not ocr:
                rows.append(
                    {
                        "Year": year,
                        "Folder": str(folder.relative_to(ROOT)),
                        "OcrFile": "",
                        "OcrPages": 0,
                        "PrintedMin": "",
                        "PrintedMax": "",
                        "PrintedCount": 0,
                        "MissingCount": 0,
                        "Missing": "NO_OCR",
                    }
                )
                print(f"{year}\t{folder.name}\tNO_OCR", flush=True)
                continue
            text = ocr.read_text(encoding="utf-8", errors="ignore")
            pages = split_pages(text)
            printed = []
            for _idx, body in pages:
                n = printed_page_number(body)
                if n is not None:
                    printed.append(n)
            year_printed.extend(printed)
            miss = gaps(printed)
            pmin = min(printed) if printed else ""
            pmax = max(printed) if printed else ""
            miss_s = ",".join(str(x) for x in miss[:60])
            if len(miss) > 60:
                miss_s += f",...(+{len(miss)-60})"
            rows.append(
                {
                    "Year": year,
                    "Folder": str(folder.relative_to(ROOT)),
                    "OcrFile": ocr.name,
                    "OcrPages": len(pages),
                    "PrintedMin": pmin,
                    "PrintedMax": pmax,
                    "PrintedCount": len(printed),
                    "MissingCount": len(miss),
                    "Missing": miss_s or "",
                }
            )
            print(
                f"{year}\t{folder.name}\t{ocr.name}\t{len(pages)}\t{pmin}\t{pmax}\t{len(miss)}\t{miss_s[:50]}",
                flush=True,
            )
        # Year-level summary across volumes
        if len(folders) > 1 and year_printed:
            miss = gaps(year_printed)
            rows.append(
                {
                    "Year": year,
                    "Folder": "[YEAR_SUMMARY]",
                    "OcrFile": "",
                    "OcrPages": "",
                    "PrintedMin": min(year_printed),
                    "PrintedMax": max(year_printed),
                    "PrintedCount": len(year_printed),
                    "MissingCount": len(miss),
                    "Missing": ",".join(str(x) for x in miss[:80]),
                }
            )

    with OUT.open("w", encoding="utf-8", newline="") as f:
        w = csv.DictWriter(
            f,
            fieldnames=[
                "Year",
                "Folder",
                "OcrFile",
                "OcrPages",
                "PrintedMin",
                "PrintedMax",
                "PrintedCount",
                "MissingCount",
                "Missing",
            ],
        )
        w.writeheader()
        w.writerows(rows)
    print(f"\nWrote {OUT}", flush=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
