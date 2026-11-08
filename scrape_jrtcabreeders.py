#!/usr/bin/env python3
"""Scrape jrtcabreeders.com (live + archive.org), save pages/photos, load TrialResults."""
from __future__ import annotations

import html
import json
import os
import re
import time
import urllib.error
import urllib.parse
import urllib.request
from dataclasses import asdict, dataclass, field, replace
from datetime import datetime
from pathlib import Path
from typing import Optional

import pyodbc

ROOT = Path(__file__).resolve().parent / "jrtcabreeders.com"
PAGES_LIVE = ROOT / "pages" / "live"
PAGES_ARCHIVE = ROOT / "pages" / "archive"
PHOTOS = ROOT / "photos"
API = ROOT / "api"
for _d in (PAGES_LIVE, PAGES_ARCHIVE, PHOTOS, API):
    _d.mkdir(parents=True, exist_ok=True)

UA = {"User-Agent": "Mozilla/5.0 jrtca-results-research"}
LIVE_HOST = "https://www.jrtcabreeders.com"
SKIP_IMG = re.compile(
    r"(jrtcalogo|logoleash|logolarge|breeders\.jpg|truegrit|data:image)", re.I
)
SKIP_PAGES = {
    "",
    "jrtca-breeders",
    "jrtca-breeders-by-state",
    "code-of-ethics",
    "contact",
    "requirements-for-jrtca-directory-of-breeders-applicants",
    "jack-russell-terrier-club-of-america",
    "category/breeder",
    "feed",
    "comments/feed",
}
SECTION_SEX = [
    (re.compile(r"\b(boys?|studs?|gentlemen|dogs|males?)\b", re.I), "dog"),
    (re.compile(r"\b(girls?|ladies|bitches|females?)\b", re.I), "bitch"),
]
STOP_HEADERS = re.compile(
    r"contact information|contact breeder|list of breeders|the breeders highlighted",
    re.I,
)
SECTION_HDR = re.compile(
    r"^(our |my |the |meet |standing |also |working |introducing|at stud|"
    r"the gentlemen|the ladies|boys|girls|dogs|bitches)",
    re.I,
)
HEIGHT_RE = re.compile(
    r"(\d{1,2}(?:\s*[½¼¾]|\s+\d/\d|\.\d+|-\d/\d)?)\s*(?:[\"”″]|in(?:ch(?:es)?)?)(?!\w)",
    re.I,
)
COAT_RE = re.compile(
    r"\b((?:lightly\s+)?(?:broken|smooth|rough)|lighlty\s+broken)\b", re.I
)
COLOR_RE = re.compile(
    r"\b(tricolor|tri-color|tan/?\s*white|black/?\s*white|white|tan and white|"
    r"black and white|black/white|tan/white)\b",
    re.I,
)
DOB_RE = re.compile(
    r"\b(?:DOB|born|b\.)\s*[:\-]?\s*"
    r"(\d{1,2}[/-]\d{1,2}[/-]\d{2,4}|[A-Za-z]{3,9}\s+\d{1,2},?\s+\d{4}|\d{4})\b",
    re.I,
)
SIRE_DAM_RE = re.compile(
    r"\(([^()\n]+?)\s+[xX×]\s+([^()\n]+?)\)\s*(.*)$"
)
CLASSIC_BOLD_RE = re.compile(
    r"<b(?:\s[^>]*)?>(.*?)</b>\s*(?:<i(?:\s[^>]*)?>)?(.*?)(?=<b[\s>]|visitors and inquiries|visit our website|\[<a\s+href)",
    re.I | re.S,
)
CLASSIC_LOC_RE = re.compile(
    r'Lucida Handwriting[^>]*>([^<]+)', re.I
)
JUNK_NOTE_RE = re.compile(
    r"(\[\s*Introduction\s*\].*$|Visit our Website.*$|Email:\s*\S+@\S+|"
    r"All breeding stock BAER.*$|Visitors and inquiries.*$)",
    re.I,
)
BY_OUT_RE = re.compile(
    r"\b(?:full siblings?\s+)?by\s+(.+?),\s+out of\s+(.+)$", re.I
)
CALL_RE = re.compile(r'call name\s*[“"\']([^”"\']+)[”"\']', re.I)
COOWN_RE = re.compile(r"co-?owned with\s+([^)\n]+)", re.I)
EMAIL_RE = re.compile(r"[A-Z0-9._%+-]+@[A-Z0-9.-]+\.[A-Z]{2,}", re.I)
PHONE_RE = re.compile(r"\(?\d{3}\)?[-.\s]\d{3}[-.\s]\d{4}(?:\s*/\s*\(?\d{3}\)?[-.\s]\d{3}[-.\s]\d{4})?")
ZIP_RE = re.compile(r"\b(\d{5}(?:-\d{4})?)\b")
ST_RE = re.compile(
    r",\s*([A-Z]{2}|Alabama|Alaska|Arizona|Arkansas|California|Colorado|Florida|"
    r"Georgia|Iowa|Massachusetts|Michigan|Mississippi|Missouri|Nebraska|"
    r"New Jersey|New York|North Carolina|Oklahoma|Oregon|Pennsylvania|"
    r"Tennessee|Texas|Virginia|Washington|West Virginia|Wisconsin|Wyoming)\s*(\d{5})?",
    re.I,
)
TAG_RE = re.compile(r"<[^>]+>")
BR_RE = re.compile(r"(?i)<br\s*/?>")
BLOCK_RE = re.compile(r"(?i)</(?:p|h[1-6]|li|div|tr)>")
TITLE_KEEP = re.compile(
    r"\b("
    r"NHC(?:\s+to\s+[A-Za-z][\w\s/&'-]+)?|"
    r"natural hunting certificate(?:\s+(?:below ground\s+)?(?:in the field|to\s+[A-Za-z][\w\s/&'-]+))?|"
    r"bronze medallion(?:\s+for[^,.\n]+)?|"
    r"working achievement(?:\s+award)?(?:\s+for[^,.\n]+)?|"
    r"WAA|"
    r"(?:JRTCA|JRTCC|JRTGB|UK)\s+[^\n]+|"
    r"(?:19|20)\d{2}(?:\s*[&/,]\s*(?:19|20)\d{2})*\s+[^\n]+|"
    r"(?:\d+-time\s+)?(?:national|reserve|best|high[- ]point|champion|championship)[^\n]*|"
    r"sire of[^\n]+|"
    r"standing at stud[^\n]*|"
    r"limited availability[^\n]*"
    r")\b",
    re.I,
)
HEALTH_RE = re.compile(
    r"\b((?:BAER|CERF|CAER|CARE|PLL|SCA|DM|NNA|LOA|HU|LOA)"
    r"(?:/?\s*(?:BAER|CERF|CAER|PLL|SCA|DM|NNA|LOA|HU))*"
    r"(?:\s*(?:tested|normal|clear|nbd|DNA normal|clear by descent|clear/normal|by descent)[^.\n]*)?|"
    r"BB/?DD|"
    r"clear by descent|"
    r"health registry)\b",
    re.I,
)
NAME_LINE_RE = re.compile(
    r"^[A-Z0-9][A-Z0-9'’\-\./& ]{2,80}$"
)
SKIP_NAME = re.compile(
    r"^(contact|website|facebook|instagram|email|phone|fax|introducing|our |"
    r"my |the |meet |standing|also at|working |boys|girls|dogs|bitches|"
    r"please |visitors|all terriers|all breeding|find us|or find|y.all|"
    r"for your|we |i |this |she |he |can.t|wonderful|prior to|"
    r"pll|baer|cerf|caer|sca|dm|nna|loa|nhc|bb/?dd|"
    r"nhc,? baer.*|at stud|the girls|the boys|introduction|"
    r"our girls|our boys|our young|litter planning|code of ethics|"
    r"inquiries|visitors always|standing at stud)$",
    re.I,
)
JUNK_NAME_RE = re.compile(
    r"(?:(?:^|\s)fax(?:\s*:|\s*\()|\bphone\b|\bemail\b|href\s*=|<\s*a\s|www\.|"
    r"inquiries always|visitors welcome|our girls include|"
    r"litter planning|introducing:|standing at stud|"
    r"negative brucellosis|always welcome)",
    re.I,
)
JUNK_OWNER_RE = re.compile(
    r"(inquir|welcome|brucellosis|www\.|href|visitors|always welcome|"
    r"our girls|standing at|ell\.com|http|fax\b|@)",
    re.I,
)
DATE_TAIL_RE = re.compile(r"\s+\d{1,2}/\d{1,2}(?:/\d{2,4})?\s*$")
WELCOME_PREFIX_RE = re.compile(r"^welcome\s*[~\-–—:]\s*", re.I)
HEALTH_ONLY_RE = re.compile(
    r"^(?:all\s+)?(?:(?:BAER|CERF|PLL|SCA|DM|NNA|LOA|HU|NHC)"
    r"(?:[\s,;&/]+|\s+and\s+|\s*tested\s*|\s*clear\s*|\s*normal\s*|:|-)+)+$",
    re.I,
)
JUNK_PHRASE_RE = re.compile(
    r"(current chat|please note|general care|ready to go hunting|"
    r"chat room users|get dns)",
    re.I,
)
US_CAN_STATES = {
    "alabama", "alaska", "arizona", "arkansas", "california", "colorado",
    "connecticut", "delaware", "florida", "georgia", "hawaii", "idaho",
    "illinois", "indiana", "iowa", "kansas", "kentucky", "louisiana",
    "maine", "maryland", "massachusetts", "michigan", "minnesota",
    "mississippi", "missouri", "montana", "nebraska", "nevada",
    "new hampshire", "new jersey", "new mexico", "new york",
    "north carolina", "north dakota", "ohio", "oklahoma", "oregon",
    "pennsylvania", "rhode island", "south carolina", "south dakota",
    "tennessee", "texas", "utah", "vermont", "virginia", "washington",
    "west virginia", "wisconsin", "wyoming", "ontario", "quebec",
    "british columbia", "alberta", "manitoba", "saskatchewan",
    "nova scotia", "new brunswick",
}
JUNK_KENNEL_NAMES = {
    "chat users", "get dns", "index", "index of dogs", "index of stud dogs",
    "introducing", "breeder archives", "untitled", "our dogs", "our gang",
    "pups", "stud dogs", "jrtca breeders directory and stud book",
    "jrtca stud book", "ready to race", "chance, scatter & shambles",
}
SCRAPE_INSERT_MIN_ID = 1263800


def fetch_bytes(url: str, retries: int = 4, timeout: int = 90) -> Optional[bytes]:
    for attempt in range(retries):
        try:
            req = urllib.request.Request(url, headers=UA)
            with urllib.request.urlopen(req, timeout=timeout) as resp:
                return resp.read()
        except Exception:
            time.sleep(1.5 * (attempt + 1))
    return None


