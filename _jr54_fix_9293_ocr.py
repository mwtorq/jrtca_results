"""Honest 1992/1993 place-prefix OCR recoveries (no invented surnames/placements)."""
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


# 1992: Parmeliff Gretel was invisible 4th
fix(
    resolve("2026-11-03_214057_ocr_hqmax.txt"),
    "3rd: Foxfield Flor of The Hollow, owned by The Hollow Terriers\n"
    "# PARKED jr54: place-rank gap after Foxfield Flor of The Hollow before unknown (OCR blank; no surname invent)\n\n"
    "'Parmeliff:Gretel,, owned:by:Bob:Franklin- +\n\n"
    "5th: North Country Pinocchio, owned by Norah Risley",
    "3rd: Foxfield Flor of The Hollow, owned by The Hollow Terriers\n\n"
    "4th: Farmeliff Gretel, owned by Bob Franklin\n\n"
    "5th: North Country Pinocchio, owned by Norah Risley",
    "gretel4",
)

# 1993: Farmeliff Chip 3rd; with semicolon/junk
fix(
    resolve("2026-11-04_000731_ocr_hqmax.txt"),
    "2nd: Farmeliff Kermit, ownedgay, Bob Franidits\n"
    "# PARKED jr54: place-rank gap after Farmeliff Kermit before The Hollow Tracker (OCR blank; no surname invent)\n"
    "3rd;.-. Rarmeliffi. Chip,;owned by-Genie Er\n"
    "4th: The Hollow Tracker, owned by The Hollow. Terriers",
    "2nd: Farmeliff Kermit, owned by Bob Franklin\n"
    "3rd: Farmeliff Chip, owned by Genie Franklin\n"
    "4th: The Hollow Tracker, owned by The Hollow. Terriers",
    "chip3",
)

# 1993: Farmeliff Snowflake 2nd
fix(
    resolve("2026-11-04_000731_ocr_hqmax.txt"),
    "1st: Foxfield Flor of The Hollow, owned by The Hollow Terriers\n"
    "# PARKED jr54: place-rank gap after Foxfield Flor of The Hollow before Claydale Twigg of Thimble Farm (OCR blank; no surname invent)\n\n"
    "2nggaiiermclift Snowflake, owned.by Genie Frariklin®\n\n"
    "3rd: Claydale Twigg of Thimble Farm, owned by Val Wasch",
    "1st: Foxfield Flor of The Hollow, owned by The Hollow Terriers\n\n"
    "2nd: Farmeliff Snowflake, owned by Genie Franklin\n\n"
    "3rd: Claydale Twigg of Thimble Farm, owned by Val Wasch",
    "snowflake2",
)

# 1993: rd: → 3rd: Ravenswood Excel
fix(
    resolve("2026-11-04_000731_ocr_hqmax.txt"),
    "2nd: Bay Briar Dallas, owned by Larry Hartis\n"
    "# PARKED jr54: place-rank gap after Bay Briar Dallas before Foxfield Sprig of Courtwood (OCR blank; no surname invent)\n\n"
    "rd: Ravenswood Excel, owned by Ray & Jean Derrick\n\n"
    "4th:  Foxfield Sprig of Courtwood, owned by Rusty & Debbie Graydon",
    "2nd: Bay Briar Dallas, owned by Larry Hartis\n\n"
    "3rd: Ravenswood Excel, owned by Ray & Jean Derrick\n\n"
    "4th:  Foxfield Sprig of Courtwood, owned by Rusty & Debbie Graydon",
    "excel3",
)

# 1993: leading junk before 3rd: Windermere Shark
fix(
    resolve("2026-11-04_001048_ocr_hqmax.txt"),
    "2nd: SHENNANIGAN'S SUEDE OF BRIARPATCH, owned by Terri & Jack Batzer\n"
    "# PARKED jr54: place-rank gap after SHENNANIGAN'S SUEDE OF BRIARPATCH before THE HOLLOW SCAMPER (OCR blank; no surname invent)\n"
    "7           3rd: WINDERMERE SHARK, owned by Linda Cowasjee\n"
    "4th: THE HOLLOW SCAMPER, owned by Margaret Wheeler Garvin Warner",
    "2nd: SHENNANIGAN'S SUEDE OF BRIARPATCH, owned by Terri & Jack Batzer\n"
    "3rd: WINDERMERE SHARK, owned by Linda Cowasjee\n"
    "4th: THE HOLLOW SCAMPER, owned by Margaret Wheeler Garvin Warner",
    "shark3",
)

# 1993: 3rd; → 3rd: Cottonwood Worry
fix(
    resolve("2026-11-04_001704_ocr_hqmax.txt"),
    "2nd: The Hollow Dallion of Earthworks, owned by Barbara Van Tuy!\n"
    "# PARKED jr54: place-rank gap after The Hollow Dallion of Earthworks before Jersey Devil Peter Built (OCR blank; no surname invent)\n\n"
    "3rd; Cottonwood Worry, owned by Nancee Cahill                                                                         —_\n"
    "4th: Jersey Devil Peter Built, owned by Charles & Kim Cramer",
    "2nd: The Hollow Dallion of Earthworks, owned by Barbara Van Tuy!\n\n"
    "3rd: Cottonwood Worry, owned by Nancee Cahill\n"
    "4th: Jersey Devil Peter Built, owned by Charles & Kim Cramer",
    "worry3",
)
