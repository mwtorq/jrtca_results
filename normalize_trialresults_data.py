#!/usr/bin/env python3
"""
Normalize DivisionName, ClassName, DogName, and OwnerName in the TrialResults database.

Fixes OCR mangling, standardizes height categories in class names (using division context),
and consolidates similar name variants to the most descriptive canonical form.
"""

import argparse
import os
import re
import subprocess
import sys
import time
from collections import defaultdict
from datetime import datetime

import pyodbc

sys.path.insert(0, __import__('os').path.dirname(__import__('os').path.abspath(__file__)))

from parse_catalog import (
    find_canonical_name_for_similar_names,
    names_are_similar,
    normalize_for_matching,
    normalize_name,
)
from populate_trialresults_fixed import (
    normalize_owned_by_text,
    strip_entries_from_class_name,
    clean_parsed_owner_name,
    canonicalize_height_fragment,
    classify_height_fragment,
    is_truncated_class_fragment,
    normalize_stored_division_name,
    canonicalize_over_under_championship_class,
    canonicalize_gtg_championship_height,
)
from scrape_trial_results_fixed import normalize_class_name, normalize_division_name as _scrape_normalize_division

CONN_STR = (
    "DRIVER={ODBC Driver 17 for SQL Server};"
    "SERVER=localhost\\SQLEXPRESS;"
    "DATABASE=TrialResults;"
    "Trusted_Connection=yes;"
)

ODBC_DRIVERS = [
    "ODBC Driver 17 for SQL Server",
    "ODBC Driver 18 for SQL Server",
    "SQL Server Native Client 11.0",
    "SQL Server",
]

PUPPY_RE = re.compile(r"\b(?:PUP|PUPS|PUPPY|PUPPIES)\b", re.IGNORECASE)
VARIANT_QUOTES = "\u201c\u201d\u2033\u2034\uff02"
INVALID_OWNER_RE = re.compile(
    r"^[\d:$.,\s]+(?:owned\s*by\s*)?",
    re.IGNORECASE,
)
# Racing times leaked into owner fields (e.g. "Jenni Mitchell, owned by 59.04")
RACE_TIME_SUFFIX_RE = re.compile(
    r"^\d{1,2}\.\d{1,2}$|^\d+:\d{2}\.\d+$|^\d+\.\d+$"
)
PLACEMENT_PREFIX_RE = re.compile(
    r"^(?:&\s*)?(?:RESERVE\s*)?(?:\d+(?:st|nd|rd|th)|BEST|CHAMP(?:ION)?|RESERVE)\s*:\s*",
    re.IGNORECASE,
)
SIZE_CHAMPION_PREFIX_RE = re.compile(
    r"^[\d\w\-½%\"'./\s(),·°]+?\s*(?:Champion|Reserve)\s*:\s*",
    re.IGNORECASE,
)


def print_ts(msg: str) -> None:
    print(f"[{datetime.now().strftime('%H:%M:%S')}] {msg}", flush=True)


def normalize_quotes(text: str) -> str:
    """Normalize curly/variant double quotes to ASCII straight quote."""
    if not text:
        return text
    for ch in VARIANT_QUOTES:
        text = text.replace(ch, '"')
    return text


