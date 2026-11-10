#!/usr/bin/env python3
"""HQ OCR 1990-2001 Yearbook Scans PDFs into _ocr_baseline_v2.

Writes ONLY under ``_ocr_baseline_v2/`` — never overwrites scan-folder sidecars.
Canonical CLI for plan steps A1/A4 (use this, not ``_ocr_baseline_v2_yearbook_9701``).

Default: two parallel year tracks (separate processes, each with 10 tess workers):
  Track A: 1999, 2001
  Track B: 2000

1997–98 baseline complete; 1990–96 parked (laptop thrash at 4×10).
"""
from __future__ import annotations

import argparse
import os
import re
import subprocess
import sys
from pathlib import Path

ROOT = Path(r"c:\Users\mw\OneDrive - timberwilde.net\repos\jrtca_results")
YB = ROOT / "Yearbook Scans"
UPDATED = ROOT / "Updated Yearbook Scans"
OUT_ROOT = ROOT / "_ocr_baseline_v2" / "yearbook_1990_2001"
YEARS = range(1990, 2002)

# Parallel year tracks (sequential years within each track)
TRACKS: list[tuple[str, list[int]]] = [
    ("trackA", [1999, 2001]),
    ("trackB", [2000]),
]
# A4 — 1990–96 yearbook (Updated Yearbook Scans is the real PDF source)
TRACKS_A4: list[tuple[str, list[int]]] = [
    ("trackA", [1990, 1992, 1994, 1996]),
    ("trackB", [1991, 1993, 1995]),
]
# A5 — early / non-yearbook packs under Updated (1984–90)
TRACKS_A5: list[tuple[str, list[int]]] = [
    ("trackA", [1984, 1986, 1988, 1990]),
    ("trackB", [1985, 1987, 1989]),
]


def prefer_pdfs(folder: Path) -> list[Path]:
    """Prefer full volume PDFs; skip obvious trunc/dup when full exists."""
    pdfs = sorted(folder.glob("*.pdf"))

    def _is_page_leaf(name: str) -> bool:
        low = name.lower()
        return bool(
            re.search(r"\bpg\.?\s*\d", low)
            or re.search(r"\bpages?\s+\d", low)
            or re.match(r"^\d{4}-\d{2}-\d{2}_\d+", low)  # camera burst leaves
        )

    def _is_fullish(q: Path) -> bool:
        low = q.name.lower()
        if _is_page_leaf(q.name) or "trunc" in low or "even only" in low:
            return False
        if low.startswith("docscan"):
            return False
        # Updated Yearbook Scans: large Document_*.pdf / scan.pdf volumes
        if low.startswith("document") or q.stem.lower() in {"scan", "jrtca national"}:
            return True
        if re.search(r"\bvol\b", low):
            return True
        try:
            return q.stat().st_size >= 8_000_000
        except OSError:
            return False

    has_full = any(_is_fullish(q) for q in pdfs)
    stems = {q.stem.lower() for q in pdfs}
    out = []
    for p in pdfs:
        low = p.name.lower()
        # skip trunc if non-trunc sibling exists
        if "trunc" in low:
            if any(
                "trunc" not in q.name.lower()
                and re.sub(r"\s*trunc", "", q.stem, flags=re.I).lower()
                == re.sub(r"\s*trunc", "", p.stem, flags=re.I).lower()
                for q in pdfs
            ):
                continue
        # skip "even only" if full pt exists
        if "even only" in low:
            continue
        # skip DocScan
        if low.startswith("docscan"):
            continue
        # skip .pre_rotate when base PDF exists
        if low.endswith(".pre_rotate.pdf") or p.stem.lower().endswith(".pre_rotate"):
            base = re.sub(r"\.pre_rotate$", "", p.stem, flags=re.I)
            if base.lower() in stems:
                continue
        # skip page extracts / burst leaves when a full volume sibling exists
        if _is_page_leaf(p.name) and has_full:
            continue
        out.append(p)
    return out


def out_path_for(pdf: Path, year: int) -> Path:
    # Yearbook Scans\1997 Vol I\file.pdf -> yearbook_1990_2001\1997\1997_Vol_I\file_ocr_hqmax.txt
    rel_parent = pdf.parent.name
    safe = re.sub(r"[^\w\-]+", "_", rel_parent).strip("_")
    dest_dir = OUT_ROOT / str(year) / safe
    dest_dir.mkdir(parents=True, exist_ok=True)
    return dest_dir / (pdf.stem + "_ocr_hqmax.txt")