def fetch_text(url: str) -> Optional[str]:
    data = fetch_bytes(url)
    if data is None:
        return None
    return data.decode("utf-8", errors="ignore")


def slug_from_url(url: str) -> str:
    path = urllib.parse.urlparse(html.unescape(url)).path.strip("/")
    path = path.replace("/", "_") or "home"
    return re.sub(r"[^\w.\-]+", "_", path)[:160]


def html_to_text(raw: str) -> str:
    text = BR_RE.sub("\n", raw)
    text = BLOCK_RE.sub("\n", text)
    text = TAG_RE.sub(" ", text)
    text = html.unescape(text)
    text = text.replace("\xa0", " ").replace("\u2022", " • ").replace("•", " • ")
    text = re.sub(r"[ \t]+", " ", text)
    text = re.sub(r"\n[ \t]+", "\n", text)
    text = re.sub(r"\n{3,}", "\n\n", text)
    return text.strip()


def normalize_name(name: str) -> str:
    if not name:
        return ""
    n = html.unescape(name)
    n = n.replace("’", "'").replace("`", "'")
    n = re.sub(r"\s+", " ", n).strip(" ,;.-")
    return n


def normalize_key(name: str) -> str:
    n = normalize_name(name).lower()
    n = re.sub(r"[^a-z0-9 ]+", "", n)
    return re.sub(r"\s+", " ", n).strip()


def frac_height(raw: str) -> str:
    s = raw.replace(" ", "")
    s = s.replace("½", ".5").replace("¼", ".25").replace("¾", ".75")
    s = s.replace("1/2", ".5").replace("1/4", ".25").replace("3/4", ".75")
    return s


@dataclass
class ParsedDog:
    name: str
    sex: Optional[str] = None
    sire: Optional[str] = None
    dam: Optional[str] = None
    dob: Optional[str] = None
    height: Optional[str] = None
    coat: Optional[str] = None
    color: Optional[str] = None
    call_name: Optional[str] = None
    titles: list[str] = field(default_factory=list)
    health_tests: list[str] = field(default_factory=list)
    co_owner: Optional[str] = None
    notes: list[str] = field(default_factory=list)
    photo_urls: list[str] = field(default_factory=list)
    photo_paths: list[str] = field(default_factory=list)
    source_url: str = ""
    source_snapshot: str = ""
    raw: str = ""


@dataclass
class ParsedBreeder:
    kennel_name: str
    slug: str
    location: str = ""
    city: str = ""
    state: str = ""
    owner_name: str = ""
    address: str = ""
    postal_code: str = ""
    email: str = ""
    phone: str = ""
    website: str = ""
    facebook: str = ""
    instagram: str = ""
    description: str = ""
    page_url: str = ""
    snapshot: str = ""
    photo_urls: list[str] = field(default_factory=list)
    photo_paths: list[str] = field(default_factory=list)
    dogs: list[ParsedDog] = field(default_factory=list)
    raw_text: str = ""


def clean_piece(s: str) -> str:
    s = normalize_name(s)
    s = re.sub(r"^[\s,;:\-–—•]+|[\s,;:\-–—•]+$", "", s)
    return s


def add_unique(bucket: list[str], value: str) -> None:
    v = clean_piece(value)
    if not v:
        return
    key = v.lower()
    if key not in {x.lower() for x in bucket}:
        bucket.append(v)


def extract_titles(text: str) -> list[str]:
    found: list[str] = []
    for m in TITLE_KEEP.finditer(text):
        add_unique(found, m.group(0))
    # Keep quarry-specific NHC even if regex clipped
    for m in re.finditer(r"NHC\s+to\s+[A-Za-z][\w\s/&'-]{1,40}", text, re.I):
        add_unique(found, m.group(0))
    for m in re.finditer(
        r"Natural Hunting Certificate[^\n.]{0,80}", text, re.I
    ):
        add_unique(found, m.group(0))
    for m in re.finditer(
        r"Bronze Medallion[^\n.]{0,80}", text, re.I
    ):
        add_unique(found, m.group(0))
    for m in re.finditer(
        r"Working Achievement(?: Award)?[^\n.]{0,80}", text, re.I
    ):
        add_unique(found, m.group(0))
    return found


def extract_health(text: str) -> list[str]:
    found: list[str] = []
    for m in HEALTH_RE.finditer(text):
        add_unique(found, m.group(0))
    return found


def looks_like_dog_name(line: str) -> bool:
    s = clean_piece(line)
    if not s or len(s) < 3 or len(s) > 80:
        return False
    if SKIP_NAME.search(s):
        return False
    if JUNK_NAME_RE.search(s) or EMAIL_RE.search(s) or PHONE_RE.search(s):
        return False
    if "<" in s or ">" in s or "http" in s.lower():
        return False
    if s.lower().startswith("website"):
        return False
    letters = re.sub(r"[^A-Za-z]", "", s)
    if len(letters) < 4:
        return False
    upper = sum(1 for c in letters if c.isupper())
    if NAME_LINE_RE.match(s) and upper >= max(3, int(0.7 * len(letters))):
        return True
    # Title-case kennel-style names that were in <strong>
    words = s.split()
    if 1 <= len(words) <= 8 and upper >= int(0.6 * len(letters)):
        return True
    return False


def is_junk_slug(slug: str) -> bool:
    s = (slug or "").lower()
    if s in SKIP_PAGES or s.startswith("jrtca-breeders"):
        return True
    if "studbook" in s or "index_of_dogs" in s or s.startswith("chat_") or "category_breeder" in s:
        return True
    if s in {"index.html", "home", "breeders.htm", "breeders_breeders.htm"}:
        return True
    return False


def is_junk_breeder(name: str, url: str = "") -> bool:
    n = (name or "").strip().lower()
    u = (url or "").lower()
    if "studbook" in u or "index_of_dogs" in u or "chat_" in u or "category_breeder" in u:
        return True
    if "/index.html" in u or u.rstrip("/").endswith("jrtcabreeders.com"):
        return True
    if n in JUNK_KENNEL_NAMES or "directory of breeders" in n or "code of ethics" in n:
        return True
    return False


def split_two_kennel_names(name: str, kennels: list[str]) -> list[str]:
    n = clean_piece(name)
    hits: list[tuple[int, int]] = []
    for k in sorted({clean_piece(x) for x in kennels if x}, key=len, reverse=True):
        if len(k) < 5:
            continue
        if k.lower() in JUNK_KENNEL_NAMES:
            continue
        for m in re.finditer(r"(?<![A-Za-z])" + re.escape(k) + r"\b", n, re.I):
            prefix = n[: m.start()].rstrip()
            if re.search(r"\bof(?:\s+the)?$", prefix, re.I):
                continue
            hits.append((m.start(), m.end()))
    hits = sorted(set(hits))
    picked: list[tuple[int, int]] = []
    last = -1
    for start, end in hits:
        if start >= last:
            picked.append((start, end))
            last = end
    if len(picked) >= 2 and picked[1][0] > 0:
        a = clean_piece(n[: picked[1][0]])
        b = clean_piece(n[picked[1][0] :])
        if (
            looks_like_dog_name(a)
            and looks_like_dog_name(b)
            and len(a.split()) >= 2
            and len(b.split()) >= 2
            and not re.search(r"\bof(?:\s+the)?$", a, re.I)
        ):
            return [a, b]
    return [n]


def split_paired_dog_names(name: str, kennels: Optional[list[str]] = None) -> list[str]:
    n = clean_piece(name).strip('"').strip()
    n = WELCOME_PREFIX_RE.sub("", n)
    n = re.sub(r"\s+and her daughter.*$", "", n, flags=re.I)
    n = re.sub(r"\s+and family\s*$", "", n, flags=re.I)
    m = re.search(r"\s+and introducing\s+", n, re.I)
    if m:
        a, b = clean_piece(n[: m.start()]), clean_piece(n[m.end() :])
        if looks_like_dog_name(a) and looks_like_dog_name(b):
            return [a, b]
    low = n.lower()
    if "/" in n and not re.search(r"\d/\d", n):
        if not any(k in low for k in ("mac's/jacks", "macs/jacks", "j & j", "r & b")):
            parts = [clean_piece(p) for p in n.split("/")]
            if len(parts) == 2 and all(looks_like_dog_name(p) for p in parts):
                return parts
    if kennels:
        split = split_two_kennel_names(n, kennels)
        if len(split) == 2:
            return split
    return [n]


def tidy_dog_name(name: str) -> tuple[str, str]:
    n = clean_piece(name)
    extra: list[str] = []
    dm = DATE_TAIL_RE.search(n)
    if dm:
        extra.append(dm.group(0).strip())
        n = clean_piece(n[: dm.start()])
    paren = re.search(r"\s*\(([^)]+)\)\s*$", n)
    if paren and re.search(r"NHC|WAA|BAER|CERF|PLL|co-?owned", paren.group(1), re.I):
        extra.append(paren.group(1))
        n = clean_piece(n[: paren.start()])
    base, rest = split_name_extras(n)
    if rest:
        extra.append(rest)
        n = base
    n = n.rstrip("?*").strip()
    return n, " ".join(extra)


def expand_listed_names(
    name: str, kennels: Optional[list[str]] = None
) -> list[tuple[str, str]]:
    out: list[tuple[str, str]] = []
    for piece in split_paired_dog_names(name, kennels):
        cleaned, extra = tidy_dog_name(piece)
        if cleaned:
            out.append((cleaned, extra))
    return out or [(clean_piece(name), "")]


def split_name_extras(line: str) -> tuple[str, str]:
    line = clean_piece(line)
    line = re.sub(r"^(latest addition|introducing)\s*:?\s+", "", line, flags=re.I)
    line = re.sub(r"\s+", " ", line)
    # Name is typically the leading CAPS phrase before a comma or height/title
    m = re.match(
        r"^([A-Z0-9][A-Z0-9'’\-\./& ]{1,70}?)(?:,\s+|\s+[–—-]\s+)(.+)$",
        line,
    )
    if m and looks_like_dog_name(m.group(1)):
        return clean_piece(m.group(1)), clean_piece(m.group(2))
    # "NAME 12½" without comma
    hm = HEIGHT_RE.search(line)
    if hm and hm.start() > 3:
        left = clean_piece(line[: hm.start()])
        if looks_like_dog_name(left):
            return left, clean_piece(line[hm.start() :])
    return line, ""


