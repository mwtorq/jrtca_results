#!/usr/bin/env python3
"""Canonical yearbook HQ OCR + results-text cleanup (baseline v2 pipeline).

Correction order (do not invert):
  1. OCR first — preprocess ensemble, PSM variants, place-line token voting
  2. Structural finalize — place ranks, owned-by, heights, gutter
  3. Name hardcodes last — ``_OCR_NAME_PHRASES`` only for residuals OCR missed

Public entry points used by ``ocr_yearbook_baseline_v2`` and related CLIs:
  - ``ocr_pdf_hq`` / ``ocr_page_best`` — structure OCR (header + two-column)
  - ``finalize_results_ocr`` — gutter strip + place/lexical repairs
  - ``audit_results_ocr_page`` — residual defect self-audit

Prefer this module over the legacy ``_yearbook_meta_strict`` shim.
"""
from __future__ import annotations

import argparse
import os
import re
import sys
import threading
from concurrent.futures import FIRST_COMPLETED, ThreadPoolExecutor, as_completed, wait
from dataclasses import dataclass
from pathlib import Path
from typing import Callable

import pyodbc
from PIL import Image, ImageFilter, ImageOps

from ocr_yearbook_source import (
    TESSERACT_EXE,
    configure_tesseract,
    derive_year_from_text,
    ocr_sibling_path,
    render_pdf_pages,
)
from remount_source_divisions import CONN
from yearbook_meta_schema import ensure

ROOT = Path(r"c:\Users\mw\OneDrive - timberwilde.net\repos\jrtca_results")
UPDATED = ROOT / "Updated Yearbook Scans"

EARLY = ["1984 & 1985", "1986", "1987", "1988", "1989", "1990"]

_END_HEADERS = re.compile(
    r"(?i)^(?:"
    r"BOARD\s+OF\s+DIRECTORS|"
    r"REPRESENTATIVES?\s+COMMITTEE|"
    r"JUDGES\s+COMMITTEE|"
    r"TRIAL\s+COMMITTEE|"
    r"BREEDERS?\s+COMMITTEE|"
    r"STANDARDS?\s+COMMITTEE|"
    r"STATE\s+REPRESENTATIVES?|"
    r"NEW\s+CLUB\s+MEMBERS?|"
    r"NEW\s+KENNEL\s+PREFIX|"
    r"NEWLY\s+REGISTERED\s+KENNEL|"
    r"TRANSFERS?\s+OF\s+OWNERSHIP|"
    r"NEW\s+TERRIER\s+REGISTRATIONS?|"
    r"NEW\s+REGISTRATIONS?|"
    r"DIRECTORY\s+OF\s+BREEDERS?|"
    r".*BREEDER\s+DIRECTORY|"
    r"TRIAL\s+CERTIFICATES?|"
    r"NATURAL\s+HUNTING|"
    r"WORKING\s+CERTIFICATES?|"
    r"DIVISION\s+[A-D]\b|"
    r"SANCTIONED\s+TRIAL|"
    r"CONTENTS\b|"
    r"INTRODUCTION\b|"
    r"OCR-ENSEMBLE-EXTRAS"
    r")"
)

_ROLE_RE = (
    r"(Chairman|Chairperson|Vice[- ]?Chairman|Vice[- ]?Chair|"
    r"President|Secretary|Treasurer|Director|VC)\b"
)
# Honorific + First + optional middle initial/name + Last + optional suffix
# Mes./Mre./Mra. are common OCR mangling of Mrs.
_NAME_CORE = (
    r"(?:(?:Mrs?|Ms|Miss|Dr|Mes|Mre|Mra)\.?\s+)?"
    r"([A-Z][A-Za-z'\-]+"
    r"(?:\s+[A-Z]\.?)?"  # middle initial Harden L. / Harden L
    r"(?:\s+[A-Z][A-Za-z'\-]+){1,2}"  # last (+ optional maiden/middle)
    r"(?:\s+(?:Jr\.?|Sr\.?|II|III|IV|2nd|3rd))?"
    r")"
)
_ROLE_WORDS = {
    "chairman", "chairperson", "vice-chairman", "vice", "chair",
    "president", "secretary", "treasurer", "director", "member", "vc",
}

_ADDR_TOKENS = {
    "road", "rd", "street", "st", "ave", "avenue", "blvd", "boulevard",
    "lane", "ln", "drive", "dr", "way", "court", "ct", "circle", "cir",
    "place", "pl", "parkway", "pkwy", "highway", "hwy", "route", "rte",
    "rt", "box", "po", "pob", "rural", "rr", "tel", "telephone", "phone",
    "fax", "suite", "ste", "apt", "apartment", "unit", "floor", "fl",
    "cove", "hills", "hill", "bend", "creek", "brook", "ridge", "valley",
    "springs", "spring", "meadow", "meadows", "acres", "farm", "ranch",
    "manor", "estate", "estates", "heights", "park", "plaza", "square",
    "north", "south", "east", "west", "n", "s", "e", "w", "ne", "nw", "se", "sw",
}

_REJECT_TOKENS = {
    "dog", "dogs", "bitch", "bitches", "pup", "pups", "puppy", "entries",
    "class", "champion", "championship", "reserve", "novice", "open",
    "smooth", "broken", "rough", "adult", "veteran", "working", "terrier",
    "terriers", "best", "owned", "judge", "judges", "division", "racing",
    "conformation", "ground", "certificate", "certificates", "hollow",
    "gate", "farm", "kennel", "network", "trial", "club", "jrtca", "awta",
    "sth", "bths", "lst", "nd", "rd", "th", "committee", "board", "breed",
    "standard", "directory", "listing", "members", "continued", "page",
    "chalrman", "chalrsan", "chairnan",
} | _ADDR_TOKENS

_STATE_NAMES_TO_ABBR = {
    "ALABAMA": "AL", "ALASKA": "AK", "ARIZONA": "AZ", "ARKANSAS": "AR",
    "CALIFORNIA": "CA", "COLORADO": "CO", "CONNECTICUT": "CT", "DELAWARE": "DE",
    "FLORIDA": "FL", "GEORGIA": "GA", "HAWAII": "HI", "IDAHO": "ID",
    "ILLINOIS": "IL", "INDIANA": "IN", "IOWA": "IA", "KANSAS": "KS",
    "KENTUCKY": "KY", "LOUISIANA": "LA", "MAINE": "ME", "MARYLAND": "MD",
    "MASSACHUSETTS": "MA", "MICHIGAN": "MI", "MINNESOTA": "MN", "MISSISSIPPI": "MS",
    "MISSOURI": "MO", "MONTANA": "MT", "NEBRASKA": "NE", "NEVADA": "NV",
    "NEW HAMPSHIRE": "NH", "NEW JERSEY": "NJ", "NEW MEXICO": "NM", "NEW YORK": "NY",
    "NORTH CAROLINA": "NC", "NORTH DAKOTA": "ND", "OHIO": "OH", "OKLAHOMA": "OK",
    "OREGON": "OR", "PENNSYLVANIA": "PA", "RHODE ISLAND": "RI",
    "SOUTH CAROLINA": "SC", "SOUTH DAKOTA": "SD", "TENNESSEE": "TN", "TEXAS": "TX",
    "UTAH": "UT", "VERMONT": "VT", "VIRGINIA": "VA", "WASHINGTON": "WA",
    "WEST VIRGINIA": "WV", "WISCONSIN": "WI", "WYOMING": "WY",
}
_STATE_NAME_ALT = "|".join(
    re.escape(s) for s in sorted(_STATE_NAMES_TO_ABBR, key=len, reverse=True)
)
_CITY_ST = re.compile(
    rf"\b([A-Z][A-Za-z.'\-]+(?:\s+[A-Z][A-Za-z.'\-]+){{0,4}}),\s*"
    rf"(?:([A-Z]{{2}})|({_STATE_NAME_ALT}))\s+(\d{{5}})",
    re.I,
)
_PHONE = re.compile(r"\(?\d{3}\)?[-.\s]?\d{3}[-.\s]?\d{4}")
_STREET = re.compile(
    r"(?i)\b("
    r"P\.?\s*[O0]\.?\s*Box\s+\d+"
    r"|Box\s+\d+"
    r"|R\.?R\.?\s*\d+(?:,?\s*Box\s+\d+)?"
    r"|R\.?D\.?\s*\d+(?:,?\s*Box\s+\d+)?"
    r"|Rt\.?\s*\d+(?:,?\s*Box\s+\d+)?"
    r"|\d{1,5}\s+[A-Za-z0-9.'\-]+(?:\s+[A-Za-z0-9.'\-]+){0,4}"
    r"\s+(?:Road|Rd|Street|St|Avenue|Ave|Lane|Ln|Drive|Dr|Way|Court|Ct|"
    r"Circle|Cir|Place|Pl|Blvd|Boulevard|Parkway|Hwy|Highway)"
    r")\b"
)
_CITY_PREFIX = {
    "new", "san", "los", "las", "fort", "ft", "port", "mount", "mt",
    "saint", "st", "west", "east", "north", "south", "lake", "des",
    "el", "la", "santa", "cape", "grand", "little", "big", "upper",
    "lower", "far",
}
_ROLE_NAME_PAT = re.compile(
    rf"{_NAME_CORE}\s*,\s*{_ROLE_RE}",
    re.I,
)
# Person line without role (stops address windows): "Mrs. Susan McRae" / "George Woodward"
_PERSON_LINE_PAT = re.compile(
    rf"(?im)^\s*{_NAME_CORE}\s*$"
)

# OCR often swaps l↔i in addresses/names (Middie→Middle, Hillis→Hills).
# Exact token fixes (matched case-insensitively; replacement keeps Title/lower form).
_OCR_LI_FIXES = {
    "middie": "middle",
    "middis": "middle",
    "hillis": "hills",
    "hilis": "hills",
    "hiils": "hills",
    "miilers": "millers",
    "miliers": "millers",
    "stilweil": "stilwell",
    "stilwell": "stilwell",
    "stiwell": "stilwell",
    "stiiwell": "stilwell",
    "beckersville": "beckleysville",
    "beckieysville": "beckleysville",
    "beckiey": "beckley",
    "brandamore": "brandamore",
    "brandemore": "brandamore",
    "brendasore": "brandamore",
    "pleasant": "pleasant",
    "phi lhower": "philhower",  # handled via multiword below
    "philhower": "philhower",
    "phihower": "philhower",
    "phiihower": "philhower",
    "woodinville": "woodinville",
    "woodinviile": "woodinville",
    "tuscumbia": "tuscumbia",
    "tuscumbla": "tuscumbia",
    "christiana": "christiana",
    "christlana": "christiana",
    "ridgefield": "ridgefield",
    "ridgeneld": "ridgefield",
    "lewisville": "lewisville",
    "lewisviile": "lewisville",
    "downingtown": "downingtown",
    "downlngtown": "downingtown",
    "fitchburg": "fitchburg",
    "fitehburg": "fitchburg",
    "pataskala": "pataskala",
    "malvern": "malvern",
    "mai vern": "malvern",
    "beavercreek": "beavercreek",
    "waterford": "waterford",
    "succabone": "succabone",
    "succahone": "succabone",
    "geneseo": "geneseo",
    "genesco": "geneseo",
    "cornersville": "cornersville",
    "comersville": "cornersville",
    "wiliiam": "william",
    "wiliam": "william",
    "califomia": "california",
    "californa": "california",
    "pennsyivania": "pennsylvania",
    "pennsyivama": "pennsylvania",
    "aiisa": "ailsa",
    "allsa": "ailsa",
    "ailsa": "ailsa",
    "chalrman": "chairman",
    "chalrsan": "chairman",
    "chairnan": "chairman",
    "vice-chalrman": "vice-chairman",
    "babzer": "batzer",
    "batzar": "batzer",
    "bater": "batzer",
    "ortolono": "ortolano",
    "dougherty": "dougherty",
    "dougerty": "dougherty",
    "deugiiencys": "dougherty",
    "deugilencys": "dougherty",
    "deugiencys": "dougherty",
    "mansy": "nancy",
    "rancy": "nancy",
    "naney": "nancy",
    "nancey": "nancy",
    "churchtield": "churchfield",
    "churchfleld": "churchfield",
    "brownridqe": "brownridge",
    "ailsa": "ailsa",
    "allsa": "ailsa",
    "aiisa": "ailsa",
    # kennel / dog-name OCR (yearbook photos)
    "foxfield": "foxfield",
    "fox6eld": "foxfield",
    "x6eld": "foxfield",
    "foxfleld": "foxfield",
    "foxtleld": "foxfield",
    "foxfiold": "foxfield",
    "briarpatch": "briarpatch",
    "brlarpatch": "briarpatch",
    "bharpatch": "briarpatch",
    "bdarpatch": "briarpatch",
    "brlatpatch": "briarpatch",
    "tailor": "tailor",
    "sukey": "sukey",
    "sukoy": "sukey",
    "windermere": "windermere",
    "windennere": "windermere",
    "pinehaven": "pinehaven",
    "plnehaven": "pinehaven",
}

# Residual name repairs AFTER OCR ensemble/voting (fallback only — fix OCR first).
_OCR_NAME_PHRASES = (
    (r"(?i)\b(?:l\\\)?x6eld|x6eld|fox6eld)\s+nor\b", "Foxfield Flor"),
    # Truncated caption "Sukoy of" / "Sukoy of\nowned by" → full name from photo
    (r"(?i)\bSukoy\s+of(?:\s+Wyndcroft)?\b", "Sukey of Wyndcroft"),
    (r"(?i)\bTaIlor\b", "Tailor"),
    (r"(?i)\bBrlarpatch\b", "Briarpatch"),
    (r"(?i)\bBHarpatch\b", "Briarpatch"),
    (r"(?i)\bBdarpatch\b", "Briarpatch"),
    (r"(?i)\bPlnehaven\b", "Pinehaven"),
    (r"(?i)\bWil1-0-Moor\b", "Will-O-Moor"),
    (r"(?i)\bWIndy\s+HIll\b", "Windy Hill"),
    # "Windy i Sugarbaker" — Hill collapsed to bare i / | / 1
    (r"(?i)\bWindy\s+[i|1l]\s+Sugarbaker\b", "Windy Hill Sugarbaker"),
    (r"(?i)\bWindy\s+[i|1l]\s+(?=[A-Z])", "Windy Hill "),
    # Fallback when ensemble still merges l into Windy / doubles i in Ellis
    (r"(?i)\bWindly\b", "Windy"),
    (r"(?i)\bEillis\b", "Ellis"),
    (r"(?i)\bSugarbak8r\b", "Sugarbaker"),
    # O↔Qa / Bia↔Bla / "& Betty"→"Bait" residuals
    (r"(?i)\bQaldield\b", "Oakfield"),
    (r"(?i)\bBianquita\b", "Blanquita"),
    (r"(?i)\bJohn\s+Bait\s+Badgwell\b", "John & Betty Badgwell"),
    (r"(?i)\bRA\.\s+(?=[A-Z])", "R.A. "),
    (r"(?i)\bowned\s+by\s+RA\.\s+", "owned by R.A. "),
    (r"(?i)\bFox\s+Ru;?I\b", "Fox Run"),
    (r"(?i)\bRusHer's\b", "Rustler's"),
    (r"(?i)\bHor9ema9tor's\b", "Horsemaster's"),
    (r"(?i)\bLnrches\b", "Larches"),
    (r"(?i)\bBogcachlel\b", "Bogachiel"),
    # g↔b under pink highlighter / thin scans (never bare Doub→Doug — breaks "Double D")
    (r"(?i)\bDoub\s*&\s*Sue\b", "Doug & Sue"),
    (r"(?i)\bDouq\s*&\s*Sue\b", "Doug & Sue"),
    (r"(?i)\bDoud\s*&\s*Sue\b", "Doug & Sue"),
    (r"(?i)\bFarmeliff\b", "Farmcliff"),
    (r"(?i)\bFarmceliff\b", "Farmcliff"),
    (r"(?i)\bFanncliff\b", "Farmcliff"),
    (r"(?i)\bFameliff\b", "Farmcliff"),
    (r"(?i)\bFanmeliff?\b", "Farmcliff"),
    (r"(?i)\bFaneliff\b", "Farmcliff"),
    (r"(?i)\bParmeutt\b", "Farmcliff"),
    (r"(?i)\bFarmclitf\b", "Farmcliff"),
    (r"(?i)\bGenie['\"]?Frankl", "Genie Franklin"),
    (r"(?i)\bBobl?\s*&\s*Geniel?\s*Frankl\w*", "Bob & Genie Franklin"),
    (r"(?i)\bB\.?\s*&\s*G\.?\s*Fr(?:ankl\w*)?\b", "B. & G. Franklin"),
    (r"(?i)\bowned['\":;,.]*by['\":;,.]*Bob", "owned by Bob"),
    (r"(?i)\bLickily\b", "Lickity"),
    (r"(?i)\bLickity\s*[.\-]*\s*Split\s*[.\-]*\s*Sassy\b", "Lickity Split Sassy"),
    # Double consonant / glyph swaps from thin Helvetica / highlighter
    (r"(?i)\bPrestwickk's\b", "Prestwick's"),
    (r"(?i)\bPrestwickk\b", "Prestwick"),
    (r"(?i)\bPrestwock's\b", "Prestwick's"),
    (r"(?i)\bPrestwock\b", "Prestwick"),
    (r"(?i)\bPrestwic's\b", "Prestwick's"),
    (r"(?i)\bLolbolly\b", "Loblolly"),
    (r"(?i)\bLobloily\b", "Loblolly"),
    (r"(?i)\bLobloly\b", "Loblolly"),
    (r"(?i)\bMountan\b", "Mountain"),
    (r"(?i)\bJ,\s*Kozak\b", "J. Kozak"),
    (r"(?i)\bGeroge\b", "George"),
    (r"(?i)\bGeorqe\b", "George"),
    (r"(?i)\bCherly\b", "Cheryl"),
    (r"(?i)\bChery!(?=\s|$|,)", "Cheryl"),
    (r"(?i)\bChery(?=\s+Wallace\b)", "Cheryl"),
    # Judges: "NANCY DIedKslone" / "DiedKslone" → Breakstone
    (r"(?i)\bD[Ii]edKslone\b", "Breakstone"),
    (r"(?i)\bDiedKslone\b", "Breakstone"),
    (r"(?i)\bBreakstome\b", "Breakstone"),
    (r"(?i)\bBreakstoue\b", "Breakstone"),
    (r"(?i)\bRidgebiew\b", "Ridgeview"),
    (r"(?i)\bBiorkland\b", "Bjorkland"),
    (r"(?i)\bHghland\b", "Highland"),
    (r"(?i)\bVog\s+Fups\b", "Dog Pups"),
    (r"(?i)\bDog\s+Fups\b", "Dog Pups"),
    (r"(?i)\bVog\s+Pups\b", "Dog Pups"),
    # Leading Th eaten by old dup-place bug / thin OCR
    (r"(?i)\bree\s+Oaks\b", "Three Oaks"),
    (r"(?i)\bTh\s*ree\s+Oaks\b", "Three Oaks"),
    (r"(?i)\bablemate'?s?\b", "Tablemate's"),
    (r"(?i)\bTablemate'?s\b", "Tablemate's"),
    # Mid-line wrap OCR: "Farms Hu" + "inter," → Huinter
    (r"(?i)\bHuinter\b", "Hunter"),
    (r"(?i)\bHideaway\s+Farms\s+Huinter\b", "Hideaway Farms Hunter"),
    # Owner wrap: "Marchlinsh" + "um" / bare truncation
    (r"(?i)\bMarchlinshum\b", "Marchlinski"),
    (r"(?i)\bMarchlinsh\b", "Marchlinski"),
    # Glued trial title words
    (r"(?i)\bWorkingTerrier\b", "Working Terrier"),
    (r"(?i)\bJRTCAWORKING\b", "JRTCA WORKING"),
    (r"(?i)\bJRTCA(?=[A-Z][a-z])", "JRTCA "),
    (r"(?i)\bWorking\s*Terrier\s*Trial\b", "Working Terrier Trial"),
    (r"(?i)\bNovic[eéèê]\b", "Novice"),
    (r"(?i)\bVOWaSJee\b", "Cowasjee"),
    (r"(?i)\bVowaSjee\b", "Cowasjee"),
    (r"(?i)\bCowasjee\b", "Cowasjee"),
    (r"(?i)\bGo-\s*1\s*O-?UlOUn'?\b", "Go-to-Ground"),
    (r"(?i)\bGo-\s*to-\s*Ground\b", "Go-to-Ground"),
    # Roman III misread as Ill / Ili / lll (before owned by OR as owner/dog suffix)
    (r"(?i)\bIll\b(?=,?\s*owned\s+by)", "III"),
    (r"(?i)\bSmarty\s+Ill\b", "Smarty III"),
    # "owned by Bobby Joe Duty Ill/Ili/lll" and EOL surname+Ill
    (r"(?i)\b(Ill|Ili|Iii|lll)\b(?=\s*$)", "III"),
    (r"(?i)\b(Ill|Ili|Iii|lll)\b(?=,)", "III"),
    # Cut-off steeplechase section title (leading S eaten)
    (r"(?im)^TEEPLECHASE\b", "STEEPLECHASE"),
    (r"(?i)(?<![A-Za-z])TEEPLECHASE\b", "STEEPLECHASE"),
    (r"(?i)\bCormwell\b", "Cromwell"),
    (r"(?i)\bSeview\b", "Seaview"),
    (r"(?i)\bMeredithRennie\b", "Meredith Rennie"),
    (r"(?i)\bHeavin\s+Hill\b", "Heaven Hill"),
    (r"(?i)\bHeaven\s+Hil\b", "Heaven Hill"),
    (r"(?i)\bHeven\s+Hill\b", "Heaven Hill"),
    # Heaven Hill Guinness owner — 1997 OCR Shirley→Shelley (later vols agree)
    (r"(?i)\bShirley\s+Holland\b", "Shelley Holland"),
    (r"(?i)\bShelly\s+Holland\b", "Shelley Holland"),
    # Kennel Duir — Duie/Dur OCR; Bellistic variants
    (r"(?i)\bDuie\s+Bellistic\b", "Duir Bellistic"),
    (r"(?i)\bDur\s+Bellistic\b", "Duir Bellistic"),
    (r"(?i)\bDuirBellistic\b", "Duir Bellistic"),
    (r"(?i)\bDuir\s+Bellell?istic\b", "Duir Bellistic"),
    (r"(?i)\bBellell?istic\b", "Bellistic"),
    # Kennel Terrier Turf — Tufts/Turfs/Mayhym OCR
    (r"(?i)\bTerrier\s+Tufts\b", "Terrier Turf"),
    (r"(?i)\bTerrier\s+Turfs\b", "Terrier Turf"),
    (r"(?i)\bTerrier\s+Turf\s+Mayhym\b", "Terrier Turf Mayhem"),
    (r"(?i)\bTerrier\s+Turf\s+Mayhem\b", "Terrier Turf Mayhem"),
    # Cut-off leading letter(s) on class / racing headers
    (r"(?im)^3itches\b", "Bitches"),
    (r"(?im)^itches\b", "Bitches"),
    (r"(?im)^itch\s+Pups\b", "Bitch Pups"),
    (r"(?im)^Jog\s+Pups\b", "Dog Pups"),
    (r"(?im)^logs\b", "Dogs"),
    (r"(?im)^nder\s+12\b", "Under 12"),
    (r"(?im)^ver\s+12\b", "Over 12"),
    # Mid-line cutoffs (after place prefix stripped / still on place line)
    (r"(?i)(?<![A-Za-z])nder\s+12\b", "Under 12"),
    (r"(?i)(?<![A-Za-z])ver\s+12\b", "Over 12"),
    # "Dilsneriii" — Champion-header "iii" glued onto surname
    (r"([A-Za-z]{3,})iii\b", r"\1"),
    # Recover leading letters eaten by old bare d/st dust strip
    (r"(?i)(?<=: )\bogwood\b", "Dogwood"),
    (r"(?i)(?<=: )\biggerdown\b", "Diggertown"),
    (r"(?i)(?<=: )\bephen\b", "Stephen"),
    (r"(?im)^ACING\s+CHAMPIONS\b", "RACING CHAMPIONS"),
    (r"(?im)^UPPIES\b", "PUPPIES"),
    (r"(?im)^DULTS\b", "ADULTS"),
    # Cut-off leading letter on division / youth / agility / role headers
    (r"(?im)^GILITY\b", "AGILITY"),
    (r"(?im)^OUTH\b", "YOUTH"),
    (r"(?im)^tarters\b", "Starters"),
    (r"(?im)^hild\s+Handler\b", "Child Handler"),
    (r"(?im)^hampion\s*:", "Champion:"),
    (r"(?im)^eserve\s*:", "Reserve:"),
    # Place-body ate leading Y: ``Galterioouth Handler`` → ``Galterio Youth Handler``
    (r"(?i)(?<=[a-z])outh\s+Handler\b", " Youth Handler"),
    (r"(?i)(?<=[a-z])outh\s+Handling\b", " Youth Handling"),

    (r"(?i)\bJUQGES\b", "Judges"),
    (r"(?i)\bJUOCES\b", "Judges"),
    (r"(?i)\bJUDCFS\b", "Judges"),
    (r"(?i)\bJuages\b", "Judges"),
    (r"(?i)\bJuaqes\b", "Judges"),
    (r"(?i)\bJudqes\b", "Judges"),
    # Junior Handler OCR (r↔t): Juniot / Junlor / Juntor
    (r"(?i)\bJuniot\s+Handler\b", "Junior Handler"),
    (r"(?i)\bJunlor\s+Handler\b", "Junior Handler"),
    (r"(?i)\bJuntor\s+Handler\b", "Junior Handler"),
    (r"(?i)\bJuniot\b", "Junior"),
    (r"(?i)\bJunlor\b", "Junior"),
    # Highlighter ate leading letter(s): "ugar"→Sugar, "eggy"→Peggy
    (r"(?i)\bFarmcl\w*['\":;,.]*\s*ugar\b", "Farmcliff Sugar"),
    (r"(?i)(?<![A-Za-z])ugar(?=['\":;,.]*\s*owned)", "Sugar"),
    (r"(?i)\bFarmcl\w*['\":;,.]*\s*eggy\b", "Farmcliff Peggy"),
    (r"(?i)\bameliffi?\s*Peggy\b", "Farmcliff Peggy"),
    (r"(?i)(?<![A-Za-z])eggy(?=['\":;,.]*\s*owned)", "Peggy"),
    (r"(?i)\bFarmcliff\s+Sugars?\b", "Farmcliff Sugar"),
    (r"(?i)\bFarmcliff\s+Peggys?\b", "Farmcliff Peggy"),
    # Glued highlight OCR: FarmcliffSugarowned / Sugarsowned / Peggyssowned
    (r"(?i)F\w{0,3}armel?iff?['\":;,.]*Sugars?['\":;,.]*owned", "Farmcliff Sugar, owned"),
    (r"(?i)F\w{0,3}aneliff['\":;,.]*Sugars?['\":;,.]*owned", "Farmcliff Sugar, owned"),
    (r"(?i)Farmcl\w*['\":;,.]*Sugars?['\":;,.]*owned", "Farmcliff Sugar, owned"),
    (r"(?i)Farmcl\w*['\":;,.]*Peggys?['\":;,.]*owned", "Farmcliff Peggy, owned"),
    (r"(?i)(?<![A-Za-z])Sugars?['\":;,.]*owned", "Sugar, owned"),
    (r"(?i)(?<![A-Za-z])Peggys?['\":;,.]*owned", "Peggy, owned"),
)

# Street-name lexicon: if OCR token is an l/i variant of these, restore.
_STREET_LEXICON = {
    "middle", "mill", "mills", "miller", "millers", "hill", "hills", "hollow",
    "pleasant", "spring", "springs", "willow", "william", "williams", "valley",
    "village", "villa", "lakeville", "beckley", "beckleysville", "brandamore",
    "redmon", "trosper", "benjamin", "beavercreek", "waterford", "succabone",
    "lakeville", "peppertree", "donerail", "moore", "bull", "ballamahack",
    "montano", "paradise", "meadowlark", "hickory", "walnut", "oak", "pine",
    "maple", "cedar", "birch", "elm", "view", "main", "church", "school",
    "market", "center", "central", "college", "station", "industrial",
    "commercial", "residential", "imperial", "colonial", "national",
    "federal", "state", "county", "village", "circle", "crescent",
}


def _title_preserve(sample: str, fixed_lower: str) -> str:
    """Apply casing of sample to corrected lowercase word."""
    if sample.isupper():
        return fixed_lower.upper()
    if sample[:1].isupper():
        return fixed_lower[:1].upper() + fixed_lower[1:]
    return fixed_lower


def _li_variants(word: str) -> set[str]:
    """Generate alternate spellings swapping i↔l (common OCR confusion)."""
    w = word.lower()
    out = {w}
    # single-position swaps of i/l
    for i, ch in enumerate(w):
        if ch == "i":
            out.add(w[:i] + "l" + w[i + 1 :])
        elif ch == "l":
            out.add(w[:i] + "i" + w[i + 1 :])
    # also ii↔il, il↔li, ll↔il common digraphs
    for a, b in (("ii", "il"), ("il", "ii"), ("li", "ll"), ("ll", "li"), ("ie", "le"), ("le", "ie")):
        if a in w:
            out.add(w.replace(a, b, 1))
    return out


# Standalone place-rank tokens where the leading digit was misread as a letter.
# Patterns follow common OCR digit↔glyph swaps (1↔I/l/i, 3↔8/B, 5↔S, 6↔B/G, …).
_PLACE_RANK_OCR = (
    # Leading junk digit glued on (14st / (st → 1st)
    (r"(?i)\b1\dst\b", "1st"),  # 14st, 11st → 1st
    (r"(?i)(?:\(|\b)\d?[ilI|!]st\b", "1st"),
    (r"(?i)\(\s*st\b", "1st"),
    (r"(?i)(?<![0-9a-z])st\s*[:;]", "1st:"),
    # Place dust: lost digit+colon — "st Sady Lady" → "1st: Sady Lady"
    (r"(?im)^(?:\(\s*)?st\s+(?=[A-Z\"'“])", "1st: "),
    (r"(?i)\b(?:ists|lsts|Ists|l sts|I sts)\b", "1sts"),
    (r"(?i)\b(?:ist|lst|Ist|tst|dst)\b(?=\s*[:.;]|\s|$)", "1st"),
    (r"(?i)\b1st\s*;", "1st:"),
    # 2nd — leading digit dropped / read as quote ("'nd:")
    # Require trailing "s" for plural — do NOT use nds? (that turns 'nd → 2nds).
    (r"(?i)[''‘’`´]\s*nds\b", "2nds"),
    (r"(?i)[''‘’`´]\s*nd\b", "2nd"),
    # "'et Eqytale…" — 1st with digit lost (not "pet")
    (r"(?im)^[''‘’`´]\s*et\b\s*", "1st: "),
    (r"(?i)[''‘’`´]\s*et\s*:", "1st:"),
    (r"(?i)(?<![0-9a-z])nd\s*:", "2nd:"),
    (r"(?im)^(?:\(\s*)?nd\s+(?=[A-Z\"'“])", "2nd: "),
    # Leading digit dropped: "rd: Name" → "3rd:" (same family as nd:→2nd:)
    (r"(?i)(?<![0-9a-z])rd\s*:", "3rd:"),
    (r"(?i)(?<![0-9a-z])rd\b(?=\s+[A-Z\"'“])", "3rd"),
    (r"(?im)^(?:\(\s*)?rd\s+(?=[A-Z\"'“])", "3rd: "),
    # Place line never uses plural "2nds:" — undo over-correction
    (r"(?i)\b2nds\s*:", "2nd:"),
    (r"(?i)\b(?:Znds|znds|Qnds|qnds)\b", "2nds"),
    (r"(?i)\b(?:Znd|znd|Qnd|qnd)\b", "2nd"),
    # 2↔9 digit swap: "9nd:" → "2nd:"
    (r"(?i)\b9nds\b", "2nds"),
    (r"(?i)\b9nd\b", "2nd"),
    # "2nd:" misread as "and:" / "dnd:" (line-start only — not "owned by X and Y")
    (r"(?im)^and\s*:", "2nd:"),
    (r"(?im)^ands\s*:", "2nds:"),
    (r"(?im)^dnd\s*:", "2nd:"),
    (r"(?i)\bdnd\s*:", "2nd:"),
    # 3rd (3↔8, B, E; rd↔id)
    (r"(?i)\b(?:8rds|Brds|brds|Erds|ards|Ards)\b", "3rds"),
    (r"(?i)\b(?:8rd|Brd|brd|Erd|ard|Ard)\b", "3rd"),
    (r"(?i)\b3id\b", "3rd"),
    (r"(?i)\b3ids\b", "3rds"),
    # 4th — also 4st (digit kept, suffix mangled as st)
    (r"(?i)\b4st\b", "4th"),
    (r"(?i)\b(?:Aths|aths|Hths)\b", "4ths"),
    (r"(?i)\b(?:Ath|ath|Hth)\b", "4th"),
    # 5th
    (r"(?i)\b5st\b", "5th"),
    (r"(?i)\b(?:Sths|sths)\b", "5ths"),
    (r"(?i)\b(?:Sth|sth)\b", "5th"),
    # Leading 5 dropped: "ith:" (not "with")
    (r"(?im)^ith\s*:", "5th:"),
    (r"(?i)\bith\s*:", "5th:"),
    # 6th — oth/6st common
    (r"(?i)\b6st\b", "6th"),
    (r"(?i)\both\b(?=\s*[:.]|\s|$)", "6th"),
    (r"(?i)\bBths\b", "6ths"),
    (r"(?i)\bBth\b", "6th"),
    (r"\bGths\b", "6ths"),
    (r"\bGth\b", "6th"),
    # 7th
    (r"(?i)\bTths\b", "7ths"),
    (r"(?i)\bTth\b", "7th"),
    # 8th
    (r"(?i)\b&ths\b", "8ths"),
    # 9th
    (r"(?i)\bqths\b", "9ths"),
    (r"(?i)\bqth\b", "9th"),
    (r"\bgths\b", "9ths"),
    (r"\bgth\b", "9th"),
)


