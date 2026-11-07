#!/usr/bin/env python3
"""Ingest New Club Members / Kennel Prefixes / Transfers / Registrations.

From early Updated Yearbook OCR into Owner / Breeder / Dog.
Year-scoped; conservative parsers for multi-column OCR.
"""
from __future__ import annotations

import argparse
import re
from pathlib import Path

import pyodbc

from ocr_yearbook_source import folder_year_hint
from remount_source_divisions import CONN
from yearbook_meta_ingest import append_note, insert_identity, plausible_person
from yearbook_meta_schema import ensure
from yearbook_ocr import (
    ROOT,
    early_pdfs,
    fix_ocr_li_confusion,
    is_human_name,
    name_key,
    norm_space,
    ocr_pdf_hq,
)

_US = {
    "AL", "AK", "AZ", "AR", "CA", "CO", "CT", "DE", "FL", "GA", "HI", "ID", "IL",
    "IN", "IA", "KS", "KY", "LA", "ME", "MD", "MA", "MI", "MN", "MS", "MO", "MT",
    "NE", "NV", "NH", "NJ", "NM", "NY", "NC", "ND", "OH", "OK", "OR", "PA", "RI",
    "SC", "SD", "TN", "TX", "UT", "VT", "VA", "WA", "WV", "WI", "WY", "DC",
}

_HDR = re.compile(
    r"(?im)^(?:"
    r"NEW\s+CLUB\s+MEMBERS?|"
    r"NEW\s+KENNEL\s+PREFIX(?:ES)?|"
    r"NEWLY\s+REGISTERED\s+KENNEL|"
    r"KENNEL\s+PREFIX(?:ES)?|"
    r"TRANSFERS?\s+OF\s+OWNERSHIP|"
    r"NEW\s+TERRIER\s+REGISTRATIONS?|"
    r"NEW\s+REGISTRATIONS?"
    r")\b.*$"
)
_STOP = re.compile(
    r"(?im)^(?:"
    r"BOARD\s+OF\s+DIRECTORS|DIRECTORY\s+OF\s+BREEDERS?|.*BREEDER\s+DIRECTORY|"
    r"TRIAL\s+CERTIFICATES?|NATURAL\s+HUNTING|DIVISION\s+[A-D]\b|"
    r"SANCTIONED\s+TRIAL|CONTENTS|INTRODUCTION|STATE\s+REPRESENT|"
    r"HAPPY\s+HUNTING\s+GROUNDS|TRUE\s+GRIT"
    r")\b"
)

# "Linda Barret, GA" / "Brian & Dianne Ferguson, NY" / "M/M Spencer Scott, Jr., CT"
_MEMBER = re.compile(
    r"(?m)^\s*((?:M/?M|Mr\.?|Mrs\.?|Ms\.?|Miss|Dr\.?)\s+)?"
    r"([A-Z][A-Za-z'\-]+(?:\s+(?:&|and)\s+[A-Z][A-Za-z'\-]+)?"
    r"(?:\s+[A-Z]\.?)?"
    r"(?:\s+[A-Z][A-Za-z'\-]+){0,3}"
    r"(?:,?\s*(?:Jr\.?|Sr\.?|II|III|IV))?)"
    r",\s*([A-Z]{2})\s*$"
)

# Transfer: "DOG NAME, from A of ST to B of ST."
_TRANSFER = re.compile(
    r"(?is)\b([A-Z][A-Z0-9' \-]{2,50}?),\s*from\s+(.+?)\s+to\s+(.+?)(?:\.|\n)"
)

# Prefix table-ish: ALLCAPS PREFIX then owner name (same/next lines hard in columns)
_PREFIX_ROW = re.compile(
    r"(?m)^\s*([A-Z][A-Z0-9' \-]{2,30})\s{2,}([A-Z][A-Za-z' &\-.]{2,50})\s*$"
)
_PREFIX_INLINE = re.compile(
    r"(?m)^\s*([A-Z][A-Z0-9' \-]{2,30})\s+([A-Z][A-Za-z'\-]+(?:\s+(?:&|and)\s+[A-Z][A-Za-z'\-]+)?(?:\s+[A-Z][A-Za-z'\-]+){0,3})\s*$"
)

