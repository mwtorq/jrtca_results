"""
reload_mo_earthdogs.py
======================
Clear and reload all MO Earthdogs trial data (1999-2019) from source files.

This script deletes every TrialList/TrialClass/TrialPlacements/TrialPlacements_Times
row whose TrialResultFilePath references the 'MO Earthdogs' folder (or whose
TrialName matches 'Missouri Earthdogs'), then re-runs the full discovery and
load pipeline for that folder using the fixed parsing logic in
populate_trialresults_fixed.py.

Usage
-----
    python reload_mo_earthdogs.py [--dry-run] [--log-file FILE]

    --dry-run    Show which trials would be deleted without touching the DB.
    --log-file   Path for the run log (default: reload_mo_earthdogs.log).

What it does
------------
1. Identify all existing TrialList rows belonging to MO Earthdogs by matching
   TrialResultFilePath (contains 'MO Earthdogs') OR TrialName (contains
   'Missouri Earthdogs' or 'MOE').
2. Delete associated TrialPlacements_Times, TrialPlacements, TrialClass, and
   TrialList rows for those trials (cascading delete in dependency order).
3. Rediscover and load all MO Earthdogs files (1999-2019) from the
   'MO Earthdogs' subfolder using discover_special_folder_files() and
   process_trial_file().
4. Run deferred post-load normalization on all newly inserted trials.

Dogs/Owners/Divisions/Classes from any previous MO Earthdogs load are
retained in place and REUSED (--reuse-entities mode) so they can be matched
back against catalog entries and other trial data.
"""

from __future__ import annotations

import argparse
import os
import sys
from datetime import datetime

# ---------------------------------------------------------------------------
# Tee stdout → console + log file
# ---------------------------------------------------------------------------

def _make_tee(log_path: str):
    log_handle = open(log_path, 'a', encoding='utf-8', buffering=1)
    log_handle.write(
        f"\n{'=' * 80}\n"
        f"RELOAD_MO_EARTHDOGS RUN START {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n"
        f"{'=' * 80}\n"
    )
    original_stdout = sys.stdout

    class _Tee:
        def write(self, data):
            if not data:
                return
            log_handle.write(data)
            try:
                original_stdout.write(data)
            except UnicodeEncodeError:
                enc = getattr(original_stdout, 'encoding', None) or 'utf-8'
                original_stdout.write(data.encode(enc, errors='replace').decode(enc))

        def flush(self):
            original_stdout.flush()
            log_handle.flush()

        def __getattr__(self, name):
            return getattr(original_stdout, name)

    sys.stdout = _Tee()
    return log_handle, original_stdout


# ---------------------------------------------------------------------------
# Find existing MO Earthdogs trials in the database
# ---------------------------------------------------------------------------

def find_mo_earthdogs_trial_ids(conn) -> list[int]:
    """Return TrialListIDs for all MO Earthdogs trials currently in the DB."""
    cursor = conn.cursor()
    cursor.execute(
        """
        SELECT TrialListID, Year, TrialName, TrialResultFilePath
        FROM   [sResults].[TrialList]
        WHERE  (
                   TrialResultFilePath LIKE '%MO Earthdogs%'
                OR TrialName           LIKE '%Missouri Earthdogs%'
                OR TrialName           LIKE '%MOE%Memorial%'
               )
        ORDER BY Year, TrialListID
        """
    )
    rows = cursor.fetchall()
    if not rows:
        return []
    print(f"Found {len(rows)} existing MO Earthdogs trial(s) in the database:")
    for row in rows:
        tid, year, name, path = row
        print(f"  TrialListID={tid}  Year={year}  {name!r}")
    return [row[0] for row in rows]


# ---------------------------------------------------------------------------
# Delete existing MO Earthdogs data
# ---------------------------------------------------------------------------

def delete_mo_earthdogs_trials(conn, trial_ids: list[int], dry_run: bool = False) -> None:
    """Delete all rows associated with the given TrialListIDs, in FK order."""
    if not trial_ids:
        print("No existing MO Earthdogs trials to delete.")
        return

    placeholders = ','.join('?' * len(trial_ids))
    cursor = conn.cursor()

    steps = [
        ("TrialPlacements_Times",
         f"""DELETE t FROM [sResults].[TrialPlacements_Times] t
             JOIN   [sResults].[TrialPlacements] p ON t.TrialPlacementsID = p.TrialPlacementsID
             WHERE  p.TrialListID IN ({placeholders})"""),
        ("TrialPlacements",
         f"DELETE FROM [sResults].[TrialPlacements] WHERE TrialListID IN ({placeholders})"),
        ("TrialClass",
         f"DELETE FROM [sResults].[TrialClass]       WHERE TrialListID IN ({placeholders})"),
        ("TrialList",
         f"DELETE FROM [sResults].[TrialList]        WHERE TrialListID IN ({placeholders})"),
    ]

    print(
        f"\n{'[DRY RUN] Would delete' if dry_run else 'Deleting'} "
        f"data for {len(trial_ids)} trial(s): {trial_ids}"
    )

    for label, sql in steps:
        if dry_run:
            # Run as a SELECT COUNT to show impact without deleting
            count_sql = f"SELECT COUNT(*) FROM ({sql.replace('DELETE', 'SELECT 1 AS x', 1)}) x"
            # Simpler: just show the SQL
            print(f"  [DRY RUN] Would execute: {sql.strip()[:120]}...")
            continue
        try:
            cursor.execute(sql, trial_ids)
            print(f"  Deleted {cursor.rowcount:,} row(s) from {label}")
        except Exception as e:
            print(f"  ERROR deleting from {label}: {e}")
            conn.rollback()
            raise

    if not dry_run:
        conn.commit()
        print("  Commit successful.")


