"""2000 Vol II batch2 — PDF-backed clears + mangled place-line repairs."""
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


# --- Agility I Covergirl / Jiminy order (Yankee p11) ---
repl(
    "Agility I\n"
    "2nd: Cromwell Covergirl, owned by Jane McClay\n"
    "6th: Lakeshore Jiminy Cricket, owned by Cathy Larson\n"
    "3rd: Heart N' Soul'McSorley, owned by Walter & Marla Lutter\n",
    "Agility I\n"
    "2nd: Cromwell Covergirl, owned by Jane McClay\n"
    "3rd: Heart N' Soul McSorley, owned by Walter & Marla Lutter\n"
    "6th: Lakeshore Jiminy Cricket, owned by Cathy Larson\n",
    "Covergirl/McSorley/Jiminy order",
)

# --- Winslow smooth bitches (PDF right col) ---
repl(
    "1st: Winslow's Genevieve, owned by Lisa Fitzgerald\n"
    "2nd: Northwood Vorset, owned by Linda Cranford\n"
    "6th: North Country Pebbles, owned by Mary Lou Mogrovejo\n",
    "1st: Winslow's Genevieve, owned by Lisa Fitzgerald\n"
    "2nd: Ash Creek Pinch, owned by Mary Lou Mogrovejo\n"
    "3rd: Red Stone Dynamite, owned by Michelle Ward\n"
    "4th: Baybriar Zoe, owned by Jeanette Hutchinson\n"
    "5th: Northwood Dorset, owned by Linda Cranford\n"
    "6th: North Country Pebbles, owned by Mary Lou Mogrovejo\n",
    "Winslow/Pebbles class rebuild",
)

# --- Satin / Token column unsmash (Paumanok p27) — both copies ---
repl(
    "Bitch Pups, 9 up to 12 months, smooth Entries: | Bitches, 1 yr. & older, 12% up to 15\", smooth Entries: 6\n"
    "1st: The Hollow Phoebe, owned by Twila Decker\n"
    "Bitch Pups, 9 up to 12 months, r/br Entries: 6 2nd: Windever Token, owned by Sandy McElearney\n"
    "1st: Fox Run Skye, owned by Chris Levine\n"
    "3rd: Long Hope Satin, owned by Nellie Niewola\n"
    "Arr Viasnwatals Peden, mitted bai Pos. bik. Pe a a ee ee en\n"
    "4th: Fox Run Skye, owned by Chris Levine\n"
    "5th: Kenswick Kayla, owned by Sandy McElearney\n"
    "3rd: Kenswick Caution, owned by Sandy McElearney\n"
    "4th: Muscle Russell Duster, owned by Jill Goodman\n"
    "5th: Muscle Russell Holly, owned by Mark & Lisa Green\n"
    "6th: Sow's Ear Foxy, owned by Laura Harakaly\n",
    "Bitch Pups, 9 up to 12 months, smooth Entries: 1\n"
    "1st: The Hollow Phoebe, owned by Twila Decker\n"
    "Bitch Pups, 9 up to 12 months, r/br Entries: 6\n"
    "1st: Fox Run Skye, owned by Chris Levine\n"
    "2nd: Kenswick Kayla, owned by Sandy McElearney\n"
    "3rd: Kenswick Caution, owned by Sandy McElearney\n"
    "4th: Muscle Russell Duster, owned by Jill Goodman\n"
    "5th: Muscle Russell Holly, owned by Mark & Lisa Green\n"
    "6th: Sow's Ear Foxy, owned by Laura Harakaly\n"
    "Bitches, 1 yr. & older, 12 1/2 up to 15\", smooth Entries: 6\n"
    "1st: Willowbrook Lexus, owned by Kari Streitcher\n"
    "2nd: Windever Token, owned by Sandy McElearney\n"
    "3rd: Long Hope Satin, owned by Nellie Niewola\n"
    "4th: Muscle Russell Comet, owned by Mary Lou Mogrovejo\n"
    "5th: Andlin Sandy, owned by Samantha Cather\n"
    "6th: King, owned by Carol King\n",
    "Satin/Token column unsmash",
)