_AWARD_JUNK = re.compile(
    r"(?i)\b(handler|chairman|outstanding|reserve|breeder|committee|true grit|"
    r"happy hunting|welcome|board of directors)\b"
)


def strip_ensemble_extras(text: str) -> str:
    return re.sub(
        r"(?is)---\s*OCR-ENSEMBLE-EXTRAS\s*---.*?(?=(?:---\s*page\s+\d+\s*---)|\Z)",
        "\n",
        text,
    )


def extract_member_sections(text: str) -> dict[str, str]:
    text = fix_ocr_li_confusion(strip_ensemble_extras(text))
    lines = text.splitlines()
    headers = []
    for i, ln in enumerate(lines):
        s = norm_space(ln)
        if len(s) < 8 or len(s) > 120:
            continue
        if _HDR.match(s) or _STOP.match(s):
            headers.append((i, s.upper()))
    sections: dict[str, str] = {}
    for hi, (idx, key) in enumerate(headers):
        end = headers[hi + 1][0] if hi + 1 < len(headers) else len(lines)
        body = "\n".join(lines[idx + 1 : end])
        if "NEW CLUB MEMBER" in key:
            sections["MEMBERS"] = sections.get("MEMBERS", "") + "\n" + body
        elif "PREFIX" in key or "NEWLY REGISTERED KENNEL" in key:
            sections["PREFIX"] = sections.get("PREFIX", "") + "\n" + body
        elif "TRANSFER" in key:
            sections["TRANSFER"] = sections.get("TRANSFER", "") + "\n" + body
        elif "REGISTRATION" in key:
            sections["REG"] = sections.get("REG", "") + "\n" + body
    return sections


def clean_person(name: str) -> str | None:
    n = norm_space(name)
    n = re.sub(r"^(?:M/?M|Mr\.?|Mrs\.?|Ms\.?|Miss|Dr\.?)\s+", "", n, flags=re.I)
    n = re.sub(r"\s+", " ", n).strip(" ,.")
    if _AWARD_JUNK.search(n):
        return None
    if not plausible_person(n) and not is_human_name(n):
        # allow "A & B Last" couples
        if not re.match(
            r"^[A-Z][A-Za-z'\-]+\s+(?:&|and)\s+[A-Z][A-Za-z'\-]+(?:\s+[A-Z][A-Za-z'\-]+)?$",
            n,
        ):
            return None
    if len(n) < 5 or len(n) > 60:
        return None
    return n[:255]


def parse_members(block: str) -> list[dict]:
    rows = []
    for m in _MEMBER.finditer(block):
        name = clean_person(m.group(2))
        st = m.group(3).upper()
        if not name or st not in _US:
            continue
        rows.append({"OwnerName": name, "State": st})
    seen = set()
    out = []
    for r in rows:
        k = name_key(r["OwnerName"])
        if k in seen:
            continue
        seen.add(k)
        out.append(r)
    return out


def parse_transfers(block: str) -> list[dict]:
    rows = []
    for m in _TRANSFER.finditer(block):
        dog = norm_space(m.group(1))
        if _AWARD_JUNK.search(dog) or len(dog) < 3:
            continue
        # skip memorial blurbs without "from ... to"
        frm = norm_space(m.group(2))
        to = norm_space(m.group(3))
        # new owner: take leading person-ish chunk before "of ST" if present
        to_person = re.split(r"\s+of\s+", to, maxsplit=1)[0]
        to_person = clean_person(to_person) or None
        if not to_person:
            # "M/M D. Marcum, KY" style
            tm = re.match(
                r"((?:M/?M|Mr\.?|Mrs\.?|Ms\.?)?\s*[A-Z][A-Za-z' \-&.]{2,40})",
                to,
            )
            if tm:
                to_person = clean_person(tm.group(1))
        if not to_person:
            continue
        rows.append({"DogName": dog[:255], "OwnerName": to_person, "FromNote": frm[:200]})
    seen = set()
    out = []
    for r in rows:
        k = (name_key(r["DogName"]), name_key(r["OwnerName"]))
        if k in seen:
            continue
        seen.add(k)
        out.append(r)
    return out


