"""Honest mid-gap junk ordinal recoveries (Srd / 3rd; / lead junk). No invented placements."""
from pathlib import Path
import sys

sys.path.insert(0, ".")
from _jr54_strip_place_prefix_junk import count_gaps

ROOT = Path("Updated Yearbook Scans")


def resolve(name: str) -> Path:
    return list(ROOT.rglob(name))[0]


def fix(path: Path, old: str, new: str, label: str) -> None:
    text = path.read_text(encoding="utf-8", errors="replace")
    if old not in text:
        print("MISS", label)
        return
    b = count_gaps(text.splitlines())
    text2 = text.replace(old, new, 1)
    a = count_gaps(text2.splitlines())
    path.write_text(text2, encoding="utf-8", newline="\n")
    print(label, b, "->", a)


# 1991: Srd → 3rd Lady of Ravenswood
fix(
    resolve("2026-11-03_204327_ocr_hqmax.txt"),
    "2nd: Farmceliff Snowflake, owned by Bob & Genie Franklin\n"
    "# PARKED jr54: place-rank gap after Farmceliff Snowflake before Fox Run Judy (OCR blank; no surname invent)\n"
    "_        Srd: Lady of Ravenswood, owned by Janet & Ben Sutcliffe\n"
    "4th: Fox Run Judy, owned by Elizabeth Standish Sackson",
    "2nd: Farmceliff Snowflake, owned by Bob & Genie Franklin\n"
    "3rd: Lady of Ravenswood, owned by Janet & Ben Sutcliffe\n"
    "4th: Fox Run Judy, owned by Elizabeth Standish Sackson",
    "lady3",
)

# 1994: lead junk before Parkins Tracer 3rd
fix(
    resolve("2026-11-04_111102_ocr_hqmax.txt"),
    "2nd: Fleetwood Tess, owned by Debbie LaMantia\n"
    "# PARKED jr54: place-rank gap after Fleetwood Tess before Thimble Farm Rose (OCR blank; no surname invent)\n"
    "7       3rd: Parkins Tracer, owned by Dander & Woodcock\n"
    "4th: Thimble Farm Rose, owned by Val Wasch",
    "2nd: Fleetwood Tess, owned by Debbie LaMantia\n"
    "3rd: Parkins Tracer, owned by Dander & Woodcock\n"
    "4th: Thimble Farm Rose, owned by Val Wasch",
    "tracer3",
)

# 1994: 2nd; Ravenswood Ruby
fix(
    resolve("2026-11-04_114418_ocr_hqmax.txt"),
    "1st: Ravenswood Rambling Rose, owned by Russell & Darlene Zampella                  _\n"
    "# PARKED jr54: place-rank gap after Ravenswood Rambling Rose before Long Hope Freckles (OCR blank; no surname invent)\n"
    "2nd; Ravenswood Ruby, owned by Ben & Janet Sutcliffe\n"
    "3rd: Long Hope Freckles, owned by Nellie Niewola",
    "1st: Ravenswood Rambling Rose, owned by Russell & Darlene Zampella\n"
    "2nd: Ravenswood Ruby, owned by Ben & Janet Sutcliffe\n"
    "3rd: Long Hope Freckles, owned by Nellie Niewola",
    "ruby2",
)

# 1994: 4th; Jennifer King
fix(
    resolve("2026-11-04_114418_ocr_hqmax.txt"),
    "3rd: Justin Zampella\n"
    "# PARKED jr54: place-rank gap after Justin Zampella before Zachary Zampella (OCR blank; no surname invent)\n\n"
    "4th; Jennifer King\n\n"
    "5th: Zachary Zampella",
    "3rd: Justin Zampella\n\n"
    "4th: Jennifer King\n\n"
    "5th: Zachary Zampella",
    "jennifer4",
)