def apply_detail_text(dog: ParsedDog, text: str) -> None:
    if not text:
        return
    t = clean_piece(html.unescape(text))
    if not t:
        return
    cm = CALL_RE.search(t)
    if cm:
        dog.call_name = clean_piece(cm.group(1))
    co = COOWN_RE.search(t)
    if co:
        dog.co_owner = clean_piece(co.group(1).rstrip(")."))
    dm = DOB_RE.search(t)
    if dm:
        dog.dob = clean_piece(dm.group(1))
    if not dog.height:
        hm = HEIGHT_RE.search(t)
        if hm:
            dog.height = frac_height(hm.group(1))
    if not dog.coat:
        km = COAT_RE.search(t)
        if km:
            dog.coat = clean_piece(km.group(1).replace("lighlty", "lightly")).title()
    if not dog.color:
        cl = COLOR_RE.search(t)
        if cl:
            dog.color = re.sub(r"\s+", "", cl.group(1), flags=re.I)
            dog.color = dog.color.replace("Tri-Color", "Tricolor").replace("tricolor", "Tricolor")
            if "/" in cl.group(1) or "and" in cl.group(1).lower():
                dog.color = re.sub(r"\s+", "", cl.group(1).title().replace("And", "/"))
                dog.color = dog.color.replace("Tan/White", "Tan/White").replace("Black/White", "Black/White")
            else:
                dog.color = cl.group(1).title().replace("Tri-Color", "Tricolor")
    sire_dam = SIRE_DAM_RE.match(t) or SIRE_DAM_RE.search(t)
    if sire_dam and not dog.sire:
        dog.sire = clean_piece(sire_dam.group(1))
        dog.dam = clean_piece(sire_dam.group(2))
        t = clean_piece(sire_dam.group(3) or "") or t
    byout = BY_OUT_RE.search(t)
    if byout and not dog.sire:
        dog.sire = clean_piece(byout.group(1))
        dog.dam = clean_piece(byout.group(2))
    for title in extract_titles(t):
        add_unique(dog.titles, title)
    for ht in extract_health(t):
        add_unique(dog.health_tests, ht)
    # Keep the original leftover as notes unless it is only already-structured bits
    leftover = t
    leftover = CALL_RE.sub("", leftover)
    leftover = COOWN_RE.sub("", leftover)
    leftover = SIRE_DAM_RE.sub("", leftover)
    leftover = BY_OUT_RE.sub("", leftover)
    leftover = HEIGHT_RE.sub("", leftover)
    leftover = COAT_RE.sub("", leftover)
    leftover = COLOR_RE.sub("", leftover)
    leftover = re.sub(r"\b(full siblings?)\b", "", leftover, flags=re.I)
    leftover = JUNK_NOTE_RE.sub("", leftover)
    leftover = clean_piece(re.sub(r"[\s,;:/•]+", " ", leftover))
    if EMAIL_RE.search(leftover) or leftover.lower().startswith("visit our"):
        leftover = ""
    skip_leftover = leftover.lower() in {
        "",
        "standing at stud to approved bitches",
        "and",
        "x",
    }
    # Always keep award/working sentences in notes even if also in titles
    if TITLE_KEEP.search(t) or re.search(
        r"NHC|Bronze|Working Achievement|Champion|Championship|quarry|Groundhog|Raccoon|NHC to",
        t,
        re.I,
    ):
        add_unique(dog.notes, t)
    elif leftover and not skip_leftover and len(leftover) > 2:
        add_unique(dog.notes, leftover)


def extract_images(raw_html: str) -> list[tuple[str, str]]:
    out: list[tuple[str, str]] = []
    for m in re.finditer(
        r"<img[^>]+>", raw_html, re.I
    ):
        tag = m.group(0)
        src = re.search(r'data-src\s*=\s*["\']([^"\']+)', tag, re.I) or re.search(
            r'src\s*=\s*["\']([^"\']+)', tag, re.I
        )
        if not src:
            continue
        url = html.unescape(src.group(1))
        if SKIP_IMG.search(url):
            continue
        if url.startswith("data:"):
            continue
        title = ""
        tm = re.search(r'title\s*=\s*["\']([^"\']+)', tag, re.I)
        am = re.search(r'alt\s*=\s*["\']([^"\']+)', tag, re.I)
        if tm:
            title = html.unescape(tm.group(1))
        elif am:
            title = html.unescape(am.group(1))
        out.append((url, title))
    # widget titles after images
    for m in re.finditer(
        r'<h3 class="widget-title">([^<]+)</h3>', raw_html, re.I
    ):
        title = html.unescape(m.group(1)).strip()
        if title and title.lower() not in {"contact information", ""}:
            if out and not out[-1][1]:
                out[-1] = (out[-1][0], title)
    return out


def parse_city_state(location: str) -> tuple[str, str]:
    loc = clean_piece(location)
    m = re.search(
        r"^(?P<city>.+?)(?:,|\s+)\s*(?P<state>[A-Z]{2}|[A-Za-z][A-Za-z ]+)$",
        loc,
    )
    if not m:
        return loc, ""
    city, state = m.group("city").strip(), m.group("state").strip()
    aliases = {
        "wisconsin": "WI",
        "texas": "TX",
        "new jersey": "NJ",
        "north carolina": "NC",
        "west virginia": "WV",
        "oregon": "OR",
        "colorado": "CO",
        "arizona": "AZ",
        "california": "CA",
        "georgia": "GA",
        "oklahoma": "OK",
        "massachusetts": "MA",
        "michigan": "MI",
        "mississippi": "MS",
        "missouri": "MO",
        "nebraska": "NE",
        "florida": "FL",
        "pennsylvania": "PA",
        "tennessee": "TN",
        "virginia": "VA",
        "washington": "WA",
        "iowa": "IA",
        "arkansas": "AR",
        "wyoming": "WY",
        "new york": "NY",
    }
    if len(state) > 2:
        state = aliases.get(state.lower(), state)
    return city, state.upper() if len(state) == 2 else state


def parse_contact(block: str, breeder: ParsedBreeder) -> None:
    lines = [clean_piece(x) for x in block.splitlines() if clean_piece(x)]
    lines = [
        x
        for x in lines
        if x.lower()
        not in {"contact information", "contact breeder", "find us on facebook!"}
    ]
    if not lines:
        return
    if not breeder.owner_name:
        for line in lines:
            if EMAIL_RE.search(line) or PHONE_RE.search(line):
                continue
            if looks_like_dog_name(line) or HEIGHT_RE.search(line):
                continue
            if re.search(r"\d{5}", line) or line.lower().startswith("visit"):
                continue
            words = line.replace("&", " ").split()
            if 2 <= len(words) <= 6:
                breeder.owner_name = line
                break
    for line in lines:
        em = EMAIL_RE.search(line)
        if em and not breeder.email:
            breeder.email = em.group(0)
        ph = PHONE_RE.search(line)
        if ph and not breeder.phone:
            breeder.phone = ph.group(0).replace(" ", "")
            if "/" in ph.group(0):
                breeder.phone = ph.group(0)
        if re.search(r"\bwebsite\s*:", line, re.I) or re.search(
            r"https?://|wixsite|facebook\.com|www\.", line, re.I
        ):
            wm = re.search(r"(https?://\S+|www\.\S+|[\w.-]+\.(?:com|net|org)\S*)", line, re.I)
            if wm:
                url = wm.group(1).rstrip(").,")
                if "facebook" in url.lower():
                    breeder.facebook = url
                elif "instagram" in url.lower():
                    breeder.instagram = url
                elif not breeder.website:
                    breeder.website = url
        if "facebook" in line.lower() and not breeder.facebook:
            fm = re.search(r"(facebook\.com/\S+)", line, re.I)
            if fm:
                breeder.facebook = fm.group(1)
        sm = ST_RE.search(line)
        if sm:
            st = sm.group(1)
            if len(st) > 2:
                _, st = parse_city_state("x, " + st)
            if not breeder.state:
                breeder.state = st
            if sm.group(2):
                breeder.postal_code = sm.group(2)
            left = line[: sm.start()].strip(" •,")
            # "street • City" or "City"
            if "•" in left:
                addr, city = [x.strip() for x in left.split("•", 1)]
                if not breeder.address and 4 < len(addr) <= 80:
                    breeder.address = addr
                if not breeder.city and len(city) <= 80:
                    breeder.city = city
            else:
                # street then city before comma
                parts = [p.strip() for p in left.split(",") if p.strip()]
                if len(parts) >= 2:
                    addr = ", ".join(parts[:-1])
                    if not breeder.address and 4 < len(addr) <= 80:
                        breeder.address = addr
                    if not breeder.city and len(parts[-1]) <= 80:
                        breeder.city = parts[-1]
                elif parts and not breeder.city and not re.search(r"\d", parts[0]) and len(parts[0]) <= 80:
                    breeder.city = parts[0]
                elif parts and re.search(r"\d", parts[0]) and not breeder.address and 4 < len(parts[0]) <= 80:
                    breeder.address = parts[0]
        elif re.search(r"\d", line) and "•" in line and not breeder.address and len(line) <= 100:
            left, right = [x.strip() for x in line.split("•", 1)]
            if 4 < len(left) <= 80:
                breeder.address = left
            c, s = parse_city_state(right)
            if c and len(c) <= 80:
                breeder.city = c
            if s:
                breeder.state = s


def extract_strong_blocks(raw_html: str) -> list[tuple[str, str]]:
    """Return (strong_name, following_text) pairs from kennel body HTML."""
    pairs: list[tuple[str, str]] = []
    for m in re.finditer(
        r"<strong>(.*?)</strong>(.*?)(?=<strong>|contact information|</div></div></div></div>)",
        raw_html,
        re.I | re.S,
    ):
        name = clean_piece(html_to_text(m.group(1)))
        rest = html_to_text(m.group(2))
        if name:
            pairs.append((name, rest))
    return pairs


def kennel_from_slug(slug: str) -> str:
    s = re.sub(r"\.html?$", "", slug, flags=re.I)
    s = re.sub(r"^(breeders_)+", "", s, flags=re.I)
    s = s.replace("_", " ").strip()
    words = s.split()
    if len(words) >= 2 and words[-1].lower().replace(" ", "") == words[-2].lower().replace(" ", ""):
        words = words[:-1]
    if words and words[-1].lower() in {"htm", "html"}:
        words = words[:-1]
    return " ".join(w if w.isupper() or "-" in w else w.title() for w in words)


def is_directory_page(slug: str, raw_html: str) -> bool:
    s = slug.lower().replace(".html", "").replace(".htm", "")
    if s in {"home", "breeders", "breeders_breeders", "jrtca-breeders-by-state"}:
        return True
    if s.endswith("breeders") and raw_html.lower().count("breeders/") >= 8:
        return True
    return False


