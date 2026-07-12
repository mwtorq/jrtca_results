"""Backfill StartDate/EndDate for trials still showing a Jan-1 placeholder date.

Re-scans each trial's source file header for a real date using the same
header-scanning logic as the main loader (scan_trial_header_block). Only
UPDATEs a trial when a real, non-placeholder date is found in its source
file; trials with no discoverable date are left untouched and reported.

Safe to re-run: only ever affects rows currently at their Jan-1 placeholder.
"""
from __future__ import annotations

import os
import re
import sys

from populate_trialresults_fixed import (
    get_connection,
    scan_trial_header_block,
    expand_glued_placement_lines,
    strip_html_tags,
    _is_html_file,
    normalize_date,
)


def extract_header_dates(file_path: str, year_hint: int) -> tuple[str, str]:
    """Return (start_date_str, end_date_str) as free-text like 'October 16, 1998'."""
    try:
        if file_path.lower().endswith(".pdf"):
            from scrape_trial_results_fixed import extract_text_from_pdf
            raw_content = extract_text_from_pdf(file_path)
            if not raw_content:
                return "", ""
        else:
            with open(file_path, "r", encoding="utf-8", errors="ignore") as f:
                raw_content = f.read()
    except OSError:
        return "", ""

    content = raw_content
    if _is_html_file(file_path):
        content = strip_html_tags(raw_content)
    lines = expand_glued_placement_lines(content.split("\n"))

    last_nav_idx = 0
    for i, line in enumerate(lines):
        line_clean = line.strip()
        if re.search(
            r"\d{4}\s+(Trial Results|Conformation Division|Performance Division|"
            r"Bronze Medallions|Working Achievement Awards)",
            line_clean,
        ):
            last_nav_idx = i

    header = scan_trial_header_block(
        lines, start_idx=last_nav_idx, max_lines=500, hint_year=year_hint, quiet=True,
    )
    if not header["start_date"]:
        header = scan_trial_header_block(
            lines, start_idx=0, max_lines=500, hint_year=year_hint, quiet=True,
        )
    return header["start_date"], header["end_date"]


def main() -> None:
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    conn = get_connection()
    cur = conn.cursor()
    cur.execute(
        """
        SELECT TrialListID, Year, TrialName, TrialResultFilePath
        FROM sResults.TrialList
        WHERE MONTH(StartDate) = 1 AND DAY(StartDate) = 1
        ORDER BY Year, TrialListID
        """
    )
    rows = cur.fetchall()
    print(f"Checking {len(rows)} trials with Jan-1 placeholder StartDate...\n")

    updated = 0
    unresolved: list[tuple] = []

    for trial_id, year, trial_name, file_path in rows:
        if not file_path or not os.path.exists(file_path):
            unresolved.append((trial_id, year, trial_name, "source file missing/unset"))
            continue

        start_str, end_str = extract_header_dates(file_path, year)
        if not start_str:
            unresolved.append((trial_id, year, trial_name, "no date found in source"))
            continue

        new_start = normalize_date(start_str, year)
        new_end = normalize_date(end_str, year) if end_str else new_start

        if new_start == f"{year}-01-01":
            unresolved.append(
                (trial_id, year, trial_name, f"parsed back to placeholder ({start_str!r})")
            )
            continue

        cur.execute(
            "UPDATE sResults.TrialList SET StartDate = ?, EndDate = ? WHERE TrialListID = ?",
            new_start, new_end, trial_id,
        )
        updated += 1
        print(f"  UPDATED {trial_id} [{year}] {trial_name}: -> {new_start} to {new_end}")

    conn.commit()

    print(f"\nUpdated: {updated}")
    print(f"Unresolved: {len(unresolved)}")
    for trial_id, year, trial_name, reason in unresolved:
        print(f"  {trial_id} [{year}] {trial_name}: {reason}")

    conn.close()


if __name__ == "__main__":
    main()
