"""Honest 2001 Vol II pt1 fills from Yearbook Scans RTF/txt + duplicate page."""
from pathlib import Path
import sys

sys.path.insert(0, ".")
from _jr54_strip_place_prefix_junk import count_gaps

ROOT = Path("Updated Yearbook Scans")
path = list(ROOT.rglob("2001 Vol II pt 1_ocr_hqmax.txt"))[0]
text = path.read_text(encoding="utf-8", errors="replace")
before = count_gaps(text.splitlines())


def repl(old: str, new: str, label: str, n: int = 0) -> None:
    global text
    c = text.count(old) if n == 0 else min(n, text.count(old))
    if c == 0:
        print("MISS", label)
        return
    text = text.replace(old, new, c if n == 0 else n)
    print(label, "x", c if n == 0 else n)


# Maggie page-break: recover 3rd-5th from duplicate page-55 copy
repl(
    "2nd: Maggie, owned by Jeff Arceneaux\n"
    "# PARKED jr54: place-rank gap after Maggie before Star Catcher Roxy (page-break smash; OCR blank 3rd-5th; no surname invent)\n"
    "SWIRTN Spring 2001\n"
    "--- page 17 ---\n"
    "--- column LEFT ---\n"
    "6th: Star Catcher Roxy, owned by Lupe & Angela Saldivar",
    "2nd: Maggie, owned by Jeff Arceneaux\n"
    "SWIRTN Spring 2001\n"
    "--- page 17 ---\n"
    "--- column LEFT ---\n"
    "3rd: Circle G Chloe, owned by Jill Peikert\n"
    "4th: Star Catcher Roxy, owned by Lupe & Angela Saldivar\n"
    "5th: Roxy, owned by Page King",
    "maggie",
)

# Flat pups Ash Creek block (both copies): Tipper 2nd, Ash Creek 3rd per RTF
repl(
    "Pups, 6 up to 9 months, 10 up to 12 1/2\".\" Entries: 6\n"
    "1st: Ash Creek Theft, owned by Marylou Cassone\n"
    "# PARKED jr54: place-rank gap after Ash Creek Theft before Foxport Ting (OCR blank 2nd/3rd; no surname invent)\n"
    "4th: Foxport Ting, owned by Sharon Cudd Wirant\n"
    "5th: Northgate Hallie, owned by Doug & Sue Tack\n"
    "6th: Bluestone Sophie, owned by P. Marchetti & J. Guilmain",
    "Pups, 6 up to 9 months, 10 up to 12 1/2\".\" Entries: 6\n"
    "# PARKED jr54: illegible flat 1st before Farmcliff Tipper (OCR blank; no surname invent)\n"
    "2nd: Farmcliff Tipper, owned by Bob & Genie Franklin\n"
    "3rd: Ash Creek Theft, owned by Marylou Cassone\n"
    "4th: Foxport Ting, owned by Sharon Cudd Wirant\n"
    "5th: Bluestone Sophie, owned by P. Marchetti & J. Guilmain\n"
    "6th: Northgate Hallie, owned by Doug & Sue Tack",
    "ash_flat",
)

# Steeplechase pups: Ash Creek 2nd -> Tipper 3rd before Foxport 4th (both copies)
repl(
    "1st: Northgate Hallie, owned by Doug & Sue Tack\n"
    "2nd: Ash Creek Theft, owned by Marylou Cassone\n"
    "# PARKED jr54: place-rank gap after Ash Creek Theft before Foxport Ting (OCR blank; no surname invent)\n"
    "4th: Foxport Ting, owned by Sharon Cudd Wirant\n"
    "5th: Blue Stones Sophie, owned by P. Marchetti & J. Guilmain",
    "1st: Northgate Hallie, owned by Doug & Sue Tack\n"
    "2nd: Ash Creek Theft, owned by Marylou Cassone\n"
    "3rd: Farmcliff Tipper, owned by Bob & Genie Franklin\n"
    "4th: Foxport Ting, owned by Sharon Cudd Wirant\n"
    "5th: Blue Stones Sophie, owned by P. Marchetti & J. Guilmain",
    "ash_sc",
)

# Steeplechase Maximillion: 3rd George + 5th Carlton (both copies)
repl(
    "1st: Skyline Orchard Sir Maximillion, owned by Karen Howard\n"
    "2nd: Farmcliff Joe, owned by Bob & Genie Franklin\n"
    "# PARKED jr54: place-rank gap after Farmcliff Joe before White Gate Dodger (OCR blank; no surname invent)\n"
    "4th: White Gate Dodger, owned by Anne Ritter\n"
    "Pups, 9 up to 12 months, 10 up to 12 1/2\" Entries: 3",
    "1st: Skyline Orchard Sir Maximillion, owned by Karen Howard\n"
    "2nd: Farmcliff Joe, owned by Bob & Genie Franklin\n"
    "3rd: Farmcliff George, owned by Bob & Genie Franklin\n"
    "4th: White Gate Dodger, owned by Anne Ritter\n"
    "5th: Hines Hill Carlton, owned by Sherri Leatherman\n"
    "Pups, 9 up to 12 months, 10 up to 12 1/2\" Entries: 3",
    "max_joe",
)

# Maximillion missing 2nd/3rd but already has Carlton 5th (both copies)
repl(
    "1st: Skyline Orchard Sir Maximiliion, owned by Karen Howard\n"
    "# PARKED jr54: place-rank gap after Skyline Orchard Sir Maximiliion before White Gate Dodger (OCR blank 2nd/3rd; no surname invent)\n"
    "4th: White Gate Dodger, owned by Anne Ritter\n"
    "5th: Hines Hill Carlton, owned by Sherri Leatherman",
    "1st: Skyline Orchard Sir Maximiliion, owned by Karen Howard\n"
    "2nd: Farmcliff Joe, owned by Bob & Genie Franklin\n"
    "3rd: Farmcliff George, owned by Bob & Genie Franklin\n"
    "4th: White Gate Dodger, owned by Anne Ritter\n"
    "5th: Hines Hill Carlton, owned by Sherri Leatherman",
    "max_blank23",
)

after = count_gaps(text.splitlines())
path.write_text(text, encoding="utf-8", newline="\n")
print("file gaps", before, "->", after)
