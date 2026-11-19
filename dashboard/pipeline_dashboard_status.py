#!/usr/bin/env python3
"""Gather A1–D17 (+B6b) pipeline status into _pipeline_dashboard_status.json."""

from __future__ import annotations

import json
import os
import re
import tempfile
from datetime import datetime, timezone
from pathlib import Path
from zoneinfo import ZoneInfo

# Dashboard display zone (short CST/CDT — not Windows long tz names)
_DASH_TZ = ZoneInfo("America/Chicago")

# This module lives in repo/dashboard/; pipeline artifacts stay at repo root.
DASHBOARD_DIR = Path(__file__).resolve().parent
ROOT = DASHBOARD_DIR.parent
OUT = DASHBOARD_DIR / "_pipeline_dashboard_status.json"
MANIFEST = ROOT / "_pipeline_year_manifest.json"
HANDOFF = ROOT / "_plan_a1_d17_handoff.md"
A2_ROLLUP = ROOT / "_a2_quality_gate.md"
OCR_BASE = ROOT / "_ocr_baseline_v2" / "yearbook_1990_2001"
OCR_V2 = ROOT / "_ocr_baseline_v2"
YEARS = ("1997", "1998", "1999", "2000", "2001")
YEARS_9096 = ("1990", "1991", "1992", "1993", "1994", "1995", "1996")
YEARS_EARLY = ("1984", "1985", "1986", "1987", "1988", "1989", "1990")
# Full B6b table span (parked early years show as pending / no audit yet)
YEARS_B6B_ALL = tuple(str(y) for y in range(1984, 2002))
# Active yearbook strip shown as live year cards (eras + years_summary)
YEARS_ACTIVE = YEARS_9096 + YEARS

# Former WARN residuals demoted to FAIL (must clear before SQL apply).
B6B_DEMOTED_TO_FAIL = (
    "missing_owned_by",
    "orphan_entry_count",
    "bare_entries",
    "mangled_by",
    "cutoff_racing",
    "4th_then_2nd",
    "4th_then_6th_no_5",
)
# Detector-widen FAIL codes (page/header/dropout coverage).
B6B_DETECTOR_WIDEN = (
    "incomplete_entries",
    "midclass_page_dropout",
    "best_reserve_missing_header",
    "post_page_missing_header",
    "champ_abbrev",
    "class_header_gap",
    "two_column_smash",
    "owner_tail_trunc",
)

STEP_META = [
    ("A1", "Force HQ re-OCR 1997–2001 into baseline v2", ["1997", "1998", "1999", "2000", "2001"]),
    ("A2", "Quality gate on baseline samples", ["1997", "1998", "1999", "2000", "2001"]),
    ("A3", "Targeted fix + re-OCR bad volumes", ["1997", "1998", "1999", "2000", "2001"]),
    ("A4", "HQ baseline 1990–96 yearbook volumes", ["1990", "1991", "1992", "1993", "1994", "1995", "1996"]),
    ("A5", "HQ OCR 1984–90 non-yearbook (early packs)", ["1984", "1985", "1986", "1987", "1988", "1989", "1990"]),
    ("B6", "Re-harvest cert sections from baseline v2", ["1997", "1998", "1999", "2000", "2001"]),
    ("B6b", "Catalog cleanup + ingest audit gate", [
        "1990", "1991", "1992", "1993", "1994", "1995", "1996",
        "1997", "1998", "1999", "2000", "2001",
    ]),
    ("B7", "Tighten NHC + TrialCertificates parsers", []),
    ("B8", "Ingest NHC / TrialCertificates with Dog links", []),
    ("B9", "Spot-check certs; fix orphans", []),
    ("C10", "Normalize baseline to trial_results/", ["1997", "1998", "1999", "2000", "2001"]),
    ("C11", "Parse + validate sample trials 1990 / 1997 / 2001", ["1990", "1997", "2001"]),
    ("C12", "Full rebuild trial rows from baseline", ["1997", "1998", "1999", "2000", "2001"]),
    ("C13", "Rematch process_trial vs TrialList 1984–2001", []),
    ("C14", "Fill/correct 1984–1996 from baseline", ["1984", "1985", "1986", "1987", "1988", "1989", "1990", "1991", "1992", "1993", "1994", "1995", "1996"]),
    ("D15", "Yearbook Photos crop + caption", []),
    ("D16", "Final consistency pass", []),
    ("D17", "Handoff note PRIMARY vs REFERENCE", []),
]

STATUS_NORM = {
    "DONE": "DONE",
    "IN PROGRESS": "IN PROGRESS",
    "PENDING": "PENDING",
    "BLOCKED": "BLOCKED",
    "PARTIAL": "PARTIAL",
    "FAIL": "FAIL",
    "WARN": "WARN",
}

# Fallback How lines when handoff omits **How:** (keeps step cards OCR-complete).
STEP_HOW_FALLBACK = {
    "A3": "Fix yearbook_ocr.py / crop/PSM for A2 FAIL vols; ocr_yearbook_baseline_v2.py --force on failing PDFs only.",
    "A4": "Same as A1 for 1990–96: ocr_yearbook_baseline_v2.py --force --years 1990-1996 (parked while remediation strip runs).",
    "A5": "OCR EARLY / non-yearbook packs via yearbook_ocr.py into _ocr_baseline_v2 layout.",
    "B6": "harvest_cert_sections_v2.py --years YYYY → _ocr_baseline_v2/certs/; pipeline_advance_years.py after A2 unlock.",
    "B8": "yearbook_certs_ingest.py into SQL with Dog FK — only after B6b FAIL=0 on harvest corpus.",
    "B9": "SQL/manual orphan rematch on ingested certs; document residual orphans.",
    "C10": "pipeline_advance_years.py --advance-c10 → _ocr_baseline_v2/trial_results_norm/{year}/.",
    "C11": "Parse anchor years 1990/1997/2001; compare placement counts; B6b audit on samples.",
    "C12": "Rebuild TrialResults from norm text for unlocked years; attach per-year audit before --apply.",
    "C13": "remount_source_divisions.py / fill_from_parse.py vs TrialList 1984–2001.",
    "C14": "Prefer baseline OCR fills for 1984–1996 after A4/A5 + C12/C13.",
    "D15": "yearbook_extract_photos.py + map/cleanup/resplit helpers on Yearbook Photos.",
    "D16": "Cross-check dogs, certs, placements, photos, breeders; fix systematic mismatches.",
    "D17": "Write PRIMARY vs REFERENCE handoff note; freeze operating rules for next session.",
}


def _fmt_local(dt: datetime) -> str:
    """Format as ``YYYY-MM-DD HH:MM:SS CST`` / ``CDT`` (never long tz names)."""
    local = dt.astimezone(_DASH_TZ) if dt.tzinfo else dt.replace(tzinfo=timezone.utc).astimezone(_DASH_TZ)
    abbr = "CDT" if local.dst() else "CST"
    return local.strftime(f"%Y-%m-%d %H:%M:%S {abbr}")


def _now_iso() -> str:
    return _fmt_local(datetime.now(timezone.utc))


def _mtime_local(path: Path) -> str | None:
    try:
        return _fmt_local(datetime.fromtimestamp(path.stat().st_mtime, timezone.utc))
    except OSError:
        return None


def _iso_to_local(s: str | None) -> str | None:
    """Convert stored UTC ISO (…Z) or pass through already-local strings."""
    if not s:
        return None
    raw = str(s).strip()
    if not raw:
        return None
    # Strip Windows long names if mixed in
    raw = re.sub(r"\s*Central (?:Standard|Daylight) Time\b", "", raw, flags=re.I).strip()
    raw = re.sub(r"\s*GMT[+-]\d{1,2}(?::?\d{2})?\b", "", raw).strip()
    # Already local short form
    if re.search(r"\b(?:CST|CDT)\b", raw) and "T" not in raw:
        return raw
    try:
        if raw.endswith("Z"):
            dt = datetime.fromisoformat(raw.replace("Z", "+00:00"))
        else:
            dt = datetime.fromisoformat(raw)
            if dt.tzinfo is None:
                dt = dt.replace(tzinfo=timezone.utc)
        return _fmt_local(dt)
    except ValueError:
        # Last resort: force short abbrev if a bare datetime remains
        m = re.match(r"^(\d{4}-\d{2}-\d{2}[ T]\d{2}:\d{2}:\d{2})", raw)
        return f"{m.group(1).replace('T', ' ')} CST" if m else raw


def _line_utc_stamps_to_local(line: str) -> str:
    """Rewrite ``[2026-11-11T18:37:27Z]`` prefixes in log lines to CST/CDT."""
    if not line:
        return line

    def _repl(m: re.Match[str]) -> str:
        local = _iso_to_local(m.group(1))
        return f"[{local}]" if local else m.group(0)

    return re.sub(
        r"\[(\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}(?:\.\d+)?Z)\]",
        _repl,
        line,
    )


def _read_text(path: Path, max_bytes: int = 2_000_000) -> str:
    if not path.is_file():
        return ""
    try:
        data = path.read_bytes()[:max_bytes]
        return data.decode("utf-8", errors="replace")
    except OSError:
        return ""


def _tail_lines(path: Path, n: int = 400) -> list[str]:
    text = _read_text(path, max_bytes=800_000)
    if not text:
        return []
    lines = text.splitlines()
    return lines[-n:] if len(lines) > n else lines


def parse_handoff_statuses() -> dict[str, dict]:
    """Parse ### STEP — title blocks and **Status:** lines from handoff."""
    text = _read_text(HANDOFF)
    if not text and (ROOT / "_PLAN_A1_D17_HANDOFF.md").is_file():
        text = _read_text(ROOT / "_PLAN_A1_D17_HANDOFF.md")
    out: dict[str, dict] = {}
    # Match ### A1 — title  OR  ### B6b / ingest gate — title
    step_re = re.compile(
        r"^###\s+(A\d|B\d+b?|C\d+|D\d+)\b[^\n]*\n(.*?)(?=^###\s+(?:A\d|B\d+b?|C\d+|D\d+)\b|\Z)",
        re.MULTILINE | re.DOTALL,
    )
    status_re = re.compile(r"^\*\*Status:\*\*\s*(.+)$", re.MULTILINE)
    for m in step_re.finditer(text):
        sid = m.group(1)
        body = m.group(2)
        sm = status_re.search(body)
        raw = sm.group(1).strip() if sm else "PENDING"
        # Normalize leading status token (before paren / emdash)
        token = re.split(r"\s*[\(\u2014—\-]", raw, maxsplit=1)[0].strip().upper()
        # Map common variants
        if token.startswith("IN PROGRESS"):
            norm = "IN PROGRESS"
        elif token in STATUS_NORM:
            norm = STATUS_NORM[token]
        elif "BLOCK" in token:
            norm = "BLOCKED"
        elif "PARTIAL" in token:
            norm = "PARTIAL"
        elif "DONE" in token:
            norm = "DONE"
        elif "PENDING" in token:
            norm = "PENDING"
        else:
            norm = "PENDING"
        def _field(name: str) -> str | None:
            m = re.search(rf"^\*\*{name}:\*\*\s*(.+)$", body, re.MULTILINE)
            return m.group(1).strip() if m else None

        intent = _field("Intent")
        how = _field("How")
        exit_ = _field("Exit")
        snapshot = _field("Snapshot")
        done = _field("Done")
        remaining = _field("Remaining")
        # D15-style notes use Done/Remaining instead of Exit
        if not exit_ and remaining:
            exit_ = remaining
        detail_parts = [raw]
        if snapshot:
            detail_parts.append(snapshot)
        elif intent:
            detail_parts.append(intent[:220])
        out[sid] = {
            "status": norm,
            "detail": " — ".join(detail_parts),
            "intent": intent,
            "how": how,
            "exit": exit_,
            "snapshot": snapshot,
            "done": done,
            "remaining": remaining,
            "status_raw": raw,
        }
    return out


