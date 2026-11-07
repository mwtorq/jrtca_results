#!/usr/bin/env python3
"""Re-assign Yearbook Photos crops using per-page captions (vertical order).

Fixes folders that contain the wrong dog because every crop on a page got the
first caption, or because cleanup merged by polished dog_guess only.
"""
from __future__ import annotations

import os
import re
import time
from collections import defaultdict
from pathlib import Path

import fitz

from yearbook_ocr import fix_ocr_li_confusion, norm_space
from yearbook_cleanup_photo_names import looks_bad, polish_name, safe_folder

ROOT = Path(r"c:\Users\mw\OneDrive - timberwilde.net\repos\jrtca_results")
PHOTOS = ROOT / "Yearbook Photos"

_OWNED_LINE = re.compile(
    r"(?im)^([A-Z][A-Za-z0-9'][A-Za-z0-9' \-]{2,60}?)\s*\r?\n\s*"
    r"Owned(?:\s+and\s+(?:bred|handled))? by\b"
)
_OWNED_INLINE = re.compile(
    r"([A-Z][A-Za-z0-9' \-]{2,55}?),?\s+owned(?:\s+and\s+(?:bred|handled))? by\s+",
    re.I,
)

# Known orphan-'s recoveries from page evidence
_POSSESSIVE = {
    "s bobbett of flattwood": "Newmarket's Bobbett of Flattwood",
    "s crystal": "Fenton's Crystal",
    "s dizzy daisy of bogachiel": "Horsemaster's Dizzy Daisy of Bogachiel",
    "s dizzy daisy of bogcachlel": "Horsemaster's Dizzy Daisy of Bogachiel",
    "s honor": "Fenton's Scout's Honor",
    "s madame mustache": "Rustler's Madame Mustache",
    "s moon sprite": "Cortenbach's Moon Sprite",
    "s roost": "Cottonwood Cattle Kate of Rustler's Roost",
    "s sampson": None,  # resolve from page
    "s shameless": "Shenanigan's Shameless",
    "s sprocket of glen echo": "Horsemaster's Sprocket of Glen Echo",
    "s stormy": "Goulden Ridge's Stormy",
    "s tailor of briarpatch": "Maven's Tailor of Briarpatch",
    "s tailor of bharpatch": "Maven's Tailor of Briarpatch",
    "s tailor of bdarpatch": "Maven's Tailor of Briarpatch",
    "s trap of the larches": "Waterford's Trap of The Larches",
    "s wager of hornmasters": "Sayner's Wager of Hornmasters",
}


def page_captions(text: str) -> list[str]:
    text = fix_ocr_li_confusion(text or "")
    found: list[str] = []
    seen: set[str] = set()

    def add(c: str) -> None:
        c = polish_name(norm_space(c))
        key = c.casefold()
        # orphan s
        if re.match(r"(?i)^s\s+\S", c):
            mapped = _POSSESSIVE.get(c.casefold())
            if mapped:
                c = mapped
                key = c.casefold()
            else:
                return
        if looks_bad(c) and not re.search(r"'", c):
            c2 = safe_folder(c)
            if not looks_bad(c2):
                c = c2
                key = c.casefold()
        if len(c) < 5 or key in seen:
            return
        if re.search(r"(?i)\bof\s*$", c):
            return
        seen.add(key)
        found.append(c)

    for m in _OWNED_LINE.finditer(text):
        add(m.group(1))
    for m in _OWNED_INLINE.finditer(text):
        add(m.group(1))
    # Name\nOwned by blocks already covered; also "Name\nOwned by" without comma
    lines = [ln.strip() for ln in text.splitlines() if ln.strip()]
    for i, ln in enumerate(lines):
        if re.match(r"(?i)^owned(?:\s+and\s+(?:bred|handled))? by\b", ln) and i > 0:
            add(lines[i - 1].rstrip(","))
    return found


def parse_source(meta_path: Path) -> dict:
    meta = meta_path.read_text(encoding="utf-8", errors="ignore")
    out = {"meta_path": meta_path, "meta": meta}
    for line in meta.splitlines():
        if "=" in line:
            k, v = line.split("=", 1)
            out[k.strip()] = v.strip()
    return out


def merge_move(files: list[Path], dest_name: str) -> None:
    dest = PHOTOS / dest_name
    dest.mkdir(parents=True, exist_ok=True)
    for f in files:
        if not f.exists():
            continue
        t = dest / f.name
        if f.resolve() == t.resolve():
            continue
        if t.exists():
            try:
                f.unlink()
            except OSError:
                pass
        else:
            try:
                f.rename(t)
            except OSError:
                pass


def update_dog_guess(source_txt: Path, dog: str) -> None:
    if not source_txt.exists():
        return
    meta = source_txt.read_text(encoding="utf-8", errors="ignore")
    if re.search(r"^dog_guess=", meta, re.M):
        meta = re.sub(r"^dog_guess=.*$", f"dog_guess={dog}", meta, count=1, flags=re.M)
    else:
        meta += f"\ndog_guess={dog}\n"
    source_txt.write_text(meta, encoding="utf-8")


