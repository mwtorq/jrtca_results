#!/usr/bin/env python3
"""
Compare normalized trial data against the originally downloaded results files.

Every trial records the file it was loaded from in TrialList.TrialResultFilePath.
This module re-parses that already-downloaded file (never the website) with the
same parser the loader uses, then checks that the dog, owner, class, and division
names sitting in the database still describe the same entries the source file
does. Name cleanup and duplicate merging can quietly rewrite one entry into a
different one, and this is what catches it.

Differences are written to a CSV and are not applied, because the source files
are not a clean reference: they carry scanning typos the database has since had
cleaned up, they credit handlers with "owned by" in handler classes, and they
name whichever member of a household showed the dog that day. Each --fix flag
turns on one narrow category of repair once its findings have been reviewed.

The loading process runs this as: normalize, compare, normalize, compare.

Usage:
    python verify_trial_normalization.py                 # all loaded trials
    python verify_trial_normalization.py --trial-id 1691
    python verify_trial_normalization.py --year 2017
    python verify_trial_normalization.py --folder "MO Earthdogs"
    python verify_trial_normalization.py --fix-dog-merges
"""

import argparse
import contextlib
import csv
import io
import os
import re
import sys
from collections import defaultdict, deque
from dataclasses import dataclass
from datetime import datetime

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from normalize_trialresults_data import (
    normalize_class_name_full,
    normalize_division_name_full,
    normalize_dog_name,
    normalize_owner_name,
    person_cluster_key,
    run_batch_post_trial_normalization,
)
from parse_catalog import names_are_similar
from populate_trialresults_fixed import (
    get_connection,
    get_or_create_class,
    get_or_create_division,
    get_or_create_dog,
    get_or_create_owner,
    parse_trial_source_file,
    strip_entries_from_class_name,
)

DEFAULT_REPORT_PATH = "normalization_skew_report.csv"
# Handler classes credit the child/junior handling the dog with "owned by", so
# the name on those lines is not the owner the rest of the file records.
_HANDLER_CLASS_RE = re.compile(r"\bhandler\b", re.IGNORECASE)
MIN_SOURCE_YEAR = 1984
MAX_SOURCE_YEAR = 2026


def print_ts(msg: str) -> None:
    print(f"[{datetime.now().strftime('%H:%M:%S')}] {msg}", flush=True)


@dataclass
class SkewIssue:
    """One place where the database disagrees with the downloaded source file."""

    trial_id: int
    trial_name: str
    pass_no: int
    kind: str
    placement_id: int | None
    source_value: str
    db_value: str
    action: str
    detail: str = ""


@dataclass
class TrialComparison:
    trial_id: int
    pass_no: int
    source_rows: int = 0
    db_rows: int = 0
    matched: int = 0
    issues: list[SkewIssue] = None
    corrected: int = 0

    def __post_init__(self):
        if self.issues is None:
            self.issues = []


def source_year_for_file(file_path: str, fallback_year: int | None = None) -> int | None:
    """Recover the year the loader used: the year folder, else a year in the name."""
    normalized = (file_path or "").replace("\\", "/")
    parts = [p for p in normalized.split("/") if p]
    for part in reversed(parts[:-1]):
        if re.fullmatch(r"\d{4}", part) and MIN_SOURCE_YEAR <= int(part) <= MAX_SOURCE_YEAR:
            return int(part)
    match = re.search(r"(\d{4})", os.path.basename(normalized))
    if match and MIN_SOURCE_YEAR <= int(match.group(1)) <= MAX_SOURCE_YEAR:
        return int(match.group(1))
    return fallback_year


def _key(text: str) -> str:
    return re.sub(r"[^a-z0-9]", "", (text or "").lower())


def _stable(normalizer, value: str, limit: int = 4) -> tuple[str, bool]:
    """Apply a normalizer until it stops changing the value.

    Normalization runs more than once over the life of a row, so the value the
    database settles on is the normalizer's fixed point, not its first output.
    """
    current = value or ""
    for _ in range(limit):
        nxt = normalizer(current)
        if nxt == current:
            return current, True
        current = nxt
    return current, False


# Height/class words the placement parser sometimes glues onto an owner field
# ("Tony & Kim Anderson Under"). The database value is the clean one in that case.
_OWNER_LEAK_SUFFIX_RE = re.compile(
    r"\s+(?:over|under|up\s*to|open|adult|puppy|veteran|novice|"
    r"champion|reserve|best|dog|bitch|male|female)\s*$",
    re.IGNORECASE,
)


# Race/go-to-ground times that trail an owner in some result lines
# ("Shirley LaMear - time of 8.62 seconds").
_OWNER_TIME_SUFFIX_RE = re.compile(
    r"\s*[-–—]?\s*(?:tme|time)\s*(?:of\s+)?[\d:.]+\s*(?:seconds?|secs?)?\s*$",
    re.IGNORECASE,
)


def _strip_owner_leak(name: str) -> str:
    current = _OWNER_TIME_SUFFIX_RE.sub("", (name or "").strip()).strip(" ,-")
    previous = None
    while current != previous:
        previous = current
        current = _OWNER_LEAK_SUFFIX_RE.sub("", current).strip(" ,&")
    return current


