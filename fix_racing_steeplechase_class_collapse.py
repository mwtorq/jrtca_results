#!/usr/bin/env python3
"""
Comprehensive fix: Racing flat vs Steeplechase (etc.) collapsed into one ClassName.

For every dog with 2+ distinct places under the same TrialClass in a racing-ish
division, re-parse the trial source with division awareness. When the source
shows those places under different divisions (typically Racing + Steeplechase),
remount each placement onto a correctly named TrialClass.

Usage:
  py -3 fix_racing_steeplechase_class_collapse.py           # dry-run
  py -3 fix_racing_steeplechase_class_collapse.py --apply   # write DB
"""
from __future__ import annotations

import argparse
import re
import sys
from collections import defaultdict
from pathlib import Path

from populate_trialresults_fixed import get_or_create_class, get_or_create_division
from recover_unverified_placements import class_match_key, norm_result, resolve_source
from split_mixed_dogs_by_source_owner import connect

sys.stdout.reconfigure(encoding="utf-8", errors="replace")

DIV_HEADERS = [
    (re.compile(r"\bconformation\s+division\b", re.I), "Conformation"),
    (re.compile(r"\bgo[\s\-]?to[\s\-]?ground\s+division\b", re.I), "Go-to-Ground"),
    (re.compile(r"\bracing\s+division\b", re.I), "Racing"),
    (re.compile(r"\bflat\s+rac", re.I), "Racing"),
    (re.compile(r"\bsteeplechase\b", re.I), "Steeplechase"),
    (re.compile(r"\bhurdle\b", re.I), "Steeplechase"),
    (re.compile(r"\byouth\b.*\bdivision\b", re.I), "Youth"),
]

PLACE_RE = re.compile(
    r"^(?P<place>\d{1,2}(?:st|nd|rd|th)|Best|Reserve|Champion)\s*:\s*(?P<rest>.+)$",
    re.I,
)


def next_id(cur, table: str, col: str) -> int:
    cur.execute(f"SELECT ISNULL(MAX({col}), 0) + 1 FROM {table}")
    return int(cur.fetchone()[0])


def normalize_source_text(raw: str) -> str:
    text = re.sub(r"(?i)<br\s*/?>", "\n", raw)
    text = re.sub(r"(?i)</p>", "\n", text)
    text = re.sub(r"(?i)</h\d>", "\n", text)
    text = re.sub(r"<[^>]+>", " ", text)
    text = (
        text.replace("&nbsp;", " ")
        .replace("&amp;", "&")
        .replace("&quot;", '"')
        .replace("½", "½")
    )
    text = re.sub(r"[ \t]+", " ", text)
    return text


def parse_all_slots(src_path: Path) -> list[tuple[str, str, str, str]]:
    """Return (division, class, place, dog_line) for every placement line."""
    raw = src_path.read_text(encoding="utf-8", errors="replace")
    text = normalize_source_text(raw)

    division = "Unknown"
    current_class = ""
    out: list[tuple[str, str, str, str]] = []

    for line in text.splitlines():
        s = line.strip()
        if not s:
            continue
        low = s.lower()

        for rx, div in DIV_HEADERS:
            if rx.search(s):
                division = div
                break

        if re.search(r"\bentries\s*:", low) or (
            not PLACE_RE.match(s)
            and any(
                k in low
                for k in (
                    "pups",
                    "dogs",
                    "bitches",
                    "veteran",
                    "puppy",
                    "adult",
                    "senior",
                    "steeplechase",
                )
            )
            and "owned by" not in low
            and "ownedby" not in low
        ):
            cls = re.sub(
                r"\b(entries|entrie:s|ertries|enrties|enrtie:s)\s*:.*$",
                "",
                s,
                flags=re.I,
            ).strip(" -–—")
            cls = re.sub(r"\s+", " ", cls).strip()
            if len(cls) > 3:
                current_class = cls
                if re.search(r"\bsteeplechase\b|\bhurdle\b", low):
                    division = "Steeplechase"
            continue

        m = PLACE_RE.match(s)
        if not m or not current_class:
            continue
        place = norm_result(m.group("place"))
        rest = m.group("rest").strip()
        out.append((division, current_class, place, rest))
    return out


def dog_name_variants(dog_name: str) -> list[str]:
    n = re.sub(r"\s+", " ", (dog_name or "").strip().lower())
    # drop trailing [unverified] / parentheticals
    n = re.sub(r"\[.*?\]", "", n).strip()
    variants = [n]
    # last token call-name (if multi-word)
    parts = n.split()
    if len(parts) >= 2:
        variants.append(parts[-1])
    return [v for v in variants if len(v) >= 3]


def line_matches_dog(dog_name: str, dog_line: str) -> bool:
    line = dog_line.lower()
    # prefer match before owned-by
    head = re.split(r"owned\s*by", line, maxsplit=1, flags=re.I)[0]
    head = re.sub(r"[^a-z0-9' .\-]", " ", head)
    head = re.sub(r"\s+", " ", head).strip()
    for v in dog_name_variants(dog_name):
        if v in head:
            # require whole-token for short call-names
            if len(v) <= 5:
                if re.search(rf"(?<![a-z0-9]){re.escape(v)}(?![a-z0-9])", head):
                    return True
            else:
                return True
    return False


