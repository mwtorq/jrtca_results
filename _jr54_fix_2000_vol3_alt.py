"""Honest fills for 2000 vol 3 pt 1 (alt) from 19 to 64.txt."""
from pathlib import Path
import sys

sys.path.insert(0, ".")
from _jr54_strip_place_prefix_junk import count_gaps

path = list(Path("Updated Yearbook Scans").rglob("2000 vol 3 pt 1_ocr_hqmax.txt"))[0]
text = path.read_text(encoding="utf-8", errors="replace")
before = count_gaps(text.splitlines())

reps = [
    (
        "rooter",
        "2nd: Foxlsland Grit, owned by Dan Grimmel\n"
        "3rd: Couriwood Rooter, owned by Debbie & Rusty Graydon\n"
        "# PARKED jr54: place-rank gap after Couriwood Rooter before Easton Point Nipper (OCR blank; no surname invent)\n"
        "5th: Easton Point Nipper, owned by Sally Gay",
        "2nd: Fox Island Grit, owned by Dan Grimmel\n"
        "3rd: Courtwood Rooter, owned by Debbie & Rusty Graydon\n"
        "4th: Kingsway Rascal, owned by Jan DeWinter\n"
        "5th: Easton Point Nipper, owned by Sally Gay",
    ),
    (
        "badger",
        "Championship Certificate, 10 up to 121,\" Entries: 10\n"
        "1st: Will-O-Moor Badger, owned by Scott Whittington\n"
        "# PARKED jr54: place-rank gap after Will-O-Moor Badger before Munchkin (OCR blank; no surname invent)\n"
        "3rd: Munchkin, owned by Melissa Lowe\n"
        "4th: Takonta, owned by Eric Bartlett\n"
        "5th: Pork-chopp, owned by Kevin & Shannon Osby\n"
        "Champion: Winslow Genevieve, owned by Lisa Fitzgerald",
        "Championship Certificate, 10 up to 12 1/2\" Entries: 10\n"
        "Champion: Winslow Genevieve, owned by Lisa Fitzgerald\n"
        "Reserve: Spaz, owned by Melissa Lowe\n"
        "3rd: Munchkin, owned by Melissa Lowe\n"
        "4th: Takonta, owned by Eric Bartlett\n"
        "5th: Pork-chopp, owned by Kevin & Shannon Osby\n"
        "6th: Will-O-Moor Badger, owned by Scott Whittington",
    ),
    (
        "josie",
        "3rd: Treesbank Josie, owned by Carmen & Patricia Tosto\n"
        "# PARKED jr54: place-rank gap after Treesbank Josie before Foxton Locks Annie (OCR blank; no surname invent)\n"
        "5th: Foxton Locks Annie, owned by Jo Paddison",
        "3rd: Treesbank Josie, owned by Carmen & Patricia Tosto\n"
        "4th: Cotswold Rio, owned by Jo Paddison\n"
        "5th: Foxton Locks Annie, owned by Jo Paddison",
    ),
    (
        "gainsborough",
        "3rd: Wootinhille Gainsborough, owned by Phil & Sue Hawkir\n"
        "# PARKED jr54: place-rank gap after Wootinhille Gainsborough before PointofView Ambush (OCR blank 4th/5th; no surname invent)\n"
        "6th: PointofView Ambush, owned by Mary Stevens",
        "3rd: Wootinhille Gainsborough, owned by Phil & Sue Hawkins\n"
        "4th: Fox Run Red, owned by Michelle Ward\n"
        "5th: PointofView Ambush, owned by Mary Stevens",
    ),
]

for label, old, new in reps:
    n = text.count(old)
    if n == 0:
        print("MISS", label)
        continue
    text = text.replace(old, new)
    print(label, "x", n)

after = count_gaps(text.splitlines())
path.write_text(text, encoding="utf-8", newline="\n")
print("file", before, "->", after)
