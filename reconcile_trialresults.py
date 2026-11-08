#!/usr/bin/env python3
"""Per-trial raw reconcile + label normalize.

Default is report-only. --apply --normalize-only rewrites division/class/result
to the canonical form of the matching raw line. Does not create dogs or trials.
Does not delete or insert unless those flags are set AND the parse is trusted.
"""
from __future__ import annotations

import os
import re
import sys
from pathlib import Path

print("imports", flush=True)
import pyodbc
from normalize_maps import canon_class, canon_div, canon_dog, canon_result
from populate_trialresults_fixed import normalize_placement_label
from apply_hurdles_all_dogs import day_for_trial, is_vault, parse_tv_file, resolve_src, src_dog
from remount_source_divisions import (
    CONN,
    class_key,
    classes_ok,
    dogs_ok,
    ensure_tc,
    fam,
    res_key,
)
from fix_racing_steeplechase_class_collapse import parse_all_slots

SKIP_RES = {"SCR", "DNP", "DQ", "F", "NP", "ABS", "---", "--", "", "-- SCR --", "-- F --"}
TV_NO_RACE = {1873, 1874}


def load_slots(path, tname):
    rp = resolve_src(path)
    if not rp or not os.path.isfile(rp):
        return None, "nosource"
    try:
        if os.path.getsize(rp) > 3_000_000:
            return None, "huge"
    except OSError:
        return None, "nosource"
    vault = is_vault(rp) or is_vault(path)
    try:
        if vault:
            want_day = day_for_trial(tname)
            slots = []
            for day, div, cls, place, dog in parse_tv_file(rp):
                if want_day and day not in ("all", want_day):
                    continue
                slots.append((div, cls, place, dog))
        else:
            slots = [
                (d, c, p, src_dog(line))
                for d, c, p, line in parse_all_slots(Path(rp))
            ]
    except Exception as e:
        return None, f"parse:{e}"
    out = []
    for div, cls, place, dog in slots:
        label = normalize_placement_label(place, cls)
        if (label or "").upper() in SKIP_RES:
            continue
        out.append(
            {
                "div": div or "",
                "cls": cls or "",
                "res": label or "",
                "dog": canon_dog(dog),
                "fam": fam(div or ""),
                "ck": class_key(cls or ""),
                "rk": res_key(canon_result(label or "", cls or "")),
            }
        )
    return out, "ok"


def match_src(slot, trial_dogs):
    hits = [did for did, nm in trial_dogs if dogs_ok(slot["dog"], nm)]
    if len(hits) == 1:
        return hits[0]
    return None


def process(cur, tid, year, tname, path, apply, norm_only, stats):
    if tid in TV_NO_RACE:
        stats["tv_locked"] += 1
        return
    slots, status = load_slots(path, tname)
    if slots is None:
        stats[status.split(":")[0]] += 1
        return
    stats["parsed"] += 1
    cur.execute(
        """
        SELECT p.TrialPlacementsID, p.DogID, dog.DogName, p.Result,
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
    db = [list(r) for r in cur.fetchall()]
    trial_dogs = list({(int(r[1]), r[2]) for r in db})

    expected = {}
    for sl in slots:
        did = match_src(sl, trial_dogs)
        if did is None:
            stats["src_unmatched"] += 1
            continue
        key = (did, sl["rk"], sl["fam"], sl["ck"])
        expected.setdefault(key, sl)

    champ_re = re.compile(r"CHAMPION|RESERVE", re.I)

    def find_src(did, rk, df, ck, cls):
        sl = expected.get((did, rk, df, ck))
        if sl:
            return sl
        for (ed, er, ef, ec), sl in expected.items():
            if ed != did or er != rk or ef != df:
                continue
            if not classes_ok(cls, sl["cls"]):
                continue
            if bool(champ_re.search(cls or "")) != bool(champ_re.search(sl["cls"] or "")):
                continue
            return sl
        return None

    for row in db:
        pid, did, dname, res, div, cls, tcid = row
        did = int(did)
        rk = res_key(canon_result(res, cls))
        sl = find_src(did, rk, fam(div), class_key(cls), cls)
        if sl is None:
            stats["db_unmatched"] += 1
            continue
        ndiv = canon_div(sl["div"])
        ncls = canon_class(sl["cls"])
        nres = canon_result(sl["res"], sl["cls"])
        need_tc = canon_div(div) != ndiv or canon_class(cls) != ncls
        need_res = canon_result(res, cls) != nres
        if not need_tc and not need_res:
            stats["already"] += 1
            continue
        if apply and (norm_only or True):
            if need_tc:
                new_tc = ensure_tc(cur, tid, ndiv, ncls)
                if int(new_tc) != int(tcid):
                    cur.execute(
                        "UPDATE sResults.TrialPlacements SET TrialClassID=? "
                        "WHERE TrialPlacementsID=?",
                        new_tc,
                        pid,
                    )
                    stats["norm_tc"] += 1
            if need_res:
                cur.execute(
                    "UPDATE sResults.TrialPlacements SET Result=? WHERE TrialPlacementsID=?",
                    nres,
                    pid,
                )
                stats["norm_res"] += 1
        else:
            if need_tc:
                stats["norm_tc"] += 1
            if need_res:
                stats["norm_res"] += 1


def main():
    apply = "--apply" in sys.argv
    norm_only = "--normalize-only" in sys.argv or not apply
    year_min = 0
    year_max = 9999
    only = None
    args = sys.argv[1:]
    for i, a in enumerate(args):
        if a == "--year-min":
            year_min = int(args[i + 1])
        elif a == "--year-max":
            year_max = int(args[i + 1])
        elif a == "--trial":
            only = int(args[i + 1])
    print("connecting", flush=True)
    cn = pyodbc.connect(CONN, timeout=8)
    cn.timeout = 40
    cur = cn.cursor()
    print(f"connected apply={apply} normalize_only={norm_only}", flush=True)
    stats = {
        "parsed": 0,
        "nosource": 0,
        "huge": 0,
        "parse": 0,
        "src_unmatched": 0,
        "db_unmatched": 0,
        "already": 0,
        "norm_tc": 0,
        "norm_res": 0,
        "tv_locked": 0,
        "skip_year": 0,
    }
    if only:
        cur.execute(
            """
            SELECT TrialListID, Year, TrialName, TrialResultFilePath
            FROM sResults.TrialList WHERE TrialListID=?
            """,
            only,
        )
    else:
        cur.execute(
            """
            SELECT TrialListID, Year, TrialName, TrialResultFilePath
            FROM sResults.TrialList
            WHERE TrialResultFilePath IS NOT NULL AND LTRIM(RTRIM(TrialResultFilePath)) <> ''
            ORDER BY Year, TrialListID
            """
        )
    trials = cur.fetchall()
    print(f"trials={len(trials)}", flush=True)
    n = 0
    for tid, year, tname, path in trials:
        y = int(year or 0)
        if y < year_min or y > year_max:
            stats["skip_year"] += 1
            continue
        n += 1
        print(f"[{n}] {tid} {y}", flush=True)
        try:
            process(cur, int(tid), y, tname or "", path or "", apply, norm_only, stats)
            if apply:
                cn.commit()
        except Exception as e:
            print(f"  FAIL {tid} {e}", flush=True)
            try:
                cn.rollback()
            except Exception:
                pass
        if n % 25 == 0:
            print(f"progress {stats}", flush=True)
    print(f"DONE {stats}", flush=True)
    cn.close()


if __name__ == "__main__":
    main()
