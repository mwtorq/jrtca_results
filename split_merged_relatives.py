#!/usr/bin/env python3
"""
Separate dogs that a name-similarity merge collapsed into one record.

merge_duplicate_dogs decides purely on how alike two names look, so a dog can
absorb a relative whose name is a letter or two away. The giveaway is a
relationship row pointing at the dog itself: nothing is its own sire or niece,
so any self-reference means two related dogs now share one record.

The entries catalogs give each dog a sire and a dam. When the absorbed dog's
parents differ from the host's, the two are separate animals and the absorbed
one gets its record back, with its own pedigree. When the parents agree the two
names are just scans of one dog and the pair is left alone.

Placements are not moved here. verify_trial_normalization.py --fix-dog-merges
already does that from each trial's own results file, and the relationship rows
this script restores stop the pair being merged again.

    py split_merged_relatives.py            # report only
    py split_merged_relatives.py --apply
"""

import argparse
import json
import os
import re
import sys

from parse_catalog import (
    merge_dogs_across_years,
    names_are_similar,
    normalize_name,
    parse_catalog,
)
from normalize_trialresults_data import print_ts
from populate_trialresults_fixed import get_connection

CACHE = "catalog_pedigree_cache.json"


def build_catalog_pedigree(refresh: bool = False) -> dict[str, dict]:
    """Name, sire and dam for every dog in the entries catalogs.

    Cached because merging the catalogs across years takes a few minutes, and
    only the parents are needed. find_relationships derives the niece/cousin
    wording from these and is far slower, so it is not called.
    """
    if os.path.exists(CACHE) and not refresh:
        return json.load(open(CACHE, encoding="utf-8"))

    sources = sorted(
        f for f in os.listdir(".") if re.fullmatch(r"extracted_text_\d{4}\.txt", f)
    )
    if not sources:
        raise SystemExit("no extracted_text_<year>.txt catalogs found")

    by_year = {}
    for path in sources:
        year = re.search(r"(\d{4})", path).group(1)
        text = open(path, encoding="utf-8", errors="replace").read()
        _classes, dogs = parse_catalog(text, year)
        by_year[year] = dogs
        print_ts(f"  parsed {year}: {len(dogs):,} dogs")

    print_ts("  merging catalog dogs across years (a few minutes)...")
    merged = merge_dogs_across_years(by_year)
    pedigree = {
        normalize_name(dog.name): {
            "name": dog.name,
            "sire": getattr(dog, "sire", None),
            "dam": getattr(dog, "dam", None),
            "sex": getattr(dog, "sex", None),
        }
        for dog in merged.values()
    }
    json.dump(pedigree, open(CACHE, "w", encoding="utf-8"))
    print_ts(f"  cached {len(pedigree):,} catalog dogs to {CACHE}")
    return pedigree


def parents_differ(host: dict, other: dict) -> bool:
    """True when the catalog proves the two names belong to different dogs.

    Parent names carry the same scan damage as dog names, so 'Reynard Millen'
    and 'Reynard Miller' count as one sire. One parent disagreeing is therefore
    weak evidence: 'Muscle Russell Diamond' and 'Dimond' share a sire and their
    dam is written "Sully's Legacy" once and "Legacy" the other time, which is
    one dog. Both parents have to disagree, unless one dog is the other's
    parent, which settles it on its own.
    """
    for child, parent_of in ((host, other), (other, host)):
        for field in ("sire", "dam"):
            parent = child.get(field)
            if parent and names_are_similar(parent, parent_of.get("name") or ""):
                return True

    comparable = disagreeing = 0
    for field in ("sire", "dam"):
        a, b = host.get(field), other.get(field)
        if a and b:
            comparable += 1
            if not names_are_similar(a, b):
                disagreeing += 1
    return comparable == 2 and disagreeing == 2