def is_classic_ad(raw_html: str) -> bool:
    if "entry-content" in raw_html or "textwidget" in raw_html:
        return False
    if not re.search(r"<table", raw_html, re.I):
        return False
    return bool(re.search(r"<b[^>]*>\s*[A-Z][A-Z0-9'’\-\./& ]{2,}", raw_html, re.I))


def parse_classic_ad(
    raw_html: str,
    kennel_name: str,
    slug: str,
    page_url: str,
    snapshot: str = "",
) -> ParsedBreeder:
    title_m = re.search(r'<img[^>]+(?:alt|title)="([^"]+)"[^>]*banner', raw_html, re.I)
    if not title_m:
        title_m = re.search(r'ID="Banner\d+"[^>]+(?:alt|title)="([^"]+)"', raw_html, re.I)
    if title_m and title_m.group(1).strip():
        kennel_name = html.unescape(title_m.group(1)).strip()
    elif slug:
        derived = kennel_from_slug(slug)
        if derived:
            kennel_name = derived
    b = ParsedBreeder(
        kennel_name=kennel_name,
        slug=slug,
        page_url=page_url,
        snapshot=snapshot,
        raw_text=html_to_text(raw_html),
    )
    loc_m = CLASSIC_LOC_RE.search(raw_html)
    if loc_m:
        b.location = clean_piece(html.unescape(loc_m.group(1)))
        b.city, b.state = parse_city_state(b.location)
    if not b.location:
        loc2 = re.search(
            r'<p align="center"><font size="\+1"[^>]*>([^<]+)</font></p>',
            raw_html,
            re.I,
        )
        if loc2:
            b.location = clean_piece(html.unescape(loc2.group(1)))
            b.city, b.state = parse_city_state(b.location)

    desc_m = re.search(
        r'<p(?![^>]*align="center")[^>]*>\s*<font size="-1"[^>]*>(.*?)</font></p>',
        raw_html,
        re.I | re.S,
    )
    if desc_m:
        b.description = clean_piece(html_to_text(desc_m.group(1)))

    current_sex: Optional[str] = None
    for m in CLASSIC_BOLD_RE.finditer(raw_html):
        raw_names = [
            clean_piece(html_to_text(x))
            for x in re.split(r"<br\s*/?>", m.group(1), flags=re.I)
        ]
        raw_names = [n for n in raw_names if n]
        rest = html_to_text(m.group(2) or "")
        if not raw_names:
            continue
        if len(raw_names) > 1:
            for name in raw_names:
                if not looks_like_dog_name(name) or re.search(r"\b(pups?|puppies)\b", name, re.I):
                    continue
                b.dogs.append(
                    ParsedDog(
                        name=name,
                        sex=current_sex,
                        source_url=page_url,
                        source_snapshot=snapshot,
                        raw=name,
                    )
                )
            continue
        name = raw_names[0]
        if re.search(r"\b(pups?|puppies)\b", name, re.I):
            continue
        if SECTION_HDR.match(name) or name.lower() in {"at stud", "the girls", "the boys", "introducing"}:
            for rx, val in SECTION_SEX:
                if rx.search(name) or rx.search(rest[:40]):
                    current_sex = val
            continue
        if not looks_like_dog_name(name):
            continue
        name, extras = split_name_extras(name)
        d = ParsedDog(
            name=name,
            sex=current_sex,
            source_url=page_url,
            source_snapshot=snapshot,
            raw=clean_piece(name + " " + rest),
        )
        apply_detail_text(d, extras)
        apply_detail_text(d, rest)
        if d.sire is None:
            sm = SIRE_DAM_RE.search(rest)
            if sm:
                d.sire = clean_piece(sm.group(1))
                d.dam = clean_piece(sm.group(2))
        b.dogs.append(d)

    # Contact block: last mailto + nearby text
    mail = re.search(r'href="mailto:([^"]+)"', raw_html, re.I)
    if mail and not b.email:
        b.email = html.unescape(mail.group(1))
    web = re.search(
        r'Visit our Website.*?<a href="(https?://[^"]+)"', raw_html, re.I | re.S
    )
    if web and not b.website:
        b.website = html.unescape(web.group(1))
    # owner/address paragraph near mailto
    if mail:
        around = raw_html[max(0, mail.start() - 800) : mail.end() + 200]
        parse_contact(html_to_text(around), b)
    if not b.owner_name:
        om = re.search(
            r'<b><font[^>]*>([A-Z][A-Za-z .\'&/-]{3,60})<br>',
            raw_html,
            re.I,
        )
        if om and not looks_like_dog_name(om.group(1)):
            b.owner_name = clean_piece(html.unescape(om.group(1)))

    for url, title in extract_images(raw_html):
        if any(x in url.lower() for x in ("clearpixel", "decal", "banner", "navigation", "button")):
            continue
        add_unique(b.photo_urls, url)
    return b


def parse_breeder_html(
    raw_html: str,
    kennel_name: str,
    slug: str,
    page_url: str,
    snapshot: str = "",
) -> ParsedBreeder:
    b = ParsedBreeder(
        kennel_name=kennel_name,
        slug=slug,
        page_url=page_url,
        snapshot=snapshot,
    )
    # Prefer inner content
    raw_html = raw_html or ""
    if is_directory_page(slug, raw_html):
        return ParsedBreeder(kennel_name=kennel_name, slug=slug, page_url=page_url, snapshot=snapshot)
    if is_classic_ad(raw_html):
        return parse_classic_ad(raw_html, kennel_name, slug, page_url, snapshot)
    content_m = re.search(
        r'(<div class="entry-content".*?)(?:<!-- \.entry-content -->|<footer)',
        raw_html,
        re.I | re.S,
    )
    body = (content_m.group(1) if content_m else raw_html) or ""
    # First widget title is usually city, state
    titles = re.findall(r'<h3 class="widget-title">([^<]*)</h3>', body, re.I)
    loc = next((html.unescape(t).strip() for t in titles if t.strip() and t.strip().lower() not in {"contact information"}), "")
    if loc and not STOP_HEADERS.search(loc) and len(loc) < 80:
        b.location = loc
        b.city, b.state = parse_city_state(loc)

    text = html_to_text(body)
    b.raw_text = text
    if "Contact Information" in text:
        desc, contact = text.split("Contact Information", 1)
    else:
        desc, contact = text, ""
    parse_contact(contact, b)

    # Description = prose before first dog/section
    desc_lines = []
    for line in desc.splitlines():
        s = clean_piece(line)
        if not s:
            if desc_lines and any(looks_like_dog_name(x) for x in desc_lines[-3:]):
                break
            continue
        if SECTION_HDR.match(s) or looks_like_dog_name(s):
            break
        if STOP_HEADERS.search(s):
            break
        desc_lines.append(s)
    b.description = " ".join(desc_lines)

    current_sex: Optional[str] = None
    current: Optional[ParsedDog] = None
    dogs: list[ParsedDog] = []

    def flush() -> None:
        nonlocal current
        if current and current.name:
            dogs.append(current)
        current = None

    lines = [clean_piece(x) for x in desc.splitlines()]
    i = 0
    while i < len(lines):
        line = lines[i]
        i += 1
        if not line:
            continue
        if STOP_HEADERS.search(line):
            break
        if SECTION_HDR.match(line) and not HEIGHT_RE.search(line):
            flush()
            sex = None
            for rx, val in SECTION_SEX:
                if rx.search(line):
                    sex = val
                    break
            if "introduc" in line.lower():
                current_sex = current_sex  # keep prior if any; introducing is mixed
            elif sex:
                current_sex = sex
            continue
        name, extras = split_name_extras(line)
        if looks_like_dog_name(name) and (
            extras
            or (i <= len(lines) and (i == len(lines) or not SECTION_HDR.match(lines[i] if i < len(lines) else "")))
        ):
            # Avoid treating owner/address as dogs
            if EMAIL_RE.search(line) or PHONE_RE.search(line):
                continue
            flush()
            current = ParsedDog(
                name=name,
                sex=current_sex,
                source_url=page_url,
                source_snapshot=snapshot,
                raw=line,
            )
            apply_detail_text(current, extras)
            # pull following continuation lines
            while i < len(lines):
                nxt = lines[i]
                if not nxt:
                    i += 1
                    # one blank is ok
                    if i < len(lines) and lines[i] and not looks_like_dog_name(split_name_extras(lines[i])[0]):
                        continue
                    break
                nxt_name, nxt_ex = split_name_extras(nxt)
                if looks_like_dog_name(nxt_name) and (
                    nxt_ex or SIRE_DAM_RE.search(nxt) is None
                ) and not SIRE_DAM_RE.search(nxt) and not BY_OUT_RE.search(nxt):
                    # next dog
                    break
                if SECTION_HDR.match(nxt) and not HEIGHT_RE.search(nxt):
                    break
                if STOP_HEADERS.search(nxt):
                    break
                apply_detail_text(current, nxt)
                current.raw = (current.raw + " | " + nxt).strip(" |")
                i += 1
            continue
        if current:
            apply_detail_text(current, line)
            current.raw = (current.raw + " | " + line).strip(" |")
    flush()

    # Strong-tag pass fills gaps / catches dogs missed in plaintext
    for strong_name, rest in extract_strong_blocks(body):
        name, extras = split_name_extras(strong_name)
        if not looks_like_dog_name(name):
            continue
        existing = next((d for d in dogs if normalize_key(d.name) == normalize_key(name)), None)
        if existing:
            apply_detail_text(existing, extras)
            for piece in rest.splitlines():
                apply_detail_text(existing, piece)
            continue
        d = ParsedDog(
            name=name,
            sex=current_sex,
            source_url=page_url,
            source_snapshot=snapshot,
            raw=strong_name + " " + rest,
        )
        apply_detail_text(d, extras)
        for piece in rest.splitlines()[:8]:
            if SECTION_HDR.match(piece) or STOP_HEADERS.search(piece):
                break
            apply_detail_text(d, piece)
        dogs.append(d)

    # Images / captions often hold extra dogs or extra notes
    images = extract_images(body)
    b.photo_urls = [u for u, _ in images]
    for url, title in images:
        if not title or SKIP_IMG.search(title) or title.lower() in {"jrtca", "jrtca logo"}:
            continue
        tname, textra = split_name_extras(title.split("(")[0])
        matched = None
        for d in dogs:
            if normalize_key(d.name) and normalize_key(d.name) in normalize_key(title):
                matched = d
                break
        if matched:
            apply_detail_text(matched, title)
            if url not in matched.photo_urls:
                matched.photo_urls.append(url)
        elif looks_like_dog_name(tname):
            d = ParsedDog(
                name=tname,
                source_url=page_url,
                source_snapshot=snapshot,
                raw=title,
                photo_urls=[url],
            )
            apply_detail_text(d, title)
            if "(" in title:
                apply_detail_text(d, title[title.find("(") :])
            dogs.append(d)

    # Dedup dogs by name, merge notes
    merged: dict[str, ParsedDog] = {}
    for d in dogs:
        key = normalize_key(d.name)
        if not key:
            continue
        if key in merged:
            a = merged[key]
            for attr in ("sex", "sire", "dam", "dob", "height", "coat", "color", "call_name", "co_owner"):
                if not getattr(a, attr) and getattr(d, attr):
                    setattr(a, attr, getattr(d, attr))
            for lst in ("titles", "health_tests", "notes", "photo_urls"):
                for item in getattr(d, lst):
                    add_unique(getattr(a, lst), item)
            if d.raw and d.raw not in a.raw:
                a.raw = (a.raw + " | " + d.raw).strip(" |")
        else:
            merged[key] = d
    b.dogs = list(merged.values())
    return b


