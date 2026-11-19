"""2001 Vol III pt1 batch2 — youth smash, Wishbone, Twigg/Kermit, Paco, Teeni, Questor."""
from pathlib import Path
import sys

sys.path.insert(0, ".")
from _jr54_strip_place_prefix_junk import count_gaps

HQ = Path(r"Updated Yearbook Scans/2001 Yearbook Vol 3/2001 Vol III pt 1_ocr_hqmax.txt")
text = HQ.read_text(encoding="utf-8")
n0 = count_gaps(text.splitlines())
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


# Youth Handler + GTG + Agility rebuild (PDF p12)
repl(
    "Youth Handler                                               Entries: 6\n"
    "1st: Jeremy Black\n"
    "2nd: Taryn Lacey\n"
    "5th: Amelia Finnertyth: Bryan Schlingman\n"
    "5th: Anne Dalmadge\n"
    "Youth Handling Go-to-Ground                           Entries: 6\n"
    "1st: Anne Dalmadge\n"
    "2nd: Amelia Finnerty\n"
    "3rd: Wade Evansth: Ben Amettth: Taryn Laceyf Y\n"
    "Youth Handling Agility, On Lead Entries: 6\n"
    "2nd: Amelia Finnerty\n"
    "3rd: Taryn Laceyth: Bryan Schlingman\n"
    "--- page 13 ---\n"
    "--- column LEFT ---\n"
    "5th: Rushill Max, owned by Jerry & Eileen Stoecklein\n"
    "6th: Bridle Creek Dealer, owned by Joe & Linda Hosmer\n",
    "Youth Handler                                               Entries: 6\n"
    "1st: Jeremy Black\n"
    "2nd: Taryn Lacey\n"
    "3rd: Wade Evans\n"
    "4th: Amelia Finnerty\n"
    "5th: Bryan Schlingman\n"
    "6th: Anne Dalmadge\n"
    "Youth Handling Go-to-Ground                           Entries: 6\n"
    "1st: Anne Dalmadge\n"
    "2nd: Amelia Finnerty\n"
    "3rd: Wade Evans\n"
    "4th: Bryan Schlingman\n"
    "5th: Ben Arnett\n"
    "6th: Taryn Lacey\n"
    "Youth Handling Agility, On Lead Entries: 6\n"
    "1st: Anne Dalmadge\n"
    "2nd: Amelia Finnerty\n"
    "3rd: Taryn Lacey\n"
    "4th: Bryan Schlingman\n"
    "5th: Wade Evans\n"
    "6th: Ben Arnett\n"
    "--- page 13 ---\n"
    "--- column LEFT ---\n"
    "5th: Rushill Max, owned by Jerry & Eileen Stoecklein\n"
    "6th: Bridle Creek Dealer, owned by Joe & Linda Hosmer\n",
    "Youth Handler/GTG/Agility rebuild",
)

# Open Adult Wishbone class (PDF p15)
repl(
    "1st: R.A. Rowdy, owned by William Trulock\n"
    "2nd: Wishbone, owned by Tina Cambell\n"
    "5th: White Gate Soca, owned by Shelley Plant\n"
    "5th: Heaven Hill Minnie, owned by Rick Stephenson\n"
    "5th: Summer Sage, owned by Audie Sumner\n",
    "1st: R.A. Rowdy, owned by William Trulock\n"
    "2nd: Wishbone, owned by Tina Cambell\n"
    "3rd: R.A. Brightberry, owned by Zoe Blair\n"
    "4th: White Gate Soca, owned by Shelley Plant\n"
    "5th: Heaven Hill Minnie, owned by Rick Stephenson\n"
    "6th: Summer Sage, owned by Audie Sumner\n",
    "Wishbone Brightberry/Soca ranks",
)

