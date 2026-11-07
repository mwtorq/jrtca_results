#!/usr/bin/env python3
"""Advance year-pipelined remediation steps for 1997–2001.

For each year with A1 complete:
  - run A2 if missing/stale
  - if A2 unlocked (FAIL=0), run year-scoped B6 cert harvest
  - run B6b catalog ingest audit (blocks SQL apply on FAIL)
  - optional ``--advance-c10``: copy HQ text into a normalize staging folder (no SQL)

Safe to re-run while A1 OCR tracks continue. Does not spawn tess workers.

Usage:
  python -u pipeline_advance_years.py --years 1997 1998
  python -u pipeline_advance_years.py --years 1997-2001
  python -u pipeline_advance_years.py --years 1997 1998 --advance-c10
"""
from __future__ import annotations

import argparse
import json
import re
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path

from pipeline_year_status import HQ_MIN_BYTES, refresh_years, save_manifest, load_manifest

ROOT = Path(r"c:\Users\mw\OneDrive - timberwilde.net\repos\jrtca_results")
BASE = ROOT / "_ocr_baseline_v2" / "yearbook_1990_2001"
NORM = ROOT / "_ocr_baseline_v2" / "trial_results_norm"
LOG = ROOT / "_pipeline_advance.log"
PY = sys.executable


def _now() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def log(msg: str) -> None:
    line = f"[{_now()}] {msg}"
    print(line, flush=True)
    with LOG.open("a", encoding="utf-8") as f:
        f.write(line + "\n")


def parse_year_args(raw: list[str]) -> list[int]:
    years: set[int] = set()
    for tok in raw:
        tok = tok.strip()
        if re.fullmatch(r"\d{4}-\d{4}", tok):
            a, b = tok.split("-")
            lo, hi = int(a), int(b)
            if lo > hi:
                lo, hi = hi, lo
            years.update(range(lo, hi + 1))
        else:
            years.add(int(tok))
    return sorted(years)


def run_cmd(args: list[str]) -> int:
    log("RUN " + " ".join(args))
    p = subprocess.run(args, cwd=str(ROOT))
    return int(p.returncode)


def a2_csv_fresh(year: int) -> bool:
    p = ROOT / f"_a2_quality_gate_{year}.csv"
    return p.is_file() and p.stat().st_size > 20


def advance_c10_year(year: int) -> int:
    """Stage HQ texts under trial_results_norm/{year}/ (no SQL)."""
    src = BASE / str(year)
    if not src.is_dir():
        log(f"C10 y={year} skip — no baseline dir")
        return 0
    dest = NORM / str(year)
    dest.mkdir(parents=True, exist_ok=True)
    n = 0
    for hq in sorted(src.rglob("*_ocr_hqmax.txt")):
        if hq.stat().st_size <= HQ_MIN_BYTES:
            continue
        rel = hq.relative_to(src)
        out = dest / rel
        out.parent.mkdir(parents=True, exist_ok=True)
        out.write_text(hq.read_text(encoding="utf-8", errors="replace"), encoding="utf-8")
        n += 1
    log(f"C10 y={year} staged {n} hqmax -> {dest.relative_to(ROOT)}")
    data = load_manifest()
    ymap = dict(data.get("years") or {})
    entry = dict(ymap.get(str(year)) or {})
    entry["c10"] = "staged"
    ts = dict(entry.get("timestamps") or {})
    ts["c10_staged"] = _now()
    entry["timestamps"] = ts
    ymap[str(year)] = entry
    data["years"] = ymap
    save_manifest(data)
    return n


def mark_b6(year: int, sections: int) -> None:
    data = load_manifest()
    ymap = dict(data.get("years") or {})
    entry = dict(ymap.get(str(year)) or {})
    entry["b6"] = "done"
    entry["b6_sections"] = sections
    ts = dict(entry.get("timestamps") or {})
    ts["b6_done"] = _now()
    entry["timestamps"] = ts
    ymap[str(year)] = entry
    data["years"] = ymap
    save_manifest(data)


