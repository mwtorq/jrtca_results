#!/usr/bin/env python3
"""Per-folder printed-page audit for 1990-1996 Yearbook Vol folders.

Each Vol folder audited alone. Scan order is NON-CONTIGUOUS (front→end, then
back→start), so missing pages = gaps in the SET of footer numbers found — never
sequence interpolation between adjacent PDF leaves.

Two-up spreads often carry TWO yearbook footers in one PDF page; we collect ALL.
"""
from __future__ import annotations

import csv
import json
import os
import re
import time
from pathlib import Path

import fitz

from ocr_yearbook_source import configure_tesseract, render_pdf_pages
from yearbook_ocr import (
    _preprocess_variants,
    _tesseract_string,
    _two_up_halves,
    fix_ocr_li_confusion,
)

ROOT = Path(r"c:\Users\mw\OneDrive - timberwilde.net\repos\jrtca_results")
UPDATED = ROOT / "Updated Yearbook Scans"
OUT_CSV = ROOT / "_yearbook_vol_collective_audit.csv"
OUT_TXT = ROOT / "_yearbook_vol_rescan_needed.txt"
OUT_SUM = ROOT / "_yearbook_vol_collective_summary.csv"
OUT_CONF = ROOT / "_yearbook_vol_page_confidence.csv"
CACHE = ROOT / "_yearbook_vol_footer_ocr_cache.json"
BASELINE = ROOT / "_yearbook_vol_present_baseline.json"
# After a baseline exists, only hunt pages still missing (skip folders with no gaps).
MISSING_ONLY = os.environ.get("MISSING_ONLY", "1").strip() not in {"0", "false", "no"}

YEARS = range(1990, 1997)
# Optional: set ONLY_FOLDERS=comma-separated folder names to re-audit a subset
ONLY_FOLDERS = {
    x.strip()
    for x in __import__("os").environ.get("ONLY_FOLDERS", "").split(",")
    if x.strip()
}

# Present leaves with no printed footer (not missing scans).
# Includes user-confirmed blank page-number leaves (2026-11-05).
KNOWN_UNNUMBERED = {
    "1990 Yearbook Vol 1": {5, 9, 69},  # section headers (also auto-detected)
    "1990 Yearbook Vol 2": {15, 87},  # blank page numbers (present)
    "1991 Yearbook Vol 1": {11, 15, 87},
    "1991 Yearbook Vol 2": {13, 19, 89},
    "1992 Yearbook Vol 1": {15, 103},
    "1992 Yearbook Vol 2": {11, 101},  # 101 prior; 11 blank
    "1993 Yearbook Vol 1": {5, 11, 145},
    "1993 Yearbook Vol 2": {5, 15, 133},
    "1994 Yearbook Vol 1": {11},
    "1994 Yearbook Vol 2": {5, 13, 141},
    "1995 Yearbook Vol 1": {161},
    "1995 Yearbook Vol 2": {7, 15, 201},
    "1996 Yearbook Vol 1": {7, 13, 179},
    "1996 Yearbook Vol 2": {13, 221},
}

SECTION_TITLE_RX = re.compile(
    r"(?is)\b(?:"
    r"(?:19\d{2}\s+)?sanctioned\s+trial\s+results|"
    r"natural\s+hunting(?:\s*[&and]+\s*trial\s+certificates)?|"
    r"conformation\s+division\s+photos|"
    r"trial\s+certificates"
    r")\b"
)


def _force_halves(img):
    """1990 Vol1: if gutter detect fails, still split wide spreads at mid."""
    halves = _two_up_halves(img)
    if halves:
        return halves
    w, h = img.size
    if w >= int(h * 1.12):
        mid = w // 2
        return [img.crop((0, 0, mid, h)), img.crop((mid, 0, w, h))]
    return None


def is_section_header_leaf(leaf) -> str | None:
    """Section divider pages: big centered title, no real footer page number.

    Layout: framed/centered titles like
      - CONFORMATION DIVISION PHOTOS
      - 1990 SANCTIONED TRIAL RESULTS
      - NATURAL HUNTING & TRIAL CERTIFICATES
    These occupy a page number in sequence but have no footer integer.
    """
    try:
        from yearbook_ocr import _preprocess_variants, _tesseract_string
    except Exception:
        return None
    w, h = leaf.size
    # Title lives in upper half; avoid photo captions at bottom
    body = leaf.crop((int(w * 0.06), int(h * 0.04), int(w * 0.94), int(h * 0.58)))
    try:
        mid = next(im for name, im in _preprocess_variants(body) if name == "mid")
        text = (_tesseract_string(mid, 6) or "") + "\n" + (_tesseract_string(mid, 4) or "")
    except Exception:
        return None
    text = fix_ocr_li_confusion(text)
    m = SECTION_TITLE_RX.search(text)
    if not m:
        return None
    lines = [ln.strip() for ln in text.splitlines() if ln.strip()]
    # Content pages with these phrases are long; dividers are short title blocks
    if len(lines) > 18:
        return None
    label = re.sub(r"\s+", " ", m.group(0)).strip().title()
    return label