def print_progress(label: str, current: int, total: int, extra: str = "") -> None:
    pct = (100 * current // total) if total else 100
    suffix = f" ({extra})" if extra else ""
    print_ts(f"{label}: {current:,}/{total:,} ({pct}%){suffix}")


def kill_other_normalizer_processes() -> int:
    """Terminate other running copies of this script before starting a new run."""
    if sys.platform != "win32":
        return 0

    my_pid = os.getpid()
    parent_pid = os.getppid()
    ps = (
        "Get-CimInstance Win32_Process | "
        "Where-Object { $_.CommandLine -match 'normalize_trialresults_data' } | "
        f"Where-Object {{ $_.ProcessId -ne {my_pid} -and $_.ProcessId -ne {parent_pid} }} | "
        "ForEach-Object { taskkill /PID $_.ProcessId /F 2>$null; $_.ProcessId }"
    )
    result = subprocess.run(
        ["powershell", "-NoProfile", "-Command", ps],
        capture_output=True,
        text=True,
        check=False,
    )
    killed = [line.strip() for line in result.stdout.splitlines() if line.strip().isdigit()]
    if killed:
        time.sleep(1)
        print_ts(f"Terminated {len(killed)} other normalizer process(es): {', '.join(killed)}")
    return len(killed)


def get_connection():
    for driver in ODBC_DRIVERS:
        try:
            conn_str = CONN_STR.replace("ODBC Driver 17 for SQL Server", driver)
            return pyodbc.connect(conn_str, timeout=30)
        except pyodbc.Error:
            if driver == ODBC_DRIVERS[-1]:
                raise
    return None


def collapse_mc_prefix(text: str) -> str:
    """Prefer McCarthy over Mc Carthy (and MacDonald over Mac Donald)."""
    if not text:
        return text
    return re.sub(r"\b(Mc|Mac)\s+([A-Za-z])", lambda m: m.group(1) + m.group(2), text)


def is_puppy_division(division_name: str | None) -> bool:
    if not division_name:
        return False
    upper = division_name.upper()
    return 'PUPPY' in upper or 'YOUTH' in upper


def division_implies_gtg(division_name: str | None) -> bool:
    if not division_name:
        return False
    upper = division_name.upper()
    return any(
        token in upper
        for token in ('GO-TO-GROUND', 'GTG', 'SUPER EARTH', "MASTER'S DEN", 'SUPER-EARTH')
    )


def division_implies_racing(division_name: str | None) -> bool:
    if not division_name:
        return False
    upper = division_name.upper()
    return any(token in upper for token in ('RACING', 'FLAT RACES', 'STEEPLECHASE', 'HURDLE'))


def is_puppy_context(class_name: str, division_name: str | None = None) -> bool:
    return is_puppy_class(class_name) or is_puppy_division(division_name)


def _repair_division_ocr(part: str) -> str:
    """Fix common OCR/glue errors in division name parts."""
    if not part:
        return part

    part = re.sub(r'\s+', ' ', part.strip())
    part = re.sub(r'[\s.,;:\-]+$', '', part)
    part = re.sub(r'^[\s.,;:\-]+', '', part)
    repairs = [
        (r'(?i)CONFORMATIONDIVISION', 'CONFORMATION DIVISION'),
        (r'(?i)STEEPLECHASERACES', 'STEEPLECHASE RACES'),
        (r'(?i)STEEPLECHASERACE\b', 'STEEPLECHASE RACES'),
        (r'(?i)\bDVISION\b', 'DIVISION'),
        (r'(?i)\bDIVISIO\b', 'DIVISION'),
        (r'(?i)\bDIVISON\b', 'DIVISION'),
        (r'(?i)\bDIVISIION\b', 'DIVISION'),
        (r'(?i)\bTRAILING\s+AND\s+LOCATING\b', 'TRAILING & LOCATING'),
    ]
    for pattern, replacement in repairs:
        part = re.sub(pattern, replacement, part)
    part = re.sub(r'(?i)\b(STEEPLECHASE RACES)\s+1\b', r'\1', part)
    part = re.sub(r'(?i)\b(FLAT RACES)\s+1\b', r'\1', part)
    return part.strip()


def _canonical_division_part(part: str) -> str:
    part = _repair_division_ocr(part)
    if not part:
        return part
    normalized = _scrape_normalize_division(part)
    return normalize_stored_division_name(normalized).strip()


def _division_part_key(part: str) -> str:
    """Alphabetic key for comparing division parts."""
    return re.sub(r'[^A-Z0-9]', '', part.upper())


def _is_redundant_subdivision(main: str, sub: str) -> bool:
    """True when subdivision repeats the main division without adding information."""
    if not sub:
        return True
    main_canon = _canonical_division_part(main)
    sub_canon = _canonical_division_part(sub)
    if main_canon == sub_canon:
        return True
    if _division_part_key(main_canon) == _division_part_key(sub_canon):
        return True
    # CONFORMATION + CONFORMATION DIVISION (or OCR variants thereof)
    if main_canon == 'CONFORMATION' and sub_canon in ('CONFORMATION', 'CONFORMATION DIVISION'):
        return True
    if main_canon == 'RACING DIVISION' and sub_canon == 'RACING DIVISION':
        return True
    return False


def _normalize_division_part(part: str) -> str:
    return _canonical_division_part(part)


def normalize_division_name_full(division_name: str) -> str:
    """Canonicalize division names, including subdivision suffixes."""
    if not division_name:
        return division_name

    division_name = normalize_stored_division_name(division_name.strip())
    if ' - ' not in division_name:
        return _canonical_division_part(division_name)

    main, sub = division_name.split(' - ', 1)
    main_norm = _canonical_division_part(main)
    sub_norm = _canonical_division_part(sub)
    if _is_redundant_subdivision(main_norm, sub_norm):
        return main_norm
    if sub_norm:
        return f'{main_norm} - {sub_norm}'
    return main_norm


def normalize_age_ranges(class_name: str) -> str:
    """Normalize puppy/age range variants like '6-9 months' vs '6 up to 9 month'."""
    if not class_name:
        return class_name

    name = class_name
    age_patterns = [
        (r"\b(\d{1,2})\s*[-–]\s*(\d{1,2})\s*months?\b", r"\1 up to \2 month"),
        (r"\b(\d{1,2})\s+to\s+(\d{1,2})\s*months?\b", r"\1 up to \2 month"),
        (r"\b(\d{1,2})\s+up\s+to\s+(\d{1,2})\s*months?\b", r"\1 up to \2 month"),
        (r"\b(\d{1,2})\s*[-–]\s*(\d{1,2})\s*mos?\b", r"\1 up to \2 month"),
        (r"\b(\d{1,2})\s+to\s+(\d{1,2})\s*mos?\b", r"\1 up to \2 month"),
    ]
    for pattern, replacement in age_patterns:
        name = re.sub(pattern, replacement, name, flags=re.IGNORECASE)

    # OCR: "9 Up to 12½" months" or "9 up 12 months" age phrases
    name = re.sub(
        r"(\d{1,2})\s+Up\s+to\s+12\s*½\s*\"\s*months?\b",
        r"\1 up to 12 month",
        name,
        flags=re.IGNORECASE,
    )
    name = re.sub(
        r"(\d{1,2})\s+up\s+12\s*months?\b",
        r"\1 up to 12 month",
        name,
        flags=re.IGNORECASE,
    )

    return name


def repair_adult_class_ocr(class_name: str) -> str:
    """Repair OCR like 'Bitch Over L year' -> 'Bitches, 1 year and older'."""
    if not class_name:
        return class_name

    name = class_name
    # L/I OCR for digit 1 in age phrase
    name = re.sub(
        r"^(Bitch|Dog)\s+Over\s+(?:L|I|l)\s+year\b",
        lambda m: ("Bitches" if m.group(1).lower() == "bitch" else "Dogs") + ", 1 year and older",
        name,
        flags=re.IGNORECASE,
    )
    name = re.sub(
        r"^(Bitch|Dog)\s+Over\s+1\s+year\b",
        lambda m: ("Bitches" if m.group(1).lower() == "bitch" else "Dogs") + ", 1 year and older",
        name,
        flags=re.IGNORECASE,
    )
    return name


def repair_misclassified_class_name(class_name: str) -> str:
    """Salvage class names that are actually placements, heights, or glued champion rows."""
    if not class_name:
        return class_name

    name = class_name.strip()
    name = re.sub(r'^\\+', '', name)

    # Page/catalog artifacts: ": 10", bare punctuation
    if re.match(r'^:\s*\d+\s*$', name):
        return ''
    if re.match(r'^[\d"\')\s\\.:;~\-]+$', name):
        return ''

    # Owner fragment stored as class
    if re.match(r'^&\s', name):
        return ''

    # Truncated dog/bitch/pup header fragment (e.g. "Dog, s" from split "Dogs, ...")
    if is_truncated_class_fragment(name):
        return ''

    # Placement line mis-stored as class; extract embedded class if present
    ord_m = re.match(
        r"^\d{1,2}\s*[a-z]{0,4}\s*[:'~\s]+\s*(.+)$",
        name,
        re.IGNORECASE,
    )
    if ord_m:
        rest = ord_m.group(1).strip()
        if re.search(r'\b(?:Dog Pups|Bitch Pups|Dogs|Bitches)\b', rest, re.IGNORECASE):
            rest = re.sub(
                r'^(Dog Pups|Bitch Pups|Dogs|Bitches)\s+(\d)',
                r'\1, \2',
                rest,
                flags=re.IGNORECASE,
            )
            return rest
        return ''

    # Height + glued champion/dog row
    champ_m = re.match(r'^(.+?)\s*[":]\s*Champion\s*:', name, re.IGNORECASE)
    if champ_m:
        name = champ_m.group(1).strip()

    # Bare height stored as class (parenthetical height suffix is redundant)
    if re.match(
        r'^10\s*"\s*up\s+to\s+12\s*½\s*"\s*\([^)]+\)\s*$',
        name,
        re.IGNORECASE,
    ):
        name = re.sub(r'\s*\([^)]+\)\s*$', '', name, flags=re.IGNORECASE)

    # OCR height garbage
    name = re.sub(
        r'12\s*1[KkZz]\s*[-–]?\s*1\s*5\s*["\']*',
        'Over 12½" up to 15"',
        name,
        flags=re.IGNORECASE,
    )
    name = re.sub(
        r'\b12\s*[1KZ]\s*[-–]\s*15\s*["\']*',
        'Over 12½" up to 15"',
        name,
        flags=re.IGNORECASE,
    )
    name = re.sub(r'\b12\s*Yz\s*[-–]\s*15\b', 'Over 12½" up to 15"', name, re.IGNORECASE)
    name = re.sub(r'\bGhampion\b', 'Champion', name, flags=re.IGNORECASE)
    name = re.sub(r'\bNRESERVE\b', 'RESERVE', name, flags=re.IGNORECASE)
    name = re.sub(r'(?<!1)/2\'?\s*', ' ', name)
    name = re.sub(r'¼"\s*', '', name)
    name = re.sub(r'10\s*"\s*up\s+to\s+12\s*½\s*"\s*1\s*"+', '10" up to 12½"', name, flags=re.IGNORECASE)
    name = re.sub(r'GO·TO·GROUND', 'GO-TO-GROUND', name, flags=re.IGNORECASE)

    # Canonicalize parenthetical height fragments
    paren_m = re.match(r'^(.*)\(([^)]+)\)\s*$', name)
    if paren_m and classify_height_fragment(paren_m.group(2)):
        name = f"{paren_m.group(1).strip()} ({canonicalize_height_fragment(paren_m.group(2), is_puppy_class(name))})"

    # Strip trailing dog/owner garbage after height paren
    name = re.sub(r'\s*\(\d[^)]*owned[^)]*\)\s*$', '', name, flags=re.IGNORECASE)

    return name.strip()


def _is_age_qualifier(part: str) -> bool:
    """True for puppy/adult age phrases like '6 up to 12 month' — not height categories."""
    if re.search(r'\b\d+\s+up\s+to\s+\d+\s*months?\b', part, re.IGNORECASE):
        return True
    if re.search(r'\b\d+\s+Up to 12.*months?\b', part, re.IGNORECASE):
        return True
    return False


_AGE_QUALIFIER_MASK_RE = re.compile(
    r'\b\d+\s+up\s+to\s+\d+\s*months?\b',
    re.IGNORECASE,
)


def _mask_age_qualifiers(name: str) -> tuple[str, list[str]]:
    """Temporarily mask age phrases so height rules do not corrupt them."""
    placeholders: list[str] = []

    def _mask(m: re.Match) -> str:
        placeholders.append(m.group(0))
        return f"\x00AGE{len(placeholders) - 1}\x00"

    return _AGE_QUALIFIER_MASK_RE.sub(_mask, name), placeholders


def _unmask_age_qualifiers(name: str, placeholders: list[str]) -> str:
    for i, orig in enumerate(placeholders):
        name = name.replace(f"\x00AGE{i}\x00", orig)
    return name


def repair_corrupted_age_height_glue(class_name: str) -> str:
    """Repair age phrase corrupted by height normalization (e.g. '6 Up to 12½"months')."""
    if not class_name:
        return class_name
    return re.sub(
        r'(\d+)\s+Up to 12\s*½\s*"\s*months?\b',
        r'\1 up to 12 month',
        class_name,
        flags=re.IGNORECASE,
    )


def repair_height_slash_quote_garbage(class_name: str) -> str:
    """Strip OCR slash-quote garbage after canonical height phrases."""
    if not class_name:
        return class_name
    name = class_name
    name = re.sub(
        r'(10\s*"\s*up\s+to\s+12\s*½\s*")[/",\'\s]+',
        r'\1',
        name,
        flags=re.IGNORECASE,
    )
    name = re.sub(
        r'(Up\s+to\s+12\s*½\s*")[/",\'\s]+',
        r'\1',
        name,
        flags=re.IGNORECASE,
    )
    name = re.sub(
        r'(10\s*"\s*up\s+to\s+12\s*½\s*")\s*1\s*"+',
        r'\1',
        name,
        flags=re.IGNORECASE,
    )
    name = re.sub(
        r'(12\s*½\s*")\s*1\s*"+',
        r'\1',
        name,
        flags=re.IGNORECASE,
    )
    return name


def repair_duplicate_over_height(class_name: str) -> str:
    """Collapse duplicated OCR + canonical over-15 height phrases."""
    if not class_name:
        return class_name
    name = re.sub(
        r'Over\s+12\s*[/\'"\d.,·°\s]+\s*,\s*Over\s+12\s*½\s*"\s*up\s+to\s+15\s*"',
        'Over 12½" up to 15"',
        class_name,
        flags=re.IGNORECASE,
    )
    canon = r'Over\s+12\s*½\s*"\s*up\s+to\s+15\s*"'
    name = re.sub(rf'({canon})(?:\s*,\s*|\s+)\1+', r'\1', name, flags=re.IGNORECASE)
    return name


def repair_trailing_height_fragment(class_name: str) -> str:
    """Canonicalize OCR height suffix on regular (non-championship) class names."""
    if not class_name:
        return class_name
    if re.search(r'CHAMPION\s*(?:&|AND)\s*RESERVE|HIGH\s+POINT\s+CHAMPION', class_name, re.IGNORECASE):
        return class_name

    name = class_name
    puppy = is_puppy_class(name)
    name = repair_corrupted_age_height_glue(name)

    coat_suffix = ''
    coat_m = re.search(r'(,\s*(?:smooth|rough/broken))\s*$', name, re.IGNORECASE)
    if coat_m:
        coat_suffix = coat_m.group(1)
        name = name[: coat_m.start()]

    name = repair_duplicate_over_height(name)

    if ',' in name:
        parts = [p.strip() for p in name.split(',')]
        fixed_parts = []
        changed = False
        for part in parts:
            if classify_height_fragment(part) and not _is_age_qualifier(part):
                canon = canonicalize_height_fragment(part, puppy=puppy)
                if fixed_parts and fixed_parts[-1] == canon:
                    changed = True
                    continue
                fixed_parts.append(canon)
                if canon != part:
                    changed = True
            else:
                fixed_parts.append(part)
        if changed:
            name = ', '.join(fixed_parts)

    name = repair_duplicate_over_height(name)
    name = repair_duplicate_up_to_12(name)
    name = repair_height_slash_quote_garbage(name)
    return f"{name}{coat_suffix}" if coat_suffix else name


def normalize_championship_parenthetical(class_name: str, division_name: str | None = None) -> str:
    """Canonicalize OCR height in championship class parentheticals."""
    if not class_name:
        return class_name

    name = re.sub(r'GO·TO·GROUND', 'GO-TO-GROUND', class_name, flags=re.IGNORECASE)
    if not re.search(r'CHAMPION\s*(?:&|AND)\s*RESERVE|HIGH\s+POINT\s+CHAMPION', name, re.IGNORECASE):
        return name

    m = re.match(r'^(.*)\(([^)]+)\)\s*$', name.strip())
    if not m:
        return name

    base, frag = m.group(1).strip(), m.group(2).strip()
    # Strip trailing slash-quote garbage inside parens: 10" up to 12½"/"
    frag = re.sub(r'/["\']+\s*$', '', frag)
    puppy = is_puppy_context(name, division_name)
    if classify_height_fragment(frag):
        canon = canonicalize_height_fragment(frag, puppy=puppy)
        if division_implies_gtg(division_name) and not puppy and canon == 'Up to 12½"':
            canon = '10" up to 12½"'
        return f"{base} ({canon})"
    return name


def repair_duplicate_up_to_12(class_name: str) -> str:
    """Collapse duplicated 'Up to 12½"' phrases."""
    if not class_name:
        return class_name
    canon = r'Up\s+to\s+12\s*½\s*"'
    name = class_name
    prev = None
    while name != prev:
        prev = name
        name = re.sub(
            rf'({canon})(?:(?:\s*,\s*|\s*){canon})+',
            r'\1',
            name,
            flags=re.IGNORECASE,
        )
    return name


def repair_leading_height_championship(
    class_name: str,
    division_name: str | None = None,
) -> str:
    """Move leading height prefix before championship class name into parenthetical."""
    if not class_name:
        return class_name
    if not re.search(
        r'CHAMPION\s*(?:&|AND)\s*RESERVE|HIGH\s+POINT\s+CHAMPION|HIGH[\s-]*SCORE\s+CHAMPION',
        class_name,
        re.IGNORECASE,
    ):
        return class_name

    m = re.match(
        r'^(?P<height>'
        r'10[\s.\-]+12\s*(?:½|1\s*/\s*2|1)?\s*"|'
        r'10[\s.\-]+12\s*(?:½|1\s*/\s*2)?(?=\s)|'
        r'10\s*"\s*up\s+to\s+12\s*½\s*"|'
        r'Up\s+to\s+12\s*½\s*"|'
        r'Over\s+12\s*½\s*"\s*up\s+to\s+15\s*"|'
        r'12\s*½\s*[-–]\s*15\s*"|'
        r'12\s*1\s*/\s*2\s*[-–]\s*15\s*"'
        r')\s+(?P<base>.+)$',
        class_name.strip(),
        re.IGNORECASE,
    )
    if not m:
        return class_name

    height_frag = m.group('height').strip()
    base = m.group('base').strip()
    if not classify_height_fragment(height_frag):
        return class_name

    puppy = is_puppy_context(base, division_name)
    canon = canonicalize_height_fragment(height_frag, puppy=puppy)
    if (
        re.search(r'GO-TO-GROUND', base, re.IGNORECASE) or division_implies_gtg(division_name)
    ) and not puppy and canon == 'Up to 12½"':
        canon = '10" up to 12½"'
    return f'{base} ({canon})'


def normalize_championship_class(class_name: str, division_name: str | None = None) -> str:
    """Normalize championship class names (racing, GTG, agility) with height suffixes."""
    if not class_name:
        return class_name
    if re.search(r'Champion:\s*\S', class_name, re.IGNORECASE):
        return class_name
    if ', owned by ' in class_name.lower():
        return class_name

    name = repair_leading_height_championship(class_name, division_name)
    name = canonicalize_over_under_championship_class(name, division_name or '')
    name = normalize_championship_parenthetical(name, division_name)
    name = repair_racing_championship_height(name)

    if re.search(r'RACING\s+CHAMPION', name, re.IGNORECASE):
        height = _extract_racing_height(name)
        if height:
            height = _canonical_racing_height(height, name, division_name)
            division = _extract_racing_division(name)
            base = 'RACING CHAMPION & RESERVE'
            if division:
                return f'{division} {base} ({height})'
            return f'{base} ({height})'

    if re.search(r'GO-TO-GROUND\s+CHAMPION', name, re.IGNORECASE) or (
        division_implies_gtg(division_name)
        and re.search(r'CHAMPION\s*(?:&|AND)\s*RESERVE', name, re.IGNORECASE)
        and not re.search(r'RACING\s+CHAMPION', name, re.IGNORECASE)
    ):
        height = _extract_gtg_championship_height(name)
        if height:
            return f'GO-TO-GROUND CHAMPION & RESERVE ({height})'

    if re.search(r'HIGH\s+POINT\s+CHAMPION|HIGH[\s-]*SCORE\s+CHAMPION', name, re.IGNORECASE):
        height = _extract_racing_height(name)
        if height:
            height = _canonical_racing_height(height, name, division_name)
            base_m = re.search(
                r'^(.+?(?:HIGH\s+POINT\s+CHAMPION(?:\s+AND\s+RESERVE)?|HIGH[\s-]*SCORE\s+CHAMPION\s*&\s*RESERVE))',
                name,
                re.IGNORECASE,
            )
            base = base_m.group(1).strip() if base_m else name.split('(')[0].strip()
            return f'{base} ({height})'

    return name


def repair_class_name_ocr(class_name: str) -> str:
    """Repair common OCR corruption in class names (age, height, certificate, coat)."""
    if not class_name:
        return class_name

    name = class_name

    # Comma glued to digit: Pups,6 -> Pups, 6
    name = re.sub(r",(\d)", r", \1", name)

    # Championship Certificate OCR
    name = re.sub(r"\bC!Rtificate\b", "Certificate", name, flags=re.IGNORECASE)
    name = re.sub(r"\bCe1Ificate\b", "Certificate", name, flags=re.IGNORECASE)
    name = re.sub(
        r"\b(Championship Certificate)\s+(?=\d|10\s*\")",
        r"\1, ",
        name,
        flags=re.IGNORECASE,
    )

    # Digit 1 read as I
    name = re.sub(r"\bI\s*yr\b", "1 yr", name, flags=re.IGNORECASE)

    # Truncated "older" OCR
    name = re.sub(r"\b1\s+year\s+and\s+Ever\b", "1 year and older", name, flags=re.IGNORECASE)
    name = re.sub(r"\b1\s+year\s+and\s+Over\b", "1 year and older", name, flags=re.IGNORECASE)
    name = re.sub(r"\bOvir\b", "Over", name, flags=re.IGNORECASE)
    name = re.sub(r"\b1\s*yr\s*&\s*Ove\b", "1 year and older", name, flags=re.IGNORECASE)
    name = re.sub(r"\b1\s*yr\s*&\s*Over\b", "1 year and older", name, flags=re.IGNORECASE)

    # Bred-by-exhibitor OCR
    name = re.sub(r"\bBred\s+By\s+Exhibito\b", "Bred by Exhibitor", name, flags=re.IGNORECASE)

    # Age range OCR: 4Upm 6 months, 9to 12 months, up B/up T, Rronths/Nonths/Jonths
    name = re.sub(
        r"\b(\d{1,2})Upm\s+(\d{1,2})\s*months?\b",
        r"\1 up to \2 month",
        name,
        flags=re.IGNORECASE,
    )
    name = re.sub(
        r"\b(\d{1,2})\s+up\s+[BT]\s+(\d{1,2})\s*months?\b",
        r"\1 up to \2 month",
        name,
        flags=re.IGNORECASE,
    )
    name = re.sub(
        r"\b(\d{1,2})to\s+(\d{1,2})\s*months?\b",
        r"\1 up to \2 month",
        name,
        flags=re.IGNORECASE,
    )
    name = re.sub(
        r"\b(\d{1,2})\s+to\s+(\d{1,2})\s*(?:Rronths|Nonths)\b",
        r"\1 up to \2 month",
        name,
        flags=re.IGNORECASE,
    )
    name = re.sub(
        r"\b(\d{1,2})\s+up\s+to\s+911Jonths\b",
        r"\1 up to 9 month",
        name,
        flags=re.IGNORECASE,
    )
    name = re.sub(
        r"\b(\d{1,2})\s+up\s+to\s+(\d{1,2})Jonths\b",
        r"\1 up to \2 month",
        name,
        flags=re.IGNORECASE,
    )
    # up B/T/Ro, Upb OCR in age ranges
    name = re.sub(
        r"\b(\d{1,2})\s+up\s+[BTb]\s+(\d{1,2})\s*months?\b",
        r"\1 up to \2 month",
        name,
        flags=re.IGNORECASE,
    )
    name = re.sub(
        r"\b(\d{1,2})\s+up\s+[Rr][oO]\s+(\d{1,2})\s*months?\b",
        r"\1 up to \2 month",
        name,
        flags=re.IGNORECASE,
    )
    name = re.sub(
        r"\b(\d{1,2})\s+Upb\s+(\d{1,2})\s*months?\b",
        r"\1 up to \2 month",
        name,
        flags=re.IGNORECASE,
    )
    name = re.sub(
        r"\b(\d{1,2})\s+up\s+[Tt]\s+(\d{1,2})\s*months?\b",
        r"\1 up to \2 month",
        name,
        flags=re.IGNORECASE,
    )
    name = re.sub(r"\bmmths\b", "month", name, flags=re.IGNORECASE)

    # Stray letter before Over height
    name = re.sub(r"\bSOver\b", "Over", name, flags=re.IGNORECASE)

    # Veteran age OCR: olde,r / s6years / 6years / R6years
    name = name.replace("olde, r", "older, ")
    name = re.sub(r"olde,\s*r", "older, ", name, flags=re.IGNORECASE)
    name = re.sub(r"older,\s*rover\b", "older, over", name, flags=re.IGNORECASE)
    name = re.sub(r"older,\s*r(\d+)\s+up\b", r"older, \1\" up", name, flags=re.IGNORECASE)
    name = re.sub(r"(?<=[,\s])[sS](\d+)years\b", r"\1 years", name, flags=re.IGNORECASE)
    name = re.sub(r"(?<=[,\s])R(\d+)years\b", r"\1 years", name, flags=re.IGNORECASE)
    name = re.sub(r"\b(\d+)years\s*&", r"\1 years &", name, flags=re.IGNORECASE)
    name = re.sub(r"\b(\d+)years\b", r"\1 years", name, flags=re.IGNORECASE)
    name = re.sub(r"\bVeteranterrie\b", "Veteran Terrier", name, flags=re.IGNORECASE)
    name = re.sub(
        r"^Veteran,\s+(?=\d)",
        "Veterans, ",
        name,
        flags=re.IGNORECASE,
    )

    # Glued height + coat: 12½" to 15''R/Br
    name = re.sub(
        r'\b12\s*½\s*"\s*to\s+15\s*["\']+R/Br\b',
        'Over 12½" up to 15", rough/broken',
        name,
        flags=re.IGNORECASE,
    )

    # Mangled over-15 heights
    name = re.sub(
        r"\b12\s*½\s*[-–]\s*1\s*[\"']?\s*5\b",
        'Over 12½" up to 15"',
        name,
        flags=re.IGNORECASE,
    )
    name = re.sub(
        r'\b12\s*½\s*"\s*to\s+1L\s*"',
        'Over 12½" up to 15"',
        name,
        flags=re.IGNORECASE,
    )

    # R prefix glued to 10-12½ height = rough/broken coat
    name = re.sub(
        r",\s*R10\s*[-–]\s*12\s*½\s*\"",
        ', 10" up to 12½", rough/broken',
        name,
        flags=re.IGNORECASE,
    )

    # Coat glued after height: 15''R/Br
    name = re.sub(
        r"(15\s*['\"]+)R/Br\b",
        r'\1, rough/broken',
        name,
        flags=re.IGNORECASE,
    )

    # Garbage height fragment after canonical 10-12
    name = re.sub(r'\s+I12\s*"\s*,', ",", name, flags=re.IGNORECASE)
    name = re.sub(r'\s+I12\s*"\b', "", name, flags=re.IGNORECASE)

    # Trailing garbage after Up to 12½"
    name = re.sub(r'(Up to 12½")\s*1/,?\s*$', r"\1", name, flags=re.IGNORECASE)

    # Extra quote after certificate parenthetical
    name = re.sub(
        r'\(10" up to 12½"\)"\s*$',
        '(10" up to 12½")',
        name,
        flags=re.IGNORECASE,
    )

    return name


def normalize_legacy_class_format(class_name: str) -> str:
    """Normalize pre-2000 class name formats (singular Puppy, Over l Year, etc.)."""
    if not class_name:
        return class_name

    name = class_name
    over_year = r"(?:L|I|l|1)\s*Year"

    # Singular puppy -> plural Pups
    name = re.sub(r"^Bitch\s+Puppy\b", "Bitch Pups", name, flags=re.IGNORECASE)
    name = re.sub(r"^Dog\s+Puppy\b", "Dog Pups", name, flags=re.IGNORECASE)

    # Best Bitch or Dog Over l Year -> Best Bitch or Dog, 1 year and older
    name = re.sub(
        rf"^Best\s+Bitch\s+or\s+Dog\s+Over\s+{over_year}\b",
        "Best Bitch or Dog, 1 year and older",
        name,
        flags=re.IGNORECASE,
    )
    name = re.sub(
        rf"^Bitch\s+or\s+Dog\s+Over\s+{over_year}\b",
        "Best Bitch or Dog, 1 year and older",
        name,
        flags=re.IGNORECASE,
    )

    # Dog/Bitch Over l Year (singular) -> Dogs/Bitches, 1 year and older
    name = re.sub(
        rf"^Dog\s+Over\s+{over_year}\b",
        "Dogs, 1 year and older",
        name,
        flags=re.IGNORECASE,
    )
    name = re.sub(
        rf"^Bitch\s+Over\s+{over_year}\b",
        "Bitches, 1 year and older",
        name,
        flags=re.IGNORECASE,
    )

    # Best N up to M mmths Puppies (1980s-90s best-puppy classes)
    name = re.sub(
        r"^Best\s+(\d{1,2})\s+up\s+to\s+(\d{1,2})\s+months?\s+Puppies\b",
        r"Best Pups, \1 up to \2 month",
        name,
        flags=re.IGNORECASE,
    )
    name = re.sub(
        r"^(\d{1,2})\s+up\s+to\s+(\d{1,2})\s+months?\s+Puppies\b",
        r"Pups, \1 up to \2 month",
        name,
        flags=re.IGNORECASE,
    )

    return name


def repair_half_fraction_ocr(class_name: str) -> str:
    """Repair OCR corruption of 12½ (121/2, 121/:z, 12V2, etc.)."""
    if not class_name:
        return class_name

    name = class_name
    literal_replacements = [
        ("121/2", "12½"),
        ("12 1/2", "12½"),
        ("12112", "12½"),
        ("121h", "12½"),
        ("12'h", "12½"),
        ("12h'", "12½"),
        ("12W'", "12½"),
        ("121/z", "12½"),
        ("121/:z", "12½"),
        ("121/:i", "12½"),
        ("121:/z", "12½"),
        ("121:/i", "12½"),
        ("121: /i", "12½"),
        ("121: /z", "12½"),
        ("121/1", "12½"),
        ("12.5", "12½"),
        ("12V2", "12½"),
        ("12Y2", "12½"),
        ("12 ½", "12½"),
    ]
    for old, new in literal_replacements:
        name = name.replace(old, new)

    # 121/:z, 121/1, 121/ i, etc.
    name = re.sub(r"121/\s*[:/]?\s*\w", "12½", name, flags=re.IGNORECASE)
    name = re.sub(r"121/\s*[:;/\\]+[a-z]*;?\.?\s*", "12½", name, flags=re.IGNORECASE)
    name = re.sub(r'121/\s*["\']?\s*2', "12½", name, flags=re.IGNORECASE)
    name = re.sub(r"121/\s+", "12½", name, flags=re.IGNORECASE)
    # 12Y:i OCR variant (colon required to avoid matching "12 years")
    name = re.sub(r"12\s*Y\s*:\s*[a-z]", "12½", name, flags=re.IGNORECASE)
    # Lone 12% before -15 or 15 (percent sign OCR'd as ½)
    name = re.sub(r"12\s*%\s*(?:½|[^\d])?\s*(?=[-–]?\s*15)", "12½", name, flags=re.IGNORECASE)
    return name


def repair_mangled_over_12_15(class_name: str) -> str:
    """Repair OCR-mangled 'over 12…15' height ranges to canonical form."""
    if not class_name:
        return class_name
    if _has_canonical_12_15(class_name):
        return class_name

    name = class_name
    # Duplicated 12 from OCR: over 12 '12½15 or over 12 \'12½15
    name = re.sub(
        r"over\s+12\s*'.*?12\s*½?\s*15\s*\"*",
        'Over 12½" up to 15"',
        name,
        flags=re.IGNORECASE,
    )
    # Slash/quote garbage: over 12 \'/,½15 or over 12 '/,·15"
    name = re.sub(
        r"over\s+12\s*(?:\\?['\"]|['\"])\s*[/,\\·°.\s]*,?\s*[·°.\s]*½?\s*15\s*\"*",
        'Over 12½" up to 15"',
        name,
        flags=re.IGNORECASE,
    )
    # over 12<ocr garbage>15 with optional hyphen, quotes, trailing dots
    name = re.sub(
        r"over\s+12(?:½|1\s*/\s*2|"
        r"[%YVZ]|"
        r"['\u2018\u2019]?\\?/?\s*['\u2018\u2019]?\s*12½?|"
        r"[^\d\s,;\"]{0,5})"
        r"\s*[-–%]?\s*1\s*[\"']?\s*5\s*[\"'\.\s]*",
        'Over 12½" up to 15"',
        name,
        flags=re.IGNORECASE,
    )
    # Collapse doubled half: 12½½ -> 12½
    name = re.sub(r"12½+", "12½", name)
    return name


def fix_puppy_height_format(class_name: str, division_name: str | None = None) -> str:
    """Puppy classes use 'Up to 12½"' not adult '10\" up to 12½\"'."""
    if not class_name or not is_puppy_context(class_name, division_name):
        return class_name

    name = class_name
    name = re.sub(
        r'10\s*"\s*up\s+to\s+12\s*½\s*"+',
        'Up to 12½"',
        name,
        flags=re.IGNORECASE,
    )
    # Puppy: "10 up to 12½" (missing quote on 10) -> "Up to 12½"
    name = re.sub(
        r',\s*10\s+up\s+to\s+12\s*½\s*"+',
        ', Up to 12½"',
        name,
        flags=re.IGNORECASE,
    )
    # Truncated height at end: "... month up to 12" -> ", Up to 12½""
    name = re.sub(
        r'(?<=\bmonth\b),?\s*up\s+to\s+12\s*"(?!\s*½)\s*$',
        ', Up to 12½"',
        name,
        flags=re.IGNORECASE,
    )
    name = re.sub(
        r'(?<=\bmonth\b),?\s*up\s+to\s+12\s*$',
        ', Up to 12½"',
        name,
        flags=re.IGNORECASE,
    )
    # Truncated height: ", up to 12" at end (puppy division)
    name = re.sub(
        r',\s*up\s+to\s+12\s*$',
        ', Up to 12½"',
        name,
        flags=re.IGNORECASE,
    )
    return name


def normalize_coat_types(class_name: str) -> str:
    """Standardize coat type suffixes to rough/broken and smooth."""
    if not class_name:
        return class_name

    name = class_name
    coat_patterns = [
        (r",\s*r/br\b", ", rough/broken"),
        (r",\s*r/b\b", ", rough/broken"),
        (r",\s*rbr\b", ", rough/broken"),
        (r",\s*r/brr\b", ", rough/broken"),
        (r",\s*rlbr\b", ", rough/broken"),
        (r",\s*rough\s*/\s*br\.?\b", ", rough/broken"),
        (r",\s*sm\b", ", smooth"),
        (r",\s*ssmooth\b", ", smooth"),
        (r",\s*smooth coat\b", ", smooth"),
        (r"\bbroken\s*/\s*rough\b", "rough/broken"),
        (r"\brough\s*/\s*br\.?\b", "rough/broken"),
        (r"\brough\s*/\s*broken\b", "rough/broken"),
        (r"\bsmooth\b", "smooth"),
    ]
    for pattern, replacement in coat_patterns:
        name = re.sub(pattern, replacement, name, flags=re.IGNORECASE)
    return name


def is_puppy_class(class_name: str) -> bool:
    return bool(PUPPY_RE.search(class_name))


def _collapse_height_quotes(name: str) -> str:
    """Collapse doubled quotes introduced by repeated height normalization."""
    name = normalize_quotes(name)
    name = re.sub(r'12½["]+', '12½"', name)
    name = re.sub(r'15["]+', '15"', name)
    name = re.sub(r'10"+\s*up\s+to', '10" up to', name, flags=re.IGNORECASE)
    return name


def _has_canonical_10_12(name: str) -> bool:
    return bool(re.search(r'10"\s*up\s+to\s+12½"', name, re.IGNORECASE))


def _has_canonical_up_12(name: str) -> bool:
    return bool(re.search(r'Up\s+to\s+12½"', name, re.IGNORECASE))


def _has_canonical_12_15(name: str) -> bool:
    return bool(re.search(r'Over\s+12½"\s*up\s+to\s+15"', name, re.IGNORECASE))


def _has_height_12(name: str) -> bool:
    """Detect 12 or 12½ in height context (\\b12\\b misses 12½)."""
    return bool(re.search(r"12(?:½|1\s*/\s*2|\ufffd|\b)", name, re.IGNORECASE))


def normalize_height_categories(class_name: str, division_name: str | None = None) -> str:
    """Apply JRTCA height category rules on top of base class normalization."""
    if not class_name:
        return class_name
    if re.search(r'CHAMPION\s*(?:&|AND)\s*RESERVE|HIGH\s+POINT\s+CHAMPION', class_name, re.IGNORECASE):
        return class_name

    name = class_name.replace("\ufffd", "½")
    puppy = is_puppy_context(name, division_name)
    upper = name.upper()

    # Repair corrupted class lines that leaked placement parsing
    if ", owned by " in name.lower() and any(
        kw in upper for kw in ("BITCH", "DOG", "PUP", "WORKING", "OPEN", "VETERAN", "ADULT")
    ):
        parts = re.split(r",\s*owned by\s*", name, flags=re.IGNORECASE)
        parts = [p.strip(" ,") for p in parts if p.strip(" ,")]
        if parts:
            name = parts[-1]

    # Strip class number prefix (Class 99:, Class 38., etc.)
    name = re.sub(r"^Class\s+[\dA-Za-z]+\s*[.:]\s*", "", name, flags=re.IGNORECASE).strip()

    name, age_masks = _mask_age_qualifiers(name)

    has_10_12 = bool(re.search(r"\b10\b", name) and _has_height_12(name))
    has_12_15 = bool(_has_height_12(name) and re.search(r"\b15\b", name))

    half = r'(?:½|1\s*/\s*2|"|\'\'|[^\w\s,;])?'

    if has_10_12 and not _has_canonical_10_12(name) and not _has_canonical_up_12(name):
        patterns_10_12 = [
            rf"\b10\s*upto\s*12\s*{half}",
            rf"\b10\s+upto\s+12\s*{half}",
            rf"\b10\s*[\"'']?\s*(?:up\s+to|to)\s*12\s*{half}",
            rf"\b10\s*[-–]\s*12\s*{half}",
            rf"\b10\s+12\s*{half}",
            r"10[-\s]*1[_\s]*[iI][_\-]\s*1\s*/\s*2\s*\"",
            r"121\s*/?\s*2",
            r"12112",
            r"\b12\s*112\b",
        ]
        replacement = 'Up to 12½"' if puppy else '10" up to 12½"'
        replaced = False
        for pat in patterns_10_12:
            if re.search(pat, name, re.IGNORECASE):
                name = re.sub(pat, replacement, name, flags=re.IGNORECASE, count=1)
                replaced = True
                break
        if not replaced and puppy and re.search(rf"\bup\s+to\s+12\s*{half}", name, re.IGNORECASE):
            name = re.sub(
                rf"\bup\s+to\s+12\s*{half}",
                'Up to 12½"',
                name,
                flags=re.IGNORECASE,
                count=1,
            )

    if has_12_15 and not _has_canonical_12_15(name):
        patterns_12_15 = [
            rf"(?:Over\s+)?\b12\s*[\"'']?\s*½?\s*\"?\s*(?:up\s+to|to)\s*15\s*[\"'']+",
            rf"(?:over\s+)?\b12\s*½\s*[-–]\s*15\s*[\"'']?",
            rf"\b12\s*½\s*[-–]\s*15\s*[\"'']?",
            rf"\b12\s*[-–]\s*15\s*[\"'']?",
            r"\bover\s*12\s*[\"'']?\s*up\s+to\s+15",
        ]
        replacement = 'Over 12½" up to 15"'
        for pat in patterns_12_15:
            if re.search(pat, name, re.IGNORECASE):
                name = re.sub(pat, replacement, name, flags=re.IGNORECASE, count=1)
                break

    name = _unmask_age_qualifiers(name, age_masks)

    return re.sub(r"\s+", " ", name).strip()


def repair_corrupted_height_prefix(
    class_name: str,
    division_name: str | None = None,
) -> str:
    """Restore '10' height prefix stripped by earlier normalization bugs."""
    if not class_name:
        return class_name

    name = normalize_quotes(class_name).replace("\ufffd", "½").strip()
    name = re.sub(r'12(?:½|1\s*/\s*2|\ufffd)+', '12½', name, flags=re.IGNORECASE)
    name = _collapse_height_quotes(name)
    puppy = is_puppy_context(name, division_name)

    # " + up to 12..." -> 10" up to 12..."
    if re.match(r'^"\s*up\s+to\s+12', name, re.IGNORECASE):
        name = re.sub(r'^"\s*', '10" ', name, count=1)

    # up to 12..." at start on adult/veteran/senior classes (not puppies)
    elif not puppy and re.match(r'^up\s+to\s+12', name, re.IGNORECASE):
        name = re.sub(r'^up\s+to', '10" up to', name, count=1, flags=re.IGNORECASE)

    # ½" at start: restore full height prefix
    elif not puppy and re.match(r'^½["]?\s*', name):
        if re.search(r'\b15\b', name):
            name = re.sub(
                r'^½["]?\s*(?:up\s+to\s*)?',
                'Over 12½" up to ',
                name,
                count=1,
                flags=re.IGNORECASE,
            )
        else:
            name = re.sub(r'^½["]?\s*', '10" up to 12½" ', name, count=1)

    return _collapse_height_quotes(name)


def standardize_height_phrases(
    class_name: str,
    division_name: str | None = None,
) -> str:
    """Canonical spacing and quotes for JRTCA height category phrases."""
    if not class_name:
        return class_name

    name = normalize_quotes(class_name)
    name = name.replace("\ufffd", "½")
    name = _collapse_height_quotes(name)

    # 10 upto / 10upto (missing inch quote on 10, glued variants)
    name = re.sub(r'\b10\s*upto\s*12', '10" up to 12', name, flags=re.IGNORECASE)
    name = re.sub(r'\b10\s+up\s+to\s+12\s*½', '10" up to 12½', name, flags=re.IGNORECASE)
    # Glued 10upto15 on veteran/senior lines -> Over 12½" up to 15"
    name = re.sub(r'\b10\s*upto\s*15\s*"+', 'Over 12½" up to 15"', name, flags=re.IGNORECASE)

    # 10"up to -> 10" up to; 10" to -> 10" up to
    name = re.sub(r'10"\s*(?=up\s+to)', '10" ', name, flags=re.IGNORECASE)
    name = re.sub(r'10\s*"\s*to\s+12', '10" up to 12', name, flags=re.IGNORECASE)

    # Hyphen height range: 10" - 12½" or OCR 10"-12"
    name = re.sub(
        r'10\s*"\s*[-–]\s*12\s*½\s*"+',
        '10" up to 12½"',
        name,
        flags=re.IGNORECASE,
    )
    name = re.sub(
        r'10\s*"\s*[-–]\s*12\s*"(?!\s*½)',
        '10" up to 12½"',
        name,
        flags=re.IGNORECASE,
    )
    if is_puppy_context(name, division_name):
        name = re.sub(
            r'10\s*"\s*[-–]\s*12\s*½\s*"+',
            'Up to 12½"',
            name,
            flags=re.IGNORECASE,
        )

    # Canonical adult height (absorb any trailing quote run, emit exactly one)
    name = re.sub(
        r'10\s*"\s*up\s+to\s+12\s*½\s*"+',
        '10" up to 12½"',
        name,
        flags=re.IGNORECASE,
    )
    # Ensure closing quote when 12½ not followed by "
    name = re.sub(
        r'10"\s*up\s+to\s+12½(?!\s*")',
        '10" up to 12½"',
        name,
        flags=re.IGNORECASE,
    )
    # Incomplete height: 10" up to 12" (missing ½)
    name = re.sub(
        r'10"\s*up\s+to\s+12\s*"(?!\s*½)',
        '10" up to 12½"',
        name,
        flags=re.IGNORECASE,
    )
    # Incomplete height: Up to 12" (missing ½)
    name = re.sub(
        r'Up\s+to\s+12\s*"(?!\s*½)',
        'Up to 12½"',
        name,
        flags=re.IGNORECASE,
    )

    # Incomplete over-12 height: Over 12" without ½ or "up to 15"
    name = re.sub(
        r'Over\s+12\s*"(?!\s*½)(?!\s*up\s+to\s+15)',
        'Over 12½" up to 15"',
        name,
        flags=re.IGNORECASE,
    )

    # Canonical over-12½ height
    name = re.sub(
        r'Over\s+12\s*½\s*"\s*up\s+to\s+15\s*"+',
        'Over 12½" up to 15"',
        name,
        flags=re.IGNORECASE,
    )

    # Canonical puppy height (no leading 10")
    if is_puppy_context(name, division_name):
        name = re.sub(
            r'(?<![\d"])Up\s+to\s+12\s*½\s*"+',
            'Up to 12½"',
            name,
            flags=re.IGNORECASE,
        )

    return _collapse_height_quotes(name)


def consolidate_height_variants(class_name: str) -> str:
    """Consolidate height/age class name variants to canonical JRTCA forms."""
    if not class_name:
        return class_name

    name = normalize_quotes(class_name).replace("\ufffd", "½")

    # Repair prior normalization corruption
    name = re.sub(r"\boverOver\b", "Over", name, flags=re.IGNORECASE)
    name = re.sub(
        r'(Over\s+12\s*½\s*"\s*up\s+to\s+15\s*")(?:\s*up\s+to(?:\s+to)?\s*[-]?\s*15\s*"?)+',
        r"\1",
        name,
        flags=re.IGNORECASE,
    )
    name = re.sub(
        r'Over\s+12\s*½\s*"\s*up\s+to\s*[-]?\s*15\s*"+',
        'Over 12½" up to 15"',
        name,
        flags=re.IGNORECASE,
    )

    # Unglue "over" from "12" (over12½ -> Over 12½)
    name = re.sub(r"\bover\s*(?=12)", "Over ", name, flags=re.IGNORECASE)

    # Age qualifiers
    name = re.sub(r"\b1\s*yr\.?\s*&\s*older\b", "1 year and older", name, flags=re.IGNORECASE)
    name = re.sub(r"\b1\s*yr\.?\s+and\s+older\b", "1 year and older", name, flags=re.IGNORECASE)
    name = re.sub(r"\b1\s*yr\.?\s*&\s*over\b", "1 year and older", name, flags=re.IGNORECASE)
    name = re.sub(r"\b1\s*year\s*&\s*older\b", "1 year and older", name, flags=re.IGNORECASE)

    # OCR: 12 = - 15 height corruption
    name = re.sub(
        r'\b12\s*=\s*[-–]\s*15\s*"?',
        'Over 12½" up to 15"',
        name,
        flags=re.IGNORECASE,
    )

    # 12½-15" hyphen variants (not after "up to "); allow trailing dots/quotes
    name = re.sub(
        r'(?<!up to )(?:over\s+)?12\s*½\s*[-–]\s*15\s*["\'\.]*',
        'Over 12½" up to 15"',
        name,
        flags=re.IGNORECASE,
    )

    # Glued 12½15 without hyphen (e.g. over12½½15")
    name = re.sub(
        r'(?:over\s+)?12\s*½+\s*15\s*\"+',
        'Over 12½" up to 15"',
        name,
        flags=re.IGNORECASE,
    )

    # 12½" up to 15" missing "Over" prefix (not when preceded by "over ")
    name = re.sub(
        r'(?<![Oo]ver )12\s*½\s*"\s*up\s+to\s+15\s*"+',
        'Over 12½" up to 15"',
        name,
        flags=re.IGNORECASE,
    )

    # Incomplete "Over 12½"" missing "up to 15" (skip when already followed by "up to")
    name = re.sub(
        r'Over\s+12\s*½\s*"(?!\s*up\s+to\b)',
        'Over 12½" up to 15"',
        name,
        flags=re.IGNORECASE,
    )

    # Parenthetical height ranges: (12½-15") or (over 12½-15")
    name = re.sub(
        r'\(\s*(?:over\s+)?12\s*½\s*[-–]\s*15\s*"\s*\)',
        '(Over 12½" up to 15")',
        name,
        flags=re.IGNORECASE,
    )

    # OCR: over 12 to/upto/up 15 (with or without ½)
    name = re.sub(
        r'(?:over\s+)?12\s*½*\s*["\']?\s*(?:to|upto|up\s+)\s*15\s*"+',
        'Over 12½" up to 15"',
        name,
        flags=re.IGNORECASE,
    )
    name = re.sub(
        r'(?:over\s+)?12\s*½?\s*["\']?\s*[-–]\s*1\s*5\s*"+',
        'Over 12½" up to 15"',
        name,
        flags=re.IGNORECASE,
    )
    name = re.sub(
        r'(?:over\s+)?12\s*[%½]{1,3}\s*15\s*"+',
        'Over 12½" up to 15"',
        name,
        flags=re.IGNORECASE,
    )

    return _collapse_height_quotes(name)


def _extract_racing_height(name: str) -> str | None:
    if re.search(r'Over\s+12\s*½\s*"\s*up\s+to\s+15\s*"', name, re.IGNORECASE):
        return 'Over 12½" up to 15"'
    if re.search(r'10\s*"\s*up\s+to\s+12\s*½\s*"', name, re.IGNORECASE):
        return '10" up to 12½"'
    if re.search(r'Up\s+to\s+12\s*½\s*"', name, re.IGNORECASE):
        return 'Up to 12½"'
    return None


def _extract_gtg_championship_height(name: str) -> str | None:
    """Extract height suffix from GTG championship class names."""
    paren_m = re.search(r'\(([^)]+)\)\s*$', name)
    if paren_m:
        height = canonicalize_gtg_championship_height(paren_m.group(1).strip())
        if height:
            return height
    for fragment in (
        'Over 12½" up to 15"',
        '10" up to 12½"',
        'Up to 12½"',
        '10-12 ½"',
        '10-12½"',
        '12 ½-15"',
        '12½-15"',
    ):
        if re.search(re.escape(fragment), name, re.IGNORECASE):
            return canonicalize_gtg_championship_height(fragment)
    return None


def _canonical_racing_height(
    height: str,
    class_name: str,
    division_name: str | None = None,
) -> str:
    """Non-puppy racing championships use 10\" up to 12½\", not Up to 12½\"."""
    if height != 'Up to 12½"':
        return height
    if is_puppy_context(class_name, division_name):
        return height
    if division_implies_racing(division_name) or division_implies_gtg(division_name):
        return '10" up to 12½"'
    if re.search(r'\b(?:Adult|Veteran|Veterans|Senior|Seniors|Colored|Spayed|Neutered)\b', class_name, re.IGNORECASE):
        return '10" up to 12½"'
    return height


def _extract_racing_division(name: str) -> str | None:
    if re.search(r'Senior\s+Veteran', name, re.IGNORECASE):
        return 'Senior Veteran'
    for div in ('Adult', 'Veterans', 'Veteran', 'Seniors', 'Senior', 'Puppy', 'Colored', 'Spayed/Neutered'):
        if re.search(rf'\b{div}\b', name, re.IGNORECASE):
            return div
    return None


def repair_racing_word_ocr(class_name: str) -> str:
    """Fix OCR typos in RACING keyword (e.g. RACM)."""
    if not class_name:
        return class_name
    return re.sub(r'\bRACM\b', 'RACING', class_name, flags=re.IGNORECASE)


def repair_racing_size_prefix_ocr(text: str, puppy: bool = False) -> str:
    """Repair OCR-mangled racing height prefixes like 1()'12'/2\" or 1()'12'12\"."""
    if not text:
        return text

    name = text.strip()
    up_12 = 'Up to 12½"'
    ten_12 = '10" up to 12½"'

    for pat in (
        r"1\s*\(\s*\)\s*['\"]?\s*12\s*['\"]?\s*/2\s*\"?",
        r"1\s*\(\s*\)\s*['\"]?\s*12\s*['\"]?\s*12\s*\"?",
    ):
        if re.fullmatch(pat, name, flags=re.IGNORECASE):
            return up_12 if puppy else ten_12

    name = re.sub(r"12\s*['\"]\s*(?=Over\s+12)", "", name, flags=re.IGNORECASE)
    return name.strip()


def repair_racing_championship_height(
    class_name: str,
    division_name: str | None = None,
) -> str:
    """Fix OCR height suffixes on RACING CHAMPION & RESERVE class names."""
    if not class_name:
        return class_name
    if not re.search(r'RAC(?:ING|M)\s+CHAMPION', class_name, re.IGNORECASE):
        return class_name

    name = repair_racing_word_ocr(class_name)
    puppy = is_puppy_context(name, division_name)
    up_12 = 'Up to 12½"'
    ten_12 = '10" up to 12½"'

    # 1()'12'/2" and 1()'12'12" (OCR for 10" up to 12½) — match full parenthetical
    name = re.sub(
        r"\(\s*1\s*\(\s*\)\s*['\"]?\s*12\s*['\"]?\s*/2\s*\"?\s*\)",
        f'({up_12 if puppy else ten_12})',
        name,
        flags=re.IGNORECASE,
    )
    name = re.sub(
        r"\(\s*1\s*\(\s*\)\s*['\"]?\s*12\s*['\"]?\s*12\s*\"?\s*\)",
        f'({up_12 if puppy else ten_12})',
        name,
        flags=re.IGNORECASE,
    )
    # 12'Over 12½" up to 15" — leading garbage before Over
    name = re.sub(
        r"\(\s*12\s*['\"]\s*Over\s+12\s*½\s*\"\s*up\s+to\s+15\s*\"\s*\)",
        '(Over 12½" up to 15")',
        name,
        flags=re.IGNORECASE,
    )
    # Adult/veteran/senior: Up to 12½" -> 10" up to 12½"
    if not puppy:
        name = re.sub(
            r'\(\s*Up\s+to\s+12\s*½\s*"\s*\)',
            f'({ten_12})',
            name,
            flags=re.IGNORECASE,
        )
    return name


def normalize_racing_championship(class_name: str) -> str:
    """Consolidate RACING CHAMPION classes to '{Division} RACING CHAMPION & RESERVE ({height})'."""
    if not class_name:
        return class_name
    class_name = repair_racing_championship_height(class_name)
    if re.search(r'Champion:\s*\S', class_name, re.IGNORECASE):
        return class_name
    if ', owned by ' in class_name.lower():
        return class_name
    if not re.search(r'RACING\s+CHAMPION', class_name, re.IGNORECASE):
        return class_name

    height = _extract_racing_height(class_name)
    if not height:
        return class_name
    height = _canonical_racing_height(height, class_name)

    division = _extract_racing_division(class_name)
    base = 'RACING CHAMPION & RESERVE'
    if division:
        return f'{division} {base} ({height})'
    return f'{base} ({height})'


def finalize_class_name_formatting(class_name: str) -> str:
    """Final polish: age phrase casing, trailing punctuation, division casing."""
    if not class_name:
        return class_name

    name = class_name
    name = re.sub(r"(\d+)\s+Years\s+and\s+older\b", r"\1 years and older", name, flags=re.IGNORECASE)
    name = re.sub(r"(\d+)\s+years\s*&\s*older\b", r"\1 years and older", name, flags=re.IGNORECASE)
    # Glued text before height: RESERVE10 Up to -> RESERVE 10" up to
    name = re.sub(
        r'(?<=[A-Za-z])10\s+Up\s+to\s+12',
        ' 10" up to 12',
        name,
        flags=re.IGNORECASE,
    )
    # Duplicate height phrase: 10" up to 12½" Up to 12½"
    name = re.sub(
        r'10"\s*up\s+to\s+12½"\s+Up\s+to\s+12½"',
        '10" up to 12½"',
        name,
        flags=re.IGNORECASE,
    )
    # Repair duplicated -15" suffix
    name = re.sub(
        r'(Over\s+12\s*½\s*"\s*up\s+to\s+15\s*")[-–]?\s*15\s*"+',
        r'\1',
        name,
        flags=re.IGNORECASE,
    )
    # Repair duplicated "to 15" suffix (e.g. over 12½" to 15" -> Over 12½" up to 15" to 15")
    name = re.sub(
        r'(Over\s+12\s*½\s*"\s*up\s+to\s+15\s*")\s*to\s+15\s*"+',
        r'\1',
        name,
        flags=re.IGNORECASE,
    )

    # Age phrase period before height: "month. Under 12½"
    name = re.sub(
        r'(\bmonth)\.\s*(?:Under\s+)?12\s*½\s*"',
        r'\1, Up to 12½"',
        name,
        flags=re.IGNORECASE,
    )

    # Pups/Puppies 12½" and/& Under
    name = re.sub(
        r'^(?:Pups|Puppies)\s+12\s*½\s*"\s*(?:and|&)\s+Under\b',
        'Pups, Up to 12½"',
        name,
        flags=re.IGNORECASE,
    )
    name = re.sub(
        r'12\s*½\s*"\s*(?:and|&)\s+Under\b',
        'Up to 12½"',
        name,
        flags=re.IGNORECASE,
    )
    name = re.sub(
        r'12\s*½\s*"\s+and\s+Under\b',
        'Up to 12½"',
        name,
        flags=re.IGNORECASE,
    )

    # Puppies/Pups missing comma before age
    name = re.sub(
        r'^(?:Puppies|Pups)\s+(\d+\s+up\s+to\s+\d+\s+month)',
        r'Pups, \1',
        name,
        flags=re.IGNORECASE,
    )

    # Division missing comma before age or height
    name = re.sub(
        r'^(Dogs|Bitches|Dog Pups|Bitch Pups)\s+(\d|1\s+yr|1\s+year|Over\s+12|10\s*")',
        r'\1, \2',
        name,
        flags=re.IGNORECASE,
    )
    name = re.sub(
        r'(\bolder)\s+(10\s*"|Over\s+12|Up\s+to\s+12)',
        r'\1, \2',
        name,
        flags=re.IGNORECASE,
    )

    # Dash before height phrase -> comma
    name = re.sub(
        r'\s+-\s+(10\s*"|Over\s+12|Up\s+to\s+12)',
        r', \1',
        name,
        flags=re.IGNORECASE,
    )

    # Strip spurious " Inches" suffix
    name = re.sub(r'\s+Inches\b', '', name, flags=re.IGNORECASE)

    # Dogs/Bitches missing comma before height
    name = re.sub(
        r'^(Dogs|Bitches)\s+(10\s*"\s*(?:up\s+to|[-–])\s*12\s*½\s*")',
        r'\1, \2',
        name,
        flags=re.IGNORECASE,
    )

    # Space before entry-count parenthetical glued to quote
    name = re.sub(r'"\(', '" (', name)

    # Agility lead phrasing
    name = re.sub(r'\bon-lead\b', 'On Lead', name, flags=re.IGNORECASE)
    name = re.sub(r'\boff-lead\b', 'Off Lead', name, flags=re.IGNORECASE)

    # Trailing periods after canonical height phrases or at end of name
    name = re.sub(
        r'(10" up to 12½"|Over 12½" up to 15"|Up to 12½")\s*\.+',
        r"\1",
        name,
        flags=re.IGNORECASE,
    )
    name = re.sub(r"\.+$", "", name)
    return name


_CANONICAL_PHRASE_SPECS = [
    (re.compile(r'Over\s+12\s*½\s*"\s*up\s+to\s+15\s*"', re.IGNORECASE), 'Over 12½" up to 15"'),
    (re.compile(r'10\s*"\s*up\s+to\s+12\s*½\s*"', re.IGNORECASE), '10" up to 12½"'),
    (re.compile(r'Up\s+to\s+12\s*½\s*"', re.IGNORECASE), 'Up to 12½"'),
    (re.compile(r'RACING\s+CHAMPION\s*&\s*RESERVE', re.IGNORECASE), 'RACING CHAMPION & RESERVE'),
    (re.compile(r'\brough\s*/\s*br\.?\b', re.IGNORECASE), 'rough/broken'),
    (re.compile(r'\brough\s*/\s*broken\b', re.IGNORECASE), 'rough/broken'),
    (re.compile(r'\bsmooth\b', re.IGNORECASE), 'smooth'),
    (re.compile(r'\d+\s+up\s+to\s+\d+\s+month', re.IGNORECASE), None),
    (re.compile(r'\d+\s+years?\s+and\s+older', re.IGNORECASE), None),
]

_TITLECASE_LOWERCASE_WORDS = frozenset({
    'and', 'up', 'to', 'of', 'the', 'yr', 'year', 'years', 'month', 'months',
    'older', 'smooth', 'on', 'or', 'entries',
})

_KNOWN_ACRONYMS = frozenset({
    'JRTCA', 'GTG', 'AKC', 'OFA', 'II', 'III', 'IV', 'VI', 'VII', 'VIII',
})


def _canonicalize_masked_age_phrase(match: re.Match) -> str:
    text = re.sub(r'\s+', ' ', match.group(0)).strip()
    text = re.sub(r'\bmonths\b', 'month', text, flags=re.IGNORECASE)
    return text.lower()


def _mask_canonical_phrases(class_name: str) -> tuple[str, list[tuple[str, str]]]:
    masks: list[tuple[str, str]] = []
    name = class_name

    def replacer(canonical: str | None):
        def _repl(match: re.Match) -> str:
            replacement = canonical if canonical else _canonicalize_masked_age_phrase(match)
            token = f"\x00{len(masks)}\x01"
            masks.append((token, replacement))
            return token

        return _repl

    for pattern, canonical in _CANONICAL_PHRASE_SPECS:
        name = pattern.sub(replacer(canonical), name)
    return name, masks


def _unmask_phrases(class_name: str, masks: list[tuple[str, str]]) -> str:
    name = class_name
    for token, replacement in masks:
        name = name.replace(token, replacement)
    return name


def _alpha_case_counts(class_name: str) -> tuple[int, int]:
    upper = lower = 0
    for ch in class_name:
        if ch.isalpha():
            if ch.isupper():
                upper += 1
            else:
                lower += 1
    return upper, lower


def _should_skip_capitalization(class_name: str) -> bool:
    lower = class_name.lower()
    if ', owned by ' in lower:
        return True
    if re.search(r'Champion:\s*\S', class_name, re.IGNORECASE):
        return True
    return False


def _original_uppercase_words(class_name: str) -> set[str]:
    return {
        word.upper()
        for word in re.findall(r'[A-Za-z]+', class_name)
        if len(word) >= 2 and word.isupper()
    }


def _apply_title_case(text: str, preserve_upper: set[str] | None = None) -> str:
    preserve_upper = preserve_upper or set()

    def fix_word(match: re.Match) -> str:
        word = match.group(0)
        upper_word = word.upper()
        if upper_word in _KNOWN_ACRONYMS or upper_word in preserve_upper:
            return upper_word
        lower = word.lower()
        if re.fullmatch(r'[IVX]+', word, re.IGNORECASE):
            return word.upper()
        if lower in _TITLECASE_LOWERCASE_WORDS:
            return lower
        if '/' in lower and lower.replace('/', '') in {'rbr', 'rb'}:
            return lower
        return word[:1].upper() + word[1:].lower()

    result = re.sub(r'[A-Za-z]+', fix_word, text)
    result = re.sub(r'\bon\s+lead\b', 'On Lead', result, flags=re.IGNORECASE)
    result = re.sub(r'\boff\s+lead\b', 'Off Lead', result, flags=re.IGNORECASE)
    result = re.sub(r'\bon-lead\b', 'On-Lead', result, flags=re.IGNORECASE)
    result = re.sub(r'\boff-lead\b', 'Off-Lead', result, flags=re.IGNORECASE)
    return result


def apply_majority_capitalization(
    class_name: str,
    prefer_uppercase: bool | None = None,
    original_name: str | None = None,
) -> str:
    """Set class name casing from majority of alphabetic characters; preserve canonical phrases."""
    if not class_name or _should_skip_capitalization(class_name):
        return class_name

    masked, masks = _mask_canonical_phrases(class_name)
    if prefer_uppercase is None:
        upper, lower = _alpha_case_counts(masked)
        prefer_uppercase = upper > lower

    preserve_upper = _original_uppercase_words(original_name or class_name)

    if prefer_uppercase:
        result = masked.upper()
    else:
        result = _apply_title_case(masked, preserve_upper=preserve_upper)

    return _unmask_phrases(result, masks)


def normalize_class_name_full(class_name: str, division_name: str | None = None) -> str:
    if not class_name:
        return class_name
    if is_truncated_class_fragment(class_name):
        return ''
    class_name, _ = strip_entries_from_class_name(class_name)
    orig_upper, orig_lower = _alpha_case_counts(class_name)
    prefer_uppercase = orig_upper > orig_lower
    name = normalize_quotes(class_name).replace("\ufffd", "½")
    name = repair_leading_height_championship(name, division_name)
    name = repair_misclassified_class_name(name)
    if not name:
        return class_name
    name = normalize_championship_parenthetical(name, division_name)
    name = repair_class_name_ocr(name)
    name = normalize_legacy_class_format(name)
    name = repair_adult_class_ocr(name)
    name = repair_racing_word_ocr(name)
    name = repair_half_fraction_ocr(name)
    name = repair_corrupted_height_prefix(name, division_name)
    name = normalize_class_name(name)
    name = normalize_quotes(name)
    name = repair_half_fraction_ocr(name)
    name = repair_mangled_over_12_15(name)
    name = normalize_age_ranges(name)
    name = normalize_height_categories(name, division_name)
    name = standardize_height_phrases(name, division_name)
    name = fix_puppy_height_format(name, division_name)
    name = consolidate_height_variants(name)
    name = repair_corrupted_height_prefix(name, division_name)
    name = _collapse_height_quotes(name)
    name = consolidate_height_variants(name)
    name = repair_mangled_over_12_15(name)
    name = repair_class_name_ocr(name)
    name = normalize_coat_types(name)
    name = repair_racing_championship_height(name, division_name)
    name = normalize_championship_class(name, division_name)
    name = repair_trailing_height_fragment(name)
    name = finalize_class_name_formatting(name)
    name = apply_majority_capitalization(
        name,
        prefer_uppercase=prefer_uppercase,
        original_name=class_name,
    )
    name = normalize_coat_types(name)
    name = re.sub(r'12½"([A-Za-z])', r'12½" \1', name)
    name = re.sub(r'15"([A-Za-z])', r'15" \1', name)
    name = repair_duplicate_up_to_12(name)
    return re.sub(r"\s+", " ", name).strip()


def fix_ocr_word_spacing(text: str) -> str:
    if not text:
        return text
    text = re.sub(r"\band([A-Z][a-z])", r"and \1", text)
    text = re.sub(r"\bby([A-Z][a-z])", r"by \1", text)
    text = re.sub(r"\s*&\s*", " & ", text)
    text = re.sub(r",([A-Za-z])", r", \1", text)
    text = re.sub(r"\s+", " ", text).strip(" ,.")
    return text


def split_embedded_owner(text: str) -> tuple[str, str]:
    """Return (dog_name, owner_name) when owner text is embedded in a dog field."""
    if not text:
        return "", ""
    cleaned = normalize_owned_by_text(text)
    if ", owned by " in cleaned:
        dog, owner = cleaned.split(", owned by ", 1)
        return dog.strip(" ,"), owner.strip()
    return text.strip(), ""


def normalize_dog_name(name: str) -> str:
    if not name:
        return name

    name = name.strip()
    name = PLACEMENT_PREFIX_RE.sub("", name)
    name = SIZE_CHAMPION_PREFIX_RE.sub("", name)
    name = name.lstrip("_ ").strip()

    dog, _owner = split_embedded_owner(name)
    name = dog or name

    name = re.sub(r"owned\s*by\s*$", "", name, flags=re.IGNORECASE).strip(" ,")
    name = fix_ocr_word_spacing(name)
    name = collapse_mc_prefix(name)
    name = re.sub(r"[\u0000-\u001f\u007f-\u009f\ufffd]", "", name)
    name = re.sub(r"\s+", " ", name).strip(" ,.")
    return name


def normalize_owner_name(name: str) -> str:
    if not name:
        return name

    name = name.strip()
    name = clean_parsed_owner_name(name)

    # Racing time rows accidentally stored as owners
    if INVALID_OWNER_RE.match(name) or re.search(r"\bowned by\b.*\bowned by\b", name, re.I):
        parts = re.split(r"owned\s*by\s*", name, flags=re.IGNORECASE)
        parts = [p.strip(" ,.") for p in parts if p.strip(" ,.")]
        if parts:
            name = parts[-1]

    name = normalize_owned_by_text(name)
    if ", owned by " in name:
        before, after = name.split(", owned by ", 1)
        after = after.strip()
        if RACE_TIME_SUFFIX_RE.match(after):
            name = before.strip()
        else:
            name = after

    name = fix_ocr_word_spacing(name)
    name = collapse_mc_prefix(name)
    name = re.sub(r"^[\d:$.,\s]+", "", name).strip()
    name = re.sub(r"[\u0000-\u001f\u007f-\u009f\ufffd]", "", name)
    name = re.sub(r"\s+", " ", name).strip(" ,.")
    return name


def person_cluster_key(name: str) -> str:
    collapsed = collapse_mc_prefix(name).lower()
    collapsed = re.sub(r"[''`]", "", collapsed)
    return re.sub(r"[^a-z0-9]", "", collapsed)


def _owners_compatible(owner_ids: set[int | None]) -> bool:
    known = {oid for oid in owner_ids if oid is not None}
    return len(known) <= 1


def _partition_ids_by_owner(ids: list[int], owner_map: dict[int, int | None]) -> list[list[int]]:
    groups: list[list[int]] = []
    for dog_id in sorted(ids):
        owner_id = owner_map.get(dog_id)
        placed = False
        for group in groups:
            group_owners = {owner_map.get(did) for did in group}
            if _owners_compatible(group_owners | {owner_id}):
                group.append(dog_id)
                placed = True
                break
        if not placed:
            groups.append([dog_id])
    return [group for group in groups if len(group) > 1]


def pick_canonical_person_name(names: list[str]) -> str:
    if not names:
        return ""
    # Prefer McCarthy/McDonald over Mc Carthy/Mac Donald when both exist
    no_mc_space = [n for n in names if not re.search(r"\b(Mc|Mac)\s+", n, re.I)]
    candidates = no_mc_space if no_mc_space else names
    return collapse_mc_prefix(find_canonical_name_for_similar_names(candidates))


def entity_descriptiveness_score(name: str) -> tuple[int, int]:
    name = name or ""
    return (
        1 if " of " in name.lower() else 0,
        len(name),
    )


def entity_keep_score(entity_id: int, name: str, rel_counts: dict[int, int]) -> tuple:
    desc = entity_descriptiveness_score(name)
    return (
        rel_counts.get(entity_id, 0),
        desc[0],
        desc[1],
        -entity_id,
    )


def load_dog_relationship_counts(cursor) -> dict[int, int]:
    cursor.execute(
        """
        SELECT DogID, COUNT(*) AS RelCount
        FROM (
            SELECT DogID FROM sResults.Relationship WHERE DogID IS NOT NULL
            UNION ALL
            SELECT RelatedDogID FROM sResults.Relationship WHERE RelatedDogID IS NOT NULL
        ) rels
        GROUP BY DogID
        """
    )
    return {row[0]: row[1] for row in cursor.fetchall()}


def load_dog_placement_counts(cursor) -> dict[int, int]:
    cursor.execute(
        """
        SELECT DogID, COUNT(*) AS PlacementCount
        FROM sResults.TrialPlacements
        WHERE DogID IS NOT NULL
        GROUP BY DogID
        """
    )
    return {row[0]: row[1] for row in cursor.fetchall()}


def load_dog_metadata(cursor) -> dict[int, tuple]:
    cursor.execute(
        """
        SELECT DogID, DogName, OwnerID, Sire, Dam, Sex
        FROM sResults.Dog
        WHERE DogName IS NOT NULL AND LTRIM(RTRIM(DogName)) <> ''
        """
    )
    return {
        row[0]: (row[0], row[1], row[2], row[3], row[4], row[5])
        for row in cursor.fetchall()
    }


def _sex_is_known(sex) -> bool:
    if not sex:
        return False
    return str(sex).strip().lower() not in ('', 'unknown', 'u', 'n/a')


def dog_completeness_score(sire, dam, sex) -> int:
    score = 0
    if sire and str(sire).strip():
        score += 1
    if dam and str(dam).strip():
        score += 1
    if _sex_is_known(sex):
        score += 1
    return score


def dog_similarity_key(name: str) -> str:
    key = normalize_for_matching(normalize_name(name))
    return key.split()[0] if key else ""


def cluster_dog_ids_by_similarity(
    rows: list[tuple[int, str]],
) -> list[list[int]]:
    """Group dog IDs with similar names (typo/OCR variants) via first-word index."""
    index: dict[str, list[tuple[int, str]]] = defaultdict(list)
    for dog_id, dog_name in rows:
        first_word = dog_similarity_key(dog_name)
        if not first_word:
            continue
        index[first_word].append((dog_id, dog_name))

    clusters: list[list[int]] = []
    for bucket in index.values():
        parent = list(range(len(bucket)))

        def find(x: int) -> int:
            while parent[x] != x:
                parent[x] = parent[parent[x]]
                x = parent[x]
            return x

        def union(a: int, b: int) -> None:
            root_a, root_b = find(a), find(b)
            if root_a != root_b:
                parent[root_b] = root_a

        for i in range(len(bucket)):
            for j in range(i + 1, len(bucket)):
                if names_are_similar(bucket[i][1], bucket[j][1]):
                    union(i, j)

        groups: dict[int, list[int]] = defaultdict(list)
        for i, (dog_id, _name) in enumerate(bucket):
            groups[find(i)].append(dog_id)

        for group in groups.values():
            if len(group) > 1:
                clusters.append(group)
    return clusters


def dog_keep_score(
    entity_id: int,
    meta: tuple,
    rel_counts: dict[int, int],
    placement_counts: dict[int, int],
) -> tuple:
    _dog_id, name, _owner_id, sire, dam, sex = meta
    desc = entity_descriptiveness_score(name)
    return (
        dog_completeness_score(sire, dam, sex),
        placement_counts.get(entity_id, 0),
        rel_counts.get(entity_id, 0),
        desc[0],
        desc[1],
        -entity_id,
    )


def pick_keep_dog_id(
    ids: list[int],
    meta_by_id: dict[int, tuple],
    rel_counts: dict[int, int],
    placement_counts: dict[int, int],
) -> int:
    return max(
        ids,
        key=lambda entity_id: dog_keep_score(
            entity_id, meta_by_id[entity_id], rel_counts, placement_counts,
        ),
    )


def best_pedigree_from_cluster(
    ids: list[int],
    meta_by_id: dict[int, tuple],
) -> tuple:
    best_sire = best_dam = best_sex = None
    best_score = -1
    for entity_id in ids:
        _dog_id, _name, _owner_id, sire, dam, sex = meta_by_id[entity_id]
        score = dog_completeness_score(sire, dam, sex)
        if score > best_score:
            best_score = score
            best_sire, best_dam, best_sex = sire, dam, sex
    return best_sire, best_dam, best_sex


def load_owner_relationship_counts(
    dog_rows: list[tuple[int, str, int | None]],
    dog_rel_counts: dict[int, int],
) -> dict[int, int]:
    owner_counts: dict[int, int] = defaultdict(int)
    for dog_id, _name, owner_id in dog_rows:
        if owner_id is None:
            continue
        owner_counts[owner_id] += dog_rel_counts.get(dog_id, 0)
    return owner_counts


def pick_keep_entity_id(
    ids: list[int],
    names_by_id: dict[int, str],
    rel_counts: dict[int, int],
) -> int:
    return max(ids, key=lambda entity_id: entity_keep_score(
        entity_id, names_by_id.get(entity_id, ""), rel_counts,
    ))


def pick_canonical_name_for_cluster(
    entries: list[tuple[int, str]],
    rel_counts: dict[int, int],
) -> str:
    """Pick canonical name favoring variants with more relationships."""
    if not entries:
        return ""
    best_rel = max(rel_counts.get(entity_id, 0) for entity_id, _ in entries)
    candidate_names = [
        name for entity_id, name in entries if rel_counts.get(entity_id, 0) == best_rel
    ]
    return pick_canonical_person_name(candidate_names)


def cluster_key(name: str) -> str:
    return re.sub(r"[^a-z0-9']", "", name.lower())


def cluster_names(
    rows: list[tuple[int, str]],
    key_fn=cluster_key,
    canonical_fn=find_canonical_name_for_similar_names,
) -> dict[int, str]:
    """Cluster names by normalized key and pick the most descriptive canonical form."""
    buckets: dict[str, list[tuple[int, str]]] = defaultdict(list)
    for row_id, raw_name in rows:
        norm_name = raw_name.strip()
        if not norm_name:
            continue
        buckets[key_fn(norm_name)].append((row_id, norm_name))

    mapping: dict[int, str] = {}
    for group in buckets.values():
        names = [name for _, name in group]
        canonical = canonical_fn(names)
        for row_id, _ in group:
            mapping[row_id] = canonical
    return mapping


def merge_duplicate_divisions(conn, dry_run: bool, verbose: bool = True) -> int:
    cursor = conn.cursor()
    cursor.execute(
        """
        SELECT DivisionName, MIN(DivisionID) AS KeepID
        FROM sResults.Division
        GROUP BY DivisionName
        HAVING COUNT(*) > 1
        """
    )
    groups = cursor.fetchall()
    merged = 0

    if verbose and groups:
        print_ts(f"Found {len(groups):,} duplicate division groups to merge")
    elif verbose:
        print_ts("No duplicate division groups to merge")

    for idx, (division_name, keep_id) in enumerate(groups, start=1):
        cursor.execute(
            """
            SELECT DivisionID FROM sResults.Division
            WHERE DivisionName = ?
            """,
            division_name,
        )
        ids = [row[0] for row in cursor.fetchall() if row[0] != keep_id]
        for dup_id in ids:
            merged += 1
            if verbose and not dry_run:
                print_ts(f"  Division merge: {division_name!r} dup {dup_id} -> keep {keep_id}")
            if dry_run:
                continue
            cursor.execute(
                "UPDATE sResults.Class SET DivisionID = ? WHERE DivisionID = ?",
                keep_id,
                dup_id,
            )
            cursor.execute("DELETE FROM sResults.Division WHERE DivisionID = ?", dup_id)

        if idx % 500 == 0 or idx == len(groups):
            print_progress("Division merge", idx, len(groups), f"{merged:,} IDs consolidated")

    if not dry_run and merged:
        conn.commit()
    return merged


def merge_duplicate_classes(conn, dry_run: bool) -> int:
    cursor = conn.cursor()
    cursor.execute(
        """
        SELECT DivisionID, ClassName, MIN(ClassID) AS KeepID
        FROM sResults.Class
        GROUP BY DivisionID, ClassName
        HAVING COUNT(*) > 1
        """
    )
    groups = cursor.fetchall()
    merged = 0

    print_ts(f"Found {len(groups):,} duplicate class groups to merge")

    for idx, (division_id, class_name, keep_id) in enumerate(groups, start=1):
        cursor.execute(
            """
            SELECT ClassID FROM sResults.Class
            WHERE DivisionID = ? AND ClassName = ?
            """,
            division_id,
            class_name,
        )
        ids = [row[0] for row in cursor.fetchall() if row[0] != keep_id]
        for dup_id in ids:
            merged += 1
            if dry_run:
                continue
            cursor.execute(
                "UPDATE sResults.TrialClass SET ClassID = ? WHERE ClassID = ?",
                keep_id,
                dup_id,
            )
            cursor.execute(
                "UPDATE sResults.CatalogEntry SET ClassID = ? WHERE ClassID = ?",
                keep_id,
                dup_id,
            )
            cursor.execute("DELETE FROM sResults.Class WHERE ClassID = ?", dup_id)

        if idx % 500 == 0 or idx == len(groups):
            print_progress("Class merge", idx, len(groups), f"{merged:,} IDs consolidated")

    if not dry_run and merged:
        conn.commit()
    return merged


def merge_duplicate_owners(conn, dry_run: bool, scope_ids: set[int] | None = None) -> int:
    cursor = conn.cursor()
    print_ts("Loading owners for duplicate merge...")
    if scope_ids:
        placeholders = ",".join("?" * len(scope_ids))
        cursor.execute(
            f"""
            SELECT OwnerID, OwnerName
            FROM sResults.Owner
            WHERE OwnerID IN ({placeholders})
            ORDER BY OwnerID
            """,
            *scope_ids,
        )
    else:
        cursor.execute("SELECT OwnerID, OwnerName FROM sResults.Owner ORDER BY OwnerID")
    rows = [(r[0], r[1]) for r in cursor.fetchall() if r[1]]
    print_ts(f"Clustering {len(rows):,} owner names...")
    mapping = cluster_names(rows, key_fn=person_cluster_key, canonical_fn=pick_canonical_person_name)

    by_canonical: dict[str, list[int]] = defaultdict(list)
    for owner_id, canonical in mapping.items():
        by_canonical[canonical].append(owner_id)

    dup_groups = [(canonical, ids) for canonical, ids in by_canonical.items() if len(ids) > 1]
    if scope_ids:
        dup_groups = [
            (canonical, ids)
            for canonical, ids in dup_groups
            if scope_ids.intersection(ids)
        ]
    scope_note = " (trial-scoped)" if scope_ids else ""
    print_ts(f"Found {len(dup_groups):,} duplicate owner groups{scope_note}")

    merged = 0
    cursor.execute(
        "SELECT DogID, DogName, OwnerID FROM sResults.Dog WHERE OwnerID IS NOT NULL"
    )
    dog_rows = cursor.fetchall()
    dog_rel_counts = load_dog_relationship_counts(cursor)
    owner_rel_counts = load_owner_relationship_counts(dog_rows, dog_rel_counts)
    names_by_id = {owner_id: owner_name for owner_id, owner_name in rows}

    for idx, (_canonical, ids) in enumerate(dup_groups, start=1):
        keep_id = pick_keep_entity_id(ids, names_by_id, owner_rel_counts)
        canonical_name = pick_canonical_name_for_cluster(
            [(entity_id, names_by_id[entity_id]) for entity_id in ids],
            owner_rel_counts,
        )
        for dup_id in ids:
            if dup_id == keep_id:
                continue
            merged += 1
            if dry_run:
                continue
            cursor.execute(
                "UPDATE sResults.Dog SET OwnerID = ? WHERE OwnerID = ?",
                keep_id,
                dup_id,
            )
            cursor.execute(
                "UPDATE sResults.CatalogEntry SET OwnerID = ? WHERE OwnerID = ?",
                keep_id,
                dup_id,
            )
            cursor.execute("DELETE FROM sResults.Owner WHERE OwnerID = ?", dup_id)

        if not dry_run and canonical_name and canonical_name != names_by_id.get(keep_id):
            cursor.execute(
                "UPDATE sResults.Owner SET OwnerName = ? WHERE OwnerID = ?",
                canonical_name,
                keep_id,
            )

        if idx % 500 == 0 or idx == len(dup_groups):
            print_progress("Owner merge", idx, len(dup_groups), f"{merged:,} IDs consolidated")

    if not dry_run and merged:
        conn.commit()
    return merged


def merge_duplicate_dogs(conn, dry_run: bool, scope_ids: set[int] | None = None) -> int:
    cursor = conn.cursor()
    print_ts("Loading dogs for duplicate merge...")
    if scope_ids:
        placeholders = ",".join("?" * len(scope_ids))
        cursor.execute(
            f"""
            SELECT DogID, DogName, OwnerID, Sire, Dam, Sex
            FROM sResults.Dog
            WHERE DogID IN ({placeholders})
              AND DogName IS NOT NULL AND LTRIM(RTRIM(DogName)) <> ''
            """,
            *scope_ids,
        )
        meta_by_id = {
            row[0]: (row[0], row[1], row[2], row[3], row[4], row[5])
            for row in cursor.fetchall()
        }
    else:
        meta_by_id = load_dog_metadata(cursor)
    rows = [
        (dog_id, meta[1], meta[2])
        for dog_id, meta in meta_by_id.items()
    ]
    print_ts(f"Clustering {len(rows):,} dog names by similarity...")
    dup_clusters = cluster_dog_ids_by_similarity(
        [(dog_id, dog_name) for dog_id, dog_name, _owner_id in rows],
    )
    if scope_ids:
        dup_clusters = [
            cluster
            for cluster in dup_clusters
            if scope_ids.intersection(cluster)
        ]
    scope_note = " (trial-scoped)" if scope_ids else ""
    print_ts(f"Found {len(dup_clusters):,} duplicate dog groups{scope_note}")

    dog_rel_counts = load_dog_relationship_counts(cursor)
    placement_counts = load_dog_placement_counts(cursor)
    names_by_id = {dog_id: meta[1] for dog_id, meta in meta_by_id.items()}

    merged = 0
    for idx, merge_ids in enumerate(dup_clusters, start=1):
        keep_id = pick_keep_dog_id(
            merge_ids, meta_by_id, dog_rel_counts, placement_counts,
        )
        canonical_name = pick_canonical_person_name(
            [names_by_id[entity_id] for entity_id in merge_ids],
        )
        best_sire, best_dam, best_sex = best_pedigree_from_cluster(merge_ids, meta_by_id)
        for dup_id in merge_ids:
            if dup_id == keep_id:
                continue
            merged += 1
            if dry_run:
                continue
            cursor.execute(
                "UPDATE sResults.TrialPlacements SET DogID = ? WHERE DogID = ?",
                keep_id,
                dup_id,
            )
            cursor.execute(
                "UPDATE sResults.CatalogEntry SET DogID = ? WHERE DogID = ?",
                keep_id,
                dup_id,
            )
            cursor.execute(
                "UPDATE sResults.Relationship SET DogID = ? WHERE DogID = ?",
                keep_id,
                dup_id,
            )
            cursor.execute(
                "UPDATE sResults.Relationship SET RelatedDogID = ? WHERE RelatedDogID = ?",
                keep_id,
                dup_id,
            )
            cursor.execute("DELETE FROM sResults.Dog WHERE DogID = ?", dup_id)

        if dry_run:
            if idx % 500 == 0 or idx == len(dup_clusters):
                print_progress("Dog merge", idx, len(dup_clusters), f"{merged:,} IDs consolidated")
            continue

        keeper_meta = meta_by_id[keep_id]
        updates = []
        params = []
        if canonical_name and canonical_name != keeper_meta[1]:
            updates.append("DogName = ?")
            params.append(canonical_name)
        if best_sire and not (keeper_meta[3] and str(keeper_meta[3]).strip()):
            updates.append("Sire = ?")
            params.append(best_sire)
        if best_dam and not (keeper_meta[4] and str(keeper_meta[4]).strip()):
            updates.append("Dam = ?")
            params.append(best_dam)
        if best_sex and not _sex_is_known(keeper_meta[5]):
            updates.append("Sex = ?")
            params.append(best_sex)
        if updates:
            params.append(keep_id)
            cursor.execute(
                f"UPDATE sResults.Dog SET {', '.join(updates)} WHERE DogID = ?",
                params,
            )

        if idx % 500 == 0 or idx == len(dup_clusters):
            print_progress("Dog merge", idx, len(dup_clusters), f"{merged:,} IDs consolidated")

    if not dry_run and merged:
        conn.commit()
    return merged


def update_class_table_names(conn, dry_run: bool, sample_limit: int = 15) -> tuple[int, int]:
    """Normalize ClassName using each row's DivisionName as context."""
    cursor = conn.cursor()
    print_ts("Loading Class.ClassName with Division.DivisionName...")
    cursor.execute(
        """
        SELECT c.ClassID, c.ClassName, d.DivisionName
        FROM sResults.Class c
        JOIN sResults.Division d ON d.DivisionID = c.DivisionID
        """
    )
    rows = cursor.fetchall()
    print_ts(f"Scanning {len(rows):,} class rows for ClassName changes...")

    changes = []
    for idx, (class_id, class_name, division_name) in enumerate(rows, start=1):
        if class_name is None:
            continue
        new_name = normalize_class_name_full(class_name, division_name)
        if new_name and new_name != class_name:
            changes.append((class_id, class_name, new_name))
        if idx % 10000 == 0 or idx == len(rows):
            print_progress("Scan Class", idx, len(rows), f"{len(changes):,} changes found")

    print_ts(f"Class.ClassName: {len(changes):,} rows to update (of {len(rows):,})")
    for old, new in [(o, n) for _, o, n in changes[:sample_limit]]:
        print(f"  {old!r} -> {new!r}")

    if dry_run:
        return len(changes), 0

    print_ts(f"Writing {len(changes):,} Class.ClassName updates...")
    batch_size = 500
    updated = 0
    for i in range(0, len(changes), batch_size):
        batch = changes[i : i + batch_size]
        for class_id, _, new_name in batch:
            cursor.execute(
                "UPDATE sResults.Class SET ClassName = ? WHERE ClassID = ?",
                new_name,
                class_id,
            )
            updated += 1
        conn.commit()
        print_progress("Update Class", updated, len(changes))

    print_ts("Finished Class.ClassName updates")
    return len(changes), updated


def update_table_names(
    conn,
    table: str,
    id_col: str,
    name_col: str,
    normalizer,
    dry_run: bool,
    sample_limit: int = 15,
) -> tuple[int, int]:
    cursor = conn.cursor()
    print_ts(f"Loading {table}.{name_col}...")
    cursor.execute(f"SELECT {id_col}, {name_col} FROM sResults.{table}")
    rows = cursor.fetchall()
    print_ts(f"Scanning {len(rows):,} rows for {table}.{name_col} changes...")

    changes = []
    for idx, (row_id, raw_name) in enumerate(rows, start=1):
        if raw_name is None:
            continue
        new_name = normalizer(raw_name)
        if new_name and new_name != raw_name:
            changes.append((row_id, raw_name, new_name))
        if idx % 10000 == 0 or idx == len(rows):
            print_progress(f"Scan {table}", idx, len(rows), f"{len(changes):,} changes found")

    print_ts(f"{table}.{name_col}: {len(changes):,} rows to update (of {len(rows):,})")
    for old, new in [(o, n) for _, o, n in changes[:sample_limit]]:
        print(f"  {old!r} -> {new!r}")

    if dry_run:
        return len(changes), 0

    print_ts(f"Writing {len(changes):,} {table}.{name_col} updates...")
    batch_size = 500
    updated = 0
    for i in range(0, len(changes), batch_size):
        batch = changes[i : i + batch_size]
        for row_id, _, new_name in batch:
            cursor.execute(
                f"UPDATE sResults.{table} SET {name_col} = ? WHERE {id_col} = ?",
                new_name,
                row_id,
            )
            updated += 1
        conn.commit()
        print_progress(f"Update {table}", updated, len(changes))

    print_ts(f"Finished {table}.{name_col} updates")
    return len(changes), updated


def _get_trial_entity_ids(cursor, trial_id: int) -> tuple[list[int], list[int], list[int]]:
    cursor.execute(
        """
        SELECT DISTINCT tc.ClassID
        FROM sResults.TrialClass tc
        WHERE tc.TrialListID = ?
        """,
        trial_id,
    )
    class_ids = [row[0] for row in cursor.fetchall()]

    cursor.execute(
        """
        SELECT DISTINCT tp.DogID
        FROM sResults.TrialPlacements tp
        WHERE tp.TrialListID = ?
        """,
        trial_id,
    )
    dog_ids = [row[0] for row in cursor.fetchall()]

    owner_ids = []
    if dog_ids:
        placeholders = ",".join("?" * len(dog_ids))
        cursor.execute(
            f"""
            SELECT DISTINCT d.OwnerID
            FROM sResults.Dog d
            WHERE d.DogID IN ({placeholders}) AND d.OwnerID IS NOT NULL
            """,
            *dog_ids,
        )
        owner_ids = [row[0] for row in cursor.fetchall()]

    return class_ids, dog_ids, owner_ids


def remap_false_divisions_for_trial(conn, trial_id: int) -> int:
    """Move classes from mis-parsed divisions (e.g. JUMPING) to canonical division (AGILITY)."""
    cursor = conn.cursor()
    cursor.execute(
        """
        SELECT tc.TrialClassID, c.ClassID, c.ClassName, d.DivisionName
        FROM sResults.TrialClass tc
        JOIN sResults.Class c ON c.ClassID = tc.ClassID
        JOIN sResults.Division d ON d.DivisionID = c.DivisionID
        WHERE tc.TrialListID = ?
        """,
        trial_id,
    )
    rows = cursor.fetchall()
    remapped = 0
    for trial_class_id, class_id, class_name, division_name in rows:
        target_division = normalize_stored_division_name(division_name)
        if not target_division or target_division == division_name:
            continue

        cursor.execute(
            "SELECT DivisionID FROM sResults.Division WHERE DivisionName = ?",
            target_division,
        )
        div_row = cursor.fetchone()
        if div_row:
            target_div_id = div_row[0]
        else:
            cursor.execute(
                "INSERT INTO sResults.Division (DivisionName) OUTPUT INSERTED.DivisionID VALUES (?)",
                target_division,
            )
            target_div_id = cursor.fetchone()[0]

        cursor.execute(
            """
            SELECT ClassID FROM sResults.Class
            WHERE ClassName = ? AND DivisionID = ?
            """,
            class_name,
            target_div_id,
        )
        existing = cursor.fetchone()
        if existing:
            target_class_id = existing[0]
        else:
            cursor.execute(
                """
                INSERT INTO sResults.Class (ClassName, DivisionID)
                OUTPUT INSERTED.ClassID VALUES (?, ?)
                """,
                class_name,
                target_div_id,
            )
            target_class_id = cursor.fetchone()[0]

        if target_class_id != class_id:
            cursor.execute(
                "UPDATE sResults.TrialClass SET ClassID = ? WHERE TrialClassID = ?",
                target_class_id,
                trial_class_id,
            )
            remapped += 1

    if remapped:
        conn.commit()
    return remapped


def _get_trial_division_ids(cursor, trial_id: int) -> list[int]:
    cursor.execute(
        """
        SELECT DISTINCT c.DivisionID
        FROM sResults.TrialClass tc
        JOIN sResults.Class c ON c.ClassID = tc.ClassID
        WHERE tc.TrialListID = ?
        """,
        trial_id,
    )
    return [row[0] for row in cursor.fetchall()]


def update_division_names_for_ids(conn, division_ids: list[int], verbose: bool = True) -> int:
    if not division_ids:
        return 0

    cursor = conn.cursor()
    placeholders = ",".join("?" * len(division_ids))
    cursor.execute(
        f"SELECT DivisionID, DivisionName FROM sResults.Division WHERE DivisionID IN ({placeholders})",
        *division_ids,
    )

    updated = 0
    for division_id, raw_name in cursor.fetchall():
        if raw_name is None:
            continue
        new_name = normalize_division_name_full(raw_name)
        if new_name and new_name != raw_name:
            if verbose:
                print_ts(f"  Division {division_id}: {raw_name!r} -> {new_name!r}")
            cursor.execute(
                "UPDATE sResults.Division SET DivisionName = ? WHERE DivisionID = ?",
                new_name,
                division_id,
            )
            updated += 1
    return updated


def update_class_names_for_ids(conn, class_ids: list[int]) -> int:
    if not class_ids:
        return 0

    cursor = conn.cursor()
    placeholders = ",".join("?" * len(class_ids))
    cursor.execute(
        f"""
        SELECT c.ClassID, c.ClassName, d.DivisionName
        FROM sResults.Class c
        JOIN sResults.Division d ON d.DivisionID = c.DivisionID
        WHERE c.ClassID IN ({placeholders})
        """,
        *class_ids,
    )

    updated = 0
    for class_id, class_name, division_name in cursor.fetchall():
        if class_name is None:
            continue
        new_name = normalize_class_name_full(class_name, division_name)
        if new_name and new_name != class_name:
            cursor.execute(
                "UPDATE sResults.Class SET ClassName = ? WHERE ClassID = ?",
                new_name,
                class_id,
            )
            updated += 1
    return updated


def update_names_for_ids(
    conn,
    table: str,
    id_col: str,
    name_col: str,
    normalizer,
    entity_ids: list[int],
) -> int:
    if not entity_ids:
        return 0

    cursor = conn.cursor()
    placeholders = ",".join("?" * len(entity_ids))
    cursor.execute(
        f"SELECT {id_col}, {name_col} FROM sResults.{table} WHERE {id_col} IN ({placeholders})",
        *entity_ids,
    )

    updated = 0
    for row_id, raw_name in cursor.fetchall():
        if raw_name is None:
            continue
        new_name = normalizer(raw_name)
        if new_name and new_name != raw_name:
            cursor.execute(
                f"UPDATE sResults.{table} SET {name_col} = ? WHERE {id_col} = ?",
                new_name,
                row_id,
            )
            updated += 1
    return updated


def run_batch_post_trial_normalization(
    conn,
    trial_ids: list[int],
    *,
    skip_dog_owner_merge: bool = False,
) -> None:
    """Normalize entities touched by one or more trials in a single pass."""
    if not trial_ids:
        return

    cursor = conn.cursor()
    class_ids: set[int] = set()
    dog_ids: set[int] = set()
    owner_ids: set[int] = set()
    division_ids: set[int] = set()
    division_remapped = 0

    for trial_id in trial_ids:
        division_remapped += remap_false_divisions_for_trial(conn, trial_id)
        trial_class_ids, trial_dog_ids, trial_owner_ids = _get_trial_entity_ids(
            cursor, trial_id,
        )
        class_ids.update(trial_class_ids)
        dog_ids.update(trial_dog_ids)
        owner_ids.update(trial_owner_ids)
        division_ids.update(_get_trial_division_ids(cursor, trial_id))

    if division_remapped:
        class_ids.clear()
        dog_ids.clear()
        owner_ids.clear()
        division_ids.clear()
        for trial_id in trial_ids:
            trial_class_ids, trial_dog_ids, trial_owner_ids = _get_trial_entity_ids(
                cursor, trial_id,
            )
            class_ids.update(trial_class_ids)
            dog_ids.update(trial_dog_ids)
            owner_ids.update(trial_owner_ids)
            division_ids.update(_get_trial_division_ids(cursor, trial_id))

    if len(trial_ids) == 1:
        print_ts(f"Post-load normalization for trial {trial_ids[0]}")
    else:
        print_ts(
            f"Post-load normalization for {len(trial_ids):,} trials "
            f"(IDs {trial_ids[0]}-{trial_ids[-1]})",
        )
    print_ts(
        f"  Entities: {len(division_ids):,} divisions, {len(class_ids):,} classes, "
        f"{len(dog_ids):,} dogs, {len(owner_ids):,} owners",
    )
    if division_remapped:
        print_ts(f"  Division remaps: {division_remapped:,} trial classes")

    print_ts(f"  Normalizing {len(division_ids):,} division name(s)...")
    division_updates = update_division_names_for_ids(conn, list(division_ids))
    if division_updates == 0:
        print_ts("  No division name changes needed")
    division_merged = merge_duplicate_divisions(conn, dry_run=False)
    if division_merged:
        class_ids.clear()
        dog_ids.clear()
        owner_ids.clear()
        for trial_id in trial_ids:
            trial_class_ids, trial_dog_ids, trial_owner_ids = _get_trial_entity_ids(
                cursor, trial_id,
            )
            class_ids.update(trial_class_ids)
            dog_ids.update(trial_dog_ids)
            owner_ids.update(trial_owner_ids)
    if division_merged:
        print_ts(f"  Merged {division_merged:,} duplicate division ID(s)")

    class_updates = update_class_names_for_ids(conn, list(class_ids))
    dog_updates = update_names_for_ids(
        conn, "Dog", "DogID", "DogName", normalize_dog_name, list(dog_ids),
    )
    owner_updates = update_names_for_ids(
        conn, "Owner", "OwnerID", "OwnerName", normalize_owner_name, list(owner_ids),
    )
    print_ts(
        f"  Name updates: {class_updates:,} classes, {dog_updates:,} dogs, {owner_updates:,} owners",
    )

    class_merged = merge_duplicate_classes(conn, dry_run=False)
    if skip_dog_owner_merge:
        dog_merged = owner_merged = 0
        print_ts("  Skipping dog/owner merges (reusing existing catalog entities)")
    else:
        dog_merged = merge_duplicate_dogs(conn, dry_run=False, scope_ids=dog_ids)
        owner_merged = merge_duplicate_owners(conn, dry_run=False, scope_ids=owner_ids)
    print_ts(
        f"  Merges: {class_merged:,} class IDs, {dog_merged:,} dog IDs, {owner_merged:,} owner IDs",
    )
    conn.commit()
    if len(trial_ids) == 1:
        print_ts(f"Post-load normalization complete for trial {trial_ids[0]}")
    else:
        print_ts(f"Post-load normalization complete for {len(trial_ids):,} trials")


def run_post_trial_normalization(
    conn,
    trial_id: int,
    *,
    skip_dog_owner_merge: bool = False,
) -> None:
    """Normalize division/class/dog/owner names for entities loaded with a trial."""
    run_batch_post_trial_normalization(
        conn,
        [trial_id],
        skip_dog_owner_merge=skip_dog_owner_merge,
    )


def main():
    parser = argparse.ArgumentParser(description="Normalize TrialResults name data")
    parser.add_argument("--dry-run", action="store_true", help="Preview changes only")
    parser.add_argument("--skip-merge", action="store_true", help="Skip duplicate ID merges")
    parser.add_argument("--class-only", action="store_true")
    parser.add_argument("--division-only", action="store_true")
    parser.add_argument("--dog-only", action="store_true")
    parser.add_argument("--owner-only", action="store_true")
    args = parser.parse_args()

    run_all = not (args.class_only or args.division_only or args.dog_only or args.owner_only)
    dry_run = args.dry_run

    print("=" * 80)
    print("TRIAL RESULTS DATA NORMALIZER")
    print("=" * 80)
    if dry_run:
        print_ts("DRY RUN - no database changes will be committed")

    kill_other_normalizer_processes()

    conn = get_connection()
    print_ts("Connected to TrialResults")

    if run_all or args.division_only:
        print_ts("=== STEP: Divisions ===")
        print_ts("Phase 1/2: Normalize Division.DivisionName")
        update_table_names(
            conn, "Division", "DivisionID", "DivisionName", normalize_division_name_full, dry_run
        )
        if not args.skip_merge:
            print_ts("Phase 2/2: Merge duplicate divisions")
            merged = merge_duplicate_divisions(conn, dry_run)
            print_ts(f"Merged duplicate divisions: {merged:,}")

    if run_all or args.class_only:
        print_ts("=== STEP: Classes ===")
        print_ts("Phase 1/2: Normalize Class.ClassName (division-aware)")
        update_class_table_names(conn, dry_run)
        if not args.skip_merge:
            print_ts("Phase 2/2: Merge duplicate classes")
            merged = merge_duplicate_classes(conn, dry_run)
            print_ts(f"Merged duplicate classes: {merged:,}")

    if run_all or args.owner_only:
        print_ts("=== STEP: Owners ===")
        print_ts("Phase 1/2: Normalize Owner.OwnerName")
        update_table_names(conn, "Owner", "OwnerID", "OwnerName", normalize_owner_name, dry_run)
        if not args.skip_merge:
            print_ts("Phase 2/2: Merge duplicate owners")
            merged = merge_duplicate_owners(conn, dry_run)
            print_ts(f"Merged duplicate owners: {merged:,}")

    if run_all or args.dog_only:
        print_ts("=== STEP: Dogs ===")
        print_ts("Phase 1/2: Normalize Dog.DogName")
        update_table_names(conn, "Dog", "DogID", "DogName", normalize_dog_name, dry_run)
        if not args.skip_merge:
            print_ts("Phase 2/2: Merge duplicate dogs")
            merged = merge_duplicate_dogs(conn, dry_run)
            print_ts(f"Merged duplicate dogs: {merged:,}")

    conn.close()
    print_ts("Done")


if __name__ == "__main__":
    main()
