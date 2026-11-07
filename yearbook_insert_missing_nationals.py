#!/usr/bin/env python3
"""Insert missing JRTCA National TrialList shells for years evidenced in Yearbook Scans.

Paths point at PDF when available; otherwise first OCR/txt page. No placements here.
"""
from __future__ import annotations

import os
from pathlib import Path

import pyodbc
from remount_source_divisions import CONN

ROOT = Path(r"c:\Users\mw\OneDrive - timberwilde.net\repos\jrtca_results")
SCANS = ROOT / "Yearbook Scans"

# year -> preferred source relative path (evidence file)
SOURCES = {
    1986: "Yearbook Scans/1986/JRTCA National.pdf",
    1987: "Yearbook Scans/1987/JRTCA National.pdf",
    1988: "Yearbook Scans/1988/1988 JRTCA National pg 1.txt",
    1989: "Yearbook Scans/1989/1989 JRTCA National pg 1.txt",
    1990: "Yearbook Scans/1990 Vol II/1990 JRTCA National f.txt",
    1991: "Yearbook Scans/1991 Vol II/1991 JRTCA National f.txt",
}


def main() -> None:
    cn = pyodbc.connect(CONN, timeout=30, autocommit=True)
    cur = cn.cursor()
    cur.execute("SET LOCK_TIMEOUT 15000")
    cur.execute("SELECT ISNULL(MAX(TrialListID),0) FROM sResults.TrialList")
    next_tid = int(cur.fetchone()[0]) + 1
    created = []
    for year, rel in SOURCES.items():
        path = ROOT / rel.replace("/", os.sep)
        if not path.is_file():
            print("MISSING source", rel)
            continue
        cur.execute(
            """
            SELECT TrialListID, TrialName FROM sResults.TrialList
            WHERE Year=? AND TrialName LIKE '%National%' AND TrialName LIKE '%JRTCA%'
            """,
            year,
        )
        rows = cur.fetchall()
        if not rows:
            cur.execute(
                """
                SELECT TrialListID, TrialName FROM sResults.TrialList
                WHERE Year=? AND TrialName LIKE '%National%'
                """,
                year,
            )
            rows = cur.fetchall()
        if rows:
            print(f"{year} exists tid={rows[0][0]} {rows[0][1]!r}")
            # remap path if empty/weak
            tid = int(rows[0][0])
            cur.execute(
                "SELECT TrialResultFilePath FROM sResults.TrialList WHERE TrialListID=?",
                tid,
            )
            old = cur.fetchone()[0] or ""
            if "yearbook scans" not in old.lower():
                cur.execute(
                    "UPDATE sResults.TrialList SET TrialResultFilePath=? WHERE TrialListID=?",
                    str(path),
                    tid,
                )
                print(f"  remapped path -> {rel}")
            continue
        name = f"{year} JRTCA National Trial"
        # placeholder date = Jan 1 of year (unknown exact day until OCR)
        start = f"{year}-01-01"
        cur.execute(
            """
            INSERT INTO sResults.TrialList
            (TrialListID, Year, TrialName, StartDate, EndDate, TrialResultFilePath, CreateUser)
            VALUES (?,?,?,?,?,?,?)
            """,
            next_tid,
            year,
            name,
            start,
            start,
            str(path),
            "yearbook_scans_ingest",
        )
        created.append((next_tid, year, name, rel))
        print(f"CREATED tid={next_tid} {name} -> {rel}")
        next_tid += 1
    print("done created", len(created))
    cn.close()


if __name__ == "__main__":
    main()
