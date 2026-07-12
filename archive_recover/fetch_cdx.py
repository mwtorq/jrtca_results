"""Fetch and cache the CDX (archive.org capture index) listing for a URL."""
from __future__ import annotations

import json
import os
import urllib.request

CACHE_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "cdx_cache")
os.makedirs(CACHE_DIR, exist_ok=True)


def fetch_cdx(url: str, match_type: str = "exact") -> list[list[str]]:
    safe = url.replace("/", "_").replace(":", "_").replace("?", "_").replace("*", "")
    if match_type != "exact":
        safe = f"{safe}__{match_type}"
    cache_path = os.path.join(CACHE_DIR, f"{safe}.json")
    if os.path.exists(cache_path):
        with open(cache_path, "r", encoding="utf-8") as f:
            return json.load(f)

    clean_url = url.rstrip("*")
    cdx_url = f"https://web.archive.org/cdx/search/cdx?url={clean_url}&output=json&matchType={match_type}"
    req = urllib.request.Request(cdx_url, headers={"User-Agent": "Mozilla/5.0"})
    with urllib.request.urlopen(req, timeout=60) as resp:
        data = json.loads(resp.read().decode("utf-8"))

    with open(cache_path, "w", encoding="utf-8") as f:
        json.dump(data, f)
    return data


if __name__ == "__main__":
    import sys

    url = sys.argv[1]
    match_type = sys.argv[2] if len(sys.argv) > 2 else "exact"
    rows = fetch_cdx(url, match_type)
    print(f"{len(rows)} rows (including header)")
    for row in rows[1:]:
        print(row)
