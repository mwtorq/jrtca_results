"""Honest 1996 Vol1 pg61-110 front fills from fresh PDF OCR."""
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
    "3rd: Three Oaks Double D of Bili Brook, owned by Billy Shores\n"
    "# PARKED jr54: place-rank gap after Three Oaks Double D before Turbo (OCR blank; no surname invent)\n"
    "5th: Turbo of Ball Creek, owned by Ronnie & Wanda Dyer",
    "3rd: Three Oaks Double D of Bili Brook, owned by Billy Shores\n"
    "4th: Windermere Cy, owned by Glen & Judy Kendrick\n"
    "5th: Turbo of Ball Creek, owned by Ronnie & Wanda Dyer",
    "cy4",
)

repl(
    "2nd: Trix, owned by Richard Stephenson\n"
    "# PARKED jr54: Three Oaks / Sukhoi place smash before Sadie (OCR glue; blank 4th; no surname invent)\n"
    "5th: Sadie, owned by Chris Advani",
    "2nd: Trix, owned by Richard Stephenson\n"
    "3rd: Three Oaks Sukhoi of Good Times, owned by Steve Spruill\n"
    "4th: Sadie, owned by Christine Fraley",
    "sukhoi3",
)

after = count_gaps(text.splitlines())
path.write_text(text, encoding="utf-8", newline="\n")
print("file", before, "->", after)
