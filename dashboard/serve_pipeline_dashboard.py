#!/usr/bin/env python3
# How to run (from repo root or this folder):
#   python -u dashboard/serve_pipeline_dashboard.py
#   open http://127.0.0.1:8765/_pipeline_dashboard.html
# Refresh regenerates dashboard/_pipeline_dashboard_status.json on each status GET.
# POST /api/track/set-workers — localhost-only track worker retune (restart).

"""Tiny HTTP server for the A1–D17 pipeline dashboard (stdlib only)."""

from __future__ import annotations

import argparse
import json
import sys
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import urlparse

DASHBOARD_DIR = Path(__file__).resolve().parent
REPO_ROOT = DASHBOARD_DIR.parent
STATUS_NAME = "_pipeline_dashboard_status.json"
PORT_DEFAULT = 8765


def regenerate_status() -> None:
    # Import sibling module; reload so gatherer edits apply without restarting.
    import importlib

    if str(DASHBOARD_DIR) not in sys.path:
        sys.path.insert(0, str(DASHBOARD_DIR))
    import pipeline_dashboard_status as pds  # noqa: WPS433

    pds = importlib.reload(pds)
    data = pds.gather()
    pds.atomic_write_json(DASHBOARD_DIR / STATUS_NAME, data)


class Handler(SimpleHTTPRequestHandler):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, directory=str(DASHBOARD_DIR), **kwargs)

    def _client_is_loopback(self) -> bool:
        host = (self.client_address[0] or "").strip()
        return host in ("127.0.0.1", "::1", "localhost")

    def _send_json(self, code: int, payload: dict) -> None:
        body = json.dumps(payload, ensure_ascii=False).encode("utf-8")
        self.send_response(code)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.send_header("Cache-Control", "no-store")
        self.end_headers()
        self.wfile.write(body)

    def end_headers(self) -> None:
        # Avoid 304/stale HTML+JSON in the browser while the pipeline is live.
        path = urlparse(self.path).path
        if path.endswith((".html", ".json")) or path in (
            "/_pipeline_dashboard.html",
            "/_pipeline_dashboard_status.json",
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
            self.path = "/_pipeline_dashboard.html"
            path = self.path
        if path in ("/_pipeline_dashboard_status.json", "/api/status"):
            try:
                regenerate_status()
            except Exception as exc:  # keep serving last good file if regen fails
                sys.stderr.write(f"status regen failed: {exc}\n")
            if path == "/api/status":
                self.path = "/" + STATUS_NAME
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

        if str(DASHBOARD_DIR) not in sys.path:
            sys.path.insert(0, str(DASHBOARD_DIR))
        try:
            import importlib

            import track_worker_control as twc

            twc = importlib.reload(twc)
            result = twc.set_track_workers(kind, track, workers, page_workers)
        except Exception as exc:
            self._send_json(500, {"ok": False, "error": str(exc)})
            return

        # Refresh status JSON after retune so UI shows new workers/PIDs.
        try:
            regenerate_status()
        except Exception as exc:
            result = dict(result or {})
            result["status_regen_error"] = str(exc)
        self._send_json(200 if result.get("ok") else 409, result)

    def log_message(self, fmt: str, *args) -> None:
        sys.stderr.write("%s - %s\n" % (self.address_string(), fmt % args))


def main() -> int:
    ap = argparse.ArgumentParser(description="Serve JRTCA pipeline dashboard")
    ap.add_argument("--port", type=int, default=PORT_DEFAULT)
    ap.add_argument("--host", default="127.0.0.1")
    args = ap.parse_args()

    try:
        regenerate_status()
        print(f"Initial status written: {DASHBOARD_DIR / STATUS_NAME}")
    except Exception as exc:
        print(f"Warning: initial status regen failed: {exc}", file=sys.stderr)

    httpd = ThreadingHTTPServer((args.host, args.port), Handler)
    print(f"Serving {DASHBOARD_DIR} (repo {REPO_ROOT})")
    print(f"Open http://{args.host}:{args.port}/_pipeline_dashboard.html")
    print("API: POST /api/track/set-workers {kind,track,workers} (localhost only)")
    try:
        httpd.serve_forever()
    except KeyboardInterrupt:
        print("\nStopped.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
