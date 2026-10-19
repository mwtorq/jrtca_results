#!/usr/bin/env python3
"""
Full-database placement attestation repair.

For every TrialPlacements row:
  1. If the assigned dog name is attested in the trial source under a
     compatible owner → keep.
  2. If attested only under a foreign owner → remount to that owner’s dog
     (same registered/call name).
  3. If the dog name is NOT in the source at all → remount to the best
     source dog at the same Result place (token overlap / similarity),
     else move to a neutrally named UNVERIFIED-{id} dog so Power BI
     Contains filters on the original name no longer hit it.

Also:
  - Reassigns 1-token call-name placements by unambiguous source owner.
  - Renames any leftover *[unverified]* dogs to UNVERIFIED-{DogID}.

Usage:
  py -3 repair_all_placements_from_sources.py --dry-run
  py -3 repair_all_placements_from_sources.py
  py -3 repair_all_placements_from_sources.py --limit 5000
"""
from __future__ import annotations

import argparse
import re
import sys
from collections import defaultdict
from difflib import SequenceMatcher
from pathlib import Path

from normalize_trialresults_data import (
    normalize_owner_name,
    owners_compatible_for_dog_merge,
)
from populate_trialresults_fixed import get_or_create_dog, get_or_create_owner
from split_mixed_dogs_by_source_owner import (
    clean_source_dog_name,
    cluster_owner_label,
    connect,
    dog_match_key,
    extract_owned_by_pairs,
    is_foreign_source_owner,
    read_text,
    resolve_path,
)

sys.stdout.reconfigure(encoding="utf-8", errors="replace")

PLACE_PAIR_RE = re.compile(
    r"(?P<place>\d{1,2}(?:st|nd|rd|th)|Best|Reserve)\s*:\s*"
    r"(?P<dog>[A-Za-z0-9][^,\n\r\t]{0,80}?)\s*"
    r"(?:,\s*owned by\s+|\t+)(?P<owner>[^<\n\r]+)",
    re.I,
)


def name_attested(dog_name: str, src_dog: str) -> bool:
    want = dog_match_key(dog_name)
    sk = dog_match_key(src_dog)
    if not want or not sk:
        return False
    if sk == want:
        return True
    shorter, longer = (sk, want) if len(sk) <= len(want) else (want, sk)
    # Registered-name truncation only (Brandywine Roux ↔ … of Blackburn)
    if longer.startswith(shorter) and len(shorter) >= 10:
        return True
    # Skeeter of Blackburn ↔ Skeeter (call + of Kennel)
    src_words = re.findall(r"[A-Za-z0-9]+", src_dog or "")
    want_words = re.findall(r"[A-Za-z0-9]+", dog_name or "")
    if (
        len(want_words) >= 1
        and len(src_words) >= 1
        and want_words[0].lower() == src_words[0].lower()
    ):
        # "Skeeter of Blackburn" vs "Skeeter"
        if len(want_words) >= 3 and want_words[1].lower() == "of" and len(src_words) == 1:
            return True
        if len(src_words) >= 3 and src_words[1].lower() == "of" and len(want_words) == 1:
            return True
        # Both "X of Y" with same call
        if (
            len(want_words) >= 3
            and len(src_words) >= 3
            and want_words[1].lower() == "of"
            and src_words[1].lower() == "of"
            and want_words[0].lower() == src_words[0].lower()
        ):
            return True
    return False


def place_entries(text: str) -> list[tuple[str, str, str]]:
    out = []
    for m in PLACE_PAIR_RE.finditer(text):
        place = m.group("place").lower().replace(" ", "")
        dog = clean_source_dog_name(m.group("dog"))
        owner = re.split(
            r"(?=\d{1,2}(?:st|nd|rd|th)\s*:)|(?=\b(?:Best|Reserve)\s*:)",
            m.group("owner"),
            maxsplit=1,
            flags=re.I,
        )[0]
        owner = re.sub(r"\s+", " ", owner).strip(" .,;:")
        if dog and owner and len(dog) < 80:
            out.append((place, dog, owner))
    return out