def parse_prefixes(block: str) -> list[dict]:
    rows = []
    for pat in (_PREFIX_ROW, _PREFIX_INLINE):
        for m in pat.finditer(block):
            prefix = norm_space(m.group(1))
            owner = clean_person(m.group(2))
            if not owner:
                continue
            # prefix should look like a kennel word (mostly caps / Title)
            if len(prefix) < 3 or len(prefix) > 40:
                continue
            if prefix.lower() in {"name", "owner", "state", "breeder", "true", "grit"}:
                continue
            if _AWARD_JUNK.search(prefix):
                continue
            rows.append({"KennelPrefix": prefix[:100], "OwnerName": owner})
    # Also: lines like "Honey Hill" / "Susan Porter" / "CT" stacked — skip (too weak)
    seen = set()
    out = []
    for r in rows:
        k = (r["KennelPrefix"].lower(), name_key(r["OwnerName"]))
        if k in seen:
            continue
        seen.add(k)
        out.append(r)
    return out


def parse_regs(block: str) -> list[dict]:
    """Registration lists are often dog-name-only columns — capture dog names only."""
    rows = []
    for ln in block.splitlines():
        s = norm_space(ln)
        if len(s) < 3 or len(s) > 60:
            continue
        if _AWARD_JUNK.search(s):
            continue
        if re.fullmatch(r"\d{1,3}", s):
            continue
        if s.lower() in {"name", "owner", "breeder", "state", "same"}:
            continue
        if not re.match(r"^[A-Z][A-Za-z0-9' \-]{2,55}$", s):
            continue
        if re.search(r",\s*[A-Z]{2}$", s):
            continue
        # Drop people misread as dogs (Sue Fand, Sonja Owen, etc.)
        if is_human_name(s) or (plausible_person(s) and len(s.split()) <= 3 and " of " not in s.lower()):
            # keep if looks like kennel dog: contains of / apostrophe kennel / 4+ tokens
            if " of " not in s.lower() and "'" not in s and len(s.split()) < 4:
                continue
        # drop OCR mush lines
        if re.search(r"(?i)\b(bree|tedeseo|geof|russue)\b", s):
            continue
        if s.endswith(" of"):  # truncated "Poppycock Cheshire of"
            continue
        rows.append({"DogName": s[:255], "OwnerName": None})
    seen = set()
    out = []
    for r in rows:
        k = name_key(r["DogName"])
        if k in seen:
            continue
        seen.add(k)
        out.append(r)
    return out


def upsert_owner(cur, r: dict, note: str, apply: bool) -> int | None:
    name = r["OwnerName"]
    cur.execute("SELECT OwnerID, Notes FROM sResults.Owner WHERE OwnerName=?", name)
    row = cur.fetchone()
    if row:
        if apply:
            cur.execute(
                """
                UPDATE sResults.Owner
                SET State=COALESCE(NULLIF(?,''), State),
                    City=COALESCE(NULLIF(?,''), City),
                    Notes=?
                WHERE OwnerID=?
                """,
                r.get("State") or "",
                r.get("City") or "",
                append_note(row[1], note),
                int(row[0]),
            )
        return int(row[0])
    if not apply:
        return None
    return insert_identity(
        cur,
        "Owner",
        "OwnerID",
        ["OwnerName", "City", "State", "Notes"],
        [name, r.get("City"), r.get("State"), note],
    )


def upsert_breeder_prefix(cur, r: dict, year: int, source: str, apply: bool) -> None:
    prefix, owner = r["KennelPrefix"], r["OwnerName"]
    note = f"Yearbook kennel prefix {year}"
    cur.execute(
        "SELECT BreederID, Notes FROM sResults.Breeder WHERE KennelPrefix=? OR KennelName=?",
        prefix,
        prefix,
    )
    row = cur.fetchone()
    if row:
        if apply:
            cur.execute(
                """
                UPDATE sResults.Breeder
                SET OwnerName=COALESCE(NULLIF(?,''), OwnerName),
                    KennelPrefix=COALESCE(NULLIF(?,''), KennelPrefix),
                    Notes=?, SourceURL=COALESCE(SourceURL, ?)
                WHERE BreederID=?
                """,
                owner,
                prefix,
                append_note(row[1], note),
                f"yearbook:{source}",
                int(row[0]),
            )
    elif apply:
        insert_identity(
            cur,
            "Breeder",
            "BreederID",
            ["KennelName", "KennelPrefix", "OwnerName", "SourceURL", "Notes"],
            [prefix, prefix, owner, f"yearbook:{source}", note],
        )
    upsert_owner(cur, {"OwnerName": owner}, note, apply)


