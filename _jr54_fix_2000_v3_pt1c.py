"""Seabee class restructure + Calico false-place demote."""
from pathlib import Path
import sys

sys.path.insert(0, ".")
from _jr54_strip_place_prefix_junk import count_gaps

path = list(Path("Updated Yearbook Scans").rglob("2000 Vol III pt 1_ocr_hqmax.txt"))[0]
text = path.read_text(encoding="utf-8", errors="replace")
before = count_gaps(text.splitlines())

reps = [
    (
        "seabee",
        "Bitches, 1 yr. & older, 10 up to 12 1/2\" Entries: 5\n"
        "1st: Browns Valley Mustang Sally, owned by L. & A. Wendland\n"
        "2nd: Salishan Puff, owned by Daina Fiddler\n"
        "3rd: Sow's Ear Seabee, owned by John Rentro\n"
        "# PARKED jr54: place-rank gap after Sow's Ear Seabee before Brandywine Truffles (OCR blank; no surname invent)\n"
        "5th: Brandywine Truffles, owned by Cathy Hedberg",
        "Bitches, 1 yr. & older, 10 up to 12 1/2\", r/br Entries: 6\n"
        "1st: Fox Run Reba, owned by Sherri Rossmiller\n"
        "2nd: Boggsborough Bizzie, owned by Robert & Linda Fleck\n"
        "3rd: Sow's Ear Seabee, owned by John Renfro\n"
        "4th: Rose Tumble Asta, owned by Paula Cunningham\n"
        "5th: Rushill Spice, owned by Judie Baker/Janice Freimark\n"
        "6th: Brandywine Truffles, owned by Cathy Hedberg",
    ),
    (
        "calico",
        "2nd: Woods End Calico, owned by Doug & Noreen Loranger\n"
        "# PARKED jr54: place-rank gap after Woods End Calico before Little Eden Thriller (OCR blank; no surname invent)\n"
        "4th: Little Eden Thriller, owned by Michelle Ward\n"
        "5th: Sows Ear Snippet, owned by Karen McCarthy\n"
        "6th: JRTCA WORKING TERRIER CHAMPION & RESERVE Pur\n"
        "Champion: Little Eden Thriller, owned by Michelle Ward",
        "2nd: Woods End Calico, owned by Doug & Noreen Loranger\n"
        "BEST WORKING TERRIER BITCH & RESERVE\n"
        "Best: Sow's Ear Snippet, owned by Karen McCarthy\n"
        "Reserve: Little Eden Thriller, owned by Michelle Ward\n"
        "JRTCA WORKING TERRIER CHAMPION & RESERVE\n"
        "Champion: Sow's Ear Snippet, owned by Karen McCarthy",
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
