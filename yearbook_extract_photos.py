#!/usr/bin/env python3
"""Crop actual dog photographs from yearbook PDF pages into Yearbook Photos/.

Yearbook Photos is the TARGET folder. Full-page scan images are NOT saved as
photos — only rectangular photo regions cropped from within pages (or small
embedded images that are clearly not full-page).
"""
from __future__ import annotations

import argparse
import hashlib
import os
import re
import shutil
from io import BytesIO
from pathlib import Path

import fitz
import numpy as np
from PIL import Image
from scipy import ndimage

from ocr_yearbook_source import folder_year_hint
from yearbook_ocr import fix_ocr_li_confusion, norm_space

ROOT = Path(r"c:\Users\mw\OneDrive - timberwilde.net\repos\jrtca_results")
UPDATED = ROOT / "Updated Yearbook Scans"
SCANS = ROOT / "Yearbook Scans"
OUT = ROOT / "Yearbook Photos"

# "Name, owned by ..." (inline)
_OWNED_INLINE = re.compile(
    r"([A-Z][A-Za-z0-9' \-]{2,55}?),"
    r"?\s+owned(?:\s+and\s+(?:bred|handled))? by\s+",
    re.I,
)
# "Name\nOwned by ..." (caption under photo — common in conformation pages)
_OWNED_LINE = re.compile(
    r"(?im)^([A-Z][A-Za-z0-9'][A-Za-z0-9' \-]{2,60}?)\s*\r?\n\s*"
    r"Owned(?:\s+and\s+(?:bred|handled))? by\b"
)
_CAPTION = re.compile(
    r"(?m)^\s*([A-Z][A-Za-z0-9']+(?:\s+(?:of\s+)?[A-Z][A-Za-z0-9']+){1,5})\s*,\s+"
    r"(?:Mrs?\.?|Ms\.?|Miss|Dr\.?|M/?M|owned|[A-Z])"
)
_SAFE = re.compile(r"[^A-Za-z0-9' \-]+")
_BAD_DOG = re.compile(
    r"(?i)\b(board|committee|chairman|trial|page|true grit|certificate|"
    r"members|division|class|entries|entrants|director|welcome|"
    r"january|february|december|november|october|september|"
    r"road|street|far hills|bitch|dog|rough|smooth|puppy|"
    r"champion|reserve|conformation|yearbook|photos?)\b"
)


# Place-rank OCR junk glued onto the next dog ("Sths"/"Bths" ≈ 5ths, "ists" ≈ 1sts)
_PLACE_PREFIX = re.compile(
    r"(?i)^(?:\d{0,2}(?:sts?|nds?|rds?|ths)|sths|bths|bthe|bthre|ists|ards|brds)\s+"
)


def strip_place_rank_prefix(name: str) -> str:
    n = norm_space(name)
    while True:
        n2 = _PLACE_PREFIX.sub("", n).strip(" ,.-")
        if n2 == n:
            break
        n = n2
    return n


def safe_dog_folder(name: str) -> str:
    n = strip_place_rank_prefix(name)
    n = _SAFE.sub("", n).strip(" .-")
    n = re.sub(r"\s+", " ", n)
    return (n or "Unknown")[:80]


def _ok_dog(cand: str) -> bool:
    cand = strip_place_rank_prefix(cand)
    if len(cand) < 5 or len(cand) > 70:
        return False
    if _BAD_DOG.search(cand):
        return False
    # Orphan possessive after lost kennel: "s Tailor of Briarpatch" (was Maven's …)
    if re.match(r"(?i)^s\s+\S", cand):
        return False
    # Truncated "Name of" with no kennel after of
    if re.search(r"(?i)\bof\s*$", cand):
        return False
    # OCR junk tokens (digit-letter mash like x6eld) without a known repair
    if re.search(r"(?i)\d", cand) and not re.search(r"(?i)\b(of|and)\b", cand):
        if re.search(r"(?i)[a-z]+\d+[a-z]+|\d+[a-z]+\d*", cand):
            return False
    # Need at least two tokens for kennel/dog style names, or one long kennel word
    parts = cand.split()
    if len(parts) < 2 and len(cand) < 10:
        return False
    return True


