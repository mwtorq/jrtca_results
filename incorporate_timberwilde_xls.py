#!/usr/bin/env python3
"""Incorporate Blackburn/Timberwilde trial data.xls into TrialResults.

Matches existing TrialList / TrialClass / TrialPlacements first. Fills missing
GTG/lure/agility times, conformation judges, and racing Heat/Qtr/Semi columns
on the final-class placement. Heat/quarter/semi are not separate placements.
"""
from __future__ import annotations

import argparse
import re
from collections import defaultdict
from dataclasses import dataclass, field
from pathlib import Path

import pyodbc
import xlrd

from normalize_trialresults_data import (
    normalize_class_name_full,
    normalize_division_name_full,
)
from populate_trialresults_fixed import (
    get_next_ids_from_db,
    get_next_placement_times_id,
    get_or_create_class,
    get_or_create_division,
    normalize_placement_label,
)

XLS_CANDIDATES = [
    Path("_trial_data.xls"),
    Path(r"\\Synology\Files\Mark\trial data.xls"),
]
CONN_STR = (
    r"DRIVER={SQL Server};SERVER=Ldahsar\SQLEXPRESS;"
    r"DATABASE=TrialResults;Trusted_Connection=yes"
)
SOURCE_TAG = r"\\Synology\Files\Mark\trial data.xls"

DOG_NICK = {
    "ricky": "Dutch Creek Rick O'Shea of Blackburn",
    "katie": "Falling Branch Katie of Blackburn",
    "skeeter": "Skeeter of Blackburn",
    "zz": "Blackburn ZZTopdog",
    "zztopdog": "Blackburn ZZTopdog",
    "windy": "Blackburn Windy",
    "terra": "Sow's Ear Thierren of Blackburn",
    "kira": "Blackburn Kira Nerys",
    "roux": "Brandywine Roux of Blackburn",
    "flame": "Blackburn Flame",
    "kuri": "Blackburn Kuri",
    "saratoga": "Foxglade Saratoga of Timberwilde",
    "val": "Blackburn Valentino",
    "valentino": "Blackburn Valentino",
    "dakota": "Blackburn Dakota",
    "cosmo": "Blackburn Cosmo Topper",
    "bella": "Blackburn Bella",
    "chigurh": "Southland Chigurh of Timberwilde",
    "blanca": "Timberwilde Relampago Blanca",
    "relampago blanca": "Timberwilde Relampago Blanca",
    "relámpago blanca": "Timberwilde Relampago Blanca",
    "skeeter of blackburn": "Skeeter of Blackburn",
    "blackburn windy": "Blackburn Windy",
    "blackburn zztopdog": "Blackburn ZZTopdog",
    "sow s ear thierren of blackburn": "Sow's Ear Thierren of Blackburn",
    "brandywine roux of blackburn": "Brandywine Roux of Blackburn",
}

TRIAL_REWRITE = (
    (r"\bmwjrtc\b", "midwest"),
    (r"\bnawtc\b", "north american working terrier classic"),
    (r"\bmoe\b", "missouri earthdogs"),
    (r"\bmo earthdogs\b", "missouri earthdogs"),
    (r"\bdogwood\b", "peachtree dogwood"),
    (r"\bgcjrtn\b", "gulf coast texas two step"),
    (r"\bheartland spring\b", "heartland working"),
    (r"\bheartland fall\b", "heartland halloween happening heartland fall"),
    (r"\batf\b", "american terrier fest"),
    (r"\bswjrtn\b", "southwest"),
    (r"\bga fall\b", "georgia fall"),
    (r"\bloess hills\b", "loess hills"),
    (r"\bmid-america\b", "mid america"),
    (r"\bmidlands hunt\b", "midlands"),
    (r"\bsooner state\b", "oklahoma classic sooner state"),
)

SKIP_RESULTS = {"", "error", "canc", "unknown"}
SKIP_TIMES = {"", "unknown", "no time", "no score", "n/a", "na"}

# One racing-class placement per family. P/Q/S go on Heat/Qtr/Semi columns.
RACE_FAMILIES = (
    {
        "div": "RACING DIVISION - FLAT RACES",
        "prefix": "Flat Racing",
        "p": "Fl. P",
        "q": "Fl. Q",
        "s": "Fl. S",
        "fin": "Fl. FIN",
    },
    {
        "div": "RACING DIVISION - STEEPLECHASE RACES",
        "prefix": "Hurdles Racing",
        "p": "Hr. P",
        "q": "Hr. Q",
        "s": "Hr. S",
        "fin": "Hr. FIN",
    },
    {
        "div": "RACING DIVISION",
        "prefix": "Stakes Racing",
        "p": "St. P",
        "q": "St. Q",
        "s": "St. S",
        "fin": "St. FIN",
    },
)


