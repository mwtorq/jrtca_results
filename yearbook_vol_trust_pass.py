#!/usr/bin/env python3
"""Trust pass: re-OCR empty / weak / duplicate leaves; missing from A/B/S only.

Rules:
- Grade A/B/S counts as present.
- Grade C does NOT count toward present (or missing-gap fill).
- Baseline only raised, never demoted for A/B/S.
- Report missing page numbers only after this pass.
"""
from __future__ import annotations

import csv
import json
import time
from collections import Counter, defaultdict
from pathlib import Path

import fitz

from ocr_yearbook_source import configure_tesseract
from yearbook_vol_collective_audit import (
    KNOWN_UNNUMBERED,
    OUT_CONF,
    score_evidence,
    is_section_header_leaf,
    load_baseline,
    load_cache,
    ocr_footer_max,
    parse_footer_nums,
    save_baseline,
    save_cache,
    vote_nums,
    write_confidence_csv,
    _force_halves,
    _two_up_halves,
)

ROOT = Path(r"c:\Users\mw\OneDrive - timberwilde.net\repos\jrtca_results")
UPDATED = ROOT / "Updated Yearbook Scans"
AUDIT = ROOT / "_yearbook_vol_collective_audit.csv"
OUT_TXT = ROOT / "_yearbook_vol_trust_missing.txt"
OUT_SUM = ROOT / "_yearbook_vol_trust_summary.csv"
YEARS = range(1990, 1997)
TWO_UP = {"1990 Yearbook Vol 1"}


def vol_folders() -> list[Path]:
    out = []
    for year in YEARS:
        for vol in (1, 2):
            p = UPDATED / f"{year} Yearbook Vol {vol}"
            if p.is_dir():
                out.append(p)
    return out


def leaf_count(folder: Path, *, bulk_only: bool = False) -> int:
    """Count PDF pages. bulk_only excludes filename rescans (pg 108.pdf etc.)."""
    from yearbook_vol_collective_audit import page_num_from_filename

    n = 0
    for pdf in sorted(folder.glob("*.pdf")):
        if bulk_only and page_num_from_filename(pdf):
            continue
        doc = fitz.open(str(pdf))
        n += len(doc)
        doc.close()
    return n


def printed_cap(folder: Path) -> int:
    # Cap from bulk scans only — 1-page pg*.pdf rescans must not inflate the range
    n = leaf_count(folder, bulk_only=True)
    return n * 2 if folder.name in TWO_UP else n


def load_audit_rows() -> list[dict]:
    if not AUDIT.exists():
        return []
    with AUDIT.open(encoding="utf-8", newline="") as f:
        return list(csv.DictReader(f))


def targets_for_folder(folder_name: str, rows: list[dict]) -> list[tuple[str, int, str]]:
    """Return (pdf_name, pdf_page, reason) leaves to force re-OCR."""
    mine = [r for r in rows if r.get("Folder") == folder_name]
    claims: dict[int, list[tuple[str, int, str]]] = defaultdict(list)
    empty: list[tuple[str, int, str]] = []
    for r in mine:
        pdf = r["PDF"]
        try:
            pno = int(r["PdfPage"])
        except Exception:
            continue
        printed = (r.get("Printed") or "").strip()
        src = r.get("Source") or ""
        if not printed:
            empty.append((pdf, pno, "empty"))
            continue
        for part in printed.split(","):
            if part.strip().isdigit():
                claims[int(part.strip())].append((pdf, pno, src))

    targets: dict[tuple[str, int], str] = {}
    for pdf, pno, reason in empty:
        targets[(pdf, pno)] = reason

    # duplicates
    for page, claimants in claims.items():
        uniq = {(p, n) for p, n, _ in claimants}
        if len(uniq) > 1:
            for pdf, pno, _ in claimants:
                targets[(pdf, pno)] = targets.get((pdf, pno), f"dup:{page}")

    # C-grade leaves from confidence file (map page -> evidence pdf)
    conf_path = ROOT / "_yearbook_vol_page_confidence.csv"
    if conf_path.exists():
        with conf_path.open(encoding="utf-8", newline="") as f:
            for r in csv.DictReader(f):
                if r.get("Folder") != folder_name:
                    continue
                if r.get("Grade") != "C":
                    continue
                pdf = (r.get("PDF") or "").strip()
                pno = (r.get("PdfPage") or "").strip()
                if pdf and pno.isdigit():
                    key = (pdf, int(pno))
                    targets[key] = targets.get(key, "grade_C")
                else:
                    # no leaf pointer — re-OCR any leaf that claimed this page
                    page = int(r["Page"])
                    for pdf, pno, _ in claims.get(page, []):
                        targets[(pdf, pno)] = targets.get((pdf, pno), "grade_C")

    return [(pdf, pno, reason) for (pdf, pno), reason in sorted(targets.items())]


