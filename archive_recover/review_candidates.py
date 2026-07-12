"""For every currently-unmatched (Jan-1 placeholder) trial in a given year,
show the best-scoring archive.org candidate(s) even if below the normal
auto-apply threshold - for manual human review/approval, not auto-application.
"""
from __future__ import annotations

import difflib
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from match_year import (
    load_archive_entries,
    load_missing_trials,
    normalize_base,
    strip_suffix,
    suffix_to_int,
    token_jaccard,
)


def review_year(year: int, top_n: int = 3):
    archive_entries = load_archive_entries(year)
    missing = load_missing_trials(year)

    combined_re = __import__("re").compile(r"[IVXLCDM0-9]+\s*(?:&|and)\s*[IVXLCDM0-9]+", __import__("re").IGNORECASE)
    for e in archive_entries:
        if combined_re.search(e["name"]):
            base = combined_re.split(e["name"], maxsplit=1)[0]
            suffix = None
        else:
            base, suffix = strip_suffix(e["name"])
        e["base_norm"] = normalize_base(base)
        e["suffix"] = suffix

    results = []
    for trial_id, trial_name in missing:
        base, suffix = strip_suffix(trial_name)
        base_norm = normalize_base(base)
        trial_upper = trial_name.upper()

        scored = []
        for e in archive_entries:
            e_upper = e["name"].upper()
            if ("JRTCC" in trial_upper) != ("JRTCC" in e_upper):
                continue
            char_score = difflib.SequenceMatcher(None, base_norm, e["base_norm"]).ratio()
            jaccard = token_jaccard(base_norm, e["base_norm"])
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
                    if suffix in ("I", None):
                        date = e["day_start"]
                    elif suffix == "II":
                        date = e["day_end"]
            if date is None:
                # still show it as a candidate name/date-range, just flag no clean suffix mapping
                date = f"{e['day_start']}..{e['day_end']}" if e["day_start"] != e["day_end"] else e["day_start"]

            scored.append((score, e["name"], date))

        scored.sort(key=lambda x: -x[0])
        results.append((trial_id, trial_name, scored[:top_n]))
    return results


if __name__ == "__main__":
    year = int(sys.argv[1])
    for trial_id, trial_name, candidates in review_year(year):
        print(f"{trial_id:5d} {trial_name!r}")
        for score, name, date in candidates:
            print(f"        [{score:.2f}] {name!r} @ {date}")
        print()