# ---------------------------------------------------------------------------
# Load MO Earthdogs files
# ---------------------------------------------------------------------------

def load_mo_earthdogs(conn, dry_run: bool = False) -> list[int]:
    """Discover and load all MO Earthdogs source files (1999-2019).

    Returns the list of newly inserted TrialListIDs.
    """
    from populate_trialresults_fixed import (
        discover_special_folder_files,
        process_trial_file,
        run_deferred_trial_normalizations,
        get_next_ids_from_db,
    )
    from populate_trialresults_database import preload_dogs_and_owners_from_db

    # Discover files – scoring now correctly prefers TXT over PDF
    base_dir = os.path.dirname(os.path.abspath(__file__))
    files = discover_special_folder_files(base_dir, 'MO Earthdogs')

    if not files:
        print("ERROR: No MO Earthdogs files discovered! Check the 'MO Earthdogs' folder.")
        return []

    print(f"\nDiscovered {len(files)} MO Earthdogs file(s) to load:")
    for fp, yr in files:
        print(f"  {yr}: {os.path.basename(fp)}")

    if dry_run:
        print("\n[DRY RUN] Skipping actual database load.")
        return []

    # Reuse existing Dog/Owner/Division/Class entities
    print("\nPreloading dogs, owners, divisions, and classes from database...")
    entity_ctx = preload_dogs_and_owners_from_db(conn)
    cursor = conn.cursor()
    cursor.execute("SELECT COUNT(*) FROM [sResults].[Dog]")
    print(f"  Loaded {cursor.fetchone()[0]:,} dogs for reuse")

    # Get current ID counters
    next_trial_id, next_tc_id, next_pl_id = get_next_ids_from_db(conn)
    print(f"Starting IDs (continuing): Trial={next_trial_id}, Class={next_tc_id}, Placement={next_pl_id}")

    loaded_trial_ids: list[int] = []

    for file_path, year in files:
        try:
            next_trial_id, next_tc_id, next_pl_id = process_trial_file(
                conn,
                file_path,
                year,
                next_trial_id,
                next_tc_id,
                next_pl_id,
                entity_ctx,
                reuse_entities=True,
                defer_normalization=True,        # normalize all at end
                loaded_trial_ids=loaded_trial_ids,
            )
        except Exception as e:
            print(f"\n  ERROR processing {os.path.basename(file_path)}: {e}")
            import traceback
            traceback.print_exc()

    # Run deferred normalization for all loaded trials in one batch
    if loaded_trial_ids:
        print(
            f"\nRunning deferred post-load normalization for "
            f"{len(loaded_trial_ids)} trial(s) in one batch..."
        )
        run_deferred_trial_normalizations(
            conn,
            loaded_trial_ids,
            reuse_entities=True,
        )

    return loaded_trial_ids


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------

def main() -> None:
    parser = argparse.ArgumentParser(
        description="Clear and reload all MO Earthdogs (1999-2019) trial data",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=__doc__,
    )
    parser.add_argument(
        '--dry-run',
        action='store_true',
        help='Show what would be done without touching the database',
    )
    parser.add_argument(
        '--log-file',
        default='reload_mo_earthdogs.log',
        help='Append run output to this log file (default: reload_mo_earthdogs.log)',
    )
    args = parser.parse_args()

    log_handle, original_stdout = _make_tee(args.log_file)

    print("=" * 80)
    print("MO EARTHDOGS CLEAR + RELOAD  (1999-2019)")
    print("=" * 80)
    if args.dry_run:
        print("*** DRY RUN — no database changes will be made ***")

    try:
        from populate_trialresults_fixed import get_connection
    except ImportError:
        print("ERROR: Cannot import populate_trialresults_fixed.py. "
              "Run this script from the repo root.")
        sys.exit(1)

    print("\nConnecting to database...")
    conn = get_connection()
    if not conn:
        print("ERROR: Could not connect to database.")
        sys.exit(1)

    # ── Step 1: Find existing trials ────────────────────────────────────────
    print("\n" + "─" * 60)
    print("STEP 1: Identify existing MO Earthdogs trials")
    print("─" * 60)
    trial_ids = find_mo_earthdogs_trial_ids(conn)

    # ── Step 2: Delete them ─────────────────────────────────────────────────
    print("\n" + "─" * 60)
    print("STEP 2: Delete existing MO Earthdogs trial data")
    print("─" * 60)
    delete_mo_earthdogs_trials(conn, trial_ids, dry_run=args.dry_run)

    # ── Step 3: Reload from source files ────────────────────────────────────
    print("\n" + "─" * 60)
    print("STEP 3: Load MO Earthdogs files (1999-2019)")
    print("─" * 60)
    loaded = load_mo_earthdogs(conn, dry_run=args.dry_run)

    # ── Done ────────────────────────────────────────────────────────────────
    print("\n" + "=" * 80)
    if args.dry_run:
        print("DRY RUN COMPLETE — no changes were made.")
    else:
        print(f"DONE — loaded {len(loaded)} MO Earthdogs trial(s): {loaded}")
    print(f"RELOAD_MO_EARTHDOGS RUN END {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 80)

    conn.close()
    log_handle.write(
        f"\nRELOAD_MO_EARTHDOGS RUN END {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n"
    )
    log_handle.close()
    sys.stdout = original_stdout


if __name__ == '__main__':
    main()
