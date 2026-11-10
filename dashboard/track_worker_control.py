#!/usr/bin/env python3
"""Local-only helpers to retune OCR / force-reOCR track worker counts via restart.

Used by ``serve_pipeline_dashboard.py`` POST ``/api/track/set-workers``.
Restarts are WMI-detached (outside Cursor job). Wipes ``*.partial.txt``.
"""
from __future__ import annotations

import re
import subprocess
import time
from datetime import datetime
from pathlib import Path

DASHBOARD_DIR = Path(__file__).resolve().parent
REPO_ROOT = DASHBOARD_DIR.parent
PY = Path(r"C:\Users\mw\AppData\Local\Python\pythoncore-3.14-64\python.exe")

REOCR_TRACKS = {
    "A": {
        "years": [1998, 2000],
        "log": "_reocr_9800_trackA.log",
        "err": "_reocr_9800_trackA.err.log",
        "launcher": "_launch_reocr_trackA_9800.cmd",
        "match": "schedule_reocr_from_queue",
        "year_need": {1998, 2000},
    },
    "B": {
        "years": [1999, 2001],
        "log": "_reocr_9901_trackB.log",
        "err": "_reocr_9901_trackB.err.log",
        "launcher": "_launch_reocr_trackB_9901.cmd",
        "match": "schedule_reocr_from_queue",
        "year_need": {1999, 2001},
    },
}


def _now_stamp() -> str:
    return datetime.now().astimezone().strftime("%Y-%m-%dT%H:%M:%S%z")


def _ps(cmd: str, timeout: int = 60) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        ["powershell", "-NoProfile", "-Command", cmd],
        capture_output=True,
        text=True,
        timeout=timeout,
        cwd=str(REPO_ROOT),
    )


def _list_python(match: str) -> list[dict]:
    ps = (
        "Get-CimInstance Win32_Process -Filter \"Name='python.exe'\" | "
        f"Where-Object {{ $_.CommandLine -match '{match}' }} | "
        "ForEach-Object { '{0}|{1}' -f $_.ProcessId, $_.CommandLine }"
    )
    r = _ps(ps, timeout=20)
    out: list[dict] = []
    for line in (r.stdout or "").splitlines():
        line = line.strip()
        if "|" not in line:
            continue
        pid_s, cmd = line.split("|", 1)
        if pid_s.isdigit():
            out.append({"pid": int(pid_s), "cmd": cmd.strip()})
    return out


def _years_from_cmd(cmd: str) -> set[int]:
    m = re.search(r"--years\s+((?:\d{4}\s*)+)", cmd or "", re.I)
    if not m:
        return set()
    return {int(x) for x in re.findall(r"\d{4}", m.group(1))}


def _workers_from_cmd(cmd: str) -> int | None:
    m = re.search(r"--workers\s+(\d+)", cmd or "", re.I)
    return int(m.group(1)) if m else None


def _prior_ppm_from_log(log_path: Path, proc_start_iso: str | None = None) -> dict:
    """Best-effort prior PPM from OCR page lines vs log mtime/start."""
    if not log_path.is_file():
        return {"pages": 0, "mins": None, "ppm": None}
    text = log_path.read_text(encoding="utf-8", errors="replace")
    pages = len(re.findall(r"OCR page\s+\d+", text))
    st = log_path.stat()
    end = st.st_mtime
    start = getattr(st, "st_ctime", None) or st.st_mtime
    mins = max((end - start) / 60.0, 0.01)
    ppm = round(pages / mins, 2) if pages else None
    return {"pages": pages, "mins": round(mins, 1), "ppm": ppm}


def _wipe_partials() -> int:
    n = 0
    base = REPO_ROOT / "_ocr_baseline_v2"
    if not base.is_dir():
        return 0
    for p in base.rglob("*.partial.txt"):
        try:
            p.unlink()
            n += 1
        except OSError:
            pass
    return n


def _stop_pids(pids: list[int]) -> None:
    for pid in pids:
        _ps(f"Stop-Process -Id {pid} -Force -ErrorAction SilentlyContinue", timeout=15)
    time.sleep(1.5)
    _ps(
        "Get-Process tesseract -ErrorAction SilentlyContinue | "
        "Stop-Process -Force -ErrorAction SilentlyContinue",
        timeout=15,
    )
    time.sleep(1.0)