def recover_possessive_dog_name(text: str, fragment: str) -> str | None:
    """If caption lost the kennel before 's, recover \"Kennel's Rest\" from page text."""
    frag = strip_place_rank_prefix(norm_space(fragment))
    if not re.match(r"(?i)^s\s+\S", frag):
        return None
    rest = frag[1:].strip()
    if len(rest) < 4:
        return None
    text = fix_ocr_li_confusion(text or "")
    m = re.search(
        rf"([A-Z][A-Za-z0-9\-]+)'s\s+{re.escape(rest)}",
        text,
        re.I,
    )
    if m:
        return norm_space(f"{m.group(1)}'s {rest}")
    first = re.escape(rest.split()[0])
    m = re.search(rf"([A-Z][A-Za-z0-9\-]+)'s\s+({first}[^\n,]{{0,50}})", text, re.I)
    if m:
        return norm_space(f"{m.group(1)}'s {m.group(2).strip()}")
    return None


_TRIAL_RESULT_NOISE = re.compile(
    r"(?i)\b(entries\s*:|^\s*\d+(st|nd|rd|ths?)\s*:|bitches,|dogs,|"
    r"class\s+\d|racing champions?|go-to-ground|championship certificate)\b"
)


def _polish_dog_label(cand: str) -> str:
    """Apply shared OCR name repairs used for folder labels."""
    try:
        from yearbook_cleanup_photo_names import polish_name, safe_folder

        return safe_folder(polish_name(cand))
    except Exception:
        return strip_place_rank_prefix(norm_space(cand))


def find_all_dog_captions(text: str) -> list[str]:
    """Photo captions only (Name + Owned-by), not trial-result placement lines."""
    text = fix_ocr_li_confusion(text or "")
    found: list[str] = []
    seen: set[str] = set()

    def add(cand: str) -> None:
        cand = strip_place_rank_prefix(norm_space(cand))
        if re.match(r"(?i)^s\s+\S", cand):
            recovered = recover_possessive_dog_name(text, cand)
            if recovered:
                cand = recovered
        cand = _polish_dog_label(cand)
        if not _ok_dog(cand):
            return
        key = cand.casefold()
        if key in seen:
            return
        seen.add(key)
        found.append(cand)

    # Conformation photo style: "Name\nOwned by ..." — prefer exclusively when present
    line_hits = list(_OWNED_LINE.finditer(text))
    for m in line_hits:
        add(m.group(1))
    if line_hits:
        return found

    # Fallback: inline captions, but skip trial-result list context
    for m in _OWNED_INLINE.finditer(text):
        window = text[max(0, m.start() - 80) : m.end() + 40]
        if _TRIAL_RESULT_NOISE.search(window):
            continue
        add(m.group(1))
    return found


def _is_photo_caption_block(raw: str) -> bool:
    lines = [ln for ln in raw.splitlines() if ln.strip()]
    if not lines or len(lines) > 6:
        return False
    if not re.search(r"(?i)\bowned\b", raw):
        return False
    if _TRIAL_RESULT_NOISE.search(raw):
        return False
    return True


