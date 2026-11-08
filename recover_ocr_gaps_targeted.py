#!/usr/bin/env python3
"""Targeted C1/O6 recovery — crop OCR only for missing titles / truncated owners.

Does **not** full-PDF re-OCR. For each HQ page that still shows class_header_gap
(C1) or owner_tail_trunc (O6) after finalize:

  C1 — re-render the PDF page, split columns, run ``_fill_missing_class_titles``
       (interstitial band + box inject) on existing column text + image.
  O6 — for truncated ``owned by …`` lines, re-OCR a right-edge strip of the
       matched line band and keep a longer owner tail when found.

Writes updated ``*_ocr_hqmax.txt`` (backup ``*.pre_c1o6`` once). Keep tess load
low so live A1 tracks are not starved (default 1 page at a time).

Usage:
  python -u recover_ocr_gaps_targeted.py --years 1997 1998
  python -u recover_ocr_gaps_targeted.py --years 1997 --limit-pages 5
"""
from __future__ import annotations

import argparse
import re
import shutil
from datetime import datetime, timezone
from pathlib import Path
from zoneinfo import ZoneInfo

_LOCAL_TZ = ZoneInfo("America/Chicago")


def _local_ts() -> str:
    local = datetime.now(timezone.utc).astimezone(_LOCAL_TZ)
    abbr = "CDT" if local.dst() else "CST"
    return local.strftime(f"%Y-%m-%d %H:%M:%S {abbr}")

from PIL import Image

from yearbook_ocr import (
    _fill_missing_class_titles,
    _iter_class_header_gap_indices,
    _ocr_column_line_boxes,
    _tesseract_string,
    _two_column_cut_x,
    _column_gutter_gap,
    audit_results_ocr_page,
    configure_tesseract,
    finalize_results_ocr,
    fix_ocr_li_confusion,
    fix_place_rank_ocr,
    norm_space,
    render_pdf_pages,
)

ROOT = Path(r"c:\Users\mw\OneDrive - timberwilde.net\repos\jrtca_results")
BASE = ROOT / "_ocr_baseline_v2" / "yearbook_1990_2001"

_PAGE_SPLIT = re.compile(r"(?m)^(---\s*page\s+(\d+)\s*---)\s*$")
_COL_LEFT = re.compile(r"(?m)^---\s*column\s+LEFT\s*---\s*$", re.I)
_COL_RIGHT = re.compile(r"(?m)^---\s*column\s+RIGHT\s*---\s*$", re.I)
_HEADER = re.compile(r"(?m)^---\s*HEADER\s*---\s*$", re.I)
_OWNED_TAIL = re.compile(
    r"(?im)^(.*\bowned\s+by\b[^\n]*?)"
    r"(?:&\s+[A-Z][A-Za-z']{0,2}|[A-Z][A-Za-z']+\s+[A-Z][A-Za-z']{0,1})"
    r"\s*$"
)


def split_hqmax_pages(text: str) -> tuple[str, list[tuple[int, str, str]]]:
    """Return (preamble, [(page_no, marker_line, body), ...])."""
    parts = _PAGE_SPLIT.split(text)
    if len(parts) == 1:
        return text, []
    preamble = parts[0]
    out: list[tuple[int, str, str]] = []
    # parts: pre, marker, num, body, marker, num, body...
    i = 1
    while i + 2 < len(parts):
        marker, num_s, body = parts[i], parts[i + 1], parts[i + 2]
        out.append((int(num_s), marker.strip(), body))
        i += 3
    return preamble, out


def split_columns(body: str) -> tuple[str, str, str, str]:
    """Return (before, left, right, join_style). before may include HEADER."""
    left_m = _COL_LEFT.search(body)
    right_m = _COL_RIGHT.search(body)
    if not left_m or not right_m or right_m.start() <= left_m.start():
        return body, body, "", "flat"
    before = body[: left_m.start()]
    left = body[left_m.end() : right_m.start()]
    right = body[right_m.end() :]
    return before, left, right, "cols"


def page_needs_c1(text: str) -> bool:
    lines = finalize_results_ocr(text).splitlines()
    return bool(_iter_class_header_gap_indices(lines))


def page_o6_lines(text: str) -> list[str]:
    hits = audit_results_ocr_page(finalize_results_ocr(text), max_samples=40)
    return [ln for code, ln in hits if code == "owner_tail_trunc"]


