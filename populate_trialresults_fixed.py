#!/usr/bin/env python3
"""
Populate sResults schema tables with CORRECTLY parsed trial results from text files.

This version implements the correct parsing logic as specified:
- Extract trial name from duplicate lines before header block
- Parse header block for location, dates, chair, administrator, judges
- Parse results with correct handling of different placement formats
"""

import sys
import os
import re
import time
import subprocess
import html as html_module
import hashlib
from collections import defaultdict
from typing import List, Dict, Optional, Tuple
from dataclasses import dataclass
from datetime import datetime

# pyodbc is imported lazily (inside _require_pyodbc()) so that parsing functions
# and file-discovery functions work even when pyodbc is not installed.
# Only database-facing functions call _require_pyodbc() and will fail fast there.
_pyodbc = None  # populated on first call to _require_pyodbc()


def _require_pyodbc():
    """Return the pyodbc module, importing it on first use.  Exits with a
    descriptive message if the package or its underlying ODBC driver is absent.
    """
    global _pyodbc
    if _pyodbc is not None:
        return _pyodbc
    try:
        import pyodbc as _mod
        _pyodbc = _mod
        return _pyodbc
    except ImportError as err:
        _py = sys.executable
        print(
            f"\nERROR: cannot import pyodbc — {err}\n\n"
            f"Python running this script:\n  {_py}\n\n"
            f"Install pyodbc for THIS Python with:\n"
            f'  "{_py}" -m pip install pyodbc\n\n'
            "If pyodbc is already installed, the Microsoft ODBC Driver for SQL Server\n"
            "may be missing. Download it from: https://aka.ms/downloadmsodbcsql"
        )
        sys.exit(1)

# Force unbuffered output (skip when stdout is wrapped, e.g. log tee)
if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(line_buffering=True)
if hasattr(sys.stderr, 'reconfigure'):
    sys.stderr.reconfigure(line_buffering=True)

# Connection string
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

@dataclass
class TrialInfo:
    """Trial metadata extracted from file"""
    trial_name: str
    location: str = ""
    start_date: str = ""
    end_date: str = ""
    chair: str = ""
    administrator: str = ""
    judges: str = ""
    year: int = None

@dataclass
class PlacementResult:
    """A single placement result"""
    division: str
    class_name: str
    placement: str  # "1st", "2nd", "Champion", "Best", etc.
    dog_name: str
    owner_name: str
    entries: int = 0
    time: str = ""

# Set True via --verbose to print every division/class/placement during parsing
VERBOSE_OUTPUT = False

def safe_print(text: str, **kwargs):
    """
    Safely print text with special characters by encoding them as ASCII with backslash escapes.
    This ensures we can see what the special characters are in the console output.
    """
    if not VERBOSE_OUTPUT:
        return
    try:
        print(text, **kwargs)
        sys.stdout.flush()
    except UnicodeEncodeError:
        # Convert to ASCII representation so we can see the characters
        safe_text = text.encode('ascii', errors='backslashreplace').decode('ascii')
        print(safe_text, **kwargs)
        sys.stdout.flush()

# Placement line regex - optional size prefix (handles OCR like 10-12W', 1()'12'12", 12V2")
_ORDINAL_PLACEMENT = r'1\s*st|2\s*nd|3\s*r[a-z]{0,4}|4th|5th|6th'
# Word placements: single (Champion, Reserve, Best) and compound forms
# (Reserve Champion, Reserve Best, Reserve Choice, Reserve Working ...,
# Champion JRT Puppy, Best Working Dog, Working JRT Champion, ...).
# normalize_line_for_placement converts dash-style "Champion – Dog" to
# "Champion: Dog" before these patterns are applied, so only ':' is needed here.
_WORD_PLACEMENT = (
    r'(?:Working\s+JRT\s+)?'
    r'(?:Reserve\s+)?(?:Best|Champion)(?:\s+[\w/]+){0,10}'
    r'|Reserve(?:\s+[\w/]+){0,10}'
    r'|Best(?:\s+[\w/]+){0,10}'
    r'|Champion(?:\s+[\w/]+){0,10}'
    r'|Reserve'
)
_SIZE_PREFIX = r'[\d\w\-½%"/\'\s.,·°()]'
# Ordinals allow optional space/colon/apostrophe before rest; Best/Reserve/Champion require ':'.
_PLACEMENT_SEP = (
    rf"(?:(?:{_ORDINAL_PLACEMENT})\s*[:'~\s]+|(?:{_WORD_PLACEMENT})\s*:\s*)"
)
PLACEMENT_LINE_RE = re.compile(
    rf'^({_SIZE_PREFIX}*?)\s*{_PLACEMENT_SEP}(.+)',
    re.IGNORECASE
)
PLACEMENT_LINE_START_RE = re.compile(
    rf'^{_SIZE_PREFIX}*?\s*{_PLACEMENT_SEP}',
    re.IGNORECASE
)
# Size prefix + ~: with no placement word (OCR dropped "Champion") e.g. 1()'12'12"~: Dog, owned by Owner
IMPLICIT_CHAMPION_RE = re.compile(
    rf'^({_SIZE_PREFIX}*?)\s*~:\s*(.+)',
    re.IGNORECASE
)
# Placements glued on one line when HTML <BR> tags are stripped (e.g. "Owner2nd: Dog, owned by ...")
# Ordinals/Best: allow " in lookbehind (e.g. glued after a quote).
# Champion/Reserve: exclude " and ' so OCR height lines like "10-12 '/2' Champion:" are not split.
GLUED_ORDINAL_PLACEMENT_SPLIT_RE = re.compile(
    r'(?<=[A-Za-z0-9\'"&)/.])\s*(?=(?:\d{1,2}(?:st|nd|rd|th)|Best)\s*:)',
    re.IGNORECASE,
)
GLUED_CHAMPION_PLACEMENT_SPLIT_RE = re.compile(
    r'(?<=[A-Za-z0-9&)/.])\s*(?=(?:Reserve|Champion)\s*:)',
    re.IGNORECASE,
)
# Combined pattern for owner-field cleanup (search earliest match)
GLUED_PLACEMENT_SPLIT_RE = re.compile(
    r'(?<=[A-Za-z0-9\'"&)/.])\s*(?=(?:\d{1,2}(?:st|nd|rd|th)|Best)\s*:)'
    r'|(?<=[A-Za-z0-9&)/.])\s*(?=(?:Reserve|Champion)\s*:)',
    re.IGNORECASE,
)
_RACING_HEIGHT_PREFIX_RE = re.compile(
    r'^(?:'
    r'10\s*"?\s*up\s+to\s+|'
    r'10[\s.\-]+12|'
    r'12\s*[%½]|'
    r'over\s+|'
    r'up\s+to\s+'
    r')[\d\s/½"\-.%\'(),:·°]+["\'½]?\s*$',
    re.IGNORECASE,
)
_RACING_CHAMPION_CLASS_RE = re.compile(r'RAC(?:ING|M)\s+CHAMPION\s*&\s*RESERVE', re.IGNORECASE)
_CHAMPIONSHIP_CLASS_RE = re.compile(
    r'CHAMPION\s*(?:&|AND)\s*RESERVE|HIGH\s+POINT\s+CHAMPION',
    re.IGNORECASE,
)
_HEIGHT_ONLY_CLASS_RE = re.compile(
    r'^(?:10\s*"\s*up\s+to\s+12\s*½\s*"|Over\s+12\s*½\s*"\s*up\s+to\s+15\s*"|Up\s+to\s+12\s*½\s*"|'
    r'12\s*½\s*"\s*up\s+to\s+15\s*"|15\s*")$',
    re.IGNORECASE,
)
_CLASS_KEYWORD_RE = re.compile(
    r'\b(?:Dog|Dogs|Bitch|Bitches|Pup|Pups|Puppy|Puppies|Veteran|Senior|Adult|'
    r'Championship|Champion|Certificate|GTG|GO-TO-GROUND|RACING|SUPER\s+EARTH|'
    r'Working|Open|Handler|Stakes|Novice|Agility|Conformation)\b',
    re.IGNORECASE,
)
_TRUNCATED_CLASS_PREFIX_RE = re.compile(
    r'^(?:Dog|Dogs|Bitch|Bitches|Pup|Pups|Puppy|Puppies)\s*,?\s*'
    r'(?:[a-z]{1,2}|\d{1,2})\s*$',
    re.IGNORECASE,
)
OWNER_NAME_MAX_LEN = 100


def is_truncated_class_fragment(name: str) -> bool:
    """True for OCR line-break garbage like 'Dog, s' from a split 'Dogs, ...' header."""
    if not name:
        return False
    s = name.strip()
    if re.fullmatch(r'(?:Dog|Dogs|Bitch|Bitches|Pup|Pups|Puppy|Puppies)\s*', s, re.IGNORECASE):
        return True
    return bool(_TRUNCATED_CLASS_PREFIX_RE.match(s))


def is_plausible_class_name(name: str) -> bool:
    """Reject placement lines, page numbers, and other non-class text."""
    if not name or len(name.strip()) < 3:
        return False
    s = name.strip()
    if is_placement_line_start(s):
        return False
    if re.match(r'^:\s*\d+\s*$', s):
        return False
    if re.match(r'^[\d"\')\s\\.:;~\-]+$', s):
        return False
    if re.match(r'^&\s', s):
        return False
    if ', owned by ' in s.lower() or re.search(r'\bovmed\b', s, re.IGNORECASE):
        return False
    if re.search(r'Champion:\s*\S', s, re.IGNORECASE):
        return False
    # Sponsor / trophy / dedication lines (common in MO Earthdogs PDFs between
    # a Class header and its Champion/Reserve placements)
    low = s.lower()
    if (
        low.startswith('sponsored by')
        or ' sponsored by ' in low
        or low.endswith(' sponsored by')
        or low.startswith('for the ')
        or 'perpetual trophy' in low
        or low.startswith('in memory of')
        or low.startswith('in honor of')
        or low.startswith('honoring ')
        or low.startswith('missing and remembering')
    ):
        return False
    if _HEIGHT_ONLY_CLASS_RE.match(s):
        return False
    if is_truncated_class_fragment(s):
        return False
    if _CLASS_KEYWORD_RE.search(s):
        return True
    if re.search(r'\d+\s+up\s+to\s+\d+\s+month', s, re.IGNORECASE):
        return True
    return len(s) >= 10 and bool(re.search(r'[A-Za-z]{4,}', s))

def repair_racing_class_ocr(text: str) -> str:
    """Fix OCR typos in racing class headers (e.g. RACM -> RACING)."""
    if not text:
        return text
    return re.sub(r'\bRACM\b', 'RACING', text, flags=re.IGNORECASE)


def _normalize_fragment_for_classify(text: str) -> str:
    t = text.strip()
    for ch in ('·', '–', '—', '\u00b7'):
        t = t.replace(ch, ' ')
    t = t.replace("'", ' ').replace('"', ' ')
    t = re.sub(r'\s+', ' ', t).strip().lower()
    t = re.sub(r'12\s*1\s*/\s*2', '12½', t)
    t = re.sub(r'121/?2', '12½', t)
    t = re.sub(r'12112', '12½', t)
    return t


def classify_height_fragment(text: str) -> str | None:
    """Classify OCR height fragment as ten_12, over_15, or up_12."""
    t = _normalize_fragment_for_classify(text)
    if not t:
        return None

    if re.search(r'(?:^10[\s./%-]|^10\s*up\s*to\s*12|1\s*\(\s*\)\s*12)', t):
        return 'ten_12'

    if re.search(r'up\s+to\s+12', t) and not re.search(r'\b15\b', t):
        return 'up_12'

    if re.search(r'(?:^over\s+12|\b15\b|12\s*½?\s*[-\s.%]+15|12\s*%\s*15)', t):
        return 'over_15'

    if re.search(r'12\s*½\s*-?\s*15', t):
        return 'over_15'

    if re.search(r'^12\s', t) and re.search(r'15', t):
        return 'over_15'

    return None


def canonicalize_height_fragment(text: str, puppy: bool = False) -> str:
    """Map OCR height fragments to canonical JRTCA height phrases."""
    if not text or not text.strip():
        return text
    cat = classify_height_fragment(text)
    if cat == 'over_15':
        return 'Over 12½" up to 15"'
    if cat == 'up_12':
        return 'Up to 12½"'
    if cat == 'ten_12':
        return 'Up to 12½"' if puppy else '10" up to 12½"'
    if re.search(r'12\s*½\s*-?\s*15', text, re.IGNORECASE):
        return 'Over 12½" up to 15"'
    result = text.strip()
    result = re.sub(r'12\s*1\s*/\s*2', '12½', result, flags=re.IGNORECASE)
    result = re.sub(r'121/?2', '12½', result, flags=re.IGNORECASE)
    return result.strip()


def normalize_racing_size_prefix(size_prefix: str, current_class: str) -> str:
    """Normalize OCR-mangled racing height prefix before building class name."""
    if not size_prefix:
        return size_prefix
    puppy = bool(re.search(r'\bPUPPY\b', current_class, re.IGNORECASE))
    return canonicalize_height_fragment(size_prefix.strip(), puppy=puppy)


GTG_CHAMPIONSHIP_UNDER_HEIGHT = '10" up to 12½"'
GTG_CHAMPIONSHIP_OVER_HEIGHT = 'Over 12½" up to 15"'


def canonicalize_gtg_championship_height(text: str) -> str | None:
    """Map GTG championship height fragments to full canonical height suffixes."""
    if not text:
        return None
    raw = text.strip()
    if re.search(r'^10\s*"\s*up\s+to\s+12', raw, re.IGNORECASE):
        return GTG_CHAMPIONSHIP_UNDER_HEIGHT
    if re.search(r'^Over\s+12', raw, re.IGNORECASE):
        return GTG_CHAMPIONSHIP_OVER_HEIGHT

    label = raw.upper()
    if label in ('UNDER', 'SMALL'):
        return GTG_CHAMPIONSHIP_UNDER_HEIGHT
    if label in ('OVER', 'TALL'):
        return GTG_CHAMPIONSHIP_OVER_HEIGHT
    cat = classify_height_fragment(raw)
    if cat in ('ten_12', 'up_12'):
        return GTG_CHAMPIONSHIP_UNDER_HEIGHT
    if cat == 'over_15':
        return GTG_CHAMPIONSHIP_OVER_HEIGHT
    if re.search(r'12\s*(?:½|1\s*/\s*2)\s*-?\s*15', raw, re.IGNORECASE):
        return GTG_CHAMPIONSHIP_OVER_HEIGHT
    if re.search(r'10[\s.\-]+12', raw, re.IGNORECASE):
        return GTG_CHAMPIONSHIP_UNDER_HEIGHT
    return None


def canonicalize_over_under_championship_class(
    class_name: str,
    division_name: str = "",
) -> str:
    """Map GTG OVER/UNDER (or SMALL/TALL) championship labels to height suffixes."""
    if not class_name:
        return class_name
    name = class_name.strip()
    if not re.search(r'CHAMPION\s*(?:&|AND)\s*RESERVE', name, re.IGNORECASE):
        return name
    if re.search(r'LURE\s+COURS', name, re.IGNORECASE):
        return name

    is_gtg_name = bool(re.search(r'GO-TO-GROUND|GTG', name, re.IGNORECASE))
    is_gtg_div = bool(
        division_name
        and re.search(
            r'GO-TO-GROUND|GTG|SUPER\s*EARTH|MASTER\'?S?\s*DEN',
            division_name,
            re.IGNORECASE,
        )
    )
    if not is_gtg_name and not is_gtg_div:
        return name

    under_h = GTG_CHAMPIONSHIP_UNDER_HEIGHT
    over_h = GTG_CHAMPIONSHIP_OVER_HEIGHT
    gtg_base = 'GO-TO-GROUND CHAMPION & RESERVE'

    m = re.match(
        r'^(?P<label>SMALL|TALL)\s+GO-TO-GROUND\s+CHAMPION\s*(?:&|AND)\s*RESERVE\s*$',
        name,
        re.IGNORECASE,
    )
    if m:
        height = over_h if m.group('label').upper() == 'TALL' else under_h
        return f'{gtg_base} ({height})'

    m = re.match(
        r'^GO-TO-GROUND\s+(?P<label>UNDER|OVER)\s+CHAMPION\s*(?:&|AND)\s*RESERVE\s*$',
        name,
        re.IGNORECASE,
    )
    if m:
        height = over_h if m.group('label').upper() == 'OVER' else under_h
        return f'{gtg_base} ({height})'

    m = re.match(
        r'^(?P<prefix>'
        r'10[\s.\-]+12[\d\s/½"\-.%\'(),:·°-]*|'
        r'12\s*(?:[%½]|1\s*/\s*2)[\d\s/½"\-.%\'(),:·°-]*|'
        r'over\s+12[\d\s/½"\-.%\'(),:·°-]*'
        r')\s+'
        r'(?P<label>UNDER|OVER)\s+'
        r'(?:(?:GO-TO-GROUND|GTG)\s+)?'
        r'CHAMPION\s*(?:&|AND)\s*RESERVE\s*$',
        name,
        re.IGNORECASE,
    )
    if m:
        label = m.group('label').upper()
        prefix = m.group('prefix').strip()
        height = canonicalize_gtg_championship_height(prefix)
        if not height:
            height = over_h if label == 'OVER' else under_h
        return f'{gtg_base} ({height})'

    if is_gtg_div and not is_gtg_name:
        m = re.match(
            r'^(?P<label>UNDER|OVER)\s+CHAMPION\s*(?:&|AND)\s*RESERVE\s*$',
            name,
            re.IGNORECASE,
        )
        if m:
            height = over_h if m.group('label').upper() == 'OVER' else under_h
            return f'{gtg_base} ({height})'

    return name


def is_racing_height_prefix_line(line: str) -> bool:
    """True when line is only a height category (split off from a glued Champion/Reserve line)."""
    stripped = line.strip()
    if not stripped or is_placement_line_start(stripped):
        return False
    return bool(_RACING_HEIGHT_PREFIX_RE.match(stripped))


def split_glued_placement_parts(line: str) -> list[str]:
    """Split a line with multiple glued placements into separate parts."""
    parts = [line]
    for pattern in (GLUED_ORDINAL_PLACEMENT_SPLIT_RE, GLUED_CHAMPION_PLACEMENT_SPLIT_RE):
        next_parts: list[str] = []
        for part in parts:
            next_parts.extend(pattern.split(part))
        parts = next_parts
    return [part.strip() for part in parts if part.strip()]

def clean_parsed_owner_name(owner_name: str) -> str:
    """Remove glued subsequent placements accidentally captured in owner field."""
    if not owner_name:
        return owner_name
    owner_name = owner_name.strip()
    m = GLUED_PLACEMENT_SPLIT_RE.search(owner_name)
    if m:
        owner_name = owner_name[: m.start()].strip()
    if len(owner_name) > OWNER_NAME_MAX_LEN:
        owner_name = owner_name[:OWNER_NAME_MAX_LEN].strip()
    return owner_name


def extract_trailing_racing_height_suffix(text: str) -> tuple[str, str | None]:
    """Split OCR-glued height category from end of owner/dog field (e.g. 'Johnson 12 ½-15"')."""
    if not text:
        return text, None
    text = text.strip()
    m = re.search(
        r'\s+(?P<height>(?:'
        r'10[\s.\-]+12[\d\s/½"\-.%\'(),:·°-]*|'
        r'12\s*[%½]\s*-?\s*15[\d\s/½"\-.%\'(),:·°-]*|'
        r'12\s*[%½][\d\s/½"\-.%\'(),:·°-]*|'
        r'over\s+12[\d\s/½"\-.%\'(),:·°-]*|'
        r'10\s*"?\s*up\s+to[\d\s/½"\-.%\'(),:·°-]*|'
        r'up\s+to\s+12[\d\s/½"\-.%\'(),:·°-]*'
        r')["\'½]?)\s*$',
        text,
        re.IGNORECASE,
    )
    if not m:
        return text, None
    height = m.group('height').strip()
    if classify_height_fragment(height) or is_racing_height_prefix_line(height):
        return text[: m.start()].strip(), height
    return text, None


def expand_glued_placement_lines(lines: List[str]) -> List[str]:
    """Split lines where multiple placements were glued without newlines."""
    expanded: List[str] = []
    for line in lines:
        stripped = line.strip()
        if not stripped:
            expanded.append(line)
            continue
        parts = split_glued_placement_parts(stripped)
        if len(parts) > 1:
            for part in parts:
                part = part.strip()
                if part:
                    expanded.append(part)
        else:
            expanded.append(line)
    return expanded


def normalize_line_for_placement(line: str) -> str:
    """Normalize OCR/special chars before placement regex matching."""
    line = (
        line.replace('·', '-').replace('–', '-').replace('—', '-')
        .replace('\xa0', ' ').replace('\u00a0', ' ')
    )
    # Normalize curly/smart quotes and prime marks to ASCII for regex matching
    for old, new in (
        ('\u2018', "'"), ('\u2019', "'"), ('\u201a', "'"),
        ('\u201c', '"'), ('\u201d', '"'), ('\u2033', '"'), ('\u2032', "'"),
    ):
        line = line.replace(old, new)
    # OCR fixes for placement keywords
    line = re.sub(r'\bet[-\s]?ar?pl[o]?n\b', 'Champion', line, flags=re.IGNORECASE)
    line = re.sub(r'\bchampon\b', 'Champion', line, flags=re.IGNORECASE)
    line = re.sub(r'\bchamp\s+ion\b', 'Champion', line, flags=re.IGNORECASE)
    line = re.sub(r'\bresenve\b', 'Reserve', line, flags=re.IGNORECASE)
    # Convert dash-separated placements to colon-separated for consistent parsing.
    # Some files (e.g. 2017 MO Earthdogs PDF) use en-dash/em-dash as the placement
    # separator: "1st – Dog Name (Owner)" or "Champion – Dog Name (Owner)".
    # After the above substitutions, en/em-dashes are already normalized to '-'.
    # Convert: "1st - Dog" -> "1st: Dog"  (ordinal suffix REQUIRED to avoid matching
    # racing height prefixes like "10 - 12 1/2 Champion: Dog, owned by Owner")
    line = re.sub(
        r'^(\s*\d{1,2}(?:st|nd|rd|th))\s+-\s+',
        r'\1: ',
        line,
        count=1,
        flags=re.IGNORECASE,
    )
    # Convert compound and simple word placements, including descriptive forms used
    # in 2017 MO Earthdogs conformation: "Champion JRT Puppy - Dog",
    # "Best Working Dog - Dog", "Working JRT Champion - Dog",
    # "Reserve Champion Working Colored Terrier/Dachshund - Dog".
    line = re.sub(
        r'^(\s*(?:Working\s+JRT\s+)?'
        r'(?:Reserve\s+)?(?:Best|Champion)(?:\s+[\w/]+){0,10}'
        r'|Reserve(?:\s+[\w/]+){0,10}'
        r'|Best(?:\s+[\w/]+){0,10}'
        r'|Champion(?:\s+[\w/]+){0,10}'
        r'|Reserve)\s+-\s+',
        r'\1: ',
        line,
        count=1,
        flags=re.IGNORECASE,
    )
    return line

def parse_placement_line(line: str) -> Optional[Tuple[str, str, str]]:
    """Parse a placement line into (size_prefix, placement, rest)."""
    line_norm = normalize_line_for_placement(line)
    m = PLACEMENT_LINE_RE.match(line_norm)
    if m:
        size_prefix = m.group(1) or ''
        rest = m.group(2).strip()
        placement_m = re.match(
            rf'^({_SIZE_PREFIX}*?)\s*({_ORDINAL_PLACEMENT}|{_WORD_PLACEMENT})\s*',
            line_norm,
            re.IGNORECASE,
        )
        placement = placement_m.group(2).strip() if placement_m else ''
        return size_prefix, placement, rest
    m = IMPLICIT_CHAMPION_RE.match(line_norm)
    if m and contains_owned_by(line_norm):
        return m.group(1), 'Champion', m.group(2).strip()
    return None


