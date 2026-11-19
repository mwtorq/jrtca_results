"""Honest 2001 Yankee fills from Yankee_ocr.txt column twins."""
from pathlib import Path
import sys

sys.path.insert(0, ".")
from _jr54_strip_place_prefix_junk import count_gaps

path = list(Path("Updated Yearbook Scans").rglob("2001 Yankee_ocr_hqmax.txt"))[0]
text = path.read_text(encoding="utf-8", errors="replace")
before = count_gaps(text.splitlines())

reps = [
    (
        "natasha_kayla",
        "4th: Morgan Hill Natasha, owned by Julie Waardenburg\n"
        "# PARKED jr54: place-rank gap after Morgan Hill Natasha before Adins Trax (column-break; OCR blank 5th; no surname invent)\n"
        "--- column RIGHT ---\n"
        "6th: Adins Trax, owned by Alison Linstrum",
        "4th: Morgan Hill Natasha, owned by Julie Waardenburg\n"
        "5th: Kenswick Kayla, owned by Sandy McEleamey\n"
        "6th: Adins Trax, owned by Alison Linstrum",
    ),
]

for label, old, new in reps:
    n = text.count(old)
    if n == 0:
        print("MISS", label)
        # show nearby for debug
        continue
    text = text.replace(old, new)
    print(label, "x", n)

after = count_gaps(text.splitlines())
path.write_text(text, encoding="utf-8", newline="\n")
print("file", before, "->", after)
