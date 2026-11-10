#!/usr/bin/env python3
# Cloud / Linux alternate of the Windows pipeline dashboard.
# Same feature surface as dashboard/serve_pipeline_dashboard.py:
#   GET  /  · /_pipeline_dashboard.html · /status.json · /api/status
#   POST /api/track/set-workers  (localhost; Linux → remote-hint / optional proxy)
#
# Default --mode auto prefers Ldahsar status:
#   1) JRTCA_DASHBOARD_STATUS_URL  (HTTP GET of Windows /api/status or status JSON)
#   2) synced file (JRTCA_DASHBOARD_STATUS_JSON / _synced_*.json / Project store drop)
#   3) local live gather (no OCR PIDs on this VM — labeled status_source=local_cloud)
#
# How to run (from repo root):
#   python -u dashboard/cloud/serve_cloud_dashboard.py --port 8766
#   open http://127.0.0.1:8766/
#
# On Ldahsar, export a sync file for this VM / Project store:
#   python -u dashboard/cloud/export_ldahsar_status.py --out .../ldahsar-pipeline-status.json

"""Linux-cloud HTTP server for the A1–D17 pipeline dashboard (stdlib only)."""

from __future__ import annotations

import argparse
import json
import os
import sys
import urllib.error
import urllib.request
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import urlparse

CLOUD_DIR = Path(__file__).resolve().parent
DASHBOARD_DIR = CLOUD_DIR.parent  # original Windows dashboard (left intact)
REPO_ROOT = CLOUD_DIR.parent.parent
STATUS_NAME = "_pipeline_dashboard_status.json"
STATUS_PUBLISH_NAME = "status.json"
PORT_DEFAULT = 8766

# Shared Project store drop (written by Ldahsar export / worker).
PROJECT_STORE_STATUS = Path(
    "/cursor/stores/bc-de650876-a88d-45ea-a369-e7942cc3084e/internal/ldahsar-pipeline-status.json"
)

# Runtime config set in main()
MODE = "auto"  # auto | remote | synced | live
STATUS_FILE: Path | None = None
STATUS_URL: str | None = None


def _status_out_path() -> Path:
    return CLOUD_DIR / STATUS_NAME


def _status_publish_path() -> Path:
    return CLOUD_DIR / STATUS_PUBLISH_NAME


def _write_runtime_status(data: dict, *, also_publish_snapshot: bool = False) -> None:
    """Write underscore runtime artifact; optionally refresh committed status.json."""
    import importlib

    if str(CLOUD_DIR) not in sys.path:
        sys.path.insert(0, str(CLOUD_DIR))
    import pipeline_dashboard_status as pds  # noqa: WPS433

    pds = importlib.reload(pds)
    pds.atomic_write_json(_status_out_path(), data)
    if also_publish_snapshot or os.environ.get("JRTCA_DASHBOARD_WRITE_PUBLISH_STATUS") == "1":
        pds.atomic_write_json(_status_publish_path(), data)


def _annotate(data: dict, *, source: str, detail: str | None = None) -> dict:
    out = dict(data)
    out["dashboard_variant"] = "cloud"
    out["dashboard_host"] = "linux"
    out["status_source"] = source
    if detail:
        out["status_source_detail"] = detail
    out.setdefault(
        "worker_control",
        {
            "local": False,
            "hint": (
                "OCR / re-OCR PIDs run on Ldahsar (Windows). "
                "POST /api/track/set-workers on this cloud server returns a remote hint "
                "or proxies when JRTCA_WORKER_CONTROL_PROXY is set."
            ),
            "proxy_env": "JRTCA_WORKER_CONTROL_PROXY",
            "windows_url": "http://127.0.0.1:8765/api/track/set-workers",
        },
    )
    return out


def _fetch_remote_status(url: str, timeout: float = 20.0) -> dict:
    req = urllib.request.Request(
        url,
        headers={"Accept": "application/json", "User-Agent": "jrtca-cloud-dashboard/1.0"},
        method="GET",
    )
    with urllib.request.urlopen(req, timeout=timeout) as resp:
        raw = resp.read().decode("utf-8", errors="replace")
    data = json.loads(raw)
    if not isinstance(data, dict):
        raise ValueError(f"remote status is not a JSON object ({type(data).__name__})")
    return data


def _synced_candidates() -> list[Path]:
    out: list[Path] = []
    if STATUS_FILE is not None:
        out.append(STATUS_FILE)
    env = (os.environ.get("JRTCA_DASHBOARD_STATUS_JSON") or "").strip()
    if env:
        out.append(Path(env))
    out.extend(
        [
            CLOUD_DIR / "_synced_pipeline_dashboard_status.json",
            PROJECT_STORE_STATUS,
            Path(
                os.environ.get(
                    "JRTCA_PROJECT_STORE_STATUS",
                    str(PROJECT_STORE_STATUS),
                )
            ),
            DASHBOARD_DIR / STATUS_NAME,
        ]
    )
    # Dedupe while preserving order
    seen: set[str] = set()
    uniq: list[Path] = []
    for p in out:
        key = str(p)
        if key in seen:
            continue
        seen.add(key)
        uniq.append(p)
    return uniq