def format_ordinal_placement(rank: int) -> str:
    """Convert numeric rank to 1st/2nd/3rd style."""
    if 11 <= rank % 100 <= 13:
        suffix = 'th'
    else:
        suffix = {1: 'st', 2: 'nd', 3: 'rd'}.get(rank % 10, 'th')
    return f'{rank}{suffix}'


def is_time_token(text: str) -> bool:
    """True when text looks like a GTG/racing time value."""
    token = (text or '').strip().lstrip('$')
    return bool(_TIME_TOKEN_RE.match(token))


def split_dog_owner_time_from_rest(rest: str) -> tuple[str, str, str]:
    """Handle OCR cases like 'Dog, owned by Owner, owned by 10.31' or 'Dog, owned by 10.31'."""
    text = rest.strip()
    prize_owner = re.search(
        r'^(.*?),\s*owned by\s+\$[\d.]+,\s*owned by\s+(.+)$',
        text,
        re.IGNORECASE,
    )
    if prize_owner:
        return prize_owner.group(1).strip(), prize_owner.group(2).strip(), ''

    triple_owned = re.search(
        r'^(.*?),\s*owned by\s+([\d:$:.]+),\s*owned by\s+[^,]*,\s*owned by\s+(.+)$',
        text,
        re.IGNORECASE,
    )
    if triple_owned and is_time_token(triple_owned.group(2)):
        return (
            triple_owned.group(1).strip(),
            triple_owned.group(3).strip(),
            triple_owned.group(2).strip().lstrip('$'),
        )

    double_owned = re.search(
        r'^(.*?),\s*owned by\s+(.+?),\s*owned by\s+([\d:$:.]+)\s*$',
        text,
        re.IGNORECASE,
    )
    if double_owned and is_time_token(double_owned.group(3)):
        return (
            double_owned.group(1).strip(),
            double_owned.group(2).strip(),
            double_owned.group(3).strip().lstrip('$'),
        )

    time_only_owner = re.search(r'^(.*?),\s*owned by\s+([\d:$:.]+)\s*$', text, re.IGNORECASE)
    if time_only_owner and is_time_token(time_only_owner.group(2)):
        return time_only_owner.group(1).strip(), '', time_only_owner.group(2).strip().lstrip('$')

    return text, '', ''


def extract_placement_time_suffix(text: str) -> tuple[str, str]:
    """Split trailing '- time of 9.54' (and prize text) from dog/owner field."""
    if not text:
        return text, ''
    match = _PLACEMENT_TIME_SUFFIX_RE.search(text)
    if not match:
        return text, ''
    time_val = match.group(1).strip()
    clean = text[: match.start()].strip()
    return clean, time_val


def parse_tab_placement_line(line: str) -> Optional[Tuple[str, str, str, str]]:
    """Parse MO Earthdogs tab-separated placement -> (placement, dog, owner, time)."""
    if '\t' not in line:
        return None
    parts = [part.strip() for part in line.split('\t') if part.strip()]
    if len(parts) < 2:
        return None

    placement = ''
    dog = ''
    owner = ''
    time_val = ''
    idx = 0
    head = parts[0]

    if re.fullmatch(r'\d{1,2}', head):
        placement = format_ordinal_placement(int(head))
        dog = parts[1]
        idx = 2
    else:
        parsed = parse_placement_line(head)
        if not parsed:
            return None
        _, placement, rest = parsed
        dog = rest.strip()
        idx = 1

    while idx < len(parts):
        token = parts[idx]
        if not time_val and is_time_token(token):
            time_val = token
        elif not owner:
            owner = token
        else:
            owner = f'{owner} {token}'
        idx += 1

    dog, inline_time = extract_placement_time_suffix(dog)
    if inline_time and not time_val:
        time_val = inline_time
    owner, owner_time = extract_placement_time_suffix(owner)
    if owner_time and not time_val:
        time_val = owner_time

    if not dog:
        return None
    return placement, dog, owner, time_val


def normalize_mixed_case_section_header(line: str) -> str | None:
    """Map MO Earthdogs-style section labels to division names.

    Handles both mixed-case (e.g. 'Flat Races') and ALL-CAPS (e.g. 'FLAT RACES')
    headers that are specific to MO Earthdogs file formats.
    """
    low = re.sub(r'\s+', ' ', (line or '').strip().lower())
    if low in ('conformation results', 'conformation', 'conformation division'):
        return 'CONFORMATION'
    # OCR often inserts a space before the hyphen: "go -to-ground"
    low_gtg = re.sub(r'[\s.\-/]+', '', low)
    if low_gtg in (
        'gotoground', 'gotogroundresults', 'gotogrounddivision',
    ) or 'gotoground' in low_gtg:
        return 'GO-TO-GROUND'
    if low in ('go to ground', 'go-to-ground', 'go-to-ground results',
               'go-to-ground division', 'go to ground division'):
        return 'GO-TO-GROUND'
    if low in ('super earth', 'super-earth'):
        return 'SUPER EARTH'
    if low in (
        'racing', 'racing results', 'racing division',
        'flat races', 'flat racing',
        'steeplechase races', 'steeplechase racing', 'steeplechase',
        'hurdle races', 'hurdle racing',
        'friday night racing', 'friday racing',
        'saturday racing', 'saturday night racing',
        'sunday racing', 'sunday night racing',
    ):
        return 'RACING'
    if low in ('muskrat racing', 'muskrat races'):
        return 'MUSKRAT RACING'
    if low in ('youth division', 'youth'):
        return 'YOUTH'
    if low.startswith('olympic events'):
        return 'OLYMPIC EVENTS'
    if low in ('lure coursing', 'lure racing'):
        return 'LURE COURSING'
    if low in ('thunder tunnel', 'barn hunt'):
        return low.upper()
    return None


def find_next_placement_index(lines: List[str], idx: int, limit: int = 8) -> int | None:
    """Return index of the next placement line, skipping blank lines."""
    for j in range(idx + 1, min(idx + 1 + limit, len(lines))):
        candidate = lines[j].strip()
        if not candidate:
            continue
        if is_placement_line_start(candidate) or parse_tab_placement_line(candidate):
            return j
        if '\t' in candidate and re.match(r'^\d{1,2}(?:st|nd|rd|th)?\b', candidate, re.I):
            return j
    return None

def is_placement_line_start(line: str) -> bool:
    """True if line begins a placement entry."""
    line_norm = normalize_line_for_placement(line)
    if PLACEMENT_LINE_START_RE.match(line_norm):
        return True
    m = IMPLICIT_CHAMPION_RE.match(line_norm)
    if m and contains_owned_by(line_norm):
        return True
    if parse_tab_placement_line(line):
        return True
    return False

def normalize_owned_by_text(text: str) -> str:
    """Fix common OCR errors in owned-by separator."""
    text = re.sub(
        r'[,.\s]*(?:orwned|owend|ownde|rowned|9wned|aowned|owned)\s*(?:by\s*)?',
        ', owned by ',
        text,
        count=1,
        flags=re.IGNORECASE
    )
    # OCR merged owner name into separator (e.g. "owned byDarleneMcCutcheon")
    text = re.sub(r', owned by(\S)', r', owned by \1', text)
    text = re.sub(r'\s+', ' ', text)
    return text.strip()

def contains_owned_by(text: str) -> bool:
    """True if text has an owned-by separator (including OCR variants)."""
    return ', owned by ' in normalize_owned_by_text(text)


# Entries suffix patterns (en-dash, em-dash, hyphen, OCR typos)
_ENTRIES_MARKER_RE = re.compile(
    r'\b(?:entries?|entires?|eritries?|entry)\s*:?\s*(\d*)',
    re.IGNORECASE,
)
_TRAILING_SEP_RE = re.compile(r'[\s\-–—−‐‑‒]+$', re.UNICODE)


def strip_entries_from_class_name(class_name: str) -> tuple[str, Optional[int]]:
    """
    Remove Entries suffix variants from a class name.

    Handles: 'Class – Entries: 5', 'Class - Entries:', 'Class Entries:5', OCR 'Entires: 3',
    parenthetical '(5 entries)', and truncated OCR leftovers like '(5' / '(18'.
    Returns (clean_name, entry_count or None).
    """
    if not class_name:
        return class_name, None

    entry_count = None
    clean = class_name

    paren = re.search(
        r'\(\s*(\d+)\s*entr(?:y|ies)?\s*\)?\s*$',
        clean,
        re.IGNORECASE,
    )
    if paren:
        entry_count = int(paren.group(1))
        clean = clean[: paren.start()].strip()
    else:
        trunc = re.search(r'\(\s*(\d+)\s*$', clean)
        if trunc:
            entry_count = int(trunc.group(1))
            clean = clean[: trunc.start()].strip()

    match = _ENTRIES_MARKER_RE.search(clean)
    if match:
        entry_str = match.group(1).strip()
        if entry_str:
            entry_count = int(entry_str)
        clean = clean[: match.start()].strip()
        clean = _TRAILING_SEP_RE.sub('', clean).strip()
        return clean, entry_count

    clean = _TRAILING_SEP_RE.sub('', clean).strip()
    return clean, entry_count

_HEIGHT_ENTRIES_CONTINUATION_RE = re.compile(
    r'^,\s*(.+?)\s*[–—-]\s*Entries:\s*(\d+)\s*$',
    re.IGNORECASE,
)


def is_certificate_super_earth_header(line: str) -> bool:
    """True for Super Earth certificate class title split onto its own line."""
    stripped = (line or '').strip()
    if not stripped or 'entries' in stripped.lower():
        return False
    if re.search(r'\b(?:10|12|15|over|up to)\b', stripped, re.IGNORECASE):
        return False
    return bool(
        re.search(
            r'\b(?:Adult|Veteran|Senior|Puppy)\s+(?:Certificate|Championship)\s+Super\s+Earth\b',
            stripped,
            re.IGNORECASE,
        )
    )


def join_split_certificate_class_line(line: str, lines: List[str], idx: int) -> str:
    """Join 'Adult Certificate Super Earth' + ', 10 up to 12½" – Entries: 24' split lines."""
    stripped = (line or '').strip()
    if not _HEIGHT_ENTRIES_CONTINUATION_RE.match(stripped):
        return line
    prev = _prev_nonempty_line(lines, idx)
    if is_certificate_super_earth_header(prev):
        return f"{prev}{line}"
    return line


def try_parse_class_with_entries(
    line: str, lines: List[str], idx: int
) -> Optional[Tuple[str, int, int]]:
    """
    Parse class name and entry count from a line.

    Returns (class_name, entry_count, extra_lines_consumed) or None.
    extra_lines_consumed is 1 when the count is on the following line.
    """
    if not line or 'entr' not in line.lower():
        return None

    clean, entry_count = strip_entries_from_class_name(line)
    if not _ENTRIES_MARKER_RE.search(line):
        return None

    extra = 0
    if entry_count is None:
        nxt = _next_nonempty_line(lines, idx)
        if nxt and re.fullmatch(r'\d+', nxt.strip()):
            entry_count = int(nxt.strip())
            extra = 1

    return clean, entry_count or 0, extra


def _next_nonempty_line(lines: List[str], idx: int, limit: int = 5) -> str:
    for j in range(idx + 1, min(idx + 1 + limit, len(lines))):
        candidate = lines[j].strip()
        if candidate:
            return candidate
    return ""


def _prev_nonempty_line(lines: List[str], idx: int, limit: int = 5) -> str:
    for j in range(idx - 1, max(idx - 1 - limit, -1), -1):
        candidate = lines[j].strip()
        if candidate:
            return candidate
    return ""


def is_owner_surname_continuation(line: str, lines: List[str], idx: int) -> bool:
    """
    True when a line is an owner surname wrapped to the next line by HTML extraction.

    Example:
        1st: Piccadilly Ringer, owned by John & Judy
        Tyno
        2nd: ...
    """
    text = line.strip()
    if not text:
        return False
    if "entr" in text.lower() or ", owned by " in text.lower():
        return False
    if not re.fullmatch(r"[A-Za-z][A-Za-z'\-/]*", text):
        return False
    if len(text) > 30:
        return False

    prev = _prev_nonempty_line(lines, idx)
    if not prev or not is_placement_line_start(prev):
        return False
    if ", owned by " not in normalize_owned_by_text(prev).lower():
        return False

    nxt = _next_nonempty_line(lines, idx)
    if not nxt:
        return False
    if is_placement_line_start(nxt):
        return True
    if "entr" in nxt.lower():
        return True
    if nxt.isupper() and len(nxt) > 5 and "DIVISION" not in nxt:
        return True
    return False


def is_go_to_ground_division(line: str) -> bool:
    """Detect GO-TO-GROUND division headers including OCR variants like G()\"T()\"GROUND."""
    line_upper = line.upper().replace(' ', '-')
    if 'GO-TO-GROUND' in line_upper or 'GOTOGROUND' in line_upper.replace('-', ''):
        return True
    compact = re.sub(r'[^A-Za-z]', '', line).upper()
    return bool(re.fullmatch(r'G[O]*T[O]*GROUND(?:DIVISION)?', compact))

_DIVISION_KEYWORDS = (
    'CONFORMATION', 'DIVISION', 'GO-TO-GROUND', 'OBEDIENCE', 'AGILITY', 'RACING',
    'YOUTH', 'SUPER-EARTH', 'TRAILING', 'NOSE-WORK', 'LURE-COURSING', 'BRUSH-HUNT',
    'THUNDER-TUNNEL', 'BALL-TOSS', 'HIGH-JUMP', 'BALL-RETRIEVAL', 'MASTER-S-DEN',
    'BARN-HUNT', 'TUNNEL-VISION', 'JACKS-ARE-WILD', 'DUTCH-CREEK',
)
_FALSE_DIVISION_HEADERS = frozenset({
    'JUMPING DIVISION',
    'JUMPERS DIVISION',
})

def is_agility_subdivision_header(line_normalized: str) -> bool:
    """JUMPING DIVISION is an agility section label (Jumpers classes), not a main division."""
    upper = re.sub(r'\s+', ' ', line_normalized.strip().upper())
    if upper in _FALSE_DIVISION_HEADERS:
        return True
    return upper.startswith('JUMPING') and upper.endswith('DIVISION')

def is_division_header(line_clean: str, line_for_division: str) -> bool:
    """True if line looks like a main trial division header."""
    upper = re.sub(r'\s+', ' ', line_clean.strip().upper())
    if upper in _FALSE_DIVISION_HEADERS or is_agility_subdivision_header(upper):
        return False
    return (
        any(keyword in line_for_division for keyword in _DIVISION_KEYWORDS)
        or is_go_to_ground_division(line_clean)
    )

def normalize_stored_division_name(division_name: str) -> str:
    """Map mis-parsed section labels to canonical trial divisions."""
    if not division_name:
        return division_name
    upper = re.sub(r'\s+', ' ', division_name.strip().upper())
    if upper == 'JUMPING DIVISION':
        return 'AGILITY DIVISION'
    if upper.startswith('AGILITY DIVISION - JUMPING') or upper.endswith(' - JUMPING DIVISION'):
        return 'AGILITY DIVISION'
    return division_name.strip()


# Regex to detect class names that mistakenly use "owned by" for height specs, e.g.:
# "Working Dogs 1 yr and up, owned by 10-12.5"" -> should be "Working Dogs 1 yr and up, 10-12.5""
# Also handles trailing "owned by" with nothing after it (OCR artifact in 2002 file):
# "CLASS 3: Dog Pups 4-6 mos, owned by" -> "Dog Pups 4-6 mos"
_CLASS_OWNED_BY_HEIGHT_RE = re.compile(
    r',\s*owned\s+by\s+([\d\s./½"\'–\-]+["\']?)?\s*$',
    re.IGNORECASE,
)


def strip_owned_by_height_from_class_name(class_name: str) -> str:
    """Remove erroneous 'owned by [height]' suffix from class names.

    Handles two patterns:
    - 'Working Dogs 1 yr and up, owned by 10-12.5"' → height spec after owned by
    - 'Dog Pups 4-6 mos, owned by'  → trailing "owned by" with nothing after (OCR artifact)
    """
    m = _CLASS_OWNED_BY_HEIGHT_RE.search(class_name)
    if m:
        candidate = (m.group(1) or '').strip()
        # Accept if candidate is empty (bare trailing "owned by") or a height spec
        if not candidate or re.fullmatch(r'[\d\s./½"\'–\-]+', candidate):
            return class_name[:m.start()].strip()
    return class_name


def infer_division_from_class_name(class_name: str) -> str:
    """Infer the likely division from keywords in a class name.

    Used as a fallback when a file has no explicit division header before
    the first class (e.g. 2013 PDF starts directly with 'Class 1: Flat Racing').
    Returns a canonical division string or '' if indeterminate.
    """
    upper = re.sub(r'\s+', ' ', class_name.strip().upper())
    if re.search(r'\b(?:FLAT|HURDLE[SD]?|STEEPLECHASE|SPRINT)\s+RAC', upper):
        return 'RACING'
    # Allow OCR spacing/punctuation variants: "Go -To-Ground", "GOTOGROUND", "G.T.G."
    if re.search(r'\bGTG\b|GO[\s.\-/]*TO[\s.\-/]*GROUND', upper):
        return 'GO-TO-GROUND'
    if re.search(r'\bMUSKRAT\s+RAC', upper):
        return 'MUSKRAT RACING'
    if re.search(r'\bLURE\s+COURS', upper):
        return 'LURE COURSING'
    if re.search(r'\bTHUNDER\s+TUNNEL\b', upper):
        return 'THUNDER TUNNEL'
    if re.search(r'\bBARN\s+HUNT\b', upper):
        return 'BARN HUNT'
    if re.search(r'\bAWTA\b', upper):
        return 'GO-TO-GROUND'
    if re.search(r'\b(?:CHILD|YOUTH)\b', upper) and not re.search(r'\bGTG\b|GO[\s.\-/]*TO', upper):
        return 'YOUTH DIVISION'
    if re.search(
        r'\bPUPS?\b|\bBITCH\s+PUPS?\b|\bDOG\s+PUPS?\b|'
        r'\bWORKING\s+(?:DOG|BITCH)|'
        r'\bOPEN\s+(?:DOG|BITCH)|'
        r'\bVETERAN\s+WORKING\b|'
        r'\bCHILD\s+HANDLER\b|\bYOUTH\s+HANDLER\b|'
        r'\bCONFORMATION\b',
        upper,
    ):
        return 'CONFORMATION'
    return ''


# Divisions that may override an already-established current division.
# Only the primary JRTCA divisions and MUSKRAT RACING are allowed to override.
# Sub-events like LURE COURSING and THUNDER TUNNEL (which sometimes appear
# inside OLYMPIC EVENTS) should NOT override that wrapper division.
_DIVISION_OVERRIDE_TRIGGERS = frozenset({
    'RACING', 'CONFORMATION', 'GO-TO-GROUND', 'MUSKRAT RACING', 'YOUTH DIVISION',
})


def should_override_division(current_division: str, inferred_division: str) -> bool:
    """Return True when the inferred division should replace the current one."""
    if not inferred_division or inferred_division == current_division:
        return False
    if not current_division:
        return True
    return inferred_division in _DIVISION_OVERRIDE_TRIGGERS


def canonical_division_name(line: str) -> str:
    """Return a normalized division name for storage."""
    upper = re.sub(r'\s+', ' ', line.strip().upper())
    if re.fullmatch(r'NOSE\s*WORK(?:\s+DIVISION)?', upper) or upper == 'NOSEWORK':
        return 'NOSE WORK'
    if 'HIGH' in upper and 'JUMP' in upper:
        return 'HIGH JUMP'
    if 'BALL' in upper and 'RETRIEVAL' in upper:
        return 'BALL RETRIEVAL'
    if ('MASTER' in upper and 'DEN' in upper) or "MASTER'S DEN" in upper:
        return "MASTER'S DEN STAKES"
    if 'SUPER' in upper and 'EARTH' in upper:
        # Bare "SUPER EARTH" in older results is a section label; classes are Master's Den Stakes
        if upper in ('SUPER EARTH', 'SUPER EARTH STAKES'):
            return "MASTER'S DEN STAKES"
        return 'SUPER EARTH'
    if is_go_to_ground_division(line):
        return 'GO-TO-GROUND'
    return line.strip()


def _strip_markup(text: str) -> str:
    """Remove simple HTML/XML tags from scraped lines."""
    return re.sub(r'<[^>]+>', '', text or '').strip()


def is_nosework_section_header(line: str) -> bool:
    """True for NOSE WORK section labels (distinct from TRAILING & LOCATING)."""
    upper = re.sub(r'\s+', ' ', _strip_markup(line).upper())
    return upper in ('NOSEWORK', 'NOSE WORK', 'NOSE WORK DIVISION')


def is_nosework_class_name(class_name: str) -> bool:
    """True when a class belongs in NOSE WORK, not TRAILING & LOCATING."""
    if not class_name:
        return False
    upper = _strip_markup(class_name).upper()
    if re.search(r'NOSE\s*WORK', upper):
        return True
    if re.search(
        r'\b(?:SNIFFER|CONTAINERS?|EXTERIORS?|INTERIORS?(?:\s+SEARCH)?|'
        r'CONTAINER\s+SEARCH|EXTERIOR\s+SEARCH|BEGINNER\s+SNIFFER)\b',
        upper,
    ):
        return True
    if re.search(r'\bLEVEL\s+[12]\b', upper) and re.search(
        r'\b(?:CONTAINER|EXTERIOR|INTERIOR|SNIFFER|SEARCH|CHALLENGE)\b', upper,
    ):
        return True
    if re.search(r'\bLEVEL\s+[12]\s+HIGH\s+SCORE\s+CHAMPION\b', upper):
        return True
    return False


def maybe_switch_to_nosework_division(
    division: str,
    class_name: str = "",
    line: str = "",
) -> str:
    """Switch division to NOSE WORK for nosework sections/classes."""
    if is_nosework_section_header(line):
        return 'NOSE WORK'
    if is_nosework_class_name(class_name):
        return 'NOSE WORK'
    return division


def _expand_two_digit_year(year_str: str, hint_year: int | None = None) -> str:
    if len(year_str) == 4:
        return year_str
    year_num = int(year_str)
    if hint_year is not None:
        century = hint_year // 100
        expanded = century * 100 + year_num
        if abs(expanded - hint_year) > 30:
            expanded = (century - 1) * 100 + year_num
        return str(expanded)
    return str(2000 + year_num if year_num < 70 else 1900 + year_num)

