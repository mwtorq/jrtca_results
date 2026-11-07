#!/usr/bin/env python3
"""Scrape live + Wayback JRTCA org pages into Board / Committee / StateRepresentative + Owner.

Sources:
  - https://www.therealjackrussell.com/jrtca/board.php
  - https://www.therealjackrussell.com/jrtca/reponline.php
  - Internet Archive captures of those URLs on therealjackrussell.com and terrier.com

Usage:
  py -3 scrape_jrtca_org_meta.py                 # CDX + download + dry-run load
  py -3 scrape_jrtca_org_meta.py --from-cache    # parse cache only, dry-run
  py -3 scrape_jrtca_org_meta.py --apply         # write to TrialResults
  py -3 scrape_jrtca_org_meta.py --live-only --apply
"""
from __future__ import annotations

import argparse
import hashlib
import json
import re
import sys
import time
import urllib.error
import urllib.parse
import urllib.request
from collections import defaultdict
from dataclasses import asdict
from pathlib import Path

from bs4 import BeautifulSoup
import pyodbc

from remount_source_divisions import CONN
from yearbook_meta_schema import ensure as ensure_schema
from yearbook_meta_ingest import (
    MetaBundle,
    PersonHit,
    append_note,
    apply_bundle,
    name_key,
    norm_name,
    plausible_person,
    split_couple_name,
    _STATE_NAMES,
)

ROOT = Path(__file__).resolve().parent
ARCHIVE = ROOT / "jrtca_org_archive"
HTML_DIR = ARCHIVE / "html"
MANIFEST = ARCHIVE / "manifest.jsonl"
CDX_PATH = ARCHIVE / "cdx.json"
PARSED_PATH = ARCHIVE / "parsed_records.json"

UA = {"User-Agent": "Mozilla/5.0 jrtca-results-research"}
LIVE_YEAR = 2026
SLEEP_S = 1.0

LIVE_URLS = [
    ("board", "https://www.therealjackrussell.com/jrtca/board.php"),
    ("reponline", "https://www.therealjackrussell.com/jrtca/reponline.php"),
]

# CDX queries (narrow first — IA rate-limits broad /* scans)
CDX_QUERIES = [
    "therealjackrussell.com/jrtca/board*",
    "www.therealjackrussell.com/jrtca/board*",
    "therealjackrussell.com/jrtca/reponline*",
    "www.therealjackrussell.com/jrtca/reponline*",
    "therealjackrussell.com/jrtca/*committee*",
    "www.therealjackrussell.com/jrtca/*committee*",
    "therealjackrussell.com/jrtca/*director*",
    "www.therealjackrussell.com/jrtca/*director*",
    "therealjackrussell.com/jrtca/*rep*",
    "www.therealjackrussell.com/jrtca/*rep*",
    "terrier.com/*board*",
    "www.terrier.com/*board*",
    "terrier.com/*rep*",
    "www.terrier.com/*rep*",
    "terrier.com/*director*",
    "www.terrier.com/*director*",
    "terrier.com/*committee*",
    "www.terrier.com/*committee*",
    "terrier.com/jrtca/*",
    "www.terrier.com/jrtca/*",
]

ORG_PATH_RE = re.compile(
    r"(board|director|committee|reponline|represent|/rep\.|/reps|"
    r"officer|state.?rep)",
    re.I,
)

_COMMITTEE_FROM_ROLE = re.compile(
    r"(?:Chair(?:person|man)?(?:\s+of)?|Member(?:\s+of)?)\s*,?\s*"
    r"(?:the\s+)?(Judges|Trial|Breeders?|Representatives?)\s+Committee",
    re.I,
)
_COMMITTEE_NAME_RE = re.compile(
    r"\b((?:Judges|Trial|Breeders?|Representatives?)\s+Committee)\b",
    re.I,
)
_LOC_RE = re.compile(
    r"^(.+?),\s*([A-Z]{2})\s*$"
)
_EMAIL_RE = re.compile(r"[A-Z0-9._%+\-]+@[A-Z0-9.\-]+\.[A-Z]{2,}", re.I)
_PHONE_RE = re.compile(r"(\(?\d{3}\)?[-.\s]?\d{3}[-.\s]?\d{4})")


def http_get(url: str, timeout: int = 120, retries: int = 4) -> bytes | None:
    last_err = None
    for attempt in range(retries):
        try:
            req = urllib.request.Request(url, headers=UA)
            with urllib.request.urlopen(req, timeout=timeout) as resp:
                return resp.read()
        except Exception as e:
            last_err = e
            wait = SLEEP_S * (attempt + 1) * 2
            print(f"  GET fail ({type(e).__name__}: {e}); retry in {wait:.0f}s")
            time.sleep(wait)
    print(f"  GET gave up: {url} ({last_err})")
    return None


def cdx_fetch(url_pat: str) -> list[list[str]]:
    q = urllib.parse.urlencode(
        {
            "url": url_pat,
            "output": "json",
            "filter": "statuscode:200",
            "fl": "timestamp,original,mimetype,statuscode,digest,length",
        }
    )
    api = f"https://web.archive.org/cdx/search/cdx?{q}"
    print("CDX", url_pat)
    raw = http_get(api, timeout=180)
    if not raw:
        return []
    try:
        data = json.loads(raw.decode("utf-8", errors="ignore"))
    except Exception as e:
        print("  CDX JSON fail", e)
        return []
    if not data or len(data) < 2:
        print("  rows 0")
        return []
    body = data[1:]
    print("  rows", len(body))
    return body


def is_org_url(original: str) -> bool:
    try:
        path = urllib.parse.urlparse(original).path or ""
    except Exception:
        path = original
    # Always keep known org endpoints even if path is short
    low = path.lower()
    if any(
        x in low
        for x in (
            "/board",
            "reponline",
            "staterep",
            "state_rep",
            "directors",
            "committee",
        )
    ):
        return True
    return bool(ORG_PATH_RE.search(path))


def invent_digest(content: bytes) -> str:
    return hashlib.sha1(content).hexdigest().upper()


