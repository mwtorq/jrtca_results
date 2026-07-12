"""Parse the newest therealjackrussell.com/trial/trials.php archive.org
snapshot format (~Nov 2016+): each trial is a bordered "card" with an <h2>
name heading followed by a "<date> in <location>" line, e.g.

    <h2>Sunshine Showdown I &amp; II</h2>
    <p><b>Apr 1-2, 2017 in <span ...>Williston, Florida</span></b></p>

This superseded the earlier `<td style="width:180px...">` table-row format
used from ~2009-2016 (see parse_new_format.py).
"""
from __future__ import annotations

import re

from parse_new_format import parse_date_span

ENTRY_RE = re.compile(
    r"<h2>(?P<name>[^<]+)</h2>\s*<p>\s*<b>\s*(?P<date>[A-Za-z]{3}\s+\d{1,2}(?:\s*-\s*(?:[A-Za-z]{3}\s+)?\d{1,2})?,\s*\d{4})\s+in\b",
    re.IGNORECASE,
)


def parse_snapshot(html: str) -> list[dict]:
    results = []
    for m in ENTRY_RE.finditer(html):
        name = m.group("name").strip()
        name = re.sub(r"&amp;", "&", name)
        name = re.sub(r"\s+", " ", name)
        span = parse_date_span(m.group("date").strip())
        if span is None:
            continue
        start, end = span
        results.append({"day_start": start, "day_end": end, "name": name})
    return results


if __name__ == "__main__":
    import sys

    path = sys.argv[1] if len(sys.argv) > 1 else "snap_card.html"
    with open(path, "r", encoding="utf-8", errors="ignore") as f:
        html = f.read()
    entries = parse_snapshot(html)
    print(f"Parsed {len(entries)} entries")
    for e in entries:
        if e["day_start"] == e["day_end"]:
            print(f"  {e['day_start']}  {e['name']}")
        else:
            print(f"  {e['day_start']}..{e['day_end']}  {e['name']}")
