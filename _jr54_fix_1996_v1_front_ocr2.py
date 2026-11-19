"""Honest 1996 Vol1 pg61-110 front fills batch 2 from PDF OCR."""
from pathlib import Path
import sys

sys.path.insert(0, ".")
from _jr54_strip_place_prefix_junk import count_gaps

path = list(Path("Updated Yearbook Scans").rglob("1996 Vol 1 pg 61-110 front_ocr_hqmax.txt"))[0]
text = path.read_text(encoding="utf-8", errors="replace")
before = count_gaps(text.splitlines())


def repl(old: str, new: str, label: str) -> None:
    global text
    if old not in text:
        print("MISS", label)
        return
    text = text.replace(old, new, 1)
    print(label, "ok")


repl(
    "2nd: Frisbee, owned by Dawn Pierson\n"
    "# PARKED jr54: place-rank gap after Frisbee before Petey (OCR blank; no surname invent)\n"
    "4th: Petey, owned by Kathy Hunter",
    "2nd: Frisbee, owned by Dawn Pierson\n"
    "3rd: Twiggy, owned by Diana Schwab\n"
    "4th: Petey, owned by Kathy Hunter",
    "twiggy3",
)

repl(
    "1st: Sarah Harsh\n"
    "# PARKED jr54: place-rank gap after Sarah Harsh before Luke Hitt (OCR blank; no surname invent)\n"
    "3rd: Luke Hitt",
    "1st: Sarah Harsh\n"
    "2nd: Bobby Duty, Ill\n"
    "3rd: Luke Hitt",
    "bobby2",
)

repl(
    "1st: Camelot Derby of Marksworth, owned by Terry Clower\n"
    "# PARKED jr54: place-rank gap after Camelot Derby before Whirlwind Polo (OCR blank; no surname invent)\n"
    "3rd: Whirlwind Polo, owned by Terry Wellman",
    "1st: Camelot Derby of Marksworth, owned by Terry Clower\n"
    "2nd: Farmcliff Fred of Fox Tale, owned by Bjorkland & Staten\n"
    "3rd: Whirlwind Polo, owned by Terry Wellman",
    "fred2",
)

repl(
    "3rd: Will-O-Moor Rex, owned by Kim Wentz\n"
    "# PARKED jr54: place-rank gap after Will-O-Moor Rex before Arlins Troy Built Riley (OCR blank; no surname invent)\n"
    "5th: Arlins Troy Built Riley, owned by Alison Linstrum",
    "3rd: Will-O-Moor Rex, owned by Kim Wentz\n"
    "4th: Arlins Troy Built Riley, owned by Alison Linstrum",
    "arlins4",
)

repl(
    "1st: Farmcliff Sugar, owned by Bob Franklin\n"
    "# PARKED jr54: place-rank gap after Farmcliff Sugar before Farmcliff Becky (OCR blank; no surname invent)\n"
    "3rd: Farmcliff Becky, owned by Bob Franklin",
    "1st: Farmcliff Sugar, owned by Bob Franklin\n"
    "2nd: Fox Run Chant, owned by Doug Tack\n"
    "3rd: Farmcliff Becky, owned by Bob Franklin",
    "chant2",
)

after = count_gaps(text.splitlines())
path.write_text(text, encoding="utf-8", newline="\n")
print("file", before, "->", after)