# 1995: 3rd; Farmeliff Kathy
fix(
    resolve("2026-11-04_130959_ocr_hqmax.txt"),
    "2nd: Farmcliff Erin, owned by Bob Franklin\n"
    "# PARKED jr54: place-rank gap after Farmcliff Erin before FarmcliffKermit (OCR blank; no surname invent)\n"
    "3rd; Farmeliff Kathy, owned:by Bob Franklin\n"
    "4th: FarmcliffKermit, owned by Bob Franklin",
    "2nd: Farmcliff Erin, owned by Bob Franklin\n"
    "3rd: Farmeliff Kathy, owned by Bob Franklin\n"
    "4th: FarmcliffKermit, owned by Bob Franklin",
    "kathy3",
)

# 1995: 3rd; Ace in the Hole
fix(
    resolve("2026-11-04_130959_ocr_hqmax.txt"),
    "2nd: Farmcliff Duffy, owned by Doug & Sue Tack\n"
    "# PARKED jr54: place-rank gap after Farmcliff Duffy before Farmcliff Butch (OCR blank; no surname invent)\n"
    "_—           3rd; Ace in the Hole, owned by Pam Molloy\n"
    "4th: Farmcliff Butch, owned by Bob Franklin",
    "2nd: Farmcliff Duffy, owned by Doug & Sue Tack\n"
    "3rd: Ace in the Hole, owned by Pam Molloy\n"
    "4th: Farmcliff Butch, owned by Bob Franklin",
    "ace3",
)

# 1995: 3rd; Crossewinds Trace
fix(
    resolve("2026-11-04_142957_ocr_hqmax.txt"),
    "2nd: Three Oaks Hot Sput of Fox Brush, owned by Erin & Joe Trimmier\n"
    "# PARKED jr54: place-rank gap after Three Oaks Hot Sput of Fox Brush before Orchard Hill Kerrigan (OCR blank; no surname invent)\n\n"
    "3rd; Crossewinds Trace, owned by Becky Crosse                                                          —_\n"
    "4th: Orchard Hill Kerrigan, owned by Janet Gray",
    "2nd: Three Oaks Hot Sput of Fox Brush, owned by Erin & Joe Trimmier\n\n"
    "3rd: Crossewinds Trace, owned by Becky Crosse\n"
    "4th: Orchard Hill Kerrigan, owned by Janet Gray",
    "trace3",
)

# 1995: 3rd; White Spirits
fix(
    resolve("2026-11-04_143343_ocr_hqmax.txt"),
    "2nd: North Hills Te\n"
    "# PARKED jr54: place-rank gap after North Hills Te before Hunter (OCR blank; no surname invent)\n"
    "3rd; White Spirits\n"
    "4th: Hunter, owne",
    "2nd: North Hills Te\n"
    "3rd: White Spirits\n"
    "4th: Hunter, owne",
    "spirits3",
)

# 1995: 3rd; Briarpatch Bunny
fix(
    resolve("2026-11-04_143343_ocr_hqmax.txt"),
    "2nd: Boggsborough Poppy, owned by Karen & Dan Boggs\n"
    "# PARKED jr54: place-rank gap after Boggsborough Poppy before Badgerwood Tara-Lil (OCR blank; no surname invent)\n\n"
    "3rd; Briarpatch Bunny, owned by Maureen Tubbs                                                             -\n"
    "4th: Badgerwood Tara-Lil, owned by Anne Campbell",
    "2nd: Boggsborough Poppy, owned by Karen & Dan Boggs\n\n"
    "3rd: Briarpatch Bunny, owned by Maureen Tubbs\n"
    "4th: Badgerwood Tara-Lil, owned by Anne Campbell",
    "bunny3",
)

# 1996: lead junk before Crossewinds Smitten 2nd
fix(
    resolve("2026-11-04_145148_ocr_hqmax.txt"),
    "1st: Mayhym, owned by Kevin Osby\n"
    "# PARKED jr54: place-rank gap after Mayhym before Pine Hill Makayla (OCR blank; no surname invent)\n"
    "m4          2nd: Crossewinds Smitten, owned by David & Allyson Miller\n"
    "3rd: Pine Hill Makayla, owned by Lisa Drinkwater",
    "1st: Mayhym, owned by Kevin Osby\n"
    "2nd: Crossewinds Smitten, owned by David & Allyson Miller\n"
    "3rd: Pine Hill Makayla, owned by Lisa Drinkwater",
    "smitten2",
)