def wayback_urls(timestamp: str, original: str) -> list[str]:
    """Prefer rewritten HTML capture; id_ often returns unusable compressed/raw payloads."""
    return [
        f"https://web.archive.org/web/{timestamp}/{original}",
        f"https://web.archive.org/web/{timestamp}if_/{original}",
        f"https://web.archive.org/web/{timestamp}id_/{original}",
    ]


def _looks_like_html(raw: bytes) -> bool:
    if not raw or len(raw) < 200:
        return False
    if raw[:2] == b"\x1f\x8b":
        try:
            import gzip

            raw = gzip.decompress(raw)
        except Exception:
            return False
    sample = raw[:2000].decode("utf-8", errors="ignore").lower()
    return "<html" in sample or "<table" in sample or "<!doctype" in sample


def ensure_dirs() -> None:
    HTML_DIR.mkdir(parents=True, exist_ok=True)
    ARCHIVE.mkdir(parents=True, exist_ok=True)


def inventory_cdx() -> list[dict]:
    """Return deduped capture records; also write cdx.json."""
    ensure_dirs()
    combined: list[list[str]] = []
    seen: set[tuple] = set()
    header = ["timestamp", "original", "mimetype", "statuscode", "digest", "length"]
    for pat in CDX_QUERIES:
        rows = cdx_fetch(pat)
        time.sleep(SLEEP_S)
        for row in rows:
            if len(row) < 5:
                continue
            ts, original, mime, status, digest = row[0], row[1], row[2], row[3], row[4]
            if not is_org_url(original):
                continue
            if mime and "html" not in mime.lower() and mime != "-":
                continue
            key = (ts, original, digest)
            if key in seen:
                continue
            seen.add(key)
            combined.append(row)
    out = [header] + combined
    CDX_PATH.write_text(json.dumps(out), encoding="utf-8")
    print("CDX unique org rows", len(combined), "->", CDX_PATH)
    return [
        {
            "timestamp": r[0],
            "original": r[1],
            "mimetype": r[2],
            "statuscode": r[3],
            "digest": r[4],
            "length": r[5] if len(r) > 5 else "",
            "year": int(r[0][:4]),
            "kind": "wayback",
        }
        for r in combined
    ]


def load_cdx_cache() -> list[dict]:
    if not CDX_PATH.exists():
        return []
    data = json.loads(CDX_PATH.read_text(encoding="utf-8"))
    if not data or len(data) < 2:
        return []
    return [
        {
            "timestamp": r[0],
            "original": r[1],
            "mimetype": r[2],
            "statuscode": r[3],
            "digest": r[4],
            "length": r[5] if len(r) > 5 else "",
            "year": int(r[0][:4]),
            "kind": "wayback",
        }
        for r in data[1:]
        if len(r) >= 5 and is_org_url(r[1])
    ]


def select_captures(captures: list[dict]) -> list[dict]:
    """One capture per (year, digest); prefer earliest timestamp in that year."""
    best: dict[tuple[int, str], dict] = {}
    for c in captures:
        key = (int(c["year"]), c["digest"])
        prev = best.get(key)
        if prev is None or c["timestamp"] < prev["timestamp"]:
            best[key] = c
    selected = sorted(best.values(), key=lambda x: (x["year"], x["original"], x["timestamp"]))
    print("selected captures (year,digest)", len(selected))
    return selected


def page_kind(url: str, html: str = "") -> str:
    low = (url or "").lower()
    title = ""
    if html:
        m = re.search(r"<title[^>]*>(.*?)</title>", html, re.I | re.S)
        if m:
            title = re.sub(r"\s+", " ", m.group(1)).lower()
    blob = low + " " + title
    if "reponline" in blob or "state representative" in blob or "state rep" in blob:
        return "reponline"
    if "board" in blob or "director" in blob:
        return "board"
    if "committee" in blob:
        return "committee"
    return "unknown"


def append_manifest(rec: dict) -> None:
    with MANIFEST.open("a", encoding="utf-8") as f:
        f.write(json.dumps(rec, ensure_ascii=False) + "\n")


def download_live() -> list[dict]:
    ensure_dirs()
    out = []
    for kind, url in LIVE_URLS:
        print("LIVE", url)
        raw = http_get(url)
        time.sleep(SLEEP_S)
        if not raw:
            continue
        digest = invent_digest(raw)
        path = HTML_DIR / f"live_{kind}_{digest}.html"
        path.write_bytes(raw)
        rec = {
            "kind": "live",
            "page_kind": kind,
            "year": LIVE_YEAR,
            "timestamp": f"{LIVE_YEAR}0101000000",
            "original": url,
            "digest": digest,
            "path": str(path.relative_to(ROOT)).replace("\\", "/"),
            "source_path": f"web:{urllib.parse.urlparse(url).netloc}{urllib.parse.urlparse(url).path}@{LIVE_YEAR}",
        }
        append_manifest(rec)
        out.append(rec)
        print("  saved", path.name, "bytes", len(raw))
    return out


def download_wayback(selected: list[dict]) -> list[dict]:
    ensure_dirs()
    out = []
    for i, c in enumerate(selected, 1):
        digest = c["digest"]
        path = HTML_DIR / f"{digest}.html"
        cached_ok = path.exists() and _looks_like_html(path.read_bytes())
        if cached_ok:
            html = path.read_text(encoding="utf-8", errors="ignore")
            pk = page_kind(c["original"], html)
            rec = {
                **c,
                "page_kind": pk,
                "path": str(path.relative_to(ROOT)).replace("\\", "/"),
                "source_path": (
                    f"wayback:{urllib.parse.urlparse(c['original']).netloc}"
                    f"{urllib.parse.urlparse(c['original']).path}"
                    f"@{c['year']}/{digest}"
                ),
                "cached": True,
            }
            out.append(rec)
            continue
        print(f"[{i}/{len(selected)}] WB", c["year"], c["original"][:70])
        raw = None
        for url in wayback_urls(c["timestamp"], c["original"]):
            raw = http_get(url)
            time.sleep(SLEEP_S)
            if raw and raw[:2] == b"\x1f\x8b":
                try:
                    import gzip

                    raw = gzip.decompress(raw)
                except Exception:
                    raw = None
            if raw and _looks_like_html(raw):
                break
            raw = None
        if not raw:
            continue
        path.write_bytes(raw)
        html = raw.decode("utf-8", errors="ignore")
        pk = page_kind(c["original"], html)
        rec = {
            **c,
            "page_kind": pk,
            "path": str(path.relative_to(ROOT)).replace("\\", "/"),
            "source_path": (
                f"wayback:{urllib.parse.urlparse(c['original']).netloc}"
                f"{urllib.parse.urlparse(c['original']).path}"
                f"@{c['year']}/{digest}"
            ),
            "cached": False,
        }
        append_manifest(rec)
        out.append(rec)
    print("wayback files ready", len(out))
    return out