def upsert_dog(cur, r: dict, year: int, source: str, note: str, apply: bool) -> None:
    dog = r["DogName"]
    owner = r.get("OwnerName")
    owner_id = None
    if owner:
        owner_id = upsert_owner(cur, {"OwnerName": owner}, note, apply)
    cur.execute("SELECT DogID, Notes, OwnerID FROM sResults.Dog WHERE DogName=?", dog)
    row = cur.fetchone()
    if row:
        if apply:
            cur.execute(
                "UPDATE sResults.Dog SET OwnerID=COALESCE(?, OwnerID), Notes=? WHERE DogID=?",
                owner_id,
                append_note(row[1], note),
                int(row[0]),
            )
        return
    if apply:
        insert_identity(
            cur,
            "Dog",
            "DogID",
            ["DogName", "OwnerID", "Notes", "SourceURL"],
            [dog, owner_id, note, f"yearbook:{source}"],
        )


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--apply", action="store_true")
    ap.add_argument("--max-pages", type=int, default=12)
    args = ap.parse_args()

    cn = pyodbc.connect(CONN, timeout=120)
    cur = cn.cursor()
    ensure(cur)
    cn.commit()

    totals = {"members": 0, "prefix": 0, "reg": 0, "transfer": 0, "files": 0}
    for path in early_pdfs():
        rel = str(path.relative_to(ROOT))
        text, _year = ocr_pdf_hq(path, max_pages=args.max_pages, force=False)
        hint = folder_year_hint(str(path))
        year = hint if hint and hint in range(1984, 1991) else _year
        if not year:
            continue
        sections = extract_member_sections(text)
        print(f"{rel} year={year} sections={list(sections.keys())}", flush=True)

        if "MEMBERS" in sections:
            rows = parse_members(sections["MEMBERS"])
            print(f"  members={len(rows)} sample={rows[:8]}", flush=True)
            for r in rows:
                upsert_owner(cur, r, f"JRTCA new club member ({year})", args.apply)
            totals["members"] += len(rows)

        if "PREFIX" in sections:
            rows = [
                r
                for r in parse_prefixes(sections["PREFIX"])
                # reject OCR garbage prefixes / glued owners
                if re.match(r"^[A-Z][A-Za-z0-9' \-]{2,30}$", r["KennelPrefix"])
                and not re.search(r"(?i)[sx]{4,}|owner | me$", r["KennelPrefix"] + " " + r["OwnerName"])
                and " " not in r["OwnerName"].split()[0]  # sanity
                and len(r["OwnerName"].split()) <= 4
            ]
            print(f"  prefix={len(rows)} sample={rows[:8]}", flush=True)
            for r in rows:
                upsert_breeder_prefix(cur, r, int(year), rel, args.apply)
            totals["prefix"] += len(rows)

        if "REG" in sections:
            rows = parse_regs(sections["REG"])
            print(f"  reg={len(rows)} sample={[r['DogName'] for r in rows[:8]]}", flush=True)
            for r in rows:
                upsert_dog(cur, r, int(year), rel, f"Yearbook registration {year}", args.apply)
            totals["reg"] += len(rows)

        if "TRANSFER" in sections:
            rows = parse_transfers(sections["TRANSFER"])
            print(f"  transfer={len(rows)} sample={rows[:6]}", flush=True)
            for r in rows:
                upsert_dog(
                    cur,
                    r,
                    int(year),
                    rel,
                    f"Yearbook transfer {year}: from {r.get('FromNote','')}",
                    args.apply,
                )
            totals["transfer"] += len(rows)

        totals["files"] += 1
        if args.apply:
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
    raise SystemExit(main())
