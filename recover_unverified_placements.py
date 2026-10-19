#!/usr/bin/env python3
"""
Recover TrialPlacements that were moved onto UNVERIFIED-* dogs.

TrialVault debug HTML: re-parse scores, match by class + result, assign
one-to-one against slots not already filled by non-UNVERIFIED rows.

Older owned-by sources: match by Result place against source entries not
already claimed by verified dogs on that trial.

Usage:
  py -3 recover_unverified_placements.py --dry-run
  py -3 recover_unverified_placements.py
  py -3 recover_unverified_placements.py --years 2023,2024,2025,2026
"""
from __future__ import annotations

import argparse
import re
import sys
from collections import defaultdict
from pathlib import Path

from bs4 import BeautifulSoup

from normalize_trialresults_data import normalize_owner_name
from populate_trialresults_fixed import get_or_create_dog, get_or_create_owner
from scrape_trial_results_fixed import (
    parse_local_trial_file,
    parse_trialvault_scores_html,
)
from split_mixed_dogs_by_source_owner import (
    clean_source_dog_name,
    connect,
    dog_match_key,
    read_text,
    resolve_path,
)

sys.stdout.reconfigure(encoding="utf-8", errors="replace")

ROOT = Path(r"c:\Users\mw\OneDrive - timberwilde.net\repos\jrtca_results")

PLACE_PAIR_RE = re.compile(
    r"(?P<place>\d{1,2}(?:st|nd|rd|th)|Best|Reserve|Champion)\s*:\s*"
    r"(?P<dog>[A-Za-z0-9#][^,\n\r\t]{0,80}?)\s*"
    r"(?:,\s*owned by\s+|\t+)(?P<owner>[^<\n\r]+)",
    re.I,
)


def norm_class(s: str | None) -> str:
    return re.sub(r"\s+", " ", (s or "").strip().lower())


def norm_result(s: str | None) -> str:
    t = (s or "").strip().lower().replace(" ", "")
    return t.replace("—", "-").replace("–", "-")


def class_match_key(s: str | None) -> str:
    """Aggressive class key so DB vs OCR header variants align."""
    t = norm_class(s)
    if not t:
        return ""
    t = t.replace("½", "5").replace("1/2", "5")
    # "12 5" / "12 ½" after half-replacement → 125
    t = re.sub(r"\b12\s+5\b", "125", t)
    t = re.sub(r"\bjrtca\b", " ", t)
    # OCR / plural / synonym cleanup before collapsing
    t = re.sub(r"\bdoa\s+pups?\b", "dog pup", t)
    t = re.sub(r"\bdog\s+pups?\b", "dogpup", t)
    t = re.sub(r"\bbitch\s+pups?\b", "bitchpup", t)
    t = re.sub(r"\bpuppies\b", "puppy", t)
    t = re.sub(r"\bpups\b", "pup", t)
    t = re.sub(r"\badults\b", "adult", t)
    t = re.sub(r"\bbitches\b", "bitch", t)
    t = re.sub(r"\bdogs\b", "dog", t)
    t = re.sub(r"\bmonths?\b", "mo", t)
    t = re.sub(r"\bmos?\b", "mo", t)
    t = re.sub(r"\bsmooth\s*coated\b", "smooth", t)
    t = re.sub(r"\brough\s*/\s*broken\b", "rbr", t)
    t = re.sub(r"\br\s*/\s*br\b", "rbr", t)
    t = re.sub(r"\b1\s*y(?:ea)?rs?\.?\s*(?:&|and)\s*(?:over|older)\b", "1yo", t)
    t = re.sub(r"\b1\s*y(?:ea)?rs?\.?\s*(?:over|older)\b", "1yo", t)
    t = re.sub(r"\b1\s*year(?:s)?\s+and\s+older\b", "1yo", t)
    t = re.sub(r"\bgo[\s\-]?to[\s\-]?ground\b", "gtg", t)
    t = re.sub(r"\bchampionship\b", "champ", t)
    t = re.sub(r"\bchampion\b", "champ", t)
    t = re.sub(r"\bcertificate\b", "cert", t)
    t = re.sub(r"\bworking\s+terrier\b", "working", t)
    t = re.sub(r"\bbest\s+working\s+(?:terrier\s+)?(dog|bitch)\b", r"bestworking\1", t)
    t = re.sub(r"\bpre[\s\-]?novice\b", "prenovice", t)
    t = re.sub(r"\band\b", " ", t)
    # Age: "9 to 12 mo" / "6 up to 9 mo"
    t = re.sub(r"\b(\d{1,2})\s*(?:up\s+to|to|-)\s*(\d{1,2})\s*mo\b", r"\1upto\2mo", t)
    # Height ranges → compact tokens
    t = re.sub(
        r"(?:over\s+)?10\s*[\"']?\s*(?:up\s+to|to|-)\s*125\s*[\"']?",
        "h10125",
        t,
    )
    t = re.sub(
        r"(?:over\s+)?125\s*[\"']?\s*(?:up\s+to|to|-)\s*15\s*[\"']?",
        "h12515",
        t,
    )
    t = re.sub(r"\bup\s+to\s+125\s*[\"']?", "h10125", t)
    t = re.sub(r"\bover\s+125\s*[\"']?", "h12515", t)
    t = re.sub(r"[&+/]+", " ", t)
    t = re.sub(r"[^a-z0-9]+", "", t)
    return t


