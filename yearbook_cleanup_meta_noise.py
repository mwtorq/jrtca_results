#!/usr/bin/env python3
"""Remove clearly implausible yearbook meta rows from noisy OCR."""
from __future__ import annotations

import re

import pyodbc
from remount_source_divisions import CONN
from yearbook_meta_ingest import plausible_person, norm_name


def bad_name(name: str) -> bool:
    n = norm_name(name or "")
    if not plausible_person(n):
        return True
    if re.search(r"\b(image|damage|terriers|maryland|virginia|page)\b", n, re.I):
        return True
    if len(re.findall(r"[A-Za-z]+", n)) < 2:
        return True
    return False


def main() -> None:
    cn = pyodbc.connect(CONN, timeout=60, autocommit=True)
    cur = cn.cursor()
    cur.execute("SET LOCK_TIMEOUT 15000")

    cur.execute("SELECT StateRepID, MemberName FROM sResults.StateRepresentative")
    drop_sr = [int(r[0]) for r in cur.fetchall() if bad_name(r[1])]
    if drop_sr:
        # chunk
        for i in range(0, len(drop_sr), 100):
            chunk = drop_sr[i : i + 100]
            ph = ",".join("?" * len(chunk))
            cur.execute(
                f"DELETE FROM sResults.StateRepresentative WHERE StateRepID IN ({ph})",
                chunk,
            )
    print("deleted_state_reps", len(drop_sr))

    cur.execute(
        """
        SELECT BreederID, KennelName, OwnerName, SourceURL
        FROM sResults.Breeder
        WHERE SourceURL LIKE 'yearbook:%'
        """
    )
    drop_b = []
    for bid, kennel, owner, _src in cur.fetchall():
        if bad_name(owner or "") or len((kennel or "").strip()) < 3:
            drop_b.append(int(bid))
            continue
        if re.search(r"\d{5}|Tel\b|Road\b|eee|oaeberty", kennel or "", re.I):
            drop_b.append(int(bid))
    if drop_b:
        for i in range(0, len(drop_b), 100):
            chunk = drop_b[i : i + 100]
            ph = ",".join("?" * len(chunk))
            cur.execute(f"DELETE FROM sResults.Breeder WHERE BreederID IN ({ph})", chunk)
    print("deleted_breeders", len(drop_b))

    # Board/Committee: drop names that fail plausible_person
    for table, col in (("Board", "BoardID"), ("Committee", "CommitteeID")):
        cur.execute(f"SELECT {col}, MemberName FROM sResults.{table}")
        drop = [int(r[0]) for r in cur.fetchall() if bad_name(r[1])]
        for i in range(0, len(drop), 200):
            chunk = drop[i : i + 200]
            if not chunk:
                continue
            ph = ",".join("?" * len(chunk))
            cur.execute(f"DELETE FROM sResults.{table} WHERE {col} IN ({ph})", chunk)
        print(f"deleted_{table.lower()}", len(drop))

    # Remap empty split paths back to full PDF OCR for known failures
    remaps = {
        301: r"c:\Users\mw\OneDrive - timberwilde.net\repos\jrtca_results\Yearbook Scans\2001 Vol II\2001 Paumanok Farmstead Dutchess County.pdf",
        306: r"c:\Users\mw\OneDrive - timberwilde.net\repos\jrtca_results\Yearbook Scans\2001 Vol II\2001 MWJRTC II Wheatland I & II.pdf",
        305: r"c:\Users\mw\OneDrive - timberwilde.net\repos\jrtca_results\Yearbook Scans\2001 Vol II\2001 MWJRTC II Wheatland I & II.pdf",
        277: r"c:\Users\mw\OneDrive - timberwilde.net\repos\jrtca_results\Yearbook Scans\2001 Vol I\2001 Troon Quarry.pdf",
    }
    for tid, path in remaps.items():
        cur.execute(
            "UPDATE sResults.TrialList SET TrialResultFilePath=? WHERE TrialListID=?",
            path,
            tid,
        )
    print("remapped_failed_splits", list(remaps))

    cur.execute("SELECT COUNT(*) FROM sResults.Board")
    print("board_left", cur.fetchone()[0])
    cur.execute("SELECT COUNT(*) FROM sResults.Committee")
    print("committee_left", cur.fetchone()[0])
    cur.execute("SELECT COUNT(*) FROM sResults.StateRepresentative")
    print("staterep_left", cur.fetchone()[0])
    cn.close()


if __name__ == "__main__":
    main()
