#!/usr/bin/env python3
"""Build per-page confidence from audit CSV + OCR cache + baseline."""
from __future__ import annotations

import csv
import json
import re
from collections import Counter, defaultdict
from pathlib import Path

ROOT = Path(r"c:\Users\mw\OneDrive - timberwilde.net\repos\jrtca_results")
BASE = ROOT / "_yearbook_vol_present_baseline.json"
CACHE = ROOT / "_yearbook_vol_footer_ocr_cache.json"
AUDIT = ROOT / "_yearbook_vol_collective_audit.csv"
OUT = ROOT / "_yearbook_vol_page_confidence.csv"

YB = re.compile(r"(?is)y[e€]?a?r?b[\w]{0,4}k")

KNOWN = {
    "1990 Yearbook Vol 1": {5, 9, 69},
    "1990 Yearbook Vol 2": {15, 87},
    "1992 Yearbook Vol 2": {101},
}


def score_evidence(
    source: str,
    page: int,
    ocr_tail: str | None = None,
    native_text: str | None = None,
) -> tuple[int, str, str]:
    """Return (score 0-100, grade A/B/C/D/S, reason)."""
    text = (ocr_tail or "") + "\n" + (native_text or "")
    has_yb = bool(YB.search(text))
    near = False
    if page and text:
        if re.search(
            rf"(?is)y[e€]?a?r?b[\w]{{0,4}}k.{{0,60}}?\b{page}\b|\b{page}\b.{{0,40}}?y[e€]?a?r?b[\w]{{0,4}}k",
            text,
        ):
            near = True
        elif re.search(rf"(?is)vol(?:ume)?\.?\s*[IVXLC0-9/|]+\s+{page}\b", text):
            near = True

    src = (source or "").lower()
    if src in ("known_unnumbered", "structural", "section"):
        return 100, "S", "unnumbered-but-present (section/blank)"
    if "native" in src and "hqmax" in src:
        if near or has_yb:
            return 96, "A", "native+OCR agree"
        return 90, "A", "native+OCR"
    if src == "native" or src.startswith("native"):
        if near:
            return 95, "A", "native footer + Yearbook context"
        return 88, "A", "native footer"
    if "hqmax" in src or "ocr" in src:
        if near:
            return 78, "B", "OCR footer + Yearbook context"
        if has_yb:
            return 68, "B", "OCR with Yearbook text"
        return 55, "C", "OCR digit only"
    if src in ("baseline_prior", "prior", "prior-only"):
        return 40, "D", "prior run only — not reconfirmed"
    if src == "filename":
        return 25, "D", "filename heuristic only"
    return 50, "C", f"unspecified source ({source or 'none'})"


def grade_keep(old: dict | None, new: dict) -> dict:
    if old is None:
        return new
    return new if new["confidence"] > old["confidence"] else old


