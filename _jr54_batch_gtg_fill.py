"""Fill empty Go-to-Ground CHAMPION & RESERVE -> RACING DIVISION from PDF text."""
from __future__ import annotations

import re
from pathlib import Path

import fitz

from yearbook_ocr import audit_results_ocr_page
from _jr54_recover_v2 import TARGET, find_hq, find_pdf, find_updated_hq, BASE

EMPTY = re.compile(
    r"(Go-to-Ground CHAMPION & RESERVE|GO-TO-GROUND CHAMPION & RESERVE)\n"
    r"(RACING DIVISION\n)",
    re.I,
)

CHAMP_BLOCK = re.compile(
    r"(?is)(?:Go-?to-?Ground|GO-?TO-?GROUND)\s+CHAMPION(?:\s*&\s*RESERVE)?\s*"
    r"(.*?)"
    r"(?=RACING\s+DIVISION|FLAT\s+RACES)",
)


def extract_champ_lines(pdf_text: str) -> list[str] | None:
    m = CHAMP_BLOCK.search(pdf_text)
    if not m:
        return None
    body = m.group(1)
    lines = []
    for raw in body.splitlines():
        s = " ".join(raw.split()).strip()
        if not s:
            continue
        if re.search(r"(?i)champion|reserve", s) and re.search(r"(?i)owned by", s):
            lines.append(s)
        elif re.search(r'(?i)\d+.*"\s*Champion:', s) or re.search(r'(?i)\d+.*"\s*Reserve:', s):
            lines.append(s)
        elif re.match(r"(?i)^(Champion|Reserve)\s*:", s):
            lines.append(s)
    # Also handle split name/owner lines: Champion: NAME\nowned by OWNER
    if not lines:
        # reconstruct from looser parse
        tmp = []
        buf = ""
        for raw in body.splitlines():
            s = " ".join(raw.split()).strip()
            if not s:
                continue
            if re.match(r"(?i)^(Champion|Reserve|\d)", s) or re.search(r'(?i)\d+.*".*Champion|\d+.*".*Reserve', s):
                if buf:
                    tmp.append(buf)
                buf = s
            elif buf and re.search(r"(?i)^owned by", s):
                buf = buf.rstrip(",") + ", " + s
            elif buf:
                buf = buf + " " + s
        if buf:
            tmp.append(buf)
        lines = [x for x in tmp if re.search(r"(?i)champion|reserve", x)]
    # Must have owned-by evidence
    good = [ln for ln in lines if re.search(r"(?i)owned by", ln)]
    return good if good else None


def fill_file(year: int, hq: Path) -> tuple[int, int, list[str]]:
    text = hq.read_text(encoding="utf-8", errors="replace")
    before = sum(1 for c, _ in audit_results_ocr_page(text, max_samples=120) if c in TARGET)
    if not EMPTY.search(text):
        return before, before, []
    pdf = find_pdf(year, hq)
    if not pdf:
        return before, before, ["no pdf"]
    doc = fitz.open(str(pdf))
    notes = []
    # Build per-page champ maps
    page_champs: list[list[str] | None] = []
    for i in range(doc.page_count):
        page_champs.append(extract_champ_lines(doc.load_page(i).get_text()))

    def repl(m: re.Match) -> str:
        header, racing = m.group(1), m.group(2)
        # Find HQ page marker before this match
        start = m.start()
        page_m = None
        for pm in re.finditer(r"(?i)^---\s*page\s+(\d+)\s*---", text[:start], re.M):
            page_m = pm
        # Prefer PDF page ~= HQ page, else search nearby pages for champs
        cands: list[str] = []
        if page_m:
            p = int(page_m.group(1))
            for delta in range(0, 4):
                for pp in (p - 1 + delta, p - 1 - delta):
                    if 0 <= pp < len(page_champs) and page_champs[pp]:
                        cands = page_champs[pp]
                        break
                if cands:
                    break
        if not cands:
            for pc in page_champs:
                if pc:
                    # use first available — weak; skip to avoid wrong trial
                    pass
            notes.append(f"no champ lines near HQ page for smash at {start}")
            return m.group(0)
        block = header + "\n" + "\n".join(cands) + "\n" + racing
        notes.append(f"filled {len(cands)} champ lines near p{page_m.group(1) if page_m else '?'}")
        return block

    new_text, nsub = EMPTY.subn(repl, text)
    if nsub == 0 or new_text == text:
        return before, before, notes or ["no substitution"]
    if not new_text.endswith("\n"):
        new_text += "\n"
    hq.write_text(new_text, encoding="utf-8")
    upd = find_updated_hq(year, hq)
    if upd:
        upd.write_text(new_text, encoding="utf-8")
    after = sum(1 for c, _ in audit_results_ocr_page(new_text, max_samples=120) if c in TARGET)
    return before, after, notes


def main():
    changed = []
    for year_dir in sorted(BASE.iterdir()):
        if not year_dir.is_dir() or not year_dir.name.isdigit():
            continue
        year = int(year_dir.name)
        if year < 1994 or year > 2001:
            continue
        for hq in sorted(year_dir.rglob("*_ocr_hqmax.txt")):
            if ".pre_" in hq.name:
                continue
            text = hq.read_text(encoding="utf-8", errors="replace")
            if not EMPTY.search(text):
                continue
            b, a, notes = fill_file(year, hq)
            print(f"{year} {hq.name}: {b}->{a} | {notes}")
            if a < b:
                changed.append((year, hq.name, b, a))
    print("IMPROVED", len(changed))
    for row in changed:
        print(" ", row)


if __name__ == "__main__":
    main()
