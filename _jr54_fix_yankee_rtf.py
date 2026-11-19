"""Honest 2001 Yankee fills mirroring Vol II pt1 RTF recoveries."""
from pathlib import Path
import sys

sys.path.insert(0, ".")
from _jr54_strip_place_prefix_junk import count_gaps

path = list(Path("Updated Yearbook Scans").rglob("2001 Yankee_ocr_hqmax.txt"))[0]
text = path.read_text(encoding="utf-8", errors="replace")
before = count_gaps(text.splitlines())


def repl(old: str, new: str, label: str) -> None:
    global text
    if old not in text:
        print("MISS", label)
        return
    c = text.count(old)
    text = text.replace(old, new)
    print(label, "x", c)


repl(
    "1st: Ash Creek Theft, owned by Marylou Cassone\n"
    "# PARKED jr54: place-rank gap after Ash Creek Theft before Foxport Ting (OCR blank 2nd/3rd; no surname invent)\n"
    "4th: Foxport Ting, owned by Sharon Cudd Wirant\n"
    "5th: Northgate Hallie, owned by Doug & Sue Tack\n"
    "6th: Bluestone Sophie, owned by P. Marchetti & J. Guilmain",
    "# PARKED jr54: illegible flat 1st before Farmcliff Tipper (OCR blank; no surname invent)\n"
    "2nd: Farmcliff Tipper, owned by Bob & Genie Franklin\n"
    "3rd: Ash Creek Theft, owned by Marylou Cassone\n"
    "4th: Foxport Ting, owned by Sharon Cudd Wirant\n"
    "5th: Bluestone Sophie, owned by P. Marchetti & J. Guilmain\n"
    "6th: Northgate Hallie, owned by Doug & Sue Tack",
    "ash_flat",
)

repl(
    "1st: Skyline Orchard Sir Maximillion, owned by Karen Howard\n"
    "# PARKED jr54: place-rank gap after Skyline Orchard Sir Maximillion before White Gate Dodger (OCR blank 2nd/3rd; no surname invent)\n"
    "4th: White Gate Dodger, owned by Anne Ritter\n"
    "Pups, 9 up to 12 months, 10 up to 1212\" Entries: 3",
    "1st: Skyline Orchard Sir Maximillion, owned by Karen Howard\n"
    "2nd: Farmcliff Joe, owned by Bob & Genie Franklin\n"
    "3rd: Farmcliff George, owned by Bob & Genie Franklin\n"
    "4th: White Gate Dodger, owned by Anne Ritter\n"
    "5th: Hines Hill Carlton, owned by Sherri Leatherman\n"
    "Pups, 9 up to 12 months, 10 up to 1212\" Entries: 3",
    "max_joe",
)

# Veteran dog: Hines Hill Carlton 2nd -> Ash Creek 4th; RTF has Farmcliff Joe as 3rd
repl(
    "2nd: Hines Hill Carlton, owned by Sherri Leatherman\n"
    "# PARKED jr54: place-rank gap after Hines Hill Carlton before Ash Creek Theft (OCR blank; no surname invent)\n"
    "4th: Ash Creek Theft, owned by Marylou Cassone\n"
    "5th: Skyline Orichard Sir Maximillion, owned by Karen Howard",
    "2nd: Hines Hill Carlton, owned by Sherri Leatherman\n"
    "3rd: Farmcliff Joe, owned by Bob & Genie Franklin\n"
    "4th: Ash Creek Theft, owned by Marylou Cassone\n"
    "5th: Skyline Orichard Sir Maximillion, owned by Karen Howard",
    "carlton_joe",
)

after = count_gaps(text.splitlines())
path.write_text(text, encoding="utf-8", newline="\n")
print("yankee", before, "->", after)
