"""Honest 1996 Vol II pg163-220 front fills from fresh PDF OCR."""
from pathlib import Path
import sys

sys.path.insert(0, ".")
from _jr54_strip_place_prefix_junk import count_gaps

path = list(Path("Updated Yearbook Scans").rglob("1996 Vol II pg 163-220 front_ocr_hqmax.txt"))[0]
text = path.read_text(encoding="utf-8", errors="replace")
before = count_gaps(text.splitlines())


def repl(old: str, new: str, label: str) -> None:
    global text
    if old not in text:
        print("MISS", label)
        return
    text = text.replace(old, new, 1)
    print(label, "ok")


# Smash 1st line was Whip+others; OCR sequence Patch/Whip/Echo/Jet
repl(
    "1st: High Keswick North Mountain 4 Country up Whip, owned by Sandy\n"
    "# PARKED jr54: place-rank gap after High Keswick North Mountain 4 Country up before Farmstead Jet (OCR blank; no surname invent)\n"
    "4th: Farmstead Jet, owned by Judy Galterio\n"
    "5th: Farmstead Rocket, owned by Judy Galterio\n"
    "6th: Desert Fox Jerry Garcia, owned by T. Decker",
    "1st: North Country Patch, owned by Norah Risley\n"
    "2nd: Keswick Whip, owned by Sandy McElerney\n"
    "3rd: High Mountain Echo, owned by Allison Linstrum\n"
    "4th: Farmstead Jet, owned by Judy Galterio\n"
    "5th: Farmstead Rocket, owned by Judy Galterio\n"
    "6th: Desert Fox Jerry Garcia, owned by T. Decker",
    "whip",
)

# Itch -> Kismit: Farmstead Jazz is 3rd
repl(
    "2nd: Farmstead Keswick Itch, owned by Sandy Judy\n"
    "# PARKED jr54: place-rank gap after Farmstead Keswick Itch before Hillside Kismit (OCR blank; no surname invent)\n"
    "4th: Hillside Kismit, owned by Laura Harakaly",
    "2nd: Keswick Itch, owned by Sandy & Joel McElerney\n"
    "3rd: Farmstead Jazz, owned by Judy Galterio\n"
    "4th: Hillside Kismit, owned by Laura Harakaly",
    "jazz3",
)

# Moonrunner Courtland smash -> Courtland 3rd + Moonrunner Keeper 4th
repl(
    "2nd: Evergreen Gimel, owned by George Ridler\n"
    "3rd: Moonrunner Courtland My Keeper, owned by Joseph Clay Ackerman\n"
    "# PARKED jr54: place-rank gap after Moonrunner Courtland My Keeper before Violet (OCR blank; no surname invent)\n"
    "5th: Violet, owned by Joan Valuzzo & William Bisch",
    "2nd: Evergreen Gimel, owned by George Ridler\n"
    "3rd: Courtland My Girl, owned by Joseph Jankowski & Kellyann Morander\n"
    "4th: Moonrunner Keeper, owned by Clay Ackerman\n"
    "5th: Violet, owned by Joan Valuzzo & William Bisch",
    "moon_split",
)

after = count_gaps(text.splitlines())
path.write_text(text, encoding="utf-8", newline="\n")
print("file", before, "->", after)
