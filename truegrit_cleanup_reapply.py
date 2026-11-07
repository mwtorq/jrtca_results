#!/usr/bin/env python3
"""Delete True Grit-sourced TrialCertificates/NHC for vols 47-50, then re-apply ingest."""
from __future__ import annotations

import pyodbc
from remount_source_divisions import CONN
import truegrit_schema
from yearbook_meta_schema import ensure as ensure_yearbook_meta
from truegrit_ingest import main as ingest_main


def main() -> None:
    cn = pyodbc.connect(CONN, timeout=60)
    cur = cn.cursor()
    ensure_yearbook_meta(cur)
    _truegrit_schema.ensure(cur)
    for sql in (
        """
        DELETE FROM sResults.TrialCertificates
        WHERE Volume BETWEEN 47 AND 50
           OR SourcePath LIKE '%True Grit%'
           OR SourcePath LIKE 'True Grit%'
        """,
        """
        DELETE FROM sResults.NHC
        WHERE Volume BETWEEN 47 AND 50
           OR SourcePath LIKE '%True Grit%'
           OR SourcePath LIKE 'True Grit%'
        """,
    ):
        cur.execute(sql)
        print("deleted", cur.rowcount, flush=True)
    cn.commit()
    cn.close()
    ingest_main(["--apply"])


if __name__ == "__main__":
    main()