def _folders_for_year(year: int) -> list[Path]:
    """Yearbook Scans + Updated Yearbook Scans folders whose names start with year.

    1990–96 remediation PDFs mostly live under Updated (``{year} Yearbook Vol N``).
    Yearbook Scans 1990–95 Vol II folders are often empty stubs.
    Early packs: Updated ``1984 & 1985``, ``1986``, … plus Yearbook Scans ``1984`` etc.
    """
    folders: list[Path] = []
    for root in (YB, UPDATED):
        if not root.is_dir():
            continue
        for folder in sorted(root.iterdir()):
            if not folder.is_dir():
                continue
            name = folder.name
            low = name.lower()
            if "entries catalog" in low:
                continue
            # Exact / prefix year match: "1990 Vol II", "1990 Yearbook Vol 1", "1986"
            if name.startswith(str(year)):
                folders.append(folder)
                continue
            # Combined early pack folder "1984 & 1985" — attach once under 1984
            if year == 1984 and name.startswith("1984") and "1985" in name:
                folders.append(folder)
    return folders


def queue(years: list[int] | None = None) -> list[tuple[int, Path, Path]]:
    """Build PDF jobs. If years given, keep that year order (track order)."""
    year_list = list(years) if years is not None else list(YEARS)
    items: list[tuple[int, Path, Path]] = []
    seen_dest: set[Path] = set()
    for year in year_list:
        for folder in _folders_for_year(year):
            for pdf in prefer_pdfs(folder):
                dest = out_path_for(pdf, year)
                if dest in seen_dest:
                    continue
                seen_dest.add(dest)
                items.append((year, pdf, dest))
    return items


def run_items(
    items: list[tuple[int, Path, Path]],
    *,
    force: bool,
    label: str,
) -> tuple[int, int, int]:
    """OCR a job list sequentially (page/in-page parallelism lives inside ocr_pdf_hq)."""
    # Import here so child processes pick up env workers before yearbook_ocr loads.
    from yearbook_ocr import ocr_pdf_hq

    ok = skip = fail = 0
    n = len(items)
    print(
        f"[{label}] start jobs={n} workers={os.environ.get('JRTCA_OCR_WORKERS', '?')} "
        f"page_workers={os.environ.get('JRTCA_OCR_PAGE_WORKERS', '?')}",
        flush=True,
    )
    for i, (year, pdf, dest) in enumerate(items, 1):
        if dest.is_file() and dest.stat().st_size > 500 and not force:
            print(f"[{label}] SKIP {i}/{n} {pdf.relative_to(ROOT)}", flush=True)
            skip += 1
            continue
        print(
            f"[{label}] OCR {i}/{n} y={year} {pdf.relative_to(ROOT)} -> {dest.relative_to(ROOT)}",
            flush=True,
        )
        try:
            text, y = ocr_pdf_hq(pdf, force=True, dest_path=dest)
            dest.with_suffix(".meta.txt").write_text(
                f"source={pdf}\nyear_guess={y}\nchars={len(text or '')}\n"
                f"structure=header+two_column\nfont_hint=Helvetica\n"
                f"track={label}\n",
                encoding="utf-8",
            )
            print(f"[{label}]   year_guess={y} chars={len(text or '')}", flush=True)
            ok += 1
        except Exception as e:
            print(f"[{label}]   FAIL {e}", flush=True)
            fail += 1
    print(f"[{label}] DONE ok={ok} skip={skip} fail={fail}", flush=True)
    return ok, skip, fail


