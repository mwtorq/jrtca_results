#!/usr/bin/env python3
"""B6b — catalog cleanup + ingest quality audit (prefer cleanup over re-OCR).

Applies ``finalize_results_ocr`` (and catalog lessons already in finalize) to HQ
baseline text, **writes cleaned text back**, then audits residuals against
``_OCR_CLEANUP_CATALOG_HANDOFF.md``.

Intent: scrub OCR issues we already know how to fix so SQL ingest sees cleaner
text — **do not re-OCR** unless cleanup cannot clear FAIL defects.

Policy (2026-11-08 — user; FAIL set expanded 2026-11-13):
  - FAIL (blocks unlock / ``--apply``): smash, placeholders, height/place garble,
    **owner_tail_trunc (O6)**, **class_header_gap (C1)**, **missing_owned_by**,
    **orphan_entry_count**, **bare_entries**, **mangled_by**, **cutoff_racing**,
    **4th_then_2nd**, **4th_then_6th_no_5**, and other catalog residuals after cleanup.
  - Re-OCR: any FAIL class that finalize cannot invent (O6 right-edge cutoff, C1
    missing titles, residual smash/height) must be queued for force/targeted re-OCR.
    Structural S4/O / C6 / place-order FAILs are cleared in text (no invented surnames).
  - Handler ``handled by`` / ``handling`` lines are not scored as mangled_by / missing_owned_by.

Usage:
  python -u assess_ingest_quality_audit.py --years 1997 1998
  python -u assess_ingest_quality_audit.py --years 1998 --dry-run
"""
from __future__ import annotations

import argparse
import csv
import json
import re
import shutil
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path

from yearbook_ocr import audit_results_ocr_page, finalize_results_ocr

ROOT = Path(r"c:\Users\mw\OneDrive - timberwilde.net\repos\jrtca_results")
BASE = ROOT / "_ocr_baseline_v2" / "yearbook_1990_2001"
MANIFEST = ROOT / "_pipeline_year_manifest.json"
CATALOG = "_OCR_CLEANUP_CATALOG_HANDOFF.md"

CODE_TO_CATALOG: dict[str, str] = {
    "height_pct": "H1",
    "height_4slash2": "H2",
    "height_40_42": "H3",
    "height_101212": "H4",
    "height_bare2": "H5",
    "height_glued": "H6",
    "height_trunc_paren": "H7",
    "champ_abbrev": "H8",
    "place_ond": "P1",
    "place_ith": "P1",
    "place_rank_dust": "P2",
    "dup_place": "P2",
    "place_bang": "P3",
    "place_dnd": "P7",
    "place_3id": "P7",
    "place_9nd": "P7",
    "place_dst": "P7",
    "place_14st": "P7",
    "place_and": "P7",
    "place_smash": "S1-S3",
    "mangled_by": "S4",
    "missing_owned_by": "S4/O",
    "owend_by": "O5",
    "class_header_gap": "C1",
    "two_column_smash": "S1-S3",
    "post_page_missing_header": "C1",
    "incomplete_entries": "C1/C6",
    "midclass_page_dropout": "C1",
    "best_reserve_missing_header": "C7",
    "trial_bleed": "C5",
    "bare_entries": "C6/O1",
    "orphan_entry_count": "C6",
    "champ_reserve_split": "C7",
    "entriess": "O1",
    "cert_entries_glue": "C6",
    "owner_tail_trunc": "O6",
    "agility_pipe": "G4",
    "judges_junk": "G5",
    "juqges": "G5",
    "juages": "G5",
    "vog_fups": "G2",
    "placeholder": "C1",
}

