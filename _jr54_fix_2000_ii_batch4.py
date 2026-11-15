"""2000 Vol II batch4 — Micro/Hudson, Rolex class, Covergirl/Jiminy, vets."""
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


# Bronze Medallion: 3rd Hudson (PDF p9)
repl(
    "Bronze Medallion Dog Entries: 4\n"
    "1st: Corn Row Tucker, owned by Mark Thompson\n"
    "2nd: Farmcliff Fred, owned by Michelle Ward\n"
    "4th: Natural Instinct Micro, owned by Ken & Kathy Bushell\n",
    "Bronze Medallion Dog Entries: 4\n"
    "1st: Corn Row Tucker, owned by Mark Thompson\n"
    "2nd: Farmcliff Fred, owned by Janice Bjorkland\n"
    "3rd: Hudson, owned by Michelle Ward\n"
    "4th: Natural Instinct Micro, owned by Ken & Kathy Bushell\n",
    "Micro +Hudson",
)

# Covergirl/McSorley then Novice; Jiminy is Agility I right-col 6th before Agility II
repl(
    "Agility I\n"
    "2nd: Cromwell Covergirl, owned by Jane McClay\n"
    "3rd: Heart N' Soul McSorley, owned by Walter & Marla Lutter\n"
    "6th: Lakeshore Jiminy Cricket, owned by Cathy Larson\n"
    "Agility II, Off Lead Entries: 0\n"
    "Novice Adult Entries: 6 1st: Farmcliff Spencer, owned by Genie Franklin\n",
    "Agility I\n"
    "2nd: Cromwell Covergirl, owned by Jane McClay\n"
    "3rd: Heart N' Soul McSorley, owned by Walter & Marla Lutter\n"
    "Novice Adult Entries: 6\n",
    "Covergirl detach Jiminy",
)

# Attach Jiminy before Agility II if still orphaned near Dennis block — handle dup block
repl(
    "2nd: Cromwell Covergirl, owned by Jane McClay\n"
    "3rd: Heart N' Soul McSorley, owned by Walter & Marla Lutter\n"
    "6th: Lakeshore Jiminy Cricket, owned by Cathy Larson\n",
    "2nd: Cromwell Covergirl, owned by Jane McClay\n"
    "3rd: Heart N' Soul McSorley, owned by Walter & Marla Lutter\n",
    "Covergirl dup detach Jiminy",
)

# Rolex / Jackpot working dog + cert interleave (Crossewinds PDF)
repl(
    "1st: Foxfield Flash;, owned by Janet Sproles/Marcy Crosse\n"
    "2nd: Pork Chopp, owned by Kevin & Shannon Osby\n"
    "2nd: Run Away Farm Rolex, owned by Martha Milligan\n"
    "5th: The Wild West Jackpot, owned by Joan Stroh\n"
    "3rd: Vixen Trace Dapper Dan, owned by Russ & Barbara Gilford\n"
    "6th: Edison's Dixie Pixie, owned by Russ & Barbara Gilford\n"
    "ee eee ee 'ittaliietii: A Phamnianchin Certificate. 1214 up to 15\" Entries: 14\n"
    "3rd: Vixen Trace Dapper Dan, owned by Russ & Barbara Gilford\n"
    "Working Terrier Dog, 12% up to 15\", r/br Entries: 4\n",
    "1st: Foxfield Flash, owned by Janet Sproles/Marcy Crosse\n"
    "2nd: Run Away Farm Rolex, owned by Martha Milligan\n"
    "3rd: Vixen Trace Dapper Dan, owned by Russ & Barbara Gilford\n"
    "Championship Certificate, 12 1/2 up to 15\" Entries: 14\n"
    "3rd: Corn Row Maggie, owned by Dan Peck & Jeanne Kozak\n"
    "4th: Pork Chopp, owned by Kevin & Shannon Osby\n"
    "5th: The Wild West Jackpot, owned by Joan Stroh\n"
    "6th: Edison's Dixie Pixie, owned by Russ & Barbara Gilford\n"
    "Working Terrier Dog, 12 1/2 up to 15\", r/br Entries: 4\n",
    "Rolex/Jackpot unsmash",
)

# Veterans Annie/Jade/Sugar/Risky (Crossewinds PDF p69)
repl(
    "1st: Farmcliff Sugar, owned by Bob & Genie Franklin\n"
    "2nd: Westwood Jade, owned by Rick & Leslie Hemsing\n"
    "4th: Risky, owned by Melissa Lowe\n"
    "5th: Briarpatch Skoal, owned by Carol Finglass\n"
    "6th: Mineral Springs Indiana Jones, owned by Mariellyn Zeock\n",
    "1st: Big Sky Annie, owned by Doug & Sue Tack\n"
    "2nd: Westwood Jade, owned by Rick & Leslie Hemsing\n"
    "3rd: Farmcliff Sugar, owned by Bob & Genie Franklin\n"
    "4th: Risky, owned by Melissa Lowe\n"
    "5th: Briarpatch Skoal, owned by Carol Finglass\n"
    "6th: Mineral Springs Indiana Jones, owned by Mariellyn Zeock\n",
    "Vets Annie/Jade/Sugar rebuild",
)

# Jessie veterans earlier trial — OCR shows Sugar 2nd then Jessie 4th; 3rd unscanned.
# Leave gap; do not invent.

# Petey/Stokes reorder (Spencer false 5th before 3rd)
repl(
    "1st: North Country Petey, owned by Mary Lou Mogrovejo\n"
    "5th: Farmcliff Spencer, owned by Bob Franklin\n"
    "3rd: Hunter's Green Stokes, owned by Antonio Sullo\n"
    "4th: Tackle, owned by Vicki & Megan Johnson\n"
    "5th: Taco Bill, owned by Ruth Evans\n",
    "1st: North Country Petey, owned by Mary Lou Mogrovejo\n"
    "3rd: Hunter's Green Stokes, owned by Antonio Sullo\n"
    "4th: Tackle, owned by Vicki & Megan Johnson\n"
    "5th: Farmcliff Spencer, owned by Bob Franklin\n",
    "Petey/Stokes/Spencer reorder",
)

HQ.write_text(text, encoding="utf-8")
print("applied", n)
print("gaps", count_gaps(text.splitlines()))
