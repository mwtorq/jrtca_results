"""2001 Vol III pt2 batch1 — 9th→6th already applied; Lucy Bear, Kelty, Agility II Gunner."""
from pathlib import Path
import sys

sys.path.insert(0, ".")
from _jr54_strip_place_prefix_junk import count_gaps

HQ = Path(r"Updated Yearbook Scans/2001 Yearbook Vol 3/2001 Vol III pt 2_ocr_hqmax.txt")
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


# Novice Adult: Lucy Bear 3rd (PDF p1)
repl(
    "2nd: Broken Ridge Snoopy Bear, owned by Kyle & Teresa Morrison\n"
    "4th: Jaque Barker, owned by Rebecca Barker\n",
    "2nd: Broken Ridge Snoopy Bear, owned by Kyle & Teresa Morrison\n"
    "3rd: Broken Ridge Lucy Bear, owned by Kyle & Teresa Morrison\n"
    "4th: Jaque Barker, owned by Rebecca Barker\n",
    "Snoopy +Lucy Bear 3rd",
)

# Bitch over r/br: Kelty 4th / Brook 5th (PDF p4)
repl(
    "3rd: Fox Island Sasha, owned by Zack & Tracy Waite\n"
    "5th: Ash Creek Kelty, owned by Marty & Teresa Gottlieb\n"
    "5th: Westwood Brook, owned by Arlan & Linda van Doorn\n",
    "3rd: Fox Island Sasha, owned by Zack & Tracy Waite\n"
    "4th: Ash Creek Kelty, owned by Marty & Teresa Gottlieb\n"
    "5th: Westwood Brook, owned by Arlan & Linda van Doorn\n",
    "Sasha Kelty 4th / Brook 5th",
)

# Agility II over: Gunner 4 / Wedge 5 / Hopalong 6 (PDF p5)
repl(
    "3rd: Pine Creek Little Nemo, owned by Rhonda Rebhorn\n"
    "5th: Wolf Paw Gunner, owned by Dean & Beth Buchholz\n"
    "5th: Wedge, owned by Jen Rochedieu\n"
    "5th: Shady Pine Hopalong, owned by Candy Comell\n",
    "3rd: Pine Creek Little Nemo, owned by Rhonda Rebhorn\n"
    "4th: Wolf Paw Gunner, owned by Dean & Beth Buchholz\n"
    "5th: Wedge, owned by Jen Rochedieu\n"
    "6th: Shady Pine Hopalong, owned by Candy Cornell\n",
    "Agility II Nemo Gunner ranks",
)

HQ.write_text(text, encoding="utf-8")
n1 = count_gaps(HQ.read_text(encoding="utf-8").splitlines())
print("replacements", n, "gaps", n0, "->", n1)
