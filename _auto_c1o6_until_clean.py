#!/usr/bin/env python3
"""Autonomous C1/O6 recover → B6b loop for 1997–98 until clean or plateau.

Clean = recover PLAN pages_todo==0 (and o6_todo==0).
Plateau = two consecutive full cycles with pages_todo not decreasing.
Then advance A2/B6/B6b + optional C10 staging.

Usage:
  python -u _auto_c1o6_until_clean.py
  python -u _auto_c1o6_until_clean.py --max-passes 6 --no-c10
"""
from __future__ import annotations

import argparse
import re
import subprocess
import sys
import time
from datetime import datetime
from pathlib import Path
from zoneinfo import ZoneInfo

ROOT = Path(__file__).resolve().parent
PY = sys.executable
TZ = ZoneInfo("America/Chicago")
YEARS = ["1997", "1998"]
AUTO_LOG = ROOT / "_auto_c1o6_until_clean.log"


def _ts() -> str:
    return datetime.now(TZ).strftime("%Y-%m-%d %H:%M:%S %Z").replace("Central Daylight Time", "CDT").replace("Central Standard Time", "CST")


def log(msg: str) -> None:
    line = f"[{_ts()}] {msg}"
    print(line, flush=True)
    with AUTO_LOG.open("a", encoding="utf-8") as f:
        f.write(line + "\n")


def run(args: list[str], log_path: Path, err_path: Path) -> int:
    log("RUN " + " ".join(args) + f" -> {log_path.name}")
    with log_path.open("w", encoding="utf-8") as out, err_path.open("w", encoding="utf-8") as err:
        p = subprocess.run(
            args,
            cwd=str(ROOT),
            stdout=out,
            stderr=err,
            env={**dict(**{k: v for k, v in __import__("os").environ.items()}), "PYTHONUNBUFFERED": "1"},
        )
    return int(p.returncode)


def parse_plan(text: str) -> dict[str, int] | None:
    m = None
    for m in re.finditer(
        r"PLAN pages_todo=(\d+) c1_todo=(\d+) o6_todo=(\d+)",
        text,
    ):
        pass
    if not m:
        return None
    return {
        "pages_todo": int(m.group(1)),
        "c1_todo": int(m.group(2)),
        "o6_todo": int(m.group(3)),
    }


def parse_done(text: str) -> bool:
    return bool(re.search(r"^DONE files=", text, re.M))


def recover_running() -> bool:
    try:
        import psutil  # type: ignore
    except ImportError:
        # Fallback: tasklist / fragile
        out = subprocess.run(
            ["powershell", "-NoProfile", "-Command",
             "Get-CimInstance Win32_Process -Filter \"Name='python.exe'\" | "
             "Where-Object { $_.CommandLine -match 'recover_ocr_gaps_targeted' } | "
             "Measure-Object | Select-Object -ExpandProperty Count"],
            capture_output=True,
            text=True,
            cwd=str(ROOT),
        )
        try:
            return int((out.stdout or "0").strip() or "0") > 0
        except ValueError:
            return False
    for proc in psutil.process_iter(["name", "cmdline"]):
        try:
            if (proc.info.get("name") or "").lower() != "python.exe":
                continue
            cmd = " ".join(proc.info.get("cmdline") or [])
            if "recover_ocr_gaps_targeted" in cmd:
                return True
        except (psutil.Error, TypeError):
            continue
    return False


