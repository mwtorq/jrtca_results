"""Re-OCR 2001 Vol II pt1 PDF pages that host remaining place_rank gaps."""
from pathlib import Path
import fitz
from PIL import Image
import io
import pytesseract

pytesseract.pytesseract.tesseract_cmd = r"C:\Program Files\Tesseract-OCR\tesseract.exe"
pdf = Path(r"Yearbook Scans/2001 Vol II/2001 Vol II pt 1.pdf")
doc = fitz.open(pdf)
out = Path("_jr54_ocr_2001_ii1_gaps")
out.mkdir(exist_ok=True)
print("pages", doc.page_count)

# HQ --- page N --- is 1-based yearbook page; PDF index may be N-1 or offset.
# Probe a few indices around racing keywords.
needles = [
    "Ash Creek Theft",
    "Farmcliff Joe",
    "Andlin Czar War",
    "Skyline Orchard Sir Maxim",
    "Goulden Ridge",
    "Morgan Hill Natasha",
    "Lost Acres Revion",
]


def ocr_page(i: int) -> str:
    page = doc[i]
    pix = page.get_pixmap(matrix=fitz.Matrix(2.8, 2.8), alpha=False)
    img = Image.open(io.BytesIO(pix.tobytes("png")))
    w, h = img.size
    mid = w // 2
    lt = pytesseract.image_to_string(img.crop((0, 0, mid + 30, h)), config="--psm 6")
    rt = pytesseract.image_to_string(img.crop((mid - 30, 0, w, h)), config="--psm 6")
    return f"--- L ---\n{lt}\n--- R ---\n{rt}\n"


hits = []
for i in range(doc.page_count):
    # cheap scan at lower res
    pix = doc[i].get_pixmap(matrix=fitz.Matrix(1.2, 1.2), alpha=False)
    img = Image.open(io.BytesIO(pix.tobytes("png")))
    t = pytesseract.image_to_string(img, config="--psm 6")
    h = [k for k in needles if k.lower() in t.lower()]
    if h:
        print(f"pdf[{i}] hits {h}")
        hits.append(i)

for i in sorted(set(hits)):
    p = out / f"pdf{i}.txt"
    p.write_text(ocr_page(i), encoding="utf-8")
    print("wrote", p.name, "chars", p.stat().st_size)
