"""Parse the newer therealjackrussell.com/trial/trials.php archive.org
snapshot format (2009+) into per-trial dicts with day_start/day_end.

Each sub-trial entry's date cell may be a single date ('Mar 3, 2012') or a
range ('Sep 29-30, 2012', occasionally spanning a month boundary like
'Apr 30-May 1, 2012'). Earlier versions of this parser only handled the
single-date case and silently dropped every ranged entry, which is why
whole multi-day trials (and any trial announced only via a ranged listing)
were missing from the recovered schedule.
"""
from __future__ import annotations

import re

ENTRY_RE = re.compile(
    r'<td style="width:180px;white-space:nowrap">(?P<date>[^<]+)</td>\s*'
    r'<td align="center">(?P<name>[^<]+)</td>',
)

MONTHS = {
    m: i
    for i, m in enumerate(
        ["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"],
        start=1,
    )
}

DATE_SPAN_RE = re.compile(
    r"^(?P<mon1>[A-Za-z]{3})\s+(?P<day1>\d{1,2})"
    r"(?:\s*-\s*(?:(?P<mon2>[A-Za-z]{3})\s+)?(?P<day2>\d{1,2}))?"
    r",\s*(?P<year>\d{4})$"
)


def parse_date_span(date_str: str) -> tuple[str, str] | None:
    """Parse a date cell into (start_iso, end_iso). Returns None if unparseable."""
    m = DATE_SPAN_RE.match(date_str.strip())
    if not m:
        return None
    year = int(m.group("year"))
    mon1 = MONTHS.get(m.group("mon1"))
    if mon1 is None:
        return None
    day1 = int(m.group("day1"))
    start = f"{year}-{mon1:02d}-{day1:02d}"
    if m.group("day2"):
        day2 = int(m.group("day2"))
        end_year = year
        if m.group("mon2"):
            mon2 = MONTHS.get(m.group("mon2"))
            if mon2 is None:
                return None
        elif day2 < day1:
            # Some pages write a month-boundary range without naming the
            # second month, e.g. "Mar 31-01, 2012" meaning Mar 31-Apr 1.
            mon2 = mon1 + 1
            if mon2 > 12:
                mon2 = 1
                end_year += 1
        else:
            mon2 = mon1
        end = f"{end_year}-{mon2:02d}-{day2:02d}"
    else:
        end = start
    return start, end


def parse_snapshot(html: str) -> list[dict]:
    results = []
    for m in ENTRY_RE.finditer(html):
        date_str = m.group("date").strip()
        name = m.group("name").strip()
        name = re.sub(r"&amp;", "&", name)
        name = re.sub(r"\s+", " ", name)
        span = parse_date_span(date_str)
        if span is None:
            continue
        start, end = span
        results.append({"day_start": start, "day_end": end, "name": name})
    return results


if __name__ == "__main__":
    import sys

    path = sys.argv[1] if len(sys.argv) > 1 else "snap_2012.html"
    with open(path, "r", encoding="utf-8", errors="ignore") as f:
        html = f.read()
    entries = parse_snapshot(html)
    print(f"Parsed {len(entries)} entries")
    for e in entries:
        if e["day_start"] == e["day_end"]:
            print(f"  {e['day_start']}  {e['name']}")
        else:
            print(f"  {e['day_start']}..{e['day_end']}  {e['name']}")