def clear_cache_leaf(cache: dict, folder: str, pdf: str, pno: int) -> None:
    for li in (0, 1):
        key = f"{folder}/{pdf}#p{pno}:L{li}"
        cache.pop(key, None)


_GRADE_RANK = {"S": 5, "A": 4, "B": 3, "D": 2, "C": 1}


def trust_merge(baseline: dict, folder: str, page: int, ev: dict) -> None:
    """Monotonic by grade rank, then confidence. Never replace A/B/S/D with C."""
    folders = baseline.setdefault("folders", {})
    meta = folders.setdefault(folder, {"pages": {}, "page_list": [], "count": 0})
    pages = meta.setdefault("pages", {})
    key = str(page)
    old = pages.get(key)
    new_g = ev.get("grade") or "C"
    if old is not None:
        old_g = old.get("grade") or "C"
        if _GRADE_RANK.get(new_g, 0) < _GRADE_RANK.get(old_g, 0):
            return
        if _GRADE_RANK.get(new_g, 0) == _GRADE_RANK.get(old_g, 0) and int(
            ev.get("confidence", 0)
        ) <= int(old.get("confidence", 0)):
            return
    pages[key] = {
        "confidence": int(ev["confidence"]),
        "grade": new_g,
        "reason": ev["reason"],
        "source": ev.get("source") or "",
        "pdf": ev.get("pdf") or "",
        "pdf_page": str(ev.get("pdf_page") or ""),
    }
    meta["page_list"] = sorted(int(p) for p in pages)
    meta["count"] = len(meta["page_list"])


def render_one_page(pdf: Path, pno: int, scale: float = 4.0):
    """Render a single PDF page to PIL RGB via PyMuPDF."""
    from PIL import Image

    doc = fitz.open(str(pdf))
    page = doc[pno - 1]
    mat = fitz.Matrix(scale, scale)
    pix = page.get_pixmap(matrix=mat, alpha=False)
    img = Image.frombytes("RGB", [pix.width, pix.height], pix.samples)
    native = page.get_text("text") or ""
    doc.close()
    return img, native


def ocr_pdf_page(
    folder: Path,
    pdf: Path,
    pno: int,
    cache: dict,
    force_two_up: bool,
) -> tuple[list[int], list[dict], int]:
    """Force max-OCR one PDF page. Returns (nums, evidence_list, ocr_calls)."""
    clear_cache_leaf(cache, folder.name, pdf.name, pno)
    evidence: list[dict] = []
    ocr_calls = 0

    img, native = render_one_page(pdf, pno, scale=4.0)
    native_nums = parse_footer_nums(native)
    force_two_up = force_two_up or (
        "1990" in folder.name and "vol 1" in folder.name.lower()
    )

    halves = _force_halves(img) if force_two_up else _two_up_halves(img)
    leaf_imgs = halves if halves else [img]
    leaf_hits: list[int] = []
    for li, leaf in enumerate(leaf_imgs):
        key = f"{folder.name}/{pdf.name}#p{pno}:L{li}"
        label = is_section_header_leaf(leaf)
        if label:
            cache[key] = {"nums": [], "section": f"{pdf.name}#p{pno}L{li}: {label}"}
            ocr_calls += 1
            evidence.append(
                {
                    "page": None,
                    "confidence": 100,
                    "grade": "S",
                    "reason": f"section: {label}",
                    "source": "structural",
                    "pdf": pdf.name,
                    "pdf_page": pno,
                }
            )
            continue
        ocr = ocr_footer_max(leaf)
        ocr_calls += 1
        got = vote_nums([ocr, native if li == 0 else ""])[:1]
        cache[key] = {"nums": got, "ocr_tail": (ocr or "")[-180:]}
        for n in got:
            src = "native+hqmax_footer" if n in native_nums else "hqmax_footer"
            conf, grade, reason = score_evidence(
                src, n, ocr_tail=cache[key].get("ocr_tail")
            )
            if n in native_nums:
                conf2, grade2, reason2 = score_evidence(
                    "native", n, ocr_tail=native[-180:]
                )
                if conf2 >= conf:
                    conf, grade, reason, src = conf2, grade2, reason2, "native"
            evidence.append(
                {
                    "page": n,
                    "confidence": conf,
                    "grade": grade,
                    "reason": reason,
                    "source": src,
                    "pdf": pdf.name,
                    "pdf_page": pno,
                }
            )
            leaf_hits.append(n)
    if not leaf_hits and native_nums:
        keep = native_nums if (halves or force_two_up) else native_nums[-1:]
        for n in keep:
            conf, grade, reason = score_evidence("native", n, ocr_tail=native[-180:])
            evidence.append(
                {
                    "page": n,
                    "confidence": conf,
                    "grade": grade,
                    "reason": reason,
                    "source": "native",
                    "pdf": pdf.name,
                    "pdf_page": pno,
                }
            )
            leaf_hits.append(n)
    return leaf_hits, evidence, ocr_calls


