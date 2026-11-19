"""2000 Vol II batch1 early PDF clears."""
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


repl(
    "3rd: Little Eden Banshee, owned by Rick & Mary Thornton\n"
    "5th: Farmstead Holly, owned by Kathy Hunter\n",
    "3rd: Little Eden Banshee, owned by Rick & Mary Thornton\n"
    "4th: Highwater Banjo, owned by Ann Shepard\n"
    "5th: Farmstead Holly, owned by Kathy Hunter\n",
    "Holly +Banjo",
)

repl(
    "Championship Certificate, 10 up to 12 1/2\" Entries: 6\n"
    "1st: Fox Valley Little Miss Lily, owned by Jennifer Gilligan\n"
    "2nd: Bouncin Mouse, owned by Kim Wavrin\n"
    "5th: Windsor Harli, owned by Scott & Susan Aeppli\n"
    "Champion: Leona, owned by Dave Hennes\n"
    "Reserve: Mockingpird Hills Betsy, owned by Nancy Loberg\n",
    "Championship Certificate, 10 up to 12 1/2\" Entries: 6\n"
    "Champion: Leona, owned by Dave Hennes\n"
    "Reserve: Mockingbird Hills Betsy, owned by Nancy Loberg\n"
    "3rd: Zoie, owned by Joanne Van Hom\n"
    "4th: Windsor Harli, owned by Scott & Susan Aeppli\n"
    "5th: Fox Valley Little Miss Lily, owned by Jennifer Gilligan\n"
    "6th: Bouncin Mouse, owned by Kim Wavrin\n",
    "Harli champ cert",
)

repl(
    "4th: Vixen Trace Dapper Dan, owned by Russ & Barbara Gilford\n"
    "5th: Rain Dance Apache, owned by Pam Shepherd\n"
    "6th: Rain Dance Apache, owned by Pam Shepherd\n",
    "4th: Vixen Trace Dapper Dan, owned by Russ & Barbara Gilford\n"
    "5th: Rain Dance Apache, owned by Pam Shepherd\n",
    "noop apache",
)

HQ.write_text(text, encoding="utf-8")
print("applied", n)
print("gaps", count_gaps(text.splitlines()))