def captions_with_y_from_page(page: fitz.Page, fallback_text: str) -> list[tuple[float, str]]:
    """Photo caption blocks only, top-to-bottom. Ignores trial-result owned-by lists."""
    positioned: list[tuple[float, str]] = []
    try:
        blocks = page.get_text("blocks") or []
    except Exception:
        blocks = []
    for b in blocks:
        if len(b) < 5 or b[6] != 0:
            continue
        raw = fix_ocr_li_confusion(b[4] or "")
        if not _is_photo_caption_block(raw):
            continue
        y = float(b[1])

        def _accept(cand: str) -> str | None:
            cand = strip_place_rank_prefix(cand)
            if re.match(r"(?i)^s\s+\S", cand):
                recovered = recover_possessive_dog_name(raw, cand)
                if recovered:
                    cand = recovered
            cand = _polish_dog_label(cand)
            return cand if _ok_dog(cand) else None

        m = _OWNED_LINE.search(raw)
        if m:
            cand = _accept(m.group(1))
            if cand:
                positioned.append((y, cand))
                continue
        lines = [ln.strip() for ln in raw.splitlines() if ln.strip()]
        for i, ln in enumerate(lines):
            if re.match(r"(?i)^owned(?:\s+and\s+(?:bred|handled))? by\b", ln) and i > 0:
                cand = _accept(lines[i - 1].rstrip(","))
                if cand:
                    positioned.append((y, cand))
                break
        else:
            m = _OWNED_INLINE.search(raw)
            if m:
                cand = _accept(m.group(1))
                if cand:
                    positioned.append((y, cand))
    if positioned:
        seen: set[str] = set()
        out: list[tuple[float, str]] = []
        for y, n in sorted(positioned, key=lambda t: t[0]):
            k = n.casefold()
            if k in seen:
                continue
            seen.add(k)
            out.append((y, n))
        return out
    return [(float(i), n) for i, n in enumerate(find_all_dog_captions(fallback_text))]


def assign_dogs_to_crops(
    crop_ys: list[float], captions: list[tuple[float, str]]
) -> list[str | None]:
    """Match each crop to a caption by vertical position/order.

    Same dog name may be assigned to multiple crops (a dog can appear twice).
    Different captions on one page must not all collapse to the first name.
    """
    n = len(crop_ys)
    if n == 0:
        return []
    if not captions:
        return [None] * n
    order = sorted(range(n), key=lambda i: crop_ys[i])
    caps = sorted(captions, key=lambda t: t[0])
    assigned: list[str | None] = [None] * n
    # Equal counts: zip top-to-bottom (handles 2-up pages with two different dogs)
    if len(caps) == n:
        for rank, ci in enumerate(order):
            assigned[ci] = caps[rank][1]
        return assigned
    # More captions than crops: each crop takes nearest caption; prefer unused first
    # so distinct dogs aren't skipped, but allow name reuse if captions repeat.
    used_cap: set[int] = set()
    for ci in order:
        cy = crop_ys[ci]
        best_j = None
        best_score = None
        # Pass 1: unused captions; Pass 2: any (same dog twice / leftover photo)
        for require_unused in (True, False):
            for j, (cap_y, _name) in enumerate(caps):
                if require_unused and j in used_cap:
                    continue
                dist = abs(cap_y - cy)
                below_bias = 0.0 if cap_y >= cy - 5 else 50.0
                score = dist + below_bias
                if best_score is None or score < best_score:
                    best_score = score
                    best_j = j
            if best_j is not None and (not require_unused or best_j not in used_cap):
                break
        if best_j is not None:
            used_cap.add(best_j)
            assigned[ci] = caps[best_j][1]
    return assigned


def load_ocr_pages(pdf_path: Path) -> dict[int, str]:
    stem = pdf_path.stem
    for c in (
        pdf_path.with_name(stem + "_ocr_hqmax.txt"),
        pdf_path.with_name(stem + "_ocr_hq.txt"),
        pdf_path.with_name(stem + "_ocr.txt"),
    ):
        if c.is_file() and c.stat().st_size > 50:
            text = c.read_text(encoding="utf-8", errors="ignore")
            break
    else:
        return {}
    pages: dict[int, str] = {}
    marks = list(re.finditer(r"(?im)^---\s*page\s+(\d+)\s*---\s*$", text))
    if not marks:
        return {1: text}
    for i, m in enumerate(marks):
        end = marks[i + 1].start() if i + 1 < len(marks) else len(text)
        pages[int(m.group(1))] = text[m.end() : end]
    return pages


