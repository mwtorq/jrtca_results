#!/usr/bin/env python3
"""Parse True Grit PDFs (vols 47-50 = years 2023-2026) into TrialResults.

Extracts: Board, Committees, State Representatives, New Registrations,
Registered Kennel Prefixes, Trial/Super Earth Certificates, NHC.
"""
from __future__ import annotations

import argparse
import re
import sys
from collections import defaultdict
from dataclasses import dataclass, field
from datetime import date, datetime
from pathlib import Path

import fitz
import pyodbc

from remount_source_divisions import CONN
from yearbook_meta_ingest import (
    PersonHit,
    append_note,
    find_owner_id,
    insert_identity,
    name_key,
    next_id,
    norm_name,
    plausible_person,
)
from yearbook_meta_schema import ensure as ensure_yearbook_meta
import truegrit_schema

ROOT = Path(r"c:\Users\mw\OneDrive - timberwilde.net\repos\jrtca_results")
TG_DIR = ROOT / "True Grit"

VOL_YEAR = {47: 2023, 48: 2024, 49: 2025, 50: 2026}

_STATE_NAMES = {
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
    "WEST VIRGINIA": "WV", "WISCONSIN": "WI", "WYOMING": "WY", "CANADA": "Canada",
}
_US_ABBR = set(_STATE_NAMES.values()) | {"DC"}
_PHONE_RE = re.compile(r"(\(?\d{3}\)?[-.\s]?\d{3}[-.\s]?\d{4})")
_EMAIL_RE = re.compile(r"[\w.+-]+@[\w.-]+\.\w+")
_PERIOD_RE = re.compile(
    r"from\s+([A-Za-z]+\s+\d{1,2},\s+\d{4})\s+through\s+([A-Za-z]+\s+\d{1,2},\s+\d{4})",
    re.I,
)
_ZIP_RE = re.compile(r"\b(\d{5})(?:-\d{4})?\b")
_CITY_ST_ZIP = re.compile(
    r"^([A-Za-z .'\-]+),\s*([A-Z]{2})\s+(\d{5}(?:-\d{4})?)$"
)
_QUARRY = {
    "groundhog", "opossum", "raccoon", "nutria", "red fox", "fox",
    "woodchuck", "badger", "coyote", "rat",
}
_SKIP_WORDS = {
    "name", "of", "terrier", "owner", "breeder", "state", "in", "judge",
    "trial", "quarry", "prefix", "true", "grit", "volume", "please", "note",
    "transferred", "from", "to", "the", "listings", "represent", "period",
}


@dataclass
class IssueMeta:
    path: Path
    volume: int
    issue: int
    year: int
    period_start: date | None = None
    period_end: date | None = None


@dataclass
class TGBundle:
    meta: IssueMeta
    board: list[PersonHit] = field(default_factory=list)
    committees: dict[str, list[PersonHit]] = field(default_factory=dict)
    state_reps: list[PersonHit] = field(default_factory=list)
    registrations: list[dict] = field(default_factory=list)
    kennel_prefixes: list[dict] = field(default_factory=list)
    trial_certs: list[dict] = field(default_factory=list)
    nhc: list[dict] = field(default_factory=list)


def parse_issue_name(path: Path) -> IssueMeta | None:
    path = Path(path)
    if not path.is_absolute():
        path = (ROOT / path).resolve()
    else:
        path = path.resolve()
    m = re.search(r"tgrit_(\d+)n(\d+)", path.name, re.I)
    if not m:
        return None
    vol, num = int(m.group(1)), int(m.group(2))
    year = VOL_YEAR.get(vol)
    if not year:
        return None
    return IssueMeta(path=path, volume=vol, issue=num, year=year)


def _parse_mdy(s: str) -> date | None:
    for fmt in ("%B %d, %Y", "%b %d, %Y"):
        try:
            return datetime.strptime(s.strip(), fmt).date()
        except ValueError:
            continue
    return None


def page_words(page) -> list[tuple]:
    return page.get_text("words")  # x0,y0,x1,y1,word,block,line,word_no


def words_to_lines(words, y_tol: float = 3.0) -> list[tuple[float, list]]:
    buckets: dict[float, list] = {}
    for w in words:
        y = w[1]
        key = None
        for k in buckets:
            if abs(k - y) <= y_tol:
                key = k
                break
        if key is None:
            key = y
            buckets[key] = []
        buckets[key].append(w)
    out = []
    for y in sorted(buckets):
        out.append((y, sorted(buckets[y], key=lambda w: w[0])))
    return out


def line_text(ws: list) -> str:
    return " ".join(w[4] for w in ws)


def split_columns(ws: list, mid_x: float) -> tuple[list, list]:
    left = [w for w in ws if (w[0] + w[2]) / 2 < mid_x]
    right = [w for w in ws if (w[0] + w[2]) / 2 >= mid_x]
    return left, right


def find_pages(doc, pattern: re.Pattern) -> list[int]:
    hits = []
    for i in range(doc.page_count):
        if pattern.search(doc.load_page(i).get_text("text")):
            hits.append(i)
    return hits


def extract_period(doc) -> tuple[date | None, date | None]:
    # Prefer the certificate/registration note page (mentions kennel prefixes)
    candidates: list[tuple[int, date, date]] = []
    for i in range(doc.page_count):
        t = doc.load_page(i).get_text("text")
        m = _PERIOD_RE.search(t)
        if not m:
            continue
        a, b = _parse_mdy(m.group(1)), _parse_mdy(m.group(2))
        if not a or not b:
            continue
        score = 0
        if re.search(r"kennel prefixes|New Registrations|certificates", t, re.I):
            score += 2
        if a.year >= 2022:
            score += 1
        candidates.append((score, a, b))
    if not candidates:
        return None, None
    candidates.sort(key=lambda x: (x[0], x[1]), reverse=True)
    return candidates[0][1], candidates[0][2]


# ----- Board / committees -------------------------------------------------