def load_manifest_files() -> list[dict]:
    """Rebuild file list from html/ + prior manifest / cdx."""
    ensure_dirs()
    recs = []
    # live files
    for p in sorted(HTML_DIR.glob("live_*.html")):
        html = p.read_text(encoding="utf-8", errors="ignore")
        kind = "board" if "board" in p.name else "reponline" if "reponline" in p.name else page_kind(p.name, html)
        digest = p.stem.split("_")[-1]
        url = LIVE_URLS[0][1] if kind == "board" else LIVE_URLS[1][1]
        recs.append(
            {
                "kind": "live",
                "page_kind": kind,
                "year": LIVE_YEAR,
                "timestamp": f"{LIVE_YEAR}0101000000",
                "original": url,
                "digest": digest,
                "path": str(p.relative_to(ROOT)).replace("\\", "/"),
                "source_path": f"web:{urllib.parse.urlparse(url).netloc}{urllib.parse.urlparse(url).path}@{LIVE_YEAR}",
            }
        )
    # wayback digests
    cdx = load_cdx_cache()
    by_digest = {}
    for c in cdx:
        # keep earliest overall for metadata; year still from capture
        d = c["digest"]
        by_digest.setdefault(d, []).append(c)
    for p in sorted(HTML_DIR.glob("*.html")):
        if p.name.startswith("live_"):
            continue
        digest = p.stem
        html = p.read_text(encoding="utf-8", errors="ignore")
        variants = by_digest.get(digest, [])
        if variants:
            # emit one record per year that had this digest
            years_seen = set()
            for c in variants:
                y = int(c["year"])
                if y in years_seen:
                    continue
                years_seen.add(y)
                pk = page_kind(c["original"], html)
                recs.append(
                    {
                        **c,
                        "page_kind": pk,
                        "path": str(p.relative_to(ROOT)).replace("\\", "/"),
                        "source_path": (
                            f"wayback:{urllib.parse.urlparse(c['original']).netloc}"
                            f"{urllib.parse.urlparse(c['original']).path}"
                            f"@{y}/{digest}"
                        ),
                    }
                )
        else:
            # unknown provenance — skip unless filename is sha1-like
            pk = page_kind("", html)
            if pk == "unknown":
                continue
            recs.append(
                {
                    "kind": "wayback",
                    "page_kind": pk,
                    "year": LIVE_YEAR,
                    "timestamp": f"{LIVE_YEAR}0101000000",
                    "original": "",
                    "digest": digest,
                    "path": str(p.relative_to(ROOT)).replace("\\", "/"),
                    "source_path": f"wayback:unknown@{LIVE_YEAR}/{digest}",
                }
            )
    print("from-cache records", len(recs))
    return recs


def clean_text(el) -> str:
    if el is None:
        return ""
    return re.sub(r"\s+", " ", el.get_text(" ", strip=True)).strip()


def parse_location(loc: str) -> tuple[str | None, str | None]:
    loc = (loc or "").strip()
    if not loc:
        return None, None
    m = _LOC_RE.match(loc)
    if m:
        return m.group(1).strip(), m.group(2)
    # "City ST" without comma
    m2 = re.match(r"^(.+?)\s+([A-Z]{2})$", loc)
    if m2:
        return m2.group(1).strip(), m2.group(2)
    return loc, None


def state_token(raw: str) -> str | None:
    s = (raw or "").strip()
    if not s:
        return None
    up = s.upper()
    if up in _STATE_NAMES:
        return _STATE_NAMES[up]
    if len(s) == 2 and s.isalpha():
        return s.upper()
    if up == "CANADA":
        return "Canada"
    return s[:50]


_ROLE_JUNK = re.compile(
    r"\b(books?|store|view\s+all|amazon|fleece|vest|gift|click|menu|"
    r"registration\s+state\s+reps|affiliate\s+clubs|breed\s+standard|"
    r"constitution|bylaws|members\s+only|code\s+of\s+ethics|"
    r"download\s+forms|web\s+site\s+survey|trained\s+dog|culture\s+clash)\b",
    re.I,
)
_BOARD_ROLES = re.compile(
    r"\b(Administrative\s+Director|Pres(?:ident|\.)?\s*Emeritus|"
    r"Acting\s+Chair(?:person|man)?|Vice[- ]?Chair(?:person|man)?|"
    r"Chair(?:person|man)|Elected\s+Board\s+Member|Board\s+Member|"
    r"Treasurer|Secretary|Director|Business/?Legal\s+Manager|Advisory|"
    r"Founder)\b",
    re.I,
)


def _normalize_committee_name(raw: str) -> str:
    cname = re.sub(r"\s+", " ", (raw or "")).title()
    cname = re.sub(r"Breeder\s+Committee", "Breeders Committee", cname, flags=re.I)
    cname = re.sub(r"Representative\s+Committee", "Representatives Committee", cname, flags=re.I)
    return cname


def _committee_names_in_role(role_text: str) -> list[str]:
    names = []
    for m in _COMMITTEE_NAME_RE.finditer(role_text or ""):
        names.append(_normalize_committee_name(m.group(1)))
    # dedupe preserve order
    out, seen = [], set()
    for n in names:
        k = n.lower()
        if k in seen:
            continue
        seen.add(k)
        out.append(n)
    return out


