"""2001 Vol I batch3 — Trixie cert, Bosco, Cosmo, Cody, Sean, 9th→6th OCR."""
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


# Trixie championship cert (PDF p48)
repl(
    "Championship Certificate, 12% up to 15\" Entries: 13\n"
    "1st: R.A. Trixie, owned by John & Judy Tyno\n"
    "3rd: Hart Farms Hunter II, owned by Sue & Don Wilson\n"
    "5th: Tenier-fic Wild Child, owned by Sammy & Danetta Hopewell\n"
    "Champion: Rustler's Jingles Judy, owned by L. & D. McKinney\n"
    "Reserve: Southernmost Sami D'Shark, owned by Jackie McLain\n",
    "Championship Certificate, 12 1/2 up to 15\" Entries: 13\n"
    "Champion: Rustler's Jingles Judy, owned by L. & D. McKinney\n"
    "Reserve: Southernmost Sami D'Shark, owned by Jackie McLain\n"
    "3rd: Hart Farms Hunter II, owned by Sue & Don Wilson\n"
    "4th: Terrier-ific Wild Child, owned by Sammy & Danetta Hopewell\n"
    "6th: R.A. Trixie, owned by John & Judy Tyno\n",
    "Trixie cert rebuild",
)

# Black Jack pups + Bosco (PDF p50)
repl(
    "3rd: Fox Cry Black Jack, owned by Donna Pierce\n"
    "--- column RIGHT ---\n"
    "5th: Ironwater Snowy Belle, owned by Guy & Doris Baylor\n",
    "3rd: Fox Cry Black Jack, owned by Donna Pierce\n"
    "4th: DiBo's Den Bosco, owned by Mike & Karen DiBernardo\n"
    "5th: Ironwater Snowy Belle, owned by Guy & Doris Baylor\n",
    "Black Jack +Bosco",
)

# Dogs over 12.5: Cosmo 3rd (PDF p42)
repl(
    "1st: Skeeter, owned by Jerry & lise Waelterman\n"
    "2nd: Huntington Farms Toca Jack, owned by John Allain\n"
    "4th: Hart Farms Hunter II, owned by Don & Sue Wilson\n"
    "5th: Krackerjak, owned by Jack Thole\n"
    "6th: Dogwood Glen Wotan, owned by Tom & Lucy Ramey\n",
    "1st: Skeeter, owned by Jerry & Ilse Waelterman\n"
    "2nd: Huntington Farms Toca Jack, owned by John Allain\n"
    "3rd: Cosmo, owned by Ronnie & Wanda Dyer\n"
    "4th: Hart Farms Hunter II, owned by Don & Sue Wilson\n"
    "5th: Krackerjak, owned by Jack Thole\n"
    "6th: Dogwood Glen Wotan, owned by Tom & Lucy Ramey\n",
    "Toca/Hunter +Cosmo",
)

# Jason column fragment → proper 4/5/6 of dog pups r/br (PDF p52)
repl(
    "--- column RIGHT ---\n"
    "1st: Button Top Jason, owned by Flo Clark\n"
    "4th: Legendary Joumey, owned by Brent Hopkins\n"
    "5th: Undercover Clyde, owned by Leah Rogers\n"
    "BEST DOG PUP & RESERVE\n",
    "4th: Legendary Journey, owned by Brent Hopkins\n"
    "5th: Button Top Jason, owned by Flo Clark\n"
    "6th: Undercover Clyde, owned by Leah Rogers\n"
    "BEST DOG PUP & RESERVE\n",
    "Jason/Journey/Clyde reorder",
)

# Jiminy veterans: PDF shows 2nd Cody/Coty but owner unscanned — park (no invent).


# Hale + Farmcliff Sean (PDF p116)
repl(
    "3rd: Northgate Hale, owned by Doug & Sue Tack\n"
    "5th: Sow's Ear Taltos, owned by Twila Decker\n"
    "6th: The Folly Mosquito, owned by Ben Davis\n",
    "3rd: Northgate Hale, owned by Doug & Sue Tack\n"
    "4th: Farmcliff Sean, owned by Bob Franklin\n"
    "5th: Sow's Ear Taltos, owned by Twila Decker\n"
    "6th: The Folly Mosquito, owned by Ben Davis\n",
    "Hale +Sean 4th",
)

# OCR 9th misread of 6th after a 5th
repl(
    "5th: R.A. Charley, owned by Travis & Cathy Hallman\n"
    "9th: R.A. Daphne, owned by Mike & Karen DiBernardo\n",
    "5th: R.A. Charley, owned by Travis & Cathy Hallman\n"
    "6th: R.A. Daphne, owned by Mike & Karen DiBernardo\n",
    "Charley 9th→6th Daphne",
)

repl(
    "5th: Ransom Penny Power, owned by Kimberlee Lutz\n"
    "9th: Picadilly Lucy, owned by John & Judy Tyno\n",
    "5th: Ransom Penny Power, owned by Kimberlee Lutz\n"
    "6th: Picadilly Lucy, owned by John & Judy Tyno\n",
    "Penny 9th→6th Lucy",
)

repl(
    "5th: Diamond E Bridgett Il, owned by Bob & Carolyn Skarke\n"
    "9th: Steringwood Zoe, owned by Kim Chrisman\n",
    "5th: Diamond E Bridgett II, owned by Bob & Carolyn Skarke\n"
    "6th: Sterlingwood Zoe, owned by Kim Chrisman\n",
    "Bridgett 9th→6th Zoe",
)

# Youth missing 3rd — leave parked (PDF blank between Divito and Nicholas)

HQ.write_text(text, encoding="utf-8")
print("applied", n)
print("gaps", count_gaps(text.splitlines()))
