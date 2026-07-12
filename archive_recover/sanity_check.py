"""Cross-check auto/review matches against season words embedded in the
trial's own source filename (e.g. 'Spring', 'Winter') to catch cases where
the matched archive.org date falls in a conflicting season."""
from __future__ import annotations

import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from apply_matches import AUTO_APPLY_THRESHOLD, REVIEW_THRESHOLD
from match_year import match_year
from populate_trialresults_fixed import get_connection

SEASON_MONTHS = {
    "winter": {12, 1, 2},
    "spring": {3, 4, 5},
    "summer": {6, 7, 8},
    "fall": {9, 10, 11},
    "autumn": {9, 10, 11},
    "yule": {12},
    "yuletide": {12},
    "christmas": {12},
    "january": {1},
    "february": {2},
    "march": {3},
    "april": {4},
    "june": {6},
    "july": {7},
    "august": {8},
    "september": {9},
    "october": {10},
    "november": {11},
    "december": {12},
}


def check_year(year: int) -> list[dict]:
    result = match_year(year)
    conn = get_connection()
    cur = conn.cursor()
    flags = []
    for m in result["matches"]:
        if m["score"] < REVIEW_THRESHOLD or m["score"] >= 0.95:
            continue
        cur.execute(
            "SELECT TrialResultFilePath FROM sResults.TrialList WHERE TrialListID = ?",
            m["trial_id"],
        )
        row = cur.fetchone()
        path = (row[0] or "") if row else ""
        fname = os.path.basename(path).lower()
        month = int(m["date"][5:7])
        for season, months in SEASON_MONTHS.items():
            if season in fname and month not in months:
                flags.append(
                    {
                        "trial_id": m["trial_id"],
                        "trial_name": m["trial_name"],
                        "matched_name": m["matched_name"],
                        "date": m["date"],
                        "score": m["score"],
                        "filename": fname,
                        "season_word": season,
                    }
                )
                break
    conn.close()
    return flags


if __name__ == "__main__":
    years = [int(a) for a in sys.argv[1:]]
    total = 0
    for year in years:
        flags = check_year(year)
        total += len(flags)
        for f in flags:
            print(
                f"  [{year}] {f['trial_id']:5d} {f['trial_name']!r:40s} -> {f['matched_name']!r} @ {f['date']} "
                f"(score {f['score']:.2f}) filename={f['filename']!r} conflicts with '{f['season_word']}'"
            )
    print(f"\nTotal flagged: {total}")