def _name_tokens(name: str) -> set[str]:
    return {
        token
        for token in re.split(r"[^a-z0-9]+", (name or "").lower())
        if len(token) > 1 and token != "and"
    }


def _edit_distance(a: str, b: str) -> int:
    """Damerau-Levenshtein distance, so a transposition counts as one edit.

    Scanned sources swap adjacent letters often ("Ohlhesier" for "Ohlheiser"),
    and those are the same person rather than a normalization error.
    """
    if a == b:
        return 0
    previous_previous: list[int] = []
    previous = list(range(len(b) + 1))
    for i, char_a in enumerate(a):
        current = [i + 1]
        for j, char_b in enumerate(b):
            cost = 0 if char_a == char_b else 1
            value = min(
                previous[j + 1] + 1,
                current[j] + 1,
                previous[j] + cost,
            )
            if (
                i > 0
                and j > 0
                and char_a == b[j - 1]
                and a[i - 1] == char_b
            ):
                value = min(value, previous_previous[j - 1] + cost)
            current.append(value)
        previous_previous = previous
        previous = current
    return previous[-1]


def _edit_distance_at_most_one(a: str, b: str) -> bool:
    return abs(len(a) - len(b)) <= 1 and _edit_distance(a, b) <= 1


def _is_spelling_variant(a: str, b: str) -> bool:
    """True when two names differ only by the kind of typo a scan introduces."""
    if not a or not b:
        return False
    limit = 1 if min(len(a), len(b)) <= 5 else 2
    return abs(len(a) - len(b)) <= limit and _edit_distance(a, b) <= limit


def _tokens_compatible(smaller: set[str], larger: set[str]) -> bool:
    """True when every name in the smaller set appears in the larger one.

    Co-owners are written in either order and are frequently misspelled by one
    character ("Wilburn/Emmett" vs "Emmet/Wilburn"), so order is ignored and
    long tokens tolerate a single-character difference.
    """
    for token in smaller:
        if token in larger:
            continue
        if len(token) >= 4 and any(
            len(other) >= 4 and _edit_distance_at_most_one(token, other)
            for other in larger
        ):
            continue
        return False
    return True


def dogs_match(expected: str, actual: str) -> bool:
    if not expected:
        return True
    if not actual:
        return False
    if _key(expected) == _key(actual):
        return True
    return names_are_similar(expected, actual)


DOG_SPELLING = "spelling"
DOG_KENNELMATE = "kennelmate"
DOG_UNRELATED = "unrelated"


def classify_dog_difference(expected: str, actual: str) -> str:
    """Say what kind of difference separates two dog names.

    "spelling"    the same name, scanned badly ("Sow's Ear Lberty" / "Liberty")
    "kennelmate"  a shared kennel prefix but a different dog ("Northgate
                  Britton" / "Northgate Bristol T"), which is what an over-eager
                  merge of littermates looks like
    "unrelated"   nothing in common, so a placement landed on the wrong dog
    """
    # Defer to the merge rule itself first, so the report agrees with what
    # normalization would decide about the same two names.
    if names_are_similar(expected, actual):
        return DOG_SPELLING

    expected_tokens = _name_tokens(expected)
    actual_tokens = _name_tokens(actual)
    shared = expected_tokens & actual_tokens

    if not shared:
        if _is_spelling_variant(_key(expected), _key(actual)):
            return DOG_SPELLING
        near = any(
            len(left) >= 4 and len(right) >= 4 and _edit_distance_at_most_one(left, right)
            for left in expected_tokens
            for right in actual_tokens
        )
        return DOG_SPELLING if near else DOG_UNRELATED

    # Names agree on part of the name; the rest decides whether it is one typo
    # or two different dogs from the same kennel.
    expected_rest = "".join(sorted(expected_tokens - shared))
    actual_rest = "".join(sorted(actual_tokens - shared))
    if not expected_rest and not actual_rest:
        return DOG_SPELLING
    if _edit_distance(expected_rest, actual_rest) <= 1:
        return DOG_SPELLING
    return DOG_KENNELMATE


def owners_match(expected: str, actual: str) -> bool:
    """True when both names can describe the same ownership of one entry.

    Co-ownership is treated as agreement: a source listing one of two owners
    ("Patty Nocek") does not contradict a stored pair ("Carl & Patty Nocek").
    """
    if not expected:
        return True
    if not actual:
        return False

    actual_key = person_cluster_key(actual)
    for candidate in (expected, _strip_owner_leak(expected)):
        if not candidate:
            continue
        if person_cluster_key(candidate) == actual_key:
            return True
        if names_are_similar(candidate, actual):
            return True
        if _is_spelling_variant(person_cluster_key(candidate), actual_key):
            return True

    expected_tokens = _name_tokens(_strip_owner_leak(expected) or expected)
    actual_tokens = _name_tokens(actual)
    if expected_tokens and actual_tokens:
        smaller, larger = sorted((expected_tokens, actual_tokens), key=len)
        if _tokens_compatible(smaller, larger):
            return True
    return False


def names_equal(expected: str, actual: str) -> bool:
    if not expected:
        return True
    return _key(expected) == _key(actual)