def _load_synced_status() -> tuple[dict, Path]:
    errors: list[str] = []
    for candidate in _synced_candidates():
        try:
            if not candidate.is_file():
                continue
            data = json.loads(candidate.read_text(encoding="utf-8"))
            if isinstance(data, dict) and data.get("steps") is not None:
                return data, candidate
            errors.append(f"{candidate}: missing steps")
        except (OSError, json.JSONDecodeError) as exc:
            errors.append(f"{candidate}: {exc}")
    raise FileNotFoundError(
        "no usable synced Ldahsar status JSON; tried: "
        + "; ".join(str(p) for p in _synced_candidates())
        + (f" ({'; '.join(errors)})" if errors else "")
    )


def _gather_local() -> dict:
    import importlib

    if str(CLOUD_DIR) not in sys.path:
        sys.path.insert(0, str(CLOUD_DIR))
    import pipeline_dashboard_status as pds  # noqa: WPS433

    pds = importlib.reload(pds)
    return pds.gather()


def regenerate_status() -> dict | None:
    """Resolve status for the cloud dashboard (prefer Ldahsar)."""
    mode = (MODE or "auto").strip().lower()
    url = (STATUS_URL or os.environ.get("JRTCA_DASHBOARD_STATUS_URL") or "").strip()

    def from_remote() -> dict:
        if not url:
            raise RuntimeError("remote mode needs --status-url or JRTCA_DASHBOARD_STATUS_URL")
        data = _fetch_remote_status(url)
        return _annotate(data, source="ldahsar_remote", detail=url)

    def from_synced() -> dict:
        data, path = _load_synced_status()
        return _annotate(data, source="ldahsar_synced", detail=str(path))

    def from_live() -> dict:
        data = _gather_local()
        return _annotate(
            data,
            source="local_cloud",
            detail=(
                "Local gather on cloud VM (no Ldahsar OCR PIDs). "
                "Set JRTCA_DASHBOARD_STATUS_URL or drop "
                "internal/ldahsar-pipeline-status.json from Ldahsar."
            ),
        )

    data: dict | None = None
    last_err: Exception | None = None

    if mode == "remote":
        data = from_remote()
    elif mode == "synced":
        data = from_synced()
    elif mode == "live":
        data = from_live()
    else:  # auto
        if url:
            try:
                data = from_remote()
            except Exception as exc:
                last_err = exc
                sys.stderr.write(f"auto: remote status failed ({exc}); trying synced\n")
        if data is None:
            try:
                data = from_synced()
            except Exception as exc:
                last_err = exc
                sys.stderr.write(f"auto: synced status failed ({exc}); falling back to local live\n")
        if data is None:
            data = from_live()
            if last_err is not None:
                data["status_source_fallback_error"] = str(last_err)

    _write_runtime_status(data, also_publish_snapshot=False)
    return data


