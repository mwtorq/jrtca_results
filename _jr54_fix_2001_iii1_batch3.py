"""2001 Vol III pt1 batch3 — Spayed/Maggie/Agility I/MN bred/Chanel smash."""
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


# Spayed Adult: continue Tea Cup/Moxie/Paddy/Molly (PDF p22)
repl(
    "Spayed Adult Bitch, VE          Entries: 1\n"
    "1st: Andiin Layla Pearl, owned by Karen Howard\n"
    "--- column RIGHT ---\n"
    "1st: Sass 'N Dash Molly, owned by Mary Webb\n"
    "4th: Way Lin Moxie, owned by Moira Kelly\n"
    "5th: Autum Hill Puck's Paddy, owned by Susan Heckelman\n",
    "Spayed Adult Bitch                                              Entries: 10\n"
    "1st: Andlin Layla Pearl, owned by Karen Howard\n"
    "2nd: Farmstead Bella, owned by Tricia Candido\n"
    "3rd: Farmcliff Tea Cup, owned by Margaret & Richard Minutello\n"
    "4th: Way Lin Moxie, owned by Moira Kelly\n"
    "5th: Autum Hill Puck's Paddy, owned by Susan Heckelman\n"
    "6th: Sass 'N Dash Molly, owned by Mary Webb\n",
    "Spayed Layla/Tea Cup/Molly",
)

# Spayed Adult Trial II: Bailey 4th between Maggie and Reggie (PDF p26)
repl(
    "3rd: Down East Maggie, owned by Linda Pereboom\n"
    "--- column RIGHT ---\n"
    "5th: Reggie, owned by Steve & Kim Sutherland\n",
    "3rd: Down East Maggie, owned by Linda Pereboom\n"
    "4th: Down East Bailey, owned by Linda Pereboom\n"
    "5th: Reggie, owned by Steve & Kim Sutherland\n",
    "Maggie +Bailey 4th",
)

# Agility I 10-12.5: Clover 4 / Paddy 5 / Badger 6 (PDF p28)
repl(
    "3rd: Smilin' Jack Full Monty, owned by Lisa Decker/Scooter Mauck\n"
    "5th: Katie Clover, owned by Naialene Lamming\n"
    "5th: Autumn Hill Puck's Paddy, owned by Susan Heckelman\n"
    "5th: WIill-O-Moor Badger, owned by Scott & Christina Whittington\n",
    "3rd: Smilin' Jack Full Monty, owned by Lisa Decker/Scooter Mauck\n"
    "4th: Katie Clover, owned by Natalene Lamming\n"
    "5th: Autumn Hill Puck's Paddy, owned by Susan Heckelman\n"
    "6th: Will-O-Moor Badger, owned by Scott & Christina Whittington\n",
    "Agility I Monty/Clover ranks",
)

# Agility I over 12.5: Darby 3 / Bella 4 / Skipjack 5 / Dodger 6 (PDF p28)
repl(
    "1st: Deerpath Ripley, owned by Jeanette Hutchison\n"
    "2nd: Loblolly Reno, owned by Jeannette Hutchison\n"
    "5th: Westwood Skipjack, owned by Nancy Henry\n"
    "5th: Mousemoor Dodger, owned by Scott & Christina Whittington\n",
    "1st: Deerpath Ripley, owned by Jeanette Hutchison\n"
    "2nd: Loblolly Reno, owned by Jeannette Hutchison\n"
    "3rd: Sass 'N Dash Darby, owned by Mike Murphy\n"
    "4th: Farmstead Bella, owned by Tricia Candido\n"
    "5th: Westwood Skipjack, owned by Nancy Henry\n"
    "6th: Mousemoor Dodger, owned by Scott & Christina Whittington\n",
    "Agility I Reno Darby/Bella",
)