def _a2_detail_from_csv(year: str, *, max_vols: int = 12) -> dict:
    """Per-volume A2 gate rows from ``_a2_quality_gate_{year}.csv``."""
    path = ROOT / f"_a2_quality_gate_{year}.csv"
    out: dict = {
        "volumes": [],
        "unlock": None,
        "rollup": None,
        "path": path.name if path.is_file() else None,
    }
    md = ROOT / f"_a2_quality_gate_{year}.md"
    if md.is_file():
        for line in _read_text(md, max_bytes=40_000).splitlines()[:20]:
            if "Volumes scored" in line or "PASS=" in line:
                out["rollup"] = line.strip()
            if "B6 unlock" in line or "unlock" in line.lower():
                if "YES" in line.upper():
                    out["unlock"] = True
                elif "NO" in line.upper():
                    out["unlock"] = False
    if not path.is_file():
        return out
    try:
        import csv

        with path.open("r", encoding="utf-8", errors="replace", newline="") as f:
            reader = csv.DictReader(f)
            for i, row in enumerate(reader):
                if i >= max_vols:
                    break
                fpath = str(row.get("file") or "")
                short = Path(fpath).name if fpath else "?"
                out["volumes"].append(
                    {
                        "file": short,
                        "verdict": str(row.get("verdict") or ""),
                        "owned_per_10k": row.get("owned_per_10k"),
                        "place_per_10k": row.get("place_per_10k"),
                        "audit_per_10k": row.get("audit_per_10k"),
                        "fail_code_hits": row.get("fail_code_hits"),
                        "top_codes": str(row.get("top_codes") or ""),
                        "chars": row.get("chars"),
                    }
                )
    except OSError:
        pass
    return out


