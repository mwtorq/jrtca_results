"""Match a year's recovered archive.org trial schedule against DB trials
still showing a Jan-1 placeholder StartDate, and report/apply confident
matches.
"""
from __future__ import annotations

import difflib
import json
import os
import re
import sys
from datetime import datetime, timedelta

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from populate_trialresults_fixed import get_connection

SCHEDULES_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "schedules")

ROMAN_RE = re.compile(r"^[IVXLCDM]+$")
ARABIC_TO_ROMAN = {"1": "I", "2": "II", "3": "III", "4": "IV"}
ROMAN_VALUES = {"I": 1, "V": 5, "X": 10, "L": 50, "C": 100, "D": 500, "M": 1000}


def suffix_to_int(s: str | None) -> int | None:
    """Convert a roman-numeral or arabic-digit suffix to its integer value,
    so e.g. DB suffix 'V' can be recognized as the same position as an
    archive entry's '5'."""
    if not s:
        return None
    if s.isdigit():
        return int(s)
    if not ROMAN_RE.match(s):
        return None
    total = 0
    prev = 0
    for ch in reversed(s):
        val = ROMAN_VALUES[ch]
        total += -val if val < prev else val
        prev = max(prev, val)
    return total


def strip_suffix(name: str) -> tuple[str, str | None]:
    """Split trailing numeral suffix (roman or arabic) off a trial name.
    Returns (base_name, suffix_or_None)."""
    name = name.strip()
    trailing_paren = ""
    m = re.match(r"^(.*\S)\s*(\(\d{4}\))$", name)
    if m:
        name, trailing_paren = m.group(1), " " + m.group(2)
    tokens = name.strip().split()
    if not tokens:
        return name + trailing_paren, None
    last = tokens[-1].strip(".,")
    if ROMAN_RE.match(last) or last in ARABIC_TO_ROMAN:
        suffix = ARABIC_TO_ROMAN.get(last, last)
        base = " ".join(tokens[:-1]) + trailing_paren
        return base, suffix
    return name + trailing_paren, None


def normalize_base(name: str) -> str:
    name = name.lower()
    name = re.sub(r"\(.*?\)", " ", name)  # drop parentheticals
    name = re.sub(r"[^a-z0-9 ]", " ", name)
    name = re.sub(r"\bnumber\b", " ", name)
    name = re.sub(r"\band\b", " ", name)
    # Standalone 4-digit years (e.g. "2002 Yuletide", "Carolinas Winter
    # Festival 2002") are inconsistently present on one side or the other -
    # the enclosing year-file already disambiguates the year, so they only
    # dilute the similarity score between an otherwise-identical name.
    name = re.sub(r"\b(19|20)\d{2}\b", " ", name)
    name = re.sub(r"\s+", " ", name).strip()
    return name


STOPWORDS = {
    "terrier", "terriers", "trial", "trials", "classic", "jrtc", "jrtca",
    "annual", "challenge", "the", "of", "for", "in", "at", "a", "b",
    "rated", "jrtn", "club", "hunt", "cup", "event", "invitational",
    "extravaganza", "fest", "festival",
}


def token_jaccard(a: str, b: str) -> float:
    ta = {t for t in a.split() if t not in STOPWORDS}
    tb = {t for t in b.split() if t not in STOPWORDS}
    if not ta or not tb:
        return 0.0
    inter = ta & tb
    union = ta | tb
    jaccard = len(inter) / len(union)
    # A short abbreviated DB name (e.g. "PNWJRTN") that is fully contained
    # within a longer archive name ("PNWJRTN Spring Classic") is still a
    # confident match even though the raw Jaccard score is diluted.
    smaller, larger = (ta, tb) if len(ta) <= len(tb) else (tb, ta)
    if smaller and smaller <= larger:
        jaccard = max(jaccard, 0.5)
    return jaccard


def _month_day_to_iso(year: int, month: int, day: int, wrapped: bool) -> str:
    if wrapped:
        month += 1
        if month > 12:
            month = 1
            year += 1
    return f"{year}-{month:02d}-{day:02d}"


