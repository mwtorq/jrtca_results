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
# Pre-2010 leftover "RACING DIVISION"/"Racing" remounts by class/raw to
# generic flats/steeple only (those files have no Friday/Sunday headings).
DIV_ALIASES = {
    "RACING": "RACING DIVISION - FLAT RACES",
    "RACING DIVISION": "RACING DIVISION - FLAT RACES",
    "FLAT RACES": "RACING DIVISION - FLAT RACES",
    "FLAT RACE": "RACING DIVISION - FLAT RACES",
    "SECTION I. FLAT RACING": "RACING DIVISION - FLAT RACES",
    "SECTION 1: LURE COURSING (NON-SANCTIONED)": "LURE COURSING",
    "SECTION 2: RAT RACE! RAT HUNT GAME": "RAT RACE! RAT HUNT GAME",
    "RACING DIVISION - HURDLES RACING DIVISION": "RACING DIVISION - STEEPLECHASE RACES",
    "FLAT RACES - STEEPLECHASE RACES": "RACING DIVISION - STEEPLECHASE RACES",
    "AGILITY DIVISION - STEEPLECHASE RACES": "RACING DIVISION - STEEPLECHASE RACES",
    "JRTCA FLAT RACES": "RACING DIVISION - FLAT RACES",
    "STEEPLECHASE": "RACING DIVISION - STEEPLECHASE RACES",
    "STEEPLECHASE RACES": "RACING DIVISION - STEEPLECHASE RACES",
    "RACING DIVISION - STEEPLECHASE RACES": "RACING DIVISION - STEEPLECHASE RACES",
    "RACING DIVISION - FLAT RACES - FRIDAY": "RACING DIVISION - FLAT RACES - FRIDAY",
    "RACING DIVISION - STEEPLECHASE RACES - FRIDAY": "RACING DIVISION - STEEPLECHASE RACES - FRIDAY",
    "RACING DIVISION - FLAT RACES - SUNDAY": "RACING DIVISION - FLAT RACES - SUNDAY",
    "RACING DIVISION - STEEPLECHASE RACES - SUNDAY": "RACING DIVISION - STEEPLECHASE RACES - SUNDAY",
    "JRTCA STEEPLECHASE RACES": "RACING DIVISION - STEEPLECHASE RACES",
    "HURDLES": "RACING DIVISION - STEEPLECHASE RACES",
    "HURDLE RACES": "RACING DIVISION - STEEPLECHASE RACES",
    "HURDLE RACING": "RACING DIVISION - STEEPLECHASE RACES",
    "DIVISION C: CONFORMATION": "CONFORMATION",
    "DIVISION D: GO-TO-GROUND": "GO-TO-GROUND",
    "OPEN ADULT CONFORMATION": "CONFORMATION",
    "YOUTH COMFORMATION": "YOUTH CONFORMATION",
    "YOUTH CONFORMATION": "YOUTH CONFORMATION",
    "GO-TO-GROUND": "GO-TO-GROUND",
    "GO TO GROUND": "GO-TO-GROUND",
    "GTG": "GO-TO-GROUND",
    "SUPER EARTH": "SUPER EARTH",
    "SUPEREARTH": "SUPER EARTH",
    "MASTER'S DEN STAKES": "SUPER EARTH",
    "MASTERS DEN STAKES": "SUPER EARTH",
    "SUPER EARTH STAKES": "SUPER EARTH",
    "CONFORMATION": "CONFORMATION",
    "YOUTH": "YOUTH DIVISION",
    "YOUTH DIVISION": "YOUTH DIVISION",
    "CHILD / YOUTH": "YOUTH DIVISION",
    "CHILD/YOUTH": "YOUTH DIVISION",
    "AGILITY": "AGILITY",
    "NOSE WORK": "NOSE WORK",
    "NOSEWORK": "NOSE WORK",
    "BRUSH HUNT": "BRUSH HUNT",
    "LURE COURSING": "LURE COURSING",
    "BARN HUNT": "BARN HUNT",
    "STAKES BARN HUNT": "BARN HUNT",
    "STAKES BARN HUNT (NON-SANCTIONED)": "BARN HUNT",
    "RUMBLE TUNNEL DIVISION": "RUMBLE TUNNEL (NON-SANCTIONED)",
    "TRAILING & LOCATING HIGH SCORE & RESERVE": "TRAILING & LOCATING",
    "EARTHDOG STEEPLECHASE RACES": "EARTHDOG STEEPLECHASE RACES",
    "RALLY-OBEDIENCE DIVISION": "RALLY OBEDIENCE DIVISION",
    "RALLY_O DIVISION": "RALLY OBEDIENCE DIVISION",
    "JACK RUSSELL TERRIER NOSEWORK": "NOSE WORK",
    "TRAIL & LOCATE OBSTACLE COURSE": "TRAILING & LOCATING",
    "PUPPY RACING": "RACING DIVISION - FLAT RACES",
    "FEO RACING": "RACING DIVISION - FLAT RACES",
    "AGILITY I": "AGILITY DIVISION",
    "AGILITY II": "AGILITY DIVISION",
    "AGILITY III": "AGILITY DIVISION",
}