def iter_yearbook_pdfs(years: range) -> list[tuple[int | None, Path]]:
    out = []
    for root in (UPDATED, SCANS):
        if not root.is_dir():
            continue
        for name in sorted(os.listdir(root)):
            if "entries catalog" in name.lower():
                continue
            d = root / name
            if not d.is_dir():
                continue
            y = folder_year_hint(name)
            if y is None or y not in years:
                continue
            if root == SCANS and y <= 1996:
                continue
            for fn in sorted(os.listdir(d)):
                if not fn.lower().endswith(".pdf"):
                    continue
                if fn.lower().endswith(".pre_rotate.pdf"):
                    continue
                if re.match(r"scan_\d+\.pdf$", fn, re.I):
                    continue
                out.append((y, d / fn))
    return out


def _region_looks_like_photo(gray_roi: np.ndarray) -> bool:
    """Reject text/page fragments; keep continuous midtone photo blocks."""
    if gray_roi.size < 400:
        return False
    g = gray_roi.astype(np.float32)
    h, w = g.shape
    white = float((g > 235).mean())
    mid = float(((g >= 40) & (g <= 210)).mean())
    std = float(g.std())
    # Text/ads on paper: lots of white, little photographic midtone
    if white > 0.55:
        return False
    if mid < 0.28:
        return False
    if std < 28:
        return False
    # Horizontal projection: text has strong row periodicity; photos are smoother
    row_ink = (g < 200).mean(axis=1)
    if len(row_ink) >= 20:
        # autocorrelation-ish: variance of differences — text lines pulse
        d = np.diff(row_ink)
        pulse = float(d.std())
        if pulse > 0.12 and white > 0.35:
            return False
    # Edge density via simple gradients — photos have 2D texture, not sparse ink
    gy, gx = np.gradient(g)
    edge = np.hypot(gx, gy)
    e_frac = float((edge > 18).mean())
    if e_frac < 0.04 or e_frac > 0.55:
        return False
    return True


def _find_photo_boxes(gray: np.ndarray) -> list[tuple[int, int, int, int]]:
    """Return (x0,y0,x1,y1) photo-like boxes in gray image coordinates."""
    h, w = gray.shape
    # Background ≈ paper white; keep darker / midtone content
    blur = ndimage.gaussian_filter(gray.astype(np.float32), 1.2)
    # Local variance — photos are textured 2D blocks; empty margins are flat
    win = 9
    mean = ndimage.uniform_filter(blur, win)
    mean2 = ndimage.uniform_filter(blur * blur, win)
    var = np.clip(mean2 - mean * mean, 0, None)
    # Content mask: not near-white OR high local variance
    mask = (blur < 245) & (var > 18)
    # Kill thin text: open then close
    mask = ndimage.binary_opening(mask, structure=np.ones((3, 3)))
    mask = ndimage.binary_closing(mask, structure=np.ones((15, 15)))
    mask = ndimage.binary_dilation(mask, structure=np.ones((7, 7)))
    labeled, nlab = ndimage.label(mask)
    if nlab == 0:
        return []
    boxes = []
    page_area = h * w
    for lab in range(1, nlab + 1):
        ys, xs = np.where(labeled == lab)
        if len(xs) < 500:
            continue
        x0, x1 = int(xs.min()), int(xs.max()) + 1
        y0, y1 = int(ys.min()), int(ys.max()) + 1
        bw, bh = x1 - x0, y1 - y0
        area = bw * bh
        fill = len(xs) / max(area, 1)
        # Reject full-page / near-full-page and tiny icons
        if area > 0.42 * page_area:
            continue
        if area < 0.012 * page_area:
            continue
        if bw < 0.12 * w or bh < 0.08 * h:
            continue
        ar = bw / max(bh, 1)
        if ar < 0.45 or ar > 2.4:
            continue
        # Photos are fairly filled rectangles; text columns are sparser after open
        if fill < 0.42:
            continue
        # Reject very tall thin text columns / half-page text blocks
        if bh > 0.50 * h and bw < 0.45 * w:
            continue
        if bh > 0.62 * h:
            continue
        region = gray[y0:y1, x0:x1]
        if not _region_looks_like_photo(region):
            continue
        boxes.append((x0, y0, x1, y1))
    # Prefer larger boxes; drop heavy overlaps (keep larger)
    boxes.sort(key=lambda b: (b[2] - b[0]) * (b[3] - b[1]), reverse=True)
    kept: list[tuple[int, int, int, int]] = []
    for b in boxes:
        x0, y0, x1, y1 = b
        area = (x1 - x0) * (y1 - y0)
        ok = True
        for kx0, ky0, kx1, ky1 in kept:
            ix0, iy0 = max(x0, kx0), max(y0, ky0)
            ix1, iy1 = min(x1, kx1), min(y1, ky1)
            if ix1 > ix0 and iy1 > iy0:
                inter = (ix1 - ix0) * (iy1 - iy0)
                if inter / area > 0.55:
                    ok = False
                    break
        if ok:
            kept.append(b)
    return kept[:8]