# --- Carley flat bitches (PDF) ---
repl(
    "1st: Big Hickory Terra, owned by Ronnie & Wanda Dyer\n"
    "2nd: Carter's Legend Rose, owned by Eddie & Jeanette Carter\n"
    "6th: Carley, owned by Marc & Laura Cormier\n",
    "1st: Big Hickory Terra, owned by Ronnie & Wanda Dyer\n"
    "2nd: Carter's Legend Rose, owned by Eddie & Jeanette Carter\n"
    "3rd: Heaven Hill Dixie, owned by Tom Arnold\n"
    "4th: Rustler's Emma Peel, owned by Tony & Linda Marchlinski\n"
    "5th: Fox Island Ms. Pebbles, owned by G. Taylor & Barbara Gilford\n"
    "6th: Carley, owned by Marc & Laura Cormier\n",
    "Carley +Dixie/Emma/Pebbles",
)

# --- Andlin Tessa / Moxie smash → PDF smooth bitch class ---
repl(
    "Bitches, 1 yr. & older, 12 1/2 up to 15\", smooth Entries: 7\n"
    "1st: Andlin Tessa, owned by Jane Collard\n"
    "5th: The Folly Moxie, owned by Rick & Mary Thorton\n"
    "2nd: Crossewinds Scurry, owned by Becky Crosse\n"
    "5th: The Folly Moxie, owned by Rick & Mary Thorton\n"
    "6th: Arlins Indigo Ink, owned by Alison Lindstrum\n",
    "Bitches, 1 yr. & older, 12 1/2 up to 15\", smooth Entries: 7\n"
    "1st: Andlin Tessa, owned by Jane Collard\n"
    "2nd: Crossewinds Scurry, owned by Becky Crosse\n"
    "3rd: Muscle Russell Comet, owned by Mary Lou Mogrovejo\n"
    "4th: Sunny Ridge Robin, owned by Karen Cooper\n"
    "5th: Wynchwood Rosie, owned by J. Bower/K. Potter\n"
    "6th: Easton Point Zest, owned by Kathryn Franklin\n",
    "Tessa/Moxie → PDF smooth class",
)

# --- Gabe / Novice Adult unsmash (Hi-Bid p44) ---
repl(
    "Dogs, 1 yr. & older, 10 up to 12 1/2\" Entries: 18\n"
    "1st: North Country Petey, owned by Mary Lou Mogrovejo\n"
    "Novice Adult Entries: 22 2nd: High & Low Hooligan, owned by Melissa Lowe\n"
    "1st: Windstars Winston, owned by Sandy Wolownik\n"
    "3rd: Gabe, owned by Janice Irving\n"
    "2nd: Sweet Bay Spotswood, owned by Ania Cowley i i eee\n"
    "2nd: Sweet Bay Spotswood, owned by Anja Cowley\n",
    "Dogs, 1 yr. & older, 10 up to 12 1/2\" Entries: 18\n"
    "1st: North Country Petey, owned by Mary Lou Mogrovejo\n"
    "2nd: High & Low Hooligan, owned by Melissa Lowe\n"
    "3rd: Gabe, owned by Janice Irving\n"
    "Novice Adult Entries: 22\n"
    "1st: Windstars Winston, owned by Sandy Wolownik\n"
    "2nd: Sweet Bay Spotswood, owned by Anja Cowley\n",
    "Gabe/Novice Adult unsmash",
)

# --- Skipper false 6th in dogs class (p45); real 6th is Gus ---
repl(
    "Dogs, 1 yr. & older, 10 up to 1214\" Entries: 17 5th: Summer Run Forest, owned by Joanna Proctor\n"
    "1st: High & Low Hooligan, owned by Melissa Lowe\n"
    "6th: Skipper, owned by Terri Parrow\n"
    "2nd: Spanky, owned by Bettyann Senf Novice Entries: 7\n"
    "2nd: Spanky, owned by Bettyann Senf\n",
    "Dogs, 1 yr. & older, 10 up to 12 1/2\" Entries: 17\n"
    "1st: High & Low Hooligan, owned by Melissa Lowe\n"
    "2nd: Spanky, owned by Bettyann Senf\n",
    "Skipper false-6th remove",
)