def divisions_match(expected: str, actual: str) -> bool:
    """Allow the stored division to be a refinement of the one in the source.

    A file may head a block "Racing Division" where the database records the
    specific "Racing Division - Flat Races"; the narrower name is extra detail,
    not a placement that drifted into the wrong division.
    """
    if not expected:
        return True
    expected_key, actual_key = _key(expected), _key(actual)
    if expected_key == actual_key:
        return True
    return expected_key.startswith(actual_key) or actual_key.startswith(expected_key)


def expected_rows_from_source(placements) -> tuple[list[dict], list[tuple[str, str]]]:
    """Build the rows the database should hold, plus any unstable normalizations."""
    rows: list[dict] = []
    unstable: list[tuple[str, str]] = []

    for order, placement in enumerate(placements):
        division, div_stable = _stable(
            normalize_division_name_full, placement.division or "",
        )
        clean_class, _entries = strip_entries_from_class_name(placement.class_name or "")
        class_name, class_stable = _stable(
            lambda name: normalize_class_name_full(name, division), clean_class,
        )
        dog, dog_stable = _stable(normalize_dog_name, placement.dog_name or "")
        owner, owner_stable = _stable(normalize_owner_name, placement.owner_name or "")

        if not div_stable:
            unstable.append(("division", placement.division or ""))
        if not class_stable:
            unstable.append(("class", placement.class_name or ""))
        if not dog_stable:
            unstable.append(("dog", placement.dog_name or ""))
        if not owner_stable:
            unstable.append(("owner", placement.owner_name or ""))

        rows.append(
            {
                "order": order,
                "division": division,
                "class_name": class_name,
                "dog": dog,
                "owner": owner,
                "result": placement.placement or "",
                "raw_dog": placement.dog_name or "",
                "raw_owner": placement.owner_name or "",
                "raw_class": placement.class_name or "",
                "class_key": _key(class_name),
                "result_key": _key(placement.placement or ""),
                "dog_key": _key(dog),
                "owner_key": _key(owner),
            }
        )
    return rows, unstable


def db_rows_for_trial(cursor, trial_id: int) -> list[dict]:
    cursor.execute(
        """
        SELECT
            p.TrialPlacementsID,
            p.TrialClassID,
            tc.EntryCount,
            c.ClassID,
            c.ClassName,
            dv.DivisionID,
            dv.DivisionName,
            d.DogID,
            d.DogName,
            o.OwnerID,
            o.OwnerName,
            p.Result
        FROM [sResults].[TrialPlacements] p
        JOIN [sResults].[TrialClass] tc ON tc.TrialClassID = p.TrialClassID
        JOIN [sResults].[Class] c ON c.ClassID = tc.ClassID
        JOIN [sResults].[Division] dv ON dv.DivisionID = c.DivisionID
        LEFT JOIN [sResults].[Dog] d ON d.DogID = p.DogID
        LEFT JOIN [sResults].[Owner] o ON o.OwnerID = d.OwnerID
        WHERE p.TrialListID = ?
        ORDER BY p.TrialPlacementsID
        """,
        trial_id,
    )

    rows = []
    for record in cursor.fetchall():
        (
            placement_id,
            trialclass_id,
            entry_count,
            class_id,
            class_name,
            division_id,
            division_name,
            dog_id,
            dog_name,
            owner_id,
            owner_name,
            result,
        ) = record
        rows.append(
            {
                "placement_id": placement_id,
                "trialclass_id": trialclass_id,
                "entry_count": entry_count,
                "class_id": class_id,
                "class_name": class_name or "",
                "division_id": division_id,
                "division_name": division_name or "",
                "dog_id": dog_id,
                "dog_name": dog_name or "",
                "owner_id": owner_id,
                "owner_name": owner_name or "",
                "result": result or "",
                "class_key": _key(class_name),
                "result_key": _key(result),
                "dog_key": _key(dog_name),
                "owner_key": _key(owner_name),
            }
        )
    return rows


# Progressively looser pairings: a row is matched on the strongest key that still
# has a partner, so the fields that disagree are the ones left over to report.
_MATCH_STAGES = (
    ("class_key", "result_key", "dog_key"),
    ("class_key", "result_key", "owner_key"),
    ("class_key", "result_key"),
    ("result_key", "dog_key"),
    ("class_key", "dog_key"),
    ("dog_key",),
)

# Stages that pin a row to one class and one placing. Only these identify an
# entry precisely enough to act on; looser stages can pair a dog's win in one
# class with the same dog's win in another, which would move a correct row.
_ANCHORED_STAGES = frozenset({0, 1, 2})