# Approved new TrialList names. Key = (year, excel trial name lowercased).
CREATE_TRIALS: dict[tuple[int, str], str] = {
    (1998, "mo earthdogs"): "1998 Missouri Earthdogs Memorial Day Bash",
    (1999, "heartland fall"): "1999 Heartland Halloween Happening",
    (1999, "incredible dog challenge"): "1999 Incredible Dog Challenge",
    (1999, "midlands hunt i"): "1999 Midlands Hunt I",
    (1999, "midlands hunt ii"): "1999 Midlands Hunt II",
    (1999, "nawtc"): "1999 North American Working Terrier Classic",
    (2000, "american terrier fest"): "2000 American Terrier Fest",
    (2000, "heartland fall"): "2000 Heartland Halloween Happening",
    (2000, "incredible dog challenge"): "2000 Incredible Dog Challenge",
    (2000, "old dominion"): "2000 Old Dominion Jack Russell Terrier Trial",
    (2001, "american terrier fest"): "2001 American Terrier Fest",
    (2001, "heartland spring"): "2001 Heartland Working Terrier Trial",
    (2001, "incredible dog challenge"): "2001 Incredible Dog Challenge",
    (2001, "mwjrtc fall"): "2001 Midwest Fall",
    (2001, "tarascon"): "2001 Tarascon Working Terrier Open Trial",
    (2002, "american terrier fest"): "2002 American Terrier Fest",
    (2002, "heartland fall"): "2002 Heartland Halloween Happening",
    (2002, "loess hills"): "2002 Loess Hills",
    (2003, "cumberland i"): "2003 Cumberland I",
    (2003, "cumberland ii"): "2003 Cumberland II",
    (2003, "heartland fall"): "2003 Heartland Halloween Happening",
    (2003, "incredible dog challenge"): "2003 Incredible Dog Challenge",
    (2003, "loess hills"): "2003 Loess Hills",
    (2003, "mwjrtc spring"): "2003 Midwest Spring",
    (2004, "heartland fall"): "2004 Heartland Halloween Happening",
    (2005, "heartland fall"): "2005 Heartland Halloween Happening",
    (2005, "mo earthdogs"): "2005 Missouri Earthdogs Memorial Day Bash",
    (2006, "mo earthdogs"): "2006 Missouri Earthdogs Memorial Day Bash",
    (2006, "nawtc"): "2006 North American Working Terrier Classic",
    (2007, "incredible dog challenge"): "2007 Incredible Dog Challenge",
    (2007, "mo earthdogs"): "2007 Missouri Earthdogs Memorial Day Bash",
    (2008, "incredible dog challenge"): "2008 Incredible Dog Challenge",
    (2009, "incredible dog challenge"): "2009 Incredible Dog Challenge",
}

# (year, excel name lower) -> existing TrialName must contain this (case-insensitive).
EXISTING_ALIAS: dict[tuple[int, str], str] = {
    (1998, "mwjrtc fall"): "mwjrtc trial ill",
    (1999, "mwjrtc fall"): "mwjrtc",
    (2000, "mwjrtc fall"): "mwjrtc trial ill",
    (2000, "magnolia ii"): "magnolia classic jrt trial i",
    (2001, "heartland fall"): "heartland",
    (2002, "fox cry january i"): "fox cry i",
    (2002, "fox cry january ii"): "fox cry ii",
    (2002, "mwjrtc fall"): "mwjrtc fall festival",
    (2003, "mwjrtc fall"): "mwjrtc fall",
    (2003, "magnolia classic i"): "magnolia i",
    (2003, "magnolia classic ii"): "magnolia ii",
    (2003, "river city i"): "rcjrtc spring trial 1",
    (2003, "river city ii"): "rcjrtc spring trial 2",
    (2004, "river city i"): "rcjrtc trial i",
    (2006, "dogwood i"): "endless summer bash i",
    (2006, "dogwood ii"): "endless summer bash ii",
    (2006, "mwjrtc spring i"): "mwjrt summer celebration i",
    (2006, "mwjrtc spring ii"): "mwjrt summer celebration ii",
    (2006, "mwjrtc summer i"): "mwjrtc end of summer i",
    (2006, "mwjrtc summer ii"): "mwjrtc end of summer ii",
    (2008, "dogwood i"): "endless summer bash i",
    (2008, "dogwood ii"): "endless summer bash ii",
    (2008, "mwjrtc summer i"): "summer celebration i",
    (2008, "mwjrtc summer ii"): "summer celebration ii",
    (2008, "mid-america i"): "mid-america working v",
    (2008, "mid-america ii"): "mid-america working vi",
    (2008, "swjrtn i"): "swjrtn fall festival i",
    (2008, "swjrtn ii"): "swjrtn fall festival ii",
    (2008, "sooner state i"): "oklahoma classic i",
    (2008, "sooner state ii"): "oklahoma classic ii",
    (2009, "mid-america i"): "mid-america trial vii",
    (2009, "mid-america ii"): "mid-america trial viii",
    (2010, "piney woods i"): "piney woods vii",
    (2010, "piney woods ii"): "piney woods viii",
}


@dataclass
class Event:
    dog_nick: str
    year: int | None
    trial_raw: str
    excel_trial: str
    day: str | None
    excel_class: str
    division: str
    class_name: str
    result: str
    time: str | None = None
    judge: str | None = None
    owner: str | None = None
    source: str = ""
    heat: str | None = None
    qtr: str | None = None
    semi: str | None = None
    allow_create_dog: bool = False


@dataclass
class Stats:
    parsed: int = 0
    skipped: int = 0
    matched: int = 0
    times_added: int = 0
    placements_added: int = 0
    heats_updated: int = 0
    judges_added: int = 0
    trials_created: int = 0
    dogs_created: int = 0
    owners_created: int = 0
    unmatched_trial: list = field(default_factory=list)
    unmatched_dog: list = field(default_factory=list)
    created_names: list = field(default_factory=list)
    samples: list = field(default_factory=list)