def find_self_references(cursor) -> list[tuple]:
    cursor.execute(
        """
        SELECT r.DogID, d.DogName, r.RelatedDogName, COUNT(*)
        FROM [sResults].[Relationship] r
        JOIN [sResults].[Dog] d ON d.DogID = r.DogID
        WHERE r.DogID = r.RelatedDogID
        GROUP BY r.DogID, d.DogName, r.RelatedDogName
        ORDER BY COUNT(*) DESC
        """
    )
    return cursor.fetchall()


def resolve_or_create_dog(cursor, name: str, pedigree: dict) -> tuple[int, bool]:
    """Find the record for a dog by name, or give it one back."""
    cursor.execute(
        "SELECT TOP 1 DogID FROM [sResults].[Dog] WHERE DogName = ? ORDER BY DogID",
        name,
    )
    row = cursor.fetchone()
    if row:
        return row[0], False

    cursor.execute(
        "INSERT INTO [sResults].[Dog] (DogName, Sire, Dam, Sex) "
        "OUTPUT INSERTED.DogID VALUES (?, ?, ?, ?)",
        name,
        pedigree.get("sire"),
        pedigree.get("dam"),
        pedigree.get("sex"),
    )
    return cursor.fetchone()[0], True


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--apply", action="store_true", help="Write the changes")
    parser.add_argument("--refresh-catalog", action="store_true", help="Re-parse catalogs")
    args = parser.parse_args()

    print_ts("Loading catalog pedigrees...")
    catalog = build_catalog_pedigree(args.refresh_catalog)

    conn = get_connection()
    cursor = conn.cursor()
    self_refs = find_self_references(cursor)
    print_ts(f"Self-referencing relationships: {len(self_refs):,} name pairs")

    confirmed, unproven, same_dog = [], 0, 0
    for host_id, host_name, absorbed_name, rows in self_refs:
        host = catalog.get(normalize_name(host_name))
        other = catalog.get(normalize_name(absorbed_name))
        if not host or not other or not (other.get("sire") or other.get("dam")):
            unproven += 1
            continue
        if parents_differ(host, other):
            confirmed.append((host_id, host_name, absorbed_name, other, rows))
        else:
            same_dog += 1

    print_ts(f"  {len(confirmed):,} confirmed separate dogs (parents differ)")
    print_ts(f"  {same_dog:,} scan variants of one dog, left merged")
    print_ts(f"  {unproven:,} without catalog pedigree to judge on")

    if not confirmed:
        conn.close()
        return

    print()
    created = repointed = 0
    for host_id, host_name, absorbed_name, pedigree, rows in confirmed:
        if not args.apply:
            print(f"  would split {absorbed_name!r} out of {host_name!r} ({rows} rows)")
            continue

        dog_id, is_new = resolve_or_create_dog(cursor, absorbed_name, pedigree)
        if dog_id == host_id:
            continue
        created += int(is_new)
        cursor.execute(
            """
            UPDATE [sResults].[Relationship]
            SET RelatedDogID = ?
            WHERE DogID = ? AND RelatedDogID = ? AND RelatedDogName = ?
            """,
            dog_id,
            host_id,
            host_id,
            absorbed_name,
        )
        repointed += cursor.rowcount
        print(f"  split {absorbed_name!r} out of {host_name!r} "
              f"({'new record' if is_new else 'existing record'} {dog_id}, {cursor.rowcount} rows)")

    if args.apply:
        conn.commit()
        print()
        print_ts(f"Dog records restored: {created:,}")
        print_ts(f"Relationship rows repointed: {repointed:,}")
        cursor.execute(
            "SELECT COUNT(*) FROM [sResults].[Relationship] WHERE DogID = RelatedDogID"
        )
        print_ts(f"Self-references remaining: {cursor.fetchone()[0]:,}")
    else:
        print()
        print_ts("Report only. Re-run with --apply to write these changes.")

    conn.close()


if __name__ == "__main__":
    sys.exit(main())
