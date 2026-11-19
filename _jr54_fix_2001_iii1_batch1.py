"""2001 Vol III pt1 batch1 — early PDF page OCR clears (p2/6/17/19/20)."""
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


# Bitches over 12.5: Candycane 3rd + Puff 4th (PDF p2)
repl(
    "1st: Muscle Russell Zippity Zoe, owned by Jim & Mandy Roth\n"
    "2nd: Brandywine Gale, owned by Jim & Sally Saul\n"
    "--- column RIGHT ---\n"
    "5th: Terrier Turf Mayhem, owned by Kevin & Shannon Osby\n"
    "6th: R.A. Trixie, owned by John & Judy Tyno\n",
    "1st: Muscle Russell Zippity Zoe, owned by Jim & Mandy Roth\n"
    "2nd: Brandywine Gale, owned by Jim & Sally Saul\n"
    "3rd: Candycane, owned by Lisanne & Mike Gray\n"
    "4th: Dogwood Glen Puff O'Wind, owned by Lucy Ramey\n"
    "5th: Terrier Turf Mayhem, owned by Kevin & Shannon Osby\n"
    "6th: R.A. Trixie, owned by John & Judy Tyno\n",
    "Gale +Candycane/Puff",
)

# Agility I Off Lead: right column is 5th Breeze / 6th Tuppence (PDF p6)
repl(
    "4th: Farrier Point Ranger, owned by Denise Neuner\n"
    "--- column RIGHT ---\n"
    "1st: Bowery Tuppence, owned by Rhonda Rebhom\n"
    "5th: Amblegreen Breeze, owned by Cindy Monk\n",
    "4th: Farrier Point Ranger, owned by Denise Neuner\n"
    "5th: Amblegreen Breeze, owned by Cindy Monk\n"
    "6th: Bowery Tuppence, owned by Rhonda Rebhom\n",
    "Agility I Breeze/Tuppence",
)

# Working dog: Farmcliff Spencer 2nd (PDF p17)
repl(
    "1st: Sow's Ear Taltos, owned by Twila Decker\n"
    "@ndz=mEamclift:Spencer, owniediby: Bob Eranklin:\n"
    "3rd: Natural Instinct Mr. Clean, owned by Ken Bushell\n",
    "1st: Sow's Ear Taltos, owned by Twila Decker\n"
    "2nd: Farmcliff Spencer, owned by Bob Franklin\n"
    "3rd: Natural Instinct Mr. Clean, owned by Ken Bushell\n",
    "Taltos +Spencer 2nd",
)

# Dog pups 9-12 r/br: Farmcliff Joey 3rd (PDF p19)
repl(
    "2nd: Round the Bend Dart, owned by Kay Sadowsky\n"
    "BrdzmFammolifJoeyowned:by:Bob:&:Genie Franklin\n"
    "4th: Glen Coe Miner, owned by Jan Bell\n",
    "2nd: Round the Bend Dart, owned by Kay Sadowsky\n"
    "3rd: Farmcliff Joey, owned by Bob & Genie Franklin\n"
    "4th: Glen Coe Miner, owned by Jan Bell\n",
    "Dart +Joey 3rd",
)

# Bitches 10-12.5: Teeni Weeni 4th (PDF p20)
repl(
    "3rd: The Folly Piper, owned by Rick & Mary Thomton\n"
    "5th: The Folly Lucy, owned by Rick & Mary Thomton\n"
    "6th: Woods End Calico, owned by Doug & Noreen Loranger\n",
    "3rd: The Folly Piper, owned by Rick & Mary Thornton\n"
    "4th: Long Hope Teeni Weeni, owned by Nellie Niewola\n"
    "5th: The Folly Lucy, owned by Rick & Mary Thornton\n"
    "6th: Woods End Calico, owned by Doug & Noreen Loranger\n",
    "Piper +Teeni 4th",
)

# Veteran bitches 10-12.5: Sassy/Revion/Ember/Sugar/Sophie/Wee Won (PDF p20)
repl(
    "Veteran Bitches, 6 years & older, 10up to 12%.\" Entries: 9\n"
    "2nd: Lost Acres Revion, owned by Karen McCarthy\n"
    "3rd: Briarpatch Ember, owned by Doug & Noreen Loranger\n"
    "6th: : Farmcliff Spencer, owned by:Bob & Genie Frankin\n"
    "5th: Crosspatch Sophie, owned by Cheri Oliver\n"
    "6th: Long Hope Wee Won, owned by Nellie Niewola\n",
    "Veteran Bitches, 6 years & older, 10 up to 12 1/2\" Entries: 9\n"
    "1st: Lickity Split Sassy, owned by Bob & Genie Franklin\n"
    "2nd: Lost Acres Revion, owned by Karen McCarthy\n"
    "3rd: Briarpatch Ember, owned by Doug & Noreen Loranger\n"
    "4th: Farmcliff Sugar, owned by Karin Franklin\n"
    "5th: Crosspatch Sophie, owned by Cheri Oliver\n"
    "6th: Long Hope Wee Won, owned by Nellie Niewola\n",
    "Vet bitches Sassy/Sugar rebuild",
)

# Veteran dogs 10-12.5: Farmcliff Kermit 3rd (PDF p20)
repl(
    "1st: Dudley, owned by Cathy Larson\n"
    "2nd: Stone's Throw Griffey, owned by Karen Merriman\n"
    "4th: Jessie, owned by Sandy Brown\n"
    "5th: Casey Jones, owned by John Scully\n",
    "1st: Dudley, owned by Cathy Larson\n"
    "2nd: Stone's Throw Griffey, owned by Karen Merriman\n"
    "3rd: Farmcliff Kermit, owned by Bob & Genie Franklin\n"
    "4th: Jessie, owned by Sandy Brown\n"
    "5th: Casey Jones, owned by John Scully\n",
    "Griffey +Kermit 3rd",
)

# Pups 9-12 over: Peggy/Max/Joe/George/Olive (PDF p20)
repl(
    "Pups, 9 up to 12 months, over 12 1/2-15\" Entries: 5\n"
    "3rd: :Farmcliff: Kermit;, owned by Bob & Genie Franklin\n"
    "2nd: Skyline Orchard Max, owned by Karen Howard\n"
    "5th: Oakwood Olive, owned by Shannon Rice\n"
    "SrcmmmiamisiiiioenauncdiSIBTHSIETHRVErEn\n",
    "Pups, 9 up to 12 months, over 12 1/2-15\" Entries: 5\n"
    "1st: Farmcliff Peggy, owned by Bob & Genie Franklin\n"
    "2nd: Skyline Orchard Max, owned by Karen Howard\n"
    "3rd: Farmcliff Joe, owned by Bob & Genie Franklin\n"
    "4th: Farmcliff George, owned by Bob & Genie Franklin\n"
    "5th: Oakwood Olive, owned by Shannon Rice\n",
    "Pups Peggy/Joe/George/Olive",
)

HQ.write_text(text, encoding="utf-8")
n1 = count_gaps(HQ.read_text(encoding="utf-8").splitlines())
print("replacements", n, "gaps", n0, "->", n1)
