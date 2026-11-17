"""2001 Vol III pt1 batch4 — clean glued ranks + Jasper/Puck + Hutch + Sugar + youth GTG."""
from pathlib import Path
import sys

sys.path.insert(0, ".")
from _jr54_strip_place_prefix_junk import count_gaps

HQ = Path(r"Updated Yearbook Scans/2001 Yearbook Vol 3/2001 Vol III pt 1_ocr_hqmax.txt")
text = HQ.read_text(encoding="utf-8")
n0 = count_gaps(text.splitlines())
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


# Youth GTG: unglue Christine Roth / Patrick Fitzgerald (PDF p4)
repl(
    "1st:      Ben Lavender\n"
    "2nd: Eleanor Bramwell\n"
    "--- column RIGHT ---\n"
    "3rd: Christine Rothth: Patrick Fitzgerald\n"
    "Youth Handling Agility, On Lead Entries: 4\n"
    "1st: Faithful Impulse\n"
    "2nd: Ben Lavender\n"
    "--- page 5 ---\n"
    "--- column LEFT ---\n"
    "5th: Sweetgrass Dinah, owned by Wendy Schmaltz\n"
    "6th: Mac's/Jacks Mara, owned by Bob MacFarland\n",
    "1st: Ben Lavender\n"
    "2nd: Eleanor Bramwell\n"
    "3rd: Christine Roth\n"
    "4th: Patrick Fitzgerald\n"
    "Youth Handling Agility, On Lead Entries: 4\n"
    "1st: Faithful Impulse\n"
    "2nd: Ben Lavender\n"
    "--- page 5 ---\n"
    "--- column LEFT ---\n"
    "5th: Sweetgrass Dinah, owned by Wendy Schmaltz\n"
    "6th: Mac's/Jacks Mara, owned by Bob MacFarland\n",
    "Youth GTG Roth/Fitzgerald (+Dinah still orphan)",
)

# Cert 10-12.5: clean Farmcliff Becky 4th so place_re matches
repl(
    "3rd: Kenswick Kayla, owned by Joel & Sandy McEleamey\n"
    "4th:~-Farmcliff: Becky, owned by Joe MAcCoy\n"
    "5th: Jack, owned by Bettyann Senf\n",
    "3rd: Kenswick Kayla, owned by Joel & Sandy McEleamey\n"
    "4th: Farmcliff Becky, owned by Joe McCoy\n"
    "5th: Jack, owned by Bettyann Senf\n",
    "Kayla Becky 4th clean",
)

# Steeple pups page62: Jasper/Puck/Pearl order (PDF p62)
repl(
    "3rd: Winn Creek Jasper, owned by Tom Collmar\n"
    "5th: Blue Dome Gimel, owned by George Ridler\n"
    "4th: The Folly Puck, owned by Rick & Mary Thomton\n"
    "Veteran Dogs, 6 years & older, 10 up to 12 1/2\" Entries: 5\n"
    "1st: Stone's Throw Griffey, owned by Karen Merriman\n"
    "5th: Winn Creek Pearl, owned by Tom Collmar\n"
    "6th: Sow's Ear Mascara, owned by Twila Decker\n",
    "3rd: Winn Creek Jasper, owned by Tom Collmar\n"
    "4th: The Folly Puck, owned by Rick & Mary Thornton\n"
    "5th: Winn Creek Pearl, owned by Tom Collmar\n"
    "6th: Sow's Ear Mascara, owned by Twila Decker\n",
    "Jasper/Puck/Pearl steeple unsmash",
)

# Dogs 10-12.5: Hutch is 4th not 3rd (PDF p62)
repl(
    "1st: Sow's Ear Taltos, owned by Twila Decker\n"
    "2nd: Charade Beaumont, owned by Tom Collmar\n"
    "3rd: >=~=Famneliff: Hutchy, owned by:Dave & Marti' McMahori\n"
    "5th: Arlins My Ty, owned by Michael Beach\n"
    "6th: The Folly Fitzpatrick, owned by Pat Sullivan\n",
    "1st: Sow's Ear Taltos, owned by Twila Decker\n"
    "2nd: Charade Beaumont, owned by Tom Collmar\n"
    "4th: Farmcliff Hutch, owned by Dave & Marti McMahon\n"
    "5th: Arlins My Ty, owned by Michael Beach\n"
    "6th: The Folly Fitzpatrick, owned by Pat Sullivan\n",
    "Beaumont Hutch 4th (3rd unscanned)",
)

# Vet bitches: Sugar 3rd clean (PDF p62)
repl(
    "1st: Lost Acres Revion, owned by Karen one\n"
    "2nd: A�Srd:~Farmcliff Sugar, owned by Karin'Franklin\n"
    "4th: Briarpatch Ember, owned by Doug & Noreen Loranger\n",
    "1st: Lost Acres Revion, owned by Karen McCarthy\n"
    "3rd: Farmcliff Sugar, owned by Karin Franklin\n"
    "4th: Briarpatch Ember, owned by Doug & Noreen Loranger\n",
    "Revion Sugar 3rd clean",
)

# Agility I Tomba: missing 2nd (PDF p62) — leave gap but clean if OCR has nothing
# Open Puppy Ripley: 3rd missing — park

# Bitches Teeni: 4th unscanned between Teeni and Banjo — park

# Max/Olive class: insert 1st Farmcliff Peggy if missing
repl(
    "Pups, 9 up to 12 months, over 12 1/2-15\" Entries: 5\n"
    "2nd: Skyline Orchard Sir Max, owned by Karen Howard\n"
    "3rd: Farmcliff George, owned by Bob & Genie Franklin\n"
    "4th: Farmcliff Joe, owned by Bob & Genie Franklin\n"
    "5th: Oakwood Olive, owned by David & Shannon Rice\n",
    "Pups, 9 up to 12 months, over 12 1/2-15\" Entries: 5\n"
    "1st: Farmcliff Peggy, owned by Bob & Genie Franklin\n"
    "2nd: Skyline Orchard Sir Max, owned by Karen Howard\n"
    "3rd: Farmcliff Joe, owned by Bob & Genie Franklin\n"
    "4th: Farmcliff George, owned by Bob & Genie Franklin\n"
    "5th: Oakwood Olive, owned by David & Shannon Rice\n",
    "Max class +Peggy reorder Joe/George",
)

HQ.write_text(text, encoding="utf-8")
n1 = count_gaps(HQ.read_text(encoding="utf-8").splitlines())
print("replacements", n, "gaps", n0, "->", n1)
