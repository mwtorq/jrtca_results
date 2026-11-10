#!/usr/bin/env python3
"""Export Ldahsar (Windows) pipeline status JSON for the cloud dashboard.

Run on the OCR host (Ldahsar), from repo root:

  python -u dashboard/cloud/export_ldahsar_status.py

Prefers a live regen from the Windows gatherer (dashboard/pipeline_dashboard_status.py).
Falls back to GET http://127.0.0.1:8765/api/status if the gatherer import fails.

Writes (in order of --out, else defaults):
  - path from --out / JRTCA_DASHBOARD_EXPORT_OUT
  - dashboard/cloud/_synced_pipeline_dashboard_status.json
  - Project store internal/ldahsar-pipeline-status.json when that path exists
"""

from __future__ import annotations

import argparse
import json
import os
import sys
import urllib.request
from pathlib import Path

CLOUD_DIR = Path(__file__).resolve().parent
DASHBOARD_DIR = CLOUD_DIR.parent
REPO_ROOT = CLOUD_DIR.parent.parent
PROJECT_STORE_STATUS = Path(
    "/cursor/stores/bc-de650876-a88d-45ea-a369-e7942cc3084e/internal/ldahsar-pipeline-status.json"
)


def _gather_windows() -> dict:
    if str(DASHBOARD_DIR) not in sys.path:
        sys.path.insert(0, str(DASHBOARD_DIR))
    import importlib

    import pipeline_dashboard_status as pds

    pds = importlib.reload(pds)
    data = pds.gather()
    # Also refresh the Windows dashboard artifact when possible.
    try:
        pds.atomic_write_json(DASHBOARD_DIR / "_pipeline_dashboard_status.json", data)
    except OSError:
        pass
    return data


def _fetch_local_api() -> dict:
    url = os.environ.get("JRTCA_DASHBOARD_EXPORT_URL", "http://127.0.0.1:8765/api/status")
    with urllib.request.urlopen(url, timeout=30) as resp:
        return json.loads(resp.read().decode("utf-8", errors="replace"))


def _atomic_write(path: Path, data: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    payload = json.dumps(data, indent=2, ensure_ascii=False) + "\n"
    tmp = path.with_suffix(path.suffix + ".tmp")
    tmp.write_text(payload, encoding="utf-8", newline="\n")
    tmp.replace(path)


def main() -> int:
    ap = argparse.ArgumentParser(description="Export Ldahsar status for cloud dashboard")
    ap.add_argument(
        "--out",
        action="append",
        default=[],
        help="Output path (repeatable). Defaults applied when omitted.",
    )
    args = ap.parse_args()

    err = None
    try:
        data = _gather_windows()
        how = "gather:dashboard/pipeline_dashboard_status.py"
    except Exception as exc:
        err = exc
        try:
            data = _fetch_local_api()
            how = "GET http://127.0.0.1:8765/api/status"
        except Exception as exc2:
            print(f"gather failed: {err}", file=sys.stderr)
            print(f"api fetch failed: {exc2}", file=sys.stderr)
            return 1

    data = dict(data)
    data["exported_for"] = "cloud_dashboard"
    data["export_how"] = how
    data["status_source"] = "ldahsar_export"

    outs: list[Path] = [Path(p) for p in args.out]
    env_out = (os.environ.get("JRTCA_DASHBOARD_EXPORT_OUT") or "").strip()
    if env_out:
        outs.append(Path(env_out))
    if not outs:
        outs = [
            CLOUD_DIR / "_synced_pipeline_dashboard_status.json",
            CLOUD_DIR / "status.json",
        ]
        if PROJECT_STORE_STATUS.parent.is_dir() or os.name != "nt":
            # On Ldahsar the Project store path may not exist; skip quietly.
            if PROJECT_STORE_STATUS.parent.is_dir():
                outs.append(PROJECT_STORE_STATUS)

    for path in outs:
        try:
            _atomic_write(path, data)
            print(f"Wrote {path} via {how}")
        except OSError as exc:
            print(f"Skip {path}: {exc}", file=sys.stderr)

    ocr = (data.get("ocr_live") or {}).get("processes") or {}
    print(
        "summary:",
        "generated=",
        data.get("generated_at"),
        "ocr_alive=",
        ocr.get("alive"),
        "pids=",
        ocr.get("pids"),
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