def wait_for_existing_recover(timeout_sec: int = 60 * 60 * 8) -> Path | None:
    """If a recover is already running, wait and return its newest log."""
    if not recover_running():
        return None
    log("Existing recover_ocr_gaps_targeted detected — waiting for DONE")
    deadline = time.time() + timeout_sec
    newest: Path | None = None
    while time.time() < deadline:
        logs = sorted(ROOT.glob("_recover_c1o6_9798*.log"), key=lambda p: p.stat().st_mtime, reverse=True)
        for lp in logs:
            if lp.name.endswith(".err.log"):
                continue
            text = lp.read_text(encoding="utf-8", errors="replace")
            if parse_done(text):
                # still running? wait until process exits
                if not recover_running():
                    log(f"Existing recover finished via {lp.name}")
                    return lp
        time.sleep(30)
        if int(time.time()) % 300 < 35:
            log("…still waiting on existing recover")
    log("TIMEOUT waiting on existing recover")
    return newest


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--max-passes", type=int, default=6)
    ap.add_argument("--scale", type=float, default=2.5)
    ap.add_argument("--no-c10", action="store_true")
    ap.add_argument("--skip-wait-existing", action="store_true")
    args = ap.parse_args()

    log(f"START auto C1/O6 until clean years={' '.join(YEARS)} max_passes={args.max_passes}")

    if not args.skip_wait_existing:
        wait_for_existing_recover()

    # Refresh audit once after the in-flight pass (if any) before cycling.
    warm_log = ROOT / "_b6b_rerun_9798_warmup.log"
    warm_err = ROOT / "_b6b_rerun_9798_warmup.err.log"
    run(
        [PY, "-u", str(ROOT / "assess_ingest_quality_audit.py"), "--years", *YEARS],
        warm_log,
        warm_err,
    )

    prev_todo: int | None = None
    plateau = 0
    last_plan: dict[str, int] | None = None

    for pass_i in range(1, args.max_passes + 1):
        tag = f"auto{pass_i}"
        rec_log = ROOT / f"_recover_c1o6_9798_{tag}.log"
        rec_err = ROOT / f"_recover_c1o6_9798_{tag}.err.log"
        rc = run(
            [PY, "-u", str(ROOT / "recover_ocr_gaps_targeted.py"), "--years", *YEARS, "--scale", str(args.scale)],
            rec_log,
            rec_err,
        )
        text = rec_log.read_text(encoding="utf-8", errors="replace") if rec_log.is_file() else ""
        plan = parse_plan(text)
        last_plan = plan
        log(f"pass={pass_i} recover_rc={rc} plan={plan} done={parse_done(text)}")
        if plan is None:
            log("No PLAN line — abort")
            return 2

        todo = int(plan["pages_todo"])
        if todo == 0 and int(plan["c1_todo"]) == 0 and int(plan["o6_todo"]) == 0:
            log("CLEAN: nothing left for C1/O6")
            break

        b6_log = ROOT / f"_b6b_rerun_9798_{tag}.log"
        b6_err = ROOT / f"_b6b_rerun_9798_{tag}.err.log"
        brc = run(
            [PY, "-u", str(ROOT / "assess_ingest_quality_audit.py"), "--years", *YEARS],
            b6_log,
            b6_err,
        )
        b6_text = b6_log.read_text(encoding="utf-8", errors="replace") if b6_log.is_file() else ""
        log(f"pass={pass_i} b6b_rc={brc} tail={b6_text[-400:].replace(chr(10), ' | ')}")

        if prev_todo is not None and todo >= prev_todo:
            plateau += 1
            log(f"plateau_count={plateau} todo={todo} prev={prev_todo}")
        else:
            plateau = 0
        prev_todo = todo

        if plateau >= 2:
            log(f"STOP plateau: C1/O6 residual not shrinking (todo={todo}) — WARN eyes-on OK")
            break
    else:
        log(f"STOP max_passes={args.max_passes} last_plan={last_plan}")

    # Final B6b + pipeline advance
    fin_log = ROOT / "_b6b_rerun_9798_final.log"
    fin_err = ROOT / "_b6b_rerun_9798_final.err.log"
    run(
        [PY, "-u", str(ROOT / "assess_ingest_quality_audit.py"), "--years", *YEARS],
        fin_log,
        fin_err,
    )

    adv = [
        PY, "-u", str(ROOT / "pipeline_advance_years.py"),
        "--years", *YEARS,
        "--force-b6b",
    ]
    if not args.no_c10:
        adv.append("--advance-c10")
    adv_log = ROOT / "_pipeline_advance_auto.log"
    adv_err = ROOT / "_pipeline_advance_auto.err.log"
    arc = run(adv, adv_log, adv_err)
    log(f"ADVANCE rc={arc} — see {adv_log.name}")
    log("DONE auto loop")
    return 0 if arc == 0 else arc


if __name__ == "__main__":
    raise SystemExit(main())
