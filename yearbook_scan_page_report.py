#!/usr/bin/env python3
"""Report missing printed pages and two-up (morphed) scan pages that need rescan.

For each PDF under Updated Yearbook Scans (and Yearbook Scans 1997+):
  - Detect per PDF-page whether it is a facing-page spread (two-up)
  - Read printed footer page numbers from OCR when available (incl. LEFT/RIGHT)
  - List gaps in printed page sequences and which PDF pages are two-up

Does not invent content — geometry + OCR footers only.
"""
from __future__ import annotations

import csv
import os
import re
from pathlib import Path

import fitz
from PIL import Image

from ocr_yearbook_source import folder_year_hint
from yearbook_ocr import _two_up_halves, fix_ocr_li_confusion

ROOT = Path(r"c:\Users\mw\OneDrive - timberwilde.net\repos\jrtca_results")
UPDATED = ROOT / "Updated Yearbook Scans"
SCANS = ROOT / "Yearbook Scans"
OUT_CSV = ROOT / "_yearbook_scan_page_report.csv"
OUT_TXT = ROOT / "_yearbook_rescan_needed.txt"

_PAGE_HEADER = re.compile(r"(?im)^---\s*page\s+(\d+)\s*---\s*$")
_SPREAD_LEFT = re.compile(r"(?im)^---\s*spread\s+LEFT\s*---\s*$")
_SPREAD_RIGHT = re.compile(r"(?im)^---\s*spread\s+RIGHT\s*---\s*$")


def iter_pdfs() -> list[tuple[int | None, Path]]:
    out: list[tuple[int | None, Path]] = []
    for root in (UPDATED, SCANS):
        if not root.is_dir():
            continue
        for name in sorted(os.listdir(root)):
            if "entries catalog" in name.lower():
                continue
            d = root / name
            if not d.is_dir():
                continue
            y = folder_year_hint(name)
            if root == SCANS and y is not None and y <= 1996:
                continue
            for fn in sorted(os.listdir(d)):
                if not fn.lower().endswith(".pdf"):
                    continue
                if fn.lower().endswith(".pre_rotate.pdf"):
                    continue
                if re.match(r"scan_\d+\.pdf$", fn, re.I):
                    continue
                out.append((y, d / fn))
    return out


def best_ocr(pdf: Path) -> Path | None:
    for suf in ("_ocr_hqmax.txt", "_ocr_hq.txt", "_ocr.txt"):
        p = pdf.with_name(pdf.stem + suf)
        if p.is_file() and p.stat().st_size > 50:
            return p
    return None


def printed_nums_from_tail(text: str) -> list[int]:
    """Footer-ish integers from end of a leaf/page body."""
    tail = text[-700:] if len(text) > 700 else text
    found: list[int] = []
    for ln in [ln.strip() for ln in tail.splitlines() if ln.strip()][-15:]:
        if re.fullmatch(r"\d{1,3}", ln):
            n = int(ln)
            if 1 <= n <= 500:
                found.append(n)
                continue
        # "1990 JRTCA Yearbook, Vol. I    42"
        m = re.search(r"\b(\d{1,3})\s*$", ln)
        if m and re.search(r"(?i)yearbook|vol\.?|trial|page", ln):
            n = int(m.group(1))
            if 1 <= n <= 500:
                found.append(n)
    return found


def ocr_printed_by_pdf_page(ocr_path: Path) -> dict[int, list[int]]:
    """Map PDF page index (1-based) -> printed page numbers found."""
    text = fix_ocr_li_confusion(ocr_path.read_text(encoding="utf-8", errors="ignore"))
    marks = list(_PAGE_HEADER.finditer(text))
    out: dict[int, list[int]] = {}
    if not marks:
        nums = printed_nums_from_tail(text)
        if nums:
            out[1] = nums
        return out
    for i, m in enumerate(marks):
        end = marks[i + 1].start() if i + 1 < len(marks) else len(text)
        body = text[m.end() : end]
        pdf_page = int(m.group(1))
        nums: list[int] = []
        # Prefer per-leaf footers after two-up split
        left = _SPREAD_LEFT.search(body)
        right = _SPREAD_RIGHT.search(body)
        if left and right:
            left_body = body[left.end() : right.start()]
            right_body = body[right.end() :]
            nums.extend(printed_nums_from_tail(left_body)[-1:])
            nums.extend(printed_nums_from_tail(right_body)[-1:])
        else:
            nums = printed_nums_from_tail(body)
        out[pdf_page] = nums
    return out


def gaps(nums: list[int]) -> list[int]:
    clean = sorted({n for n in nums if 1 <= n <= 500})
    if len(clean) < 2:
        return []
    missing: list[int] = []
    for a, b in zip(clean, clean[1:]):
        if 1 < b - a < 80:
            missing.extend(range(a + 1, b))
    return missing