def clean_class_label(class_name: str) -> str:
    cname = class_name.strip()
    cname = re.sub(
        r"\b(entries|entrie:s|ertries|enrties|enrtie:s)\s*:.*$",
        "",
        cname,
        flags=re.I,
    )
    cname = re.sub(r"\s+", " ", cname).strip(" -–—")
    return cname


def qualify_class_name(division: str, class_name: str) -> tuple[str, str]:
    """Return (normalized_division, class_name with Racing/Steeplechase prefix)."""
    div = division
    if div.lower().startswith("racing") or "flat" in div.lower():
        div = "Racing"
    elif "steeple" in div.lower() or "hurdle" in div.lower():
        div = "Steeplechase"

    cname = clean_class_label(class_name)
    # strip existing prefixes then re-apply cleanly
    cname = re.sub(r"^(racing|steeplechase)\s+", "", cname, flags=re.I).strip()
    if div == "Steeplechase":
        cname = f"Steeplechase {cname}"
    elif div == "Racing":
        cname = f"Racing {cname}"
    return div, cname


def ensure_trial_class(cur, trial_list_id: int, division: str, class_name: str) -> int:
    div, cname = qualify_class_name(division, class_name)
    div_id = get_or_create_division(cur, div)
    class_id = get_or_create_class(cur, cname, div_id)
    cur.execute(
        """
        SELECT tc.TrialClassID
        FROM sResults.TrialClass tc
        WHERE tc.TrialListID = ? AND tc.ClassID = ?
        """,
        trial_list_id,
        class_id,
    )
    row = cur.fetchone()
    if row:
        return int(row[0])
    tcid = next_id(cur, "[sResults].[TrialClass]", "TrialClassID")
    cur.execute(
        """
        INSERT INTO sResults.TrialClass (TrialClassID, TrialListID, ClassID, EntryCount)
        VALUES (?, ?, ?, 0)
        """,
        tcid,
        trial_list_id,
        class_id,
    )
    return tcid


def class_keys_compatible(db_class: str, src_class: str) -> bool:
    a = class_match_key(re.sub(r"^(racing|steeplechase)\s+", "", db_class or "", flags=re.I))
    b = class_match_key(re.sub(r"^(racing|steeplechase)\s+", "", src_class or "", flags=re.I))
    if not a or not b:
        return False
    return a == b or a in b or b in a