def parse_board_page(text: str) -> tuple[list[PersonHit], dict[str, list[PersonHit]]]:
    board: list[PersonHit] = []
    committees: dict[str, list[PersonHit]] = {}
    lines = [re.sub(r"\s+", " ", ln).strip() for ln in text.splitlines()]
    lines = [ln for ln in lines if ln]

    section = None
    committee = None
    current: PersonHit | None = None

    def flush():
        nonlocal current
        if not current or not plausible_person(current.name):
            current = None
            return
        if section == "board":
            board.append(current)
        elif section == "committee" and committee:
            committees.setdefault(committee, []).append(current)
        current = None

    board_start = re.compile(r"^BOARD OF DIRECTORS\s*:?\s*$", re.I)
    club_office = re.compile(r"^CLUB OFFICE\s*:?\s*$", re.I)
    comm_hdr = re.compile(
        r"^([A-Z][A-Z0-9 /&\-]{2,60}?(?:COMMITTEE|SUB-?COMMITTEE|SUBCOMMITTEE))\s*:?\s*$",
        re.I,
    )
    name_role = re.compile(
        r"^([A-Z][A-Za-z'\-]+(?:\s+[A-Z][A-Za-z'\-]+){1,3})"
        r"(?:,\s*(.+))?$"
    )

    for ln in lines:
        if board_start.match(ln):
            flush()
            section = "board"
            committee = None
            continue
        if club_office.match(ln):
            flush()
            section = "office"
            committee = None
            continue
        m = comm_hdr.match(ln)
        if m:
            flush()
            section = "committee"
            committee = re.sub(r"\s+", " ", m.group(1)).title().replace("Sub-Committee", "Sub-Committee")
            committee = committee.replace("Sub Committee", "Sub-Committee")
            continue
        if re.match(r"^BOARD OF DIRECTORS\s*&\s*COMMITTEES", ln, re.I):
            flush()
            break
        if section not in ("board", "committee"):
            continue
        if _EMAIL_RE.fullmatch(ln) or "@" in ln and " " not in ln.strip():
            continue
        if _PHONE_RE.fullmatch(ln.replace(" ", "")):
            if current:
                current.phone = _PHONE_RE.search(ln).group(1)
            continue
        if _CITY_ST_ZIP.match(ln):
            if current:
                mm = _CITY_ST_ZIP.match(ln)
                current.city, current.state, current.postal = mm.group(1), mm.group(2), mm.group(3)
            continue
        if re.match(r"^\d", ln) or re.match(r"^(P\.?O\.?\s*Box|RR|Rt\.?)\b", ln, re.I):
            if current and not current.address:
                current.address = ln
            elif current:
                current.address = ((current.address or "") + " " + ln).strip()
            continue
        # name / role line
        # "Don Gaskell, Vice-Chair" or "Ted Ely, Chairperson," or "Dawn Weiss - Chairperson"
        ln2 = ln.replace(" - ", ", ").rstrip(",")
        # committee member "Name, email" or "Name email"
        em = _EMAIL_RE.search(ln2)
        email = em.group(0) if em else None
        name_part = ln2[: em.start()].strip(" ,") if em else ln2

        # Role-only continuations attached to prior name
        role_bits = []
        nm = name_role.match(name_part)
        if not nm:
            # "Name email" without comma
            parts = name_part.split()
            if len(parts) >= 2 and plausible_person(" ".join(parts[:2])):
                # try 2 or 3 token name
                for ntok in (3, 2):
                    cand = " ".join(parts[:ntok])
                    if plausible_person(cand):
                        flush()
                        current = PersonHit(name=norm_name(cand), role="Member" if section == "committee" else None)
                        if email:
                            current.extra = email
                        break
            continue

        name = norm_name(nm.group(1))
        rest = (nm.group(2) or "").strip()
        role = None
        if rest:
            # strip trailing emails already handled
            role = rest
            if re.search(r"chair|vice|director|coordinator|member", rest, re.I):
                role = rest.split(",")[0].strip()
            else:
                role = "Member" if section == "committee" else None
                if current and not current.role and rest:
                    # might be second role line for board member
                    pass
        if not plausible_person(name):
            # role continuation like "Judges Committee Chairperson" for previous
            if current and section == "board" and re.search(r"chair|committee", name_part, re.I):
                current.role = ((current.role or "") + " " + name_part).strip()
            continue
        flush()
        if section == "board":
            current = PersonHit(name=name, role=role or "Board Member")
        else:
            current = PersonHit(name=name, role=role or "Member")
        if email:
            current.extra = email

    flush()
    # Dedupe
    def dedupe(hits: list[PersonHit]) -> list[PersonHit]:
        seen = set()
        out = []
        for h in hits:
            k = (name_key(h.name), (h.role or "").lower())
            if k in seen:
                continue
            seen.add(k)
            out.append(h)
        return out

    board = dedupe(board)
    committees = {k: dedupe(v) for k, v in committees.items()}
    return board, committees


# ----- State reps ---------------------------------------------------------


def parse_state_reps_text(text: str) -> list[PersonHit]:
    hits: list[PersonHit] = []
    state = None
    lines = [re.sub(r"\s+", " ", ln).strip() for ln in text.splitlines() if ln.strip()]
    name_phone = re.compile(
        r"^([A-Z][A-Za-z'\-]+(?:\s+[A-Z][A-Za-z'\-]+){1,3}),\s*"
        r"(\(?\d{3}\)?[-.\s]?\d{3}[-.\s]?\d{4})"
    )
    for ln in lines:
        up = ln.upper()
        if up in _STATE_NAMES:
            state = _STATE_NAMES[up]
            continue
        if re.match(r"^JRTCA State Representatives", ln, re.I):
            continue
        if re.match(r"^Meet One of Your", ln, re.I):
            break
        if re.match(r"^TRUE GRIT|^Volume\b|^\d{1,3}$", ln, re.I):
            continue
        m = name_phone.match(ln)
        if m and state:
            name = norm_name(m.group(1))
            if plausible_person(name):
                hits.append(
                    PersonHit(
                        name=name,
                        role="State Representative",
                        state=state,
                        phone=m.group(2),
                    )
                )
            continue
        # name only then phone on next line already handled; phone-only skip
        if state and plausible_person(ln) and not _EMAIL_RE.search(ln):
            hits.append(PersonHit(name=norm_name(ln), role="State Representative", state=state))
    # dedupe
    seen = set()
    out = []
    for h in hits:
        k = (name_key(h.name), h.state or "")
        if k in seen:
            continue
        seen.add(k)
        out.append(h)
    return out


# ----- Columnar listing helpers -------------------------------------------


def _is_state_token(tok: str) -> bool:
    t = tok.strip()
    if t.upper() in _US_ABBR or t == "Canada":
        return True
    return False


def _clean_person_field(s: str) -> str:
    s = re.sub(r"\s+", " ", s).strip(" ,/")
    s = s.replace("/", " / ")
    s = re.sub(r"\s+", " ", s).strip()
    return s