def pair_rows(
    source_rows: list[dict], db_rows: list[dict],
) -> tuple[list[tuple[int, int, int]], list[int], list[int]]:
    """Pair source placements with database placements.

    Returns (pairs, unmatched_source, unmatched_db) where each pair carries the
    index of the stage that matched it, i.e. how much of the row agreed.
    """
    remaining_src = list(range(len(source_rows)))
    remaining_db = list(range(len(db_rows)))
    pairs: list[tuple[int, int, int]] = []

    for stage_no, stage in enumerate(_MATCH_STAGES):
        if not remaining_src or not remaining_db:
            break

        buckets: dict[tuple, deque] = defaultdict(deque)
        for db_idx in remaining_db:
            buckets[tuple(db_rows[db_idx][f] for f in stage)].append(db_idx)

        still_src: list[int] = []
        matched_db: set[int] = set()
        for src_idx in remaining_src:
            queue = buckets.get(tuple(source_rows[src_idx][f] for f in stage))
            if queue:
                db_idx = queue.popleft()
                pairs.append((src_idx, db_idx, stage_no))
                matched_db.add(db_idx)
            else:
                still_src.append(src_idx)

        remaining_src = still_src
        remaining_db = [idx for idx in remaining_db if idx not in matched_db]

    return pairs, remaining_src, remaining_db


def find_or_create_trial_class(
    cursor, trial_id: int, class_id: int, entry_count=None,
) -> int | None:
    cursor.execute(
        """
        SELECT TrialClassID FROM [sResults].[TrialClass]
        WHERE TrialListID = ? AND ClassID = ?
        """,
        trial_id,
        class_id,
    )
    row = cursor.fetchone()
    if row:
        return row[0]

    cursor.execute("SELECT ISNULL(MAX(TrialClassID), 0) + 1 FROM [sResults].[TrialClass]")
    new_id = cursor.fetchone()[0]
    cursor.execute(
        """
        INSERT INTO [sResults].[TrialClass] (TrialClassID, TrialListID, ClassID, EntryCount)
        VALUES (?, ?, ?, ?)
        """,
        new_id,
        trial_id,
        class_id,
        entry_count,
    )
    return new_id


def owner_is_actionable(owner_name: str) -> bool:
    """A lone surname is too thin a parse to reassign ownership on."""
    return len(_name_tokens(_strip_owner_leak(owner_name)) ) >= 2


def owners_share_a_name(expected: str, actual: str) -> bool:
    """True when two owner names have a word in common, i.e. one household.

    Results files credit a dog to whichever family member handled it that day,
    so these differences are ambiguous in the source rather than caused by
    normalization, and splitting the dog on them would invent a second dog.
    """
    expected_tokens = _name_tokens(_strip_owner_leak(expected))
    actual_tokens = _name_tokens(actual)
    if not expected_tokens or not actual_tokens:
        return False
    if expected_tokens & actual_tokens:
        return True
    return any(
        len(left) >= 4 and len(right) >= 4 and _edit_distance_at_most_one(left, right)
        for left in expected_tokens
        for right in actual_tokens
    )


def resolve_dog_by_name(cursor, dog_name: str, owner_id: int | None) -> int | None:
    """Find the record for the dog a source file names, preferring its owner.

    get_or_create_dog adds a second row whenever the name already exists under
    another owner. Splitting a placement out of a merge must not do that, so an
    existing record for the name is reused before a new one is created.
    """
    if owner_id:
        cursor.execute(
            "SELECT DogID FROM [sResults].[Dog] WHERE DogName = ? AND OwnerID = ?",
            dog_name,
            owner_id,
        )
        row = cursor.fetchone()
        if row:
            return row[0]

    cursor.execute(
        "SELECT TOP 1 DogID FROM [sResults].[Dog] WHERE DogName = ? ORDER BY DogID",
        dog_name,
    )
    row = cursor.fetchone()
    if row:
        return row[0]

    return get_or_create_dog(cursor, dog_name, owner_id)


def repoint_placement_entities(
    cursor, row: dict, src: dict, *, use_source_dog: bool, use_source_owner: bool,
) -> bool:
    """Point a placement at the dog/owner the source file names."""
    dog_name = (src["dog"] if use_source_dog else row["dog_name"]) or row["dog_name"]
    if not dog_name:
        return False

    owner_id = row["owner_id"]
    if use_source_owner and src["owner"]:
        owner_id = get_or_create_owner(cursor, src["owner"]) or owner_id

    if use_source_dog:
        dog_id = resolve_dog_by_name(cursor, dog_name, owner_id)
    else:
        dog_id = get_or_create_dog(cursor, dog_name, owner_id)
    if not dog_id or dog_id == row["dog_id"]:
        return False

    cursor.execute(
        "UPDATE [sResults].[TrialPlacements] SET DogID = ? WHERE TrialPlacementsID = ?",
        dog_id,
        row["placement_id"],
    )
    row["dog_id"] = dog_id
    return True


def repoint_placement_class(
    cursor, trial_id: int, row: dict, src: dict, vacated: set[int],
) -> bool:
    """Point a placement at the class/division the source file names."""
    class_name = src["class_name"]
    if not class_name:
        return False

    div_id = get_or_create_division(cursor, src["division"] or row["division_name"])
    if not div_id:
        return False
    class_id = get_or_create_class(cursor, class_name, div_id)
    if not class_id:
        return False

    trialclass_id = find_or_create_trial_class(
        cursor, trial_id, class_id, row["entry_count"],
    )
    if not trialclass_id or trialclass_id == row["trialclass_id"]:
        return False

    cursor.execute(
        "UPDATE [sResults].[TrialPlacements] SET TrialClassID = ? WHERE TrialPlacementsID = ?",
        trialclass_id,
        row["placement_id"],
    )
    vacated.add(row["trialclass_id"])
    row["trialclass_id"] = trialclass_id
    return True