def pages_by_grade(
    baseline: dict, folder: str, cap: int
) -> tuple[set[int], set[int], set[int]]:
    """Returns (trusted A/B/S, locked D prior, weak C)."""
    meta = (baseline.get("folders") or {}).get(folder) or {}
    pages = meta.get("pages") or {}
    trusted: set[int] = set()
    locked_d: set[int] = set()
    weak_c: set[int] = set()
    if isinstance(pages, dict):
        for p, ev in pages.items():
            n = int(p)
            if not (1 <= n <= cap):
                continue
            g = ev.get("grade")
            if g in {"A", "B", "S"}:
                trusted.add(n)
            elif g == "D":
                locked_d.add(n)
            elif g == "C":
                weak_c.add(n)
    known = KNOWN_UNNUMBERED.get(folder, set())
    trusted |= {n for n in known if 1 <= n <= cap}
    return trusted, locked_d, weak_c


def gaps_missing(present: set[int], cap: int, known: set[int]) -> list[int]:
    if not present:
        return []
    hi = min(cap, max(present))
    return [n for n in range(1, hi + 1) if n not in present and n not in known]


def main() -> int:
    configure_tesseract()
    cache = load_cache()
    baseline = load_baseline()
    rows = load_audit_rows()
    summaries = []
    lines = [
        "TRUST PASS — missing page numbers (A/B/S only)",
        "===============================================",
        "Re-OCR'd: empty-footer leaves, grade-C leaves, duplicate claimants.",
        "Grade C does not count as present. Missing = holes in trusted span.",
        "",
    ]

    for folder in vol_folders():
        name = folder.name
        cap = printed_cap(folder)
        force_two = name in TWO_UP
        targets = targets_for_folder(name, rows)
        print(
            f"{name}: cap={cap} reocr_targets={len(targets)}",
            flush=True,
        )
        ocr_used = 0
        newly = []
        t0 = time.time()
        for i, (pdf_name, pno, reason) in enumerate(targets, 1):
            pdf = folder / pdf_name
            if not pdf.is_file():
                print(f"  missing file {pdf_name}", flush=True)
                continue
            print(
                f"  [{i}/{len(targets)}] {pdf_name} p{pno} ({reason})",
                flush=True,
            )
            nums, evidence, calls = ocr_pdf_page(
                folder, pdf, pno, cache, force_two_up=force_two
            )
            ocr_used += calls
            for ev in evidence:
                page = ev.get("page")
                if page is None:
                    continue
                old_t, old_d, _ = pages_by_grade(baseline, name, cap)
                old_present = old_t | old_d
                trust_merge(baseline, name, int(page), ev)
                if (
                    ev["grade"] in {"A", "B", "S"}
                    and int(page) not in old_present
                    and 1 <= int(page) <= cap
                ):
                    newly.append(int(page))
            if i % 5 == 0:
                save_cache(cache)
                save_baseline(baseline)
        save_cache(cache)
        save_baseline(baseline)

        # Ensure known unnumbered marked S
        known = KNOWN_UNNUMBERED.get(name, set())
        for n in known:
            if 1 <= n <= cap:
                trust_merge(
                    baseline,
                    name,
                    n,
                    {
                        "confidence": 100,
                        "grade": "S",
                        "reason": "unnumbered-but-present (section/blank)",
                        "source": "structural",
                        "pdf": "",
                        "pdf_page": "",
                    },
                )

        trusted, locked_d, weak_c = pages_by_grade(baseline, name, cap)
        # Present for gaps: A/B/S + locked D. C never fills gaps.
        present = trusted | locked_d
        missing = gaps_missing(present, cap, known)
        # Remaining C claims that aren't otherwise present = uncertain, not missing
        uncertain = sorted(n for n in weak_c if n not in present)
        grades = Counter()
        meta = (baseline.get("folders") or {}).get(name) or {}
        for ev in (meta.get("pages") or {}).values():
            grades[ev.get("grade", "?")] += 1

        print(
            f"  DONE {time.time()-t0:.0f}s present={len(present)} "
            f"(A/B/S={len(trusted)} D={len(locked_d)}) "
            f"missing={len(missing)} weak_C={len(uncertain)} "
            f"newly={sorted(set(newly))} grades={dict(grades)}",
            flush=True,
        )
        if missing:
            print(f"  MISSING: {','.join(map(str, missing))}", flush=True)
        else:
            print("  MISSING: (none)", flush=True)
        if uncertain:
            print(
                f"  UNCERTAIN_C (not counted present): "
                f"{','.join(map(str, uncertain[:40]))}"
                f"{'...' if len(uncertain)>40 else ''}",
                flush=True,
            )

        lines.append(name)
        lines.append(
            f"  printed_cap~{cap}  present={len(present)} "
            f"(A/B/S={len(trusted)} D={len(locked_d)})"
        )
        lines.append(f"  reocr_targets={len(targets)}  ocr_calls={ocr_used}")
        lines.append(
            f"  newly_confirmed: "
            + (",".join(map(str, sorted(set(newly)))) if newly else "(none)")
        )
        lines.append(
            f"  MISSING ({len(missing)}): "
            + (",".join(map(str, missing)) if missing else "(none)")
        )
        lines.append(
            f"  UNCERTAIN_C ({len(uncertain)}): "
            + (",".join(map(str, uncertain)) if uncertain else "(none)")
        )
        lines.append(f"  grade_counts: {dict(sorted(grades.items()))}")
        lines.append("")
        OUT_TXT.write_text("\n".join(lines) + "\n", encoding="utf-8")
        write_confidence_csv(baseline)

        summaries.append(
            {
                "Folder": name,
                "PrintedCap": cap,
                "TrustedCount": len(trusted),
                "LockedD": len(locked_d),
                "PresentCount": len(present),
                "MissingCount": len(missing),
                "Missing": ",".join(map(str, missing)),
                "UncertainC": ",".join(map(str, uncertain)),
                "ReocrTargets": len(targets),
                "OcrCalls": ocr_used,
                "NewlyConfirmed": ",".join(map(str, sorted(set(newly)))),
            }
        )

    with OUT_SUM.open("w", encoding="utf-8", newline="") as f:
        w = csv.DictWriter(
            f,
            fieldnames=[
                "Folder",
                "PrintedCap",
                "TrustedCount",
                "LockedD",
                "PresentCount",
                "MissingCount",
                "Missing",
                "UncertainC",
                "ReocrTargets",
                "OcrCalls",
                "NewlyConfirmed",
            ],
        )
        w.writeheader()
        w.writerows(summaries)
    save_baseline(baseline)
    write_confidence_csv(baseline)
    OUT_TXT.write_text("\n".join(lines) + "\n", encoding="utf-8")
    print(f"Wrote {OUT_TXT}", flush=True)
    print(f"Wrote {OUT_SUM}", flush=True)
    print(f"Wrote {OUT_CONF}", flush=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