# Bitches 10": Teeni 5th / Piper 6th not Eth/9th (PDF p18)
repl(
    "3rd:      Woods End Calico, owned by Doug &1 Noreen Loranger\n"
    "4th: Eth:      Long Hope Teeni Ween,  owned by Nello Niwola\n"
    "9th: The Folly Piper, owned by Rick & Mary Thomton\n",
    "3rd: Woods End Calico, owned by Doug & Noreen Loranger\n"
    "5th: Long Hope Teeni Weeni, owned by Nellie Niewola\n"
    "6th: The Folly Piper, owned by Rick & Mary Thornton\n",
    "Calico Teeni/Piper ranks",
)

# Veteran dogs over: Questor 4th + Mustang 5th (PDF p18)
repl(
    "2nd: Bugsy, owned by Richard & Annette Kent\n"
    "3rd: 4h: Questor, owned by Bill O'Brien\n"
    "6th: Wyndcroft Tiller, owned by Richie & Margaret Minutello\n",
    "2nd: Bugsy, owned by Richard & Annette Kent\n"
    "4th: Questor, owned by Bill O'Brien\n"
    "5th: Mustang, owned by Jill Goodman\n"
    "6th: Wyndcroft Tiller, owned by Richie & Margaret Minutello\n",
    "Bugsy Questor/Mustang",
)

# Veteran Dog: Farmcliff Kermit 3rd (2nd Mickey smashed) (PDF p19)
repl(
    "1st: Clay Dale Twigg, owned by Val Davis\n"
    "REIGN Ho peiNlickeyvaeo Whe HIbAB ob aGenieshianklin\n"
    "4th: Sass 'N Dash Solo, owned by Joan Stroh\n",
    "1st: Clay Dale Twigg, owned by Val Davis\n"
    "3rd: Farmcliff Kermit, owned by Bob & Genie Franklin\n"
    "4th: Sass 'N Dash Solo, owned by Joan Stroh\n",
    "Twigg +Kermit 3rd (2nd unscanned)",
)

# Gray Fox: Natasha/Chaos/Tally between Paco and Layla (PDF p19)
repl(
    "1st: Andlin Paco, owned by George Anderson\n"
    "--- column RIGHT ---\n"
    "5th: Andlin Layla Pearl, owned by Karen Howard\n"
    "6th: Lakeshore Tackle, owned by Cathy Larson\n",
    "1st: Andlin Paco, owned by George Anderson\n"
    "2nd: Morgan Hill Natasha, owned by Julie Waardenburg\n"
    "3rd: Ashland Chaos, owned by Barbara Bancroft\n"
    "4th: Double D Tally Ho, owned by Dorothy Whiting\n"
    "5th: Andlin Layla Pearl, owned by Karen Howard\n"
    "6th: Lakeshore Tackle, owned by Cathy Larson\n",
    "Paco +Natasha/Chaos/Tally",
)

# Veteran bitches over Heidi: Snowflake 3rd (PDF p18/17) — HQ Pepsi lead wrong
repl(
    "Veteran Bitches, 6 years & older, over 12 1/2-15\" Entries: 0\n"
    "1st: Whispering Winds Pepsi, owned by R. & M. Minutello\n"
    "2nd: Bittersweet Belle, owned by Doug & Noreen Loranger\n"
    "3rd:      Whispering Winds Heidi Ho, owned by Ken Yield\n"
    "5th:      Abby, owned by Richard 2 Annette Kent\n",
    "Veteran Bitches, 6 years & older, over 12 1/2-15\" Entries: 5\n"
    "1st: Bittersweet Belle, owned by Doug & Noreen Loranger\n"
    "2nd: Abby, owned by Richard & Annette Kent\n"
    "3rd: Farmcliff Snowflake, owned by Bob & Genie Franklin\n"
    "4th: Whispering Winds Heidi Ho, owned by Ken Winfield\n"
    "5th: Whispering Winds Pepsi, owned by R. & M. Minutello\n",
    "Vet bitches over Snowflake/Heidi",
)

HQ.write_text(text, encoding="utf-8")
n1 = count_gaps(HQ.read_text(encoding="utf-8").splitlines())
print("replacements", n, "gaps", n0, "->", n1)