def main() -> int:
    baseline = json.loads(BASE.read_text(encoding="utf-8")) if BASE.exists() else {"folders": {}}
    baseline["folders"] = {
        k: v
        for k, v in baseline.get("folders", {}).items()
        if re.match(r"^\d{4} Yearbook Vol \d$", k)
    }
    cache = json.loads(CACHE.read_text(encoding="utf-8")) if CACHE.exists() else {}
    best: dict[str, dict[int, dict]] = defaultdict(dict)

    if AUDIT.exists():
        with AUDIT.open(encoding="utf-8", newline="") as f:
            for row in csv.DictReader(f):
                folder = row.get("Folder") or ""
                printed = (row.get("Printed") or "").strip()
                if not folder or not printed or printed.startswith("OPEN_FAIL"):
                    continue
                src = row.get("Source") or ""
                pdf = row.get("PDF") or ""
                pno = row.get("PdfPage") or ""
                tails = []
                for li in (0, 1):
                    key = f"{folder}/{pdf}#p{pno}:L{li}"
                    if key in cache and cache[key].get("ocr_tail"):
                        tails.append(cache[key]["ocr_tail"])
                for part in printed.split(","):
                    part = part.strip()
                    if not part.isdigit():
                        continue
                    page = int(part)
                    conf, grade, reason = score_evidence(
                        src, page, ocr_tail="\n".join(tails)
                    )
                    ev = {
                        "page": page,
                        "confidence": conf,
                        "grade": grade,
                        "reason": reason,
                        "source": src,
                        "pdf": pdf,
                        "pdf_page": pno,
                        "two_up": row.get("TwoUp") or "",
                    }
                    best[folder][page] = grade_keep(best[folder].get(page), ev)

    for key, val in cache.items():
        m = re.match(r"^(.+?)/([^/]+)#p(\d+):L(\d+)$", key)
        if not m:
            continue
        folder, pdf, pno, li = m.group(1), m.group(2), m.group(3), m.group(4)
        if not re.match(r"^\d{4} Yearbook Vol \d$", folder):
            continue
        if val.get("section"):
            continue
        nums = val.get("nums") or []
        tail = val.get("ocr_tail") or ""
        for page in nums:
            conf, grade, reason = score_evidence("hqmax_footer", int(page), ocr_tail=tail)
            ev = {
                "page": int(page),
                "confidence": conf,
                "grade": grade,
                "reason": reason,
                "source": "hqmax_footer",
                "pdf": pdf,
                "pdf_page": pno,
                "two_up": "",
            }
            best[folder][int(page)] = grade_keep(best[folder].get(int(page)), ev)

    for folder, meta in baseline.get("folders", {}).items():
        pages = meta.get("page_list") or meta.get("pages") or []
        if isinstance(pages, dict):
            page_list = [int(x) for x in pages.keys()]
        else:
            page_list = [int(x) for x in pages]
        for page in page_list:
            if page not in best[folder]:
                conf, grade, reason = score_evidence("baseline_prior", page)
                best[folder][page] = {
                    "page": page,
                    "confidence": conf,
                    "grade": grade,
                    "reason": reason,
                    "source": "baseline_prior",
                    "pdf": "",
                    "pdf_page": "",
                    "two_up": "",
                }

    for folder, pages in KNOWN.items():
        for page in pages:
            conf, grade, reason = score_evidence("structural", page)
            best[folder][page] = {
                "page": page,
                "confidence": conf,
                "grade": grade,
                "reason": reason,
                "source": "structural",
                "pdf": "",
                "pdf_page": "",
                "two_up": "",
            }

    rows = []
    new_folders = {}
    for folder in sorted(best.keys()):
        by_page = best[folder]
        page_map = {}
        for page in sorted(by_page):
            ev = by_page[page]
            page_map[str(page)] = {
                "confidence": ev["confidence"],
                "grade": ev["grade"],
                "reason": ev["reason"],
                "source": ev["source"],
                "pdf": ev["pdf"],
                "pdf_page": ev["pdf_page"],
            }
            rows.append(
                {
                    "Folder": folder,
                    "Page": page,
                    "Confidence": ev["confidence"],
                    "Grade": ev["grade"],
                    "Reason": ev["reason"],
                    "Source": ev["source"],
                    "PDF": ev["pdf"],
                    "PdfPage": ev["pdf_page"],
                    "TwoUp": ev.get("two_up") or "",
                }
            )
        new_folders[folder] = {
            "count": len(page_map),
            "pages": page_map,
            "page_list": sorted(int(p) for p in page_map),
        }

    payload = {
        "note": (
            "Monotonic present baseline with per-page confidence. "
            "Later runs ONLY search pages still missing. "
            "Never demote/remove a page; only raise confidence when better evidence appears."
        ),
        "grades": {
            "A": "85-100 native footer (or native+OCR)",
            "B": "65-84 OCR with Yearbook/Vol context",
            "C": "50-64 weak OCR digit",
            "D": "25-49 prior-only / weak heuristic",
            "S": "100 structural unnumbered-but-present",
        },
        "folders": new_folders,
    }
    BASE.write_text(json.dumps(payload, indent=2), encoding="utf-8")

    with OUT.open("w", encoding="utf-8", newline="") as f:
        w = csv.DictWriter(
            f,
            fieldnames=[
                "Folder",
                "Page",
                "Confidence",
                "Grade",
                "Reason",
                "Source",
                "PDF",
                "PdfPage",
                "TwoUp",
            ],
        )
        w.writeheader()
        w.writerows(rows)

    g = Counter(r["Grade"] for r in rows)
    print(f"Wrote {OUT} rows={len(rows)}")
    print("Grades:", dict(sorted(g.items())))
    for folder, meta in new_folders.items():
        grades = Counter(v["grade"] for v in meta["pages"].values())
        print(f"  {folder}: {meta['count']} {dict(sorted(grades.items()))}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