def load_manifest() -> dict:
    if not MANIFEST.is_file():
        return {"years": {}}
    try:
        return json.loads(MANIFEST.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return {"years": {}}


def count_hqmax(year: str) -> int:
    d = OCR_BASE / year
    if not d.is_dir():
        return 0
    n = 0
    try:
        # Layout: yearbook_1990_2001/{year}/{VolDir}/*_ocr_hqmax.txt (avoid deep OneDrive rglob)
        for vol in d.iterdir():
            if not vol.is_dir():
                continue
            for p in vol.glob("*_ocr_hqmax.txt"):
                n += 1
    except OSError:
        return n
    return n


def a2_rollup_summary() -> str:
    text = _read_text(A2_ROLLUP)
    if not text:
        return "no _a2_quality_gate.md"
    for line in text.splitlines()[:12]:
        if "PASS=" in line or "Volumes scored" in line:
            return line.strip()
    return "a2 rollup present"


def b6b_year_detail(year: str, yinfo: dict) -> str:
    path = ROOT / f"_b6b_ingest_audit_{year}.md"
    if path.is_file():
        for line in _read_text(path).splitlines()[:12]:
            if "Year verdict" in line or "Volumes:" in line:
                return line.strip()
    verdict = yinfo.get("b6b_verdict") or yinfo.get("b6b") or ""
    if verdict:
        return f"manifest b6b={yinfo.get('b6b')} verdict={verdict} unlocked={yinfo.get('b6b_unlocked')}"
    return ""


def parse_ocr_track(
    log_name: str,
    *,
    workers_cmdline: int | None = None,
    page_workers_cmdline: int | None = None,
    pids: list[int] | None = None,
    tess_live: int | None = None,
) -> dict:
    """Parse last OCR job + page from a track log (full paths; no short slice).

    Elapsed = wall clock (log birth → now/mtime). Do **not** divide by tess
    workers — that under-reports runtime by ~N× (e.g. 3h → 18 min at workers=10).
    PPM = pages_total / wall_minutes. ``worker_min`` is optional capacity metric
    (wall × workers).

    ``workers`` prefers live ``--workers`` from process cmdline over log text
    (logs often retain stale ``workers=`` from earlier runs).
    """
    path = ROOT / log_name
    job_index = None
    job_total = None
    year = None
    pdf_rel = None
    dest_rel = None
    page = None
    job_line_full = ""
    page_line_full = ""
    pages_total = 0
    pages_this_job = 0
    workers_log = None
    job_re = re.compile(r"OCR\s+(\d+)/(\d+)\s+y=(\d{4})\s+(.+)")
    page_re = re.compile(r"OCR page\s+(\d+)\b")
    workers_re = re.compile(r"\bworkers=(\d+)\b")
    # Job lines are sparse (often early in the log); page lines are dense near the end.
    # Stream the whole file for last job + page counts; tail window for last page display.
    if path.is_file():
        try:
            with path.open("r", encoding="utf-8", errors="replace") as f:
                for line in f:
                    wm = workers_re.search(line)
                    if wm:
                        # Keep *last* workers= (restarts append; first hit is stale).
                        workers_log = max(1, int(wm.group(1)))
                    jm = job_re.search(line)
                    if jm:
                        pages_this_job = 0
                        job_index = int(jm.group(1))
                        job_total = int(jm.group(2))
                        year = jm.group(3)
                        rest = jm.group(4).strip()
                        pdf_rel = None
                        dest_rel = None
                        if "->" in rest:
                            left, right = rest.split("->", 1)
                            pdf_rel = left.strip()
                            dest_rel = right.strip() or None
                        else:
                            pdf_rel = rest
                        if dest_rel:
                            job_line_full = (
                                f"OCR {job_index}/{job_total} y={year} "
                                f"{pdf_rel} -> {dest_rel}"
                            )
                        else:
                            job_line_full = (
                                f"OCR {job_index}/{job_total} y={year} {pdf_rel}"
                            )
                        continue
                    pm = page_re.search(line)
                    if pm:
                        pages_total += 1
                        pages_this_job += 1
                        page = int(pm.group(1))
                        page_line_full = f"OCR page {page}"
        except OSError:
            pass
    workers = _effective_workers(workers_cmdline, workers_log)
    if workers is None:
        workers = max(1, int(os.environ.get("JRTCA_OCR_WORKERS", "10")))
    if not page_line_full:
        for line in _tail_lines(path, 500):
            pm = page_re.search(line)
            if pm:
                page = int(pm.group(1))
                page_line_full = f"OCR page {page}"

    mtime = _mtime_local(path) if path.is_file() else None
    ppm = None
    ppm_job = None
    elapsed_min = None
    worker_min = None
    if path.is_file() and pages_total > 0:
        try:
            st = path.stat()
            # Prefer birth time (Windows st_ctime); fall back to mtime window
            start = getattr(st, "st_ctime", None) or st.st_mtime
            end = st.st_mtime
            import time as _time

            now = _time.time()
            # Actively writing → measure to now (running PPM)
            if now - end < 180:
                end = now
            # File birth→now is already wall clock (not tess-slot sum).
            elapsed_min = max((end - start) / 60.0, 0.01)
            worker_min = round(elapsed_min * max(workers, 1), 2)
            ppm = round(pages_total / elapsed_min, 2)
            # Current-job PPM ≈ session rate scaled by page share (no per-job timestamps)
            if pages_this_job > 0 and pages_total > 0:
                job_frac = pages_this_job / max(pages_total, 1)
                job_min = max(elapsed_min * job_frac, 0.01)
                ppm_job = round(pages_this_job / job_min, 2)
        except OSError:
            pass

    job_display = job_line_full or "(no OCR N/M line yet)"
    page_display = page_line_full or "(no OCR page line yet)"
    return {
        "log": log_name,
        "job": job_display,
        "page": page_display,
        "job_line_full": job_display,
        "page_line_full": page_display,
        "job_index": job_index,
        "job_total": job_total,
        "year": year,
        "pdf_rel": pdf_rel,
        "dest_rel": dest_rel,
        "page_num": page,
        "log_mtime": mtime,
        "exists": path.is_file(),
        "pages_total": pages_total,
        "pages_this_job": pages_this_job,
        "workers": workers,
        "workers_log": workers_log,
        "workers_cmdline": workers_cmdline,
        "page_workers": page_workers_cmdline,
        "pids": list(pids or []),
        "tess_live": tess_live,
        "ppm": ppm,
        "ppm_job": ppm_job,
        "elapsed_min": round(elapsed_min, 1) if elapsed_min is not None else None,
        "worker_min": round(worker_min, 1) if worker_min is not None else None,
    }


def _handoff_step_status(handoff: dict[str, dict], sid: str) -> tuple[str, str]:
    h = handoff.get(sid) or {}
    return str(h.get("status") or "PENDING"), str(h.get("detail") or "")


def _shallow_present(path: Path) -> dict:
    """Light existence check; top-level entry count only (no recursion)."""
    if not path.exists():
        return {"present": False, "top_entries": 0}
    if not path.is_dir():
        return {"present": True, "top_entries": 0, "is_file": True}
    n = 0
    try:
        for _ in path.iterdir():
            n += 1
    except OSError:
        pass
    return {"present": True, "top_entries": n}


def gather_eras(
    handoff: dict[str, dict],
    years_summary: dict[str, dict],
) -> dict:
    """Prep UI data for live 1997–2001 + 1990–96 B6b clears + parked A5."""
    a4_status, a4_detail = _handoff_step_status(handoff, "A4")
    a5_status, a5_detail = _handoff_step_status(handoff, "A5")

    y9096: dict[str, dict] = {}
    fail_yrs: list[str] = []
    for y in YEARS_9096:
        row = dict(years_summary.get(y) or {})
        hq = row.get("hqmax_count")
        if hq is None:
            hq = count_hqmax(y)
            row["hqmax_count"] = hq
        fail_n = int(row.get("b6b_fail") or 0)
        verd = str(row.get("b6b_verdict") or row.get("b6b") or "").upper()
        if fail_n > 0 or verd == "FAIL":
            y_status = "fail"
            fail_yrs.append(y)
        elif verd == "PASS" and row.get("b6b_unlocked"):
            y_status = "pass"
        elif verd in ("PASS", "WARN", "DONE") or (row.get("b6b_pass") or 0) > 0:
            y_status = "partial"
        elif hq and int(hq) > 0:
            y_status = "partial"
        elif a4_status.upper() in ("PENDING", "BLOCKED"):
            y_status = "parked"
        else:
            y_status = a4_status.lower().replace(" ", "_")
        row["year"] = y
        row["status"] = y_status
        y9096[y] = row

    era9096_status = "parked"
    if any(int(r.get("hqmax_count") or 0) > 0 for r in y9096.values()):
        era9096_status = "partial"
    if fail_yrs:
        era9096_status = "in_progress"
    elif a4_status.upper() == "IN PROGRESS":
        era9096_status = "in_progress"
    elif a4_status.upper() == "DONE" and not fail_yrs:
        era9096_status = "done"

    if fail_yrs:
        note_9096 = (
            f"B6b surgical / clear lane · FAIL years: {', '.join(fail_yrs)} "
            "(live audit F/W/P on year cards)."
        )
    else:
        note_9096 = (
            "1990–1996 yearbook · B6b live audit on year cards "
            "(not A4-parked-only placeholders)."
        )

    nonyb = _shallow_present(OCR_V2 / "nonyearbook_1984_1990")
    certs = _shallow_present(OCR_V2 / "certs")
    early_notes = [
        f"plan A5: {a5_status}",
        f"nonyearbook_1984_1990={'present' if nonyb.get('present') else 'absent'}"
        + (f" ({nonyb.get('top_entries')} top)" if nonyb.get("present") else ""),
        f"certs={'present' if certs.get('present') else 'absent'}"
        + (f" ({certs.get('top_entries')} top)" if certs.get("present") else ""),
    ]
    early_status = "parked"
    if a5_status.upper() == "IN PROGRESS":
        early_status = "in_progress"
    elif a5_status.upper() == "DONE":
        early_status = "done"
    elif nonyb.get("top_entries", 0) > 0:
        early_status = "partial"

    return {
        "remediation_1997_2001": {
            "label": "1997–2001 remediation",
            "status": "live",
            "note": "Active remediation strip with live B6b audit counts.",
            "years": {y: years_summary[y] for y in YEARS if y in years_summary},
        },
        "yearbook_1990_1996": {
            "label": "1990–1996 yearbook",
            "status": era9096_status,
            "plan_step": "A4/B6b",
            "plan_status": a4_status,
            "detail": a4_detail,
            "note": note_9096,
            "fail_years": fail_yrs,
            "years": y9096,
            "card_mode": "live",
        },
        "early_1984_1990": {
            "label": "1984–1990 early / non-yearbook",
            "status": early_status,
            "plan_step": "A5",
            "plan_status": a5_status,
            "detail": a5_detail,
            "note": "; ".join(early_notes),
            "years_keys": list(YEARS_EARLY),
            "paths": {
                "nonyearbook_1984_1990": nonyb,
                "certs": certs,
            },
        },
    }


def _win32_python_cmdlines(match_re: str, timeout: int = 10) -> list[dict]:
    """Shallow Win32 python process scan; never kill. Returns {pid, cmdline}."""
    out: list[dict] = []
    try:
        import subprocess

        # Emit pid|cmdline so years/scripts stay parseable without extra CIM round-trips.
        ps = (
            f"Get-CimInstance Win32_Process -Filter \"Name='python.exe'\" | "
            f"Where-Object {{ $_.CommandLine -match '{match_re}' }} | "
            "ForEach-Object { '{0}|{1}' -f $_.ProcessId, $_.CommandLine }"
        )
        r = subprocess.run(
            ["powershell", "-NoProfile", "-Command", ps],
            capture_output=True,
            text=True,
            timeout=timeout,
            cwd=str(ROOT),
        )
        for line in (r.stdout or "").splitlines():
            line = line.strip()
            if "|" not in line:
                continue
            pid_s, cmdline = line.split("|", 1)
            if pid_s.isdigit():
                out.append({"pid": int(pid_s), "cmdline": cmdline.strip()})
    except Exception:
        pass
    return out


def ocr_processes_alive() -> dict:
    """Optional: detect python OCR driver processes (Windows). Never kill."""
    rows = _win32_python_cmdlines(r"ocr_yearbook_baseline_v2|ocr_yearbook")
    pids = [r["pid"] for r in rows]
    return {"alive": bool(pids), "pids": pids, "rows": rows}


def _parse_years_from_cmdline(cmdline: str) -> list[int]:
    m = re.search(r"--years\s+((?:\d{4}\s*)+)", cmdline or "", re.I)
    if not m:
        return []
    return [int(x) for x in re.findall(r"\d{4}", m.group(1))]


def _workers_from_cmdline(cmdline: str) -> int | None:
    m = re.search(r"--workers\s+(\d+)", cmdline or "", re.I)
    if not m:
        return None
    try:
        return max(1, int(m.group(1)))
    except ValueError:
        return None


def _page_workers_from_cmdline(cmdline: str) -> int | None:
    m = re.search(r"--page-workers\s+(\d+)", cmdline or "", re.I)
    if not m:
        return None
    try:
        return max(1, int(m.group(1)))
    except ValueError:
        return None


def _tess_count_live() -> int:
    """Live tesseract.exe count (all tracks combined)."""
    try:
        import subprocess

        r = subprocess.run(
            [
                "powershell",
                "-NoProfile",
                "-Command",
                "(Get-Process tesseract -ErrorAction SilentlyContinue | Measure-Object).Count",
            ],
            capture_output=True,
            text=True,
            timeout=10,
        )
        tok = (r.stdout or "").strip().splitlines()
        if tok and tok[-1].isdigit():
            return int(tok[-1])
    except Exception:
        pass
    return 0


def _effective_workers(workers_cmdline: int | None, workers_log: int | None) -> int | None:
    """Prefer live process cmdline over log (log may retain stale workers= from prior runs)."""
    if workers_cmdline is not None:
        return workers_cmdline
    if workers_log is not None:
        return workers_log
    return None


def _classify_baseline_ocr_track(cmdline: str) -> str | None:
    """Map baseline OCR process to trackA/trackB via log path or years in cmdline."""
    cmd = cmdline or ""
    low = cmd.lower()
    if "tracka" in low or "_ocr_a4_tracka" in low or "_ocr_a5_tracka" in low or "_ocr_9701_tracka" in low:
        return "trackA"
    if "trackb" in low or "_ocr_a4_trackb" in low or "_ocr_a5_trackb" in low or "_ocr_9701_trackb" in low:
        return "trackB"
    years = set(_parse_years_from_cmdline(cmd))
    # Historical dual-track splits (non-overlapping)
    if years and years <= {1999, 2001}:
        return "trackA"
    if years and years <= {2000}:
        return "trackB"
    if years and years <= {1990, 1991, 1992, 1993, 1994, 1995, 1996, 1997, 1998, 1999, 2001}:
        # A4/A5 style: if track token absent, leave unclassified
        return None
    return None


def parse_c1o6_recover_log(log_name: str = "_recover_c1o6_9798.log") -> dict:
    """Parse recover_ocr_gaps_targeted stdout log (known path only)."""
    path = ROOT / log_name
    err_path = ROOT / log_name.replace(".log", ".err.log")
    year_re = re.compile(r"^===\s*y=(\d{4})\s+files=(\d+)\s*===")
    file_re = re.compile(r"^\s*(.+_ocr_hqmax\.txt):\s*recover pages")
    progress_re = re.compile(
        r"^PROGRESS\s+pages_done=(\d+)\s+pages_todo=(\d+)\s+pages_left=(\d+)"
        r"(?:\s+c1_done=(\d+)\s+c1_todo=(\d+)\s+o6_done=(\d+)\s+o6_todo=(\d+))?\s*$"
    )
    plan_re = re.compile(
        r"^PLAN\s+pages_todo=(\d+)(?:\s+c1_todo=(\d+)\s+o6_todo=(\d+))?"
    )
    file_need_re = re.compile(
        r"^\s*(.+_ocr_hqmax\.txt):\s*recover pages .+ \((\d+)\)"
        r"(?:\s+c1=(\d+)\s+o6=(\d+))?\s*$"
    )
    done_re = re.compile(
        r"^DONE\s+files=(\d+)\s+pages_c1_fixed=(\d+)\s+pages_o6_fixed=(\d+)"
    )
    # Timestamp + optional done/left + C1=a/b O6=c/d
    page_re = re.compile(
        r"^\s*(?:\[(?P<ts>\d{4}-\d{2}-\d{2}\s+\d{2}:\d{2}:\d{2}(?:\s+(?:CST|CDT))?)\]\s+)?"
        r"page\s+(?P<pno>\d+):\s*c1=(?P<c1>True|False)\s+o6=(?P<o6>True|False)"
        r"(?:\s+done=(?P<done>\d+)/(?P<todo>\d+)\s+left=(?P<left>\d+))?"
        r"(?:\s+C1=(?P<c1d>\d+)/(?P<c1t>\d+)\s+O6=(?P<o6d>\d+)/(?P<o6t>\d+))?\s*$"
    )

    current_year: str | None = None
    current_file: str | None = None
    pages_c1 = 0
    pages_o6 = 0
    page_lines: list[str] = []
    done: dict | None = None
    years_seen: list[str] = []
    pages_todo = 0
    pages_done = 0
    pages_left: int | None = None
    queued_need = 0
    c1_todo = 0
    o6_todo = 0
    c1_done_prog = 0
    o6_done_prog = 0
    plan_seen = False

    # Full read capped at 800KB (logs stay small; avoids undercounting via tail).
    for line in _read_text(path, max_bytes=800_000).splitlines():
        ym = year_re.match(line)
        if ym:
            current_year = ym.group(1)
            if current_year not in years_seen:
                years_seen.append(current_year)
            continue
        pl = plan_re.match(line.strip())
        if pl:
            plan_seen = True
            pages_todo = int(pl.group(1))
            if pl.group(2):
                c1_todo = int(pl.group(2))
                o6_todo = int(pl.group(3))
            continue
        fn = file_need_re.match(line)
        if fn:
            current_file = fn.group(1).strip()
            queued_need += int(fn.group(2))
            if fn.group(3) and not plan_seen:
                c1_todo += int(fn.group(3))
                o6_todo += int(fn.group(4))
            continue
        fm = file_re.match(line)
        if fm:
            current_file = fm.group(1).strip()
            continue
        pr = progress_re.match(line.strip())
        if pr:
            pages_done = int(pr.group(1))
            pages_todo = int(pr.group(2))
            pages_left = int(pr.group(3))
            if pr.group(4) is not None:
                c1_done_prog = int(pr.group(4))
                c1_todo = int(pr.group(5))
                o6_done_prog = int(pr.group(6))
                o6_todo = int(pr.group(7))
            continue
        pm = page_re.match(line)
        if pm:
            c1 = pm.group("c1") == "True"
            o6 = pm.group("o6") == "True"
            if c1:
                pages_c1 += 1
            if o6:
                pages_o6 += 1
            if pm.group("todo"):
                pages_todo = int(pm.group("todo"))
                pages_done = int(pm.group("done") or 0)
                pages_left = int(pm.group("left") or 0)
            if pm.group("c1t"):
                c1_done_prog = int(pm.group("c1d") or 0)
                c1_todo = int(pm.group("c1t") or 0)
                o6_done_prog = int(pm.group("o6d") or 0)
                o6_todo = int(pm.group("o6t") or 0)
            # Prefix with HQ file so recent lines stay unambiguous across volumes
            file_label = current_file or "?"
            if file_label.endswith("_ocr_hqmax.txt"):
                file_label = file_label[: -len("_ocr_hqmax.txt")]
            ts = pm.group("ts")
            ts_bit = f"{ts} · " if ts else ""
            prog = ""
            if pm.group("c1t"):
                prog = (
                    f" · C1 {pm.group('c1d')}/{pm.group('c1t')}"
                    f" O6 {pm.group('o6d')}/{pm.group('o6t')}"
                )
            elif pm.group("left") is not None:
                prog = f" · left {pm.group('left')}"
            page_lines.append(
                f"{ts_bit}{file_label} · page {pm.group('pno')}: "
                f"c1={pm.group('c1')} o6={pm.group('o6')}{prog}"
            )
            continue
        dm = done_re.match(line)
        if dm:
            done = {
                "files": int(dm.group(1)),
                "pages_c1_fixed": int(dm.group(2)),
                "pages_o6_fixed": int(dm.group(3)),
                "line": line.strip(),
            }
            pages_left = 0

    mtime = _mtime_local(path) if path.is_file() else None

    err_bytes = 0
    if err_path.is_file():
        try:
            err_bytes = err_path.stat().st_size
        except OSError:
            err_bytes = 0

    if pages_left is None and queued_need:
        pages_todo = queued_need
        pages_left = max(0, queued_need - pages_done)

    return {
        "log": log_name,
        "err_log": err_path.name if err_path.is_file() else None,
        "err_bytes": err_bytes,
        "exists": path.is_file(),
        "log_mtime": mtime,
        "current_year": current_year,
        "current_file": current_file,
        "years_seen": years_seen,
        "pages_c1_true": pages_c1,
        "pages_o6_true": pages_o6,
        "pages_todo": pages_todo or queued_need,
        "pages_done": pages_done,
        "pages_left": pages_left,
        "c1_done": c1_done_prog,
        "c1_todo": c1_todo,
        "o6_done": o6_done_prog,
        "o6_todo": o6_todo,
        "recent_page_lines": page_lines[-8:],
        "done": done,
    }


def _latest_c1o6_recover_log() -> str:
    """Newest ``_recover_c1o6*.log`` in repo root (pass1, pass2, …). Shallow only."""
    cands: list[tuple[float, str]] = []
    try:
        for p in ROOT.glob("_recover_c1o6*.log"):
            if p.name.endswith(".err.log"):
                continue
            try:
                cands.append((p.stat().st_mtime, p.name))
            except OSError:
                continue
    except OSError:
        pass
    if not cands:
        return "_recover_c1o6_9798.log"
    cands.sort(key=lambda t: t[0], reverse=True)
    return cands[0][1]


def c1o6_recover_live() -> dict:
    """C1/O6 targeted recover process + log snapshot. Never kill."""
    rows = _win32_python_cmdlines(r"recover_ocr_gaps_targeted")
    running = bool(rows)
    pids = [r["pid"] for r in rows]
    years_argv: list[int] = []
    cmdline = ""
    if rows:
        cmdline = rows[0].get("cmdline") or ""
        years_argv = _parse_years_from_cmdline(cmdline)
        for r in rows[1:]:
            for y in _parse_years_from_cmdline(r.get("cmdline") or ""):
                if y not in years_argv:
                    years_argv.append(y)

    log_name = _latest_c1o6_recover_log()
    log = parse_c1o6_recover_log(log_name)
    # Pass label from filename (e.g. _recover_c1o6_9798_pass2.log)
    pass_label = "pass1"
    m_pass = re.search(r"pass(\d+)", log_name, re.I)
    if m_pass:
        pass_label = f"pass{m_pass.group(1)}"
    elif log_name != "_recover_c1o6_9798.log":
        pass_label = log_name
    log["pass_label"] = pass_label

    if running:
        state = "running"
    elif log.get("done"):
        state = "done"
    elif log.get("exists"):
        state = "idle"
    else:
        state = "idle"

    return {
        "kind": "c1_o6_targeted",
        "script": "recover_ocr_gaps_targeted.py",
        "state": state,
        "running": running,
        "pids": pids,
        "pid": pids[0] if pids else None,
        "years_argv": years_argv,
        "cmdline": cmdline[:400] if cmdline else "",
        "log": log,
        "active_log": log_name,
        "pass_label": pass_label,
    }


def assess_ingest_audit_alive() -> dict:
    """Detect assess_ingest_quality_audit process (B6b executor). Never kill."""
    rows = _win32_python_cmdlines(r"assess_ingest_quality_audit")
    pids = [r["pid"] for r in rows]
    return {"alive": bool(pids), "pids": pids}


def _b6b_verdict_from_audit_md(year: str) -> dict:
    """Light parse of ``_b6b_ingest_audit_{year}.md`` if present."""
    path = ROOT / f"_b6b_ingest_audit_{year}.md"
    out: dict = {}
    if not path.is_file():
        return out
    try:
        out["audit_mtime_epoch"] = path.stat().st_mtime
    except OSError:
        pass
    text = _read_text(path, max_bytes=80_000)
    for line in text.splitlines()[:30]:
        if "Year verdict" in line:
            m = re.search(r"\*\*(PASS|WARN|FAIL)\*\*", line)
            if m:
                out["b6b_verdict"] = m.group(1)
            if "unlock: YES" in line or "SQL-apply unlock: YES" in line:
                out["b6b_unlocked"] = True
            elif "unlock: NO" in line:
                out["b6b_unlocked"] = False
        vm = re.search(
            r"Volumes:\s*(\d+)\s+cleaned=(\d+)\s+PASS=(\d+)\s+WARN=(\d+)\s+FAIL=(\d+)",
            line,
        )
        if vm:
            out["b6b_pass"] = int(vm.group(3))
            out["b6b_warn"] = int(vm.group(4))
            out["b6b_fail"] = int(vm.group(5))
            out["b6b"] = "done"
    if path.is_file() and "b6b_done" not in out:
        out["b6b_done"] = _mtime_local(path)
    return out


def _b6b_summary_from_audit_json(year: str) -> dict:
    """PASS/WARN/FAIL tallies + year verdict from ``_b6b_ingest_audit_{year}.json``."""
    path = ROOT / f"_b6b_ingest_audit_{year}.json"
    out: dict = {}
    if not path.is_file():
        return out
    try:
        out["audit_mtime_epoch"] = path.stat().st_mtime
        out["b6b_done"] = _mtime_local(path)
        raw = json.loads(path.read_text(encoding="utf-8", errors="replace"))
    except (OSError, json.JSONDecodeError):
        return out
    if not isinstance(raw, dict):
        return out
    verd = raw.get("year_verdict") or raw.get("verdict")
    if verd:
        out["b6b_verdict"] = str(verd).upper()
    if "unlocked" in raw:
        out["b6b_unlocked"] = bool(raw.get("unlocked"))
    elif "sql_apply_unlock" in raw:
        out["b6b_unlocked"] = bool(raw.get("sql_apply_unlock"))
    f = w = p = 0
    for vol in raw.get("volumes") or []:
        if not isinstance(vol, dict):
            continue
        v = str(vol.get("verdict") or "").upper()
        if v == "FAIL":
            f += 1
        elif v == "WARN":
            w += 1
        elif v == "PASS":
            p += 1
    if raw.get("volumes") is not None:
        out["b6b_fail"] = f
        out["b6b_warn"] = w
        out["b6b_pass"] = p
        out["b6b"] = "done"
        if not out.get("b6b_verdict"):
            out["b6b_verdict"] = "FAIL" if f else ("WARN" if w else "PASS")
    return out


def _b6b_live_fields(year: str, yinfo: dict) -> dict:
    """Live B6b gate fields: prefer on-disk audit over stale manifest mid-clear.

    ``assess_ingest_quality_audit`` writes md/json first; manifest can lag until
    ``update_manifest`` finishes. Mid-clear FAIL/PASS must follow the audit files.
    """
    md = _b6b_verdict_from_audit_md(year)
    js = _b6b_summary_from_audit_json(year)
    # Prefer json tallies when present (exact vol counts); md for unlock wording.
    file_bits: dict = {}
    for src in (md, js):
        for k, v in src.items():
            if v is None:
                continue
            if k == "audit_mtime_epoch":
                prev = file_bits.get(k)
                file_bits[k] = max(prev, v) if isinstance(prev, (int, float)) else v
                continue
            # json overwrites md for numeric tallies / verdict when both exist
            if k in ("b6b_fail", "b6b_warn", "b6b_pass", "b6b_verdict", "b6b") and k in js:
                file_bits[k] = js[k]
            elif k not in file_bits:
                file_bits[k] = v
            elif k in js and k in ("b6b_unlocked", "b6b_done"):
                file_bits[k] = js[k]

    has_audit = bool(
        file_bits.get("b6b_verdict")
        or file_bits.get("b6b_fail") is not None
        or file_bits.get("b6b_pass") is not None
    )
    if has_audit:
        verd = file_bits.get("b6b_verdict") or yinfo.get("b6b_verdict")
        b6b = file_bits.get("b6b") or yinfo.get("b6b") or "done"
        unlocked = (
            file_bits["b6b_unlocked"]
            if "b6b_unlocked" in file_bits
            else yinfo.get("b6b_unlocked")
        )
        fail = file_bits["b6b_fail"] if "b6b_fail" in file_bits else yinfo.get("b6b_fail")
        warn = file_bits["b6b_warn"] if "b6b_warn" in file_bits else yinfo.get("b6b_warn")
        pas = file_bits["b6b_pass"] if "b6b_pass" in file_bits else yinfo.get("b6b_pass")
        done = file_bits.get("b6b_done") or _iso_to_local(
            (yinfo.get("timestamps") or {}).get("b6b_done")
        )
        source = "audit_file"
    else:
        verd = yinfo.get("b6b_verdict")
        b6b = yinfo.get("b6b")
        unlocked = yinfo.get("b6b_unlocked")
        fail = yinfo.get("b6b_fail")
        warn = yinfo.get("b6b_warn")
        pas = yinfo.get("b6b_pass")
        done = _iso_to_local((yinfo.get("timestamps") or {}).get("b6b_done"))
        source = "manifest"

    audit_mtime = None
    epoch = file_bits.get("audit_mtime_epoch")
    if isinstance(epoch, (int, float)) and epoch > 0:
        audit_mtime = _fmt_local(datetime.fromtimestamp(epoch, timezone.utc))

    return {
        "b6b": b6b,
        "b6b_verdict": verd,
        "b6b_unlocked": unlocked,
        "b6b_fail": fail,
        "b6b_warn": warn,
        "b6b_pass": pas,
        "b6b_done": done,
        "b6b_source": source,
        "audit_mtime": audit_mtime,
        "has_audit": has_audit,
    }


def _b6b_detail_from_audit_json(year: str, *, max_samples_per_vol: int = 8) -> dict:
    """Volume FAIL/WARN detail + sample hits from ``_b6b_ingest_audit_{year}.json``."""
    path = ROOT / f"_b6b_ingest_audit_{year}.json"
    out: dict = {"volumes": [], "by_catalog": {}, "fail_samples": [], "warn_samples": []}
    if not path.is_file():
        return out
    try:
        raw = json.loads(path.read_text(encoding="utf-8", errors="replace"))
    except (OSError, json.JSONDecodeError):
        return out
    if not isinstance(raw, dict):
        return out
    cat_totals: dict[str, int] = {}
    fail_samples: list[dict] = []
    warn_samples: list[dict] = []
    volumes_out: list[dict] = []
    for vol in raw.get("volumes") or []:
        if not isinstance(vol, dict):
            continue
        verd = str(vol.get("verdict") or "")
        if verd not in ("FAIL", "WARN"):
            continue
        fpath = str(vol.get("file") or "")
        short = Path(fpath).name if fpath else "?"
        by_code = vol.get("by_code") if isinstance(vol.get("by_code"), dict) else {}
        top_catalog = str(vol.get("top_catalog") or "")
        samples_in = vol.get("samples") if isinstance(vol.get("samples"), list) else []
        code_to_cat: dict[str, str] = {}
        for s in samples_in:
            if isinstance(s, dict) and s.get("code"):
                code_to_cat[str(s["code"])] = str(s.get("catalog") or s["code"])
        for code, n in by_code.items():
            cat = code_to_cat.get(str(code)) or str(code)
            try:
                ni = int(n)
            except (TypeError, ValueError):
                ni = 0
            cat_totals[cat] = cat_totals.get(cat, 0) + ni
        if not by_code and top_catalog:
            for bit in top_catalog.split(","):
                bit = bit.strip().replace("×", "x")
                m = re.match(r"^([A-Za-z0-9/?]+).*?[x\-]?(\d+)\s*$", bit)
                if not m:
                    continue
                cat_totals[m.group(1)] = cat_totals.get(m.group(1), 0) + int(m.group(2))
        samples_out: list[dict] = []
        for s in samples_in:
            if not isinstance(s, dict):
                continue
            code = str(s.get("code") or "")
            catalog = str(s.get("catalog") or "")
            line = str(s.get("line") or "").replace("\n", " ").strip()
            if len(line) > 160:
                line = line[:157] + "…"
            entry = {
                "year": year,
                "file": short,
                "code": code,
                "catalog": catalog,
                "line": line,
                "vol_verdict": verd,
            }
            samples_out.append(entry)
            if verd == "FAIL":
                fail_samples.append(entry)
            else:
                warn_samples.append(entry)
            if len(samples_out) >= max_samples_per_vol:
                break
        volumes_out.append(
            {
                "file": short,
                "verdict": verd,
                "fail_hits": int(vol.get("fail_hits") or 0),
                "warn_hits": int(vol.get("warn_hits") or 0),
                "top_catalog": top_catalog,
                "by_code": {str(k): int(v) for k, v in by_code.items()},
                "samples": samples_out,
            }
        )
    # Prefer FAIL samples, then non-C1 WARN, then C1 WARN — cap list size
    def _rank(s: dict) -> tuple[int, str]:
        cat = (s.get("catalog") or "").upper()
        if cat == "C1":
            return (2, s.get("code") or "")
        return (0 if s.get("catalog") else 1, s.get("code") or "")

    fail_samples.sort(key=_rank)
    warn_samples.sort(key=_rank)
    out["volumes"] = volumes_out
    out["by_catalog"] = dict(sorted(cat_totals.items(), key=lambda kv: (-kv[1], kv[0])))
    out["fail_samples"] = fail_samples[:20]
    out["warn_samples"] = warn_samples[:24]
    return out


def b6b_ingest_audit_status(myears: dict, recover_running: bool) -> dict:
    """B6b gate snapshot for 1984–2001; note pending re-run if recover still live."""
    audit_proc = assess_ingest_audit_alive()
    years_out: dict[str, dict] = {}
    details: list[dict] = []
    fail_years: list[str] = []
    for y in YEARS_B6B_ALL:
        yinfo = myears.get(y) or {}
        live = _b6b_live_fields(y, yinfo)
        verdict = live.get("b6b_verdict")
        b6b = live.get("b6b")
        if y < "1997" and not b6b and not verdict:
            b6b = "parked"
            era = "early" if y < "1990" else "yearbook_9096"
        elif not b6b and not verdict:
            b6b = "pending"
            era = "remediation"
        else:
            era = "remediation" if y >= "1997" else ("early" if y < "1990" else "yearbook_9096")
        fail_n = int(live.get("b6b_fail") or 0)
        warn_n = int(live.get("b6b_warn") or 0)
        detail = _b6b_detail_from_audit_json(y) if (
            (verdict in ("FAIL", "WARN"))
            or fail_n > 0
            or warn_n > 0
            or live.get("has_audit")
        ) else {"volumes": [], "by_catalog": {}, "fail_samples": [], "warn_samples": []}
        years_out[y] = {
            "b6b": b6b,
            "b6b_verdict": verdict,
            "b6b_unlocked": live.get("b6b_unlocked"),
            "b6b_fail": live.get("b6b_fail"),
            "b6b_warn": live.get("b6b_warn"),
            "b6b_pass": live.get("b6b_pass"),
            "b6b_done": live.get("b6b_done"),
            "b6b_source": live.get("b6b_source"),
            "audit_mtime": live.get("audit_mtime"),
            "era": era,
            "by_catalog": detail.get("by_catalog") or {},
            "volumes": detail.get("volumes") or [],
        }
        if fail_n > 0 or (str(verdict or "").upper() == "FAIL"):
            fail_years.append(y)
        if detail.get("volumes"):
            details.append(
                {
                    "year": y,
                    "verdict": verdict,
                    "by_catalog": detail.get("by_catalog") or {},
                    "volumes": detail.get("volumes") or [],
                    "fail_samples": detail.get("fail_samples") or [],
                    "warn_samples": detail.get("warn_samples") or [],
                }
            )

    if audit_proc["alive"]:
        state = "running"
        note = "assess_ingest_quality_audit process alive · polling audit files live"
    elif recover_running:
        state = "pending_rerun"
        note = "C1/O6 recover still running -> B6b re-run pending (not executing now)"
    else:
        any_done = any(
            (v.get("b6b") == "done") or v.get("b6b_verdict")
            for v in years_out.values()
        )
        state = "idle_with_results" if any_done else "idle"
        if fail_years:
            note = (
                f"Years 1984–2001 · FAIL residual on {', '.join(fail_years)} "
                "(audit-file live counts)"
            )
        else:
            note = "Years 1984–2001 · audit-file live counts (manifest lag ignored)"

    return {
        "kind": "b6b_ingest_audit",
        "state": state,
        "running": audit_proc["alive"],
        "pids": audit_proc["pids"],
        "recover_still_running": recover_running,
        "note": note,
        "fail_years": fail_years,
        "years": years_out,
        "details": details,
    }


def reocr_queue_live() -> dict:
    """FAIL→re-OCR queue + dual-track live ``schedule_reocr_from_queue`` (Track A/B).

    Convention (non-overlapping years):
      Track A: ``--years 1998 2000`` → ``_reocr_9800_trackA.log``
      Track B: ``--years 1999 2001`` → ``_reocr_9901_trackB.log``
    """
    qpath = ROOT / "_reocr_queue.json"
    entries: list[dict] = []
    if qpath.is_file():
        try:
            raw = json.loads(qpath.read_text(encoding="utf-8"))
            if isinstance(raw, list):
                entries = [e for e in raw if isinstance(e, dict)]
        except (OSError, json.JSONDecodeError):
            entries = []

    # Live processes: PID + command line (for year-set → track mapping)
    proc_rows = [
        {"pid": r["pid"], "cmd": r.get("cmdline") or ""}
        for r in _win32_python_cmdlines(r"schedule_reocr_from_queue")
    ]
    pids = [p["pid"] for p in proc_rows]

    def _read_reocr_log_text(path: Path) -> str:
        """Read re-OCR logs; PowerShell Tee-Object often writes UTF-16 LE."""
        raw = path.read_bytes()
        if not raw:
            return ""
        if raw.startswith(b"\xff\xfe") or raw.startswith(b"\xfe\xff"):
            return raw.decode("utf-16", errors="replace")
        # UTF-16 without BOM (nulls between ASCII)
        if b"\x00" in raw[: min(200, len(raw))]:
            return raw.decode("utf-16-le", errors="replace")
        return raw.decode("utf-8", errors="replace")

    def _parse_reocr_log(path: Path) -> dict:
        """Same wall PPM model as ``parse_ocr_track`` (birth→now; not ÷ workers)."""
        job_line = page_line = ""
        job_index = job_total = None
        pages_total = 0
        pages_this_job = 0
        workers_log = None
        page_re = re.compile(r"OCR page\s+(\d+)\b")
        workers_re = re.compile(r"\bworkers=(\d+)\b")
        try:
            text = _read_reocr_log_text(path)
            for line in text.splitlines():
                wm = workers_re.search(line)
                if wm:
                    workers_log = max(1, int(wm.group(1)))
                if "REOCR " in line:
                    job_line = line.strip()
                    m = re.search(r"REOCR\s+(\d+)/(\d+)", line)
                    if m:
                        job_index = int(m.group(1))
                        job_total = int(m.group(2))
                    pages_this_job = 0
                    continue
                if re.search(r"OCR\s+\d+/\d+\s+y=", line) and "REOCR" not in line:
                    pages_this_job = 0
                    if not job_line:
                        job_line = line.strip()
                    continue
                pm = page_re.search(line)
                if pm:
                    pages_total += 1
                    pages_this_job += 1
                    page_line = f"OCR page {int(pm.group(1))}"
        except OSError:
            pass

        return {
            "job_line": job_line,
            "page_line": page_line,
            "job_index": job_index,
            "job_total": job_total,
            "pages_total": pages_total,
            "pages_this_job": pages_this_job,
            "workers_log": workers_log,
            "ppm": None,
            "ppm_job": None,
            "elapsed_min": None,
            "worker_min": None,
            "_pages_total_raw": pages_total,
            "_pages_this_job_raw": pages_this_job,
            "_path": path,
        }

    def _finish_reocr_parsed(parsed: dict, workers: int) -> dict:
        """Attach wall PPM using effective worker count."""
        path = parsed.pop("_path", None)
        pages_total = int(parsed.pop("_pages_total_raw", 0) or 0)
        pages_this_job = int(parsed.pop("_pages_this_job_raw", 0) or 0)
        parsed["pages_total"] = pages_total
        parsed["pages_this_job"] = pages_this_job
        parsed["workers"] = workers
        ppm = ppm_job = elapsed_min = worker_min = None
        if path is not None and path.is_file() and pages_total > 0:
            try:
                import time as _time

                st = path.stat()
                start = getattr(st, "st_ctime", None) or st.st_mtime
                end = st.st_mtime
                now = _time.time()
                if now - end < 180:
                    end = now
                elapsed_min = max((end - start) / 60.0, 0.01)
                worker_min = round(elapsed_min * max(workers, 1), 2)
                ppm = round(pages_total / elapsed_min, 2)
                if pages_this_job > 0 and pages_total > 0:
                    job_frac = pages_this_job / max(pages_total, 1)
                    job_min = max(elapsed_min * job_frac, 0.01)
                    ppm_job = round(pages_this_job / job_min, 2)
            except OSError:
                pass
        parsed["ppm"] = ppm
        parsed["ppm_job"] = ppm_job
        parsed["elapsed_min"] = round(elapsed_min, 1) if elapsed_min is not None else None
        parsed["worker_min"] = round(worker_min, 1) if worker_min is not None else None
        return parsed

    def _years_from_cmd(cmd: str) -> set[int]:
        # ``--years 1998 2000 --workers`` → {1998, 2000}
        m = re.search(r"--years\s+((?:\d{4}\s*)+)", cmd or "", re.I)
        if not m:
            return set()
        out: set[int] = set()
        for tok in m.group(1).split():
            try:
                out.add(int(tok))
            except ValueError:
                pass
        return out

    TRACK_A_YEARS = {1998, 2000}
    TRACK_B_YEARS = {1999, 2001}
    TRACK_LOGS = {
        "trackA": ROOT / "_reocr_9800_trackA.log",
        "trackB": ROOT / "_reocr_9901_trackB.log",
    }

    def _classify_track(years: set[int]) -> str | None:
        if not years:
            return None
        if years <= TRACK_A_YEARS or years == TRACK_A_YEARS:
            return "trackA"
        if years <= TRACK_B_YEARS or years == TRACK_B_YEARS:
            return "trackB"
        # Prefer majority membership for odd one-offs
        if years & TRACK_A_YEARS and not (years & TRACK_B_YEARS):
            return "trackA"
        if years & TRACK_B_YEARS and not (years & TRACK_A_YEARS):
            return "trackB"
        return None

    track_pids: dict[str, list[int]] = {"trackA": [], "trackB": []}
    track_cmds: dict[str, list[str]] = {"trackA": [], "trackB": []}
    for row in proc_rows:
        label = _classify_track(_years_from_cmd(row["cmd"]))
        if label:
            track_pids[label].append(row["pid"])
            track_cmds[label].append(row["cmd"])
        else:
            # Unclassified (e.g. old 1998-2001 single queue): attach to A for visibility
            track_pids["trackA"].append(row["pid"])
            track_cmds["trackA"].append(row["cmd"])

    tess_live = _tess_count_live()

    def _track_payload(label: str, years: set[int]) -> dict:
        log_path = TRACK_LOGS[label]
        raw = (
            _parse_reocr_log(log_path)
            if log_path.is_file()
            else {
                "job_line": "",
                "page_line": "",
                "job_index": None,
                "job_total": None,
                "pages_total": 0,
                "pages_this_job": 0,
                "workers_log": None,
                "ppm": None,
                "ppm_job": None,
                "elapsed_min": None,
                "worker_min": None,
                "_pages_total_raw": 0,
                "_pages_this_job_raw": 0,
                "_path": None,
            }
        )
        tpids = track_pids.get(label) or []
        cmds = track_cmds.get(label) or []
        workers_cmdline = None
        page_workers = None
        for cmd in cmds:
            w = _workers_from_cmdline(cmd)
            if w is not None:
                workers_cmdline = w
            pw = _page_workers_from_cmdline(cmd)
            if pw is not None:
                page_workers = pw
        workers_log = raw.get("workers_log")
        workers = _effective_workers(workers_cmdline, workers_log)
        if workers is None:
            workers = max(1, int(os.environ.get("JRTCA_OCR_WORKERS", "10")))
        parsed = _finish_reocr_parsed(raw, workers)
        running = bool(tpids)
        y_sorted = sorted(years)
        return {
            "label": "A" if label == "trackA" else "B",
            "kind": "reocr",
            "years": y_sorted,
            "years_label": " ".join(str(y) for y in y_sorted),
            "running": running,
            "state": "running" if running else ("queued" if entries else "idle"),
            "pids": tpids,
            "active_log": log_path.name if log_path.is_file() else None,
            "log_mtime": _mtime_local(log_path) if log_path.is_file() else None,
            "job_line": parsed.get("job_line") or "",
            "page_line": parsed.get("page_line") or "",
            "job_index": parsed.get("job_index"),
            "job_total": parsed.get("job_total"),
            "pages_total": parsed.get("pages_total"),
            "pages_this_job": parsed.get("pages_this_job"),
            "workers": parsed.get("workers"),
            "workers_log": workers_log,
            "workers_cmdline": workers_cmdline,
            "page_workers": page_workers,
            "tess_live": tess_live,
            "adjustable": True,
            "ppm": parsed.get("ppm"),
            "ppm_job": parsed.get("ppm_job"),
            "elapsed_min": parsed.get("elapsed_min"),
            "worker_min": parsed.get("worker_min"),
        }

    trackA = _track_payload("trackA", TRACK_A_YEARS)
    trackB = _track_payload("trackB", TRACK_B_YEARS)

    # Aggregate compat fields (prefer busier / trackA then trackB)
    def _score(t: dict) -> int:
        return int(t.get("pages_total") or 0) + (1000 if t.get("running") else 0)

    primary = trackA if _score(trackA) >= _score(trackB) else trackB

    by_year: dict[str, int] = {}
    for e in entries:
        y = str(e.get("year") or "?")
        by_year[y] = by_year.get(y, 0) + 1

    running = bool(pids)
    state = "running" if running else ("queued" if entries else "idle")
    return {
        "kind": "reocr_queue",
        "state": state,
        "running": running,
        "pids": pids,
        "queue_count": len(entries),
        "by_year": by_year,
        "entries": [
            {
                "year": e.get("year"),
                "hqmax": Path(str(e.get("hqmax") or "")).name,
                "hqmax_full": e.get("hqmax"),
                "codes": e.get("codes") or [],
                "fail_hits": e.get("fail_hits"),
                "top_catalog": e.get("top_catalog"),
                "reason": e.get("reason"),
            }
            for e in entries[:40]
        ],
        "trackA": trackA,
        "trackB": trackB,
        # Backward-compatible single-card fields (aggregate / primary track)
        "job_line": primary.get("job_line") or "",
        "page_line": primary.get("page_line") or "",
        "job_index": primary.get("job_index"),
        "job_total": primary.get("job_total"),
        "pages_total": primary.get("pages_total"),
        "pages_this_job": primary.get("pages_this_job"),
        "workers": primary.get("workers"),
        "ppm": primary.get("ppm"),
        "ppm_job": primary.get("ppm_job"),
        "elapsed_min": primary.get("elapsed_min"),
        "worker_min": primary.get("worker_min"),
        "active_log": primary.get("active_log"),
        "log_mtime": primary.get("log_mtime"),
        "tess_live": tess_live,
        "note": (
            "B6b FAIL → force re-OCR dual-track: "
            "A={1998,2000} / B={1999,2001}; workers from live cmdline; "
            "unlock blocked until FAIL=0"
        ),
    }


def surgical_reocr_live() -> dict:
    """Single-vol / prove-slice force re-OCR (``_tmp_reocr_*.py`` + ``_reocr_c1_*.log``).

    Dual-track cards only watch ``schedule_reocr_from_queue``; surgical jobs must
    surface separately so the dashboard shows live page progress.
    """
    rows = _win32_python_cmdlines(r"_tmp_reocr_|_reocr_c1_")
    # Also catch direct ocr_pdf_hq one-offs launched from tmp helpers.
    if not rows:
        rows = [
            r
            for r in _win32_python_cmdlines(r"ocr_pdf_hq|_tmp_reocr")
            if "_tmp_reocr" in (r.get("cmdline") or "")
            or "reocr_c1" in (r.get("cmdline") or "").lower()
        ]
    pids = [r["pid"] for r in rows]
    cmdline = (rows[0].get("cmdline") or "") if rows else ""

    log_path: Path | None = None
    try:
        cands = [
            p
            for p in ROOT.glob("_reocr_c1_*.log")
            if p.is_file() and not p.name.endswith(".err.log")
        ]
        if cands:
            cands.sort(key=lambda p: p.stat().st_mtime, reverse=True)
            log_path = cands[0]
    except OSError:
        log_path = None

    # Fallback: any live tmp script often tees to a matching _reocr_*.log
    if log_path is None and cmdline:
        m = re.search(r"(_reocr_[A-Za-z0-9_\-]+\.log)", cmdline)
        if m and (ROOT / m.group(1)).is_file():
            log_path = ROOT / m.group(1)

    job_line = page_line = ""
    pages_total = 0
    pages_this_job = 0
    page_current = None
    dest_hqmax: Path | None = None
    workers_log = None
    done_line = ""
    if log_path and log_path.is_file():
        raw = log_path.read_bytes()
        if raw.startswith(b"\xff\xfe") or raw.startswith(b"\xfe\xff") or (
            b"\x00" in raw[: min(200, len(raw))]
        ):
            text = raw.decode("utf-16-le", errors="replace")
        else:
            text = raw.decode("utf-8", errors="replace")
        page_re = re.compile(r"OCR page\s+(\d+)\b")
        workers_re = re.compile(r"\bworkers=(\d+)\b")
        dest_re = re.compile(r"->\s*(.+?_ocr_hqmax\.txt)\s*$")
        for line in text.splitlines():
            wm = workers_re.search(line)
            if wm:
                workers_log = max(1, int(wm.group(1)))
            if "REOCR " in line or ("REOCR" in line and "->" in line):
                job_line = _line_utc_stamps_to_local(line.strip())
                pages_this_job = 0
                dm = dest_re.search(line.replace("/", "\\"))
                if not dm:
                    dm = re.search(r"->\s*(.+?_ocr_hqmax\.txt)", line)
                if dm:
                    cand = Path(dm.group(1).strip().strip('"'))
                    if not cand.is_absolute():
                        cand = ROOT / cand
                    dest_hqmax = cand
            pm = page_re.search(line)
            if pm:
                pages_total += 1
                pages_this_job += 1
                page_current = int(pm.group(1))
                page_line = f"OCR page {page_current}"
            if "ok year_guess=" in line:
                done_line = _line_utc_stamps_to_local(line.strip())

    workers = workers_log if workers_log is not None else max(
        1, int(os.environ.get("JRTCA_OCR_WORKERS", "4"))
    )

    pages_expected = None
    if dest_hqmax is not None:
        # Prefer pre-job backup (complete prior OCR); else live hqmax if present.
        for cand in (
            Path(str(dest_hqmax) + ".pre_1999_volii_pt1_c1"),
            Path(str(dest_hqmax) + ".pre_1997_voli_pt1_c1"),
            Path(str(dest_hqmax) + ".pre_1997_volii_pt2_c1"),
            Path(str(dest_hqmax) + ".pre_1997_volii_pt1_c1"),
            Path(str(dest_hqmax) + ".pre_1997_voli_pt2_c1"),
            Path(str(dest_hqmax) + ".pre_voliii_pt2_c1"),
            Path(str(dest_hqmax) + ".pre_voliii_pt1_c1"),
            Path(str(dest_hqmax) + ".pre_volii_pt2_c1"),
            Path(str(dest_hqmax) + ".pre_volii_pt1_c1"),
            Path(str(dest_hqmax) + ".pre_voli_pt1_c1"),
            dest_hqmax.with_suffix(dest_hqmax.suffix + ".pre_1999_volii_pt1_c1"),
            dest_hqmax.with_suffix(dest_hqmax.suffix + ".pre_1997_voli_pt1_c1"),
            dest_hqmax.with_suffix(dest_hqmax.suffix + ".pre_1997_volii_pt2_c1"),
            dest_hqmax.with_suffix(dest_hqmax.suffix + ".pre_1997_volii_pt1_c1"),
            dest_hqmax.with_suffix(dest_hqmax.suffix + ".pre_1997_voli_pt2_c1"),
            dest_hqmax.with_suffix(dest_hqmax.suffix + ".pre_voliii_pt2_c1"),
            dest_hqmax.with_suffix(dest_hqmax.suffix + ".pre_voliii_pt1_c1"),
            dest_hqmax.with_suffix(dest_hqmax.suffix + ".pre_volii_pt2_c1"),
            dest_hqmax.with_suffix(dest_hqmax.suffix + ".pre_volii_pt1_c1"),
            dest_hqmax.with_suffix(dest_hqmax.suffix + ".pre_voli_pt1_c1"),
            Path(str(dest_hqmax) + ".pre_c1o6"),
            dest_hqmax,
        ):
            if cand.is_file():
                try:
                    n = cand.read_text(encoding="utf-8", errors="replace").count(
                        "--- page "
                    )
                    if n > 0:
                        pages_expected = n
                        break
                except OSError:
                    pass

    ppm = elapsed_min = None
    if log_path and log_path.is_file() and pages_total > 0:
        try:
            import time as _time

            st = log_path.stat()
            start = getattr(st, "st_ctime", None) or st.st_mtime
            end = st.st_mtime
            now = _time.time()
            if now - end < 180:
                end = now
            elapsed_min = max((end - start) / 60.0, 0.01)
            ppm = round(pages_total / elapsed_min, 2)
        except OSError:
            pass

    running = bool(pids)
    if running:
        state = "running"
    elif done_line:
        state = "done"
    elif log_path:
        state = "idle"
    else:
        state = "idle"

    progress_pct = None
    eta_min = None
    pages_left = None
    progress_label = ""
    done_n = page_current if page_current is not None else pages_total
    if done_line and pages_expected:
        progress_label = f"{pages_expected}/{pages_expected} (100%)"
        progress_pct = 100.0
        pages_left = 0
        eta_min = 0.0
    elif pages_expected and done_n is not None:
        # Prefer highest observed page number as position; clamp to expected.
        done_n = min(int(done_n), int(pages_expected))
        pages_left = max(0, int(pages_expected) - done_n)
        progress_pct = round(100.0 * done_n / max(int(pages_expected), 1), 1)
        if ppm and pages_left > 0 and running:
            eta_min = round(pages_left / max(ppm, 0.01), 1)
        progress_label = f"{done_n}/{pages_expected} ({progress_pct:.0f}%)"
        if eta_min is not None:
            progress_label += f" · ETA ~{eta_min} min"

    script = None
    sm = re.search(r"(_tmp_reocr_[A-Za-z0-9_\-]+\.py)", cmdline)
    if sm:
        script = sm.group(1)

    return {
        "kind": "surgical_reocr",
        "state": state,
        "running": running,
        "pids": pids,
        "pid": pids[0] if pids else None,
        "script": script,
        "cmdline": cmdline[:400] if cmdline else "",
        "active_log": log_path.name if log_path else None,
        "log_mtime": _mtime_local(log_path) if log_path else None,
        "job_line": job_line,
        "page_line": page_line,
        "pages_total": pages_total,
        "pages_this_job": pages_this_job,
        "page_current": page_current,
        "pages_expected": pages_expected,
        "pages_left": pages_left,
        "progress_pct": progress_pct,
        "progress_label": progress_label,
        "eta_min": eta_min,
        "workers": workers,
        "workers_log": workers_log,
        "tess_live": _tess_count_live(),
        "ppm": ppm,
        "elapsed_min": round(elapsed_min, 1) if elapsed_min is not None else None,
        "done_line": done_line,
        "note": "Single-vol / prove-slice force re-OCR (not dual-track schedule_reocr)",
    }


def other_targeted_recoveries(c1o6_pids: list[int] | None = None) -> dict:
    """Cheap scan: root _recover_*.log + other recover_*.py processes. Cap few entries."""
    skip_pids = set(c1o6_pids or [])
    entries: list[dict] = []

    # Known sibling scripts / logs at repo root only (no rglob into OneDrive trees).
    try:
        log_names = sorted(
            p.name
            for p in ROOT.glob("_recover_*.log")
            if p.is_file() and not p.name.endswith(".err.log")
        )
    except OSError:
        log_names = []

    try:
        script_names = sorted(p.name for p in ROOT.glob("recover_*.py") if p.is_file())
    except OSError:
        script_names = []

    rows = _win32_python_cmdlines(r"recover_")
    for r in rows:
        if r["pid"] in skip_pids:
            continue
        if "recover_ocr_gaps_targeted" in (r.get("cmdline") or ""):
            continue
        script = None
        cm = re.search(r"(recover_[A-Za-z0-9_\-]+\.py)", r.get("cmdline") or "")
        if cm:
            script = cm.group(1)
        entries.append(
            {
                "state": "running",
                "pid": r["pid"],
                "script": script,
                "cmdline": (r.get("cmdline") or "")[:300],
                "log": None,
                "log_mtime": None,
            }
        )

    # Recent idle logs that are not the C1/O6 family (active pass shown in main card).
    for name in log_names:
        if name.startswith("_recover_c1o6"):
            continue
        path = ROOT / name
        entries.append(
            {
                "state": "log_only",
                "pid": None,
                "script": None,
                "cmdline": "",
                "log": name,
                "log_mtime": _mtime_local(path),
            }
        )

    # Cap to a few recent/active: running first, then by mtime.
    running = [e for e in entries if e.get("state") == "running"]
    others = [e for e in entries if e.get("state") != "running"]
    others.sort(key=lambda e: e.get("log_mtime") or "", reverse=True)
    return {
        "scripts_at_root": script_names,
        "entries": (running + others)[:5],
    }


def year_pipeline_row(year: str, yinfo: dict, hqmax: int) -> dict:
    a2_detail = _a2_detail_from_csv(year)
    live = _b6b_live_fields(year, yinfo)
    b6b_json = _b6b_detail_from_audit_json(year) if (
        live.get("b6b_verdict") in ("FAIL", "WARN")
        or (live.get("b6b_fail") or 0) > 0
        or (live.get("b6b_warn") or 0) > 0
        or live.get("b6b") == "done"
        or live.get("has_audit")
    ) else {"volumes": [], "by_catalog": {}}
    # Prefer audit-file done stamp when present (mid-clear freshness).
    merged_yinfo = dict(yinfo)
    for k in ("b6b", "b6b_verdict", "b6b_unlocked", "b6b_fail", "b6b_warn", "b6b_pass"):
        if live.get(k) is not None:
            merged_yinfo[k] = live.get(k)
    return {
        "year": year,
        "a1": yinfo.get("a1", "pending"),
        "a1_done": yinfo.get("a1_done"),
        "a1_jobs": yinfo.get("a1_jobs"),
        "a1_complete": yinfo.get("a1_complete"),
        "a2": yinfo.get("a2", "pending"),
        "a2_pass": yinfo.get("a2_pass"),
        "a2_warn": yinfo.get("a2_warn"),
        "a2_fail": yinfo.get("a2_fail"),
        "a2_unlocked": yinfo.get("a2_unlocked"),
        "a2_detail": a2_detail,
        "b6": yinfo.get("b6", "pending"),
        "b6_sections": yinfo.get("b6_sections"),
        "b6b": live.get("b6b") or yinfo.get("b6b", "pending"),
        "b6b_verdict": live.get("b6b_verdict"),
        "b6b_unlocked": live.get("b6b_unlocked"),
        "b6b_fail": live.get("b6b_fail"),
        "b6b_warn": live.get("b6b_warn"),
        "b6b_pass": live.get("b6b_pass"),
        "b6b_done": live.get("b6b_done"),
        "b6b_source": live.get("b6b_source"),
        "audit_mtime": live.get("audit_mtime"),
        "b6b_by_catalog": b6b_json.get("by_catalog") or {},
        "b6b_volumes": b6b_json.get("volumes") or [],
        "c10": yinfo.get("c10", "pending"),
        "hqmax_count": hqmax,
        "b6b_detail": b6b_year_detail(year, merged_yinfo),
        "timestamps_local": {
            k: _iso_to_local(v)
            for k, v in ((yinfo.get("timestamps") or {}).items())
            if v
        },
    }


def updated_vs_baseline_status() -> dict:
    """Shallow Updated Yearbook Scans dirs vs baseline hqmax counts (1990–2001)."""
    updated_root = ROOT / "Updated Yearbook Scans"
    years_out: dict[str, dict] = {}
    try:
        upd_dirs = (
            [p for p in updated_root.iterdir() if p.is_dir()]
            if updated_root.is_dir()
            else []
        )
    except OSError:
        upd_dirs = []
    for y in YEARS_ACTIVE:
        matches = [p.name for p in upd_dirs if y in p.name]
        years_out[y] = {
            "year": y,
            "baseline_hqmax": count_hqmax(y),
            "updated_dir_count": len(matches),
            "updated_dirs": matches[:10],
        }
    return {
        "kind": "updated_vs_baseline",
        "updated_root_present": updated_root.is_dir(),
        "baseline_root": str(OCR_BASE.relative_to(ROOT)) if OCR_BASE.is_dir() else None,
        "years": years_out,
        "note": "Updated Yearbook Scans (source scans) vs _ocr_baseline_v2 hqmax counts",
    }


def _year_fail_code_hits(year: str) -> dict[str, int]:
    """Aggregate by_code hit counts across FAIL volumes for one year."""
    path = ROOT / f"_b6b_ingest_audit_{year}.json"
    totals: dict[str, int] = {}
    if not path.is_file():
        return totals
    try:
        raw = json.loads(path.read_text(encoding="utf-8", errors="replace"))
    except (OSError, json.JSONDecodeError):
        return totals
    if not isinstance(raw, dict):
        return totals
    for vol in raw.get("volumes") or []:
        if not isinstance(vol, dict):
            continue
        if str(vol.get("verdict") or "").upper() != "FAIL":
            continue
        by = vol.get("by_code") if isinstance(vol.get("by_code"), dict) else {}
        for code, n in by.items():
            try:
                totals[str(code)] = totals.get(str(code), 0) + int(n)
            except (TypeError, ValueError):
                pass
    return totals


def workstreams_status(b6b: dict, surgical: dict, myears: dict) -> dict:
    """Surface mid-clear / demotion / detector-widen / Updated-tree lanes."""
    years = b6b.get("years") or {}
    fail_years = list(b6b.get("fail_years") or [])
    if not fail_years:
        fail_years = [
            y
            for y, r in years.items()
            if (r.get("b6b_fail") or 0) > 0
            or str(r.get("b6b_verdict") or "").upper() == "FAIL"
        ]

    demotion_years: list[dict] = []
    widen_years: list[dict] = []
    for y in YEARS_ACTIVE:
        hits = _year_fail_code_hits(y)
        if not hits:
            continue
        dem = {c: hits[c] for c in B6B_DEMOTED_TO_FAIL if c in hits}
        wid = {c: hits[c] for c in B6B_DETECTOR_WIDEN if c in hits}
        live = years.get(y) or {}
        if dem:
            demotion_years.append(
                {
                    "year": y,
                    "codes": dem,
                    "b6b_fail": live.get("b6b_fail"),
                    "b6b_pass": live.get("b6b_pass"),
                }
            )
        if wid:
            widen_years.append(
                {
                    "year": y,
                    "codes": wid,
                    "b6b_fail": live.get("b6b_fail"),
                    "b6b_pass": live.get("b6b_pass"),
                }
            )

    mid_clear = {
        "kind": "mid_clear_fail",
        "state": "in_progress" if fail_years else "clear",
        "fail_years": fail_years,
        "rows": [
            {
                "year": y,
                "verdict": (years.get(y) or {}).get("b6b_verdict"),
                "fail": (years.get(y) or {}).get("b6b_fail"),
                "warn": (years.get(y) or {}).get("b6b_warn"),
                "pass": (years.get(y) or {}).get("b6b_pass"),
                "audit_mtime": (years.get(y) or {}).get("audit_mtime"),
                "source": (years.get(y) or {}).get("b6b_source"),
            }
            for y in fail_years
        ],
        "note": (
            "Years with live B6b FAIL>0 (audit-file counts refresh on each status poll)"
            if fail_years
            else "No FAIL residual on 1990–2001 audit files"
        ),
    }

    surg_state = surgical.get("state") or "idle"
    surgical_ws = {
        "kind": "surgical_clears",
        "state": surg_state,
        "running": bool(surgical.get("running")),
        "pids": surgical.get("pids") or [],
        "script": surgical.get("script"),
        "active_log": surgical.get("active_log"),
        "progress_label": surgical.get("progress_label"),
        "job_line": surgical.get("job_line"),
        "page_line": surgical.get("page_line"),
        "note": surgical.get("note")
        or "Single-vol / prove-slice force re-OCR (sibling OCR lane)",
    }

    return {
        "mid_clear_fail": mid_clear,
        "surgical_clears": surgical_ws,
        "b6b_demotion": {
            "kind": "b6b_demotion",
            "state": "active" if demotion_years else "idle",
            "codes": list(B6B_DEMOTED_TO_FAIL),
            "years": demotion_years,
            "note": (
                "Former WARN residuals now FAIL; years still hitting demoted codes"
                if demotion_years
                else "No demoted-code FAIL hits on current audits"
            ),
        },
        "detector_widen": {
            "kind": "detector_widen",
            "state": "active" if widen_years else "idle",
            "codes": list(B6B_DETECTOR_WIDEN),
            "years": widen_years,
            "note": (
                "Detector-widen FAIL codes still firing (header/dropout/smash/trunc)"
                if widen_years
                else "No detector-widen FAIL hits on current audits"
            ),
        },
        "updated_vs_baseline": updated_vs_baseline_status(),
        "audit_proc_running": bool(b6b.get("running")),
    }


def enrich_step(
    sid: str,
    title: str,
    years_touch: list[str],
    handoff: dict[str, dict],
    years_summary: dict[str, dict],
    a2_summary: str,
    ocr_live: dict,
    targeted: dict | None = None,
) -> dict:
    h = handoff.get(sid, {"status": "PENDING", "detail": "not found in handoff"})
    status = h["status"]
    detail = h["detail"]
    lines: list[str] = []
    sections: list[dict] = []

    def _add_section(label: str, body_lines: list[str]) -> None:
        body_lines = [x for x in body_lines if x]
        if body_lines:
            sections.append({"label": label, "lines": body_lines})

    how = h.get("how") or STEP_HOW_FALLBACK.get(sid)
    if h.get("intent"):
        _add_section("Intent", [str(h["intent"])])
    if how:
        _add_section("How", [str(how)])
    if h.get("done"):
        _add_section("Done", [str(h["done"])])
    if h.get("remaining"):
        _add_section("Remaining", [str(h["remaining"])])
    elif h.get("exit"):
        _add_section("Exit", [str(h["exit"])])
    if h.get("snapshot"):
        _add_section("Snapshot", [str(h["snapshot"])])

    def _live_track_lines() -> list[str]:
        ta = ocr_live.get("trackA", {})
        tb = ocr_live.get("trackB", {})
        track_lines: list[str] = []
        log_a = ocr_live.get("log_trackA")
        log_b = ocr_live.get("log_trackB")
        if log_a or log_b:
            track_lines.append(f"logs: {log_a or '—'} / {log_b or '—'}")
        for label, t in (("A", ta), ("B", tb)):
            if not (t.get("job_line_full") or t.get("job") or t.get("exists")):
                continue
            track_lines.append(t.get("job_line_full") or t.get("job") or "")
            track_lines.append(t.get("page_line_full") or t.get("page") or "")
            if t.get("ppm") is not None:
                track_lines.append(
                    f"Track {label}: {t.get('ppm')} ppm · "
                    f"{t.get('elapsed_min')} min wall · "
                    f"{t.get('workers')}w · {t.get('pages_total')} pages"
                )
            if t.get("log_mtime"):
                track_lines.append(f"Track {label} log {t.get('log_mtime')}")
        procs = ocr_live.get("processes") or {}
        if procs.get("alive"):
            track_lines.append(
                f"OCR python PIDs: {', '.join(str(p) for p in (procs.get('pids') or []))}"
            )
        return track_lines

    if sid == "A1":
        hq_line = "hqmax: " + ", ".join(
            f"{y}={years_summary.get(y, {}).get('hqmax_count', 0)}" for y in YEARS
        )
        bits = [hq_line]
        track_lines = _live_track_lines()
        bits.extend(track_lines[:2])
        detail = " — ".join([detail] + bits)
        _add_section("HQ counts", [hq_line])
        _add_section("Live tracks", track_lines)
        lines.extend(track_lines)
    elif sid == "A4":
        a4_lines = [f"{y}: hqmax={count_hqmax(y) if OCR_BASE.is_dir() else 0}" for y in YEARS_9096]
        _add_section("1990–96 HQ counts", a4_lines)
        track_lines = _live_track_lines()
        if track_lines:
            _add_section("Live tracks", track_lines)
            lines.extend(track_lines)
    elif sid == "A5":
        _add_section(
            "Early-year scope",
            [
                "years: " + ", ".join(YEARS_EARLY),
                "sources: EARLY packs + Updated Yearbook Scans 1984–89",
                "queued after A4 tess budget frees (`--phase a5`)",
            ],
        )
        track_lines = _live_track_lines()
        if track_lines:
            _add_section("Live tracks", track_lines)
            lines.extend(track_lines)
    elif sid == "A2":
        detail = f"{detail} | {a2_summary}"
        done_yrs = [y for y, r in years_summary.items() if r.get("a2") == "done"]
        if done_yrs:
            detail += f" | years done: {', '.join(done_yrs)}"
        _add_section("Rollup", [a2_summary])
        for y in YEARS:
            r = years_summary.get(y) or {}
            ad = r.get("a2_detail") or {}
            vol_lines = [
                f"{y}: a2={r.get('a2')} F{r.get('a2_fail')} W{r.get('a2_warn')} P{r.get('a2_pass')} "
                f"unlock={r.get('a2_unlocked')}"
            ]
            if ad.get("rollup"):
                vol_lines.append(str(ad["rollup"]))
            for v in (ad.get("volumes") or [])[:8]:
                vol_lines.append(
                    f"  {v.get('verdict')} · {v.get('file')} · top {v.get('top_codes')}"
                )
            _add_section(f"A2 {y}", vol_lines)
    elif sid == "A3":
        fail_yrs = [
            y
            for y, r in years_summary.items()
            if (r.get("a2_fail") or 0) > 0
        ]
        _add_section(
            "A2 FAIL years (A3 candidates)",
            [", ".join(fail_yrs) if fail_yrs else "none — no A2 FAIL volumes in remediation strip"],
        )
    elif sid == "B6":
        done = [y for y, r in years_summary.items() if r.get("b6") == "done"]
        detail = f"{detail} | B6 done years: {', '.join(done) if done else 'none'}"
        b6_lines = [
            f"{y}: b6={r.get('b6')} sections={r.get('b6_sections')}"
            for y, r in years_summary.items()
        ]
        _add_section("Harvest", b6_lines)
        idx_path = OCR_V2 / "certs" / "cert_sections_index.json"
        if idx_path.is_file():
            try:
                idx = json.loads(idx_path.read_text(encoding="utf-8"))
                by_year: dict[str, int] = {}
                flags = {"nhc": 0, "trial_cert": 0, "bronze": 0}
                if isinstance(idx, list):
                    for it in idx:
                        if not isinstance(it, dict):
                            continue
                        yk = str(it.get("year") or "?")
                        by_year[yk] = by_year.get(yk, 0) + 1
                        if it.get("has_nhc"):
                            flags["nhc"] += 1
                        if it.get("has_trial_cert"):
                            flags["trial_cert"] += 1
                        if it.get("has_bronze"):
                            flags["bronze"] += 1
                idx_lines = [
                    f"index={idx_path.name} entries={len(idx) if isinstance(idx, list) else '?'}",
                    "flags: " + " · ".join(f"{k}×{n}" for k, n in flags.items()),
                    "by year: "
                    + ", ".join(f"{y}={by_year[y]}" for y in sorted(by_year, key=lambda x: (len(x), x))),
                ]
                rem_missing = [y for y in YEARS if by_year.get(y, 0) == 0]
                if rem_missing:
                    idx_lines.append(
                        "remediation years with 0 index rows: " + ", ".join(rem_missing)
                    )
                _add_section("Cert sections index", idx_lines)
            except (OSError, json.JSONDecodeError, TypeError):
                pass
        for log_name in ("_harvest_certs_9798.log", "_harvest_certs_9798.err.log"):
            lp = ROOT / log_name
            if lp.is_file():
                _add_section(
                    "Harvest log",
                    [f"{log_name} mtime={_mtime_local(lp)} size={lp.stat().st_size}"],
                )
                break
    elif sid == "B6b":
        parts = []
        for y, r in years_summary.items():
            if r.get("b6b"):
                parts.append(
                    f"{y}:{r.get('b6b_verdict') or r.get('b6b')} "
                    f"F{r.get('b6b_fail')} W{r.get('b6b_warn')} P{r.get('b6b_pass')} "
                    f"unlock={r.get('b6b_unlocked')}"
                )
        if parts:
            detail = f"{detail} | " + "; ".join(parts)
        _add_section("Year verdicts", parts)
        tgt = (targeted or {}).get("b6b") or {}
        for d in (tgt.get("details") or [])[:6]:
            cat = d.get("by_catalog") or {}
            cat_s = " ".join(f"{k}×{n}" for k, n in list(cat.items())[:8])
            vol_lines = [f"{d.get('year')} {d.get('verdict')} · {cat_s}"]
            for v in (d.get("volumes") or [])[:6]:
                vol_lines.append(
                    f"  {v.get('verdict')} F{v.get('fail_hits')} W{v.get('warn_hits')} · {v.get('file')} · {v.get('top_catalog')}"
                )
                for s in (v.get("samples") or [])[:4]:
                    vol_lines.append(
                        f"    [{s.get('catalog')} {s.get('code')}] {s.get('line')}"
                    )
            _add_section(f"B6b {d.get('year')}", vol_lines)
        for r in years_summary.values():
            if (r.get("b6b_verdict") or "").upper() == "FAIL" or (r.get("b6b_fail") or 0) > 0:
                if status not in ("DONE",):
                    status = "WARN" if status == "IN PROGRESS" else status
                detail += " | note: FAIL residual on a year"
                break
    elif sid == "B7":
        spot = ROOT / "_b7_cert_parse_spot.json"
        if spot.is_file():
            try:
                payload = json.loads(spot.read_text(encoding="utf-8"))
                kinds = payload.get("kinds") or {}
                quarries = payload.get("quarries") or {}
                spot_lines = [
                    f"artifact={spot.name} mtime={_mtime_local(spot)}",
                    f"rows={payload.get('rows')} · missing_dog={payload.get('missing_dog')} · "
                    f"nhc_missing_quarry={payload.get('nhc_missing_quarry')}",
                    "kinds: "
                    + (
                        " · ".join(f"{k}×{n}" for k, n in kinds.items())
                        if isinstance(kinds, dict)
                        else str(kinds)
                    ),
                    "quarries: "
                    + (
                        " · ".join(
                            f"{k}×{n}"
                            for k, n in sorted(
                                quarries.items(), key=lambda kv: -int(kv[1] or 0)
                            )[:8]
                        )
                        if isinstance(quarries, dict)
                        else str(quarries)
                    ),
                ]
                _add_section("Spot-check rollup", spot_lines)
                sample_lines = []
                for s in (payload.get("samples") or [])[:12]:
                    if not isinstance(s, dict):
                        continue
                    sample_lines.append(
                        f"{s.get('year')} {s.get('kind')}: {s.get('dog')} · "
                        f"owner={s.get('owner')} · quarry={s.get('quarry')}"
                    )
                if sample_lines:
                    _add_section("Spot samples", sample_lines)
                top_files = []
                for row in (payload.get("per_file_top") or [])[:10]:
                    if isinstance(row, (list, tuple)) and len(row) >= 2:
                        top_files.append(f"{row[1]}× {row[0]}")
                    elif isinstance(row, dict):
                        top_files.append(
                            f"{row.get('count') or row.get('n')}× {row.get('file') or row.get('name')}"
                        )
                if top_files:
                    _add_section("Top source files", top_files)
            except (OSError, json.JSONDecodeError, TypeError):
                pass
        else:
            _add_section("Spot-check", ["_b7_cert_parse_spot.json not found yet"])
    elif sid == "C10":
        staged = [y for y, r in years_summary.items() if r.get("c10") in ("staged", "done")]
        pending = [y for y, r in years_summary.items() if r.get("c10") not in ("staged", "done")]
        detail = (
            f"{detail} | staged={', '.join(staged) or 'none'} · "
            f"pending={', '.join(pending) or 'none'}"
        )
        _add_section(
            "Normalize staging",
            [
                f"staged: {', '.join(staged) or 'none'}",
                f"pending: {', '.join(pending) or 'none'}",
                "path: _ocr_baseline_v2/trial_results_norm/{year}/",
            ],
        )
        norm_root = OCR_V2 / "trial_results_norm"
        norm_lines = []
        for y in YEARS:
            yd = norm_root / y
            if not yd.is_dir():
                norm_lines.append(f"{y}: (no norm dir)")
                continue
            files = [p for p in yd.rglob("*") if p.is_file()]
            bytes_ = sum(p.stat().st_size for p in files)
            names = ", ".join(p.name for p in sorted(files, key=lambda p: p.name)[:6])
            more = f" (+{len(files) - 6})" if len(files) > 6 else ""
            norm_lines.append(
                f"{y}: files={len(files)} bytes={bytes_} · {names}{more}"
            )
        if norm_lines:
            _add_section("Norm tree", norm_lines)
    elif sid == "D15":
        photo_scripts = [
            "yearbook_extract_photos.py",
            "yearbook_map_photos.py",
            "yearbook_cleanup_photo_names.py",
            "yearbook_resplit_photo_names.py",
        ]
        present = [n for n in photo_scripts if (ROOT / n).is_file()]
        photo_dir = ROOT / "Yearbook Photos"
        n_photos = 0
        if photo_dir.is_dir():
            try:
                n_photos = sum(1 for _ in photo_dir.rglob("*") if _.is_file())
            except OSError:
                n_photos = -1
        _add_section(
            "Photo pipeline",
            [
                f"scripts present: {', '.join(present) or 'none'}",
                f"Yearbook Photos files≈{n_photos if n_photos >= 0 else '?'}",
            ],
        )
        touch = [
            f"{y}: a1={r.get('a1')} a2={r.get('a2')} b6b={r.get('b6b_verdict') or r.get('b6b')} c10={r.get('c10')}"
            for y, r in years_summary.items()
        ]
        if touch:
            _add_section("Related year flags", touch)
    elif sid in ("C11", "C12", "C13", "C14", "B8", "B9", "D16", "D17"):
        touch = [
            f"{y}: a1={r.get('a1')} a2={r.get('a2')} b6b={r.get('b6b_verdict') or r.get('b6b')} c10={r.get('c10')}"
            for y, r in years_summary.items()
            if not years_touch or y in years_touch
        ]
        if touch:
            _add_section("Related year flags", touch)
        if sid == "C11":
            _add_section(
                "Anchor years",
                ["1990 / 1997 / 2001 — parse + validate vs placement counts; B6b audit on samples"],
            )
        elif sid == "B8":
            _add_section(
                "Gate",
                ["Blocked until B6b FAIL=0 on harvest corpus; script yearbook_certs_ingest.py"],
            )
        elif sid == "D17":
            _add_section(
                "Doctrine",
                [
                    "PRIMARY = this handoff + live artifacts; REFERENCE = OCR_PIPELINE.md / catalog notes",
                ],
            )

    # Always include per-touched-year timestamp snapshot when present
    ts_lines = []
    for y in years_touch or list(years_summary):
        r = years_summary.get(y) or {}
        ts = r.get("timestamps_local") or {}
        if ts:
            ts_lines.append(f"{y}: " + ", ".join(f"{k}={v}" for k, v in ts.items()))
    if ts_lines:
        _add_section("Timestamps", ts_lines)

    return {
        "id": sid,
        "title": title,
        "status": status,
        "detail": detail,
        "years_touch": years_touch,
        "intent": h.get("intent"),
        "how": how,
        "exit": h.get("exit"),
        "lines": lines,
        "sections": sections,
    }


def gather() -> dict:
    handoff = parse_handoff_statuses()
    manifest = load_manifest()
    myears = manifest.get("years") or {}
    hq = {y: count_hqmax(y) for y in YEARS_ACTIVE}
    years_summary = {
        y: year_pipeline_row(y, myears.get(y) or {}, hq[y]) for y in YEARS_ACTIVE
    }
    def _newest_track_log(label: str) -> str:
        """Prefer live A4/A5 logs over finished A1 9701 logs when newer."""
        cands = [
            f"_ocr_a4_{label}.log",
            f"_ocr_a5_{label}.log",
            f"_ocr_9701_{label}.log",
        ]
        best = cands[-1]
        best_mtime = -1.0
        for name in cands:
            p = ROOT / name
            if p.is_file():
                mt = p.stat().st_mtime
                if mt >= best_mtime:
                    best_mtime = mt
                    best = name
        return best

    ocr_procs = ocr_processes_alive()
    tess_live = _tess_count_live()
    ocr_track_pids: dict[str, list[int]] = {"trackA": [], "trackB": []}
    ocr_track_cmds: dict[str, list[str]] = {"trackA": [], "trackB": []}
    for row in ocr_procs.get("rows") or []:
        label = _classify_baseline_ocr_track(row.get("cmdline") or "")
        if not label:
            continue
        ocr_track_pids[label].append(row["pid"])
        ocr_track_cmds[label].append(row.get("cmdline") or "")

    def _ocr_track_enriched(label: str) -> dict:
        log_name = _newest_track_log(label)
        cmds = ocr_track_cmds.get(label) or []
        w_cmd = None
        pw_cmd = None
        for cmd in cmds:
            w = _workers_from_cmdline(cmd)
            if w is not None:
                w_cmd = w
            pw = _page_workers_from_cmdline(cmd)
            if pw is not None:
                pw_cmd = pw
        t = parse_ocr_track(
            log_name,
            workers_cmdline=w_cmd,
            page_workers_cmdline=pw_cmd,
            pids=ocr_track_pids.get(label) or [],
            tess_live=tess_live,
        )
        t["kind"] = "baseline_ocr"
        t["label"] = "A" if label == "trackA" else "B"
        t["running"] = bool(ocr_track_pids.get(label))
        t["adjustable"] = True
        return t

    ocr_live = {
        "trackA": _ocr_track_enriched("trackA"),
        "trackB": _ocr_track_enriched("trackB"),
        "processes": ocr_procs,
        "tess_live": tess_live,
        "log_trackA": _newest_track_log("trackA"),
        "log_trackB": _newest_track_log("trackB"),
    }
    c1o6 = c1o6_recover_live()
    reocr = reocr_queue_live()
    surgical = surgical_reocr_live()
    b6b = b6b_ingest_audit_status(myears, bool(c1o6.get("running")))
    targeted_ocr = {
        "c1_o6": c1o6,
        "b6b": b6b,
        "reocr": reocr,
        "surgical": surgical,
        "other": other_targeted_recoveries(c1o6.get("pids") or []),
    }
    workstreams = workstreams_status(b6b, surgical, myears)
    a2_summary = a2_rollup_summary()
    eras = gather_eras(handoff, years_summary)
    steps = [
        enrich_step(
            sid, title, yt, handoff, years_summary, a2_summary, ocr_live, targeted_ocr
        )
        for sid, title, yt in STEP_META
    ]
    counts: dict[str, int] = {}
    for s in steps:
        counts[s["status"]] = counts.get(s["status"], 0) + 1
    return {
        "generated_at": _now_iso(),
        "manifest_updated": _iso_to_local(manifest.get("updated")),
        "timezone": "America/Chicago",
        "steps": steps,
        "years": years_summary,
        "eras": eras,
        "ocr_live": ocr_live,
        "targeted_ocr": targeted_ocr,
        "workstreams": workstreams,
        "a2_rollup": a2_summary,
        "summary": {
            "counts": counts,
            "total_steps": len(steps),
            "hqmax_by_year": hq,
            "b6b_fail_years": b6b.get("fail_years") or [],
        },
    }


def atomic_write_json(path: Path, data: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    payload = json.dumps(data, indent=2, ensure_ascii=False) + "\n"
    fd, tmp = tempfile.mkstemp(prefix=path.name + ".", suffix=".tmp", dir=str(path.parent))
    try:
        with os.fdopen(fd, "w", encoding="utf-8", newline="\n") as f:
            f.write(payload)
            f.flush()
            os.fsync(f.fileno())
        os.replace(tmp, path)
    except Exception:
        try:
            os.unlink(tmp)
        except OSError:
            pass
        raise


def main() -> int:
    data = gather()
    atomic_write_json(OUT, data)
    c = data["summary"]["counts"]
    print(f"Wrote {OUT.name} at {data['generated_at']}")
    print("summary:", ", ".join(f"{k}={v}" for k, v in sorted(c.items())))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