def parse_trial_date_part(date_part: str, hint_year: int | None = None) -> tuple:
    """Parse date text into (start_date, end_date) like 'October 16, 1998'."""
    date_part = date_part.strip()
    if not date_part:
        return "", ""

    # Month + one or more days + year (handles ranges, lists, and single dates)
    # e.g. "October 16, 17, & 18, 1998", "October 10 – 12, 2025", "May 17 & 18, 1997"
    date_part = re.sub(r',(\d{4}\b)', r', \1', date_part)
    list_match = re.search(r'(\w+)\s+(.+?),?\s*(\d{4})$', date_part)
    if list_match:
        month = list_match.group(1)
        days_part = list_match.group(2)
        year_str = list_match.group(3)
        days = [int(d) for d in re.findall(r'\d{1,2}', days_part)]
        if days:
            start_date = f"{month} {days[0]}, {year_str}"
            end_date = f"{month} {days[-1]}, {year_str}"
            return start_date, end_date

    single_month_match = re.search(
        r'^(January|February|March|April|May|June|July|August|September|October|November|December)\s+(\d{1,2}),?\s+(\d{4})$',
        date_part,
    )
    if single_month_match:
        month = single_month_match.group(1)
        day = single_month_match.group(2)
        year_str = single_month_match.group(3)
        start_date = f"{month} {day}, {year_str}"
        return start_date, start_date

    numeric_date_match = re.search(r'(\d{1,2})[/\-](\d{1,2})[/\-](\d{2,4})', date_part)
    range_numeric_match = re.match(
        r'^(\d{1,2})/(\d{1,2})-(\d{1,2})/(\d{2,4})$',
        date_part,
    )
    if range_numeric_match:
        month_num = int(range_numeric_match.group(1))
        day_start = int(range_numeric_match.group(2))
        day_end = int(range_numeric_match.group(3))
        year_str = _expand_two_digit_year(range_numeric_match.group(4), hint_year)
        month_names = ['', 'January', 'February', 'March', 'April', 'May', 'June',
                       'July', 'August', 'September', 'October', 'November', 'December']
        month = month_names[month_num] if month_num <= 12 else str(month_num)
        start_date = f"{month} {day_start}, {year_str}"
        end_date = f"{month} {day_end}, {year_str}"
        return start_date, end_date

    if numeric_date_match:
        month_num = numeric_date_match.group(1)
        day = numeric_date_match.group(2)
        year_str = _expand_two_digit_year(numeric_date_match.group(3), hint_year)
        month_names = ['', 'January', 'February', 'March', 'April', 'May', 'June',
                       'July', 'August', 'September', 'October', 'November', 'December']
        month = month_names[int(month_num)] if int(month_num) <= 12 else month_num
        start_date = f"{month} {day}, {year_str}"
        return start_date, start_date

    return date_part, date_part

_MONTH_NAMES = (
    'January', 'February', 'March', 'April', 'May', 'June',
    'July', 'August', 'September', 'October', 'November', 'December',
)

def _normalize_header_line(header_line: str) -> str:
    header_line = header_line.strip()
    header_line = header_line.replace('"', '').replace('"', '').replace('"', '')
    return re.sub(
        r'(January|February|March|April|May|June|July|August|September|October|November|December)(\d)',
        r'\1 \2',
        header_line,
    )

def _line_looks_like_bare_date(header_line: str) -> bool:
    return bool(re.match(
        r'^(January|February|March|April|May|June|July|August|September|October|November|December)\s+\d{1,2},?\s+\d{4}$',
        header_line.strip(),
    ))

def _line_looks_like_location_date(header_line: str) -> bool:
    """Return True when a line looks like a trial location/date header, not a placement."""
    stripped = header_line.strip()
    low = stripped.lower()
    if low.startswith('class ') or 'owned by' in low or low.startswith('result'):
        return False
    if re.search(r'\b(?:dogs?|bitches?|puppies|veteran|championship|novice|open)\b', low):
        return False
    if re.search(r'\d\s*1/2', stripped):
        return False
    if _line_looks_like_bare_date(stripped):
        return False
    if any(x in header_line.lower() for x in ['chair', 'judge', 'administrator']):
        return False
    if re.search(r'\d{1,2}[/\-]\d{1,2}[/\-]\d{2,4}', header_line):
        return True
    if '~' in header_line and (
        re.search(r'\b\d{4}\b', header_line)
        or re.search(r'\d{1,2}[/\-]\d{1,2}[/\-]\d{2}\b', header_line)
    ):
        return True
    if header_line.strip().startswith('~') and re.search(
        r'\b(January|February|March|April|June|July|August|September|October|November|December)\b',
        header_line,
    ):
        return True
    for month in _MONTH_NAMES:
        if month == 'May':
            if re.search(r'(?:~|,|\s)May\s+\d', header_line):
                return True
        elif re.search(rf'\b{month}\s+\d', header_line):
            return True
    return False

def _parse_location_date_from_line(
    header_line: str,
    prev_line: str = "",
    hint_year: int | None = None,
) -> Tuple[str, str, str]:
    """Parse one header line into (location, start_date, end_date)."""
    header_line = _normalize_header_line(header_line)
    header_line = re.sub(r',(\d{4}\b)', r', \1', header_line)

    date_in_location = re.match(
        r'^((?:January|February|March|April|May|June|July|August|September|October|November|December)\s+.+?,\s*\d{4})\s+in\s+(.+)$',
        header_line.strip(),
        re.IGNORECASE,
    )
    if date_in_location:
        date_part = date_in_location.group(1).strip()
        location = date_in_location.group(2).strip()
        start_date, end_date = parse_trial_date_part(date_part, hint_year)
        return location, start_date, end_date

    if header_line.strip().startswith('~'):
        date_part = header_line.strip().lstrip('~').strip()
        location = prev_line.strip() if prev_line and ',' in prev_line else ""
        start_date, end_date = parse_trial_date_part(date_part, hint_year)
        return location, start_date, end_date

    has_month_name = any(month in header_line for month in _MONTH_NAMES)
    has_numeric_date = re.search(r'\d{1,2}[/\-]\d{1,2}[/\-]\d{2,4}', header_line)

    separator = None
    if '~' in header_line:
        separator = '~'
    elif ' - ' in header_line and ',' in header_line:
        separator = ' - '
    elif '-' in header_line and ',' in header_line and (has_month_name or has_numeric_date):
        if not re.search(r'\d{1,2}-\d{1,2}', header_line):
            separator = '-'

    if not separator and has_month_name and header_line.count(',') >= 1:
        for month in _MONTH_NAMES:
            if month in header_line:
                idx = header_line.index(month)
                if idx > 0:
                    location = header_line[:idx].strip().rstrip(',').strip()
                    date_part = header_line[idx:].strip()
                    start_date, end_date = parse_trial_date_part(date_part, hint_year)
                    return location, start_date, end_date

    if separator and (has_month_name or has_numeric_date):
        parts = header_line.split(separator, 1)
        if len(parts) >= 2:
            location = parts[0].strip()
            date_part = parts[1].strip()
            if not location and prev_line:
                prev_line = prev_line.strip()
                if ',' in prev_line and len(prev_line) < 100:
                    location = prev_line
            start_date, end_date = parse_trial_date_part(date_part, hint_year)
            return location, start_date, end_date

    if not separator and (has_month_name or has_numeric_date) and header_line.count(',') >= 2:
        parts = header_line.split(',')
        if len(parts) >= 3:
            location = f"{parts[0].strip()}, {parts[1].strip()}"
            date_part = ','.join(parts[2:]).strip()
            start_date, end_date = parse_trial_date_part(date_part, hint_year)
            return location, start_date, end_date

    return "", "", ""

def _is_results_division_boundary(header_line: str) -> bool:
    if re.match(r'^[A-Z\s]+DIVISION$', header_line):
        return True
    return header_line.endswith('DIVISION') and 'CONFORMATION' in header_line

def scan_trial_header_block(
    lines: List[str],
    start_idx: int = 0,
    max_lines: int = 1500,
    hint_year: int | None = None,
    quiet: bool = False,
) -> Dict[str, str]:
    """Scan lines for location, dates, chair, administrator, and judges."""
    result = {
        'location': '',
        'start_date': '',
        'end_date': '',
        'chair': '',
        'administrator': '',
        'judges': '',
    }

    scan_end = min(len(lines), start_idx + max_lines)

    for j in range(start_idx, scan_end):
        header_line = lines[j].strip()
        if not header_line or result['start_date']:
            continue

        if _line_looks_like_bare_date(header_line):
            start_date, end_date = parse_trial_date_part(header_line, hint_year)
            if start_date:
                result['start_date'] = start_date
                result['end_date'] = end_date
                if not quiet:
                    print(f"    Dates: {start_date} to {end_date}")
            continue

        if _line_looks_like_location_date(header_line):
            prev_line = lines[j - 1].strip() if j > 0 else ""
            location, start_date, end_date = _parse_location_date_from_line(
                header_line, prev_line, hint_year,
            )
            if start_date:
                result['location'] = location
                result['start_date'] = start_date
                result['end_date'] = end_date
                if not quiet:
                    if location:
                        print(f"    Location: {location}")
                    print(f"    Dates: {start_date} to {end_date}")
            continue

        if (
            not result['location']
            and re.match(r'^[A-Za-z].+,\s*[A-Z]{2}$', header_line)
            and not _line_looks_like_location_date(header_line)
        ):
            result['location'] = header_line
            if not quiet:
                print(f"    Location: {header_line}")

    metadata_end = scan_end
    for j in range(start_idx, scan_end):
        header_line = lines[j].strip()
        if _is_results_division_boundary(header_line):
            metadata_end = j
            break

    for j in range(start_idx, metadata_end):
        header_line = lines[j].strip()
        if not header_line:
            continue

        if re.match(r'^[A-Z\s]+DIVISION$', header_line):
            break

        if re.match(r'Chair(persons?|man)?:\s*', header_line, re.IGNORECASE) and not result['chair']:
            result['chair'] = re.sub(r'Chair(persons?|man)?:\s*', '', header_line, flags=re.IGNORECASE).strip()
            if not quiet:
                print(f"    Chair: {result['chair']}")
        elif re.match(r'Chaired by:\s*', header_line, re.IGNORECASE) and not result['chair']:
            result['chair'] = re.sub(r'Chaired by:\s*', '', header_line, flags=re.IGNORECASE).strip()
            if not quiet:
                print(f"    Chair: {result['chair']}")
        elif re.match(r'Administrator:\s*', header_line, re.IGNORECASE) and not result['administrator']:
            result['administrator'] = re.sub(r'Administrator:\s*', '', header_line, flags=re.IGNORECASE).strip()
            if not quiet:
                print(f"    Administrator: {result['administrator']}")
        elif re.match(r'Judges?:\s*', header_line, re.IGNORECASE) and not result['judges']:
            result['judges'] = re.sub(r'Judges?:\s*', '', header_line, flags=re.IGNORECASE).strip()
            if not quiet:
                print(f"    Judges: {result['judges']}")

    return result

_TITLE_SKIP_MARKERS = (
    'click here', 'homepage', 'go-to-ground', 'go-to-gound', 'conformation division',
    'trial results', 'jrtca yearbook', 'owned by', 'entries:', 'welcome',
)

_TITLE_KEYWORDS = (
    'trial', 'classic', 'festival', 'national', 'challenge', 'terrier', 'jamboree',
    'benefit', 'showdown', 'spectacular', 'championship', 'rendezvous', 'congress',
    'cup', 'celebration', 'regional', 'promenade', 'earthdog', 'missouri', 'memorial',
)
_CLASS_HEADER_RE = re.compile(
    r'^Class\s+(\d+[a-z]?)(?:st|nd|rd|th)?\s*[:.\t]\s*(.+)$',
    re.IGNORECASE,
)
# For files that omit the colon after the class number (e.g. 2009 MO Earthdogs TXT):
# "Class 13 Working Dogs 1 yr and up, 10-12.5"" - no colon separator
_CLASS_HEADER_NO_COLON_RE = re.compile(
    r'^Class\s+(\d+[a-z]?)\s+([A-Z][^\t]+)$',
    re.IGNORECASE,
)
# 2017 MO Earthdogs PDF uses "Division N: Name" and "Section A: Name" headers.
# Division headers are treated like top-level section headers (division inference
# is applied to their name to determine the actual division).
# Section headers are treated like racing/division subdivisions.
_DIVISION_HEADER_RE = re.compile(
    r'^Division\s+\d+[a-z]?\s*:\s+(.+)$',
    re.IGNORECASE,
)
_SECTION_HEADER_RE = re.compile(
    r'^Section\s+\w+\s*:\s+(.+)$',
    re.IGNORECASE,
)
_TIME_TOKEN_RE = re.compile(r'^\d+:\d+(?:\.\d+)?$|^\d+\.\d+$')
_PLACEMENT_TIME_SUFFIX_RE = re.compile(
    r'\s*[-–—]\s*(?:tme|time)\s*(?:of\s+)?(\d+:\d+(?:\.\d+)?|\d+\.\d+)\s*(?:;.*)?$',
    re.IGNORECASE,
)
SPECIAL_TRIAL_FOLDERS = ('Gold Coast', 'JRTCC', 'MO Earthdogs')
_TITLE_SUBDIVISION_MARKERS = (
    'flat races', 'steeplechase races', 'steeplechase', 'hurdle races', 'hurdles',
    'super earth', 'go-to-ground', 'go-to-gound', 'conformation division',
    'agility division', 'obedience division', 'racing division', 'youth division',
)
_GENERIC_SEASON_TRIAL_RE = re.compile(
    r'^(?:january|february|march|april|may|june|july|august|september|october|november|december|'
    r'fall|spring|winter|summer)(?:\s+\d{4})?\s+trial$',
    re.IGNORECASE,
)
_JRTNNC_PREFIX_RE = re.compile(
    r'^JRTNNC\s+.+\bAnnual\b',
    re.IGNORECASE,
)

def _is_ocr_garbage_title(line: str) -> bool:
    """Reject mangled OCR like 'SOUTHFLO DATER ERTR L'."""
    if not line or len(line) < 8:
        return False
    low = line.lower()
    # Any recognised trial-title keyword means this is not OCR garbage
    if any(keyword in low for keyword in _TITLE_KEYWORDS):
        return False
    if re.search(
        r'\b(?:terrier|trial|festival|classic|national|jrtca|jrtnnc|showdown|benefit|'
        r'earthdogs?|missouri|memorial)\b',
        line,
        re.I,
    ):
        return False
    if _line_looks_like_location_date(line):
        return False
    words = re.findall(r'[A-Za-z]{3,}', line)
    if len(words) >= 2 and line.strip().isupper():
        recognized = {
            'south', 'north', 'east', 'west', 'florida', 'texas', 'trial', 'annual',
            'jrtca', 'jrtnnc', 'national', 'festival', 'classic', 'carolina', 'mason',
            'dixon', 'heartland', 'yankee', 'museum', 'midwest', 'autumn', 'spring',
            'missouri', 'earthdogs', 'earthdog', 'memorial', 'bash', 'day',
        }
        if not any(w.lower() in recognized for w in words):
            return True
    return False

def is_weak_trial_name(name: str) -> bool:
    """True when extracted title should be replaced by filename."""
    if not name:
        return True
    low = name.strip().lower()
    if low in _TITLE_SUBDIVISION_MARKERS or low == 'racing':
        return True
    if _GENERIC_SEASON_TRIAL_RE.match(low):
        return True
    if _is_ocr_garbage_title(name):
        return True
    return False

def trial_name_from_filename(file_path: str) -> str:
    import os
    filename = os.path.basename(file_path)
    trial_name = filename.replace('debug_trialvault_', '').replace('debug_trial_', '').replace('_raw.txt', '')
    for ext in ('.txt', '.html', '.htm', '.pdf'):
        trial_name = trial_name.replace(ext, '')
    trial_name = trial_name.replace('_', ' ')
    trial_name = re.sub(r'\s+w\s+gtg\s+times$', '', trial_name, flags=re.IGNORECASE).strip()
    mo_match = re.match(r'^(\d{4})\s+mo\s+earthdogs', trial_name, re.IGNORECASE)
    if mo_match:
        return f'{mo_match.group(1)} Missouri Earthdogs Memorial Day Bash'
    # Bare PDF names: trialresults2013.pdf / moearthdogs trialresults2017.pdf
    moe_pdf = re.search(
        r'(?:mo\s*earthdogs?\s+)?trial\s*results?\s*(\d{4})',
        trial_name,
        re.IGNORECASE,
    )
    if moe_pdf and 'earthdog' in (file_path or '').lower().replace('\\', '/'):
        return f'{moe_pdf.group(1)} Missouri Earthdogs Memorial Day Bash'
    # Filename without year prefix but path year present
    if re.search(r'\bmo\s*earthdogs?\b', trial_name, re.IGNORECASE):
        year_match = re.search(r'(\d{4})', trial_name)
        if year_match:
            return f'{year_match.group(1)} Missouri Earthdogs Memorial Day Bash'
    gc_match = re.match(r'^(\d{4})\s+gold coast\s+([ivx]+)\b', trial_name, re.IGNORECASE)
    if gc_match:
        return f'{gc_match.group(1)} Gold Coast {gc_match.group(2).upper()}'
    if re.search(r'\bgctn\b', trial_name, re.IGNORECASE):
        year_match = re.search(r'(\d{4})', trial_name)
        if year_match:
            return f'{year_match.group(1)} Gold Coast Trial'
    jrtcc_match = re.search(r'(\d{4})\s+jrtcc', trial_name, re.IGNORECASE)
    if jrtcc_match:
        year = jrtcc_match.group(1)
        base = f'{year} JRTCC National Trial'
        low = trial_name.lower()
        if re.search(r'\b(sat|saturday)\b', low):
            return f'{base} - Saturday'
        if re.search(r'\b(sun|sunday)\b', low):
            return f'{base} - Sunday'
        return base
    return ' '.join(trial_name.split())

def combine_split_trial_title(lines: List[str]) -> str:
    """Merge split headers like 'JRTNNC Sixteenth Annual' + 'MAY TRIAL'."""
    for i in range(min(len(lines) - 1, 15)):
        line1 = _clean_trial_title_candidate(lines[i].strip())
        line2 = _clean_trial_title_candidate(lines[i + 1].strip())
        if not line1 or not line2:
            continue
        if _JRTNNC_PREFIX_RE.match(line1) and _GENERIC_SEASON_TRIAL_RE.match(line2):
            season = line2.title()
            return f"{line1} {season}"
        if re.search(r'\bAnnual\b', line1, re.I) and _GENERIC_SEASON_TRIAL_RE.match(line2):
            return f"{line1} {line2.title()}"
    return ""

def _is_title_metadata_line(line: str) -> bool:
    """Return True when a line is header metadata, not a trial title."""
    low = line.lower()
    if any(marker in low for marker in _TITLE_SKIP_MARKERS):
        return True
    if re.match(
        r'^(chair(?:person|man)?s?|judges?|administrators?|administered by|1st|2nd|3rd|4th|best|entries)\b',
        low,
    ):
        return True
    if re.match(r'^(conformation|go-to-ground|go-to-gound|racing|trailing|agility)\b', low):
        return True
    if low in _TITLE_SUBDIVISION_MARKERS:
        return True
    if _GENERIC_SEASON_TRIAL_RE.match(low):
        return True
    if _is_ocr_garbage_title(line):
        return True
    if _line_looks_like_location_date(line):
        return True
    return False

def _clean_trial_title_candidate(candidate: str) -> str:
    candidate = candidate.lstrip('\ufeff')
    candidate = re.sub(r'\s*-\s*jrtca yearbook.*$', '', candidate, flags=re.IGNORECASE).strip()
    return candidate.rstrip(' -')

def extract_trial_title_line(lines: List[str]) -> str:
    """Return the best line that looks like a trial title."""
    candidates: List[str] = []
    for line in lines[:40]:
        candidate = _clean_trial_title_candidate(line.strip())
        if not candidate or len(candidate) < 5 or len(candidate) > 100:
            continue
        if _is_title_metadata_line(candidate):
            continue
        if re.match(r'^\d', candidate):
            if not (
                re.match(r'^\d{4}\s', candidate)
                and any(keyword in candidate.lower() for keyword in _TITLE_KEYWORDS)
            ):
                continue
        candidates.append(candidate)

    for candidate in candidates:
        low = candidate.lower()
        if any(keyword in low for keyword in _TITLE_KEYWORDS):
            return candidate
    # Prefer combined JRTNNC split title over weak first candidate
    combined = combine_split_trial_title(lines)
    if combined:
        return combined
    return candidates[0] if candidates else ""

def trial_name_key(name: str) -> str:
    return re.sub(r'[^a-z0-9]', '', (name or '').lower())

def _effective_national_year(name: str, year: int | None) -> int | None:
    """Prefer year embedded in trial name over folder/DB year for national trials."""
    if name:
        match = re.search(r'\b(19\d{2}|20\d{2})\b', name)
        if match:
            return int(match.group(1))
    return year

def canonical_trial_match_key(name: str, year: int | None = None) -> str:
    """Normalize trial names for duplicate detection across year prefixes/variants."""
    low = (name or '').strip().lower()
    day_suffix = ''
    if re.search(r'\b(saturday|sat\.?)\b', low):
        day_suffix = ':sat'
    elif re.search(r'\b(sunday|sun\.?)\b', low):
        day_suffix = ':sun'
    low = re.sub(r'^\d{4}\s+', '', low)
    alnum = re.sub(r'[^a-z0-9]', '', low)
    if 'national' in alnum or alnum in ('jrtcanationals', 'nationaltrial'):
        effective_year = _effective_national_year(name, year)
        year_part = str(effective_year) if effective_year else ''
        if 'jrtcc' in alnum:
            return f'{year_part}:jrtcc:national{day_suffix}' if year_part else f'jrtcc:national{day_suffix}'
        if 'jrtca' in alnum:
            return f'{year_part}:jrtca:national{day_suffix}' if year_part else f'jrtca:national{day_suffix}'
        return f'{year_part}:national{day_suffix}' if year_part else f'national{day_suffix}'
    return f'{year}:{alnum}' if year else alnum

def canonical_trial_display_name(name: str, year: int) -> str:
    """Return a consistent display name for well-known trial variants."""
    key = canonical_trial_match_key(name, year)
    if ':jrtcc:national:sat' in key:
        effective_year = int(key.split(':', 1)[0])
        return f'{effective_year} JRTCC National Trial - Saturday'
    if ':jrtcc:national:sun' in key:
        effective_year = int(key.split(':', 1)[0])
        return f'{effective_year} JRTCC National Trial - Sunday'
    if ':jrtcc:national' in key:
        effective_year = int(key.split(':', 1)[0])
        return f'{effective_year} JRTCC National Trial'
    if key.endswith(':national') and key != 'national':
        effective_year = int(key.split(':', 1)[0])
        return f'{effective_year} JRTCA National Trial'
    return (name or '').strip()

def is_invalid_trial_name(name: str) -> bool:
    """True when extracted title is clearly not a trial name."""
    if is_weak_trial_name(name):
        return True
    low = (name or '').strip().lower()
    if not low:
        return True
    if low.startswith('/') or 'accordion content' in low or 'dynamic drive' in low:
        return True
    # Narrative boilerplate (e.g. 2009 MO Earthdogs disclaimer / website promo)
    if (
        'if you find any errors' in low
        or 'please send me a' in low
        or 'results will also be posted' in low
        or 'www.' in low
        or low.startswith('http')
    ):
        return True
    if re.match(r'^[^,]+,\s*[a-z]{2,}$', low):
        return True
    if re.match(r'^(working terrier )?conformation( division)?$', low):
        return True
    if low.endswith(' division') and 'trial' not in low:
        return True
    if low.startswith('champion:') or low.startswith('reserve:'):
        return True
    if re.match(r'^class\s+\d', low):
        return True
    return False