def fix_place_rank_ocr(text: str) -> str:
    """Correct misread trial/class place ranks (Sths→5ths, Bths→6ths, …)."""
    if not text:
        return text
    # Leading dust before place: "'1st:" / "é2nd:" / "©3rd:"
    # Use ASCII-only class — Python \w matches é and would miss it.
    text = re.sub(
        r"(?im)^[^A-Za-z0-9]*"
        r"(?=(?:\d*(?:st|nd|rd|th)|best|champion|reserve)\s*:)",
        "",
        text,
    )
    # Next place glued onto previous surname: "Kesickoth: Michelle" / "Berkebileoth: — Crystal"
    # (leading digit of 5th dropped → "oth:"/"ith:"; not a real surname before ":")
    text = re.sub(
        r"(?i)([A-Za-z])(?:5\s*th|oth|ith)\s*:\s*[_\-–—−]*\s*(?=[A-Z\"'])",
        r"\1\n5th: ",
        text,
    )
    # "4th: ith: Name" — 5th mangled after prior place (4th dog often lost in OCR)
    text = re.sub(
        r"(?i)\b\d+(?:st|nd|rd|th)\s*:\s*(?:ith|oth)\s*:\s*",
        "5th: ",
        text,
    )
    # "5th: th. Name" / "4th: th Name" — leftover ordinal dust (dup_place)
    text = re.sub(
        r"(?i)\b((?:\d+(?:st|nd|rd|th)|best|champion|reserve)\s*:)\s*"
        r"(?:th|nd|rd|st)\s*[.:]?\s+",
        r"\1 ",
        text,
    )
    for pat, repl in _PLACE_RANK_OCR:
        text = re.sub(pat, repl, text)
    # Scanner/rule dust between place and dog name:
    # "6th: — Name" / "1st: ! Farmstead" / fullwidth ！ / ¡
    text = re.sub(
        r"(?i)\b((?:\d+(?:st|nd|rd|th)|best|champion|reserve)\s*:)\s*"
        r"(?:[_\-–—−+!.¡！'\"`]+(?:\s*[_\-–—−+!.¡！'\"`]*)*)\s*",
        r"\1 ",
        text,
    )
    # Pipe/broken-bar after place (OCR reads leading I as | ¦ ǀ etc.):
    #   "| Am Prancer" / "¦Am Prancer" → "I Am …"
    #   "| Foxwarren" / "|mpressive" → strip pipe or I+letter (not a free leading I)
    _PIPE = r"[|¦ǀӀІ丨]"
    text = re.sub(
        rf"(?i)\b((?:\d+(?:st|nd|rd|th)|best|champion|reserve)\s*:)\s*{_PIPE}\s*Am\b",
        r"\1 I Am",
        text,
    )
    text = re.sub(
        rf"(?i)\b((?:\d+(?:st|nd|rd|th)|best|champion|reserve)\s*:)\s*{_PIPE}\s+(?=[A-Za-z\"'])",
        r"\1 ",
        text,
    )
    text = re.sub(
        rf"(?i)\b((?:\d+(?:st|nd|rd|th)|best|champion|reserve)\s*:)\s*{_PIPE}([a-z])",
        r"\1 I\2",
        text,
    )
    text = re.sub(
        rf"(?i)\b((?:\d+(?:st|nd|rd|th)|best|champion|reserve)\s*:)\s*{_PIPE}([A-Z])",
        r"\1 \2",
        text,
    )
    # Spurious leading "I " before a real dog/kennel name (over-corrected pipe dust)
    text = re.sub(
        r"(?i)\b((?:\d+(?:st|nd|rd|th)|best|champion|reserve)\s*:)\s+I\s+"
        r"(?!Am\b)(?=[A-Z][a-z]{2,})",
        r"\1 ",
        text,
    )
    # "4th: 3 ey             4th: Rootie" / "1st: fn,             1st Name"
    # junk then repeated place (2nd place often missing colon); keep last place
    text = re.sub(
        r"(?im)^(?:\d+(?:st|nd|rd|th)\s*:)\s*.{0,40}?\s{2,}"
        r"(?=(\d+(?:st|nd|rd|th)\s*:?\s))",
        "",
        text,
    )
    # Same with only one space before the repeated place: "1st: fn, 1st Name"
    text = re.sub(
        r"(?im)^(?:\d+(?:st|nd|rd|th)\s*:)\s+[A-Za-z]{1,4}[.,]?\s+"
        r"(?=(\d+(?:st|nd|rd|th)\s*:?\s))",
        "",
        text,
    )
    # "2nd: ond: Name" / "3rd: did: Name" / "3rd: rd: Name" — mangled place echo
    text = re.sub(
        r"(?i)\b((?:\d+(?:st|nd|rd|th)|best|champion|reserve)\s*:)\s*"
        r"(?:ond|did|rd|st|th|nd|nnd|prd|ith)\s*:\s*",
        r"\1 ",
        text,
    )
    # "2nd: F-            ond: Name" — junk fragment then place-echo (1997 Vol I)
    text = re.sub(
        r"(?i)\b((?:\d+(?:st|nd|rd|th)|best|champion|reserve)\s*:)\s*"
        r"[A-Za-z0-9]{1,6}[\-–—.]?\s{2,}"
        r"(?:ond|did|rd|st|th|nd|nnd|prd|ith)\s*:\s*",
        r"\1 ",
        text,
    )
    # "2nd: ;         ond: Name" / "2nd: :          ond:" / "2nd: ]        ond:"
    # punct/symbol dust between place and place-echo (1999–2001)
    text = re.sub(
        r"(?i)\b((?:\d+(?:st|nd|rd|th)|best|champion|reserve)\s*:)\s*"
        r"[^\w\n]{1,8}\s*"
        r"(?:ond|did|rd|st|th|nd|nnd|prd|ith)\s*:\s*",
        r"\1 ",
        text,
    )
    # Bare "ond: Name" (lost leading "2") — line-start or mid-line after non-letters
    text = re.sub(r"(?i)(?<![A-Za-z])ond\s*:\s*", "2nd: ", text)
    # "{st Name" / "{nd Name" after place (brace OCR of 1/2)
    text = re.sub(
        r"(?i)\b((?:\d+(?:st|nd|rd|th)|best|champion|reserve)\s*:)\s*"
        r"\{?\s*(?:st|nd|rd|th)\s+",
        r"\1 ",
        text,
    )
    # Leading single-letter dust: "1st: t Name" / "2nd: in   ond: Name" (in→strip)
    text = re.sub(
        r"(?i)\b((?:\d+(?:st|nd|rd|th)|best|champion|reserve)\s*:)\s+"
        r"(?:[a-z]{1,3})\s{2,}(?=(?:ond\s*:|[A-Z\"'“]|\{))",
        r"\1 ",
        text,
    )
    text = re.sub(
        r"(?i)\b((?:\d+(?:st|nd|rd|th)|best|champion|reserve)\s*:)\s+"
        r"t\s+(?=[A-Z\"'“])",
        r"\1 ",
        text,
    )
    # Re-run place-echo after stripping "in   ond:" gaps
    text = re.sub(
        r"(?i)\b((?:\d+(?:st|nd|rd|th)|best|champion|reserve)\s*:)\s*"
        r"(?:ond|did|rd|st|th|nd|nnd|prd|ith)\s*:\s*",
        r"\1 ",
        text,
    )
    # Line junk before place: "I.              1st: Chris"
    text = re.sub(
        r"(?im)^[A-Za-z]\.?\s{2,}(?=\d+(?:st|nd|rd|th)\s*:)",
        "",
        text,
    )
    # Missing colon: "1st Foxton" / "2nd Diana" (place + Capital name)
    text = re.sub(
        r"(?im)^(\d+(?:st|nd|rd|th))\s+(?=[A-Z\"'“])",
        r"\1: ",
        text,
    )
    # Semicolon after place rank (OCR colon→semicolon)
    text = re.sub(
        r"(?i)\b((?:\d*(?:st|nd|rd|th)|best|champion|reserve))\s*;",
        r"\1:",
        text,
    )
    # "Champion: Babe, owned by Reserve: Pepper, owned by …" — role glued after owned-by
    text = re.sub(
        r"(?i),\s*owned\s+by\s+(?=(?:reserve|champion|best)\s*:)",
        "\n",
        text,
    )
    # Multi-place smash after an owned-by: "…owned by X 4th: Y" / "… Cilliers i 3rd: Y"
    # (gated on owned-by so normal "10-12 1/2\" Champion:" stays one line)
    text = re.sub(
        r"(?i)(owned\s+by\b[^\n]{1,90}?)\s+"
        r"(?=(\d+(?:st|nd|rd|th)|best|champion|reserve)\s*:)",
        r"\1\n",
        text,
    )
    # Doubled place ranks: "2nd: 3rd: Name" → keep the last place
    # Require digits (\d+) — bare "th" must not eat "Three"/"Tablemate".
    text = re.sub(
        r"(?i)(?:\b\d+(?:st|nd|rd|th)\s*:\s*)+(?=\d+(?:st|nd|rd|th)\s*:)",
        "",
        text,
    )
    # Repeated place after colon: "1st: 1st. Name" / "4th: 4th.Westwood"
    # Also rank dust without punct: "1st: 4th Blackland" / "2nd: 3rd Name"
    text = re.sub(
        r"(?i)\b((?:\d+(?:st|nd|rd|th)|best|champion|reserve)\s*:)\s*"
        r"(?:\d+(?:st|nd|rd|th)|best|champion|reserve)\s*[.:。．]?\s*",
        r"\1 ",
        text,
    )
    # Second pass: stray ordinal glued before the dog name (no trailing punct)
    text = re.sub(
        r"(?i)\b((?:\d+(?:st|nd|rd|th)|best|champion|reserve)\s*:)\s+"
        r"\d+(?:st|nd|rd|th)\s+(?=[A-Z\"'“])",
        r"\1 ",
        text,
    )
    return _repair_orphan_owned_by_places(_repair_first_place_ocr(text))


def _place_ordinal(n: int) -> str:
    suf = {1: "st", 2: "nd", 3: "rd"}.get(n, "th")
    return f"{n}{suf}"


def _is_results_section_header(s: str) -> bool:
    s = s.strip()
    if not s or _MARKER_RE.match(s):
        return True
    if re.match(
        r"(?i)^(?:championship\s+certificate|child\s+handler|junior\s+handler|"
        r"dog\s+pups|bitch\s+pups|dogs,|bitches,|novice|open\s|pre-novice|"
        r"steeplechase|working\s+terrier|go-?to-?ground|family\s+class|"
        r"pair\s+class|veteran|bred\s+by|youth\s|agility|racing|puppy\s+champion|"
        r"best\s+\d|adults?\b)",
        s,
    ):
        return True
    if re.search(r"(?i)\bentries\s*:", s) and not re.match(
        r"(?i)^(?:\d*(?:st|nd|rd|th)|champion|reserve|best)\s*:", s
    ):
        return True
    return False


def _repair_orphan_owned_by_places(text: str) -> str:
    """Assign missing place ranks to ``Name, owned by…`` lines that lost ``1st:``/``2nd:``."""
    if not text:
        return text
    place_re = re.compile(r"(?i)^(\d+)(?:st|nd|rd|th)\s*:")
    lines = text.splitlines()
    out: list[str] = []
    i = 0
    n = len(lines)
    while i < n:
        ln = lines[i]
        if _is_results_section_header(ln):
            out.append(ln)
            i += 1
            continue
        # Gather a contiguous place/orphan block
        block: list[str] = []
        while i < n and not _is_results_section_header(lines[i]):
            block.append(lines[i])
            i += 1
        placed: dict[int, str] = {}
        orphans: list[str] = []
        other: list[str] = []
        for bl in block:
            m = place_re.match(bl.strip())
            if m:
                num = int(m.group(1))
                if 1 <= num <= 9 and num not in placed:
                    placed[num] = bl
                else:
                    other.append(bl)
            elif re.search(r"(?i)\bowned\s+by\b", bl) and not re.match(
                r"(?i)^(?:champion|reserve|best)\s*:", bl.strip()
            ):
                orphans.append(bl)
            else:
                other.append(bl)
        if orphans and placed:
            missing = [p for p in range(1, 7) if p not in placed]
            for orphan, pnum in zip(orphans, missing):
                body = re.sub(r"(?i)^(?:\d*(?:st|nd|rd|th)\s*:)\s*", "", orphan).strip()
                placed[pnum] = f"{_place_ordinal(pnum)}: {body}"
            orphans = orphans[len(missing) :]  # unused leftovers
            rebuilt = [placed[p] for p in sorted(placed)]
            rebuilt.extend(orphans)
            rebuilt.extend(other)
            out.extend(rebuilt)
        else:
            out.extend(block)
    return "\n".join(out)


def _repair_first_place_ocr(text: str) -> str:
    """Fix systematic Tesseract ``1st``→``4th`` confusion using place order.

    Yearbooks list places in order. A ``4th:`` line immediately followed (next
    place line) by ``2nd:`` is almost always a misread ``1st:`` — not a dog-name
    hardcode.
    """
    if not text:
        return text
    place_re = re.compile(r"(?i)^(\(?\s*)(\d+)(st|nd|rd|th)(\s*:)")
    lines = text.splitlines()
    out = list(lines)

    def place_num(s: str) -> int | None:
        m = place_re.match(s.strip())
        return int(m.group(2)) if m else None

    for i, ln in enumerate(out):
        if place_num(ln) != 4:
            continue
        for j in range(i + 1, min(i + 8, len(out))):
            s = out[j].strip()
            if not s or _MARKER_RE.match(s):
                continue
            pj = place_num(s)
            if pj is None:
                # Stop at class / division headers so we don't pair across classes
                if re.match(
                    r"(?i)^(?:dog|bitch|dogs|bitches|novice|open|pre-|puppy|adult|"
                    r"championship|champion|reserve|steeple|working|go-?to|"
                    r"conformation|racing|family|bred|youth|entries)\b",
                    s,
                ):
                    break
                continue
            if pj == 2:
                out[i] = place_re.sub(r"\g<1>1st\g<4>", ln, count=1)
            break
    return _repair_skipped_place_ocr("\n".join(out))


def _repair_skipped_place_ocr(text: str) -> str:
    """Fix ``5th``→``6th`` when place order skips (``4th`` then ``6th``, no ``5th``).

    Keeps a later second ``6th`` (ties / Junior Handler) intact.
    """
    if not text:
        return text
    place_re = re.compile(r"(?i)^(\(?\s*)(\d+)(st|nd|rd|th)(\s*:)")
    lines = text.splitlines()
    out = list(lines)
    i = 0
    n = len(out)
    while i < n:
        if _is_results_section_header(out[i]):
            i += 1
            continue
        block_idx: list[int] = []
        while i < n and not _is_results_section_header(out[i]):
            block_idx.append(i)
            i += 1
        nums: dict[int, list[int]] = {}
        for bi in block_idx:
            m = place_re.match(out[bi].strip())
            if not m:
                continue
            num = int(m.group(2))
            if 1 <= num <= 9:
                nums.setdefault(num, []).append(bi)
        # 4 present, 5 missing, ≥1 sixth → first 6th was almost always 5th
        if 4 in nums and 5 not in nums and 6 in nums:
            bi = nums[6][0]
            out[bi] = place_re.sub(r"\g<1>5th\g<4>", out[bi], count=1)
    return "\n".join(out)


def normalize_ocr_apostrophes(text: str) -> str:
    """Map curly/typographic quotes to ASCII so Maven's isn't split into 's Name'."""
    if not text:
        return text
    return (
        text.replace("\u2019", "'")  # right single quotation mark
        .replace("\u2018", "'")  # left single quotation mark
        .replace("\u2032", "'")  # prime
        .replace("\u00B4", "'")  # acute
        .replace("`", "'")
        .replace("\u201C", '"')
        .replace("\u201D", '"')
    )


def fix_ocr_li_confusion(text: str) -> str:
    """Correct l↔i OCR swaps in tokens (addresses, cities, roles, names)."""
    if not text:
        return text
    text = normalize_ocr_apostrophes(text)
    text = fix_place_rank_ocr(text)
    text = normalize_height_class_ocr(text)
    text = normalize_coat_ocr(text)
    text = normalize_agility_level_ocr(text)
    text = normalize_cert_entries_glue(text)
    text = _normalize_owned_by_ocr(text)
    # "O'Toole,owned by" missing space after comma
    text = re.sub(r",(owned\s+by\b)", r", \1", text, flags=re.IGNORECASE)
    # "Ringlet,t, owned by" / "Name,x, owned" — gutter letter between commas
    text = re.sub(
        r",\s*[A-Za-z]\s*,\s*(?=owned\s+by\b)",
        ", ",
        text,
        flags=re.IGNORECASE,
    )
    # Missing comma before owned by: "Kid owned by" → "Kid, owned by"
    text = re.sub(r"(?i)([^\s,])\s+owned\s+by\b", r"\1, owned by", text)
    # "Entriess 5" / "Entries 5" / "Entriess:" → "Entries: 5"
    text = re.sub(r"(?i)\bEntriess?\s*:?\s*(\d+)\b", r"Entries: \1", text)
    text = re.sub(r"(?i)\bEntriess\b", "Entries", text)
    text = re.sub(r"(?i)\bEntricer\s*:?\s*(\d+)\b", r"Entries: \1", text)
    text = re.sub(r"(?i)\bEntricer\b", "Entries", text)
    # "Crntrine: OO" / "Entrine:" — Helvetica Entries mangling on handler headers
    text = re.sub(r"(?i)\bCrntrines?\b", "Entries", text)
    text = re.sub(r"(?i)\bEntrines?\b", "Entries", text)
    text = re.sub(r"(?i)\bEntries\s*:\s*[Oo0]{1,2}\b", "Entries:", text)
    text = re.sub(r"(?i)\bFan+m?[il1]lv\s+Class\b", "Family Class", text)

    # Bare "Entries" / "Entries:" tidy
    text = re.sub(r"(?im)\bEntries\s*$", "Entries:", text)
    # Trailing space before comma: "Ravenswood Lady ,"
    text = re.sub(r"([A-Za-z0-9.'])\s+,", r"\1,", text)
    # "Hunter., owned" / doubled punct before comma
    text = re.sub(r"([A-Za-z])\.,", r"\1,", text)
    # "Reserve:Foxwarren" missing space after role colon
    text = re.sub(
        r"(?i)\b((?:champion|reserve|best)\s*:)(?=[A-Za-z\"'])",
        r"\1 ",
        text,
    )
    # Name hardcodes: residual only (OCR reconcile already ran at page OCR time)
    for pat, repl in _OCR_NAME_PHRASES:
        text = re.sub(pat, repl, text)
    # After Novicé→Novice: strip "Novice Puppies - "" junk before Entries
    text = re.sub(r"(?i)\b(Novice\s+Puppies)\s*[-–—]\s*[\"“”']?\s*", r"\1 ", text)
    # Class-header currency/glyph dust: "Novice Puppies ¥    Entries:"
    text = re.sub(
        r"(?i)\b((?:Novice|Open|Puppy|Adults?|Working|Veteran|Senior)\s+[A-Za-z][A-Za-z'/\-]*)"
        r"\s*[¥£€¢§†‡¶•¤°]\s*(?=Entries\b)",
        r"\1 ",
        text,
    )
    # Height role abbreviation: `12 1/2-15" Champ:` → `… Champion:`
    text = re.sub(r'(?i)(")\s*Champ\s*:', r'\1 Champion:', text)
    text = re.sub(r"(?i)\bChamp\s*:(?=\s)", "Champion:", text)
    # "iii            Champion:" / place dust "st!" / "d:" / "fh:" before name
    # Require "st!" or a dust token WITH colon — bare "d"/"st" ate Dogwood/Stephen.
    text = re.sub(
        r"(?im)^(?:iii|ii|i)\s{2,}(?=(?:Champion|Reserve)\s*:)",
        "",
        text,
    )
    text = re.sub(
        r"(?i)\b((?:\d+(?:st|nd|rd|th)|best|champion|reserve)\s*:)\s*"
        r"(?:st!\s*|(?:sth?|d|fh|nd|rd)\s*:)\s*[_\-–—−]*\s*",
        r"\1 ",
        text,
    )
    # Place line that is actually a height champion/reserve row:
    #   "5th: nder 12…" / "4th: 10-12 1/2\" Champion:" / "5th: 10-12 12\" Reserve:"
    text = re.sub(
        r"(?im)^\d+(?:st|nd|rd|th)\s*:\s*(?="
        r"(?:Under|Over|nder|ver)\s+\d|"
        r"\d{1,2}[\d\s./\"'%-]{0,24}(?:Champion|Reserve|Champ)\s*:)",
        "",
        text,
    )
    # Multiword OCR splits first
    text = re.sub(r"(?i)\bPhi\s+lhower\b", "Philhower", text)
    text = re.sub(r"(?i)\bMai\s+vern\b", "Malvern", text)
    text = re.sub(r"(?i)\bP\.?\s*0\.?\s*Box\b", "P.O. Box", text)

    def repl_token(m: re.Match) -> str:
        tok = m.group(0)
        low = tok.lower()
        if low in _OCR_LI_FIXES:
            fixed = _OCR_LI_FIXES[low]
            if fixed != low:
                return _title_preserve(tok, fixed)
        # Before street suffixes, prefer lexicon match via i/l variants
        # (handled in pair pass below) — still try lexicon here
        if len(low) >= 4:
            for variant in _li_variants(low):
                if variant in _STREET_LEXICON and variant != low:
                    return _title_preserve(tok, variant)
                if variant in _OCR_LI_FIXES and _OCR_LI_FIXES[variant] != low:
                    return _title_preserve(tok, _OCR_LI_FIXES[variant])
        return tok

    text = re.sub(r"[A-Za-z][A-Za-z'\-]*", repl_token, text)

    # Explicit high-confidence address phrases
    phrase_fixes = (
        (r"(?i)\bMiddie\s+Street\b", "Middle Street"),
        (r"(?i)\bFar\s+Hillis\b", "Far Hills"),
        (r"(?i)\bMt\.?\s+Pleasant\b", "Mt. Pleasant"),
        (r"(?i)\bBeckieysville\b", "Beckleysville"),
        (r"(?i)\bMiilers\b", "Millers"),
    )
    for pat, repl in phrase_fixes:
        text = re.sub(pat, repl, text)
    # After name phrases so Cowasjee / Go-to-Ground repairs apply first
    text = normalize_judges_line_ocr(text)
    return text


def _levenshtein(a: str, b: str) -> int:
    if a == b:
        return 0
    if not a:
        return len(b)
    if not b:
        return len(a)
    prev = list(range(len(b) + 1))
    for i, ca in enumerate(a, 1):
        cur = [i]
        for j, cb in enumerate(b, 1):
            cur.append(min(cur[j - 1] + 1, prev[j] + 1, prev[j - 1] + (ca != cb)))
        prev = cur
    return prev[-1]


def _normalize_owned_by_ocr(text: str) -> str:
    """Fix near-miss OCR of ``owned by`` (owend/owncd/…), not only a fixed list."""
    if not text:
        return text

    def repl(m: re.Match) -> str:
        word = m.group(1)
        low = word.lower()
        if low in ("owned", "bred"):
            return m.group(0)
        if low in ("hy", "ny", "dowend", "owend", "owncd", "owmed", "ovned"):
            return "owned by"
        if low == "hy" or (len(low) <= 6 and _levenshtein(low, "owned") <= 2):
            return "owned by"
        if len(low) <= 7 and _levenshtein(low, "owned") <= 3 and low.endswith("ed"):
            return "owned by"
        return m.group(0)

    # Explicit near-misses before generic levenshtein
    text = re.sub(r"(?i)\bdowend\s+by\b", "owned by", text)
    text = re.sub(r"(?i)\bowned\s+(?:hy|ny)\b", "owned by", text)
    # "owned byJamie" (missing space after by) — before missing-by insert
    text = re.sub(r"(?i)\bowned\s+by([A-Za-z])", r"owned by \1", text)
    # "owned Butch Harris" (missing by) — capital owner token; never tokens
    # that start with ``by`` (``byJamie`` is handled by the space-insert above).
    text = re.sub(
        r"(?i)\bowned\s+(?!by)([A-Z][A-Za-z.'\-]+)",
        r"owned by \1",
        text,
    )
    # "owend by" / "owncd by" / "owned hy"
    text = re.sub(r"(?i)\b([A-Za-z]{3,8})\s+by\b", repl, text)
    # Trailing crumb: "owned by Will Hahn by" (not "… by Trial Chairperson")
    text = re.sub(
        r"(?im)(\bowned\s+by\b[^\n]{2,90}?)\s+by\s*$",
        r"\1",
        text,
    )
    # Trailing 1–2 lowercase dust: "owned by Debra Ellis i" / "… Reifel ed"
    # (middle initials are uppercase / dotted; Jr/Sr kept)
    text = re.sub(
        r"(?im)(\bowned\s+by\b[^\n]{2,80}?[A-Za-z.]{2,})\s+(?!jr\b|sr\b)[a-z]{1,2}\s*$",
        r"\1",
        text,
    )
    # Co-owner joiner OCR: "Whittaker! E." / "Whittaker` E." → "&"
    # (require Initial. after so O'Brien / possessive stay intact)
    text = re.sub(
        r"(?i)(owned\s+by\b[^\n]{0,100}?[A-Za-z.])\s*[!`´]\s+(?=[A-Z]\.)",
        r"\1 & ",
        text,
    )
    # After backtick→apostrophe fold: "Whittaker' E. Boehme" (space optional before ')
    text = re.sub(
        r"(?i)(owned\s+by\b[^\n]{0,100}?[A-Za-z.])\s*'\s+(?=[A-Z]\.)",
        r"\1 & ",
        text,
    )
    return text



_PLACE_NON_FIRST_RE = re.compile(r"(?i)^(?:\d+)?(?:nd|rd|th)\s*:")
# Accept Ist:/lst: — Helvetica often reads leading ``1`` as ``I``/``l``.
_PLACE_FIRST_RE = re.compile(r"(?i)^(?:1|l|I)st\s*:")
_CHAMP_RESERVE_ROLE_RE = re.compile(r"(?i)^(?:champion|reserve)\s*:")
_COLUMN_MARK_RE = re.compile(r"(?i)^---\s*column\s+(?:LEFT|RIGHT)\s*---$")
_SECTIONISH_RE = re.compile(
    r"(?i)entries\s*:|division\b|champion\s*&\s*reserve|"
    r"\bbest\b.+(?:bitch|dog|puppy)|"
    r"\b(?:novice|open|advanced|bred by|puppies|adults|veteran)\b|"
    r"missing class header|"
    r"\b(?:smooth|rough|broken)\b|"
    r"\b(?:bitches|dogs)\b|"
    r"family\s+class|brace\b|stud\s+dog|brood\s+bitch|"
    r"\b(?:youth|junior|child|pee\s*wee)\b.*\bhandler\b|"
    r"\bhandler\s+class\b|\bshowmanship\b|"
    r"\b(?:on|off)\s+lead\b|"
    r"\bsteeplechase\b|\bracing\s+champions?\b|\bflat\s+races?\b|"
    r"\bgo-?to-?ground\b|\bagility\b|"
    r"\bsuitability\b|\bspayed\b|\bneutered\b|"
    r"\d+\s*(?:up to|/|-)\s*\d+"
)
_CLASS_HEADER_HINT_RE = re.compile(
    r"(?i)entries\s*:|"
    r"\b(?:novice|open|advanced|bred by|puppies|adults?|veteran)\b|"
    r"\b(?:smooth|rough|broken)\b|"
    r"\b(?:bitches|dogs)\b|"
    r"\bbest\b.+(?:bitch|dog|puppy)|"
    r"champion\s*&\s*reserve|"
    r"family\s+class|brace\b|stud\s+dog|brood\s+bitch|"
    r"\b(?:youth|junior|child|pee\s*wee)\s+handler\b|"
    r"\bhandler\b|\bshowmanship\b|"
    r"\b(?:on|off)\s+lead\b|"
    r"\bsteeplechase\b|\bracing\s+champions?\b|\bflat\s+races?\b|"
    r"\bgo-?to-?ground\b|\bagility\b|"
    r"\bsuitability\b|\bspayed\b|\bneutered\b|"
    r"\d+\s*(?:up to|/|-)\s*\d+|"
    r"yr\s*&?\s*older|months?\b"
)


def _looks_like_class_header_line(s: str) -> bool:
    """True when a short line looks like a recovered class/section title."""
    t = norm_space(s or "")
    if not t or len(t) > 120:
        return False
    if _PLACE_FIRST_RE.match(t) or _PLACE_NON_FIRST_RE.match(t):
        return False
    if re.search(r"(?i)\bowned\s+by\b", t):
        return False
    if re.search(r"(?i)^(?:champion|reserve|best)\s*:", t):
        return False
    if t.lower().startswith("[missing class header]"):
        return False
    return bool(_CLASS_HEADER_HINT_RE.search(t))


def _iter_class_header_gap_indices(lines: list[str]) -> list[int]:
    """Indices of ``1st:`` lines that restart a class with no header above.

    Arms on non-first places and on Champion/Reserve role lines (common before
    Youth/Pee Wee handler blocks under BEST … CHAMPION & RESERVE).
    Column LEFT/RIGHT markers reset the arm — a new column is not a class gap.
    """
    gaps: list[int] = []
    gap_armed = False
    for i, line in enumerate(lines):
        s = line.strip()
        if not s:
            continue
        if _COLUMN_MARK_RE.match(s):
            gap_armed = False
            continue
        if _PLACE_FIRST_RE.match(s):
            if gap_armed:
                gaps.append(i)
            gap_armed = False
        elif _PLACE_NON_FIRST_RE.match(s) or _CHAMP_RESERVE_ROLE_RE.match(s):
            gap_armed = True
        elif _SECTIONISH_RE.search(s) or _looks_like_class_header_line(s):
            gap_armed = False
    return gaps


def _line_fingerprint_keys(s: str) -> set[str]:
    """Alphanumeric stems ≥4 chars for matching OCR lines across passes."""
    return {m.group(0).lower() for m in re.finditer(r"[A-Za-z]{4,}", s or "")}


