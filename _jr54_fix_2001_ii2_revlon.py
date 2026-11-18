"""Fill Revlon→Carley 2nd (Lickity Split Sassy) in 2001 Vol II pt2 + Paumanok."""
from pathlib import Path
import sys

sys.path.insert(0, ".")
from _jr54_strip_place_prefix_junk import count_gaps

OLD = (
    "1st: Lost Acres Revlon, owned by Karen McCarthy\n"
    "# PARKED jr54: place-rank gap after Lost Acres Revlon before Bent Creek Carley (OCR blank; no surname invent)\n"
    "3rd: Bent Creek Carley, owned by Marc & Laura Cormier"
)
NEW = (
    "1st: Lost Acres Revlon, owned by Karen McCarthy\n"
    "2nd: Lickity Split Sassy, owned by Bob Franklin\n"
    "3rd: Bent Creek Carley, owned by Marc & Laura Cormier"
)

for name in [
    "2001 Vol II pt 2_ocr_hqmax.txt",
    "2001 Paumanok Farmstead Dutchess County_ocr_hqmax.txt",
]:
    paths = list(Path("Updated Yearbook Scans").rglob(name))
    if not paths:
        print("NOFILE", name)
        continue
    p = paths[0]
    text = p.read_text(encoding="utf-8", errors="replace")
    before = count_gaps(text.splitlines())
    n = text.count(OLD)
    if n == 0:
        print("MISS", name)
        continue
    text = text.replace(OLD, NEW)
    after = count_gaps(text.splitlines())
    p.write_text(text, encoding="utf-8", newline="\n")
    print(name, "x", n, before, "->", after)
