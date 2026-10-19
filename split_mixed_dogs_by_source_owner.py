#!/usr/bin/env python3
"""
Split Dog rows that incorrectly absorbed placements for same-named dogs
owned by different households (e.g. Skeeter / Roux short-name merges).

For each candidate dog, re-read TrialResultFilePath sources, extract
"DogName, owned by Owner" lines, and when a placement's trial source
attributes that dog name to an incompatible owner, remount the placement
onto a dog owned by that source owner.

Usage:
  py -3 split_mixed_dogs_by_source_owner.py --dry-run
  py -3 split_mixed_dogs_by_source_owner.py
  py -3 split_mixed_dogs_by_source_owner.py --dog-id 1075561
"""
from __future__ import annotations

import argparse
import html as html_lib
import re
import sys
from collections import defaultdict
from pathlib import Path

import pyodbc
from normalize_trialresults_data import (
    _canonicalize_owner_tokens,
    normalize_dog_name,
    normalize_owner_name,
    owner_name_tokens,
    owners_compatible_for_dog_merge,
)
from populate_trialresults_fixed import get_or_create_dog, get_or_create_owner


def is_foreign_source_owner(db_owner: str | None, src_owner: str) -> bool:
    """True when source owner is a different household than the DB dog's owner.

    Same-surname family listings (Mark Waelterman vs Jerry & Ilse Waelterman)
    are kept together for short-name splits — those are usually the same dog
    shown under a household member, not a different Skeeter/Roux.
    """
    if owners_compatible_for_dog_merge(db_owner, src_owner):
        return False
    ta, tb = owner_name_tokens(db_owner), owner_name_tokens(src_owner)
    if not ta or not tb:
        return False
    ta, tb = _canonicalize_owner_tokens(ta, tb)
    shared = ta & tb
    # Long shared token ≈ shared surname (Waelterman, Howerton, …)
    if any(len(t) >= 6 for t in shared):
        return False
    return True


def cluster_owner_label(owners: list[str]) -> str:
    """Pick a canonical owner string from compatible variants."""
    if not owners:
        return ""
    clusters: list[list[str]] = []
    for o in owners:
        placed = False
        for c in clusters:
            if owners_compatible_for_dog_merge(o, c[0]):
                c.append(o)
                placed = True
                break
        if not placed:
            clusters.append([o])
    clusters.sort(key=len, reverse=True)
    # Prefer cleaned, longer spellings
    best = clusters[0]
    scored = []
    for o in best:
        cleaned = normalize_owner_name(o) or o
        scored.append((len(cleaned), cleaned.count("&"), len(cleaned.split()), cleaned))
    scored.sort(reverse=True)
    return scored[0][3]

sys.stdout.reconfigure(encoding="utf-8", errors="replace")

ROOT = Path(r"c:\Users\mw\OneDrive - timberwilde.net\repos\jrtca_results")

OWNED_BY_RE = re.compile(
    r"(?P<dog>[A-Za-z0-9][^,\n\r<]{0,80}?)\s*,\s*owned by\s+(?P<owner>[^<\n\r]+)",
    re.I,
)
# Tab / two-column yearbook lines: "2nd: DogName\tOwner Name"
TAB_OWNER_RE = re.compile(
    r"(?P<place>(?:\d{1,2}(?:st|nd|rd|th)|Best|Reserve)\s*:\s*)"
    r"(?P<dog>[^\t\n\r,]{1,80}?)\t+(?P<owner>[^\t\n\r]{2,80})",
    re.I,
)
# HTML debris glued onto dog capture groups (e.g. "BR>2nd: Skeeter")
HTML_DOG_JUNK_RE = re.compile(
    r"^(?:BR>)+|^SPAN\s+STYLE=\"[^\"]*\">\s*|^</?[A-Za-z][^>]*>\s*",
    re.I,
)


def connect():
    last = None
    for d in (
        "ODBC Driver 17 for SQL Server",
        "ODBC Driver 18 for SQL Server",
        "SQL Server",
    ):
        try:
            return pyodbc.connect(
                f"DRIVER={{{d}}};SERVER=localhost\\SQLEXPRESS;"
                f"DATABASE=TrialResults;Trusted_Connection=yes;",
                timeout=30,
            )
        except Exception as e:
            last = e
    raise SystemExit(f"DB connect failed: {last}")