def analyze_pdf(year: int | None, pdf: Path) -> dict:
    rel = str(pdf.relative_to(ROOT))
    two_up_pages: list[int] = []
    single_pages = 0
    try:
        doc = fitz.open(str(pdf))
    except Exception as e:
        return {
            "Year": year or "",
            "PDF": rel,
            "PdfPages": 0,
            "TwoUpPages": "",
            "TwoUpCount": 0,
            "SingleCount": 0,
            "PrintedNums": "",
            "PrintedMin": "",
            "PrintedMax": "",
            "MissingPrinted": f"OPEN_FAIL:{e}",
            "MissingCount": 0,
            "OcrFile": "",
            "NeedsRescan": "yes-open-fail",
        }
    try:
        for i in range(len(doc)):
            pix = doc[i].get_pixmap(matrix=fitz.Matrix(1.25, 1.25))
            img = Image.frombytes("RGB", (pix.width, pix.height), pix.samples)
            if _two_up_halves(img) is not None:
                two_up_pages.append(i + 1)
            else:
                single_pages += 1
    finally:
        doc.close()

    ocr = best_ocr(pdf)
    printed: list[int] = []
    ocr_name = ""
    if ocr:
        ocr_name = ocr.name
        by = ocr_printed_by_pdf_page(ocr)
        for nums in by.values():
            printed.extend(nums)
    printed_u = sorted(set(printed))
    miss = gaps(printed_u) if printed_u else []

    needs = []
    if two_up_pages:
        needs.append(f"two-up PDF pages {','.join(map(str, two_up_pages))} (rescan as single leaves)")
    if miss:
        needs.append(f"missing printed pages {','.join(map(str, miss))}")
    if not ocr:
        needs.append("NO_OCR yet — printed gaps unknown until OCR finishes")

    return {
        "Year": year or "",
        "PDF": rel,
        "PdfPages": single_pages + len(two_up_pages),
        "TwoUpPages": ",".join(map(str, two_up_pages)),
        "TwoUpCount": len(two_up_pages),
        "SingleCount": single_pages,
        "PrintedNums": ",".join(map(str, printed_u[:80])),
        "PrintedMin": min(printed_u) if printed_u else "",
        "PrintedMax": max(printed_u) if printed_u else "",
        "MissingPrinted": ",".join(map(str, miss[:80])),
        "MissingCount": len(miss),
        "OcrFile": ocr_name,
        "NeedsRescan": "; ".join(needs) if needs else "",
    }


def main() -> int:
    pdfs = iter_pdfs()
    print(f"pdfs={len(pdfs)}", flush=True)
    rows = []
    for y, pdf in pdfs:
        print(f"AUDIT {y} {pdf.relative_to(ROOT)}", flush=True)
        row = analyze_pdf(y, pdf)
        rows.append(row)
        if row["TwoUpCount"] or row["MissingCount"] or not row["OcrFile"]:
            print(
                f"  two_up={row['TwoUpCount']} missing={row['MissingCount']} "
                f"printed={row['PrintedMin']}-{row['PrintedMax']} ocr={row['OcrFile'] or 'NONE'}",
                flush=True,
            )

    fields = list(rows[0].keys()) if rows else []
    with OUT_CSV.open("w", encoding="utf-8", newline="") as f:
        w = csv.DictWriter(f, fieldnames=fields)
        w.writeheader()
        w.writerows(rows)

    # Human rescan list
    lines = [
        "YEARBOOK RESCAN NEEDED",
        "======================",
        "Two-up = facing pages scanned as one image (morphed together) — rescan each leaf separately.",
        "Missing printed = footer page numbers absent from sequence (after OCR).",
        "",
    ]
    for r in rows:
        if not r["NeedsRescan"]:
            continue
        lines.append(f"{r['Year']}  {r['PDF']}")
        lines.append(f"  PDF pages: {r['PdfPages']}  two-up: {r['TwoUpCount']}  singles: {r['SingleCount']}")
        if r["TwoUpPages"]:
            lines.append(f"  Two-up PDF page indexes: {r['TwoUpPages']}")
        if r["PrintedMin"] != "":
            lines.append(
                f"  Printed range seen: {r['PrintedMin']}-{r['PrintedMax']}  "
                f"missing: {r['MissingPrinted'] or '(none in-range)'}"
            )
        else:
            lines.append("  Printed range: unknown (no OCR footers yet)")
        lines.append(f"  Action: {r['NeedsRescan']}")
        lines.append("")
    OUT_TXT.write_text("\n".join(lines) + "\n", encoding="utf-8")
    print(f"Wrote {OUT_CSV}", flush=True)
    print(f"Wrote {OUT_TXT}", flush=True)

    # Short 1990 spotlight
    print("\n=== 1990 spotlight ===", flush=True)
    for r in rows:
        if r["Year"] == 1990 or (isinstance(r["Year"], int) and r["Year"] == 1990):
            print(
                f"  {Path(r['PDF']).parent.name}/{Path(r['PDF']).name}: "
                f"two_up={r['TwoUpCount']}/{r['PdfPages']} missing={r['MissingPrinted'] or '-'}",
                flush=True,
            )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