def drop_vacated_trial_classes(cursor, vacated: set[int]) -> int:
    """Remove class rows this run emptied, leaving entry-only classes alone."""
    removed = 0
    for trialclass_id in vacated:
        cursor.execute(
            """
            SELECT COUNT(*) FROM [sResults].[TrialPlacements]
            WHERE TrialClassID = ?
            """,
            trialclass_id,
        )
        if cursor.fetchone()[0]:
            continue
        cursor.execute(
            """
            DELETE FROM [sResults].[TrialClass]
            WHERE TrialClassID = ? AND ISNULL(EntriesOnly, 0) = 0
            """,
            trialclass_id,
        )
        removed += cursor.rowcount if cursor.rowcount and cursor.rowcount > 0 else 0
    return removed


def compare_trial(
    conn,
    trial: dict,
    source_rows: list[dict],
    pass_no: int,
    *,
    correct: bool = True,
    fix_class_assignments: bool = False,
    fix_owner_assignments: bool = False,
    fix_dog_merges: bool = False,
) -> TrialComparison:
    """Compare one trial against its source file, correcting skew when allowed."""
    cursor = conn.cursor()
    db_rows = db_rows_for_trial(cursor, trial["trial_id"])
    pairs, unmatched_src, unmatched_db = pair_rows(source_rows, db_rows)

    comparison = TrialComparison(
        trial_id=trial["trial_id"],
        pass_no=pass_no,
        source_rows=len(source_rows),
        db_rows=len(db_rows),
        matched=len(pairs),
    )
    vacated: set[int] = set()

    def add_issue(kind, placement_id, source_value, db_value, action, detail=""):
        comparison.issues.append(
            SkewIssue(
                trial_id=trial["trial_id"],
                trial_name=trial["trial_name"],
                pass_no=pass_no,
                kind=kind,
                placement_id=placement_id,
                source_value=source_value,
                db_value=db_value,
                action=action,
                detail=detail,
            )
        )

    source_class_keys = {row["class_key"] for row in source_rows if row["class_key"]}

    # A results file often credits one dog to different members of the same
    # household from class to class. Consolidating those is what normalization
    # is for, so any owner the source ties to this dog counts as agreement.
    source_owners_by_dog: dict[str, list[str]] = defaultdict(list)
    for row in source_rows:
        if row["dog_key"] and row["owner"]:
            source_owners_by_dog[row["dog_key"]].append(row["owner"])

    for src_idx, db_idx, stage_no in pairs:
        src = source_rows[src_idx]
        row = db_rows[db_idx]

        candidate_owners = source_owners_by_dog.get(src["dog_key"]) or [src["owner"]]
        dog_skewed = not dogs_match(src["dog"], row["dog_name"])
        owner_skewed = bool(src["owner"]) and not any(
            owners_match(candidate, row["owner_name"]) for candidate in candidate_owners
        )
        class_skewed = not names_equal(src["class_name"], row["class_name"])
        division_skewed = not divisions_match(src["division"], row["division_name"])

        if not (dog_skewed or owner_skewed or class_skewed or division_skewed):
            continue

        anchored = stage_no in _ANCHORED_STAGES
        # Any class disagreement means the row could not be anchored by class, so
        # the pairing itself is in doubt: the same dog often places in several
        # classes. Moving such a row is opt-in; by default it is only reported.
        entry_agrees = not dog_skewed and not owner_skewed
        class_absent_from_source = row["class_key"] not in source_class_keys
        allow_class_fix = (
            fix_class_assignments
            and entry_agrees
            and (
                (class_skewed and class_absent_from_source)
                or (division_skewed and not class_skewed)
            )
        )

        handler_class = bool(
            _HANDLER_CLASS_RE.search(src["class_name"] or "")
            or _HANDLER_CLASS_RE.search(row["class_name"] or "")
        )
        # A merge that deleted a dog without moving its placements leaves the
        # row pointing at nothing; the source still says which dog it was.
        dog_orphaned = row["dog_id"] is None
        if dog_orphaned:
            dog_difference = DOG_UNRELATED
        elif dog_skewed:
            dog_difference = classify_dog_difference(src["dog"], row["dog_name"])
        else:
            dog_difference = ""
        # Split whenever the merge rule itself says these are two dogs; a
        # spelling variant is the rule saying they are one, so it stays merged.
        dog_fix_allowed = fix_dog_merges and dog_difference in (
            DOG_UNRELATED,
            DOG_KENNELMATE,
        )
        owner_household = owner_skewed and owners_share_a_name(src["owner"], row["owner_name"])
        owner_fix_allowed = (
            fix_owner_assignments
            and owner_skewed
            and owner_is_actionable(src["owner"])
            and not owner_household
            and not handler_class
        )
        allow_entity_fix = anchored and (dog_fix_allowed or owner_fix_allowed)

        entity_fixed = False
        class_fixed = False
        if correct and allow_entity_fix:
            # A dog being split off needs the owner the source gives it, or the
            # new record would inherit the owner of the dog it was merged into.
            split_takes_source_owner = (
                dog_fix_allowed
                and not handler_class
                and owner_is_actionable(src["owner"])
            )
            entity_fixed = repoint_placement_entities(
                cursor,
                row,
                src,
                use_source_dog=dog_fix_allowed,
                use_source_owner=owner_fix_allowed or split_takes_source_owner,
            )
        if correct and allow_class_fix:
            class_fixed = repoint_placement_class(cursor, trial["trial_id"], row, src, vacated)

        if not anchored:
            entity_note = "unanchored match - class and placing did not both agree"
        elif handler_class:
            entity_note = "handler class names the handler, not the owner"
        elif owner_household:
            entity_note = "same household in the source; left as normalized"
        elif owner_skewed and not owner_is_actionable(src["owner"]):
            entity_note = "source names only a surname"
        elif owner_skewed and not fix_owner_assignments:
            entity_note = "owner reassignment not enabled"
        else:
            entity_note = ""
        class_note = (
            ""
            if allow_class_fix
            else "class moves not applied; the same dog can place in several classes"
        )

        if dog_skewed:
            if dog_orphaned:
                dog_note = "stored dog record no longer exists"
            elif dog_difference == DOG_SPELLING:
                dog_note = "spelling variant of the same dog; left as normalized"
            elif dog_difference == DOG_KENNELMATE:
                dog_note = "shares a kennel prefix; review for an over-eager merge"
            elif not fix_dog_merges:
                dog_note = "dog reassignment not enabled"
            else:
                dog_note = entity_note
            add_issue(
                "orphaned_dog" if dog_orphaned else {
                    DOG_SPELLING: "dog_spelling",
                    DOG_KENNELMATE: "dog_kennelmate",
                }.get(dog_difference, "dog"),
                row["placement_id"],
                src["dog"],
                row["dog_name"],
                "corrected" if (entity_fixed and dog_fix_allowed) else "reported",
                dog_note or f"source line: {src['raw_dog']}",
            )
        if owner_skewed:
            if handler_class:
                owner_kind = "owner_handler_class"
            elif owner_household:
                owner_kind = "owner_household"
            else:
                owner_kind = "owner"
            add_issue(
                owner_kind,
                row["placement_id"],
                src["owner"],
                row["owner_name"],
                "corrected" if (entity_fixed and owner_fix_allowed) else "reported",
                entity_note or f"source line: {src['raw_owner']}",
            )
        if class_skewed:
            add_issue(
                "class",
                row["placement_id"],
                src["class_name"],
                row["class_name"],
                "corrected" if class_fixed else "reported",
                class_note or f"source line: {src['raw_class']}",
            )
        if division_skewed:
            add_issue(
                "division",
                row["placement_id"],
                src["division"],
                row["division_name"],
                "corrected" if class_fixed else "reported",
                class_note,
            )

        if entity_fixed or class_fixed:
            comparison.corrected += 1

    for src_idx in unmatched_src:
        src = source_rows[src_idx]
        add_issue(
            "missing_in_db",
            None,
            f"{src['result']} | {src['class_name']} | {src['dog']} | {src['owner']}",
            "",
            "reported",
        )

    for db_idx in unmatched_db:
        row = db_rows[db_idx]
        add_issue(
            "extra_in_db",
            row["placement_id"],
            "",
            f"{row['result']} | {row['class_name']} | {row['dog_name']} | {row['owner_name']}",
            "reported",
        )

    if correct and (comparison.corrected or vacated):
        drop_vacated_trial_classes(cursor, vacated)
        conn.commit()

    return comparison


