#!/usr/bin/env python3
"""B7 — Parse harvested NHC / Trial Certificate / Bronze section text.

Reads ``_ocr_baseline_v2/certs/raw_sections/*.txt`` (+ optional year filter),
emits structured rows. Tolerates common OCR height/size dust and smashed
columns. Does **not** write SQL (B8).

Usage:
  python -u parse_cert_sections.py --spot-check
  python -u parse_cert_sections.py --years 1994 1995 1996 --out _b7_cert_parse_spot.json
"""
from __future__ import annotations

import argparse
import json
import re
from collections import Counter
from pathlib import Path

ROOT = Path(r"c:\Users\mw\OneDrive - timberwilde.net\repos\jrtca_results")
RAW = ROOT / "_ocr_baseline_v2" / "certs" / "raw_sections"

QUARRY_RX = re.compile(
    r"(?i)\b("
    r"groundhog|woodchuck|opossum|raccoon|nutria|"
    r"red\s*fox|grey\s*fox|gray\s*fox|fox|"
    r"badger|coyote|rat"
    r")\b"
)
HEADER_RX = re.compile(
    r"(?im)^(?:"
    r"name(?:\s+of\s+terrier)?|owner|judge|quarry|"
    r"natural\s+hunting|trial\s+certificates?|"
    r"bronze\s+medallions?|honorable\s+mention|"
    r"working\s+achievement"
    r").*$"
)
# Single-line table: Dog … Owner … Judge … Quarry (last token often quarry)
LINE_TABLE_RX = re.compile(
    r"^(?P<dog>.+?)\s{2,}(?P<owner>.+?)\s{2,}(?P<rest>.+)$"
)
def normalize_quarry(s: str) -> str:
    s = re.sub(r"\s+", " ", (s or "").strip().lower())
    s = s.replace("gray fox", "grey fox")
    if s == "fox":
        return "fox"
    return s.title() if s else ""


def clean_name(s: str) -> str:
    s = (s or "").replace("\u2019", "'").replace("`", "'")
    s = re.sub(r"[|_]+", " ", s)
    s = re.sub(r"\s{2,}", " ", s).strip(" .-–,")
    # Drop leading OCR dust like ". " or lone digits glued to names
    s = re.sub(r"^[.\d]+\s+", "", s)
    return s.strip()


def section_kind(text: str) -> str:
    head = text[:400].lower()
    if "bronze medallion" in head and "special merit" in head:
        return "bronze"
    if "trial certificate" in head:
        return "trial_cert"
    if "natural hunting" in head:
        return "nhc"
    if "working achievement" in head:
        return "wa"
    return "unknown"


def parse_section(text: str, *, year: int | None, source: str) -> list[dict]:
    """Extract best-effort rows from one harvested section."""
    kind = section_kind(text)
    rows: list[dict] = []
    pending_dog: str | None = None
    pending_owner: str | None = None

    for raw in text.splitlines():
        line = raw.rstrip()
        if not line.strip():
            continue
        if HEADER_RX.match(line.strip()):
            continue
        if re.match(r"(?i)^(?:name|owner|judge|quarry)\s*$", line.strip()):
            continue

        qm = QUARRY_RX.search(line)
        # Dense table line with 2+ wide gaps
        if "  " in line and qm:
            m = LINE_TABLE_RX.match(line.strip())
            if m:
                dog = clean_name(m.group("dog"))
                owner = clean_name(m.group("owner"))
                rest = m.group("rest").strip()
                # Split rest into judge + quarry (quarry is last animal token)
                quarry = normalize_quarry(qm.group(0))
                judge = clean_name(QUARRY_RX.sub("", rest))
                if dog and len(dog) >= 3:
                    rows.append(
                        {
                            "year": year,
                            "kind": kind,
                            "dog": dog,
                            "owner": owner,
                            "judge": judge,
                            "quarry": quarry,
                            "source": source,
                            "raw": line.strip()[:200],
                        }
                    )
                    pending_dog = None
                    pending_owner = None
                    continue

        # Continuation: owner/judge on prior line, quarry-only or dog-only
        if qm and len(line.strip()) < 40:
            quarry = normalize_quarry(qm.group(0))
            who = clean_name(QUARRY_RX.sub("", line))
            if pending_dog:
                rows.append(
                    {
                        "year": year,
                        "kind": kind,
                        "dog": pending_dog,
                        "owner": pending_owner or who,
                        "judge": "",
                        "quarry": quarry,
                        "source": source,
                        "raw": line.strip()[:200],
                    }
                )
                pending_dog = None
                pending_owner = None
            continue

        # Name-only / wrapped dog line (no quarry yet)
        if not qm and len(line.strip()) >= 4 and not re.search(r"\d{3,}", line):
            # Likely a dog name if it has letters and isn't a page chrome
            if re.search(r"[A-Za-z]", line) and "Entries:" not in line:
                pending_dog = clean_name(line)
                pending_owner = None

    return rows