def open_xls() -> xlrd.Book:
    for path in XLS_CANDIDATES:
        if path.exists():
            print(f"Reading {path}")
            return xlrd.open_workbook(str(path))
    raise FileNotFoundError("trial data.xls not found")


def nick_key(name: str) -> str:
    text = (name or "").strip().lower()
    text = text.replace("á", "a").replace("â", "a").replace("à", "a").replace("ä", "a")
    text = re.sub(r"[^a-z0-9 ]+", " ", text)
    text = re.sub(r"\s+", " ", text).strip()
    if "blanca" in text:
        return "relampago blanca"
    return text


def canon_result(raw: str, class_name: str = "") -> str:
    text = str(raw or "").strip()
    if not text:
        return ""
    low = text.lower()
    if low in SKIP_RESULTS:
        return ""
    low = re.sub(r"\s+place$", "", low).strip()
    low = re.sub(r"\s*\(pts\)$", "", low).strip()
    low = re.sub(r"\s*\(\d+(?:st|nd|rd|th)\)$", "", low).strip()
    if low in ("champ", "champion"):
        text = "Champion"
    elif low == "reserve":
        text = "Reserve"
    elif low in ("scr", "scr."):
        text = "SCR"
    elif low == "dnc":
        text = "DNC"
    elif low == "dnf":
        text = "DNF"
    else:
        text = low
    return normalize_placement_label(text, class_name)


def canon_time(raw) -> str | None:
    if raw in (None, ""):
        return None
    text = str(raw).strip()
    if text.lower() in SKIP_TIMES:
        return None
    text = re.sub(r"\s+secs?\.?$", "", text, flags=re.IGNORECASE).strip()
    text = re.sub(r"\s+mins?\.?$", "", text, flags=re.IGNORECASE).strip()
    return text or None


def tokens(text: str) -> set[str]:
    t = (text or "").lower().replace("½", "1/2")
    t = re.sub(r"[^a-z0-9]+", " ", t)
    stop = {
        "the", "and", "of", "trial", "terrier", "jack", "russell", "annual",
        "club", "network", "jrt", "jrtc", "working",
    }
    return {w for w in t.split() if w and w not in stop and len(w) > 1}


def rewrite_trial(name: str) -> tuple[str, str | None]:
    raw = (name or "").strip()
    day = None
    m = re.search(r"\((friday|saturday|sunday)\)", raw, re.I)
    if m:
        day = m.group(1).title()
        raw = raw[: m.start()] + raw[m.end() :]
    key = raw.strip().lower()
    for pat, repl in TRIAL_REWRITE:
        key = re.sub(pat, repl, key)
    key = re.sub(r"\s+", " ", key).strip()
    return key, day


def excel_class_to_base(excel_class: str, division: str) -> str:
    name = (excel_class or "").strip()
    name = name.replace("1/2", "½")
    name = re.sub(r"\s+", " ", name)
    # Racing shorthand: '12½-15" dogs'
    m = re.match(
        r'^(10-12\s*½"|12\s*½-15")\s+(dogs|bitches|veterans?|veteran dogs|veteran bitches|'
        r'senior veterans?)\s*$',
        name,
        re.I,
    )
    if m:
        height, who = m.group(1), m.group(2).lower()
        ht = (
            '10" up to 12½"'
            if height.startswith("10")
            else 'Over 12½" up to 15"'
        )
        if "senior" in who:
            return f"Senior, 9 years and older, {ht}"
        if "veteran bitch" in who:
            return f"Veteran Bitches, 6 years and older, {ht}"
        if "veteran dog" in who:
            return f"Veteran Dogs, 6 years and older, {ht}"
        if "veteran" in who:
            return f"Veteran, 6 years and older, {ht}"
        noun = "Dogs" if "dog" in who else "Bitches"
        return f"{noun}, 1 year and older, {ht}"
    m = re.match(
        r'^(\d{1,2}-\d{1,2}mo\.),\s*(10-12\s*½"|12\s*½-15")\s+(dog |bitch )?pups?$',
        name,
        re.I,
    )
    if m:
        ages, height, sex = m.group(1), m.group(2), (m.group(3) or "").lower()
        lo, hi = ages.replace("mo.", "").split("-")
        ht = 'Up to 12½"' if height.startswith("10") else 'Over 12½" up to 15"'
        return f"Pups, {lo} up to {hi} month, {ht}"
    # GTG shorthand
    name = re.sub(
        r'^(10-12\s*½"|12\s*½-15")\s+Championship,\s*(puppy|adult|veteran|senior)$',
        lambda m: f"{m.group(2).title()} Championship Certificate, {m.group(1)}",
        name,
        flags=re.I,
    )
    name = re.sub(r"\bsuper gtg\b", "Super Earth", name, flags=re.I)
    return normalize_class_name_full(name, division) or name