def vol_folders(year: int) -> list[Path]:
    out = []
    if not UPDATED.is_dir():
        return out
    for name in sorted(os.listdir(UPDATED)):
        if not name.startswith(f"{year} "):
            continue
        p = UPDATED / name
        if p.is_dir() and "vol" in name.lower():
            out.append(p)
    return out



_PG_FILE = re.compile(r"(?i)\bpg[\s._-]*(\d{1,3})\b")
_PAGE_FILE = re.compile(r"(?i)\bpage[\s._-]*(\d{1,3})\b")
# Multi: "pg 65, 71, 73" / "pg 92-93" / "pg 68 & 70"
_PG_MULTI = re.compile(
    r"(?i)^(?:pg|page)\s*([\d\s,;&\-–—]+)$"
)


def page_num_from_filename(pdf: Path) -> list[int]:
    """Rescan PDFs named 'pg 108.pdf' / 'pg 65, 71, 73.pdf' / 'pg 92-93.pdf'."""
    stem = pdf.stem.strip()
    m = _PG_MULTI.match(stem)
    if m:
        chunk = m.group(1)
        nums: list[int] = []
        # ranges first
        for a, b in re.findall(r"(\d{1,3})\s*[-–—]\s*(\d{1,3})", chunk):
            lo, hi = int(a), int(b)
            if 1 <= lo <= hi <= 400 and hi - lo <= 20:
                nums.extend(range(lo, hi + 1))
        # remaining singles
        for n in re.findall(r"\d{1,3}", chunk):
            v = int(n)
            if 1 <= v <= 400 and v not in nums:
                nums.append(v)
        return nums
    for rx in (_PG_FILE, _PAGE_FILE):
        m = rx.search(stem)
        if m:
            n = int(m.group(1))
            if 1 <= n <= 400:
                return [n]
    return []


def pdfs_in(folder: Path) -> list[Path]:
    out = []
    for fn in sorted(os.listdir(folder)):
        if not fn.lower().endswith(".pdf"):
            continue
        if fn.lower().endswith(".pre_rotate.pdf"):
            continue
        out.append(folder / fn)
    return out


def load_cache() -> dict:
    if CACHE.is_file():
        try:
            return json.loads(CACHE.read_text(encoding="utf-8"))
        except Exception:
            return {}
    return {}


def save_cache(cache: dict) -> None:
    CACHE.write_text(json.dumps(cache, indent=0, sort_keys=True), encoding="utf-8")


def parse_footer_nums(text: str, expect_two: bool = False) -> list[int]:
    """ALL yearbook footer page numbers on a page (1 or 2 for two-up).

    Native OCR often garbles Yearbook (Yearbodk, Yeartook, …). Match fuzzily.
    Never treat 'Vol 1' as the page number. Never harvest 'Entries: N'.
    """
    text = fix_ocr_li_confusion(text or "")
    if not text.strip():
        return []
    # Fuzzy: Yearb…k (Yearbook / Yearbodk / Yearbcxk / …)
    yb = r"y[e€]?a?r?b[\w]{0,4}k"
    lines = [ln.strip() for ln in text.splitlines() if ln.strip()]
    hits: list[int] = []

    for i, ln in enumerate(lines):
        if not re.search(rf"(?i){yb}", ln):
            continue
        year_here = re.search(r"(?:19\d{2}|20\d{2})", ln)
        year_prev = i > 0 and re.search(r"(?:19\d{2}|20\d{2})", lines[i - 1])
        has_vol = re.search(r"(?i)\bvol(?:ume)?\b", ln)
        if not year_here and not year_prev and not has_vol:
            continue

        stripped = re.sub(r"(?i),?\s*vol(?:ume)?\.?\s*[IVXLC0-9/|]+", "", ln)
        m = re.search(rf"(?i){yb}\s*[,.]?\s*(\d{{1,3}})\s*$", stripped)
        if m:
            n = int(m.group(1))
            if 1 <= n <= 400:
                hits.append(n)
            continue

        for j in range(i + 1, min(i + 3, len(lines))):
            nxt = lines[j]
            if re.search(r"(?i)^volume\b", nxt):
                break
            if re.fullmatch(r"\d{1,3}", nxt):
                n = int(nxt)
                if 1 <= n <= 400:
                    hits.append(n)
                break
            m2 = re.match(r"^(\d{1,3})(?:\s+|$)", nxt)
            if m2:
                n = int(m2.group(1))
                if 1 <= n <= 400:
                    hits.append(n)
                break
            break

    # "…Yearbodk, Vol. I 44" same-line after vol
    for m in re.finditer(
        rf"(?i){yb}\s*,?\s*vol(?:ume)?\.?\s*[IVXLC0-9/|]+\s+(\d{{1,3}})\b",
        text,
    ):
        n = int(m.group(1))
        if 1 <= n <= 400:
            hits.append(n)


    seen = set()
    ordered = []
    for n in hits:
        if n not in seen:
            seen.add(n)
            ordered.append(n)
    return ordered