def primary_board_role(role_html_text: str) -> str | None:
    """Return a normalized board role, or None if the cell is not a real role.

    Committee chairs keep the committee in the Board.Role value
    (e.g. 'Chairperson, Judges Committee') — never collapse those to bare
    'Chairperson', which is reserved for the club Board chair.
    """
    t = re.sub(r"\s+", " ", role_html_text or "").strip()
    if not t or _ROLE_JUNK.search(t):
        return None

    committees = _committee_names_in_role(t)
    is_vice = bool(re.search(r"\bVice[- ]?Chair(?:person|man)?\b", t, re.I))
    is_acting = bool(re.search(r"\bActing\s+Chair(?:person|man)?\b", t, re.I))
    is_chair = bool(re.search(r"\bChair(?:person|man)\b", t, re.I))

    # Committee chair(s) on the board — keep committee name(s) on Board.Role
    if committees and is_chair:
        chair_bits = [f"Chairperson, {c}" for c in committees]
        if is_vice:
            return ("Vice Chairperson; " + "; ".join(chair_bits))[:100]
        if is_acting:
            return ("Acting Chairperson; " + "; ".join(chair_bits))[:100]
        # Pure committee chair seat(s) — not the club Board Chairperson
        return "; ".join(chair_bits)[:100]

    for pat, label in (
        (r"\bAdministrative\s+Director\b", "Administrative Director"),
        (r"\bFounder\b.*\bEmeritus\b|\bPres\.?\s*Emeritus\b|\bPresident\s+Emeritus\b", "President Emeritus"),
        (r"\bBusiness/?Legal\s+Manager\b", "Business/Legal Manager"),
        (r"\bActing\s+Chair(?:person|man)?\b", "Acting Chairperson"),
        (r"\bVice[- ]?Chair(?:person|man)?\b", "Vice Chairperson"),
        # Bare Chairperson = club Board chair only (no committee in text)
        (r"\bChair(?:person|man)\b", "Chairperson"),
        (r"\bElected\s+Board\s+Member\b", "Elected Board Member"),
        (r"\bBoard\s+Member\b", "Board Member"),
        (r"\bTreasurer\b", "Treasurer"),
        (r"\bSecretary\b", "Secretary"),
        (r"\bAdvisory\b", "Advisory"),
        (r"\bDirector\b", "Director"),
    ):
        if re.search(pat, t, re.I):
            return label
    if _BOARD_ROLES.search(t):
        return t[:100]
    # Unrecognized role text on a board page — do not invent "Board Member"
    return None


def committee_hits_from_role(name: str, role_text: str, city, state, phone, email) -> list[tuple[str, PersonHit]]:
    out = []
    for cname in _committee_names_in_role(role_text or ""):
        role = "Chairperson" if re.search(r"Chair", role_text or "", re.I) else "Member"
        hit = PersonHit(
            name=name,
            role=role,
            city=city,
            state=state,
            phone=phone,
            extra=email,
        )
        out.append((cname, hit))
    return out


def _name_and_email_from_cell(cell) -> tuple[str, str | None]:
    """Extract person name + email from a TD/LI-like element without letting mailto text replace the name."""
    if cell is None:
        return "", None
    email = None
    # Prefer mailto href
    for a in cell.find_all("a", href=True) if hasattr(cell, "find_all") else []:
        href = str(a.get("href") or "")
        if href.lower().startswith("mailto:"):
            email = href.split(":", 1)[1].strip()
            break
    # Bold name preferred when present (common on mid-2010s reponline pages)
    bold = cell.find("b") if hasattr(cell, "find") else None
    if bold:
        name = norm_name(_EMAIL_RE.sub("", clean_text(bold)))
        if plausible_person(name):
            if not email:
                em = _EMAIL_RE.search(clean_text(cell))
                if em:
                    email = em.group(0)
            return name, email
    raw = clean_text(cell)
    if not email:
        em = _EMAIL_RE.search(raw)
        if em:
            email = em.group(0)
    # Strip emails and trailing role commas handled by caller
    name = norm_name(_EMAIL_RE.sub("", raw))
    # If first mailto anchor text is a real name (not an email), prefer it
    if hasattr(cell, "find"):
        a = cell.find("a", href=True)
        if a and str(a.get("href") or "").lower().startswith("mailto:"):
            an = norm_name(_EMAIL_RE.sub("", clean_text(a)))
            if plausible_person(an):
                name = an
    return name, email


_LI_CHUNK_RE = re.compile(r"<li[^>]*>(.*?)(?=<li|</ul|</ol)", re.I | re.S)
_NAV_NAME_RE = re.compile(
    r"\b(gift\s*store|affiliate|fleece|bylaws|constitution|registration|"
    r"home\s*page|click\s*here|jack\s*russell\s*terrier\s*club|"
    r"main\s*menu|members?\s*only|about\s+the|terrier\s+boutique|"
    r"why\s+support|breed\s+standard|local\s+clubs|sample\s+contracts|"
    r"true\s+grit|download\s+forms|join\s+the|state\s+reps?|"
    r"jrtca\s+state\s+reps?|real\s+jack|membership\s+benefits|"
    r"jrtca\s+registry|jrtca\s+main\s+menu|web\s+site|"
    r"book\s*store|view\s+book|all\s+books|found\s+dogs)\b",
    re.I,
)
_BOARD_ROLE_HINT = re.compile(
    r"Chair|Director|Treasurer|Secretary|Board\s+Member|Emeritus|Vice",
    re.I,
)


def _parse_li_chunk(chunk_html: str) -> tuple[str, str | None, str]:
    """Return (name, email, role_text) from one legacy <LI> inner HTML chunk."""
    frag = BeautifulSoup(f"<div>{chunk_html}</div>", "html.parser")
    root = frag.div
    email = None
    name = ""
    for a in root.find_all("a", href=True):
        href = str(a.get("href") or "")
        if href.lower().startswith("mailto:"):
            email = href.split(":", 1)[1].strip()
            an = norm_name(_EMAIL_RE.sub("", clean_text(a)))
            if plausible_person(an):
                name = an
            break
    raw = clean_text(root)
    if not name:
        # text before first comma is usually the name
        head = raw.split(",", 1)[0]
        name = norm_name(_EMAIL_RE.sub("", head))
    role_text = ""
    if "," in raw:
        role_text = _EMAIL_RE.sub("", raw.split(",", 1)[1]).strip(" ,")
        # Drop nested link labels like leftover "Trial Committee" already in role
        role_text = re.sub(r"\s+", " ", role_text)
    if not email:
        em = _EMAIL_RE.search(raw)
        if em:
            email = em.group(0)
    return name, email, role_text


