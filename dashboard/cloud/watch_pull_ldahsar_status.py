#!/usr/bin/env python3
"""Cloud-side: every N seconds pull newest Ldahsar status dump into the dashboard.

Reads (first existing, newest mtime wins among candidates):
  - Project store internal/ldahsar-pipeline-status.json
  - dashboard/cloud/_synced_pipeline_dashboard_status.json
  - JRTCA_DASHBOARD_STATUS_JSON / --status-file

When the chosen source is newer than the local runtime artifact (or missing),
copies it to:
  - dashboard/cloud/_synced_pipeline_dashboard_status.json
  - dashboard/cloud/_pipeline_dashboard_status.json  (what :8766 serves after regen)
and annotates status_source=ldahsar_synced.

Optionally refreshes publishable status.json when JRTCA_DASHBOARD_WRITE_PUBLISH_STATUS=1
(do NOT enable that in a tight loop for Cursor publish-app unless you intend commits).

Run on the cloud VM (alongside serve_cloud_dashboard.py):

  python -u dashboard/cloud/watch_pull_ldahsar_status.py --interval 60
"""

from __future__ import annotations

import argparse
import json
import os
import sys
import time
from pathlib import Path

CLOUD_DIR = Path(__file__).resolve().parent
PROJECT_STORE_STATUS = Path(
    "/cursor/stores/bc-de650876-a88d-45ea-a369-e7942cc3084e/internal/ldahsar-pipeline-status.json"
)
SYNCED = CLOUD_DIR / "_synced_pipeline_dashboard_status.json"
RUNTIME = CLOUD_DIR / "_pipeline_dashboard_status.json"
PUBLISH = CLOUD_DIR / "status.json"


def _candidates(extra: Path | None) -> list[Path]:
    out: list[Path] = []
    if extra is not None:
        out.append(extra)
    env = (os.environ.get("JRTCA_DASHBOARD_STATUS_JSON") or "").strip()
    if env:
        out.append(Path(env))
    out.extend([PROJECT_STORE_STATUS, SYNCED])
    seen: set[str] = set()
    uniq: list[Path] = []
    for p in out:
        k = str(p.resolve()) if p.exists() else str(p)
        if k in seen:
            continue
        seen.add(k)
        uniq.append(p)
    return uniq


def _newest_valid(paths: list[Path]) -> tuple[Path, dict, float] | None:
    best = None
    for p in paths:
        try:
            if not p.is_file():
                continue
            data = json.loads(p.read_text(encoding="utf-8"))
            if not isinstance(data, dict) or data.get("steps") is None:
                continue
            # Skip empty local-cloud restores mistakenly labeled as Ldahsar
            if data.get("status_source") == "ldahsar_synced_restored":
                continue
            mtime = p.stat().st_mtime
            if best is None or mtime > best[2]:
                best = (p, data, mtime)
        except (OSError, json.JSONDecodeError):
            continue
    return best