def _discover_reg_schemas(lines: list[tuple[float, list]]) -> list[dict]:
    """New Registrations tables: Name / Owner / Breeder / State."""
    tables: list[dict] = []
    for y, ws in lines:
        toks = [(w[0], w[4]) for w in ws]
        labels = {t.lower().rstrip(":") for _, t in toks}
        if "owner" not in labels or "breeder" not in labels:
            continue
        name_idxs = [i for i, (_, t) in enumerate(toks) if t.lower() == "name"]
        if not name_idxs:
            continue
        for ni, idx in enumerate(name_idxs):
            x_name = toks[idx][0]
            x_right = toks[name_idxs[ni + 1]][0] - 1.0 if ni + 1 < len(name_idxs) else 1e9
            cols: dict[str, float] = {"dog": x_name}
            for x, t in toks[idx + 1 :]:
                if x >= x_right:
                    break
                tl = t.lower().rstrip(":")
                if tl in {"owner", "breeder", "state"} and tl not in cols:
                    cols[tl] = x
            if not {"owner", "breeder", "state"}.issubset(cols):
                continue
            tables.append(
                {"y": y, "x_left": x_name - 5.0, "x_right": x_right, "cols": cols}
            )
    return tables


def parse_registration_rows(page) -> list[dict]:
    """New Registrations via header column bands (Dog|Owner|Breeder|State)."""
    lines = words_to_lines(page_words(page), y_tol=2.5)
    rows: list[dict] = []
    # Limit to New Registrations section
    y0 = y1 = None
    for y, ws in lines:
        text = line_text(ws)
        if y0 is None and re.search(r"^New Registrations\b", text, re.I):
            y0 = y
            continue
        if y0 is not None and re.search(
            r"^New Recordings|^Registered Kennel|^Transfers\b", text, re.I
        ):
            y1 = y
            break
    if y0 is None:
        return []
    if y1 is None:
        y1 = lines[-1][0] + 1
    section = [(y, ws) for y, ws in lines if y0 < y < y1]
    tables = _discover_reg_schemas(section)
    for table in tables:
        use = table["cols"]
        for y, ws in section:
            if y <= table["y"] + 1:
                continue
            txt = line_text(ws)
            if re.search(r"Name of Terrier", txt, re.I):
                break
            fields = _assign_by_col_starts(
                ws, use, x_left=table["x_left"], x_right=table["x_right"], tol=10.0
            )
            dog = (fields.get("dog") or "").strip()
            owner = (fields.get("owner") or "").strip()
            breeder = (fields.get("breeder") or "").strip()
            st = (fields.get("state") or "").strip()
            # State column may include trailing "In" header bleed — take first token
            st_tok = st.split()[0] if st else ""
            if st_tok.upper() == "IN" and len(st.split()) == 1:
                # could be Indiana abbreviation... header leftover; skip empty dogs
                st_tok = ""
            if _is_state_token(st_tok):
                st_out = "Canada" if st_tok == "Canada" else st_tok.upper()
            else:
                st_out = None
            if len(dog) < 3 or len(owner) < 2:
                continue
            if dog.lower().startswith("name"):
                continue
            rows.append(
                {
                    "DogName": dog[:255],
                    "OwnerName": owner[:255],
                    "BreederName": breeder[:255] if breeder else None,
                    "State": st_out,
                }
            )
    seen = set()
    out = []
    for r in rows:
        k = (r["DogName"].lower(), (r.get("OwnerName") or "").lower())
        if k in seen:
            continue
        seen.add(k)
        out.append(r)
    return out


def parse_kennel_prefix_rows(page) -> list[dict]:
    """Parse 'Prefix | Owner | State' column (left or right — varies by issue)."""
    words = page_words(page)
    mid = page.rect.width / 2
    lines = words_to_lines(words, y_tol=4)
    rows: list[dict] = []
    in_section = False
    # Column bounds for the prefix table (None until header found)
    col_min: float | None = None
    col_max: float | None = None

    def _score_prefix_split(toks: list[str]) -> tuple[int, str, str, str | None] | None:
        if len(toks) < 3:
            return None
        st = None
        body = toks
        if _is_state_token(toks[-1]):
            st = toks[-1].upper() if toks[-1] != "Canada" else "Canada"
            body = toks[:-1]
        # If a couple marker exists, owner must include both sides of '&'
        amp_at = next((idx for idx, t in enumerate(body) if t == "&"), None)
        best = None
        for i in range(1, min(5, len(body))):
            prefix = " ".join(body[:i]).strip()
            owner = _clean_person_field(" ".join(body[i:]))
            if len(prefix) < 3 or len(owner) < 5:
                continue
            if prefix.lower() in {"name", "of", "terrier", "owner", "prefix", "state", "volume"} or prefix.endswith("&"):
                continue
            if owner.startswith("&"):
                continue
            if amp_at is not None and i > amp_at:
                # split cut through the couple — invalid
                continue
            if amp_at is not None and i <= amp_at and amp_at + 1 >= len(body):
                continue
            owner_probe = owner.split("/")[0].strip()
            if "&" in owner_probe:
                # "Jay & Rose Shoemaker" / "Donna & Mike Malone"
                ok_couple = bool(
                    re.match(
                        r"^[A-Z][A-Za-z'\-]+\s+&\s+[A-Z][A-Za-z'\-]+(?:\s+[A-Z][A-Za-z'\-]+)?$",
                        owner_probe,
                    )
                )
            else:
                ok_couple = False
            if not (plausible_person(owner_probe) or ok_couple or "/" in owner):
                continue
            score = 0
            if 2 <= i <= 3:
                score += 2
            elif i == 1:
                score += 1
            if plausible_person(owner_probe):
                score += 2
            if ok_couple:
                score += 3
            # Prefer owner starting with a capital name token
            if re.match(r"^[A-Z][a-z]", owner):
                score += 1
            if best is None or score > best[0]:
                best = (score, prefix, owner, st)
        return best

    for y, ws in lines:
        text = line_text(ws)
        if re.search(r"Registered Kennel Prefixes", text, re.I):
            in_section = True
            # Locate "Prefix Owner State" header on this or nearby lines to pin column
            continue
        if not in_section:
            continue
        if re.search(r"^Transfers\b|^CURRENT JRTCA|^Membership:", text, re.I):
            break
        # Header row pins the column
        if re.search(r"\bPrefix\b", text, re.I) and re.search(r"\bOwner\b", text, re.I):
            pref_words = [w for w in ws if w[4].lower() == "prefix"]
            if pref_words:
                px = pref_words[0][0]
                # column is the half containing Prefix
                if px < mid:
                    col_min, col_max = 0.0, mid
                else:
                    col_min, col_max = mid, page.rect.width
            continue
        if re.search(r"^Name of Terrier", text, re.I):
            continue
        if col_min is None:
            # fallback: use half that contained "Registered Kennel Prefixes"
            title_ws = [w for w in ws]  # noqa — keep scanning until header
            continue
        col = [w for w in ws if col_min <= w[0] < col_max]
        if not col:
            continue
        toks = [w[4] for w in col]
        scored = _score_prefix_split(toks)
        if not scored or scored[0] < 3:
            continue
        _, prefix, owner, st = scored
        rows.append(
            {
                "KennelPrefix": prefix[:100],
                "KennelName": prefix[:255],
                "OwnerName": owner[:255],
                "State": st,
            }
        )
    seen = set()
    out = []
    for r in rows:
        k = (r["KennelPrefix"].lower(), name_key(r["OwnerName"]))
        if k in seen:
            continue
        seen.add(k)
        out.append(r)
    return out


