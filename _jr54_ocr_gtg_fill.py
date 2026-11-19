"""OCR-fill empty GTG CHAMPION -> RACING smashes when PDF text layer lacks champs."""
from __future__ import annotations

import io
import re
from pathlib import Path

import fitz
import pytesseract
from PIL import Image

from yearbook_ocr import audit_results_ocr_page
from _jr54_recover_v2 import TARGET, find_hq, find_pdf, find_updated_hq, BASE

pytesseract.pytesseract.tesseract_cmd = r"C:\Program Files\Tesseract-OCR\tesseract.exe"

EMPTY = re.compile(
    r"(Go-to-Ground CHAMPION & RESERVE|GO-TO-GROUND CHAMPION & RESERVE)\n"
    r"(RACING DIVISION\n)",
    re.I,
)


def ocr_page(pdf: Path, page_0: int) -> str:
    doc = fitz.open(str(pdf))
    if page_0 < 0 or page_0 >= doc.page_count:
        return ""
    page = doc.load_page(page_0)
    pix = page.get_pixmap(matrix=fitz.Matrix(2.5, 2.5), alpha=False)
    img = Image.open(io.BytesIO(pix.tobytes("png")))
    return pytesseract.image_to_string(img)


def champs_from_ocr(ot: str) -> list[str]:
    # window around GTG header
    m = re.search(r"(?i)GO-?TO-?GROUND\s+CHAMPION", ot)
    if not m:
        return []
    chunk = ot[m.start() : m.start() + 900]
    stop = re.search(r"(?i)RACING\s+DIVISION|FLAT\s+RACES", chunk)
    if stop:
        chunk = chunk[: stop.start()]
    lines = []
    for raw in chunk.splitlines():
        s = " ".join(raw.split()).strip()
        if re.search(r"(?i)owned by", s) and re.search(r"(?i)champion|reserve", s):
            lines.append(s)
        elif re.match(r"(?i)^(Champion|Reserve)\s*:", s) and "owned" in s.lower():
            lines.append(s)
    return lines


def process_hq(year: int, hq: Path) -> None:
    text = hq.read_text(encoding="utf-8", errors="replace")
    if not EMPTY.search(text):
        return
    pdf = find_pdf(year, hq)
    if not pdf:
        print(year, hq.name, "no pdf")
        return
    before = sum(1 for c, _ in audit_results_ocr_page(text, max_samples=80) if c in TARGET)

    def repl(m: re.Match) -> str:
        header, racing = m.group(1), m.group(2)
        start = m.start()
        page_m = None
        for pm in re.finditer(r"(?i)^---\s*page\s+(\d+)\s*---", text[:start], re.M):
            page_m = pm
        pages = []
        if page_m:
            p = int(page_m.group(1))
            pages = [p - 1, p, p - 2, p + 1]
        else:
            pages = [0, 1, 2]
        for p0 in pages:
            ot = ocr_page(pdf, p0)
            lines = champs_from_ocr(ot)
            if lines:
                return header + "\n" + "\n".join(lines) + "\n" + racing
        return m.group(0)

    new_text = EMPTY.sub(repl, text)
    if new_text == text:
        print(year, hq.name, "no OCR fill")
        return
    if not new_text.endswith("\n"):
        new_text += "\n"
    hq.write_text(new_text, encoding="utf-8")
    upd = find_updated_hq(year, hq)
    if upd:
        upd.write_text(new_text, encoding="utf-8")
    after = sum(1 for c, _ in audit_results_ocr_page(new_text, max_samples=80) if c in TARGET)
    print(year, hq.name, f"{before}->{after}")


def main():
    # Focus Document_* vols first (have usable PDFs), then a few 1996 fronts
    targets = []
    for year in range(1994, 2002):
        ydir = BASE / str(year)
        if not ydir.exists():
            continue
        for hq in sorted(ydir.rglob("*_ocr_hqmax.txt")):
            if ".pre_" in hq.name:
                continue
            t = hq.read_text(encoding="utf-8", errors="replace")
            if EMPTY.search(t):
                targets.append((year, hq))
    print("empty smash files", len(targets))
    # Prefer Document_ and smaller files first
    targets.sort(key=lambda x: (0 if "Document_" in x[1].name else 1, x[1].stat().st_size))
    for year, hq in targets[:25]:
        process_hq(year, hq)


if __name__ == "__main__":
    main()
