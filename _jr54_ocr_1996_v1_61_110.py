"""Re-OCR selected pages from 1996 Vol1 pg61-110 front for parked gaps."""
from pathlib import Path
import fitz
from PIL import Image
import io
import pytesseract

pytesseract.pytesseract.tesseract_cmd = r"C:\Program Files\Tesseract-OCR\tesseract.exe"
pdf = Path(r"Yearbook Scans/1996 Vol I/1996 Vol 1 pg 61-110 front.pdf")
doc = fitz.open(pdf)
out = Path("_jr54_ocr_1996_v1_61_110")
out.mkdir(exist_ok=True)
print("pages", doc.page_count)

# HQ --- page N --- ~ PDF index N-1 for this extract
targets = [0, 1, 21]  # page1 (Double D), page2 (Susie), page22 (Megan)
needles = ["Whirlwing", "Susie", "Megan", "Locust Ridge", "Three Oaks Double", "Turbo of Ball"]


def ocr_page(i: int) -> str:
    page = doc[i]
    pix = page.get_pixmap(matrix=fitz.Matrix(2.8, 2.8), alpha=False)
    img = Image.open(io.BytesIO(pix.tobytes("png")))
    w, h = img.size
    mid = w // 2
    lt = pytesseract.image_to_string(img.crop((0, 0, mid + 30, h)), config="--psm 6")
    rt = pytesseract.image_to_string(img.crop((mid - 30, 0, w, h)), config="--psm 6")
    return f"--- L ---\n{lt}\n--- R ---\n{rt}\n"


# also scan for needle hits
for i in range(doc.page_count):
    pix = doc[i].get_pixmap(matrix=fitz.Matrix(1.15, 1.15), alpha=False)
    img = Image.open(io.BytesIO(pix.tobytes("png")))
    t = pytesseract.image_to_string(img, config="--psm 6")
    h = [k for k in needles if k.lower() in t.lower()]
    if h:
        print(f"pdf[{i}] {h}")
        targets.append(i)

for i in sorted(set(targets)):
    if i >= doc.page_count:
        continue
    p = out / f"pdf{i}.txt"
    p.write_text(ocr_page(i), encoding="utf-8")
    print("wrote", p.name)