def _discover_table_schemas(
    lines: list[tuple[float, list]],
    *,
    want_fourth: str,
) -> list[dict]:
    """Each 'Name' on a header row opens a table band until the next 'Name' (or page end).

    Returns dicts: y, x_left, x_right, cols={dog,owner,judge,quarry|trial}.
    """
    tables: list[dict] = []
    for y, ws in lines:
        toks = [(w[0], w[4]) for w in ws]
        if not any(t.lower() == "owner" for _, t in toks):
            continue
        name_idxs = [i for i, (_, t) in enumerate(toks) if t.lower() == "name"]
        if not name_idxs:
            continue
        # Prefer rows that look like column headers
        labels_present = {t.lower().rstrip(":") for _, t in toks}
        if "owner" not in labels_present:
            continue
        if want_fourth not in labels_present and "judge" not in labels_present:
            continue
        for ni, idx in enumerate(name_idxs):
            x_name = toks[idx][0]
            x_right = toks[name_idxs[ni + 1]][0] - 1.0 if ni + 1 < len(name_idxs) else 1e9
            cols: dict[str, float] = {"dog": x_name}
            for x, t in toks[idx + 1 :]:
                if x >= x_right:
                    break
                tl = t.lower().rstrip(":")
                if tl in {"owner", "judge", "quarry", "trial", "breeder", "state", "prefix"} and tl not in cols:
                    cols[tl] = x
            if "owner" not in cols or "judge" not in cols:
                continue
            fourth = want_fourth if want_fourth in cols else ("trial" if "trial" in cols else "quarry" if "quarry" in cols else None)
            if not fourth:
                continue
            # normalize fourth key to want_fourth for callers
            if fourth != want_fourth and fourth in cols:
                cols[want_fourth] = cols[fourth]
            tables.append(
                {
                    "y": y,
                    "x_left": x_name - 5.0,
                    "x_right": x_right,
                    "cols": cols,
                    "fourth": want_fourth,
                }
            )
    return tables


def _assign_by_col_starts(
    ws: list, starts: dict[str, float], *, x_left: float, x_right: float, tol: float = 10.0
) -> dict[str, str]:
    """Assign words in [x_left, x_right) to columns via header x-starts + tolerance."""
    ordered = sorted(((lab, x) for lab, x in starts.items()), key=lambda p: p[1])
    fields: dict[str, list[str]] = {lab: [] for lab, _ in ordered}
    for w in sorted(ws, key=lambda w: w[0]):
        if w[0] < x_left or w[0] >= x_right:
            continue
        chosen = ordered[0][0]
        for lab, sx in ordered:
            if w[0] + tol >= sx:
                chosen = lab
            else:
                break
        fields[chosen].append(w[4])
    out = {}
    for k, v in fields.items():
        s = " ".join(v).strip()
        out[k] = _clean_person_field(s) if k in {"owner", "judge"} else s
    return out


def _valid_nhc_row(fields: dict[str, str]) -> bool:
    dog = fields.get("dog") or ""
    owner = fields.get("owner") or ""
    quarry = (fields.get("quarry") or "").strip()
    if len(dog) < 3 or len(owner) < 3 or not quarry:
        return False
    if quarry.lower() not in {q.lower() for q in _QUARRY}:
        # allow multi-word quarry already titled
        if not any(q in quarry.lower() for q in _QUARRY):
            return False
    # reject prose / headers
    if re.search(r"\b(photo|submit|online|gallery|section|include)\b", dog, re.I):
        return False
    return True


def _valid_trial_row(fields: dict[str, str]) -> bool:
    dog = fields.get("dog") or ""
    owner = fields.get("owner") or ""
    trial = fields.get("trial") or fields.get("quarry") or ""
    if len(dog) < 3 or len(owner) < 3 or len(trial) < 3:
        return False
    if re.search(r"\b(photo|submit|online|gallery|section|include|please|champion)\b", dog, re.I):
        return False
    if not re.search(
        r"(Trial|Fest|Classic|National|West End|Midwest|Northgate|Dogwood|"
        r"Wilderness|Museum|Magnolia|Frolic|Dream|Step|Fox|Yuletide|Tahoma|"
        r"Mid-America|Benefit)|[IVX]+\b|\b20\d{2}\b",
        trial,
        re.I,
    ):
        return False
    return True


def _title_anchors(lines: list[tuple[float, list]], kind: str) -> list[tuple[float, float]]:
    """Return (y, x0) anchors for section titles of this certificate kind."""
    anchors: list[tuple[float, float]] = []
    if kind == "Trial":
        # "Trial Certificates" but not when only Super Earth on line? allow both
        for y, ws in lines:
            for i, w in enumerate(ws):
                if w[4].lower() != "trial":
                    continue
                # next token Certificates
                if i + 1 < len(ws) and ws[i + 1][4].lower().startswith("cert"):
                    anchors.append((y, w[0]))
    elif kind == "Super Earth":
        for y, ws in lines:
            for i, w in enumerate(ws):
                if w[4].lower() != "super":
                    continue
                # Super Earth Certificates
                nxt = " ".join(ws[j][4].lower() for j in range(i, min(i + 3, len(ws))))
                if "earth" in nxt and "cert" in nxt:
                    anchors.append((y, w[0]))
    else:  # NHC
        for y, ws in lines:
            text = line_text(ws)
            if re.search(r"Natural Hunting Certificates?", text, re.I) and "Criteria" not in text:
                # x of Natural
                for w in ws:
                    if w[4].lower() == "natural":
                        anchors.append((y, w[0]))
                        break
    return anchors


