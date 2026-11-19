"""2001 Vol I batch2 — Chewey/Jake cert/Maggie/Jackie VCC/Tipper/Disco (PDF)."""
from pathlib import Path
import sys

sys.path.insert(0, ".")
from _jr54_strip_place_prefix_junk import count_gaps

HQ = Path(r"Updated Yearbook Scans/2001 Yearbook Vol 1/2001 Vol I_ocr_hqmax.txt")
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


# Novice Adult Chewey (Fox Cry PDF p12)
repl(
    "Novice Adult                                                                 Entries: 8\n"
    "1st: Chewey, owned by Melanie Starr\n"
    "2nd: Rock Ridge Cooper Fox, owned by Joanna Godwin\n"
    "5th: 7 Summer Sage, owned by Audie Sumner\n",
    "Novice Adult Entries: 8\n"
    "1st: Chewey, owned by Melanie Starr\n"
    "2nd: Rock Ridge Cooper Fox, owned by Joanna Godwin\n"
    "3rd: Red Hills Brody, owned by Jane Colvin\n"
    "4th: 7 Summer Sage, owned by Audie Sumner\n",
    "Chewey +Brody/Sage",
)

# Championship 12.5-15" (PDF p14) — Jake is 6th not 1st
repl(
    "Championship Certificate, 121: up to 15\" Entries: 12\n"
    "1st: Edison's Pride Jake, owned by John & Judy Tyno\n"
    "3rd: Westside Lucky, owned by Chris & Hana Smith\n"
    "5th: R.A. Russell Trulock, owned by Mike & Lynda Trulock\n"
    "Champion: Fox Cry Hailey Trulock, owned by M. & L. Trulock\n"
    "Reserve: Terrier-ific Wild Child, owned by S. & D. Hopewell\n"
    "5th: R.A. Trixie, owned by John & Judy Tyno\n",
    "Championship Certificate, 12 1/2 up to 15\" Entries: 12\n"
    "Champion: Fox Cry Hailey Trulock, owned by M. & L. Trulock\n"
    "Reserve: Terrier-ific Wild Child, owned by S. & D. Hopewell\n"
    "3rd: Westside Lucky, owned by Chris & Hana Smith\n"
    "4th: R.A. Russell Trulock, owned by Mike & Lynda Trulock\n"
    "5th: R.A. Trixie, owned by John & Judy Tyno\n"
    "6th: Edison's Pride Jake, owned by John & Judy Tyno\n",
    "Jake cert rebuild",
)

# Maggie/Reve bitch pups (PDF p25)
repl(
    "1st: Troon Quarry Ivory, owned by Ward & Renee Skinner\n"
    "2nd: Circle G Chloe, owned by Jill Peikert\n"
    "3rd: 3d: Maggie, owned by Jeff & Cathy Arceneaux\n"
    "5th: Reve, owned by Amy Allen\n"
    "5th: Kingsfield Spinner, owned by Wendy Houtz\n",
    "1st: Troon Quarry Ivory, owned by Ward & Renee Skinner\n"
    "2nd: Circle G Chloe, owned by Jill Peikert\n"
    "3rd: Maggie, owned by Jeff & Cathy Arceneaux\n"
    "4th: Reve, owned by Amy Allen\n"
    "5th: Kingsfield Spinner, owned by Wendy Houtz\n",
    "Maggie/Reve/Spinner",
)

# Jackie VCC (PDF p26)
repl(
    "Veteran Championship Certificate                         Entries: 0\n"
    "1st: Button Top Jackie, owned by Flo Clark\n"
    "3rd: Land's End Nutmeg, owned by Emily Hempel\n"
    "4th: Kensington Baiman, owned by Lisa Richards\n"
    "5th: Kinsington Devonshire Sno-patch, owned by Teresa King\n"
    "Champion: Newmarket Trouble, owned by Barbara Dickinson\n"
    "Reserve: Red Oak Maddy, owned by James & Carolyn Tate\n",
    "Veteran Championship Certificate Entries: 6\n"
    "Champion: Newmarket Trouble, owned by Barbara Dickinson\n"
    "Reserve: Red Oak Maddy, owned by James & Carolyn Tate\n"
    "3rd: Land's End Nutmeg, owned by Emily Hempel\n"
    "4th: Kensington Batman, owned by Lisa Richards\n"
    "5th: Kensington Devonshire Sno-patch, owned by Teresa King\n"
    "6th: Button Top Jackie, owned by Flo Clark\n",
    "Jackie VCC rebuild",
)

# Pepper + Farmcliff Tipper (PDF p31)
repl(
    "1st: Thimble Farm Coyy, owned by Val Davis\n"
    "2nd: Pepper, owned by Richard Buford\n"
    "4th: Karal Roxi, owned by Karen Cooper\n",
    "1st: Thimble Farm Coyy, owned by Val Davis\n"
    "2nd: Pepper, owned by Richard Buford\n"
    "3rd: Farmcliff Tipper, owned by Bob Franklin\n"
    "4th: Karal Roxi, owned by Karen Cooper\n",
    "Pepper +Tipper",
)

# Disco r/br continues on right col (PDF p21)
repl(
    "Dog Pups, 9 up to 12 months, r/br                        Entries: 6\n"
    "1st: Rainbow Pride Disco, owned by Sal & Theresa Lopresti\n"
    "--- column RIGHT ---\n"
    "5th: Old South Dylan, owned by Cheryl Fowler\n"
    "6th: Paddlefoot Case, owned by Betty Ahlbom\n",
    "Dog Pups, 9 up to 12 months, r/br Entries: 6\n"
    "1st: Rainbow Pride Disco, owned by Sal & Theresa Lopresti\n"
    "2nd: T.J. Farms Factor, owned by Teresa Wellman\n"
    "3rd: Foxbolt Glacier, owned by Chris Boesel\n"
    "4th: Bridle Creek Gunny, owned by Ruth Camp\n"
    "5th: Old South Dylan, owned by Cheryl Fowler\n"
    "6th: Paddlefoot Case, owned by Betty Ahlbom\n",
    "Disco +Factor/Glacier/Gunny",
)

# Bali page-break false gap: prior class 6th before Novice Adult
repl(
    "2nd: Battle Bom Blizzard, owned by Anita Phillips\n"
    "Troon Quarry 2001 Terrier Trial\n"
    "--- page 18 ---\n"
    "--- column LEFT ---\n"
    "6th: Conquest Bali, owned by John Mohon\n"
    "Novice Adult                                                          Entries: 0\n",
    "2nd: Battle Bom Blizzard, owned by Anita Phillips\n"
    "Troon Quarry 2001 Terrier Trial\n"
    "--- page 18 ---\n"
    "--- column LEFT ---\n"
    "Open Puppy Entries: 6\n"
    "6th: Conquest Bali, owned by John Mohon\n"
    "Novice Adult Entries: 28\n",
    "Bali Open Puppy flush",
)

# Youth Divito column smash — insert 3rd if PDF; else flush with handler class header
# Gentry OCR says 2nd not 1st
repl(
    "1st: TFoxisiand Gentry, owned by Handy & Donna Hastings\n"
    "3rd: Russell's Jack RJ\", owned by Sylvia Reams\n",
    "2nd: Fox Island Gentry, owned by Randy & Donna Hastings\n"
    "3rd: Russell's Jack RJ, owned by Sylvia Reams\n",
    "Gentry 1st→2nd OCR",
)

HQ.write_text(text, encoding="utf-8")
print("applied", n)
print("gaps", count_gaps(text.splitlines()))