def fetch_collapsed_groups(cur) -> list[tuple]:
    cur.execute(
        """
        SELECT p.DogID, d.DogName, p.TrialListID, tl.Year, tl.TrialName,
               tl.TrialResultFilePath, p.TrialClassID, cl.ClassName, div.DivisionName,
               COUNT(*) AS n, COUNT(DISTINCT p.Result) AS n_places
        FROM sResults.TrialPlacements p
        JOIN sResults.Dog d ON d.DogID = p.DogID
        JOIN sResults.TrialList tl ON tl.TrialListID = p.TrialListID
        JOIN sResults.TrialClass tc ON tc.TrialClassID = p.TrialClassID
        JOIN sResults.Class cl ON cl.ClassID = tc.ClassID
        JOIN sResults.Division div ON div.DivisionID = cl.DivisionID
        WHERE (
            div.DivisionName LIKE '%Racing%'
            OR div.DivisionName LIKE '%FLAT%'
            OR div.DivisionName LIKE '%Steeple%'
            OR div.DivisionName LIKE '%Hurdle%'
        )
        -- skip already-split prefixed classes that still collide for other reasons
        AND cl.ClassName NOT LIKE 'Racing %'
        AND cl.ClassName NOT LIKE 'Steeplechase %'
        GROUP BY p.DogID, d.DogName, p.TrialListID, tl.Year, tl.TrialName,
                 tl.TrialResultFilePath, p.TrialClassID, cl.ClassName, div.DivisionName
        HAVING COUNT(*) > 1 AND COUNT(DISTINCT p.Result) > 1
        ORDER BY tl.Year, tl.TrialName, d.DogName
        """
    )
    return cur.fetchall()


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--apply", action="store_true", help="Write changes to DB")
    ap.add_argument("--limit-trials", type=int, default=0, help="Process only N trials (0=all)")
    args = ap.parse_args()

    cn = connect()
    cur = cn.cursor()
    groups = fetch_collapsed_groups(cur)
    print(f"Collapsed candidate groups: {len(groups)}")

    by_trial: dict[int, list] = defaultdict(list)
    for g in groups:
        by_trial[g[2]].append(g)

    trial_ids = sorted(by_trial.keys())
    if args.limit_trials:
        trial_ids = trial_ids[: args.limit_trials]
    print(f"Trials to process: {len(trial_ids)}")

    fixed = 0
    skipped_no_src = 0
    skipped_no_div_split = 0
    skipped_no_match = 0
    slot_cache: dict[str, list[tuple[str, str, str, str]]] = {}

    for tid in trial_ids:
        glist = by_trial[tid]
        path = glist[0][5]
        year, tname = glist[0][3], glist[0][4]
        rp = resolve_source(path)
        if not rp or not rp.exists():
            skipped_no_src += len(glist)
            continue

        cache_key = str(rp.resolve())
        if cache_key not in slot_cache:
            try:
                slot_cache[cache_key] = parse_all_slots(rp)
            except Exception as e:
                print(f"  parse fail {year} {tname}: {e}")
                skipped_no_src += len(glist)
                continue
        slots = slot_cache[cache_key]

        for dog_id, dog_name, trial_list_id, year, tname, path, tcid, cls, div, n, n_places in glist:
            dog_slots = [
                (d, c, p, line)
                for d, c, p, line in slots
                if line_matches_dog(dog_name, line) and class_keys_compatible(cls, c)
            ]
            # unique by (div, class_key, place)
            seen = set()
            uniq = []
            for d, c, p, line in dog_slots:
                k = (d, class_match_key(c), p)
                if k in seen:
                    continue
                seen.add(k)
                uniq.append((d, c, p, line))
            dog_slots = uniq

            divisions = {d for d, _, _, _ in dog_slots}
            # Need at least Racing + Steeplechase (or two distinct racing-family divs)
            racing_family = {
                d
                for d in divisions
                if d in ("Racing", "Steeplechase")
                or "racing" in d.lower()
                or "steeple" in d.lower()
                or "flat" in d.lower()
                or "hurdle" in d.lower()
            }
            if len(racing_family) < 2:
                skipped_no_div_split += 1
                continue

            cur.execute(
                """
                SELECT TrialPlacementsID, Result, TrialClassID
                FROM sResults.TrialPlacements
                WHERE DogID = ? AND TrialClassID = ?
                ORDER BY Result, TrialPlacementsID
                """,
                dog_id,
                tcid,
            )
            placements = cur.fetchall()

            used = set()
            moves = []
            for pid, result, old_tcid in placements:
                res_n = norm_result(result)
                match = None
                for i, (sdiv, scname, place, line) in enumerate(dog_slots):
                    if i in used:
                        continue
                    if place != res_n:
                        continue
                    if sdiv not in racing_family and not any(
                        x in sdiv.lower() for x in ("racing", "steeple", "flat", "hurdle")
                    ):
                        continue
                    match = (i, sdiv, scname, place)
                    break
                if not match:
                    continue
                i, sdiv, scname, place = match
                used.add(i)
                moves.append((pid, result, old_tcid, sdiv, scname))

            # Only apply if we remapped to at least 2 different target divisions
            move_divs = {m[3] for m in moves}
            if len(moves) < 2 or len(move_divs) < 2:
                skipped_no_match += 1
                continue

            for pid, result, old_tcid, sdiv, scname in moves:
                new_tcid = ensure_trial_class(cur, trial_list_id, sdiv, scname)
                if new_tcid == old_tcid:
                    continue
                if args.apply:
                    cur.execute(
                        "UPDATE sResults.TrialPlacements SET TrialClassID=? WHERE TrialPlacementsID=?",
                        new_tcid,
                        pid,
                    )
                fixed += 1
                if fixed <= 40 or fixed % 500 == 0:
                    print(
                        f"  {'APPLY' if args.apply else 'DRY'} {year} {tname[:28]} | "
                        f"{dog_name[:24]} | {result} -> {sdiv} / {scname[:40]}"
                    )

    if args.apply:
        cn.commit()
        print("Committed.")
    else:
        cn.rollback()
        print("Dry-run only (no commit).")

    print(
        f"\nplacements remounted: {fixed}\n"
        f"skipped no source: {skipped_no_src}\n"
        f"skipped no racing/steeple split in source: {skipped_no_div_split}\n"
        f"skipped no place match: {skipped_no_match}"
    )

    if args.apply:
        cur.execute(
            """
            SELECT COUNT(*) FROM (
                SELECT p.DogID, p.TrialClassID
                FROM sResults.TrialPlacements p
                JOIN sResults.TrialClass tc ON tc.TrialClassID = p.TrialClassID
                JOIN sResults.Class cl ON cl.ClassID = tc.ClassID
                JOIN sResults.Division div ON div.DivisionID = cl.DivisionID
                WHERE (
                    div.DivisionName LIKE '%Racing%'
                    OR div.DivisionName LIKE '%FLAT%'
                    OR div.DivisionName LIKE '%Steeple%'
                    OR div.DivisionName LIKE '%Hurdle%'
                )
                AND cl.ClassName NOT LIKE 'Racing %'
                AND cl.ClassName NOT LIKE 'Steeplechase %'
                GROUP BY p.DogID, p.TrialClassID
                HAVING COUNT(*) > 1 AND COUNT(DISTINCT p.Result) > 1
            ) x
            """
        )
        print(f"remaining unprefixed racing multis: {cur.fetchone()[0]}")

    cn.close()


if __name__ == "__main__":
    main()
