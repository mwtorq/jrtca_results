#!/usr/bin/env python3
"""Ensure yearbook meta tables/columns exist (Board, Committee, StateRepresentative, Owner.Notes)."""
from __future__ import annotations

import pyodbc
from remount_source_divisions import CONN


def _ensure_owner_id(cur, table: str) -> None:
    """Add nullable OwnerID + soft FK to Owner when missing."""
    cur.execute(
        f"""
        IF COL_LENGTH('sResults.{table}','OwnerID') IS NULL
          ALTER TABLE sResults.[{table}] ADD OwnerID int NULL
        """
    )
    fk = f"FK_{table}_Owner"
    cur.execute(
        f"""
        IF NOT EXISTS (
          SELECT 1 FROM sys.foreign_keys
          WHERE name = '{fk}' AND parent_object_id = OBJECT_ID('sResults.{table}')
        )
        AND COL_LENGTH('sResults.{table}','OwnerID') IS NOT NULL
        AND OBJECT_ID('sResults.Owner','U') IS NOT NULL
        BEGIN
          BEGIN TRY
            ALTER TABLE sResults.[{table}] WITH NOCHECK
              ADD CONSTRAINT [{fk}] FOREIGN KEY (OwnerID)
              REFERENCES sResults.Owner(OwnerID)
          END TRY
          BEGIN CATCH
            -- leave column without FK if locks / orphans block it
          END CATCH
        END
        """
    )


def ensure(cur) -> None:
    # Owner.Notes may be locked by SSMS; try but continue if lock timeout.
    try:
        cur.execute(
            """
            IF COL_LENGTH('sResults.Owner','Notes') IS NULL
              ALTER TABLE sResults.Owner ADD Notes nvarchar(max) NULL
            """
        )
    except Exception as e:
        print("Owner.Notes alter skipped:", e)
    cur.execute(
        """
        IF OBJECT_ID('sResults.Board','U') IS NULL
        BEGIN
          CREATE TABLE sResults.Board (
            BoardID int NOT NULL PRIMARY KEY,
            Year int NOT NULL,
            MemberName nvarchar(255) NOT NULL,
            Role nvarchar(100) NULL,
            Address nvarchar(255) NULL,
            City nvarchar(100) NULL,
            State nvarchar(50) NULL,
            PostalCode nvarchar(20) NULL,
            Phone nvarchar(100) NULL,
            SourcePath nvarchar(1000) NULL,
            Notes nvarchar(max) NULL,
            OwnerID int NULL,
            CreateDateTime datetime NULL CONSTRAINT DF_Board_Create DEFAULT (GETDATE())
          );
          CREATE UNIQUE INDEX UX_Board_Year_Name_Role ON sResults.Board(Year, MemberName, Role);
        END
        """
    )
    cur.execute(
        """
        IF OBJECT_ID('sResults.Committee','U') IS NULL
        BEGIN
          CREATE TABLE sResults.Committee (
            CommitteeID int NOT NULL PRIMARY KEY,
            Year int NOT NULL,
            CommitteeName nvarchar(255) NOT NULL,
            MemberName nvarchar(255) NOT NULL,
            Role nvarchar(100) NULL,
            Address nvarchar(255) NULL,
            City nvarchar(100) NULL,
            State nvarchar(50) NULL,
            PostalCode nvarchar(20) NULL,
            Phone nvarchar(100) NULL,
            SourcePath nvarchar(1000) NULL,
            Notes nvarchar(max) NULL,
            OwnerID int NULL,
            CreateDateTime datetime NULL CONSTRAINT DF_Committee_Create DEFAULT (GETDATE())
          );
          CREATE UNIQUE INDEX UX_Committee_Year_Comm_Name_Role
            ON sResults.Committee(Year, CommitteeName, MemberName, Role);
        END
        """
    )
    cur.execute(
        """
        IF OBJECT_ID('sResults.StateRepresentative','U') IS NULL
        BEGIN
          CREATE TABLE sResults.StateRepresentative (
            StateRepID int NOT NULL PRIMARY KEY,
            Year int NOT NULL,
            State nvarchar(50) NULL,
            MemberName nvarchar(255) NOT NULL,
            Role nvarchar(100) NULL,
            Address nvarchar(255) NULL,
            City nvarchar(100) NULL,
            PostalCode nvarchar(20) NULL,
            Phone nvarchar(100) NULL,
            SourcePath nvarchar(1000) NULL,
            Notes nvarchar(max) NULL,
            OwnerID int NULL,
            CreateDateTime datetime NULL CONSTRAINT DF_StateRep_Create DEFAULT (GETDATE())
          );
          CREATE UNIQUE INDEX UX_StateRep_Year_Name_State
            ON sResults.StateRepresentative(Year, MemberName, State);
        END
        """
    )
    # Existing tables created before OwnerID: add column + soft FK.
    for t in ("Board", "Committee", "StateRepresentative"):
        try:
            _ensure_owner_id(cur, t)
        except Exception as e:
            print(f"{t}.OwnerID alter skipped:", e)

    # Natural Hunting Certificates
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
          CREATE INDEX IX_NHC_DogName ON sResults.NHC(DogName);
          CREATE INDEX IX_NHC_Year ON sResults.NHC(Year);
        END
        """
    )
    # Trial Certificates (yearbook listings)
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
            CreateDateTime datetime NULL CONSTRAINT DF_TrialCert_Create DEFAULT (GETDATE())
          );
          CREATE INDEX IX_TrialCert_DogName ON sResults.TrialCertificates(DogName);
          CREATE INDEX IX_TrialCert_Year ON sResults.TrialCertificates(Year);
        END
        """
    )


def main() -> None:
    cn = pyodbc.connect(CONN, timeout=30, autocommit=True)
    cur = cn.cursor()
    cur.execute("SET LOCK_TIMEOUT 15000")
    ensure(cur)
    cur.execute(
        """
        SELECT name FROM sys.tables
        WHERE schema_id=SCHEMA_ID('sResults')
          AND name IN ('Board','Committee','StateRepresentative')
        ORDER BY name
        """
    )
    print("tables", [r[0] for r in cur.fetchall()])
    for t in ("Board", "Committee", "StateRepresentative"):
        cur.execute(f"SELECT COL_LENGTH('sResults.{t}','OwnerID')")
        print(f"{t}.OwnerID", cur.fetchone()[0])
    cur.execute("SELECT COL_LENGTH('sResults.Owner','Notes')")
    print("Owner.Notes", cur.fetchone()[0])
    cn.close()


if __name__ == "__main__":
    main()
