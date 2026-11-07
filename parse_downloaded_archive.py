#!/usr/bin/env python3
"""Parse archive HTML already on disk: update existing dogs and insert new ones.

Runs separately from the Wayback downloader. Re-scans for new files so it can
keep a head start while snapshots are still arriving.
"""
from __future__ import annotations

import argparse
import time
from pathlib import Path

from scrape_jrtcabreeders import (
    PAGES_ARCHIVE,
    download_all_photos,
    dump_parsed,
    load_sql,
    merge_breeders,
    parse_existing_archive_files,
)

LOG = Path(__file__).resolve().parent / "jrtcabreeders.com" / "archive_parse_headstart.log"


def log(msg: str) -> None:
    line = f"{time.strftime('%H:%M:%S')} {msg}"
    print(line, flush=True)
    with LOG.open("a", encoding="utf-8") as f:
        f.write(line + "\n")


def process_batch(force: bool = False, skip_photos: bool = True) -> int:
    breeders, n_files = parse_existing_archive_files(force=force)
    if not n_files:
        return 0
    merged = merge_breeders(breeders)
    dog_n = sum(len(b.dogs) for b in merged)
    log(f"parsed {n_files} new files -> {len(merged)} kennels, {dog_n} dogs")
    dump_parsed(merged)
    log("loading SQL (update existing + insert new)")
    load_sql(merged)
    if skip_photos:
        log("SQL load finished; skipping photos")
    else:
        log("SQL load finished; downloading photos")
        download_all_photos(merged)
        log("photo pass finished")
    return n_files


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--once", action="store_true", help="Parse current files only")
    ap.add_argument("--force", action="store_true", help="Re-parse files already in the manifest")
    ap.add_argument("--photos", action="store_true", help="Download photos after SQL (off by default)")
    ap.add_argument("--idle-rounds", type=int, default=40, help="Exit after this many empty scans")
    ap.add_argument("--sleep", type=int, default=20)
    args = ap.parse_args()

    log(f"head-start parser watching {PAGES_ARCHIVE} (update existing + insert new)")
    on_disk = len(list(PAGES_ARCHIVE.glob("*.html")))
    log(f"{on_disk} html files already on disk")
    idle = 0
    first = True
    while True:
        n = process_batch(force=args.force and first, skip_photos=not args.photos)
        first = False
        if args.once:
            break
        if n == 0:
            idle += 1
            log(f"no new settled files ({idle}/{args.idle_rounds})")
            if idle >= args.idle_rounds:
                log("idle limit reached; exiting")
                break
        else:
            idle = 0
        time.sleep(args.sleep)
    log("head-start parser finished")


if __name__ == "__main__":
    main()