def load_source_rows(trial: dict) -> tuple[list[dict] | None, list[tuple[str, str]], str | None]:
    """Parse a trial's downloaded results file into expected rows."""
    file_path = trial["file_path"]
    if not file_path:
        return None, [], "no source file recorded"
    if not os.path.exists(file_path):
        return None, [], f"source file missing: {file_path}"

    year = source_year_for_file(file_path, trial["year"])
    # The parser narrates each header it recognizes; that belongs in a load log,
    # not in a comparison report.
    with contextlib.redirect_stdout(io.StringIO()):
        _info, placements, error = parse_trial_source_file(file_path, year, quiet=True)
    if error:
        return None, [], error
    if not placements:
        return None, [], "no placements parsed from source file"

    rows, unstable = expected_rows_from_source(placements)
    return rows, unstable, None


def fetch_trials(
    cursor,
    trial_ids: list[int] | None = None,
    year: int | None = None,
    folder: str | None = None,
) -> list[dict]:
    query = """
        SELECT TrialListID, TrialName, Year, TrialResultFilePath
        FROM [sResults].[TrialList]
        WHERE TrialResultFilePath IS NOT NULL
          AND LTRIM(RTRIM(TrialResultFilePath)) <> ''
    """
    params: list = []
    if trial_ids:
        query += f" AND TrialListID IN ({','.join('?' * len(trial_ids))})"
        params.extend(trial_ids)
    if year:
        query += " AND Year = ?"
        params.append(year)
    if folder:
        query += " AND TrialResultFilePath LIKE ?"
        params.append(f"%{folder}%")
    query += " ORDER BY TrialListID"

    cursor.execute(query, *params) if params else cursor.execute(query)
    return [
        {
            "trial_id": row[0],
            "trial_name": row[1] or "",
            "year": row[2],
            "file_path": row[3] or "",
        }
        for row in cursor.fetchall()
    ]


