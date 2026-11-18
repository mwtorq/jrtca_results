"""Honest fixes: demote No-qualifiers note; attach Three Oaks Penny to empty 1st."""
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


# 1991: "1st: No qualifiers" is a class note, not a place — demote so 3rd page-top isn't a false gap
fix(
    resolve("2026-11-03_205300_ocr_hqmax.txt"),
    "1st: No qualifiers                                                                                                              _\n"
    "# PARKED jr54: place-rank gap after No qualifiers                            before Willowall Mr. Nelson of Honey Hill (OCR blank; no surname invent)\n"
    "1991 JRTCA Yearbook, Vol. I                    62                            JRTNNC Trial Results         _\n\n"
    "--- page 13 ---\n"
    "3rd: Willowall Mr. Nelson of Honey Hill, owned by Susan Porter                                    _",
    "# note jr54: no qualifiers (class note; not a place)\n"
    "1991 JRTCA Yearbook, Vol. I                    62                            JRTNNC Trial Results\n\n"
    "--- page 13 ---\n"
    "# PARKED jr54: page-top 3rd Willowall Mr. Nelson (prior places OCR blank across break; no surname invent)\n"
    "3rd: Willowall Mr. Nelson of Honey Hill, owned by Susan Porter",
    "noqual",
)

# 1993: attach Penny to empty 1st: (still parks 2-4 blanks)
fix(
    resolve("2026-11-04_001704_ocr_hqmax.txt"),
    "1st:\n"
    "# PARKED jr54: place-rank gap after unknown before Three Oaks Britches (OCR blank; no surname invent)\n\n"
    "Three Oaks Penny, owned by Ken Eidson\n\n"
    "1993 JRTCA Yearbook, Vol. II\n\n"
    "28\n\n"
    "Peach State Trial Results\n\n"
    "--- page 15 ---\n"
    "5th: Three Oaks Britches, owned by Carolyn McGaughey                                                             _",
    "1st: Three Oaks Penny, owned by Ken Eidson\n"
    "# PARKED jr54: place-rank gap after Three Oaks Penny before Three Oaks Britches (OCR blank 2nd-4th; no surname invent)\n\n"
    "1993 JRTCA Yearbook, Vol. II\n\n"
    "28\n\n"
    "Peach State Trial Results\n\n"
    "--- page 15 ---\n"
    "5th: Three Oaks Britches, owned by Carolyn McGaughey",
    "penny1",
)

# 1994: split Kiwi C6th glue (honesty; may not change gap count)
fix(
    resolve("Document_2026-11-04_105927_ocr_hqmax.txt"),
    "5th: Kiwi C6th: Molly Brown, owned by Dianne Crone",
    "5th: Kiwi\n"
    "6th: Molly Brown, owned by Dianne Crone",
    "kiwi6",
)

# 1996: drop bare orphan '5th' before real 5th: Oakfield Annie
fix(
    resolve("1996 Vol 1 pg 111-160 back_ocr_hqmax.txt"),
    "3rd: Briarpatch Brash, owned by Jane Griffin\n"
    "# PARKED jr54: place-rank gap after Briarpatch Brash before Oakfield Annie (OCR blank; no surname invent)\n"
    "5th\n"
    "5th: Oakfield Annie, owned by Albert & Heather Dickau",
    "3rd: Briarpatch Brash, owned by Jane Griffin\n"
    "# PARKED jr54: place-rank gap after Briarpatch Brash before Oakfield Annie (OCR blank 4th; no surname invent)\n"
    "5th: Oakfield Annie, owned by Albert & Heather Dickau",
    "bare5a",
)

# 1996: bare 5th with no dog before 6th Chaz — leave park; remove bare token only
fix(
    resolve("1996 Vol II pg 23-92 front_ocr_hqmax.txt"),
    "4th: Fox Run Sonic, owned by Sandra Ferber\n"
    "# PARKED jr54: place-rank gap after Fox Run Sonic before Hillside Chaz (OCR blank; no surname invent)\n"
    "5th\n"
    "6th: Hillside Chaz, owned by Doug & Noreen Loranger",
    "4th: Fox Run Sonic, owned by Sandra Ferber\n"
    "# PARKED jr54: place-rank gap after Fox Run Sonic before Hillside Chaz (OCR blank 5th; no surname invent)\n"
    "6th: Hillside Chaz, owned by Doug & Noreen Loranger",
    "bare5b",
)
