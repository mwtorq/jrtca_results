"""Build a merged (name -> date(s)) trial schedule for a given year by
downloading and parsing every relevant archive.org snapshot of the JRTCA
trial-schedule page.

Old format (terrier.com/trial/trials.php3, ~1999-2006): calendar page shows
upcoming trials from the capture date forward, month/day only (no year),
combined "Name I & II" style entries with a day range.

New format (therealjackrussell.com/trial/trials.php, ~2009+): each sub-trial
(I, II, ...) is its own entry with an explicit single full date.
"""
from __future__ import annotations

import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from fetch_cdx import fetch_cdx
from fetch_snapshot import fetch_snapshot
from parse_old_format import parse_snapshot as parse_old
from parse_new_format import parse_snapshot as parse_new
from parse_card_format import parse_snapshot as parse_card

OUT_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "schedules")
os.makedirs(OUT_DIR, exist_ok=True)

OLD_URL = "terrier.com/trial/trials.php3"
OLD_URL4 = "terrier.com/trial/trials.php4"
NEW_URL = "therealjackrussell.com/trial/trials.php"


def snapshots_for_url(cdx_url: str) -> list[tuple[str, str]]:
    """Return list of (timestamp, original_url) for 200-status HTML captures."""
    rows = fetch_cdx(cdx_url)
    out = []
    seen_ts = set()
    for row in rows[1:]:
        timestamp, original, mimetype, statuscode = row[1], row[2], row[3], row[4]
        if statuscode != "200" or mimetype != "text/html":
            continue
        if timestamp in seen_ts:
            continue
        seen_ts.add(timestamp)
        out.append((timestamp, original))
    return out


MONTH_NUMS = {
    "jan": 1, "feb": 2, "mar": 3, "apr": 4, "may": 5, "jun": 6,
    "jul": 7, "aug": 8, "sep": 9, "oct": 10, "nov": 11, "dec": 12,
}


def smonth_snapshots_for_url(base_url: str) -> list[tuple[str, str, int]]:
    """Some captures of these pages support a '?smonth=Xxx' query param that
    forces the calendar to display a specific month regardless of the capture
    date - a single such snapshot effectively gives us a whole extra month of
    schedule data "for free". Returns (timestamp, original_url, target_month)."""
    import re

    rows = fetch_cdx(f"{base_url}*", "prefix")
    out = []
    seen_ts = set()
    for row in rows[1:]:
        timestamp, original, mimetype, statuscode = row[1], row[2], row[3], row[4]
        if statuscode != "200" or mimetype != "text/html":
            continue
        m = re.search(r"smonth=([A-Za-z]+)", original, re.IGNORECASE)
        if not m:
            continue
        month = MONTH_NUMS.get(m.group(1).lower())
        if month is None:
            continue
        key = (timestamp, month)
        if key in seen_ts:
            continue
        seen_ts.add(key)
        out.append((timestamp, original, month))
    return out


def build_old_format_year(year: int) -> list[dict]:
    """Merge trials.php3 (and .php4) snapshots covering Nov(year-1)..Dec(year)."""
    all_snaps = snapshots_for_url(OLD_URL) + snapshots_for_url(OLD_URL4)
    relevant = []
    lo = f"{year - 1}11"
    hi = f"{year}12"
    for ts, orig in all_snaps:
        ym = ts[:6]
        if lo <= ym <= hi:
            relevant.append((ts, orig))
    relevant.sort()

    merged: dict[tuple, dict] = {}
    for ts, orig in relevant:
        snap_year = int(ts[:4])
        snap_month = int(ts[4:6])
        html = fetch_snapshot(ts, orig)
        if not html:
            continue
        entries = parse_old(html, snap_year, snap_month)
        for e in entries:
            if e["year"] != year:
                continue
            key = (e["month"], e["day_start"], e["day_end"], e["name"].lower())
            if key not in merged:
                merged[key] = e
                merged[key]["source_ts"] = ts

    # "?smonth=Xxx" snapshots force the calendar to show a specific month
    # regardless of capture date - the site shows the *next* occurrence of
    # that month, so if the target month has already passed in the capture
    # year, it's actually showing next year's occurrence of that month.
    smonth_snaps = smonth_snapshots_for_url(OLD_URL) + smonth_snapshots_for_url(OLD_URL4)
    for ts, orig, target_month in smonth_snaps:
        snap_year = int(ts[:4])
        snap_month = int(ts[4:6])
        effective_year = snap_year + 1 if target_month < snap_month else snap_year
        if effective_year != year:
            continue
        html = fetch_snapshot(ts, orig)
        if not html:
            continue
        entries = parse_old(html, effective_year, target_month)
        for e in entries:
            if e["year"] != year or e["month"] != target_month:
                continue
            key = (e["month"], e["day_start"], e["day_end"], e["name"].lower())
            if key not in merged:
                merged[key] = e
                merged[key]["source_ts"] = ts
    return sorted(merged.values(), key=lambda e: (e["month"], e["day_start"]))


