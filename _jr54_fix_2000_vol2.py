"""Honest 2000 Vol II fills from 15-48 / 49-86.txt."""
from pathlib import Path
import sys

sys.path.insert(0, ".")
from _jr54_strip_place_prefix_junk import count_gaps

path = list(Path("Updated Yearbook Scans").rglob("2000 Vol II_ocr_hqmax.txt"))[0]
text = path.read_text(encoding="utf-8", errors="replace")
before = count_gaps(text.splitlines())

reps = [
    (
        "hutch_tackle",
        "1st: Farmcliff Hutch, owned by Dave McMahon\n"
        "# PARKED jr54: place-rank gap after Farmcliff Hutch before Hunter's Green Stokes (OCR blank; no surname invent)\n"
        "3rd: Hunter's Green Stokes, owned by Antonio Sullo\n"
        "4th: North Country Petey, owned by Marylou Mogrovejo",
        "1st: Farmcliff Hutch, owned by Dave McMahon\n"
        "2nd: Farmcliff Tackle, owned by Megan Johnson\n"
        "3rd: Hunter's Green Stokes, owned by Antonio Sullo\n"
        "4th: North Country Petey, owned by Marylou Mogrovejo",
    ),
    (
        "dudley",
        "1st: Sow's Ear Solitaire, owned by Karen McCarthy\n"
        "2nd: Round the Bend Dudley, owned by Carol Watson\n"
        "# PARKED jr54: place-rank gap after Round the Bend Dudley before Muscle Russell Hustle (OCR blank; no surname invent)\n"
        "4th: Muscle Russell Hustle, owned by Rick Thornton\n"
        "5th: Northgate Hank, owned by Bob Franklin",
        "1st: Round the Bend Dudley, owned by Carol Watson\n"
        "2nd: Muscle Russell Hustle, owned by Rick Thornton\n"
        "3rd: Sow's Ear Solitaire, owned by Karen McCarthy\n"
        "4th: Long Hope Risley, owned by B. Franklin & Nellie Niewola\n"
        "5th: Northgate Hank, owned by Bob Franklin",
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