def _atomic_write(path: Path, data: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    payload = json.dumps(data, indent=2, ensure_ascii=False) + "\n"
    tmp = path.with_suffix(path.suffix + ".tmp")
    tmp.write_text(payload, encoding="utf-8", newline="\n")
    tmp.replace(path)


def _git_push_status(generated_at: str | None) -> dict:
    """Commit+push dashboard/cloud/status.json when content changed (public raw feed)."""
    import subprocess

    repo = CLOUD_DIR.parent.parent
    rel = "dashboard/cloud/status.json"
    try:
        diff = subprocess.run(
            ["git", "diff", "--", rel],
            cwd=str(repo),
            capture_output=True,
            text=True,
            timeout=30,
        )
        staged = subprocess.run(
            ["git", "status", "--porcelain", "--", rel],
            cwd=str(repo),
            capture_output=True,
            text=True,
            timeout=30,
        )
        if not (diff.stdout or "").strip() and not (staged.stdout or "").strip():
            return {"pushed": False, "reason": "clean"}
        subprocess.run(["git", "add", "--", rel], cwd=str(repo), check=True, timeout=30)
        msg = f"chore(cloud): refresh Ldahsar status.json ({generated_at or 'unknown'})"
        subprocess.run(
            ["git", "commit", "-m", msg],
            cwd=str(repo),
            check=True,
            timeout=60,
            capture_output=True,
            text=True,
        )
        branch = subprocess.run(
            ["git", "rev-parse", "--abbrev-ref", "HEAD"],
            cwd=str(repo),
            capture_output=True,
            text=True,
            timeout=30,
            check=True,
        ).stdout.strip()
        push = subprocess.run(
            ["git", "push", "-u", "origin", branch],
            cwd=str(repo),
            capture_output=True,
            text=True,
            timeout=120,
        )
        return {
            "pushed": push.returncode == 0,
            "branch": branch,
            "returncode": push.returncode,
            "stderr": (push.stderr or "")[-400:],
        }
    except Exception as exc:
        return {"pushed": False, "error": str(exc)}


def pull_once(
    extra: Path | None,
    *,
    write_publish: bool,
    git_push_status: bool = False,
) -> dict:
    found = _newest_valid(_candidates(extra))
    if found is None:
        return {"ok": False, "error": "no usable Ldahsar status JSON"}
    src_path, data, mtime = found
    data = dict(data)
    data["status_source"] = "ldahsar_synced"
    data["status_source_detail"] = str(src_path)
    data["dashboard_variant"] = "cloud"
    data["dashboard_host"] = "linux"

    runtime_mtime = RUNTIME.stat().st_mtime if RUNTIME.is_file() else 0.0
    # Compare by generated_at when possible so identical mtimes still refresh
    # after an in-place store rewrite with newer gather timestamp.
    prev_gen = None
    if RUNTIME.is_file():
        try:
            prev_gen = json.loads(RUNTIME.read_text(encoding="utf-8")).get("generated_at")
        except (OSError, json.JSONDecodeError):
            prev_gen = None
    changed = (
        not RUNTIME.is_file()
        or mtime > runtime_mtime + 0.01
        or data.get("generated_at") != prev_gen
    )
    push_info = None
    if changed:
        _atomic_write(SYNCED, data)
        _atomic_write(RUNTIME, data)
        if write_publish or git_push_status:
            _atomic_write(PUBLISH, data)
        if git_push_status:
            push_info = _git_push_status(data.get("generated_at"))
    reocr = (data.get("targeted_ocr") or {}).get("reocr") or {}
    return {
        "ok": True,
        "changed": changed,
        "source": str(src_path),
        "generated_at": data.get("generated_at"),
        "reocr_pids": reocr.get("pids"),
        "wrote_publish": bool(write_publish or git_push_status),
        "git_push": push_info,
    }


def main() -> int:
    ap = argparse.ArgumentParser(description="Pull Ldahsar status dump on an interval")
    ap.add_argument("--interval", type=float, default=60.0)
    ap.add_argument("--status-file", default=None)
    ap.add_argument(
        "--once",
        action="store_true",
        help="Single pull then exit",
    )
    ap.add_argument(
        "--write-publish",
        action="store_true",
        help="Also refresh dashboard/cloud/status.json (git-tracked publish snapshot)",
    )
    ap.add_argument(
        "--git-push-status",
        action="store_true",
        help="Commit+push status.json when it changes (feeds published app via GitHub raw)",
    )
    args = ap.parse_args()
    interval = max(5.0, float(args.interval))
    extra = Path(args.status_file) if args.status_file else None
    write_publish = bool(args.write_publish) or os.environ.get(
        "JRTCA_DASHBOARD_WRITE_PUBLISH_STATUS"
    ) == "1"
    git_push_status = bool(args.git_push_status) or os.environ.get(
        "JRTCA_DASHBOARD_GIT_PUSH_STATUS"
    ) == "1"

    print(
        f"Cloud Ldahsar pull watcher: interval={interval}s "
        f"write_publish={write_publish} git_push_status={git_push_status}",
        flush=True,
    )
    n = 0
    result: dict = {"ok": False}
    while True:
        n += 1
        t0 = time.time()
        try:
            result = pull_once(
                extra,
                write_publish=write_publish,
                git_push_status=git_push_status,
            )
            print(
                f"[{time.strftime('%Y-%m-%d %H:%M:%S')}] tick={n} {json.dumps(result, ensure_ascii=False)}",
                flush=True,
            )
        except Exception as exc:
            print(
                f"[{time.strftime('%Y-%m-%d %H:%M:%S')}] tick={n} ERROR {exc}",
                file=sys.stderr,
                flush=True,
            )
        if args.once:
            return 0 if result.get("ok") else 1
        elapsed = time.time() - t0
        time.sleep(max(0.5, interval - elapsed))


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except KeyboardInterrupt:
        print("\nStopped.", flush=True)
        raise SystemExit(0)
