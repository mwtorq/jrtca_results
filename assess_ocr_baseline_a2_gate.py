#!/usr/bin/env python3
"""A2 quality gate for ``_ocr_baseline_v2`` HQ OCR text.

Scores each ``*_ocr_hqmax.txt`` for place/owned-by density and residual audit
codes from ``audit_results_ocr_page``. Writes per-year checklist CSV/MD plus a
combined rollup so gating one year does not wipe another.

Unlock rule: FAIL=0 → year unlocked for B6 even if WARN>0.

Usage:
  python -u assess_ocr_baseline_a2_gate.py
  python -u assess_ocr_baseline_a2_gate.py --years 1997 1998
"""
from __future__ import annotations

import argparse
import csv
import json
import re
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path

from yearbook_ocr import audit_results_ocr_page, finalize_results_ocr

ROOT = Path(r"c:\Users\mw\OneDrive - timberwilde.net\repos\jrtca_results")
BASE = ROOT / "_ocr_baseline_v2" / "yearbook_1990_2001"
OUT_CSV = ROOT / "_a2_quality_gate.csv"
OUT_MD = ROOT / "_a2_quality_gate.md"
MANIFEST = ROOT / "_pipeline_year_manifest.json"

# Soft thresholds for a volume-level pass (tune after first gate run)
MIN_OWNED_BY_PER_10K = 8
MIN_PLACE_PER_10K = 12
MAX_AUDIT_HITS_PER_10K = 25
FAIL_CODES = {
    "class_header_gap",
    "place_smash",
    "height_bare2",
    "height_pct",
    "height_4slash2",
    "height_101212",
}


def year_from_path(p: Path) -> int | None:
    for part in p.parts:
        if part.isdigit() and 1980 <= int(part) <= 2035:
            return int(part)
    return None


def score_text(text: str) -> dict:
    n = max(1, len(text))
    owned = len(re.findall(r"(?i)\bowned\s+by\b", text))
    place = len(re.findall(r"(?i)\b(?:1st|2nd|3rd|4th|5th|6th)\s*:", text))
    entries = len(re.findall(r"(?i)\bentries\s*:\s*\d+", text))
    bare_ent = len(re.findall(r"(?i)\bentries\s*:\s*$", text, flags=re.M))
    missing_ph = len(re.findall(r"(?i)\[missing class header\]", text))
    sample = text
    if len(text) > 140_000:
        sample = text[:80_000] + "\n" + text[-40_000:]
    hits = audit_results_ocr_page(finalize_results_ocr(sample), max_samples=8)
    codes = Counter(c for c, _ in hits)
    fail_hits = sum(codes[c] for c in FAIL_CODES if c in codes)
    per_10k = 10_000 / n
    return {
        "chars": n,
        "owned_by": owned,
        "place": place,
        "entries_n": entries,
        "bare_entries": bare_ent,
        "missing_placeholder": missing_ph,
        "owned_per_10k": round(owned * per_10k, 2),
        "place_per_10k": round(place * per_10k, 2),
        "audit_hits": len(hits),
        "audit_per_10k": round(len(hits) * per_10k, 2),
        "fail_code_hits": fail_hits,
        "top_codes": ",".join(f"{c}×{n}" for c, n in codes.most_common(6)),
    }