# --- Scout/Sassy bitches (steeplechase PDF) ---
repl(
    "Bitches, 1 yr. & older, 10 up to 12/4\" Entries: 23\n"
    "1st: Gills Creek Scout, owned by Brooks Kelley & Joe Shapiro\n"
    "FA —_-  airaineontar vier mama\n"
    "3rd: Lickity Split Sassy, owned by Bob Franklin\n"
    "4th: Lucy, owned by Brooks Kelley & Joe Shapiro\n"
    "5th:  Meadowlake Lyric, owned by Paul & Tammie Davis\n"
    "6th: Fox Run Chant, owned by Doug & Sue Tack\n",
    "Bitches, 1 yr. & older, 10 up to 12 1/2\" Entries: 23\n"
    "1st: Farmcliff Holland, owned by Doug & Sue Tack\n"
    "2nd: Gills Creek Scout, owned by Brooks Kelley & Joe Shapiro\n"
    "3rd: The Folly Lucy, owned by Mary & Rick Thornton\n"
    "4th: Fox Run Chant, owned by Doug & Sue Tack\n"
    "5th: Lickity Split Sassy, owned by Bob Franklin\n"
    "6th: Lucy, owned by Brooks Kelley & Joe Shapiro\n",
    "Scout/Sassy steeplechase rebuild",
)

# --- Youth agility Ashley/Jessica stub ---
repl(
    "Youth Handling Agility, On Lead Entries: 6\n"
    "2nd: Ashley Boyd\n"
    "8 ag\n"
    "6th: Jessica Pancoast\n",
    "Youth Handling Agility, On Lead Entries: 6\n"
    "2nd: Ashley Boyd\n"
    "6th: Jessica Pancoast\n",
    "Youth Ashley stub clean",
)

# --- Baileys starters: restore Tackle 3rd between Digger and Baileys ---
repl(
    "2nd: Pine Hill Digger, owned by Lisa Drinkwater\n"
    "5th: Baileys Irish Cream, owned by Dawn Strawn\n"
    "Open Adult Entries: 23 6th: Blue Dome Top Targa, owned by Mira Leibstein\n",
    "2nd: Pine Hill Digger, owned by Lisa Drinkwater\n"
    "3rd: Farmcliff Tackle, owned by Vicki & Megan Johnson\n"
    "4th: Briarpatch Junior, owned by Beverly Hirt\n"
    "5th: Baileys Irish Cream, owned by Dawn Strawn\n"
    "6th: Blue Dome Top Targa, owned by Mira Leibstein\n",
    "Baileys +Tackle/Junior",
)

# --- Agility I A.J. / Katie: fix Tackle mangled 3rd ---
repl(
    "\"Srd:---Farmcliff Tackle;, owned by-Vicki:& Megan Johnson\n"
    "2nd: Briarpatch A.J, owned by Beverly Hirt\n"
    "4th: Katie Clover, owned by Natalene Lamming\n",
    "2nd: Briarpatch A.J, owned by Beverly Hirt\n"
    "3rd: Will-O-Moor Badger, owned by Scott Whittington\n"
    "4th: Katie Clover, owned by Natalene Lamming\n",
    "A.J./Katie +Badger 3rd",
)

# --- Youth obedience 38rd → 3rd ---
repl("38rd: Ashley Boyd\n", "3rd: Ashley Boyd\n", "38rd→3rd Ashley")

# --- Bronze Micro: leave 3rd unknown — only normalize Fred OCR ---
repl(
    "2nd: Farmcliff. Fred, owned by Michelle Ward\n"
    "4th: Natural Instinct Micro, owned by Ken & Kathy Bushell\n",
    "2nd: Farmcliff Fred, owned by Michelle Ward\n"
    "4th: Natural Instinct Micro, owned by Ken & Kathy Bushell\n",
    "Fred OCR normalize (gap remains)",
)