def parse_cert_table(page, kind: str) -> list[dict]:
    """Parse cert tables using scan geometry: title anchors + per-header column bands."""
    lines = words_to_lines(page_words(page), y_tol=2.5)
    rows: list[dict] = []
    hard_stop = re.compile(
        r"(BRONZE MEDALLION|WORKING ACHIEVEMENT|New Registrations|IMPORTANT NOTICE|"
        r"REMINDER:|Natural Hunting Certificate Criteria|Online results)",
        re.I,
    )
    fourth = "quarry" if kind == "NHC" else "trial"

    # Collect title anchors for all kinds on this page (for nearest-title ownership)
    kind_anchors = {
        "Trial": _title_anchors(lines, "Trial"),
        "Super Earth": _title_anchors(lines, "Super Earth"),
        "NHC": _title_anchors(lines, "NHC"),
    }
    anchors = kind_anchors[kind]
    if not anchors:
        return []
    all_anchors: list[tuple[float, float, str]] = []
    for kn, alist in kind_anchors.items():
        for y, x in alist:
            all_anchors.append((y, x, kn))

    # Y positions of hard section breaks (Bronze / Working Achievement / etc.)
    break_ys = [y for y, ws in lines if hard_stop.search(line_text(ws))]

    # Discover all dog/owner/judge/(trial|quarry) tables on page
    tables = _discover_table_schemas(lines, want_fourth=fourth)
    # Own a table if its nearest title-above is this kind
    owned: list[dict] = []
    for table in tables:
        if fourth not in table["cols"] and table.get("fourth") != fourth:
            continue
        tx = table["cols"]["dog"]
        ty = table["y"]
        # Skip tables that sit below a hard break (Bronze Medallion layout, etc.)
        if any(by < ty for by in break_ys):
            # unless our kind title is also below that break (shouldn't happen for NHC list)
            kind_below = [ay for ay, ax in anchors if ay > max(by for by in break_ys if by < ty)]
            if not kind_below:
                continue
        best = None
        for y, x, kn in all_anchors:
            if y > ty + 5:
                continue
            # Title must not cross a hard break between title and table
            if any(y < by < ty for by in break_ys):
                continue
            score = abs(ty - y) * 20 + abs(tx - x)
            if best is None or score < best[0]:
                best = (score, kn, y, x)
        if best and best[1] == kind:
            # NHC listing columns are tight (judge→quarry ~40-70pt); Bronze blocks are wider
            if kind == "NHC" and "quarry" in table["cols"] and "judge" in table["cols"]:
                span = table["cols"]["quarry"] - table["cols"]["judge"]
                if span > 90:
                    continue
            owned.append(table)

    for table in owned:
        cols = table["cols"]
        use = {k: cols[k] for k in ("dog", "owner", "judge", fourth) if k in cols}
        if fourth not in use:
            continue
        # Row window: from header to next hard stop or next header in-band or far y
        for y, ws in lines:
            if y <= table["y"] + 1:
                continue
            if y > table["y"] + 220:
                break
            txt = line_text(ws)
            if hard_stop.search(txt):
                break
            if re.search(r"Name of Terrier", txt, re.I) and re.search(r"\bOwner\b", txt, re.I):
                # another header — end this table's rows
                break
            fields = _assign_by_col_starts(
                ws, use, x_left=table["x_left"], x_right=table["x_right"], tol=10.0
            )
            if kind == "NHC":
                if not _valid_nhc_row(fields):
                    continue
                rows.append(
                    {
                        "DogName": fields["dog"][:255],
                        "OwnerName": fields["owner"][:255],
                        "JudgeName": (fields.get("judge") or None),
                        "Quarry": fields["quarry"].title()[:100],
                    }
                )
            else:
                if "trial" not in fields and fourth in fields:
                    fields["trial"] = fields[fourth]
                if not _valid_trial_row(fields):
                    continue
                rows.append(
                    {
                        "DogName": fields["dog"][:255],
                        "OwnerName": fields["owner"][:255],
                        "JudgeName": (fields.get("judge") or None),
                        "TrialName": fields["trial"][:255],
                        "CertType": kind,
                    }
                )

    seen = set()
    out = []
    for r in rows:
        k = tuple(
            (r.get(x) or "").lower()
            for x in ("DogName", "OwnerName", "JudgeName", "TrialName", "Quarry", "CertType")
        )
        if k in seen:
            continue
        seen.add(k)
        out.append(r)
    return out


def _split_trial_suffix(toks: list[str]) -> tuple[str | None, list[str]]:
    n = len(toks)
    for take in range(1, min(6, n - 2)):
        trial = " ".join(toks[-take:])
        # trial-like if contains National/Trial/Fest/Classic/Roman numerals/digits
        if re.search(
            r"(National|Trial|Fest|Classic|West End|Midwest|Northgate|Dogwood|"
            r"Wilderness|Museum|Magnolia|Frolic|Dream|Step|Fox)\b|[IVX]+$|\b\d{4}\b",
            trial,
            re.I,
        ):
            return trial, toks[:-take]
    # fallback last 2 tokens
    if n >= 5:
        return " ".join(toks[-2:]), toks[:-2]
    return None, toks


_COUPLE_AMP = re.compile(
    r"^([A-Z][A-Za-z'\-]+)\s+&\s+([A-Z][A-Za-z'\-]+)\s+([A-Z][A-Za-z'\-]+)$"
)
_COUPLE_SLASH = re.compile(
    r"^([A-Z][A-Za-z'\-]+(?:\s+[A-Z][A-Za-z'\-]+)?)\s*/\s*"
    r"([A-Z][A-Za-z'\-]+(?:\s+[A-Z][A-Za-z'\-]+)?)$"
)
_JUDGE_OK = re.compile(
    r"^(?:"
    r"[A-Z][A-Za-z'\-]+(?:\s+[A-Z][A-Za-z'\-]+){0,2}"  # First Last
    r"|[A-Z]\.\s*[A-Z][A-Za-z'\-]+"  # G. Redpath-Schaeper
    r"|[A-Z]\.\s*[A-Z][A-Za-z'\-]+-[A-Z][A-Za-z'\-]+"
    r")$"
)


def _looks_like_judge(s: str) -> bool:
    s = _clean_person_field(s)
    if not s or len(s) > 40:
        return False
    if _JUDGE_OK.match(s):
        return True
    # Initials glued: "G.Redpath-Schaeper"
    if re.match(r"^[A-Z]\.[A-Z][A-Za-z'\-]+", s):
        return True
    return bool(plausible_person(s) and len(s.split()) <= 3)


