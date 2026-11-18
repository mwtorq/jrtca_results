"""Clear Kalispell→Pistol structural smash using twin Document Family Class."""
from pathlib import Path
import sys

sys.path.insert(0, ".")
from _jr54_strip_place_prefix_junk import count_gaps

path = list(Path("Updated Yearbook Scans").rglob("1996 Vol II pg 163-220 front_ocr_hqmax.txt"))[0]
text = path.read_text(encoding="utf-8", errors="replace")
before = count_gaps(text.splitlines())

old = (
    "4th: Kalispell, owned by Kaitlyn Kinsley\n"
    "# PARKED jr54: place-rank gap after Kalispell before Pistol (OCR blank; no surname invent)\n"
    "New York State Bred\n"
    "8th: Pistol, owned by Sandy LaMantia & Joel McElearney & Sandra Ferber Entries: 4\n"
    "3rd: Fox Run Topper, owned by Rick & Mary Thornton"
)
new = (
    "4th: Kalispell, owned by Kaitlyn Kinsley\n"
    "Family Class                                                     Entries: 4\n"
    "1st: North Country Pinnocchio, owned by Norah Risley\n"
    "2nd: Windermere Pistol, owned by Sandy & Joel McElearney\n"
    "3rd: Riverview Calvin, owned by Karen Vernon\n"
    "4th: Fox Run Topper, owned by Rick & Mary Thornton"
)
if old not in text:
    print("MISS kalispell")
else:
    text = text.replace(old, new, 1)
    print("kalispell ok")

after = count_gaps(text.splitlines())
path.write_text(text, encoding="utf-8", newline="\n")
print("file", before, "->", after)
