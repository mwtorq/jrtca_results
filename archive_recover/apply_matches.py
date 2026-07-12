"""Apply high-confidence archive.org-recovered dates to sResults.TrialList,
and report medium-confidence matches for manual review.

Usage:
  py apply_matches.py <year> [--apply]

Without --apply, runs in dry-run/report mode only.
"""
from __future__ import annotations

import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from match_year import match_year
from populate_trialresults_fixed import get_connection

AUTO_APPLY_THRESHOLD = 0.5
REVIEW_THRESHOLD = 0.5

# Trial IDs where the algorithmic match scored above threshold but manual
# verification against the trial's own source filename (season words,
# sponsoring club abbreviations) showed it was matched to the wrong
# real-world event. Never auto-apply these.
EXCLUDE_IDS = {
    1304, 1305,  # Del Sol Winter I/II (2001) -> matched to unrelated April "Del Sol 9 & 10"
    1339, 1340,  # Fox Cry I/II (2002, actually the January Jamboree) -> matched to March Spring Fling
    1423, 1424,  # Mason-Dixon Ice Breaker I/II (2003, a spring event) -> matched to the summer Mason Dixon trial
    1437, 1438,  # Rocky Mountain Spring Trial 1/2 (2003) -> matched to the August "Challenge" event
    1440,        # SCJRTC Spring Fling (2003) -> matched to unrelated Fox Cry Spring Fling
    1445,        # St. Croix Spring (2003) -> matched to the summer St. Croix Terrier Trial
    1662, 1663,  # Spring Classic I/II (2015) -> matched to unrelated Spring Fever
    1659,        # Rainier Hunt Classic II (2015) -> matched via ambiguous whole-range
                 # fallback to a stale early-announcement date (Jul 25-26) that
                 # collides with "Rainier Hunt Classic" (day I)'s already-confirmed
                 # 2015-07-26; the real event is day I + 1 = 2015-07-27 (set manually).
}


def run(year: int, apply: bool) -> None:
    result = match_year(year)
    candidates = [m for m in result["matches"] if m["trial_id"] not in EXCLUDE_IDS]
    auto = [m for m in candidates if m["score"] >= AUTO_APPLY_THRESHOLD]
    review = [m for m in candidates if REVIEW_THRESHOLD <= m["score"] < AUTO_APPLY_THRESHOLD]

    print(f"=== Year {year}: {len(auto)} auto, {len(review)} review, {len(result['unmatched'])} unmatched ===")

    if apply and auto:
        conn = get_connection()
        cur = conn.cursor()
        for m in auto:
            cur.execute(
                "UPDATE sResults.TrialList SET StartDate = ?, EndDate = ? WHERE TrialListID = ?",
                m["date"], m["date"], m["trial_id"],
            )
            print(f"  UPDATED {m['trial_id']:5d} {m['trial_name']!r} -> {m['date']} (score {m['score']:.2f}, matched {m['matched_name']!r})")
        conn.commit()
        conn.close()
    else:
        for m in auto:
            print(f"  [AUTO ] {m['trial_id']:5d} {m['trial_name']!r:45s} -> {m['matched_name']!r} @ {m['date']} ({m['score']:.2f})")

    if review:
        print("  --- REVIEW (not applied) ---")
        for m in review:
            print(f"  [REVIEW] {m['trial_id']:5d} {m['trial_name']!r:45s} -> {m['matched_name']!r} @ {m['date']} ({m['score']:.2f})")


if __name__ == "__main__":
    year = int(sys.argv[1])
    apply = "--apply" in sys.argv
    run(year, apply)
