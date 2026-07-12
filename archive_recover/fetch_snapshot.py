"""Fetch and cache a single archive.org snapshot's HTML content."""
from __future__ import annotations

import os
import time
import urllib.error
import urllib.request

CACHE_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "snapshot_cache")
os.makedirs(CACHE_DIR, exist_ok=True)


def fetch_snapshot(timestamp: str, original_url: str, retries: int = 3) -> str | None:
    cache_path = os.path.join(CACHE_DIR, f"{timestamp}.html")
    if os.path.exists(cache_path):
        with open(cache_path, "r", encoding="utf-8", errors="ignore") as f:
            return f.read()

    wb_url = f"https://web.archive.org/web/{timestamp}/{original_url}"
    for attempt in range(retries):
        try:
            req = urllib.request.Request(wb_url, headers={"User-Agent": "Mozilla/5.0"})
            with urllib.request.urlopen(req, timeout=60) as resp:
                data = resp.read().decode("utf-8", errors="ignore")
            with open(cache_path, "w", encoding="utf-8") as f:
                f.write(data)
            return data
        except urllib.error.HTTPError as e:
            if e.code == 404:
                return None
            time.sleep(2 * (attempt + 1))
        except Exception:
            time.sleep(2 * (attempt + 1))
    return None