def _call_name(name: str) -> str:
    words = re.findall(r"[a-z0-9]+", name.lower())
    return words[-1] if words else ""


def _call_names_compatible(a: str, b: str) -> bool:
    """True when call names are the same dog (OCR), not litter-mates (Nash≠Rush)."""
    ca, cb = _call_name(a), _call_name(b)
    if not ca or not cb:
        return False
    if ca == cb:
        return True
    if ca.rstrip("s") == cb.rstrip("s"):
        return True
    # Roux↔Roxy / Cobbie↔Cobble: small OCR drift on the call token only
    if min(len(ca), len(cb)) >= 3 and SequenceMatcher(None, ca, cb).ratio() >= 0.8:
        return abs(len(ca) - len(cb)) <= 2
    return False


def best_place_remount(
    dog_name: str, place: str, entries: list[tuple[str, str, str]]
) -> tuple[str, str] | None:
    """Pick source (dog, owner) at same place most similar to current dog name."""
    cands = [
        (d, o)
        for pl, d, o in entries
        if pl == place and _call_names_compatible(dog_name, d)
    ]
    if not cands:
        return None
    scored = []
    for d, o in cands:
        ratio = SequenceMatcher(
            None, dog_match_key(dog_name), dog_match_key(d)
        ).ratio()
        scored.append((ratio, d, o))
    scored.sort(reverse=True)
    best = scored[0]
    # Strong overall similarity required (kennel+call OCR cleanup)
    if best[0] >= 0.75:
        return best[1], best[2]
    return None


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--dry-run", action="store_true")
    ap.add_argument("--limit", type=int, default=0)
    ap.add_argument("--log-every", type=int, default=5000)
    ap.add_argument(
        "--commit-every",
        type=int,
        default=2000,
        help="Commit after this many writes (0 = only at end)",
    )
    args = ap.parse_args()

    cn = connect()
    # Avoid one giant transaction locking SQL Server for hours
    try:
        cn.autocommit = False
    except Exception:
        pass
    cur = cn.cursor()
    writes_since_commit = 0

    def maybe_commit(force: bool = False) -> None:
        nonlocal writes_since_commit
        if args.dry_run:
            return
        if force or (
            args.commit_every and writes_since_commit >= args.commit_every
        ):
            cn.commit()
            writes_since_commit = 0

    top = f"TOP ({int(args.limit)}) " if args.limit else ""
    cur.execute(
        f"""
        SELECT {top}p.TrialPlacementsID, p.DogID, d.DogName, o.OwnerName,
               p.Result, tl.Year, tl.TrialName, tl.TrialResultFilePath
        FROM sResults.TrialPlacements p
        JOIN sResults.Dog d ON d.DogID = p.DogID
        LEFT JOIN sResults.Owner o ON o.OwnerID = d.OwnerID
        JOIN sResults.TrialList tl ON tl.TrialListID = p.TrialListID
        ORDER BY p.TrialPlacementsID
        """
    )
    rows = cur.fetchall()
    # Group by source file so each trial is parsed once, not once per dog
    rows = sorted(rows, key=lambda r: (r[7] or "", r[0]))
    print(f"Scanning {len(rows):,} placements...", flush=True)

    path_cache: dict[str, str | None] = {}
    # Per resolved path: list of (dog, owner) and list of (place, dog, owner)
    pairs_cache: dict[str, list[tuple[str, str]]] = {}
    entries_cache: dict[str, list[tuple[str, str, str]]] = {}
    MAX_FILE_BYTES = 2_500_000

    stats = defaultdict(int)
    samples: dict[str, list[str]] = defaultdict(list)

    def sample(kind: str, msg: str) -> None:
        if len(samples[kind]) < 25:
            samples[kind].append(msg)

    def load_source(resolved: str) -> bool:
        if resolved in pairs_cache:
            return True
        try:
            p = Path(resolved)
            if p.stat().st_size > MAX_FILE_BYTES:
                stats["skip_huge_file"] += 1
                pairs_cache[resolved] = []
                entries_cache[resolved] = []
                return True
            text = read_text(p)
        except Exception:
            stats["read_err"] += 1
            return False
        pairs_cache[resolved] = extract_owned_by_pairs(text)
        entries_cache[resolved] = place_entries(text)
        return True

    def owners_for(resolved: str, dog_name: str) -> list[str]:
        return [o for d, o in pairs_cache[resolved] if name_attested(dog_name, d)]

    t0 = __import__("time").time()
    for i, (pid, did, dog_name, db_owner, result, year, tname, path) in enumerate(rows):
        if (i + 1) % args.log_every == 0:
            elapsed = max(__import__("time").time() - t0, 0.1)
            rate = (i + 1) / elapsed
            eta_min = (len(rows) - i - 1) / rate / 60
            print(
                f"  ... {i+1:,}/{len(rows):,} "
                f"({100*(i+1)/len(rows):.1f}%) "
                f"{rate:.0f}/s eta={eta_min:.0f}m | "
                f"keep={stats['keep']} owner_rm={stats['owner_remount']} "
                f"place_rm={stats['place_remount']} detach={stats['detach']} "
                f"| {year} {tname}",
                flush=True,
            )
            maybe_commit(force=True)

        stats["scanned"] += 1
        if not dog_name or not str(dog_name).strip():
            stats["skip_empty_name"] += 1
            continue

        # Already neutral unverified — leave
        if str(dog_name).startswith("UNVERIFIED-"):
            stats["skip_unverified"] += 1
            continue

        if not path:
            stats["no_path"] += 1
            continue
        if path not in path_cache:
            rp = resolve_path(path)
            path_cache[path] = str(rp) if rp else None
        resolved = path_cache[path]
        if not resolved:
            stats["no_path"] += 1
            continue

        if not load_source(resolved):
            continue

        # TrialVault / modern HTML often has no "owned by" lines. If we
        # extracted nothing from the file, do NOT detach — format unknown.
        if not pairs_cache[resolved] and not entries_cache[resolved]:
            stats["keep_no_parse"] += 1
            continue

        src_owners = owners_for(resolved, dog_name)
        home = [o for o in src_owners if not is_foreign_source_owner(db_owner, o)]
        foreign = [o for o in src_owners if is_foreign_source_owner(db_owner, o)]

        if home:
            stats["keep"] += 1
            continue

        if foreign and not home:
            # Unambiguous foreign household(s)?
            clusters: list[list[str]] = []
            for o in foreign:
                placed = False
                for c in clusters:
                    if owners_compatible_for_dog_merge(o, c[0]):
                        c.append(o)
                        placed = True
                        break
                if not placed:
                    clusters.append([o])
            if len(clusters) == 1:
                target = cluster_owner_label(clusters[0])
                msg = (
                    f"{year} {tname!r} {result!r}: {dog_name!r}/{db_owner!r} "
                    f"-> owner {target!r}"
                )
                sample("owner_remount", msg)
                stats["owner_remount"] += 1
                if not args.dry_run:
                    oid = get_or_create_owner(
                        cur, normalize_owner_name(target) or target
                    )
                    # Keep registered name; for call-name "Skeeter of Blackburn"
                    # stay on that name under new owner only if source used it
                    nid = get_or_create_dog(cur, dog_name, oid)
                    if nid == did:
                        cur.execute(
                            "INSERT INTO sResults.Dog (DogName, OwnerID) "
                            "OUTPUT INSERTED.DogID VALUES (?, ?)",
                            dog_name,
                            oid,
                        )
                        nid = cur.fetchone()[0]
                    cur.execute(
                        "UPDATE sResults.TrialPlacements SET DogID=? "
                        "WHERE TrialPlacementsID=?",
                        nid,
                        pid,
                    )
                    writes_since_commit += 1
                    maybe_commit()
                continue
            stats["ambiguous_owner"] += 1
            sample(
                "ambiguous_owner",
                f"{year} {tname!r} {dog_name!r} owners={foreign[:3]}",
            )
            # fall through to place remount / detach

        # Dog name not attested (or ambiguous) — try place-based remount
        place = (result or "").lower().replace(" ", "")
        remount = best_place_remount(dog_name, place, entries_cache[resolved])
        if remount:
            src_dog, src_owner = remount
            # Don't remount onto same dog+compatible owner
            if name_attested(dog_name, src_dog) and not is_foreign_source_owner(
                db_owner, src_owner
            ):
                stats["keep"] += 1
                continue
            msg = (
                f"{year} {tname!r} {result!r}: {dog_name!r} -> "
                f"{src_dog!r}/{src_owner!r}"
            )
            sample("place_remount", msg)
            stats["place_remount"] += 1
            if not args.dry_run:
                oid = get_or_create_owner(
                    cur, normalize_owner_name(src_owner) or src_owner
                )
                nid = get_or_create_dog(cur, src_dog, oid)
                if nid == did:
                    cur.execute(
                        "INSERT INTO sResults.Dog (DogName, OwnerID) "
                        "OUTPUT INSERTED.DogID VALUES (?, ?)",
                        src_dog,
                        oid,
                    )
                    nid = cur.fetchone()[0]
                cur.execute(
                    "UPDATE sResults.TrialPlacements SET DogID=? "
                    "WHERE TrialPlacementsID=?",
                    nid,
                    pid,
                )
                writes_since_commit += 1
                maybe_commit()
            continue

        # Detach to neutral name
        stats["detach"] += 1
        sample(
            "detach",
            f"{year} {tname!r} {result!r}: {dog_name!r}/{db_owner!r}",
        )
        if not args.dry_run:
            oid = get_or_create_owner(cur, "UNVERIFIED SOURCE MATCH")
            # Prefer per-placement dog to avoid lumping unrelated detaches
            cur.execute(
                "INSERT INTO sResults.Dog (DogName, OwnerID) OUTPUT INSERTED.DogID "
                "VALUES (?, ?)",
                f"UNVERIFIED-{pid}",
                oid,
            )
            nid = cur.fetchone()[0]
            cur.execute(
                "UPDATE sResults.TrialPlacements SET DogID=? WHERE TrialPlacementsID=?",
                nid,
                pid,
            )
            writes_since_commit += 1
            maybe_commit()

    # Rename leftover dogs whose names still contain the literal marker
    # (escape [] so SQL Server does not treat them as a character class)
    cur.execute(
        r"""
        SELECT DogID, DogName FROM sResults.Dog
        WHERE DogName LIKE '%\[unverified\]%' ESCAPE '\'
           OR (DogName LIKE '%unverified%' AND DogName NOT LIKE 'UNVERIFIED-%')
        """
    )
    for did, dname in cur.fetchall():
        if str(dname).startswith("UNVERIFIED-"):
            continue
        stats["renamed_unverified"] += 1
        if not args.dry_run:
            cur.execute(
                "UPDATE sResults.Dog SET DogName=? WHERE DogID=?",
                f"UNVERIFIED-{did}",
                did,
            )

    if args.dry_run:
        cn.rollback()
        print("\nDry run — rolled back.", flush=True)
    else:
        maybe_commit(force=True)
        print("\nCommitted.", flush=True)

    print("\n=== SUMMARY ===")
    for k in sorted(stats):
        print(f"  {k}: {stats[k]}")
    for kind, msgs in samples.items():
        print(f"\n--- sample {kind} ---")
        for m in msgs:
            print(f"  {m}")

    cn.close()


if __name__ == "__main__":
    main()
