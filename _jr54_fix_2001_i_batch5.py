"""2001 Vol I batch5 — Ike/Jack/Kolby, Lucy Lou, Snapdragon 4th, Beezer ranks, Calumet 3rd."""
from pathlib import Path
import sys

sys.path.insert(0, ".")
from _jr54_strip_place_prefix_junk import count_gaps

HQ = Path(r"Updated Yearbook Scans/2001 Yearbook Vol 1/2001 Vol I_ocr_hqmax.txt")
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


# Dog pups 6-9 smooth: Ike / Jack / Kolby (PDF p70; HQ mislabeled 4-6mo)
repl(
    "Dog Pups, 4 up fo 6 months, smooth Entries: 2\n"
    "1st: Ike, owned by Jay & Amy Crutchfield\n"
    "--- column RIGHT ---\n"
    "3rd: Seven Springs Kolby, owned by Karen Uswald\n",
    "Dog Pups, 6 up to 9 months, smooth Entries: 3\n"
    "1st: Ike, owned by Jay & Amy Crutchfield\n"
    "2nd: Jack, owned by Bettyann Senf\n"
    "3rd: Seven Springs Kolby, owned by Karen Oswald\n",
    "Ike+Jack+Kolby 6-9 smooth",
)

# Bitch pups 6-9 r/br: Lucy Lou 4th between Sally and Tailor (PDF p70)
repl(
    "3rd: Silver Valley Sally, owned by Richard & Rebecca Paff\n"
    "5th: Cason's Quarters Tailor Made, owned by P. & P. McConville\n"
    "6th: Mountain Legends Hannah, owned by Carol Voyles\n",
    "3rd: Silver Valley Sally, owned by Richard & Rebecca Paff\n"
    "4th: Lucy Lou, owned by Josie Nicoletta\n"
    "5th: Cason's Quarters Tailor Made, owned by P. & P. McConville\n"
    "6th: Mountain Legends Hannah, owned by Carol Voyles\n",
    "Sally +Lucy Lou 4th",
)

# Pre-Novice: Snapdragon is 4th not 5th (PDF p82)
repl(
    "3rd: Russell's Jack \"RJ\", owned by Sylvia Reams\n"
    "5th: Terier-ific Snapdragon, owned by Kim & Nixy Morales\n",
    "3rd: Russell's Jack \"RJ\", owned by Sylvia Reams\n"
    "4th: Terrier-ific Snapdragon, owned by Kim & Nixy Morales\n",
    "RJ +Snapdragon 4th",
)

# Novice Adult: Snaffles 4 / Foxster 5 / Hooha 6 (PDF p82)
repl(
    "3rd: Beezer, owned by Diana Amador\n"
    "5th: Badakashan Snaffles, owned by Rhonda Vega & Larry Carson\n"
    "5th: Oaks Edge Foxster, owned by George Riley\n"
    "5th: J. B.s Hooha, owned by Joanne Bates\n",
    "3rd: Beezer, owned by Diana Amador\n"
    "4th: Badakashan Snaffles, owned by Rhonda Vega & Larry Carson\n"
    "5th: Oaks Edge Foxster, owned by George Riley\n"
    "6th: J. B.s Hooha, owned by Joanne Bates\n",
    "Beezer Snaffles/Foxster/Hooha ranks",
)

# Dogs 10-12.5 smooth: Calumet is 3rd (bogus BBE header smashed in) (PDF p90)
repl(
    "1st: Circle G Rush, owned by Jill Peikert\n"
    "2nd: Button Top Devil, owned by Flo Clark\n"
    "Bred by Exhibitor Dog                                       Entries: 0\n"
    "1st: Com Row Calumet, owned by L. M. Measles & P. Brock\n"
    "4th: Bright Stars Coco Pop, owned by Nancy Lundmark\n"
    "5th: Roxie, owned by David Buckholts\n",
    "1st: Circle G Rush, owned by Jill Peikert\n"
    "2nd: Button Top Devil, owned by Flo Clark\n"
    "3rd: Corn Row Calumet, owned by L. M. Measles & P. Brock\n"
    "4th: Bright Stars Coco Pop, owned by Nancy Lundmark\n"
    "5th: Roxie, owned by David Buckholts\n",
    "Calumet 3rd unsmash BBE",
)

HQ.write_text(text, encoding="utf-8")
n1 = count_gaps(HQ.read_text(encoding="utf-8").splitlines())
print("replacements", n, "gaps", n0, "->", n1)