# --- Veteran cert: Champion/Reserve not 1st Duke ---
repl(
    "Veteran Championship Certificate Entries: 6\n"
    "1st: 31x Farmelift Duke;owned by-dim Hughes\n"
    "4th: Li'l Efforts Petey, owned by Kathy Hunter\n"
    "5th: Treetop Zenith Acorn, owned by Catherine Brown\n"
    "6th:  Wil-O-Moor Rex, owned by M. Williams/K. Hom\n"
    "Champion: Double D Pfoxie, owned by Dorothy Whiting\n"
    "Reserve: Lost Acres Revion, owned by Karen McCarthy\n",
    "Veteran Championship Certificate Entries: 6\n"
    "Champion: Double D Pfoxie, owned by Dorothy Whiting\n"
    "Reserve: Lost Acres Revion, owned by Karen McCarthy\n"
    "4th: Li'l Efforts Petey, owned by Kathy Hunter\n"
    "5th: Treetop Zenith Acorn, owned by Catherine Brown\n"
    "6th: Wil-O-Moor Rex, owned by M. Williams/K. Hom\n",
    "Petey VCC Champion/Reserve",
)

# --- Calvin Advanced On Lead ---
repl(
    "Advanced, On Lead Entries: 1\n"
    "4th, Riverview Calvin, owned by Karen Vernon\n",
    "Advanced, On Lead Entries: 1\n"
    "1st: Riverview Calvin, owned by Karen Vernon\n",
    "Calvin 4th→1st",
)

# --- Syber Sonic starters ---
repl(
    "Starters Agility Entries: 7\n"
    "1st: Tackle, owned by Vicki Johnson\n"
    "2nd: Li'l Efforts Petey, owned by Kathy Hunter\n"
    "5th: Windermere Syber Sonic, owned by Debbie Cavicchi\n",
    "Starters Agility Entries: 7\n"
    "1st: Tackle, owned by Vicki Johnson\n"
    "2nd: Li'l Efforts Petey, owned by Kathy Hunter\n"
    "3rd: North Country Pringle, owned by Dale & Cathy Larson\n"
    "4th: Blue Dome Top Targa, owned by Mira Leibstein\n"
    "5th: Windermere Syber Sonic, owned by Debbie Cavicchi\n",
    "Syber +Pringle/Targa",
)

# --- Tally Ho smashed into bitch pups ---
repl(
    "Bitch Pups, 9 up to 12 months, r/br Entries: 6 5th: Cromwell Corby, owned by Jane McClay\n"
    "1st: Kenswick Kayla, owned by Joel & Sandy McElearney\n"
    "6th: Ash Creek Tally Ho, owned by Kari Streicher\n"
    "2nd: Brandywine Tumble, owned by Stephanie Taylor Bitches, 1 yr. & older, 12% up to 15\", smooth Entries: 4\n"
    "3rd:  Kenswick Caution, owned by Ine! & Sandy MaClearne:) aass ee eee aw 5 Seer\n"
    "3rd: Kenswick Caution, owned by Joel & Sandy McElearney\n",
    "Bitch Pups, 9 up to 12 months, r/br Entries: 6\n"
    "1st: Kenswick Kayla, owned by Joel & Sandy McElearney\n"
    "2nd: Brandywine Tumble, owned by Stephanie Taylor\n"
    "3rd: Kenswick Caution, owned by Joel & Sandy McElearney\n"
    "5th: Cromwell Corby, owned by Jane McClay\n",
    "Tally Ho out of bitch pups",
)

# --- Youth GTG Anne/Sarah smash ---
repl(
    "2nd: Anne Dalmadgerd: Sarah Cranor\n"
    "4th: Taryn Lacy\n",
    "2nd: Anne Dalmadge\n"
    "3rd: Sarah Cranor\n"
    "4th: Taryn Lacy\n",
    "Anne/Sarah unsmash",
)

# --- Farmcliff Becky mangled 4th ---
repl(
    "4th>===Farmcliff:Beckypowned by.Bob.&.Genie Franklinin\n",
    "4th: Farmcliff Becky, owned by Bob & Genie Franklin\n",
    "Becky 4th OCR",
)

# --- Big Sky Annie veterans ---
repl(
    "3rd\" Big-Sky Aninierowned by Doug-&Sue Tack\n",
    "3rd: Big Sky Annie, owned by Doug & Sue Tack\n",
    "Annie 3rd OCR",
)

# --- Tea Cup mangled 4th ---
repl(
    "4th-~Farmelift-TeaCupyowned by-Richard:Minutello\n",
    "4th: Farmcliff Tea Cup, owned by Richard Minutello\n",
    "Tea Cup 4th OCR",
)

HQ.write_text(text, encoding="utf-8")
print("applied", n)
print("gaps", count_gaps(text.splitlines()))