def class_structure_key(s: str | None) -> str:
    """Class key with coat/1yo tokens removed for coat-split / adult matching."""
    k = class_match_key(s)
    k = k.replace("smooth", "").replace("rbr", "").replace("1yo", "")
    return k


def classes_compatible(db_class: str, src_class: str) -> bool:
    a, b = norm_class(db_class), norm_class(src_class)
    if not a or not b:
        return False
    if a == b:
        return True
    ka, kb = class_match_key(db_class), class_match_key(src_class)
    if ka and kb and ka == kb:
        return True
    # Same tokens, different order (height prefix vs suffix)
    if ka and kb and len(ka) >= 12 and sorted(ka) == sorted(kb):
        return True
    aa = re.sub(r"[^a-z0-9]+", "", a)
    bb = re.sub(r"[^a-z0-9]+", "", b)
    if aa == bb:
        return True
    if ka and kb and (ka in kb or kb in ka) and min(len(ka), len(kb)) >= 10:
        return True
    if aa in bb or bb in aa:
        return min(len(aa), len(bb)) >= 12
    if not ka or not kb:
        return False
    marker_re = (
        r"(?:dogpup|bitchpup|h10125|h12515|1yo|"
        r"\d+upto\d+mo|rbr|smooth|juniorhandler|childhandler|"
        r"noviceadult|openadult|gtgchamp|workingbitch|workingdog|champcert)"
    )
    markers_a = set(re.findall(marker_re, ka))
    markers_b = set(re.findall(marker_re, kb))
    if markers_a and markers_b and markers_a == markers_b and len(markers_a) >= 2:
        return True
    return False


def best_class_pool_key(
    cls: str,
    res_n: str,
    pool: dict[tuple[str, str], list],
) -> tuple[str, str] | None:
    """Pick the best source pool key for a DB class at a given place."""
    cls_n = norm_class(cls)
    exact = (cls_n, res_n)
    if pool.get(exact):
        return exact
    key = class_match_key(cls)
    cands: list[tuple[int, tuple[str, str]]] = []
    for (pc, pr), rows in pool.items():
        if pr != res_n or not rows:
            continue
        if classes_compatible(cls, pc):
            pk = class_match_key(pc)
            score = 100 if pk == key else 50
            if key and pk:
                common = 0
                for ca, cb in zip(key, pk):
                    if ca != cb:
                        break
                    common += 1
                score += common
            cands.append((score, (pc, pr)))
    if cands:
        cands.sort(key=lambda x: -x[0])
        if len(cands) > 1 and cands[0][0] == cands[1][0]:
            if class_match_key(cands[0][1][0]) != class_match_key(cands[1][1][0]):
                # Fall through to structure-key unique match
                pass
            else:
                return cands[0][1]
        else:
            return cands[0][1]

    # Structure fallback: match coat-agnostic DB classes to coated source
    # headers, or coat-specific DB classes to the same coat only.
    db_key = class_match_key(cls)
    db_has_coat = ("smooth" in db_key) or ("rbr" in db_key)
    struct = class_structure_key(cls)
    if not struct or len(struct) < 8:
        return None
    def struct_ok(ps: str) -> bool:
        if not ps:
            return False
        if ps == struct:
            return True
        if len(struct) >= 12 and sorted(ps) == sorted(struct):
            return True
        if min(len(ps), len(struct)) >= 10 and (ps in struct or struct in ps):
            return True
        return False

    for (pc, pr), rows in pool.items():
        if pr != res_n or not rows:
            continue
        if not struct_ok(class_structure_key(pc)):
            continue
        sk = class_match_key(pc)
        if db_has_coat:
            if "smooth" in db_key and "smooth" not in sk:
                continue
            if "rbr" in db_key and "rbr" not in sk:
                continue
        return (pc, pr)
    return None


def place_entries(text: str) -> list[tuple[str, str, str]]:
    out = []
    for m in PLACE_PAIR_RE.finditer(text):
        place = norm_result(m.group("place"))
        dog = clean_source_dog_name(m.group("dog"))
        dog = re.sub(r"^#\d+:\s*", "", dog)
        owner = re.split(
            r"(?=\d{1,2}(?:st|nd|rd|th)\s*:)|(?=\b(?:Best|Reserve|Champion)\s*:)",
            m.group("owner"),
            maxsplit=1,
            flags=re.I,
        )[0]
        owner = re.sub(r"\s+", " ", owner).strip(" .,;:")
        if dog and owner:
            out.append((place, dog, owner))
    return out


