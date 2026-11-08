#!/usr/bin/env python3
import pyodbc
from _remount_source_divisions import CONN
from _yearbook_certs_ingest import main as ingest_main

cn = pyodbc.connect(CONN, timeout=30)
cur = cn.cursor()
cur.execute("DELETE FROM sResults.NHC WHERE SourcePath LIKE '%jrtcayearbook%'")
print("deleted", cur.rowcount, flush=True)
cn.commit()
cn.close()
raise SystemExit(ingest_main(["--apply"]))
