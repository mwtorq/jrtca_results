#!/usr/bin/env python3
"""Ingest yearbook non-trial meta from OCR text into Board/Committee/StateRep/Breeder/Dog/Owner.

Conservative: only upsert when names look plausible. Year from OCR content
(DerivedYear / date phrases), never from folder name alone.
State Representatives: insert year rows + augment matching Owner contact/Notes.
"""
from __future__ import annotations

import argparse
import os
import re
import sys
from dataclasses import dataclass, field
from pathlib import Path

import pyodbc

from ocr_yearbook_source import (
    derive_year_from_text,
    folder_year_hint,
    is_yearbook_path,
    write_ocr_sibling,
)
from remount_source_divisions import CONN

ROOT = Path(r"c:\Users\mw\OneDrive - timberwilde.net\repos\jrtca_results")

_US_STATES = {
    "AL", "AK", "AZ", "AR", "CA", "CO", "CT", "DE", "FL", "GA", "HI", "ID", "IL",
    "IN", "IA", "KS", "KY", "LA", "ME", "MD", "MA", "MI", "MN", "MS", "MO", "MT",
    "NE", "NV", "NH", "NJ", "NM", "NY", "NC", "ND", "OH", "OK", "OR", "PA", "RI",
    "SC", "SD", "TN", "TX", "UT", "VT", "VA", "WA", "WV", "WI", "WY", "DC",
}
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
    "WEST VIRGINIA": "WV", "WISCONSIN": "WI", "WYOMING": "WY",
}

_NAME_RE = re.compile(
    r"\b((?:Mrs\.|Mr\.|Ms\.|Dr\.)?\s*[A-Z][A-Za-z'\-]+(?:\s+[A-Z][A-Za-z'\-]+){1,3})\b"
)
_CITY_ST_ZIP = re.compile(
    r"([A-Za-z .'\-]+),\s*([A-Z]{2})\s+(\d{5}(?:-\d{4})?)"
)
_PHONE_RE = re.compile(r"(\(?\d{3}\)?[-.\s]?\d{3}[-.\s]?\d{4})")
_ROLE_RE = re.compile(
    r"(Chairman|Chairperson|Vice[- ]?Chairman|Vice[- ]?Chair|President|Secretary|"
    r"Treasurer|Director|Member|Representative)",
    re.I,
)
_COMMITTEE_HDR = re.compile(
    r"(BOARD\s+OF\s+DIRECTORS|REPRESENTATIVES?\s+COMMITTEE|JUDGES\s+COMMITTEE|"
    r"TRIAL\s+COMMITTEE|BREEDERS?\s+COMMITTEE|STATE\s+REPRESENTATIVES?|"
    r"DIRECTORY\s+OF\s+BREEDERS?|NEW\s+REGISTRATIONS?|NEWLY\s+REGISTERED\s+KENNEL|"
    r"KENNEL\s+PREFIX(?:ES)?|TRIAL\s+CERTIFICATES?|NATURAL\s+HUNTING\s+CERTIFICATES?|"
    r"WORKING\s+CERTIFICATES?)",
    re.I,
)


def norm_name(s: str) -> str:
    s = re.sub(r"\s+", " ", (s or "").strip())
    s = re.sub(r"^(Mrs\.|Mr\.|Ms\.|Dr\.)\s*", "", s, flags=re.I)
    return s


def name_key(s: str) -> str:
    return re.sub(r"[^a-z]", "", norm_name(s).lower())


# Allow "Mary", "O'Brien", "Foshay-Schmitt", and single initials "H" / "H."
_PERSON_PART = re.compile(r"^[A-Za-z](?:\.|[A-Za-z'\-]{0,30})$")
_NAME_JUNK = re.compile(
    r"\b(committee|board|director|chairman|chairperson|trial|continued|page|"
    r"kennel|farm|terriers?|maryland|virginia|image|damage|books?|store|"
    r"menu|boutique|registry|membership|affiliate|constitution|bylaws|"
    r"download|forms?|survey|amazon|fleece|vest|click|home|about|"
    r"support|standard|contracts?|magazine|articles?|details|trained|"
    r"culture|clash|view|join|gift|official|site|web)\b",
    re.I,
)