def _parse_board_list_items(html: str) -> tuple[list[PersonHit], dict[str, list[PersonHit]]]:
    """Legacy terrier.com board.php3 UL/LI rosters (often unclosed <LI> tags)."""
    board: list[PersonHit] = []
    committees: dict[str, list[PersonHit]] = defaultdict(list)
    # Prefer body content after the visible Board heading (skip title-only hit when possible)
    low = html.lower()
    start = -1
    for marker in (
        ">jrtca board of directors",
        "jrtca board of directors<",
        ">board of directors<",
        "board of directors",
    ):
        start = low.find(marker)
        if start >= 0:
            break
    section = html[start:] if start >= 0 else html
    # Stop before later major club sections (avoid cutting on nav "True Grit" links)
    for stop in (
        "state representatives<",
        "directory of breeders",
        "new registrations",
        "<!-- footer",
        '<footer',
    ):
        i = section.lower().find(stop)
        if i > 400:
            section = section[:i]
            break
    for m in _LI_CHUNK_RE.finditer(section):
        name, email, role_text = _parse_li_chunk(m.group(1))
        if not plausible_person(name):
            continue
        if _NAV_NAME_RE.search(name) or _NAV_NAME_RE.search(role_text):
            continue
        if name.lower() in ("home", "jrtca", "trial"):
            continue
        # Legacy LI pages usually include a role; skip bare nav labels
        if role_text and not _BOARD_ROLE_HINT.search(role_text):
            # Still allow plain members with no role on early pages
            if email is None:
                continue
        if role_text:
            role = primary_board_role(role_text)
            if role is None and not committee_hits_from_role(name, role_text, None, None, None, email):
                continue
            if role is None:
                role = "Board Member"
            if re.search(r"\bEmeritus\b", role_text, re.I):
                role = "President Emeritus"
        else:
            role = "Board Member"
        board.append(PersonHit(name=name, role=role, extra=email))
        for cname, hit in committee_hits_from_role(name, role_text, None, None, None, email):
            if plausible_person(hit.name):
                committees[cname].append(hit)
    return board, committees


def parse_board_html(html: str) -> tuple[list[PersonHit], dict[str, list[PersonHit]]]:
    soup = BeautifulSoup(html, "html.parser")
    board: list[PersonHit] = []
    committees: dict[str, list[PersonHit]] = defaultdict(list)
    # Prefer tables with Name/Position headers OR class=board body cells
    for table in soup.find_all("table"):
        headers = [clean_text(th).lower() for th in table.find_all("th")]
        if not headers:
            first = table.find("tr")
            if first:
                headers = [clean_text(td).lower() for td in first.find_all(["td", "th"])]
        joined = " ".join(headers)
        has_board_class = bool(table.find(attrs={"class": re.compile(r"\bboard\b", re.I)}))
        looks_like = (
            ("name" in joined and ("position" in joined or "role" in joined or "email" in joined))
            or ("director" in joined and "board" in joined)
            or ("officer" in joined and "name" in joined)
        )
        if not looks_like and not has_board_class:
            continue
        rows = table.find_all("tr")
        # Skip header row when th present or first row looks like headers
        start = 0
        if table.find("th"):
            start = 1
        elif headers and any(h in ("name", "position", "email") for h in headers):
            start = 1
        for tr in rows[start:]:
            cells = tr.find_all(["td", "th"])
            if len(cells) < 2:
                continue
            name, email_from_name = _name_and_email_from_cell(cells[0])
            if name.lower() in ("name", "member", ""):
                continue
            if not plausible_person(name):
                continue
            role_text = clean_text(cells[1])
            # Some legacy tables are Name | Role | Email (no location)
            loc = ""
            email_cell = ""
            if len(cells) >= 4:
                loc = clean_text(cells[2])
                email_cell = clean_text(cells[3])
            elif len(cells) == 3:
                third = clean_text(cells[2])
                if _EMAIL_RE.search(third):
                    email_cell = third
                else:
                    loc = third
            city, st = parse_location(loc)
            email = email_from_name
            em = _EMAIL_RE.search(email_cell)
            if em:
                email = em.group(0)
            phone = None
            ph = _PHONE_RE.search(role_text + " " + loc + " " + email_cell)
            if ph:
                phone = ph.group(1)
            role = primary_board_role(role_text)
            if role is None and not committee_hits_from_role(name, role_text, city, st, phone, email):
                continue
            if role is None:
                role = "Board Member"
            if not plausible_person(name):
                continue
            board.append(
                PersonHit(
                    name=name,
                    role=role,
                    city=city,
                    state=st,
                    phone=phone,
                    extra=email,
                )
            )
            for cname, hit in committee_hits_from_role(name, role_text, city, st, phone, email):
                if plausible_person(hit.name):
                    committees[cname].append(hit)
    # Legacy UL/LI board pages (terrier.com board.php3) — only when table parse found nobody
    list_board, list_comms = _parse_board_list_items(html)
    board = [
        h
        for h in board
        if plausible_person(h.name) and not _NAV_NAME_RE.search(h.name)
    ]
    list_board = [
        h
        for h in list_board
        if plausible_person(h.name) and not _NAV_NAME_RE.search(h.name)
    ]
    if not board and list_board:
        board = list_board
        committees = defaultdict(list, list_comms)
    elif list_board:
        for cn, members in list_comms.items():
            committees[cn].extend(members)
    # Fallback: plain text "Name - Role"
    if not board:
        text = soup.get_text("\n", strip=True)
        for m in re.finditer(
            r"([A-Z][A-Za-z'\-]+(?:\s+[A-Z][A-Za-z'\-]+){1,3})\s*[-–:]\s*"
            r"(Chair(?:person|man)|Vice[- ]?Chair(?:person|man)|Director|Secretary|Treasurer|"
            r"Elected Board Member|Board Member|Administrative Director)[^\n]{0,80}",
            text,
        ):
            name = norm_name(m.group(1))
            if not plausible_person(name) or _NAV_NAME_RE.search(name):
                continue
            role = primary_board_role(m.group(0))
            if role is None:
                continue
            board.append(PersonHit(name=name, role=role))
    # Drop nav junk that sneaks through table parses
    board = [
        h
        for h in board
        if plausible_person(h.name)
        and not _NAV_NAME_RE.search(h.name)
        and h.role
        and not _ROLE_JUNK.search(h.role or "")
    ]
    # dedupe board
    seen = set()
    board_out = []
    for h in board:
        k = (name_key(h.name), (h.role or "").lower())
        if k in seen:
            continue
        seen.add(k)
        board_out.append(h)
    committees_out: dict[str, list[PersonHit]] = {}
    for cname, members in committees.items():
        s2 = set()
        uniq = []
        for h in members:
            k = (name_key(h.name), (h.role or "").lower())
            if k in s2:
                continue
            s2.add(k)
            uniq.append(h)
        committees_out[cname] = uniq
    return board_out, committees_out