FAIL_CODES = {
    "place_smash",
    "placeholder",
    "height_pct",
    "height_4slash2",
    "height_101212",
    "height_bare2",
    "height_40_42",
    "height_glued",
    "height_trunc_paren",
    "place_ond",
    "place_ith",
    "place_bang",
    "place_rank_dust",
    "owend_by",
    "champ_abbrev",
    # User paste / catalog — must FAIL and schedule re-OCR (not inventable)
    "owner_tail_trunc",
    "class_header_gap",
    "two_column_smash",
    "two_column_smash",
    "post_page_missing_header",
    "incomplete_entries",
    "midclass_page_dropout",
    "best_reserve_missing_header",
    # Former WARN-tier residuals — now FAIL; must clear before SQL apply (2026-11-13)
    "missing_owned_by",
    "orphan_entry_count",
    "bare_entries",
    "mangled_by",
    "cutoff_racing",
    "4th_then_2nd",
    "4th_then_6th_no_5",
}

# Codes that require image re-OCR / targeted recover (not finalize-only)
REOCR_CODES = {
    "owner_tail_trunc",
    "class_header_gap",
    "two_column_smash",
    "placeholder",
    "place_smash",
    "height_pct",
    "height_4slash2",
    "height_101212",
    "height_bare2",
    "height_40_42",
    "height_glued",
    "height_trunc_paren",
    "incomplete_entries",
    "midclass_page_dropout",
    "best_reserve_missing_header",
    "champ_abbrev",
}

PLACEHOLDER_RE = re.compile(r"(?i)\[missing class header\]")
HANDLED_BY_RE = re.compile(r"(?i)\bhandled\s+by\b|\bhandling\b")
_OWNER_UNKNOWN_RE = re.compile(r"(?i)\bowner\s+unknown\b")
_LAST_NAME_NOT_PROVIDED_RE = re.compile(r"(?i)\blast\s+name\s+not\s+provided\b")
_HANDLER_NOT_PROVIDED_RE = re.compile(r"(?i)\bhandler\s+not\s+provided\b")
_DISQUALIFIED_RE = re.compile(r"(?i)\bdisqualified\b")
_OWNER_NAMED_WITHOUT_OWNED_RE = re.compile(
    r"(?i),\s*owner\s+[A-Z]"  # "Terrier not provided, owner Pam Williams"
)


def _now() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def year_from_path(p: Path) -> int | None:
    for part in p.parts:
        if part.isdigit() and 1980 <= int(part) <= 2035:
            return int(part)
    return None


_NOT_PROVIDED_BY_RE = re.compile(
    r"(?i)\b(?:not\s+provided|owner\s+not\s+provided)\s+by\b|"
    r"\bprovided\s+by\s+(?:trial\s+)?(?:chair|chairman|chairperson)\b"
)
# Yearbook may omit "owned by" when the owner was not given; treat as intentional.
_OWNER_NOT_PROVIDED_RE = re.compile(
    r"(?i)\b(?:name\s+of\s+)?owner(?:\'s)?\s+(?:name\s+)?not\s+(?:provided|furnished|reported|available)\b"
)
_PROPER_OWNED_BY_RE = re.compile(r"(?i)\bowned\s+by\b")


def filter_handler_false_positives(
    hits: list[tuple[str, str]],
) -> list[tuple[str, str]]:
    """Drop known non-defect mangled_by / missing_owned_by hits."""
    out = []
    for code, line in hits:
        if code in ("mangled_by", "missing_owned_by") and HANDLED_BY_RE.search(line):
            continue
        if code == "mangled_by" and _NOT_PROVIDED_BY_RE.search(line):
            continue
        # Intentional yearbook wording, not an OCR defect
        if code == "missing_owned_by" and _OWNER_NOT_PROVIDED_RE.search(line):
            continue
        if code == "missing_owned_by" and (
            _OWNER_UNKNOWN_RE.search(line)
            or _LAST_NAME_NOT_PROVIDED_RE.search(line)
            or _HANDLER_NOT_PROVIDED_RE.search(line)
            or _DISQUALIFIED_RE.search(line)
            or _OWNER_NAMED_WITHOUT_OWNED_RE.search(line)
        ):
            continue
        # Dog name contains "… Bad by," but line also has a real owned-by clause
        if code == "mangled_by" and _PROPER_OWNED_BY_RE.search(line):
            continue
        # Lone high integers are page/cert noise, not class entry counts
        if code == "orphan_entry_count":
            try:
                if int(line.strip()) > 40:
                    continue
            except ValueError:
                pass
        out.append((code, line))
    return out


