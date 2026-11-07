#!/usr/bin/env python3
"""Detect sideways yearbook PDF pages via Tesseract OSD and rewrite upright PDFs.

Keeps a .pre_rotate.pdf backup next to the original on first fix.
Rotate value from OSD is degrees CW to apply to make text upright.
"""
from __future__ import annotations

import argparse
import os
import re
import shutil
import sys
from pathlib import Path

import fitz  # PyMuPDF
import pytesseract
from PIL import Image

from ocr_yearbook_source import TESSERACT_EXE, configure_tesseract

ROOT = Path(r"c:\Users\mw\OneDrive - timberwilde.net\repos\jrtca_results")
DEFAULT_DIRS = [
    ROOT / "Updated Yearbook Scans",
    ROOT / "Yearbook Scans",
]

# Skip known non-yearbook dumps / catalogs unless explicitly passed
SKIP_NAME_FRAGMENTS = (
    "national entries catalog",
    "yearbook scans - ",
)


def page_osd_rotate(pil_img: Image.Image) -> tuple[int, float]:
    """Return (rotate_degrees_cw, confidence). 0 means already upright."""
    configure_tesseract()
    # Downscale for speed if huge
    img = pil_img
    w, h = img.size
    max_side = max(w, h)
    if max_side > 1800:
        scale = 1800 / max_side
        img = img.resize((int(w * scale), int(h * scale)), Image.Resampling.BILINEAR)
    try:
        osd = pytesseract.image_to_osd(img)
    except Exception:
        return 0, 0.0
    rot_m = re.search(r"Rotate:\s*(\d+)", osd)
    conf_m = re.search(r"Orientation confidence:\s*([0-9.]+)", osd)
    rot = int(rot_m.group(1)) if rot_m else 0
    conf = float(conf_m.group(1)) if conf_m else 0.0
    if rot % 360 == 0:
        return 0, conf
    return rot % 360, conf


def render_page_pil(doc: fitz.Document, page_index: int, scale: float = 1.2) -> Image.Image:
    page = doc[page_index]
    mat = fitz.Matrix(scale, scale)
    pix = page.get_pixmap(matrix=mat, alpha=False)
    return Image.frombytes("RGB", (pix.width, pix.height), pix.samples)


def analyze_pdf(path: Path, max_pages: int | None = None, min_conf: float = 2.0):
    """Return list of (page_index_0based, rotate_cw, conf) for every page.

    Rotation is decided per page by OSD; callers may majority-vote and apply
    one rotation to all pages (--uniform).
    """
    doc = fitz.open(path)
    n = len(doc)
    limit = n if max_pages is None else min(n, max_pages)
    needs = []
    for i in range(limit):
        img = render_page_pil(doc, i)
        rot, conf = page_osd_rotate(img)
        needs.append((i, rot % 360, conf))
    # If PDF has more pages than sampled, extend majority later in main
    doc.close()
    return needs, n


def majority_rotation(page_results: list[tuple[int, int, float]], min_conf: float) -> int | None:
    """Pick dominant non-zero CW rotation among confident pages; else among all."""
    from collections import Counter

    confident = [(r, c) for _, r, c in page_results if r and c >= min_conf]
    pool = confident if confident else [(r, c) for _, r, c in page_results if r]
    if not pool:
        return None
    # weight by confidence
    scores: dict[int, float] = {}
    for r, c in pool:
        scores[r] = scores.get(r, 0.0) + max(c, 0.1)
    best = max(scores.items(), key=lambda kv: kv[1])
    return best[0]


def apply_rotations(path: Path, rotations: dict[int, int], backup: bool = True) -> Path:
    """Apply CW rotations to pages; write upright PDF. Returns output path."""
    doc = fitz.open(path)
    for i, rot in rotations.items():
        if not rot:
            continue
        page = doc[i]
        # PyMuPDF set_rotation is absolute page rotation in PDF (0/90/180/270)
        cur = page.rotation
        page.set_rotation((cur + rot) % 360)
    out = path.with_name(path.stem + "_upright.pdf")
    # If already processing an upright file, overwrite target as original name after backup
    if backup and not path.name.endswith(".pre_rotate.pdf"):
        bak = path.with_name(path.stem + ".pre_rotate.pdf")
        if not bak.exists():
            shutil.copy2(path, bak)
    doc.save(out, garbage=3, deflate=True)
    doc.close()
    # Replace original with upright (keep .pre_rotate.pdf backup)
    if path.suffix.lower() == ".pdf" and not path.name.endswith("_upright.pdf"):
        shutil.move(str(out), str(path))
        return path
    return out