def parse_reponline_html(html: str) -> list[PersonHit]:
    soup = BeautifulSoup(html, "html.parser")
    hits: list[PersonHit] = []
    for table in soup.find_all("table"):
        headers = [clean_text(th).lower() for th in table.find_all("th")]
        joined = " ".join(headers)
        if headers and not any(x in joined for x in ("state", "representative", "name", "phone")):
            continue
        rows = table.find_all("tr")
        start = 1 if table.find("th") else 0
        for tr in rows[start:]:
            cells = tr.find_all(["td", "th"])
            if len(cells) < 2:
                continue
            st_raw = clean_text(cells[0])
            if st_raw.lower() in ("state", ""):
                continue
            name, email = _name_and_email_from_cell(cells[1])
            if _NAV_NAME_RE.search(name or ""):
                continue
            st = state_token(st_raw)
            # Require a recognizable state / Canada / province-like token
            if not st or len(st) > 24 or _NAV_NAME_RE.search(st_raw):
                continue
            if st not in _STATE_NAMES.values() and st not in ("Canada", "DC") and len(st) != 2:
                # Allow full names already mapped; reject garbage like nav blobs
                if st.upper() not in _STATE_NAMES and st.title() not in (
                    "Canada",
                ):
                    continue
            phone = None
            if len(cells) > 2:
                ph = _PHONE_RE.search(clean_text(cells[2]))
                if ph:
                    phone = ph.group(1)
            names = split_couple_name(name) or ([name] if plausible_person(name) else [])
            for nm in names:
                if not plausible_person(nm):
                    continue
                hits.append(
                    PersonHit(
                        name=nm,
                        role="State Representative",
                        state=st,
                        phone=phone,
                        extra=email,
                    )
                )
    if not hits:
        # older free-form pages
        text = soup.get_text("\n", strip=True)
        for m in re.finditer(
            r"(?m)^("
            + "|".join(re.escape(n.title()) for n in sorted(_STATE_NAMES, key=len, reverse=True))
            + r"|Canada)\s*[:\-]\s*([A-Z][A-Za-z'\-]+(?:\s+[A-Z][A-Za-z'\-]+){1,3})",
            text,
        ):
            st = state_token(m.group(1))
            name = norm_name(m.group(2))
            if plausible_person(name):
                hits.append(PersonHit(name=name, role="State Representative", state=st))
    seen = set()
    out = []
    for h in hits:
        k = (name_key(h.name), h.state or "")
        if k in seen:
            continue
        seen.add(k)
        out.append(h)
    return out


def parse_committee_html(html: str) -> dict[str, list[PersonHit]]:
    """Best-effort parse of dedicated committee roster pages."""
    soup = BeautifulSoup(html, "html.parser")
    title = clean_text(soup.find("title"))
    cname = None
    m = _COMMITTEE_NAME_RE.search(title or "")
    if m:
        cname = re.sub(r"\s+", " ", m.group(1)).title()
    committees: dict[str, list[PersonHit]] = defaultdict(list)
    # If page has section headers
    text = soup.get_text("\n", strip=True)
    current = cname
    for line in text.splitlines():
        hm = _COMMITTEE_NAME_RE.search(line)
        if hm and len(line) < 80:
            current = re.sub(r"\s+", " ", hm.group(1)).title()
            continue
        if not current:
            continue
        nm = re.match(
            r"^([A-Z][A-Za-z'\-]+(?:\s+[A-Z][A-Za-z'\-]+){1,3})(?:\s*[-–,]\s*(Chair(?:person|man)|Member|Secretary))?$",
            line.strip(),
        )
        if not nm:
            continue
        name = norm_name(nm.group(1))
        if not plausible_person(name):
            continue
        role = nm.group(2) or "Member"
        if role.lower().startswith("chair"):
            role = "Chairperson"
        committees[current].append(PersonHit(name=name, role=role))
    # Also tables
    board, from_board = parse_board_html(html)
    for cn, members in from_board.items():
        committees[cn].extend(members)
    if cname and board:
        for h in board:
            committees[cname].append(h)
    out = {}
    for cn, members in committees.items():
        s = set()
        uniq = []
        for h in members:
            k = (name_key(h.name), (h.role or "").lower())
            if k in s:
                continue
            s.add(k)
            uniq.append(h)
        if uniq:
            out[cn] = uniq
    return out


def parse_record(rec: dict) -> MetaBundle | None:
    path = ROOT / rec["path"]
    if not path.exists():
        return None
    html = path.read_text(encoding="utf-8", errors="ignore")
    year = int(rec["year"])
    src = rec["source_path"]
    pk = rec.get("page_kind") or page_kind(rec.get("original") or "", html)
    bundle = MetaBundle(year=year, source=src)
    if pk == "board":
        board, committees = parse_board_html(html)
        bundle.board = board
        bundle.committees = committees
    elif pk == "reponline":
        bundle.state_reps = parse_reponline_html(html)
    elif pk == "committee":
        bundle.committees = parse_committee_html(html)
    else:
        # try both
        board, committees = parse_board_html(html)
        reps = parse_reponline_html(html)
        if board or committees:
            bundle.board = board
            bundle.committees = committees
        if reps:
            bundle.state_reps = reps
        if not (bundle.board or bundle.committees or bundle.state_reps):
            return None
    if not (bundle.board or bundle.committees or bundle.state_reps):
        return None
    return bundle


