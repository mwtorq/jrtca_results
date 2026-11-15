"""JR-54: recover place gaps from sibling HQ OCR (front/back/reversed) when no PDF.

Same evidence gate as PDF path: missing rank only if sibling text has both
neighbors with an owned-by body strictly between them in a short window.
"""
from __future__ import annotations

import json
import re
import shutil
from dataclasses import asdict, dataclass, field
from pathlib import Path

from _jr54_recover_v2 import (
    TARGET,
    dog_key,
    find_gap_blocks,
    find_hq,
    find_updated_hq,
    ordinal,
    places_between_neighbors,
)
from yearbook_ocr import audit_results_ocr_page

BASE = Path("_ocr_baseline_v2/yearbook_1990_2001")


@dataclass
class Log:
    year: int
    file: str
    before: int = 0
    after: int = 0
    recovered: list[str] = field(default_factory=list)
    parked: list[str] = field(default_factory=list)
    siblings: list[str] = field(default_factory=list)


def sibling_hq_files(hq: Path) -> list[Path]:
    """Same page-range family: front/back/back reversed variants."""
    name = hq.name
    if "_ocr_hqmax.txt" not in name:
        return []
    # Normalize to page-range stem
    # e.g. "1996 Vol 1 pg 61-110 front_ocr_hqmax.txt"
    m = re.match(r"^(.*?\bpg\s+\d+\s*-\s*\d+)\b", name, flags=re.I)
    if not m:
        return []
    prefix = m.group(1)
    out = []
    for f in hq.parent.glob(prefix + "*_ocr_hqmax.txt"):
        if f.resolve() != hq.resolve():
            out.append(f)
    return sorted(out)


def process(year: int, file: str) -> Log:
    log = Log(year=year, file=file)
    hq = find_hq(year, file)
    if not hq:
        return log
    text = hq.read_text(encoding="utf-8", errors="replace")
    log.before = sum(1 for c, _ in audit_results_ocr_page(text, max_samples=120) if c in TARGET)
    sibs = sibling_hq_files(hq)
    log.siblings = [s.name for s in sibs]
    if not sibs:
        return log

    bak = Path(str(hq) + ".pre_jr54_sib")
    if not bak.exists():
        shutil.copy2(hq, bak)

    lines = text.splitlines()
    gaps = find_gap_blocks(lines)
    sib_texts = [(s, s.read_text(encoding="utf-8", errors="replace")) for s in sibs]

    for g in sorted(gaps, key=lambda x: x["ia"], reverse=True):
        ka = dog_key(g["sa"])
        kb = dog_key(g["sb"])
        recovered = {}
        used = None
        for s, st in sib_texts:
            got = places_between_neighbors(st, ka, kb, g["missing"])
            if got:
                recovered = got
                used = s.name
                break
        if not recovered:
            log.parked.append(
                f"SIB_MISS {g['header'][:40]} missing {g['missing']} between {g['sa'][:35]} / {g['sb'][:35]}"
            )
            continue
        insert_at = g["ia"] + 1
        block = [f"{ordinal(r)}: {recovered[r]}" for r in sorted(recovered)]
        lines[insert_at:insert_at] = block
        for r in sorted(recovered):
            log.recovered.append(f"{ordinal(r)}: {recovered[r][:70]} <- {used} | {g['header'][:30]}")

    new_text = "\n".join(lines)
    if not new_text.endswith("\n"):
        new_text += "\n"
    if log.recovered:
        hq.write_text(new_text, encoding="utf-8")
        upd = find_updated_hq(year, hq)
        if upd:
            upd.write_text(new_text, encoding="utf-8")
        text = new_text

    log.after = sum(1 for c, _ in audit_results_ocr_page(text, max_samples=120) if c in TARGET)
    park = hq.with_name(hq.name.replace("_ocr_hqmax.txt", "_PARKED_jr54.txt"))
    prev = park.read_text(encoding="utf-8") if park.exists() else ""
    park.write_text(
        prev
        + "\n## Sibling recovery\n"
        + f"before {log.before} after {log.after}\n"
        + "RECOVERED:\n"
        + "\n".join(f"- {x}" for x in log.recovered)
        + "\nPARKED:\n"
        + "\n".join(f"- {x}" for x in log.parked[:40])
        + "\n",
        encoding="utf-8",
    )
    return log


def main() -> None:
    import argparse

    ap = argparse.ArgumentParser()
    ap.add_argument("--years", type=int, nargs="+", default=[1996])
    args = ap.parse_args()
    dem = json.loads(Path("_jr54_demote_counts.json").read_text(encoding="utf-8"))
    reports = []
    for d in dem["demoted"]:
        if d["year"] not in args.years:
            continue
        if "pg " not in d["file"] and "Vol" not in d["file"]:
            # still try — sibling helper no-ops without page-range
            pass
        print(f"\n### {d['year']} {d['file']}", flush=True)
        log = process(d["year"], d["file"])
        print(
            f"hits {log.before}->{log.after} recovered={len(log.recovered)} "
            f"sibs={len(log.siblings)} parked={len(log.parked)}",
            flush=True,
        )
        for r in log.recovered[:8]:
            print(" +", r, flush=True)
        reports.append(asdict(log))
    out = Path(f"_jr54_recover_sib_{'_'.join(map(str, args.years))}.json")
    out.write_text(json.dumps(reports, indent=2), encoding="utf-8")
    print("WROTE", out)


if __name__ == "__main__":
    main()