def extra_hits(text: str, *, max_samples: int = 20) -> list[tuple[str, str]]:
    hits: list[tuple[str, str]] = []
    n = 0
    for m in PLACEHOLDER_RE.finditer(text):
        start = text.rfind("\n", 0, m.start()) + 1
        end = text.find("\n", m.end())
        if end < 0:
            end = min(len(text), m.end() + 120)
        hits.append(("placeholder", text[start:end].strip()[:160]))
        n += 1
        if n >= max_samples:
            break
    return hits


def audit_cleaned(text: str, *, max_samples: int = 25) -> list[tuple[str, str]]:
    hits = list(audit_results_ocr_page(text, max_samples=max_samples))
    hits.extend(extra_hits(text, max_samples=max_samples))
    return filter_handler_false_positives(hits)


def classify(hits: list[tuple[str, str]]) -> tuple[str, Counter, Counter]:
    by_code: Counter = Counter(c for c, _ in hits)
    fail_codes = Counter({c: by_code[c] for c in FAIL_CODES if c in by_code})
    if fail_codes:
        return "FAIL", by_code, fail_codes
    if by_code:
        return "WARN", by_code, Counter()
    return "PASS", by_code, Counter()


def cleanup_file(path: Path, *, dry_run: bool, max_samples: int = 25) -> dict:
    raw = path.read_text(encoding="utf-8", errors="replace")
    cleaned = finalize_results_ocr(raw)
    changed = cleaned != raw
    backup = path.with_suffix(path.suffix + ".pre_b6b")
    if changed and not dry_run:
        if not backup.is_file():
            shutil.copy2(path, backup)
        path.write_text(cleaned, encoding="utf-8")
    hits = audit_cleaned(cleaned, max_samples=max_samples)
    verdict, by_code, fail_codes = classify(hits)
    catalog_hits: Counter = Counter()
    for c, n in by_code.items():
        catalog_hits[CODE_TO_CATALOG.get(c, f"?/{c}")] += n
    samples = []
    seen = set()
    for c, line in hits:
        key = (c, line[:60])
        if key in seen:
            continue
        seen.add(key)
        samples.append({"code": c, "catalog": CODE_TO_CATALOG.get(c, "?"), "line": line})
        if len(samples) >= 40:
            break
    rel = str(path.relative_to(ROOT)) if path.is_relative_to(ROOT) else str(path)
    reocr_codes = sorted(c for c in fail_codes if c in REOCR_CODES)
    return {
        "file": rel,
        "chars_before": len(raw),
        "chars_after": len(cleaned),
        "cleaned": changed,
        "verdict": verdict,
        "fail_hits": int(sum(fail_codes.values())),
        "warn_hits": int(sum(n for c, n in by_code.items() if c not in FAIL_CODES)),
        "top_codes": ",".join(f"{c}×{n}" for c, n in by_code.most_common(8)),
        "top_catalog": ",".join(f"{c}×{n}" for c, n in catalog_hits.most_common(8)),
        "by_code": dict(by_code),
        "samples": samples,
        "reocr_required": bool(reocr_codes),
        "reocr_codes": reocr_codes,
    }


def update_manifest(year: int, summary: dict) -> None:
    data = {"updated": None, "years": {}}
    if MANIFEST.is_file():
        try:
            data = json.loads(MANIFEST.read_text(encoding="utf-8"))
        except Exception:
            pass
    ymap = dict(data.get("years") or {})
    entry = dict(ymap.get(str(year)) or {})
    unlocked = summary["verdict"] != "FAIL"
    entry["b6b"] = "done"
    entry["b6b_verdict"] = summary["verdict"]
    entry["b6b_unlocked"] = unlocked
    entry["b6b_fail"] = summary["fail_vols"]
    entry["b6b_warn"] = summary["warn_vols"]
    entry["b6b_pass"] = summary["pass_vols"]
    entry["b6b_cleaned_vols"] = summary["cleaned_vols"]
    ts = dict(entry.get("timestamps") or {})
    ts["b6b_done"] = _now()
    entry["timestamps"] = ts
    ymap[str(year)] = entry
    data["years"] = ymap
    data["updated"] = _now()
    MANIFEST.write_text(json.dumps(data, indent=2) + "\n", encoding="utf-8")


