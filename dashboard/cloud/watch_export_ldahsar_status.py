#!/usr/bin/env python3
"""Loop: export Ldahsar pipeline status every N seconds (run on Windows OCR host).

Intended for the Ldahsar self-hosted worker / a detached console:

  python -u dashboard/cloud/watch_export_ldahsar_status.py --interval 60

Each tick runs ``export_ldahsar_status.py`` logic (gather or :8765 API) and writes:
  - dashboard/cloud/_synced_pipeline_dashboard_status.json
  - Project store internal/ldahsar-pipeline-status.json (when that path exists)
  - optional --out paths / JRTCA_DASHBOARD_EXPORT_OUT

Does not kill OCR. Ctrl+C to stop.
"""

from __future__ import annotations

import argparse
import importlib.util
import sys
import time
from pathlib import Path

CLOUD_DIR = Path(__file__).resolve().parent


def _load_exporter():
    path = CLOUD_DIR / "export_ldahsar_status.py"
    spec = importlib.util.spec_from_file_location("export_ldahsar_status", path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"cannot load {path}")
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def main() -> int:
    ap = argparse.ArgumentParser(description="Export Ldahsar status on an interval")
    ap.add_argument("--interval", type=float, default=60.0, help="Seconds between exports")
    ap.add_argument(
        "--out",
        action="append",
        default=[],
        help="Extra output path (repeatable); passed through to exporter",
    )
    args = ap.parse_args()
    interval = max(5.0, float(args.interval))

    # Reuse exporter CLI by setting argv for its argparse when outs provided.
    exporter = _load_exporter()
    print(
        f"Ldahsar status export watcher: interval={interval}s cwd={Path.cwd()} "
        f"repo_cloud={CLOUD_DIR}",
        flush=True,
    )
    n = 0
    while True:
        n += 1
        t0 = time.time()
        try:
            # Call exporter main with optional outs
            old_argv = sys.argv[:]
            sys.argv = [str(CLOUD_DIR / "export_ldahsar_status.py")]
            for out in args.out:
                sys.argv.extend(["--out", out])
            try:
                rc = int(exporter.main() or 0)
            finally:
                sys.argv = old_argv
            print(f"[{time.strftime('%Y-%m-%d %H:%M:%S')}] tick={n} rc={rc}", flush=True)
        except Exception as exc:
            print(
                f"[{time.strftime('%Y-%m-%d %H:%M:%S')}] tick={n} ERROR {exc}",
                file=sys.stderr,
                flush=True,
            )
        elapsed = time.time() - t0
        time.sleep(max(0.5, interval - elapsed))


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except KeyboardInterrupt:
        print("\nStopped.", flush=True)
        raise SystemExit(0)