def count_index_sections(year: int) -> int:
    idx = ROOT / "_ocr_baseline_v2" / "certs" / "cert_sections_index.json"
    if not idx.is_file():
        return 0
    try:
        data = json.loads(idx.read_text(encoding="utf-8"))
    except Exception:
        return 0
    return sum(1 for m in data if m.get("year") == year)


def advance_years(
    years: list[int],
    *,
    do_c10: bool,
    force_a2: bool,
    force_b6: bool,
    force_b6b: bool,
) -> int:
    refresh_years(years)
    data = load_manifest()
    ymap = data.get("years") or {}
    rc_worst = 0

    for year in years:
        entry = dict(ymap.get(str(year)) or {})
        if not entry.get("a1_complete"):
            log(f"y={year} skip — A1 not complete ({entry.get('a1_done')}/{entry.get('a1_jobs')})")
            continue

        need_a2 = force_a2 or not a2_csv_fresh(year) or entry.get("a2") != "done"
        if need_a2:
            rc = run_cmd([PY, "-u", str(ROOT / "assess_ocr_baseline_a2_gate.py"), "--years", str(year)])
            if rc:
                rc_worst = rc
            data = load_manifest()
            entry = dict((data.get("years") or {}).get(str(year)) or {})
        else:
            log(f"y={year} A2 already done (unlock={entry.get('a2_unlocked')})")

        if not entry.get("a2_unlocked"):
            log(f"y={year} blocked — A2 not unlocked (fail={entry.get('a2_fail')})")
            continue

        need_b6 = force_b6 or entry.get("b6") != "done"
        if need_b6:
            rc = run_cmd(
                [PY, "-u", str(ROOT / "harvest_cert_sections_v2.py"), "--years", str(year)]
            )
            if rc:
                rc_worst = rc
                log(f"y={year} B6 harvest rc={rc}")
            else:
                n = count_index_sections(year)
                mark_b6(year, n)
                log(f"y={year} B6 done sections={n}")
        else:
            log(f"y={year} B6 already done sections={entry.get('b6_sections')}")

        need_b6b = force_b6b or entry.get("b6b") != "done"
        if need_b6b:
            rc = run_cmd(
                [
                    PY,
                    "-u",
                    str(ROOT / "assess_ingest_quality_audit.py"),
                    "--years",
                    str(year),
                ]
            )
            data = load_manifest()
            entry = dict((data.get("years") or {}).get(str(year)) or {})
            log(
                f"y={year} B6b verdict={entry.get('b6b_verdict')} "
                f"unlock={entry.get('b6b_unlocked')} rc={rc}"
            )
            if rc:
                rc_worst = rc
        else:
            log(
                f"y={year} B6b already done verdict={entry.get('b6b_verdict')} "
                f"unlock={entry.get('b6b_unlocked')}"
            )

        if do_c10:
            if entry.get("b6b_unlocked") is False:
                log(f"y={year} skip C10 — B6b not unlocked")
            else:
                advance_c10_year(year)

    refresh_years(years)
    log("advance complete")
    return rc_worst


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument(
        "--years",
        nargs="+",
        default=["1997", "1998"],
        help="Years or ranges (e.g. 1997 1998 or 1997-2001)",
    )
    ap.add_argument(
        "--advance-c10",
        action="store_true",
        help="Stage HQ texts into _ocr_baseline_v2/trial_results_norm/{year}/ (no SQL)",
    )
    ap.add_argument("--force-a2", action="store_true", help="Re-run A2 even if CSV exists")
    ap.add_argument("--force-b6", action="store_true", help="Re-run B6 even if marked done")
    ap.add_argument("--force-b6b", action="store_true", help="Re-run B6b ingest audit even if done")
    args = ap.parse_args()
    years = parse_year_args(list(args.years))
    log(f"advance years={years} c10={args.advance_c10}")
    return advance_years(
        years,
        do_c10=args.advance_c10,
        force_a2=args.force_a2,
        force_b6=args.force_b6,
        force_b6b=args.force_b6b,
    )


if __name__ == "__main__":
    raise SystemExit(main())
