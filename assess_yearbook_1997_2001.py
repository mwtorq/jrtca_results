#!/usr/bin/env python3
"""Quality assessment of 1997-2001 Yearbook Scans volumes (no missing-page hunt)."""
from __future__ import annotations

import csv
import re
from pathlib import Path

import fitz

ROOT = Path(r"c:\Users\mw\OneDrive - timberwilde.net\repos\jrtca_results")
YB = ROOT / "Yearbook Scans"
OUT = ROOT / "_assess_yearbook_1997_2001.txt"
OUT_CSV = ROOT / "_assess_yearbook_1997_2001.csv"

YEARS = range(1997, 2002)


def folder_for(year: int) -> list[Path]:
    hits = []
    if not YB.is_dir():
        return hits
    for p in sorted(YB.iterdir()):
        if not p.is_dir():
            continue
        if re.match(rf"^{year}\b", p.name) or f"{year} " in p.name:
            hits.append(p)
        if p.name.lower().startswith("page redos") or p.name.lower() == "page redos":
            # include redo PDFs for that year
            pass
    # also Page Redos matching year
    redos = YB / "Page Redos"
    if redos.is_dir():
        hits.append(redos)
    return hits


def pdf_stats(pdf: Path) -> dict:
    try:
        doc = fitz.open(str(pdf))
    except Exception as e:
        return {"pages": 0, "error": str(e), "w": 0, "h": 0, "landscape_share": 0}
    pages = len(doc)
    landscape = 0
    w = h = 0
    for i in range(min(pages, 30)):
        r = doc[i].rect
        w, h = r.width, r.height
        if r.width > r.height * 1.05:
            landscape += 1
    sample_n = min(pages, 30)
    doc.close()
    return {
        "pages": pages,
        "error": "",
        "w": round(w),
        "h": round(h),
        "landscape_share": round(landscape / max(1, sample_n), 2),
    }


def ocr_sidecar_quality(pdf: Path) -> dict:
    """Check companion OCR txt quality if present."""
    stem = pdf.with_suffix("")
    candidates = [
        Path(str(stem) + "_ocr_hqmax.txt"),
        Path(str(stem) + "_ocr_hq.txt"),
        Path(str(stem) + "_ocr.txt"),
        pdf.with_suffix(".txt"),
    ]
    # also same-dir loose matches
    for p in pdf.parent.glob(pdf.stem + "*ocr*.txt"):
        candidates.append(p)
    best = None
    for c in candidates:
        if c.is_file() and c.stat().st_size > 200:
            best = c
            break
    if not best:
        return {"ocr_file": "", "ocr_bytes": 0, "owned_by": 0, "place": 0, "garbage": 1.0, "ok": False}
    t = best.read_text(encoding="utf-8", errors="replace")
    owned = len(re.findall(r"(?i)\bowned by\b", t))
    place = len(re.findall(r"(?i)\b(?:1st|2nd|3rd|4th|5th|6th)\b", t))
    gar = len(re.findall(r"[^\x09\x0a\x0d\x20-\x7e]", t)) / max(1, len(t))
    cert = bool(
        re.search(
            r"(?i)natural\s+hunting\s+cert|trial\s+certificates?|bronze\s+medallion",
            t,
        )
    )
    ok = owned >= 5 or place >= 10 or len(t) > 5000
    return {
        "ocr_file": best.name,
        "ocr_bytes": len(t.encode("utf-8", errors="ignore")),
        "owned_by": owned,
        "place": place,
        "garbage": round(gar, 4),
        "has_cert_heading": cert,
        "ok": ok,
    }