# 1996: 3rd; Meynell Climber
fix(
    resolve("2026-11-04_150238_ocr_hqmax.txt"),
    "2nd: Falling Branch Spade, owned by L. McKinney/L. Grimsley                                                 ~~\n"
    "# PARKED jr54: place-rank gap after Falling Branch Spade before Fox Run Casey (OCR blank; no surname invent)\n"
    "3rd; Meynell Climber, owned by Cheryl Edwards\n\n"
    "4th: Fox Run Casey, owned by Kathy Potter",
    "2nd: Falling Branch Spade, owned by L. McKinney/L. Grimsley\n"
    "3rd: Meynell Climber, owned by Cheryl Edwards\n\n"
    "4th: Fox Run Casey, owned by Kathy Potter",
    "climber3",
)

# 1996: 3rd; Baybriar Kato
fix(
    resolve("2026-11-04_150545_ocr_hqmax.txt"),
    "2nd: Quatro, owned by Robin Winsinger\n"
    "# PARKED jr54: place-rank gap after Quatro before Easton Point Duke (OCR blank; no surname invent)\n"
    "3rd; Baybriar Kato, owned by Kathryn Franklin                                                                  ,\n"
    "4th: Easton Point Duke, owned by Sally Gay",
    "2nd: Quatro, owned by Robin Winsinger\n"
    "3rd: Baybriar Kato, owned by Kathryn Franklin\n"
    "4th: Easton Point Duke, owned by Sally Gay",
    "kato3",
)

# 1996: 3rd; Oakfield Moe Mandy
fix(
    resolve("2026-11-04_154359_ocr_hqmax.txt"),
    "2nd: Heaven Hill Chipper, owned by Doug Stephenson\n"
    "# PARKED jr54: place-rank gap after Heaven Hill Chipper before RA Flash (OCR blank; no surname invent)\n"
    "3rd; Oakfield Moe Mandy, owned by Phil & Suzy Cunningham\n"
    "4th: RA Flash, owned by RA Terriers                                                                                  _",
    "2nd: Heaven Hill Chipper, owned by Doug Stephenson\n"
    "3rd: Oakfield Moe Mandy, owned by Phil & Suzy Cunningham\n"
    "4th: RA Flash, owned by RA Terriers",
    "mandy3",
)

# 1996: lead junk before Heaven Hill Chipper 2nd
fix(
    resolve("2026-11-04_154359_ocr_hqmax.txt"),
    "           1st: Nevada, owned by Laura O'Leary\n"
    "# PARKED jr54: place-rank gap after Nevada before Astro (OCR blank; no surname invent)\n\n"
    "4        2nd: Heaven Hill Chipper, owned by Doug Stephenson                                                       ~~\n\n"
    "3rd: Astro, owned by Chris Boesel",
    "1st: Nevada, owned by Laura O'Leary\n\n"
    "2nd: Heaven Hill Chipper, owned by Doug Stephenson\n\n"
    "3rd: Astro, owned by Chris Boesel",
    "chipper2",
)

# 1996: 2nd; Farmcliff Donny
fix(
    resolve("2026-11-04_154359_ocr_hqmax.txt"),
    "1st: Petey, owned by Kathy Hunter                                                                                  :\n"
    "# PARKED jr54: place-rank gap after Petey before Farmcliff Sugar (OCR blank; no surname invent)\n"
    "2nd; Farmcliff Donny, owned by Bob Franklin                                                                           _\n"
    "3rd: Farmcliff Sugar, owned by Genie Franklin",
    "1st: Petey, owned by Kathy Hunter\n"
    "2nd: Farmcliff Donny, owned by Bob Franklin\n"
    "3rd: Farmcliff Sugar, owned by Genie Franklin",
    "donny2",
)