def write_reports(year: int, rows: list[dict]) -> tuple[Path, Path]:
    csv_path = ROOT / f"_b6b_ingest_audit_{year}.csv"
    md_path = ROOT / f"_b6b_ingest_audit_{year}.md"
    flat = []
    for r in rows:
        flat.append(
            {
                "year": year,
                "file": r["file"],
                "cleaned": r["cleaned"],
                "chars_before": r["chars_before"],
                "chars_after": r["chars_after"],
                "verdict": r["verdict"],
                "fail_hits": r["fail_hits"],
                "warn_hits": r["warn_hits"],
                "top_codes": r["top_codes"],
                "top_catalog": r["top_catalog"],
            }
        )
    with csv_path.open("w", encoding="utf-8", newline="") as f:
        if flat:
            w = csv.DictWriter(f, fieldnames=list(flat[0].keys()))
            w.writeheader()
            w.writerows(flat)
    passes = sum(1 for r in rows if r["verdict"] == "PASS")
    warns = sum(1 for r in rows if r["verdict"] == "WARN")
    fails = sum(1 for r in rows if r["verdict"] == "FAIL")
    cleaned_vols = sum(1 for r in rows if r["cleaned"])
    year_verdict = "FAIL" if fails else ("WARN" if warns else "PASS")
    unlocked = year_verdict != "FAIL"
    lines = [
        f"# B6b cleanup + ingest audit — {year}",
        "",
        f"Catalog: `{CATALOG}`",
        f"Volumes: {len(rows)}  cleaned={cleaned_vols}  PASS={passes}  WARN={warns}  FAIL={fails}",
        f"Year verdict: **{year_verdict}**  SQL-apply unlock: {'YES' if unlocked else 'NO'}",
        "",
        "## Intent",
        "- Apply finalize/catalog cleanups to stored HQ text (backup `*.pre_b6b`).",
        "- Re-OCR only if FAIL remains after cleanup — not as the default path.",
        "",
        "## Policy",
        "- FAIL (blocks apply/unlock): smash, height/place, O6, C1, placeholders, **missing_owned_by**, **orphan_entry_count**, **bare_entries**, **mangled_by**, **cutoff_racing**, **4th_then_2nd**, **4th_then_6th_no_5**",
        "- Re-OCR queued when FAIL includes REOCR_CODES (O6/C1/smash/height) — structural S4/O/C6 cleared in text; do not invent surnames/titles",
        "- `handled by` / `handling` lines excluded from mangled_by / missing_owned_by",
        "",
        "## Per volume",
        "",
        "| Verdict | Cleaned | Fail | Warn | Catalog | File |",
        "|---------|---------|------|------|---------|------|",
    ]
    for r in rows:
        lines.append(
            f"| {r['verdict']} | {r['cleaned']} | {r['fail_hits']} | {r['warn_hits']} | "
            f"{r['top_catalog'] or '—'} | `{Path(r['file']).name}` |"
        )
    lines.extend(["", "## Sample residual hits (after cleanup)", ""])
    for r in rows:
        if not r["samples"]:
            continue
        lines.append(f"### `{Path(r['file']).name}` ({r['verdict']})")
        for s in r["samples"][:12]:
            lines.append(f"- `{s['catalog']}` / `{s['code']}`: {s['line']}")
        lines.append("")
    md_path.write_text("\n".join(lines).rstrip() + "\n", encoding="utf-8")
    update_manifest(
        year,
        {
            "verdict": year_verdict,
            "pass_vols": passes,
            "warn_vols": warns,
            "fail_vols": fails,
            "cleaned_vols": cleaned_vols,
        },
    )
    (ROOT / f"_b6b_ingest_audit_{year}.json").write_text(
        json.dumps({"year": year, "verdict": year_verdict, "volumes": rows}, indent=2),
        encoding="utf-8",
    )
    return csv_path, md_path