def wp_api_all(kind: str) -> list[dict]:
    cache = API / f"{kind}.json"
    if cache.exists():
        return json.loads(cache.read_text(encoding="utf-8"))
    items: list[dict] = []
    page = 1
    while True:
        url = (
            f"{LIVE_HOST}/wp-json/wp/v2/{kind}?per_page=100&page={page}"
            "&_fields=id,slug,title,link,content,date,modified"
        )
        req = urllib.request.Request(url, headers=UA)
        try:
            with urllib.request.urlopen(req, timeout=60) as resp:
                batch = json.loads(resp.read().decode("utf-8", errors="ignore"))
        except urllib.error.HTTPError as e:
            if e.code in (400, 404):
                break
            raise
        if not batch:
            break
        items.extend(batch)
        if len(batch) < 100:
            break
        page += 1
    cache.write_text(json.dumps(items, indent=2), encoding="utf-8")
    return items


def save_live_page(url: str) -> Path:
    slug = slug_from_url(url)
    path = PAGES_LIVE / f"{slug}.html"
    if path.exists() and path.stat().st_size > 500:
        return path
    text = fetch_text(url)
    if text:
        path.write_text(text, encoding="utf-8")
        time.sleep(0.2)
    return path


def cdx_rows() -> list[list[str]]:
    path = API / "cdx.json"
    if not path.exists():
        return []
    data = json.loads(path.read_text(encoding="utf-8"))
    if not data:
        return []
    return data[1:] if data[0] and data[0][0] == "timestamp" else data


def unique_snapshots(rows: list[list[str]]) -> list[tuple[str, str, str]]:
    """(timestamp, original_url, digest) unique by digest+url path."""
    skip = re.compile(
        r"/wp-(?:json|content|includes|admin|login)|/feed|/xmlrpc|/comments|"
        r"/page/\d+|/\?s=|/tag/|/author/",
        re.I,
    )
    seen_digest: set[str] = set()
    out: list[tuple[str, str, str]] = []
    for row in rows:
        if len(row) < 5:
            continue
        ts, original, _mt, _st, digest = row[:5]
        parsed = urllib.parse.urlparse(original)
        path = parsed.path.lower().rstrip("/")
        if skip.search(original) or skip.search(path):
            continue
        slug = path.strip("/").split("/")[-1] if path else "home"
        if slug in SKIP_PAGES:
            continue
        key = f"{digest}|{path}"
        if key in seen_digest:
            continue
        seen_digest.add(key)
        out.append((ts, original, digest))
    return out


def save_archive_page(ts: str, original: str) -> Optional[Path]:
    slug = slug_from_url(original)
    path = PAGES_ARCHIVE / f"{ts}_{slug}.html"
    if path.exists() and path.stat().st_size > 200:
        return path
    wb = f"https://web.archive.org/web/{ts}id_/{original}"
    text = fetch_text(wb)
    if not text:
        wb = f"https://web.archive.org/web/{ts}/{original}"
        text = fetch_text(wb)
    if text:
        path.write_text(text, encoding="utf-8")
        time.sleep(0.4)
        return path
    return None


def safe_filename(s: str) -> str:
    s = re.sub(r"[^\w.\-]+", "_", s.strip(), flags=re.U)
    return s.strip("_")[:140] or "photo"


def download_photo(url: str, kennel: str, dog: str = "") -> Optional[str]:
    if not url or SKIP_IMG.search(url):
        return None
    # unwrap archive im_
    m = re.search(r"/web/\d+(?:im_)?/(.+)$", url)
    live = url
    if "web.archive.org" in url and m:
        live = m.group(1)
        if not live.startswith("http"):
            live = "https://" + live
    ext = Path(urllib.parse.urlparse(live.split("?")[0]).path).suffix.lower()
    if ext not in {".jpg", ".jpeg", ".png", ".gif", ".webp"}:
        ext = ".jpg"
    label = safe_filename(kennel)
    if dog:
        label += "__" + safe_filename(dog)
    base = Path(urllib.parse.urlparse(live).path).name
    dest = PHOTOS / f"{label}__{safe_filename(base) or 'img'}{ext if '.' not in base else ''}"
    if dest.suffix == "":
        dest = dest.with_suffix(ext)
    if dest.exists() and dest.stat().st_size > 0:
        return str(dest.relative_to(ROOT.parent))
    data = fetch_bytes(live) or fetch_bytes(url)
    if not data:
        return None
    dest.write_bytes(data)
    return str(dest.relative_to(ROOT.parent))


def merge_breeders(items: list[ParsedBreeder]) -> list[ParsedBreeder]:
    by_slug: dict[str, ParsedBreeder] = {}
    for b in items:
        key = b.slug.lower()
        if key not in by_slug:
            by_slug[key] = b
            continue
        a = by_slug[key]
        # Prefer live (no snapshot) for contact; keep historic dogs
        if not a.owner_name and b.owner_name:
            for attr in (
                "owner_name",
                "address",
                "city",
                "state",
                "postal_code",
                "email",
                "phone",
                "website",
                "facebook",
                "location",
                "description",
            ):
                if not getattr(a, attr) and getattr(b, attr):
                    setattr(a, attr, getattr(b, attr))
        # merge dogs
        have = {normalize_key(d.name): d for d in a.dogs}
        for d in b.dogs:
            k = normalize_key(d.name)
            if k in have:
                x = have[k]
                for attr in ("sex", "sire", "dam", "dob", "height", "coat", "color", "call_name", "co_owner"):
                    if not getattr(x, attr) and getattr(d, attr):
                        setattr(x, attr, getattr(d, attr))
                for lst in ("titles", "health_tests", "notes", "photo_urls"):
                    for item in getattr(d, lst):
                        add_unique(getattr(x, lst), item)
                if d.raw and d.raw not in x.raw:
                    x.raw = (x.raw + " | " + d.raw).strip(" |")
            else:
                a.dogs.append(d)
                have[k] = d
    return list(by_slug.values())


def collect_live() -> list[ParsedBreeder]:
    parsed: list[ParsedBreeder] = []
    posts = wp_api_all("posts")
    pages = wp_api_all("pages")
    for item in posts + pages:
        link = item.get("link") or ""
        slug = item.get("slug") or slug_from_url(link)
        path = save_live_page(link)
        title = html.unescape(item.get("title", {}).get("rendered", slug))
        content = item.get("content", {}).get("rendered", "")
        raw = path.read_text(encoding="utf-8", errors="ignore") if path.exists() else (content or "")
        if slug in SKIP_PAGES or slug.startswith("jrtca-breeders"):
            continue
        if "/category/" in link:
            continue
        body = raw if "<strong>" in raw or "textwidget" in raw else f"<div class='entry-content'>{content}</div>"
        p = parse_breeder_html(body, title, slug, link, "")
        if p.dogs or p.owner_name:
            parsed.append(p)
            print(f"  live {slug}: {len(p.dogs)} dogs, owner={p.owner_name!r}")
    return parsed


def collect_archive() -> list[ParsedBreeder]:
    parsed: list[ParsedBreeder] = []
    rows = cdx_rows()
    snaps = unique_snapshots(rows)
    print(f"archive unique snapshots: {len(snaps)} (from {len(rows)} CDX rows)")
    for i, (ts, original, _digest) in enumerate(snaps, 1):
        path = save_archive_page(ts, original)
        if not path:
            continue
        slug = slug_from_url(original)
        if slug in SKIP_PAGES or slug.startswith("jrtca-breeders"):
            continue
        raw = path.read_text(encoding="utf-8", errors="ignore")
        title_m = re.search(r"<title>([^<]+)</title>", raw, re.I)
        title = html.unescape(title_m.group(1)).split("–")[0].split("-")[0].strip() if title_m else slug
        p = parse_breeder_html(raw, title, slug, original, ts)
        if p.dogs or p.owner_name:
            parsed.append(p)
            print(f"  arch {i}/{len(snaps)} {ts} {slug}: {len(p.dogs)} dogs")
        elif i % 50 == 0:
            print(f"  arch {i}/{len(snaps)} saved {slug}")
    return parsed


def collect() -> list[ParsedBreeder]:
    return merge_breeders(collect_live() + collect_archive())


def _archive_manifest_path() -> Path:
    return API / "archive_parsed_files.json"


def load_archive_manifest() -> set[str]:
    path = _archive_manifest_path()
    if not path.exists():
        return set()
    try:
        return set(json.loads(path.read_text(encoding="utf-8")))
    except Exception:
        return set()


def save_archive_manifest(done: set[str]) -> None:
    _archive_manifest_path().write_text(
        json.dumps(sorted(done), indent=2), encoding="utf-8"
    )


def _ok_to_insert_dog(d: ParsedDog, b: ParsedBreeder) -> bool:
    """Insert unmatched dogs, but skip directory-list junk and health-test leftovers."""
    if not d.name or not looks_like_dog_name(d.name):
        return False
    if JUNK_NAME_RE.search(d.name) or PHONE_RE.search(d.name):
        return False
    if normalize_key(d.name) == normalize_key(b.kennel_name):
        return False
    slug = (b.slug or "").lower()
    directory_page = slug in {"home"} or "breeders.htm" in slug or slug.endswith("breeders")
    if directory_page and not b.owner_name and not d.sire and not d.dam:
        return False
    return True