def _extend_box_for_caption(
    boxes: list[tuple[int, int, int, int]],
    caption_ys_small: list[float],
    page_h: int,
    page_w: int,
) -> list[tuple[int, int, int, int]]:
    """Grow each photo box downward to include its caption strip."""
    if not boxes:
        return []
    # Sort by y; each photo may extend down toward the next photo (or page end)
    indexed = sorted(enumerate(boxes), key=lambda t: t[1][1])
    extended = list(boxes)
    for rank, (orig_i, (x0, y0, x1, y1)) in enumerate(indexed):
        bh = y1 - y0
        # Default caption band under photo (~18–28% of photo height, min/max clamped)
        default_extra = max(28, min(int(bh * 0.28), int(page_h * 0.12)))
        limit_y = page_h - 2
        if rank + 1 < len(indexed):
            next_y0 = indexed[rank + 1][1][1]
            # leave a small gap before next photo
            limit_y = min(limit_y, next_y0 - 4)
        # If we know a caption y under this photo, extend at least to cover it + pad
        cy_target = None
        mid = (y0 + y1) / 2.0
        for cy in sorted(caption_ys_small):
            if cy >= y1 - 8 and cy < limit_y + 20:
                cy_target = cy
                break
        extra = default_extra
        if cy_target is not None:
            extra = max(extra, int(cy_target - y1) + 22)
        new_y1 = min(limit_y, y1 + extra)
        # Also widen slightly so wrapped caption lines aren't clipped
        pad_x = max(6, int((x1 - x0) * 0.03))
        nx0 = max(0, x0 - pad_x)
        nx1 = min(page_w, x1 + pad_x)
        # Reject if extension would swallow most of the page (page-dump guard)
        if (nx1 - nx0) * (new_y1 - y0) > 0.55 * page_h * page_w:
            new_y1 = y1
        extended[orig_i] = (nx0, y0, nx1, max(y1, new_y1))
    return extended


def crop_photos_from_page_image(
    pil: Image.Image,
    caption_ys_page: list[float] | None = None,
    page_height_pts: float | None = None,
) -> list[tuple[Image.Image, float]]:
    """Detect photo regions; extend each crop to include caption under the photo.

    Returns list of (crop_image, y_center_in_page_fraction 0..1) sorted stably.
    """
    rgb = pil.convert("RGB")
    max_dim = 1400
    scale = min(1.0, max_dim / max(rgb.size))
    small = rgb.resize(
        (max(1, int(rgb.size[0] * scale)), max(1, int(rgb.size[1] * scale))),
        Image.Resampling.BILINEAR,
    )
    gray = np.asarray(small.convert("L"))
    sh, sw = gray.shape
    boxes = _find_photo_boxes(gray)
    # Map caption Y from PDF points → small-image pixels
    cap_ys_small: list[float] = []
    if caption_ys_page and page_height_pts and page_height_pts > 0:
        for cy in caption_ys_page:
            # page rendered to rgb at matrix 2.0 typically; use fraction of page
            frac = cy / page_height_pts
            cap_ys_small.append(frac * sh)
    boxes = _extend_box_for_caption(boxes, cap_ys_small, sh, sw)
    out: list[tuple[Image.Image, float]] = []
    for x0, y0, x1, y1 in boxes:
        X0 = int(x0 / scale)
        Y0 = int(y0 / scale)
        X1 = int(x1 / scale)
        Y1 = int(y1 / scale)
        pad = 4
        X0, Y0 = max(0, X0 - pad), max(0, Y0 - pad)
        X1, Y1 = min(rgb.size[0], X1 + pad), min(rgb.size[1], Y1 + pad)
        # Final page-dump guard on full-res crop
        area = (X1 - X0) * (Y1 - Y0)
        if area > 0.55 * rgb.size[0] * rgb.size[1]:
            continue
        crop = rgb.crop((X0, Y0, X1, Y1))
        if crop.size[0] < 80 or crop.size[1] < 80:
            continue
        y_frac = ((Y0 + Y1) / 2.0) / max(rgb.size[1], 1)
        out.append((crop, y_frac))
    # Top-to-bottom for stable crop01/crop02 numbering
    out.sort(key=lambda t: t[1])
    return out