def resolve_source(path: str | None) -> Path | None:
    if not path:
        return None
    rp = resolve_path(path)
    if rp:
        return rp
    cand = ROOT / str(path).replace("/", "\\")
    return cand if cand.is_file() else None


def load_trialvault_rows(
    html_path: Path, trial_name: str, year: int
) -> list[tuple[str, str, str, str]]:
    raw = read_text(html_path)
    soup = BeautifulSoup(raw, "html.parser")
    results, _judges = parse_trialvault_scores_html(soup, trial_name, "", str(year))
    out = []
    for r in results:
        if not r.dog_name or not r.placement:
            continue
        dog = re.sub(r"^#\d+:\s*", "", (r.dog_name or "").strip())
        out.append(
            (r.class_name or "", norm_result(r.placement), dog, (r.owner or "").strip())
        )
    return out


def load_ocr_class_rows(
    path: Path, year: int
) -> list[tuple[str, str, str, str]]:
    """Parse owned-by OCR/HTML sources into (class, place, dog, owner)."""
    import io
    import contextlib

    buf = io.StringIO()
    with contextlib.redirect_stdout(buf):
        results, _judges = parse_local_trial_file(str(path), str(year))
    out = []
    for r in results:
        dog = clean_source_dog_name(
            re.sub(r"^#\d+:\s*", "", (getattr(r, "dog_name", None) or "").strip())
        )
        place = norm_result(getattr(r, "placement", None))
        cls = (getattr(r, "class_name", None) or "").strip()
        owner = (getattr(r, "owner", None) or "").strip()
        if dog and place:
            out.append((cls, place, dog, owner))
    return out


def is_unverified_name(name: str | None) -> bool:
    n = (name or "").strip()
    return n.startswith("UNVERIFIED-") or "[unverified]" in n.lower()