def iter_pdfs(roots: list[Path]):
    for root in roots:
        if not root.is_dir():
            continue
        for dp, dns, fns in os.walk(root):
            low = dp.lower()
            if any(s in low for s in SKIP_NAME_FRAGMENTS):
                dns[:] = []
                continue
            if "page redos" in low:
                continue
            for fn in fns:
                if not fn.lower().endswith(".pdf"):
                    continue
                if fn.endswith(".pre_rotate.pdf") or fn.endswith("_upright.pdf"):
                    continue
                if fn.endswith("_ocr.txt"):
                    continue
                yield Path(dp) / fn


def restore_pre_rotate_if_present(path: Path) -> Path:
    """If a prior partial rotate left .pre_rotate.pdf, restore it as the working source."""
    bak = path.with_name(path.stem + ".pre_rotate.pdf")
    if bak.is_file():
        shutil.copy2(bak, path)
        return path
    return path


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--roots", nargs="*", default=None, help="Root folders to scan")
    ap.add_argument("--apply", action="store_true", help="Write rotated PDFs")
    ap.add_argument("--min-conf", type=float, default=3.0)
    ap.add_argument("--force-low-conf", action="store_true")
    ap.add_argument(
        "--uniform",
        action="store_true",
        default=True,
        help="Apply majority rotation to EVERY page in the PDF (default)",
    )
    ap.add_argument("--no-uniform", action="store_true", help="Per-page rotate only")
    ap.add_argument(
        "--restore-backup",
        action="store_true",
        help="Restore from .pre_rotate.pdf before analyzing (undo partial rotates)",
    )
    ap.add_argument("--max-pages", type=int, default=None)
    ap.add_argument("--limit-pdfs", type=int, default=None)
    args = ap.parse_args(argv)
    uniform = not args.no_uniform

    if os.path.isfile(TESSERACT_EXE):
        configure_tesseract()

    roots = [Path(r) for r in args.roots] if args.roots else DEFAULT_DIRS
    pdfs = list(iter_pdfs(roots))
    if args.limit_pdfs:
        pdfs = pdfs[: args.limit_pdfs]

    print(
        f"pdfs={len(pdfs)} apply={args.apply} uniform={uniform} min_conf={args.min_conf}",
        flush=True,
    )
    report = []
    fixed = 0
    for i, path in enumerate(pdfs, 1):
        rel = path.relative_to(ROOT) if ROOT in path.parents or path.is_relative_to(ROOT) else path
        if args.restore_backup or args.apply:
            restore_pre_rotate_if_present(path)
        try:
            needs, page_count = analyze_pdf(
                path, max_pages=args.max_pages, min_conf=0.0
            )
        except Exception as e:
            print(f"ERR {rel}: {e}", flush=True)
            continue

        apply_map: dict[int, int] = {}
        if uniform:
            maj = majority_rotation(needs, args.min_conf)
            if maj is None and args.force_low_conf:
                maj = majority_rotation(needs, 0.0)
            if maj:
                # Apply same rotation to every page in the PDF
                apply_map = {p: maj for p in range(page_count)}
                print(
                    f"[{i}/{len(pdfs)}] {rel}: UNIFORM rotate all {page_count} pages -> {maj}°",
                    flush=True,
                )
            else:
                print(f"[{i}/{len(pdfs)}] {rel}: no rotation consensus (upright)", flush=True)
            for page_i, rot, conf in needs:
                report.append((str(rel), page_i + 1, maj or 0, conf, bool(maj)))
        else:
            for page_i, rot, conf in needs:
                use = bool(rot) and (
                    conf >= args.min_conf or (args.force_low_conf and rot)
                )
                if use:
                    apply_map[page_i] = rot
                report.append((str(rel), page_i + 1, rot, conf, use))
            if apply_map:
                print(
                    f"[{i}/{len(pdfs)}] {rel}: rotate pages "
                    + ", ".join(
                        f"p{p+1}->{r}°"
                        for p, r, c in needs
                        if p in apply_map
                    ),
                    flush=True,
                )

        if apply_map and args.apply:
            # Backup original only if no pre_rotate yet (restore already copied backup->path)
            bak = path.with_name(path.stem + ".pre_rotate.pdf")
            if not bak.exists():
                shutil.copy2(path, bak)
            apply_rotations(path, apply_map, backup=False)
            fixed += 1

    to_fix = [r for r in report if r[4]]
    print(f"\npages_marked={len(to_fix)} pdfs_fixed={fixed}", flush=True)
    out_csv = ROOT / "_yearbook_reorient_report.csv"
    with open(out_csv, "w", encoding="utf-8") as f:
        f.write("rel_path,page,rotate_cw,confidence,applied\n")
        for rel, pg, rot, conf, applied in report:
            f.write(f"{rel},{pg},{rot},{conf:.3f},{int(applied)}\n")
    print(f"wrote {out_csv}", flush=True)
    return 0


if __name__ == "__main__":
    sys.exit(main())