def main() -> int:
    # Index all crops by (source pdf, page)
    by_page: dict[tuple[str, int], list[dict]] = defaultdict(list)
    for src in PHOTOS.rglob("*.source.txt"):
        if "_uncaptioned" in src.parts:
            continue
        info = parse_source(src)
        rel = info.get("source")
        page = info.get("page")
        if not rel or not page:
            continue
        try:
            page_i = int(page)
        except ValueError:
            continue
        png = src.with_name(src.name[: -len(".source.txt")])
        # filename ...cropNN...
        m = re.search(r"_crop(\d+)_", src.name)
        crop_i = int(m.group(1)) if m else 0
        by_page[(rel, page_i)].append(
            {
                "src": src,
                "png": png if png.exists() else None,
                "crop_i": crop_i,
                "folder": src.parent.name,
                "guess": info.get("dog_guess", ""),
            }
        )

    moved = 0
    for (rel, page_i), items in sorted(by_page.items()):
        items.sort(key=lambda x: x["crop_i"])
        pdf = ROOT / rel
        if not pdf.is_file():
            continue
        try:
            doc = fitz.open(str(pdf))
            text = doc[page_i - 1].get_text("text") or ""
            doc.close()
        except Exception:
            continue
        caps = page_captions(text)
        if not caps:
            # still polish each guess / folder
            for it in items:
                dog = safe_folder(it["guess"] or it["folder"])
                mapped = _POSSESSIVE.get((it["guess"] or it["folder"]).casefold())
                if mapped:
                    dog = mapped
                if re.match(r"(?i)^s\s+", dog):
                    continue
                files = [p for p in (it["png"], it["src"]) if p]
                if it["folder"] != dog:
                    merge_move(files, dog)
                    update_dog_guess(PHOTOS / dog / it["src"].name, dog)
                    moved += 1
            continue

        # Assign crops to captions by order; if more crops than caps, extras keep polish(guess)
        for i, it in enumerate(items):
            if len(caps) == len(items):
                dog = caps[i]
            elif len(caps) == 1 and len(items) >= 1:
                # one caption: only crop closest / first gets it if single; if multi crops with one
                # caption, assign that caption to all only when guesses already match same dog
                dog = caps[0]
            elif i < len(caps):
                dog = caps[i]
            else:
                dog = safe_folder(it["guess"] or it["folder"])
            mapped = _POSSESSIVE.get(dog.casefold())
            if mapped:
                dog = mapped
            dog = safe_folder(dog)
            files = [p for p in (it["png"], it["src"]) if p]
            if it["folder"] != dog or (it["guess"] or "").casefold() != dog.casefold():
                print(
                    f"SPLIT {rel} p{page_i} crop{it['crop_i']:02d}: "
                    f"{it['folder']!r}/{it['guess']!r} -> {dog!r}",
                    flush=True,
                )
                merge_move(files, dog)
                new_src = PHOTOS / dog / it["src"].name
                update_dog_guess(new_src, dog)
                moved += 1

    # Merge case-only duplicate folders
    folders = [d for d in PHOTOS.iterdir() if d.is_dir() and not d.name.startswith("_")]
    by_key: dict[str, list[Path]] = defaultdict(list)
    for d in folders:
        by_key[safe_folder(d.name).casefold()].append(d)
    for key, ds in by_key.items():
        if len(ds) < 2:
            continue
        canon = safe_folder(ds[0].name)
        # prefer name that already equals safe_folder and has fewer OCR marks
        ds_sorted = sorted(ds, key=lambda p: (looks_bad(p.name), len(p.name), p.name))
        canon = safe_folder(ds_sorted[0].name)
        for d in ds:
            if d.name == canon:
                continue
            print(f"MERGE {d.name!r} -> {canon!r}", flush=True)
            merge_move(list(d.iterdir()), canon)
            try:
                d.rmdir()
            except OSError:
                os.system(f'cmd /c rd /s /q "{d}"')

    # Final possessive sweep
    for d in list(PHOTOS.iterdir()):
        if not d.is_dir() or d.name.startswith("_"):
            continue
        mapped = _POSSESSIVE.get(d.name.casefold())
        if mapped and mapped != d.name:
            print(f"POSSESSIVE {d.name!r} -> {mapped!r}", flush=True)
            merge_move(list(d.iterdir()), mapped)
            try:
                d.rmdir()
            except OSError:
                os.system(f'cmd /c rd /s /q "{d}"')
        elif looks_bad(d.name):
            fixed = safe_folder(d.name)
            if fixed != d.name and not looks_bad(fixed):
                print(f"POLISH {d.name!r} -> {fixed!r}", flush=True)
                merge_move(list(d.iterdir()), fixed)
                try:
                    d.rmdir()
                except OSError:
                    os.system(f'cmd /c rd /s /q "{d}"')

    # Report mixed dog_guess folders (true multi-dog contamination)
    mixed = 0
    for d in PHOTOS.iterdir():
        if not d.is_dir() or d.name.startswith("_"):
            continue
        guesses = set()
        for src in d.glob("*.source.txt"):
            info = parse_source(src)
            g = safe_folder(info.get("dog_guess") or d.name)
            guesses.add(g.casefold())
        if len(guesses) > 1:
            mixed += 1
            print(f"MIXED {d.name!r} -> {sorted(guesses)}", flush=True)
    print(f"DONE moved={moved} mixed_left={mixed}", flush=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