def plausible_person(name: str) -> bool:
    """True only for individual person names (not nav/product/couple blobs)."""
    n = norm_name(name)
    if len(n) < 5 or len(n) > 40:
        return False
    # Couples must be split before insert ("Don and Brenda McGowan")
    if re.search(r"\band\b", n, re.I):
        return False
    parts = n.split()
    if len(parts) < 2 or len(parts) > 4:
        return False
    if _NAME_JUNK.search(n):
        return False
    for p in parts:
        # Allow hyphenated surnames as one token
        core = p.replace("'", "")
        if not _PERSON_PART.match(core):
            return False
        letters = "".join(ch for ch in core if ch.isalpha())
        if not letters:
            return False
        # Single initials OK ("H", "H.")
        if len(letters) == 1:
            continue
        if len(letters) < 2:
            return False
        # Reject ALL-CAPS org acronyms (JRT, AKC); allow II/III/JR/SR
        if letters.isupper() and len(letters) <= 4 and letters not in {"II", "III", "JR", "SR"}:
            return False
    if sum(c.isalpha() for c in n) < 6:
        return False
    if sum(1 for c in n if not (c.isalnum() or c in " -'.")) > 2:
        return False
    return True


def split_couple_name(name: str) -> list[str]:
    """Split 'First and First Last' into two person names; else []."""
    n = norm_name(name)
    m = re.match(
        r"^([A-Z][A-Za-z'\-]+)\s+and\s+([A-Z][A-Za-z'\-]+)\s+([A-Z][A-Za-z'\-]+(?:\s+[A-Z][A-Za-z'\-]+)?)$",
        n,
        re.I,
    )
    if not m:
        return []
    first_a, first_b, last = m.group(1), m.group(2), m.group(3)
    return [norm_name(f"{first_a} {last}"), norm_name(f"{first_b} {last}")]


@dataclass
class PersonHit:
    name: str
    role: str | None = None
    address: str | None = None
    city: str | None = None
    state: str | None = None
    postal: str | None = None
    phone: str | None = None
    extra: str | None = None


@dataclass
class MetaBundle:
    year: int | None = None
    source: str = ""
    board: list[PersonHit] = field(default_factory=list)
    committees: dict[str, list[PersonHit]] = field(default_factory=dict)
    state_reps: list[PersonHit] = field(default_factory=list)
    breeders: list[dict] = field(default_factory=list)
    registrations: list[dict] = field(default_factory=list)
    certificates: list[dict] = field(default_factory=list)


def _attach_contact(hit: PersonHit, blob: str) -> None:
    m = _CITY_ST_ZIP.search(blob)
    if m:
        hit.city = m.group(1).strip(" .")
        hit.state = m.group(2)
        hit.postal = m.group(3)
    ph = _PHONE_RE.search(blob)
    if ph:
        hit.phone = ph.group(1)
    # crude street line: digits + street words before city
    sm = re.search(
        r"((?:P\.?O\.?\s*Box\s+\d+|R\.?R\.?\s*\d+|Rt\.?\s*\d+|[\d]+[\w\s.'\-]{3,40}))",
        blob,
        re.I,
    )
    if sm and hit.city and sm.group(1) not in (hit.city or ""):
        hit.address = sm.group(1).strip(" ,.")


def parse_section_people(block: str, default_role: str | None = None) -> list[PersonHit]:
    hits: list[PersonHit] = []
    # Prefer "Name, Role" then nearby address
    for m in re.finditer(
        r"([A-Z][A-Za-z'\-]+(?:\s+[A-Z][A-Za-z'\-]+){1,3})\s*,?\s*"
        r"(Chairman|Vice[- ]?Chairman|President|Secretary|Treasurer|Director)?",
        block,
    ):
        name = norm_name(m.group(1))
        if not plausible_person(name):
            continue
        role = m.group(2) or default_role
        hit = PersonHit(name=name, role=role)
        window = block[m.end() : m.end() + 120]
        _attach_contact(hit, window)
        hits.append(hit)
    # dedupe by name+role
    seen = set()
    out = []
    for h in hits:
        k = (name_key(h.name), (h.role or "").lower())
        if k in seen:
            continue
        seen.add(k)
        out.append(h)
    return out