def _split_dog_owner_judge(toks: list[str]) -> tuple[str, str, str] | None:
    """Split Dog | Owner | Judge. Couples with '&' must not leak into Judge."""
    if len(toks) < 3:
        return None

    # --- Preferred path: couple with '&' (Janet & Brian Franklin) ---
    amp_idxs = [i for i, t in enumerate(toks) if t == "&"]
    for amp in amp_idxs:
        # Require First & First Last  → owner uses amp-1 .. amp+2 inclusive
        if amp < 1 or amp + 2 >= len(toks):
            continue
        owner_start = amp - 1
        owner_end = amp + 3  # exclusive
        # Optional: First Middle & First Last (rare) — skip; keep tight couple
        owner_toks = toks[owner_start:owner_end]
        owner = _clean_person_field(" ".join(owner_toks))
        if not _COUPLE_AMP.match(owner):
            continue
        dog_toks = toks[:owner_start]
        judge_toks = toks[owner_end:]
        if not dog_toks or not judge_toks:
            continue
        dog = " ".join(dog_toks).strip()
        judge = _clean_person_field(" ".join(judge_toks))
        if len(dog) < 3 or not _looks_like_judge(judge):
            continue
        return dog, owner, judge

    # --- Slash couples: "Connie McKee/Michelle Davies" may be 1-3 tokens ---
    for i, t in enumerate(toks):
        if "/" not in t and not (i + 1 < len(toks) and toks[i + 1] == "/"):
            continue
        # Token contains slash: McKee/Michelle
        if "/" in t:
            # owner is previous token + this + next? "Connie" "McKee/Michelle" "Davies"
            for start in range(max(0, i - 1), i + 1):
                for end in range(i + 1, min(len(toks), i + 3) + 1):
                    owner = _clean_person_field(" ".join(toks[start:end]))
                    if not _COUPLE_SLASH.match(owner.replace(" / ", "/")):
                        # also accept "Connie McKee/Michelle Davies"
                        if "/" not in owner:
                            continue
                    dog_toks = toks[:start]
                    judge_toks = toks[end:]
                    if not dog_toks or not judge_toks:
                        continue
                    dog = " ".join(dog_toks).strip()
                    judge = _clean_person_field(" ".join(judge_toks))
                    if len(dog) >= 3 and _looks_like_judge(judge):
                        return dog, owner, judge

    # --- No couple marker: score splits; never cut a trailing '&' into owner ---
    best = None
    n = len(toks)
    for i in range(1, n - 1):
        for j in range(i + 1, n):
            dog = " ".join(toks[:i]).strip()
            owner = _clean_person_field(" ".join(toks[i:j]))
            judge = _clean_person_field(" ".join(toks[j:]))
            if len(dog) < 3 or len(owner) < 3 or len(judge) < 3:
                continue
            if owner.endswith("&") or owner.startswith("&") or "&" in owner:
                # unfinished / misplaced couple — reject (handled above)
                continue
            if not _looks_like_judge(judge):
                continue
            score = 0
            # Prefer multi-word dog names (kennel + call name)
            if 2 <= i <= 5:
                score += 3
            elif i == 1:
                score += 0
            # Owner typically 2-4 tokens
            ow = len(toks[i:j])
            if 2 <= ow <= 4:
                score += 2
            if plausible_person(owner.split("/")[0].strip()) or " " in owner:
                score += 1
            if _looks_like_judge(judge):
                score += 2
            # Prefer shorter judges (First Last or G. Last)
            if len(judge.split()) <= 2:
                score += 1
            if best is None or score > best[0]:
                best = (score, dog, owner, judge)
    if not best or best[0] < 4:
        return None
    return best[1], best[2], best[3]


# ----- Bundle build -------------------------------------------------------


def parse_pdf(meta: IssueMeta) -> TGBundle:
    doc = fitz.open(meta.path)
    ps, pe = extract_period(doc)
    meta.period_start, meta.period_end = ps, pe
    bundle = TGBundle(meta=meta)

    # Board page: first "BOARD OF DIRECTORS:"
    for i in find_pages(doc, re.compile(r"BOARD OF DIRECTORS\s*:", re.I)):
        text = doc.load_page(i).get_text("text")
        if "JUDGES COMMITTEE" in text.upper() or "TRIAL COMMITTEE" in text.upper():
            board, comm = parse_board_page(text)
            bundle.board, bundle.committees = board, comm
            break

    # State reps: page containing "JRTCA State Representatives" footer/header with state list
    for i in find_pages(doc, re.compile(r"JRTCA State Representatives", re.I)):
        text = doc.load_page(i).get_text("text")
        # Prefer the listing page (has many state names), not bios
        if sum(1 for s in _STATE_NAMES if s.title() in text or s in text.upper()) >= 5:
            bundle.state_reps = parse_state_reps_text(text)
            break
    if not bundle.state_reps:
        for i in find_pages(doc, re.compile(r"^ARIZONA\s*$", re.M)):
            text = doc.load_page(i).get_text("text")
            reps = parse_state_reps_text(text)
            if len(reps) >= 5:
                bundle.state_reps = reps
                break

    # Registrations
    for i in find_pages(doc, re.compile(r"^New Registrations\s*$", re.M)):
        page = doc.load_page(i)
        bundle.registrations = parse_registration_rows(page)
        if re.search(r"Registered Kennel Prefixes", page.get_text("text"), re.I):
            bundle.kennel_prefixes.extend(parse_kennel_prefix_rows(page))
        break

    # Kennel prefixes (may be on a later/other page than registrations)
    if not bundle.kennel_prefixes:
        for i in find_pages(doc, re.compile(r"Registered Kennel Prefixes", re.I)):
            bundle.kennel_prefixes.extend(parse_kennel_prefix_rows(doc.load_page(i)))
            if bundle.kennel_prefixes:
                break

    # Trial + Super Earth certificates
    for i in find_pages(doc, re.compile(r"^Trial Certificates\s*$", re.M)):
        page = doc.load_page(i)
        bundle.trial_certs.extend(parse_cert_table(page, "Trial"))
        bundle.trial_certs.extend(parse_cert_table(page, "Super Earth"))
        if i + 1 < doc.page_count:
            nxt = doc.load_page(i + 1)
            nt = nxt.get_text("text")
            if re.search(r"Super Earth Certificates|Trial Certificates", nt):
                bundle.trial_certs.extend(parse_cert_table(nxt, "Trial"))
                bundle.trial_certs.extend(parse_cert_table(nxt, "Super Earth"))

    # NHC listing pages (not criteria)
    for i in find_pages(doc, re.compile(r"Natural Hunting Certificates Below Ground", re.I)):
        page = doc.load_page(i)
        # NHC rows often appear on prior page (two-column spill)
        if i > 0:
            bundle.nhc.extend(parse_cert_table(doc.load_page(i - 1), "NHC"))
        bundle.nhc.extend(parse_cert_table(page, "NHC"))

    # Deduplicate trial certs / nhc
    def dedupe_dicts(rows, keys):
        seen = set()
        out = []
        for r in rows:
            k = tuple((r.get(x) or "").lower() for x in keys)
            if k in seen:
                continue
            seen.add(k)
            out.append(r)
        return out

    bundle.trial_certs = dedupe_dicts(
        bundle.trial_certs, ["DogName", "OwnerName", "JudgeName", "TrialName", "CertType"]
    )
    bundle.nhc = dedupe_dicts(bundle.nhc, ["DogName", "OwnerName", "JudgeName", "Quarry"])
    bundle.kennel_prefixes = dedupe_dicts(
        bundle.kennel_prefixes, ["KennelPrefix", "OwnerName"]
    )
    return bundle