def parse_existing_archive_files(
    min_age_sec: float = 3.0, force: bool = False
) -> tuple[list[ParsedBreeder], int]:
    """Parse archive HTML already on disk. Skips files still being written."""
    done = set() if force else load_archive_manifest()
    parsed: list[ParsedBreeder] = []
    now = time.time()
    files = sorted(PAGES_ARCHIVE.glob("*.html"))
    new_count = 0
    for path in files:
        if path.name in done:
            continue
        try:
            st = path.stat()
        except OSError:
            continue
        if st.st_size < 200 or (now - st.st_mtime) < min_age_sec:
            continue
        name = path.stem
        ts = name[:14] if len(name) >= 14 and name[:14].isdigit() else ""
        slug = name[15:] if ts and name[14:15] == "_" else name
        if is_junk_slug(slug) or slug in SKIP_PAGES or slug.startswith("jrtca-breeders"):
            done.add(path.name)
            continue
        raw = path.read_text(encoding="utf-8", errors="ignore")
        title_m = re.search(r"<title>([^<]+)</title>", raw, re.I)
        title = (
            html.unescape(title_m.group(1)).split("–")[0].split("-")[0].strip()
            if title_m
            else slug
        )
        original = f"https://www.jrtcabreeders.com/{slug}/" if slug != "home" else LIVE_HOST + "/"
        p = parse_breeder_html(raw, title, slug, original, ts)
        if p.dogs or p.owner_name:
            parsed.append(p)
            print(f"  disk {path.name}: {len(p.dogs)} dogs owner={p.owner_name!r}")
        done.add(path.name)
        new_count += 1
    save_archive_manifest(done)
    return parsed, new_count


def download_all_photos(breeders: list[ParsedBreeder]) -> None:
    for b in breeders:
        for url in b.photo_urls:
            dest = download_photo(url, b.kennel_name)
            if dest:
                add_unique(b.photo_paths, dest)
        for d in b.dogs:
            for url in d.photo_urls:
                dest = download_photo(url, b.kennel_name, d.name)
                if dest:
                    add_unique(d.photo_paths, dest)
            if not d.photo_paths and b.photo_paths and len(b.dogs) == 1:
                d.photo_paths = list(b.photo_paths)


def get_conn() -> pyodbc.Connection:
    for driver in (
        "ODBC Driver 17 for SQL Server",
        "ODBC Driver 18 for SQL Server",
        "SQL Server Native Client 11.0",
        "SQL Server",
    ):
        try:
            return pyodbc.connect(
                f"DRIVER={{{driver}}};SERVER=localhost\\SQLEXPRESS;"
                "DATABASE=TrialResults;Trusted_Connection=yes;",
                timeout=10,
            )
        except pyodbc.Error:
            continue
    raise RuntimeError("Could not connect to TrialResults")


def ensure_schema(cur: pyodbc.Cursor) -> None:
    cur.execute(
        """
        IF OBJECT_ID('sResults.Breeder','U') IS NULL
        CREATE TABLE sResults.Breeder (
            BreederID INT IDENTITY(1,1) NOT NULL PRIMARY KEY,
            KennelName NVARCHAR(255) NOT NULL,
            KennelPrefix NVARCHAR(100) NULL,
            OwnerName NVARCHAR(255) NULL,
            Address NVARCHAR(255) NULL,
            City NVARCHAR(100) NULL,
            State NVARCHAR(50) NULL,
            PostalCode NVARCHAR(20) NULL,
            Email NVARCHAR(255) NULL,
            Phone NVARCHAR(100) NULL,
            Website NVARCHAR(500) NULL,
            Facebook NVARCHAR(500) NULL,
            Instagram NVARCHAR(500) NULL,
            Location NVARCHAR(255) NULL,
            Description NVARCHAR(MAX) NULL,
            PhotoPath NVARCHAR(1000) NULL,
            SourceURL NVARCHAR(500) NULL,
            SourceSnapshot NVARCHAR(30) NULL,
            Notes NVARCHAR(MAX) NULL
        );
        """
    )
    alters = [
        ("Dog", "DateOfBirth", "DATE NULL"),
        ("Dog", "Height", "NVARCHAR(50) NULL"),
        ("Dog", "Coat", "NVARCHAR(80) NULL"),
        ("Dog", "Color", "NVARCHAR(80) NULL"),
        ("Dog", "CallName", "NVARCHAR(100) NULL"),
        ("Dog", "Titles", "NVARCHAR(MAX) NULL"),
        ("Dog", "HealthTests", "NVARCHAR(MAX) NULL"),
        ("Dog", "CoOwner", "NVARCHAR(255) NULL"),
        ("Dog", "Notes", "NVARCHAR(MAX) NULL"),
        ("Dog", "PhotoPath", "NVARCHAR(1000) NULL"),
        ("Dog", "SourceURL", "NVARCHAR(500) NULL"),
        ("Dog", "BreederID", "INT NULL"),
        ("Owner", "Address", "NVARCHAR(255) NULL"),
        ("Owner", "City", "NVARCHAR(100) NULL"),
        ("Owner", "State", "NVARCHAR(50) NULL"),
        ("Owner", "PostalCode", "NVARCHAR(20) NULL"),
        ("Owner", "Email", "NVARCHAR(255) NULL"),
        ("Owner", "Phone", "NVARCHAR(100) NULL"),
        ("Owner", "Website", "NVARCHAR(500) NULL"),
        ("Owner", "KennelPrefix", "NVARCHAR(100) NULL"),
        ("Owner", "BreederID", "INT NULL"),
    ]
    for table, col, typ in alters:
        cur.execute(
            f"""
            IF COL_LENGTH('sResults.{table}', '{col}') IS NULL
                ALTER TABLE sResults.{table} ADD [{col}] {typ};
            """
        )


def clip(val: Optional[str], n: int) -> Optional[str]:
    if val is None:
        return None
    s = clean_piece(str(val))
    if not s:
        return None
    return s[:n]


def join_notes(parts: list[str]) -> Optional[str]:
    cleaned = [clean_piece(p) for p in parts if clean_piece(p)]
    if not cleaned:
        return None
    out: list[str] = []
    seen: set[str] = set()
    for p in cleaned:
        k = p.lower()
        if k in seen:
            continue
        seen.add(k)
        out.append(p)
    return " | ".join(out)


def merge_text(existing: Optional[str], incoming: Optional[str]) -> Optional[str]:
    if not incoming:
        return existing
    if not existing:
        return incoming
    have = existing.lower()
    extra = []
    for piece in incoming.split(" | "):
        p = clean_piece(piece)
        if p and p.lower() not in have:
            extra.append(p)
    if not extra:
        return existing
    return existing + " | " + " | ".join(extra)


def fill_if_empty(cur: pyodbc.Cursor, table: str, pk: str, pk_val: int, updates: dict) -> None:
    sets = []
    vals = []
    for col, val in updates.items():
        if val in (None, "", []):
            continue
        sets.append(f"[{col}] = COALESCE([{col}], ?)")
        vals.append(val if not isinstance(val, list) else join_notes(val))
    if not sets:
        return
    vals.append(pk_val)
    cur.execute(
        f"UPDATE sResults.{table} SET {', '.join(sets)} WHERE {pk}=?",
        vals,
    )


def owner_name_keys(name: str) -> list[str]:
    keys = [normalize_key(name)]
    n = normalize_name(name)
    n = n.replace(" and ", " & ").replace("/", " & ").replace(",", " & ")
    if "&" in n:
        last = n.split()[-1]
        for part in [x.strip() for x in n.split("&") if x.strip()]:
            keys.append(normalize_key(part))
            if last.lower() not in part.lower().split() and len(part.split()) == 1:
                keys.append(normalize_key(f"{part} {last}"))
    parts = re.sub(r"[&/,]", " ", n).split()
    if len(parts) >= 2:
        keys.append(normalize_key(f"{parts[0]} {parts[-1]}"))
        keys.append(normalize_key(f"{parts[-2]} {parts[-1]}"))
    out = []
    seen = set()
    for k in keys:
        if k and k not in seen:
            seen.add(k)
            out.append(k)
    return out


def compact_key(name: str) -> str:
    n = normalize_key(name)
    n = n.replace(" and ", " n ")
    return re.sub(r"\s+", "", n)


def listed_name_keys(name: str, kennel: str) -> list[str]:
    name = re.sub(r"^(latest addition|introducing)\s+", "", name, flags=re.I)
    if "/" in name:
        # photo caption with two dogs; do not treat as one name
        return []
    keys = [normalize_key(name)]
    words = name.split()
    if len(words) >= 2:
        keys.append(normalize_key(" ".join(words[-2:])))
    if kennel:
        keys.append(normalize_key(f"{kennel} {name}"))
        last = words[-1] if words else ""
        if last:
            keys.append(normalize_key(f"{kennel} {last}"))
    return [k for k in keys if k]


@dataclass
class DogRow:
    dog_id: int
    name: str
    owner_id: Optional[int]
    owner_name: str
    sire: str
    dam: str
    notes: Optional[str] = None
    titles: Optional[str] = None
    health: Optional[str] = None


def find_existing_dog(
    listed: ParsedDog,
    kennel: str,
    owner_id: Optional[int],
    owner_name: str,
    by_key: dict[str, list[DogRow]],
) -> Optional[DogRow]:
    keys = listed_name_keys(listed.name, kennel)
    cands: list[DogRow] = []
    seen: set[int] = set()
    for k in keys:
        for row in by_key.get(k, []):
            if row.dog_id not in seen:
                seen.add(row.dog_id)
                cands.append(row)
    listed_k = normalize_key(listed.name)
    listed_c = compact_key(listed.name)
    kennel_c = compact_key(f"{kennel} {listed.name}") if kennel else ""
    last_two = normalize_key(" ".join(listed.name.split()[-2:])) if len(listed.name.split()) >= 2 else ""
    if listed_k and len(listed_k) >= 4:
        for k, rows in by_key.items():
            k_c = compact_key(k)
            if (
                k == listed_k
                or k.endswith(" " + listed_k)
                or listed_k.endswith(" " + k)
                or (last_two and len(last_two) >= 6 and k.endswith(" " + last_two))
                or k_c == listed_c
                or (kennel_c and k_c == kennel_c)
            ):
                for row in rows:
                    if row.dog_id not in seen:
                        seen.add(row.dog_id)
                        cands.append(row)
    if not cands:
        return None

    def score(row: DogRow) -> int:
        s = 0
        if owner_id and row.owner_id == owner_id:
            s += 50
        if owner_name and normalize_key(row.owner_name):
            o_keys = set(owner_name_keys(owner_name))
            r_keys = set(owner_name_keys(row.owner_name))
            if o_keys & r_keys:
                s += 30
            elif any(x in normalize_key(row.owner_name) for x in o_keys if " " in x):
                s += 20
        if kennel and kennel.lower() in row.name.lower():
            s += 15
        if listed.sire and normalize_key(listed.sire) and normalize_key(listed.sire) == normalize_key(row.sire):
            s += 20
        if listed.dam and normalize_key(listed.dam) and normalize_key(listed.dam) == normalize_key(row.dam):
            s += 20
        if normalize_key(row.name) == normalize_key(listed.name):
            s += 10
        if normalize_key(row.name) == normalize_key(f"{kennel} {listed.name}"):
            s += 12
        return s

    ranked = sorted(cands, key=score, reverse=True)
    best = ranked[0]
    best_score = score(best)
    if best_score >= 10:
        return best
    if len(ranked) == 1 and (normalize_key(best.name) == listed_k or listed_k in normalize_key(best.name)):
        return best
    return None