def split_sections(text: str) -> list[tuple[str, str]]:
    """Return list of (section_label, body)."""
    matches = list(_COMMITTEE_HDR.finditer(text))
    if not matches:
        # soft detect
        soft = []
        for label, pat in (
            ("BOARD OF DIRECTORS", r"BOARD[_\s]+OF[_\s]+DIRECTORS"),
            ("STATE REPRESENTATIVES", r"STATE\s+REPRESENT"),
            ("REPRESENTATIVES COMMITTEE", r"REPRESENTATIVES?\s+COMMITTEE"),
            ("DIRECTORY OF BREEDERS", r"DIRECTORY\s+OF\s+BREEDERS?|BREEDER\s+DIRECTORY"),
            ("NEW REGISTRATIONS", r"NEW\s+REGISTRATIONS?"),
            ("KENNEL PREFIXES", r"KENNEL\s+PREFIX"),
            ("TRIAL CERTIFICATES", r"TRIAL\s+CERTIFICATES?"),
            ("NATURAL HUNTING CERTIFICATES", r"NATURAL\s+HUNTING"),
        ):
            for m in re.finditer(pat, text, re.I):
                soft.append((m.start(), label))
        soft.sort()
        if not soft:
            return []
        out = []
        for i, (pos, label) in enumerate(soft):
            end = soft[i + 1][0] if i + 1 < len(soft) else len(text)
            out.append((label, text[pos:end]))
        return out

    out = []
    for i, m in enumerate(matches):
        label = re.sub(r"\s+", " ", m.group(1).upper())
        end = matches[i + 1].start() if i + 1 < len(matches) else len(text)
        out.append((label, text[m.start() : end]))
    return out


def parse_breeders_block(block: str) -> list[dict]:
    rows = []
    # KennelName - Owner / City, ST
    for m in re.finditer(
        r"([A-Z][A-Za-z0-9 '&/\-]{2,40})\s*[-–:]\s*"
        r"([A-Z][A-Za-z'\-]+(?:\s+[A-Z][A-Za-z'\-]+){0,3})"
        r"(?:[,\s]+([A-Za-z .]+),\s*([A-Z]{2}))?",
        block,
    ):
        kennel, owner, city, st = m.group(1).strip(), norm_name(m.group(2)), m.group(3), m.group(4)
        if len(kennel) < 3 or not plausible_person(owner):
            # kennel-only prefix lines
            if len(kennel) >= 3 and not owner:
                pass
            else:
                if not plausible_person(owner):
                    continue
        rows.append(
            {
                "KennelName": kennel[:255],
                "KennelPrefix": kennel[:100],
                "OwnerName": owner[:255] if owner else None,
                "City": (city or "").strip()[:100] or None,
                "State": st,
            }
        )
    # Prefix-only: "PREFIX - Owner"
    for m in re.finditer(
        r"\b([A-Z][A-Z0-9]{2,20})\s*[-–]\s*([A-Z][A-Za-z'\-]+(?:\s+[A-Z][A-Za-z'\-]+)+)",
        block,
    ):
        prefix, owner = m.group(1), norm_name(m.group(2))
        if not plausible_person(owner):
            continue
        rows.append(
            {
                "KennelName": prefix.title(),
                "KennelPrefix": prefix[:100],
                "OwnerName": owner[:255],
                "City": None,
                "State": None,
            }
        )
    # dedupe
    seen = set()
    out = []
    for r in rows:
        k = (r["KennelPrefix"] or "").lower(), name_key(r.get("OwnerName") or "")
        if k in seen:
            continue
        seen.add(k)
        out.append(r)
    return out


def parse_registrations_block(block: str) -> list[dict]:
    rows = []
    # DogName, owned by Owner  /  DogName - Owner
    for m in re.finditer(
        r"([A-Z][A-Za-z0-9' \-]{3,60}?)\s*(?:,\s*owned by\s*|,\s*owner[:\s]+|[-–]\s*)"
        r"([A-Z][A-Za-z'\-]+(?:\s+[A-Z][A-Za-z'\-/]+){0,4})",
        block,
        re.I,
    ):
        dog, owner = m.group(1).strip(" ,."), norm_name(m.group(2))
        if len(dog) < 3 or not plausible_person(owner):
            continue
        if any(x in dog.lower() for x in ("committee", "board", "page", "continued")):
            continue
        rows.append({"DogName": dog[:255], "OwnerName": owner[:255]})
    return rows


