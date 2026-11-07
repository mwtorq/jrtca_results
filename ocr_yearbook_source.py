#!/usr/bin/env python3
"""OCR Yearbook Scans / Photos image PDFs and JPGs into sibling *_ocr.txt files.

Year is derived from page content (dates / trial headers), not from folder names.
Legacy Yearbook Scans *.txt/*.rtf OCR is non-authoritative for placements.
"""
from __future__ import annotations

import argparse
import os
import re
import sys
from collections import Counter
from pathlib import Path

TESSERACT_EXE = r"C:\Program Files\Tesseract-OCR\tesseract.exe"

_YEAR_RE = re.compile(r"\b(19[8-9]\d|20[0-2]\d)\b")
_DATEISH_RE = re.compile(
    r"(?:Jan(?:uary)?|Feb(?:ruary)?|Mar(?:ch)?|Apr(?:il)?|May|Jun(?:e)?|"
    r"Jul(?:y)?|Aug(?:ust)?|Sep(?:t(?:ember)?)?|Oct(?:ober)?|Nov(?:ember)?|"
    r"Dec(?:ember)?)\s+\d{1,2},?\s+(19[8-9]\d|20[0-2]\d)"
    r"|\b(19[8-9]\d|20[0-2]\d)\b",
    re.I,
)


def configure_tesseract() -> None:
    import pytesseract

    if os.path.isfile(TESSERACT_EXE):
        pytesseract.pytesseract.tesseract_cmd = TESSERACT_EXE


def ocr_sibling_path(source_path: str) -> str:
    p = Path(source_path)
    return str(p.with_name(p.stem + "_ocr.txt"))


def is_yearbook_path(path: str) -> bool:
    norm = path.replace("/", "\\").lower()
    return "yearbook scans" in norm or "yearbook photos" in norm


def extract_embedded_pdf_text(pdf_path: str) -> str:
    try:
        from scrape_trial_results_fixed import extract_text_from_pdf

        return (extract_text_from_pdf(pdf_path) or "").strip()
    except Exception:
        return ""


def render_pdf_pages(pdf_path: str, max_pages: int | None = None, scale: float = 2.0):
    """Yield (page_index_1based, PIL.Image) for each PDF page."""
    import pypdfium2 as pdfium
    from PIL import Image

    pdf = pdfium.PdfDocument(pdf_path)
    n = len(pdf)
    limit = n if max_pages is None else min(n, max_pages)
    for i in range(limit):
        page = pdf[i]
        bitmap = page.render(scale=scale)
        pil = bitmap.to_pil()
        if not isinstance(pil, Image.Image):
            pil = Image.fromarray(pil)
        yield i + 1, pil.convert("RGB")


def ocr_pil_image(img, psm: int = 6) -> str:
    import pytesseract

    configure_tesseract()
    return pytesseract.image_to_string(img, config=f"--psm {psm}") or ""


def ocr_image_file(image_path: str) -> str:
    from PIL import Image

    with Image.open(image_path) as im:
        return ocr_pil_image(im.convert("RGB"))


def ocr_pdf_file(pdf_path: str, max_pages: int | None = None) -> str:
    embedded = extract_embedded_pdf_text(pdf_path)
    if len(embedded) >= 80:
        return embedded
    chunks = []
    for page_no, img in render_pdf_pages(pdf_path, max_pages=max_pages):
        text = ocr_pil_image(img)
        chunks.append(f"--- page {page_no} ---\n{text}".rstrip())
    return "\n\n".join(chunks).strip()


def ocr_source_to_text(source_path: str, max_pages: int | None = None) -> str:
    ext = Path(source_path).suffix.lower()
    if ext in (".jpg", ".jpeg", ".png", ".tif", ".tiff", ".webp", ".bmp"):
        return ocr_image_file(source_path).strip()
    if ext == ".pdf":
        return ocr_pdf_file(source_path, max_pages=max_pages).strip()
    if ext in (".txt", ".rtf"):
        with open(source_path, "r", encoding="utf-8", errors="ignore") as f:
            return f.read().strip()
    raise ValueError(f"Unsupported source type: {ext}")