def _inject_peer_class_headers(primary: str, candidates: list[str]) -> str:
    """Insert short class-header lines that peer ensemble passes already saw.

    Primary scoring often discards sparse header-only lines; pull them back
    when a place-rank gap aligns with a peer that kept the title.
    """
    if not primary or not candidates:
        return primary
    lines = primary.splitlines()
    gaps = _iter_class_header_gap_indices(lines)
    if not gaps:
        return primary
    others = [c for c in candidates if c and c != primary]
    if not others:
        return primary

    def _prev_place_line(idx: int) -> str:
        for j in range(idx - 1, -1, -1):
            s = lines[j].strip()
            if (
                _PLACE_NON_FIRST_RE.match(s)
                or _PLACE_FIRST_RE.match(s)
                or _CHAMP_RESERVE_ROLE_RE.match(s)
            ):
                return s
        return ""

    def _prior_header_above(idx: int) -> str:
        for j in range(idx - 1, -1, -1):
            s = lines[j].strip()
            if _looks_like_class_header_line(s) or _SECTIONISH_RE.search(s):
                return norm_space(s).lower()
            if _PLACE_FIRST_RE.match(s) or _PLACE_NON_FIRST_RE.match(s):
                # Keep scanning above this class block for its title.
                continue
        return ""

    def _best_place_match(alines: list[str], keys: set[str]) -> int | None:
        if len(keys) < 2:
            return None
        best_i, best_ov = None, 0
        for i, aln in enumerate(alines):
            if not (
                _PLACE_FIRST_RE.match(aln)
                or _PLACE_NON_FIRST_RE.match(aln)
                or _CHAMP_RESERVE_ROLE_RE.match(aln)
            ):
                continue
            ov = len(keys & _line_fingerprint_keys(aln))
            if ov > best_ov:
                best_ov, best_i = ov, i
        return best_i if best_i is not None and best_ov >= 2 else None

    inserts: dict[int, str] = {}
    for gi in gaps:
        nxt = lines[gi].strip()
        prev = _prev_place_line(gi)
        prev_keys = _line_fingerprint_keys(prev)
        next_keys = _line_fingerprint_keys(nxt)
        prior_hdr = _prior_header_above(gi)
        best_hdr = ""
        best_sc = -1
        for alt in others:
            alines = [ln.strip() for ln in alt.splitlines() if ln.strip()]
            ip = _best_place_match(alines, prev_keys)
            inn = _best_place_match(alines, next_keys)
            if ip is None or inn is None or inn <= ip:
                continue
            # Only headers strictly between the matched place lines.
            for i in range(ip + 1, inn):
                aln = alines[i]
                if not _looks_like_class_header_line(aln):
                    continue
                if prior_hdr and norm_space(aln).lower() == prior_hdr:
                    continue  # don't re-insert the previous class title
                sc = (
                    (inn - ip)
                    + (8 if re.search(r"(?i)entries\s*:", aln) else 0)
                    + (6 if re.search(r"(?i)\bhandler\b", aln) else 0)
                    + min(20, len(aln) // 4)
                )
                if sc > best_sc:
                    best_sc, best_hdr = sc, aln
        if best_hdr and best_sc >= 4:
            inserts[gi] = best_hdr

    if not inserts:
        return primary
    out: list[str] = []
    for i, ln in enumerate(lines):
        if i in inserts:
            out.append(inserts[i])
        out.append(ln)
    return "\n".join(out)


def _ocr_column_line_boxes(
    img: Image.Image, conf_min: float = 20.0
) -> list[tuple[str, int, int]]:
    """Single-column ``image_to_data`` lines as ``(text, y0, y1)`` top→bottom."""
    import pytesseract

    with _tess_slots:
        try:
            data = pytesseract.image_to_data(
                img,
                config=_tesseract_cfg(4, _OCR_LANG),
                output_type=pytesseract.Output.DICT,
            )
        except Exception:
            data = pytesseract.image_to_data(
                img,
                config=_tesseract_cfg(4, "eng"),
                output_type=pytesseract.Output.DICT,
            )
    n = len(data["text"])
    words: list[dict] = []
    for i in range(n):
        txt = (data["text"][i] or "").strip()
        try:
            conf = float(data["conf"][i])
        except Exception:
            conf = -1.0
        if not txt or conf < conf_min:
            continue
        x, y, w, h = data["left"][i], data["top"][i], data["width"][i], data["height"][i]
        words.append(
            {"t": txt, "x": x, "y": y, "w": w, "h": h, "cy": y + h / 2.0}
        )
    if len(words) < 4:
        return []
    words.sort(key=lambda z: (z["cy"], z["x"]))
    lines_w: list[list[dict]] = []
    for w in words:
        if not lines_w:
            lines_w.append([w])
            continue
        prev = lines_w[-1][-1]
        if abs(w["cy"] - prev["cy"]) <= max(12, 0.65 * max(w["h"], prev["h"])):
            lines_w[-1].append(w)
        else:
            lines_w.append([w])
    out: list[tuple[str, int, int]] = []
    for line in lines_w:
        line.sort(key=lambda z: z["x"])
        text = " ".join(z["t"] for z in line)
        y0 = min(z["y"] for z in line)
        y1 = max(z["y"] + z["h"] for z in line)
        out.append((text, y0, y1))
    return out


def _match_text_line_to_box(
    text_line: str, boxes: list[tuple[str, int, int]], used: set[int]
) -> int | None:
    """Best unused box index matching a finalized text line, or None."""
    keys = _line_fingerprint_keys(text_line)
    if len(keys) < 2 and not re.search(r"(?i)^\d*(?:st|nd|rd|th)\s*:", text_line):
        return None
    best_i, best_ov = None, 0
    for i, (bt, _y0, _y1) in enumerate(boxes):
        if i in used:
            continue
        bkeys = _line_fingerprint_keys(bt)
        ov = len(keys & bkeys)
        # Place-rank cue boost when stems are thin
        if re.search(r"(?i)^\d*(?:st|nd|rd|th)\s*:", text_line) and re.search(
            r"(?i)^\d*(?:st|nd|rd|th)\s*:", bt
        ):
            ov += 1
        if ov > best_ov:
            best_ov, best_i = ov, i
    if best_i is None:
        return None
    need = 2 if len(keys) >= 3 else 1
    return best_i if best_ov >= need else None


_CLASS_HEADER_SPAN_WITH_ENTRIES_RE = re.compile(
    r"(?i)\b("
    r"(?:dogs|bitches|pups|puppies|adults?|veterans?|novice|open|advanced|"
    r"starters(?:\s+agility)?|agility(?:\s+[ivx1-3]+)?|"
    r"bred\s+by(?:\s+exhibitor)?|suitability|spayed|neutered|"
    r"(?:youth|junior|child|pee\s*wee)\s+handler)"
    r"\b[^|\n]{0,110}?"
    r"entries\s*:\s*\d+"
    r")"
)
_CLASS_HEADER_SPAN_RE = re.compile(
    r"(?i)\b("
    r"(?:dogs|bitches|pups|puppies|adults?|veterans?|novice|open|advanced|"
    r"starters(?:\s+agility)?|agility(?:\s+[ivx1-3]+)?|"
    r"bred\s+by(?:\s+exhibitor)?|suitability|spayed|neutered|"
    r"(?:youth|junior|child|pee\s*wee)\s+handler)"
    r"\b[^|\n]{0,90}"
    r")"
)
# Right-column agility title swallowed into the following ``1st:`` box.
_AGILITY_TITLE_BEFORE_PLACE_RE = re.compile(
    r"(?i)\b("
    r"(?:Novice|Open|Advanced)(?:\s*,?\s*(?:On|Off)\s+Lead)?|"
    r"Starters\s+Agility(?:\s*,?\s*(?:On|Off)\s+Lead)?|"
    r"Agility\s+(?:I{1,3}|[123]|IV)\s*,?\s*(?:On|Off)\s+Lead"
    r")\b[^|\n]{0,40}?"
    r"(?=\s*(?:['\"`´]?\s*)?(?:\d+|l|I)?(?:st|nd|rd|th)\s*:)"
)
_AGILITY_LEVEL_TITLE_RE = re.compile(
    r"(?i)^(?:Novice|Open|Advanced)\b|Starters\s+Agility\b|"
    r"Agility\s+(?:I{1,3}|[123]|IV)\b"
)


def _extract_class_header_span(s: str) -> str:
    """Pull a class-title span out of a noisy interstitial OCR string."""
    flat = norm_space(fix_ocr_li_confusion(s or ""))
    flat = re.sub(r"^[\s|Z_~]+", "", flat)
    flat = re.sub(r"(?i)^TEEPLECHASE\b", "STEEPLECHASE", flat)
    flat = re.sub(r"(?i)^ACING\s+CHAMPIONS\b", "RACING CHAMPIONS", flat)

    def _clean_cand(raw: str) -> str:
        cand = norm_space(raw)
        cand = re.split(r"(?i)\b(?:\d+|l|I)?(?:st|nd|rd|th)\s*:", cand)[0]
        return norm_space(cand.strip(" ,;|._-'\"`´"))

    # Prefer title glued immediately before a place rank (right-col swallow).
    # OCR often splits ``Advanced, On Lead Entries: 2`` as
    # ``Advanced, '1st: Riverview On Lead … Entries: 2``.
    m_pre = _AGILITY_TITLE_BEFORE_PLACE_RE.search(flat)
    if m_pre:
        cand = _clean_cand(m_pre.group(1))
        if cand and re.match(r"(?i)^(Novice|Open|Advanced)$", cand):
            tail = flat[m_pre.start() :]
            m_lead = re.search(r"(?i)\b((?:On|Off)\s+Lead)\b", tail)
            ents = list(_ENTRIES_COUNT_RE.finditer(tail))
            if m_lead:
                cand = f"{cand}, {m_lead.group(1)}"
            if ents:
                cand = f"{cand} Entries: {ents[-1].group(1)}"
            cand = norm_space(cand)
        if cand and _looks_like_class_header_line(cand):
            return cand

    # Prefer the last Entries-bearing span — left-col titles often precede
    # the right-col title in the same smashed box line.
    matches = list(_CLASS_HEADER_SPAN_WITH_ENTRIES_RE.finditer(flat))
    if matches:
        cand = _clean_cand(matches[-1].group(1))
        if cand:
            return cand
    m = _CLASS_HEADER_SPAN_RE.search(flat)
    if not m:
        return flat
    return _clean_cand(m.group(1))


def _ocr_interstitial_class_header(band: Image.Image) -> str:
    """Re-OCR a tight Y-band between place blocks for a dropped class title."""
    if band.size[0] < 8 or band.size[1] < 6:
        return ""
    # Upsample short header strips like highlight-band recovery.
    scale = 3 if band.size[1] <= 40 else 2
    big = band.resize(
        (band.size[0] * scale, band.size[1] * scale), Image.Resampling.LANCZOS
    )
    variants = _preprocess_variants(big)
    mid = next((im for name, im in variants if name == "mid"), variants[0][1])
    crisp = next((im for name, im in variants if name == "crisp"), mid)
    best = ""
    best_sc = -1
    for im in (mid, crisp):
        for psm in (7, 6, 4):
            try:
                raw = _tesseract_string(im, psm)
            except Exception:
                continue
            flat = _extract_class_header_span(raw)
            if not _looks_like_class_header_line(flat):
                continue
            sc = (
                min(40, len(flat))
                + (12 if re.search(r"(?i)entries\s*:", flat) else 0)
                + (8 if re.search(r"(?i)\bhandler\b", flat) else 0)
                + (6 if re.search(r"(?i)\b(?:steeplechase|racing|agility)\b", flat) else 0)
                + (4 if re.search(r"(?i)\b(?:bitch|dog|puppy|open|novice)\b", flat) else 0)
            )
            if sc > best_sc:
                best_sc, best = sc, flat
    return best


def _recover_class_titles_from_image(img: Image.Image, text: str) -> str:
    """Crop interstitial bands at place-rank gaps and insert recovered titles.

    Finalize has no image — this must run on the column OCR path. Unrecovered
    gaps still get ``[missing class header]`` later in finalize.
    """
    if not text or img is None:
        return text
    lines = text.splitlines()
    gaps = _iter_class_header_gap_indices(lines)
    if not gaps:
        return text
    boxes = _ocr_column_line_boxes(img)
    if len(boxes) < 4:
        return text

    def _prev_place_idx(gi: int) -> int | None:
        for j in range(gi - 1, -1, -1):
            s = lines[j].strip()
            if (
                _PLACE_NON_FIRST_RE.match(s)
                or _PLACE_FIRST_RE.match(s)
                or _CHAMP_RESERVE_ROLE_RE.match(s)
            ):
                return j
        return None

    def _prior_header_above(idx: int) -> str:
        for j in range(idx - 1, -1, -1):
            s = lines[j].strip()
            if _looks_like_class_header_line(s) or _SECTIONISH_RE.search(s):
                return norm_space(s).lower()
        return ""

    used: set[int] = set()
    inserts: dict[int, str] = {}
    h = img.size[1]
    for gi in gaps:
        pi = _prev_place_idx(gi)
        if pi is None:
            continue
        prior_hdr = _prior_header_above(gi)
        bi_prev = _match_text_line_to_box(lines[pi], boxes, used)
        bi_next = _match_text_line_to_box(lines[gi], boxes, used)
        if bi_prev is None or bi_next is None:
            continue

        def _accept_swallowed(span: str) -> bool:
            return bool(
                span
                and (
                    _ENTRIES_COUNT_RE.search(span)
                    or _AGILITY_LEVEL_TITLE_RE.search(span)
                )
                and _looks_like_class_header_line(span)
                and not (prior_hdr and _headers_near_duplicate(span, prior_hdr))
                and not _text_has_near_header(lines, span)
            )

        if bi_next <= bi_prev:
            # Column smash can map prev/next onto overlapping boxes; still try
            # a swallowed agility/class title from the ``1st:`` box.
            nxt_span = _extract_class_header_span(boxes[bi_next][0])
            if _accept_swallowed(nxt_span):
                inserts[gi] = nxt_span
                used.add(bi_next)
            continue
        used.add(bi_prev)
        used.add(bi_next)
        y0 = boxes[bi_prev][2]  # bottom of prior place
        y1 = boxes[bi_next][1]  # top of new 1st
        # Prefer any already-visible box text in the interstitial that looks
        # like a header (cheap win before a re-OCR).
        for bj in range(bi_prev + 1, bi_next):
            bt = _extract_class_header_span(boxes[bj][0])
            if not _looks_like_class_header_line(bt):
                continue
            if prior_hdr and _headers_near_duplicate(bt, prior_hdr):
                continue
            if _text_has_near_header(lines, bt):
                continue
            inserts[gi] = bt
            break
        if gi in inserts:
            continue
        # Next place box often swallows the header (highlight smear / tight Y).
        # Prefer Entries-bearing spans; also allow agility level titles
        # (``Advanced, On Lead``) when Entries was lost in the smash.
        nxt_span = _extract_class_header_span(boxes[bi_next][0])
        if _accept_swallowed(nxt_span):
            inserts[gi] = nxt_span
            continue
        gap_h = y1 - y0
        if gap_h > max(120, h // 8):
            # Too tall — likely misaligned boxes; skip rather than invent.
            continue
        if gap_h >= 6:
            pad = max(2, gap_h // 6)
            band_y0 = max(0, y0 - pad)
            band_y1 = min(h, y1 + pad)
        else:
            # Boxes abut/overlap — probe a thin strip across the boundary and
            # the upper third of the next place box (where the title sits).
            next_h = max(8, boxes[bi_next][2] - boxes[bi_next][1])
            band_y0 = max(0, min(y0, y1) - 25)
            band_y1 = min(h, max(y0, y1) + max(35, next_h // 3))
            if band_y1 - band_y0 < 8:
                continue
        band = img.crop((0, band_y0, img.size[0], band_y1))
        hdr = _ocr_interstitial_class_header(band)
        if (
            hdr
            and not (prior_hdr and _headers_near_duplicate(hdr, prior_hdr))
            and not _text_has_near_header(lines, hdr)
        ):
            inserts[gi] = hdr

    if not inserts:
        return text
    out: list[str] = []
    for i, ln in enumerate(lines):
        if i in inserts:
            out.append(inserts[i])
        out.append(ln)
    return "\n".join(out)


_ENTRIES_COUNT_RE = re.compile(r"(?i)entries\s*:\s*(\d+)")


def _header_line_key(s: str) -> str:
    return re.sub(r"[^a-z0-9]", "", norm_space(s or "").lower())


def _header_stems(s: str) -> set[str]:
    """Class-title stems, ignoring Entries/count noise.

    Extract from the original words (not the compacted key) so
    ``Child Handler`` → {child, handler}, not {childhandler}.
    """
    return {
        t.lower()
        for t in re.findall(r"[A-Za-z]{3,}", s or "")
        if t.lower() not in {"entries", "entry", "owned", "class"}
    }


def _header_height_key(s: str) -> str:
    """Coarse height-band key so ``10 up to 12 1/2`` ≠ ``over 12 1/2-15``."""
    t = norm_space(s or "").lower().replace("½", "1/2")
    # Keep range punctuation until the band is parsed (don't space-fold ``-``).
    m = re.search(
        r"(?i)(?:over\s*)?(\d+)\s*(?:1/2)?\s*(?:up\s*to|/|-|–|—|to)\s*(\d+)\s*(?:1/2)?",
        t,
    )
    if m:
        return f"{m.group(1)}-{m.group(2)}"
    m = re.search(r"(?i)\bover\s+(\d+)\s*(?:1/2)?", t)
    if m:
        return f"over-{m.group(1)}"
    m = re.search(r"(?i)\bup\s*to\s+(\d+)\s*(?:1/2)?", t)
    if m:
        return f"upto-{m.group(1)}"
    return ""


def _header_coat_key(s: str) -> str:
    """Coat marker including short OCR forms ``sm`` / ``r/br`` / ``rfbr``."""
    t = norm_space(s or "").lower()
    if re.search(r"(?i)\b(?:smooth|sm)\b", t):
        return "smooth"
    if re.search(r"(?i)\b(?:r\s*/\s*br|r/?br|rfbr|rough|broken)\b", t):
        return "rbr"
    return ""


def _headers_near_duplicate(a: str, b: str) -> bool:
    """True when two header lines are the same class (count may differ)."""
    sa, sb = _header_stems(a), _header_stems(b)
    if not sa or not sb:
        return False
    ov = len(sa & sb)
    need = min(2, len(sa), len(sb))
    if ov < need:
        return False
    # Distinct height bands are different classes (digits aren't in stems).
    ha, hb = _header_height_key(a), _header_height_key(b)
    if ha and hb and ha != hb:
        return False
    # Avoid collapsing distinct coat variants (smooth vs r/br), incl. ``sm``.
    ca, cb = _header_coat_key(a), _header_coat_key(b)
    if ca and cb and ca != cb:
        return False
    for coat in ("smooth", "rbr", "rough", "broken"):
        if (coat in sa) != (coat in sb):
            return False
    # Dog vs Bitch / Child vs Junior are different classes.
    if (bool(sa & {"dog", "dogs"}) and bool(sb & {"bitch", "bitches"})) or (
        bool(sa & {"bitch", "bitches"}) and bool(sb & {"dog", "dogs"})
    ):
        return False
    for pair in (("child", "junior"), ("junior", "youth"), ("child", "youth")):
        if (pair[0] in sa and pair[1] in sb) or (pair[1] in sa and pair[0] in sb):
            return False
    return True


def _find_near_header_index(lines: list[str], hdr: str) -> int | None:
    """Index of an existing similar class header, or None.

    Uses ``_headers_near_duplicate`` (height/coat aware) — stem-only matching
    falsely treated ``10 up to 12 1/2`` and ``over 12 1/2-15`` as the same class.
    """
    if not _header_stems(hdr):
        return None
    for i, ln in enumerate(lines):
        if not (_looks_like_class_header_line(ln) or _SECTIONISH_RE.search(ln or "")):
            continue
        if _headers_near_duplicate(hdr, ln):
            return i
    return None


def _text_has_near_header(lines: list[str], hdr: str) -> bool:
    return _find_near_header_index(lines, hdr) is not None


def _prefer_header_with_entries(a: str, b: str) -> str:
    """Keep the header that carries ``Entries: N`` (prefer richer text)."""
    a_n = _ENTRIES_COUNT_RE.search(a or "")
    b_n = _ENTRIES_COUNT_RE.search(b or "")
    if b_n and not a_n:
        return b
    if a_n and not b_n:
        return a
    return a if len(a or "") >= len(b or "") else b


def _dedupe_adjacent_class_headers(text: str) -> str:
    """Collapse duplicated class titles; keep the copy with Entries: N."""
    if not text:
        return text
    out: list[str] = []
    for ln in text.splitlines():
        if (
            out
            and (
                _looks_like_class_header_line(ln)
                or (_SECTIONISH_RE.search(ln) and not _PLACE_FIRST_RE.match(ln.strip()))
            )
            and (
                _looks_like_class_header_line(out[-1])
                or _SECTIONISH_RE.search(out[-1])
            )
            and _headers_near_duplicate(out[-1], ln)
        ):
            out[-1] = _prefer_header_with_entries(out[-1], ln)
            continue
        out.append(ln)
    return "\n".join(out)


def _merge_entry_counts_from_boxes(
    lines: list[str], boxes: list[tuple[str, int, int]]
) -> list[str]:
    """Attach ``Entries: N`` from word-boxes onto titles that lack a count."""
    out = list(lines)
    drop: set[int] = set()
    for i, ln in enumerate(out):
        if i in drop:
            continue
        if not (_looks_like_class_header_line(ln) or _SECTIONISH_RE.search(ln or "")):
            continue
        if _ENTRIES_COUNT_RE.search(ln):
            continue
        stems = _header_stems(ln)
        if not stems:
            continue
        best = ""
        best_ov = 0
        for raw, _y0, _y1 in boxes:
            hdr = norm_space(fix_ocr_li_confusion(fix_place_rank_ocr(raw)))
            if not _ENTRIES_COUNT_RE.search(hdr):
                continue
            if not _looks_like_class_header_line(hdr):
                continue
            ov = len(stems & _header_stems(hdr))
            if ov > best_ov and _headers_near_duplicate(ln, hdr):
                best_ov, best = ov, hdr
        if best:
            out[i] = best
            continue
        # Orphan digit on the next line after a bare ``Entries:`` / title
        if i + 1 < len(out) and re.fullmatch(r"\d{1,2}", out[i + 1].strip()):
            n = out[i + 1].strip()
            base = re.sub(r"(?i)\bentries\s*:\s*$", "", ln).rstrip()
            out[i] = norm_space(f"{base} Entries: {n}")
            drop.add(i + 1)
    return [ln for i, ln in enumerate(out) if i not in drop]


def _inject_headers_from_column_boxes(img: Image.Image, text: str) -> str:
    """Merge entry counts / insert missing titles from column word-boxes.

    Only inserts at place-rank gaps (never scatter-insert), and upgrades an
    existing title in place when boxes have ``Entries: N`` and text does not.
    """
    if not text or img is None:
        return text
    boxes = _ocr_column_line_boxes(img)
    if len(boxes) < 4:
        return text
    lines = [fix_place_rank_ocr(ln) for ln in text.splitlines()]
    lines = _merge_entry_counts_from_boxes(lines, boxes)

    gaps = _iter_class_header_gap_indices(lines)
    inserts: dict[int, str] = {}
    for gi in gaps:
        nxt = lines[gi].strip()
        nxt_keys = _line_fingerprint_keys(nxt)
        if len(nxt_keys) < 2:
            continue
        if gi > 0 and (
            _looks_like_class_header_line(lines[gi - 1])
            or _SECTIONISH_RE.search(lines[gi - 1])
        ):
            continue
        best_hdr = ""
        best_ov = 0
        for bi, (raw, _y0, _y1) in enumerate(boxes):
            hdr = norm_space(fix_ocr_li_confusion(fix_place_rank_ocr(raw)))
            if not _looks_like_class_header_line(hdr):
                continue
            # Skip BEST/division banners here — gap fill wants class titles.
            if re.search(r"(?i)champion\s*&\s*reserve|^best\b|division\b", hdr):
                continue
            # Next place under this header (tight window)
            next_place = ""
            for j in range(bi + 1, min(len(boxes), bi + 4)):
                bt = fix_place_rank_ocr(boxes[j][0]).strip()
                if _PLACE_FIRST_RE.match(bt) or _PLACE_NON_FIRST_RE.match(bt):
                    next_place = bt
                    break
                if _CHAMP_RESERVE_ROLE_RE.match(bt):
                    break
            if not next_place:
                continue
            ov = len(nxt_keys & _line_fingerprint_keys(next_place))
            if ov > best_ov:
                best_ov, best_hdr = ov, hdr
        if best_hdr and best_ov >= 2 and not _text_has_near_header(lines, best_hdr):
            inserts[gi] = best_hdr

    if inserts:
        out: list[str] = []
        for i, ln in enumerate(lines):
            if i in inserts:
                out.append(inserts[i])
            out.append(ln)
        lines = out
    return _dedupe_adjacent_class_headers("\n".join(lines))


def _fill_missing_class_titles(
    img: Image.Image, text: str, candidates: list[str] | None = None
) -> str:
    """Peer-mine then image-recover dropped class titles before finalize.

    Always normalize ``Ist:``→``1st:`` first — otherwise place-rank gaps (and
    Child/Junior Handler recovery) never arm. Dedupes adjacent headers and
    prefers the copy that kept ``Entries: N``.
    """
    if not text:
        return text
    text = fix_place_rank_ocr(text)
    text = _inject_headers_from_column_boxes(img, text)
    if candidates:
        text = _inject_peer_class_headers(
            text, [fix_place_rank_ocr(c) for c in candidates]
        )
    text = _recover_class_titles_from_image(img, text)
    return _dedupe_adjacent_class_headers(text)


def _drop_duplicate_owner_crumb_lines(lines: list[str]) -> list[str]:
    """Drop a lone owner-name line that repeats the prior place's owned-by tail.

    Example::
        3rd: Westmorland's Best Bet Yet, owned by L.Westmorland/D. Whitaker
        L.Westmorland/D.Whitaker
    """
    out: list[str] = []
    for ln in lines:
        s = ln.strip()
        if (
            out
            and s
            and not _PLACE_FIRST_RE.match(s)
            and not _PLACE_NON_FIRST_RE.match(s)
            and not _CHAMP_RESERVE_ROLE_RE.match(s)
            and not _looks_like_class_header_line(s)
            and not _SECTIONISH_RE.search(s)
            and not re.search(r"(?i)\bowned\s+by\b", s)
            and not re.match(r"(?i)^(?:best|champion|reserve)\s*:", s)
        ):
            prev = out[-1]
            m = re.search(r"(?i)\bowned\s+by\s+(.+)$", prev)
            if m:
                owner = re.sub(r"[^a-z0-9]", "", m.group(1).lower())
                cur = re.sub(r"[^a-z0-9]", "", s.lower())
                if cur and owner and len(cur) >= 6 and (cur in owner or owner in cur):
                    continue
        out.append(ln)
    return out


def finalize_results_ocr(text: str) -> str:
    """Structure cleanup first, then lexical OCR fixes.

    Name phrases like Huinter->Hunter only match after mid-line wraps are
    rejoined, so strip/rejoin must run before fix_ocr_li_confusion.
    Column-bleed smash repair runs after lexical owned-by normalization.
    Height Champ/Reserve rehome runs last so place-prefix stripping has already
    turned height-role crumbs into bare height role lines.

    Never insert [missing class header] placeholders — dropped titles are
    recovered from the column image / ensemble peers in
    _fill_missing_class_titles. Dedupes adjacent class titles and keeps the
    copy with Entries: N.
    """
    if not text:
        return text
    text = fix_ocr_li_confusion(_strip_gutter_noise(text))
    # Multi-place glue before smash unsmash — clears false C1 from ``1st:…5th:``
    text = _split_glued_multi_place_lines(text)
    text = _repair_smashed_place_lines(text)
    # Youth/Agility headers glued onto prior place bodies (``Galterio Youth Handler``)
    text = _unglue_place_embedded_class_headers(text)
    # Champ → false ``1st:`` → column → Reserve (Puppy Champ bleed)
    text = _drop_false_first_between_champ_and_column_reserve(text)
    # Reserve: Dog → ``1st:`` same Dog (High Score role replayed as a class)
    text = _drop_false_first_restarting_reserve_dog(text)
    # Champion/Reserve parked before the real class, HIGH SCORE header below
    text = _reorder_premature_high_score_roles(text)
    text = _demote_false_first_using_entries(text)
    text = _lift_class_header_before_orphan_first(text)
    text = "\n".join(_rehome_orphan_adult_height_champs(text.splitlines()))
    # Glue orphan entry-count digit onto prior bare Entries: / class title
    glued: list[str] = []
    lines = text.splitlines()
    i = 0
    while i < len(lines):
        ln = lines[i]
        if (
            i + 1 < len(lines)
            and re.fullmatch(r"\d{1,2}", lines[i + 1].strip())
            and (
                re.search(r"(?i)entries\s*:\s*$", ln)
                or (
                    _looks_like_class_header_line(ln)
                    and not _ENTRIES_COUNT_RE.search(ln)
                )
            )
        ):
            base = re.sub(r"(?i)\bentries\s*:\s*$", "", ln).rstrip()
            glued.append(norm_space(f"{base} Entries: {lines[i + 1].strip()}"))
            i += 2
            continue
        glued.append(ln)
        i += 1
    return _dedupe_adjacent_class_headers(
        "\n".join(_drop_duplicate_owner_crumb_lines(glued))
    )


# Residual OCR failure signatures — if these remain AFTER finalize, the page
# still needs a parser fix (self-audit as pages are written).
# Prefer class detectors over one-off tokens so new typos surface without a
# prior paste.
_OCR_AUDIT_PATTERNS: tuple[tuple[str, re.Pattern[str]], ...] = (
    ("height_pct", re.compile(r"(?i)\b10\s*-\s*12\s*%|\b12\s*%\s*-")),
    ("height_4slash2", re.compile(r"(?i)\b12\s*4/2\b|\b10\s*-\s*12\s*4/2\b|\b40\s*-\s*12\s*4/2\b")),
    ("height_101212", re.compile(r'(?i)\b10\s*-\s*1212\s*"?')),
    ("height_bare2", re.compile(
        r'(?i)\b10\s*-\s*12\s+2\s*"?|\b10\s*-\s*12\s+12\s*"?|\b12\s+2\s*-\s*15\s*"?|'
        r'\b12\s*%\s*2\b|\b12\s+2\s+up\s+to\s+15\b'
    )),
    ("champ_abbrev", re.compile(r"(?i)\bChamp\s*:")),
    ("height_40_42", re.compile(
        r"(?i)\b40\s*-\s*12\b|\b42\s*1/2\b|\b42\.?112\b|\b42\s*112\b|"
        r"\b42112\s*-\s*45\b|\b4211245\b|\b40\s*-\s*12\s*\.?\s*112\b|"
        r"\b40\s*-\s*12\s*\.?\s*4/2\b|\b12\s*\.\s*412\b|"
        r"\b1042112\b|\b121/215\b|\b10-127\b|\b10-2112\b|\b1012\s*12\b"
    )),
    ("vog_fups", re.compile(r"(?i)\bVog\s+Fups\b|\bDog\s+Fups\b")),
    ("place_ith", re.compile(r"(?i)\bith\s*:")),
    ("place_ond", re.compile(r"(?i)\b(?:ond|did)\s*:")),
    ("place_smash", re.compile(
        r"(?i)\bowned\s*,\s*owned\b|\bowned\s+by\s+owned\b|"
        r"\bowned\s+by\b.+\bowned\s+by\b|\bowned\s+by\b.+\bby\b.+\bby\b"
    )),
    ("trial_bleed", re.compile(
        r"(?i)^\d{1,3}\s{2,}.+\b(?:trial|harvest)\b|^\d{4}\s+JRTCA\s+Yearbook\b"
    )),
    ("place_bang", re.compile(r"(?i)\b\d+(?:st|nd|rd|th)\s*:\s*!")),
    # "1st: 4th Blackland" / "2nd: 3rd Name" — rank dust after the real place
    ("place_rank_dust", re.compile(
        r"(?i)\b(?:\d+(?:st|nd|rd|th)|best|champion|reserve)\s*:\s*"
        r"\d+(?:st|nd|rd|th)\b"
    )),
    ("owend_by", re.compile(r"(?i)\b(?:owend|owncd|owmed|ovned)\s+by\b|\bowned\s+hy\b")),
    ("agility_pipe", re.compile(r"(?i)\bAgility\s*[|¦!]")),
    ("judges_junk", re.compile(
        r'(?i)^Judges\s*:.*(?:GU["“”]|,\s*[A-Za-z]{1,2}\s*$|,\s*[A-Za-z]{1,3}\s*,\s*[A-Za-z]{1,3}\s*$)'
    )),
    ("champ_reserve_split", re.compile(
        r"(?im)^.*\bCHAMPION\s*$\n(?:AND\s+|&\s*)?RESERVE\s*$"
    )),
    ("cert_trailing_dash", re.compile(
        r'(?i)Championship\s+Certificate\s*\([^)\n]*"[–—−‐‑‒-]+\)'
    )),
    ("leading_I_garbage", re.compile(
        r"(?i)\b(?:\d+(?:st|nd|rd|th)|best|champion|reserve)\s*:\s+I\s+(?!Am\b)[A-Z][a-z]{2,}"
    )),
    ("cutoff_bitches", re.compile(r"(?im)^(?:3itches|itches)\b")),
    ("cutoff_dogs", re.compile(r"(?im)^(?:Jog\s+Pups|logs|itch\s+Pups)\b")),
    ("cutoff_racing", re.compile(r"(?im)^(?:nder|ver)\s+12\b|^(?:ACING|UPPIES|DULTS)\b")),
    # Class: any "... by" on a place/champ line that isn't owned/bred
    ("mangled_by", re.compile(
        r"(?i)(?:\d+(?:st|nd|rd|th)|champion|reserve|best)\s*:.*\b(?!owned\b|bred\b)[A-Za-z]{3,8}\s+by\b"
    )),
    ("height_trunc_paren", re.compile(r"(?i)\(10\s*-\s*12\s*1\)")),
    ("height_glued", re.compile(r"(?i)\b1211215\b")),
    ("age_I_yr", re.compile(r"(?i),\s*[I|]\s*yr\b|\b[I|]\s*yr\s*&")),
    ("juages", re.compile(r"(?i)\bJuages\b|\bJuaqes\b")),
    ("place_dnd", re.compile(r"(?im)^dnd\s*:|\bdnd\s*:")),
    ("dup_place", re.compile(r"(?im)^(?:\d*(?:st|nd|rd|th)\s*:)\s*(?:\d*(?:st|nd|rd|th))\s*[.:]")),
    ("place_and", re.compile(r"(?im)^and\s*:")),
    ("place_3id", re.compile(r"(?im)^3id\s*:")),
    ("place_9nd", re.compile(r"(?i)\b9nd\s*:")),
    ("place_dst", re.compile(r"(?im)^dst\s*:")),
    ("place_14st", re.compile(r"(?i)\b1\dst\s*:")),
    ("prestwock", re.compile(r"(?i)\bPrestwock")),
    ("lolbolly", re.compile(r"(?i)\bLolbolly\b")),
    ("mountan", re.compile(r"(?i)\bMountan\b")),
    ("geroge", re.compile(r"(?i)\bGeroge\b")),
    ("juniot", re.compile(r"(?i)\bJuniot\b|\bJunlor\b")),
    ("ribr", re.compile(r'(?i)(?<=[",\s])ribr\b')),
    ("rlbr", re.compile(r'(?i)(?<=[",\s])rlbr\b')),
    ("juqges", re.compile(r"(?i)\bJUQGES\b")),
    ("workingterrier", re.compile(r"(?i)\bWorkingTerrier\b")),
    ("glued_oth_place", re.compile(r"(?i)[A-Za-z](?:5\s*th|oth)\s*:")),
    ("cert_entries_glue", re.compile(r'(?i)1/2-15"Entries')),
    ("entriess", re.compile(r"(?i)\bEntriess\b|\bEntries\s+\d+\b")),
    ("4th_then_2nd", re.compile(r"(?im)^4th\s*:.*\n2nd\s*:")),
    ("4th_then_6th_no_5", re.compile(r"(?im)^4th\s*:.*\n6th\s*:")),
    ("ree_oaks", re.compile(r"(?i)\bree\s+Oaks\b")),
)

# Known truncated owner tails from pastes / catalog (O6). Finalize must NOT invent
# missing letters — only OCR ensemble / wider crop can restore.
_OWNER_TAIL_STUBS = frozenset(
    {
        "ste",
        "steph",
        "stephel",
        "crom",
        "louc",
        "lir",
        "alte",
        "bilinsk",
        "linc",
        "bett",
        "mi",
        # Observed post-reOCR crop stubs (not complete surnames)
        "pryc",
        "veaz",
        "vea",
        "kman",
        "ost",
        "osb",
        "tho",
        "brut",
        "hop",
        "kru",
        "beli",
        "kell",  # "...Brooks Kell" cut before Kelley
        "vin",  # "...Patricia Vin" → Vinet
        "bos",  # "...Lea Bos" → Boa/Boast trunc variants
        "tuy",  # "...Van Tuy" → Tuyl
        "gil",  # "...Susan Gil" → Gill
        "eic",  # "...Cathy Eic" → Eick
        "tes",  # "...Priscilla Tes" → Testa
        "tac",  # "...Sue Tac" → Tack
        "nel",  # "...Laura Nel" → Nelson
        "tri",  # "...Valerie Tri" → ?
        "sul",  # "...Barbara Sul" → Sullivan
    }
)

# Complete owner tokens that must NOT trip O6. Prior bug: any short surname
# matched. Prefer allowlisting real short names over flagging them.
_OWNER_TAIL_COMPLETE = frozenset(
    {
        # ultra-common / previously false-positive surnames (2–5 letters)
        "king",
        "smith",
        "hall",
        "brown",
        "jones",
        "davis",
        "fox",
        "day",
        "ward",
        "bell",
        "kent",
        "yee",
        "wren",
        "quick",
        "wilde",
        "healy",
        "frank",
        "meyer",
        "faust",
        "lynch",
        "ellis",
        "horn",
        "boa",
        "kemp",
        "guja",
        "robin",
        "burke",
        "gough",
        "smoke",
        "petty",
        "tatum",
        "white",
        "black",
        "green",
        "clark",
        "young",
        "allen",
        "adams",
        "baker",
        "cook",
        "gray",
        "grey",
        "hill",
        "hunt",
        "long",
        "reed",
        "ross",
        "ryan",
        "scott",
        "wood",
        "cole",
        "cross",
        "ford",
        "shaw",
        "west",
        "lane",
        "page",
        "pope",
        "snow",
        "stone",
        "vinet",
        "franklin",
        "gottlieb",
        "beaudoin",
        "maher",
        "heym",
        "tack",
        "hart",
        "nash",
        "hahn",
        "tait",
        "rose",
        "best",
        "glen",
        "rich",
        "ladd",
        "bird",
        "ries",
        "buck",
        "love",
        "monk",
        "erb",
        "lowe",
        "gay",
        "saul",
        "eick",
        "tuyl",
        "vega",
        "peck",
        "roth",
        "osby",
        "rico",
        "cox",
        "camp",
        "dye",
        "gill",
        "carr",
        "port",
        "byrd",
        "owen",
        "paff",
        "rowe",
        "mann",
        "neff",
        "lino",
        "jino",
        "mei",
        "vale",
        "inia",
        "gero",
        "kee",
        "webb",
        "jrt",
        "spec",
        "poe",
        "noa",
        "leo",
        "ary",
        "piel",
        "fed",
        "moe",
        "bay",
        "hom",
        "kem",
        "dog",  # "owned by Exhibitor Dog" boilerplate
        "verg",
        # short given / co-owner tokens (& Sue, & Ann, …)
        "lee",
        "sue",
        "ann",
        "amy",
        "joy",
        "kay",
        "may",
        "kim",
        "pat",
        "jim",
        "joe",
        "tom",
        "sam",
        "max",
        "ben",
        "dan",
        "meg",
        "deb",
        "don",
        "tim",
        "bob",
        "ron",
        "roy",
        "ray",
        "ned",
        "nan",
        "bea",
        "ada",
        "eva",
        "ida",
        "ora",
        "una",
        "lyn",
        "gail",
        "dale",
        "kirk",
        "kurt",
        "mark",
        "mary",
        "paul",
        "ruth",
        "todd",
        "wade",
        "yale",
        "zack",
        "john",
        "jon",
        "ali",
        "miwa",
    }
)


_OWNER_TAIL_SUFFIX_RE = re.compile(
    r"(?i)\s+(?:Jr\.?|Sr\.?|II|III|IV|2nd|3rd|Ill|Ili|Iii|lll)\s*$"
)


def is_owner_tail_trunc_line(line: str) -> bool:
    """True when owned-by clause ends in a crop/bleed stub (O6), not a short real name."""
    s = (line or "").strip()
    if not s or not re.search(r"(?i)\bowned\s+by\b", s):
        return False
    # Section boilerplate, not an owner surname crop
    if re.search(r"(?i)conformation\s+champion|exhibitor\s+dog", s):
        return False
    m = re.search(r"(?i)\bowned\s+by\b(.+)$", s)
    if not m:
        return False
    # Strip Jr/Sr/III (and OCR Ill/Ili) so "Duty III" is not a 3-letter surname hit
    tail = _OWNER_TAIL_SUFFIX_RE.sub("", m.group(1).strip()).strip()
    if not tail:
        return False
    # Co-owner cut: "... & Lir" / "& Bett" / "& Mi"
    m_amp = re.search(r"&\s+([A-Za-z']+)\s*$", tail)
    if m_amp:
        tok = m_amp.group(1).lower().rstrip(".")
        if tok in _OWNER_TAIL_STUBS:
            return True
        if 1 <= len(tok) <= 3 and tok not in _OWNER_TAIL_COMPLETE:
            return True
        return False
    # Given + surname at EOL
    m_name = re.search(r"\b([A-Z][A-Za-z']+)\s+([A-Z][A-Za-z']+)\s*$", tail)
    if not m_name:
        # Bare single token after owned by — only stubs / very short unknowns
        m_one = re.search(r"^([A-Za-z']+)\s*$", tail)
        if m_one:
            tok = m_one.group(1).lower().rstrip(".")
            if tok in _OWNER_TAIL_STUBS:
                return True
            if tok in _OWNER_TAIL_COMPLETE:
                return False
            # "owned by Jon" alone is incomplete (needs surname), flag
            return len(tok) <= 4
        return False
    last = m_name.group(2).lower().rstrip(".")
    if last in _OWNER_TAIL_STUBS:
        return True
    if last in _OWNER_TAIL_COMPLETE:
        return False
    # Unknown short surname: only 2–3 letters (4-letter unknowns are usually real)
    # Exception: trailing particle "Van"/"Der" often cut before the rest of the name.
    if last in {"van", "der", "de", "di", "le", "la", "du"}:
        return True
    if 2 <= len(last) <= 3:
        return True
    return False


def audit_results_ocr_page(text: str, *, max_samples: int = 3) -> list[tuple[str, str]]:
    """Return residual audit hits ``(code, sample_line)`` after finalize."""
    if not text:
        return []
    hits: list[tuple[str, str]] = []
    for code, pat in _OCR_AUDIT_PATTERNS:
        n = 0
        for m in pat.finditer(text):
            start = text.rfind("\n", 0, m.start()) + 1
            end = text.find("\n", m.end())
            if end < 0:
                end = min(len(text), m.end() + 120)
            line = text[start:end].strip()
            hits.append((code, line[:160]))
            n += 1
            if n >= max_samples:
                break
    # O6 — owner tail truncation (function, not broad 2–5 letter surname regex)
    n = 0
    for ln in text.splitlines():
        s = ln.strip()
        if not is_owner_tail_trunc_line(s):
            continue
        hits.append(("owner_tail_trunc", s[:160]))
        n += 1
        if n >= max_samples:
            break
    # Structural: place/champ line with a comma but no owned/bred by
    # (Junior/Child Handler names have no comma — skipped).
    n = 0
    for ln in text.splitlines():
        s = ln.strip()
        if not re.match(r"(?i)^(?:\d+(?:st|nd|rd|th)|champion|reserve)\s*:", s):
            continue
        if "," not in s:
            continue
        if re.search(r"(?i)\b(?:owned|bred)\s+by\b", s):
            continue
        hits.append(("missing_owned_by", s[:160]))
        n += 1
        if n >= max_samples:
            break
    # Bare Entries: with no count still present after finalize
    n = 0
    for ln in text.splitlines():
        if _ENTRIES_ONLY_RE.match(ln.strip()):
            hits.append(("bare_entries", ln.strip()[:160]))
            n += 1
            if n >= max_samples:
                break
    # Orphan 1–3 digit lines (stray entry counts)
    n = 0
    for ln in text.splitlines():
        if _NUM_ONLY_RE.match(ln.strip()):
            hits.append(("orphan_entry_count", ln.strip()[:160]))
            n += 1
            if n >= max_samples:
                break
    # Place-rank / Champ-Reserve → 1st gaps with no recoverable title yet
    lines = text.splitlines()
    for gi in _iter_class_header_gap_indices(lines)[:max_samples]:
        sample = lines[gi].strip()[:160]
        hits.append(("class_header_gap", sample))
    return hits


def report_ocr_page_audit(page_no: int, hits: list[tuple[str, str]]) -> int:
    """Print residual OCR issues for a page; return hit count."""
    if not hits:
        return 0
    by_code: dict[str, list[str]] = {}
    for code, line in hits:
        by_code.setdefault(code, []).append(line)
    summary = ", ".join(f"{c}×{len(v)}" for c, v in sorted(by_code.items()))
    print(f"    AUDIT page {page_no}: {summary}", flush=True)
    for code, lines in sorted(by_code.items()):
        for line in lines[:2]:
            print(f"      [{code}] {line}", flush=True)
    return len(hits)


@dataclass
class Person:
    name: str
    role: str | None = None
    address: str | None = None
    city: str | None = None
    state: str | None = None
    postal: str | None = None
    phone: str | None = None
    owner_id: int | None = None


def norm_space(s: str) -> str:
    return re.sub(r"\s+", " ", (s or "").strip())


def name_key(s: str) -> str:
    return re.sub(r"[^a-z]", "", (s or "").lower())


_SUFFIXES = {"jr", "jr.", "sr", "sr.", "ii", "iii", "iv", "2nd", "3rd"}


def _looks_like_ocr_garbage_token(tok: str) -> bool:
    """Reject tokens with unlikely letter runs from bad OCR."""
    t = tok.lower().strip(".,")
    if not t or re.match(r"^[a-z]\.?$", t):
        return False
    # triple same letter, or 'ii'/'iii' inside non-suffix words, or vowel-less blobs
    if re.search(r"(.)\1\1", t):
        return True
    if "ii" in t and t not in {"illinois", "hawaii"} and not t.endswith("ii"):
        # Dougherty misspellings like deugiiencys already mapped; residual junk
        if t.count("i") >= 3:
            return True
    vowels = sum(1 for c in t if c in "aeiou")
    if len(t) >= 6 and vowels <= 1:
        return True
    # uncommon consonant clusters from OCR mush
    if re.search(r"gii|encys|iienc|lhower|tield|fleld", t):
        return True
    return False


def is_human_name(name: str) -> bool:
    """Strict person name; allows middle initial and Jr/Sr/III."""
    n = norm_space(name)
    n = re.sub(r"^(Mrs?|Ms|Miss|Dr|Mes|Mre|Mra)\.?\s+", "", n, flags=re.I)
    if len(n) < 7 or len(n) > 50:
        return False
    if re.search(r"\d", n) or n.endswith("-"):
        return False
    parts = n.split()
    if len(parts) < 2 or len(parts) > 5:
        return False
    core = [p for p in parts if p.lower().strip(".") not in _SUFFIXES]
    if len(core) < 2:
        return False
    for p in parts:
        bare = p.strip(".,").lower()
        if bare in _SUFFIXES:
            continue
        if re.match(r"^[A-Z]\.?$", p):
            continue
        if len(bare) < 3:
            return False
        if bare in _REJECT_TOKENS or bare in _ROLE_WORDS:
            return False
        if _looks_like_ocr_garbage_token(p):
            return False
        if not re.match(r"^[A-Z][A-Za-z'\-]+$", p):
            return False
        if p.isupper() and len(p) > 3:
            return False
        if p.endswith("-"):
            return False
    if len(core) == 2 and parts[-1].lower().strip(".") in _SUFFIXES:
        return False
    low = n.lower()
    if any(re.search(rf"\b{re.escape(t)}\b", low) for t in _REJECT_TOKENS):
        return False
    if n.isupper():
        return False
    return True


_CITY_BAD = {
    "tel", "phone", "fax", "vc", "chairman", "committee", "road", "rd",
    "street", "ave", "avenue", "lane", "ln", "drive", "dr", "way", "box",
    "blvd", "court", "ct", "circle", "highway", "hwy", "route", "rte", "rt",
}


def clean_city(raw: str) -> str | None:
    """Strip leading person/garbage tokens; keep real place names only."""
    city = norm_space(raw)
    city = re.sub(r"^(?:V\.?C\.?|Vice[- ]?Chairman|Chairman)\s+", "", city, flags=re.I)
    words = [w for w in city.split() if w.lower().strip(".,") not in _CITY_BAD and not re.search(r"\d", w)]
    if not words:
        return None
    # Multi-column OCR often prefixes a neighbor's name: "Mike Adler Waynesville"
    if len(words) >= 3:
        if words[-2].lower() in _CITY_PREFIX:
            words = words[-2:]
        else:
            words = words[-1:]
    elif len(words) == 2 and words[0].lower() not in _CITY_PREFIX:
        words = [words[-1]]
    city = " ".join(words)
    if len(city) < 3 or len(city) > 40:
        return None
    return city


def contact_window(block: str, start: int) -> str:
    """Strict address block: only lines right under the name, stop at next person."""
    rest = block[start:]
    for pat in (
        _ROLE_NAME_PAT,
        _PERSON_LINE_PAT,
        _END_HEADERS,
        re.compile(r"(?i)OCR-ENSEMBLE-EXTRAS"),
        re.compile(r"(?i)^\s*Chairman,\s+\w+\s+Committee\s*$", re.M),
    ):
        m = pat.search(rest)
        if m and m.start() > 0:
            rest = rest[: m.start()]
    lines = []
    blanks = 0
    for ln in rest.splitlines():
        s = norm_space(ln)
        if not s:
            blanks += 1
            # allow one blank between street and city (common OCR); stop on 2nd
            if lines and blanks >= 2:
                break
            continue
        blanks = 0
        # stop if line looks like another person (First Last) without digits
        if (
            lines
            and re.match(r"^(?:Mrs?|Ms|Miss|Dr|Mes|Mre|Mra)\.?\s+[A-Z]", s, re.I)
        ) or (
            lines
            and re.match(r"^[A-Z][a-z]+\s+[A-Z][a-z]+(?:\s+[A-Z][a-z]+)?$", s)
            and not _STREET.search(s)
            and not _CITY_ST.search(s)
            and not _PHONE.search(s)
        ):
            break
        lines.append(s)
        if len(lines) >= 5:  # street, city, phone, spare
            break
    return "\n".join(lines)


def attach_contact(p: Person, window: str) -> None:
    """Street + city must come from the same short block under the name."""
    window = fix_ocr_li_confusion(window)
    lines = [ln for ln in window.splitlines() if norm_space(ln)]
    if not lines:
        return

    # Find city line index first — street may only come from lines BEFORE it
    city_idx = None
    city_m = None
    for i, ln in enumerate(lines):
        cm = _CITY_ST.search(ln)
        if not cm:
            continue
        city = clean_city(cm.group(1))
        if not city:
            continue
        st = (cm.group(2) or "").upper()
        if not st and cm.group(3):
            st = _STATE_NAMES_TO_ABBR.get(cm.group(3).upper(), "")
        postal = cm.group(4)
        if st and postal:
            city_idx, city_m = i, (city, st, postal)
            break

    if city_m and not p.city:
        p.city = fix_ocr_li_confusion(city_m[0])
        p.state = city_m[1]
        p.postal = city_m[2]

    # Street only from lines above the city (same person block)
    street_region = "\n".join(lines[: city_idx if city_idx is not None else len(lines)])
    if not p.address and street_region:
        sm = _STREET.search(street_region)
        if sm:
            addr = fix_ocr_li_confusion(norm_space(sm.group(1))).strip(" ,;")
            # Do NOT split on Titlecase pairs — that turns "2644 Beckleysville Road" into "2644"
            if 4 <= len(addr) <= 70 and not re.search(r"[A-Z]{2}\s+\d{5}", addr):
                p.address = addr

    # Phone from same block only
    if not p.phone:
        ph = _PHONE.search(window)
        if ph:
            p.phone = ph.group(0)

    # If we somehow got a street but no city, keep street; if city but street
    # came from a different glued column (contains another city name), drop street
    if p.address and p.city and p.city.lower() in p.address.lower():
        p.address = None


_MIDDLE_KEEP = {
    "cross", "ann", "anne", "marie", "lynn", "sue", "jo", "lee", "may",
    "van", "von", "de", "dela", "st",
}


def refine_name(raw: str) -> str | None:
    """Normalize honorifics/initials/suffixes; drop column-bleed leading junk."""
    n = norm_space(raw)
    n = re.sub(r"^(Mrs?|Ms|Miss|Dr|Mes|Mre|Mra)\.?\s+", "", n, flags=re.I)
    n = fix_ocr_li_confusion(n)
    parts = n.split()
    while parts and parts[-1].lower().strip(".,") in _ADDR_TOKENS:
        parts.pop()
    # Keep suffix at end
    suffix = []
    if parts and parts[-1].lower().strip(".") in {s.strip(".") for s in _SUFFIXES}:
        suffix = [parts.pop()]
    # Drop leading bleed token when 4+ core parts (e.g. "Moles Harden L Crawford")
    if len(parts) >= 4:
        parts = parts[-3:]
    elif len(parts) == 3:
        mid = parts[1]
        keep_mid = (
            re.match(r"^[A-Z]\.?$", mid)
            or mid.lower().strip(".,") in _MIDDLE_KEEP
            or "-" in mid
        )
        if not keep_mid:
            parts = parts[-2:]
    name = " ".join(parts + suffix)
    name = re.sub(r"\b([A-Z])\b(?!\.)", r"\1.", name)
    name = re.sub(r"\b(Jr|Sr|II|III|IV)\.", r"\1", name, flags=re.I)
    return name if is_human_name(name) else None


def parse_role_anchored(block: str) -> list[Person]:
    """Only accept 'Name, Role' (comma required) to avoid loose matches."""
    # Strip ensemble extras so alt OCR phones/cities cannot steal addresses
    block = re.split(r"(?i)---\s*OCR-ENSEMBLE-EXTRAS\s*---", block)[0]
    people: list[Person] = []
    for m in _ROLE_NAME_PAT.finditer(block):
        name = refine_name(m.group(1))
        if not name:
            continue
        role = norm_space(m.group(2))
        p = Person(name=name, role=role.title().replace("Vc", "VC"))
        attach_contact(p, contact_window(block, m.end()))
        people.append(p)
    return dedupe_people(people)


def dedupe_people(people: list[Person]) -> list[Person]:
    seen = set()
    out = []
    for p in people:
        k = (name_key(p.name), (p.role or "").lower())
        if k in seen:
            continue
        seen.add(k)
        out.append(p)
    return out


def _upscale(img: Image.Image, min_long: int = 3200) -> Image.Image:
    w, h = img.size
    long = max(w, h)
    if long >= min_long:
        return img
    factor = min_long / float(long)
    return img.resize((int(w * factor), int(h * factor)), Image.Resampling.LANCZOS)


def _despink_highlighter(img: Image.Image) -> Image.Image:
    """Suppress pink/magenta/yellow highlighter wash; keep black ink.

    Manual highlight pens (Yankee 2001 etc.) crush contrast so place/owner
    lines mangle (Doub/Doug, Bobl&GenielFranklin, …). Use green minus pinkness
    (pink = R>G); whiten pure wash; leave dark strokes.
    """
    try:
        import numpy as np
    except Exception:
        return ImageOps.grayscale(img)
    rgb = img.convert("RGB")
    arr = np.asarray(rgb).astype(np.float32)
    r, g, b = arr[:, :, 0], arr[:, :, 1], arr[:, :, 2]
    mn = np.minimum(np.minimum(r, g), b)
    mx = np.maximum(np.maximum(r, g), b)
    sat = (mx - mn) / (mx + 1e-3)
    # Pink/magenta OR yellow highlighter
    pinkness = np.clip(r - g, 0, 255)
    yellowness = np.clip(np.minimum(r, g) - b, 0, 255)
    ink = np.clip(g - 0.75 * pinkness - 0.35 * yellowness, 0, 255)
    # Prefer min-channel in non-highlight areas (truer gray text)
    hl = sat > 0.10
    out = mn.copy()
    out[hl] = ink[hl]
    # Wipe highlighter background (no ink stroke)
    out[hl & (out > 145)] = 255
    return Image.fromarray(out.astype(np.uint8), "L")


def _preprocess_variants(img: Image.Image) -> list[tuple[str, Image.Image]]:
    """Preprocess paths for mixed fonts/contrast (no giant RAM blowups)."""
    # Despink first when RGB highlighter is present; else plain gray.
    try:
        import numpy as np

        rgb = img.convert("RGB")
        a = np.asarray(rgb).astype(np.float32)
        r, g, b = a[:, :, 0], a[:, :, 1], a[:, :, 2]
        mx = np.maximum(np.maximum(r, g), b)
        mn = np.minimum(np.minimum(r, g), b)
        sat = (mx - mn) / (mx + 1e-3)
        has_hl = float(((sat > 0.12) & (mx > 100) & (mn > 50)).mean()) > 0.004
    except Exception:
        has_hl = False

    if has_hl:
        base = _despink_highlighter(img)
    else:
        base = ImageOps.grayscale(img)
    base = _upscale(base, 3400)
    variants: list[tuple[str, Image.Image]] = []

    soft = ImageOps.autocontrast(base, cutoff=0.5)
    soft = soft.filter(ImageFilter.UnsharpMask(radius=1.2, percent=140, threshold=2))
    variants.append(("soft", soft))

    mid = ImageOps.autocontrast(base, cutoff=1)
    mid = mid.filter(ImageFilter.MedianFilter(size=3))
    mid = mid.filter(ImageFilter.UnsharpMask(radius=1.6, percent=180, threshold=2))
    variants.append(("mid", mid))

    # Crisp (no median): median blur merges thin Helvetica stems (l↔i, n↔ri).
    crisp = ImageOps.autocontrast(base, cutoff=0.8)
    crisp = crisp.filter(ImageFilter.UnsharpMask(radius=1.0, percent=200, threshold=1))
    variants.append(("crisp", crisp))

    # Binarize recovers faint/thin type that soft/mid miss.
    hard = ImageOps.autocontrast(base, cutoff=2)
    hard = hard.point(lambda p: 255 if p > 168 else 0)
    variants.append(("bin", hard))

    # Extra despink-bin path when highlighter detected (helps Lickity/Franklin lines)
    if has_hl:
        db = ImageOps.autocontrast(_despink_highlighter(img), cutoff=1)
        db = _upscale(db, 3400)
        db = db.filter(ImageFilter.UnsharpMask(radius=1.8, percent=220, threshold=1))
        db = db.point(lambda p: 255 if p > 155 else 0)
        variants.append(("hlbin", db))
    return variants


def _ocr_score(text: str) -> int:
    """Prefer OCR that recovers roles, city/state/zip, phones, and clean names."""
    if not text:
        return 0
    score = 0
    score += 10 * len(
        re.findall(
            r"\b(?:Chairman|Chairperson|Vice[- ]?Chairman|Vice[- ]?Chair|"
            r"President|Secretary|Treasurer|Director|VC)\b",
            text,
            re.I,
        )
    )
    score += 6 * len(_CITY_ST.findall(text))
    score += 4 * len(_PHONE.findall(text))
    score += 3 * len(_STREET.findall(text))
    score += 2 * len(re.findall(r"(?i)\b(?:Board|Committee|Representative|Directors)\b", text))
    score += len(re.findall(r"\b[A-Z][a-z]+\s+[A-Z][a-z]+\b", text)) // 4
    score -= text.count("|") * 2
    score -= len(re.findall(r"[A-Za-z]\s[A-Za-z]\s[A-Za-z]", text)) // 2
    return score


def _valuable_lines(text: str) -> list[str]:
    """Contact-only lines for ensemble merge (never merge alt name OCR — causes junk people)."""
    out = []
    for ln in text.splitlines():
        s = norm_space(ln)
        if len(s) < 5 or len(s) > 80:
            continue
        # Only phones / city-state-zip / street — not Name,Role (primary column OCR owns people)
        if _CITY_ST.search(s) or _PHONE.search(s) or _STREET.search(s):
            out.append(s)
    return out


def _merge_ocr_texts(candidates: list[str]) -> str:
    """Keep best full page, then append unique high-value lines from others."""
    if not candidates:
        return ""
    ranked = sorted((( _ocr_score(t), len(t), i, t) for i, t in enumerate(candidates)), reverse=True)
    primary = ranked[0][3]
    seen = {norm_space(x).lower() for x in primary.splitlines() if norm_space(x)}
    # also index by collapsed alnum for fuzzy-ish dupes
    seen_keys = {re.sub(r"[^a-z0-9]", "", s) for s in seen}
    extras: list[str] = []
    for _sc, _ln, _i, t in ranked[1:]:
        for line in _valuable_lines(t):
            key = re.sub(r"[^a-z0-9]", "", line.lower())
            if not key or key in seen_keys:
                continue
            if line.lower() in seen:
                continue
            seen.add(line.lower())
            seen_keys.add(key)
            extras.append(line)
    if not extras:
        return primary
    return primary.rstrip() + "\n\n--- OCR-ENSEMBLE-EXTRAS ---\n" + "\n".join(extras)


def _cluster_columns(xs: list[float], page_w: float) -> list[float]:
    """Return sorted x-boundaries (right edge of each column cluster)."""
    if not xs:
        return [page_w]
    xs = sorted(xs)
    gaps = []
    for i in range(1, len(xs)):
        gap = xs[i] - xs[i - 1]
        if gap > page_w * 0.07:
            gaps.append((gap, (xs[i - 1] + xs[i]) / 2))
    gaps.sort(reverse=True)
    cuts = sorted(c for g, c in gaps[:4] if g > page_w * 0.09)
    return cuts + [page_w]


def _ocr_columns_from_data(img: Image.Image, conf_min: float = 25) -> str:
    """OCR with word boxes; reconstruct column-then-row reading order."""
    import pytesseract

    # TESSDATA_PREFIX set process-wide in ocr_pdf_hq — do not lock around OCR.
    with _tess_slots:
        try:
            data = pytesseract.image_to_data(
                img,
                config=_tesseract_cfg(3, _OCR_LANG),
                output_type=pytesseract.Output.DICT,
            )
        except Exception:
            data = pytesseract.image_to_data(
                img,
                config=_tesseract_cfg(3, "eng"),
                output_type=pytesseract.Output.DICT,
            )
    n = len(data["text"])
    words = []
    page_w = img.size[0]
    for i in range(n):
        txt = (data["text"][i] or "").strip()
        try:
            conf = float(data["conf"][i])
        except Exception:
            conf = -1
        if not txt or conf < conf_min:
            continue
        x, y, w, h = data["left"][i], data["top"][i], data["width"][i], data["height"][i]
        words.append(
            {"t": txt, "x": x, "y": y, "w": w, "h": h, "cx": x + w / 2.0, "cy": y + h / 2.0}
        )
    if len(words) < 8:
        return ""
    bounds = _cluster_columns([w["cx"] for w in words], float(page_w))
    for w in words:
        col = 0
        for b in bounds:
            if w["cx"] <= b:
                break
            col += 1
        w["col"] = col
    cols: dict[int, list] = {}
    for w in words:
        cols.setdefault(w["col"], []).append(w)
    blocks = []
    for col in sorted(cols):
        items = sorted(cols[col], key=lambda z: (z["cy"], z["x"]))
        lines: list[list] = []
        for w in items:
            if not lines:
                lines.append([w])
                continue
            prev = lines[-1][-1]
            if abs(w["cy"] - prev["cy"]) <= max(12, 0.65 * max(w["h"], prev["h"])):
                lines[-1].append(w)
            else:
                lines.append([w])
        col_lines = []
        for line in lines:
            line.sort(key=lambda z: z["x"])
            col_lines.append(" ".join(z["t"] for z in line))
        blocks.append("\n".join(col_lines).strip())
    return "\n\n".join(b for b in blocks if b)


def _ocr_vertical_strips(img: Image.Image, n_strips: int = 3) -> str:
    """Force column separation by cropping vertical strips and OCRing each.

    Strips stay sequential here to avoid nested ThreadPools when the parent
    ensemble already runs strips2/strips3 in parallel with other jobs.
    """
    w, h = img.size
    pad = max(8, w // 80)
    parts: list[str] = []
    for i in range(n_strips):
        x0 = max(0, int(i * w / n_strips) - pad)
        x1 = min(w, int((i + 1) * w / n_strips) + pad)
        crop = img.crop((x0, 0, x1, h))
        best = ""
        best_sc = -10**9
        for psm in (4, 6):
            t = _tesseract_string(crop, psm)
            sc = _ocr_score(t)
            if sc > best_sc:
                best_sc, best = sc, t
        if best.strip():
            parts.append(best.strip())
    return "\n\n".join(parts)


# Font-matched Tesseract lang for current PDF (set in ocr_pdf_hq).
_OCR_LANG: str = "eng"
_OCR_TESSDATA_DIR: str | None = None
# In-page parallel tesseract (quality-neutral: same jobs, deterministic gather).
_OCR_WORKERS = max(1, int(os.environ.get("JRTCA_OCR_WORKERS", "10")))
# Parallel pages within a PDF (shared _tess_slots cap; write partials in order).
_OCR_PAGE_WORKERS = max(1, int(os.environ.get("JRTCA_OCR_PAGE_WORKERS", "2")))
_tess_env_lock = threading.Lock()
# Cap concurrent tesseract.exe processes across nested pools (columns × ensemble).
_tess_slots = threading.Semaphore(_OCR_WORKERS)


def _ocr_workers() -> int:
    return _OCR_WORKERS


def _ocr_page_workers() -> int:
    return _OCR_PAGE_WORKERS


def _run_ocr_jobs(jobs: list[tuple[str, Callable[[], str]]]) -> list[str]:
    """Run OCR callables in parallel; return non-empty texts in stable job order."""
    if not jobs:
        return []
    workers = min(_ocr_workers(), len(jobs))
    results: list[str | None] = [None] * len(jobs)

    def _call(fn: Callable[[], str]) -> str:
        try:
            return fn() or ""
        except Exception:
            return ""

    if workers <= 1:
        for i, (_label, fn) in enumerate(jobs):
            results[i] = _call(fn)
    else:
        with ThreadPoolExecutor(max_workers=workers) as ex:
            futs = {ex.submit(_call, fn): i for i, (_label, fn) in enumerate(jobs)}
            for fut in as_completed(futs):
                results[futs[fut]] = fut.result()
    return [t for t in results if t and str(t).strip()]


def _tesseract_cfg(psm: int, lang: str) -> str:
    return f"--oem 3 --psm {psm} -l {lang} -c preserve_interword_spaces=1"


def _tesseract_string(img: Image.Image, psm: int) -> str:
    import pytesseract

    # Preserve spaces helps multi-column / tabular yearbook layouts.
    # TESSDATA_PREFIX is set once in ocr_pdf_hq (path-without-spaces runtime dir).
    # Do not hold a lock across image_to_string — that serializes the ensemble.
    cfg = _tesseract_cfg(psm, _OCR_LANG)
    with _tess_slots:
        try:
            return pytesseract.image_to_string(img, config=cfg) or ""
        except Exception:
            if _OCR_LANG == "eng":
                raise
    # Rare fallback to stock eng — briefly clear custom prefix
    with _tess_env_lock:
        prev_prefix = os.environ.get("TESSDATA_PREFIX")
        try:
            os.environ.pop("TESSDATA_PREFIX", None)
            with _tess_slots:
                return (
                    pytesseract.image_to_string(img, config=_tesseract_cfg(psm, "eng"))
                    or ""
                )
        finally:
            if prev_prefix is not None:
                os.environ["TESSDATA_PREFIX"] = prev_prefix
            elif _OCR_TESSDATA_DIR:
                os.environ["TESSDATA_PREFIX"] = _OCR_TESSDATA_DIR


def _two_up_halves(img: Image.Image) -> list[Image.Image] | None:
    """Per-page detect facing-page spreads; return [left, right] or None.

    Must be decided page-by-page — e.g. 1990 Vol 1 scans are landscape
    two-up (≈756×610 with a white gutter); 1990 Vol 2 is single-leaf
    near-square (≈610×599) and must NOT be split.
    """
    w, h = img.size
    # Single leaves are ~1:1; true spreads are clearly wider than tall.
    if w < int(h * 1.18):
        return None
    try:
        import numpy as np
    except Exception:
        return None
    gray = np.asarray(img.convert("L"))
    # Whitest vertical band near center = binding gutter between facing pages
    lo, hi = int(w * 0.42), int(w * 0.58)
    best_x, best_white = lo, -1.0
    band = max(3, w // 250)
    for x in range(lo, hi):
        strip = gray[:, max(0, x - band) : min(w, x + band + 1)]
        white = float((strip > 235).mean())
        if white > best_white:
            best_white, best_x = white, x
    # Spreads show a near-paper gutter; single pages rarely hit this in-center.
    if best_white < 0.92:
        return None
    gap = max(6, w // 180)
    x_cut = best_x
    left = gray[:, : max(1, x_cut - gap)]
    right = gray[:, min(w - 1, x_cut + gap) :]
    if left.size < 100 or right.size < 100:
        return None
    left_ink = float((left < 200).mean())
    right_ink = float((right < 200).mean())
    # Both leaves must carry real print (avoid margin-only false gutters)
    if left_ink < 0.04 or right_ink < 0.04:
        return None
    # Reject lopsided cuts (one side almost empty = not a real spread)
    if min(left_ink, right_ink) / max(left_ink, right_ink) < 0.25:
        return None
    return [
        img.crop((0, 0, x_cut - gap, h)),
        img.crop((x_cut + gap, 0, w, h)),
    ]


def _two_column_cut_x(img: Image.Image) -> int | None:
    """Return gutter x for portrait two-column page, or None if not two-column."""
    w, h = img.size
    if w >= int(h * 1.18):
        return None
    try:
        import numpy as np
    except Exception:
        return None
    gray = np.asarray(img.convert("L"))
    lo, hi = int(w * 0.38), int(w * 0.62)
    best_x, best_white = (lo + hi) // 2, -1.0
    band = max(4, w // 200)
    for x in range(lo, hi):
        strip = gray[:, max(0, x - band) : min(w, x + band + 1)]
        white = float((strip > 230).mean())
        if white > best_white:
            best_white, best_x = white, x
    if best_white < 0.55:
        best_x = w // 2
    # Wide gap to exclude midpoint gutter garbage from both halves
    gap = _column_gutter_gap(w)
    x_cut = best_x
    left = gray[:, : max(1, x_cut - gap)]
    right = gray[:, min(w - 1, x_cut + gap) :]
    if left.size < 100 or right.size < 100:
        return None
    left_ink = float((left < 200).mean())
    right_ink = float((right < 200).mean())
    if left_ink < 0.035 or right_ink < 0.035:
        return None
    if min(left_ink, right_ink) / max(left_ink, right_ink) < 0.30:
        return None
    return x_cut


def _two_column_halves(img: Image.Image) -> list[Image.Image] | None:
    """Portrait single-leaf with TWO text columns (1997+ yearbook results pages).

    Landscape facing-page spreads are handled by _two_up_halves. Portrait pages
    with a center gutter must be split too — full-page OCR interleaves columns
    and scrambles 1st/2nd/3rd order.
    """
    w, h = img.size
    x_cut = _two_column_cut_x(img)
    if x_cut is None:
        return None
    gap = _column_gutter_gap(w)
    return [
        img.crop((0, 0, max(1, x_cut - gap), h)),
        img.crop((min(w - 1, x_cut + gap), 0, w, h)),
    ]


def _header_band_height(img: Image.Image) -> int:
    """Top band kept full-width so trial title/date/chair/judges stay intact.

    Structure baseline: title / place-date / Chairperson / Judges only.
    Must STOP before CONFORMATION / first class rows — those live in the two columns.

    Centered titles ink BOTH left and right mid-bands — require a *white
    gutter* as well so we don't cut through the title (1997 p25 failure).
    """
    w, h = img.size
    try:
        import numpy as np

        gray = np.asarray(img.convert("L"))
        hh, ww = gray.shape
        # Chair/judges sit ~8–16% down; never treat that band as column start.
        y0 = int(hh * 0.155)
        y1 = int(hh * 0.34)
        lx0, lx1 = int(ww * 0.06), int(ww * 0.40)
        rx0, rx1 = int(ww * 0.60), int(ww * 0.94)
        gx0, gx1 = int(ww * 0.47), int(ww * 0.53)
        row_h = max(8, hh // 100)
        streak = 0
        first_y = None
        for y in range(y0, y1, row_h):
            band = gray[y : y + row_h, :]
            left_ink = float((band[:, lx0:lx1] < 200).mean())
            right_ink = float((band[:, rx0:rx1] < 200).mean())
            gut_ink = float((band[:, gx0:gx1] < 200).mean())
            # Two columns: ink on both sides, nearly empty center gutter
            if left_ink > 0.035 and right_ink > 0.035 and gut_ink < 0.025:
                streak += 1
                if first_y is None:
                    first_y = y
                if streak >= 2:
                    # Back up one row so last header line isn't clipped
                    return max(int(hh * 0.15), first_y - row_h)
            else:
                streak = 0
                first_y = None
    except Exception:
        pass
    return max(int(h * 0.14), min(int(h * 0.18), int(h * 0.16)))


def _column_gutter_gap(w: int) -> int:
    """Half-width of excluded midpoint strip (structure: vertical rule only).

    Was ~4.8% per side (~117px @ 2448) and clipped owner surnames at the
    column edge (Mathi/Mathis, Sandr/Sandra, Fi/Fulton, Ro/…). Keep just
    enough to drop the center rule / gutter dust — ~1.5% per side.
    """
    return max(6, int(w * 0.015))


_PLACE_ONLY_RE = re.compile(
    r"(?i)^(best|champion|reserve|\d*(?:st|nd|rd|th))\s*:\s*$"
)
_ENTRIES_ONLY_RE = re.compile(r"(?i)^entries\s*:\s*$")
_NUM_ONLY_RE = re.compile(r"^\d{1,3}$")
_CLASS_HEADER_RE = re.compile(
    r"(?i)^(novice|open|pre-|puppy|adult|dog|bitch|go-?to|working|family|bred|youth|"
    r"conformation|agility|racing|super|championship)"
)
# Next-section race/division header glued onto a place/owner line
# (e.g. ``owned by Alte STEEPLECHASE RACES`` / ``owned by Alta RACING CHAMPIONS``).
_GLUED_SECTION_HEADER_RE = re.compile(
    r"(?i)^(.+?)\s+("
    r"RACING\s+CHAMPIONS?|"
    r"STEEPLECHASE\s+RACES?|"
    r"FLAT\s+RACES?|"
    r"(?:CONFORMATION|RACING|AGILITY|OBEDIENCE)\s+DIVISION|"
    r"GO-?TO-?GROUND(?:\s+DIVISION)?|"
    r"WORKING\s+TERRIER(?:\s+DIVISION)?"
    r")\s*$"
)
# Height band glued to place/role with no space: ``12 1/2-15"1st:`` / ``10-12 1/2"Champion:``
# (Do NOT match spaced ``10-12 1/2" Champion:`` — that is the normal single-line form.)
_HEIGHT_GLUED_PLACE_RE = re.compile(
    r'(?i)((?:10\s*-\s*12(?:\s*1/2)?|12(?:\s*1/2)?(?:\s*-\s*15)?)\s*")'
    r'(?=((?:\d+(?:st|nd|rd|th)|champion|reserve|best)\s*:))'
)
_MARKER_RE = re.compile(
    r"(?i)^---\s*(?:page\s+\d+|HEADER|column\s+(?:LEFT|RIGHT)|spread\s+(?:LEFT|RIGHT)|OCR-ENSEMBLE)"
)


def _looks_like_dog_line(s: str) -> bool:
    if not s or _PLACE_ONLY_RE.match(s) or _ENTRIES_ONLY_RE.match(s) or _MARKER_RE.match(s):
        return False
    if _CLASS_HEADER_RE.match(s):
        return False
    if re.search(r"(?i)owned\s+by", s):
        return True
    return bool(re.match(r"^[A-Z\"'‘’+\-]", s)) and not _NUM_ONLY_RE.match(s)


def _looks_like_incomplete_entry(s: str) -> bool:
    """Place/champion line that never got to ``owned by`` (name split onto next line)."""
    if not s or re.search(r"(?i)owned\s+by", s):
        return False
    if _MARKER_RE.match(s) or _ENTRIES_ONLY_RE.match(s) or _PLACE_ONLY_RE.match(s):
        return False
    return bool(
        re.search(
            r"(?i)(?:\d*(?:st|nd|rd|th)|champion|reserve|best)\s*:\s*\S",
            s,
        )
    )


def _looks_like_name_continuation(s: str) -> bool:
    """Continuation of a dog name split mid-token (``Hu`` / ``inter, owned by``)."""
    if not s or _MARKER_RE.match(s) or _PLACE_ONLY_RE.match(s) or _ENTRIES_ONLY_RE.match(s):
        return False
    if _CLASS_HEADER_RE.match(s):
        return False
    if re.match(r"^[a-z]", s):
        return True
    return bool(re.match(r"(?i)^[A-Za-z]{1,12},?\s+owned\s+by\b", s))


def normalize_height_class_ocr(text: str) -> str:
    """Fix common OCR mangling of ``10-12 1/2\"`` / ``12 1/2-15\"`` size bands."""
    if not text:
        return text
    reps = (
        (r'(?i)\b1211215\s*"', '12 1/2-15"'),
        (r"(?i)\b1211215\s*['’]?", '12 1/2-15"'),  # single-quote OCR of "
        (r'(?i)\b12\s*1215\s*"', '12 1/2-15"'),
        (r'(?i)\b12\s*\.\s*1/2\s*-\s*15\s*"', '12 1/2-15"'),
        (r'(?i)\b12\s*4112\s*-?\s*15\s*"?', '12 1/2-15"'),
        (r'(?i)\b12\s*112\s*-?\s*15\s*"', '12 1/2-15"'),
        # 1 misread as 4 in fraction: "12 4/2-15"" / "under 12 4/2""
        (r'(?i)\b12\s*4/2\s*-\s*15\s*"?', '12 1/2-15"'),
        (r'(?i)\b12\s*4/2\s*"', '12 1/2"'),
        (r'(?i)\b12\s*1/2\s*-\s*15\s*"?', '12 1/2-15"'),
        (r'(?i)\b10\s*-\s*12\s*1/2\s*"?', '10-12 1/2"'),
        (r'(?i)\b10\s*-\s*12\s*4/2\s*"?', '10-12 1/2"'),
        # "10-1212"" — missing space/½ (common GTG reserve bleed)
        (r'(?i)\b10\s*-\s*1212\s*"?:?', '10-12 1/2"'),
        (r'(?i)\b10\s*12112\s*"', '10-12 1/2"'),
        (r'(?i)\b10\s*-\s*12\s*112\s*"', '10-12 1/2"'),
        # Truncated cert/class size: "(10-12 1)" / "(10-12 1 –)" → "(10-12 1/2")"
        (r'(?i)\(\s*10\s*-\s*12\s*1\s*[–—−‐‑‒-]?\s*\)', '(10-12 1/2")'),
        (r'(?i)\(\s*10\s*-\s*12\s*1\s*[–—−‐‑‒-]?\s*(?=Entries)', '(10-12 1/2") '),
        (r'(?i)\(\s*10\s*-\s*12\s*1\s*/\s*\)', '(10-12 1/2")'),
        # "1/2"" misread as "%": "10-12% Champion"
        (r'(?i)\b10\s*-\s*12\s*%', '10-12 1/2"'),
        (r'(?i)\b12\s*-\s*15\s*%', '12 1/2-15"'),
        (r'(?i)\b12\s*%\s*-\s*15', '12 1/2-15'),
        # "Working Terrier Dog, 12% - oy" — bare 12% dash (½ misread; 1999–2001)
        (r'(?i)\b12\s*%\s*-', '12 1/2" -'),
        # "12 %--15"" / "12%--15"" — % for 1/2 plus doubled dash (B6b / 1998 Vol III)
        (r'(?i)\b12\s*%\s*-{1,2}\s*15\s*"?', '12 1/2-15"'),
        (r'(?i)\b10\s*-\s*12\s*%\s*-{1,2}', '10-12 1/2"'),
        # Class header: "10 up to 12 %-"" / "10 up to 12%"
        (r'(?i)\b(10\s+up\s+to\s+12)\s*%\s*-?\s*"?', r'\1 1/2"'),
        (r'(?i)\b(10\s+up\s+to\s+12)\s*%', r'\1 1/2"'),
        # "12 %2" / "10-12 2"" / "10-12 12"" / "12 2-15"" — 1/2 → 2 or %2
        (r'(?i)\b12\s*%\s*2\b', '12 1/2'),
        (r'(?i)\b10\s*-\s*12\s+2\s*"?:?', '10-12 1/2"'),
        (r'(?i)\b10\s*-\s*12\s+12\s*"?:?', '10-12 1/2"'),
        (r'(?i)\b12\s+2\s*-\s*15\s*"?:?', '12 1/2-15"'),
        (r'(?i)\b12\s*2\s*-\s*15\s*"?:?', '12 1/2-15"'),
        # Certificate band: ``12 2 up to 15"`` → ``12 1/2 up to 15"``
        (r'(?i)\b12\s+2\s+up\s+to\s+15\s*"?', '12 1/2 up to 15"'),
        (r'(?i)\b12\s+2\s+up\s+to\s+15\b', '12 1/2 up to 15'),

        # Leading 1→4 / 10→40 / 12→42 digit noise on racing/adult heights
        (r'(?i)\b40\s*-\s*12\s*4/2\s*"?:?', '10-12 1/2"'),
        (r'(?i)\b40\s*-\s*12\s*1/2\s*"?:?', '10-12 1/2"'),
        # "40-12. 112"" / "40-12 112"" (1/2 → 112, leading 1→4)
        (r'(?i)\b40\s*-\s*12\s*\.?\s*112\s*"?', '10-12 1/2"'),
        # "40-12.4/2:" / "40-12.4/2"" (1→4 in 10 and in 1/2)
        (r'(?i)\b40\s*-\s*12\s*\.?\s*4/2\s*"?:?', '10-12 1/2"'),
        (r'(?i)\b42\s*112\s*-?\s*15\s*"?', '12 1/2-15"'),
        (r'(?i)\b42\.112\s*-?\s*15\s*"?', '12 1/2-15"'),
        (r'(?i)\b42\s*1/2\s*-\s*15\s*"?', '12 1/2-15"'),
        (r'(?i)\b42\s+1/2\s*-\s*15\s*"?', '12 1/2-15"'),
        # "42112-45"" / "4211245"" → "12 1/2-15"" (1→4 throughout; hyphen often dropped)
        (r'(?i)\b42112\s*-\s*45\s*"?', '12 1/2-15"'),
        (r'(?i)\b4211245\s*"?', '12 1/2-15"'),
        (r'(?i)\b42\s*112\s*-\s*45\s*"?', '12 1/2-15"'),
        (r'(?i)\b40112\s*"?', '10-12 1/2"'),
        # Racing pups: "Under 12.412"" / "Over 12.412"" → "… 12 1/2""
        (r'(?i)\b(Under|Over)\s+12\s*\.\s*412\s*"?', r'\1 12 1/2"'),
        (r'(?i)\b12\s*\.\s*412\s*"?', '12 1/2"'),
        (r'(?i)\b12\s*\.\s*4/2\s*"?', '12 1/2"'),
        # Compact / digit-run heights from racing & GTG banners
        (r'(?i)\b1042112\s*"?:?', '10-12 1/2"'),
        (r'(?i)\b10\s*-\s*2112\s*"?:?', '10-12 1/2"'),
        (r'(?i)\b10\s*-\s*127\s*"?:?', '10-12 1/2"'),
        (r'(?i)\b1012\s*12\s*"?:?', '10-12 1/2"'),
        # Duplicated height crumb: "1012 10-12 1/2"" → "10-12 1/2""
        (r'(?i)\b1012\s+(?=10\s*-\s*12\b)', ''),
        (r'(?i)\b10\s*12\s*12\s*"?:?', '10-12 1/2"'),
        (r'(?i)\b121/215\s*"?:?', '12 1/2-15"'),
        (r'(?i)\b12\s*1/215\s*"?:?', '12 1/2-15"'),
        (r'(?i)\b1212245\s*"?:?', '12 1/2-15"'),
        (r'(?i)\b1211\s*-\s*15\s*"?:?', '12 1/2-15"'),
        (r'(?i)\b12\s*12\s*-\s*15\s*"?:?', '12 1/2-15"'),
        (r'(?i)\b(Under|Over)\s+12\s+112\s*"?:?', r'\1 12 1/2"'),
        (r'(?i)\b12\s+112\s*"?(?=\s*(?:Champion|Reserve)\b)', '12 1/2"'),
        (r'(?i)\b(Under|Over)\s+12\s+12\s*"?:?', r'\1 12 1/2"'),
        (r'(?i)\b12\s+12\s*-\s*15\s*"?:?', '12 1/2-15"'),
        # Age band: "I yr" / "| yr" → "1 yr"
        (r"(?i),\s*I\s*yr\b", ", 1 yr"),
        (r"(?i),\s*\|\s*yr\b", ", 1 yr"),
        (r"(?i)\bI\s*yr\s*&\s*over\b", "1 yr & over"),
        (r"(?i)\|\s*yr\s*&\s*over\b", "1 yr & over"),
        # Cut-off leading 1 on heights: "2 1/2-15"" / "1/2-15"" / "12 1/2: Champion"
        (r'(?m)^2\s*1/2\s*-\s*15\s*"?', '12 1/2-15"'),
        (r'(?m)^1/2\s*-\s*15\s*"?', '12 1/2-15"'),
        (r'(?i)\b12\s*1/2\s*:\s*(?=Champion|Reserve)', '12 1/2" '),
        # Stray colon after height quote: ``10-12 1/2": Champion:`` → ``…" Champion:``
        (r'(?i)(")\s*:\s*(?=Champion|Reserve\b)', r"\1 "),
    )
    for pat, repl in reps:
        text = re.sub(pat, repl, text)
    return text


def normalize_coat_ocr(text: str) -> str:
    """Fix coat abbreviations: ``ribr``/``rlbr`` → ``r/br`` (rough/broken)."""
    if not text:
        return text
    # Standalone coat token after a size/class comma or quote
    text = re.sub(r'(?i)(?<=["\s,])ribr\b', "r/br", text)
    text = re.sub(r'(?i)(?<=["\s,])rlbr\b', "r/br", text)
    text = re.sub(r"(?i)(?<=[\"\s,])rib/?r\b", "r/br", text)
    text = re.sub(r"(?i)(?<=[\"\s,])r\s*/\s*br\b", "r/br", text)
    return text


def normalize_agility_level_ocr(text: str) -> str:
    """Fix Roman-numeral level OCR: ``Agility |, Off Lead`` → ``Agility I, Off Lead``."""
    if not text:
        return text
    # Pipe / broken bar misread of capital I after Agility (optionally Starters/…)
    text = re.sub(
        r"(?i)\b(Agility)\s*[|¦!](?=\s*,)",
        r"\1 I",
        text,
    )
    text = re.sub(
        r"(?i)\b(Agility)\s*[|¦!](?=\s|$)",
        r"\1 I",
        text,
    )
    # "Agility l," / "Agility 1," when clearly a level before Off/On Lead
    text = re.sub(
        r"(?i)\b(Agility)\s+[l1](?=\s*,\s*(?:Off|On)\s+Lead\b)",
        r"\1 I",
        text,
    )
    text = re.sub(
        r"(?i)\b(Agility)\s+ll(?=\s*,)",
        r"\1 II",
        text,
    )
    text = re.sub(
        r"(?i)\b(Agility)\s+lll(?=\s*,)",
        r"\1 III",
        text,
    )
    return text


def _is_judge_name_fragment_garbage(part: str) -> bool:
    """True for unrecoverable judge-list crumbs (``GU\" Uo``, ``Sn``)."""
    p = (part or "").strip()
    if not p:
        return True
    if re.search(r"[\"“”]", p):
        return True
    letters = re.findall(r"[A-Za-z]+", p)
    if not letters:
        return True
    # All crumbs ≤3 letters (Sn / Uo / GU) — not a real surname token
    if all(len(t) <= 3 for t in letters) and sum(len(t) for t in letters) <= 6:
        return True
    # Mostly non-letters
    alnum = sum(1 for c in p if c.isalnum() or c.isspace() or c in ".'-")
    if alnum / max(len(p), 1) < 0.55:
        return True
    return False


def normalize_judges_line_ocr(text: str) -> str:
    """Clean Judges lines from yearbook OCR without inventing names.

    Keeps discipline + recoverable name tokens; drops trailing gutter junk
    after the first garbage fragment. Fixes mid-token capital ``I``
    (``DIed…`` → ``Died…``).
    """
    if not text:
        return text
    out_lines: list[str] = []
    for ln in text.splitlines():
        m = re.match(
            r"(?i)^(Judges\s*:\s*)"
            r"((?:Conformation|Go-?to-?Ground|Racing|Agility|GTG|Obedience"
            r"|Nosework|Barn\s+Hunt|Lure\s+Coursing)[^,\n]*)"
            r"(,\s*)(.*)$",
            ln.strip(),
        )
        if not m:
            out_lines.append(ln)
            continue
        prefix, discipline, sep, rest = m.group(1), m.group(2), m.group(3), m.group(4)
        # Mid-name capital I: DIedKslone → DiedKslone (keep glyphs; don't invent surname)
        rest = re.sub(r"\b([A-Z])I([a-zA-Z]{2,})", r"\1i\2", rest)
        kept: list[str] = []
        for part in re.split(r"\s*,\s*", rest):
            if _is_judge_name_fragment_garbage(part):
                break
            # Title-case ALLCAPS first names: NANCY → Nancy
            tokens = []
            for tok in part.split():
                if tok.isupper() and len(tok) > 1:
                    tokens.append(tok.title())
                else:
                    tokens.append(tok.rstrip("'\""))
            cleaned = " ".join(tokens).strip(" ,'")
            if cleaned:
                kept.append(cleaned)
        if kept:
            out_lines.append(f"{prefix}{discipline}{sep}{', '.join(kept)}")
        else:
            out_lines.append(f"{prefix}{discipline}".rstrip(" ,"))
    return "\n".join(out_lines)


def normalize_cert_entries_glue(text: str) -> str:
    """Fix ``Championship Certificate (12 1/2-15"Entries:`` missing ``)`` / space."""
    if not text:
        return text
    # Trailing dash before close: (12 1/2-15"–) → (12 1/2-15")
    text = re.sub(
        r'(?i)(Championship\s+Certificate\s*\([^)\n]*?)"\s*[–—−‐‑‒-]+\s*\)',
        r'\1")',
        text,
    )
    text = re.sub(
        r'(?i)(Championship\s+Certificate\s*\([^)\n]*?)"\s*Entries\s*:',
        r'\1") Entries:',
        text,
    )
    text = re.sub(
        r'(?i)(Championship\s+Certificate\s*\([^)\n]*?)(?<![)"])\s*Entries\s*:',
        r'\1) Entries:',
        text,
    )
    # Height/class title glued to Entries: ``12 1/2-15"Entries: 7``
    text = re.sub(r'(?i)(")\s*(Entries\s*:)', r"\1 \2", text)
    return text


def _rejoin_broken_results_lines(text: str) -> str:
    """Collapse double-spacing and reattach split place/Entries fragments.

    Some pages (esp. with highlighter / large leading) come back as::

        6th:

        Brandy, owned by …

        Entries:

        23
    """
    if not text:
        return text
    lines = [ln.strip() for ln in text.splitlines() if ln.strip()]
    out: list[str] = []
    i = 0
    n = len(lines)
    while i < n:
        ln = lines[i]
        if _MARKER_RE.match(ln):
            out.append(ln)
            i += 1
            continue

        # Header wrap: "…CHAMPION" / "RESERVE" → "…CHAMPION AND RESERVE"
        # (yearbook titles: BEST … AND RESERVE / … CHAMPION AND RESERVE)
        if i + 1 < n and re.search(r"(?i)\bCHAMPION\s*$", ln):
            nxt = lines[i + 1]
            if re.fullmatch(r"(?i)(?:AND\s+|&\s*)?RESERVE\b", nxt):
                if not re.search(r"(?i)\bAND\s+RESERVE\b|\b&\s*RESERVE\b", ln):
                    ln = f"{ln} AND RESERVE"
                i += 2
                # fall through to other joins with updated ln / or append
                # Re-check marker etc. on combined header — just append
                out.append(ln)
                continue
            if re.fullmatch(r"(?i)AND\s+RESERVE\b.*", nxt) or re.fullmatch(
                r"(?i)&\s*RESERVE\b.*", nxt
            ):
                rest = re.sub(r"(?i)^(?:AND\s+|&\s*)RESERVE\b\s*", "", nxt).strip()
                ln = f"{ln} AND RESERVE" + (f" {rest}" if rest else "")
                out.append(ln)
                i += 2
                continue

        # Mid-name wrap: "…Champion: Hideaway Farms Hu" + "inter, owned by…"
        if (
            i + 1 < n
            and _looks_like_incomplete_entry(ln)
            and _looks_like_name_continuation(lines[i + 1])
        ):
            nxt = lines[i + 1]
            joined = f"{ln}{nxt}" if nxt[:1].islower() else f"{ln} {nxt}"
            out.append(joined)
            i += 2
            continue

        # "owned by Kevin" / "Shannon Osby" (surname alone on next line)
        # Do not rejoin race/division headers split off a prior owner line
        # (``…owned by Alte`` / ``STEEPLECHASE RACES``).
        # Do not invent surnames onto truncated stubs (``owned by Mi`` + ``Carlier``).
        if (
            i + 1 < n
            and re.search(r"(?i)\bowned\s+by\s+[A-Z][a-zA-Z.'\-]+\s*$", ln)
            and re.match(r"^[A-Z][a-zA-Z.'\-]+(?:\s+[A-Z][a-zA-Z.'\-]+)?\s*$", lines[i + 1])
            and not _is_results_section_header(lines[i + 1])
            and not re.match(
                r"(?i)^(?:\d*(?:st|nd|rd|th)|champion|reserve|best|dog|bitch)\b",
                lines[i + 1],
            )
        ):
            m_tail = re.search(r"(?i)\bowned\s+by\s+(.+)$", ln)
            last = (m_tail.group(1).split()[-1] if m_tail else "")
            last_alpha = re.sub(r"[^A-Za-z]", "", last)
            if 0 < len(last_alpha) <= 3:
                out.append(ln)
                i += 1
                continue
            out.append(f"{ln} {lines[i + 1]}")
            i += 2
            continue

        # Owner surname wrap before next place: "…Marchlinsh" / "um   Reserve: …"
        # Do NOT treat "iii"/"ii"/"i" crumbs (Champion header dust) as surnames.
        if i + 1 < n and re.search(r"(?i)\bowned\s+by\b", ln):
            m = re.match(
                r"(?i)^([a-z]{1,6})\s{2,}((?:champion|reserve|\d*(?:st|nd|rd|th))\s*:.*)$",
                lines[i + 1],
            )
            if m and m.group(1).lower() not in {
                "i",
                "ii",
                "iii",
                "iiii",
                "and",
                "the",
                "or",
                "a",
            }:
                out.append(ln + m.group(1))
                out.append(m.group(2))
                i += 2
                continue
            if m and m.group(1).lower() in {"i", "ii", "iii", "iiii"}:
                # Drop the dust token; keep the Champion/Reserve line
                out.append(ln)
                out.append(m.group(2))
                i += 2
                continue

        # Entries: / N
        if _ENTRIES_ONLY_RE.match(ln) and i + 1 < n and _NUM_ONLY_RE.match(lines[i + 1]):
            out.append(f"Entries: {lines[i + 1]}")
            i += 2
            continue

        # Entries: / 1st: / N / Dog…  (count landed between place and name)
        if (
            _ENTRIES_ONLY_RE.match(ln)
            and i + 3 < n
            and _PLACE_ONLY_RE.match(lines[i + 1])
            and _NUM_ONLY_RE.match(lines[i + 2])
            and _looks_like_dog_line(lines[i + 3])
        ):
            out.append(f"Entries: {lines[i + 2]}")
            out.append(f"{lines[i + 1]} {lines[i + 3]}")
            i += 4
            continue

        if _PLACE_ONLY_RE.match(ln):
            # 1st: / N / Dog… with prior bare Entries:
            if (
                i + 2 < n
                and _NUM_ONLY_RE.match(lines[i + 1])
                and _looks_like_dog_line(lines[i + 2])
            ):
                if out and _ENTRIES_ONLY_RE.match(out[-1]):
                    out[-1] = f"Entries: {lines[i + 1]}"
                out.append(f"{ln} {lines[i + 2]}")
                i += 3
                continue
            if i + 1 < n and _looks_like_dog_line(lines[i + 1]):
                out.append(f"{ln} {lines[i + 1]}")
                i += 2
                continue

        out.append(ln)
        i += 1

    # Drop orphan crumbs between complete results lines (Seana / yay)
    cleaned: list[str] = []
    for j, ln in enumerate(out):
        if re.fullmatch(r"[A-Za-z]{2,12}", ln) and not _CLASS_HEADER_RE.match(ln):
            prev = cleaned[-1] if cleaned else ""
            nxt = out[j + 1] if j + 1 < len(out) else ""
            if re.search(r"(?i)\bowned\s+by\b", prev) and re.match(
                r"(?i)^(?:champion|reserve|\d*(?:st|nd|rd|th))\s*:", nxt
            ):
                continue
        cleaned.append(ln)
    return "\n".join(
        _reorder_puppy_championship_block(
            _join_class_header_with_entries(
                _lift_trailing_entries_to_class_header(
                    _reattach_orphan_entry_counts(cleaned)
                )
            )
        )
    )


def _puppy_entry_dog_key(body: str) -> str:
    """Normalize dog name from a place/Champion body for dedupe."""
    name = re.split(r"(?i)\s*,\s*owned\s+by\b", body, maxsplit=1)[0]
    name = re.sub(r"[^a-z0-9]+", " ", name.lower()).strip()
    return name


def _reorder_puppy_championship_block(lines: list[str]) -> list[str]:
    """Restore Puppy Championship to printed yearbook order from OCR lines.

    Results layouts (never invent a header that OCR did not emit):
      A) ``PUPPY CHAMPION & RESERVE`` present → 1st–6th, then that header,
         Champion, Reserve. Champion/Reserve dogs in the OCR are the printed
         1st/2nd when ranks were scrambled or duplicated.
      B) No PCR header → Champion, Reserve, then 3rd–6th (Champion≈1st).
    """
    if not lines:
        return lines
    puppy_re = re.compile(r"(?i)^Puppy\s+Championship\b")
    pcr_header_re = re.compile(
        r"(?i)^PUPPY\s+CHAMPION\b(?:\s*(?:&|AND)\s*RESERVE)?\s*$"
    )
    stop_re = re.compile(
        r"(?i)^(?:Championship\s+Certificate|Dogs?\b|Bitches?\b|Dog\s+Pups|"
        r"Bitch\s+Pups|Novice|Open|Adult|Junior|Child|BEST\b|JRTCA\b|"
        r"Working\s+Terrier|Steeple|RACING|GO-?TO-?GROUND|ADULTS|PUPPIES|"
        r"FLAT\s+RACES|--- )"
    )
    place_re = re.compile(r"(?i)^(\d+)(?:st|nd|rd|th)\s*:\s*(.*)$")
    champ_re = re.compile(r"(?i)^(Champion|Reserve)\s*:\s*(.*)$")
    suffix = {
        1: "st",
        2: "nd",
        3: "rd",
        4: "th",
        5: "th",
        6: "th",
        7: "th",
        8: "th",
        9: "th",
    }

    def _place_line(num: int, body: str) -> str:
        return f"{num}{suffix.get(num, 'th')}: {body.strip()}"

    out: list[str] = []
    i = 0
    n = len(lines)
    while i < n:
        ln = lines[i]
        if not puppy_re.match(ln):
            out.append(ln)
            i += 1
            continue
        out.append(ln)
        i += 1
        block: list[str] = []
        while i < n and not stop_re.match(lines[i]) and not puppy_re.match(lines[i]):
            if _MARKER_RE.match(lines[i]):
                break
            block.append(lines[i])
            i += 1

        champ = reserve = None
        has_pcr_header = False
        place_bodies: dict[int, list[str]] = {}
        other: list[str] = []
        for bl in block:
            s = bl.strip()
            if pcr_header_re.match(s):
                has_pcr_header = True
                continue
            m = champ_re.match(s)
            if m:
                if m.group(1).lower() == "champion":
                    champ = m.group(2).strip()
                else:
                    reserve = m.group(2).strip()
                continue
            m = place_re.match(s)
            if m:
                num = int(m.group(1))
                if 1 <= num <= 9:
                    place_bodies.setdefault(num, []).append(m.group(2).strip())
                else:
                    other.append(bl)
                continue
            other.append(bl)

        champ_key = _puppy_entry_dog_key(champ) if champ else ""
        reserve_key = _puppy_entry_dog_key(reserve) if reserve else ""
        ranked: dict[int, str] = {}
        orphans: list[str] = []
        for num in sorted(place_bodies):
            for body in place_bodies[num]:
                key = _puppy_entry_dog_key(body)
                if key and key in {champ_key, reserve_key}:
                    continue
                if num not in ranked:
                    ranked[num] = body
                else:
                    orphans.append(_place_line(num, body))

        # Layout A: results printed 1st–6th + PUPPY CHAMPION & RESERVE
        if has_pcr_header:
            if champ:
                ranked[1] = champ
            if reserve:
                ranked[2] = reserve
            for num in sorted(ranked):
                out.append(_place_line(num, ranked[num]))
            out.append("PUPPY CHAMPION & RESERVE")
            if champ:
                out.append(f"Champion: {champ}")
            if reserve:
                out.append(f"Reserve: {reserve}")
            out.extend(other)
            out.extend(orphans)
            continue

        # Layout B: results printed Champion, Reserve, 3rd–6th
        if champ or reserve:
            if 1 in ranked and 6 not in ranked:
                body = ranked.pop(1)
                if _puppy_entry_dog_key(body) not in {champ_key, reserve_key}:
                    ranked[6] = body
            if champ:
                out.append(f"Champion: {champ}")
            if reserve:
                out.append(f"Reserve: {reserve}")
            for num in sorted(k for k in ranked if k >= 3):
                out.append(_place_line(num, ranked[num]))
            for num in sorted(k for k in ranked if k < 3):
                out.append(_place_line(num, ranked[num]))
            out.extend(other)
            out.extend(orphans)
            continue

        for num in sorted(ranked):
            out.append(_place_line(num, ranked[num]))
        out.extend(other)
        out.extend(orphans)
    return out



# Adult racing height Champion/Reserve (not Under/Over puppy bands).
_ADULT_HEIGHT_CHAMP_RE = re.compile(
    r'(?i)^(?:10\s*-\s*12(?:\s*1/2)?\s*"?|12(?:\s*1/2)?\s*-\s*15\s*"?)\s*'
    r"(?:Champion|Reserve|Champ)\s*:"
)
_ADULT_RACING_CR_HEADER_RE = re.compile(
    r"(?i)^ADULT\s+RACING\s+CHAMPION(?:\s*(?:&|AND)\s*RESERVE)?\s*$"
)
_PUPPY_RACING_CR_HEADER_RE = re.compile(
    r"(?i)^PUPPY\s+RACING\s+CHAMPION(?:\s*(?:&|AND)\s*RESERVE)?\s*$"
)


def _rehome_orphan_adult_height_champs(lines: list[str]) -> list[str]:
    """Move orphan adult height Champ/Reserve lines under ADULT RACING CR.

    Column OCR often dumps ``10-12 1/2" Champion/Reserve`` / ``12 1/2-15" …``
    under the preceding class (e.g. Veteran) while leaving
    ``PUPPY RACING CHAMPION & RESERVE`` / ``ADULT RACING CHAMPION & RESERVE``
    empty. Keep empty Puppy/Adult headers; create the Adult header if missing.
    """
    if not lines:
        return lines

    adult_idx = next(
        (
            i
            for i, ln in enumerate(lines)
            if _ADULT_RACING_CR_HEADER_RE.match(ln.strip())
        ),
        None,
    )

    orphans: list[str] = []
    orphan_idxs: set[int] = set()
    i = 0
    n = len(lines)
    while i < n:
        if not _ADULT_HEIGHT_CHAMP_RE.match(lines[i].strip()):
            i += 1
            continue
        start = i
        while i < n and _ADULT_HEIGHT_CHAMP_RE.match(lines[i].strip()):
            i += 1
        end = i

        # Already immediately under ADULT (only height lines between)?
        if adult_idx is not None and adult_idx < start:
            between = lines[adult_idx + 1 : start]
            if all(
                (not s.strip()) or _ADULT_HEIGHT_CHAMP_RE.match(s.strip())
                for s in between
            ):
                continue

        # Walk back past height peers; already-homed sections keep their lines.
        already_homed = False
        j = start - 1
        while j >= 0:
            s = lines[j].strip()
            if not s or _ADULT_HEIGHT_CHAMP_RE.match(s):
                j -= 1
                continue
            if _ADULT_RACING_CR_HEADER_RE.match(s):
                already_homed = True
            elif re.match(
                r"(?i)^(?:racing\s+champions?|steeplechase\s+races?|flat\s+races?|"
                r"adults?\b|puppies\b)\b",
                s,
            ):
                # Under RACING CHAMPIONS / ADULTS / PUPPIES — not a mid-class orphan
                already_homed = True
            break
        if already_homed:
            continue

        for k in range(start, end):
            orphans.append(lines[k])
            orphan_idxs.add(k)

    if not orphans:
        return lines

    kept = [ln for idx, ln in enumerate(lines) if idx not in orphan_idxs]
    adult_idx = next(
        (
            i
            for i, ln in enumerate(kept)
            if _ADULT_RACING_CR_HEADER_RE.match(ln.strip())
        ),
        None,
    )
    if adult_idx is None:
        # Prefer an existing RACING CHAMPIONS home over inventing ADULT RACING CR
        racing_idx = next(
            (
                i
                for i, ln in enumerate(kept)
                if re.match(r"(?i)^racing\s+champions?\b", ln.strip())
            ),
            None,
        )
        if racing_idx is not None:
            adult_idx = racing_idx
        else:
            puppy_idx = next(
                (
                    i
                    for i, ln in enumerate(kept)
                    if _PUPPY_RACING_CR_HEADER_RE.match(ln.strip())
                ),
                None,
            )
            insert_at = (puppy_idx + 1) if puppy_idx is not None else len(kept)
            kept.insert(insert_at, "ADULT RACING CHAMPION & RESERVE")
            adult_idx = insert_at

    insert_pos = adult_idx + 1
    while insert_pos < len(kept) and _ADULT_HEIGHT_CHAMP_RE.match(
        kept[insert_pos].strip()
    ):
        insert_pos += 1
    kept[insert_pos:insert_pos] = orphans
    return kept


def _lift_trailing_entries_to_class_header(lines: list[str]) -> list[str]:
    """Move ``Entries: N`` that OCR placed after the last place onto the class header.

    Printed layout is ``Pair Class … Entries: 4`` then places; column OCR often
    emits places first and dumps ``Entries: 4`` at the end of the block.
    """
    if not lines:
        return lines
    entries_only = re.compile(r"(?i)^entries\s*:\s*(\d+)\s*$")
    place_re = re.compile(
        r"(?i)^(?:\d+(?:st|nd|rd|th)|champion|reserve|best)\s*:"
    )
    out = list(lines)
    i = 0
    while i < len(out):
        m = entries_only.match(out[i].strip())
        if not m:
            i += 1
            continue
        j = i - 1
        saw_place = False
        header_idx: int | None = None
        while j >= 0:
            s = out[j].strip()
            if _MARKER_RE.match(s):
                break
            if place_re.match(s) or re.search(r"(?i)\bowned\s+by\b", s):
                saw_place = True
                j -= 1
                continue
            if not s:
                j -= 1
                continue
            if (
                saw_place
                and not re.search(r"(?i)\bentries\s*:", s)
                and not place_re.match(s)
                and not entries_only.match(s)
            ):
                header_idx = j
            break
        if header_idx is not None:
            out[header_idx] = f"{out[header_idx].rstrip()} – Entries: {m.group(1)}"
            del out[i]
            i = header_idx + 1
            continue
        i += 1
    return out


def _join_class_header_with_entries(lines: list[str]) -> list[str]:
    """Fold ``ClassName`` + ``Entries: N`` onto one line for DB parsers.

    ``populate_trialresults_fixed.try_parse_class_with_entries`` ignores a
    standalone ``Entries: N`` line (so it won't wipe the class) but also never
    applies that count to the prior class — so split form stores entries=0.
    """
    if not lines:
        return lines
    out: list[str] = []
    i = 0
    n = len(lines)
    entries_only_num = re.compile(r"(?i)^entries\s*:\s*(\d+)\s*$")
    while i < n:
        ln = lines[i]
        if i + 1 < n and not _MARKER_RE.match(ln):
            m = entries_only_num.match(lines[i + 1])
            if (
                m
                and not re.search(r"(?i)\bentries\s*:", ln)
                and not re.match(
                    r"(?i)^(?:\d+(?:st|nd|rd|th)|champion|reserve|best)\s*:", ln
                )
                and not _ENTRIES_ONLY_RE.match(ln)
            ):
                out.append(f"{ln} – Entries: {m.group(1)}")
                i += 2
                continue
        out.append(ln)
        i += 1
    return out


def _reattach_orphan_entry_counts(lines: list[str]) -> list[str]:
    """Pull a stray entry count back onto a bare ``Entries:`` / header line.

    OCR/column order often yields::

        Entries:
        1st: …
        6th: …
        23
        Open Puppies
    """
    if not lines:
        return lines
    out = list(lines)
    i = 0
    while i < len(out):
        if not _ENTRIES_ONLY_RE.match(out[i]):
            i += 1
            continue
        found: int | None = None
        j = i + 1
        while j < len(out):
            s = out[j]
            if _MARKER_RE.match(s):
                break
            if _NUM_ONLY_RE.match(s):
                found = j
                break
            # Stay inside this class: places / owned-by rows; stop at next class header
            if re.match(
                r"(?i)^(?:\d+(?:st|nd|rd|th)|champion|reserve|best)\s*:", s
            ) or re.search(r"(?i)\bowned\s+by\b", s):
                j += 1
                continue
            if _is_results_section_header(s):
                break
            j += 1
        if found is not None:
            out[i] = f"Entries: {out[found]}"
            del out[found]
        i += 1

    # Second pass: digit-only line after places → prior class header lacking a count
    i = 0
    while i < len(out):
        if not _NUM_ONLY_RE.match(out[i].strip()):
            i += 1
            continue
        try:
            n = int(out[i].strip())
        except ValueError:
            i += 1
            continue
        if n < 1 or n > 40:
            i += 1
            continue
        k = i - 1
        while k >= 0:
            s = out[k].strip()
            if _MARKER_RE.match(s):
                break
            if re.match(
                r"(?i)^(?:\d+(?:st|nd|rd|th)|champion|reserve)\s*:", s
            ) or re.search(r"(?i)\bowned\s+by\b", s):
                k -= 1
                continue
            if _ENTRIES_ONLY_RE.match(s):
                out[k] = f"Entries: {n}"
                del out[i]
                i = k
                break
            if re.search(r"(?i)\bEntries\s*:\s*\d+", s):
                break
            if _is_results_section_header(s) or _looks_like_class_header_line(s):
                if not re.search(r"(?i)\bEntries\s*:", s):
                    out[k] = f"{s}  Entries: {n}"
                    del out[i]
                    i = k
                break
            break
        i += 1
    return out


def _strip_trailing_column_bleed(s: str) -> str:
    """Remove far-right gutter crumbs / next-column bleed after a complete results line.

    Narrower column gutters keep surnames intact but OCR still picks up dust or
    the first glyphs of the opposite column (``…Ellis   weed``, ``Entries: 7  oF``).
    """
    if not s:
        return s
    # Leading column bleed before a class header:
    # ``ah             California Bred … Entries: 11``
    # ``n—            Dog Pups, 6 up to 9 months… Entries: 9``
    s = re.sub(
        r"(?i)^[a-z0-9]{1,4}(?:\s*[–—\-−_./|]+)?\s{2,}"
        r"(?=[A-Z][A-Za-z].{0,120}\bEntries\s*:)",
        "",
        s,
    )
    # Collapse ``Entries:      7`` → ``Entries: 7`` BEFORE crumb stripping.
    # 1998 yearbooks right-align the count; a prior EOL crumb rule that allowed
    # digits was matching the wide gap and deleting the count.
    s = re.sub(r"(?i)\bEntries\s*:\s*(\d+)\b", r"Entries: \1", s)
    # After owner name, drop wide-gap trailing junk / next-column start
    s = re.sub(r"(?i)(\bowned by\b.{3,90}?)(\s{2,}\S.*)$", r"\1", s)
    # Class header ending in Entries: N — keep count, drop rest after a wide gap
    s = re.sub(r"(?i)(\bEntries:\s*\d+)(\s{2,}\S.*)$", r"\1", s)
    # Letters-only EOL crumb (aon/anes/teed). Digits are never crumbs here —
    # they are entry counts (or ages) after a right-aligned gap.
    s = re.sub(r"(?<=\S)\s{3,}[A-Za-z]{1,6}\s*$", "", s)
    # Double commas from highlight/gutter noise
    s = re.sub(r",\s*,+", ",", s)
    return s.rstrip(" ,;")


def _is_ocr_noise_line(s: str) -> bool:
    """Drop unrecoverable header/gutter noise (not place/owner/class lines)."""
    if not s or _MARKER_RE.match(s):
        return False
    # Page# + next-trial bleed: ``39        SWUJRTN Fall Harvest``
    if re.match(
        r"(?i)^\d{1,3}\s{2,}[A-Z0-9].{0,60}\b(?:trial|harvest|classic|specialty)\b",
        s,
    ):
        return True
    # Yearbook folio bleed: ``1997 JRTCA Yearbook, Vol. I – 28`` / ``Vol. | 28``
    if re.match(r"(?i)^\d{4}\s+JRTCA\s+Yearbook\b", s):
        return True
    # Place dust without colon: ``1t Stephens`` / ``t Name`` (mangled 1st:)
    if re.match(r"(?i)^(?:\d?t|[il!|]st)\s+[A-Za-z]", s) and not re.search(
        r"(?i)\b(?:owned\s+by|entries\s*:)\b", s
    ):
        return True
    # Keep real results / role lines (owned-by, champ, class keywords).
    # NOTE: bare ``Bitches/Dogs, 1 yr & older, 10 up to 12…`` must stay even
    # without Entries — short tokens ``yr``/``up``/``to`` otherwise trip the
    # short-token noise ratio and drop the title → false C1 (1998 pt3 Lickity).
    if re.search(
        r"(?i)\b(?:owned\s+by|chairperson|chair\s*:|champion|reserve|"
        r"go-?to-?ground|conformation|novice|open|advanced|starters|"
        r"puppy|puppies|working\s+terrier|"
        r"yearbook|best\s+dog|best\s+bitch|steeple|adults?|pair\s+class|veteran|"
        r"handler|showmanship|pee\s*wee|suitability|spayed|neutered|"
        r"(?:on|off)\s+lead|"
        r"bitches|dogs|pups|older|months?|"
        r"red\s+fox|bronze|silver|gold)\b",
        s,
    ):
        return False
    if re.match(r"(?i)^(?:\d*(?:st|nd|rd|th)|best)\s*:", s):
        return False
    # Entries: keep class headers + bare ``Entries:``; drop owner-crumb + Entries bleed
    # NOTE: ``Suitability To Red Fox Entries: N`` must stay (was false-noise → C1 gap).
    # NOTE: ``Advanced, On Lead Entries: N`` must stay (was false-noise → C1 gap).
    if re.search(r"(?i)\bentries\s*:", s):
        if re.match(r"(?i)^entries\s*:", s):
            return False
        if re.search(
            r"(?i)\b(?:dog|bitch|bitches|dogs|pup|pups|novice|open|advanced|"
            r"starters|adults?|pair|"
            r"family|bred|youth|child|junior|handler|pee\s*wee|showmanship|"
            r"working|veteran|racing|agility|steeple|"
            r"(?:on|off)\s+lead|"
            r"suitability|spayed|neutered|fox|bronze|silver|gold|"
            r"championship|certificate|pre-|gtg|smooth|broken|rough|"
            r"puppies|bitches|dogs)\b",
            s,
        ):
            return False
        return True
    # Leading-lowercase surname/owner crumbs: ``ephenson`` / ``ley & S. Hudson``
    if re.match(r"^[a-z]", s) and not re.match(r"(?i)^(?:under|over)\s+\d", s):
        return True
    # Mangled Judges line (JUQGES / Judges. OV TOU…) — NOT "Junior Handler"
    if re.match(r"(?i)^(?:judges?|juqges|juoces|judcfs)\b", s) and not re.search(
        r"(?i)conformation|go-?to-?ground|ground\s*,|handler", s
    ):
        return True
    tokens = re.findall(r"[A-Za-z]+", s)
    if len(tokens) >= 5:
        short = sum(1 for t in tokens if len(t) <= 2)
        if short / len(tokens) >= 0.55:
            return True
    if len(re.findall(r"(?i)\bee\b", s)) >= 3:
        return True
    # Upside-down / gutter gibberish: "ANQWITIG GNI WUT WIM at"
    caps_words = re.findall(r"\b[A-Z]{3,}\b", s)
    if len(caps_words) >= 3:
        lower_words = re.findall(r"\b[a-z]+\b", s)
        if len(lower_words) <= 2 and not re.search(
            r"(?i)\b(?:best|dog|bitch|pup|reserve|champion|trial|volume|judges?)\b",
            s,
        ):
            return True
    # Mostly punctuation / single-letter crumbs
    if len(s) >= 20 and len(tokens) <= 3 and re.search(r"[)(,./]{3,}", s):
        return True
    # Sparse spaced gibberish: ``oS                         F 5-5``
    if len(s) >= 12 and re.search(r"\s{4,}", s):
        letter_runs = re.findall(r"[A-Za-z]+", s)
        if letter_runs and max(len(t) for t in letter_runs) <= 3:
            return True
    # Short multi-token crumb runs: "eo nr re" / "TTT eee ee"
    if (
        re.fullmatch(r"(?:[A-Za-z]{1,3}\s+){1,3}[A-Za-z]{1,3}", s)
        and not re.search(
            r"(?i)\b(?:dog|bitch|best|open|novice|adults?|pups?|gtg|youth|pair|"
            r"racing|agility|obey|owned|entries|champion|reserve|trial)\b",
            s,
        )
    ):
        return True
    # Short alphabetic crumbs between classes: "oe S" / "Ape"
    if re.fullmatch(r"[A-Za-z]{1,4}(?:\s+[A-Za-z]{1,2})?", s) and not re.fullmatch(
        r"(?i)(?:dog|bitch|best|open|novice|adults?|pups?|gtg|youth|pair|racing|"
        r"agility|obey|rally)",
        s,
    ):
        return True
    return False


def _is_solid_results_line(s: str) -> bool:
    """True for place/champ/class lines that end a real results block."""
    s = (s or "").strip()
    if not s or _MARKER_RE.match(s):
        return False
    if re.search(r"(?i)\bowned\s+by\b", s):
        return True
    if re.match(r"(?i)^(?:\d+(?:st|nd|rd|th)|champion|reserve|best)\s*:", s):
        return True
    if re.match(
        r"(?i)^(?:(?:under|over)\s+)?(?:10\s*-\s*12|12)(?:\s*1/2)?(?:\s*-\s*15)?\s*\"?\s*"
        r"(?:champion|reserve)\s*:",
        s,
    ):
        return True
    if re.match(
        r"(?i)^(?:puppies|adults?|dogs?,?|bitches?,?|racing\s+champions?|"
        r"steeplechase|flat\s+races|novice|open|pups?|"
        r"(?:child|junior|youth|pee\s*wee)\s+handler|handler\b|"
        r"(?:conformation|racing|agility|obedience|go-?to-?ground|working)"
        r"(?:\s+division)?)\b",
        s,
    ):
        return True
    if re.match(r"(?i)^\d{4}\s*:", s):
        return True
    if re.search(r"(?i)\bentries\s*:", s) and not _is_ocr_noise_line(s):
        return True
    return False


def _drop_trailing_gutter_crumbs(lines: list[str]) -> list[str]:
    """Drop surname/Entries/page/next-trial crumb runs after the last solid result.

    Column bleed often dumps truncated owners + ``Entries: N`` + page# + the next
    trial title after the real Champ/Reserve lines. Do not invent surnames — just
    discard the unusable tail. Keep a later trial title only if solid results follow.
    """
    if not lines:
        return lines
    last_solid = -1
    for i, ln in enumerate(lines):
        if _MARKER_RE.match(ln.strip()):
            last_solid = i
            continue
        if _is_solid_results_line(ln):
            last_solid = i
    if last_solid < 0 or last_solid >= len(lines) - 1:
        return lines
    tail = lines[last_solid + 1 :]
    resume: int | None = None
    for j, ln in enumerate(tail):
        if _is_solid_results_line(ln):
            resume = j
            break
        if re.search(r"(?i)\b(?:terrier\s+)?trial\b", ln):
            for k in range(j + 1, min(j + 10, len(tail))):
                if _is_solid_results_line(tail[k]):
                    resume = j
                    break
            if resume is not None:
                break
    if resume is not None:
        return lines[: last_solid + 1] + tail[resume:]
    crumbish = sum(
        1 for ln in tail if _is_ocr_noise_line(ln) or not _is_solid_results_line(ln)
    )
    if crumbish >= max(2, int(len(tail) * 0.6)):
        return lines[: last_solid + 1]
    return lines


def _strip_gutter_noise(text: str) -> str:
    """Drop midpoint OCR junk (underscore/tilde runs, lone glyphs, column bleed)."""
    if not text:
        return text
    out: list[str] = []
    for line in text.splitlines():
        s = line.strip()
        if not s:
            continue  # results are single-spaced; drop blank padding
        # Preserve structural markers used for resume / column assembly
        if _MARKER_RE.match(s):
            out.append(s)
            continue
        if re.fullmatch(r"[\W_]{1,16}", s):
            continue
        # Lone OCR crumbs (t / tn / ee) — not real place/class tokens
        if re.fullmatch(r"[A-Za-z]{1,2}", s):
            continue
        # Height glued to place/role: ``…12 1/2-15"1st:`` → height line + place line
        m_ht = _HEIGHT_GLUED_PLACE_RE.search(s)
        if m_ht:
            head = s[: m_ht.end(1)].rstrip()
            rest = s[m_ht.end(1) :].lstrip()
            if head and rest:
                if not _is_ocr_noise_line(head):
                    out.append(head)
                s = rest
        if _is_ocr_noise_line(s):
            continue
        # Division header + next-column bleed:
        # ``CONFORMATION DIVISION   I   Qed: Davinnuinnd…``
        # ``CONFORMATION DIVISION    : Fanmilv Class   Entricer 0``
        m_div = re.match(
            r"(?i)^((?:Conformation|Go-?to-?Ground|Racing|Agility|Obedience|"
            r"Working(?:\s+Terrier)?|Super\s+Earth)\s+DIVISION)\b(.*)$",
            s,
        )
        if m_div and m_div.group(2).strip():
            rest = m_div.group(2)
            salvage = None
            m_fam = re.search(
                r"(?i)\bFan+m?[il1]lv\s+Class\b|\bFamily\s+Class\b",
                rest,
            )
            m_ent = re.search(r"(?i)\bEntr(?:ies|icer|les)\s*:?\s*(\d+)\b", rest)
            if m_fam:
                salvage = "Family Class"
                if m_ent:
                    salvage = f"Family Class Entries: {m_ent.group(1)}"
            if re.match(r"\s{2,}", rest) or not re.search(
                r"(?i)\b(?:entries|champion|reserve|owned\s+by|"
                r"\d+(?:st|nd|rd|th)|best)\b",
                rest,
            ):
                if salvage:
                    out.append(m_div.group(1))
                    s = salvage
                else:
                    s = m_div.group(1)
        s = re.sub(r"^[\W_]{2,}\s*", "", s)
        s = re.sub(r"\s*[\W_]{2,}$", "", s)
        s = re.sub(r"[~_]{2,}", " ", s)
        # Mid-gutter bleed before a place rank: "posi   1st:" / "7   3rd:" / "sas   Dog"
        s = re.sub(
            r"(?i)^(?:[a-z]{1,5}|\d{1,2})\s{2,}(?=\(?\s*(?:\d*(?:st|nd|rd|th)|[ilI!]st|dst)\b)",
            "",
            s,
        )
        # Leading paren before place: "(4th: …"
        s = re.sub(
            r"(?i)^\(\s*(?=(?:\d*(?:st|nd|rd|th)|best|champion|reserve)\s*:)",
            "",
            s,
        )
        # Leading _ / dash / + dust after place: (also covered in fix_place_rank_ocr)
        s = re.sub(
            r"(?i)^((?:\d+(?:st|nd|rd|th)|best|champion|reserve)\s*:)\s*"
            r"(?:[_\-–—−+!.¡！'\"`]+(?:\s*[_\-–—−+!.¡！'\"`]*)*)\s*",
            r"\1 ",
            s,
        )
        s = re.sub(
            r"(?i)^((?:\d+(?:st|nd|rd|th)|best|champion|reserve)\s*:)\s*\|\s*Am\b",
            r"\1 I Am",
            s,
        )
        s = re.sub(
            r"(?i)^((?:\d+(?:st|nd|rd|th)|best|champion|reserve)\s*:)\s*\|\s+(?=[A-Za-z\"'])",
            r"\1 ",
            s,
        )
        s = re.sub(
            r"(?i)^((?:\d+(?:st|nd|rd|th)|best|champion|reserve)\s*:)\s*\|([a-z])",
            r"\1 I\2",
            s,
        )
        s = re.sub(
            r"(?i)^((?:\d+(?:st|nd|rd|th)|best|champion|reserve)\s*:)\s*\|([A-Z])",
            r"\1 \2",
            s,
        )
        s = re.sub(
            r"(?i)^((?:\d+(?:st|nd|rd|th)|best|champion|reserve)\s*:)\s+I\s+"
            r"(?!Am\b)(?=[A-Z][a-z]{2,})",
            r"\1 ",
            s,
        )
        # Leading stray glyph/token before a class/cert/header/role line:
        # "a    Championship…" / "m=    Dogs…" / "es   Chairperson…"
        # "Bi    Gold Coast Terrier Trial"
        s = re.sub(
            r"(?i)^(?:[a-z]{1,5}=?|[A-Z][a-z]{0,2}|\d{1,2})\s{2,}"
            r"(?=(?:Dog|Bitch|Dogs|Bitches|Novice|Open|Pre-|Puppy|Adult|"
            r"Championship|Steeple|Working|Go-?to|Family|Bred|Youth|"
            r"JRTCA|BEST|CONFORMATION|RACING|Chairperson|Judges|Chair\s*:|"
            r"[A-Z][A-Za-z]*(?:\s+[A-Za-z&.'-]+){0,6}\s+Trial\b|"
            r"\d{2}\s*-))",
            "",
            s,
        )
        s = _strip_trailing_column_bleed(s)
        # Place/owner + next-section header smash:
        # ``…owned by Alte STEEPLECHASE RACES`` → owner line + header line
        m_glue = _GLUED_SECTION_HEADER_RE.match(s.strip())
        if m_glue and (
            re.search(r"(?i)\bowned\s+by\b", m_glue.group(1))
            or re.match(
                r"(?i)^(?:\d*(?:st|nd|rd|th)|best|champion|reserve)\s*:",
                m_glue.group(1).strip(),
            )
        ):
            owner = m_glue.group(1).rstrip(" ,;")
            header = m_glue.group(2).strip()
            if owner:
                out.append(owner)
            if header:
                out.append(header)
            continue
        if s.strip():
            out.append(s.strip())
    rejoined = _rejoin_broken_results_lines("\n".join(out))
    return "\n".join(_drop_trailing_gutter_crumbs(rejoined.splitlines()))


def _ocr_page_best_single(img: Image.Image) -> str:
    """Max-quality ensemble for a single leaf (not a two-up spread)."""
    variants = _preprocess_variants(img)
    mid = next((im for name, im in variants if name == "mid"), variants[0][1])

    # Column reconstruction + forced strips + preprocess/PSM — parallel jobs
    jobs: list[tuple[str, Callable[[], str]]] = [
        ("cols", lambda: _ocr_columns_from_data(mid, conf_min=20)),
        ("strips3", lambda: _ocr_vertical_strips(mid, n_strips=3)),
        ("strips2", lambda: _ocr_vertical_strips(mid, n_strips=2)),
    ]
    # soft/mid: broad PSM coverage; bin: sparse/faint recovery only
    psm_by = {"soft": (3, 4, 6), "mid": (3, 4, 6, 11), "bin": (4, 6, 11)}
    for name, im in variants:
        for psm in psm_by.get(name, (4, 6)):
            jobs.append(
                (f"{name}-psm{psm}", lambda im=im, psm=psm: _tesseract_string(im, psm))
            )

    candidates = _run_ocr_jobs(jobs)
    uniq: list[str] = []
    seen_hash: set[str] = set()
    for t in candidates:
        h = re.sub(r"\s+", " ", t)[:2000]
        if h in seen_hash:
            continue
        seen_hash.add(h)
        uniq.append(t)
    return _merge_ocr_texts(uniq)


def _ocr_leaf_fast(img: Image.Image) -> str:
    """Solid OCR for one leaf after a two-up split (avoid double full-ensemble cost)."""
    variants = _preprocess_variants(img)
    mid = next((im for name, im in variants if name == "mid"), variants[0][1])
    crisp = next((im for name, im in variants if name == "crisp"), mid)
    jobs: list[tuple[str, Callable[[], str]]] = [
        ("cols", lambda: _ocr_columns_from_data(mid, conf_min=20)),
        ("strips2", lambda: _ocr_vertical_strips(mid, n_strips=2)),
    ]
    for label, im in (("mid", mid), ("crisp", crisp)):
        for psm in (4, 6):
            jobs.append(
                (f"{label}-psm{psm}", lambda im=im, psm=psm: _tesseract_string(im, psm))
            )
    candidates = _run_ocr_jobs(jobs)
    if not candidates:
        return ""
    # Trial leaves: vote place tokens across passes before BOD-style merge
    if re.search(r"(?i)\b(?:1|l|I)st\s*:|\b(?:2nd|3rd)\s*:", "\n".join(candidates)):
        text = _reconcile_trial_ocr_candidates(candidates)
    else:
        text = _merge_ocr_texts(candidates)
    # Use original leaf image — preprocess mid often drops Child/Junior Handler.
    return _fill_missing_class_titles(img, text, candidates)


def _ocr_highlight_bands(img: Image.Image) -> str:
    """OCR pink/yellow highlighter line bands separately at high scale.

    Full-column OCR routinely destroys human-highlighted place lines; focused
    band crops + green-channel binarization recover names like
    ``Lickity Split Sassy`` / ``Doug & Sue Tack``.
    """
    try:
        import numpy as np
    except Exception:
        return ""
    rgb = img.convert("RGB")
    arr = np.asarray(rgb).astype(np.float32)
    r, g, b = arr[:, :, 0], arr[:, :, 1], arr[:, :, 2]
    mn = np.minimum(np.minimum(r, g), b)
    mx = np.maximum(np.maximum(r, g), b)
    sat = (mx - mn) / (mx + 1e-3)
    # Loose detect — dark pink markers vary by scanner
    hl = (sat > 0.08) & (mx > 90)
    if float(hl.mean()) < 0.002:
        return ""
    row = hl.mean(axis=1)
    active = row > 0.025
    runs: list[tuple[int, int]] = []
    on = False
    start = 0
    for i, v in enumerate(active):
        if v and not on:
            start = i
            on = True
        elif not v and on:
            runs.append((start, i))
            on = False
    if on:
        runs.append((start, len(active)))
    h = rgb.size[1]
    bands = [(a, b) for a, b in runs if max(8, h // 250) <= (b - a) <= max(90, h // 20)]
    lines: list[str] = []
    for a, b in bands[:50]:
        pad = max(6, (b - a) // 3)
        strip = rgb.crop((0, max(0, a - pad), rgb.size[0], min(h, b + pad)))
        sa = np.asarray(strip).astype(np.float32)
        sg = sa[:, :, 1]
        # Green channel + contrast + bin recovers pink-marker text best (Yankee 2001).
        gc = Image.fromarray(sg.astype(np.uint8), "L")
        gc = ImageOps.autocontrast(gc, cutoff=2)
        candidates_img: list[Image.Image] = []
        for thr in (100, 110, 125):
            binim = gc.point(lambda p, t=thr: 255 if p > t else 0)
            big = binim.resize((binim.size[0] * 3, binim.size[1] * 3), Image.Resampling.LANCZOS)
            big = big.filter(ImageFilter.UnsharpMask(radius=2.0, percent=240, threshold=1))
            candidates_img.append(big)
        # Also despink gray path
        desp = _despink_highlighter(strip)
        desp = ImageOps.autocontrast(desp, cutoff=1)
        desp = desp.resize((desp.size[0] * 3, desp.size[1] * 3), Image.Resampling.LANCZOS)
        candidates_img.append(desp)

        best = ""
        best_score = -1
        for imx in candidates_img:
            for psm in (7, 6):
                try:
                    t = fix_ocr_li_confusion(_tesseract_string(imx, psm))
                except Exception:
                    continue
                flat = " ".join(t.split())
                if len(flat) < 8:
                    continue
                score = (
                    5 * len(re.findall(r"(?i)\bowned\s+by\b", flat))
                    + 3 * len(re.findall(r"(?i)\b(?:1st|2nd|3rd|4th|5th|6th)\b", flat))
                    + 4 * len(re.findall(r"(?i)\b(?:champion|reserve)\b", flat))
                    + (5 if re.search(r"(?i)lickity\s+split\s+sassy", flat) else 0)
                    + (3 if re.search(r"(?i)\bdoug\s*&", flat) else 0)
                    - (6 if re.search(r"(?i)\bdoub\s*&", flat) else 0)
                    - flat.count("|")
                    - len(re.findall(r"[A-Za-z]{18,}", flat))
                )
                if score > best_score:
                    best_score, best = score, flat
        if best and best_score >= 2:
            lines.append(best)
    return "\n".join(lines)


# Any results placement line: optional height/under-over, then place role + body.
# Covers ``1st:``, ``10-12 1/2" Champion:``, ``Under 12 1/2" Reserve:``, etc.
_RESULT_PLACE_LINE_RE = re.compile(
    r"(?i)^("
    r"(?:(?:under|over)\s+12(?:\s*1/2)?\s*\"?\s+)?"
    r"(?:(?:\d{2,6}\s+)?(?:10\s*-\s*12|12)(?:\s*1/2)?(?:\s*-\s*15)?\s*\"?\s+)?"
    r"(?:\d+(?:st|nd|rd|th)|champion|reserve|best)\s*:\s*"
    r")(.*)$"
)


def _split_result_place_line(line: str) -> tuple[str, str] | None:
    """Return ``(prefix_with_colon, body)`` for any place/champ/reserve results line."""
    m = _RESULT_PLACE_LINE_RE.match(line.strip())
    if not m:
        return None
    return m.group(1), m.group(2)


# Second (or later) place/role marker glued into a place-line body.
# Example: ``1st: <garble> 5th: Farmcliff Mint, owned by Bob Franklin``
_INNER_PLACE_RANK_RE = re.compile(
    r"(?i)(?<![A-Za-z0-9/])((?:\d+(?:st|nd|rd|th)|champion|reserve|best)\s*:)"
)


def _ordinal_prefix(n: int) -> str:
    if 10 <= (n % 100) <= 20:
        suf = "th"
    else:
        suf = {1: "st", 2: "nd", 3: "rd"}.get(n % 10, "th")
    return f"{n}{suf}:"


def _split_glued_multi_place_lines(text: str) -> str:
    """Split ``1st: … 5th: Dog, owned by X`` into separate place lines.

    Keeps segments with ``owned by`` (or a clean champ/reserve body). Drops the
    leading garble fragment that often false-arms ``class_header_gap``.
    """
    if not text:
        return text
    out: list[str] = []
    for ln in text.splitlines():
        parts = _split_result_place_line(ln)
        if not parts:
            out.append(ln)
            continue
        prefix, body = parts
        matches = list(_INNER_PLACE_RANK_RE.finditer(body))
        if not matches:
            out.append(ln)
            continue
        segments: list[tuple[str, str]] = [
            (prefix.strip(), body[: matches[0].start()].strip())
        ]
        for i, m in enumerate(matches):
            end = matches[i + 1].start() if i + 1 < len(matches) else len(body)
            segments.append((m.group(1).strip(), body[m.end() : end].strip()))
        kept: list[str] = []
        for pref, bod in segments:
            if not bod:
                continue
            line = norm_space(f"{pref} {bod}")
            if re.search(r"(?i)\bowned\s+by\b", bod):
                kept.append(line)
                continue
            # Champ/reserve without owned-by still structural
            if re.match(r"(?i)^(?:champion|reserve|best)\s*:", pref) and len(bod) >= 3:
                kept.append(line)
                continue
            # Drop garble-only fragments (no owner, mostly OCR mush)
        if kept:
            out.extend(kept)
        else:
            out.append(ln)
    return "\n".join(out)


def _demote_false_first_using_entries(text: str) -> str:
    """When Entries:N has places 1..N-1 then a gap ``1st:``, demote that ``1st``→``Nth``.

    Common OCR: Family Class Entries: 4 with 1st/2nd/3rd then ``1st:`` for the 4th dog.
    """
    if not text:
        return text
    lines = text.splitlines()
    out: list[str] = []
    entries_n: int | None = None
    places_seen: list[int] = []

    def _place_num(s: str) -> int | None:
        m = re.match(r"(?i)^(\d+)(?:st|nd|rd|th)\s*:", s.strip())
        return int(m.group(1)) if m else None

    for ln in lines:
        s = ln.strip()
        if not s:
            out.append(ln)
            continue
        if _MARKER_RE.match(s) or _COLUMN_MARK_RE.match(s):
            entries_n, places_seen = None, []
            out.append(ln)
            continue
        if _looks_like_class_header_line(s) or (
            _SECTIONISH_RE.search(s) and not _PLACE_FIRST_RE.match(s)
        ):
            m = _ENTRIES_COUNT_RE.search(s)
            entries_n = int(m.group(1)) if m else None
            places_seen = []
            out.append(ln)
            continue
        n = _place_num(s)
        if (
            n == 1
            and entries_n
            and entries_n >= 2
            and places_seen
            and sorted(places_seen) == list(range(1, entries_n))
        ):
            s = re.sub(
                r"(?i)^\d+(?:st|nd|rd|th)\s*:",
                _ordinal_prefix(entries_n) + " ",
                s,
                count=1,
            )
            s = norm_space(s)
            n = entries_n
            ln = s
        if n is not None:
            places_seen.append(n)
        out.append(ln)
    return "\n".join(out)


# Place line with next class title smashed onto the owner/name body.
# After leading-Y repair: ``2nd: Carley Galterio Youth Handler Entries: 3``.
_PLACE_EMBEDDED_HEADER_RE = re.compile(
    r"(?i)^("
    r"(?:\d+(?:st|nd|rd|th)|best|champion|reserve)\s*:\s*.+?"
    r")\s+("
    r"(?:Youth|Child|Junior)\s+Handler(?:\s+Class)?|"
    r"(?:Youth|Child|Junior)\s+Handling(?:\s+(?:Go-?to-?Ground|Agility\b[^:\n]*?))?|"
    r"Starters\s+Agility\b[^:\n]*?|"
    r"Agility\s+(?:I{1,3}|[123]|IV)\s*,?\s*(?:On|Off)\s+Lead|"
    r"(?:Novice|Open|Advanced)\s*,?\s*(?:On|Off)\s+Lead"
    r")(\s+Entries\s*:\s*\d+)?\s*$"
)


def _unglue_place_embedded_class_headers(text: str) -> str:
    """Split place+class-header smash; defer headers until the next orphan ``1st:``.

    Yearbook OCR often glues the *next* class title onto the previous class's
    last place (``…Galterio Youth Handler Entries: 3``). Emitting the header
    immediately parks it mid-class; deferring until the next ``1st:`` restores
    the printed order without inventing titles.
    """
    if not text:
        return text
    out: list[str] = []
    pending: list[str] = []

    def _flush_pending() -> None:
        nonlocal pending
        out.extend(pending)
        pending = []

    for ln in text.splitlines():
        s = ln.strip()
        m = _PLACE_EMBEDDED_HEADER_RE.match(s) if s else None
        if m:
            place = norm_space(m.group(1))
            hdr = norm_space(f"{m.group(2)}{m.group(3) or ''}")
            if place and _PLACE_FIRST_RE.match(place):
                _flush_pending()
            if place:
                out.append(place)
            if hdr:
                pending.append(hdr)
            continue
        if s and _PLACE_FIRST_RE.match(s):
            _flush_pending()
            out.append(ln)
            continue
        if s and (
            _COLUMN_MARK_RE.match(s)
            or _MARKER_RE.match(s)
            or _looks_like_class_header_line(s)
            or (_SECTIONISH_RE.search(s) and not _CHAMP_RESERVE_ROLE_RE.match(s))
        ):
            _flush_pending()
            out.append(ln)
            continue
        out.append(ln)
    _flush_pending()
    return "\n".join(out)


def _drop_false_first_between_champ_and_column_reserve(text: str) -> str:
    """Drop bleed ``1st:`` between ``Champion:`` and a column-break ``Reserve:``.

    Pattern: Champion / ``1st: <other class dog>`` / ``--- column … ---`` / Reserve
    — the ``1st`` is almost always a neighboring-class Champion line that lost
    its role prefix. Removing it clears a false C1 without inventing a title.
    """
    if not text:
        return text
    lines = text.splitlines()
    out: list[str] = []
    i = 0
    while i < len(lines):
        s = lines[i].strip()
        if re.match(r"(?i)^champion\s*:", s):
            j = i + 1
            while j < len(lines) and not lines[j].strip():
                j += 1
            if j < len(lines) and _PLACE_FIRST_RE.match(lines[j].strip()):
                k = j + 1
                while k < len(lines) and not lines[k].strip():
                    k += 1
                if k < len(lines) and _COLUMN_MARK_RE.match(lines[k].strip()):
                    m = k + 1
                    while m < len(lines) and not lines[m].strip():
                        m += 1
                    if m < len(lines) and re.match(r"(?i)^reserve\s*:", lines[m].strip()):
                        out.append(lines[i])
                        for t in range(i + 1, j):
                            out.append(lines[t])
                        # skip false 1st at j
                        for t in range(j + 1, k):
                            out.append(lines[t])
                        out.append(lines[k])
                        i = k + 1
                        continue
        out.append(lines[i])
        i += 1
    return "\n".join(out)


def _place_dog_fingerprint(s: str) -> str:
    """Normalize dog-name stem from a place/role body for duplicate detection."""
    body = re.sub(
        r"(?i)^(?:\d+(?:st|nd|rd|th)|champion|reserve|best)\s*:\s*",
        "",
        (s or "").strip(),
    )
    body = re.split(r"(?i),\s*owned\s+by\b", body, maxsplit=1)[0]
    return re.sub(r"[^a-z0-9]+", "", body.lower())


def _drop_false_first_restarting_reserve_dog(text: str) -> str:
    """Drop a false class that restarts with the same dog as the prior ``Reserve:``.

    Pattern: ``Reserve: Katie Clover…`` / ``1st: Katie Clover…`` / ``2nd:…`` —
    OCR replayed High Score Reserve as an orphan class before the real next
    ``1st:``. Drop the duplicate ``1st`` block (non-first places too) until the
    next ``1st:`` / header / marker.
    """
    if not text:
        return text
    lines = text.splitlines()
    out: list[str] = []
    i = 0
    while i < len(lines):
        s = lines[i].strip()
        if re.match(r"(?i)^reserve\s*:", s):
            fp = _place_dog_fingerprint(s)
            j = i + 1
            while j < len(lines) and not lines[j].strip():
                j += 1
            if (
                fp
                and len(fp) >= 6
                and j < len(lines)
                and _PLACE_FIRST_RE.match(lines[j].strip())
                and _place_dog_fingerprint(lines[j]) == fp
            ):
                out.append(lines[i])
                for t in range(i + 1, j):
                    out.append(lines[t])
                # skip false 1st + following non-first places
                k = j + 1
                while k < len(lines):
                    ks = lines[k].strip()
                    if not ks:
                        k += 1
                        continue
                    if _PLACE_NON_FIRST_RE.match(ks):
                        k += 1
                        continue
                    break
                i = k
                continue
        out.append(lines[i])
        i += 1
    return "\n".join(out)


_HIGH_SCORE_HEADER_RE = re.compile(
    r"(?i)^(?:AGILITY|YOUTH|RACING|GTG|GO-?TO-?GROUND|OVERALL)?\s*"
    r"HIGH\s+SCORE\s+CHAMPION(?:\s*(?:&|AND)\s*RESERVE)?\s*$"
)


def _reorder_premature_high_score_roles(text: str) -> str:
    """Move Champion/Reserve that sit above their class to after HIGH SCORE header.

    OCR sometimes emits High Score roles, then the preceding class's ``1st:…6th:``,
    then ``AGILITY HIGH SCORE CHAMPION & RESERVE``. Printed order is class places,
    then the HIGH SCORE header, then Champion/Reserve.
    """
    if not text:
        return text
    lines = text.splitlines()
    out: list[str] = []
    i = 0
    while i < len(lines):
        s = lines[i].strip()
        if not re.match(r"(?i)^champion\s*:", s):
            out.append(lines[i])
            i += 1
            continue
        # Champion + optional Reserve
        role_block = [lines[i]]
        j = i + 1
        while j < len(lines) and not lines[j].strip():
            role_block.append(lines[j])
            j += 1
        if j < len(lines) and re.match(r"(?i)^reserve\s*:", lines[j].strip()):
            role_block.append(lines[j])
            j += 1
            while j < len(lines) and not lines[j].strip():
                role_block.append(lines[j])
                j += 1
        if j >= len(lines) or not _PLACE_FIRST_RE.match(lines[j].strip()):
            out.append(lines[i])
            i += 1
            continue
        # Collect orphan class places until HIGH SCORE header
        place_block: list[str] = []
        k = j
        found_hdr = None
        while k < len(lines):
            ks = lines[k].strip()
            if _HIGH_SCORE_HEADER_RE.match(ks):
                found_hdr = k
                break
            if (
                ks
                and not _PLACE_FIRST_RE.match(ks)
                and not _PLACE_NON_FIRST_RE.match(ks)
                and not _CHAMP_RESERVE_ROLE_RE.match(ks)
                and (
                    _looks_like_class_header_line(ks)
                    or _SECTIONISH_RE.search(ks)
                    or _COLUMN_MARK_RE.match(ks)
                    or _MARKER_RE.match(ks)
                )
            ):
                break
            place_block.append(lines[k])
            k += 1
        if found_hdr is None or not place_block:
            out.append(lines[i])
            i += 1
            continue
        # places → HIGH SCORE header → Champion/Reserve → rest after header
        out.extend(place_block)
        out.append(lines[found_hdr])
        out.extend(role_block)
        i = found_hdr + 1
    return "\n".join(out)


def _lift_class_header_before_orphan_first(text: str) -> str:
    """If a gap ``1st:`` is immediately followed by a class header, lift the header above.

    Pattern: ``… 6th: …`` / ``1st: Dog…`` / ``Championship Certificate… Entries:``
    → header then ``1st:``.

    Also: header appears after 1..N places of the orphan class when
    ``Entries: N`` matches that place count (e.g. ``Advanced, On Lead Entries: 2``
    after ``1st``+``2nd``).
    """
    if not text:
        return text
    lines = text.splitlines()
    out: list[str] = []
    i = 0
    while i < len(lines):
        s = lines[i].strip()
        if not _PLACE_FIRST_RE.match(s):
            out.append(lines[i])
            i += 1
            continue

        prev_place = False
        for k in range(len(out) - 1, -1, -1):
            ps = out[k].strip()
            if not ps:
                continue
            if (
                _PLACE_NON_FIRST_RE.match(ps)
                or _PLACE_FIRST_RE.match(ps)
                or _CHAMP_RESERVE_ROLE_RE.match(ps)
            ):
                prev_place = True
            break

        if not prev_place:
            out.append(lines[i])
            i += 1
            continue

        j = i + 1
        while j < len(lines) and not lines[j].strip():
            j += 1
        if (
            j < len(lines)
            and _looks_like_class_header_line(lines[j].strip())
            and not _PLACE_FIRST_RE.match(lines[j].strip())
            and not _PLACE_NON_FIRST_RE.match(lines[j].strip())
        ):
            out.append(lines[j])
            out.append(lines[i])
            i = j + 1
            continue

        # Delayed header: 1st + non-first places then header with matching Entries
        place_n = 1
        t = i + 1
        lifted = False
        while t < len(lines) and place_n <= 6:
            ts = lines[t].strip()
            if not ts:
                t += 1
                continue
            if _PLACE_NON_FIRST_RE.match(ts):
                place_n += 1
                t += 1
                continue
            if (
                _looks_like_class_header_line(ts)
                and not _PLACE_FIRST_RE.match(ts)
                and not _PLACE_NON_FIRST_RE.match(ts)
            ):
                em = _ENTRIES_COUNT_RE.search(ts)
                if em and int(em.group(1)) == place_n:
                    out.append(lines[t])
                    out.append(lines[i])
                    for u in range(i + 1, t):
                        out.append(lines[u])
                    i = t + 1
                    lifted = True
            break
        if lifted:
            continue

        out.append(lines[i])
        i += 1
    return "\n".join(out)


def _place_line_is_smashed(body: str) -> bool:
    """True when two place/owner results were mashed into one line (column bleed)."""
    if not body:
        return False
    if len(re.findall(r"(?i)\bowned\s+by\b", body)) >= 2:
        return True
    if re.search(r"(?i)\bowned\s*,\s*owned\b", body):
        return True
    if re.search(r"(?i)\bowned\s+by\s+owned\b", body):
        return True
    # "owned by Jennifer by Ken" / "Gayle by Jennings by Steve" (dual+ by-chains)
    if re.search(r"(?i)\bowned\s+by\b.+\bby\b", body):
        return True
    if re.search(r"(?i)\bowned\b.+\bowned\b", body):
        return True
    # Interleaved: "Hunt's owned Comet, by Gayle" (owned mid-dog, bare by)
    if re.search(r"(?i)\b[A-Za-z][A-Za-z'\-]*\s+owned\s+[A-Z]", body) and re.search(
        r"(?i),\s*by\s+[A-Z]", body
    ):
        return True
    # Two kennel-ish name chunks before owned (Farms X, Y, owned) with dual commas
    if re.search(r"(?i),\s*[^,]{2,40},\s*owned\b", body) and re.search(
        r"(?i)\b(?:farms?|hill|oaks?|wood|creek|split)\b.+\b(?:farms?|hill|oaks?|wood|creek|split)\b",
        body,
    ):
        return True
    return False


def _score_clean_place_body(body: str) -> int:
    """Higher = likelier a single ``Dog, owned by Owner`` (no column bleed)."""
    if not body:
        return -1000
    if _place_line_is_smashed(body):
        return -1000
    m = re.match(r"(?i)^(.+?),\s*owned\s+by\s+(.+)$", body.strip())
    if not m:
        return -100
    dog, owner = m.group(1).strip(), m.group(2).strip()
    score = 0
    if re.search(r"(?i)\b(?:owned|by)\b", dog):
        score -= 50
    if "," in dog:
        score -= 15
    dog_toks = [t for t in dog.split() if t]
    if not dog_toks:
        score -= 40
    elif len(dog_toks) > 8:
        score -= 20
    else:
        score += min(len(dog_toks), 5) * 2
    if re.search(r"(?i)\b(?:owned|by)\b", owner):
        score -= 50
    own_toks = [t for t in owner.split() if t]
    if len(own_toks) < 2:
        score -= 12  # bare first name often a smash remnant
    else:
        score += 12
    if "&" in owner:
        score += 8
    if re.fullmatch(r"[A-Z]\.", owner.strip()):
        score -= 30  # orphan initial from "D. by Peck" split
    if re.search(r"\b[A-Z]\.\s*[A-Z][a-z]+\b", owner) and len(own_toks) <= 3:
        score += 10  # clean "D. Peck" / "J. Kozak"
    elif re.search(r"\b[A-Z]\.\s*[A-Z]", owner):
        score += 5
    # Prefer owners that look like people (Titlecase tokens), not mid-garble
    caps = sum(1 for t in own_toks if t[:1].isupper())
    score += min(caps, 4)
    # Very long owner strings are often two interleaved owner lines
    if len(own_toks) > 6:
        score -= 10
    # "Jennifer & J. Scarborough Kozak" — dual surname after & = interleave remnant
    if re.search(r"&\s*[A-Z]\.?\s+[A-Z][a-z]+\s+[A-Z][a-z]+\s*$", owner):
        score -= 15
    return score


def _owner_partition_alts(owner_side: str) -> list[list[str]]:
    """Alternate ways to split a mangled ``by``-chained owner side into owners."""
    parts = [p.strip() for p in re.split(r"(?i)\s+by\s+", owner_side) if p.strip()]
    if not parts:
        return []
    alts: list[list[str]] = [parts]
    # "Gayle by Jennings" → "Gayle Jennings" (spurious by before surname)
    if (
        len(parts) >= 2
        and len(parts[0].split()) == 1
        and len(parts[1].split()) == 1
        and parts[0][-1:] != "."
    ):
        alts.append([f"{parts[0]} {parts[1]}"] + parts[2:])
    # "D. by Peck …" → "D. Peck" + remainder tokens of parts[1]
    if len(parts) >= 2 and re.fullmatch(r"[A-Z]\.", parts[0]):
        rest_toks = parts[1].split()
        if rest_toks:
            merged = [f"{parts[0]} {rest_toks[0]}"]
            tail = " ".join(rest_toks[1:]).strip()
            if tail:
                merged.append(tail)
            merged.extend(parts[2:])
            alts.append(merged)
    # Dedupe while preserving order
    seen: set[tuple[str, ...]] = set()
    out: list[list[str]] = []
    for alt in alts:
        key = tuple(alt)
        if key in seen:
            continue
        seen.add(key)
        out.append(alt)
    return out


def _pair_dog_owner_candidates(
    dog_chunks: list[str], owners: list[str]
) -> list[str]:
    """Build ``dog, owned by owner`` candidates without inventing extra places."""
    cands: list[str] = []
    if not dog_chunks or not owners:
        return cands
    n = min(len(dog_chunks), len(owners))
    # Align from the start and from the end (either column may be more intact)
    for dogs in (dog_chunks[:n], dog_chunks[-n:]):
        for d, o in zip(dogs, owners):
            d, o = d.strip(), o.strip()
            if d and o:
                cands.append(f"{d}, owned by {o}")
    # Single fused dog phrase vs multiple owners: try token bipartitions
    if len(dog_chunks) == 1 and len(owners) >= 2:
        toks = dog_chunks[0].split()
        if len(toks) >= 2:
            cuts = {len(toks) // 2, 1, len(toks) - 1}
            for cut in sorted(cuts):
                if not (0 < cut < len(toks)):
                    continue
                left, right = " ".join(toks[:cut]), " ".join(toks[cut:])
                cands.append(f"{left}, owned by {owners[0]}")
                cands.append(f"{right}, owned by {owners[1]}")
    return cands


def _unsmash_place_body(body: str) -> str:
    """Collapse column-bleed smash to the cleanest single dog + owner.

    Does not emit extra place rows — leftovers without evidence are dropped.
    """
    if not body or not _place_line_is_smashed(body):
        return body
    b = body.strip()
    # Normalize duplicated owned markers (keep trailing space so "Gayle" stays separate)
    b = re.sub(r"(?i)\bowned\s*,\s*owned\s+by\b", "owned by ", b)
    b = re.sub(r"(?i)\bowned\s+by\s+(?:owned\s+)+", "owned by ", b)
    b = re.sub(r"(?i)\bowned\s+by\s+owned\b", "owned by ", b)
    b = re.sub(r"(?i)\bowned\s+by(?=[A-Za-z])", "owned by ", b)
    b = re.sub(r"(?i)([^\s,])\s+owned\s+by\b", r"\1, owned by", b)
    b = re.sub(r"\s{2,}", " ", b).strip()
    if not _place_line_is_smashed(b):
        return b

    cands: list[str] = []

    # Interleave: "South Badger, Hunt's owned Comet, by Gayle owned Jennings by Dan"
    m_int = re.match(
        r"(?i)^(.+?),\s*(.+?)\s+owned\s+(.+?),\s*by\s+(.+?)\s+owned\s+(.+?)\s+by\s+(.+)$",
        b,
    )
    if m_int:
        d1, d2a, d2b, o1a, o1b, o2 = (g.strip() for g in m_int.groups())
        cands.append(f"{d1}, owned by {o1a} {o1b}")
        cands.append(f"{d2a} {d2b}, owned by {o2}")

    # Standard: dog-side, owned by owner-side (possibly by-chained)
    m = re.match(r"(?i)^(.+?),\s*owned\s+by\s+(.+)$", b)
    if m:
        dog_side, owner_side = m.group(1).strip(), m.group(2).strip()
        dog_chunks = [c.strip() for c in dog_side.split(",") if c.strip()]
        for owners in _owner_partition_alts(owner_side):
            cands.extend(_pair_dog_owner_candidates(dog_chunks, owners))
        # If owner side still has a single clean owner after surname-merge only
        for owners in _owner_partition_alts(owner_side):
            if len(owners) == 1 and dog_chunks:
                # Prefer shortest plausible dog chunk (often the intact right column)
                for d in sorted(dog_chunks, key=lambda x: (len(x.split()), len(x))):
                    cands.append(f"{d}, owned by {owners[0]}")

    if not cands:
        return body
    # Keep only non-smashed; pick highest score (stable: first max)
    scored = [( _score_clean_place_body(c), i, c) for i, c in enumerate(cands)]
    scored.sort(reverse=True)
    best_score, _, best = scored[0]
    if best_score < 0:
        # Still better to emit least-bad non-smash if any cleared the detector
        clean = [c for c in cands if not _place_line_is_smashed(c)]
        if not clean:
            return body
        return max(clean, key=_score_clean_place_body)
    return best


def _repair_smashed_place_lines(text: str) -> str:
    """Finalize pass: unsmash column-bleed place/champ lines to one dog+owner."""
    if not text:
        return text
    out: list[str] = []
    for ln in text.splitlines():
        parts = _split_result_place_line(ln)
        if not parts:
            if _place_line_is_smashed(ln):
                out.append(_unsmash_place_body(ln))
            else:
                out.append(ln)
            continue
        prefix, body = parts
        if _place_line_is_smashed(body):
            out.append(prefix + _unsmash_place_body(body))
        else:
            out.append(ln)
    return "\n".join(out)


def _result_line_is_smashed(line: str) -> bool:
    """Smash check for a full results line (any place/champ/reserve form)."""
    parts = _split_result_place_line(line)
    if not parts:
        # Still catch owned-by smash on unlabeled continuation lines
        return _place_line_is_smashed(line)
    return _place_line_is_smashed(parts[1])


def _trial_ocr_score(text: str) -> int:
    """Score trial-results OCR (prefer clean place/owner lines over BOD metrics)."""
    if not text:
        return 0
    score = len(text) // 180
    score += 5 * len(re.findall(r"(?i)\bowned\s+by\b", text))
    score += 4 * len(re.findall(r"(?i)\b(?:1st|2nd|3rd|4th|5th|6th)\s*:", text))
    score += 2 * len(re.findall(r"(?i)\b(?:champion|reserve)\s*:", text))
    score -= 8 * len(re.findall(r"(?i)\bDoub\s*&", text))
    score -= text.count("|") * 2
    # Glued tokens typical of highlighter failure
    score -= len(re.findall(r"[A-Za-z]{20,}", text))
    # Prefer passes without digit-letter garble in names (Sugarbak8r, Wil1)
    score -= 4 * len(re.findall(r"(?i)\b[a-z]*\d[a-z0-9]*\b", text))
    # Prefer passes without place bang / rank dust
    score -= 6 * len(re.findall(r"(?i)\b\d+(?:st|nd|rd|th)\s*:\s*!", text))
    score -= 6 * len(
        re.findall(
            r"(?i)\b(?:\d+(?:st|nd|rd|th)|best|champion|reserve)\s*:\s*\d+(?:st|nd|rd|th)\b",
            text,
        )
    )
    # Column-bleed smash on ANY results line form (1st / height Champion / …)
    for ln in text.splitlines():
        if _result_line_is_smashed(ln):
            score -= 40
    return score


def _inject_highlight_lines(column_text: str, hl_text: str) -> str:
    """Replace mangled column lines with cleaner highlighter-band OCR."""
    if not hl_text.strip():
        return column_text
    lines = column_text.splitlines()
    for raw in hl_text.splitlines():
        hl = norm_space(fix_ocr_li_confusion(raw))
        if len(hl) < 12 or not re.search(r"(?i)owned\s+by", hl):
            continue
        if _result_line_is_smashed(hl):
            continue  # never inject a smashed highlight band
        tokens = set(re.findall(r"[A-Za-z]{4,}", hl.lower()))
        if len(tokens) < 2:
            continue
        best_i, best_score = None, 0
        for i, ln in enumerate(lines):
            lt = set(re.findall(r"[A-Za-z]{4,}", ln.lower()))
            ov = len(tokens & lt)
            if ov < 2:
                continue
            garble = len(re.findall(r"[^A-Za-z0-9\s,.\-&:'\"()/]", ln))
            glued = 1 if re.search(r"[A-Za-z]{18,}", ln) else 0
            missing_owned = 0 if re.search(r"(?i)owned\s+by", ln) else 2
            smash_bonus = 8 if _result_line_is_smashed(ln) else 0
            score = ov * 4 + garble + glued * 3 + missing_owned + smash_bonus
            if score > best_score:
                best_score, best_i = score, i
        if best_i is not None and best_score >= 8:
            lines[best_i] = hl
        else:
            key = re.sub(r"[^a-z0-9]", "", hl.lower())
            existing = {re.sub(r"[^a-z0-9]", "", x.lower()) for x in lines}
            if key not in existing:
                lines.append(hl)
    return "\n".join(lines)


def _ocr_token_vote_key(tok: str) -> str:
    """Bucket tokens that differ only by common stem OCR confusions."""
    # Digits often stand in for letters in Helvetica (8≈e/B, 0≈O, 1≈l/i, 5≈S)
    t = tok.lower()
    for dig, let in (("0", "o"), ("1", "i"), ("5", "s"), ("8", "e"), ("9", "g")):
        t = t.replace(dig, let)
    t = re.sub(r"[^a-z]", "", t)
    if not t:
        return ""
    # l↔i interchangeable for voting; collapse doubles (Eillis/Ellis)
    t = t.replace("l", "i")
    t = re.sub(r"(.)\1+", r"\1", t)
    return t


def _ocr_tokens_same_bucket(a: str, b: str) -> bool:
    """True when tokens are the same word under l/i / doubled-letter noise.

    ``Windly`` vs ``Windy`` → keys ``windiy`` / ``windy`` (edit distance 1).
    """
    ka, kb = _ocr_token_vote_key(a), _ocr_token_vote_key(b)
    if not ka or not kb:
        return False
    if ka == kb:
        return True
    return _levenshtein(ka, kb) <= 1


def _prefer_ocr_token(votes: list[str]) -> str:
    """Majority vote; tie-break toward fewer doubled letters / shorter stem."""
    from collections import Counter

    cleaned = [v for v in votes if v]
    if not cleaned:
        return votes[0] if votes else ""
    counts = Counter(cleaned)
    top = counts.most_common()
    winners = [t for t, n in top if n == top[0][1]]
    if len(winners) == 1:
        return winners[0]

    def _tie_key(t: str) -> tuple:
        digits = len(re.findall(r"\d", t))
        letters = re.sub(r"[^A-Za-z]", "", t)
        doubles = len(re.findall(r"(.)\1", letters.lower()))
        # Prefer no embedded digits (Sugarbak8r), fewer doubles, then shorter
        return (digits, doubles, len(letters), t.lower())

    return sorted(winners, key=_tie_key)[0]


def _result_role_key(prefix: str) -> str:
    """Normalize place-line prefix to a role key for peer matching.

    ``1012 10-12 1/2" Champion:`` and ``10-12 1/2" Champion:`` → ``champion:``
    plus a coarse height band when present.
    """
    p = prefix.lower()
    p = re.sub(r"^\d{3,6}\s+", "", p)
    band = ""
    if re.search(r"10\s*-\s*12|under\s+12", p):
        band = "10-12|"
    elif re.search(r"12\s*1/2\s*-\s*15|over\s+12|12\s*12", p):
        band = "12-15|"
    m = re.search(r"(1st|2nd|3rd|4th|5th|6th|champion|reserve|best)\s*:", p)
    role = m.group(0) if m else p.strip()
    return band + role


def _reconcile_trial_ocr_candidates(candidates: list[str]) -> str:
    """Pick best trial OCR, then vote place-line tokens across the ensemble.

    Fixes cases where the top-scoring pass reads ``Windly`` / ``Eillis`` but
    sibling preprocess/PSM passes already have ``Windy`` / ``Ellis``.
    Covers all result line forms (``1st:``, ``10-12 1/2" Champion:``, …).
    """
    if not candidates:
        return ""
    if len(candidates) == 1:
        return candidates[0]
    primary = max(candidates, key=lambda t: (_trial_ocr_score(t), len(t)))
    others = [c for c in candidates if c is not primary and c != primary]
    if not others:
        return primary
    out_lines: list[str] = []
    for ln in primary.splitlines():
        parts = _split_result_place_line(ln)
        if not parts:
            out_lines.append(ln)
            continue
        prefix, body = parts
        role = _result_role_key(prefix)
        # If primary place line is column-bleed smash, prefer a clean peer line
        if _place_line_is_smashed(body):
            best_clean = None
            best_ov = -1
            p_keys = {_ocr_token_vote_key(t) for t in body.split() if len(t) >= 3}
            for alt in others:
                for aln in alt.splitlines():
                    ap = _split_result_place_line(aln)
                    if not ap or _result_role_key(ap[0]) != role:
                        continue
                    abody = ap[1]
                    if _place_line_is_smashed(abody):
                        continue
                    a_keys = {
                        _ocr_token_vote_key(t) for t in abody.split() if len(t) >= 3
                    }
                    ov = len(p_keys & a_keys)
                    if ov > best_ov:
                        best_ov, best_clean = ov, aln.strip()
            if best_clean is not None and best_ov >= 2:
                out_lines.append(best_clean)
                continue
            # No clean peer — structurally unsmash to one dog+owner
            fixed_body = _unsmash_place_body(body)
            if fixed_body != body and not _place_line_is_smashed(fixed_body):
                out_lines.append(prefix + fixed_body)
                continue
            out_lines.append(ln)
            continue
        primary_toks = body.split()
        if len(primary_toks) < 2:
            out_lines.append(ln)
            continue
        # Collect near-matching place lines from other candidates
        peer_bodies: list[list[str]] = []
        p_keys = {_ocr_token_vote_key(t) for t in primary_toks if len(t) >= 3}
        for alt in others:
            best_toks = None
            best_ov = 0
            for aln in alt.splitlines():
                ap = _split_result_place_line(aln)
                if not ap or _result_role_key(ap[0]) != role:
                    continue
                if _place_line_is_smashed(ap[1]):
                    continue
                atoks = ap[1].split()
                # Reject peers that look like a different dog (length wildly off)
                if abs(len(atoks) - len(primary_toks)) > max(4, len(primary_toks) // 2):
                    continue
                a_keys = {_ocr_token_vote_key(t) for t in atoks if len(t) >= 3}
                ov = len(p_keys & a_keys)
                if ov > best_ov:
                    best_ov, best_toks = ov, atoks
            if best_toks is not None and best_ov >= max(2, len(p_keys) // 3):
                peer_bodies.append(best_toks)
        if not peer_bodies:
            out_lines.append(ln)
            continue
        voted: list[str] = []
        for i, tok in enumerate(primary_toks):
            votes = [tok]
            for peer in peer_bodies:
                if i < len(peer) and _ocr_tokens_same_bucket(peer[i], tok):
                    votes.append(peer[i])
                else:
                    for pt in peer:
                        if _ocr_tokens_same_bucket(pt, tok):
                            votes.append(pt)
                            break
            voted.append(_prefer_ocr_token(votes))
        out_lines.append(prefix + " ".join(voted))
    return "\n".join(out_lines)


def _ocr_single_column(img: Image.Image) -> str:
    """OCR one already-split results column — do NOT re-run column/strip detection.

    Structure baseline: each half is a single vertical list of class headers +
    ``1st: dog, owned by owner`` lines. Re-splitting invents fake gutters and
    scrambles place order (the 1997 quality failure mode).
    """
    variants = _preprocess_variants(img)
    mid = next((im for name, im in variants if name == "mid"), variants[0][1])
    soft = next((im for name, im in variants if name == "soft"), mid)
    crisp = next((im for name, im in variants if name == "crisp"), mid)
    hlbin = next((im for name, im in variants if name == "hlbin"), None)
    # PSM 4 = single column of variable sizes; 6 = uniform block of text.
    jobs: list[tuple[str, Callable[[], str]]] = []
    for label, im in (("mid", mid), ("soft", soft), ("crisp", crisp)):
        for psm in (4, 6):
            jobs.append(
                (f"{label}-psm{psm}", lambda im=im, psm=psm: _tesseract_string(im, psm))
            )
    if hlbin is not None:
        for psm in (4, 6):
            jobs.append(
                (f"hlbin-psm{psm}", lambda psm=psm: _tesseract_string(hlbin, psm))
            )
    hb_box: list[str] = [""]

    def _hb() -> str:
        try:
            hb_box[0] = _ocr_highlight_bands(img) or ""
        except Exception:
            hb_box[0] = ""
        return hb_box[0]

    jobs.append(("highlight_bands", _hb))
    candidates = _run_ocr_jobs(jobs)
    hb = hb_box[0]
    if not candidates:
        return ""
    primary = _reconcile_trial_ocr_candidates(candidates)
    # Original column image — mid preprocess drops Child/Junior Handler boxes.
    primary = _fill_missing_class_titles(img, primary, candidates)
    return _inject_highlight_lines(primary, hb)


def _ocr_header_band(img: Image.Image) -> str:
    """Full-width trial header (title / place / date / chair / judges)."""
    variants = _preprocess_variants(img)
    mid = next((im for name, im in variants if name == "mid"), variants[0][1])
    jobs = [
        (f"hdr-psm{psm}", lambda psm=psm: _tesseract_string(mid, psm))
        for psm in (6, 4)
    ]
    candidates = _run_ocr_jobs(jobs)
    return _merge_ocr_texts(candidates) if candidates else ""


def ocr_page_best(img: Image.Image) -> str:
    """Max-quality OCR. Two-up spreads OR portrait two-column pages are split first.

    Portrait two-column results pages (STRUCTURE_BASELINE):
      1) full-width HEADER band (trial title/date/chair/judges)
      2) BODY split on center vertical rule with wide gutter
      3) each column OCR'd as a single column (no re-split)
    Font assumption: Helvetica Regular / Bold (neo-grotesque).
    """
    configure_tesseract()
    spread = _two_up_halves(img)
    if spread:
        # Parallel left/right leaves (independent ensembles)
        with ThreadPoolExecutor(max_workers=min(2, _ocr_workers())) as ex:
            fl = ex.submit(lambda: _strip_gutter_noise(_ocr_leaf_fast(spread[0])))
            fr = ex.submit(lambda: _strip_gutter_noise(_ocr_leaf_fast(spread[1])))
            left, right = fl.result(), fr.result()
        return (
            "--- spread LEFT ---\n"
            + (left or "").strip()
            + "\n\n--- spread RIGHT ---\n"
            + (right or "").strip()
        )

    x_cut = _two_column_cut_x(img)
    if x_cut is not None:
        w, h = img.size
        gap = _column_gutter_gap(w)

        def _split_cols(src: Image.Image, cut: int) -> tuple[str, str]:
            bw = src.size[0]
            bh = src.size[1]
            left_im = src.crop((0, 0, max(1, cut - gap), bh))
            right_im = src.crop((min(bw - 1, cut + gap), 0, bw, bh))
            with ThreadPoolExecutor(max_workers=min(2, _ocr_workers())) as ex:
                fl = ex.submit(
                    lambda: _strip_gutter_noise(_ocr_single_column(left_im))
                )
                fr = ex.submit(
                    lambda: _strip_gutter_noise(_ocr_single_column(right_im))
                )
                return fl.result(), fr.result()

        header_h = _header_band_height(img)
        header_img = img.crop((0, 0, w, header_h))
        header = _strip_gutter_noise(_ocr_header_band(header_img))
        # Trial-start pages: title/chair/judges, no place ranks.
        # Continuation pages: top band is just more class results — do NOT
        # peel a HEADER (that interleaves both columns' tops). Full-height split.
        is_trial_start = bool(
            header
            and not re.search(
                r"(?i)\b(?:1st|2nd|3rd|4th|5th|6th|7th|8th|9th)\s*[:.]?", header
            )
            and re.search(
                r"(?i)(?:chairperson|judges\s*:|chair\s*:|terrier\s+trial|"
                r"working\s+terrier|go-?to-?ground)",
                header,
            )
        )
        if is_trial_start:
            body = img.crop((0, header_h, w, h))
            body_cut = _two_column_cut_x(body)
            bx = body_cut if body_cut is not None else x_cut
            left_t, right_t = _split_cols(body, bx)
            return (
                "--- HEADER ---\n"
                + (header or "").strip()
                + "\n\n--- column LEFT ---\n"
                + (left_t or "").strip()
                + "\n\n--- column RIGHT ---\n"
                + (right_t or "").strip()
            )

        left_t, right_t = _split_cols(img, x_cut)
        return (
            "--- column LEFT ---\n"
            + (left_t or "").strip()
            + "\n\n--- column RIGHT ---\n"
            + (right_t or "").strip()
        )

    return _ocr_page_best_single(img)


def _year_hint_from_paths(*paths: Path | None) -> int | None:
    """Pull a 19xx/20xx year folder segment from dest/source paths."""
    for path in paths:
        if path is None:
            continue
        for part in Path(path).parts:
            if part.isdigit() and 1980 <= int(part) <= 2035:
                return int(part)
        m = re.search(r"\b(19[8-9]\d|20[0-3]\d)\b", Path(path).as_posix())
        if m:
            return int(m.group(1))
    return None


def ocr_pdf_hq(
    path: Path,
    max_pages: int | None = None,
    force: bool = False,
    dest_path: Path | None = None,
) -> tuple[str, int | None]:
    """Max OCR: ~4x render, multi-preprocess/PSM/column ensemble + fact merge.

    If dest_path is set, write ONLY there (baseline v2) — never touch scan-folder
    sidecars. Otherwise legacy sibling ``*_hqmax.txt`` under the PDF folder.
    """
    global _OCR_LANG, _OCR_TESSDATA_DIR
    configure_tesseract()
    try:
        from yearbook_ocr_fonts import tessdata_dir_for_lang, tesseract_lang_for_year

        yhint = _year_hint_from_paths(dest_path, Path(path))
        _OCR_LANG = tesseract_lang_for_year(yhint)
        _OCR_TESSDATA_DIR = tessdata_dir_for_lang(_OCR_LANG)
        if _OCR_TESSDATA_DIR:
            os.environ["TESSDATA_PREFIX"] = _OCR_TESSDATA_DIR
        else:
            os.environ.pop("TESSDATA_PREFIX", None)
        print(
            f"    OCR lang={_OCR_LANG} year_hint={yhint} "
            f"workers={_ocr_workers()} page_workers={_ocr_page_workers()}",
            flush=True,
        )
    except Exception:
        _OCR_LANG, _OCR_TESSDATA_DIR = "eng", None
        os.environ.pop("TESSDATA_PREFIX", None)
    if dest_path is not None:
        hq = Path(dest_path)
        hq.parent.mkdir(parents=True, exist_ok=True)
    else:
        out = Path(ocr_sibling_path(str(path)))
        hq = out.with_name(out.stem + "_hqmax.txt")
    if hq.is_file() and not force and hq.stat().st_size > 100:
        text = fix_ocr_li_confusion(hq.read_text(encoding="utf-8", errors="ignore"))
        return text, derive_year_from_text(text)

    # Resume support: keep pages already written if force re-run interrupted.
    # Always re-strip gutter bleed on resume — older partial pages may predate
    # trailing-crumb cleanup.
    chunks: list[str] = []
    start_page = 1
    partial = hq.with_name(hq.stem + ".partial.txt")
    if force and partial.is_file() and partial.stat().st_size > 50:
        prev = finalize_results_ocr(
            partial.read_text(encoding="utf-8", errors="ignore")
        )
        for m in re.finditer(r"--- page (\d+) ---", prev):
            start_page = max(start_page, int(m.group(1)) + 1)
        chunks = [prev.rstrip()]
        partial.write_text(prev.rstrip() + "\n", encoding="utf-8")
        print(f"    resume from page {start_page} (gutter-stripped)", flush=True)

    # pdfium scale 4 ≈ 288 DPI; preprocess upscales long edge to ~3400px.
    audit_hits = 0
    audit_path = hq.with_name(hq.stem + ".audit.jsonl")

    def _ocr_one_page(page_no: int, img: Image.Image) -> tuple[int, str, list]:
        print(f"    OCR page {page_no} ({img.size[0]}x{img.size[1]})", flush=True)
        text = finalize_results_ocr(ocr_page_best(img))
        return page_no, text, audit_results_ocr_page(text)

    def _commit_page(page_no: int, text: str, page_hits: list) -> None:
        nonlocal audit_hits
        audit_hits += report_ocr_page_audit(page_no, page_hits)
        if page_hits:
            try:
                import json

                with audit_path.open("a", encoding="utf-8") as af:
                    for code, line in page_hits:
                        af.write(
                            json.dumps(
                                {
                                    "page": page_no,
                                    "code": code,
                                    "line": line,
                                    "source": path.name,
                                },
                                ensure_ascii=False,
                            )
                            + "\n"
                        )
            except Exception:
                pass
        chunks.append(f"--- page {page_no} ---\n{text}".rstrip())
        partial.write_text(
            finalize_results_ocr("\n\n".join(chunks)).rstrip() + "\n", encoding="utf-8"
        )

    page_workers = _ocr_page_workers()
    if page_workers <= 1:
        for page_no, img in render_pdf_pages(
            str(path), max_pages=max_pages, scale=4.0
        ):
            if page_no < start_page:
                continue
            _commit_page(*_ocr_one_page(page_no, img))
    else:
        # Sliding window of page OCR; commit partials in page order.
        pending: dict[int, tuple[str, list]] = {}
        next_write = start_page
        page_iter = (
            (n, im)
            for n, im in render_pdf_pages(str(path), max_pages=max_pages, scale=4.0)
            if n >= start_page
        )
        with ThreadPoolExecutor(max_workers=page_workers) as ex:
            in_flight: dict = {}
            exhausted = False
            while True:
                while not exhausted and len(in_flight) < page_workers:
                    try:
                        page_no, img = next(page_iter)
                    except StopIteration:
                        exhausted = True
                        break
                    in_flight[ex.submit(_ocr_one_page, page_no, img)] = page_no
                if not in_flight:
                    break
                done, _ = wait(in_flight.keys(), return_when=FIRST_COMPLETED)
                for fut in done:
                    page_no, text, hits = fut.result()
                    pending[page_no] = (text, hits)
                    del in_flight[fut]
                while next_write in pending:
                    text, hits = pending.pop(next_write)
                    _commit_page(next_write, text, hits)
                    next_write += 1
    body = finalize_results_ocr("\n\n".join(chunks))
    year = derive_year_from_text(body)
    header = f"Source: {path.name}\nDerivedYear: {year or ''}\nOCR: hqmax\nFontHint: Helvetica\n\n"
    hq.write_text(header + body + "\n", encoding="utf-8")
    if audit_hits:
        print(f"    AUDIT TOTAL residual_hits={audit_hits} log={audit_path.name}", flush=True)
    if partial.is_file():
        try:
            partial.unlink()
        except Exception:
            pass
    return header + body, year


def strip_ensemble_extras(text: str) -> str:
    """Remove OCR-ENSEMBLE-EXTRAS blocks without dropping later pages."""
    return re.sub(
        r"(?is)---\s*OCR-ENSEMBLE-EXTRAS\s*---.*?(?=(?:---\s*page\s+\d+\s*---)|\Z)",
        "\n",
        text,
    )


def extract_sections(text: str) -> dict[str, str]:
    """Map canonical section key -> body until next header."""
    # Drop ensemble extras per page — never truncate later pages
    text = fix_ocr_li_confusion(strip_ensemble_extras(text))
    lines = text.splitlines()
    headers: list[tuple[int, str]] = []
    for i, line in enumerate(lines):
        s = norm_space(line)
        if len(s) < 8 or len(s) > 100:
            continue
        if _END_HEADERS.match(s) or re.search(r"(?i)BREEDER\s+DIRECTORY", s):
            key = re.sub(r"\s+", " ", s.upper())
            headers.append((i, key))
    sections: dict[str, str] = {}
    for hi, (idx, key) in enumerate(headers):
        end = headers[hi + 1][0] if hi + 1 < len(headers) else len(lines)
        body = "\n".join(lines[idx + 1 : end])
        if "OCR-ENSEMBLE" in key:
            continue
        if "BOARD OF DIRECTORS" in key:
            sections["BOARD"] = sections.get("BOARD", "") + "\n" + body
        elif "STATE REPRESENT" in key:
            sections["STATE_REP"] = sections.get("STATE_REP", "") + "\n" + body
        elif "BREEDER DIRECTORY" in key or "DIRECTORY OF BREEDERS" in key:
            continue  # hard stop; do not ingest directory as committee
        elif "REPRESENTATIVES COMMITTEE" in key:
            sections["COMMITTEE:Representatives Committee"] = (
                sections.get("COMMITTEE:Representatives Committee", "") + "\n" + body
            )
        elif "JUDGES COMMITTEE" in key:
            sections["COMMITTEE:Judges Committee"] = (
                sections.get("COMMITTEE:Judges Committee", "") + "\n" + body
            )
        elif "TRIAL COMMITTEE" in key:
            sections["COMMITTEE:Trial Committee"] = (
                sections.get("COMMITTEE:Trial Committee", "") + "\n" + body
            )
        elif "STANDARD" in key and "COMMITTEE" in key:
            sections["COMMITTEE:Standards Committee"] = (
                sections.get("COMMITTEE:Standards Committee", "") + "\n" + body
            )
        elif "BREEDER" in key and "COMMITTEE" in key:
            sections["COMMITTEE:Breeders Committee"] = (
                sections.get("COMMITTEE:Breeders Committee", "") + "\n" + body
            )
    return sections


def parse_state_rep_block(block: str) -> list[Person]:
    people = []
    state_names = {
        "ALABAMA": "AL", "ALASKA": "AK", "ARIZONA": "AZ", "ARKANSAS": "AR",
        "CALIFORNIA": "CA", "COLORADO": "CO", "CONNECTICUT": "CT", "DELAWARE": "DE",
        "FLORIDA": "FL", "GEORGIA": "GA", "HAWAII": "HI", "IDAHO": "ID",
        "ILLINOIS": "IL", "INDIANA": "IN", "IOWA": "IA", "KANSAS": "KS",
        "KENTUCKY": "KY", "LOUISIANA": "LA", "MAINE": "ME", "MARYLAND": "MD",
        "MASSACHUSETTS": "MA", "MICHIGAN": "MI", "MINNESOTA": "MN", "MISSISSIPPI": "MS",
        "MISSOURI": "MO", "MONTANA": "MT", "NEBRASKA": "NE", "NEVADA": "NV",
        "NEW HAMPSHIRE": "NH", "NEW JERSEY": "NJ", "NEW MEXICO": "NM", "NEW YORK": "NY",
        "NORTH CAROLINA": "NC", "NORTH DAKOTA": "ND", "OHIO": "OH", "OKLAHOMA": "OK",
        "OREGON": "OR", "PENNSYLVANIA": "PA", "RHODE ISLAND": "RI",
        "SOUTH CAROLINA": "SC", "SOUTH DAKOTA": "SD", "TENNESSEE": "TN", "TEXAS": "TX",
        "UTAH": "UT", "VERMONT": "VT", "VIRGINIA": "VA", "WASHINGTON": "WA",
        "WEST VIRGINIA": "WV", "WISCONSIN": "WI", "WYOMING": "WY",
    }
    pat = (
        r"\b("
        + "|".join(re.escape(s) for s in sorted(state_names, key=len, reverse=True))
        + r")\b[:\s\-]+([A-Z][A-Za-z'\-]+(?:\s+[A-Z][A-Za-z'\-]+){1,2})"
    )
    for m in re.finditer(pat, block, re.I):
        st = state_names[m.group(1).upper()]
        name = norm_space(m.group(2))
        if not is_human_name(name):
            continue
        p = Person(name=name, role="State Representative", state=st)
        attach_contact(p, block[m.end() : m.end() + 140])
        people.append(p)
    return dedupe_people(people)


def resolve_owner(cur, name: str, state: str | None = None) -> int | None:
    """Match Owner by exact OwnerName, else unique last-name / first-initial."""
    n = norm_space(name)
    if not n:
        return None
    cur.execute(
        "SELECT OwnerID, OwnerName, State FROM sResults.Owner WHERE OwnerName=?",
        n[:255],
    )
    rows = cur.fetchall()
    if len(rows) == 1:
        return int(rows[0][0])
    if len(rows) > 1 and state:
        matched = [r for r in rows if (r[2] or "").upper() == state.upper()]
        if len(matched) == 1:
            return int(matched[0][0])

    parts = n.split()
    if len(parts) < 2:
        return None
    last = parts[-1]
    first_i = parts[0][0].lower()
    cur.execute(
        "SELECT OwnerID, OwnerName, State FROM sResults.Owner WHERE OwnerName LIKE ?",
        f"% {last}",
    )
    cand = []
    nk = name_key(n)
    for oid, oname, ost in cur.fetchall():
        on = (oname or "").strip()
        if name_key(on) == nk:
            cand.append((oid, on, ost))
            continue
        op = on.split()
        if len(op) >= 2 and op[-1].lower() == last.lower() and op[0][:1].lower() == first_i:
            cand.append((oid, on, ost))
    if state:
        st_match = [c for c in cand if (c[2] or "").upper() == state.upper()]
        if len(st_match) == 1:
            return int(st_match[0][0])
    if len(cand) == 1:
        return int(cand[0][0])
    return None


def augment_owner(cur, owner_id: int, p: Person, year: int, label: str) -> None:
    cur.execute(
        """
        UPDATE sResults.Owner
        SET Address=COALESCE(NULLIF(?,''), Address),
            City=COALESCE(NULLIF(?,''), City),
            State=COALESCE(NULLIF(?,''), State),
            PostalCode=COALESCE(NULLIF(?,''), PostalCode),
            Phone=COALESCE(NULLIF(?,''), Phone)
        WHERE OwnerID=?
        """,
        p.address or "",
        p.city or "",
        p.state or "",
        p.postal or "",
        p.phone or "",
        owner_id,
    )
    try:
        note = f"JRTCA {label} ({year})" + (f" — {p.role}" if p.role else "")
        cur.execute("SELECT Notes FROM sResults.Owner WHERE OwnerID=?", owner_id)
        old = cur.fetchone()[0]
        if old and note in old:
            return
        new = (old.rstrip() + "\n" + note)[:4000] if old else note
        cur.execute("UPDATE sResults.Owner SET Notes=? WHERE OwnerID=?", new, owner_id)
    except Exception:
        pass


def next_id(cur, table: str, col: str) -> int:
    cur.execute(f"SELECT ISNULL(MAX([{col}]),0)+1 FROM sResults.[{table}]")
    return int(cur.fetchone()[0])


# Years this reload owns (early Updated Yearbook Scans). Never wipe later years.
WORK_YEARS = list(range(1984, 1991))


def clear_meta_years(cur, years: list[int]) -> None:
    """Delete Board/Committee/StateRep rows only for the years being reloaded."""
    if not years:
        return
    placeholders = ",".join("?" for _ in years)
    for t in ("Board", "Committee", "StateRepresentative"):
        cur.execute(
            f"SELECT COUNT(*) FROM sResults.[{t}] WHERE Year IN ({placeholders})",
            years,
        )
        before = int(cur.fetchone()[0])
        cur.execute(
            f"DELETE FROM sResults.[{t}] WHERE Year IN ({placeholders})",
            years,
        )
        print(f"cleared {t} years={years[0]}-{years[-1]} rows={before}", flush=True)


def upsert_board(cur, year: int, people: list[Person], source: str) -> int:
    n = 0
    for p in people:
        if not is_human_name(p.name):
            continue
        oid = resolve_owner(cur, p.name, p.state)
        p.owner_id = oid
        if oid:
            augment_owner(cur, oid, p, year, "Board")
        cur.execute(
            "SELECT BoardID FROM sResults.Board WHERE Year=? AND MemberName=? AND ISNULL(Role,'')=ISNULL(?, '')",
            year,
            p.name,
            p.role,
        )
        row = cur.fetchone()
        if row:
            cur.execute(
                """
                UPDATE sResults.Board
                SET Address=COALESCE(?,Address), City=COALESCE(?,City), State=COALESCE(?,State),
                    PostalCode=COALESCE(?,PostalCode), Phone=COALESCE(?,Phone),
                    SourcePath=?, OwnerID=COALESCE(?,OwnerID)
                WHERE BoardID=?
                """,
                p.address,
                p.city,
                p.state,
                p.postal,
                p.phone,
                source,
                oid,
                int(row[0]),
            )
        else:
            bid = next_id(cur, "Board", "BoardID")
            cur.execute(
                """
                INSERT INTO sResults.Board
                (BoardID, Year, MemberName, Role, Address, City, State, PostalCode, Phone, SourcePath, OwnerID)
                VALUES (?,?,?,?,?,?,?,?,?,?,?)
                """,
                bid,
                year,
                p.name,
                p.role,
                p.address,
                p.city,
                p.state,
                p.postal,
                p.phone,
                source,
                oid,
            )
        n += 1
    return n


def upsert_committee(cur, year: int, cname: str, people: list[Person], source: str) -> int:
    n = 0
    for p in people:
        if not is_human_name(p.name):
            continue
        oid = resolve_owner(cur, p.name, p.state)
        p.owner_id = oid
        if oid:
            augment_owner(cur, oid, p, year, f"Committee:{cname}")
        cur.execute(
            """
            SELECT CommitteeID FROM sResults.Committee
            WHERE Year=? AND CommitteeName=? AND MemberName=? AND ISNULL(Role,'')=ISNULL(?, '')
            """,
            year,
            cname,
            p.name,
            p.role,
        )
        row = cur.fetchone()
        if row:
            cur.execute(
                """
                UPDATE sResults.Committee
                SET Address=COALESCE(?,Address), City=COALESCE(?,City), State=COALESCE(?,State),
                    PostalCode=COALESCE(?,PostalCode), Phone=COALESCE(?,Phone),
                    SourcePath=?, OwnerID=COALESCE(?,OwnerID)
                WHERE CommitteeID=?
                """,
                p.address,
                p.city,
                p.state,
                p.postal,
                p.phone,
                source,
                oid,
                int(row[0]),
            )
        else:
            cid = next_id(cur, "Committee", "CommitteeID")
            cur.execute(
                """
                INSERT INTO sResults.Committee
                (CommitteeID, Year, CommitteeName, MemberName, Role, Address, City, State, PostalCode, Phone, SourcePath, OwnerID)
                VALUES (?,?,?,?,?,?,?,?,?,?,?,?)
                """,
                cid,
                year,
                cname,
                p.name,
                p.role,
                p.address,
                p.city,
                p.state,
                p.postal,
                p.phone,
                source,
                oid,
            )
        n += 1
    return n


def upsert_state_rep(cur, year: int, people: list[Person], source: str) -> int:
    n = 0
    for p in people:
        if not is_human_name(p.name):
            continue
        oid = resolve_owner(cur, p.name, p.state)
        p.owner_id = oid
        if oid:
            augment_owner(cur, oid, p, year, "State Representative")
        cur.execute(
            """
            SELECT StateRepID FROM sResults.StateRepresentative
            WHERE Year=? AND MemberName=? AND ISNULL(State,'')=ISNULL(?, '')
            """,
            year,
            p.name,
            p.state,
        )
        row = cur.fetchone()
        if row:
            cur.execute(
                """
                UPDATE sResults.StateRepresentative
                SET Address=COALESCE(?,Address), City=COALESCE(?,City),
                    PostalCode=COALESCE(?,PostalCode), Phone=COALESCE(?,Phone),
                    SourcePath=?, OwnerID=COALESCE(?,OwnerID)
                WHERE StateRepID=?
                """,
                p.address,
                p.city,
                p.postal,
                p.phone,
                source,
                oid,
                int(row[0]),
            )
        else:
            sid = next_id(cur, "StateRepresentative", "StateRepID")
            cur.execute(
                """
                INSERT INTO sResults.StateRepresentative
                (StateRepID, Year, State, MemberName, Role, Address, City, PostalCode, Phone, SourcePath, OwnerID)
                VALUES (?,?,?,?,?,?,?,?,?,?,?)
                """,
                sid,
                year,
                p.state,
                p.name,
                p.role,
                p.address,
                p.city,
                p.postal,
                p.phone,
                source,
                oid,
            )
        n += 1
    return n


def early_pdfs() -> list[Path]:
    out = []
    for folder in EARLY:
        d = UPDATED / folder
        if not d.is_dir():
            continue
        for fn in sorted(os.listdir(d)):
            if not fn.lower().endswith(".pdf"):
                continue
            if fn.endswith(".pre_rotate.pdf"):
                continue
            # prefer scan.pdf over timestamped duplicates
            if re.match(r"scan_\d+\.pdf$", fn, re.I):
                continue
            out.append(d / fn)
    return out


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--apply", action="store_true")
    ap.add_argument("--force-ocr", action="store_true")
    ap.add_argument("--max-pages", type=int, default=None)
    args = ap.parse_args()

    cn = pyodbc.connect(CONN, timeout=120)
    cur = cn.cursor()
    cur.execute("SET LOCK_TIMEOUT 30000")
    ensure(cur)
    cn.commit()

    if args.apply:
        clear_meta_years(cur, WORK_YEARS)
        cn.commit()

    totals = {"board": 0, "committee": 0, "state_rep": 0, "owner_linked": 0, "files": 0}
    for path in early_pdfs():
        rel = str(path.relative_to(ROOT))
        print(f"HQ-OCR {rel}", flush=True)
        text, year = ocr_pdf_hq(path, max_pages=args.max_pages, force=args.force_ocr)
        if not year:
            year = derive_year_from_text(text)
        if not year:
            print("  skip no year", flush=True)
            continue
        sections = extract_sections(text)
        print(f"  year={year} sections={list(sections.keys())}", flush=True)

        b_ct = c_ct = s_ct = 0
        linked = 0
        if "BOARD" in sections:
            people = parse_role_anchored(sections["BOARD"])
            print(
                f"  board candidates={len(people)}: "
                f"{[(p.name, p.role, p.city, p.state, p.address) for p in people[:12]]}",
                flush=True,
            )
            if args.apply:
                b_ct = upsert_board(cur, int(year), people, rel)
                linked += sum(1 for p in people if p.owner_id)
            else:
                b_ct = len(people)
                for p in people:
                    p.owner_id = resolve_owner(cur, p.name, p.state)
                    if p.owner_id:
                        linked += 1
        for key, body in sections.items():
            if not key.startswith("COMMITTEE:"):
                continue
            cname = key.split(":", 1)[1]
            people = parse_role_anchored(body)
            print(
                f"  {cname} candidates={len(people)}: "
                f"{[(p.name, p.role, p.city, p.state) for p in people[:8]]}",
                flush=True,
            )
            if args.apply:
                c_ct += upsert_committee(cur, int(year), cname, people, rel)
                linked += sum(1 for p in people if p.owner_id)
            else:
                c_ct += len(people)
                for p in people:
                    p.owner_id = resolve_owner(cur, p.name, p.state)
                    if p.owner_id:
                        linked += 1
        if "STATE_REP" in sections:
            people = parse_state_rep_block(sections["STATE_REP"])
            print(
                f"  state_rep candidates={len(people)}: "
                f"{[(p.name, p.state) for p in people[:12]]}",
                flush=True,
            )
            if args.apply:
                s_ct = upsert_state_rep(cur, int(year), people, rel)
                linked += sum(1 for p in people if p.owner_id)
            else:
                s_ct = len(people)
                for p in people:
                    p.owner_id = resolve_owner(cur, p.name, p.state)
                    if p.owner_id:
                        linked += 1

        totals["files"] += 1
        totals["board"] += b_ct
        totals["committee"] += c_ct
        totals["state_rep"] += s_ct
        totals["owner_linked"] += linked
        if args.apply:
            cn.commit()

    if args.apply:
        cn.commit()
        print("COMMITTED", totals, flush=True)
    else:
        cn.rollback()
        print("DRY-RUN", totals, flush=True)

    for t in ("Board", "Committee", "StateRepresentative"):
        cur.execute(
            f"SELECT COUNT(*), SUM(CASE WHEN OwnerID IS NOT NULL THEN 1 ELSE 0 END), "
            f"MIN(Year), MAX(Year) FROM sResults.[{t}]"
        )
        print(t, cur.fetchone(), flush=True)
        cur.execute(
            f"SELECT TOP 10 MemberName, Role, City, State, OwnerID FROM sResults.[{t}] ORDER BY MemberName"
        )
        print(" ", [tuple(r) for r in cur.fetchall()], flush=True)
    cn.close()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