COMBINE_RE = re.compile(
    r"^(.*?)\s+([IVXLCDM]+|\d+)\s*(?:&|and)\s*([IVXLCDM]+|\d+)\b.*$",
    re.IGNORECASE,
)


def split_ranged_entry(name: str, d_start: str, d_end: str) -> list[dict]:
    """For a trial name spanning d_start..d_end (ISO dates), produce one
    sub-entry per suffix ('Name I & II', 'Name I and II', 'Name XIX & XX
    Finale', etc.) with its own date. Also returns the unsplit whole-range
    entry (suffix=None) so unsuffixed DB names (e.g. 'JRTCA National Trial'),
    or DB names whose suffix doesn't textually appear in the combined name,
    can still match by position within the range."""
    whole = {"name": name, "date": d_start, "date_end": d_end, "day_start": d_start, "day_end": d_end}

    m = COMBINE_RE.match(name)
    if not m:
        return [whole]
    base, s1, s2 = m.group(1), m.group(2), m.group(3)
    s1 = ARABIC_TO_ROMAN.get(s1, s1)
    s2 = ARABIC_TO_ROMAN.get(s2, s2)
    # Preserve the pair's own suffix labels on the whole entry so a DB name
    # using the *same* numbering (e.g. "Pioneer Classic V" matching archive
    # "Pioneer Classic 5 and 6") can be positioned correctly even when it
    # isn't literally "I"/"II".
    whole["seq_s1"], whole["seq_s2"] = s1, s2
    return [
        {"name": f"{base} {s1}", "date": d_start, "date_end": d_start, "day_start": d_start, "day_end": d_end},
        {"name": f"{base} {s2}", "date": d_end, "date_end": d_end, "day_start": d_start, "day_end": d_end},
        whole,
    ]


def split_combined_entry(entry: dict) -> list[dict]:
    """Old-format entries carry (year, month, day_start, day_end) as plain
    ints with no explicit end-month; convert to ISO dates first."""
    name = entry["name"]
    day_start, day_end = entry["day_start"], entry["day_end"]
    wrapped = day_end < day_start
    d_start = _month_day_to_iso(entry["year"], entry["month"], day_start, False)
    d_end = _month_day_to_iso(entry["year"], entry["month"], day_end, wrapped)
    return split_ranged_entry(name, d_start, d_end)


def load_archive_entries(year: int) -> list[dict]:
    path = os.path.join(SCHEDULES_DIR, f"{year}.json")
    if not os.path.exists(path):
        return []
    with open(path, "r", encoding="utf-8") as f:
        data = json.load(f)
    out = []
    for e in data["entries"]:
        if "year" in e and "month" in e:
            out.extend(split_combined_entry(e))
        else:
            out.extend(split_new_format_entry(e))
    return out


def split_new_format_entry(entry: dict) -> list[dict]:
    """New-format entries carry day_start/day_end as ISO date strings
    already (single date if day_start == day_end)."""
    name = entry["name"]
    d_start, d_end = entry["day_start"], entry["day_end"]
    if d_start != d_end:
        return split_ranged_entry(name, d_start, d_end)

    # Single date given but the name is still a combined 'Name I & II' -
    # the page only listed one date for what's actually a 2-day event;
    # assume day 2 is the following day.
    whole = {"name": name, "date": d_start, "date_end": d_start, "day_start": d_start, "day_end": d_start}
    m = COMBINE_RE.match(name)
    if not m:
        return [whole]
    base, s1, s2 = m.group(1), m.group(2), m.group(3)
    s1 = ARABIC_TO_ROMAN.get(s1, s1)
    s2 = ARABIC_TO_ROMAN.get(s2, s2)
    d2 = (datetime.strptime(d_start, "%Y-%m-%d") + timedelta(days=1)).strftime("%Y-%m-%d")
    return [
        {"name": f"{base} {s1}", "date": d_start, "date_end": d_start, "day_start": d_start, "day_end": d2},
        {"name": f"{base} {s2}", "date": d2, "date_end": d2, "day_start": d_start, "day_end": d2},
        whole,
    ]