def build_new_format_year(year: int) -> list[dict]:
    """Merge trials.php snapshots covering Nov(year-1)..Dec(year)."""
    all_snaps = snapshots_for_url(NEW_URL)
    relevant = []
    lo = f"{year - 1}11"
    hi = f"{year}12"
    for ts, orig in all_snaps:
        ym = ts[:6]
        if lo <= ym <= hi:
            relevant.append((ts, orig))
    relevant.sort()

    merged: dict[tuple, dict] = {}
    for ts, orig in relevant:
        html = fetch_snapshot(ts, orig)
        if not html:
            continue
        entries = parse_new(html)
        if not entries:
            # ~Nov 2016+ snapshots use the newer bordered-"card" template
            # with an <h2> heading instead of the table-row layout.
            entries = parse_card(html)
        if not entries:
            # Some 2009-2011 snapshots use the older mid-format template
            # (month/day only, no year) even on the new domain.
            snap_year = int(ts[:4])
            for e in parse_old(html, snap_year, int(ts[4:6])):
                if e["year"] != year:
                    continue
                d_start = f"{e['year']}-{e['month']:02d}-{e['day_start']:02d}"
                wrapped = e["day_end"] < e["day_start"]
                end_month = e["month"] + 1 if wrapped else e["month"]
                end_year = e["year"] + 1 if end_month > 12 else e["year"]
                end_month = 1 if end_month > 12 else end_month
                d_end = f"{end_year}-{end_month:02d}-{e['day_end']:02d}"
                entries.append({"day_start": d_start, "day_end": d_end, "name": e["name"]})
        for e in entries:
            if not e["day_start"].startswith(str(year)):
                continue
            key = (e["day_start"], e["day_end"], e["name"].lower())
            if key not in merged:
                merged[key] = e
                merged[key]["source_ts"] = ts

    # "?smonth=Xxx" snapshots on the new domain already embed a full year in
    # the returned dates, so no year-inference needed - just parse and filter.
    for ts, orig, _target_month in smonth_snapshots_for_url(NEW_URL):
        html = fetch_snapshot(ts, orig)
        if not html:
            continue
        entries = parse_new(html) or parse_card(html)
        for e in entries:
            if not e["day_start"].startswith(str(year)):
                continue
            key = (e["day_start"], e["day_end"], e["name"].lower())
            if key not in merged:
                merged[key] = e
                merged[key]["source_ts"] = ts
    return sorted(merged.values(), key=lambda e: (e["day_start"],))


def build_year(year: int) -> list[dict]:
    entries = []
    if year <= 2009:
        entries += build_old_format_year(year)
    if year >= 2008:
        entries += build_new_format_year(year)
    out_path = os.path.join(OUT_DIR, f"{year}.json")
    with open(out_path, "w", encoding="utf-8") as f:
        json.dump({"year": year, "format": "merged", "entries": entries}, f, indent=2)
    return entries


if __name__ == "__main__":
    year = int(sys.argv[1])
    entries = build_year(year)
    print(f"Year {year}: {len(entries)} entries")
    for e in entries:
        if "day_start" in e:
            if e["day_start"] == e["day_end"]:
                print(f"  {e['day_start']}  {e['name']}")
            else:
                print(f"  {e['day_start']}..{e['day_end']}  {e['name']}")
        else:
            print(f"  {e['year']}-{e['month']:02d} {e['day_start']}-{e['day_end']}  {e['name']}")
