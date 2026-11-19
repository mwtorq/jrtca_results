"""Honest 2001 Vol III pt2 fills from yearbook txt / National OCR."""
from pathlib import Path
import sys

sys.path.insert(0, ".")
from _jr54_strip_place_prefix_junk import count_gaps

path = list(Path("Updated Yearbook Scans").rglob("2001 Vol III pt 2_ocr_hqmax.txt"))[0]
text = path.read_text(encoding="utf-8", errors="replace")
before = count_gaps(text.splitlines())

reps = [
    (
        "bearette_fiddle",
        "2nd: The Larches Bearette, owned by Rick & Mary Thornton\n"
        "# PARKED jr54: place-rank gap after The Larches Bearette before Leewinds Sadie (OCR blank; no surname invent)\n"
        "4th: Leewinds Sadie, owned by Margaret Strickler",
        "2nd: The Larches Bearette, owned by Rick & Mary Thornton\n"
        "3rd: Highwater Fiddle, owned by Bob Franklin\n"
        "4th: Leewinds Sadie, owned by Margaret Strickler",
    ),
    (
        "bearette_fiddle2",
        "2nd: The Larches Bearette, owned by Rick & Mary Thomton\n"
        "# PARKED jr54: place-rank gap after The Larches Bearette before Leewinds Sadie (OCR blank; no surname invent)\n"
        "4th:  Leewinds Sadie, owned by Margaret Strickler",
        "2nd: The Larches Bearette, owned by Rick & Mary Thomton\n"
        "3rd: Highwater Fiddle, owned by Bob Franklin\n"
        "4th: Leewinds Sadie, owned by Margaret Strickler",
    ),
    (
        "bearette_fiddle3",
        "2nd: The Larches Bearette, owned by Rick & Mary\n"
        "# PARKED jr54: place-rank gap after The Larches Bearette before Leewinds Sadie (OCR blank; no surname invent)\n"
        "4th:  Leewinds Sadie, owned by Margaret Strickler",
        "2nd: The Larches Bearette, owned by Rick & Mary Thornton\n"
        "3rd: Highwater Fiddle, owned by Bob Franklin\n"
        "4th: Leewinds Sadie, owned by Margaret Strickler",
    ),
    (
        "dabble",
        "2nd: Orchard Hill Dabble, owned by Cheryl Robson\n"
        "# PARKED jr54: place-rank gap after Orchard Hill Dabble before Tippycanoe Storm (OCR blank; no surname invent)\n"
        "5th: Tippycanoe Storm, owned by Barbara Tyler",
        "2nd: Orchard Hill Dabble, owned by Cheryl Robson\n"
        "3rd: Troon Quarry Outlaw, owned by Sue & Elizabeth Murphree\n"
        "4th: Farmstead Puzzle, owned by Judy Galterio\n"
        "5th: Tippycanoe Storm, owned by Barbara Tyler",
    ),
    (
        "carley_annie",
        "2nd: Bent Creek Carley, owned by Marc & Laura Cormier\n"
        "# PARKED jr54: place-rank gap after Bent Creek Carley before Old Glory Priscilla (OCR blank; no surname invent)\n"
        "4th: Old Glory Priscilla, owned by Pat Combs",
        "2nd: Bent Creek Carley, owned by Marc & Laura Cormier\n"
        "3rd: Big Sky Annie, owned by Doug & Sue Tack\n"
        "4th: Old Glory Priscilla, owned by Pat Combs",
    ),
    (
        "maddy_spencer",
        "1st: Fox Chase Maddy, owned by Linda Knowles\n"
        "# PARKED jr54: place-rank gap after Fox Chase Maddy before BayBriar Penelopy (OCR blank; no surname invent)\n"
        "3rd: BayBriar Penelopy, owned by David & Jeannette Hutchison",
        "1st: Fox Chase Maddy, owned by Linda Knowles\n"
        "2nd: Farmcliff Spencer, owned by Bob & Genie Franklin\n"
        "3rd: BayBriar Penelopy, owned by David & Jeannette Hutchison",
    ),
    (
        "hutch_fitz",
        "1st: Northgate Hale, owned by Doug & Sue Tack\n"
        "2nd: Farmcliff Hutch, owned by Dave & Marti McMahon\n"
        "# PARKED jr54: place-rank gap after Farmcliff Hutch before Arlins My Ty (OCR blank; no surname invent)\n"
        "4th: Arlins My Ty, owned by Michael Beach",
        "1st: Northgate Hale, owned by Doug & Sue Tack\n"
        "2nd: Farmcliff Hutch, owned by Dave & Marti McMahon\n"
        "3rd: Farmcliff Spencer, owned by Bob & Genie Franklin\n"
        "4th: Arlins My Ty, owned by Michael Beach",
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