def load_missing_trials(year: int) -> list[tuple]:
    conn = get_connection()
    cur = conn.cursor()
    cur.execute(
        """
        SELECT TrialListID, TrialName
        FROM sResults.TrialList
        WHERE Year = ? AND MONTH(StartDate) = 1 AND DAY(StartDate) = 1
        ORDER BY TrialListID
        """,
        year,
    )
    rows = cur.fetchall()
    conn.close()
    return [(r[0], r[1]) for r in rows]


def match_year(year: int) -> dict:
    archive_entries = load_archive_entries(year)
    missing = load_missing_trials(year)

    # Precompute normalized base+suffix for archive entries. Names that are
    # still a combined "Name I & II" / "Name I and II" whole-range entry
    # (i.e. split_ranged_entry's unsplit fallback) get no suffix so they
    # fall back to the more reliable day_start/day_end range-based matching
    # instead of a bogus suffix derived from trailing garbage tokens.
    combined_re = re.compile(r"[IVXLCDM0-9]+\s*(?:&|and)\s*[IVXLCDM0-9]+", re.IGNORECASE)
    for e in archive_entries:
        if combined_re.search(e["name"]):
            base = combined_re.split(e["name"], maxsplit=1)[0]
            suffix = None
        else:
            base, suffix = strip_suffix(e["name"])
        e["base_norm"] = normalize_base(base)
        e["suffix"] = suffix

    matches = []
    unmatched = []
    for trial_id, trial_name in missing:
        base, suffix = strip_suffix(trial_name)
        base_norm = normalize_base(base)

        trial_upper = trial_name.upper()

        best = None
        best_score = -1.0
        best_date = None
        for e in archive_entries:
            # JRTCA (US club) and JRTCC (Canada club) are different
            # organizations; never cross-match between them.
            e_upper = e["name"].upper()
            if ("JRTCC" in trial_upper) != ("JRTCC" in e_upper):
                continue

            char_score = difflib.SequenceMatcher(None, base_norm, e["base_norm"]).ratio()
            jaccard = token_jaccard(base_norm, e["base_norm"])
            if jaccard < 0.34:
                continue
            score = 0.5 * char_score + 0.5 * jaccard

            date = None
            if suffix == e["suffix"]:
                date = e["date"]
            elif e["suffix"] is None and e["day_start"] != e["day_end"]:
                suffix_val = suffix_to_int(suffix)
                if suffix_val is not None and suffix_val == suffix_to_int(e.get("seq_s1")):
                    date = e["day_start"]
                elif suffix_val is not None and suffix_val == suffix_to_int(e.get("seq_s2")):
                    date = e["day_end"]
                elif "seq_s1" not in e:
                    # Genuinely unsuffixed archive entry (no numbering at
                    # all, e.g. "JRTCA Memorial Weekend Trial"); position
                    # DB suffix I/1 -> start of range, II/2 -> end of range.
                    if suffix in ("I", None):
                        date = e["day_start"]
                    elif suffix == "II":
                        date = e["day_end"]
            if date is None:
                continue

            if score > best_score:
                best_score = score
                best = e
                best_date = date

        if best and best_score >= 0.5:
            matches.append(
                {
                    "trial_id": trial_id,
                    "trial_name": trial_name,
                    "matched_name": best["name"],
                    "date": best_date,
                    "score": round(best_score, 3),
                }
            )
        else:
            unmatched.append({"trial_id": trial_id, "trial_name": trial_name})

    return {"year": year, "matches": matches, "unmatched": unmatched}


if __name__ == "__main__":
    year = int(sys.argv[1])
    result = match_year(year)
    print(f"Year {year}: {len(result['matches'])} matched, {len(result['unmatched'])} unmatched\n")
    print("MATCHES:")
    for m in sorted(result["matches"], key=lambda x: -x["score"]):
        print(f"  [{m['score']:.2f}] {m['trial_id']:5d} {m['trial_name']!r:45s} -> {m['matched_name']!r} @ {m['date']}")
    print("\nUNMATCHED:")
    for u in result["unmatched"]:
        print(f"  {u['trial_id']:5d} {u['trial_name']!r}")