def verdict(row: dict) -> str:
    reasons: list[str] = []
    if row["chars"] < 500:
        return "FAIL:too_small"
    if row["owned_per_10k"] < MIN_OWNED_BY_PER_10K and row["place_per_10k"] < MIN_PLACE_PER_10K:
        reasons.append("sparse_results")
    if row["audit_per_10k"] > MAX_AUDIT_HITS_PER_10K:
        reasons.append("audit_dense")
    if row["fail_code_hits"] >= 4:
        reasons.append("fail_codes")
    if row["missing_placeholder"] > 0:
        reasons.append("placeholder")
    if row["bare_entries"] > max(3, row["entries_n"] // 5):
        reasons.append("bare_entries")
    if not reasons:
        return "PASS"
    if "sparse_results" in reasons or "placeholder" in reasons:
        return "FAIL:" + "+".join(reasons)
    return "WARN:" + "+".join(reasons)


def _now() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def year_paths(year: int) -> tuple[Path, Path]:
    return (
        ROOT / f"_a2_quality_gate_{year}.csv",
        ROOT / f"_a2_quality_gate_{year}.md",
    )


def write_year_md(year: int, rows: list[dict], path: Path) -> tuple[int, int, int]:
    passes = sum(1 for r in rows if r["verdict"] == "PASS")
    warns = sum(1 for r in rows if str(r["verdict"]).startswith("WARN"))
    fails = sum(1 for r in rows if str(r["verdict"]).startswith("FAIL"))
    unlocked = fails == 0 and len(rows) > 0
    lines = [
        f"# A2 quality gate — {year}",
        "",
        f"Volumes scored: {len(rows)}  PASS={passes}  WARN={warns}  FAIL={fails}",
        f"B6 unlock (FAIL=0): {'YES' if unlocked else 'NO'}",
        "",
        "## Thresholds",
        f"- owned_by per 10k chars ≥ {MIN_OWNED_BY_PER_10K} (or place ≥ {MIN_PLACE_PER_10K})",
        f"- audit hits per 10k ≤ {MAX_AUDIT_HITS_PER_10K}",
        f"- fail-code hits (class_header_gap/smash/heights) < 4 on sample",
        "- no `[missing class header]` placeholders",
        "- bare `Entries:` not excessive vs counted Entries",
        "",
        "## Per volume",
        "",
        "| Year | Verdict | Owned/10k | Place/10k | Audit/10k | Top codes | File |",
        "|------|---------|-----------|-----------|-----------|-----------|------|",
    ]
    for r in rows:
        lines.append(
            f"| {r['year']} | {r['verdict']} | {r['owned_per_10k']} | "
            f"{r['place_per_10k']} | {r['audit_per_10k']} | {r['top_codes'] or '—'} | "
            f"`{Path(r['file']).name}` |"
        )
    lines.extend(
        [
            "",
            "## Next",
            "- FAIL → A3 targeted fix + `--force` re-OCR that PDF only",
            "- WARN → proceed B6 for this year; spot-check residual codes",
            "- PASS/WARN with FAIL=0 → year-pipelined B6 (do not wait for other years)",
            "",
            f"CSV: `_a2_quality_gate_{year}.csv`",
        ]
    )
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")
    return passes, warns, fails


def write_csv(path: Path, rows: list[dict]) -> None:
    with path.open("w", encoding="utf-8", newline="") as f:
        if not rows:
            return
        w = csv.DictWriter(f, fieldnames=list(rows[0].keys()))
        w.writeheader()
        w.writerows(rows)


def load_year_csv(year: int) -> list[dict]:
    csv_path, _ = year_paths(year)
    if not csv_path.is_file():
        return []
    with csv_path.open(encoding="utf-8", newline="") as f:
        return list(csv.DictReader(f))


def rebuild_rollup() -> list[dict]:
    """Merge all per-year CSVs into combined rollup artifacts."""
    rows: list[dict] = []
    for csv_path in sorted(ROOT.glob("_a2_quality_gate_*.csv")):
        name = csv_path.stem  # _a2_quality_gate_1997
        if not name.startswith("_a2_quality_gate_"):
            continue
        suffix = name[len("_a2_quality_gate_") :]
        if not suffix.isdigit():
            continue
        with csv_path.open(encoding="utf-8", newline="") as f:
            for row in csv.DictReader(f):
                # normalize numeric fields that may be strings
                for k in (
                    "year",
                    "chars",
                    "owned_by",
                    "place",
                    "entries_n",
                    "bare_entries",
                    "missing_placeholder",
                    "audit_hits",
                    "fail_code_hits",
                ):
                    if k in row and row[k] != "":
                        try:
                            row[k] = int(float(row[k]))
                        except ValueError:
                            pass
                for k in ("owned_per_10k", "place_per_10k", "audit_per_10k"):
                    if k in row and row[k] != "":
                        try:
                            row[k] = float(row[k])
                        except ValueError:
                            pass
                rows.append(row)
    rows.sort(key=lambda r: (int(r.get("year") or 0), str(r.get("file") or "")))
    write_csv(OUT_CSV, rows)
    years = sorted({int(r["year"]) for r in rows if r.get("year") is not None})
    passes = sum(1 for r in rows if r.get("verdict") == "PASS")
    warns = sum(1 for r in rows if str(r.get("verdict", "")).startswith("WARN"))
    fails = sum(1 for r in rows if str(r.get("verdict", "")).startswith("FAIL"))
    lines = [
        "# A2 quality gate — OCR baseline v2 (rollup)",
        "",
        f"Years: {', '.join(str(y) for y in years) if years else '(none)'}",
        f"Volumes scored: {len(rows)}  PASS={passes}  WARN={warns}  FAIL={fails}",
        "",
        "Per-year details: `_a2_quality_gate_{year}.md`",
        "",
        "## Unlock doctrine (1997–2001 remediation)",
        "- FAIL=0 for a year → unlock B6 for that year (WARN OK).",
        "- Do not wait for all of 1999–2001 before advancing completed years.",
        "",
        "## Per volume",
        "",
        "| Year | Verdict | Owned/10k | Place/10k | Audit/10k | Top codes | File |",
        "|------|---------|-----------|-----------|-----------|-----------|------|",
    ]
    for r in rows:
        lines.append(
            f"| {r.get('year')} | {r.get('verdict')} | {r.get('owned_per_10k')} | "
            f"{r.get('place_per_10k')} | {r.get('audit_per_10k')} | {r.get('top_codes') or '—'} | "
            f"`{Path(str(r.get('file') or '')).name}` |"
        )
    lines.extend(["", f"CSV: `{OUT_CSV.name}`"])
    OUT_MD.write_text("\n".join(lines) + "\n", encoding="utf-8")
    return rows


def update_manifest_a2(
    year: int, passes: int, warns: int, fails: int, fail_vols: list[str]
) -> None:
    data = {"updated": None, "years": {}}
    if MANIFEST.is_file():
        try:
            data = json.loads(MANIFEST.read_text(encoding="utf-8"))
        except Exception:
            pass
    ymap = dict(data.get("years") or {})
    key = str(year)
    entry = dict(ymap.get(key) or {})
    unlocked = fails == 0 and (passes + warns + fails) > 0
    entry["a2"] = "done"
    entry["a2_pass"] = passes
    entry["a2_warn"] = warns
    entry["a2_fail"] = fails
    entry["a2_unlocked"] = unlocked
    entry["a3"] = "pending" if fails else "n/a"
    entry["a3_fail_vols"] = fail_vols
    ts = dict(entry.get("timestamps") or {})
    ts["a2_done"] = _now()
    entry["timestamps"] = ts
    ymap[key] = entry
    data["years"] = ymap
    data["updated"] = _now()
    MANIFEST.write_text(json.dumps(data, indent=2) + "\n", encoding="utf-8")


def gate_years(years: list[int]) -> int:
    any_fail = False
    for year in sorted(years):
        rows: list[dict] = []
        for hq in sorted(BASE.rglob("*_ocr_hqmax.txt")):
            y = year_from_path(hq)
            if y != year:
                continue
            text = hq.read_text(encoding="utf-8", errors="ignore")
            sc = score_text(text)
            row = {"year": year, "file": str(hq.relative_to(ROOT)), **sc}
            row["verdict"] = verdict(row)
            rows.append(row)
        rows.sort(key=lambda r: r["file"])
        csv_path, md_path = year_paths(year)
        write_csv(csv_path, rows)
        passes, warns, fails = write_year_md(year, rows, md_path)
        fail_vols = [
            Path(r["file"]).name
            for r in rows
            if str(r["verdict"]).startswith("FAIL")
        ]
        update_manifest_a2(year, passes, warns, fails, fail_vols)
        unlocked = fails == 0 and len(rows) > 0
        print(
            f"A2 y={year} vols={len(rows)} PASS={passes} WARN={warns} FAIL={fails} "
            f"unlock={unlocked} -> {md_path.name}",
            flush=True,
        )
        for r in rows:
            print(
                f"  {r['verdict']:20} {Path(r['file']).name} "
                f"owned/10k={r['owned_per_10k']} audit/10k={r['audit_per_10k']} "
                f"{r['top_codes']}",
                flush=True,
            )
        if fails:
            any_fail = True
    rebuild_rollup()
    print(f"Rollup -> {OUT_MD.name}, {OUT_CSV.name}", flush=True)
    return 1 if any_fail else 0


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument(
        "--years",
        type=int,
        nargs="*",
        default=[1997, 1998],
        help="Years to gate (default 1997 1998)",
    )
    ap.add_argument(
        "--rollup-only",
        action="store_true",
        help="Only rebuild combined rollup from per-year CSVs",
    )
    args = ap.parse_args()
    if args.rollup_only:
        rebuild_rollup()
        print(f"Rollup -> {OUT_MD.name}, {OUT_CSV.name}", flush=True)
        return 0
    return gate_years(list(args.years))


if __name__ == "__main__":
    raise SystemExit(main())
