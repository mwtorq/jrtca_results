"""Written canonical maps. Normalize labels only; never invent placements.

Every change is a spelling/alias rewrite of a string that already exists.
Re-diff against the raw line after applying.
"""
from __future__ import annotations

import re

_INCH = re.compile(r"[\"”″]|&#8243;|&#8221;")
_HALF = re.compile(r"[½]|1/2|1⁄2")
_DASH = re.compile(r"[–—−]|&#8211;|&#8212;")
_SPACE = re.compile(r"\s+")
_YEAR = re.compile(r"\bYEARS?\b", re.I)
_AND = re.compile(r"\bAND\b", re.I)
_HTML = re.compile(r"&#39;|&apos;|&amp;|&nbsp;", re.I)

# Division aliases seen in yearbook / site / Trial Vault / MOE.
DIV_ALIASES = {
    "RACING": "RACING DIVISION - FLAT RACES",
    "RACING DIVISION": "RACING DIVISION - FLAT RACES",
    "FLAT RACES": "RACING DIVISION - FLAT RACES",
    "FLAT RACE": "RACING DIVISION - FLAT RACES",
    "SECTION I. FLAT RACING": "RACING DIVISION - FLAT RACES",
    "JRTCA FLAT RACES": "RACING DIVISION - FLAT RACES",
    "STEEPLECHASE": "STEEPLECHASE RACES",
    "STEEPLECHASE RACES": "STEEPLECHASE RACES",
    "RACING DIVISION - STEEPLECHASE RACES": "STEEPLECHASE RACES",
    "JRTCA STEEPLECHASE RACES": "STEEPLECHASE RACES",
    "HURDLES": "STEEPLECHASE RACES",
    "HURDLE RACES": "STEEPLECHASE RACES",
    "GO-TO-GROUND": "GO-TO-GROUND",
    "GO TO GROUND": "GO-TO-GROUND",
    "GTG": "GO-TO-GROUND",
    "SUPER EARTH": "SUPER EARTH",
    "SUPEREARTH": "SUPER EARTH",
    "CONFORMATION": "CONFORMATION",
    "YOUTH": "YOUTH",
    "AGILITY": "AGILITY",
    "NOSE WORK": "NOSE WORK",
    "NOSEWORK": "NOSE WORK",
    "BRUSH HUNT": "BRUSH HUNT",
    "LURE COURSING": "LURE COURSING",
    "BARN HUNT": "BARN HUNT",
    "EARTHDOG STEEPLECHASE RACES": "EARTHDOG STEEPLECHASE RACES",
}

# Keep session-specific racing labels; do not collapse them into generic flats.
DIV_KEEP = (
    "FRIDAY NIGHT RACING",
    "FRIDAY NIGHT STEEPLE",
    "UNDER THE LIGHTS",
    "EARTHDOG STEEPLE",
    "MW MAYHEM",
    "HAY STACK",
    "TRAIL",
    "THUNDER",
)

CHAMP_CLASS = re.compile(r"CHAMPION|RESERVE", re.I)
BEST_RES = re.compile(r"^best\b", re.I)


def tidy(s: str) -> str:
    s = (s or "").replace("\xa0", " ")
    s = _HTML.sub(lambda m: {"&#39;": "'", "&apos;": "'", "&amp;": "&", "&nbsp;": " "}[m.group(0).lower()], s)
    s = _INCH.sub('"', s)
    s = _HALF.sub(" 1/2", s)
    s = _DASH.sub("-", s)
    s = s.replace("12.5", "12 1/2").replace("12½", "12 1/2")
    s = _YEAR.sub("years", s)
    s = _AND.sub("and", s)
    s = _SPACE.sub(" ", s).strip()
    return s


def canon_div(name: str) -> str:
    raw = tidy(name)
    u = raw.upper()
    for keep in DIV_KEEP:
        if keep in u:
            return raw
    if u in DIV_ALIASES:
        return DIV_ALIASES[u]
    for alias, canon in DIV_ALIASES.items():
        if u.startswith(alias) and "CHAMPION" not in u:
            return canon
    return raw


def canon_class(name: str) -> str:
    s = tidy(name)
    s = re.sub(r"^class\s+\d+\s*:\s*", "", s, flags=re.I)
    s = re.sub(r"\bflat racing\s*-\s*", "", s, flags=re.I)
    s = re.sub(r"\bhurdles? racing\s*-\s*", "", s, flags=re.I)
    s = re.sub(r"\bsteeplechase\s+racing\s*-?\s*", "", s, flags=re.I)
    return _SPACE.sub(" ", s).strip()


def canon_result(res: str, cls: str = "") -> str:
    r = tidy(res)
    if BEST_RES.match(r) and CHAMP_CLASS.search(cls or ""):
        return "Champion"
    low = r.lower()
    if low in {"1st", "first"}:
        return "1st"
    if low in {"2nd", "second"}:
        return "2nd"
    if low in {"3rd", "third"}:
        return "3rd"
    if low.startswith("champion"):
        return "Champion"
    if low.startswith("reserve"):
        return "Reserve"
    return r


def canon_dog(name: str) -> str:
    s = tidy(name)
    s = re.sub(r"^#\d+:\s*", "", s)
    s = re.split(r"\s+owned\s+by\s+", s, maxsplit=1, flags=re.I)[0]
    # Known source typos for dogs already in the catalog (same animal).
    s = re.sub(r"\bWhatz\s*b\b", "Watzb", s, flags=re.I)
    s = re.sub(r"\bWhatzb\b", "Watzb", s, flags=re.I)
    s = re.sub(r"\bWatz\s*B\b", "Watzb", s, flags=re.I)
    s = re.sub(r"\bHapn['’]?n\b", "Happn'n", s, flags=re.I)
    return _SPACE.sub(" ", s).strip()
