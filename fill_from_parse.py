#!/usr/bin/env python3
"""Fill/remount catalog placements from parse_trial_source_file.

Inserts only for dogs already in the catalog (Cumberland LC may create).
No extra-row deletes. No 2011 MOE invention.
"""
from __future__ import annotations

import contextlib
import io
import os
import re
import sys
from concurrent.futures import ThreadPoolExecutor, TimeoutError as FuturesTimeout

import pyodbc
from normalize_maps import canon_class, canon_div, canon_result
from populate_trialresults_fixed import (
    get_or_create_dog,
    get_or_create_owner,
    parse_trial_source_file,
    strip_entries_from_class_name,
)
from apply_hurdles_all_dogs import SKIP_RES
from remount_source_divisions import (
    CONN,
    class_key,
    classes_ok,
    dog_key,
    dogs_ok,
    ensure_tc,
    fam,
    res_key,
    resolve_path,
)

_JUNK = re.compile(
    r"^(?:class|division|section|entries|judge|owned by|number of)\b",
    re.I,
)


def junk_dog(name: str) -> bool:
    n = (name or "").strip()
    if len(n) < 3:
        return True
    return bool(_JUNK.search(n))


def moe_2011(year, tname: str) -> bool:
    if year != 2011:
        return False
    u = (tname or "").upper()
    return "EARTHDOG" in u and ("MISSOURI" in u or "MOE" in u)


def next_pid(cur) -> int:
    cur.execute("SELECT ISNULL(MAX(TrialPlacementsID),0)+1 FROM sResults.TrialPlacements")
    return int(cur.fetchone()[0])


def build_catalog_index(cur):
    cur.execute("SELECT DogID, DogName FROM sResults.Dog")
    idx = {}
    n = 0
    for did, nm in cur.fetchall():
        k = dog_key(nm)
        if len(k) < 10:
            continue
        idx.setdefault(k[:4], []).append((int(did), nm))
        n += 1
    return idx, n


def _unique_dog_id(parsed_name: str, hit_ids, id_name_pairs):
    """Return one DogID when hits are unique or exact duplicate registered names."""
    hits = list(dict.fromkeys(int(x) for x in hit_ids))
    if len(hits) == 1:
        return hits[0]
    if len(hits) < 2:
        return None
    pk = dog_key(parsed_name)
    if len(pk) < 10:
        return None
    names = {int(did): dog_key(nm) for did, nm in id_name_pairs if int(did) in hits}
    # Only collapse when every hit is an exact registered-name duplicate.
    if names and all(k == pk for k in names.values()):
        return min(hits)
    return None


def prefer_session_dest(parse_dest: str, existing_dest: str) -> str:
    """Do not remount Friday/Sunday racing dests down to generic flats/steeple."""
    pu = (parse_dest or "").upper()
    eu = (existing_dest or "").upper()
    if not eu:
        return parse_dest
    has_day_e = "FRIDAY" in eu or "SUNDAY" in eu
    has_day_p = "FRIDAY" in pu or "SUNDAY" in pu
    if not (has_day_e and not has_day_p):
        return parse_dest
    e_h = "STEEPLE" in eu or "HURDLE" in eu
    p_h = "STEEPLE" in pu or "HURDLE" in pu
    e_f = "FLAT" in eu
    p_f = "FLAT" in pu or (not p_h and "RACING" in pu)
    if e_h and p_h:
        return existing_dest
    if e_f and p_f:
        return existing_dest
    return parse_dest


def _vault_html_path(rp: str) -> str | None:
    """Resolve TrialVault scrape HTML from an html path or sibling *_raw.txt."""
    base = os.path.basename(rp).lower()
    if "trialvault" not in base:
        return None
    if base.endswith((".html", ".htm")):
        return rp if os.path.isfile(rp) else None
    if base.endswith("_raw.txt"):
        html = rp[: -len("_raw.txt")] + ".html"
        return html if os.path.isfile(html) else None
    return None