def ocr_footer_max(leaf) -> str:
    import pytesseract

    w, h = leaf.size
    strip = leaf.crop((0, max(0, int(h * 0.86)), w, h))
    strip_tight = leaf.crop((0, max(0, int(h * 0.92)), w, h))
    candidates: list[str] = []
    for crop in (strip, strip_tight):
        for name, im in _preprocess_variants(crop):
            psms = (4, 6, 7, 11, 13) if name != "bin" else (6, 7, 13)
            for psm in psms:
                try:
                    t = _tesseract_string(im, psm)
                    if t and t.strip():
                        candidates.append(t)
                except Exception:
                    continue
            for psm in (7, 13):
                try:
                    cfg = (
                        f"--oem 3 --psm {psm} "
                        "-c tessedit_char_whitelist=0123456789 "
                        "-c preserve_interword_spaces=1"
                    )
                    t = pytesseract.image_to_string(im, config=cfg) or ""
                    if t.strip():
                        candidates.append("1990 JRTCA Yearbook\n" + t.strip())
                except Exception:
                    continue
    uniq, seen = [], set()
    for t in candidates:
        hsh = re.sub(r"\s+", " ", t).strip()[:400]
        if hsh and hsh not in seen:
            seen.add(hsh)
            uniq.append(t)
    return fix_ocr_li_confusion("\n".join(uniq))


def vote_nums(texts: list[str]) -> list[int]:
    """Rank footer candidates; yearbook+vol adjacency beats stray digits (7, 3, …)."""
    from collections import Counter

    yb = r"y[e€]?a?r?b[\w]{0,4}k"
    c: Counter[int] = Counter()
    for text in texts:
        if not text:
            continue
        for n in parse_footer_nums(text):
            c[n] += 1
        # Strong bonus: explicit Yearbook/Vol … N
        for m in re.finditer(
            rf"(?i){yb}.{{0,50}}?vol(?:ume)?\.?\s*[IVXLC0-9/|]+.{{0,40}}?\b(\d{{1,3}})\b",
            text,
        ):
            n = int(m.group(1))
            if 1 <= n <= 400:
                c[n] += 5
        for m in re.finditer(
            rf"(?i){yb}[^\n]{{0,60}}?\b(\d{{1,3}})\b[^\n]{{0,40}}(?:trial|photo|result|volume)",
            text,
        ):
            n = int(m.group(1))
            if 1 <= n <= 400:
                c[n] += 4
    if not c:
        return []
    ranked = c.most_common()
    # Prefer real footer magnitudes: if any n>=10 scored well, drop 1-9 noise
    strong = [(n, k) for n, k in ranked if n >= 10]
    if strong and strong[0][1] >= 2:
        ranked = [(n, k) for n, k in ranked if n >= 10 or k >= strong[0][1]]
        if not ranked:
            ranked = strong
    return [n for n, _ in ranked]


def gaps_in_set(nums: set[int]) -> list[int]:
    clean = sorted(nums)
    if len(clean) < 2:
        return []
    missing = []
    for a, b in zip(clean, clean[1:]):
        if 1 < b - a < 120:
            missing.extend(range(a + 1, b))
    return missing


def score_evidence(
    source: str,
    page: int,
    ocr_tail: str | None = None,
) -> tuple[int, str, str]:
    """Per-found-page confidence: score 0-100, grade A/B/C/D/S, reason."""
    text = ocr_tail or ""
    has_yb = bool(re.search(r"(?is)y[e€]?a?r?b[\w]{0,4}k", text))
    near = False
    if page and text:
        if re.search(
            rf"(?is)y[e€]?a?r?b[\w]{{0,4}}k.{{0,60}}?\b{page}\b|"
            rf"\b{page}\b.{{0,40}}?y[e€]?a?r?b[\w]{{0,4}}k",
            text,
        ):
            near = True
        elif re.search(rf"(?is)vol(?:ume)?\.?\s*[IVXLC0-9/|]+\s+{page}\b", text):
            near = True
    src = (source or "").lower()
    if src in ("known_unnumbered", "structural", "section"):
        return 100, "S", "unnumbered-but-present (section/blank)"
    if "native" in src and "hqmax" in src:
        return (96, "A", "native+OCR agree") if (near or has_yb) else (90, "A", "native+OCR")
    if src == "native" or src.startswith("native"):
        return (95, "A", "native footer + Yearbook context") if near else (88, "A", "native footer")
    if "hqmax" in src or "ocr" in src:
        if near:
            return 78, "B", "OCR footer + Yearbook context"
        if has_yb:
            return 68, "B", "OCR with Yearbook text"
        return 55, "C", "OCR digit only"
    if src in ("baseline_prior", "prior", "prior-only"):
        return 40, "D", "prior run only — not reconfirmed"
    return 50, "C", f"unspecified source ({source or 'none'})"