def iter_raw_sections(years: set[int] | None) -> list[tuple[Path, dict]]:
    out: list[tuple[Path, dict]] = []
    for meta_path in sorted(RAW.glob("*.meta.json")):
        try:
            meta = json.loads(meta_path.read_text(encoding="utf-8"))
        except Exception:
            continue
        y = meta.get("year")
        if years is not None and y not in years:
            continue
        raw_name = meta.get("raw_file") or meta_path.name.replace(".meta.json", "")
        raw_path = RAW / raw_name
        if not raw_path.is_file():
            continue
        out.append((raw_path, meta))
    return out


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--years", type=int, nargs="*", default=None)
    ap.add_argument("--out", type=Path, default=None)
    ap.add_argument(
        "--spot-check",
        action="store_true",
        help="Parse 1990–1996 samples and print quality summary (default years if omitted)",
    )
    args = ap.parse_args()
    years: set[int] | None
    if args.years:
        years = set(args.years)
    elif args.spot_check:
        years = set(range(1990, 1997))
    else:
        years = None

    all_rows: list[dict] = []
    by_file = Counter()
    for raw_path, meta in iter_raw_sections(years):
        text = raw_path.read_text(encoding="utf-8", errors="replace")
        rows = parse_section(
            text,
            year=meta.get("year"),
            source=str(meta.get("source_path") or raw_path.name),
        )
        all_rows.extend(rows)
        by_file[raw_path.name] = len(rows)

    kinds = Counter(r["kind"] for r in all_rows)
    quarries = Counter(r["quarry"] for r in all_rows if r.get("quarry"))
    missing_dog = sum(1 for r in all_rows if not r.get("dog"))
    missing_quarry = sum(1 for r in all_rows if r.get("kind") == "nhc" and not r.get("quarry"))

    print(f"sections_scanned={len(by_file)} rows={len(all_rows)}")
    print(f"  kinds={dict(kinds)}")
    print(f"  top_quarries={quarries.most_common(8)}")
    print(f"  missing_dog={missing_dog} nhc_missing_quarry={missing_quarry}")
    # Spot samples
    for r in all_rows[:8]:
        print(
            f"  sample y={r.get('year')} {r.get('kind')}: "
            f"{r.get('dog')} | {r.get('owner')} | {r.get('judge')} | {r.get('quarry')}"
        )

    out = args.out
    if out is None and args.spot_check:
        out = ROOT / "_b7_cert_parse_spot.json"
    if out is not None:
        payload = {
            "rows": len(all_rows),
            "kinds": dict(kinds),
            "quarries": dict(quarries),
            "missing_dog": missing_dog,
            "nhc_missing_quarry": missing_quarry,
            "samples": all_rows[:50],
            "per_file_top": by_file.most_common(20),
        }
        out.write_text(json.dumps(payload, indent=2), encoding="utf-8")
        print(f"Wrote {out}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
