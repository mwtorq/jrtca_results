"""More honest 2000 Vol III pt1 fills from 19 to 64.txt."""
from pathlib import Path
import sys

sys.path.insert(0, ".")
from _jr54_strip_place_prefix_junk import count_gaps

path = list(Path("Updated Yearbook Scans").rglob("2000 Vol III pt 1_ocr_hqmax.txt"))[0]
text = path.read_text(encoding="utf-8", errors="replace")
before = count_gaps(text.splitlines())

reps = [
    (
        "molly",
        "1st: Kenswick Danger, owned by Tonya Adams\n"
        "2nd: Fancy Jax Nikita, owned by Allen & Denise Wessel\n"
        "3rd: Sweetie, owned by Sheryl Evans\n"
        "--- column RIGHT ---\n"
        "1st: Salt Valley Fanny, owned by Richard & Jan Finnerty\n"
        "2nd: Briar Patch Molly, owned by Richard & Jan Finnerty\n"
        "# PARKED jr54: place-rank gap after Briar Patch Molly before Tortilla Flat Fiesta (OCR blank; no surname invent)\n"
        "4th: Tortilla Flat Fiesta, owned by Patti Freemark",
        "1st: Kenswick Danger, owned by Tonya Adams\n"
        "2nd: Fancy Jax Nikita, owned by Allen & Denise Wessel\n"
        "3rd: Sweetie, owned by Sheryl Evans\n"
        "4th: Tortilla Flat Fiesta, owned by Patti Freemark\n"
        "5th: Salt Valley Fanny, owned by Richard & Jan Finnerty\n"
        "6th: Briar Patch Molly, owned by Richard & Jan Finnerty",
    ),
    (
        "scatter",
        "3rd: Burrows Inn Scatter, owned by Cheryl & Robby Robson\n"
        "# PARKED jr54: place-rank gap after Burrows Inn Scatter before Rebel Yelp Georgia (column smash; OCR blank 4th/5th; no surname invent)\n"
        "--- column RIGHT ---\n"
        "6th: Rebel Yelp Georgia, owned by Judith Stuckey",
        "3rd: Burrows Inn Scatter, owned by Cheryl & Robby Robson\n"
        "4th: Brooks Chase Luna, owned by Brooks Kelley/Joe Shapiro\n"
        "5th: Harbor Site Mambo, owned by Michael Ireland\n"
        "6th: Rebel Yelp Storm, owned by Scott & Diana Alguire",
    ),
    (
        "bella",
        "3rd: The Folly Bella, owned by Dorothy Whiting\n"
        "# PARKED jr54: place-rank gap after The Folly Bella before Little Eden Folly (OCR blank; no surname invent)\n"
        "5th: Little Eden Folly, owned by George Anderson",
        "3rd: The Folly Bella, owned by Dorothy Whiting\n"
        "4th: Kimberwick Popular, owned by Joyce Robin\n"
        "5th: Little Eden Folly, owned by George Anderson",
    ),
    (
        "chelsea",
        "3rd: White Phantom Chelsea, owned by Sandy Kiteley\n"
        "# PARKED jr54: place-rank gap after White Phantom Chelsea before Live Wire Noa (OCR blank; no surname invent)\n"
        "5th: Live Wire Noa, owned by C. & J. Kemp",
        "3rd: White Phantom Chelsea, owned by Sandy Kiteley\n"
        "4th: Windever Crumb, owned by Lea Boa\n"
        "5th: Live Wire Noa, owned by C. & J. Kemp",
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
