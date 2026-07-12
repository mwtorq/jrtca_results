"""Parse the old terrier.com/trial/trials.php3 (and .php4) calendar-style
archive.org snapshot format into (month, day_start, day_end, name, location)
tuples.
"""
from __future__ import annotations

import re

MONTHS = {
    "Jan": 1, "Feb": 2, "Mar": 3, "Apr": 4, "May": 5, "Jun": 6,
    "Jul": 7, "Aug": 8, "Sep": 9, "Oct": 10, "Nov": 11, "Dec": 12,
}

ROW_RE = re.compile(
    r'<td[^>]*rowspan="2"><font size="5"[^>]*>(?P<month>Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)'
    r'<br>\s*(?P<days>\d{1,2}(?:\s*-\s*\d{1,2})?)\s*<br>.*?</td>\s*'
    r'<td[^>]*><font size="2"[^>]*><b>(?P<name>.+?)</b>',
    re.DOTALL,
)

# "Mid" template (~2003-2008): <td class="date">...<br>Mon DD(-DD)?</td>
# followed by <td class="name">...<td class="name2">NAME &nbsp;</td>
MID_ROW_RE = re.compile(
    r'<td[^>]*class="date"[^>]*>.*?<br>(?P<month>Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)\s+'
    r'(?P<days>\d{1,2}(?:\s*-\s*\d{1,2})?)</td>\s*'
    r'<td[^>]*class="name"[^>]*>.*?<td class="name2">(?P<name>.+?)\s*&nbsp;\s*</td>',
    re.DOTALL,
)


def _process_matches(matches, snapshot_year: int) -> list[dict]:
    results = []
    year = snapshot_year
    prev_month_num = 0
    for m in matches:
        month_str = m.group("month")
        month_num = MONTHS[month_str]
        days_str = m.group("days").replace(" ", "")
        if "-" in days_str:
            day_start, day_end = days_str.split("-")
        else:
            day_start = day_end = days_str
        name = m.group("name")
        name = re.sub(r"&amp;", "&", name)
        name = re.sub(r"<[^>]+>", "", name)
        name = re.sub(r"\s+", " ", name).strip()
        if not name:
            continue

        # Entries are chronological; if month drops (e.g. Dec -> Jan), we've
        # crossed a year boundary.
        if month_num < prev_month_num - 1:  # allow same-month repeats
            year += 1
        prev_month_num = month_num

        results.append(
            {
                "month": month_num,
                "day_start": int(day_start),
                "day_end": int(day_end),
                "name": name,
                "year": year,
            }
        )
    return results


def parse_snapshot(html: str, snapshot_year: int, snapshot_month: int) -> list[dict]:
    """Return list of {month, day_start, day_end, name, year} dicts."""
    old_matches = list(ROW_RE.finditer(html))
    if old_matches:
        return _process_matches(old_matches, snapshot_year)
    mid_matches = list(MID_ROW_RE.finditer(html))
    return _process_matches(mid_matches, snapshot_year)


if __name__ == "__main__":
    import sys

    path = sys.argv[1] if len(sys.argv) > 1 else "snap_2002.html"
    with open(path, "r", encoding="utf-8", errors="ignore") as f:
        html = f.read()
    entries = parse_snapshot(html, 2002, 1)
    print(f"Parsed {len(entries)} entries")
    for e in entries:
        print(f"  {e['year']}-{e['month']:02d} {e['day_start']}-{e['day_end']}  {e['name']}")
