#!/usr/bin/env python3
"""Map Yearbook Scans/Photos sources to TrialList; flag MISSING and weak remaps.

Does not treat folder year as authoritative — filename year is a weak hint only.
National Entries Catalogs are skipped (entries, not results).
Legacy .txt/.rtf are catalogued as hints, not placement authority.
"""
from __future__ import annotations

import csv
import os
import re
import sys
from pathlib import Path

import pyodbc

from remount_source_divisions import CONN

ROOT = Path(r"c:\Users\mw\OneDrive - timberwilde.net\repos\jrtca_results")
SCANS = ROOT / "Yearbook Scans"
PHOTOS = ROOT / "Yearbook Photos"
OUT_CSV = ROOT / "_yearbook_gap_map.csv"

_SKIP_DIR_FRAGMENTS = (
    "national entries catalog",
)
_SKIP_NAME_FRAGMENTS = (
    "entries catalog",
    "yearbook scans - ",
)
_YEAR_RE = re.compile(r"(19[8-9]\d|20[0-2]\d)")


def trial_key(name: str) -> str:
    s = (name or "").lower()
    s = re.sub(r"[^a-z0-9]+", " ", s)
    s = re.sub(r"\b(19[8-9]\d|20[0-2]\d)\b", " ", s)
    s = re.sub(r"\b(jrtca|jrtcc|trial|trials|annual|the|and|&)\b", " ", s)
    return re.sub(r"\s+", " ", s).strip()


def filename_trial_guess(path: Path) -> tuple[str | None, int | None]:
    stem = path.stem
    # strip common suffixes
    stem = re.sub(r"_(ocr|raw)$", "", stem, flags=re.I)
    stem = re.sub(r"\s*pg\s*\d+.*$", "", stem, flags=re.I)
    stem = re.sub(r"\s*p\.?\s*\d+.*$", "", stem, flags=re.I)
    stem = re.sub(r"\s*\(.*$", "", stem)
    stem = re.sub(r"\s*pt\.?\s*\d+.*$", "", stem, flags=re.I)
    stem = re.sub(r"\s*vol\.?\s*[ivx0-9]+.*$", "", stem, flags=re.I)
    stem = stem.strip(" -_,.")
    ym = _YEAR_RE.search(stem) or _YEAR_RE.search(str(path))
    year = int(ym.group(1)) if ym else None
    # phone photo names are not trial names
    if re.match(r"^\d{8}[_-]\d+", stem):
        return None, year
    if re.match(r"^\d+\s*to\s*\d+$", stem, re.I):
        return None, year
    if stem.lower() in ("docscan",):
        return None, year
    if "vol" in stem.lower() and "national" not in stem.lower():
        # multi-trial volume dump — not a single trial source
        return f"[VOLUME] {stem}", year
    return stem or None, year


def iter_sources():
    for base in (SCANS, PHOTOS):
        if not base.is_dir():
            continue
        for dirpath, dirnames, filenames in os.walk(base):
            # prune entries catalogs
            dirnames[:] = [
                d
                for d in dirnames
                if not any(s in d.lower() for s in _SKIP_DIR_FRAGMENTS)
            ]
            rel_dir = os.path.relpath(dirpath, ROOT)
            if any(s in rel_dir.lower() for s in _SKIP_DIR_FRAGMENTS):
                continue
            for fn in filenames:
                fl = fn.lower()
                if fl.endswith((".zip", ".db", ".ds_store")):
                    continue
                if any(s in fl for s in _SKIP_NAME_FRAGMENTS):
                    continue
                if fl.endswith("_ocr.txt"):
                    continue  # generated
                ext = Path(fn).suffix.lower()
                if ext not in (
                    ".pdf",
                    ".txt",
                    ".rtf",
                    ".jpg",
                    ".jpeg",
                    ".png",
                    ".tif",
                    ".tiff",
                ):
                    continue
                path = Path(dirpath) / fn
                yield path


def load_trials(cur):
    cur.execute(
        """
        SELECT TrialListID, Year, TrialName, TrialResultFilePath
        FROM sResults.TrialList
        """
    )
    by_year: dict[int, list] = {}
    for tid, year, name, path in cur.fetchall():
        y = int(year) if year is not None else None
        if y is None:
            continue
        by_year.setdefault(y, []).append(
            {
                "tid": int(tid),
                "name": name or "",
                "path": path or "",
                "key": trial_key(name or ""),
            }
        )
    return by_year