def racing_champ_class(excel_class: str) -> str:
    name = excel_class_to_base(excel_class, "RACING DIVISION")
    low = name.lower()
    if "pup" in low:
        age = "PUPPY"
    elif "senior" in low:
        age = "SENIOR"
    elif "veteran" in low:
        age = "VETERAN"
    else:
        age = "ADULT"
    if "10" in name and "12" in name:
        ht = '(10" up to 12½")'
    else:
        ht = '(Over 12½" up to 15")'
    return f"{age} RACING CHAMPION & RESERVE {ht}"


def infer_other_division(excel_class: str) -> str:
    low = (excel_class or "").lower()
    if "trail" in low or "locat" in low:
        return "TRAILING & LOCATING"
    if "barn" in low:
        return "BARN HUNT"
    if "brush" in low:
        return "BRUSH HUNT"
    if "ball toss" in low:
        return "BALL TOSS"
    if "ball retrieval" in low:
        return "BALL RETRIEVAL"
    if "lure" in low:
        return "LURE COURSING"
    if "agility" in low:
        return "AGILITY DIVISION"
    return "UNKNOWN"


def forward_fill_rows(sh, ncols: int) -> list[list]:
    rows = []
    year = None
    trial = None
    for r in range(1, sh.nrows):
        row = [sh.cell_value(r, c) for c in range(ncols)]
        if not any(v not in ("", None) for v in row):
            continue
        if row[1] not in ("", None):
            try:
                year = int(float(row[1]))
            except (TypeError, ValueError):
                pass
        if row[2] not in ("", None):
            trial = str(row[2]).strip()
        row[1] = year
        row[2] = trial
        rows.append(row)
    return rows


def parse_events(book: xlrd.Book) -> list[Event]:
    events: list[Event] = []

    sh = book.sheet_by_name("Racing")
    headers = [sh.cell_value(0, c) for c in range(sh.ncols)]
    for row in forward_fill_rows(sh, sh.ncols):
        nick, year, trial, excel_class = row[0], row[1], row[2], str(row[3] or "").strip()
        if not nick or not trial or not excel_class:
            continue
        trial_key, day = rewrite_trial(trial)
        for fam in RACE_FAMILIES:
            heat = canon_result(row[headers.index(fam["p"])])
            qtr = canon_result(row[headers.index(fam["q"])])
            semi = canon_result(row[headers.index(fam["s"])])
            final = canon_result(row[headers.index(fam["fin"])])
            if not (heat or qtr or semi or final):
                continue
            base = excel_class_to_base(excel_class, fam["div"])
            events.append(
                Event(
                    str(nick), year, trial_key, str(trial), day, excel_class, fam["div"],
                    f"{fam['prefix']} - {base}", final or "DNP",
                    source="Racing",
                    heat=heat or None,
                    qtr=qtr or None,
                    semi=semi or None,
                )
            )
        champ = canon_result(row[headers.index("Champ.")])
        if champ:
            events.append(
                Event(
                    str(nick), year, trial_key, str(trial), day, excel_class,
                    "RACING DIVISION", racing_champ_class(excel_class),
                    champ, source="Racing-Champ",
                )
            )

    def add_simple(sheet, division, time_col="Time", result_col="Result", extra=None):
        if sheet not in book.sheet_names():
            return
        sh = book.sheet_by_name(sheet)
        headers = [sh.cell_value(0, c) for c in range(sh.ncols)]
        for row in forward_fill_rows(sh, sh.ncols):
            nick, year, trial = row[0], row[1], row[2]
            excel_class = str(row[3] or "").strip()
            if not nick or not trial or not excel_class:
                continue
            trial_key, day = rewrite_trial(str(trial))
            result = canon_result(row[headers.index(result_col)] if result_col in headers else "")
            time = None
            if time_col in headers:
                time = canon_time(row[headers.index(time_col)])
            judge = None
            if extra == "judge" and "Judge" in headers:
                j = str(row[headers.index("Judge")] or "").strip()
                judge = j or None
            div = division
            if sheet == "GTG" and re.search(r"super", excel_class, re.I):
                div = "SUPER EARTH"
            if sheet == "Other":
                div = infer_other_division(excel_class)
            class_name = excel_class_to_base(excel_class, div)
            if day and div in ("LURE COURSING", "BRUSH HUNT", "BARN HUNT"):
                if not class_name.lower().startswith(day.lower()):
                    class_name = f"{day} - {class_name}"
            if not result and not time:
                continue
            if not result:
                result = "DNP"
            events.append(
                Event(
                    str(nick), year, trial_key, str(trial), day, excel_class, div,
                    class_name, result, time=time, judge=judge, source=sheet,
                )
            )

    add_simple("Conf", "CONFORMATION", time_col="", extra="judge")
    add_simple("GTG", "GO-TO-GROUND")
    add_simple("Agility", "AGILITY DIVISION", time_col="Score")
    add_simple("LC", "LURE COURSING")
    add_simple("Other", "UNKNOWN")

    if "03 Cumberland LC" in book.sheet_names():
        sh = book.sheet_by_name("03 Cumberland LC")
        for r in range(1, sh.nrows):
            nick = str(sh.cell_value(r, 0) or "").strip()
            owner = str(sh.cell_value(r, 1) or "").strip() or None
            trial = str(sh.cell_value(r, 2) or "").strip()
            excel_class = str(sh.cell_value(r, 3) or "").strip()
            time = canon_time(sh.cell_value(r, 4))
            if not nick or not excel_class:
                continue
            excel_name = re.sub(r"^\d{4}\s+", "", trial).strip() or "Cumberland I"
            trial_key, day = rewrite_trial(excel_name)
            events.append(
                Event(
                    nick, 2003, trial_key or excel_name.lower(), excel_name, day, excel_class,
                    "LURE COURSING", excel_class_to_base(excel_class, "LURE COURSING"),
                    "DNP", time=time, owner=owner, source="CumberlandLC",
                    allow_create_dog=True,
                )
            )
    return events


