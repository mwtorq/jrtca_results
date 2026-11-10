#!/usr/bin/env python3
"""Cloud/Linux adapt of dashboard track-worker retune.

Same public API as ``dashboard/track_worker_control.py``:
``set_track_workers(kind, track, workers, page_workers)``.

On Linux (this cloud VM), OCR PIDs usually live on Ldahsar (Windows). Behavior:
1. If ``JRTCA_WORKER_CONTROL_PROXY`` is set (e.g. ``http://ldahsar:8765``),
   POST the same JSON to that host's ``/api/track/set-workers`` and return it.
2. Else return a structured remote-hint payload (``ok: false``) so the UI
   Apply button still works end-to-end without pretending a local restart happened.

Windows path (PowerShell / WMI) is retained for parity if this module is ever
run on the OCR host directly.
"""
from __future__ import annotations

import json
import os
import re
import subprocess
import time
import urllib.error
import urllib.request
from datetime import datetime
from pathlib import Path

CLOUD_DIR = Path(__file__).resolve().parent
REPO_ROOT = CLOUD_DIR.parent.parent
# Windows OCR host python (only used when os.name == "nt")
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


def _remote_hint(kind: str, track: str, workers: int, page_workers: int) -> dict:
    proxy = (os.environ.get("JRTCA_WORKER_CONTROL_PROXY") or "").strip()
    return {
        "ok": False,
        "cloud": True,
        "kind": kind,
        "track": track,
        "workers": workers,
        "page_workers": page_workers,
        "error": (
            "Worker retune is not executed on this Linux cloud VM "
            "(OCR / re-OCR processes run on Ldahsar). "
            "Use the Windows dashboard at :8765, or set JRTCA_WORKER_CONTROL_PROXY "
            "to that host (e.g. http://ldahsar:8765)."
        ),
        "remote_hint": {
            "windows_dashboard": "python -u dashboard/serve_pipeline_dashboard.py --port 8765",
            "api": "POST /api/track/set-workers",
            "body": {
                "kind": kind,
                "track": track,
                "workers": workers,
                "page_workers": page_workers,
            },
            "proxy_env": "JRTCA_WORKER_CONTROL_PROXY",
            "proxy_set": bool(proxy),
            "proxy_url": proxy or None,
        },
        "prior_ppm": None,
        "prior_pages": None,
        "prior_mins": None,
        "prior_workers": None,
        "stopped_pids": [],
        "wiped_partials": 0,
        "new_pids": [],
        "log": None,
        "launch": None,
    }


def _proxy_set_workers(kind: str, track: str, workers: int, page_workers: int) -> dict | None:
    base = (os.environ.get("JRTCA_WORKER_CONTROL_PROXY") or "").strip().rstrip("/")
    if not base:
        return None
    url = base + "/api/track/set-workers"
    payload = json.dumps(
        {
            "kind": kind,
            "track": track,
            "workers": workers,
            "page_workers": page_workers,
        }
    ).encode("utf-8")
    req = urllib.request.Request(
        url,
        data=payload,
        headers={"Content-Type": "application/json"},
        method="POST",
    )
    try:
        with urllib.request.urlopen(req, timeout=120) as resp:
            raw = resp.read().decode("utf-8", errors="replace")
            data = json.loads(raw) if raw else {}
            if isinstance(data, dict):
                data = dict(data)
                data["proxied"] = True
                data["proxy_url"] = url
                return data
            return {"ok": False, "error": "proxy returned non-object", "proxied": True}
    except urllib.error.HTTPError as exc:
        body = ""
        try:
            body = exc.read().decode("utf-8", errors="replace")
            parsed = json.loads(body) if body else {}
            if isinstance(parsed, dict):
                parsed = dict(parsed)
                parsed["proxied"] = True
                parsed["proxy_url"] = url
                parsed["proxy_http"] = exc.code
                return parsed
        except Exception:
            pass
        return {
            "ok": False,
            "error": f"proxy HTTP {exc.code}: {body[:300]}",
            "proxied": True,
            "proxy_url": url,
        }
    except Exception as exc:
        return {
            "ok": False,
            "error": f"proxy failed: {exc}",
            "proxied": True,
            "proxy_url": url,
        }


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
    """Restart one force-reOCR track with new --workers (WMI-detached; Windows only)."""
    track = track.upper().strip()
    if track not in REOCR_TRACKS:
        return {"ok": False, "error": f"unknown reocr track {track}"}
    workers = max(1, min(16, int(workers)))
    page_workers = max(1, min(8, int(page_workers)))
    meta = REOCR_TRACKS[track]
    log_path = REPO_ROOT / meta["log"]

    rows = _list_python(meta["match"])
    victims: list[dict] = []
    for row in rows:
        ys = _years_from_cmd(row["cmd"])
        if ys == set(meta["year_need"]) or ys <= set(meta["year_need"]):
            if ys & set(meta["year_need"]):
                victims.append(row)
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
    """Restart a live baseline OCR track (Windows only)."""
    track = track.upper().strip()
    if track not in ("A", "B"):
        return {"ok": False, "error": f"unknown baseline track {track}"}
    workers = max(1, min(16, int(workers)))
    page_workers = max(1, min(8, int(page_workers)))

    rows = _list_python(r"ocr_yearbook_baseline_v2|ocr_yearbook")
    victims: list[dict] = []
    for row in rows:
        cmd = row["cmd"]
        low = cmd.lower()
        hit = False
        if f"track{track.lower()}" in low:
            hit = True
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

    log_name = None
    m = re.search(r"(_ocr_\w+_track[AB]\.log)", victims[0]["cmd"], re.I)
    if m:
        log_name = m.group(1)
    if not log_name:
        log_name = f"_ocr_live_track{track}.log"
    log_path = REPO_ROOT / log_name

    prior = _prior_ppm_from_log(log_path)
    prior_workers = _workers_from_cmd(victims[0]["cmd"])

    old_cmd = victims[0]["cmd"]
    mpy = re.search(r'python(?:\.exe)?["\s]+(-u\s+)?(.+)$', old_cmd, re.I)
    rest = mpy.group(2).strip() if mpy else old_cmd
    rest = re.sub(r"--workers\s+\d+", "", rest)
    rest = re.sub(r"--page-workers\s+\d+", "", rest)
    rest = re.sub(r"\s+", " ", rest).strip()
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
    kind_norm = (kind or "").strip().lower()
    if kind_norm in ("reocr", "force", "force_reocr"):
        kind_out = "reocr"
    elif kind_norm in ("ocr", "baseline", "baseline_ocr", "a1"):
        kind_out = "baseline"
    else:
        return {"ok": False, "error": f"unknown kind {kind} (use reocr|baseline)"}

    # Linux cloud: proxy or remote-hint (do not run Windows WMI locally).
    if os.name != "nt":
        proxied = _proxy_set_workers(kind_out, track, workers, page_workers)
        if proxied is not None:
            return proxied
        return _remote_hint(kind_out, track, workers, page_workers)

    if kind_out == "reocr":
        return set_reocr_workers(track, workers, page_workers)
    return set_baseline_ocr_workers(track, workers, page_workers)
