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

STEP_META = [
    ("A1", "Force HQ re-OCR 1997–2001 into baseline v2", ["1997", "1998", "1999", "2000", "2001"]),
    ("A2", "Quality gate on baseline samples", ["1997", "1998", "1999", "2000", "2001"]),
    ("A3", "Targeted fix + re-OCR bad volumes", ["1997", "1998", "1999", "2000", "2001"]),
    ("A4", "HQ baseline 1990–96 yearbook volumes", ["1990", "1991", "1992", "1993", "1994", "1995", "1996"]),
    ("A5", "HQ OCR 1984–90 non-yearbook (early packs)", ["1984", "1985", "1986", "1987", "1988", "1989", "1990"]),
    ("B6", "Re-harvest cert sections from baseline v2", ["1997", "1998", "1999", "2000", "2001"]),
    ("B6b", "Catalog cleanup + ingest audit gate", ["1997", "1998", "1999", "2000", "2001"]),
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
        # First Intent line as detail seed
        intent_m = re.search(r"^\*\*Intent:\*\*\s*(.+)$", body, re.MULTILINE)
        snapshot_m = re.search(r"^\*\*Snapshot:\*\*\s*(.+)$", body, re.MULTILINE)
        detail_parts = [raw]
        if snapshot_m:
            detail_parts.append(snapshot_m.group(1).strip())
        elif intent_m:
            detail_parts.append(intent_m.group(1).strip()[:160])
        out[sid] = {"status": norm, "detail": " — ".join(detail_parts)}
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


def parse_ocr_track(log_name: str) -> dict:
    """Parse last OCR job + page from a track log (full paths; no short slice).

    Session PPM uses page-line count / wall minutes. Log birth→now is treated as
    summed tess-worker minutes (N workers accumulate in parallel); divide by
    workers=N from the track start line so elapsed/PPM are wall-clock.
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
    workers = None
    job_re = re.compile(r"OCR\s+(\d+)/(\d+)\s+y=(\d{4})\s+(.+)")
    page_re = re.compile(r"OCR page\s+(\d+)\b")
    workers_re = re.compile(r"\bworkers=(\d+)\b")
    # Job lines are sparse (often early in the log); page lines are dense near the end.
    # Stream the whole file for last job + page counts; tail window for last page display.
    if path.is_file():
        try:
            with path.open("r", encoding="utf-8", errors="replace") as f:
                for line in f:
                    if workers is None:
                        wm = workers_re.search(line)
                        if wm:
                            workers = max(1, int(wm.group(1)))
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
            # Birth→now sums parallel tess slots; collapse to wall minutes.
            worker_min = max((end - start) / 60.0, 0.01)
            elapsed_min = max(worker_min / max(workers, 1), 0.01)
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
    """Prep UI data for live 1997–2001 + parked A4/A5 eras (do not pretend running)."""
    a4_status, a4_detail = _handoff_step_status(handoff, "A4")
    a5_status, a5_detail = _handoff_step_status(handoff, "A5")

    y9096: dict[str, dict] = {}
    for y in YEARS_9096:
        hq = count_hqmax(y)
        if hq > 0:
            y_status = "partial"
        elif a4_status.upper() in ("PENDING", "BLOCKED"):
            y_status = "parked"
        else:
            y_status = a4_status.lower().replace(" ", "_")
        y9096[y] = {
            "year": y,
            "hqmax_count": hq,
            "status": y_status,
        }

    era9096_status = "parked"
    if any(r["hqmax_count"] > 0 for r in y9096.values()):
        era9096_status = "partial"
    if a4_status.upper() == "IN PROGRESS":
        era9096_status = "in_progress"
    elif a4_status.upper() == "DONE":
        era9096_status = "done"

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
            "note": "Active remediation strip (manifest years).",
            "years": {y: years_summary[y] for y in YEARS if y in years_summary},
        },
        "yearbook_1990_1996": {
            "label": "1990–1996 yearbook",
            "status": era9096_status,
            "plan_step": "A4",
            "plan_status": a4_status,
            "detail": a4_detail,
            "note": "A4 parked — placeholders from hqmax under yearbook_1990_2001/{year}.",
            "years": y9096,
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
    return {"alive": bool(pids), "pids": pids}


def _parse_years_from_cmdline(cmdline: str) -> list[int]:
    m = re.search(r"--years\s+((?:\d{4}\s*)+)", cmdline or "", re.I)
    if not m:
        return []
    return [int(x) for x in re.findall(r"\d{4}", m.group(1))]


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
    for y in YEARS_B6B_ALL:
        yinfo = myears.get(y) or {}
        ts = yinfo.get("timestamps") or {}
        file_bits = _b6b_verdict_from_audit_md(y)
        # Manifest wins when present; audit md fills gaps / early years
        verdict = yinfo.get("b6b_verdict") or file_bits.get("b6b_verdict")
        b6b = yinfo.get("b6b") or file_bits.get("b6b")
        if y < "1997" and not b6b and not verdict:
            b6b = "parked"
            era = "early" if y < "1990" else "yearbook_9096"
        elif not b6b and not verdict:
            b6b = "pending"
            era = "remediation"
        else:
            era = "remediation" if y >= "1997" else ("early" if y < "1990" else "yearbook_9096")
        detail = _b6b_detail_from_audit_json(y) if verdict in ("FAIL", "WARN") or (
            (file_bits.get("b6b_fail") or 0) > 0 or (file_bits.get("b6b_warn") or 0) > 0
        ) else {"volumes": [], "by_catalog": {}, "fail_samples": [], "warn_samples": []}
        years_out[y] = {
            "b6b": b6b,
            "b6b_verdict": verdict,
            "b6b_unlocked": yinfo.get("b6b_unlocked")
            if "b6b_unlocked" in yinfo
            else file_bits.get("b6b_unlocked"),
            "b6b_fail": yinfo.get("b6b_fail")
            if yinfo.get("b6b_fail") is not None
            else file_bits.get("b6b_fail"),
            "b6b_warn": yinfo.get("b6b_warn")
            if yinfo.get("b6b_warn") is not None
            else file_bits.get("b6b_warn"),
            "b6b_pass": yinfo.get("b6b_pass")
            if yinfo.get("b6b_pass") is not None
            else file_bits.get("b6b_pass"),
            "b6b_done": _iso_to_local(ts.get("b6b_done")) or file_bits.get("b6b_done"),
            "era": era,
            "by_catalog": detail.get("by_catalog") or {},
            "volumes": detail.get("volumes") or [],
        }
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
        note = "assess_ingest_quality_audit process alive"
    elif recover_running:
        state = "pending_rerun"
        note = "C1/O6 recover still running -> B6b re-run pending (not executing now)"
    else:
        any_done = any(
            (v.get("b6b") == "done") or v.get("b6b_verdict")
            for v in years_out.values()
        )
        state = "idle_with_results" if any_done else "idle"
        note = "Years 1984–2001 · early/parked until remediation reaches them"

    return {
        "kind": "b6b_ingest_audit",
        "state": state,
        "running": audit_proc["alive"],
        "pids": audit_proc["pids"],
        "recover_still_running": recover_running,
        "note": note,
        "years": years_out,
        "details": details,
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
        "b6": yinfo.get("b6", "pending"),
        "b6_sections": yinfo.get("b6_sections"),
        "b6b": yinfo.get("b6b", "pending"),
        "b6b_verdict": yinfo.get("b6b_verdict"),
        "b6b_unlocked": yinfo.get("b6b_unlocked"),
        "b6b_fail": yinfo.get("b6b_fail"),
        "b6b_warn": yinfo.get("b6b_warn"),
        "b6b_pass": yinfo.get("b6b_pass"),
        "b6b_done": _iso_to_local(
            (yinfo.get("timestamps") or {}).get("b6b_done")
        ),
        "c10": yinfo.get("c10", "pending"),
        "hqmax_count": hqmax,
        "b6b_detail": b6b_year_detail(year, yinfo),
        "timestamps_local": {
            k: _iso_to_local(v)
            for k, v in ((yinfo.get("timestamps") or {}).items())
            if v
        },
    }


def enrich_step(
    sid: str,
    title: str,
    years_touch: list[str],
    handoff: dict[str, dict],
    years_summary: dict[str, dict],
    a2_summary: str,
    ocr_live: dict,
) -> dict:
    h = handoff.get(sid, {"status": "PENDING", "detail": "not found in handoff"})
    status = h["status"]
    detail = h["detail"]

    if sid == "A1":
        bits = [f"hqmax: " + ", ".join(f"{y}={years_summary.get(y, {}).get('hqmax_count', 0)}" for y in YEARS)]
        ta = ocr_live.get("trackA", {})
        tb = ocr_live.get("trackB", {})

        def _track_bit(label: str, t: dict) -> str:
            page = t.get("page_line_full") or t.get("page") or ""
            job = t.get("job_line_full") or t.get("job") or ""
            return f"{label}: {page} | {job}"

        if ta.get("job_line_full") or ta.get("job"):
            bits.append(_track_bit("A", ta))
        if tb.get("job_line_full") or tb.get("job"):
            bits.append(_track_bit("B", tb))
        detail = " — ".join([detail] + bits)
    elif sid == "A2":
        detail = f"{detail} | {a2_summary}"
        # Reflect year flags
        done_yrs = [y for y, r in years_summary.items() if r.get("a2") == "done"]
        if done_yrs:
            detail += f" | years done: {', '.join(done_yrs)}"
    elif sid == "B6":
        done = [y for y, r in years_summary.items() if r.get("b6") == "done"]
        detail = f"{detail} | B6 done years: {', '.join(done) if done else 'none'}"
    elif sid == "B6b":
        parts = []
        for y, r in years_summary.items():
            if r.get("b6b"):
                parts.append(f"{y}:{r.get('b6b_verdict') or r.get('b6b')} unlock={r.get('b6b_unlocked')}")
        if parts:
            detail = f"{detail} | " + "; ".join(parts)
        # Escalate status if any FAIL verdict
        for r in years_summary.values():
            if (r.get("b6b_verdict") or "").upper() == "FAIL" or (r.get("b6b_fail") or 0) > 0:
                if status not in ("DONE",):
                    status = "WARN" if status == "IN PROGRESS" else status
                detail += " | note: FAIL residual on a year"
                break
    elif sid == "C10":
        pending = [y for y, r in years_summary.items() if r.get("c10") != "done"]
        detail = f"{detail} | c10 pending years: {', '.join(pending) if pending else 'none'}"

    return {
        "id": sid,
        "title": title,
        "status": status,
        "detail": detail,
        "years_touch": years_touch,
    }


def gather() -> dict:
    handoff = parse_handoff_statuses()
    manifest = load_manifest()
    myears = manifest.get("years") or {}
    hq = {y: count_hqmax(y) for y in YEARS}
    years_summary = {
        y: year_pipeline_row(y, myears.get(y) or {}, hq[y]) for y in YEARS
    }
    ocr_live = {
        "trackA": parse_ocr_track("_ocr_9701_trackA.log"),
        "trackB": parse_ocr_track("_ocr_9701_trackB.log"),
        "processes": ocr_processes_alive(),
    }
    c1o6 = c1o6_recover_live()
    targeted_ocr = {
        "c1_o6": c1o6,
        "b6b": b6b_ingest_audit_status(myears, bool(c1o6.get("running"))),
        "other": other_targeted_recoveries(c1o6.get("pids") or []),
    }
    a2_summary = a2_rollup_summary()
    eras = gather_eras(handoff, years_summary)
    steps = [
        enrich_step(sid, title, yt, handoff, years_summary, a2_summary, ocr_live)
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
        "a2_rollup": a2_summary,
        "summary": {
            "counts": counts,
            "total_steps": len(steps),
            "hqmax_by_year": hq,
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
