"""2000 Vol II batch3 — Corby misplace, Covergirl dup, more OCR mangled ranks."""
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


# Corby was right-column bleed; bitch pups continue Rose/Breeze/Foxy
repl(
    "1st: Kenswick Kayla, owned by Joel & Sandy McElearney\n"
    "2nd: Brandywine Tumble, owned by Stephanie Taylor\n"
    "3rd: Kenswick Caution, owned by Joel & Sandy McElearney\n"
    "5th: Cromwell Corby, owned by Jane McClay\n"
    "4th: Hart Farm Rose, owned by Mary Stevens\n"
    "5th: Glenhaven Breeze, owned by Geri Morin\n"
    "6th: Sow's Ear Foxy Brown, owned by James Harakaly\n",
    "1st: Kenswick Kayla, owned by Joel & Sandy McElearney\n"
    "2nd: Brandywine Tumble, owned by Stephanie Taylor\n"
    "3rd: Kenswick Caution, owned by Joel & Sandy McElearney\n"
    "4th: Hart Farm Rose, owned by Mary Stevens\n"
    "5th: Glenhaven Breeze, owned by Geri Morin\n"
    "6th: Sow's Ear Foxy Brown, owned by James Harakaly\n",
    "Corby bleed remove / reorder Rose",
)

# Duplicate Covergirl/Jiminy block (same reorder as batch2)
repl(
    "2nd: Cromwell Covergirl, owned by Jane McClay\n"
    "6th: Lakeshore Jiminy Cricket, owned by Cathy Larson\n"
    "3rd: Heart N' Soul'McSorley, owned by Walter & Marla Lutter\n",
    "2nd: Cromwell Covergirl, owned by Jane McClay\n"
    "3rd: Heart N' Soul McSorley, owned by Walter & Marla Lutter\n"
    "6th: Lakeshore Jiminy Cricket, owned by Cathy Larson\n",
    "Covergirl dup reorder",
)

# Peppermint/Hunter/Taco Bill scramble on p91
repl(
    "2nd: Romney Peppermint Patty, owned by B. Boyd & C. Wardell\n"
    "5th: Singletrack Hunter, owned by Mark & Lisa Green\n"
    "3rd: Taco Bill, owned by Ruth Evans\n"
    "6th: Blue Barns Charlie, owned by Michael Durante\n"
    "4th: Ash Creek Pinch, owned by Mary Lou Mogrovejo Bitches, 1 vr. & older. 10 up to 1214\" Eniriee: 99\n"
    "4th: Ash Creek Pinch, owned by Mary Lou Mogrovejo\n",
    "2nd: Romney Peppermint Patty, owned by B. Boyd & C. Wardell\n"
    "3rd: Taco Bill, owned by Ruth Evans\n"
    "4th: Ash Creek Pinch, owned by Mary Lou Mogrovejo\n"
    "5th: Singletrack Hunter, owned by Mark & Lisa Green\n"
    "6th: Blue Barns Charlie, owned by Michael Durante\n",
    "Peppermint/Taco/Hunter reorder",
)

# Luna/Punkin/Shabby scramble
repl(
    "5th: Prestige Farms Oliver, owned by Jennifer Gilligan\n"
    "3rd: Brooks Chase Luna, owned by Brooks Chase Terriers\n"
    "6th: Stealth Punkin, owned by Stealth Terriers\n"
    "4th: Ransome Shabby, owned by Cheryl Elisworth\n"
    "RACING DIVISION 5th: Foxi Loxi Codi, owned by Scott & Susan Aeppli\n",
    "3rd: Brooks Chase Luna, owned by Brooks Chase Terriers\n"
    "4th: Ransome Shabby, owned by Cheryl Elisworth\n"
    "5th: Prestige Farms Oliver, owned by Jennifer Gilligan\n"
    "6th: Stealth Punkin, owned by Stealth Terriers\n"
    "RACING DIVISION\n",
    "Luna/Shabby/Oliver/Punkin reorder",
)

# Tackle mangled 1st (missing 2nd still may remain)
repl(
    "1st: i-==Farmcliff.Tackle,.owned by.Megan.Johnson:\n"
    "3rd: Spanky, owned by Betty Anne Senf\n",
    "1st: Farmcliff Tackle, owned by Megan Johnson\n"
    "3rd: Spanky, owned by Betty Anne Senf\n",
    "Tackle 1st OCR (2nd still missing)",
)

# Big Sky Annie VCC mangled 1st
repl(
    "Veteran Championship Certificate Entries: 9 5th: Chelsea Rose, owned by Kay Sadowsky\n"
    "1st: Big'Sky-Annie;-owned by:-Doug'&Sue.Tack\n"
    "4th: Round the Bend Orbit, owned by Sandra Ryan\n"
    "5th: Farmcliff Sugar, owned by Genie Franklin\n"
    "6th: Round the Bend Orbit, owned by Sandra Ryan\n",
    "Veteran Championship Certificate Entries: 9\n"
    "1st: Big Sky Annie, owned by Doug & Sue Tack\n"
    "4th: Round the Bend Orbit, owned by Sandra Ryan\n"
    "5th: Chelsea Rose, owned by Kay Sadowsky\n"
    "6th: Farmcliff Sugar, owned by Genie Franklin\n",
    "Annie VCC normalize (2nd/3rd still missing)",
)

# Veterans Sugar/Jade OCR junk
repl(
    "1st: Sid: Farmcliff Sugar, owned by Bob & Genie Frankdin\n"
    "2nd: Westwood Jade, owned by Rick &Leslie Hemsing\n"
    "4th: Risky, owned by Melissa Lowe\n",
    "1st: Farmcliff Sugar, owned by Bob & Genie Franklin\n"
    "2nd: Westwood Jade, owned by Rick & Leslie Hemsing\n"
    "4th: Risky, owned by Melissa Lowe\n",
    "Sugar/Jade OCR normalize",
)

# Westwood Jade / Sugar missing 2nd — leave unless PDF clear; normalize only
repl(
    "1st: Westwood Jade, owned by Rick & Leslie Hemsing\n"
    "3rd:  Farmcliff Sugar, owned by Bob & Genie Franklin\n"
    "4th: Risky, owned by Melissa Lowe\n",
    "1st: Westwood Jade, owned by Rick & Leslie Hemsing\n"
    "2nd: Farmcliff Sugar, owned by Bob & Genie Franklin\n"
    "4th: Risky, owned by Melissa Lowe\n",
    "Jade/Sugar 3rd→2nd (Risky 3rd still open)",
)

HQ.write_text(text, encoding="utf-8")
print("applied", n)
print("gaps", count_gaps(text.splitlines()))