def extract_html_trial_metadata(raw_html: str) -> Dict[str, str]:
    """Extract location/dates from modern HTML meta tags before tag stripping."""
    result = {
        'location': '',
        'start_date': '',
        'end_date': '',
        'chair': '',
        'administrator': '',
        'judges': '',
    }
    if not raw_html:
        return result

    meta_text = ''
    for pattern in (
        r'property=["\']og:description["\'][^>]*content=["\']([^"\']+)',
        r'content=["\']([^"\']+)["\'][^>]*property=["\']og:description',
        r'name=["\']description["\'][^>]*content=["\']([^"\']+)',
    ):
        match = re.search(pattern, raw_html, re.IGNORECASE | re.DOTALL)
        if match:
            meta_text = html_module.unescape(match.group(1))
            break

    if meta_text:
        header_part = re.split(r'\bChaired by\b', meta_text, maxsplit=1, flags=re.IGNORECASE)[0].strip()
        if '~' in header_part or any(month in header_part for month in _MONTH_NAMES):
            location, start_date, end_date = _parse_location_date_from_line(header_part)
            if start_date:
                result['location'] = location
                result['start_date'] = start_date
                result['end_date'] = end_date

        chair_match = re.search(r'Chaired by:\s*([^A]+?)(?:\s+Administered by:|\s+Administrators?:|\s+Judges:|$)', meta_text, re.IGNORECASE)
        if chair_match:
            result['chair'] = chair_match.group(1).strip()
        admin_match = re.search(r'(?:Administered by|Administrators?):\s*([^J]+?)(?:\s+Judges:|$)', meta_text, re.IGNORECASE)
        if admin_match:
            result['administrator'] = admin_match.group(1).strip()
        judges_match = re.search(r'Judges:\s*(.+)$', meta_text, re.IGNORECASE)
        if judges_match:
            result['judges'] = judges_match.group(1).strip()

    time_match = re.search(r'<time[^>]*datetime=["\'](\d{4}-\d{2}-\d{2})', raw_html, re.IGNORECASE)
    if time_match and not result['start_date']:
        iso_date = time_match.group(1)
        try:
            dt = datetime.strptime(iso_date, '%Y-%m-%d')
            result['start_date'] = dt.strftime('%B %d, %Y').replace(' 0', ' ')
            result['end_date'] = result['start_date']
        except ValueError:
            pass

    return result

def get_connection():
    """Get database connection."""
    for driver in ODBC_DRIVERS:
        try:
            conn_str = CONN_STR.replace("ODBC Driver 17 for SQL Server", driver)
            conn = _require_pyodbc().connect(conn_str, timeout=10)
            print(f"  Connected using driver: {driver}")
            return conn
        except Exception as e:
            if driver == ODBC_DRIVERS[-1]:
                raise
            continue
    return None

def get_next_ids_from_db(conn) -> tuple[int, int, int]:
    """Read next ID counters from current database state."""
    cursor = conn.cursor()
    cursor.execute("SELECT ISNULL(MAX(TrialListID), 0) + 1 FROM [sResults].[TrialList]")
    next_trial_id = cursor.fetchone()[0]
    cursor.execute("SELECT ISNULL(MAX(TrialClassID), 0) + 1 FROM [sResults].[TrialClass]")
    next_trialclass_id = cursor.fetchone()[0]
    cursor.execute("SELECT ISNULL(MAX(TrialPlacementsID), 0) + 1 FROM [sResults].[TrialPlacements]")
    next_placement_id = cursor.fetchone()[0]
    return next_trial_id, next_trialclass_id, next_placement_id


def get_next_placement_times_id(conn) -> int:
    """Read next TrialPlacements_TimesID from current database state."""
    cursor = conn.cursor()
    cursor.execute(
        "SELECT ISNULL(MAX(TrialPlacements_TimesID), 0) + 1 FROM [sResults].[TrialPlacements_Times]"
    )
    return cursor.fetchone()[0]


def clear_all_trial_data(conn):
    """Clear all trial results and related lookup tables for a fresh reload."""
    cursor = conn.cursor()
    
    print("\n" + "=" * 80)
    print("CLEARING ALL TRIAL RESULTS DATA")
    print("=" * 80)
    
    try:
        max_attempts = 5
        tables_in_order = [
            ("TrialPlacements_Times", "[sResults].[TrialPlacements_Times]"),
            ("TrialPlacements", "[sResults].[TrialPlacements]"),
            ("TrialClass", "[sResults].[TrialClass]"),
            ("CatalogEntry", "[sResults].[CatalogEntry]"),
            ("Relationship", "[sResults].[Relationship]"),
            ("TrialList", "[sResults].[TrialList]"),
            ("Dog", "[sResults].[Dog]"),
            ("Owner", "[sResults].[Owner]"),
            ("Class", "[sResults].[Class]"),
            ("Division", "[sResults].[Division]"),
        ]

        for attempt in range(1, max_attempts + 1):
            print(f"\nClear attempt {attempt}/{max_attempts}...")
            totals = {}
            for label, table in tables_in_order:
                try:
                    cursor.execute(f"DELETE FROM {table}")
                    totals[label] = cursor.rowcount
                    print(f"  Deleted {totals[label]:,} from {label}")
                except Exception as e:
                    if "Invalid object name" in str(e):
                        print(f"  Skipping {label} (table not found)")
                        totals[label] = 0
                    else:
                        raise

            conn.commit()

            remaining = 0
            for label, table in tables_in_order:
                try:
                    cursor.execute(f"SELECT COUNT(*) FROM {table}")
                    count = cursor.fetchone()[0]
                    if count:
                        print(f"  Remaining in {label}: {count:,}")
                    remaining += count
                except Exception:
                    pass

            if remaining == 0:
                print(f"\n  SUCCESS: All tables empty after attempt {attempt}")
                break
            if attempt == max_attempts:
                raise Exception(f"Database clearing failed - {remaining:,} records remain")

        print("=" * 80)
        
    except Exception as e:
        conn.rollback()
        print(f"ERROR: Failed to clear trial results tables: {e}")
        raise

def _is_html_file(file_path: str) -> bool:
    return file_path.lower().endswith(('.html', '.htm'))

def extract_trial_info(lines: List[str], year: int, file_path: str = None) -> Optional[TrialInfo]:
    """
    Extract trial metadata from file lines.
    
    Logic:
    1. Skip lines until after year-based navigation (e.g., "2025 Trial Results", "2025 Conformation Division", etc.)
    2. Find two duplicate lines - these are the trial name
    3. Shortly after, find the header block with location, dates, chair, administrator, judges
    """
    trial_name = None
    location = ""
    start_date = ""
    end_date = ""
    chair = ""
    administrator = ""
    judges = ""
    
    # First, skip all the navigation/header stuff
    # Look for end of navigation (last occurrence of year-based links like "2025 Working Achievement Awards")
    last_nav_idx = 0
    for i, line in enumerate(lines):
        line_clean = line.strip()
        # Check if this is a year-based navigation line
        if re.search(r'\d{4}\s+(Trial Results|Conformation Division|Performance Division|Bronze Medallions|Working Achievement Awards)', line_clean):
            last_nav_idx = i
    
    # Now look for duplicate trial name lines after navigation
    for i in range(last_nav_idx, min(len(lines) - 1, last_nav_idx + 50)):
        line1 = lines[i].strip()
        line2 = lines[i + 1].strip() if i + 1 < len(lines) else ""
        
        # Skip empty lines and very short lines
        if not line1 or len(line1) < 5:
            continue
        
        # Check for duplicate lines (trial name)
        if line1 == line2 and line1 and not is_weak_trial_name(line1):
            # This looks like our trial name!
            trial_name = line1
            safe_print(f"    Found trial name: {trial_name}", flush=True)

            header = scan_trial_header_block(lines, start_idx=i + 2, max_lines=500, hint_year=year)
            location = header['location']
            start_date = header['start_date']
            end_date = header['end_date']
            chair = header['chair']
            administrator = header['administrator']
            judges = header['judges']
            break

    if not trial_name:
        combined = combine_split_trial_title(lines)
        if combined:
            trial_name = combined
            safe_print(f"    Found combined trial name: {trial_name}", flush=True)
            header = scan_trial_header_block(lines, start_idx=0, max_lines=500, hint_year=year)
            location = header['location']
            start_date = header['start_date']
            end_date = header['end_date']
            chair = header['chair']
            administrator = header['administrator']
            judges = header['judges']

    if not trial_name:
        # Try to extract trial name from file content, then filename
        title_line = extract_trial_title_line(lines)
        if title_line and not is_weak_trial_name(title_line):
            trial_name = title_line
            safe_print(f"    Found trial name from content: {trial_name}", flush=True)
            header = scan_trial_header_block(lines, start_idx=0, max_lines=500, hint_year=year)
            location = header['location'] or location
            start_date = header['start_date'] or start_date
            end_date = header['end_date'] or end_date
            chair = header['chair'] or chair
            administrator = header['administrator'] or administrator
            judges = header['judges'] or judges

    if not trial_name or is_invalid_trial_name(trial_name):
        if file_path:
            filename_name = trial_name_from_filename(file_path)
            if filename_name:
                if trial_name and is_invalid_trial_name(trial_name):
                    safe_print(
                        f"    Replacing weak trial name '{trial_name}' with filename: {filename_name}",
                        flush=True,
                    )
                else:
                    safe_print(f"    Using trial name from filename: {filename_name}", flush=True)
                trial_name = filename_name
                if not location and not start_date:
                    header = scan_trial_header_block(lines, start_idx=0, max_lines=500, hint_year=year)
                    location = header['location'] or location
                    start_date = header['start_date'] or start_date
                    end_date = header['end_date'] or end_date
                    chair = header['chair'] or chair
                    administrator = header['administrator'] or administrator
                    judges = header['judges'] or judges
        elif not trial_name:
            print("    WARNING: Could not extract trial name")
            return None

    # Use extracted dates/name year before canonical naming (folder year can be wrong)
    if start_date:
        year_match = re.search(r',?\s*(\d{4})', start_date)
        if year_match:
            extracted_year = int(year_match.group(1))
            if extracted_year != year:
                if abs(extracted_year - year) <= 1:
                    print(f"    Note: Using extracted year {extracted_year} instead of folder year {year}")
                    year = extracted_year
                else:
                    print(
                        f"    Note: Ignoring suspicious extracted year {extracted_year}; "
                        f"keeping folder year {year}",
                        flush=True,
                    )
                    start_date = start_date.replace(str(extracted_year), str(year))
                    if end_date:
                        end_date = end_date.replace(str(extracted_year), str(year))
    else:
        name_year_match = re.search(r'\b(19\d{2}|20\d{2})\b', trial_name or '')
        if name_year_match:
            extracted_year = int(name_year_match.group(1))
            if extracted_year != year and abs(extracted_year - year) <= 1:
                print(f"    Note: Using name year {extracted_year} instead of folder year {year}")
                year = extracted_year

    if file_path:
        path_lower = file_path.replace('\\', '/').lower()
        is_jrtcc = '/jrtcc/' in path_lower or path_lower.startswith('jrtcc/')
        is_moe = '/mo earthdogs/' in path_lower or path_lower.startswith('mo earthdogs/')
        if is_jrtcc or is_moe:
            # Prefer stable filename-derived names over flaky PDF/TXT header noise
            filename_name = trial_name_from_filename(file_path)
            if filename_name:
                trial_name = filename_name
        for folder_name in SPECIAL_TRIAL_FOLDERS:
            if f'/{folder_name.lower()}/' in path_lower:
                slot = _special_folder_slot_key(os.path.basename(file_path), folder_name)
                if folder_name == 'Gold Coast' and slot:
                    if not re.search(rf'\b{re.escape(slot)}\b', trial_name or '', re.IGNORECASE):
                        trial_name = f'{trial_name} {slot}'
                elif folder_name == 'JRTCC' and slot == 'sat':
                    if not re.search(r'\b(saturday|sat\.?)\b', trial_name or '', re.IGNORECASE):
                        trial_name = f'{trial_name} - Saturday'
                elif folder_name == 'JRTCC' and slot == 'sun':
                    if not re.search(r'\b(sunday|sun\.?)\b', trial_name or '', re.IGNORECASE):
                        trial_name = f'{trial_name} - Sunday'
                break

    trial_name = canonical_trial_display_name(trial_name, year)
    
    return TrialInfo(
        trial_name=trial_name,
        location=location,
        start_date=start_date,
        end_date=end_date,
        chair=chair,
        administrator=administrator,
        judges=judges,
        year=year
    )