# ----- DB apply -----------------------------------------------------------


def _with_deadlock_retry(fn, retries: int = 4):
    last = None
    for attempt in range(retries):
        try:
            return fn()
        except pyodbc.Error as e:
            last = e
            msg = str(e)
            if "1205" in msg or "deadlock" in msg.lower():
                import time

                time.sleep(0.4 * (attempt + 1))
                continue
            raise
    raise last  # type: ignore[misc]


def ensure_owner(cur, name: str | None, *, apply: bool, state: str | None = None) -> int | None:
    if not name:
        return None
    # Keep couple names as a single OwnerName string when not a clean single person
    display = _clean_person_field(name)[:255]
    if not display:
        return None

    def _run():
        cur.execute("SELECT OwnerID FROM sResults.Owner WHERE OwnerName=?", display)
        row = cur.fetchone()
        if row:
            oid = int(row[0])
            if apply and state:
                cur.execute(
                    "UPDATE sResults.Owner SET State=COALESCE(NULLIF(?,''), State) WHERE OwnerID=?",
                    state,
                    oid,
                )
            return oid
        # try primary person if couple
        primary = display.split("/")[0].strip()
        primary = re.split(r"\s+&\s+", primary)[0].strip()
        if plausible_person(primary):
            oid = find_owner_id(cur, primary)
            if oid:
                return oid
        if not apply:
            return None
        cols = ["OwnerName"]
        vals = [display]
        if state:
            cols.append("State")
            vals.append(state)
        return insert_identity(cur, "Owner", "OwnerID", cols, vals)

    return _with_deadlock_retry(_run)


def ensure_dog(
    cur,
    dog_name: str,
    owner_id: int | None,
    *,
    apply: bool,
    note: str,
    source: str,
    breeder_id: int | None = None,
) -> int | None:
    dog_name = dog_name[:255]
    cur.execute("SELECT DogID, Notes, OwnerID, BreederID FROM sResults.Dog WHERE DogName=?", dog_name)
    row = cur.fetchone()
    if row:
        if apply:
            cur.execute(
                """
                UPDATE sResults.Dog
                SET OwnerID=COALESCE(?, OwnerID),
                    BreederID=COALESCE(?, BreederID),
                    Notes=?
                WHERE DogID=?
                """,
                owner_id,
                breeder_id,
                append_note(row[1], note),
                int(row[0]),
            )
        return int(row[0])
    if not apply:
        return None
    return insert_identity(
        cur,
        "Dog",
        "DogID",
        ["DogName", "OwnerID", "BreederID", "Notes", "SourceURL"],
        [dog_name, owner_id, breeder_id, note, source],
    )


def ensure_breeder_prefix(cur, row: dict, *, apply: bool, year: int, source: str) -> int | None:
    prefix = (row.get("KennelPrefix") or "").strip()
    kennel = (row.get("KennelName") or prefix).strip()
    owner = (row.get("OwnerName") or "").strip()
    state = row.get("State")
    if len(prefix) < 2:
        return None
    cur.execute(
        "SELECT BreederID, Notes FROM sResults.Breeder WHERE KennelPrefix=? OR KennelName=?",
        prefix[:100],
        kennel[:255],
    )
    existing = cur.fetchone()
    note = f"True Grit kennel prefix ({year})"
    if existing:
        if apply:
            cur.execute(
                """
                UPDATE sResults.Breeder
                SET OwnerName=COALESCE(NULLIF(?,''), OwnerName),
                    State=COALESCE(NULLIF(?,''), State),
                    KennelPrefix=COALESCE(NULLIF(?,''), KennelPrefix),
                    Notes=?,
                    SourceURL=COALESCE(SourceURL, ?)
                WHERE BreederID=?
                """,
                owner,
                state or "",
                prefix[:100],
                append_note(existing[1], note),
                source,
                int(existing[0]),
            )
            # also set Owner.KennelPrefix when owner matches
            oid = ensure_owner(cur, owner, apply=True, state=state)
            if oid:
                cur.execute(
                    "UPDATE sResults.Owner SET KennelPrefix=COALESCE(NULLIF(?,''), KennelPrefix) WHERE OwnerID=?",
                    prefix[:100],
                    oid,
                )
        return int(existing[0])
    if not apply:
        return None
    bid = insert_identity(
        cur,
        "Breeder",
        "BreederID",
        ["KennelName", "KennelPrefix", "OwnerName", "State", "SourceURL", "Notes"],
        [kennel[:255], prefix[:100], owner or None, state, source, note],
    )
    oid = ensure_owner(cur, owner, apply=True, state=state)
    if oid:
        cur.execute(
            "UPDATE sResults.Owner SET KennelPrefix=COALESCE(NULLIF(?,''), KennelPrefix), BreederID=COALESCE(BreederID, ?) WHERE OwnerID=?",
            prefix[:100],
            bid,
            oid,
        )
    return bid


def upsert_board_committee_reps(cur, bundle: TGBundle, *, apply: bool) -> dict:
    """Reuse yearbook-style upserts for Board/Committee/StateRep."""
    from yearbook_meta_ingest import MetaBundle, apply_bundle

    mb = MetaBundle(
        year=bundle.meta.year,
        source=str(bundle.meta.path.relative_to(ROOT)),
        board=bundle.board,
        committees=bundle.committees,
        state_reps=bundle.state_reps,
    )
    return apply_bundle(cur, mb, apply=apply)