def match_trial(guess: str | None, year: int | None, by_year) -> tuple[str, int | None, str]:
    if not guess or guess.startswith("[VOLUME]"):
        return ("VOLUME" if guess and guess.startswith("[VOLUME]") else "NO_NAME"), None, ""
    if year is None:
        return "NO_YEAR", None, ""
    candidates = by_year.get(year, [])
    gk = trial_key(guess)
    if not gk:
        return "NO_NAME", None, ""
    # exact key
    for c in candidates:
        if c["key"] == gk:
            return "MATCH", c["tid"], c["name"]
    # substring either way
    hits = []
    for c in candidates:
        if not c["key"]:
            continue
        if gk in c["key"] or c["key"] in gk:
            hits.append(c)
    if len(hits) == 1:
        return "MATCH", hits[0]["tid"], hits[0]["name"]
    if len(hits) > 1:
        return "AMBIG", hits[0]["tid"], hits[0]["name"]
    # national special-case
    if "national" in gk:
        nat = [c for c in candidates if "national" in c["key"]]
        if len(nat) == 1:
            return "MATCH", nat[0]["tid"], nat[0]["name"]
        if len(nat) > 1:
            # prefer JRTCA vs JRTCC by guess
            if "jrtcc" in guess.lower() or "jrtcc" in gk:
                j = [c for c in nat if "jrtcc" in (c["name"] or "").lower()]
                if len(j) == 1:
                    return "MATCH", j[0]["tid"], j[0]["name"]
            else:
                j = [c for c in nat if "jrtca" in (c["name"] or "").lower() or "jrtcc" not in (c["name"] or "").lower()]
                if len(j) == 1:
                    return "MATCH", j[0]["tid"], j[0]["name"]
            return "AMBIG", nat[0]["tid"], nat[0]["name"]
    return "MISSING", None, ""


def weak_path(db_path: str) -> bool:
    p = (db_path or "").lower()
    if not p.strip():
        return True
    if "synology" in p or p.endswith(".xls") or p.endswith(".xlsx"):
        return True
    if "yearbook scans" in p or "yearbook photos" in p:
        return False
    return True  # existing non-yearbook path — candidate for remap if we have better scan


def main() -> int:
    cn = pyodbc.connect(CONN, timeout=60)
    cur = cn.cursor()
    by_year = load_trials(cur)
    cn.close()

    rows = []
    for path in sorted(iter_sources(), key=lambda p: str(p).lower()):
        rel = str(path.relative_to(ROOT))
        guess, year_hint = filename_trial_guess(path)
        status, tid, matched_name = match_trial(guess, year_hint, by_year)
        db_path = ""
        if tid:
            for c in by_year.get(year_hint or -1, []):
                if c["tid"] == tid:
                    db_path = c["path"]
                    break
        authority = "hint_only" if path.suffix.lower() in (".txt", ".rtf") else "scan"
        if path.suffix.lower() in (".jpg", ".jpeg", ".png"):
            authority = "photo"
        remap = ""
        if status == "MATCH" and authority in ("scan", "photo") and weak_path(db_path):
            remap = "REMAP_CANDIDATE"
        if status == "MISSING" and guess and not str(guess).startswith("[VOLUME]"):
            remap = "CREATE_SHELL"
        rows.append(
            {
                "rel_path": rel,
                "ext": path.suffix.lower(),
                "authority": authority,
                "name_guess": guess or "",
                "year_hint_filename": year_hint or "",
                "match_status": status,
                "trial_list_id": tid or "",
                "matched_trial_name": matched_name,
                "db_path": db_path,
                "action": remap,
                "size": path.stat().st_size,
            }
        )

    with open(OUT_CSV, "w", encoding="utf-8", newline="") as f:
        w = csv.DictWriter(f, fieldnames=list(rows[0].keys()) if rows else [])
        if rows:
            w.writeheader()
            w.writerows(rows)

    # summary
    from collections import Counter

    st = Counter(r["match_status"] for r in rows)
    act = Counter(r["action"] for r in rows if r["action"])
    print(f"wrote {OUT_CSV} rows={len(rows)}")
    print("status", dict(st))
    print("actions", dict(act))
    print("\nMISSING / CREATE_SHELL:")
    for r in rows:
        if r["action"] == "CREATE_SHELL":
            print(f"  {r['year_hint_filename']} {r['name_guess']!r} <- {r['rel_path']}")
    print("\nREMAP_CANDIDATE (named scans):")
    for r in rows:
        if r["action"] == "REMAP_CANDIDATE" and r["authority"] == "scan" and r["ext"] == ".pdf":
            if r["name_guess"] and not str(r["name_guess"]).startswith("[VOLUME]"):
                print(
                    f"  tid={r['trial_list_id']} {r['name_guess']!r} -> {r['rel_path']}"
                )
    # years with zero trials in DB but sources present
    print("\nYears with sources but sparse/no DB trials:")
    src_years = Counter()
    for r in rows:
        y = r["year_hint_filename"]
        if y:
            src_years[int(y)] += 1
    for y in sorted(src_years):
        n = len(by_year.get(y, []))
        if n <= 2:
            print(f"  {y}: sources={src_years[y]} db_trials={n}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