def find_existing_owner(
    name: str, owner_by_key: dict[str, int]
) -> Optional[int]:
    if not name:
        return None
    for k in owner_name_keys(name):
        if k in owner_by_key:
            return owner_by_key[k]
    # last-name + shared first token
    last = normalize_key(name).split()[-1] if normalize_key(name) else ""
    if len(last) < 4:
        return None
    hits = [i for k, i in owner_by_key.items() if k.endswith(" " + last) and k.split()[0] in normalize_key(name).split()]
    if len(set(hits)) == 1:
        return hits[0]
    return None


def load_sql(breeders: list[ParsedBreeder]) -> None:
    conn = get_conn()
    cur = conn.cursor()
    ensure_schema(cur)
    conn.commit()

    cur.execute("SELECT OwnerID, OwnerName FROM sResults.Owner")
    owner_by_key: dict[str, int] = {}
    for oid, oname in cur.fetchall():
        if not oname:
            continue
        for k in owner_name_keys(oname):
            owner_by_key.setdefault(k, oid)
    cur.execute(
        """
        SELECT d.DogID, d.DogName, d.OwnerID, ISNULL(o.OwnerName,''),
               ISNULL(d.Sire,''), ISNULL(d.Dam,''),
               d.Notes, d.Titles, d.HealthTests
        FROM sResults.Dog d
        LEFT JOIN sResults.Owner o ON d.OwnerID=o.OwnerID
        """
    )
    dogs_by_key: dict[str, list[DogRow]] = {}
    dogs_by_id: dict[int, DogRow] = {}
    for did, dname, oid, oname, sire, dam, notes, titles, health in cur.fetchall():
        row = DogRow(did, dname or "", oid, oname, sire, dam, notes, titles, health)
        dogs_by_id[did] = row
        dogs_by_key.setdefault(normalize_key(dname), []).append(row)
    cur.execute("SELECT DogID, RelatedDogName, RelationshipType FROM sResults.Relationship")
    rel_have = {(a, normalize_key(b), c.lower()) for a, b, c in cur.fetchall() if b}

    stats = {"breeders": 0, "owners_new": 0, "owners_upd": 0, "dogs_new": 0, "dogs_upd": 0, "dogs_unmatched": 0, "rels": 0}
    unmatched: list[str] = []

    for b in breeders:
        b.kennel_name = clip(b.kennel_name, 255) or (b.kennel_name or "")[:255]
        b.owner_name = clip(b.owner_name, 255) or ""
        b.address = clip(b.address, 255)
        b.city = clip(b.city, 100)
        b.state = clip(b.state, 50)
        b.postal_code = clip(b.postal_code, 20)
        b.email = clip(b.email, 255)
        b.phone = clip(b.phone, 100)
        b.website = clip(b.website, 500)
        b.facebook = clip(b.facebook, 500)
        b.instagram = clip(b.instagram, 500)
        b.location = clip(b.location, 255)
        b.page_url = clip(b.page_url, 500) or ""
        for d in b.dogs:
            d.name = clip(d.name, 255) or (d.name or "")[:255]
            d.sire = clip(d.sire, 255)
            d.dam = clip(d.dam, 255)
            d.sex = clip(d.sex, 50)
            d.height = clip(d.height, 50)
            d.coat = clip(d.coat, 80)
            d.color = clip(d.color, 80)
            d.call_name = clip(d.call_name, 100)
            d.co_owner = clip(d.co_owner, 255)
            d.source_url = clip(d.source_url, 500) or ""
        if b.slug in SKIP_PAGES or is_junk_slug(b.slug) or is_junk_breeder(b.kennel_name, b.page_url):
            continue
        if b.owner_name and JUNK_OWNER_RE.search(b.owner_name):
            b.owner_name = ""
        notes = join_notes(
            [
                b.location,
                f"Snapshot {b.snapshot}" if b.snapshot else "Live site",
            ]
        )
        cur.execute(
            """
            SELECT BreederID FROM sResults.Breeder
            WHERE KennelName=? OR SourceURL=?
            """,
            b.kennel_name,
            b.page_url,
        )
        row = cur.fetchone()
        if row:
            breeder_id = row[0]
            fill_if_empty(
                cur,
                "Breeder",
                "BreederID",
                breeder_id,
                {
                    "KennelPrefix": b.kennel_name,
                    "OwnerName": b.owner_name,
                    "Address": b.address,
                    "City": b.city,
                    "State": b.state,
                    "PostalCode": b.postal_code,
                    "Email": b.email,
                    "Phone": b.phone,
                    "Website": b.website,
                    "Facebook": b.facebook,
                    "Instagram": b.instagram,
                    "Location": b.location,
                    "Description": b.description,
                    "PhotoPath": join_notes(b.photo_paths),
                    "SourceURL": b.page_url,
                    "Notes": notes,
                },
            )
        else:
            cur.execute(
                """
                INSERT INTO sResults.Breeder (
                    KennelName, KennelPrefix, OwnerName, Address, City, State, PostalCode,
                    Email, Phone, Website, Facebook, Instagram, Location, Description,
                    PhotoPath, SourceURL, SourceSnapshot, Notes
                )
                OUTPUT INSERTED.BreederID
                VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)
                """,
                b.kennel_name,
                b.kennel_name,
                b.owner_name or None,
                b.address or None,
                b.city or None,
                b.state or None,
                b.postal_code or None,
                b.email or None,
                b.phone or None,
                b.website or None,
                b.facebook or None,
                b.instagram or None,
                b.location or None,
                b.description or None,
                join_notes(b.photo_paths),
                b.page_url or None,
                b.snapshot or None,
                notes,
            )
            breeder_id = cur.fetchone()[0]
            stats["breeders"] += 1

        owner_id = find_existing_owner(b.owner_name, owner_by_key) if b.owner_name else None
        if owner_id:
            fill_if_empty(
                cur,
                "Owner",
                "OwnerID",
                owner_id,
                {
                    "Address": b.address,
                    "City": b.city,
                    "State": b.state,
                    "PostalCode": b.postal_code,
                    "Email": b.email,
                    "Phone": b.phone,
                    "Website": b.website,
                    "KennelPrefix": b.kennel_name,
                    "BreederID": breeder_id,
                },
            )
            stats["owners_upd"] += 1
        elif b.owner_name:
            cur.execute(
                """
                INSERT INTO sResults.Owner (
                    OwnerName, Address, City, State, PostalCode, Email, Phone,
                    Website, KennelPrefix, BreederID
                )
                OUTPUT INSERTED.OwnerID
                VALUES (?,?,?,?,?,?,?,?,?,?)
                """,
                b.owner_name,
                b.address or None,
                b.city or None,
                b.state or None,
                b.postal_code or None,
                b.email or None,
                b.phone or None,
                b.website or None,
                b.kennel_name,
                breeder_id,
            )
            owner_id = cur.fetchone()[0]
            for k in owner_name_keys(b.owner_name):
                owner_by_key.setdefault(k, owner_id)
            stats["owners_new"] += 1

        kennel_list = [b.kennel_name] + [x.kennel_name for x in breeders if x.kennel_name]
        expanded_dogs: list[ParsedDog] = []
        for d in b.dogs:
            for nm, extra in expand_listed_names(d.name, kennel_list):
                if is_junk_row_name(nm):
                    continue
                nd = replace(d, name=nm)
                if extra:
                    apply_detail_text(nd, extra)
                expanded_dogs.append(nd)
        b.dogs = expanded_dogs

        for d in b.dogs:
            match = find_existing_dog(d, b.kennel_name, owner_id, b.owner_name, dogs_by_key)
            note = join_notes(d.notes + ([d.raw] if d.raw else []))
            titles = join_notes(d.titles)
            health = join_notes(d.health_tests)
            photo = join_notes(d.photo_paths)
            if match:
                dog_id = match.dog_id
                merged_notes = merge_text(match.notes, note)
                merged_titles = merge_text(match.titles, titles)
                merged_health = merge_text(match.health, health)
                fill_if_empty(
                    cur,
                    "Dog",
                    "DogID",
                    dog_id,
                    {
                        "Sire": d.sire,
                        "Dam": d.dam,
                        "Sex": d.sex,
                        "Height": d.height,
                        "Coat": d.coat,
                        "Color": d.color,
                        "CallName": d.call_name,
                        "CoOwner": d.co_owner,
                        "PhotoPath": photo,
                        "SourceURL": d.source_url or b.page_url,
                        "BreederID": breeder_id,
                    },
                )
                cur.execute(
                    """
                    UPDATE sResults.Dog
                    SET Notes=?, Titles=?, HealthTests=?
                    WHERE DogID=?
                    """,
                    merged_notes,
                    merged_titles,
                    merged_health,
                    dog_id,
                )
                if d.dob:
                    cur.execute(
                        "UPDATE sResults.Dog SET DateOfBirth = COALESCE(DateOfBirth, TRY_CONVERT(date, ?)) WHERE DogID=?",
                        d.dob,
                        dog_id,
                    )
                match.notes = merged_notes
                match.titles = merged_titles
                match.health = merged_health
                stats["dogs_upd"] += 1
            else:
                if not _ok_to_insert_dog(d, b):
                    unmatched.append(
                        f"{b.kennel_name}\t{d.name}\tsire={d.sire}\tdam={d.dam}\towner={b.owner_name}\tskip"
                    )
                    stats["dogs_unmatched"] += 1
                    continue
                cur.execute(
                    """
                    INSERT INTO sResults.Dog (
                        DogName, OwnerID, Sire, Dam, Sex, DateOfBirth, Height, Coat, Color,
                        CallName, Titles, HealthTests, CoOwner, Notes, PhotoPath, SourceURL, BreederID
                    )
                    OUTPUT INSERTED.DogID
                    VALUES (?,?,?,?,?,TRY_CONVERT(date, ?),?,?,?,?,?,?,?,?,?,?,?)
                    """,
                    d.name,
                    owner_id,
                    d.sire,
                    d.dam,
                    d.sex,
                    d.dob,
                    d.height,
                    d.coat,
                    d.color,
                    d.call_name,
                    titles,
                    health,
                    d.co_owner,
                    note,
                    photo,
                    d.source_url or b.page_url,
                    breeder_id,
                )
                dog_id = cur.fetchone()[0]
                row = DogRow(
                    dog_id,
                    d.name,
                    owner_id,
                    b.owner_name or "",
                    d.sire or "",
                    d.dam or "",
                    note,
                    titles,
                    health,
                )
                dogs_by_key.setdefault(normalize_key(d.name), []).append(row)
                unmatched.append(
                    f"{b.kennel_name}\t{d.name}\tsire={d.sire}\tdam={d.dam}\towner={b.owner_name}\tINSERTED {dog_id}"
                )
                stats["dogs_new"] += 1

            for related, rtype in ((d.sire, "Sire"), (d.dam, "Dam")):
                if not related:
                    continue
                rkey = (dog_id, normalize_key(related), rtype.lower())
                if rkey in rel_have:
                    continue
                related_id = None
                rcands = dogs_by_key.get(normalize_key(related), [])
                if len(rcands) == 1:
                    related_id = rcands[0].dog_id
                cur.execute(
                    """
                    INSERT INTO sResults.Relationship (
                        DogID, RelatedDogID, RelatedDogName, RelationshipType, RelatedDogSex
                    ) VALUES (?,?,?,?,?)
                    """,
                    dog_id,
                    related_id,
                    related,
                    rtype,
                    "dog" if rtype == "Sire" else "bitch",
                )
                rel_have.add(rkey)
                stats["rels"] += 1

    conn.commit()
    conn.close()
    (ROOT / "unmatched_dogs.txt").write_text("\n".join(unmatched), encoding="utf-8")
    print("SQL load", stats)
    if unmatched:
        print("Unmatched dogs written to", ROOT / "unmatched_dogs.txt")


