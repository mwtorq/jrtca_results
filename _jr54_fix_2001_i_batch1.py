"""2001 Vol I batch1 — Coal Tree Farmcliff OCR + racing unsmash (PDF p37-38)."""
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


repl(
    "3rd: Karal Otter, owned by Alan & Karen Cooper\n"
    "HYimmsEamicliffiGeorgeXownedibyaBobiErankiin\n"
    "5th: Milton, owned by Barbara Barrett\n",
    "3rd: Karal Otter, owned by Alan & Karen Cooper\n"
    "4th: Farmcliff George, owned by Bob Franklin\n"
    "5th: Milton, owned by Barbara Barrett\n",
    "George 4th",
)

repl(
    "2nd: Brookside Brass, owned by Debbie LaMantia\n"
    "GrammmEarmelifioenownediby; Bob Franklins\n"
    "4th: Silent Partner Tow Truck, owned by Heath Ogbum\n",
    "2nd: Brookside Brass, owned by Debbie LaMantia\n"
    "3rd: Farmcliff Joe, owned by Bob Franklin\n"
    "4th: Silent Partner Tow Truck, owned by Heath Ogbum\n",
    "Joe 3rd",
)

repl(
    "1st: Larches Spirit of Starphyre, owned by Virginia Mei\n"
    "@ndmmbEamcliffiPeggienownedibyiBobiFranklinms\n"
    "3rd: Ash Creek Pin Up, owned by Mary Lou Cassone\n",
    "1st: Larches Spirit of Starphyre, owned by Virginia Mei\n"
    "2nd: Farmcliff Peggie, owned by Bob Franklin\n"
    "3rd: Ash Creek Pin Up, owned by Mary Lou Cassone\n",
    "Peggie 2nd",
)

repl(
    "2nd: The Larches Liam McGee, owned by Donald & Joan LaPlace\n"
    "3rd: Fox Run Topper, owned by Rick & Mary Thomton\n"
    "5th: Riverview Calvin, owned by Karen Vemon\n"
    "6th: The Folly Deuce, owned by Rick & Mary Thomton\n",
    "2nd: The Larches Liam McGee, owned by Donald & Joan LaPlace\n"
    "3rd: Long Hope Mickey, owned by Bob Franklin\n"
    "4th: Fox Run Topper, owned by Rick & Mary Thornton\n"
    "5th: Riverview Calvin, owned by Karen Vernon\n"
    "6th: The Folly Deuce, owned by Rick & Mary Thornton\n",
    "Veteran Dog +Mickey",
)

repl(
    "2nd: Lakeshore Tackle, owned by Dale & Cathy Larson\n"
    "3rd: Sow's Ear Einstein, owned by Rick & Mary Thomton\n"
    "5th: Long Hope Sabre, owned by Bob Franklin\n"
    "5th: Morgan Hill Dewey, owned by Don & Gail Stock\n",
    "2nd: Lakeshore Tackle, owned by Dale & Cathy Larson\n"
    "3rd: Sow's Ear Einstein, owned by Rick & Mary Thornton\n"
    "4th: Oliver Twist, owned by Kathryn Franklin\n"
    "5th: Morgan Hill Dewey, owned by Don & Gail Stock\n",
    "Einstein +Oliver/Dewey",
)

repl(
    "1st: Zoro, owned by Laura Mutton\n"
    "2nd: Kenswick Dottie, owned by Sandy & Joel McEleamey\n"
    "4th: Famncliff Liz, owned by Bob Franklin\n"
    "5th: The Eallv Pinar numad hir KIam: © Dials Th mod oo\n",
    "1st: Zorro, owned by Laura Mutton\n"
    "2nd: Kenswick Dottie, owned by Sandy & Joel McElearney\n"
    "3rd: Long Hope Sable, owned by Bob Franklin\n"
    "Pups, 9 up to 12 months, over 12 1/2-15\" Entries: 4\n",
    "Zorro/Dottie +Sable (Liz was wrong class)",
)

repl(
    "1st: Farmcliff Holland, owned by Doug & Sue Tack\n"
    "3rd: Long Hope Mickey, owned by Bob Franklin\n"
    "3rd: Woods End Calico, owned by Doug & Noreen Loranger\n"
    "Ero PLZ ¥ownedibyaBobiEEmidine™\n"
    "5th: The Folly Piper, owned by Mary & Rick Thomton\n"
    "6th: The Folly Lucy, owned by Mary & Rick Thomton\n",
    "1st: Farmcliff Holland, owned by Doug & Sue Tack\n"
    "2nd: Long Hope Tini Wini, owned by Nellie Niewola\n"
    "3rd: Woods End Calico, owned by Doug & Noreen Loranger\n"
    "4th: Farmcliff Liz, owned by Bob Franklin\n"
    "5th: The Folly Piper, owned by Mary & Rick Thornton\n"
    "6th: The Folly Lucy, owned by Mary & Rick Thornton\n",
    "Holland +Tini Wini/Liz",
)

repl(
    "1st: Bugsy, owned by Richard & Annette Kent\n"
    "2nd: Mustang, owned by Jill Goodman\n"
    "KrimmlongIHepSNTkeyae wed byBobiRFaRKIR:\n"
    "4th: Wyndcroft Tiller, owned by Margaret & Richard Minutello\n",
    "1st: Bugsy, owned by Richard & Annette Kent\n"
    "2nd: Mustang, owned by Jill Goodman\n"
    "3rd: Long Hope Mickey, owned by Bob Franklin\n"
    "4th: Wyndcroft Tiller, owned by Margaret & Richard Minutello\n",
    "Veterans +Mickey 3rd",
)

HQ.write_text(text, encoding="utf-8")
print("applied", n)
print("gaps", count_gaps(text.splitlines()))
