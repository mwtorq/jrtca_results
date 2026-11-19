"""Honest 1996 Vol II pg93-162 front fills: orphan joins + PDF OCR."""
from pathlib import Path
import sys

sys.path.insert(0, ".")
from _jr54_strip_place_prefix_junk import count_gaps

path = list(Path("Updated Yearbook Scans").rglob("1996 Vol II pg 93-162 front_ocr_hqmax.txt"))[0]
text = path.read_text(encoding="utf-8", errors="replace")
before = count_gaps(text.splitlines())


def repl(old: str, new: str, label: str) -> None:
    global text
    if old not in text:
        print("MISS", label)
        return
    text = text.replace(old, new, 1)
    print(label, "ok")


# Orphan dogs before 2nd Grizzle are 1st/3rd
repl(
    "Rainland Romeo, owned by Robert & Linda Fleck\n"
    "Ridgeviews Riley, owned by Bill & Renee Herold\n"
    "2nd: RuffN Tumble Grizzle, owned by Donald Tait\n"
    "# PARKED jr54: place-rank gap after RuffN Tumble Grizzle before Golden Hills Rush (OCR blank; no surname invent)\n"
    "4th: Golden Hills Rush, owned by Jeff & Connie McKee",
    "1st: Rainland Romeo, owned by Robert & Linda Fleck\n"
    "2nd: RuffN Tumble Grizzle, owned by Donald Tait\n"
    "3rd: Ridgeviews Riley, owned by Bill & Renee Herold\n"
    "4th: Golden Hills Rush, owned by Jeff & Connie McKee",
    "grizzle",
)

after = count_gaps(text.splitlines())
path.write_text(text, encoding="utf-8", newline="\n")
print("file", before, "->", after)