def load_baseline() -> dict:
    if not BASELINE.exists():
        return {"folders": {}}
    try:
        data = json.loads(BASELINE.read_text(encoding="utf-8"))
    except Exception:
        return {"folders": {}}
    folders = {}
    for name, meta in (data.get("folders") or {}).items():
        if not re.match(r"^\d{4} Yearbook Vol \d$", name):
            continue
        pages = meta.get("pages") or {}
        if isinstance(pages, list):
            page_map = {
                str(p): {
                    "confidence": 40,
                    "grade": "D",
                    "reason": "prior run only — not reconfirmed",
                    "source": "baseline_prior",
                    "pdf": "",
                    "pdf_page": "",
                }
                for p in pages
            }
            page_list = sorted(int(p) for p in pages)
        else:
            page_map = dict(pages)
            page_list = sorted(int(p) for p in page_map)
        folders[name] = {
            "pages": page_map,
            "page_list": page_list,
            "count": len(page_list),
        }
    data["folders"] = folders
    return data


def baseline_pages(baseline: dict, folder: str) -> set[int]:
    meta = (baseline.get("folders") or {}).get(folder) or {}
    return set(meta.get("page_list") or [])


def merge_baseline_page(baseline: dict, folder: str, page: int, ev: dict) -> None:
    """Monotonic: add page or raise confidence; never remove/demote."""
    folders = baseline.setdefault("folders", {})
    meta = folders.setdefault(folder, {"pages": {}, "page_list": [], "count": 0})
    pages = meta.setdefault("pages", {})
    key = str(page)
    old = pages.get(key)
    if old is None or int(ev.get("confidence", 0)) > int(old.get("confidence", 0)):
        pages[key] = {
            "confidence": int(ev["confidence"]),
            "grade": ev["grade"],
            "reason": ev["reason"],
            "source": ev.get("source") or "",
            "pdf": ev.get("pdf") or "",
            "pdf_page": str(ev.get("pdf_page") or ""),
        }
    meta["page_list"] = sorted(int(p) for p in pages)
    meta["count"] = len(meta["page_list"])


def save_baseline(baseline: dict) -> None:
    baseline = dict(baseline)
    baseline["note"] = (
        "Monotonic present baseline with per-page confidence. "
        "Later runs ONLY search pages still missing. "
        "Never demote/remove a page; only raise confidence when better evidence appears."
    )
    baseline["grades"] = {
        "A": "85-100 native footer (or native+OCR)",
        "B": "65-84 OCR with Yearbook/Vol context",
        "C": "50-64 weak OCR digit",
        "D": "25-49 prior-only / weak heuristic",
        "S": "100 structural unnumbered-but-present",
    }
    BASELINE.write_text(json.dumps(baseline, indent=2), encoding="utf-8")


def write_confidence_csv(baseline: dict) -> None:
    rows = []
    for folder, meta in sorted((baseline.get("folders") or {}).items()):
        for page_s, ev in sorted(
            (meta.get("pages") or {}).items(), key=lambda kv: int(kv[0])
        ):
            rows.append(
                {
                    "Folder": folder,
                    "Page": page_s,
                    "Confidence": ev.get("confidence", ""),
                    "Grade": ev.get("grade", ""),
                    "Reason": ev.get("reason", ""),
                    "Source": ev.get("source", ""),
                    "PDF": ev.get("pdf", ""),
                    "PdfPage": ev.get("pdf_page", ""),
                    "TwoUp": "",
                }
            )
    with OUT_CONF.open("w", encoding="utf-8", newline="") as f:
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