def _parse_trialvault_placements(html_path: str, year, tname: str):
    """Parse TrialVault HTML; keep only rows for this TrialList session name."""
    from scrape_trial_results_fixed import parse_trialvault_html_file
    from populate_trialresults_fixed import PlacementResult, TrialInfo

    results = parse_trialvault_html_file(
        html_path, year_hint=str(int(year or 0)), force_folder_year=True
    )
    if not results:
        return None, [], "empty vault parse"
    want = re.sub(r"\s+", " ", (tname or "").strip().lower())
    matched = []
    for r in results:
        got = re.sub(r"\s+", " ", (r.trial_name or "").strip().lower())
        # Exact day/session match only — do not let Sat/Sun rows fall into an
        # undated parent TrialList via prefix matching.
        if got != want:
            continue
        matched.append(
            PlacementResult(
                division=r.division or "",
                class_name=r.class_name or "",
                placement=r.placement or "",
                dog_name=r.dog_name or "",
                owner_name=r.owner or "",
                entries=int(r.entry_count or 0),
                time=r.time or "",
            )
        )
    if not matched:
        return None, [], "no vault rows for trial name"
    info = TrialInfo(
        trial_name=tname or results[0].trial_name or "",
        location="",
        start_date="",
        end_date="",
        chair="",
        administrator="",
        judges="",
        year=int(year or 0),
    )
    return info, matched, None


def process_trial(cur, tid, year, tname, path, apply, stats, catalog_idx=None):
    if moe_2011(year, tname):
        stats["skip_2011"] += 1
        return
    rp = resolve_path(path or "")
    if not rp or not os.path.isfile(rp):
        stats["skip_nopath"] += 1
        return
    vault_html = _vault_html_path(rp)
    yearbook = False
    try:
        from ocr_yearbook_source import is_yearbook_path, resolve_parse_text_path

        yearbook = is_yearbook_path(rp)
    except Exception:
        resolve_parse_text_path = None
    try:
        size = os.path.getsize(rp)
        base = os.path.basename(rp).lower()
        if base.startswith("debug_"):
            # TrialVault HTML is usable via scrape parser; *_raw.txt uses HTML sibling.
            if "trialvault" in base and base.endswith((".html", ".htm")) and not vault_html:
                stats["skip_nopath"] += 1
                return
            if not base.endswith(("_raw.txt", ".txt", ".html", ".htm")):
                stats["skip_nopath"] += 1
                return
        if base.endswith((".xls", ".xlsx")) and size > 3_000_000:
            stats["skip_nopath"] += 1
            return
        # Yearbook image PDFs are often >15MB; allow them (OCR path).
        if size > 15_000_000 and not yearbook:
            stats["skip_nopath"] += 1
            return
    except OSError:
        stats["skip_nopath"] += 1
        return

    parse_rp = rp
    if yearbook and resolve_parse_text_path is not None and not vault_html:
        try:
            parse_rp = resolve_parse_text_path(rp, ensure_ocr=True)
        except Exception:
            stats["skip_err"] += 1
            return

    def _parse():
        with contextlib.redirect_stdout(io.StringIO()):
            if vault_html:
                return _parse_trialvault_placements(vault_html, year, tname)
            # yearbook: content-derived year inside parse_trial_source_file
            return parse_trial_source_file(parse_rp, int(year or 0), quiet=True)

    # Vault HTML / yearbook OCR can exceed 20s.
    timeout = 300 if yearbook else (90 if vault_html else 20)
    ex = ThreadPoolExecutor(max_workers=1)
    try:
        info, placements, err = ex.submit(_parse).result(timeout=timeout)
    except (FuturesTimeout, Exception):
        stats["skip_err"] += 1
        return
    finally:
        ex.shutdown(wait=False, cancel_futures=True)
    if err or not placements:
        stats["skip_err"] += 1
        return
    cur.execute(
        """
        SELECT p.TrialPlacementsID, dog.DogID, dog.DogName, p.Result,
               div.DivisionName, c.ClassName, p.TrialClassID
        FROM sResults.TrialPlacements p
        JOIN sResults.Dog dog ON dog.DogID=p.DogID
        JOIN sResults.TrialClass tc ON tc.TrialClassID=p.TrialClassID
        JOIN sResults.Class c ON c.ClassID=tc.ClassID
        JOIN sResults.Division div ON div.DivisionID=c.DivisionID
        WHERE tc.TrialListID=?
        """,
        tid,
    )
    db = cur.fetchall()
    trial_dogs = [(int(r[1]), r[2]) for r in db]
    cache = {}
    used = set()
    # Insert any unmatched parse slot whose dog is already resolved in catalog.
    # The old len(parse)>len(db) gate blocked ~98% of true unders when the DB
    # was already dense with extras/miscategorized rows.
    allow_insert = True
    cumberland_lc = "CUMBERLAND" in (tname or "").upper() and "LURE" in (tname or "").upper()

    for p in placements:
        res = canon_result(p.placement or "", p.class_name or "")
        if not res or res.upper() in SKIP_RES:
            stats["skip_nonplace"] += 1
            continue
        dog = (p.dog_name or "").strip()
        if junk_dog(dog):
            stats["skip_junk"] += 1
            continue
        cls, _ = strip_entries_from_class_name(p.class_name or "")
        cls = canon_class(cls)
        dest = canon_div(p.division or "", cls)
        if not dest or not cls:
            stats["skip_junk"] += 1
            continue
        key = dog.strip().lower()
        if key in cache:
            did = cache[key]
        else:
            hits = [tdid for tdid, nm in trial_dogs if dogs_ok(dog, nm)]
            did = _unique_dog_id(dog, hits, trial_dogs)
            if did is None and catalog_idx is not None:
                dk = dog_key(dog)
                if len(dk) >= 10:
                    bucket = catalog_idx.get(dk[:4], [])
                    chits = list(dict.fromkeys(cid for cid, nm in bucket if dogs_ok(dog, nm)))
                    did = _unique_dog_id(dog, chits, bucket)
                    if did is not None:
                        stats["catalog_hit"] += 1
            cache[key] = did
        if did is None and cumberland_lc:
            oid = get_or_create_owner(cur, p.owner_name) if apply else None
            if apply:
                did = get_or_create_dog(cur, dog, oid)
                trial_dogs.append((int(did), dog))
                stats["new_cumberland"] += 1
        if did is None:
            stats["skip_nodog"] += 1
            continue
        sf = fam(dest)
        sck = class_key(cls)
        sr = res_key(res)
        match = None
        fam_match = None
        for row in db:
            pid, odid, oname, ores, odiv, ocls, tcid = row
            if pid in used or int(odid) != int(did):
                continue
            if res_key(ores) != sr:
                continue
            of = fam(odiv)
            if of != sf and of not in ("UNKNOWN", "OTHER"):
                continue
            if classes_ok(cls, ocls) or class_key(ocls) == sck:
                match = row
                break
            if fam_match is None:
                fam_match = row
        if match is None:
            match = fam_match
        if match:
            pid, odid, oname, ores, odiv, ocls, tcid = match
            used.add(pid)
            dest = prefer_session_dest(dest, odiv or "")
            if dest.upper() != (odiv or "").upper() or canon_class(ocls) != cls:
                if apply:
                    new_tc = ensure_tc(cur, tid, dest, cls)
                    cur.execute(
                        "UPDATE sResults.TrialPlacements SET TrialClassID=?, Result=? WHERE TrialPlacementsID=?",
                        new_tc,
                        res,
                        pid,
                    )
                stats["remount"] += 1
            else:
                stats["ok"] += 1
            continue
        if not allow_insert:
            stats["skip_under"] += 1
            continue
        if apply:
            tcid = ensure_tc(cur, tid, dest, cls)
            pid = next_pid(cur)
            cur.execute(
                """
                INSERT INTO sResults.TrialPlacements
                    (TrialPlacementsID, TrialListID, TrialClassID, DogID, Result)
                VALUES (?, ?, ?, ?, ?)
                """,
                pid,
                tid,
                tcid,
                did,
                res,
            )
            db.append((pid, did, dog, res, dest, cls, tcid))
            used.add(pid)
        stats["insert"] += 1