def extract_embedded_non_page_images(
    doc: fitz.Document, page: fitz.Page, page_no: int
) -> list[bytes]:
    """Embedded images that are clearly smaller than the page (real figures)."""
    rect = page.rect
    out = []
    for img in page.get_images(full=True):
        xref = img[0]
        try:
            pix = fitz.Pixmap(doc, xref)
            if pix.n > 4:
                pix = fitz.Pixmap(fitz.csRGB, pix)
            img_area = pix.width * pix.height
            # Never save full-page scan embeds
            if img_area > 1_800_000:
                continue
            if pix.width > 0.80 * rect.width * 2 and pix.height > 0.80 * rect.height * 2:
                continue
            if pix.width * pix.height > 0.50 * (rect.width * 2) * (rect.height * 2):
                continue
            if min(pix.width, pix.height) < 120:
                continue
            data = pix.tobytes("png")
            if len(data) < 5000:
                continue
            out.append(data)
        except Exception:
            continue
    return out


def save_png(data: bytes, dest_dir: Path, base: str, meta: str) -> bool:
    dest_dir.mkdir(parents=True, exist_ok=True)
    out_path = dest_dir / base
    if out_path.exists():
        return False
    out_path.write_bytes(data)
    (dest_dir / f"{base}.source.txt").write_text(meta, encoding="utf-8")
    return True