def load_dogs(cur) -> dict[str, int]:
    wanted = list(dict.fromkeys(DOG_NICK.values()))
    q = ",".join("?" * len(wanted))
    cur.execute(
        f"""
        SELECT d.DogID, d.DogName, COUNT(p.TrialPlacementsID) n
        FROM sResults.Dog d
        LEFT JOIN sResults.TrialPlacements p ON p.DogID=d.DogID
        WHERE LOWER(d.DogName) IN ({q})
        GROUP BY d.DogID, d.DogName
        """,
        [w.lower() for w in wanted],
    )
    best: dict[str, tuple[int, int]] = {}
    for dog_id, name, n in cur.fetchall():
        key = name.lower()
        prev = best.get(key)
        if not prev or n > prev[1]:
            best[key] = (dog_id, n)
    canon_by_lower = {w.lower(): w for w in wanted}
    return {canon_by_lower[k]: dog_id for k, (dog_id, _n) in best.items() if k in canon_by_lower}


def load_trials(cur) -> list[tuple[int, int, str, set[str]]]:
    cur.execute("SELECT TrialListID, Year, TrialName FROM sResults.TrialList")
    out = []
    for tid, year, name in cur.fetchall():
        out.append((tid, int(year or 0), name or "", tokens(name or "")))
    return out


def excel_trial_key(year, excel_trial: str) -> tuple[int, str]:
    name = re.sub(r"^\d{4}\s+", "", (excel_trial or "").strip())
    name = re.sub(r"\s+", " ", name).lower().strip()
    return int(year), name


def alias_match(year, needle: str, trials) -> tuple[int | None, str]:
    year_trials = [(tid, name) for tid, yr, name, _tks in trials if yr == int(year)]
    exact = [(tid, name) for tid, name in year_trials if name.lower() == needle]
    if len(exact) == 1:
        return exact[0]
    hits = [(tid, name) for tid, name in year_trials if needle in name.lower()]
    if not hits:
        return None, ""
    hits.sort(key=lambda t: (0 if t[1].lower() == needle else 1, len(t[1])))
    if len(hits) == 1 or hits[0][1].lower() == needle:
        return hits[0]
    if hits[0][1].lower() != hits[1][1].lower() and len(hits[0][1]) < len(hits[1][1]):
        return hits[0]
    return None, ""


def match_trial(year, trial_key: str, day: str | None, trials) -> tuple[int | None, str]:
    if not year or not trial_key:
        return None, ""
    low = re.sub(r"\s+", " ", trial_key.lower()).strip()
    roman = "ii" if re.search(r"\bii\b", low) else ("i" if re.search(r"\bi\b", low) else "")
    if int(year) == 2008 and ("sooner" in low or "oklahoma classic" in low):
        needle = "oklahoma classic ii" if roman == "ii" else "oklahoma classic i"
        for tid, yr, name, _tks in trials:
            if yr == int(year) and needle in name.lower():
                return tid, name
    want = tokens(trial_key)
    roman = None
    if re.search(r"\bii\b", trial_key):
        roman = "ii"
    elif re.search(r"\bi\b", trial_key):
        roman = "i"
    scored = []
    for tid, yr, name, tks in trials:
        if yr != int(year):
            continue
        overlap = len(want & tks)
        if overlap == 0:
            continue
        score = overlap * 2
        lname = name.lower()
        if trial_key in lname or all(w in lname for w in trial_key.split()[:2]):
            score += 3
        if roman == "ii" and re.search(r"\bii\b|2\b", lname):
            score += 2
        elif roman == "i" and re.search(r"\bi\b|1\b", lname) and not re.search(r"\bii\b", lname):
            score += 2
        if day and day.lower() in lname:
            score += 1
        scored.append((score, overlap, tid, name))
    if not scored:
        return None, ""
    scored.sort(reverse=True)
    best = scored[0]
    if best[0] < 3 or best[1] < 1:
        return None, ""
    if len(scored) > 1 and scored[0][0] == scored[1][0] and scored[0][2] != scored[1][2]:
        # tie: prefer unique token-heavy name
        if scored[0][1] == scored[1][1]:
            return None, ""
    return best[2], best[3]


def class_score(a: str, b: str) -> int:
    ta, tb = tokens(a), tokens(b)
    if not ta or not tb:
        return 0
    return int(10 * len(ta & tb) / len(ta | tb))