def scrub(s: str) -> str:
    s = html_lib.unescape(s or "")
    s = s.replace("\xa0", " ").replace("&nbsp;", " ")
    return re.sub(r"\s+", " ", s).strip(" .,;:")


def clean_source_dog_name(dog: str) -> str:
    """Strip HTML/placement junk so 'BR>2nd: Skeeter' → 'Skeeter'."""
    dog = scrub(dog)
    # Repeat junk strip — SPAN/BR can stack with ordinals
    for _ in range(4):
        nxt = HTML_DOG_JUNK_RE.sub("", dog).strip()
        if nxt == dog:
            break
        dog = nxt
    dog = normalize_dog_name(dog) or dog
    return scrub(dog)


def dog_match_key(name: str) -> str:
    n = clean_source_dog_name(name) or scrub(name)
    return re.sub(r"[^a-z0-9]", "", n.lower())


def resolve_path(path: str | None) -> Path | None:
    if not path:
        return None
    p = Path(path)
    if p.is_file():
        return p
    # Try under repo root by basename / relative tail
    candidates = [
        ROOT / p.name,
        ROOT / Path(*p.parts[-2:]) if len(p.parts) >= 2 else None,
        ROOT / Path(*p.parts[-3:]) if len(p.parts) >= 3 else None,
    ]
    for c in candidates:
        if c and c.is_file():
            return c
    return None


def read_text(path: Path) -> str:
    raw = path.read_bytes()
    for enc in ("utf-8", "cp1252", "latin-1"):
        try:
            return raw.decode(enc)
        except Exception:
            continue
    return raw.decode("utf-8", errors="replace")


def _trim_owner(owner: str) -> str:
    owner = scrub(owner)
    owner = re.split(
        r"(?=\d{1,2}(?:st|nd|rd|th)\s*:)|(?=\b(?:Best|Reserve|Champion)\s*:)",
        owner,
        maxsplit=1,
        flags=re.I,
    )[0]
    return scrub(owner)


def extract_owned_by_pairs(text: str) -> list[tuple[str, str]]:
    pairs = []
    seen: set[tuple[str, str]] = set()

    def add(dog: str, owner: str) -> None:
        dog = clean_source_dog_name(dog)
        owner = _trim_owner(owner)
        if not dog or not owner or len(dog) >= 80:
            return
        key = (dog_match_key(dog), owner.lower())
        if key in seen:
            return
        seen.add(key)
        pairs.append((dog, owner))

    for m in OWNED_BY_RE.finditer(text):
        add(m.group("dog"), m.group("owner"))
    for m in TAB_OWNER_RE.finditer(text):
        add(m.group("dog"), m.group("owner"))
    return pairs


def source_owners_for_dog(text: str, dog_name: str) -> list[str]:
    """Owners attributed to this dog name (exact or safe registered-name match).

    Does NOT treat short call names as prefixes of longer kennel names
    (e.g. 'Roux' must not match 'Brandywine Roux').
    """
    want = dog_match_key(dog_name)
    if not want:
        return []
    want_words = re.findall(r"[A-Za-z0-9]+", dog_name or "")
    owners = []
    for src_dog, src_owner in extract_owned_by_pairs(text):
        sk = dog_match_key(src_dog)
        if not sk:
            continue
        if sk == want:
            owners.append(src_owner)
            continue
        # Registered-name truncation: "Brandywine Roux" ↔
        # "Brandywine Roux of Blackburn" (require long shared stem)
        shorter, longer = (sk, want) if len(sk) <= len(want) else (want, sk)
        if longer.startswith(shorter) and len(shorter) >= 10:
            owners.append(src_owner)
            continue
        # "Skeeter of Blackburn" ↔ "Skeeter" (either direction)
        src_words = re.findall(r"[A-Za-z0-9]+", src_dog or "")
        if want_words and src_words and want_words[0].lower() == src_words[0].lower():
            if (
                len(want_words) == 1
                and len(src_words) >= 3
                and src_words[1].lower() == "of"
            ):
                owners.append(src_owner)
            elif (
                len(src_words) == 1
                and len(want_words) >= 3
                and want_words[1].lower() == "of"
            ):
                owners.append(src_owner)
    return owners


def dominant_owner(owners: list[str]) -> str | None:
    if not owners:
        return None
    # Cluster compatible owners and pick largest cluster's first name
    clusters: list[list[str]] = []
    for o in owners:
        placed = False
        for c in clusters:
            if owners_compatible_for_dog_merge(o, c[0]):
                c.append(o)
                placed = True
                break
        if not placed:
            clusters.append([o])
    clusters.sort(key=len, reverse=True)
    # Prefer longer/more complete spelling in the dominant cluster
    return max(clusters[0], key=lambda s: (len(s), s))


