#!/usr/bin/env python3
"""
Create the indexes normalization and verification rely on.

Duplicate merges rewrite entity IDs with statements like
"UPDATE TrialPlacements SET DogID = ? WHERE DogID = ?", and the verifier reads
a trial's placements by TrialListID. Without an index on those columns each
statement scans the whole half-million-row table, which is what makes a full
normalization pass take hours instead of minutes.

Safe to re-run: each index is created only when it is missing.
"""

import sys

from populate_trialresults_fixed import get_connection

INDEXES = (
    ("IX_TrialPlacements_DogID", "TrialPlacements", "DogID"),
    ("IX_TrialPlacements_TrialListID", "TrialPlacements", "TrialListID"),
    ("IX_TrialPlacements_TrialClassID", "TrialPlacements", "TrialClassID"),
    ("IX_TrialClass_TrialListID", "TrialClass", "TrialListID"),
    ("IX_TrialClass_ClassID", "TrialClass", "ClassID"),
    ("IX_CatalogEntry_DogID", "CatalogEntry", "DogID"),
    ("IX_CatalogEntry_ClassID", "CatalogEntry", "ClassID"),
    ("IX_Relationship_DogID", "Relationship", "DogID"),
    ("IX_Relationship_RelatedDogID", "Relationship", "RelatedDogID"),
    ("IX_Dog_OwnerID", "Dog", "OwnerID"),
    ("IX_Dog_DogName", "Dog", "DogName"),
    ("IX_Class_DivisionID", "Class", "DivisionID"),
)


def main() -> None:
    conn = get_connection()
    cursor = conn.cursor()
    created = 0

    for index_name, table, columns in INDEXES:
        cursor.execute(
            """
            SELECT COUNT(*)
            FROM sys.indexes i
            JOIN sys.tables t ON t.object_id = i.object_id
            JOIN sys.schemas s ON s.schema_id = t.schema_id
            WHERE s.name = 'sResults' AND t.name = ? AND i.name = ?
            """,
            table,
            index_name,
        )
        if cursor.fetchone()[0]:
            print(f"  exists: {index_name}")
            continue

        print(f"  creating {index_name} on {table}({columns})...", flush=True)
        cursor.execute(
            f"CREATE NONCLUSTERED INDEX [{index_name}] "
            f"ON [sResults].[{table}] ({columns})"
        )
        conn.commit()
        created += 1

    print(f"\n{created} index(es) created.")
    conn.close()


if __name__ == "__main__":
    sys.exit(main())