def parse_placements(lines: List[str], trial_info: TrialInfo) -> List[PlacementResult]:
    """
    Parse placement results from file lines.
    
    Handles different formats:
    1. Standard: "1st: Dog Name, owned by Owner Name"
    2. Best/Reserve: "Best: Dog Name, owned by Owner Name"
    3. Champion/Reserve: "Champion: Dog Name, owned by Owner Name"
    """
    results = []
    current_division = ""
    current_subdivision = ""  # For things like "FLAT RACES", "STEEPLECHASE RACES"
    current_class = ""
    current_entries = 0
    pending_racing_height_prefix = ""
    last_parsed_class = ""
    # True when the current division was set by an explicit section header line
    # (via normalize_mixed_case_section_header or the all-caps keyword detection).
    # False when it was inferred from the class name.  Only inferred divisions
    # may be silently overridden by class-name inference; explicit ones are kept.
    current_division_is_explicit = False
    
    # Find where results start (after header block).
    # Look for the FIRST line that could be a division header or class header,
    # whichever comes first.  This is important for files that begin directly
    # with "Class N:" lines and have no explicit division header (e.g. 2013 PDF).
    start_idx = 0
    for i, line in enumerate(lines):
        line_clean = line.strip()
        if normalize_mixed_case_section_header(line_clean):
            start_idx = i
            break
        # Normalize special characters for consistent division detection
        line_normalized = line_clean.replace('·', '-').replace('–', '-').replace('—', '-')
        # Check if this line is a division header
        # Normalize for comparison (handle spaces and special chars)
        line_normalized_temp = line_clean.replace('·', '-').replace('–', '-').replace('—', '-').replace('\xa0', '-').replace('\u00a0', '-').replace(' ', '-')
        if line_clean.isupper() and len(line_clean) > 3 and len(line_clean) < 50:
            if any(keyword in line_normalized_temp for keyword in _DIVISION_KEYWORDS) or is_go_to_ground_division(line_clean):
                start_idx = i
                break
        # Also treat the first "Class N:" or "Division N:" line as a valid start point.
        # This handles PDF files that lack an explicit division header before Class 1.
        if (_CLASS_HEADER_RE.match(line_clean) or _DIVISION_HEADER_RE.match(line_clean)) and i > 0:
            start_idx = i
            break
    
    i = start_idx
    while i < len(lines):
        line = lines[i].strip()
        
        # Normalize special characters (middle dot, en-dash, em-dash, nbsp, etc) to regular hyphen
        # This handles cases like "GO·TO·GROUND" or "GO–TO–GROUND" or "GO TO-GROUND"
        line_normalized = line.replace('·', '-').replace('–', '-').replace('—', '-').replace('\xa0', '-').replace('\u00a0', '-')
        # For division detection, also try with spaces normalized to hyphens
        line_for_division = line_normalized.replace(' ', '-')
        
        # Skip empty lines
        if not line:
            i += 1
            continue

        section_header = normalize_mixed_case_section_header(line)
        if section_header:
            current_division = canonical_division_name(section_header)
            current_division_is_explicit = True
            current_subdivision = ""
            current_class = ""
            safe_print(f"  Processing division: {current_division}", flush=True)
            i += 1
            continue

        # Handle "Division N: Name" headers (2017 MO Earthdogs PDF format).
        # Treat them like section headers: infer or set the division from the name.
        div_header_m = _DIVISION_HEADER_RE.match(line)
        if div_header_m:
            div_name = div_header_m.group(1).strip()
            explicit = normalize_mixed_case_section_header(div_name)
            if explicit:
                inferred_div = canonical_division_name(explicit)
            else:
                inferred_div = infer_division_from_class_name(div_name)
            if inferred_div:
                current_division = inferred_div
                current_division_is_explicit = True
                current_subdivision = ""
                current_class = ""
                safe_print(f"  Processing division (from Division header): {current_division}", flush=True)
            i += 1
            continue

        # Handle "Section A: Name" headers (2017 MO Earthdogs PDF format).
        # Treat as a racing/section subdivision label when inside a racing division,
        # or as a section/class indicator otherwise.
        # When the section itself is clearly GTG/Racing/etc., also switch the main
        # division so Championship GTG does not stay under CONFORMATION.
        sec_header_m = _SECTION_HEADER_RE.match(line)
        if sec_header_m:
            sec_name = sec_header_m.group(1).strip()
            sec_upper = sec_name.upper()
            if re.search(r'\b(?:CHILD|YOUTH)\b', sec_upper):
                # Keep youth sections in YOUTH even when they mention Go-to-Ground
                if current_division != 'YOUTH DIVISION':
                    current_division = 'YOUTH DIVISION'
                    current_division_is_explicit = True
                    safe_print(
                        f"  Processing division (from Section header): {current_division}",
                        flush=True,
                    )
            else:
                inferred_from_section = infer_division_from_class_name(sec_name)
                if inferred_from_section and should_override_division(
                    current_division, inferred_from_section,
                ):
                    current_division = inferred_from_section
                    current_division_is_explicit = True
                    safe_print(
                        f"  Processing division (from Section header): {current_division}",
                        flush=True,
                    )
            if current_division:
                current_subdivision = sec_name
                current_class = ""
                safe_print(f"    Section: {sec_name}", flush=True)
            i += 1
            continue

        # Check for all-caps headers (could be division, subdivision, or class)
        # Pattern: All caps line that's likely a header (not a class name)
        # Headers are usually short (< 50 chars) and don't contain "Entries:"
        # Note: We allow "–" in headers (e.g., "SUITABILITY – JUDGE'S CHOICE") as long as there's no "ENTRIES"
        if line.isupper() and len(line) > 3 and len(line) < 50 and 'ENTRIES' not in line and 'CHAMPION' not in line and 'RESERVE' not in line and 'BEST' not in line:

            # FIRST: Check if this is a known CONFORMATION subdivision pattern (BEFORE checking if it's a division)
            # These should NEVER be treated as main divisions
            is_conformation_subdivision = False
            if 'CONFORMATION' in line_normalized and line_normalized not in ['CONFORMATION', 'CONFORMATION DIVISION']:
                # Patterns like "WORKING TERRIER CONFORMATION", "OPEN ADULT CONFORMATION"
                is_conformation_subdivision = True
            elif any(keyword in line_for_division for keyword in ['FAMILY', 'BREEDER', 'MISCELLANEOUS', 'SUITABILITY', 'VETERAN']):
                # Patterns like "FAMILY CLASSES", "BREEDER'S CLASSES", "MISCELLANEOUS", "SUITABILITY"
                is_conformation_subdivision = True
            
            if is_conformation_subdivision:
                # If we don't have a CONFORMATION division set yet, set it now
                if not current_division or 'CONFORMATION' not in current_division:
                    current_division = "CONFORMATION DIVISION"
                    current_division_is_explicit = True
                    safe_print(f"  Processing division: {current_division}", flush=True)

                # Now set this as a subdivision
                current_subdivision = line
                current_class = ""  # Reset class when entering new subdivision
                safe_print(f"    Subdivision: {current_subdivision}", flush=True)
                i += 1
                continue
            
            # SECOND: Check for RACING subdivision headers
            if current_division and 'RACING' in current_division and any(keyword in line_normalized for keyword in ['RACES', 'HURDLES', 'JUMPS']):
                current_subdivision = line
                current_class = ""  # Reset class when entering new subdivision
                safe_print(f"    Subdivision: {current_subdivision}", flush=True)
                i += 1
                continue

            # NOSEWORK section under a trial is its own division (not TRAILING & LOCATING)
            if is_nosework_section_header(line):
                current_division = 'NOSE WORK'
                current_division_is_explicit = True
                current_subdivision = ""
                current_class = ""
                safe_print(f"  Processing division: {current_division}", flush=True)
                i += 1
                continue

            # JUMPING DIVISION is an agility section (Jumpers), not a separate division
            if is_agility_subdivision_header(line_normalized):
                if not current_division or 'AGILITY' not in current_division:
                    current_division = "AGILITY DIVISION"
                    current_division_is_explicit = True
                    safe_print(f"  Processing division: {current_division}", flush=True)
                current_subdivision = ""
                current_class = ""
                safe_print(f"    Agility section: {line}", flush=True)
                i += 1
                continue
            
            # THIRD: Check for division header (new main division)
            # Can be: "CONFORMATION DIVISION", "CONFORMATION", "GO-TO-GROUND", "OBEDIENCE", "RALLY OBEDIENCE", "YOUTH", etc.
            # Common divisions: CONFORMATION, GO-TO-GROUND, AGILITY, OBEDIENCE, RACING, YOUTH, BALL TOSS, etc.
            if is_division_header(line, line_for_division):
                current_division = canonical_division_name(line)
                current_division_is_explicit = True
                current_subdivision = ""  # Reset subdivision when entering new division
                current_class = ""  # Reset class when entering new division
                safe_print(f"  Processing division: {current_division}", flush=True)
                i += 1
                continue
        
        # Pre-process class lines that mis-use "owned by" for height specifications.
        # e.g. "Class 13 Working Dogs 1 yr and up, owned by 10-12.5"" ->
        #      "Class 13 Working Dogs 1 yr and up, 10-12.5""
        # This appears in some older MO Earthdogs TXT files.
        if re.match(r'^class\s+\d', line, re.IGNORECASE) and ', owned by' in line.lower():
            cleaned_line = strip_owned_by_height_from_class_name(line)
            if cleaned_line != line:
                line = cleaned_line

        # Check for class name with entries count
        # Format: "Dog Pups, 6 up to 9 months – Entries: 5" or "Puppy Championship GTG – Entries: 5"
        # Also handle missing entry count: "Youth Handler Go-To-Ground – Entries:"
        # Also handle no dash: "Bitch Pups, 4-6 months Entries: 1"
        # Also handle HTML split: "Adult Certificate Super Earth" + ", 10 up to 12½" – Entries: 24"
        line = join_split_certificate_class_line(line, lines, i)
        parsed_class = try_parse_class_with_entries(line, lines, i)
        if parsed_class:
            current_class, current_entries, extra = parsed_class
            current_division = maybe_switch_to_nosework_division(
                current_division, current_class,
            )
            inferred = infer_division_from_class_name(current_class)
            if not current_division_is_explicit and should_override_division(current_division, inferred):
                current_division = inferred
                safe_print(f"  Processing division (inferred): {current_division}", flush=True)
            if current_entries > 0:
                safe_print(f"    Class: {current_class} ({current_entries} entries)", flush=True)
            else:
                safe_print(f"    Class: {current_class}", flush=True)
            i += 1 + extra
            continue
        
        # Check for class name without entries (e.g., "BEST PUPPY BITCH & RESERVE")
        # These are all-caps lines that aren't divisions
        # Also handle mixed-case OCR like "PUppy RACING CHAMPION & RESERVE"
        # IMPORTANT: do not treat placement lines like "Reserve Champion – Dog (Owner)"
        # as class headers — that drops racing/GTG reserves entirely.
        line_upper = line.upper()
        is_champion_reserve_class = (
            'CHAMPION' in line_upper and 'RESERVE' in line_upper
            and 'DIVISION' not in line_upper
            and ', owned by' not in line.lower()
            and not is_placement_line_start(line)
        )
        if (line.isupper() or is_champion_reserve_class) and len(line) > 5 and 'DIVISION' not in line:
            clean_class, entries = strip_entries_from_class_name(line)
            candidate = repair_racing_class_ocr(clean_class if entries is not None else line)
            if not is_plausible_class_name(candidate):
                i += 1
                continue
            current_class = canonicalize_over_under_championship_class(candidate, current_division)
            current_division = maybe_switch_to_nosework_division(
                current_division, current_class,
            )
            current_entries = entries if entries is not None else 0
            safe_print(f"    Class: {current_class}", flush=True)
            i += 1
            continue

        class_header = _CLASS_HEADER_RE.match(line)
        # Also try no-colon format: "Class 13 Working Dogs 1 yr and up, 10-12.5""
        if not class_header and re.match(r'^class\s+\d', line, re.IGNORECASE):
            nc = _CLASS_HEADER_NO_COLON_RE.match(line)
            if nc and is_plausible_class_name(nc.group(2).strip()):
                class_header = nc
        if class_header:
            current_class = repair_racing_class_ocr(class_header.group(2).strip())
            current_class, parsed_entries = strip_entries_from_class_name(current_class)
            current_division = maybe_switch_to_nosework_division(
                current_division, current_class,
            )
            # Infer the division from class name keywords.
            # Only allowed when the current division was NOT set by an explicit
            # section header line.  This prevents class names like "Stakes Go-To-Ground"
            # (within SUPER EARTH / MASTER'S DEN STAKES) from incorrectly overriding
            # the explicitly-set MASTER'S DEN STAKES division.
            inferred = infer_division_from_class_name(current_class)
            if not current_division_is_explicit and should_override_division(current_division, inferred):
                current_division = inferred
                safe_print(f"  Processing division (inferred): {current_division}", flush=True)
            current_entries = parsed_entries if parsed_entries is not None else 0
            safe_print(f"    Class: {current_class}", flush=True)
            i += 1
            continue
        
        # Check for mixed-case class names (older files format)
        # If next line starts with placement marker, this line is likely a class name
        # Example: "Bitch Puppy, 6-11 months, 10"-12""
        # BUT: don't treat placement lines themselves as class names
        # BUT: don't treat wrapped owner surnames as class names (Peachtree 2014 HTML)
        if results and is_owner_surname_continuation(line, lines, i):
            results[-1].owner_name = f"{results[-1].owner_name} {line.strip()}".strip()
            i += 1
            continue

        line_for_placement = normalize_line_for_placement(line)
        current_line_is_placement = is_placement_line_start(line)
        next_placement_idx = find_next_placement_index(lines, i)
        if not current_line_is_placement and next_placement_idx is not None:
            is_placement = True
            if current_division and not line.isupper() and ', owned by' not in line.lower():
                # Height-only line before Champion/Reserve belongs to championship class
                if _CHAMPIONSHIP_CLASS_RE.search(current_class or '') and is_racing_height_prefix_line(line):
                    pass
                else:
                    clean_class, entries = strip_entries_from_class_name(line)
                    candidate = repair_racing_class_ocr(clean_class if entries is not None else line)
                    if is_racing_height_prefix_line(candidate):
                        if re.search(r'CHAMPION|CERTIFICATE', current_class or '', re.IGNORECASE):
                            i += 1
                            continue
                    if not is_plausible_class_name(candidate):
                        i += 1
                        continue
                    current_class = canonicalize_over_under_championship_class(
                        candidate, current_division,
                    )
                    current_division = maybe_switch_to_nosework_division(
                        current_division, current_class,
                    )
                    current_entries = entries if entries is not None else 0
                    safe_print(f"    Class: {current_class}", flush=True)
                    i += 1
                    continue
        
        # Rejoin height prefix split onto its own line (e.g. '10" up to 12½"' + 'Champion: Dog...')
        placement_line = line
        placement_line_extra_skip = 0
        if (
            current_class
            and current_division
            and _CHAMPIONSHIP_CLASS_RE.search(current_class)
            and is_racing_height_prefix_line(line)
            and i + 1 < len(lines)
        ):
            next_line = lines[i + 1].strip()
            if re.match(r'^(?:Champion|Reserve)\s*:', next_line, re.IGNORECASE):
                placement_line = f"{line.strip()} {next_line}"
                placement_line_extra_skip = 1
        
        # Parse placement line
        # Format: "1st: Dog Name, owned by Owner Name"
        # Format: "Best: Dog Name, owned by Owner Name"
        # Format: "Champion: Dog Name, owned by Owner Name"
        # Format: "Reserve: Dog Name, owned by Owner Name"
        # Format (YOUTH): "1st: Handler Name" (no ", owned by")
        # Format (with size prefix): '10-12½" Champion: Dog Name, owned by Owner Name'
        # Format (MO Earthdogs tab): "1st: Dog<TAB>Owner" or "1<TAB>Dog<TAB>Time<TAB>Owner"
        tab_parsed = parse_tab_placement_line(placement_line)
        if tab_parsed and current_class and current_division:
            placement, dog_name, owner_name, time_val = tab_parsed
            # Remove spaces only for split ordinals ("1 st" -> "1st");
            # preserve spaces in compound word placements ("Reserve Best").
            if re.match(r'^\d', placement):
                placement = placement.replace(' ', '')
            if placement.lower().startswith('3r'):
                placement = '3rd'
            placement = placement.capitalize() if len(placement) <= 3 else placement.title()
            dog_name = re.sub(r'\s+', ' ', dog_name)
            owner_name = clean_parsed_owner_name(re.sub(r'\s+', ' ', owner_name))
            full_division = current_division
            if current_subdivision:
                full_division = f"{current_division} - {current_subdivision}"
            clean_class, _ = strip_entries_from_class_name(current_class)
            results.append(PlacementResult(
                division=full_division,
                class_name=clean_class,
                placement=placement,
                dog_name=dog_name,
                owner_name=owner_name,
                entries=current_entries,
                time=time_val or '',
            ))
            safe_print(f"      {placement}: {dog_name}", flush=True)
            last_parsed_class = current_class
            i += 1 + placement_line_extra_skip
            continue

        parsed_placement = parse_placement_line(placement_line)
        if parsed_placement and current_class and current_division:
            current_division = maybe_switch_to_nosework_division(
                current_division, current_class,
            )
            size_prefix, placement, rest = parsed_placement

            if current_class != last_parsed_class:
                pending_racing_height_prefix = ""

            # Height glued onto prior line's owner field (e.g. Reserve ... Johnson 12 ½-15")
            if size_prefix and size_prefix.strip():
                pending_racing_height_prefix = ""
            elif (
                pending_racing_height_prefix
                and _CHAMPIONSHIP_CLASS_RE.search(current_class)
            ):
                size_prefix = pending_racing_height_prefix
                pending_racing_height_prefix = ""
            
            # If there's a size prefix (e.g., "10-12½""), create a size-specific class name
            # This is common in racing champions where there are separate champions for different height classes
            effective_class = current_class
            if size_prefix and size_prefix.strip():
                size_prefix = normalize_racing_size_prefix(size_prefix.strip(), current_class)
                if _CHAMPIONSHIP_CLASS_RE.search(current_class):
                    effective_class = f"{current_class} ({size_prefix})"
                elif _HEIGHT_ONLY_CLASS_RE.match(current_class.strip()):
                    effective_class = size_prefix
                else:
                    effective_class = f"{current_class} ({size_prefix})"
                # Print the size-specific class header if this is a new size class
                if effective_class != current_class:
                    safe_print(f"    Class: {effective_class}", flush=True)

            clean_class, _ = strip_entries_from_class_name(effective_class)
            effective_class = clean_class
            
            # Normalize OCR errors in placement text.
            # Only strip spaces from split ordinals ("1 st" -> "1st"), not from
            # compound word placements ("Reserve Best" must stay as two words).
            if re.match(r'^\d', placement):
                placement = placement.replace(' ', '')
            if placement.lower().startswith('3r'):
                placement = '3rd'  # Fix "3r~" or "3rd" to "3rd"
            placement = placement.capitalize() if len(placement) <= 3 else placement.title()
            # PDF extracts often use "Reserve Champion"; store as canonical "Reserve"
            if re.match(r'^reserve\s+champion\b', placement, re.IGNORECASE):
                placement = 'Reserve'
            elif re.match(r'^working\s+jrt\s+reserve\s+champion\b', placement, re.IGNORECASE):
                placement = 'Reserve'
            elif re.match(r'^working\s+jrt\s+champion\b', placement, re.IGNORECASE):
                placement = 'Champion'
            elif re.match(r'^champion\b', placement, re.IGNORECASE) and placement.lower() != 'champion':
                placement = 'Champion'
            elif re.match(r'^reserve\s+(?:best|working|choice)\b', placement, re.IGNORECASE):
                placement = 'Reserve'
            elif re.match(r'^best\b', placement, re.IGNORECASE) and placement.lower() != 'best':
                placement = 'Best'
            
            # Fix OCR typos in owner separator before parsing
            rest = normalize_owned_by_text(rest)
            time_val = ''

            def finalize_names(dog: str, owner: str) -> tuple[str, str, str]:
                dog_clean = re.sub(r'\s+', ' ', dog)
                dog_clean = re.sub(r'[\?\ufffd]', '', dog_clean)
                owner_clean = re.sub(r'\s+', ' ', owner)
                dog_clean, dog_time = extract_placement_time_suffix(dog_clean.strip())
                owner_clean, owner_time = extract_placement_time_suffix(
                    clean_parsed_owner_name(owner_clean.strip()),
                )
                return dog_clean, owner_clean, dog_time or owner_time
            
            # Extract dog name and owner
            # YOUTH division or Handler classes: "1st: Handler Name" (no ", owned by")
            if ('YOUTH' in current_division or 'HANDLER' in current_class.upper()) and ', owned by ' not in rest:
                dog_name, owner_name, time_val = finalize_names(rest.strip(), "")
                full_division = current_division
                if current_subdivision:
                    full_division = f"{current_division} - {current_subdivision}"
                results.append(PlacementResult(
                    division=full_division,
                    class_name=effective_class,
                    placement=placement,
                    dog_name=dog_name,
                    owner_name=owner_name,
                    entries=current_entries,
                    time=time_val,
                ))
                safe_print(f"      {placement}: {dog_name}", flush=True)
            elif re.search(r',\s*presented by\s+', rest, re.IGNORECASE):
                dog_name, owner_name = re.split(
                    r',\s*presented by\s+', rest, maxsplit=1, flags=re.IGNORECASE,
                )
                dog_name, owner_name, time_val = finalize_names(dog_name, owner_name)
                full_division = current_division
                if current_subdivision:
                    full_division = f"{current_division} - {current_subdivision}"
                results.append(PlacementResult(
                    division=full_division,
                    class_name=effective_class,
                    placement=placement,
                    dog_name=dog_name,
                    owner_name=owner_name,
                    entries=current_entries,
                    time=time_val,
                ))
                safe_print(f"      {placement}: {dog_name} (Owner: {owner_name})", flush=True)
                last_parsed_class = current_class
            elif ', owned by ' in rest:
                dog_name, owner_name, ocr_time = split_dog_owner_time_from_rest(rest)
                if ocr_time:
                    time_val = ocr_time
                elif dog_name == rest.strip():
                    dog_name, owner_name = rest.split(', owned by ', 1)
                if _CHAMPIONSHIP_CLASS_RE.search(current_class):
                    owner_name, trailing_height = extract_trailing_racing_height_suffix(owner_name)
                    if trailing_height:
                        pending_racing_height_prefix = normalize_racing_size_prefix(
                            trailing_height, current_class,
                        )
                dog_name, owner_name, parsed_time = finalize_names(dog_name, owner_name)
                if parsed_time and not time_val:
                    time_val = parsed_time
                full_division = current_division
                if current_subdivision:
                    full_division = f"{current_division} - {current_subdivision}"
                results.append(PlacementResult(
                    division=full_division,
                    class_name=effective_class,
                    placement=placement,
                    dog_name=dog_name,
                    owner_name=owner_name,
                    entries=current_entries,
                    time=time_val,
                ))
                safe_print(f"      {placement}: {dog_name} (Owner: {owner_name})", flush=True)
                last_parsed_class = current_class
            elif rest.strip():
                # Handle "Dog Name (Owner)" format used in some PDF-extracted files
                # (e.g. 2013 MO Earthdogs PDF: "River Bottom Sorce 'o Trouble (Cagle)")
                # The owner is the LAST parenthesized group at the end of the field.
                # Double open-parens typos like "((Halfar)" are also handled.
                _rest_stripped = rest.strip()
                _paren_match = re.match(
                    r'^(.+?)\s*\(+([^)]+)\)+\s*$',
                    _rest_stripped,
                )
                _owner_in_parens = (
                    _paren_match is not None
                    and len(_paren_match.group(2)) <= 60
                    and not _paren_match.group(2).strip().lower().startswith('owned by')
                    # Must contain at least one letter (exclude pure-numeric times/codes)
                    and re.search(r'[A-Za-z]', _paren_match.group(2))
                    # Must look like a name (not a breed abbreviation like "PRT" or "JRTA")
                    # and have at least 2 chars
                    and len(_paren_match.group(2).strip()) >= 2
                )
                if _owner_in_parens:
                    dog_name = _paren_match.group(1).strip()
                    owner_name = _paren_match.group(2).strip()
                    # If dog_name itself ends with a paren group (e.g. nickname "(Cora)"),
                    # that is fine – keep it as part of the dog name.
                else:
                    dog_name = _rest_stripped
                    owner_name = ""
                dog_name, owner_name, time_val = finalize_names(dog_name, owner_name)
                full_division = current_division
                if current_subdivision:
                    full_division = f"{current_division} - {current_subdivision}"
                results.append(PlacementResult(
                    division=full_division,
                    class_name=effective_class,
                    placement=placement,
                    dog_name=dog_name,
                    owner_name=owner_name,
                    entries=current_entries,
                    time=time_val,
                ))
                if owner_name:
                    safe_print(f"      {placement}: {dog_name} (Owner: {owner_name})", flush=True)
                else:
                    safe_print(f"      {placement}: {dog_name}", flush=True)
                last_parsed_class = current_class
            
            i += 1 + placement_line_extra_skip
            continue
        
        i += 1
    
    return results

def normalize_date(date_str: str, year: int) -> str:
    """Convert date string to SQL Server format (YYYY-MM-DD)."""
    if not date_str:
        return f"{year}-01-01"
    
    # Try common formats
    formats = [
        '%B %d, %Y',  # October 10, 2025
        '%b %d, %Y',  # Oct 10, 2025
        '%m/%d/%Y',
        '%m/%d/%y',
        '%Y-%m-%d'
    ]
    
    for fmt in formats:
        try:
            dt = datetime.strptime(date_str, fmt)
            return dt.strftime('%Y-%m-%d')
        except ValueError:
            continue
    
    # If parsing fails, return default
    return f"{year}-01-01"


def parse_trialvault_date_range(date_str: str, year: int) -> tuple[str, str]:
    """Parse Trial Vault date metadata into SQL start/end dates."""
    if not date_str:
        default = f"{year}-01-01"
        return default, default

    cleaned = re.sub(r"^(?:Friday|Saturday|Sunday)\s*\(", "", date_str.strip())
    cleaned = cleaned.rstrip(")").strip()

    range_match = re.search(
        r"(?:\w+\.\s+)?([A-Za-z]+)\s+(\d{1,2})\s*-\s*(?:\w+\.\s+)?([A-Za-z]+)\s+(\d{1,2}),?\s+(\d{4})",
        cleaned,
    )
    if range_match:
        month1, day1, month2, day2, year_str = range_match.groups()
        year_val = int(year_str)
        start = normalize_date(f"{month1} {day1}, {year_str}", year_val)
        end = normalize_date(f"{month2} {day2}, {year_str}", year_val)
        return start, end

    single = normalize_date(cleaned, year)
    return single, single


def load_trialvault_results_to_database(
    results,
    results_url: str,
    source_file_path: str | None = None,
) -> None:
    """Insert Trial Vault scrape results and event times into the database."""
    from collections import defaultdict
    from normalize_trialresults_data import normalize_class_name_full, normalize_dog_name

    if not results:
        print("  No results to load.")
        return

    conn = get_connection()
    cursor = conn.cursor()
    source_path = source_file_path or results_url

    try:
        by_trial = defaultdict(list)
        for result in results:
            by_trial[result.trial_name].append(result)

        for trial_name, trial_results in by_trial.items():
            year = int(trial_results[0].year)
            start_date, end_date = parse_trialvault_date_range(trial_results[0].date or "", year)

            cursor.execute(
                "SELECT TrialListID, TrialName FROM [sResults].[TrialList] WHERE Year = ?",
                str(year),
            )
            current_key = canonical_trial_match_key(trial_name, year)
            duplicate_id = None
            duplicate_name = None
            for existing_id, existing_name in cursor.fetchall():
                if (
                    existing_name == trial_name
                    or trial_name_key(existing_name) == trial_name_key(trial_name)
                    or canonical_trial_match_key(existing_name, year) == current_key
                ):
                    duplicate_id = existing_id
                    duplicate_name = existing_name
                    break

            if duplicate_id:
                print(
                    f"  Trial already exists in database "
                    f"(ID: {duplicate_id}, name: {duplicate_name}), skipping '{trial_name}'...",
                    flush=True,
                )
                continue

            next_trial_id, next_trialclass_id, next_placement_id = get_next_ids_from_db(conn)
            next_times_id = get_next_placement_times_id(conn)
            trial_id = next_trial_id

            cursor.execute(
                """
                INSERT INTO [sResults].[TrialList] (
                    TrialListID, TrialName, Year, StartDate, EndDate, TrialResultFilePath
                )
                VALUES (?, ?, ?, ?, ?, ?)
                """,
                trial_id,
                trial_name,
                str(year),
                start_date,
                end_date,
                source_path,
            )
            print(f"  Inserted trial '{trial_name}' (ID: {trial_id})", flush=True)

            by_class = defaultdict(list)
            for result in trial_results:
                key = (result.division, result.class_name, result.entry_count)
                by_class[key].append(result)

            times_inserted = 0
            for (division, class_name, entry_count), class_results in by_class.items():
                division_name = division or "UNKNOWN"
                div_id = get_or_create_division(cursor, division_name)
                if not div_id:
                    continue

                clean_class_name, _ = strip_entries_from_class_name(class_name or "Unknown Class")
                clean_class_name = normalize_class_name_full(clean_class_name, division_name)
                class_id = get_or_create_class(cursor, clean_class_name, div_id)
                if not class_id:
                    continue

                trialclass_id = next_trialclass_id
                next_trialclass_id += 1
                cursor.execute(
                    """
                    INSERT INTO [sResults].[TrialClass] (TrialClassID, TrialListID, ClassID, EntryCount)
                    VALUES (?, ?, ?, ?)
                    """,
                    trialclass_id,
                    trial_id,
                    class_id,
                    entry_count,
                )

                for result in class_results:
                    owner_id = get_or_create_owner(cursor, result.owner)
                    dog_id = get_or_create_dog(cursor, result.dog_name, owner_id)

                    placement_id = next_placement_id
                    next_placement_id += 1
                    cursor.execute(
                        """
                        INSERT INTO [sResults].[TrialPlacements] (
                            TrialPlacementsID, TrialListID, TrialClassID, DogID, Result
                        )
                        VALUES (?, ?, ?, ?, ?)
                        """,
                        placement_id,
                        trial_id,
                        trialclass_id,
                        dog_id,
                        result.placement,
                    )

                    if result.time:
                        cursor.execute(
                            """
                            INSERT INTO [sResults].[TrialPlacements_Times] (
                                TrialPlacements_TimesID, TrialPlacementsID, Time
                            )
                            VALUES (?, ?, ?)
                            """,
                            next_times_id,
                            placement_id,
                            result.time,
                        )
                        next_times_id += 1
                        times_inserted += 1

            print(
                f"  Loaded {len(trial_results)} placements for '{trial_name}' "
                f"({times_inserted} with times)",
                flush=True,
            )

        conn.commit()
        print("  Trial Vault database load complete.", flush=True)
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()


def normalize_trialvault_placement_result(placement: str) -> str:
    """Normalize Trial Vault rank text to match stored TrialPlacements.Result values."""
    if not placement:
        return ""
    text = re.sub(r"\s+", " ", placement.strip())
    if re.fullmatch(r"\d+", text):
        n = int(text)
        if 11 <= n % 100 <= 13:
            suffix = "th"
        else:
            suffix = {1: "st", 2: "nd", 3: "rd"}.get(n % 10, "th")
        return f"{n}{suffix}"
    return text


def normalize_event_base_name(name: str) -> str:
    """Strip year, day suffixes, and roman numerals to get the shared event name."""
    text = (name or "").strip()
    text = re.sub(r"\s+-\s+(Friday|Saturday|Sunday)\s*$", "", text, flags=re.I)
    text = re.sub(r"^\d{4}\s+", "", text)
    text = re.sub(r"\b(19\d{2}|20\d{2})\b", "", text)
    text = re.sub(r"\s+I\s*&\s*II\s*$", "", text, flags=re.I)
    text = re.sub(r"\s+I\s+and\s+II\s*$", "", text, flags=re.I)
    text = re.sub(
        r"\b(?:jack\s+russell\s+terrier\s+club|jrtc)\s+",
        "",
        text,
        flags=re.I,
    )
    text = re.sub(r"\s+(I{1,3}|IV|VI{0,3}|IX|X{1,3})\s*$", "", text, flags=re.I)
    return re.sub(r"\s+", " ", text).strip()


def event_base_key(name: str) -> str:
    return trial_name_key(normalize_event_base_name(name))


def extract_trial_day_name(name: str) -> str | None:
    match = re.search(r"\s+-\s+(Friday|Saturday|Sunday)\s*$", name or "", flags=re.I)
    return match.group(1).lower() if match else None


_ROMAN_NUMERAL_RE = re.compile(r"\b(I{1,3}|IV|VI{0,3}|IX|X{1,3})\s*$", re.I)


def extract_trial_roman_numeral(name: str) -> str | None:
    match = _ROMAN_NUMERAL_RE.search((name or "").strip())
    return match.group(1).upper() if match else None


_TRIALVAULT_DAY_TO_ROMAN = {
    "friday": "I",
    "saturday": "I",
    "sunday": "II",
}


def trialvault_day_to_roman(day: str | None) -> str | None:
    if not day:
        return None
    return _TRIALVAULT_DAY_TO_ROMAN.get(day.lower())


def trialvault_parts_match(
    tv_day: str | None,
    db_trial_name: str,
) -> bool:
    """True when a Trial Vault day maps to a DB trial's day suffix or roman numeral."""
    if not tv_day:
        return False
    tv_day = tv_day.lower()
    db_day = extract_trial_day_name(db_trial_name)
    if db_day:
        return tv_day == db_day
    db_roman = extract_trial_roman_numeral(db_trial_name)
    if db_roman:
        return trialvault_day_to_roman(tv_day) == db_roman
    return False


def trialvault_db_name_candidates(trial_name: str, year: int | str | None) -> list[str]:
    """Generate likely database trial names for a Trial Vault event/day label."""
    name = (trial_name or "").strip()
    if not name:
        return []

    candidates = [name]
    day = extract_trial_day_name(name)
    day_stripped = re.sub(r"\s+-\s+(Friday|Saturday|Sunday)\s*$", "", name, flags=re.I).strip()
    if day_stripped and day_stripped != name:
        candidates.append(day_stripped)
    base = normalize_event_base_name(name)
    year_str = str(year).strip() if year is not None else None

    if base and base != name:
        candidates.append(base)
    if base and year_str:
        candidates.extend([f"{base} {year_str}", f"{year_str} {base}"])

    roman = trialvault_day_to_roman(day)
    if not roman:
        roman = extract_trial_roman_numeral(name)
    if base and roman:
        candidates.append(f"{base} {roman}")

    deduped: list[str] = []
    seen: set[str] = set()
    for candidate in candidates:
        if candidate and candidate not in seen:
            seen.add(candidate)
            deduped.append(candidate)
    return deduped


def _trial_name_lookup_keys(trial_name: str, year: int | str | None) -> list[tuple[str, str | int | None]]:
    """Build lookup keys for resolving a scraped trial name to TrialList rows."""
    year_str = str(year).strip() if year is not None else None
    year_int = int(year_str) if year_str and year_str.isdigit() else None
    keys: list[tuple[str, str | int | None]] = []

    def add(key_name: str, key_year: str | int | None) -> None:
        pair = (key_name, key_year)
        if pair not in keys:
            keys.append(pair)

    for candidate in trialvault_db_name_candidates(trial_name, year):
        add(candidate, year_str)
        if year_int is not None:
            add(candidate, year_int)

    return keys