def collect_paths(years: list[int], extra: list[Path]) -> dict[int, list[Path]]:
    by_year: dict[int, list[Path]] = {y: [] for y in years}
    for y in years:
        ydir = BASE / str(y)
        if ydir.is_dir():
            by_year[y].extend(sorted(ydir.rglob("*_ocr_hqmax.txt")))
    for p in extra:
        y = year_from_path(p)
        if y is None:
            y = years[0] if len(years) == 1 else 0
        by_year.setdefault(y, []).append(p)
    return by_year


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--years", type=int, nargs="*", default=[1997, 1998])
    ap.add_argument("--path", type=Path, action="append", default=[])
    ap.add_argument("--max-samples", type=int, default=25)
    ap.add_argument(
        "--dry-run",
        action="store_true",
        help="Finalize+audit in memory only; do not write cleaned HQ text",
    )
    args = ap.parse_args()
    years = list(args.years) or [1997, 1998]
    by_year = collect_paths(years, list(args.path))
    any_fail = False
    reocr_queue: list[dict] = []
    for year in sorted(by_year):
        paths = by_year[year]
        if not paths:
            print(f"B6b y={year} no files", flush=True)
            continue
        rows = []
        for p in paths:
            print(f"B6b cleanup+audit {p.name} …", flush=True)
            rows.append(
                cleanup_file(p, dry_run=args.dry_run, max_samples=args.max_samples)
            )
        _csv, md_path = write_reports(year, rows)
        fails = sum(1 for r in rows if r["verdict"] == "FAIL")
        warns = sum(1 for r in rows if r["verdict"] == "WARN")
        passes = sum(1 for r in rows if r["verdict"] == "PASS")
        cleaned = sum(1 for r in rows if r["cleaned"])
        print(
            f"B6b y={year} cleaned={cleaned} PASS={passes} WARN={warns} FAIL={fails} "
            f"-> {md_path.name}",
            flush=True,
        )
        for r in rows:
            if r.get("reocr_required"):
                reocr_queue.append(
                    {
                        "year": year,
                        "hqmax": r["file"],
                        "codes": r.get("reocr_codes") or [],
                        "fail_hits": r.get("fail_hits"),
                        "top_catalog": r.get("top_catalog"),
                        "reason": "B6b FAIL after finalize — re-OCR required",
                    }
                )
        if fails:
            any_fail = True
    # Refresh queue for audited years: drop prior entries for those years, keep others,
    # then add any new FAIL-driven re-OCR rows (cleared years leave the queue).
    audited_years = set(years)
    qpath = ROOT / "_reocr_queue.json"
    prior: list[dict] = []
    if qpath.is_file():
        try:
            prior = json.loads(qpath.read_text(encoding="utf-8"))
            if not isinstance(prior, list):
                prior = []
        except Exception:
            prior = []
    kept = [
        e
        for e in prior
        if isinstance(e, dict) and e.get("year") not in audited_years
    ]
    by_hq = {e.get("hqmax"): e for e in kept if e.get("hqmax")}
    for e in reocr_queue:
        by_hq[e["hqmax"]] = e
    merged = list(by_hq.values())
    qpath.write_text(json.dumps(merged, indent=2) + "\n", encoding="utf-8")
    print(
        f"Re-OCR queue refreshed: {len(merged)} vols "
        f"(audited years {sorted(audited_years)}; new FAIL={len(reocr_queue)}) "
        f"-> {qpath.name}",
        flush=True,
    )
    return 1 if any_fail else 0


if __name__ == "__main__":
    raise SystemExit(main())
