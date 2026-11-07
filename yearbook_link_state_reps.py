#!/usr/bin/env python3
"""Link existing StateRepresentative rows to Owner and augment contact/Notes."""
from __future__ import annotations

import re

import pyodbc
from remount_source_divisions import CONN


def name_key(s: str) -> str:
    return re.sub(r"[^a-z]", "", (s or "").lower())


def append_note(existing, note: str) -> str:
    if existing and note in existing:
        return existing
    if not existing:
        return note
    return (existing.rstrip() + "\n" + note)[:4000]


def main() -> None:
    cn = pyodbc.connect(CONN, timeout=60)
    cur = cn.cursor()
    cur.execute(
        """
        SELECT StateRepID, Year, State, MemberName, Address, City, PostalCode, Phone, OwnerID
        FROM sResults.StateRepresentative
        """
    )
    reps = cur.fetchall()
    linked = updated = 0
    for sid, year, state, name, addr, city, postal, phone, owner_id in reps:
        oid = int(owner_id) if owner_id else None
        if not oid:
            cur.execute(
                "SELECT OwnerID, OwnerName FROM sResults.Owner WHERE OwnerName=?",
                (name or "")[:255],
            )
            row = cur.fetchone()
            if not row:
                parts = (name or "").split()
                if len(parts) >= 2:
                    last = parts[-1]
                    cur.execute(
                        "SELECT OwnerID, OwnerName FROM sResults.Owner WHERE OwnerName LIKE ?",
                        f"% {last}",
                    )
                    cands = [
                        r
                        for r in cur.fetchall()
                        if name_key(r[1]) == name_key(name)
                        or (
                            r[1]
                            and parts[0][0].lower() == r[1].strip()[:1].lower()
                            and r[1].lower().endswith(last.lower())
                        )
                    ]
                    if len(cands) == 1:
                        row = cands[0]
            if row:
                oid = int(row[0])
                cur.execute(
                    "UPDATE sResults.StateRepresentative SET OwnerID=? WHERE StateRepID=?",
                    oid,
                    int(sid),
                )
                linked += 1
        if not oid:
            continue
        note = f"JRTCA State Representative ({year})" + (f" — {state}" if state else "")
        cur.execute(
            "SELECT Address, City, State, PostalCode, Phone, Notes FROM sResults.Owner WHERE OwnerID=?",
            oid,
        )
        o = cur.fetchone()
        if not o:
            continue
        cur.execute(
            """
            UPDATE sResults.Owner
            SET Address=COALESCE(NULLIF(?,''), Address),
                City=COALESCE(NULLIF(?,''), City),
                State=COALESCE(NULLIF(?,''), State),
                PostalCode=COALESCE(NULLIF(?,''), PostalCode),
                Phone=COALESCE(NULLIF(?,''), Phone),
                Notes=?
            WHERE OwnerID=?
            """,
            addr or "",
            city or "",
            state or "",
            postal or "",
            phone or "",
            append_note(o[5], note),
            oid,
        )
        updated += 1
    cn.commit()
    print(f"reps={len(reps)} linked={linked} owner_updated={updated}")
    cn.close()


if __name__ == "__main__":
    main()