def build_trial_list_lookup(cursor) -> tuple[
    dict[tuple[str, str | int | None], int],
    dict[str, list[tuple[int, str, str]]],
    dict[tuple[str, int], list[tuple[int, str]]],
    dict[int, int],
]:
    """Map trial names, canonical keys, and base+year keys to TrialListID."""
    cursor.execute(
        "SELECT TrialListID, TrialName, Year FROM [sResults].[TrialList]"
    )
    lookup: dict[tuple[str, str | int | None], int] = {}
    canonical: dict[str, list[tuple[int, str, str]]] = defaultdict(list)
    by_base_year: dict[tuple[str, int], list[tuple[int, str]]] = defaultdict(list)
    trial_years: dict[int, int] = {}

    for trial_id, trial_name, year in cursor.fetchall():
        year_str = str(year).strip() if year is not None else None
        year_int = int(year_str) if year_str and year_str.isdigit() else None
        name = (trial_name or "").strip()
        if year_int is not None:
            trial_years[trial_id] = year_int
            lookup[(name, year_str)] = trial_id
            lookup[(name, year_int)] = trial_id
            canonical[canonical_trial_match_key(name, year_int)].append(
                (trial_id, name, year_str or "")
            )
            by_base_year[(event_base_key(name), year_int)].append((trial_id, name))

    return lookup, dict(canonical), dict(by_base_year), trial_years


def resolve_trial_list_id(
    trial_name: str,
    year: str | int | None,
    trial_lookup: dict[tuple[str, str | int | None], int],
    canonical_lookup: dict[str, list[tuple[int, str, str]]] | None = None,
    base_year_lookup: dict[tuple[str, int], list[tuple[int, str]]] | None = None,
    trial_years: dict[int, int] | None = None,
) -> int | None:
    """Resolve a Trial Vault trial name/year to an existing TrialListID."""
    year_int = int(year) if year is not None and str(year).isdigit() else None

    def year_ok(trial_id: int | None) -> bool:
        if trial_id is None or year_int is None or not trial_years:
            return trial_id is not None
        return trial_years.get(trial_id) == year_int

    for key_name, key_year in _trial_name_lookup_keys(trial_name, year):
        trial_id = trial_lookup.get((key_name, key_year))
        if year_ok(trial_id):
            return trial_id
        if key_year is not None:
            trial_id = trial_lookup.get((key_name, str(key_year)))
            if year_ok(trial_id):
                return trial_id

    if year_int is not None and base_year_lookup is not None:
        tv_day = extract_trial_day_name(trial_name)
        base_key = event_base_key(trial_name)
        for trial_id, existing_name in base_year_lookup.get((base_key, year_int), []):
            if trialvault_parts_match(tv_day, existing_name) and year_ok(trial_id):
                return trial_id
            if tv_day and year_ok(trial_id):
                existing_day = extract_trial_day_name(existing_name)
                existing_roman = extract_trial_roman_numeral(existing_name)
                if not existing_day and not existing_roman:
                    tv_stripped = re.sub(
                        r"\s+-\s+(Friday|Saturday|Sunday)\s*$",
                        "",
                        trial_name,
                        flags=re.I,
                    ).strip()
                    if trial_name_key(tv_stripped) == trial_name_key(existing_name):
                        return trial_id

    if year_int is not None and canonical_lookup is not None:
        current_key = canonical_trial_match_key(trial_name, year_int)
        for trial_id, existing_name, _existing_year in canonical_lookup.get(current_key, []):
            if (
                existing_name == trial_name
                or trial_name_key(existing_name) == trial_name_key(trial_name)
            ) and year_ok(trial_id):
                return trial_id
    return None


def _owner_name_key(owner_name: str | None) -> str:
    if not owner_name:
        return ""
    return re.sub(r"[^a-z0-9]", "", owner_name.lower())


def class_match_key_for_trialvault(class_name: str, division_name: str | None) -> str:
    """Canonical class key for matching Trial Vault times to existing placements."""
    from normalize_trialresults_data import normalize_class_name_full, normalize_division_name_full

    division = normalize_division_name_full(division_name or "")
    normalized = normalize_class_name_full(class_name or "", division)
    if not normalized:
        return ""

    key = normalized.lower()
    key = re.sub(r"\s+go-to-ground\s*$", "", key)
    key = re.sub(r"\s+gtg\s*$", "", key)
    key = re.sub(r"\s+super earth\s*$", "", key)
    key = re.sub(r"\s+", " ", key).strip()

    if "championship certificate" not in key:
        return key

    height = ""
    for pattern in (
        r'10"\s*up\s*to\s*12½"',
        r'10\s*up\s*to\s*12½"',
        r'over\s*12½"\s*up\s*to\s*15"',
        r'12½"\s*up\s*to\s*15"',
        r'up\s*to\s*12½"',
    ):
        match = re.search(pattern, key)
        if match:
            height = re.sub(r"\s+", " ", match.group(0)).strip()
            break

    category = ""
    for cat in ("adult", "senior", "veteran"):
        if re.search(rf"\b{cat}\b", key):
            category = cat
            break

    if height:
        if category:
            return f"{height}|{category}|championship certificate"
        return f"{height}|championship certificate"
    return key


def _load_trial_placement_rows(cursor, trial_id: int) -> list[dict]:
    cursor.execute(
        """
        SELECT
            p.TrialPlacementsID,
            dv.DivisionName,
            c.ClassName,
            d.DogID,
            d.DogName,
            o.OwnerName,
            p.Result,
            pt.TrialPlacements_TimesID
        FROM [sResults].[TrialPlacements] p
        JOIN [sResults].[TrialClass] tc ON tc.TrialClassID = p.TrialClassID
        JOIN [sResults].[Class] c ON c.ClassID = tc.ClassID
        JOIN [sResults].[Division] dv ON dv.DivisionID = c.DivisionID
        JOIN [sResults].[Dog] d ON d.DogID = p.DogID
        LEFT JOIN [sResults].[Owner] o ON o.OwnerID = d.OwnerID
        LEFT JOIN [sResults].[TrialPlacements_Times] pt
            ON pt.TrialPlacementsID = p.TrialPlacementsID
        WHERE p.TrialListID = ?
        """,
        trial_id,
    )
    rows = []
    for (
        placement_id,
        division_name,
        class_name,
        dog_id,
        dog_name,
        owner_name,
        result,
        times_id,
    ) in cursor.fetchall():
        rows.append(
            {
                "placement_id": placement_id,
                "division_name": division_name,
                "class_name": class_name,
                "dog_id": dog_id,
                "dog_name": dog_name,
                "owner_name": owner_name,
                "result": result,
                "has_time": times_id is not None,
            }
        )
    return rows


def find_trialvault_placement_id(
    cursor,
    result,
    trial_lookup: dict[tuple[str, str | int | None], int],
    canonical_lookup: dict[str, list[tuple[int, str, str]]],
    base_year_lookup: dict[tuple[str, int], list[tuple[int, str]]],
    placement_cache: dict[int, list[dict]],
    trial_years: dict[int, int] | None = None,
) -> int | None:
    """Match a Trial Vault result with a time to an existing TrialPlacements row."""
    from normalize_trialresults_data import (
        normalize_class_name_full,
        normalize_division_name_full,
        normalize_dog_name,
    )
    from parse_catalog import names_are_similar

    if not result.time:
        return None

    trial_id = resolve_trial_list_id(
        result.trial_name,
        result.year,
        trial_lookup,
        canonical_lookup,
        base_year_lookup,
        trial_years,
    )
    if not trial_id:
        return None

    if trial_id not in placement_cache:
        placement_cache[trial_id] = _load_trial_placement_rows(cursor, trial_id)

    division_key = normalize_division_name_full(result.division or "")
    class_key = class_match_key_for_trialvault(result.class_name or "", division_key)
    result_key = normalize_trialvault_placement_result(result.placement or "")
    tv_dog = normalize_dog_name(result.dog_name) or (result.dog_name or "").strip()
    owner_key = _owner_name_key(result.owner)

    candidates = []
    for row in placement_cache[trial_id]:
        row_division = normalize_division_name_full(row["division_name"] or "")
        row_class = class_match_key_for_trialvault(row["class_name"] or "", row_division)
        row_result = normalize_trialvault_placement_result(row["result"] or "")
        if row_division != division_key or row_class != class_key or row_result != result_key:
            continue
        row_dog = normalize_dog_name(row["dog_name"]) or (row["dog_name"] or "").strip()
        if tv_dog and row_dog and (tv_dog == row_dog or names_are_similar(tv_dog, row_dog)):
            score = 2
            row_owner_key = _owner_name_key(row["owner_name"])
            if owner_key and row_owner_key:
                if owner_key == row_owner_key:
                    score = 4
                elif owner_key in row_owner_key or row_owner_key in owner_key:
                    score = 3
            candidates.append((score, row["placement_id"], row["has_time"]))

    if not candidates:
        return None
    candidates.sort(key=lambda item: (-item[0], item[1]))
    return candidates[0][1]


def append_trialvault_times_to_database(results, source_label: str = "") -> dict[str, int]:
    """Append Trial Vault event times to existing trial placements only."""
    if not results:
        return {"matched": 0, "inserted": 0, "skipped_no_time": 0, "skipped_has_time": 0, "unmatched": 0}

    conn = get_connection()
    cursor = conn.cursor()
    stats = {
        "matched": 0,
        "inserted": 0,
        "skipped_no_time": 0,
        "skipped_has_time": 0,
        "unmatched": 0,
    }

    try:
        trial_lookup, canonical_lookup, base_year_lookup, trial_years = build_trial_list_lookup(cursor)
        placement_cache: dict[int, list[dict]] = {}
        next_times_id = get_next_placement_times_id(conn)

        for result in results:
            if not result.time:
                stats["skipped_no_time"] += 1
                continue

            placement_id = find_trialvault_placement_id(
                cursor,
                result,
                trial_lookup,
                canonical_lookup,
                base_year_lookup,
                placement_cache,
                trial_years,
            )
            if not placement_id:
                stats["unmatched"] += 1
                continue

            stats["matched"] += 1
            cursor.execute(
                """
                SELECT 1
                FROM [sResults].[TrialPlacements_Times]
                WHERE TrialPlacementsID = ?
                """,
                placement_id,
            )
            if cursor.fetchone():
                stats["skipped_has_time"] += 1
                continue

            cursor.execute(
                """
                INSERT INTO [sResults].[TrialPlacements_Times] (
                    TrialPlacements_TimesID, TrialPlacementsID, Time
                )
                VALUES (?, ?, ?)
                """,
                next_times_id,
                placement_id,
                result.time,
            )
            next_times_id += 1
            stats["inserted"] += 1

            trial_id = resolve_trial_list_id(
                result.trial_name,
                result.year,
                trial_lookup,
                canonical_lookup,
                base_year_lookup,
                trial_years,
            )
            if trial_id and trial_id in placement_cache:
                for row in placement_cache[trial_id]:
                    if row["placement_id"] == placement_id:
                        row["has_time"] = True
                        break

        conn.commit()
        label = f" ({source_label})" if source_label else ""
        print(
            f"  Times append{label}: inserted {stats['inserted']:,}, "
            f"matched {stats['matched']:,}, already had time {stats['skipped_has_time']:,}, "
            f"unmatched {stats['unmatched']:,}, no time in source {stats['skipped_no_time']:,}",
            flush=True,
        )
        return stats
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()


def is_nonsanctioned_trialvault_result(result) -> bool:
    """True when a Trial Vault result belongs to a non-sanctioned class or division."""
    if getattr(result, "nonsanctioned_event", False):
        return True
    parts = [result.division, result.section, result.class_name]
    return any(part and "non-sanctioned" in part.lower() for part in parts)


_MISASSIGNED_LURE_CLASS_MARKERS = (
    "ball retrieval",
    "rumble tunnel",
    "rat dash",
    "tunnelers",
    "brush hunt",
    "jack in the shack",
    "thunder tunnel",
    "doggie fun zone",
    "barn-hunt",
    "barn hunt",
)


def _trialvault_class_misassigned_to_lure_coursing(class_name: str) -> bool:
    class_lower = (class_name or "").lower()
    if "lure coursing" in class_lower:
        return False
    return any(marker in class_lower for marker in _MISASSIGNED_LURE_CLASS_MARKERS)


def repair_super_earth_division_assignments(
    trial_ids: list[int] | None = None,
) -> dict[str, int]:
    """Move Super Earth classes out of GO-TO-GROUND into SUPER EARTH."""
    from normalize_trialresults_data import normalize_class_name_full

    stats = {"trials": 0, "classes": 0, "placements": 0}
    conn = get_connection()
    cursor = conn.cursor()
    try:
        query = """
            SELECT tc.TrialClassID, tc.TrialListID, c.ClassName, d.DivisionName
            FROM [sResults].[TrialClass] tc
            JOIN [sResults].[Class] c ON tc.ClassID = c.ClassID
            JOIN [sResults].[Division] d ON c.DivisionID = d.DivisionID
            WHERE d.DivisionName IN ('GO-TO-GROUND', 'SUPER EARTH GO-TO-GROUND')
              AND c.ClassName LIKE '%Super Earth%'
        """
        params: list = []
        if trial_ids:
            placeholders = ",".join("?" for _ in trial_ids)
            query += f" AND tc.TrialListID IN ({placeholders})"
            params.extend(trial_ids)

        cursor.execute(query, params)
        rows = cursor.fetchall()
        touched_trials: set[int] = set()
        for trialclass_id, trial_id, class_name, _division_name in rows:
            super_earth_div_id = get_or_create_division(cursor, "SUPER EARTH")
            if not super_earth_div_id:
                continue
            clean_class_name, _ = strip_entries_from_class_name(class_name or "")
            clean_class_name = normalize_class_name_full(clean_class_name, "SUPER EARTH")
            super_earth_class_id = get_or_create_class(cursor, clean_class_name, super_earth_div_id)
            if not super_earth_class_id:
                continue
            cursor.execute(
                "UPDATE [sResults].[TrialClass] SET ClassID = ? WHERE TrialClassID = ?",
                super_earth_class_id,
                trialclass_id,
            )
            cursor.execute(
                "SELECT COUNT(*) FROM [sResults].[TrialPlacements] WHERE TrialClassID = ?",
                trialclass_id,
            )
            stats["placements"] += cursor.fetchone()[0]
            stats["classes"] += 1
            touched_trials.add(trial_id)

        stats["trials"] = len(touched_trials)
        conn.commit()
        print(
            f"  Super Earth repair: trials {stats['trials']:,}, "
            f"classes {stats['classes']:,}, placements {stats['placements']:,}",
            flush=True,
        )
        return stats
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()


def fix_dog_owner_transfer_after_year(
    from_dog_id: int,
    to_dog_id: int,
    year_cutoff: int,
    canonical_dog_name: str | None = None,
) -> dict[str, int]:
    """Move placements/catalog rows after a year from one dog record to another."""
    stats = {
        "placements_moved": 0,
        "placements_deleted": 0,
        "catalog_updated": 0,
        "duplicates_removed": 0,
    }
    conn = get_connection()
    cursor = conn.cursor()
    try:
        if canonical_dog_name:
            cursor.execute(
                "UPDATE [sResults].[Dog] SET DogName = ? WHERE DogID = ?",
                canonical_dog_name,
                to_dog_id,
            )

        cursor.execute(
            """
            SELECT p.TrialPlacementsID, p.TrialListID, p.TrialClassID, p.Result, tl.Year
            FROM [sResults].[TrialPlacements] p
            JOIN [sResults].[TrialList] tl ON p.TrialListID = tl.TrialListID
            WHERE p.DogID = ?
              AND TRY_CAST(tl.Year AS INT) > ?
            ORDER BY p.TrialPlacementsID
            """,
            from_dog_id,
            year_cutoff,
        )
        for placement_id, trial_id, trialclass_id, result_text, _year in cursor.fetchall():
            cursor.execute(
                """
                SELECT TrialPlacementsID
                FROM [sResults].[TrialPlacements]
                WHERE DogID = ?
                  AND TrialListID = ?
                  AND TrialClassID = ?
                  AND Result = ?
                """,
                to_dog_id,
                trial_id,
                trialclass_id,
                result_text,
            )
            existing = cursor.fetchone()
            if existing:
                cursor.execute(
                    """
                    DELETE t
                    FROM [sResults].[TrialPlacements_Times] t
                    WHERE t.TrialPlacementsID = ?
                    """,
                    placement_id,
                )
                cursor.execute(
                    "DELETE FROM [sResults].[TrialPlacements] WHERE TrialPlacementsID = ?",
                    placement_id,
                )
                stats["placements_deleted"] += 1
            else:
                cursor.execute(
                    """
                    UPDATE [sResults].[TrialPlacements]
                    SET DogID = ?
                    WHERE TrialPlacementsID = ?
                    """,
                    to_dog_id,
                    placement_id,
                )
                stats["placements_moved"] += 1

        cursor.execute(
            """
            UPDATE ce
            SET ce.DogID = ?
            FROM [sResults].[CatalogEntry] ce
            WHERE ce.DogID = ?
              AND TRY_CAST(ce.Year AS INT) > ?
            """,
            to_dog_id,
            from_dog_id,
            year_cutoff,
        )
        stats["catalog_updated"] = cursor.rowcount

        cursor.execute(
            """
            SELECT p.TrialPlacementsID, p.TrialListID, p.TrialClassID, p.Result
            FROM [sResults].[TrialPlacements] p
            WHERE p.DogID = ?
            ORDER BY p.TrialListID, p.TrialClassID, p.Result, p.TrialPlacementsID
            """,
            to_dog_id,
        )
        seen: set[tuple] = set()
        for placement_id, trial_id, trialclass_id, result_text in cursor.fetchall():
            key = (trial_id, trialclass_id, result_text)
            if key in seen:
                cursor.execute(
                    """
                    DELETE t
                    FROM [sResults].[TrialPlacements_Times] t
                    WHERE t.TrialPlacementsID = ?
                    """,
                    placement_id,
                )
                cursor.execute(
                    "DELETE FROM [sResults].[TrialPlacements] WHERE TrialPlacementsID = ?",
                    placement_id,
                )
                stats["duplicates_removed"] += 1
            else:
                seen.add(key)

        conn.commit()
        print(
            f"  Dog owner transfer (> {year_cutoff}): moved {stats['placements_moved']:,}, "
            f"deleted dupes {stats['placements_deleted']:,}, "
            f"catalog {stats['catalog_updated']:,}, "
            f"deduped {stats['duplicates_removed']:,}",
            flush=True,
        )
        return stats
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()


def dedupe_duplicate_trial_classes(trial_ids: list[int]) -> dict[str, int]:
    """Merge duplicate TrialClass rows (same trial + class name) and remove duplicate placements."""
    stats = {
        "class_groups": 0,
        "classes_removed": 0,
        "placements_moved": 0,
        "placements_deleted": 0,
        "intra_class_deleted": 0,
    }
    if not trial_ids:
        return stats

    conn = get_connection()
    cursor = conn.cursor()
    try:
        placeholders = ",".join("?" for _ in trial_ids)
        cursor.execute(
            f"""
            SELECT tc.TrialListID, c.ClassName, tc.TrialClassID
            FROM [sResults].[TrialClass] tc
            JOIN [sResults].[Class] c ON tc.ClassID = c.ClassID
            WHERE tc.TrialListID IN ({placeholders})
            ORDER BY tc.TrialListID, c.ClassName, tc.TrialClassID
            """,
            trial_ids,
        )
        groups: dict[tuple[int, str], list[int]] = defaultdict(list)
        for trial_id, class_name, trialclass_id in cursor.fetchall():
            groups[(trial_id, class_name or "")].append(trialclass_id)

        for (_trial_id, _class_name), trialclass_ids in groups.items():
            if len(trialclass_ids) < 2:
                continue
            stats["class_groups"] += 1
            canonical_id = trialclass_ids[0]
            for duplicate_id in trialclass_ids[1:]:
                cursor.execute(
                    """
                    SELECT p.TrialPlacementsID, p.DogID, p.Result
                    FROM [sResults].[TrialPlacements] p
                    WHERE p.TrialClassID = ?
                    """,
                    duplicate_id,
                )
                for placement_id, dog_id, result_text in cursor.fetchall():
                    cursor.execute(
                        """
                        SELECT 1
                        FROM [sResults].[TrialPlacements]
                        WHERE TrialClassID = ? AND DogID = ? AND Result = ?
                        """,
                        canonical_id,
                        dog_id,
                        result_text,
                    )
                    if cursor.fetchone():
                        cursor.execute(
                            """
                            DELETE t
                            FROM [sResults].[TrialPlacements_Times] t
                            WHERE t.TrialPlacementsID = ?
                            """,
                            placement_id,
                        )
                        cursor.execute(
                            "DELETE FROM [sResults].[TrialPlacements] WHERE TrialPlacementsID = ?",
                            placement_id,
                        )
                        stats["placements_deleted"] += 1
                    else:
                        cursor.execute(
                            """
                            UPDATE [sResults].[TrialPlacements]
                            SET TrialClassID = ?
                            WHERE TrialPlacementsID = ?
                            """,
                            canonical_id,
                            placement_id,
                        )
                        stats["placements_moved"] += 1
                cursor.execute(
                    "DELETE FROM [sResults].[TrialClass] WHERE TrialClassID = ?",
                    duplicate_id,
                )
                stats["classes_removed"] += 1

        cursor.execute(
            f"""
            SELECT p.TrialPlacementsID, p.TrialClassID, p.DogID, p.Result
            FROM [sResults].[TrialPlacements] p
            JOIN [sResults].[TrialClass] tc ON p.TrialClassID = tc.TrialClassID
            WHERE tc.TrialListID IN ({placeholders})
            ORDER BY p.TrialClassID, p.DogID, p.Result, p.TrialPlacementsID
            """,
            trial_ids,
        )
        seen: set[tuple[int, int, str]] = set()
        for placement_id, trialclass_id, dog_id, result_text in cursor.fetchall():
            key = (trialclass_id, dog_id, result_text or "")
            if key in seen:
                cursor.execute(
                    """
                    DELETE t
                    FROM [sResults].[TrialPlacements_Times] t
                    WHERE t.TrialPlacementsID = ?
                    """,
                    placement_id,
                )
                cursor.execute(
                    "DELETE FROM [sResults].[TrialPlacements] WHERE TrialPlacementsID = ?",
                    placement_id,
                )
                stats["intra_class_deleted"] += 1
            else:
                seen.add(key)

        conn.commit()
        print(
            f"  Trial class dedupe: groups {stats['class_groups']:,}, "
            f"removed classes {stats['classes_removed']:,}, "
            f"moved {stats['placements_moved']:,}, deleted {stats['placements_deleted']:,}, "
            f"intra-class {stats['intra_class_deleted']:,}",
            flush=True,
        )
        return stats
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()