# Neutered Adult MN trial: rebuild around Ranger/Bisket (PDF p30)
repl(
    "1st: Bark River Bulldozer, owned by Julie Grim\n"
    "2nd: Pine Creek Little Nemo, owned by Rhonda Rebhom\n"
    "3rd: Farrier Point Ranger, owned by Denise Neuner\n"
    "5th: Nampara Bisket, owned by Mary Labrosse\n"
    "Spayed Adult Bitch                                              Entries: 7\n"
    "1st: Meadowlake Wicca, owned by Pat Weber\n"
    "2nd: Serena, owned by Cathy Johnson\n"
    "5th: Nina, owned by Tom Brecklin\n"
    "5th:  Killare Birdie, owned by Rachelle Goldsmith\n"
    "5th: Lucy, owned by Robb & Susan Pieper\n"
    "Suitability To Red Fox                                     Entries: 11\n"
    "1st: Thombush Rosemary, owned by Char Smith\n"
    "2nd: Anglo Terra Bandit, owned by Joanne Van Hom\n"
    "5th: Hedgerow O'Tilley, owned by Deb Port\n"
    "5th: Mac's/Jacks Loyal Laddie, owned by Jody Stewart\n"
    "6th: Foxi Loxi Codi, owned by Scott & Susan Aeppli\n",
    "Neutered Adult Dog                                              Entries: 7\n"
    "1st: Anglo Terra Bandit, owned by Joanne Van Hom\n"
    "2nd: Nampara Charles Warleggen, owned by M. Labrosse & A. Merrick\n"
    "3rd: Farrier Point Ranger, owned by Denise Neuner\n"
    "4th: Nampara Bisket, owned by Mary Labrosse\n"
    "5th: Bark River Bulldozer, owned by Julie Grim\n"
    "6th: Pine Creek Little Nemo, owned by Rhonda Rebhom\n"
    "Spayed Adult Bitch                                              Entries: 7\n"
    "1st: Meadowlake Wicca, owned by Pat Weber\n"
    "2nd: Serena, owned by Cathy Johnson\n"
    "3rd: Foxi Loxi Gabbi, owned by Doris Hansen\n"
    "4th: Nina, owned by Tom Brecklin\n"
    "5th: Killare Birdie, owned by Rachelle Goldsmith\n"
    "6th: Lucy, owned by Robb & Susan Pieper\n"
    "Suitability To Red Fox                                     Entries: 11\n"
    "1st: Thornbush Rosemary, owned by Char Smith\n"
    "2nd: Anglo Terra Bandit, owned by Joanne Van Hom\n"
    "3rd: Killare Bugsy, owned by Jen Reiland\n"
    "4th: Hedgerow O'Tilley, owned by Deb Port\n"
    "5th: Mac's/Jacks Loyal Laddie, owned by Jody Stewart\n"
    "6th: Foxi Loxi Codi, owned by Scott & Susan Aeppli\n",
    "MN Neutered/Spayed/Red Fox rebuild",
)

# Agility I Willa class smashed with racing (PDF p49) — insert Cody/Norma/Snickers
repl(
    "Agility II, Off Lead, 10 up to 12 1/2\" Entries: 5\n"
    "1st: Terrier-ific Willa, owned by Jackie McLain\n"
    "4th: Wild Remain Montgomery, owned by Connie Jones\n",
    "Agility I, Off Lead, 10 up to 12 1/2\" Entries: 5\n"
    "1st: Terrier-ific Willa, owned by Jackie McLain\n"
    "2nd: Cody D'Cuda, owned by Jackie McLain\n"
    "3rd: Arrowhead Norma Sue, owned by Jack & Laura Phillips\n"
    "4th: Big Hickory Snickers, owned by Lynn Jerome\n"
    "5th: Queso, owned by Kirk & Susan Brister\n",
    "Willa Agility I rebuild (drop Montgomery bleed)",
)

HQ.write_text(text, encoding="utf-8")
n1 = count_gaps(HQ.read_text(encoding="utf-8").splitlines())
print("replacements", n, "gaps", n0, "->", n1)
