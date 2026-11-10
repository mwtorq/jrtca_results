#!/usr/bin/env python3
"""Harvest NHC / Trial Certificate OCR sections into baseline v2 certs raw.

Does not write to DB. Outputs raw section text for parser development + JSON index.

Sources:
  - 1984–1996: ``Updated Yearbook Scans`` ``*_ocr_hqmax.txt`` (legacy path)
  - 1997–2001: ``_ocr_baseline_v2/yearbook_1990_2001/{year}/**`` (remediation HQ)

``--years`` scopes harvest; other years already in the index are preserved.

Usage:
  python -u harvest_cert_sections_v2.py
  python -u harvest_cert_sections_v2.py --years 1997 1998
"""
from __future__ import annotations

import argparse
import json
import re
from pathlib import Path

ROOT = Path(r"c:\Users\mw\OneDrive - timberwilde.net\repos\jrtca_results")
UPDATED = ROOT / "Updated Yearbook Scans"
BASELINE_YB = ROOT / "_ocr_baseline_v2" / "yearbook_1990_2001"
OUT = ROOT / "_ocr_baseline_v2" / "certs"
RAW = OUT / "raw_sections"
RAW.mkdir(parents=True, exist_ok=True)
IDX_PATH = OUT / "cert_sections_index.json"

# True yearbook *lists* — not go-to-ground "Championship Certificate" classes
# and not conformation "Bronze Medallion Class".
HEAD_RX = re.compile(
    r"(?is)(?:"
    r"natural\s+hunting\s+certificates?(?:\s+below\s+ground|\s+in\s+the\s+field|\s*\(cont)?"
    r"|trial\s+certificates?(?:\s*\(cont)?"
    r"|bronze\s+medallions?\s+for\s+special\s+merit"
    r"|working\s+achievement\s+awards?"
    r")"
)
# Explicit false positives (trial-result class titles / ads).
FALSE_HEAD_RX = re.compile(
    r"(?is)(?:championship\s+certificate|advanced\s+certificate|"
    r"agility\s+[il1]{1,2}\s+certificate|bronze\s+medallion\s+class|"
    r"bronze\s+medallion\s+(?:dog|bitch)\b)"
)
STOP_RX = re.compile(
    r"(?is)^(?:sanctioned\s+trial\s+results|conformation\s+division|"
    r"go-?to-?ground|racing\s+division|new\s+members|board\s+of\s+directors|"
    r"state\s+representatives|table\s+of\s+contents)\b"
)
MIN_SECTION_CHARS = 280


def split_pages(text: str) -> list[tuple[str, str]]:
    """Return list of (page_label, page_text)."""
    parts = re.split(r"(?m)^(---\s*page\s+\d+\s*---)\s*$", text)
    if len(parts) == 1:
        return [("all", text)]
    out = []
    if parts[0].strip():
        out.append(("preamble", parts[0]))
    for i in range(1, len(parts), 2):
        label = parts[i].strip()
        body = parts[i + 1] if i + 1 < len(parts) else ""
        out.append((label, body))
    return out


def harvest_file(path: Path, year: int | None, source_kind: str) -> list[dict]:
    text = path.read_text(encoding="utf-8", errors="replace")
    pages = split_pages(text)
    hits = []
    for label, body in pages:
        # Drop pages that are only false-positive class titles.
        if FALSE_HEAD_RX.search(body) and not HEAD_RX.search(body) and not HEAD_RX.search(label):
            continue
        if not HEAD_RX.search(body) and not HEAD_RX.search(label):
            if not re.search(r"(?is)natural\s+hunting\s+certificates?\s*\(cont", body):
                continue
        m = HEAD_RX.search(body)
        if not m:
            continue
        # Skip if the match itself is a false class title (e.g. bronze…class).
        head_line = body[m.start() : m.start() + 80]
        if FALSE_HEAD_RX.search(head_line):
            continue
        start = m.start()
        chunk = body[start:]
        stop = STOP_RX.search(chunk[200:]) if len(chunk) > 200 else None
        if stop:
            chunk = chunk[: 200 + stop.start()]
        chunk = chunk.strip()
        if len(chunk) < MIN_SECTION_CHARS:
            continue
        has_nhc = bool(re.search(r"(?is)natural\s+hunting", chunk))
        has_trial = bool(re.search(r"(?is)trial\s+certificates?", chunk))
        has_bronze = bool(re.search(r"(?is)bronze\s+medallions?\s+for\s+special\s+merit", chunk))
        # Require at least one real list signal (not a stray mention in an ad).
        if not (has_nhc or has_trial or has_bronze):
            continue
        hits.append(
            {
                "year": year,
                "source_kind": source_kind,
                "source_path": str(path.relative_to(ROOT)),
                "page": label,
                "chars": len(chunk),
                "has_nhc": has_nhc,
                "has_trial_cert": has_trial,
                "has_bronze": has_bronze,
                "text": chunk,
            }
        )
    return hits