def load_dog_placements(cur, dog_ids: list[int]) -> dict[tuple[int, int], list[tuple]]:
    if not dog_ids:
        return {}
    q = ",".join("?" * len(dog_ids))
    cur.execute(
        f"""
        SELECT p.TrialPlacementsID, p.TrialListID, p.DogID, p.Result, p.TrialClassID,
               c.ClassName, dv.DivisionName, t.Time, p.Heat, p.Qtr, p.Semi
        FROM sResults.TrialPlacements p
        JOIN sResults.TrialClass tc ON tc.TrialClassID=p.TrialClassID
        JOIN sResults.Class c ON c.ClassID=tc.ClassID
        JOIN sResults.Division dv ON dv.DivisionID=c.DivisionID
        LEFT JOIN sResults.TrialPlacements_Times t ON t.TrialPlacementsID=p.TrialPlacementsID
        WHERE p.DogID IN ({q})
        """,
        dog_ids,
    )
    by = defaultdict(list)
    for row in cur.fetchall():
        by[(row[1], row[2])].append(row)
    return by


def same_division(a: str, b: str) -> bool:
    left = (normalize_division_name_full(a) or a or "").upper()
    right = (normalize_division_name_full(b) or b or "").upper()
    return bool(left) and left == right


def find_match(ev: Event, dog_id: int, trial_id: int, existing) -> tuple | None:
    cands = existing.get((trial_id, dog_id), [])
    if not cands:
        return None
    scored = []
    for row in cands:
        _pid, _tl, _did, result, _tc, cname, div, _time = row[:8]
        if re.search(r"\b(prelim|quarter|semi)\b", cname or "", re.I):
            continue
        if not same_division(ev.division, div or ""):
            continue
        score = 0
        if result == ev.result:
            score += 6
        elif result.lower() == ev.result.lower():
            score += 5
        score += class_score(ev.class_name, cname)
        scored.append((score, row))
    scored.sort(key=lambda x: x[0], reverse=True)
    if scored and scored[0][0] >= 8:
        return scored[0][1]
    return None


def placement_has_time(cur, pid: int) -> bool:
    cur.execute(
        "SELECT 1 FROM sResults.TrialPlacements_Times WHERE TrialPlacementsID=?",
        pid,
    )
    return cur.fetchone() is not None


def next_judge_id(cur) -> int:
    cur.execute("SELECT ISNULL(MAX(TrialList_JudgesID),0)+1 FROM sResults.TrialList_Judges")
    return cur.fetchone()[0]


def get_or_create_trialclass(cur, trial_id: int, class_id: int, next_tc: int) -> tuple[int, int, bool]:
    cur.execute(
        """
        SELECT TrialClassID FROM sResults.TrialClass
        WHERE TrialListID=? AND ClassID=?
        """,
        trial_id,
        class_id,
    )
    row = cur.fetchone()
    if row:
        return row[0], next_tc, False
    cur.execute(
        """
        INSERT INTO sResults.TrialClass (TrialClassID, TrialListID, ClassID, EntriesOnly)
        VALUES (?, ?, ?, 0)
        """,
        next_tc,
        trial_id,
        class_id,
    )
    return next_tc, next_tc + 1, True


def create_trial(cur, year: int, display_name: str, next_trial: int) -> int:
    cur.execute(
        """
        INSERT INTO sResults.TrialList
            (TrialListID, Year, TrialName, StartDate, EndDate,
             TrialResultFilePath, Loaded, CreateUser)
        VALUES (?, ?, ?, ?, ?, ?, 1, 'xls-tw')
        """,
        next_trial,
        year,
        display_name[:100],
        f"{year}-01-01",
        f"{year}-01-01",
        SOURCE_TAG[:255],
    )
    return next_trial


def lookup_dogs_by_name(cur, name: str) -> list[tuple]:
    cur.execute(
        """
        SELECT d.DogID, d.DogName, o.OwnerName, COUNT(p.TrialPlacementsID) n
        FROM sResults.Dog d
        LEFT JOIN sResults.Owner o ON o.OwnerID=d.OwnerID
        LEFT JOIN sResults.TrialPlacements p ON p.DogID=d.DogID
        WHERE LOWER(d.DogName)=LOWER(?)
        GROUP BY d.DogID, d.DogName, o.OwnerName
        ORDER BY COUNT(p.TrialPlacementsID) DESC
        """,
        name,
    )
    return cur.fetchall()


def get_or_create_owner(cur, owner_name: str, apply: bool, stats: Stats) -> int | None:
    name = re.sub(r"\s+", " ", (owner_name or "").strip())
    if not name:
        return None
    cur.execute(
        "SELECT OwnerID FROM sResults.Owner WHERE LOWER(OwnerName)=LOWER(?)",
        name,
    )
    row = cur.fetchone()
    if row:
        return row[0]
    if apply:
        cur.execute(
            "INSERT INTO sResults.Owner (OwnerName) OUTPUT INSERTED.OwnerID VALUES (?)",
            name[:255],
        )
        owner_id = cur.fetchone()[0]
    else:
        owner_id = None
    stats.owners_created += 1
    return owner_id


def pick_existing_dog(rows: list[tuple], owner: str | None) -> int | None:
    if not rows:
        return None
    if owner:
        scored = []
        want = tokens(owner)
        for dog_id, _name, owner_name, n in rows:
            overlap = len(want & tokens(owner_name or ""))
            scored.append((overlap, n, dog_id))
        scored.sort(reverse=True)
        if scored[0][0] >= 1:
            return scored[0][2]
    if len(rows) == 1:
        return rows[0][0]
    name = rows[0][1] or ""
    if len(name.split()) >= 3:
        return rows[0][0]
    return None


