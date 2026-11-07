#!/usr/bin/env python3
"""Ensure True Grit certificate tables exist (TrialCertificates, NHC)."""
from __future__ import annotations

import pyodbc
from remount_source_divisions import CONN


def ensure(cur) -> None:
    """Create tables if missing; add optional True Grit columns when absent."""
    cur.execute(
        """
        IF OBJECT_ID('sResults.TrialCertificates','U') IS NULL
        BEGIN
          CREATE TABLE sResults.TrialCertificates (
            TrialCertificateID int NOT NULL PRIMARY KEY,
            Year int NULL,
            DogName nvarchar(255) NOT NULL,
            DogID int NULL,
            OwnerName nvarchar(255) NULL,
            OwnerID int NULL,
            BreederName nvarchar(255) NULL,
            BreederID int NULL,
            JudgeName nvarchar(255) NULL,
            TrialName nvarchar(255) NULL,
            CertificateType nvarchar(100) NULL,
            Notes nvarchar(max) NULL,
            SourcePath nvarchar(1000) NULL,
            CreateDateTime datetime NULL CONSTRAINT DF_TC_Create DEFAULT (GETDATE())
          );
        END
        """
    )
    cur.execute(
        """
        IF OBJECT_ID('sResults.NHC','U') IS NULL
        BEGIN
          CREATE TABLE sResults.NHC (
            NHCID int NOT NULL PRIMARY KEY,
            Year int NULL,
            DogName nvarchar(255) NOT NULL,
            DogID int NULL,
            OwnerName nvarchar(255) NULL,
            OwnerID int NULL,
            BreederName nvarchar(255) NULL,
            BreederID int NULL,
            CertificateType nvarchar(100) NULL,
            Prey nvarchar(100) NULL,
            Notes nvarchar(max) NULL,
            SourcePath nvarchar(1000) NULL,
            CreateDateTime datetime NULL CONSTRAINT DF_NHC_Create DEFAULT (GETDATE())
          );
        END
        """
    )
    # Optional enrichments used by True Grit ingest
    for table, col, typ in (
        ("TrialCertificates", "Volume", "int NULL"),
        ("TrialCertificates", "Issue", "int NULL"),
        ("TrialCertificates", "PeriodStart", "date NULL"),
        ("TrialCertificates", "PeriodEnd", "date NULL"),
        ("NHC", "JudgeName", "nvarchar(255) NULL"),
        ("NHC", "Volume", "int NULL"),
        ("NHC", "Issue", "int NULL"),
        ("NHC", "PeriodStart", "date NULL"),
        ("NHC", "PeriodEnd", "date NULL"),
    ):
        cur.execute(
            f"""
            IF COL_LENGTH('sResults.{table}', '{col}') IS NULL
              ALTER TABLE sResults.[{table}] ADD [{col}] {typ}
            """
        )


def main() -> None:
    cn = pyodbc.connect(CONN, timeout=30, autocommit=True)
    cur = cn.cursor()
    ensure(cur)
    for t in ("TrialCertificates", "NHC"):
        cur.execute(f"SELECT COL_LENGTH('sResults.{t}','DogName')")
        print(t, "ok" if cur.fetchone()[0] else "missing")
    cn.close()


if __name__ == "__main__":
    main()