def parse_certificates_block(block: str, cert_type: str) -> list[dict]:
    rows = []
    for m in re.finditer(
        r"([A-Z][A-Za-z0-9' \-]{3,60}?)\s*(?:,\s*owned by\s*|[-–]\s*)"
        r"([A-Z][A-Za-z'\-]+(?:\s+[A-Z][A-Za-z'\-/]+){0,4})",
        block,
        re.I,
    ):
        dog, owner = m.group(1).strip(" ,."), norm_name(m.group(2))
        if len(dog) < 3:
            continue
        rows.append(
            {
                "DogName": dog[:255],
                "OwnerName": owner[:255] if plausible_person(owner) else None,
                "CertType": cert_type,
            }
        )
    return rows


def parse_state_reps_block(block: str) -> list[PersonHit]:
    hits: list[PersonHit] = []
    # STATE NAME followed by person
    for m in re.finditer(
        r"\b(" + "|".join(re.escape(n) for n in sorted(_STATE_NAMES, key=len, reverse=True)) + r")\b"
        r"[:\s\-]+([A-Z][A-Za-z'\-]+(?:\s+[A-Z][A-Za-z'\-]+){1,3})",
        block,
        re.I,
    ):
        st = _STATE_NAMES[m.group(1).upper()]
        name = norm_name(m.group(2))
        if not plausible_person(name):
            continue
        hit = PersonHit(name=name, role="State Representative", state=st)
        _attach_contact(hit, block[m.end() : m.end() + 100])
        hits.append(hit)
    # Also "Name ... City, ST zip" under STATE REPRESENTATIVES without state header
    if not hits:
        for m in _CITY_ST_ZIP.finditer(block):
            pre = block[max(0, m.start() - 80) : m.start()]
            nm = _NAME_RE.findall(pre)
            if not nm:
                continue
            name = norm_name(nm[-1])
            if not plausible_person(name):
                continue
            hit = PersonHit(
                name=name,
                role="State Representative",
                city=m.group(1).strip(" ."),
                state=m.group(2),
                postal=m.group(3),
            )
            hits.append(hit)
    seen = set()
    out = []
    for h in hits:
        k = (name_key(h.name), h.state or "")
        if k in seen:
            continue
        seen.add(k)
        out.append(h)
    return out


def parse_meta_text(text: str, source: str) -> MetaBundle:
    year = derive_year_from_text(text)
    bundle = MetaBundle(year=year, source=source)
    for label, body in split_sections(text):
        ul = label.upper()
        if "BOARD OF DIRECTORS" in ul or ul.startswith("BOARD"):
            bundle.board.extend(parse_section_people(body, default_role="Director"))
        elif "STATE REPRESENT" in ul:
            bundle.state_reps.extend(parse_state_reps_block(body))
        elif "REPRESENTATIVES COMMITTEE" in ul:
            bundle.committees.setdefault("Representatives Committee", []).extend(
                parse_section_people(body)
            )
            # reps committee members sometimes double as state-ish contacts
        elif "JUDGES" in ul:
            bundle.committees.setdefault("Judges Committee", []).extend(
                parse_section_people(body)
            )
        elif "TRIAL COMMITTEE" in ul:
            bundle.committees.setdefault("Trial Committee", []).extend(
                parse_section_people(body)
            )
        elif "BREEDER" in ul and "DIRECTORY" not in ul and "COMMITTEE" in ul:
            bundle.committees.setdefault("Breeders Committee", []).extend(
                parse_section_people(body)
            )
        elif "DIRECTORY" in ul or ("BREEDER" in ul and "COMMITTEE" not in ul):
            bundle.breeders.extend(parse_breeders_block(body))
        elif "KENNEL PREFIX" in ul or "NEWLY REGISTERED KENNEL" in ul:
            bundle.breeders.extend(parse_breeders_block(body))
        elif "NEW REGISTRATION" in ul:
            bundle.registrations.extend(parse_registrations_block(body))
        elif "NATURAL HUNTING" in ul:
            bundle.certificates.extend(
                parse_certificates_block(body, "Natural Hunting Certificate")
            )
        elif "TRIAL CERTIFICATE" in ul or "WORKING CERTIFICATE" in ul:
            bundle.certificates.extend(
                parse_certificates_block(body, "Trial/Working Certificate")
            )
    return bundle


