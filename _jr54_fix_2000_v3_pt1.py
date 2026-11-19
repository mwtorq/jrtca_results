"""Honest 2000 Vol III pt1 fills from Yearbook Scans/2000 Vol III/19 to 64.txt + twin OCR."""
from pathlib import Path
import sys

sys.path.insert(0, ".")
from _jr54_strip_place_prefix_junk import count_gaps

FILES = [
    "2000 Vol III pt 1_ocr_hqmax.txt",
]

# Common replacements applied to every matching file (duplicates included via replace_all).
REPLACEMENTS: list[tuple[str, str, str]] = [
    (
        "stinger",
        "Championship Certificate, 10 up to 1215\" Entries: 22\n"
        "1st: Button Top Stinger, owned by Debby Calloway\n"
        "# PARKED jr54: place-rank gap after Button Top Stinger before Anderson Acres Tater Bug (OCR blank; no surname invent)\n"
        "3rd: Anderson Acres Tater Bug, owned by Tony Anderson\n"
        "4th: Gill's Creek Scout, owned by Brooks Kelley/Joe Shapiro\n"
        "5th: Anderson Acres Rascal, owned by Tony Anderson\n"
        "Champion: Arrowhead Norma Sue, owned by Jackie Phillips\n"
        "Champion: Porkchop, owned by Kevin & Shannon Osby\n"
        "Reserve: R.A. Legacy, owned by Pam Williams",
        "Championship Certificate, 10 up to 1215\" Entries: 22\n"
        "Champion: Arrowhead Norma Sue, owned by Jackie Phillips\n"
        "Champion: Porkchop, owned by Kevin & Shannon Osby\n"
        "Reserve: R.A. Legacy, owned by Pam Williams\n"
        "3rd: Anderson Acres Tater Bug, owned by Tony Anderson\n"
        "4th: Gill's Creek Scout, owned by Brooks Kelley/Joe Shapiro\n"
        "5th: Anderson Acres Rascal, owned by Tony Anderson\n"
        "6th: Button Top Stinger, owned by Debby Calloway",
    ),
    (
        "ruffian",
        "2nd: Diamond E Ruffian, owned by Cathy Eick\n"
        "# PARKED jr54: place-rank gap after Diamond E Ruffian before Winslow Genevieve (OCR blank 3rd/4th; no surname invent)\n"
        "5th: Winslow Genevieve, owned by Lisa Fitzgerald\n"
        "5th: Ash Creek Pinch, owned by Mary Lou Mogrovejo",
        "2nd: Diamond E Ruffian, owned by Cathy Eick\n"
        "3rd: Gadget, owned by Kathryn Franklin\n"
        "4th: Winslow Genevieve, owned by Lisa Fitzgerald\n"
        "5th: Ash Creek Pinch, owned by Mary Lou Mogrovejo",
    ),
    (
        "hawk",
        "1st: Natural Instinct Flip, owned by Lynda Clement\n"
        "--- column RIGHT ---\n"
        "1st: Pleasant Hill Hawk, owned by Jill Denker\n"
        "# PARKED jr54: place-rank gap after Pleasant Hill Hawk before Muscle Russell Flyer (OCR blank 2nd/3rd; no surname invent)\n"
        "4th: Muscle Russell Flyer, owned by Jill Goodman",
        "1st: Natural Instinct Flip, owned by Lynda Clement\n"
        "2nd: Brandywine Paco, owned by Diane Wright\n"
        "3rd: Pleasant Hill Hawk, owned by Jill Denker\n"
        "4th: Muscle Russell Flyer, owned by Jill Goodman",
    ),
    (
        "wee_won",
        "2nd: Sass 'N Dash Molly, owned by Mary Webb\n"
        "3rd: Long Hope Wee Won, owned by Nellie Niewola\n"
        "# PARKED jr54: place-rank gap after Long Hope Wee Won before The Hollow Primrose (OCR blank; no surname invent)\n"
        "5th: The Hollow Primrose, owned by Linda St. Quintin",
        "2nd: Sass 'N Dash Molly, owned by Mary Webb\n"
        "3rd: Long Hope Wee Won, owned by Nellie Niewola\n"
        "4th: Farmstead Bella, owned by Tricia Candido\n"
        "5th: The Hollow Primrose, owned by Linda St. Quintin",
    ),
    (
        "deuce_nick",
        "1st: The Folly Deuce, owned by Rick & Mary Thornton\n"
        "# PARKED jr54: place-rank gap after The Folly Deuce before Nick (column smash; OCR blank 2nd; no surname invent)\n"
        "--- column RIGHT ---\n"
        "3rd: Nick, owned by Carole Nicolson",
        "1st: The Folly Deuce, owned by Rick & Mary Thornton\n"
        "2nd: Sass 'N Dash Trevor, owned by Cynthia Palmer\n"
        "3rd: Nick, owned by Carole Nicolson",
    ),
    (
        "mockingbird",
        "3rd: Mockingbird Hills KRKLN Rose, owned by Pam Larson\n"
        "# PARKED jr54: place-rank gap after Mockingbird Hills KRKLN Rose before Tybalt Cauplet (OCR blank; no surname invent)\n"
        "5th: Tybalt Cauplet, owned by Julie Anderson",
        "3rd: Mockingbird Hills KRKLN Rose, owned by Pam Larson\n"
        "4th: Nampara Fritz, owned by Mary Labrosse\n"
        "5th: Tybalt Cauplet, owned by Julie Anderson",
    ),
]


def apply(path: Path) -> tuple[int, int]:
    text = path.read_text(encoding="utf-8", errors="replace")
    before = count_gaps(text.splitlines())
    for label, old, new in REPLACEMENTS:
        n = text.count(old)
        if n == 0:
            print("MISS", path.name, label)
            continue
        text = text.replace(old, new)
        print(label, path.name, "x", n)
    after = count_gaps(text.splitlines())
    path.write_text(text, encoding="utf-8", newline="\n")
    return before, after


def main() -> None:
    for name in FILES:
        paths = list(Path("Updated Yearbook Scans").rglob(name))
        if not paths:
            print("NOFILE", name)
            continue
        for p in paths:
            b, a = apply(p)
            print("file", p.name, b, "->", a)


if __name__ == "__main__":
    main()