def augment_owner_contacts(cur, hits: list[PersonHit], note: str, *, apply: bool) -> tuple[int, int]:
    """Fill empty Owner contact fields + Notes for matched names. Returns (matched, unmatched)."""
    matched = unmatched = 0
    has_email = False
    has_notes = False
    try:
        cur.execute("SELECT COL_LENGTH('sResults.Owner','Email')")
        has_email = cur.fetchone()[0] is not None
        cur.execute("SELECT COL_LENGTH('sResults.Owner','Notes')")
        has_notes = cur.fetchone()[0] is not None
    except Exception:
        pass
    for h in hits:
        if not plausible_person(h.name):
            continue
        cur.execute(
            "SELECT OwnerID, Address, City, State, PostalCode, Phone"
            + (", Email" if has_email else "")
            + (", Notes" if has_notes else "")
            + " FROM sResults.Owner WHERE OwnerName=?",
            h.name[:255],
        )
        row = cur.fetchone()
        if not row:
            # first-initial + last unique
            parts = norm_name(h.name).split()
            if len(parts) >= 2:
                last = parts[-1]
                cur.execute(
                    "SELECT OwnerID, OwnerName FROM sResults.Owner WHERE OwnerName LIKE ?",
                    f"% {last}",
                )
                cand = []
                nk = name_key(h.name)
                for r in cur.fetchall():
                    on = r[1] or ""
                    if name_key(on) == nk or (
                        on.strip().lower().endswith(last.lower())
                        and (on.strip()[:1] or "").lower() == parts[0][0].lower()
                    ):
                        cand.append(r)
                if len(cand) == 1:
                    cur.execute(
                        "SELECT OwnerID, Address, City, State, PostalCode, Phone"
                        + (", Email" if has_email else "")
                        + (", Notes" if has_notes else "")
                        + " FROM sResults.Owner WHERE OwnerID=?",
                        int(cand[0][0]),
                    )
                    row = cur.fetchone()
        if not row:
            unmatched += 1
            continue
        matched += 1
        if not apply:
            continue
        oid = int(row[0])
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
            h.address or "",
            h.city or "",
            h.state or "",
            h.postal or "",
            h.phone or "",
            oid,
        )
        if has_email and h.extra:
            cur.execute(
                "UPDATE sResults.Owner SET Email=COALESCE(NULLIF(?,''), Email) WHERE OwnerID=?",
                h.extra,
                oid,
            )
        if has_notes and note:
            try:
                cur.execute("SELECT Notes FROM sResults.Owner WHERE OwnerID=?", oid)
                old = cur.fetchone()[0]
                cur.execute(
                    "UPDATE sResults.Owner SET Notes=? WHERE OwnerID=?",
                    append_note(old, note),
                    oid,
                )
            except Exception:
                pass
    return matched, unmatched


def load_bundles(bundles: list[MetaBundle], *, apply: bool) -> dict:
    cn = pyodbc.connect(CONN, timeout=30, autocommit=True)
    cur = cn.cursor()
    cur.execute("SET LOCK_TIMEOUT 15000")
    ensure_schema(cur)
    totals = defaultdict(int)
    unmatched_reps: list[str] = []
    for bundle in bundles:
        stats = apply_bundle(cur, bundle, apply=apply)
        for k, v in stats.items():
            totals[k] += v
        # Extra Owner augment for board/committee (state_rep already handled in apply_bundle)
        board_hits = list(bundle.board)
        for members in bundle.committees.values():
            board_hits.extend(members)
        if board_hits and bundle.year:
            m, u = augment_owner_contacts(
                cur,
                board_hits,
                f"JRTCA Board/Committee ({bundle.year})",
                apply=apply,
            )
            totals["owner_aug_board"] += m
            totals["owner_unmatched_board"] += u
        # Track state rep unmatched (apply_bundle doesn't report them)
        for h in bundle.state_reps:
            if not plausible_person(h.name):
                continue
            cur.execute(
                "SELECT OwnerID FROM sResults.Owner WHERE OwnerName=?",
                h.name[:255],
            )
            if not cur.fetchone():
                unmatched_reps.append(f"{bundle.year}\t{h.state or ''}\t{h.name}")
            # Also push email for matched state reps (apply_bundle skips Email)
            if h.extra and apply:
                cur.execute(
                    "SELECT COL_LENGTH('sResults.Owner','Email')"
                )
                if cur.fetchone()[0] is not None:
                    cur.execute(
                        """
                        UPDATE sResults.Owner
                        SET Email=COALESCE(NULLIF(?,''), Email)
                        WHERE OwnerName=? AND (Email IS NULL OR Email='')
                        """,
                        h.extra,
                        h.name[:255],
                    )
    cn.close()
    totals["unmatched_state_rep_names"] = len(set(unmatched_reps))
    report = ARCHIVE / "unmatched_state_reps.txt"
    report.write_text("\n".join(sorted(set(unmatched_reps))), encoding="utf-8")
    return dict(totals)


def bundles_to_jsonable(bundles: list[MetaBundle]) -> list[dict]:
    out = []
    for b in bundles:
        out.append(
            {
                "year": b.year,
                "source": b.source,
                "board": [asdict(h) for h in b.board],
                "committees": {k: [asdict(h) for h in v] for k, v in b.committees.items()},
                "state_reps": [asdict(h) for h in b.state_reps],
            }
        )
    return out