def next_id(cur, table: str, col: str) -> int:
    cur.execute(f"SELECT ISNULL(MAX({col}),0)+1 FROM sResults.[{table}]")
    return int(cur.fetchone()[0])


def insert_identity(cur, table: str, id_col: str, columns: list[str], values: list) -> int:
    """INSERT into an IDENTITY table without supplying the ID; return new ID."""
    cols = ", ".join(f"[{c}]" for c in columns)
    ph = ", ".join("?" for _ in columns)
    cur.execute(
        f"INSERT INTO sResults.[{table}] ({cols}) OUTPUT INSERTED.[{id_col}] VALUES ({ph})",
        values,
    )
    return int(cur.fetchone()[0])


def append_note(existing: str | None, note: str) -> str:
    note = note.strip()
    if not note:
        return existing or ""
    if existing and note in existing:
        return existing
    if not existing:
        return note
    return (existing.rstrip() + "\n" + note)[:4000]


def find_owner_id(cur, name: str) -> int | None:
    """Resolve OwnerID by exact name, then conservative fuzzy last-name match."""
    if not name or not plausible_person(name):
        return None
    cur.execute(
        "SELECT OwnerID FROM sResults.Owner WHERE OwnerName=?",
        name[:255],
    )
    row = cur.fetchone()
    if row:
        return int(row[0])
    parts = norm_name(name).split()
    if len(parts) < 2:
        return None
    last = parts[-1]
    cur.execute(
        """
        SELECT OwnerID, OwnerName
        FROM sResults.Owner
        WHERE OwnerName LIKE ?
        """,
        f"%{last}",
    )
    cand = []
    nk = name_key(name)
    for row in cur.fetchall():
        on = row[1] or ""
        if name_key(on) == nk or on.strip().lower().endswith(last.lower()):
            if parts[0][0].lower() == (on.strip()[:1] or "").lower() or name_key(on) == nk:
                cand.append(row)
    if len(cand) == 1:
        return int(cand[0][0])
    if not cand:
        cur.execute(
            """
            SELECT OwnerID FROM sResults.Owner WHERE OwnerName LIKE ?
            """,
            f"% {last}",
        )
        rows = cur.fetchall()
        if len(rows) == 1:
            return int(rows[0][0])
    return None


def augment_owner_from_hit(cur, owner_id: int, h: PersonHit, note: str, *, apply: bool) -> None:
    if not apply or not owner_id:
        return
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
        owner_id,
    )
    try:
        cur.execute("SELECT Notes FROM sResults.Owner WHERE OwnerID=?", owner_id)
        old_notes = cur.fetchone()[0]
        cur.execute(
            "UPDATE sResults.Owner SET Notes=? WHERE OwnerID=?",
            append_note(old_notes, note),
            owner_id,
        )
    except Exception:
        pass


