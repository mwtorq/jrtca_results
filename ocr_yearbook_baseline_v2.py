#!/usr/bin/env python3
"""HQ OCR 1990-2001 Yearbook Scans PDFs into _ocr_baseline_v2.

Writes ONLY under ``_ocr_baseline_v2/`` — never overwrites scan-folder sidecars.
Canonical CLI for plan steps A1/A4 (use this, not ``_ocr_baseline_v2_yearbook_9701``).

Default: two parallel year tracks (separate processes, each with 10 tess workers):
  Track A: 1997
  Track B: 1998

1990–96 / 1999–2001 tracks are parked (laptop thrash at 4×10). Re-add when ready.
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
OUT_ROOT = ROOT / "_ocr_baseline_v2" / "yearbook_1990_2001"
YEARS = range(1990, 2002)

# Parallel year tracks (sequential years within each track)
TRACKS: list[tuple[str, list[int]]] = [
    ("trackA", [1997]),
    ("trackB", [1998]),
]


def prefer_pdfs(folder: Path) -> list[Path]:
    """Prefer full volume PDFs; skip obvious trunc/dup when full exists."""
    pdfs = sorted(folder.glob("*.pdf"))
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
        out.append(p)
    return out


def out_path_for(pdf: Path, year: int) -> Path:
    # Yearbook Scans\1997 Vol I\file.pdf -> yearbook_1990_2001\1997\1997_Vol_I\file_ocr_hqmax.txt
    rel_parent = pdf.parent.name
    safe = re.sub(r"[^\w\-]+", "_", rel_parent).strip("_")
    dest_dir = OUT_ROOT / str(year) / safe
    dest_dir.mkdir(parents=True, exist_ok=True)
    return dest_dir / (pdf.stem + "_ocr_hqmax.txt")


def queue(years: list[int] | None = None) -> list[tuple[int, Path, Path]]:
    """Build PDF jobs. If years given, keep that year order (track order)."""
    year_list = list(years) if years is not None else list(YEARS)
    items: list[tuple[int, Path, Path]] = []
    for year in year_list:
        for folder in sorted(YB.iterdir()):
            if not folder.is_dir():
                continue
            if not folder.name.startswith(str(year)):
                continue
            for pdf in prefer_pdfs(folder):
                items.append((year, pdf, out_path_for(pdf, year)))
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

    # Default: four parallel tracks, each with its own 10-worker tess pool
    procs: list[tuple[str, subprocess.Popen]] = []
    for label, years in TRACKS:
        log_path = ROOT / f"_ocr_9701_{label}.log"
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
        "baseline_v2 parallel tracks:\n"
        + "\n".join(f"  {lab}: {yrs}" for lab, yrs in TRACKS)
        + f"\n(each workers={args.workers}, ~{args.workers * len(TRACKS)} tess max)",
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
        "  logs: " + ", ".join(f"_ocr_9701_{lab}.log" for lab, _ in TRACKS),
        flush=True,
    )
    return 0 if all(c == 0 for c in exits.values()) else 1


if __name__ == "__main__":
    raise SystemExit(main())