class Handler(SimpleHTTPRequestHandler):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, directory=str(CLOUD_DIR), **kwargs)

    def _client_is_loopback(self) -> bool:
        host = (self.client_address[0] or "").strip()
        return host in ("127.0.0.1", "::1", "localhost", "::ffff:127.0.0.1")

    def _send_json(self, code: int, payload: dict) -> None:
        body = json.dumps(payload, ensure_ascii=False).encode("utf-8")
        self.send_response(code)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.send_header("Cache-Control", "no-store")
        self.end_headers()
        self.wfile.write(body)

    def end_headers(self) -> None:
        path = urlparse(self.path).path
        if path.endswith((".html", ".json")) or path in (
            "/_pipeline_dashboard.html",
            "/_pipeline_dashboard_status.json",
            "/status.json",
            "/api/status",
            "/",
            "/index.html",
        ):
            self.send_header("Cache-Control", "no-store, no-cache, must-revalidate, max-age=0")
            self.send_header("Pragma", "no-cache")
            self.send_header("Expires", "0")
        super().end_headers()

    def do_GET(self):  # noqa: N802
        path = urlparse(self.path).path
        if path in ("/", "/index.html"):
            if (CLOUD_DIR / "index.html").is_file():
                self.path = "/index.html"
            else:
                self.path = "/_pipeline_dashboard.html"
            path = self.path
        if path in (
            "/_pipeline_dashboard_status.json",
            "/status.json",
            "/api/status",
        ):
            try:
                regenerate_status()
            except Exception as exc:
                sys.stderr.write(f"status regen failed: {exc}\n")
            self.path = "/" + STATUS_NAME
        return super().do_GET()

    def do_POST(self):  # noqa: N802
        path = urlparse(self.path).path
        if path != "/api/track/set-workers":
            self.send_error(404, "unknown API")
            return
        if not self._client_is_loopback():
            self._send_json(403, {"ok": False, "error": "localhost only"})
            return
        length = int(self.headers.get("Content-Length") or "0")
        # Bound body size (security review: unbounded Content-Length).
        if length < 0 or length > 64_000:
            self._send_json(400, {"ok": False, "error": "body too large or invalid Content-Length"})
            return
        raw = self.rfile.read(length) if length > 0 else b"{}"
        try:
            body = json.loads(raw.decode("utf-8") or "{}")
        except json.JSONDecodeError:
            self._send_json(400, {"ok": False, "error": "invalid JSON"})
            return
        kind = str(body.get("kind") or "reocr")
        track = str(body.get("track") or "")
        try:
            workers = int(body.get("workers"))
        except (TypeError, ValueError):
            self._send_json(400, {"ok": False, "error": "workers must be int 1..16"})
            return
        try:
            page_workers = int(body.get("page_workers") or 2)
        except (TypeError, ValueError):
            page_workers = 2
        if workers < 1 or workers > 16:
            self._send_json(400, {"ok": False, "error": "workers must be 1..16"})
            return

        if str(CLOUD_DIR) not in sys.path:
            sys.path.insert(0, str(CLOUD_DIR))
        try:
            import importlib

            import track_worker_control as twc

            twc = importlib.reload(twc)
            result = twc.set_track_workers(kind, track, workers, page_workers)
        except Exception as exc:
            self._send_json(500, {"ok": False, "error": str(exc)})
            return

        try:
            regenerate_status()
        except Exception as exc:
            result = dict(result or {})
            result["status_regen_error"] = str(exc)
        self._send_json(200 if result.get("ok") else 409, result)

    def log_message(self, fmt: str, *args) -> None:
        sys.stderr.write("%s - %s\n" % (self.address_string(), fmt % args))


def main() -> int:
    global MODE, STATUS_FILE, STATUS_URL

    ap = argparse.ArgumentParser(
        description="Serve JRTCA pipeline dashboard (Linux cloud alternate)"
    )
    ap.add_argument("--port", type=int, default=PORT_DEFAULT)
    ap.add_argument(
        "--host",
        default="127.0.0.1",
        help="Bind address (default 127.0.0.1; use 0.0.0.0 only if you intend remote access)",
    )
    ap.add_argument(
        "--mode",
        choices=("auto", "remote", "synced", "live"),
        default=os.environ.get("JRTCA_DASHBOARD_MODE", "auto"),
        help="auto=Ldahsar URL then synced file then local; remote/synced/live force one path",
    )
    ap.add_argument(
        "--status-file",
        default=os.environ.get("JRTCA_DASHBOARD_STATUS_JSON") or None,
        help="Path to synced Ldahsar status JSON",
    )
    ap.add_argument(
        "--status-url",
        default=os.environ.get("JRTCA_DASHBOARD_STATUS_URL") or None,
        help="HTTP URL of Ldahsar status (e.g. http://HOST:8765/api/status)",
    )
    args = ap.parse_args()
    MODE = args.mode
    STATUS_FILE = Path(args.status_file) if args.status_file else None
    STATUS_URL = args.status_url

    try:
        data = regenerate_status()
        src = (data or {}).get("status_source")
        print(f"Initial status written: {_status_out_path()} (mode={MODE}, source={src})")
    except Exception as exc:
        print(f"Warning: initial status regen failed: {exc}", file=sys.stderr)

    httpd = ThreadingHTTPServer((args.host, args.port), Handler)
    print(f"Cloud dashboard serving {CLOUD_DIR} (repo {REPO_ROOT})")
    print(f"Open http://{args.host}:{args.port}/")
    print(f"Also: http://127.0.0.1:{args.port}/status.json · /api/status")
    if STATUS_URL or (os.environ.get("JRTCA_DASHBOARD_STATUS_URL") or "").strip():
        print(f"Status URL: {STATUS_URL or os.environ.get('JRTCA_DASHBOARD_STATUS_URL')}")
    print(f"Sync drop: {PROJECT_STORE_STATUS}")
    print("API: POST /api/track/set-workers {kind,track,workers} (localhost; remote-hint/proxy on Linux)")
    proxy = (os.environ.get("JRTCA_WORKER_CONTROL_PROXY") or "").strip()
    if proxy:
        print(f"Worker-control proxy: {proxy}")
    else:
        print("Worker-control: no proxy set (JRTCA_WORKER_CONTROL_PROXY); Apply returns remote hint")
    try:
        httpd.serve_forever()
    except KeyboardInterrupt:
        print("\nStopped.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
