"""Honest 2001 Vol III pt1 fills from Yearbook Scans/2001 Vol III/*.txt."""
from pathlib import Path
import sys

sys.path.insert(0, ".")
from _jr54_strip_place_prefix_junk import count_gaps

path = list(Path("Updated Yearbook Scans").rglob("2001 Vol III pt 1_ocr_hqmax.txt"))[0]
text = path.read_text(encoding="utf-8", errors="replace")
before = count_gaps(text.splitlines())

reps = [
    (
        "cronic_joe",
        "2nd: Foxnorton Cronic, owned by Lea Boa\n"
        "# PARKED jr54: place-rank gap after Foxnorton Cronic before Round the Bend Dart (OCR blank; no surname invent)\n"
        "4th: Round the Bend Dart, owned by Kay Sadowsky",
        "2nd: Foxnorton Cronic, owned by Lea Boa\n"
        "3rd: Farmcliff Joe, owned by Bob & Genie Franklin\n"
        "4th: Round the Bend Dart, owned by Kay Sadowsky",
    ),
    (
        "ripley_novice",
        "Open Puppy Entries: 0\n"
        "1st: Brooke Hollow Dottie, owned by John & Amy Callahan\n"
        "2nd: North Hills Ripley, owned by Cheri Oliver\n"
        "# PARKED jr54: place-rank gap after North Hills Ripley before Northgate Hallie (OCR blank; no surname invent)\n"
        "4th: Northgate Hallie, owned by Michael Beach\n"
        "5th: Suzy, owned by Pam Smith",
        "Novice Puppy Entries: 12\n"
        "1st: Sow's Ear Mascara, owned by Twila Decker\n"
        "2nd: North Hills Ripley, owned by Cheri Oliver\n"
        "3rd: Brooke Hollow Dottie, owned by John & Amy Callahan\n"
        "4th: Northgate Hallie, owned by Michael Beach\n"
        "5th: Suzy, owned by Pam Smith",
    ),
    (
        "jessie_kermit",
        "1st: Dudley, owned by Cathy Larson\n"
        "2nd: Griffey, owned by Karen Merriman\n"
        "3rd: Jessie, owned by Sandy Brown\n"
        "# PARKED jr54: place-rank gap between Jessie and J Russell Tee JR (OCR blank / junk line removed; no surname invent)\n"
        "5th: J Russell Tee JR, owned by Sue Walski",
        "1st: Dudley, owned by Cathy Larson\n"
        "2nd: Griffey, owned by Karen Merriman\n"
        "3rd: Jessie, owned by Sandy Brown\n"
        "4th: Farmcliff Kermit, owned by Bob & Genie Franklin\n"
        "5th: J Russell Tee JR, owned by Sue Walski",
    ),
    (
        "heidi_snowflake",
        "3rd: Whispering Winds Heidi Ho, owned by Ken Winfield\n"
        "# PARKED jr54: place-rank gap after Whispering Winds Heidi Ho; OCR places Abby as 5th (no invent)\n"
        "5th: Abby, owned by Richard & Annette Kent",
        "3rd: Whispering Winds Heidi Ho, owned by Ken Winfield\n"
        "4th: Farmcliff Snowflake, owned by Bob & Genie Franklin\n"
        "5th: Abby, owned by Richard & Annette Kent",
    ),
    (
        "arlins_taltos",
        "3rd: Arlins My Ty, owned by Michael Beach\n"
        "# PARKED jr54: place-rank gap between Arlins My Ty and Sow's Ear Taltos (OCR blank; no surname invent)\n"
        "5th: Sow's Ear Taltos, owned by Twila Decker\n"
        "6th: Farmcliff Merlin, owned by Karen Franklin",
        "3rd: Arlins My Ty, owned by Michael Beach\n"
        "4th: Sow's Ear Taltos, owned by Twila Decker\n"
        "5th: Farmcliff Merlin, owned by Karen Franklin",
    ),
    (
        "bugsy_questor",
        "1st: Green Gate Tomba, owned by Joe & Priscilla Testa\n"
        "2nd: Bugsy, owned by Richard & Annette Kent\n"
        "# PARKED jr54: place-rank gap between Bugsy and Questor (OCR blank; no surname invent)\n"
        "4th: Questor, owned by Bill O'Brien",
        "1st: Green Gate Tomba, owned by Joe & Priscilla Testa\n"
        "2nd: Bugsy, owned by Richard & Annette Kent\n"
        "3rd: Long Hope Mickey, owned by Bob & Genie Franklin\n"
        "4th: Questor, owned by Bill O'Brien",
    ),
    (
        "clean_dylan",
        "1st: Natural Instinct Mr. Clean, owned by Ken & Kathy Bushell\n"
        "# PARKED jr54: place-rank gap after Natural Instinct Mr. Clean before Old Glory Dylan (OCR blank; no surname invent)\n"
        "3rd: Old Glory Dylan, owned by Sandy Brown",
        "1st: Natural Instinct Mr. Clean, owned by Ken & Kathy Bushell\n"
        "2nd: Old Glory Dylan, owned by Sandy Brown\n"
        "3rd: Little Eden Bazooka, owned by Gaye Redpath",
    ),
    (
        "jessie_casey",
        "1st: Stone's Throw Griffey, owned by Karen Merriman\n"
        "2nd: Dudley, owned by Cathy Larson\n"
        "3rd: Jessie, owned by Sandy Brown\n"
        "# PARKED jr54: place-rank gap between Jessie and Casey Jones (OCR blank; no surname invent)\n"
        "5th: Casey Jones, owned by John Scully",
        "1st: Stone's Throw Griffey, owned by Karen Merriman\n"
        "2nd: Dudley, owned by Cathy Larson\n"
        "3rd: Farmcliff Kermit, owned by Bob & Genie Franklin\n"
        "4th: Jessie, owned by Sandy Brown\n"
        "5th: Casey Jones, owned by John Scully",
    ),
    (
        "teeni_liz",
        "3rd: Long Hope Teeni Weeni, owned by Nellie Niewola\n"
        "# PARKED jr54: place-rank gap after Long Hope Teeni Weeni before Highwater Banjo (OCR blank; no surname invent)\n"
        "5th: Highwater Banjo, owned by Ann Shephard",
        "3rd: Long Hope Teeni Weeni, owned by Nellie Niewola\n"
        "4th: Farmcliff Liz, owned by Bob & Genie Franklin\n"
        "5th: Highwater Banjo, owned by Ann Shephard",
    ),
]

for label, old, new in reps:
    n = text.count(old)
    if n == 0:
        print("MISS", label)
        continue
    text = text.replace(old, new)
    print(label, "x", n)

after = count_gaps(text.splitlines())
path.write_text(text, encoding="utf-8", newline="\n")
print("file", before, "->", after)