def main() -> int:
    rows = []
    lines = [
        "1997-2001 YEARBOOK VOLUME QUALITY ASSESSMENT",
        "============================================",
        "Source: Yearbook Scans\\ (PDFs). Missing-page audit skipped (user: 100% confident complete).",
        "Focus: scan geometry, OCR sidecar presence/quality, cert-section presence.",
        "",
    ]
    for year in YEARS:
        dirs = [
            p
            for p in sorted(YB.iterdir())
            if p.is_dir() and (p.name.startswith(str(year)) or str(year) in p.name[:6])
        ]
        # Page Redos for year
        redos = YB / "Page Redos"
        redo_pdfs = []
        if redos.is_dir():
            redo_pdfs = [
                p
                for p in redos.glob("*.pdf")
                if str(year) in p.name
            ]
        lines.append(f"YEAR {year}")
        lines.append(f"  folders: {', '.join(d.name for d in dirs) or '(none)'}")
        year_pages = 0
        year_pdfs = 0
        ocr_ok = ocr_missing = cert_files = 0
        for d in dirs:
            pdfs = sorted(d.glob("*.pdf"))
            lines.append(f"  [{d.name}] pdfs={len(pdfs)}")
            for pdf in pdfs:
                year_pdfs += 1
                st = pdf_stats(pdf)
                year_pages += st["pages"]
                oq = ocr_sidecar_quality(pdf)
                if oq["ocr_file"]:
                    if oq["ok"]:
                        ocr_ok += 1
                    else:
                        ocr_missing += 1  # weak
                else:
                    ocr_missing += 1
                if oq.get("has_cert_heading"):
                    cert_files += 1
                flag = []
                if st["landscape_share"] >= 0.5:
                    flag.append("LANDSCAPE?")
                if not oq["ocr_file"]:
                    flag.append("NO_OCR")
                elif not oq["ok"]:
                    flag.append("WEAK_OCR")
                if oq.get("has_cert_heading"):
                    flag.append("CERT_SECTION")
                lines.append(
                    f"    {pdf.name}: pages={st['pages']} "
                    f"{st['w']}x{st['h']} land={st['landscape_share']} "
                    f"ocr={oq['ocr_file'] or '-'} owned_by={oq['owned_by']} "
                    f"gar={oq['garbage']} {' '.join(flag)}"
                )
                rows.append(
                    {
                        "Year": year,
                        "Folder": d.name,
                        "PDF": pdf.name,
                        "Pages": st["pages"],
                        "LandscapeShare": st["landscape_share"],
                        "OcrFile": oq["ocr_file"],
                        "OcrBytes": oq["ocr_bytes"],
                        "OwnedBy": oq["owned_by"],
                        "Garbage": oq["garbage"],
                        "HasCertHeading": oq.get("has_cert_heading") or False,
                        "Flags": " ".join(flag),
                    }
                )
        if redo_pdfs:
            lines.append(f"  [Page Redos] matching {year}: {len(redo_pdfs)}")
            for pdf in redo_pdfs:
                st = pdf_stats(pdf)
                lines.append(f"    {pdf.name}: pages={st['pages']}")
        # Also note pre-extracted trial txt quality in year folder
        ydir = ROOT / str(year)
        txts = list(ydir.glob("*.txt")) if ydir.is_dir() else []
        lines.append(
            f"  SUMMARY pdfs={year_pdfs} pages~{year_pages} "
            f"ocr_okish={ocr_ok} need_ocr_or_weak={ocr_missing} "
            f"cert_heading_in_ocr={cert_files}"
        )
        lines.append(
            f"  Pre-extracted trial .txt in /{year}/: {len(txts)} files "
            f"(separate from yearbook PDF OCR)"
        )
        lines.append("")

    OUT.write_text("\n".join(lines) + "\n", encoding="utf-8")
    with OUT_CSV.open("w", encoding="utf-8", newline="") as f:
        w = csv.DictWriter(
            f,
            fieldnames=[
                "Year",
                "Folder",
                "PDF",
                "Pages",
                "LandscapeShare",
                "OcrFile",
                "OcrBytes",
                "OwnedBy",
                "Garbage",
                "HasCertHeading",
                "Flags",
            ],
        )
        w.writeheader()
        w.writerows(rows)
    print(OUT.read_text(encoding="utf-8"))
    print(f"Wrote {OUT}")
    print(f"Wrote {OUT_CSV}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