def resolve_dog(
    cur, ev: Event, dogs: dict[str, int], created_dogs: dict, apply: bool, stats: Stats
) -> int | None:
    canon = DOG_NICK.get(nick_key(ev.dog_nick))
    if canon:
        return dogs.get(canon)
    if not ev.allow_create_dog:
        return None
    cache_key = (ev.dog_nick.lower(), (ev.owner or "").lower())
    if cache_key in created_dogs:
        return created_dogs[cache_key]
    rows = lookup_dogs_by_name(cur, ev.dog_nick)
    dog_id = pick_existing_dog(rows, ev.owner)
    if dog_id:
        created_dogs[cache_key] = dog_id
        return dog_id
    owner_id = get_or_create_owner(cur, ev.owner or "", apply, stats) if ev.owner else None
    if apply:
        cur.execute(
            "INSERT INTO sResults.Dog (DogName, OwnerID) OUTPUT INSERTED.DogID VALUES (?, ?)",
            ev.dog_nick[:255],
            owner_id,
        )
        dog_id = cur.fetchone()[0]
    else:
        dog_id = -1 - len(created_dogs)
    created_dogs[cache_key] = dog_id
    stats.dogs_created += 1
    return dog_id


def resolve_trial(
    ev: Event, trials, created_trials: dict, cur, next_trial: int, apply: bool, stats: Stats
) -> tuple[int | None, str, int]:
    key = excel_trial_key(ev.year, ev.excel_trial)
    if key in created_trials:
        tid, name = created_trials[key]
        return tid, name, next_trial
    alias = EXISTING_ALIAS.get(key)
    if alias:
        tid, name = alias_match(ev.year, alias, trials)
        if tid:
            return tid, name, next_trial
    tid, name = match_trial(ev.year, ev.trial_raw, ev.day, trials)
    if tid:
        return tid, name, next_trial
    display = CREATE_TRIALS.get(key)
    if not display:
        return None, "", next_trial
    if apply:
        tid = create_trial(cur, int(ev.year), display, next_trial)
        next_trial += 1
    else:
        tid = -1 - len(created_trials)
    created_trials[key] = (tid, display)
    trials.append((tid, int(ev.year), display, tokens(display)))
    stats.trials_created += 1
    stats.created_names.append(display)
    return tid, display, next_trial