# Keep session-specific racing labels; do not collapse them into generic flats.
DIV_KEEP = (
    "FLAT RACES - FRIDAY",
    "STEEPLECHASE RACES - FRIDAY",
    "FLAT RACES - SUNDAY",
    "STEEPLECHASE RACES - SUNDAY",
    "FRIDAY NIGHT RACING",
    "FRIDAY NIGHT STEEPLE",
    "UNDER THE LIGHTS",
    "EARTHDOG STEEPLE",
    " - SATURDAY",
    " - SUNDAY",
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


def _hurdle_label(div_u: str, cls_u: str) -> bool:
    return bool(re.search(r"HURDLE|STEEPLE", f"{div_u} {cls_u}"))


def canon_div(name: str, class_name: str = "") -> str:
    raw = tidy(name).replace("COMFORMATION", "CONFORMATION")
    raw = raw.replace("comformation", "conformation").replace(": ", " - ")
    u = raw.upper()
    cls_u = tidy(class_name).upper()
    hurdle = _hurdle_label(u, cls_u)
    if re.search(r"\bGTG\b|GO[\s\-]*TO[\s\-]*GROUND", u) and (
        "CHILD" in u or "YOUTH" in u
    ):
        return "GO-TO-GROUND"
    if (
        "CHILD/YOUTH" in u
        or "CHILD / YOUTH" in u
        or u in {"YOUTH", "YOUTH DIVISION"}
        or u.startswith("YOUTH")
        or re.search(r"\b(?:CHILD|JUNIOR|YOUTH)\s+HANDLER", u)
        or (u.startswith("SECTION") and ("CHILD" in u or "YOUTH" in u))
    ):
        return "YOUTH DIVISION"
    if "FRIDAY NIGHT STEEPLE" in u or u.endswith("STEEPLECHASE RACES - FRIDAY"):
        return "RACING DIVISION - STEEPLECHASE RACES - FRIDAY"
    if (
        "FRIDAY NIGHT RACING" in u
        or "UNDER THE LIGHTS" in u
        or u.endswith("FLAT RACES - FRIDAY")
    ):
        return "RACING DIVISION - STEEPLECHASE RACES - FRIDAY" if hurdle else "RACING DIVISION - FLAT RACES - FRIDAY"
    if (
        u.startswith("SUNDAY RACING")
        or u.endswith("RACES - SUNDAY")
        or u.endswith("STEEPLECHASE RACES - SUNDAY")
    ):
        if hurdle:
            return "RACING DIVISION - STEEPLECHASE RACES - SUNDAY"
        return "RACING DIVISION - FLAT RACES - SUNDAY"
    if u.startswith("GO-TO-GROUND") or u.startswith("GO TO GROUND"):
        return "GO-TO-GROUND"
    if "CONFORMATION" in u:
        return "CONFORMATION"
    if u in {
        "RACING",
        "RACING DIVISION",
        "RACES",
        "DIVISION - RACING",
        "DIVISION A - RACING",
    }:
        return (
            "RACING DIVISION - STEEPLECHASE RACES"
            if hurdle
            else "RACING DIVISION - FLAT RACES"
        )
    for keep in DIV_KEEP:
        if keep in u:
            return raw
    if u in DIV_ALIASES:
        return DIV_ALIASES[u]
    for alias, canon in DIV_ALIASES.items():
        if u.startswith(alias + " ") or u.startswith(alias + "-") or u == alias:
            return canon
    return raw


def canon_class(name: str) -> str:
    s = tidy(name)
    s = s.replace("COMFORMATION", "CONFORMATION")
    s = re.sub(r"^class(?:es)?\s+\d+[A-Z]?(?:st|nd|rd|th)?\s*[:,]?\s*", "", s, flags=re.I)
    s = re.sub(r",?\s*owned by\b.*$", "", s, flags=re.I)
    s = re.sub(r"\bnumber of(?:\s+entries)?\b.*$", "", s, flags=re.I)
    s = re.sub(r"\bflat racing\s*[-:]\s*", "", s, flags=re.I)
    s = re.sub(r"\bhurdles? racing\s*[-:]\s*", "", s, flags=re.I)
    s = re.sub(r"\bsteeplechase\s+racing\s*[-:]?\s*", "", s, flags=re.I)
    return _SPACE.sub(" ", s).strip(" -:;,")


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