def prune_page_nums(nums: set[int], leaf_est: int) -> set[int]:
    """Drop impossible/outlier page numbers from bad OCR.

    Single-leaf scans cannot have printed page N much above leaf count.
    Also drop a sparse high tail after a large gap (e.g. dense 1..112 then lone 199).
    """
    if not nums:
        return nums
    cleaned = set(nums)
    if leaf_est > 0:
        # allow a few unnumbered extras, not dozens past the leaf count
        cap = max(leaf_est + 8, int(leaf_est * 1.05) + 3)
        cleaned = {n for n in cleaned if n <= cap}
    if len(cleaned) < 3:
        return cleaned
    ordered = sorted(cleaned)
    # Find largest gap; if tail after gap is thin vs head, drop tail
    best_i, best_gap = 0, 0
    for i in range(len(ordered) - 1):
        g = ordered[i + 1] - ordered[i]
        if g > best_gap:
            best_gap, best_i = g, i
    if best_gap >= 20:
        head, tail = ordered[: best_i + 1], ordered[best_i + 1 :]
        # Lone/sparse high tail after a large gap = bad OCR (e.g. …171 then 202)
        if len(tail) <= 3 and best_gap >= 20:
            cleaned = set(head)
        elif len(tail) <= max(5, len(head) // 8) and best_gap >= 30:
            span = tail[-1] - tail[0] + 1
            if len(tail) < span * 0.35:
                cleaned = set(head)
    return cleaned



def audit_folder(
    year: int,
    folder: Path,
    cache: dict,
    baseline: dict | None = None,
    missing_targets: set[int] | None = None,
) -> dict:
    two_up: list[str] = []
    page_map: list[dict] = []
    pdf_count = 0
    leaf_est = 0
    ocr_used = 0
    all_present: set[int] = set()
    section_headers: list[str] = []
    page_evidence: dict[int, dict] = {}
    baseline = baseline or {"folders": {}}
    # Locked prior finds — never dropped this run
    prior = baseline_pages(baseline, folder.name)
    all_present |= prior
    # If missing-only and we already know targets, still scan leaves that might hold them.
    # Empty Printed leaves / need_ocr paths remain the search surface.
    _ = missing_targets

    for pdf in pdfs_in(folder):
        pdf_count += 1
        print(f"    PDF {pdf.name}", flush=True)
        t0 = time.time()
        try:
            doc = fitz.open(str(pdf))
            native_by_page = {}
            for i in range(len(doc)):
                try:
                    native_by_page[i + 1] = doc[i].get_text("text") or ""
                except Exception:
                    native_by_page[i + 1] = ""
            n_pages = len(doc)
            doc.close()
        except Exception as e:
            page_map.append(
                {
                    "Year": year,
                    "Folder": folder.name,
                    "PDF": pdf.name,
                    "PdfPage": "",
                    "TwoUp": "",
                    "Printed": f"OPEN_FAIL:{e}",
                    "Source": "",
                }
            )
            continue

        native_nums_by_page: dict[int, list[int]] = {}
        need_ocr: list[int] = []
        # 1990 Vol 1 is two-up; other vols are single-leaf
        force_two_up = "1990" in folder.name and "vol 1" in folder.name.lower()
        for pno in range(1, n_pages + 1):
            nums = parse_footer_nums(native_by_page.get(pno, ""))
            if nums:
                native_nums_by_page[pno] = nums
            # Native often garbles readable footers (e.g. "m" for 108) — max-OCR the strip
            if not nums:
                need_ocr.append(pno)
            elif force_two_up and len(nums) < 2:
                need_ocr.append(pno)

        print(
            f"      native ok={len(native_nums_by_page)} need_ocr={len(need_ocr)}/{n_pages} "
            f"native_nums={sum(len(v) for v in native_nums_by_page.values())}",
            flush=True,
        )

        ocr_nums_by_page: dict[int, list[int]] = {}
        two_up_pages: set[int] = set()
        if need_ocr:
            need_set = set(need_ocr)
            for page_no, img in render_pdf_pages(str(pdf), scale=4.0):
                if page_no not in need_set:
                    continue
                halves = _force_halves(img) if force_two_up else _two_up_halves(img)
                if halves or force_two_up:
                    if halves:
                        two_up_pages.add(page_no)
                        leaf_imgs = halves
                    else:
                        leaf_imgs = [img]
                    leaf_hits: list[int] = []
                    for li, leaf in enumerate(leaf_imgs):
                        key = f"{folder.name}/{pdf.name}#p{page_no}:L{li}"
                        # Section dividers first — ignore cached/stray OCR digits on title leaves
                        label = is_section_header_leaf(leaf)
                        if label:
                            sec = f"{pdf.name}#p{page_no}L{li}: {label}"
                            section_headers.append(sec)
                            cache[key] = {"nums": [], "section": sec}
                            ocr_used += 1
                            continue
                        if (
                            key in cache
                            and cache[key].get("nums")
                            and not cache[key].get("section")
                        ):
                            leaf_hits.extend(cache[key]["nums"])
                            continue
                        ocr = ocr_footer_max(leaf)
                        nums = vote_nums([ocr])[:1]  # best footer per leaf
                        cache[key] = {"nums": nums, "ocr_tail": (ocr or "")[-180:]}
                        leaf_hits.extend(nums)
                        ocr_used += 1
                    # merge any native nums we already had
                    for n in native_nums_by_page.get(page_no, []):
                        if n not in leaf_hits:
                            leaf_hits.append(n)
                    ocr_nums_by_page[page_no] = leaf_hits
                else:
                    key = f"{folder.name}/{pdf.name}#p{page_no}:L0"
                    if key in cache and cache[key].get("nums"):
                        ocr_nums_by_page[page_no] = list(cache[key]["nums"])
                        if cache[key].get("section"):
                            section_headers.append(cache[key]["section"])
                    elif key in cache and cache[key].get("section"):
                        section_headers.append(cache[key]["section"])
                        ocr_nums_by_page[page_no] = []
                    else:
                        label = is_section_header_leaf(img)
                        if label:
                            sec = f"{pdf.name}#p{page_no}: {label}"
                            section_headers.append(sec)
                            cache[key] = {"nums": [], "section": sec}
                            ocr_nums_by_page[page_no] = []
                            ocr_used += 1
                        else:
                            ocr = ocr_footer_max(img)
                            nums = vote_nums([ocr, native_by_page.get(page_no, "")])[:1]
                            cache[key] = {"nums": nums, "ocr_tail": (ocr or "")[-180:]}
                            ocr_nums_by_page[page_no] = nums
                            ocr_used += 1
                if len(ocr_nums_by_page) % 3 == 0:
                    save_cache(cache)
                    print(
                        f"      ocr {len(ocr_nums_by_page)}/{len(need_ocr)} "
                        f"last p{page_no}={ocr_nums_by_page[page_no]} "
                        f"({time.time()-t0:.0f}s)",
                        flush=True,
                    )

        # Also detect two-up on native-ok pages via cheap geometry (for reporting)
        # Quick: re-check pages that yielded 2 native nums as two-up
        for pno in range(1, n_pages + 1):
            # Merge native + OCR (do NOT use `or` — a single native num would
            # discard the OCR'd partner leaf on two-up spreads).
            merged = []
            seen_n = set()
            for n in (native_nums_by_page.get(pno) or []) + (ocr_nums_by_page.get(pno) or []):
                if n not in seen_n:
                    seen_n.add(n)
                    merged.append(n)
            nums = merged
            if pno in ocr_nums_by_page and pno in native_nums_by_page:
                src = "native+hqmax_footer"
            elif pno in native_nums_by_page:
                src = "native"
            elif pno in ocr_nums_by_page:
                src = "hqmax_footer"
            else:
                src = "none"
            # Only geometry (or Vol1 force-split) marks two-up — never len(nums)>=2
            # (OCR often returns junk extras like [23,7,8] on a single leaf).
            # Two-up if geometry said so, OR Vol1 native already yielded two footers.
            # Do NOT use len(nums)>=2 on other years (OCR junk like [23,7,8]).
            is_two = pno in two_up_pages or (force_two_up and len(nums) >= 2)
            if is_two:
                two_up.append(f"{folder.name}/{pdf.name}#p{pno}")
                leaf_est += 2
                # keep BOTH footer numbers
            else:
                leaf_est += 1
                # True single leaf: at most one page number (prefer last = footer)
                if len(nums) > 1:
                    nums = [nums[-1]]
            all_present.update(nums)
            # Per-page confidence from best evidence on this leaf
            tails = []
            for li in (0, 1):
                ck = f"{folder.name}/{pdf.name}#p{pno}:L{li}"
                if ck in cache and cache[ck].get("ocr_tail"):
                    tails.append(cache[ck]["ocr_tail"])
            conf_bits = []
            for n in nums:
                conf, grade, reason = score_evidence(src, n, ocr_tail="\n".join(tails))
                conf_bits.append(f"{n}:{grade}{conf}")
                ev = {
                    "confidence": conf,
                    "grade": grade,
                    "reason": reason,
                    "source": src,
                    "pdf": pdf.name,
                    "pdf_page": pno,
                }
                old = page_evidence.get(n)
                if old is None or conf > old["confidence"]:
                    page_evidence[n] = ev
                merge_baseline_page(baseline, folder.name, n, ev)
            page_map.append(
                {
                    "Year": year,
                    "Folder": folder.name,
                    "PDF": pdf.name,
                    "PdfPage": pno,
                    "TwoUp": "yes" if is_two else "no",
                    "Printed": ",".join(map(str, nums)) if nums else "",
                    "Source": src,
                    "Confidence": ";".join(conf_bits),
                }
            )

        save_cache(cache)
        print(
            f"      done {pdf.name} in {time.time()-t0:.0f}s "
            f"folder_present_so_far={len(all_present)}",
            flush=True,
        )

    # Cap/prune impossible OCR page numbers using leaf estimate
    # BUT never prune away prior baseline pages (monotonic trust).
    pruned = prune_page_nums(set(all_present) - prior, leaf_est)
    all_present = pruned | prior
    known_u = KNOWN_UNNUMBERED.get(folder.name, set())
    if all_present:
        lo, hi = min(all_present), max(all_present)
        all_present |= {n for n in known_u if lo <= n <= hi}
        for n in known_u:
            if lo <= n <= hi:
                merge_baseline_page(
                    baseline,
                    folder.name,
                    n,
                    {
                        "confidence": 100,
                        "grade": "S",
                        "reason": "unnumbered-but-present (section/blank)",
                        "source": "structural",
                        "pdf": "",
                        "pdf_page": "",
                    },
                )
    # Ensure every present page has evidence (prior-only = D if not reconfirmed)
    for n in sorted(all_present):
        if n not in page_evidence:
            if n in known_u:
                conf, grade, reason = score_evidence("structural", n)
                src = "structural"
            else:
                conf, grade, reason = score_evidence("baseline_prior", n)
                src = "baseline_prior"
            page_evidence[n] = {
                "confidence": conf,
                "grade": grade,
                "reason": reason,
                "source": src,
                "pdf": "",
                "pdf_page": "",
            }
            merge_baseline_page(baseline, folder.name, n, page_evidence[n])
    printed_u = sorted(all_present)
    missing = gaps_in_set(all_present)
    # Section-header leaves (no footer) explain that many set-gaps — not true missing
    n_sec = len(section_headers)
    if n_sec and missing:
        missing = missing[n_sec:] if len(missing) > n_sec else []
    # Known blank page-number leaves also explain gaps
    missing = [n for n in missing if n not in known_u]
    # HARD RULE: a page previously found can never be "missing" / rescan
    missing = [n for n in missing if n not in prior]
    newly_found = sorted(n for n in page_evidence if n not in prior and n not in known_u)
    return {
        "year": year,
        "folder": folder.name,
        "pdf_count": pdf_count,
        "leaf_est": leaf_est,
        "printed": printed_u,
        "printed_min": printed_u[0] if printed_u else None,
        "printed_max": printed_u[-1] if printed_u else None,
        "missing": missing,
        "two_up": two_up,
        "page_map": page_map,
        "ocr_used": ocr_used,
        "section_headers": section_headers,
        "page_evidence": page_evidence,
        "newly_found": newly_found,
        "prior_locked": len(prior),
    }


def main() -> int:
    configure_tesseract()
    cache = load_cache()  # resume footer OCR across runs
    baseline = load_baseline()
    summaries = []
    all_rows: list[dict] = []
    lines = [
        "1990-1996 YEARBOOK VOL PER-FOLDER AUDIT",
        "=======================================",
        "Each Vol folder audited alone.",
        "Scan order is non-contiguous (front→end, then back→start).",
        "Missing = SET gaps among ALL footer page numbers found in the folder.",
        "HARD RULE: pages previously found (baseline) never become missing/rescan.",
        "MISSING_ONLY mode: skip folders with no remaining gaps vs baseline.",
        "Each found page has Confidence grade A/B/C/D/S (see baseline grades).",
        "Two-up pages contribute BOTH leaf footer numbers when readable.",
        "Native text when clear; else hqmax bottom-strip OCR (scale 4).",
        "",
    ]
    for year in YEARS:
        folders = vol_folders(year)
        print(f"YEAR {year} ({len(folders)} folders)", flush=True)
        for folder in folders:
            if ONLY_FOLDERS and folder.name not in ONLY_FOLDERS:
                continue
            prior = baseline_pages(baseline, folder.name)
            known_u = KNOWN_UNNUMBERED.get(folder.name, set())
            present_est = set(prior) | known_u
            targets = []
            if present_est:
                targets = [
                    n
                    for n in gaps_in_set(present_est)
                    if n not in known_u and n not in prior
                ]
            if MISSING_ONLY and prior and not targets:
                print(
                    f"  {folder.name} ... SKIP (baseline locked, no missing targets; "
                    f"prior={len(prior)})",
                    flush=True,
                )
                printed_u = sorted(present_est)
                summaries.append(
                    {
                        "year": year,
                        "folder": folder.name,
                        "pdf_count": 0,
                        "leaf_est": 0,
                        "printed": printed_u,
                        "printed_min": printed_u[0] if printed_u else None,
                        "printed_max": printed_u[-1] if printed_u else None,
                        "missing": [],
                        "two_up": [],
                        "page_map": [],
                        "ocr_used": 0,
                        "section_headers": [],
                        "page_evidence": {},
                        "newly_found": [],
                        "prior_locked": len(prior),
                        "skipped": True,
                    }
                )
                lines.append(f"{folder.name}")
                lines.append(f"  Year: {year}")
                lines.append(
                    f"  SKIPPED (MISSING_ONLY): no gap targets; "
                    f"locked_present={len(prior)}"
                )
                lines.append(
                    f"  Found list: {','.join(map(str, printed_u)) if printed_u else '(none)'}"
                )
                lines.append("  Missing (rescan): (none)")
                lines.append("")
                continue
            print(
                f"  {folder.name} ... "
                f"(prior_locked={len(prior)} missing_targets="
                f"{len(targets) if prior else 'FULL'})",
                flush=True,
            )
            s = audit_folder(
                year,
                folder,
                cache,
                baseline=baseline,
                missing_targets=set(targets) if targets else None,
            )
            summaries.append(s)
            all_rows.extend(s["page_map"])
            save_cache(cache)
            save_baseline(baseline)
            write_confidence_csv(baseline)
            print(
                f"    RESULT pdfs={s['pdf_count']} printed={s['printed_min']}-{s['printed_max']} "
                f"n={len(s['printed'])} "
                f"two_up={len(s['two_up'])} ocr={s['ocr_used']} "
                f"newly_found={len(s.get('newly_found') or [])}",
                flush=True,
            )
            if s["missing"]:
                print(
                    f"    RESCAN PAGES ({len(s['missing'])}): "
                    + ",".join(map(str, s["missing"])),
                    flush=True,
                )
            else:
                print("    RESCAN PAGES: (none)", flush=True)
            # Grade histogram for this folder
            grades = {}
            for ev in (s.get("page_evidence") or {}).values():
                g = ev.get("grade") or "?"
                grades[g] = grades.get(g, 0) + 1
            if grades:
                print(
                    "    CONFIDENCE: "
                    + " ".join(f"{g}={grades[g]}" for g in sorted(grades)),
                    flush=True,
                )
            lines.append(f"{s['folder']}")
            lines.append(f"  Year: {year}")
            lines.append(
                f"  PDFs: {s['pdf_count']}  leaves~{s['leaf_est']}  "
                f"ocr_footer_calls: {s['ocr_used']}  "
                f"prior_locked: {s.get('prior_locked', 0)}"
            )
            if s["printed"]:
                lines.append(
                    f"  Printed pages found: {s['printed_min']}-{s['printed_max']} "
                    f"({len(s['printed'])} distinct)"
                )
                lines.append(
                    f"  Rescan (never-found gaps) ({len(s['missing'])}): "
                    + (",".join(map(str, s["missing"])) if s["missing"] else "(none)")
                )
                if s.get("newly_found"):
                    lines.append(
                        f"  Newly found this run: "
                        + ",".join(map(str, s["newly_found"]))
                    )
                lines.append(f"  Found list: {','.join(map(str, s['printed']))}")
                # Compact confidence list: page:grade
                conf_bits = []
                for n in s["printed"]:
                    ev = (s.get("page_evidence") or {}).get(n) or {}
                    conf_bits.append(f"{n}:{ev.get('grade', '?')}{ev.get('confidence', '')}")
                lines.append(f"  Confidence: {','.join(conf_bits)}")
            else:
                lines.append("  Printed pages found: NONE")
            if s["two_up"]:
                lines.append(f"  Two-up PDF pages ({len(s['two_up'])}):")
                for item in s["two_up"][:80]:
                    lines.append(f"    - {item}")
                if len(s["two_up"]) > 80:
                    lines.append(f"    ... +{len(s['two_up'])-80} more")
            else:
                lines.append("  Two-up PDF pages: none flagged")
            lines.append("")
            OUT_TXT.write_text("\n".join(lines) + "\n", encoding="utf-8")
            with OUT_SUM.open("w", encoding="utf-8", newline="") as f:
                w = csv.DictWriter(
                    f,
                    fieldnames=[
                        "Year",
                        "Folder",
                        "Pdfs",
                        "LeafEst",
                        "PrintedMin",
                        "PrintedMax",
                        "PrintedCount",
                        "MissingCount",
                        "Missing",
                        "TwoUpCount",
                        "OcrUsed",
                        "PriorLocked",
                        "NewlyFound",
                    ],
                )
                w.writeheader()
                for ss in summaries:
                    w.writerow(
                        {
                            "Year": ss["year"],
                            "Folder": ss["folder"],
                            "Pdfs": ss["pdf_count"],
                            "LeafEst": ss["leaf_est"],
                            "PrintedMin": ss["printed_min"] or "",
                            "PrintedMax": ss["printed_max"] or "",
                            "PrintedCount": len(ss["printed"]),
                            "MissingCount": len(ss["missing"]),
                            "Missing": ",".join(map(str, ss["missing"])),
                            "TwoUpCount": len(ss["two_up"]),
                            "OcrUsed": ss["ocr_used"],
                            "PriorLocked": ss.get("prior_locked", 0),
                            "NewlyFound": ",".join(
                                map(str, ss.get("newly_found") or [])
                            ),
                        }
                    )

    with OUT_CSV.open("w", encoding="utf-8", newline="") as f:
        w = csv.DictWriter(
            f,
            fieldnames=[
                "Year",
                "Folder",
                "PDF",
                "PdfPage",
                "TwoUp",
                "Printed",
                "Source",
                "Confidence",
            ],
        )
        w.writeheader()
        w.writerows(all_rows)
    OUT_TXT.write_text("\n".join(lines) + "\n", encoding="utf-8")
    save_baseline(baseline)
    write_confidence_csv(baseline)
    print(f"Wrote {OUT_TXT}", flush=True)
    print(f"Wrote {OUT_CSV}", flush=True)
    print(f"Wrote {OUT_SUM}", flush=True)
    print(f"Wrote {OUT_CONF}", flush=True)
    print(f"Wrote {BASELINE}", flush=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