def is_junk_row_name(name: str) -> bool:
    n = clean_piece(name or "")
    if not n:
        return True
    if PHONE_RE.search(n) or JUNK_NAME_RE.search(n) or SKIP_NAME.search(n):
        return True
    if JUNK_PHRASE_RE.search(n) or HEALTH_ONLY_RE.match(n):
        return True
    if n.lower() in US_CAN_STATES:
        return True
    if "<" in n or ">" in n or "http" in n.lower() or "href" in n.lower():
        return True
    if re.match(r"^\(?\d{3}\)", n):
        return True
    letters = re.sub(r"[^A-Za-z]", "", n)
    return len(letters) < 3


def _delete_dogs(cur: pyodbc.Cursor, ids: list[int]) -> tuple[int, int]:
    rels = 0
    dogs = 0
    if not ids:
        return 0, 0
    chunk = 400
    for i in range(0, len(ids), chunk):
        part = ids[i : i + chunk]
        marks = ",".join("?" * len(part))
        cur.execute(
            f"DELETE FROM sResults.Relationship WHERE DogID IN ({marks}) OR RelatedDogID IN ({marks})",
            part + part,
        )
        rels += cur.rowcount or 0
        cur.execute(f"DELETE FROM sResults.Dog WHERE DogID IN ({marks})", part)
        dogs += cur.rowcount or 0
    return rels, dogs


def cleanup_junk_sql() -> dict:
    """Split paired names, strip extras, delete non-dogs and studbook/index breeders."""
    conn = get_conn()
    cur = conn.cursor()
    ensure_schema(cur)
    cur.execute("SELECT KennelName FROM sResults.Breeder")
    kennels = [r[0] for r in cur.fetchall() if r[0] and not is_junk_breeder(r[0], "")]
    cur.execute("SELECT BreederID, KennelName, ISNULL(SourceURL,'') FROM sResults.Breeder")
    junk_breeders = [
        bid for bid, name, url in cur.fetchall() if is_junk_breeder(name or "", url or "")
    ]
    junk_breeder_set = set(junk_breeders)
    cur.execute("SELECT DogID, DogName FROM sResults.Dog")
    by_key: dict[str, int] = {}
    for did, dname in cur.fetchall():
        k = normalize_key(dname or "")
        if k:
            by_key.setdefault(k, did)
    cur.execute(
        """
        SELECT DogID, DogName, OwnerID, Sire, Dam, Notes, SourceURL, BreederID
        FROM sResults.Dog
        WHERE SourceURL LIKE '%jrtcabreeders%'
           OR BreederID IS NOT NULL
        """
    )
    rows = cur.fetchall()
    junk_ids: list[int] = []
    samples: list[str] = []
    renamed: list[str] = []
    split_n = 0
    stats = {
        "dogs": 0,
        "rels": 0,
        "breeders": 0,
        "owners": 0,
        "renamed": 0,
        "split": 0,
        "unlinked": 0,
        "samples": samples,
    }

    def mark(did: int, label: str) -> None:
        junk_ids.append(did)
        if len(samples) < 100:
            samples.append(f"{did}\t{label}")

    for did, name, oid, sire, dam, notes, url, bid in rows:
        n = name or ""
        pieces = expand_listed_names(n, kennels)
        first = pieces[0][0] if pieces else ""
        extra = pieces[0][1] if pieces else ""
        hard_junk = bool(
            HEALTH_ONLY_RE.match(n)
            or JUNK_PHRASE_RE.search(n)
            or PHONE_RE.search(n)
            or JUNK_NAME_RE.search(n)
        )
        if hard_junk or is_junk_row_name(first):
            if did >= SCRAPE_INSERT_MIN_ID or hard_junk:
                mark(did, n)
                continue
        if (
            bid in junk_breeder_set
            and did >= SCRAPE_INSERT_MIN_ID
            and not sire
            and not dam
        ):
            mark(did, f"{n} [studbook-insert]")
            continue
        if first and first != n:
            new_notes = merge_text(notes, extra) if extra else notes
            cur.execute(
                "UPDATE sResults.Dog SET DogName=?, Notes=? WHERE DogID=?",
                first[:255],
                new_notes,
                did,
            )
            stats["renamed"] += 1
            renamed.append(f"{did}\t{n}\t->\t{first}")
            by_key.setdefault(normalize_key(first), did)
        if len(pieces) > 1:
            for nm, ex in pieces[1:]:
                if is_junk_row_name(nm):
                    continue
                k = normalize_key(nm)
                if k in by_key:
                    continue
                cur.execute(
                    """
                    INSERT INTO sResults.Dog (
                        DogName, OwnerID, Notes, SourceURL, BreederID
                    )
                    OUTPUT INSERTED.DogID
                    VALUES (?,?,?,?,?)
                    """,
                    nm[:255],
                    oid,
                    merge_text(None, ex),
                    url,
                    bid if bid not in junk_breeder_set else None,
                )
                new_id = cur.fetchone()[0]
                by_key[k] = new_id
                split_n += 1
                samples.append(f"{new_id}\tSPLIT {nm}\tfrom {did} {n}")

    stats["split"] = split_n
    rels, dogs = _delete_dogs(cur, junk_ids)
    stats["rels"] += rels
    stats["dogs"] += dogs

    if junk_breeders:
        marks = ",".join("?" * len(junk_breeders))
        cur.execute(
            f"""
            UPDATE sResults.Dog
            SET BreederID = NULL,
                SourceURL = CASE
                    WHEN SourceURL LIKE '%studbook%' OR SourceURL LIKE '%index_of_dogs%'
                      OR SourceURL LIKE '%chat_%' OR SourceURL LIKE '%category_breeder%'
                    THEN NULL ELSE SourceURL END
            WHERE BreederID IN ({marks})
            """,
            junk_breeders,
        )
        stats["unlinked"] = cur.rowcount or 0
        cur.execute(
            f"DELETE FROM sResults.Breeder WHERE BreederID IN ({marks})",
            junk_breeders,
        )
        stats["breeders"] = cur.rowcount or 0

    cur.execute(
        """
        DELETE FROM sResults.Owner
        WHERE (OwnerName LIKE '%inquir%'
            OR OwnerName LIKE '%welcome%'
            OR OwnerName LIKE '%href%'
            OR OwnerName LIKE '%www.%'
            OR OwnerName LIKE '%http%'
            OR OwnerName LIKE '%Fax%'
            OR OwnerName LIKE '%brucellosis%'
            OR OwnerName LIKE '%Our Girls%'
            OR OwnerName LIKE '%Standing At Stud%'
            OR OwnerName LIKE '%ell.com%'
            OR OwnerName LIKE '%CELLPADDING%'
            OR OwnerName LIKE '%Zurich BT%'
            OR OwnerName LIKE 'ER>%')
          AND NOT EXISTS (SELECT 1 FROM sResults.Dog d WHERE d.OwnerID = sResults.Owner.OwnerID)
        """
    )
    stats["owners"] = cur.rowcount or 0
    conn.commit()
    conn.close()
    (ROOT / "junk_deleted.txt").write_text(
        "\n".join(samples + [""] + renamed[:80]), encoding="utf-8"
    )
    print("Junk cleanup", {k: stats[k] for k in stats if k != "samples"})
    return stats


def dump_parsed(breeders: list[ParsedBreeder]) -> None:
    payload = []
    for b in breeders:
        rec = asdict(b)
        payload.append(rec)
    (API / "parsed.json").write_text(json.dumps(payload, indent=2), encoding="utf-8")
    lines = []
    for b in sorted(breeders, key=lambda x: x.kennel_name.lower()):
        lines.append("=" * 80)
        lines.append(
            f"{b.kennel_name} | {b.owner_name} | {b.address} | {b.city}, {b.state} {b.postal_code}"
        )
        lines.append(f"{b.email} | {b.phone} | {b.website} | dogs={len(b.dogs)}")
        for d in b.dogs:
            lines.append(
                f"  {d.name} sex={d.sex} ht={d.height} coat={d.coat} color={d.color} "
                f"sire={d.sire} dam={d.dam} call={d.call_name}"
            )
            if d.titles:
                lines.append(f"    TITLES: {' | '.join(d.titles)}")
            if d.health_tests:
                lines.append(f"    HEALTH: {' | '.join(d.health_tests)}")
            if d.notes:
                lines.append(f"    NOTES: {' | '.join(d.notes)}")
    (ROOT / "parsed_review.txt").write_text("\n".join(lines), encoding="utf-8")


def main() -> None:
    print("Collecting live pages...")
    live = collect_live()
    print("Live breeders:", len(live), "dogs", sum(len(b.dogs) for b in live))
    print("Downloading live photos...")
    download_all_photos(live)
    dump_parsed(live)
    print("Augmenting existing Dog/Owner rows from live site...")
    load_sql(live)

    print("Collecting archive.org snapshots...")
    archived = collect_archive()
    merged = merge_breeders(live + archived)
    print("After archive merge:", len(merged), "dogs", sum(len(b.dogs) for b in merged))
    print("Downloading remaining photos...")
    download_all_photos(merged)
    dump_parsed(merged)
    print("Augmenting from archive snapshots...")
    load_sql(merged)
    print("Done. Pages:", PAGES_LIVE, PAGES_ARCHIVE, "Photos:", PHOTOS)


if __name__ == "__main__":
    main()