def harvest_updated_pre1997(years: set[int]) -> list[dict]:
    hits: list[dict] = []
    for year in range(1990, 1997):
        if year not in years:
            continue
        for vol in (1, 2):
            folder = UPDATED / f"{year} Yearbook Vol {vol}"
            if not folder.is_dir():
                continue
            for p in sorted(folder.glob("*_ocr_hqmax.txt")):
                hits.extend(harvest_file(p, year, "yearbook_vol"))
    for name in ["1984 & 1985", "1986", "1987", "1988", "1989", "1990"]:
        folder = UPDATED / name
        if not folder.is_dir():
            continue
        year = 1984 if "1984" in name else int(name[:4])
        if year not in years:
            continue
        for p in sorted(folder.glob("*_ocr_hqmax.txt")):
            hits.extend(harvest_file(p, year, "nonyearbook"))
    return hits


def harvest_baseline_v2(years: set[int]) -> list[dict]:
    """1997+ remediation HQ under yearbook_1990_2001."""
    hits: list[dict] = []
    for year in sorted(years):
        if year < 1997:
            continue
        ydir = BASELINE_YB / str(year)
        if not ydir.is_dir():
            continue
        for p in sorted(ydir.rglob("*_ocr_hqmax.txt")):
            hits.extend(harvest_file(p, year, "baseline_v2"))
    return hits


def load_index() -> list[dict]:
    if not IDX_PATH.is_file():
        return []
    try:
        data = json.loads(IDX_PATH.read_text(encoding="utf-8"))
        return data if isinstance(data, list) else []
    except Exception:
        return []


def purge_year_raw_files(years: set[int]) -> None:
    """Remove raw section files belonging to years being re-harvested."""
    for meta_path in list(RAW.glob("*.meta.json")):
        try:
            meta = json.loads(meta_path.read_text(encoding="utf-8"))
        except Exception:
            continue
        y = meta.get("year")
        if y in years:
            raw_name = meta.get("raw_file") or meta_path.name.replace(".meta.json", "")
            raw_path = RAW / raw_name
            if raw_path.is_file():
                raw_path.unlink()
            meta_path.unlink()


def write_hits(all_hits: list[dict]) -> Path:
    index = []
    for i, h in enumerate(all_hits, 1):
        fn = f"{h['year'] or 'unk'}_{h['source_kind']}_{i:04d}.txt"
        (RAW / fn).write_text(h["text"], encoding="utf-8")
        meta = {k: v for k, v in h.items() if k != "text"}
        meta["raw_file"] = fn
        index.append(meta)
        (RAW / (fn + ".meta.json")).write_text(
            json.dumps(meta, indent=2), encoding="utf-8"
        )
    IDX_PATH.write_text(json.dumps(index, indent=2), encoding="utf-8")
    return IDX_PATH


def parse_years(args_years: list[int] | None) -> set[int]:
    if not args_years:
        # Default: full legacy pre-1997 pass (backward compatible)
        return set(range(1984, 1997))
    return set(args_years)


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument(
        "--years",
        type=int,
        nargs="*",
        default=None,
        help="Years to (re)harvest. Default: 1984–1996 legacy. "
        "Use 1997+ for baseline_v2 remediation harvest.",
    )
    args = ap.parse_args()
    years = parse_years(args.years)

    new_hits: list[dict] = []
    new_hits.extend(harvest_updated_pre1997(years))
    new_hits.extend(harvest_baseline_v2(years))

    # Preserve index entries for years not in this run; drop text (reload from disk N/A)
    # Rebuild: keep other years' hits by re-reading their raw files via old index.
    old_index = load_index()
    preserved: list[dict] = []
    for meta in old_index:
        y = meta.get("year")
        if y in years:
            continue
        raw_file = meta.get("raw_file")
        if not raw_file:
            continue
        raw_path = RAW / raw_file
        if not raw_path.is_file():
            continue
        text = raw_path.read_text(encoding="utf-8", errors="replace")
        preserved.append({**{k: v for k, v in meta.items() if k != "raw_file"}, "text": text})

    purge_year_raw_files(years)
    # Also wipe all raw when doing a full rewrite of combined set — we rewrite everything
    # from preserved + new to avoid stale filenames / index drift.
    for p in list(RAW.glob("*")):
        if p.is_file():
            p.unlink()

    all_hits = preserved + new_hits
    write_hits(all_hits)

    print(f"harvested_sections={len(all_hits)} (new={len(new_hits)} preserved={len(preserved)})")
    print(
        f"  nhc={sum(1 for h in all_hits if h['has_nhc'])} "
        f"trial_cert={sum(1 for h in all_hits if h['has_trial_cert'])} "
        f"bronze={sum(1 for h in all_hits if h['has_bronze'])}"
    )
    by_year: dict[int, int] = {}
    for h in all_hits:
        y = h["year"] or 0
        by_year[y] = by_year.get(y, 0) + 1
    for y in sorted(by_year):
        tag = " *" if y in years else ""
        print(f"  {y}: {by_year[y]} sections{tag}")
    print(f"Wrote {IDX_PATH}")
    print(f"Wrote {RAW}")
    # return count of new sections for orchestrator (via stdout parse) — also exit 0
    print(f"new_sections_for_years={len(new_hits)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