def remount(cur, pid: int, dog: str, owner: str) -> None:
    oid = get_or_create_owner(cur, normalize_owner_name(owner) or owner or "Unknown")
    nid = get_or_create_dog(cur, dog, oid)
    cur.execute(
        "UPDATE sResults.TrialPlacements SET DogID=? WHERE TrialPlacementsID=?",
        nid,
        pid,
    )


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--dry-run", action="store_true")
    ap.add_argument("--years", default="", help="Comma years, empty=all")
    args = ap.parse_args()
    year_filter = (
        {int(y) for y in args.years.split(",") if y.strip()} if args.years else None
    )

    cn = connect()
    cur = cn.cursor()
    cur.execute(
        """
        SELECT p.TrialPlacementsID, p.Result, p.TrialListID,
               c.ClassName, tl.Year, tl.TrialName, tl.TrialResultFilePath
        FROM sResults.TrialPlacements p
        JOIN sResults.Dog d ON d.DogID = p.DogID
        JOIN sResults.TrialList tl ON tl.TrialListID = p.TrialListID
        JOIN sResults.TrialClass tc ON tc.TrialClassID = p.TrialClassID
        JOIN sResults.Class c ON c.ClassID = tc.ClassID
        WHERE d.DogName LIKE ?
           OR LOWER(d.DogName) LIKE N'%[[]unverified]%'
        ORDER BY tl.Year, tl.TrialListID, c.ClassName, p.Result, p.TrialPlacementsID
        """,
        "UNVERIFIED-%",
    )
    rows = cur.fetchall()
    if year_filter:
        rows = [r for r in rows if int(r[4]) in year_filter]
    print(f"UNVERIFIED placements to recover: {len(rows):,}", flush=True)

    by_trial: dict[int, list] = defaultdict(list)
    for r in rows:
        by_trial[r[2]].append(r)

    tv_cache: dict[str, list[tuple[str, str, str, str]]] = {}
    ocr_cache: dict[str, list[tuple[str, str, str, str]]] = {}
    recovered = 0
    skipped = 0
    samples: list[str] = []

    def remount_from_class_pool(
        placements: list,
        source_rows: list[tuple[str, str, str, str]],
        verified_counts: dict[tuple[str, str, str], int],
        label: str,
        year: int,
    ) -> tuple[int, int]:
        """Match UNVERIFIED rows by class+result; return (recovered, skipped)."""
        needed: list[tuple[str, str, str, str]] = []
        used_verified: dict[tuple[str, str, str], int] = defaultdict(int)
        for cls, res, dog, owner in source_rows:
            vk = (norm_class(cls), res, dog.strip().lower())
            if used_verified[vk] < verified_counts.get(vk, 0):
                used_verified[vk] += 1
                continue
            needed.append((cls, res, dog, owner))

        pool: dict[tuple[str, str], list[tuple[str, str, str, str]]] = defaultdict(list)
        for row in needed:
            pool[(norm_class(row[0]), row[1])].append(row)

        rec = 0
        skip = 0
        for pid, result, _tid, cls, _y, _tn, _path in placements:
            res_n = norm_result(result)
            pk = best_class_pool_key(cls, res_n, pool)
            if not pk:
                skip += 1
                continue
            cands = pool.get(pk, [])
            if not cands:
                skip += 1
                continue
            _sc, _sr, src_dog, src_owner = cands.pop(0)
            # Clean OCR glue where owner leaked into dog field
            if ", own" in src_dog.lower() and not src_owner:
                parts = re.split(r",\s*own\w*\s*(?:by\s*)?", src_dog, maxsplit=1, flags=re.I)
                if len(parts) == 2:
                    src_dog, src_owner = parts[0].strip(" ,"), parts[1].strip(" ,")
            src_dog = clean_source_dog_name(src_dog)
            if len(samples) < 25:
                samples.append(
                    f"{label} {year} {result!r} {cls!r} -> {src_dog!r} / {src_owner!r}"
                )
            rec += 1
            if not args.dry_run:
                remount(cur, pid, src_dog, src_owner)
        return rec, skip

    for trial_id, placements in by_trial.items():
        year = int(placements[0][4])
        tname = placements[0][5]
        path = placements[0][6]
        rp = resolve_source(path)
        if not rp:
            skipped += len(placements)
            continue

        cur.execute(
            """
            SELECT c.ClassName, p.Result, d.DogName
            FROM sResults.TrialPlacements p
            JOIN sResults.Dog d ON d.DogID = p.DogID
            JOIN sResults.TrialClass tc ON tc.TrialClassID = p.TrialClassID
            JOIN sResults.Class c ON c.ClassID = tc.ClassID
            WHERE p.TrialListID = ?
            """,
            trial_id,
        )
        verified_counts: dict[tuple[str, str, str], int] = defaultdict(int)
        for cls, res, dog in cur.fetchall():
            if is_unverified_name(dog):
                continue
            verified_counts[
                (norm_class(cls), norm_result(res), (dog or "").strip().lower())
            ] += 1

        is_tv = "debug_trialvault" in str(rp).lower()
        key = str(rp.resolve())

        if is_tv:
            if key not in tv_cache:
                try:
                    tv_cache[key] = load_trialvault_rows(rp, tname, year)
                except Exception as e:
                    print(f"  parse fail {rp.name}: {e}", flush=True)
                    skipped += len(placements)
                    continue
            r, s = remount_from_class_pool(
                placements, tv_cache[key], verified_counts, "TV", year
            )
            recovered += r
            skipped += s
        else:
            if key not in ocr_cache:
                try:
                    ocr_cache[key] = load_ocr_class_rows(rp, year)
                except Exception as e:
                    print(f"  OCR parse fail {rp.name}: {e}", flush=True)
                    skipped += len(placements)
                    continue
            if not ocr_cache[key]:
                skipped += len(placements)
                continue
            r, s = remount_from_class_pool(
                placements, ocr_cache[key], verified_counts, "OCR", year
            )
            recovered += r
            skipped += s

        print(
            f"  trial {year} {tname!r}: running total recovered={recovered} skipped={skipped}",
            flush=True,
        )

    deleted_dogs = 0
    if args.dry_run:
        cn.rollback()
        print("\nDry run — rolled back.", flush=True)
    else:
        cur.execute(
            """
            DELETE FROM sResults.Dog
            WHERE (
                    DogName LIKE ?
                 OR LOWER(DogName) LIKE N'%[[]unverified]%'
                  )
              AND NOT EXISTS (
                  SELECT 1 FROM sResults.TrialPlacements p WHERE p.DogID = sResults.Dog.DogID
              )
            """,
            "UNVERIFIED-%",
        )
        deleted_dogs = cur.rowcount
        cn.commit()
        print("\nCommitted.", flush=True)

    print(
        f"recovered={recovered} skipped={skipped} deleted_empty_dogs={deleted_dogs}",
        flush=True,
    )
    for s in samples:
        print(f"  {s}")

    cur.execute(
        """
        SELECT COUNT(*) FROM sResults.TrialPlacements p
        JOIN sResults.Dog d ON d.DogID = p.DogID
        WHERE d.DogName LIKE ?
           OR LOWER(d.DogName) LIKE N'%[[]unverified]%'
        """,
        "UNVERIFIED-%",
    )
    print(f"remaining UNVERIFIED placements: {cur.fetchone()[0]}")
    cn.close()


if __name__ == "__main__":
    main()