def recover_owner_tails(img: Image.Image, text: str) -> str:
    """Widen right edge for trunc owner lines; splice longer OCR when credible."""
    if not text or img is None:
        return text
    boxes = _ocr_column_line_boxes(img)
    if len(boxes) < 3:
        return text
    lines = text.splitlines()
    w, h = img.size
    changed = False
    for i, ln in enumerate(lines):
        s = ln.strip()
        if not _OWNED_TAIL.search(s) and "owned by" not in s.lower():
            continue
        # Only touch short tails / audit-like stubs
        if not re.search(
            r"(?i)owned\s+by\b.*(?:\s[A-Za-z]{1,3}|&\s+[A-Z][A-Za-z']{0,2})\s*$",
            s,
        ):
            continue
        # Match box
        bi = None
        keys = set(re.findall(r"[A-Za-z]{3,}", s.lower()))
        best = 0
        for j, (raw, y0, y1) in enumerate(boxes):
            ov = len(keys & set(re.findall(r"[A-Za-z]{3,}", raw.lower())))
            if ov > best:
                best, bi = ov, j
        if bi is None or best < 2:
            continue
        _raw, y0, y1 = boxes[bi]
        pad = max(2, (y1 - y0) // 4)
        # Right half / gutter-to-edge strip (owner often in right of column)
        x0 = max(0, int(w * 0.35))
        band = img.crop((x0, max(0, y0 - pad), w, min(h, y1 + pad)))
        try:
            raw = _tesseract_string(band, 7)
        except Exception:
            continue
        flat = norm_space(fix_ocr_li_confusion(fix_place_rank_ocr(raw)))
        m = re.search(r"(?i)\bowned\s+by\b\s+(.+)$", flat)
        if not m:
            continue
        new_owner = m.group(1).strip().rstrip(" .,;:")
        old_m = re.search(r"(?i)\bowned\s+by\b\s+(.+)$", s)
        if not old_m:
            continue
        old_owner = old_m.group(1).strip()
        if len(new_owner) <= len(old_owner) + 1:
            continue
        # Require shared prefix token to avoid wild swaps
        ot = re.findall(r"[A-Za-z]+", old_owner)
        nt = re.findall(r"[A-Za-z]+", new_owner)
        if ot and nt and ot[0].lower() != nt[0].lower():
            continue
        lines[i] = re.sub(
            r"(?i)(\bowned\s+by\b\s+).+$",
            r"\1" + new_owner,
            s,
        )
        changed = True
    return "\n".join(lines) if changed else text


def recover_page(
    img: Image.Image, body: str, *, do_c1: bool, do_o6: bool
) -> tuple[str, dict]:
    stats = {"c1": False, "o6": False}
    before, left, right, style = split_columns(body)
    if style == "cols":
        cut = _two_column_cut_x(img)
        w, h = img.size
        if cut is None:
            cut = w // 2
        gap = _column_gutter_gap(w)
        left_im = img.crop((0, 0, max(1, cut - gap), h))
        right_im = img.crop((min(w - 1, cut + gap), 0, w, h))
        if do_c1 and page_needs_c1(left):
            new_l = _fill_missing_class_titles(left_im, left)
            if new_l != left:
                left, stats["c1"] = new_l, True
        if do_c1 and page_needs_c1(right):
            new_r = _fill_missing_class_titles(right_im, right)
            if new_r != right:
                right, stats["c1"] = new_r, True
        if do_o6:
            if page_o6_lines(left):
                new_l = recover_owner_tails(left_im, left)
                if new_l != left:
                    left, stats["o6"] = new_l, True
            if page_o6_lines(right):
                new_r = recover_owner_tails(right_im, right)
                if new_r != right:
                    right, stats["o6"] = new_r, True
        body = (
            before
            + "--- column LEFT ---\n"
            + left.lstrip("\n")
            + "--- column RIGHT ---\n"
            + right.lstrip("\n")
        )
    else:
        if do_c1 and page_needs_c1(body):
            new_b = _fill_missing_class_titles(img, body)
            if new_b != body:
                body, stats["c1"] = new_b, True
        if do_o6 and page_o6_lines(body):
            new_b = recover_owner_tails(img, body)
            if new_b != body:
                body, stats["o6"] = new_b, True
    return body, stats


def meta_pdf(hq: Path) -> Path | None:
    # ``foo_ocr_hqmax.txt`` → ``foo_ocr_hqmax.meta.txt``
    meta = hq.with_suffix(".meta.txt")
    if not meta.is_file():
        return None
    for ln in meta.read_text(encoding="utf-8", errors="replace").splitlines():
        if ln.startswith("source="):
            p = Path(ln.split("=", 1)[1].strip())
            return p if p.is_file() else None
    return None


def pages_needing_c1_o6(
    hq: Path,
    *,
    do_c1: bool,
    do_o6: bool,
    limit_pages: int | None,
) -> tuple[set[int], set[int]]:
    """Return (c1_pages, o6_pages) still needing recovery in ``hq``."""
    if not hq.is_file():
        return set(), set()
    raw = hq.read_text(encoding="utf-8", errors="replace")
    _preamble, pages = split_hqmax_pages(raw)
    c1_need: set[int] = set()
    o6_need: set[int] = set()
    for num, _mk, body in pages:
        if do_c1 and page_needs_c1(body):
            c1_need.add(num)
        if do_o6 and page_o6_lines(body):
            o6_need.add(num)
    if limit_pages is not None:
        # Cap applies to union order, then re-filter membership
        union = sorted(c1_need | o6_need)[:limit_pages]
        keep = set(union)
        c1_need &= keep
        o6_need &= keep
    return c1_need, o6_need


def pages_needing_work(
    hq: Path,
    *,
    do_c1: bool,
    do_o6: bool,
    limit_pages: int | None,
) -> set[int]:
    """Page numbers in ``hq`` that still need C1 and/or O6 recovery."""
    c1_need, o6_need = pages_needing_c1_o6(
        hq, do_c1=do_c1, do_o6=do_o6, limit_pages=limit_pages
    )
    return c1_need | o6_need


def _emit_progress(progress: dict) -> None:
    c1_todo = int(progress.get("c1_todo") or 0)
    o6_todo = int(progress.get("o6_todo") or 0)
    c1_done = int(progress.get("c1_done") or 0)
    o6_done = int(progress.get("o6_done") or 0)
    pages_todo = int(progress.get("pages_todo") or 0)
    pages_done = int(progress.get("done") or 0)
    print(
        f"PROGRESS pages_done={pages_done} pages_todo={pages_todo} "
        f"pages_left={max(0, pages_todo - pages_done)} "
        f"c1_done={c1_done} c1_todo={c1_todo} "
        f"o6_done={o6_done} o6_todo={o6_todo}",
        flush=True,
    )


def process_hq(
    hq: Path,
    *,
    do_c1: bool,
    do_o6: bool,
    limit_pages: int | None,
    scale: float,
    progress: dict,
) -> dict:
    pdf = meta_pdf(hq)
    if not pdf:
        print(f"  SKIP no PDF meta: {hq.name}", flush=True)
        return {"file": hq.name, "skipped": True}
    raw = hq.read_text(encoding="utf-8", errors="replace")
    preamble, pages = split_hqmax_pages(raw)
    if not pages:
        print(f"  SKIP no page markers: {hq.name}", flush=True)
        return {"file": hq.name, "skipped": True}

    c1_need, o6_need = pages_needing_c1_o6(
        hq, do_c1=do_c1, do_o6=do_o6, limit_pages=limit_pages
    )
    need = c1_need | o6_need
    if not need:
        print(f"  OK no C1/O6 pages: {hq.name}", flush=True)
        return {"file": hq.name, "need": 0, "c1": 0, "o6": 0}

    pages_todo = int(progress.get("pages_todo") or 0)
    print(
        f"  {hq.name}: recover pages {sorted(need)[:12]}"
        f"{'…' if len(need) > 12 else ''} ({len(need)}) "
        f"c1={len(c1_need)} o6={len(o6_need)}",
        flush=True,
    )
    by_num = {n: (mk, body) for n, mk, body in pages}
    c1_n = o6_n = 0
    # Render only needed pages — render_pdf_pages yields all; skip early
    max_page = max(need)
    for pno, img in render_pdf_pages(str(pdf), max_pages=max_page, scale=scale):
        if pno not in need:
            continue
        mk, body = by_num[pno]
        new_body, st = recover_page(img, body, do_c1=do_c1, do_o6=do_o6)
        progress["done"] = int(progress.get("done") or 0) + 1
        if pno in c1_need:
            progress["c1_done"] = int(progress.get("c1_done") or 0) + 1
        if pno in o6_need:
            progress["o6_done"] = int(progress.get("o6_done") or 0) + 1
        done = progress["done"]
        left = max(0, pages_todo - done)
        c1_done = int(progress.get("c1_done") or 0)
        o6_done = int(progress.get("o6_done") or 0)
        c1_todo = int(progress.get("c1_todo") or 0)
        o6_todo = int(progress.get("o6_todo") or 0)
        ts = _local_ts()
        if st["c1"] or st["o6"]:
            by_num[pno] = (mk, new_body)
            c1_n += int(st["c1"])
            o6_n += int(st["o6"])
        # Always log attempt so dashboard progress advances
        print(
            f"    [{ts}] page {pno}: c1={st['c1']} o6={st['o6']} "
            f"done={done}/{pages_todo} left={left} "
            f"C1={c1_done}/{c1_todo} O6={o6_done}/{o6_todo}",
            flush=True,
        )
        _emit_progress(progress)

    # Rebuild
    chunks = [preamble.rstrip() + "\n\n"] if preamble.strip() else []
    for num, mk, _body in pages:
        mk2, body2 = by_num[num]
        chunks.append(f"{mk2}\n{body2.lstrip('\n')}")
        if not body2.endswith("\n"):
            chunks.append("\n")
    new_text = "".join(chunks)
    if new_text != raw:
        bak = hq.with_suffix(hq.suffix + ".pre_c1o6")
        if not bak.is_file():
            shutil.copy2(hq, bak)
        hq.write_text(new_text, encoding="utf-8")
    return {
        "file": hq.name,
        "need": len(need),
        "c1": c1_n,
        "o6": o6_n,
        "wrote": new_text != raw,
    }


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--years", type=int, nargs="+", default=[1997, 1998])
    ap.add_argument("--limit-pages", type=int, default=None, help="Cap pages per PDF")
    ap.add_argument("--scale", type=float, default=2.5)
    ap.add_argument("--no-c1", action="store_true")
    ap.add_argument("--no-o6", action="store_true")
    args = ap.parse_args()
    print(
        f"START recover years={' '.join(str(y) for y in args.years)} "
        f"scale={args.scale} ts={_local_ts()}",
        flush=True,
    )
    configure_tesseract()
    do_c1, do_o6 = not args.no_c1, not args.no_o6

    # Preflight: total pages still needing C1/O6 across selected years
    work: list[tuple[int, Path, int, int, int]] = []
    for year in args.years:
        ydir = BASE / str(year)
        if not ydir.is_dir():
            print(f"y={year} missing dir", flush=True)
            continue
        hq_files = sorted(ydir.rglob("*_ocr_hqmax.txt"))
        print(f"PREFLIGHT y={year} scanning {len(hq_files)} hqmax…", flush=True)
        for hq in hq_files:
            c1_need, o6_need = pages_needing_c1_o6(
                hq, do_c1=do_c1, do_o6=do_o6, limit_pages=args.limit_pages
            )
            n = len(c1_need | o6_need)
            if n:
                work.append((year, hq, n, len(c1_need), len(o6_need)))
                print(
                    f"  queue {hq.name}: pages={n} c1={len(c1_need)} o6={len(o6_need)}",
                    flush=True,
                )
    pages_todo = sum(n for _y, _h, n, _c, _o in work)
    c1_todo = sum(c for _y, _h, _n, c, _o in work)
    o6_todo = sum(o for _y, _h, _n, _c, o in work)
    print(
        f"PLAN pages_todo={pages_todo} c1_todo={c1_todo} o6_todo={o6_todo} "
        f"files_with_work={len(work)} "
        f"years={' '.join(str(y) for y in args.years)}",
        flush=True,
    )
    # Snapshot so dashboard can show 0/x before first page
    print(
        f"PROGRESS pages_done=0 pages_todo={pages_todo} pages_left={pages_todo} "
        f"c1_done=0 c1_todo={c1_todo} o6_done=0 o6_todo={o6_todo}",
        flush=True,
    )

    totals = {"c1": 0, "o6": 0, "files": 0}
    progress = {
        "done": 0,
        "pages_todo": pages_todo,
        "c1_todo": c1_todo,
        "o6_todo": o6_todo,
        "c1_done": 0,
        "o6_done": 0,
    }
    last_year: int | None = None
    for year, hq, _n, _c, _o in work:
        if year != last_year:
            print(
                f"=== y={year} files={sum(1 for y, _h, _n, _c, _o in work if y == year)} ===",
                flush=True,
            )
            last_year = year
        r = process_hq(
            hq,
            do_c1=do_c1,
            do_o6=do_o6,
            limit_pages=args.limit_pages,
            scale=args.scale,
            progress=progress,
        )
        if r.get("skipped"):
            continue
        totals["files"] += 1
        totals["c1"] += int(r.get("c1") or 0)
        totals["o6"] += int(r.get("o6") or 0)
    print(
        f"DONE files={totals['files']} pages_c1_fixed={totals['c1']} "
        f"pages_o6_fixed={totals['o6']} pages_todo={pages_todo} "
        f"pages_done={progress['done']} "
        f"c1_done={progress['c1_done']}/{c1_todo} "
        f"o6_done={progress['o6_done']}/{o6_todo}",
        flush=True,
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