def derive_year_from_text(text: str, folder_hint: int | None = None) -> int | None:
    """Pick most likely trial year from OCR/text content.

    Folder/path year is only a weak tie-break when content is ambiguous.
    Never returns folder_hint alone without at least one content year.
    """
    if not text:
        return None
    head = text[:4000]
    # Strong: "BOARD ... FOR 1986", "1988 JRTCA", "THE J.R.T.C.A. 1988"
    titled = re.findall(
        r"(?i)(?:FOR|YEARBOOK|JRTCA|J\.?R\.?T\.?C\.?A\.?)\s+(19[8-9]\d|20[0-2]\d)"
        r"|(19[8-9]\d|20[0-2]\d)\s+(?:JRTCA|J\.?R\.?T\.?C\.?A\.?|YEARBOOK|BOARD|BREEDER)",
        head,
    )
    title_years = []
    for g in titled:
        if isinstance(g, tuple):
            title_years.extend(int(x) for x in g if x)
        elif g:
            title_years.append(int(g))
    if title_years:
        return Counter(title_years).most_common(1)[0][0]

    date_years = []
    for m in _DATEISH_RE.finditer(head):
        y = m.group(1) or m.group(2)
        if y:
            date_years.append(int(y))
    if date_years:
        # Prefer years appearing in date-like phrases near the top.
        return Counter(date_years).most_common(1)[0][0]

    years = [int(y) for y in _YEAR_RE.findall(text)]
    if not years:
        return None
    counts = Counter(years)
    # Prefer years that also appear in the first 1500 chars.
    head_years = [int(y) for y in _YEAR_RE.findall(head)]
    if head_years:
        head_counts = Counter(head_years)
        best = max(head_counts.items(), key=lambda kv: (kv[1], -abs((folder_hint or kv[0]) - kv[0])))
        return best[0]
    if folder_hint and folder_hint in counts:
        return folder_hint
    return counts.most_common(1)[0][0]


def folder_year_hint(path: str) -> int | None:
    """Weak hint only — not authoritative."""
    m = re.search(r"(19[8-9]\d|20[0-2]\d)", path.replace("\\", "/"))
    return int(m.group(1)) if m else None


def write_ocr_sibling(
    source_path: str,
    *,
    force: bool = False,
    max_pages: int | None = None,
) -> tuple[str, int | None, str]:
    """OCR source to sibling *_ocr.txt. Returns (ocr_path, derived_year, text)."""
    out = ocr_sibling_path(source_path)
    if os.path.isfile(out) and not force and os.path.getsize(out) > 40:
        with open(out, "r", encoding="utf-8", errors="ignore") as f:
            text = f.read()
        year = derive_year_from_text(text, folder_year_hint(source_path))
        return out, year, text

    text = ocr_source_to_text(source_path, max_pages=max_pages)
    year = derive_year_from_text(text, folder_year_hint(source_path))
    header = []
    header.append(f"Source: {os.path.basename(source_path)}")
    if year:
        header.append(f"DerivedYear: {year}")
    header.append(f"FolderHintYear: {folder_year_hint(source_path) or ''}")
    header.append("")
    body = "\n".join(header) + text + ("\n" if text and not text.endswith("\n") else "")
    with open(out, "w", encoding="utf-8", newline="\n") as f:
        f.write(body)
    return out, year, body


def resolve_parse_text_path(source_path: str, *, ensure_ocr: bool = True) -> str:
    """Return a text path suitable for parse_trial_source_file.

    For yearbook image PDFs/JPGs, ensure *_ocr.txt exists and return that.
    """
    ext = Path(source_path).suffix.lower()
    if ext in (".txt", ".html", ".htm", ".rtf"):
        return source_path
    sibling = ocr_sibling_path(source_path)
    if os.path.isfile(sibling) and os.path.getsize(sibling) > 40:
        return sibling
    if ensure_ocr and ext in (".pdf", ".jpg", ".jpeg", ".png", ".tif", ".tiff", ".webp", ".bmp"):
        out, _, _ = write_ocr_sibling(source_path)
        return out
    return source_path


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("paths", nargs="+", help="PDF/JPG/PNG files to OCR")
    ap.add_argument("--force", action="store_true")
    ap.add_argument("--max-pages", type=int, default=None)
    args = ap.parse_args(argv)
    configure_tesseract()
    for path in args.paths:
        if not os.path.isfile(path):
            print(f"MISSING {path}", flush=True)
            continue
        out, year, text = write_ocr_sibling(
            path, force=args.force, max_pages=args.max_pages
        )
        print(
            f"OK year={year} chars={len(text)} out={out}",
            flush=True,
        )
        print(text[:500].replace("\r", ""), flush=True)
        print("---", flush=True)
    return 0


if __name__ == "__main__":
    sys.exit(main())