class SkewReport:
    """Appends every reported or corrected difference to a CSV."""

    FIELDS = (
        "timestamp", "trial_id", "trial_name", "pass", "kind",
        "placement_id", "source_value", "db_value", "action", "detail",
    )

    def __init__(self, path: str):
        self.path = path
        self.rows_written = 0
        write_header = not os.path.exists(path) or os.path.getsize(path) == 0
        self._handle = open(path, "a", encoding="utf-8-sig", newline="")
        self._writer = csv.writer(self._handle)
        if write_header:
            self._writer.writerow(self.FIELDS)

    def write(self, issues: list[SkewIssue]) -> None:
        stamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        for issue in issues:
            self._writer.writerow(
                [
                    stamp,
                    issue.trial_id,
                    issue.trial_name,
                    issue.pass_no,
                    issue.kind,
                    issue.placement_id if issue.placement_id is not None else "",
                    issue.source_value,
                    issue.db_value,
                    issue.action,
                    issue.detail,
                ]
            )
            self.rows_written += 1
        self._handle.flush()

    def close(self) -> None:
        self._handle.close()


def summarize(issues: list[SkewIssue]) -> str:
    if not issues:
        return "clean"
    counts: dict[str, int] = defaultdict(int)
    for issue in issues:
        counts[issue.kind] += 1
    corrected = sum(1 for issue in issues if issue.action == "corrected")
    parts = [f"{kind} {count}" for kind, count in sorted(counts.items())]
    return f"{', '.join(parts)} ({corrected} corrected)"


def run_normalize_verify_cycle(
    conn,
    trials: list[dict],
    *,
    passes: int = 2,
    correct: bool = True,
    skip_dog_owner_merge: bool = False,
    report: SkewReport | None = None,
    batch_size: int = 100,
    verbose: bool = True,
    sources: dict[int, list] | None = None,
    fix_class_assignments: bool = False,
    fix_owner_assignments: bool = False,
    fix_dog_merges: bool = False,
) -> dict:
    """Run normalize/compare passes over trials, correcting skew as it is found.

    Each batch is normalized as a unit and then compared trial by trial against
    the downloaded source files, twice, so that changes made by the first
    comparison are themselves re-normalized and re-checked.
    """
    totals = {
        "trials": 0,
        "skipped": 0,
        "issues": 0,
        "corrected": 0,
        "unstable": 0,
        "persistent": 0,
    }
    if not trials:
        return totals

    def prepare_batch(batch: list[dict]) -> tuple[list[dict], dict[int, list[dict]]]:
        """Parse the source files for one batch of trials."""
        cache: dict[int, list[dict]] = {}
        ready: list[dict] = []
        for trial in batch:
            if sources and trial["trial_id"] in sources:
                rows, unstable = expected_rows_from_source(sources[trial["trial_id"]])
                error = None
            else:
                rows, unstable, error = load_source_rows(trial)

            if error or not rows:
                totals["skipped"] += 1
                if verbose:
                    print_ts(
                        f"  Trial {trial['trial_id']}: skipped ({error or 'no source rows'})"
                    )
                if report and error:
                    report.write(
                        [
                            SkewIssue(
                                trial_id=trial["trial_id"],
                                trial_name=trial["trial_name"],
                                pass_no=0,
                                kind="source_unavailable",
                                placement_id=None,
                                source_value=trial["file_path"],
                                db_value="",
                                action="reported",
                                detail=error or "",
                            )
                        ]
                    )
                continue

            if unstable:
                totals["unstable"] += len(unstable)
                if report:
                    report.write(
                        [
                            SkewIssue(
                                trial_id=trial["trial_id"],
                                trial_name=trial["trial_name"],
                                pass_no=0,
                                kind="unstable_normalization",
                                placement_id=None,
                                source_value=value,
                                db_value="",
                                action="reported",
                                detail=f"{field} name never settles",
                            )
                            for field, value in unstable
                        ]
                    )

            cache[trial["trial_id"]] = rows
            ready.append(trial)
        return ready, cache

    for start in range(0, len(trials), batch_size):
        batch, source_cache = prepare_batch(trials[start : start + batch_size])
        if not batch:
            continue
        totals["trials"] += len(batch)
        batch_ids = [trial["trial_id"] for trial in batch]
        last_pass_issues: dict[int, int] = {}

        for pass_no in range(1, passes + 1):
            run_batch_post_trial_normalization(
                conn, batch_ids, skip_dog_owner_merge=skip_dog_owner_merge,
            )

            for trial in batch:
                comparison = compare_trial(
                    conn,
                    trial,
                    source_cache[trial["trial_id"]],
                    pass_no,
                    correct=correct,
                    fix_class_assignments=fix_class_assignments,
                    fix_owner_assignments=fix_owner_assignments,
                    fix_dog_merges=fix_dog_merges,
                )
                totals["issues"] += len(comparison.issues)
                totals["corrected"] += comparison.corrected
                if report:
                    report.write(comparison.issues)

                if pass_no == passes and last_pass_issues.get(trial["trial_id"]):
                    still_open = sum(
                        1 for issue in comparison.issues
                        if issue.kind in ("dog", "owner", "class", "division")
                    )
                    totals["persistent"] += still_open
                last_pass_issues[trial["trial_id"]] = len(comparison.issues)

                if verbose and comparison.issues:
                    print_ts(
                        f"  Trial {trial['trial_id']} pass {pass_no}: "
                        f"{summarize(comparison.issues)}"
                    )

        if verbose:
            print_ts(
                f"Verified {min(start + batch_size, len(trials)):,}/{len(trials):,} trials "
                f"({totals['issues']:,} differences, {totals['corrected']:,} corrections)"
            )

    return totals