def repair_barn_hunt_division_assignments(
    trial_ids: list[int] | None = None,
) -> dict[str, int]:
    """Move Barn Hunt classes out of GO-TO-GROUND into BARN HUNT, merging duplicates."""
    from normalize_trialresults_data import normalize_class_name_full

    stats = {
        "trials": 0,
        "classes": 0,
        "placements_moved": 0,
        "placements_deleted": 0,
        "classes_removed": 0,
    }
    conn = get_connection()
    cursor = conn.cursor()
    try:
        query = """
            SELECT tc.TrialClassID, tc.TrialListID, c.ClassName
            FROM [sResults].[TrialClass] tc
            JOIN [sResults].[Class] c ON tc.ClassID = c.ClassID
            JOIN [sResults].[Division] d ON c.DivisionID = d.DivisionID
            WHERE d.DivisionName = 'GO-TO-GROUND'
              AND c.ClassName LIKE '%Barn Hunt%'
        """
        params: list = []
        if trial_ids:
            placeholders = ",".join("?" for _ in trial_ids)
            query += f" AND tc.TrialListID IN ({placeholders})"
            params.extend(trial_ids)

        cursor.execute(query, params)
        wrong_rows = cursor.fetchall()
        touched_trials: set[int] = set()

        for wrong_trialclass_id, trial_id, class_name in wrong_rows:
            touched_trials.add(trial_id)
            stats["classes"] += 1

            cursor.execute(
                """
                SELECT tc.TrialClassID
                FROM [sResults].[TrialClass] tc
                JOIN [sResults].[Class] c ON tc.ClassID = c.ClassID
                JOIN [sResults].[Division] d ON c.DivisionID = d.DivisionID
                WHERE tc.TrialListID = ?
                  AND d.DivisionName = 'BARN HUNT'
                  AND c.ClassName = ?
                """,
                trial_id,
                class_name,
            )
            correct_row = cursor.fetchone()
            if correct_row:
                correct_trialclass_id = correct_row[0]
                cursor.execute(
                    """
                    SELECT p.TrialPlacementsID, p.DogID, p.Result
                    FROM [sResults].[TrialPlacements] p
                    WHERE p.TrialClassID = ?
                    """,
                    wrong_trialclass_id,
                )
                for placement_id, dog_id, result_text in cursor.fetchall():
                    cursor.execute(
                        """
                        SELECT 1
                        FROM [sResults].[TrialPlacements]
                        WHERE TrialClassID = ? AND DogID = ? AND Result = ?
                        """,
                        correct_trialclass_id,
                        dog_id,
                        result_text,
                    )
                    if cursor.fetchone():
                        cursor.execute(
                            """
                            DELETE t
                            FROM [sResults].[TrialPlacements_Times] t
                            WHERE t.TrialPlacementsID = ?
                            """,
                            placement_id,
                        )
                        cursor.execute(
                            "DELETE FROM [sResults].[TrialPlacements] WHERE TrialPlacementsID = ?",
                            placement_id,
                        )
                        stats["placements_deleted"] += 1
                    else:
                        cursor.execute(
                            """
                            UPDATE [sResults].[TrialPlacements]
                            SET TrialClassID = ?
                            WHERE TrialPlacementsID = ?
                            """,
                            correct_trialclass_id,
                            placement_id,
                        )
                        stats["placements_moved"] += 1
                cursor.execute(
                    "DELETE FROM [sResults].[TrialClass] WHERE TrialClassID = ?",
                    wrong_trialclass_id,
                )
                stats["classes_removed"] += 1
                continue

            barn_hunt_div_id = get_or_create_division(cursor, "BARN HUNT")
            if not barn_hunt_div_id:
                continue
            clean_class_name, _ = strip_entries_from_class_name(class_name or "")
            clean_class_name = normalize_class_name_full(clean_class_name, "BARN HUNT")
            barn_hunt_class_id = get_or_create_class(cursor, clean_class_name, barn_hunt_div_id)
            if not barn_hunt_class_id:
                continue
            cursor.execute(
                "UPDATE [sResults].[TrialClass] SET ClassID = ? WHERE TrialClassID = ?",
                barn_hunt_class_id,
                wrong_trialclass_id,
            )
            cursor.execute(
                "SELECT COUNT(*) FROM [sResults].[TrialPlacements] WHERE TrialClassID = ?",
                wrong_trialclass_id,
            )
            stats["placements_moved"] += cursor.fetchone()[0]

        stats["trials"] = len(touched_trials)
        conn.commit()
        print(
            f"  Barn Hunt repair: trials {stats['trials']:,}, "
            f"classes {stats['classes']:,}, moved {stats['placements_moved']:,}, "
            f"deleted dupes {stats['placements_deleted']:,}, "
            f"removed classes {stats['classes_removed']:,}",
            flush=True,
        )
        return stats
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()


def purge_trialvault_nonsanctioned_data(trial_ids: list[int] | None = None) -> dict[str, int]:
    """Remove Trial Vault non-sanctioned classes/placements, including mis-assigned lure rows."""
    stats = {
        "trials": 0,
        "classes": 0,
        "placements": 0,
        "times": 0,
    }
    if not trial_ids:
        return stats

    conn = get_connection()
    cursor = conn.cursor()
    try:
        for trial_id in sorted(set(trial_ids)):
            cursor.execute(
                """
                SELECT tc.TrialClassID, d.DivisionName, c.ClassName
                FROM [sResults].[TrialClass] tc
                JOIN [sResults].[Class] c ON tc.ClassID = c.ClassID
                JOIN [sResults].[Division] d ON c.DivisionID = d.DivisionID
                WHERE tc.TrialListID = ?
                """,
                trial_id,
            )
            trialclass_ids: list[int] = []
            for trialclass_id, division_name, class_name in cursor.fetchall():
                division_upper = (division_name or "").upper()
                division_lower = (division_name or "").lower()
                remove = False
                if "non-sanctioned" in division_lower:
                    remove = True
                elif division_upper == "AGILITY TUNNELERS":
                    remove = True
                elif (
                    division_upper == "LURE COURSING (NON-SANCTIONED)"
                    and _trialvault_class_misassigned_to_lure_coursing(class_name)
                ):
                    remove = True
                if remove:
                    trialclass_ids.append(trialclass_id)

            if not trialclass_ids:
                continue

            stats["trials"] += 1
            stats["classes"] += len(trialclass_ids)
            for trialclass_id in trialclass_ids:
                cursor.execute(
                    """
                    DELETE t
                    FROM [sResults].[TrialPlacements_Times] t
                    JOIN [sResults].[TrialPlacements] p ON t.TrialPlacementsID = p.TrialPlacementsID
                    WHERE p.TrialClassID = ?
                    """,
                    trialclass_id,
                )
                stats["times"] += cursor.rowcount
                cursor.execute(
                    "DELETE FROM [sResults].[TrialPlacements] WHERE TrialClassID = ?",
                    trialclass_id,
                )
                stats["placements"] += cursor.rowcount
                cursor.execute(
                    "DELETE FROM [sResults].[TrialClass] WHERE TrialClassID = ?",
                    trialclass_id,
                )

        conn.commit()
        print(
            f"  Purged non-sanctioned TV data: trials {stats['trials']:,}, "
            f"classes {stats['classes']:,}, placements {stats['placements']:,}, "
            f"times {stats['times']:,}",
            flush=True,
        )
        return stats
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()


def append_trialvault_nonsanctioned_to_database(
    results,
    source_label: str = "",
) -> dict[str, int]:
    """Insert non-sanctioned Trial Vault placements into existing trials."""
    from collections import defaultdict
    from normalize_trialresults_data import normalize_class_name_full

    stats = {
        "trials": 0,
        "classes": 0,
        "inserted": 0,
        "skipped_duplicate": 0,
        "skipped_no_trial": 0,
        "skipped_sanctioned": 0,
        "times_inserted": 0,
    }
    nonsanctioned = [r for r in results if is_nonsanctioned_trialvault_result(r)]
    if not nonsanctioned:
        return stats

    conn = get_connection()
    cursor = conn.cursor()
    try:
        trial_lookup, canonical_lookup, base_year_lookup, trial_years = build_trial_list_lookup(cursor)
        by_trial: dict[int, list] = defaultdict(list)

        for result in nonsanctioned:
            trial_id = resolve_trial_list_id(
                result.trial_name,
                result.year,
                trial_lookup,
                canonical_lookup,
                base_year_lookup,
                trial_years,
            )
            if not trial_id:
                stats["skipped_no_trial"] += 1
                continue
            by_trial[trial_id].append(result)

        for trial_id, trial_results in by_trial.items():
            stats["trials"] += 1
            cursor.execute(
                "SELECT TrialName FROM [sResults].[TrialList] WHERE TrialListID = ?",
                trial_id,
            )
            trial_name_row = cursor.fetchone()
            trial_name = trial_name_row[0] if trial_name_row else str(trial_id)

            cursor.execute(
                """
                SELECT tc.TrialClassID, c.ClassName, d.DivisionName
                FROM [sResults].[TrialClass] tc
                JOIN [sResults].[Class] c ON tc.ClassID = c.ClassID
                JOIN [sResults].[Division] d ON c.DivisionID = d.DivisionID
                WHERE tc.TrialListID = ?
                """,
                trial_id,
            )
            existing_classes: dict[tuple[str, str], int] = {}
            for trialclass_id, class_name, division_name in cursor.fetchall():
                key = (
                    (division_name or "").strip().lower(),
                    (class_name or "").strip().lower(),
                )
                existing_classes[key] = trialclass_id

            cursor.execute(
                """
                SELECT p.TrialPlacementsID, p.TrialClassID, p.Result, d.DogName, o.OwnerName
                FROM [sResults].[TrialPlacements] p
                JOIN [sResults].[Dog] d ON p.DogID = d.DogID
                LEFT JOIN [sResults].[Owner] o ON d.OwnerID = o.OwnerID
                WHERE p.TrialListID = ?
                """,
                trial_id,
            )
            existing_placements: set[tuple] = set()
            for _pid, trialclass_id, result_text, dog_name, owner_name in cursor.fetchall():
                existing_placements.add((
                    trialclass_id,
                    normalize_trialvault_placement_result(result_text or ""),
                    (dog_name or "").strip().lower(),
                    _owner_name_key(owner_name),
                ))

            next_trialclass_id, next_placement_id = get_next_ids_from_db(conn)[1:3]
            next_times_id = get_next_placement_times_id(conn)

            by_class = defaultdict(list)
            for result in trial_results:
                key = (result.division, result.class_name, result.entry_count)
                by_class[key].append(result)

            for (division, class_name, entry_count), class_results in by_class.items():
                division_name = division or "UNKNOWN"
                div_id = get_or_create_division(cursor, division_name)
                if not div_id:
                    continue

                clean_class_name, _ = strip_entries_from_class_name(class_name or "Unknown Class")
                clean_class_name = normalize_class_name_full(clean_class_name, division_name)
                class_id = get_or_create_class(cursor, clean_class_name, div_id)
                if not class_id:
                    continue

                class_key = (division_name.strip().lower(), clean_class_name.strip().lower())
                trialclass_id = existing_classes.get(class_key)
                if not trialclass_id:
                    trialclass_id = next_trialclass_id
                    next_trialclass_id += 1
                    cursor.execute(
                        """
                        INSERT INTO [sResults].[TrialClass] (TrialClassID, TrialListID, ClassID, EntryCount)
                        VALUES (?, ?, ?, ?)
                        """,
                        trialclass_id,
                        trial_id,
                        class_id,
                        entry_count or len(class_results),
                    )
                    existing_classes[class_key] = trialclass_id
                    stats["classes"] += 1

                for result in class_results:
                    owner_id = get_or_create_owner(cursor, result.owner)
                    dog_id = get_or_create_dog(cursor, result.dog_name, owner_id)
                    placement_key = (
                        trialclass_id,
                        normalize_trialvault_placement_result(result.placement or ""),
                        (result.dog_name or "").strip().lower(),
                        _owner_name_key(result.owner),
                    )
                    if placement_key in existing_placements:
                        stats["skipped_duplicate"] += 1
                        continue

                    placement_id = next_placement_id
                    next_placement_id += 1
                    cursor.execute(
                        """
                        INSERT INTO [sResults].[TrialPlacements] (
                            TrialPlacementsID, TrialListID, TrialClassID, DogID, Result
                        )
                        VALUES (?, ?, ?, ?, ?)
                        """,
                        placement_id,
                        trial_id,
                        trialclass_id,
                        dog_id,
                        result.placement,
                    )
                    existing_placements.add(placement_key)
                    stats["inserted"] += 1

                    if result.time:
                        cursor.execute(
                            """
                            INSERT INTO [sResults].[TrialPlacements_Times] (
                                TrialPlacements_TimesID, TrialPlacementsID, Time
                            )
                            VALUES (?, ?, ?)
                            """,
                            next_times_id,
                            placement_id,
                            result.time,
                        )
                        next_times_id += 1
                        stats["times_inserted"] += 1

            conn.commit()

        stats["skipped_sanctioned"] = len(results) - len(nonsanctioned)
        label = f" ({source_label})" if source_label else ""
        print(
            f"  Non-sanctioned append{label}: trials {stats['trials']:,}, "
            f"classes {stats['classes']:,}, placements {stats['inserted']:,}, "
            f"times {stats['times_inserted']:,}, duplicates {stats['skipped_duplicate']:,}, "
            f"no trial match {stats['skipped_no_trial']:,}",
            flush=True,
        )
        return stats
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()


def get_or_create_division(cursor, division_name: str) -> int:
    """Get or create division ID."""
    from normalize_trialresults_data import normalize_division_name_full

    division_name = normalize_division_name_full(division_name)
    cursor.execute("SELECT DivisionID FROM [sResults].[Division] WHERE DivisionName = ?", division_name)
    row = cursor.fetchone()
    if row:
        return row[0]
    
    cursor.execute("INSERT INTO [sResults].[Division] (DivisionName) OUTPUT INSERTED.DivisionID VALUES (?)", division_name)
    row = cursor.fetchone()
    return row[0] if row else None

def get_or_create_class(cursor, class_name: str, division_id: int) -> int:
    """Get or create class ID."""
    cursor.execute("SELECT ClassID FROM [sResults].[Class] WHERE ClassName = ? AND DivisionID = ?", class_name, division_id)
    row = cursor.fetchone()
    if row:
        return row[0]
    
    cursor.execute("INSERT INTO [sResults].[Class] (ClassName, DivisionID) OUTPUT INSERTED.ClassID VALUES (?, ?)", class_name, division_id)
    row = cursor.fetchone()
    return row[0] if row else None

def get_or_create_owner(cursor, owner_name: str) -> Optional[int]:
    """Get or create owner ID."""
    if not owner_name or not owner_name.strip():
        return None

    owner_name = clean_parsed_owner_name(owner_name.strip())
    if not owner_name:
        return None
    cursor.execute("SELECT OwnerID FROM [sResults].[Owner] WHERE OwnerName = ?", owner_name)
    row = cursor.fetchone()
    if row:
        return row[0]

    cursor.execute(
        "INSERT INTO [sResults].[Owner] (OwnerName) OUTPUT INSERTED.OwnerID VALUES (?)",
        owner_name,
    )
    row = cursor.fetchone()
    return row[0] if row else None


def get_or_create_dog(cursor, dog_name: str, owner_id: Optional[int] = None) -> int:
    """Get or create dog ID, matching on name and owner when owner is known."""
    if owner_id:
        cursor.execute(
            "SELECT DogID, OwnerID FROM [sResults].[Dog] WHERE DogName = ? AND OwnerID = ?",
            dog_name,
            owner_id,
        )
        row = cursor.fetchone()
        if row:
            return row[0]

        cursor.execute(
            "SELECT DogID FROM [sResults].[Dog] WHERE DogName = ? AND OwnerID IS NULL",
            dog_name,
        )
        row = cursor.fetchone()
        if row:
            dog_id = row[0]
            cursor.execute(
                "UPDATE [sResults].[Dog] SET OwnerID = ? WHERE DogID = ?",
                owner_id,
                dog_id,
            )
            return dog_id

        cursor.execute(
            "INSERT INTO [sResults].[Dog] (DogName, OwnerID) OUTPUT INSERTED.DogID VALUES (?, ?)",
            dog_name,
            owner_id,
        )
        row = cursor.fetchone()
        return row[0] if row else None

    cursor.execute(
        "SELECT DogID, OwnerID FROM [sResults].[Dog] WHERE DogName = ? AND OwnerID IS NULL",
        dog_name,
    )
    row = cursor.fetchone()
    if row:
        return row[0]

    cursor.execute(
        "INSERT INTO [sResults].[Dog] (DogName) OUTPUT INSERTED.DogID VALUES (?)",
        dog_name,
    )
    row = cursor.fetchone()
    return row[0] if row else None

def strip_html_tags(html: str) -> str:
    """Remove HTML tags and decode HTML entities, excluding script/style content."""
    import html as html_module
    from html.parser import HTMLParser

    class MLStripper(HTMLParser):
        def __init__(self):
            super().__init__()
            self.reset()
            self.strict = False
            self.convert_charrefs = True
            self.text = []
            self.skip_tags = set()

        def handle_starttag(self, tag, attrs):
            # Skip content inside script and style tags
            if tag.lower() in ('script', 'style'):
                self.skip_tags.add(tag.lower())
            elif tag.lower() in ('br', 'p', 'div', 'tr', 'li', 'h1', 'h2', 'h3', 'hr'):
                self.text.append('\n')

        def handle_endtag(self, tag):
            # Resume processing when script/style tag ends
            if tag.lower() in ('script', 'style'):
                self.skip_tags.discard(tag.lower())
            elif tag.lower() in ('p', 'div', 'tr', 'td', 'li', 'h1', 'h2', 'h3'):
                self.text.append('\n')

        def handle_data(self, d):
            # Only append data if we're not inside a skip tag
            if not self.skip_tags:
                self.text.append(d)

        def get_data(self):
            return ''.join(self.text)

    s = MLStripper()
    s.feed(html)
    text = s.get_data()
    # Decode HTML entities
    text = html_module.unescape(text)
    return text


def peek_trial_start_date(raw_content: str, file_path: str, year_dir: int) -> str:
    """Extract trial start date from file content for discovery sort order."""
    content = raw_content
    if _is_html_file(file_path):
        content = strip_html_tags(raw_content)
    lines = expand_glued_placement_lines(content.split('\n'))

    last_nav_idx = 0
    for i, line in enumerate(lines):
        line_clean = line.strip()
        if re.search(
            r'\d{4}\s+(Trial Results|Conformation Division|Performance Division|'
            r'Bronze Medallions|Working Achievement Awards)',
            line_clean,
        ):
            last_nav_idx = i

    header = scan_trial_header_block(
        lines, start_idx=last_nav_idx, max_lines=500, hint_year=year_dir, quiet=True,
    )
    if not header['start_date']:
        header = scan_trial_header_block(
            lines, start_idx=0, max_lines=500, hint_year=year_dir, quiet=True,
        )
    return header['start_date']


def trial_file_sort_key(file_path: str, year_dir: int, start_date: str = "") -> tuple:
    """Sort key: calendar date globally, then folder year and filename."""
    trial_name = os.path.splitext(os.path.basename(file_path))[0].lower()
    basename = os.path.basename(file_path).lower()
    if start_date:
        return (0, normalize_date(start_date, year_dir), year_dir, trial_name, basename)
    return (1, f"{year_dir:04d}-99-99", year_dir, trial_name, basename)


def _normalize_special_file_stem(filename: str) -> str:
    stem = os.path.splitext(filename)[0].lower()
    return re.sub(r'\s+w\s+gtg\s+times$', '', stem).strip()


def _special_folder_slot_key(filename: str, folder_name: str) -> str:
    """Distinguish multiple trials in the same year (I/II, Sat/Sun)."""
    low = filename.lower()
    if folder_name == 'Gold Coast':
        match = re.search(r'gold coast\s+([ivx]+)\b', low)
        if match:
            return match.group(1).upper()
        return ''
    if folder_name == 'JRTCC':
        if re.search(r'\b(sat|saturday)\b', low):
            return 'sat'
        if re.search(r'\b(sun|sunday)\b', low):
            return 'sun'
        return ''
    return ''


def _score_special_folder_file(filename: str, folder_name: str) -> int:
    """Prefer times-rich text sources over plain text and PDF."""
    low = filename.lower()
    score = 0
    if 'incl times' in low or 'w gtg times' in low:
        score += 200
    elif 'nationals' in low and not re.search(r'\bresults\b', low):
        score += 80
    elif re.search(r'\bresults\b', low):
        # Require word boundary so 'trialresults2008.pdf' does NOT get this bonus
        # while '2012 MO Earthdogs Results.txt' does.
        score += 70
    if low.endswith('.txt'):
        score += 50
    elif low.endswith('.pdf'):
        score += 10
    if folder_name == 'MO Earthdogs' and 'mo earthdogs' in low:
        score += 5
    return score


def _dedupe_special_folder_files(
    files: list[tuple[str, int]],
    folder_name: str,
) -> list[tuple[str, int]]:
    """Prefer richer text sources; keep separate I/II and Sat/Sun trials."""
    from collections import defaultdict

    grouped: dict[tuple[int, str], list[tuple[str, int, int]]] = defaultdict(list)
    for file_path, year in files:
        filename = os.path.basename(file_path)
        slot = _special_folder_slot_key(filename, folder_name)
        score = _score_special_folder_file(filename, folder_name)
        grouped[(year, slot)].append((file_path, year, score))

    return [(entries[0][0], entries[0][1]) for entries in (
        sorted(items, key=lambda item: item[2], reverse=True)[:1]
        for items in grouped.values()
    )]


def discover_special_folder_files(
    base_dir: str,
    folder_name: str,
    year_filter: int | None = None,
) -> list[tuple[str, int]]:
    """Discover trial files from folders like MO Earthdogs."""
    folder_path = os.path.join(base_dir, folder_name)
    if not os.path.isdir(folder_path):
        return []

    candidates: list[tuple[str, int]] = []
    for filename in os.listdir(folder_path):
        if filename.startswith('debug_trialvault_'):
            continue
        if not filename.lower().endswith(('.txt', '.html', '.htm', '.pdf')):
            continue
        year_match = re.search(r'(\d{4})', filename)
        if not year_match:
            continue
        year = int(year_match.group(1))
        if year_filter and year != year_filter:
            continue
        candidates.append((os.path.join(folder_path, filename), year))

    deduped = _dedupe_special_folder_files(candidates, folder_name)

    content_deduped: list[tuple[str, int, str]] = []
    signature_seen: dict[int, set[str]] = {}
    for file_path, year_dir in deduped:
        if file_path.lower().endswith('.pdf'):
            content_deduped.append((file_path, year_dir, ""))
            continue
        try:
            with open(file_path, 'r', encoding='utf-8', errors='ignore') as handle:
                raw_text = handle.read()
        except OSError:
            content_deduped.append((file_path, year_dir, ""))
            continue
        sig = hashlib.md5(
            re.sub(r'\s+', ' ', raw_text).strip().lower().encode('utf-8', errors='ignore'),
        ).hexdigest()
        year_sigs = signature_seen.setdefault(year_dir, set())
        if sig in year_sigs:
            continue
        year_sigs.add(sig)
        start_date = peek_trial_start_date(raw_text, file_path, year_dir)
        content_deduped.append((file_path, year_dir, start_date))

    content_deduped.sort(key=lambda item: trial_file_sort_key(item[0], item[1], item[2]))
    return [(file_path, year_dir) for file_path, year_dir, _ in content_deduped]


def discover_trial_files(
    base_dir: str = ".",
    year_filter: int | None = None,
    folder_filter: str | None = None,
) -> list[tuple[str, int]]:
    """Discover trial result files using the same rules as populate main()."""
    if folder_filter:
        return discover_special_folder_files(base_dir, folder_filter, year_filter)

    all_files: list[tuple[str, int]] = []

    for year_dir in range(1984, 2027):
        if year_filter and year_dir != year_filter:
            continue
        year_path = os.path.join(base_dir, str(year_dir))
        if not os.path.exists(year_path):
            continue

        for file in os.listdir(year_path):
            if file.startswith('debug_trialvault_'):
                continue
            if file.endswith('_raw.txt') or file.endswith('.txt'):
                all_files.append((os.path.join(year_path, file), year_dir))
            elif _is_html_file(file) and not file.startswith('debug') and 'Trial Results' not in file:
                all_files.append((os.path.join(year_path, file), year_dir))

    html_stems_by_year: dict[int, set[str]] = {}
    for file_path, year_dir in all_files:
        if _is_html_file(file_path):
            stem = os.path.splitext(os.path.basename(file_path))[0].lower()
            html_stems_by_year.setdefault(year_dir, set()).add(stem)

    deduped_files: list[tuple[str, int]] = []
    for file_path, year_dir in all_files:
        if file_path.endswith('.txt'):
            stem = os.path.splitext(os.path.basename(file_path))[0].lower()
            if stem in html_stems_by_year.get(year_dir, set()):
                continue
        deduped_files.append((file_path, year_dir))

    def content_signature(raw_text: str) -> str:
        normalized = re.sub(r'\s+', ' ', raw_text).strip().lower()
        return hashlib.md5(normalized.encode('utf-8', errors='ignore')).hexdigest()

    signature_seen: dict[int, set[str]] = {}
    content_deduped: list[tuple[str, int, str]] = []
    for file_path, year_dir in deduped_files:
        try:
            with open(file_path, 'r', encoding='utf-8', errors='ignore') as handle:
                raw_text = handle.read()
        except OSError:
            content_deduped.append((file_path, year_dir, ""))
            continue
        sig = content_signature(raw_text)
        year_sigs = signature_seen.setdefault(year_dir, set())
        if sig in year_sigs:
            continue
        year_sigs.add(sig)
        start_date = peek_trial_start_date(raw_text, file_path, year_dir)
        content_deduped.append((file_path, year_dir, start_date))

    content_deduped.sort(key=lambda item: trial_file_sort_key(item[0], item[1], item[2]))
    return [(file_path, year_dir) for file_path, year_dir, _ in content_deduped]