def _wmi_launch_cmd(cmd_path: Path) -> dict:
    # Win32_Process.Create via PowerShell
    ps = (
        f"$r = Invoke-CimMethod -ClassName Win32_Process -MethodName Create "
        f"-Arguments @{{ CommandLine = 'cmd.exe /c \"{cmd_path}\"'; "
        f"CurrentDirectory = '{REPO_ROOT}' }}; "
        "\"{0}|{1}\" -f $r.ReturnValue, $r.ProcessId"
    )
    r = _ps(ps, timeout=30)
    line = (r.stdout or "").strip().splitlines()
    last = line[-1] if line else "1|0"
    parts = last.split("|")
    return {
        "return": int(parts[0]) if parts and parts[0].isdigit() else 1,
        "cmd_pid": int(parts[1]) if len(parts) > 1 and parts[1].isdigit() else None,
        "raw": last,
    }


def set_reocr_workers(track: str, workers: int, page_workers: int = 2) -> dict:
    """Restart one force-reOCR track with new --workers (WMI-detached)."""
    track = track.upper().strip()
    if track not in REOCR_TRACKS:
        return {"ok": False, "error": f"unknown reocr track {track}"}
    workers = max(1, min(16, int(workers)))
    page_workers = max(1, min(8, int(page_workers)))
    meta = REOCR_TRACKS[track]
    log_path = REPO_ROOT / meta["log"]

    # Find matching live process(es)
    rows = _list_python(meta["match"])
    victims: list[dict] = []
    for row in rows:
        ys = _years_from_cmd(row["cmd"])
        if ys == set(meta["year_need"]) or ys <= set(meta["year_need"]):
            if ys & set(meta["year_need"]):
                victims.append(row)
    # Prefer exact year-set match
    exact = [v for v in victims if _years_from_cmd(v["cmd"]) == set(meta["year_need"])]
    if exact:
        victims = exact

    prior = _prior_ppm_from_log(log_path)
    prior_workers = None
    if victims:
        prior_workers = _workers_from_cmd(victims[0]["cmd"])

    _stop_pids([v["pid"] for v in victims])
    wiped = _wipe_partials()

    year_args = " ".join(str(y) for y in meta["years"])
    launcher = REPO_ROOT / meta["launcher"]
    err = REPO_ROOT / meta["err"]
    py = str(PY)
    launcher.write_text(
        "\n".join(
            [
                "@echo off",
                f'cd /d "{REPO_ROOT}"',
                f'echo [%date% %time%] WMI_LAUNCH track=reocr{track} years={year_args} workers={workers}>> "{log_path}"',
                f'"{py}" -u schedule_reocr_from_queue.py --years {year_args} '
                f"--workers {workers} --page-workers {page_workers} "
                f'>> "{log_path}" 2>> "{err}"',
                f'echo [%date% %time%] WMI_EXIT track=reocr{track} exit=%ERRORLEVEL%>> "{log_path}"',
                "",
            ]
        ),
        encoding="ascii",
        errors="replace",
    )
    stamp = _now_stamp()
    with log_path.open("a", encoding="utf-8") as f:
        f.write("\n")
        f.write(
            f"[{stamp}] === DASHBOARD RESTART reocr Track {track} workers={workers} === "
            f"prior_ppm={prior.get('ppm')} pages={prior.get('pages')} mins={prior.get('mins')} "
            f"prior_workers={prior_workers} wiped_partials={wiped}\n"
        )

    launch = _wmi_launch_cmd(launcher)
    time.sleep(4)
    after = [
        r
        for r in _list_python(meta["match"])
        if _years_from_cmd(r["cmd"]) == set(meta["year_need"])
        or (
            _years_from_cmd(r["cmd"]) <= set(meta["year_need"])
            and _years_from_cmd(r["cmd"]) & set(meta["year_need"])
        )
    ]
    return {
        "ok": launch.get("return") == 0 and bool(after),
        "kind": "reocr",
        "track": track,
        "workers": workers,
        "page_workers": page_workers,
        "prior_ppm": prior.get("ppm"),
        "prior_pages": prior.get("pages"),
        "prior_mins": prior.get("mins"),
        "prior_workers": prior_workers,
        "stopped_pids": [v["pid"] for v in victims],
        "wiped_partials": wiped,
        "new_pids": [a["pid"] for a in after],
        "log": meta["log"],
        "launch": launch,
    }