def apply_bundle(cur, bundle: MetaBundle, *, apply: bool) -> dict:
    stats = {
        "board": 0,
        "committee": 0,
        "state_rep": 0,
        "owner_aug": 0,
        "breeder": 0,
        "dog_reg": 0,
        "dog_cert": 0,
        "skip_noyear": 0,
    }
    if not bundle.year:
        stats["skip_noyear"] = 1
        return stats
    year = int(bundle.year)
    src = bundle.source

    # Board
    for h in bundle.board:
        if not plausible_person(h.name):
            continue
        owner_id = find_owner_id(cur, h.name)
        if owner_id:
            note = f"JRTCA Board ({year})" + (f" — {h.role}" if h.role else "")
            if apply:
                augment_owner_from_hit(cur, owner_id, h, note, apply=True)
            stats["owner_aug"] += 1
        cur.execute(
            "SELECT BoardID FROM sResults.Board WHERE Year=? AND MemberName=? AND ISNULL(Role,'')=ISNULL(?, '')",
            year,
            h.name[:255],
            h.role,
        )
        row = cur.fetchone()
        if row:
            if apply:
                cur.execute(
                    """
                    UPDATE sResults.Board
                    SET Address=COALESCE(?,Address), City=COALESCE(?,City),
                        State=COALESCE(?,State), PostalCode=COALESCE(?,PostalCode),
                        Phone=COALESCE(?,Phone), SourcePath=?,
                        OwnerID=COALESCE(?,OwnerID)
                    WHERE BoardID=?
                    """,
                    h.address,
                    h.city,
                    h.state,
                    h.postal,
                    h.phone,
                    src,
                    owner_id,
                    int(row[0]),
                )
            stats["board"] += 1
            continue
        if apply:
            bid = next_id(cur, "Board", "BoardID")
            cur.execute(
                """
                INSERT INTO sResults.Board
                (BoardID, Year, MemberName, Role, Address, City, State, PostalCode, Phone, SourcePath, OwnerID)
                VALUES (?,?,?,?,?,?,?,?,?,?,?)
                """,
                bid,
                year,
                h.name[:255],
                h.role,
                h.address,
                h.city,
                h.state,
                h.postal,
                h.phone,
                src,
                owner_id,
            )
        stats["board"] += 1

    # Committees
    for cname, members in bundle.committees.items():
        for h in members:
            if not plausible_person(h.name):
                continue
            owner_id = find_owner_id(cur, h.name)
            if owner_id:
                note = f"JRTCA Committee ({year}) — {cname}"
                if apply:
                    augment_owner_from_hit(cur, owner_id, h, note, apply=True)
                stats["owner_aug"] += 1
            cur.execute(
                """
                SELECT CommitteeID FROM sResults.Committee
                WHERE Year=? AND CommitteeName=? AND MemberName=? AND ISNULL(Role,'')=ISNULL(?, '')
                """,
                year,
                cname[:255],
                h.name[:255],
                h.role,
            )
            row = cur.fetchone()
            if row:
                if apply:
                    cur.execute(
                        """
                        UPDATE sResults.Committee
                        SET Address=COALESCE(?,Address), City=COALESCE(?,City),
                            State=COALESCE(?,State), PostalCode=COALESCE(?,PostalCode),
                            Phone=COALESCE(?,Phone), SourcePath=?,
                            OwnerID=COALESCE(?,OwnerID)
                        WHERE CommitteeID=?
                        """,
                        h.address,
                        h.city,
                        h.state,
                        h.postal,
                        h.phone,
                        src,
                        owner_id,
                        int(row[0]),
                    )
                stats["committee"] += 1
                continue
            if apply:
                cid = next_id(cur, "Committee", "CommitteeID")
                cur.execute(
                    """
                    INSERT INTO sResults.Committee
                    (CommitteeID, Year, CommitteeName, MemberName, Role, Address, City, State, PostalCode, Phone, SourcePath, OwnerID)
                    VALUES (?,?,?,?,?,?,?,?,?,?,?,?)
                    """,
                    cid,
                    year,
                    cname[:255],
                    h.name[:255],
                    h.role,
                    h.address,
                    h.city,
                    h.state,
                    h.postal,
                    h.phone,
                    src,
                    owner_id,
                )
            stats["committee"] += 1

    # State reps + Owner augment
    for h in bundle.state_reps:
        if not plausible_person(h.name):
            continue
        owner_id = find_owner_id(cur, h.name)
        if owner_id:
            note = f"JRTCA State Representative ({year})" + (
                f" — {h.state}" if h.state else ""
            )
            if apply:
                augment_owner_from_hit(cur, owner_id, h, note, apply=True)
            stats["owner_aug"] += 1

        cur.execute(
            """
            SELECT StateRepID FROM sResults.StateRepresentative
            WHERE Year=? AND MemberName=? AND ISNULL(State,'')=ISNULL(?, '')
            """,
            year,
            h.name[:255],
            h.state,
        )
        row = cur.fetchone()
        if row:
            if apply:
                cur.execute(
                    """
                    UPDATE sResults.StateRepresentative
                    SET Role=COALESCE(?,Role), Address=COALESCE(?,Address), City=COALESCE(?,City),
                        PostalCode=COALESCE(?,PostalCode), Phone=COALESCE(?,Phone),
                        SourcePath=?, OwnerID=COALESCE(?,OwnerID)
                    WHERE StateRepID=?
                    """,
                    h.role,
                    h.address,
                    h.city,
                    h.postal,
                    h.phone,
                    src,
                    owner_id,
                    int(row[0]),
                )
            stats["state_rep"] += 1
            continue
        if apply:
            sid = next_id(cur, "StateRepresentative", "StateRepID")
            cur.execute(
                """
                INSERT INTO sResults.StateRepresentative
                (StateRepID, Year, State, MemberName, Role, Address, City, PostalCode, Phone, SourcePath, OwnerID)
                VALUES (?,?,?,?,?,?,?,?,?,?,?)
                """,
                sid,
                year,
                h.state,
                h.name[:255],
                h.role,
                h.address,
                h.city,
                h.postal,
                h.phone,
                src,
                owner_id,
            )
        stats["state_rep"] += 1

    # Breeders
    for b in bundle.breeders:
        kennel = (b.get("KennelName") or "").strip()
        prefix = (b.get("KennelPrefix") or kennel)[:100]
        if len(kennel) < 2:
            continue
        cur.execute(
            """
            SELECT BreederID, Notes FROM sResults.Breeder
            WHERE KennelPrefix=? OR KennelName=?
            """,
            prefix,
            kennel[:255],
        )
        row = cur.fetchone()
        note = f"Yearbook directory {year}"
        if row:
            if apply:
                cur.execute(
                    """
                    UPDATE sResults.Breeder
                    SET OwnerName=COALESCE(NULLIF(?,''), OwnerName),
                        City=COALESCE(NULLIF(?,''), City),
                        State=COALESCE(NULLIF(?,''), State),
                        KennelPrefix=COALESCE(NULLIF(?,''), KennelPrefix),
                        Notes=?,
                        SourceURL=COALESCE(SourceURL, ?)
                    WHERE BreederID=?
                    """,
                    b.get("OwnerName") or "",
                    b.get("City") or "",
                    b.get("State") or "",
                    prefix or "",
                    append_note(row[1], note),
                    f"yearbook:{src}",
                    int(row[0]),
                )
            stats["breeder"] += 1
            continue
        if apply:
            insert_identity(
                cur,
                "Breeder",
                "BreederID",
                ["KennelName", "KennelPrefix", "OwnerName", "City", "State", "SourceURL", "Notes"],
                [
                    kennel[:255],
                    prefix,
                    b.get("OwnerName"),
                    b.get("City"),
                    b.get("State"),
                    f"yearbook:{src}",
                    note,
                ],
            )
        stats["breeder"] += 1

    # Dog registrations
    for r in bundle.registrations:
        dog = (r.get("DogName") or "").strip()
        owner = (r.get("OwnerName") or "").strip()
        if len(dog) < 3:
            continue
        owner_id = None
        if owner and plausible_person(owner):
            cur.execute("SELECT OwnerID FROM sResults.Owner WHERE OwnerName=?", owner[:255])
            o = cur.fetchone()
            if o:
                owner_id = int(o[0])
            elif apply:
                owner_id = insert_identity(
                    cur, "Owner", "OwnerID", ["OwnerName"], [owner[:255]]
                )
        cur.execute("SELECT DogID, Notes, OwnerID FROM sResults.Dog WHERE DogName=?", dog[:255])
        drow = cur.fetchone()
        note = f"Yearbook new registration ({year})"
        if drow:
            if apply:
                cur.execute(
                    """
                    UPDATE sResults.Dog
                    SET OwnerID=COALESCE(?, OwnerID), Notes=?
                    WHERE DogID=?
                    """,
                    owner_id,
                    append_note(drow[1], note),
                    int(drow[0]),
                )
            stats["dog_reg"] += 1
            continue
        if apply:
            insert_identity(
                cur,
                "Dog",
                "DogID",
                ["DogName", "OwnerID", "Notes", "SourceURL"],
                [dog[:255], owner_id, note, f"yearbook:{src}"],
            )
        stats["dog_reg"] += 1

    # Certificates → Dog.Notes (create dog if needed)
    for c in bundle.certificates:
        dog = (c.get("DogName") or "").strip()
        if len(dog) < 3:
            continue
        owner = (c.get("OwnerName") or "").strip()
        owner_id = None
        if owner and plausible_person(owner):
            cur.execute("SELECT OwnerID FROM sResults.Owner WHERE OwnerName=?", owner[:255])
            o = cur.fetchone()
            if o:
                owner_id = int(o[0])
            elif apply:
                owner_id = insert_identity(
                    cur, "Owner", "OwnerID", ["OwnerName"], [owner[:255]]
                )
        note = f"{c.get('CertType', 'Certificate')} ({year})"
        cur.execute("SELECT DogID, Notes FROM sResults.Dog WHERE DogName=?", dog[:255])
        drow = cur.fetchone()
        if drow:
            if apply:
                cur.execute(
                    "UPDATE sResults.Dog SET OwnerID=COALESCE(?,OwnerID), Notes=? WHERE DogID=?",
                    owner_id,
                    append_note(drow[1], note),
                    int(drow[0]),
                )
            stats["dog_cert"] += 1
            continue
        if apply:
            insert_identity(
                cur,
                "Dog",
                "DogID",
                ["DogName", "OwnerID", "Notes", "SourceURL"],
                [dog[:255], owner_id, note, f"yearbook:{src}"],
            )
        stats["dog_cert"] += 1

    return stats


