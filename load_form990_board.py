#!/usr/bin/env python3
"""Load JRTCA Board officers from IRS Form 990 officer lists (ProPublica).

Used to fill years with no usable Wayback board.php capture.
Does not invent committee chairs or state reps.
"""
from __future__ import annotations

import argparse

import pyodbc

from remount_source_divisions import CONN
from yearbook_meta_ingest import (
    PersonHit,
    apply_bundle,
    find_owner_id,
    MetaBundle,
    plausible_person,
)
from yearbook_meta_schema import ensure

# Fiscal year ending Dec. YYYY → Board.Year = YYYY
# Extracted from https://projects.propublica.org/nonprofits/organizations/61217376
FORM990_BOARD: dict[int, list[tuple[str, str]]] = {
    # Filed Nov 8, 2022 — FY ending Dec 2021 (already have Wayback; keep for cross-check)
    2021: [
        ("Tandee Morris", "Director"),
        ("Don Gaskell", "Director"),
        ("Sandy Brown", "Director"),
        ("Martha Milligan", "Director"),
        ("Wayne May", "Director"),
        ("Colleen Reeder", "Director"),
        ("Ted Ely", "Director"),
        ("Catherine Brown", "Chairperson"),
        ("John Tyno", "Vice Chairperson"),
    ],
    # Filed Oct 22, 2024 — FY ending Dec 2022 (no Wayback board/reponline)
    2022: [
        ("Don Gaskell", "Director"),
        ("Martha Milligan", "Director"),
        ("Wayne May", "Director"),
        ("Colleen Reeder", "Director"),
        ("Ted Ely", "Director"),
        ("Dawn Weiss", "Director"),
        ("Catherine Brown", "Chairperson"),
        ("John Tyno", "Vice Chairperson"),
    ],
    # Filed June 17, 2024 — FY ending Dec 2023
    2023: [
        ("Catherine Brown", "Director"),
        ("Don Gaskell", "Director"),
        ("Chet Atkins", "Director"),
        ("Sandy Gray", "Director"),
        ("Colleen Reeder", "Director"),
        ("John Tyno", "Vice Chairperson"),
        ("Ted Ely", "Chairperson"),
    ],
    # Filed Aug 4, 2025 — FY ending Dec 2024
    2024: [
        ("Don Gaskell", "Director"),
        ("Chet Atkins", "Director"),
        ("Colleen Reeder", "Director"),
        ("Ted Ely", "Chairperson"),
        ("Trish Frankenberg", "Director"),
        ("Tracy Flora", "Director"),
        ("Todd Sena", "Director"),
        ("Bonita Knickmeyer", "Director"),
    ],
}


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--apply", action="store_true")
    ap.add_argument("--years", default="2022", help="Comma years to load (default 2022 gap)")
    args = ap.parse_args()
    years = [int(x.strip()) for x in args.years.split(",") if x.strip()]
    apply = bool(args.apply)

    cn = pyodbc.connect(CONN, timeout=30, autocommit=True)
    cur = cn.cursor()
    cur.execute("SET LOCK_TIMEOUT 15000")
    ensure(cur)

    totals = {"board": 0, "owner_aug": 0}
    for year in years:
        rows = FORM990_BOARD.get(year)
        if not rows:
            print("no Form 990 roster mapped for", year)
            continue
        board = []
        for name, role in rows:
            if not plausible_person(name):
                print("skip non-person", name)
                continue
            # Prefer Reader spelling already used from website when both exist
            board.append(PersonHit(name=name, role=role))
        bundle = MetaBundle(
            year=year,
            source=f"form990:propublica/EIN-06-1217376/FY{year}",
            board=board,
        )
        stats = apply_bundle(cur, bundle, apply=apply)
        totals["board"] += stats.get("board", 0)
        totals["owner_aug"] += stats.get("owner_aug", 0)
        print(
            year,
            "board",
            len(board),
            "stats",
            stats,
            "mode",
            "APPLY" if apply else "DRY",
        )
        for h in board:
            oid = find_owner_id(cur, h.name)
            print(" ", h.name, "|", h.role, "| OwnerID", oid)

    print("totals", totals)
    if apply:
        cur.execute(
            "SELECT Year, COUNT(*) FROM sResults.Board "
            "WHERE Year BETWEEN 2021 AND 2026 GROUP BY Year ORDER BY Year"
        )
        print("board counts", cur.fetchall())
    cn.close()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
