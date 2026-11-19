"""JR-54: glued-ordinal sweep + optional Tesseract page OCR for stubborn gaps."""
from __future__ import annotations

import json
import re
import shutil
from pathlib import Path

import fitz

from _jr54_recover_v2 import (
    TARGET,
    find_gap_blocks,
    find_hq,
    find_pdf,
    find_updated_hq,
    ordinal,
    places_between_neighbors,
    dog_key,
    clean_body,
)
from yearbook_ocr import audit_results_ocr_page

GLUED_RE = re.compile(
    r"(?im)^(\d+)(?:st|nd|rd|th)\s*:\s*(.+?)(\d+)(?:st|nd|rd|th)\s*:\s*(.+)$"
)


def split_glued_line(ln: str) -> tuple[str, str] | None:
    m = re.match(
        r"(?i)^(\d+)(?:st|nd|rd|th)\s*:\s*(.+?)(\d+)(?:st|nd|rd|th)\s*:\s*(.+)$",
        ln.strip(),
    )
    if not m:
        return None
    r1, left, r2, right = int(m.group(1)), m.group(2).strip().rstrip(",;"), int(m.group(3)), m.group(4).strip()
    if len(left) < 3 or not re.search(r"(?i)owned by|handled by", right):
        return None
    # left must already be complete enough (owned/handled) OR we skip (no invent)
    if not re.search(r"(?i)owned by|handled by", left):
        return None
    return f"{ordinal(r1)}: {left}", f"{ordinal(r2)}: {right}"


def ocr_page(pdf: Path, page_1based: int) -> str:
    try:
        import io

        import pytesseract
        from PIL import Image
    except Exception:
        return ""
    tess = Path(r"C:\Program Files\Tesseract-OCR\tesseract.exe")
    if tess.exists():
        pytesseract.pytesseract.tesseract_cmd = str(tess)
    try:
        doc = fitz.open(pdf)
        if page_1based < 1 or page_1based > doc.page_count:
            return ""
        page = doc.load_page(page_1based - 1)
        pix = page.get_pixmap(matrix=fitz.Matrix(2, 2), alpha=False)
        img = Image.open(io.BytesIO(pix.tobytes("png")))
        return pytesseract.image_to_string(img)
    except Exception as e:
        print(f"OCR fail {pdf.name} p{page_1based}: {e}", flush=True)
        return ""


def process_file(year: int, file: str, *, do_ocr: bool = False) -> dict:
    hq = find_hq(year, file)
    if not hq:
        return {"file": file, "error": "missing"}
    text = hq.read_text(encoding="utf-8", errors="replace")
    before = sum(1 for c, _ in audit_results_ocr_page(text, max_samples=150) if c in TARGET)
    glued = []
    out_lines = []
    for ln in text.splitlines():
        sp = split_glued_line(ln)
        if sp:
            out_lines.extend(sp)
            glued.append(f"{ln[:70]} => {sp[0]} | {sp[1]}")
        else:
            out_lines.append(ln)
    text2 = "\n".join(out_lines)
    ocr_rec = []
    if do_ocr:
        pdf = find_pdf(year, hq)
        if pdf and pdf.exists():
            lines = text2.splitlines()
            gaps = find_gap_blocks(lines)
            # limit OCR pages to avoid thrash
            budget = 8
            for g in sorted(gaps, key=lambda x: x["ia"])[:budget]:
                # hq page
                page = None
                for j in range(g["ia"], -1, -1):
                    m = re.match(r"(?i)^---\s*page\s+(\d+)", lines[j].strip())
                    if m:
                        page = int(m.group(1))
                        break
                if not page:
                    continue
                ka, kb = dog_key(g["sa"]), dog_key(g["sb"])
                for p in (page, page - 1, page + 1):
                    if p < 1:
                        continue
                    # try text layer first already done in v2; OCR now
                    ot = ocr_page(pdf, p)
                    if not ot or len(ot) < 40:
                        continue
                    got = places_between_neighbors(ot, ka, kb, g["missing"])
                    if got:
                        insert_at = g["ia"] + 1
                        block = [f"{ordinal(r)}: {got[r]}" for r in sorted(got)]
                        lines[insert_at:insert_at] = block
                        for r in sorted(got):
                            ocr_rec.append(f"OCR p{p} {ordinal(r)}: {got[r][:70]}")
                        text2 = "\n".join(lines)
                        break
                if len(ocr_rec) >= 5:
                    break

    changed = glued or ocr_rec
    if changed:
        bak = Path(str(hq) + ".pre_jr54_glued")
        if not bak.exists():
            shutil.copy2(hq, bak)
        if not text2.endswith("\n"):
            text2 += "\n"
        hq.write_text(text2, encoding="utf-8")
        upd = find_updated_hq(year, hq)
        if upd:
            upd.write_text(text2, encoding="utf-8")
    after = sum(1 for c, _ in audit_results_ocr_page(text2 if changed else text, max_samples=150) if c in TARGET)
    return {
        "year": year,
        "file": file,
        "before": before,
        "after": after,
        "glued": glued,
        "ocr_rec": ocr_rec,
    }


def main() -> None:
    import argparse

    ap = argparse.ArgumentParser()
    ap.add_argument("--years", type=int, nargs="+", required=True)
    ap.add_argument("--ocr", action="store_true")
    ap.add_argument("--limit", type=int, default=0)
    args = ap.parse_args()
    dem = json.loads(Path("_jr54_demote_counts.json").read_text(encoding="utf-8"))
    rows = [d for d in dem["demoted"] if d["year"] in args.years]
    if args.limit:
        rows = rows[: args.limit]
    reports = []
    for d in rows:
        print(f"### {d['year']} {d['file']}", flush=True)
        r = process_file(d["year"], d["file"], do_ocr=args.ocr)
        print(
            f"hits {r.get('before')}->{r.get('after')} glued={len(r.get('glued', []))} ocr={len(r.get('ocr_rec', []))}",
            flush=True,
        )
        for g in r.get("glued", [])[:5]:
            print(" ~", g, flush=True)
        for g in r.get("ocr_rec", [])[:5]:
            print(" +", g, flush=True)
        reports.append(r)
    out = Path(f"_jr54_glued_ocr_{'_'.join(map(str, args.years))}.json")
    out.write_text(json.dumps(reports, indent=2), encoding="utf-8")
    print("WROTE", out)


if __name__ == "__main__":
    main()
