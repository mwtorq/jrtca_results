"""Honest mid-gap OCR place recoveries batch 2 (», 3d, 3rdsm, missing colon)."""
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


# 1991: reorder + Bride = 3rd
fix(
    resolve("2026-11-03_205300_ocr_hqmax.txt"),
    "1st: East Grinstead Abe Lincoln of Raheen, handled by Cecily Taylor\n"
    "# PARKED jr54: place-rank gap after East Grinstead Abe Lincoln of Raheen before unknown (OCR blank; no surname invent)\n\n"
    "3rd:\n"
    "2nd: Beau Jeste Anchor, handled by Dawn Nafus\n"
    "# PARKED jr54: place-rank gap after Beau Jeste Anchor before Hickory (OCR blank; no surname invent)\n\n"
    "Craigengar Bride, handled by Laura Petruska\n\n"
    "—_\n\n"
    "4th: Hickory, handled by Michael Gross",
    "1st: East Grinstead Abe Lincoln of Raheen, handled by Cecily Taylor\n\n"
    "2nd: Beau Jeste Anchor, handled by Dawn Nafus\n\n"
    "3rd: Craigengar Bride, handled by Laura Petruska\n\n"
    "4th: Hickory, handled by Michael Gross",
    "bride3",
)

# 1991: Pistol = 4th; drop empty misplaced 4th:
fix(
    resolve("2026-11-03_211319_ocr_hqmax.txt"),
    "2nd: Farmcliff Barney, owned by Bob & Genie Franklin\n"
    "# PARKED jr54: place-rank gap after Farmcliff Barney before unknown (OCR blank; no surname invent)\n\n"
    "4th:\n"
    "3rd: Briarpatch Jake, owned by Jack & Terri Batzer\n"
    "# PARKED jr54: place-rank gap after Briarpatch Jake before The Hollow Mr. Belvedere (OCR blank; no surname invent)\n\n"
    "Pleasant Valley Pistol of Briarpatch, owned by Jack & Terri Batzer\n\n"
    "5th: The Hollow Mr. Belvedere, owned by Laurie Lewis",
    "2nd: Farmcliff Barney, owned by Bob & Genie Franklin\n\n"
    "3rd: Briarpatch Jake, owned by Jack & Terri Batzer\n\n"
    "4th: Pleasant Valley Pistol of Briarpatch, owned by Jack & Terri Batzer\n\n"
    "5th: The Hollow Mr. Belvedere, owned by Laurie Lewis",
    "pistol4",
)

# 1994: 5th» Pee Wee
fix(
    resolve("2026-11-04_084255_ocr_hqmax.txt"),
    "4th: Farmcliff Kermit, owned by Bob & Genie Franklin\n"
    "# PARKED jr54: place-rank gap after Farmcliff Kermit before Jessie (OCR blank; no surname invent)\n\n"
    "5th» Farmecliff Pee Wee, owned by Bob & Genie Franklin                                       :\n"
    "6th: Jessie, owned by Clint Clayton",
    "4th: Farmcliff Kermit, owned by Bob & Genie Franklin\n\n"
    "5th: Farmecliff Pee Wee, owned by Bob & Genie Franklin\n"
    "6th: Jessie, owned by Clint Clayton",
    "peewee5",
)

# 1994: 3rd» Kermit
fix(
    resolve("2026-11-04_111102_ocr_hqmax.txt"),
    "2nd: Breezewood Jessie, owned by Clint Clayton\n"
    "# PARKED jr54: place-rank gap after Breezewood Jessie before Trapper of The Manor (OCR blank; no surname invent)\n"
    "3rd» Farmeliff Kermit, owned by Bob Franklin\n"
    "4th: Trapper of The Manor, owned by Tarchini & Young",
    "2nd: Breezewood Jessie, owned by Clint Clayton\n"
    "3rd: Farmeliff Kermit, owned by Bob Franklin\n"
    "4th: Trapper of The Manor, owned by Tarchini & Young",
    "kermit3",
)

# 1995: 5th» Big Sky Annie
fix(
    resolve("2026-11-04_130959_ocr_hqmax.txt"),
    "4th: The Larches Heart & Soul, owned by Joan & Donald LaPlacé       .                     .         :\n"
    "# PARKED jr54: place-rank gap after The Larches Heart & Soul before Fox Run Chase (OCR blank; no surname invent)\n"
    "5th» Big Sky.Annie of Farmeliff, owned by Doug Tack & Bob Franklin'\n"
    "6th: Fox Run Chase, owned by William O'Brien & Sandra Ferber ~",
    "4th: The Larches Heart & Soul, owned by Joan & Donald LaPlacé\n"
    "5th: Big Sky Annie of Farmeliff, owned by Doug Tack & Bob Franklin\n"
    "6th: Fox Run Chase, owned by William O'Brien & Sandra Ferber",
    "annie5",
)

