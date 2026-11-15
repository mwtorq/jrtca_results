"""2000 Vol II batch5 — Gromit/Kirby, JoJo order, Carley unsmash, page4 flush."""
from pathlib import Path
import sys

sys.path.insert(0, ".")
from _jr54_strip_place_prefix_junk import count_gaps

HQ = Path(r"Updated Yearbook Scans/2000 Yearbook Vol 2/2000 Vol II_ocr_hqmax.txt")
text = HQ.read_text(encoding="utf-8")
n = 0


def repl(old: str, new: str, label: str) -> None:
    global text, n
    c = text.count(old)
    if c == 0:
        print("MISS", label)
        return
    text = text.replace(old, new)
    n += c
    print("OK", label, "x" + str(c))


# Gromit starters: GUID was OCR misread of Kirby (PDF p83 cols)
repl(
    "1st: Pine Meadow Gromit, owned by Dave & Kirstin Barrette\n"
    "2nd: GUID, owned by Katie Fioit\n"
    "5th: Briar Trace Rosie, owned by John & Deb Steele\n"
    "6th:  Meadowlake Josey, owned by Dean & Beth Buchholz\n",
    "1st: Pine Meadow Gromit, owned by Dave & Kirstin Barrette\n"
    "2nd: Megabyte, owned by Brad & Brenda Altman\n"
    "3rd: Rockefeller, owned by Brad & Brenda Altman\n"
    "4th: Kirby, owned by Katie Floit\n"
    "5th: Briar Trace Rosie, owned by John & Deb Steele\n"
    "6th: Meadowlake Josey, owned by Dean & Beth Buchholz\n",
    "Gromit +Megabyte/Rockefeller/Kirby",
)

# JoJo steeplechase pups (PDF flat/steeple order JoJo/Shamu/Kitti/Codi)
repl(
    "1st: Nubbin Ridge JoJo, owned by Dixie Banderman\n"
    "2nd: Foxi Loxi Kitti, owned by Scott & Susan Aeppli\n"
    "5th: Foxi Loxi Codi, owned by Scott & Susan Aeppli\n"
    "6th: Nubbin Ridge Shamu, owned by Dixie Banderman\n",
    "1st: Nubbin Ridge JoJo, owned by Dixie Banderman\n"
    "2nd: Nubbin Ridge Shamu, owned by Dixie Banderman\n"
    "3rd: Foxi Loxi Kitti, owned by Scott & Susan Aeppli\n"
    "4th: Foxi Loxi Codi, owned by Scott & Susan Aeppli\n"
    "5th: Norma Foxy, owned by Marge Meyer\n",
    "JoJo/Shamu/Kitti/Codi rebuild",
)

# Carley racing column unsmash (PNW page 77)
repl(
    "Bitches, 1 yr. & older, 10 up to 1214\" Entries: 1 2nd: Molly, owned by Toni Louison\n"
    "1st: Lickity Split Carley, owned by S. & L. Erb/D. Gough\n"
    "3rd: Foxport Tex, owned by Tooie Crooks\n"
    "Bitches, 1 yr. & older, over 12 1/2-15\" Entries: 0 4th: Simply Skyler, owned by Shawn & Kari Gerdes\n"
    "1st: Forrestar Anisette, owned by Forrest Ann Walling\n",
    "Bitches, 1 yr. & older, 10 up to 12 1/2\" Entries: 1\n"
    "1st: Lickity Split Carley, owned by S. & L. Erb/D. Gough\n"
    "Bitches, 1 yr. & older, over 12 1/2-15\" Entries: 1\n"
    "1st: Forrestar Anisette, owned by Forrest Ann Walling\n",
    "Carley/Forrestar unsmash",
)

# Page4 Kelly is Novice Puppy continuation — flush Bred-by Aspen/Rumble false gap
repl(
    "Hi-Bid Spring Fling\n"
    "--- page 4 ---\n"
    "--- column LEFT ---\n"
    "4th: Tymawr Kelly, owned by John Meany\n"
    "5th: Thistledown Carlie, owned by Sandy Brown\n",
    "Hi-Bid Spring Fling\n"
    "--- page 4 ---\n"
    "--- column LEFT ---\n"
    "Novice Puppy Entries: 13\n"
    "4th: Tymawr Kelly, owned by John Meany\n"
    "5th: Thistledown Carlie, owned by Sandy Brown\n",
    "Kelly Novice Puppy header flush",
)

# Suenami → Stretch cross-page: insert racing header flush if present
repl(
    "2nd: Suenami, owned by Cheryl Hart\n"
    "Crossewinds IT\n"
    "--- page 19 ---\n"
    "4th: R.A. Stretch, owned by Rhonda Vega Carson 12 1/2-15\"\n",
    "2nd: Suenami, owned by Cheryl Hart\n"
    "Crossewinds II\n"
    "--- page 19 ---\n"
    "Dogs, 1 yr. & older, over 12 1/2-15\" Entries: 12\n"
    "4th: R.A. Stretch, owned by Rhonda Vega Carson\n",
    "Suenami/Stretch page flush",
)

# Rebound → Phantom trial boundary flush
repl(
    "1st: Kress Country Rebound, owned by Sharon Kress\n"
    "Paumanok Terrier Trial\n"
    "--- page 28 ---\n"
    "4th: Muscle Russell Phantom, owned by Jill Goodman\n",
    "1st: Kress Country Rebound, owned by Sharon Kress\n"
    "Paumanok Terrier Trial\n"
    "--- page 28 ---\n"
    "Championship Certificate, 12 1/2 up to 15\" Entries: 14\n"
    "4th: Muscle Russell Phantom, owned by Jill Goodman\n",
    "Rebound/Phantom trial flush",
)

HQ.write_text(text, encoding="utf-8")
print("applied", n)
print("gaps", count_gaps(text.splitlines()))