def validate_db() -> None:
    cn = pyodbc.connect(CONN, timeout=30)
    cur = cn.cursor()
    print("\n=== DB validation ===")
    for table in ("Board", "Committee", "StateRepresentative"):
        try:
            cur.execute(f"SELECT COUNT(*) FROM sResults.[{table}]")
            n = cur.fetchone()[0]
            cur.execute(
                f"""
                SELECT Year, COUNT(*) FROM sResults.[{table}]
                GROUP BY Year ORDER BY Year
                """
            )
            by_year = cur.fetchall()
            print(f"{table}: {n} rows; years:", ", ".join(f"{y}:{c}" for y, c in by_year[:30]),
                  ("..." if len(by_year) > 30 else ""))
        except Exception as e:
            print(f"{table}: ERROR {e}")
    # Spot-check 2026 live board names
    cur.execute(
        """
        SELECT MemberName, Role FROM sResults.Board WHERE Year=2026 ORDER BY MemberName
        """
    )
    rows = cur.fetchall()
    print("2026 Board:", rows)
    cur.execute(
        "SELECT COUNT(*) FROM sResults.StateRepresentative WHERE Year=2026"
    )
    print("2026 StateReps:", cur.fetchone()[0])
    cur.execute(
        """
        SELECT TOP 5 MemberName, State, OwnerID FROM sResults.StateRepresentative
        WHERE Year=2026 ORDER BY State, MemberName
        """
    )
    print("2026 StateRep sample:", cur.fetchall())
    cur.execute(
        """
        SELECT COUNT(*) FROM sResults.Owner
        WHERE Notes LIKE '%JRTCA State Representative%'
           OR Notes LIKE '%JRTCA Board/Committee%'
        """
    )
    try:
        print("Owner notes with JRTCA org tags:", cur.fetchone()[0])
    except Exception as e:
        print("Owner notes check:", e)
    cn.close()


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--apply", action="store_true", help="Write to SQL Server (default dry-run)")
    ap.add_argument("--dry-run", action="store_true", help="Explicit dry-run (default)")
    ap.add_argument("--from-cache", action="store_true", help="Skip CDX/download; parse html cache")
    ap.add_argument("--live-only", action="store_true", help="Only fetch/parse live pages")
    ap.add_argument("--skip-download", action="store_true", help="Use CDX list + existing html only")
    args = ap.parse_args()
    apply = bool(args.apply) and not args.dry_run

    ensure_dirs()
    file_recs: list[dict] = []

    if args.from_cache:
        file_recs = load_manifest_files()
    else:
        live = download_live()
        file_recs.extend(live)
        if not args.live_only:
            captures = inventory_cdx()
            if not captures and CDX_PATH.exists():
                print("CDX empty/fail; falling back to cached cdx.json")
                captures = load_cdx_cache()
            selected = select_captures(captures)
            if args.skip_download:
                # attach paths if present
                for c in selected:
                    p = HTML_DIR / f"{c['digest']}.html"
                    if p.exists():
                        html = p.read_text(encoding="utf-8", errors="ignore")
                        file_recs.append(
                            {
                                **c,
                                "page_kind": page_kind(c["original"], html),
                                "path": str(p.relative_to(ROOT)).replace("\\", "/"),
                                "source_path": (
                                    f"wayback:{urllib.parse.urlparse(c['original']).netloc}"
                                    f"{urllib.parse.urlparse(c['original']).path}"
                                    f"@{c['year']}/{c['digest']}"
                                ),
                            }
                        )
            else:
                file_recs.extend(download_wayback(selected))

    # Prefer latest capture per (year, page_kind) for load speed/accuracy within a year.
    # Still keep all parsed digests in parsed_records via full_bundles below.
    scored: list[tuple[str, dict, MetaBundle]] = []
    parse_stats = defaultdict(int)
    for rec in file_recs:
        b = parse_record(rec)
        if not b:
            parse_stats["empty"] += 1
            continue
        parse_stats["ok"] += 1
        parse_stats["board_people"] += len(b.board)
        parse_stats["committee_people"] += sum(len(v) for v in b.committees.values())
        parse_stats["state_reps"] += len(b.state_reps)
        pk = rec.get("page_kind") or "unknown"
        scored.append((pk, rec, b))

    def _bundle_richness(b: MetaBundle) -> tuple[int, int, int]:
        # Prefer real roster size; board pages with only nav junk score near zero after filters.
        return (
            len(b.board),
            len(b.state_reps),
            sum(len(v) for v in b.committees.values()),
        )

    # Prefer richest parse per (year, page_kind); break ties with latest timestamp.
    best: dict[tuple[int, str], tuple[tuple[int, int, int], str, MetaBundle]] = {}
    for pk, rec, b in scored:
        key = (int(b.year or 0), pk)
        ts = str(rec.get("timestamp") or "")
        rich = _bundle_richness(b)
        prev = best.get(key)
        if prev is None or rich > prev[0] or (rich == prev[0] and ts >= prev[1]):
            best[key] = (rich, ts, b)
    bundles = [v[2] for _, v in sorted(best.items(), key=lambda kv: (kv[0][0], kv[0][1]))]
    parse_stats["load_bundles_collapsed"] = len(bundles)

    all_parsed = [b for _, _, b in scored]
    PARSED_PATH.write_text(
        json.dumps(
            {
                "stats": dict(parse_stats),
                "collapsed_for_load": bundles_to_jsonable(bundles),
                "all_captures": bundles_to_jsonable(all_parsed),
            },
            indent=2,
            ensure_ascii=False,
        ),
        encoding="utf-8",
    )
    print(
        "parsed captures",
        len(all_parsed),
        "collapsed load bundles",
        len(bundles),
        "stats",
        dict(parse_stats),
        "->",
        PARSED_PATH,
    )

    print("load mode:", "APPLY" if apply else "DRY-RUN")
    totals = load_bundles(bundles, apply=apply)
    print("load totals:", totals)

    if apply:
        validate_db()
    else:
        # summarize parsed years
        by_year = defaultdict(lambda: {"board": 0, "committee": 0, "state_rep": 0})
        for b in bundles:
            by_year[b.year]["board"] += len(b.board)
            by_year[b.year]["committee"] += sum(len(v) for v in b.committees.values())
            by_year[b.year]["state_rep"] += len(b.state_reps)
        print("parsed by year (people mentions):")
        for y in sorted(by_year):
            print(f"  {y}: {by_year[y]}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