# 1995: 3rdsm Erin
fix(
    resolve("2026-11-04_130959_ocr_hqmax.txt"),
    "2nd: Farmcliff Kermit, owned by Bob Franklin\n"
    "# PARKED jr54: place-rank gap after Farmcliff Kermit before Petey (OCR blank; no surname invent)\n"
    "3rdsm Farmcliff Erin, owned by Bob Franklin\n"
    "4th: Petey, owned by Kathy Hunter & Paul Finkernagel",
    "2nd: Farmcliff Kermit, owned by Bob Franklin\n"
    "3rd: Farmcliff Erin, owned by Bob Franklin\n"
    "4th: Petey, owned by Kathy Hunter & Paul Finkernagel",
    "erin3",
)

# 1995: 4th» Erin
fix(
    resolve("2026-11-04_143343_ocr_hqmax.txt"),
    "3rd: Jersey Devil Jean Jeanie, owned by Kim Cramer\n"
    "# PARKED jr54: place-rank gap after Jersey Devil Jean Jeanie before Killare Pippi (OCR blank; no surname invent)\n\n"
    "4th» Farmeliff Erin, owned by Bob Franklin\n\n"
    "5th: Killare Pippi, owned by Martin & Leona Roche",
    "3rd: Jersey Devil Jean Jeanie, owned by Kim Cramer\n\n"
    "4th: Farmeliff Erin, owned by Bob Franklin\n\n"
    "5th: Killare Pippi, owned by Martin & Leona Roche",
    "erin4",
)

# 1996: 2nd? Maybell
fix(
    resolve("2026-11-04_150238_ocr_hqmax.txt"),
    "1st: Foxton Locks Cricket, owned by Cheryl Costello                           ——       \"4\n"
    "# PARKED jr54: place-rank gap after Foxton Locks Cricket before Seaview Shag (OCR blank; no surname invent)\n"
    "--=2nd?Mischievous Maybell, owned by Rebecca Quick                                                         =\n\n"
    "3rd: Seaview Shag, owned by Marilynn Pryor",
    "1st: Foxton Locks Cricket, owned by Cheryl Costello\n"
    "2nd: Mischievous Maybell, owned by Rebecca Quick\n\n"
    "3rd: Seaview Shag, owned by Marilynn Pryor",
    "maybell2",
)

# 1996: 3d → 3rd KaCee Payton
fix(
    resolve("2026-11-04_151926_ocr_hqmax.txt"),
    "2nd: Foxnorton Wizard of Meadowlake, owned by Karen Reavis\n"
    "# PARKED jr54: place-rank gap after Foxnorton Wizard of Meadowlake before KaCee Reject (OCR blank; no surname invent)\n\n"
    "_. 3d: KaCee Payton of Windsor, owned by Kelcey Roberts\n"
    "4th: KaCee Reject, owned by Jeff Hamblin",
    "2nd: Foxnorton Wizard of Meadowlake, owned by Karen Reavis\n\n"
    "3rd: KaCee Payton of Windsor, owned by Kelcey Roberts\n"
    "4th: KaCee Reject, owned by Jeff Hamblin",
    "payton3",
)

# 1996: 3d → 3rd Corn Row Calumet
fix(
    resolve("2026-11-04_151926_ocr_hqmax.txt"),
    "2nd: Timber Ridge Rudger, owned by Jan Moore\n"
    "# PARKED jr54: place-rank gap after Timber Ridge Rudger before Swift River Jasper (OCR blank; no surname invent)\n"
    "_. 3d: Corn Row Calumet, owned by Phil Hawkins\n"
    "4th: Swift River Jasper, owned by Joni, Dale & Becky Green",
    "2nd: Timber Ridge Rudger, owned by Jan Moore\n"
    "3rd: Corn Row Calumet, owned by Phil Hawkins\n"
    "4th: Swift River Jasper, owned by Joni, Dale & Becky Green",
    "calumet3",
)

# 1996: fd → 3rd Wild Goose National
fix(
    resolve("2026-11-04_151926_ocr_hqmax.txt"),
    "2nd: Penny of Misty Moming, owned by Karen Richards\n"
    "# PARKED jr54: place-rank gap after Penny of Misty Moming before Red Oak Blue Bonnet (OCR blank; no surname invent)\n"
    "-; fd: Wild Goose National, owned by CJ & Ouida Harris\n"
    "4th: Red Oak Blue Bonnet, owned by Donnie & Rebecca Cox",
    "2nd: Penny of Misty Moming, owned by Karen Richards\n"
    "3rd: Wild Goose National, owned by CJ & Ouida Harris\n"
    "4th: Red Oak Blue Bonnet, owned by Donnie & Rebecca Cox",
    "national3",
)

# 1996: 4th missing colon Hillside Cooper
fix(
    resolve("2026-11-04_154359_ocr_hqmax.txt"),
    "3rd: Fleetwood Zeke, owned by Joe & Evelyn Landini\n"
    "# PARKED jr54: place-rank gap after Fleetwood Zeke before Hillside Buddy (OCR blank; no surname invent)\n\n"
    "4th Hillside Cooper, owned by Laura Harakaly                                                                  _\n\n"
    "5th: Hillside Buddy, owned by Laura Harakaly",
    "3rd: Fleetwood Zeke, owned by Joe & Evelyn Landini\n\n"
    "4th: Hillside Cooper, owned by Laura Harakaly\n\n"
    "5th: Hillside Buddy, owned by Laura Harakaly",
    "cooper4",
)