def find_candidate_dog_ids(
    cur, min_placements: int = 8, include_two_token: bool = False
) -> list[tuple[int, str, str | None, int]]:
    """Dogs with short/generic names and enough placements to risk mixing.

    Default is single-token call names only (Skeeter, Roux, Cosmo, …).
    Two-token registered names (Northgate Taylor, …) often change listed
    owners over a career; treating those as mixes fragments one dog.
    Pass include_two_token=True or --dog-id for explicit cases.
    """
    cur.execute(
        """
        SELECT d.DogID, d.DogName, o.OwnerName, COUNT(p.TrialPlacementsID) AS n
        FROM sResults.Dog d
        LEFT JOIN sResults.Owner o ON o.OwnerID = d.OwnerID
        JOIN sResults.TrialPlacements p ON p.DogID = d.DogID
        WHERE d.DogName IS NOT NULL AND LTRIM(RTRIM(d.DogName)) <> ''
        GROUP BY d.DogID, d.DogName, o.OwnerName
        HAVING COUNT(p.TrialPlacementsID) >= ?
        ORDER BY n DESC
        """,
        min_placements,
    )
    rows = cur.fetchall()
    out = []
    for dog_id, name, owner, n in rows:
        words = re.findall(r"[A-Za-z0-9]+", name or "")
        if len(words) == 1:
            out.append((dog_id, name, owner, n))
        elif include_two_token and len(words) == 2 and n >= 25:
            out.append((dog_id, name, owner, n))
    return out


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--dry-run", action="store_true")
    ap.add_argument("--dog-id", type=int, action="append")
    ap.add_argument("--min-placements", type=int, default=8)
    ap.add_argument("--limit-dogs", type=int, default=0, help="0 = all candidates")
    ap.add_argument(
        "--include-two-token",
        action="store_true",
        help="Also scan 2-token names with many placements (risky for transfers)",
    )
    args = ap.parse_args()

    cn = connect()
    cur = cn.cursor()

    if args.dog_id:
        candidates = []
        for did in args.dog_id:
            cur.execute(
                """
                SELECT d.DogID, d.DogName, o.OwnerName, COUNT(p.TrialPlacementsID)
                FROM sResults.Dog d
                LEFT JOIN sResults.Owner o ON o.OwnerID = d.OwnerID
                LEFT JOIN sResults.TrialPlacements p ON p.DogID = d.DogID
                WHERE d.DogID = ?
                GROUP BY d.DogID, d.DogName, o.OwnerName
                """,
                did,
            )
            row = cur.fetchone()
            if row:
                candidates.append(tuple(row))
    else:
        candidates = find_candidate_dog_ids(
            cur, args.min_placements, include_two_token=args.include_two_token
        )
        if args.limit_dogs:
            candidates = candidates[: args.limit_dogs]

    print(
        f"{'DRY RUN — ' if args.dry_run else ''}"
        f"Scanning {len(candidates)} candidate dogs for owner mixes..."
    )

    stats = defaultdict(int)
    mixed_summary = []
    path_cache: dict[str, str | None] = {}
    # Keyed by (resolved_path, dog_match_key) — MUST include dog name or
    # Cooper's owners get reused for Skeeter on the same trial file.
    owners_cache: dict[tuple[str, str], list[str]] = {}
    text_cache: dict[str, str] = {}

    for dog_id, dog_name, db_owner, npls in candidates:
        stats["dogs_scanned"] += 1
        dog_key = dog_match_key(dog_name)
        cur.execute(
            """
            SELECT p.TrialPlacementsID, p.TrialListID, p.Result,
                   tl.TrialResultFilePath, tl.TrialName, tl.Year
            FROM sResults.TrialPlacements p
            JOIN sResults.TrialList tl ON tl.TrialListID = p.TrialListID
            WHERE p.DogID = ?
            """,
            dog_id,
        )
        placements = cur.fetchall()

        # Collect incompatible source owners across this dog's trials
        foreign_by_path: dict[str, list[str]] = {}
        for pid, tid, result, path, tname, year in placements:
            if not path:
                continue
            if path not in path_cache:
                rp = resolve_path(path)
                path_cache[path] = str(rp) if rp else None
            resolved = path_cache[path]
            if not resolved:
                continue
            cache_key = (resolved, dog_key)
            if cache_key not in owners_cache:
                try:
                    if resolved not in text_cache:
                        text_cache[resolved] = read_text(Path(resolved))
                    owners_cache[cache_key] = source_owners_for_dog(
                        text_cache[resolved], dog_name
                    )
                except Exception:
                    owners_cache[cache_key] = []
            src_owners = owners_cache[cache_key]
            if not src_owners:
                continue
            # If ANY source owner for this name is incompatible with DB owner,
            # this trial may need remounts
            foreign = [o for o in src_owners if is_foreign_source_owner(db_owner, o)]
            home = [o for o in src_owners if not is_foreign_source_owner(db_owner, o)]
            if foreign and not home:
                foreign_by_path[resolved] = ("foreign_only", foreign)
            elif foreign and home:
                foreign_by_path[resolved] = ("ambiguous", foreign)

        if not foreign_by_path:
            continue

        stats["dogs_mixed"] += 1
        remounts = []
        for pid, tid, result, path, tname, year in placements:
            resolved = path_cache.get(path or "")
            if not resolved or resolved not in foreign_by_path:
                continue
            kind, foreign_owners = foreign_by_path[resolved]
            if kind == "ambiguous":
                stats["ambiguous_trial_skipped"] += 1
                continue
            target_owner = cluster_owner_label(foreign_owners)
            if not target_owner:
                continue
            remounts.append((pid, target_owner, year, tname, result))

        if not remounts:
            mixed_summary.append(
                (
                    dog_id,
                    dog_name,
                    db_owner,
                    npls,
                    0,
                    [v[1][:2] for v in foreign_by_path.values()][:3],
                )
            )
            continue

        # Collapse compatible target owner labels (Hines variants → one dog)
        by_owner: dict[str, list] = defaultdict(list)
        label_canon: dict[str, str] = {}
        for pid, target_owner, year, tname, result in remounts:
            canon = None
            for existing in list(label_canon.values()):
                if owners_compatible_for_dog_merge(target_owner, existing):
                    canon = existing
                    break
            if canon is None:
                canon = cluster_owner_label([target_owner])
            label_canon[target_owner] = canon
            by_owner[canon].append((pid, target_owner, year, tname, result))

        print(
            f"\nMIXED DogID={dog_id} {dog_name!r} db_owner={db_owner!r} "
            f"placements={npls} remount={len(remounts)}"
        )
        for own, items in by_owner.items():
            print(f"  -> {own!r}: {len(items)} placements")

        mixed_summary.append(
            (dog_id, dog_name, db_owner, npls, len(remounts), list(by_owner.keys()))
        )

        if args.dry_run:
            stats["would_remount"] += len(remounts)
            continue

        for target_owner, items in by_owner.items():
            clean_owner = normalize_owner_name(target_owner) or target_owner
            owner_id = get_or_create_owner(cur, clean_owner)
            new_dog_id = get_or_create_dog(cur, dog_name, owner_id)
            if new_dog_id == dog_id:
                cur.execute(
                    "INSERT INTO sResults.Dog (DogName, OwnerID) OUTPUT INSERTED.DogID "
                    "VALUES (?, ?)",
                    dog_name,
                    owner_id,
                )
                new_dog_id = cur.fetchone()[0]
            for pid, *_rest in items:
                cur.execute(
                    "UPDATE sResults.TrialPlacements SET DogID = ? WHERE TrialPlacementsID = ?",
                    new_dog_id,
                    pid,
                )
                stats["placements_remounted"] += 1
            stats["dogs_created_or_used"] += 1
            print(f"  remounted {len(items)} -> DogID {new_dog_id} ({clean_owner})")

    if not args.dry_run:
        cn.commit()
        print("\nCommitted.")
    else:
        cn.rollback()
        print("\nDry run — no changes committed.")

    print("\n=== SUMMARY ===")
    for k in sorted(stats):
        print(f"  {k}: {stats[k]}")
    print(f"\nMixed dogs found: {len(mixed_summary)}")
    for row in mixed_summary[:40]:
        print(
            f"  DogID={row[0]} {row[1]!r} owner={row[2]!r} "
            f"n={row[3]} remount={row[4]} targets={row[5]}"
        )

    cn.close()


if __name__ == "__main__":
    main()
