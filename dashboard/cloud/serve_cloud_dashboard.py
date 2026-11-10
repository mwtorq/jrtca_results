#!/usr/bin/env python3
# Cloud / Linux alternate of the Windows pipeline dashboard.
# Same feature surface as dashboard/serve_pipeline_dashboard.py:
#   GET  /  · /_pipeline_dashboard.html · /_pipeline_dashboard_status.json · /api/status
#   POST /api/track/set-workers  (localhost; Linux → remote-hint / optional proxy)
#
# How to run (from repo root):
#   python -u dashboard/cloud/serve_cloud_dashboard.py --port 8766
#   open http://127.0.0.1:8766/
#
# Synced status (when OCR lives only on Ldahsar):
#   export JRTCA_DASHBOARD_STATUS_JSON=/path/to/_pipeline_dashboard_status.json
#   python -u dashboard/cloud/serve_cloud_dashboard.py --mode synced
# Or: --status-file /path/to/synced.json
#
# Optional worker-control proxy to the Windows host:
#   export JRTCA_WORKER_CONTROL_PROXY=http://ldahsar:8765

"""Linux-cloud HTTP server for the A1–D17 pipeline dashboard (stdlib only)."""

from __future__ import annotations

import argparse
import json
import os
import shutil
import sys
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import urlparse

CLOUD_DIR = Path(__file__).resolve().parent
DASHBOARD_DIR = CLOUD_DIR.parent  # original Windows dashboard (left intact)
REPO_ROOT = CLOUD_DIR.parent.parent
STATUS_NAME = "_pipeline_dashboard_status.json"
# Committed/publishable snapshot name (HTML fetches this; kept in sync on each regen).
STATUS_PUBLISH_NAME = "status.json"
PORT_DEFAULT = 8766

# Runtime config set in main()
MODE = "live"  # live | synced
STATUS_FILE: Path | None = None


def _status_out_path() -> Path:
    return CLOUD_DIR / STATUS_NAME


def _status_publish_path() -> Path:
    return CLOUD_DIR / STATUS_PUBLISH_NAME


def _write_both_status(data: dict) -> None:
    """Write underscore runtime artifact + publishable status.json."""
    import importlib

    if str(CLOUD_DIR) not in sys.path:
        sys.path.insert(0, str(CLOUD_DIR))
    import pipeline_dashboard_status as pds  # noqa: WPS433

    pds = importlib.reload(pds)
    pds.atomic_write_json(_status_out_path(), data)
    pds.atomic_write_json(_status_publish_path(), data)


def regenerate_status() -> dict | None:
    """Build or copy status JSON into dashboard/cloud/.

    live   — run cloud gatherer (Linux /proc process scan; same schema as Windows).
    synced — copy/serve a status file from Ldahsar (or any host) without local OCR PIDs.
    """
    out = _status_out_path()
    if MODE == "synced":
        src = STATUS_FILE
        if src is None:
            env = (os.environ.get("JRTCA_DASHBOARD_STATUS_JSON") or "").strip()
            src = Path(env) if env else None
        if src is None:
            # Prefer a synced copy dropped next to this server, else Windows dashboard artifact.
            for candidate in (
                CLOUD_DIR / "_synced_pipeline_dashboard_status.json",
                CLOUD_DIR / STATUS_PUBLISH_NAME,
                DASHBOARD_DIR / STATUS_NAME,
            ):
                if candidate.is_file():
                    src = candidate
                    break
        if src is None or not Path(src).is_file():
            raise FileNotFoundError(
                "synced mode needs --status-file, JRTCA_DASHBOARD_STATUS_JSON, "
                "dashboard/cloud/_synced_pipeline_dashboard_status.json, "
                "dashboard/cloud/status.json, or dashboard/_pipeline_dashboard_status.json"
            )
        src_p = Path(src)
        data = json.loads(src_p.read_text(encoding="utf-8"))
        _write_both_status(data)
        return data

    import importlib

    if str(CLOUD_DIR) not in sys.path:
        sys.path.insert(0, str(CLOUD_DIR))
    import pipeline_dashboard_status as pds  # noqa: WPS433

    pds = importlib.reload(pds)
    data = pds.gather()
    # Annotate cloud origin without dropping any Windows-schema fields.
    data = dict(data)
    data["dashboard_variant"] = "cloud"
    data["dashboard_host"] = "linux"
    data["worker_control"] = {
        "local": False,
        "hint": (
            "OCR / re-OCR PIDs usually run on Ldahsar (Windows). "
            "POST /api/track/set-workers on this cloud server returns a remote hint "
            "or proxies when JRTCA_WORKER_CONTROL_PROXY is set."
        ),
        "proxy_env": "JRTCA_WORKER_CONTROL_PROXY",
        "windows_url": "http://127.0.0.1:8765/api/track/set-workers",
    }
    _write_both_status(data)
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
            # Prefer publishable index.html when present; fall back to underscore name.
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
            except Exception as exc:  # keep serving last good file if regen fails
                sys.stderr.write(f"status regen failed: {exc}\n")
            if path == "/api/status":
                self.path = "/" + STATUS_PUBLISH_NAME
            else:
                self.path = path
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
    global MODE, STATUS_FILE

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
        choices=("live", "synced"),
        default=os.environ.get("JRTCA_DASHBOARD_MODE", "live"),
        help="live=gather from repo artifacts; synced=serve a copied status JSON",
    )
    ap.add_argument(
        "--status-file",
        default=os.environ.get("JRTCA_DASHBOARD_STATUS_JSON") or None,
        help="Path to synced _pipeline_dashboard_status.json (synced mode)",
    )
    args = ap.parse_args()
    MODE = args.mode
    STATUS_FILE = Path(args.status_file) if args.status_file else None

    try:
        regenerate_status()
        print(f"Initial status written: {_status_out_path()} (mode={MODE})")
    except Exception as exc:
        print(f"Warning: initial status regen failed: {exc}", file=sys.stderr)

    httpd = ThreadingHTTPServer((args.host, args.port), Handler)
    print(f"Cloud dashboard serving {CLOUD_DIR} (repo {REPO_ROOT})")
    print(f"Open http://{args.host}:{args.port}/_pipeline_dashboard.html")
    print(f"Also: http://127.0.0.1:{args.port}/  ·  /api/status")
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