def iter_yearbook_media(limit: int | None = None):
    n = 0
    for folder in ("Yearbook Photos", "Yearbook Scans"):
        base = ROOT / folder
        if not base.is_dir():
            continue
        for dirpath, _, filenames in os.walk(base):
            if "national entries catalog" in dirpath.lower():
                continue
            for fn in sorted(filenames):
                fl = fn.lower()
                if fl.endswith("_ocr.txt"):
                    continue
                if not fl.endswith((".jpg", ".jpeg", ".png", ".pdf", ".txt")):
                    continue
                # skip volume multi-hundred-page PDFs here (handled elsewhere); allow nationals & photos & short pdfs
                path = Path(dirpath) / fn
                if fl.endswith(".pdf") and path.stat().st_size > 8_000_000:
                    # still allow named nationals / short trial pdfs under 25MB with max_pages
                    if "vol" in fl and "national" not in fl:
                        continue
                yield path
                n += 1
                if limit and n >= limit:
                    return


def process_path(path: Path, cur, apply: bool, max_pages: int | None) -> dict:
    ext = path.suffix.lower()
    if ext in (".jpg", ".jpeg", ".png", ".pdf"):
        ocr_path, year, text = write_ocr_sibling(
            str(path), max_pages=max_pages
        )
        src = str(path.relative_to(ROOT))
    else:
        with open(path, "r", encoding="utf-8", errors="ignore") as f:
            text = f.read()
        year = derive_year_from_text(text, folder_year_hint(str(path)))
        src = str(path.relative_to(ROOT))
        ocr_path = str(path)
    bundle = parse_meta_text(text, src)
    if not bundle.year and year:
        bundle.year = year
    stats = apply_bundle(cur, bundle, apply=apply)
    stats["year"] = bundle.year
    stats["source"] = src
    stats["ocr"] = ocr_path
    return stats


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--apply", action="store_true")
    ap.add_argument("--limit", type=int, default=None)
    ap.add_argument("--max-pages", type=int, default=3)
    ap.add_argument("paths", nargs="*", help="Optional specific files")
    args = ap.parse_args(argv)

    # ensure schema
    import yearbook_meta_schema as schema

    schema.main()

    cn = pyodbc.connect(CONN, timeout=120)
    cur = cn.cursor()
    totals = {
        k: 0
        for k in (
            "board",
            "committee",
            "state_rep",
            "owner_aug",
            "breeder",
            "dog_reg",
            "dog_cert",
            "skip_noyear",
            "files",
        )
    }
    paths = [Path(p) for p in args.paths] if args.paths else list(iter_yearbook_media(args.limit))
    for path in paths:
        if not path.is_file():
            print("MISSING", path, flush=True)
            continue
        try:
            st = process_path(path, cur, args.apply, args.max_pages)
        except Exception as e:
            print(f"ERR {path}: {e}", flush=True)
            continue
        totals["files"] += 1
        for k in totals:
            if k in st and isinstance(st[k], int):
                totals[k] += st[k]
        interesting = {
            k: st[k]
            for k in (
                "board",
                "committee",
                "state_rep",
                "owner_aug",
                "breeder",
                "dog_reg",
                "dog_cert",
            )
            if st.get(k)
        }
        if interesting or st.get("skip_noyear"):
            print(
                f"year={st.get('year')} {interesting or {'skip_noyear':1}} {st.get('source')}",
                flush=True,
            )
        if args.apply and totals["files"] % 10 == 0:
            cn.commit()
    if args.apply:
        cn.commit()
        print("COMMITTED", totals, flush=True)
    else:
        cn.rollback()
        print("DRY-RUN", totals, flush=True)
    cn.close()
    return 0


if __name__ == "__main__":
    sys.exit(main())