def run(apply: bool) -> Stats:
    book = open_xls()
    events = parse_events(book)
    stats = Stats(parsed=len(events))
    conn = pyodbc.connect(CONN_STR)
    cur = conn.cursor()
    dogs = load_dogs(cur)
    trials = load_trials(cur)
    existing = load_dog_placements(cur, list(dogs.values()))
    next_trial, next_tc, next_pl = get_next_ids_from_db(conn)
    next_tm = get_next_placement_times_id(conn)
    next_j = next_judge_id(cur)
    judges_seen: set[tuple[int, str]] = set()
    cur.execute("SELECT TrialListID, JudgeName FROM sResults.TrialList_Judges")
    for tid, jn in cur.fetchall():
        judges_seen.add((tid, (jn or "").strip().lower()))

    created_trials: dict[tuple[int, str], tuple[int, str]] = {}
    created_dogs: dict[tuple[str, str], int] = {}

    for ev in events:
        if not ev.year:
            stats.skipped += 1
            continue
        dog_id = resolve_dog(cur, ev, dogs, created_dogs, apply, stats)
        if not dog_id:
            stats.skipped += 1
            if ev.dog_nick not in stats.unmatched_dog:
                stats.unmatched_dog.append(ev.dog_nick)
            continue
        trial_id, trial_name, next_trial = resolve_trial(
            ev, trials, created_trials, cur, next_trial, apply, stats
        )
        if not trial_id:
            stats.skipped += 1
            key = excel_trial_key(ev.year, ev.excel_trial)
            if key not in stats.unmatched_trial:
                stats.unmatched_trial.append(key)
            continue

        match = find_match(ev, dog_id, trial_id, existing)
        if match:
            stats.matched += 1
            pid, _tl, _did, _res, _tc, cname, _div, time = match[:8]
            cur_heat = match[8] if len(match) > 8 else None
            cur_qtr = match[9] if len(match) > 9 else None
            cur_semi = match[10] if len(match) > 10 else None
            if ev.source == "Racing" and (ev.heat or ev.qtr or ev.semi):
                if apply:
                    cur.execute(
                        """
                        UPDATE sResults.TrialPlacements
                        SET Heat=COALESCE(?, Heat), Qtr=COALESCE(?, Qtr), Semi=COALESCE(?, Semi)
                        WHERE TrialPlacementsID=?
                        """,
                        ev.heat,
                        ev.qtr,
                        ev.semi,
                        pid,
                    )
                if (ev.heat and not cur_heat) or (ev.qtr and not cur_qtr) or (ev.semi and not cur_semi):
                    stats.heats_updated += 1
            if ev.time and not time and not (apply and placement_has_time(cur, pid)):
                if apply:
                    cur.execute(
                        """
                        INSERT INTO sResults.TrialPlacements_Times
                            (TrialPlacements_TimesID, TrialPlacementsID, Time)
                        VALUES (?, ?, ?)
                        """,
                        next_tm,
                        pid,
                        ev.time[:255],
                    )
                    next_tm += 1
                    updated = []
                    for row in existing.get((trial_id, dog_id), []):
                        vals = list(row)
                        if vals[0] == pid:
                            vals[7] = ev.time
                        updated.append(tuple(vals))
                    existing[(trial_id, dog_id)] = updated
                stats.times_added += 1
            if ev.judge and (trial_id, ev.judge.lower()) not in judges_seen:
                if apply:
                    div_id = get_or_create_division(cur, "CONFORMATION")
                    cur.execute(
                        """
                        INSERT INTO sResults.TrialList_Judges
                            (TrialList_JudgesID, TrialListID, DivisionID, JudgeName)
                        VALUES (?, ?, ?, ?)
                        """,
                        next_j,
                        trial_id,
                        div_id,
                        ev.judge[:255],
                    )
                    next_j += 1
                judges_seen.add((trial_id, ev.judge.lower()))
                stats.judges_added += 1
            if len(stats.samples) < 12:
                stats.samples.append(("MATCH", ev, trial_name or trial_id, cname))
            continue

        # Do not add a DNP when the dog already has a result in a similar class.
        if ev.result == "DNP":
            already = any(
                class_score(ev.class_name, row[5]) >= 4 and same_division(ev.division, row[6] or "")
                for row in existing.get((trial_id, dog_id), [])
            )
            if already:
                stats.skipped += 1
                continue

        if apply:
            div_id = get_or_create_division(cur, ev.division)
            class_name = normalize_class_name_full(ev.class_name, ev.division) or ev.class_name
            class_id = get_or_create_class(cur, class_name[:255], div_id)
            tc_id, next_tc, _ = get_or_create_trialclass(cur, trial_id, class_id, next_tc)
            cur.execute(
                """
                INSERT INTO sResults.TrialPlacements
                    (TrialPlacementsID, TrialListID, TrialClassID, DogID, Result, Heat, Qtr, Semi)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                """,
                next_pl,
                trial_id,
                tc_id,
                dog_id,
                ev.result[:255] if ev.result else None,
                ev.heat[:255] if ev.heat else None,
                ev.qtr[:255] if ev.qtr else None,
                ev.semi[:255] if ev.semi else None,
            )
            pid = next_pl
            next_pl += 1
            existing[(trial_id, dog_id)].append(
                (
                    pid, trial_id, dog_id, ev.result, tc_id, class_name, ev.division,
                    ev.time, ev.heat, ev.qtr, ev.semi,
                )
            )
            if ev.heat or ev.qtr or ev.semi:
                stats.heats_updated += 1
            if ev.time:
                cur.execute(
                    """
                    INSERT INTO sResults.TrialPlacements_Times
                        (TrialPlacements_TimesID, TrialPlacementsID, Time)
                    VALUES (?, ?, ?)
                    """,
                    next_tm,
                    pid,
                    ev.time[:255],
                )
                next_tm += 1
                stats.times_added += 1
            if ev.judge and (trial_id, ev.judge.lower()) not in judges_seen:
                jdiv = get_or_create_division(cur, "CONFORMATION")
                cur.execute(
                    """
                    INSERT INTO sResults.TrialList_Judges
                        (TrialList_JudgesID, TrialListID, DivisionID, JudgeName)
                    VALUES (?, ?, ?, ?)
                    """,
                    next_j,
                    trial_id,
                    jdiv,
                    ev.judge[:255],
                )
                next_j += 1
                judges_seen.add((trial_id, ev.judge.lower()))
                stats.judges_added += 1
        else:
            if ev.time:
                stats.times_added += 1
            if ev.heat or ev.qtr or ev.semi:
                stats.heats_updated += 1
            if ev.judge and (trial_id, ev.judge.lower()) not in judges_seen:
                judges_seen.add((trial_id, ev.judge.lower()))
                stats.judges_added += 1
        stats.placements_added += 1
        if len(stats.samples) < 20:
            stats.samples.append(("INSERT", ev, trial_name or trial_id, ev.class_name))

    if apply:
        conn.commit()
    else:
        conn.rollback()
    conn.close()
    return stats


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--apply", action="store_true", help="Write to TrialResults")
    args = parser.parse_args()
    stats = run(apply=args.apply)
    mode = "APPLY" if args.apply else "DRY-RUN"
    print(f"\n=== {mode} ===")
    print(f"parsed={stats.parsed} matched={stats.matched} insert={stats.placements_added}")
    print(f"times={stats.times_added} heats={stats.heats_updated} judges={stats.judges_added}")
    print(f"trials_new={stats.trials_created} dogs_new={stats.dogs_created} owners_new={stats.owners_created}")
    print(f"skipped={stats.skipped}")
    print("unmatched dogs", stats.unmatched_dog[:20])
    print("unmatched trials", stats.unmatched_trial[:30])
    print("created trials:")
    for name in stats.created_names:
        print(f"  {name}")
    print("\nSamples:")
    for kind, ev, trial, cls in stats.samples:
        print(
            f"  {kind} {ev.year} {trial!r} {ev.dog_nick} {ev.result} "
            f"{cls!r} time={ev.time} heat={ev.heat} qtr={ev.qtr} semi={ev.semi} src={ev.source}"
        )


if __name__ == "__main__":
    main()
