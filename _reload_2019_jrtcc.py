"""Delete and reload 2019 JRTCC National into TrialResults."""
from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from populate_trialresults_fixed import get_connection
import populate_trialresults_fixed as pop

YEAR = 2019


def delete_trial(conn, trial_id: int) -> None:
    cur = conn.cursor()
    cur.execute(
        """
        DELETE t FROM [sResults].[TrialPlacements_Times] t
        JOIN [sResults].[TrialPlacements] p ON t.TrialPlacementsID = p.TrialPlacementsID
        WHERE p.TrialListID = ?
        """,
        trial_id,
    )
    print(f"  Deleted times: {cur.rowcount}")
    cur.execute("DELETE FROM [sResults].[TrialPlacements] WHERE TrialListID = ?", trial_id)
    print(f"  Deleted placements: {cur.rowcount}")
    cur.execute("DELETE FROM [sResults].[TrialClass] WHERE TrialListID = ?", trial_id)
    print(f"  Deleted trial classes: {cur.rowcount}")
    cur.execute("DELETE FROM [sResults].[TrialList] WHERE TrialListID = ?", trial_id)
    print(f"  Deleted trial list: {cur.rowcount}")
    conn.commit()


def main() -> int:
    conn = get_connection()
    cur = conn.cursor()
    cur.execute(
        """
        SELECT TrialListID, TrialName FROM [sResults].[TrialList]
        WHERE Year = ? AND TrialName LIKE '%JRTCC%'
        """,
        YEAR,
    )
    rows = cur.fetchall()
    print(f"Existing 2019 JRTCC trials: {rows}")
    for tid, name in rows:
        print(f"Deleting trial {tid}: {name}")
        delete_trial(conn, tid)
    conn.close()

    sys.argv = [
        "populate_trialresults_fixed.py",
        "--folder", "JRTCC",
        "--year", "2019",
        "--reuse-entities",
        "--normalize-at-end",
        "--log-file", "populate_jrtcc_2019_reload.log",
    ]
    pop.main()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