def extract_pdf(path: Path, year: int | None) -> dict:
    stats = {
        "pages": 0,
        "embedded_saved": 0,
        "cropped_saved": 0,
        "named": 0,
        "skipped_fullpage": 0,
    }
    rel = str(path.relative_to(ROOT))
    ocr_pages = load_ocr_pages(path)
    doc = fitz.open(str(path))
    seen: set[str] = set()
    try:
        for page_no in range(len(doc)):
            page = doc[page_no]
            stats["pages"] += 1
            try:
                text = page.get_text("text") or ""
            except Exception:
                text = ""
            ocr_text = ocr_pages.get(page_no + 1, "") or ""
            if len(text.strip()) < 40:
                text = ocr_text or text
            captions = captions_with_y_from_page(page, text)
            if not captions and ocr_text and ocr_text != text:
                captions = captions_with_y_from_page(page, ocr_text)

            # 1) Small embedded images only (never full-page scans)
            embedded = extract_embedded_non_page_images(doc, page, page_no)
            page_imgs = page.get_images(full=True)
            if page_imgs and not embedded:
                stats["skipped_fullpage"] += len(page_imgs)

            if embedded:
                dogs = assign_dogs_to_crops(
                    [float(i) for i in range(len(embedded))],
                    captions if captions else [],
                )
                for i, data in enumerate(embedded, 1):
                    h = hashlib.sha1(data).hexdigest()[:16]
                    if h in seen:
                        continue
                    seen.add(h)
                    dog = dogs[i - 1] if i - 1 < len(dogs) else None
                    if dog:
                        stats["named"] += 1
                        folder = safe_dog_folder(dog)
                    else:
                        folder = f"_uncaptioned/{year or 'unk'}"
                    base = f"{year or 'unk'}_p{page_no+1:03d}_emb{i:02d}_{h}.png"
                    meta = (
                        f"source={rel}\npage={page_no+1}\ndog_guess={dog or ''}\n"
                        f"kind=embedded\n"
                    )
                    if save_png(data, OUT / folder, base, meta):
                        stats["embedded_saved"] += 1
                continue

            # 2) Scan page: crop photo+caption regions only
            pix = page.get_pixmap(matrix=fitz.Matrix(2.0, 2.0))
            img = Image.frombytes("RGB", (pix.width, pix.height), pix.samples)
            cap_ys = [c[0] for c in captions]
            crops = crop_photos_from_page_image(
                img, caption_ys_page=cap_ys, page_height_pts=float(page.rect.height)
            )
            dogs = assign_dogs_to_crops(
                [c[1] * float(page.rect.height) for c in crops],
                captions,
            )
            for i, ((crop, _yf), dog) in enumerate(zip(crops, dogs), 1):
                buf = BytesIO()
                crop.save(buf, format="PNG", optimize=True)
                data = buf.getvalue()
                h = hashlib.sha1(data).hexdigest()[:16]
                if h in seen:
                    continue
                seen.add(h)
                if dog:
                    stats["named"] += 1
                    folder = safe_dog_folder(dog)
                else:
                    folder = f"_uncaptioned/{year or 'unk'}"
                base = f"{year or 'unk'}_p{page_no+1:03d}_crop{i:02d}_{h}.png"
                meta = (
                    f"source={rel}\npage={page_no+1}\ndog_guess={dog or ''}\n"
                    f"kind=crop\nsize={crop.size[0]}x{crop.size[1]}\n"
                )
                if save_png(data, OUT / folder, base, meta):
                    stats["cropped_saved"] += 1
    finally:
        doc.close()
    return stats


def reset_output() -> None:
    """Wipe Yearbook Photos completely (photos-only target)."""
    if OUT.exists():
        # Retry — OneDrive can briefly lock dirs
        for _ in range(3):
            try:
                shutil.rmtree(OUT)
                break
            except OSError:
                import time

                time.sleep(1.5)
        else:
            for child in list(OUT.iterdir()):
                try:
                    if child.is_dir():
                        shutil.rmtree(child, ignore_errors=True)
                    else:
                        child.unlink(missing_ok=True)
                except OSError:
                    pass
    OUT.mkdir(parents=True, exist_ok=True)


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--year", type=int, default=None)
    ap.add_argument("--max-pdfs", type=int, default=None)
    ap.add_argument("--reset", action="store_true", help="Clear Yearbook Photos first")
    args = ap.parse_args()

    if args.reset:
        print(f"RESET {OUT}", flush=True)
        reset_output()
    OUT.mkdir(parents=True, exist_ok=True)

    years = range(args.year, args.year + 1) if args.year else range(1984, 2002)
    pdfs = iter_yearbook_pdfs(years)
    if args.max_pdfs:
        pdfs = pdfs[: args.max_pdfs]
    print(f"pdfs={len(pdfs)} out={OUT}", flush=True)

    totals = {
        "pdfs": 0,
        "pages": 0,
        "embedded_saved": 0,
        "cropped_saved": 0,
        "named": 0,
        "skipped_fullpage": 0,
    }
    for y, path in pdfs:
        print(f"EXTRACT {y} {path.relative_to(ROOT)}", flush=True)
        try:
            st = extract_pdf(path, y)
        except Exception as e:
            print(f"  FAIL {e}", flush=True)
            continue
        print(f"  {st}", flush=True)
        totals["pdfs"] += 1
        for k in totals:
            if k != "pdfs" and k in st:
                totals[k] += st[k]
    print("DONE", totals, flush=True)
    dog_dirs = [
        p.name
        for p in OUT.iterdir()
        if p.is_dir() and not p.name.startswith("_")
    ]
    print(f"dog_folders={len(dog_dirs)} sample={dog_dirs[:15]}", flush=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