def kill_other_populate_processes() -> int:
    """Terminate other running populate loaders before starting a new run."""
    if sys.platform != "win32":
        return 0

    my_pid = os.getpid()
    parent_pid = os.getppid()
    ps = (
        "Get-CimInstance Win32_Process | "
        "Where-Object { $_.CommandLine -match 'populate_trialresults' } | "
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
        print(
            f"Terminated {len(killed)} other populate process(es): {', '.join(killed)}",
            flush=True,
        )
    return len(killed)


def trial_result_file_path(file_path: str) -> str:
    """Return normalized absolute path stored in TrialList.TrialResultFilePath."""
    return os.path.normpath(os.path.abspath(file_path))


def is_sql_deadlock(exc: Exception) -> bool:
    """True for SQL Server deadlock victim errors (1205)."""
    msg = str(exc).lower()
    return '1205' in msg or 'deadlock' in msg


def run_db_action_with_deadlock_retry(
    conn,
    action,
    description: str,
    *,
    max_retries: int = 5,
    base_delay: float = 0.5,
) -> None:
    """Run a DB action; retry with backoff when SQL Server reports a deadlock."""
    for attempt in range(max_retries):
        try:
            action()
            conn.commit()
            return
        except Exception as e:
            conn.rollback()
            if is_sql_deadlock(e) and attempt < max_retries - 1:
                delay = base_delay * (2 ** attempt)
                print(
                    f"  Deadlock during {description}, "
                    f"retry {attempt + 2}/{max_retries} in {delay:.1f}s...",
                    flush=True,
                )
                time.sleep(delay)
                continue
            raise


def parse_trial_source_file(
    file_path: str,
    year: int,
    *,
    quiet: bool = False,
):
    """Parse a downloaded results file into (trial_info, placements, error).

    Shared by the loader and the post-load verifier so both work from an
    identical reading of the original downloaded text; error is None on success.
    """
    try:
        if file_path.lower().endswith('.pdf'):
            from scrape_trial_results_fixed import extract_text_from_pdf
            raw_content = extract_text_from_pdf(file_path)
            if not raw_content:
                return None, None, "ERROR: Could not extract text from PDF"
        else:
            with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                raw_content = f.read()
    except Exception as e:
        return None, None, f"ERROR: Could not read file: {e}"

    html_meta = {}
    content = raw_content
    if _is_html_file(file_path):
        html_meta = extract_html_trial_metadata(raw_content)
        content = strip_html_tags(raw_content)

    # Split into lines and expand glued HTML placements
    lines = expand_glued_placement_lines(content.split('\n'))

    trial_info = extract_trial_info(lines, year, file_path)
    if not trial_info:
        return None, None, "Skipping file - could not extract trial info"

    if html_meta.get('start_date') and not trial_info.start_date:
        trial_info.start_date = html_meta['start_date']
        trial_info.end_date = html_meta['end_date'] or html_meta['start_date']
        if html_meta.get('location'):
            trial_info.location = html_meta['location']
        if not quiet:
            print(f"    Location: {trial_info.location}")
            print(f"    Dates: {trial_info.start_date} to {trial_info.end_date}")
    for field in ('chair', 'administrator', 'judges'):
        if html_meta.get(field) and not getattr(trial_info, field):
            setattr(trial_info, field, html_meta[field])
            if not quiet:
                print(f"    {field.title()}: {html_meta[field]}")

    placements = parse_placements(lines, trial_info)
    return trial_info, placements, None


def process_trial_file(
    conn,
    file_path: str,
    year: int,
    next_trial_id: int,
    next_trialclass_id: int,
    next_placement_id: int,
    entity_ctx=None,
    *,
    reuse_entities: bool = False,
    defer_normalization: bool = False,
    loaded_trial_ids: list[int] | None = None,
    verify_normalization: bool = True,
):
    """Process a single trial file and insert into database. Returns updated ID counters."""
    filename = os.path.basename(file_path)
    result_file_path = trial_result_file_path(file_path)
    
    # Save original IDs in case of rollback (re-synced from DB again before insert)
    orig_trial_id = next_trial_id
    orig_trialclass_id = next_trialclass_id
    orig_placement_id = next_placement_id
    
    # Skip archive/index pages and entry catalogs (not trial result pages)
    if _is_html_file(file_path) and 'Trial Results' in filename:
        return next_trial_id, next_trialclass_id, next_placement_id
    if 'Entries Catalog' in filename:
        print(f"  Skipping entry catalog: {filename}", flush=True)
        return next_trial_id, next_trialclass_id, next_placement_id
    
    print(f"\nProcessing: {result_file_path}", flush=True)
    
    trial_info, placements, parse_error = parse_trial_source_file(file_path, year)
    if parse_error:
        print(f"  {parse_error}", flush=True)
        return next_trial_id, next_trialclass_id, next_placement_id

    print(f"  Found {len(placements)} placement results", flush=True)
    
    if not placements:
        print(f"  Skipping file - no placements found", flush=True)
        sys.stdout.flush()
        return next_trial_id, next_trialclass_id, next_placement_id
    
    # Insert into database
    cursor = conn.cursor()

    # Always sync ID counters from DB so rollback/normalization failures cannot reuse IDs
    next_trial_id, next_trialclass_id, next_placement_id = get_next_ids_from_db(conn)
    orig_trial_id = next_trial_id
    orig_trialclass_id = next_trialclass_id
    orig_placement_id = next_placement_id
    next_times_id = get_next_placement_times_id(conn)
    times_inserted = 0
    
    try:
        # Check if trial already exists (exact or normalized name)
        cursor.execute(
            "SELECT TrialListID, TrialName FROM [sResults].[TrialList] WHERE Year = ?",
            trial_info.year,
        )
        current_key = canonical_trial_match_key(trial_info.trial_name, trial_info.year)
        for existing_id, existing_name in cursor.fetchall():
            if (
                existing_name == trial_info.trial_name
                or trial_name_key(existing_name) == trial_name_key(trial_info.trial_name)
                or canonical_trial_match_key(existing_name, trial_info.year) == current_key
            ):
                cursor.execute(
                    """
                    UPDATE [sResults].[TrialList]
                    SET TrialResultFilePath = ?
                    WHERE TrialListID = ?
                      AND (TrialResultFilePath IS NULL OR LTRIM(RTRIM(TrialResultFilePath)) = '')
                    """,
                    result_file_path,
                    existing_id,
                )
                print(f"  Trial already exists in database (ID: {existing_id}, name: {existing_name}), skipping...", flush=True)
                sys.stdout.flush()
                return next_trial_id, next_trialclass_id, next_placement_id
        
        # Insert trial
        start_date_sql = normalize_date(trial_info.start_date, trial_info.year)
        end_date_sql = normalize_date(trial_info.end_date, trial_info.year)
        
        # Parse location into city and state
        location_city = None
        location_state = None
        if trial_info.location:
            # Format: "Buffalo, TX" or "Boonsboro, MD"
            parts = trial_info.location.split(',')
            if len(parts) >= 2:
                location_city = parts[0].strip()
                location_state = parts[1].strip()
            else:
                location_city = trial_info.location.strip()
        
        # Use the passed-in trial ID
        trial_id = next_trial_id
        next_trial_id += 1
        
        cursor.execute("""
            INSERT INTO [sResults].[TrialList] (
                TrialListID, TrialName, Year, StartDate, EndDate,
                LocationCity, LocationState, Chairperson, TrialResultFilePath
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, trial_id, trial_info.trial_name, trial_info.year, start_date_sql, end_date_sql,
             location_city, location_state, trial_info.chair or None, result_file_path)
        
        print(f"  Inserted trial (ID: {trial_id})", flush=True)
        
        # Process placements by class
        from collections import defaultdict
        by_class = defaultdict(list)
        for p in placements:
            key = (p.division, p.class_name, p.entries)
            by_class[key].append(p)
        
        # Insert classes and placements (use passed-in IDs)
        from normalize_trialresults_data import normalize_class_name_full
        if reuse_entities and entity_ctx is not None:
            from populate_trialresults_database import resolve_or_create_dog_owner_pair
            from normalize_trialresults_data import normalize_dog_name

            def _create_dog(cur, raw_name, owner_id):
                clean_name = normalize_dog_name(raw_name) or raw_name
                return get_or_create_dog(cur, clean_name, owner_id)

        for (division, class_name, entries), class_placements in by_class.items():
            # Get or create division
            div_id = get_or_create_division(cursor, division)
            if not div_id:
                continue
            
            # Get or create class (strip any Entries suffix that slipped through)
            clean_class_name, _ = strip_entries_from_class_name(class_name)
            clean_class_name = normalize_class_name_full(clean_class_name, division)
            class_id = get_or_create_class(cursor, clean_class_name, div_id)
            if not class_id:
                continue
            
            # Use and increment trialclass_id
            trialclass_id = next_trialclass_id
            next_trialclass_id += 1
            
            # Insert TrialClass
            cursor.execute("""
                INSERT INTO [sResults].[TrialClass] (TrialClassID, TrialListID, ClassID, EntryCount)
                VALUES (?, ?, ?, ?)
            """, trialclass_id, trial_id, class_id, entries)
            
            # Insert placements
            for p in class_placements:
                if reuse_entities and entity_ctx is not None:
                    dog_id, owner_id = resolve_or_create_dog_owner_pair(
                        p.dog_name,
                        p.owner_name,
                        entity_ctx,
                        cursor,
                        create_dog_fn=_create_dog,
                    )
                else:
                    owner_id = get_or_create_owner(cursor, p.owner_name)
                    dog_id = get_or_create_dog(cursor, p.dog_name, owner_id)
                
                # Use and increment placement_id
                placement_id = next_placement_id
                next_placement_id += 1
                
                cursor.execute("""
                    INSERT INTO [sResults].[TrialPlacements] (TrialPlacementsID, TrialListID, TrialClassID, DogID, Result)
                    VALUES (?, ?, ?, ?, ?)
                """, placement_id, trial_id, trialclass_id, dog_id, p.placement)

                if p.time:
                    cursor.execute(
                        """
                        INSERT INTO [sResults].[TrialPlacements_Times] (
                            TrialPlacements_TimesID, TrialPlacementsID, Time
                        )
                        VALUES (?, ?, ?)
                        """,
                        next_times_id,
                        placement_id,
                        p.time,
                    )
                    next_times_id += 1
                    times_inserted += 1
        
        conn.commit()
        print(
            f"  Successfully inserted {len(placements)} placements "
            f"({times_inserted} with times) (Trial ID: {trial_id})",
            flush=True,
        )

        committed_next_trial_id = next_trial_id
        committed_next_trialclass_id = next_trialclass_id
        committed_next_placement_id = next_placement_id

    except Exception as e:
        conn.rollback()
        print(f"  ERROR: {e}", flush=True)
        import traceback
        traceback.print_exc()
        sys.stdout.flush()
        # Return original IDs since insert transaction rolled back
        return orig_trial_id, orig_trialclass_id, orig_placement_id

    try:
        if defer_normalization:
            if loaded_trial_ids is not None:
                loaded_trial_ids.append(trial_id)
            print(f"  Deferred normalization for trial {trial_id}", flush=True)
        elif verify_normalization:
            from verify_trial_normalization import verify_loaded_trials

            def _normalize_and_verify() -> None:
                verify_loaded_trials(
                    conn,
                    [trial_id],
                    sources={trial_id: placements},
                    skip_dog_owner_merge=reuse_entities,
                )

            run_db_action_with_deadlock_retry(
                conn,
                _normalize_and_verify,
                f"post-load normalization and source comparison for trial {trial_id}",
            )
        else:
            from normalize_trialresults_data import run_post_trial_normalization

            def _normalize_trial() -> None:
                run_post_trial_normalization(
                    conn,
                    trial_id,
                    skip_dog_owner_merge=reuse_entities,
                )

            run_db_action_with_deadlock_retry(
                conn,
                _normalize_trial,
                f"post-load normalization for trial {trial_id}",
            )
    except Exception as e:
        print(f"  WARNING: Post-load normalization failed for trial {trial_id}: {e}", flush=True)
        import traceback
        traceback.print_exc()
        sys.stdout.flush()

    sys.stdout.flush()

    # Trial insert already committed; always advance ID counters
    return committed_next_trial_id, committed_next_trialclass_id, committed_next_placement_id


def run_deferred_trial_normalizations(
    conn,
    trial_ids: list[int],
    *,
    reuse_entities: bool = False,
    verify_normalization: bool = True,
) -> None:
    """Normalize all trials after a batch folder load in one pass."""
    if not trial_ids:
        return
    from normalize_trialresults_data import run_batch_post_trial_normalization

    print(
        f"\nRunning deferred post-load normalization for {len(trial_ids)} trial(s) "
        f"in one batch...",
        flush=True,
    )

    def _normalize_batch() -> None:
        if verify_normalization:
            from verify_trial_normalization import verify_loaded_trials

            verify_loaded_trials(
                conn,
                trial_ids,
                skip_dog_owner_merge=reuse_entities,
            )
            return
        run_batch_post_trial_normalization(
            conn,
            trial_ids,
            skip_dog_owner_merge=reuse_entities,
        )

    try:
        run_db_action_with_deadlock_retry(
            conn,
            _normalize_batch,
            f"deferred post-load normalization for {len(trial_ids)} trials",
        )
    except Exception as e:
        print(f"  WARNING: Deferred normalization failed: {e}", flush=True)
        import traceback
        traceback.print_exc()
        sys.stdout.flush()

def main():
    """Main function."""
    import argparse
    global VERBOSE_OUTPUT
    
    parser = argparse.ArgumentParser(description='Populate trial results with FIXED parsing')
    parser.add_argument('--clear', action='store_true', help='Clear ALL data (dogs, owners, catalog, trials) before loading')
    parser.add_argument(
        '--clear-trials-only',
        action='store_true',
        help='Clear only trial result tables (TrialPlacements, TrialClass, TrialList); retain dogs, owners, divisions, classes, catalog',
    )
    parser.add_argument(
        '--reuse-entities',
        action='store_true',
        help='Match dogs/owners/divisions/classes to existing catalog data; skip dog/owner merges during post-load normalization',
    )
    parser.add_argument('--year', type=int, help='Process only this year (default: all years)')
    parser.add_argument(
        '--folder',
        help='Process trial files only from this subfolder (e.g. "MO Earthdogs")',
    )
    parser.add_argument(
        '--normalize-at-end',
        action='store_true',
        help='Skip per-trial normalization during load; normalize all inserted trials once at the end',
    )
    parser.add_argument(
        '--no-verify',
        action='store_true',
        help='Skip comparing normalized names back against the downloaded source files',
    )
    parser.add_argument('--verbose', action='store_true', help='Print every division/class/placement (very noisy)')
    parser.add_argument(
        '--log-file',
        default='populate_run.log',
        help='Append populate output to this log file (default: populate_run.log)',
    )
    parser.add_argument(
        '--load-catalog',
        action='store_true',
        help='After trial results load, load 2008-2025 entry catalogs (reuses Dog/Owner from trials)',
    )
    parser.add_argument(
        '--catalog-only',
        action='store_true',
        help='Load 2008-2025 entry catalogs only; skip trial results processing',
    )
    parser.add_argument(
        '--auto-skip-catalog-processed',
        action='store_true',
        help='With --load-catalog or --catalog-only, skip catalog years already in CatalogEntry',
    )
    args = parser.parse_args()
    VERBOSE_OUTPUT = args.verbose

    if args.catalog_only and args.clear:
        print('ERROR: --catalog-only cannot be used with --clear (would wipe existing trial data)')
        sys.exit(1)
    if args.clear and args.clear_trials_only:
        print('ERROR: --clear and --clear-trials-only are mutually exclusive')
        sys.exit(1)
    if args.catalog_only and args.year:
        print('ERROR: --catalog-only cannot be used with --year')
        sys.exit(1)

    kill_other_populate_processes()

    log_handle = None
    original_stdout = sys.stdout
    if args.log_file:
        log_path = os.path.abspath(args.log_file)
        log_handle = open(log_path, 'a', encoding='utf-8', buffering=1)
        log_handle.write(
            f"\n{'=' * 80}\n"
            f"POPULATE RUN START {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n"
            f"{'=' * 80}\n"
        )

        class _TeeStdout:
            def write(self, data):
                if not data:
                    return
                if log_handle:
                    log_handle.write(data)
                try:
                    original_stdout.write(data)
                except UnicodeEncodeError:
                    enc = getattr(original_stdout, 'encoding', None) or 'utf-8'
                    original_stdout.write(data.encode(enc, errors='replace').decode(enc))

            def flush(self):
                original_stdout.flush()
                if log_handle:
                    log_handle.flush()

            def reconfigure(self, **kwargs):
                if hasattr(original_stdout, 'reconfigure'):
                    original_stdout.reconfigure(**kwargs)

            def __getattr__(self, name):
                return getattr(original_stdout, name)

        sys.stdout = _TeeStdout()
    
    print("=" * 80)
    if args.catalog_only:
        print("JRTCA ENTRY CATALOG LOADER")
    else:
        print("JRTCA TRIAL RESULTS DATABASE POPULATOR (FIXED PARSING)")
    print("=" * 80)
    
    # Connect to database
    print("\nConnecting to database...")
    conn = get_connection()
    if not conn:
        print("ERROR: Could not connect to database")
        if log_handle:
            log_handle.close()
            sys.stdout = original_stdout
        return
    
    if not args.catalog_only:
        # Clear tables if requested
        if args.clear:
            clear_all_trial_data(conn)
        elif args.clear_trials_only:
            from populate_trialresults_database import clear_trial_results_tables
            clear_trial_results_tables(conn)

        reuse_entities = args.reuse_entities or args.clear_trials_only
        defer_normalization = args.normalize_at_end or (
            args.folder in SPECIAL_TRIAL_FOLDERS
        )
        if defer_normalization:
            print("Per-trial normalization deferred until all files are loaded", flush=True)
        
        # Find all trial files
        print("\nScanning for trial files...")
        all_files = discover_trial_files(
            base_dir=".", year_filter=args.year, folder_filter=args.folder,
        )
        skipped_txt = 0
        for year_dir in range(1984, 2027):
            year_path = os.path.join(".", str(year_dir))
            if not os.path.isdir(year_path):
                continue
            if args.year and year_dir != args.year:
                continue
            for file in os.listdir(year_path):
                if not file.endswith('.txt'):
                    continue
                stem = os.path.splitext(file)[0].lower()
                html_exists = any(
                    _is_html_file(other) and os.path.splitext(other)[0].lower() == stem
                    for other in os.listdir(year_path)
                )
                if html_exists:
                    skipped_txt += 1

        print(f"Found {len(all_files)} trial files", end="")
        if skipped_txt:
            print(f" (skipped {skipped_txt} txt files with matching html/htm)", end="")
        print(" (ordered by trial date, then filename)")
        
        # Get starting IDs once at the very beginning for ALL trials
        cursor = conn.cursor()

        entity_ctx = None
        if reuse_entities:
            from populate_trialresults_database import preload_dogs_and_owners_from_db
            print("\nPreloading dogs, owners, divisions, and classes from database...")
            entity_ctx = preload_dogs_and_owners_from_db(conn)
            cursor.execute("SELECT COUNT(*) FROM [sResults].[Dog]")
            dog_count = cursor.fetchone()[0]
            cursor.execute("SELECT COUNT(*) FROM [sResults].[Owner]")
            owner_count = cursor.fetchone()[0]
            cursor.execute("SELECT COUNT(*) FROM [sResults].[Division]")
            division_count = cursor.fetchone()[0]
            cursor.execute("SELECT COUNT(*) FROM [sResults].[Class]")
            class_count = cursor.fetchone()[0]
            print(
                f"  Loaded {dog_count:,} dogs, {owner_count:,} owners, "
                f"{division_count:,} divisions, {class_count:,} classes for reuse"
            )
            print("  Dog/owner merges disabled during post-load normalization")
        
        # If we just cleared trial tables, start from 1. Otherwise, continue from MAX+1
        if args.clear or args.clear_trials_only:
            # After clearing, tables should be empty, so start from 1
            next_trial_id = 1
            next_trialclass_id = 1
            next_placement_id = 1
            print(f"Starting IDs (after clear): Trial={next_trial_id}, Class={next_trialclass_id}, Placement={next_placement_id}")
        else:
            # Not clearing, so get MAX IDs and continue from there
            cursor.execute("SELECT ISNULL(MAX(TrialListID), 0) FROM [sResults].[TrialList]")
            row = cursor.fetchone()
            max_trial_id = row[0] if row and row[0] else 0
            next_trial_id = max_trial_id + 1
            
            cursor.execute("SELECT ISNULL(MAX(TrialClassID), 0) FROM [sResults].[TrialClass]")
            row = cursor.fetchone()
            max_class_id = row[0] if row and row[0] else 0
            next_trialclass_id = max_class_id + 1
            
            cursor.execute("SELECT ISNULL(MAX(TrialPlacementsID), 0) FROM [sResults].[TrialPlacements]")
            row = cursor.fetchone()
            max_placement_id = row[0] if row and row[0] else 0
            next_placement_id = max_placement_id + 1
            
            print(f"Starting IDs (continuing): Trial={next_trial_id}, Class={next_trialclass_id}, Placement={next_placement_id}")
        
        # Process each file
        total_files = len(all_files)
        loaded_trial_ids: list[int] = []
        for i, (file_path, year) in enumerate(all_files, 1):
            print(f"[{i}/{total_files}]", end=" ", flush=True)
            prev_trial_id = next_trial_id
            next_trial_id, next_trialclass_id, next_placement_id = process_trial_file(
                conn, file_path, year, next_trial_id, next_trialclass_id, next_placement_id,
                entity_ctx,
                reuse_entities=reuse_entities,
                defer_normalization=defer_normalization,
                loaded_trial_ids=loaded_trial_ids,
                verify_normalization=not args.no_verify,
            )
            if next_trial_id > prev_trial_id:
                print(f"  -> Trial ID {prev_trial_id} committed", flush=True)
            sys.stdout.flush()
            sys.stderr.flush()

        if defer_normalization:
            run_deferred_trial_normalizations(
                conn,
                loaded_trial_ids,
                reuse_entities=reuse_entities,
                verify_normalization=not args.no_verify,
            )
    
    if args.load_catalog or args.catalog_only:
        print("\n" + "=" * 80)
        print("LOADING ENTRY CATALOGS (2008-2025)")
        print("=" * 80)
        from populate_trialresults_database import load_catalog_data
        load_catalog_data(
            conn,
            auto_skip_processed=args.auto_skip_catalog_processed,
        )
    
    conn.close()
    
    print("\n" + "=" * 80)
    print("DONE!")
    print("=" * 80)
    if log_handle:
        log_handle.write(f"POPULATE RUN END {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
        log_handle.close()
        sys.stdout = original_stdout

if __name__ == "__main__":
    main()
