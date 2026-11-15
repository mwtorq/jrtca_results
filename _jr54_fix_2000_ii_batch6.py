"""2000 Vol II batch6 — Reba unsmash, youth agility, VCC, Spencer, Hutch."""
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


# PNW page20: conformation left vs racing right unsmash
repl(
    "Bitches, 1 yr. & older, 10 up to 12 1/2\", r/br Entries: 0 2nd: Salishan Maggie, owned by Bette Hatifeld\n"
    "1st: Fox Run Reba, owned by Sherri Rossmiller\n"
    "3rd: Just Avery, owned by Shawn & Kari Gerdes\n"
    "2nd: Rushill Spice, owned by J. Baker/J. Freimark\n"
    "4th: Foxport Tex, owned by Tooie Crooks\n"
    "3rd: Boggsborough Bizzie, owned by Robert & Linda Fleck\n"
    "5th: Sweetgrass Emma, owned by Shirley Kostric\n"
    "4th: Amblegreen Breeze, owned by Cyndy Monk ils = «- eli a ee ee, ie\n"
    "4th: Amblegreen Breeze, owned by Cyndy Monk\n"
    "5th: Cotswold Skecher, owned by Constance Martin\n",
    "Bitches, 1 yr. & older, 10 up to 12 1/2\", r/br Entries: 6\n"
    "1st: Fox Run Reba, owned by Sherri Rossmiller\n"
    "2nd: Rushill Spice, owned by J. Baker/J. Freimark\n"
    "3rd: Boggsborough Bizzie, owned by Robert & Linda Fleck\n"
    "4th: Amblegreen Breeze, owned by Cyndy Monk\n"
    "5th: Cotswold Skecher, owned by Constance Martin\n"
    "Bitches, 1 yr. & older, 10 up to 12 1/2\" Entries: 6\n"
    "2nd: Salishan Maggie, owned by Bette Hatfield\n"
    "3rd: Just Avery, owned by Shawn & Kari Gerdes\n"
    "4th: Foxport Tex, owned by Tooie Crooks\n"
    "5th: Sweetgrass Emma, owned by Shirley Kostric\n"
    "6th: Simply Skyler, owned by Shawn & Kari Gerdes\n",
    "Reba/Avery column unsmash",
)

# Open Adult: drop racing bleed Emma/Skyler
repl(
    "Open Adult Entries: 19\n"
    "1st: Stafford Acres Jiggs, owned by Sandy Wiens\n"
    "6th: Sweetgrass Emma, owned by Shirley Kostric\n"
    "6th: Simply Skyler, owned by Shawn & Kari Gerdes\n"
    "Championship Certificate, 10 up to 12 1/2\"4\" Entries: 8\n",
    "Open Adult Entries: 19\n"
    "1st: Stafford Acres Jiggs, owned by Sandy Wiens\n"
    "Championship Certificate, 10 up to 12 1/2\" Entries: 8\n",
    "Jiggs drop racing bleed",
)

# Youth agility On Lead (Hi-Bid p46) — 5th unscanned
repl(
    "Youth Handling Agility, On Lead Entries: 6\n"
    "2nd: Ashley Boyd\n"
    "6th: Jessica Pancoast\n",
    "Youth Handling Agility, On Lead Entries: 6\n"
    "1st: Jeffrey Finkernagel\n"
    "2nd: Ashley Boyd\n"
    "3rd: Ben Davis\n"
    "4th: Ralph Bassett\n"
    "6th: Jessica Pancoast\n",
    "Youth agility +Jeffrey/Ben/Ralph",
)

# Petey dogs class: 2nd Hutch (PDF p91)
repl(
    "Dogs, 1 yr. & older, 10 up to 12 1/2\" Entries: 13\n"
    "1st: North Country Petey, owned by Mary Lou Mogrovejo\n"
    "3rd: Hunter's Green Stokes, owned by Antonio Sullo\n"
    "4th: Tackle, owned by Vicki & Megan Johnson\n"
    "5th: Farmcliff Spencer, owned by Bob Franklin\n",
    "Dogs, 1 yr. & older, 10 up to 12 1/2\" Entries: 13\n"
    "1st: North Country Petey, owned by Mary Lou Mogrovejo\n"
    "2nd: Farmcliff Hutch, owned by Dave McMahon\n"
    "3rd: Hunter's Green Stokes, owned by Antonio Sullo\n"
    "4th: Tackle, owned by Vicki & Megan Johnson\n"
    "5th: Farmcliff Spencer, owned by Bob Franklin\n",
    "Petey +Hutch 2nd",
)

# Killare dogs: 4th Spencer (PDF p95)
repl(
    "2nd: Killare McGwire, owned by Ben Davis\n"
    "3rd: North Country Petey, owned by Jack & Mary Lou Mogrovejo\n"
    "5th: The Folly Black Jack, owned by Rick Thornton\n"
    "6th: Norton, owned by Anne Ritter\n",
    "2nd: Killare McGwire, owned by Ben Davis\n"
    "3rd: North Country Petey, owned by Jack & Mary Lou Mogrovejo\n"
    "4th: Farmcliff Spencer, owned by Genie Franklin\n"
    "5th: The Folly Black Jack, owned by Rick Thornton\n"
    "6th: Norton, owned by Anne Ritter\n",
    "Killare +Spencer 4th",
)

# Annie VCC: Champion/Reserve not 1st Annie (PDF p95)
repl(
    "Veteran Championship Certificate Entries: 9\n"
    "1st: Big Sky Annie, owned by Doug & Sue Tack\n"
    "4th: Round the Bend Orbit, owned by Sandra Ryan\n"
    "5th: Chelsea Rose, owned by Kay Sadowsky\n"
    "6th: Farmcliff Sugar, owned by Genie Franklin\n"
    "Champion: Double D Pfoxie, owned by Dorothy Whiting\n"
    "Reserve: Wyndcroft Tiller, owned by Margaret Minutello Veterans, 6 years & older, over 121-15\" Entries: 8\n",
    "Veteran Championship Certificate Entries: 9\n"
    "Champion: Double D Pfoxie, owned by Dorothy Whiting\n"
    "Reserve: Wyndcroft Tiller, owned by Margaret Minutello\n"
    "3rd: Big Sky Annie, owned by Doug & Sue Tack\n"
    "4th: Round the Bend Orbit, owned by Sandra Ryan\n"
    "5th: Farmcliff Sugar, owned by Genie Franklin\n"
    "6th: Chelsea Rose, owned by Kay Sadowsky\n",
    "Annie VCC Champion/Reserve rebuild",
)

# Normalize Hutch OCR on other dogs class (2nd still missing — leave)
repl(
    "1st: Farmcliff Hutch, owned by:Dave McMahon\n"
    "3rd: Hunter's Green Stokes, owned by Antonio Sullo\n",
    "1st: Farmcliff Hutch, owned by Dave McMahon\n"
    "3rd: Hunter's Green Stokes, owned by Antonio Sullo\n",
    "Hutch OCR normalize",
)

repl(
    "1st: AStin=-.Farmcliff Hutch;, owned by Dave'& Marti McMahon\n",
    "1st: Farmcliff Hutch, owned by Dave & Marti McMahon\n",
    "Hutch OCR normalize 2",
)

HQ.write_text(text, encoding="utf-8")
print("applied", n)
print("gaps", count_gaps(text.splitlines()))