def apply_truegrit(cur, bundle: TGBundle, *, apply: bool) -> dict:
    meta = bundle.meta
    src = str(meta.path.relative_to(ROOT))
    stats = defaultdict(int)
    stats.update(upsert_board_committee_reps(cur, bundle, apply=apply))

    # Kennel prefixes first (for breeder links)
    prefix_to_breeder: dict[str, int] = {}
    for k in bundle.kennel_prefixes:
        bid = ensure_breeder_prefix(cur, k, apply=apply, year=meta.year, source=f"truegrit:{src}")
        stats["kennel_prefix"] += 1
        if bid:
            prefix_to_breeder[(k.get("KennelPrefix") or "").lower()] = bid

    # Registrations
    for r in bundle.registrations:
        owner_id = ensure_owner(cur, r.get("OwnerName"), apply=apply, state=r.get("State"))
        breeder_id = None
        bname = r.get("BreederName")
        if bname:
            # try match breeder by owner name on Breeder table
            cur.execute(
                "SELECT TOP 1 BreederID FROM sResults.Breeder WHERE OwnerName=? OR KennelName=?",
                bname[:255],
                bname[:255],
            )
            brow = cur.fetchone()
            if brow:
                breeder_id = int(brow[0])
        note = f"True Grit new registration (vol {meta.volume}n{meta.issue}, {meta.year})"
        ensure_dog(
            cur,
            r["DogName"],
            owner_id,
            apply=apply,
            note=note,
            source=f"truegrit:{src}",
            breeder_id=breeder_id,
        )
        stats["registration"] += 1

    # Trial certificates
    for c in bundle.trial_certs:
        owner_id = ensure_owner(cur, c.get("OwnerName"), apply=apply)
        dog_id = ensure_dog(
            cur,
            c["DogName"],
            owner_id,
            apply=apply,
            note=f"True Grit {c.get('CertType','Trial')} certificate ({meta.year})",
            source=f"truegrit:{src}",
        )
        stats["trial_cert"] += 1
        if not apply:
            continue
        cert_type = c.get("CertType") or "Trial"
        cur.execute(
            """
            SELECT TrialCertificateID FROM sResults.TrialCertificates
            WHERE DogName=? AND ISNULL(OwnerName,'')=ISNULL(?, '')
              AND ISNULL(JudgeName,'')=ISNULL(?, '')
              AND ISNULL(TrialName,'')=ISNULL(?, '')
              AND ISNULL(CertificateType,'')=ISNULL(?, '')
            """,
            c["DogName"][:255],
            (c.get("OwnerName") or "")[:255],
            (c.get("JudgeName") or "")[:255],
            (c.get("TrialName") or "")[:255],
            cert_type,
        )
        if cur.fetchone():
            continue
        tid = next_id(cur, "TrialCertificates", "TrialCertificateID")
        cur.execute(
            """
            INSERT INTO sResults.TrialCertificates
            (TrialCertificateID, DogName, OwnerName, JudgeName, TrialName, CertificateType,
             PeriodStart, PeriodEnd, Volume, Issue, Year, DogID, OwnerID, SourcePath)
            VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?)
            """,
            tid,
            c["DogName"][:255],
            (c.get("OwnerName") or None),
            (c.get("JudgeName") or None),
            (c.get("TrialName") or None),
            cert_type,
            meta.period_start.isoformat() if meta.period_start else None,
            meta.period_end.isoformat() if meta.period_end else None,
            meta.volume,
            meta.issue,
            meta.year,
            dog_id,
            owner_id,
            src,
        )

    # NHC
    for c in bundle.nhc:
        owner_id = ensure_owner(cur, c.get("OwnerName"), apply=apply)
        dog_id = ensure_dog(
            cur,
            c["DogName"],
            owner_id,
            apply=apply,
            note=f"True Grit NHC ({meta.year})" + (f" — {c.get('Quarry')}" if c.get("Quarry") else ""),
            source=f"truegrit:{src}",
        )
        stats["nhc"] += 1
        if not apply:
            continue
        prey = (c.get("Quarry") or "")[:100]
        cur.execute(
            """
            SELECT NHCID FROM sResults.NHC
            WHERE DogName=? AND ISNULL(OwnerName,'')=ISNULL(?, '')
              AND ISNULL(JudgeName,'')=ISNULL(?, '')
              AND ISNULL(Prey,'')=ISNULL(?, '')
            """,
            c["DogName"][:255],
            (c.get("OwnerName") or "")[:255],
            (c.get("JudgeName") or "")[:255],
            prey,
        )
        if cur.fetchone():
            continue
        nid = next_id(cur, "NHC", "NHCID")
        cur.execute(
            """
            INSERT INTO sResults.NHC
            (NHCID, DogName, OwnerName, JudgeName, Prey, CertificateType,
             PeriodStart, PeriodEnd, Volume, Issue, Year, DogID, OwnerID, SourcePath)
            VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?)
            """,
            nid,
            c["DogName"][:255],
            (c.get("OwnerName") or None),
            (c.get("JudgeName") or None),
            prey or None,
            "Natural Hunting Certificate",
            meta.period_start.isoformat() if meta.period_start else None,
            meta.period_end.isoformat() if meta.period_end else None,
            meta.volume,
            meta.issue,
            meta.year,
            dog_id,
            owner_id,
            src,
        )

    return dict(stats)


def iter_pdfs(vols: list[int] | None = None) -> list[Path]:
    vols = vols or [47, 48, 49, 50]
    out = []
    for p in sorted(TG_DIR.glob("tgrit_*_issue.pdf")):
        meta = parse_issue_name(p)
        if meta and meta.volume in vols:
            out.append(p)
    return out


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--apply", action="store_true")
    ap.add_argument("--vols", default="47,48,49,50")
    ap.add_argument("--limit", type=int, default=None)
    ap.add_argument("paths", nargs="*")
    args = ap.parse_args(argv)
    vols = [int(x) for x in args.vols.split(",") if x.strip()]

    cn = pyodbc.connect(CONN, timeout=60)
    cur = cn.cursor()
    ensure_yearbook_meta(cur)
    _truegrit_schema.ensure(cur)
    cn.commit()

    if args.paths:
        paths = []
        for p in args.paths:
            pp = Path(p)
            paths.append(pp if pp.is_absolute() else (ROOT / pp))
    else:
        paths = iter_pdfs(vols)
    if args.limit:
        paths = paths[: args.limit]

    totals: dict[str, int] = defaultdict(int)
    for path in paths:
        meta = parse_issue_name(path)
        if not meta:
            print("SKIP name", path.name, flush=True)
            continue
        print(f"PARSE {path.name} year={meta.year} vol={meta.volume}n{meta.issue}", flush=True)
        try:
            bundle = parse_pdf(meta)
        except Exception as e:
            print(f"  ERR parse: {e}", flush=True)
            continue
        print(
            f"  board={len(bundle.board)} committees={sum(len(v) for v in bundle.committees.values())} "
            f"reps={len(bundle.state_reps)} regs={len(bundle.registrations)} "
            f"prefixes={len(bundle.kennel_prefixes)} trial_certs={len(bundle.trial_certs)} "
            f"nhc={len(bundle.nhc)} period={meta.period_start}..{meta.period_end}",
            flush=True,
        )
        try:
            st = _with_deadlock_retry(lambda: apply_truegrit(cur, bundle, apply=args.apply))
        except Exception as e:
            try:
                cn.rollback()
            except Exception:
                pass
            print(f"  ERR apply: {e}", flush=True)
            continue
        for k, v in st.items():
            if isinstance(v, int):
                totals[k] += v
        totals["issues"] += 1
        if args.apply:
            cn.commit()

    if args.apply:
        cn.commit()
        print("COMMITTED", dict(totals), flush=True)
    else:
        cn.rollback()
        print("DRY-RUN", dict(totals), flush=True)
    cn.close()
    return 0


if __name__ == "__main__":
    sys.exit(main())
