"""2001 Vol I batch4 — residual clears from existing OCR (Trixie Hailey, Albert Mocha)."""
from pathlib import Path
import sys

sys.path.insert(0, ".")
from _jr54_strip_place_prefix_junk import count_gaps

HQ = Path(r"Updated Yearbook Scans/2001 Yearbook Vol 1/2001 Vol I_ocr_hqmax.txt")
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


# Trixie cert: OCR p48 has 5th Hailey then 6th Trixie (HQ had 6 then 5)
repl(
    "4th: Terrier-ific Wild Child, owned by Sammy & Danetta Hopewell\n"
    "6th: R.A. Trixie, owned by John & Judy Tyno\n"
    "5th: Fox Cry Hailey, owned by Mike & Linda Trulock\n",
    "4th: Terrier-ific Wild Child, owned by Sammy & Danetta Hopewell\n"
    "5th: Fox Cry Hailey, owned by Mike & Linda Trulock\n"
    "6th: R.A. Trixie, owned by John & Judy Tyno\n",
    "Trixie cert Hailey 5th order",
)

# Bred by Exhibitor Dog: 4th J&J Mocha Pudge before page-break Presley 5th (OCR p77)
repl(
    "3rd: Achin' Acres Albert, owned by Leslie Bonnette\n"
    "Troon Quarry 2001 Terrier Trial II\n"
    "--- page 78 ---\n"
    "--- column LEFT ---\n"
    "5th: Coldwater Presley, owned by Michael Healy\n",
    "3rd: Achin' Acres Albert, owned by Leslie Bonnette\n"
    "4th: J&J Mocha Pudge, owned by J. Baker/J. Freimark\n"
    "Troon Quarry 2001 Terrier Trial II\n"
    "--- page 78 ---\n"
    "--- column LEFT ---\n"
    "5th: Coldwater Presley, owned by Michael Healy\n",
    "Albert +Mocha Pudge 4th",
)

before = count_gaps(text.splitlines())
HQ.write_text(text, encoding="utf-8")
after = count_gaps(HQ.read_text(encoding="utf-8").splitlines())
print("replacements", n, "gaps", before, "->", after)