def main():
    apply = "--apply" in sys.argv
    cn = pyodbc.connect(CONN, timeout=60)
    cur = cn.cursor()
    cur.execute(
        """
        SELECT TrialListID, Year, TrialName, TrialResultFilePath
        FROM sResults.TrialList
        ORDER BY Year, TrialListID
        """
    )
    trials = cur.fetchall()
    stats = {k: 0 for k in (
        "insert", "remount", "ok", "skip_nodog", "skip_junk", "skip_nonplace",
        "skip_2011", "skip_nopath", "skip_err", "new_cumberland", "skip_under",
        "catalog_hit",
    )}
    catalog_idx, ndogs = build_catalog_index(cur)
    print(f"trials={len(trials)} apply={apply} catalog_dogs={ndogs} buckets={len(catalog_idx)}", flush=True)
    for i, (tid, year, tname, path) in enumerate(trials, 1):
        if i <= 3 or i % 20 == 0:
            print(f"  go {i} tid={tid} {year}", flush=True)
        process_trial(cur, tid, year, tname, path, apply, stats, catalog_idx)
        if apply and i % 25 == 0:
            cn.commit()
        if i % 20 == 0:
            print(f"  {i}/{len(trials)} {stats}", flush=True)
    if apply:
        cn.commit()
        print("COMMITTED", stats, flush=True)
    else:
        cn.rollback()
        print("DRY-RUN", stats, flush=True)
    cn.close()


if __name__ == "__main__":
    main()