def set_baseline_ocr_workers(track: str, workers: int, page_workers: int = 2) -> dict:
    """Restart a live baseline ``ocr_yearbook_baseline_v2`` track with new workers.

    Requires a currently running process for that track (cmdline has track token or
    classifiable years). Preserves ``--years`` / other flags from the old cmdline
    except ``--workers`` / ``--page-workers``.
    """
    track = track.upper().strip()
    if track not in ("A", "B"):
        return {"ok": False, "error": f"unknown baseline track {track}"}
    workers = max(1, min(16, int(workers)))
    page_workers = max(1, min(8, int(page_workers)))

    rows = _list_python(r"ocr_yearbook_baseline_v2|ocr_yearbook")
    label = f"track{track}"
    victims: list[dict] = []
    for row in rows:
        cmd = row["cmd"]
        low = cmd.lower()
        hit = False
        if f"track{track.lower()}" in low:
            hit = True
        # also match redirected log names in cmdline if present
        if f"_track{track.lower()}.log" in low:
            hit = True
        if hit:
            victims.append(row)
    if not victims:
        return {
            "ok": False,
            "error": (
                f"no live baseline OCR Track {track} process to retune; "
                "start ocr_yearbook_baseline_v2 first"
            ),
            "kind": "baseline_ocr",
            "track": track,
        }

    # Infer log from cmdline redirect if present; else default newest naming
    log_name = None
    m = re.search(r"(_ocr_\w+_track[AB]\.log)", victims[0]["cmd"], re.I)
    if m:
        log_name = m.group(1)
    if not log_name:
        log_name = f"_ocr_live_track{track}.log"
    log_path = REPO_ROOT / log_name

    prior = _prior_ppm_from_log(log_path)
    prior_workers = _workers_from_cmd(victims[0]["cmd"])

    # Rebuild argv: replace workers flags; keep script path + years etc.
    old_cmd = victims[0]["cmd"]
    # Strip leading python exe quotes
    mpy = re.search(r'python(?:\.exe)?["\s]+(-u\s+)?(.+)$', old_cmd, re.I)
    rest = mpy.group(2).strip() if mpy else old_cmd
    # Remove existing workers flags
    rest = re.sub(r"--workers\s+\d+", "", rest)
    rest = re.sub(r"--page-workers\s+\d+", "", rest)
    rest = re.sub(r"\s+", " ", rest).strip()
    # Ensure script-relative invocation from repo root
    new_args = f"{rest} --workers {workers} --page-workers {page_workers}"

    _stop_pids([v["pid"] for v in victims])
    wiped = _wipe_partials()

    launcher = REPO_ROOT / f"_launch_ocr_track{track}_dashboard.cmd"
    err = REPO_ROOT / f"{Path(log_name).stem}.err.log"
    py = str(PY)
    launcher.write_text(
        "\n".join(
            [
                "@echo off",
                f'cd /d "{REPO_ROOT}"',
                f'echo [%date% %time%] WMI_LAUNCH baseline track={track} workers={workers}>> "{log_path}"',
                f'"{py}" -u {new_args} >> "{log_path}" 2>> "{err}"',
                f'echo [%date% %time%] WMI_EXIT baseline track={track} exit=%ERRORLEVEL%>> "{log_path}"',
                "",
            ]
        ),
        encoding="ascii",
        errors="replace",
    )
    stamp = _now_stamp()
    with log_path.open("a", encoding="utf-8") as f:
        f.write("\n")
        f.write(
            f"[{stamp}] === DASHBOARD RESTART baseline Track {track} workers={workers} === "
            f"prior_ppm={prior.get('ppm')} pages={prior.get('pages')} mins={prior.get('mins')} "
            f"prior_workers={prior_workers} wiped_partials={wiped}\n"
        )
    launch = _wmi_launch_cmd(launcher)
    time.sleep(4)
    after = _list_python(r"ocr_yearbook_baseline_v2|ocr_yearbook")
    after_w = [a for a in after if _workers_from_cmd(a["cmd"]) == workers]
    if not after_w:
        after_w = after
    return {
        "ok": launch.get("return") == 0 and bool(after_w),
        "kind": "baseline_ocr",
        "track": track,
        "workers": workers,
        "page_workers": page_workers,
        "prior_ppm": prior.get("ppm"),
        "prior_pages": prior.get("pages"),
        "prior_mins": prior.get("mins"),
        "prior_workers": prior_workers,
        "stopped_pids": [v["pid"] for v in victims],
        "wiped_partials": wiped,
        "new_pids": [a["pid"] for a in after_w],
        "log": log_name,
        "launch": launch,
        "cmdline_tail": new_args[:240],
    }


def set_track_workers(
    kind: str, track: str, workers: int, page_workers: int = 2
) -> dict:
    kind = (kind or "").strip().lower()
    if kind in ("reocr", "force", "force_reocr"):
        return set_reocr_workers(track, workers, page_workers)
    if kind in ("ocr", "baseline", "baseline_ocr", "a1"):
        return set_baseline_ocr_workers(track, workers, page_workers)
    return {"ok": False, "error": f"unknown kind {kind} (use reocr|baseline)"}