def _spawn_track(
    years: list[int],
    *,
    force: bool,
    label: str,
    workers: int,
    page_workers: int,
    log_path: Path,
) -> subprocess.Popen:
    """Launch one year-track as its own process (own 10 tess worker pool)."""
    py = sys.executable
    script = str(Path(__file__).resolve())
    year_args = []
    for y in years:
        year_args.extend(["--track-year", str(y)])
    cmd = [
        py,
        "-u",
        script,
        "--track-worker",
        "--track-label",
        label,
        *year_args,
    ]
    if force:
        cmd.append("--force")
    env = os.environ.copy()
    env["JRTCA_OCR_WORKERS"] = str(workers)
    env["JRTCA_OCR_PAGE_WORKERS"] = str(page_workers)
    log_path.parent.mkdir(parents=True, exist_ok=True)
    logf = open(log_path, "w", encoding="utf-8")
    print(
        f"SPAWN {label} years={years} workers={workers} page_workers={page_workers} log={log_path.name}",
        flush=True,
    )
    return subprocess.Popen(
        cmd,
        cwd=str(ROOT),
        env=env,
        stdout=logf,
        stderr=subprocess.STDOUT,
        stdin=subprocess.DEVNULL,
    )


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--limit", type=int, default=None)
    ap.add_argument("--year", type=int, default=None, help="Single year only (no dual tracks)")
    ap.add_argument("--force", action="store_true")
    ap.add_argument(
        "--no-tracks",
        action="store_true",
        help="Single process, years 1997-2001 in order (legacy)",
    )
    ap.add_argument(
        "--workers",
        type=int,
        default=10,
        help="Tesseract workers per track process (default 10)",
    )
    ap.add_argument(
        "--page-workers",
        type=int,
        default=2,
        help="Parallel pages inside each PDF (default 2)",
    )
    ap.add_argument(
        "--phase",
        choices=("a1", "a4", "a5"),
        default="a1",
        help="Track set: a1=1999–2001 remnant, a4=1990–96 yearbook, a5=1984–90 early",
    )
    # Internal: child track worker
    ap.add_argument("--track-worker", action="store_true", help=argparse.SUPPRESS)
    ap.add_argument("--track-label", default="track", help=argparse.SUPPRESS)
    ap.add_argument(
        "--track-year",
        action="append",
        type=int,
        dest="track_years",
        default=None,
        help=argparse.SUPPRESS,
    )
    args = ap.parse_args()

    phase_tracks = {
        "a1": TRACKS,
        "a4": TRACKS_A4,
        "a5": TRACKS_A5,
    }
    active_tracks = phase_tracks[args.phase]
    log_prefix = {"a1": "_ocr_9701", "a4": "_ocr_a4", "a5": "_ocr_a5"}[args.phase]

    # Child process: run one track's years sequentially
    if args.track_worker:
        years = args.track_years or list(YEARS)
        items = queue(years)
        if args.limit:
            items = items[: args.limit]
        ok, skip, fail = run_items(items, force=args.force, label=args.track_label)
        return 0 if fail == 0 else 1

    # Single year or legacy single-process mode
    if args.year is not None or args.no_tracks:
        os.environ.setdefault("JRTCA_OCR_WORKERS", str(args.workers))
        os.environ.setdefault("JRTCA_OCR_PAGE_WORKERS", str(args.page_workers))
        items = queue([args.year] if args.year is not None else None)
        if args.limit:
            items = items[: args.limit]
        print(f"baseline_v2 OCR queue={len(items)} (single process)", flush=True)
        ok, skip, fail = run_items(items, force=args.force, label="main")
        print(f"DONE ok={ok} skip={skip} fail={fail}", flush=True)
        return 0 if fail == 0 else 1

    # Default: parallel tracks, each with its own tess worker pool
    procs: list[tuple[str, subprocess.Popen]] = []
    for label, years in active_tracks:
        log_path = ROOT / f"{log_prefix}_{label}.log"
        procs.append(
            (
                label,
                _spawn_track(
                    years,
                    force=args.force,
                    label=label,
                    workers=args.workers,
                    page_workers=args.page_workers,
                    log_path=log_path,
                ),
            )
        )
    print(
        f"baseline_v2 phase={args.phase} parallel tracks:\n"
        + "\n".join(f"  {lab}: {yrs}" for lab, yrs in active_tracks)
        + f"\n(each workers={args.workers}, ~{args.workers * len(active_tracks)} tess max)",
        flush=True,
    )
    exits: dict[str, int] = {}
    for label, proc in procs:
        exits[label] = proc.wait()
    print(
        "TRACKS DONE "
        + " ".join(f"{lab}_exit={code}" for lab, code in exits.items()),
        flush=True,
    )
    print(
        "  logs: " + ", ".join(f"{log_prefix}_{lab}.log" for lab, _ in active_tracks),
        flush=True,
    )
    return 0 if all(c == 0 for c in exits.values()) else 1


if __name__ == "__main__":
    raise SystemExit(main())