def verify_loaded_trials(
    conn,
    trial_ids: list[int],
    *,
    sources: dict[int, list] | None = None,
    skip_dog_owner_merge: bool = False,
    report_path: str = DEFAULT_REPORT_PATH,
    passes: int = 2,
    batch_size: int = 100,
    fix_class_assignments: bool = False,
    fix_owner_assignments: bool = False,
    fix_dog_merges: bool = False,
) -> dict:
    """Entry point used by the loader after trials are inserted."""
    if not trial_ids:
        return {}

    cursor = conn.cursor()
    trials = fetch_trials(cursor, trial_ids=trial_ids)
    if not trials:
        return {}

    report = SkewReport(report_path)
    try:
        totals = run_normalize_verify_cycle(
            conn,
            trials,
            passes=passes,
            correct=True,
            skip_dog_owner_merge=skip_dog_owner_merge,
            report=report,
            batch_size=batch_size,
            sources=sources,
            fix_class_assignments=fix_class_assignments,
            fix_owner_assignments=fix_owner_assignments,
            fix_dog_merges=fix_dog_merges,
        )
    finally:
        report.close()

    print_ts(
        f"Normalize/compare complete: {totals.get('trials', 0):,} trials, "
        f"{totals.get('issues', 0):,} differences, "
        f"{totals.get('corrected', 0):,} corrected, "
        f"{totals.get('persistent', 0):,} still open"
    )
    return totals


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Compare normalized trial data with the downloaded source files",
    )
    parser.add_argument("--trial-id", type=int, action="append", help="Limit to trial ID (repeatable)")
    parser.add_argument("--year", type=int, help="Limit to a trial year")
    parser.add_argument("--folder", help="Limit to source paths containing this folder name")
    parser.add_argument("--limit", type=int, help="Process at most this many trials")
    parser.add_argument("--passes", type=int, default=2, help="Normalize/compare passes (default: 2)")
    parser.add_argument("--batch-size", type=int, default=100, help="Trials normalized per batch")
    parser.add_argument("--report-only", action="store_true", help="Never write corrections")
    parser.add_argument("--report", default=DEFAULT_REPORT_PATH, help="CSV report path")
    parser.add_argument(
        "--fix-class-assignments",
        action="store_true",
        help="Also move placements into the class named by the source file (report-only by default)",
    )
    parser.add_argument(
        "--fix-owner-assignments",
        action="store_true",
        help="Also reassign ownership to the owner named by the source file (report-only by default)",
    )
    parser.add_argument(
        "--fix-dog-merges",
        action="store_true",
        help="Split placements back onto the dog the source names when the merge "
             "rule says the stored dog is a different one",
    )
    parser.add_argument(
        "--skip-dog-owner-merge",
        action="store_true",
        help="Skip dog/owner merges while normalizing",
    )
    args = parser.parse_args()

    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")

    print("=" * 80)
    print("TRIAL NORMALIZATION VERIFIER")
    print("=" * 80)

    conn = get_connection()
    cursor = conn.cursor()
    trials = fetch_trials(cursor, trial_ids=args.trial_id, year=args.year, folder=args.folder)
    if args.limit:
        trials = trials[: args.limit]

    print_ts(f"Comparing {len(trials):,} trial(s) against downloaded source files")
    if args.report_only:
        print_ts("REPORT ONLY - no corrections will be written")

    report = SkewReport(args.report)
    try:
        totals = run_normalize_verify_cycle(
            conn,
            trials,
            passes=args.passes,
            correct=not args.report_only,
            skip_dog_owner_merge=args.skip_dog_owner_merge,
            report=report,
            batch_size=args.batch_size,
            fix_class_assignments=args.fix_class_assignments,
            fix_owner_assignments=args.fix_owner_assignments,
            fix_dog_merges=args.fix_dog_merges,
        )
    finally:
        report.close()
        conn.close()

    print("=" * 80)
    print_ts(
        f"Trials compared: {totals['trials']:,} | skipped: {totals['skipped']:,}"
    )
    print_ts(
        f"Differences: {totals['issues']:,} | corrected: {totals['corrected']:,} | "
        f"still open after final pass: {totals['persistent']:,}"
    )
    print_ts(f"Unstable normalizations: {totals['unstable']:,}")
    print_ts(f"Report written to {os.path.abspath(args.report)}")
    print("=" * 80)


if __name__ == "__main__":
    main()
