#!/usr/bin/env python3
"""Fix OCR-garbled Yearbook Photos folder names from each file's dog_guess + polish.

Does NOT use other captions on the same page (that caused cross-dog merges).
"""
from __future__ import annotations

import os
import re
import time
from pathlib import Path

from yearbook_ocr import fix_ocr_li_confusion, norm_space

ROOT = Path(r"c:\Users\mw\OneDrive - timberwilde.net\repos\jrtca_results")
PHOTOS = ROOT / "Yearbook Photos"

_TOKEN_FIXES = {
    "pba8ant": "pleasant",
    "brbrpateh": "briarpatch",
    "brlarpatch": "briarpatch",
    "brlarpateh": "briarpatch",
    "bharpatch": "briarpatch",
    "bdarpatch": "briarpatch",
    "brlatpatch": "briarpatch",
    "fox6eld": "foxfield",
    "x6eld": "foxfield",
    "foxfleld": "foxfield",
    "foxtleld": "foxfield",
    "foxfiold": "foxfield",
    "wil1-0-moor": "will-o-moor",
    "will-0-moor": "will-o-moor",
    "sugarbak8r": "sugarbaker",
    "windennere": "windermere",
    "wlndermere": "windermere",
    "wlndormere": "windermere",
    "wlndover": "windover",
    "rav8nswood": "ravenswood",
    "rav8n9wood": "ravenswood",
    "bogcachlel": "bogachiel",
    "lnrches": "larches",
    "plnehaven": "pinehaven",
    "maefieid": "maefield",
    "l08t": "lost",
    "lo8t": "lost",
    "ru8hill": "rushill",
    "da8h": "dash",
    "nol9e": "noise",
    "white": "white",
    "rip": "rip",
    "fig1t": "fight",
    "frolle": "frolic",
    "cortenbaeh": "cortenbach",
    "cortenbacfrs": "cortenbach's",
}

_PHRASE_FIXES = [
    (re.compile(r"(?i)\bPba8ant\s+Valley\b"), "Pleasant Valley"),
    (re.compile(r"(?i)\bBrbrpateh\b"), "Briarpatch"),
    (re.compile(r"(?i)\bBrlarpateh\b"), "Briarpatch"),
    (re.compile(r"(?i)\bBrlarpatch\b"), "Briarpatch"),
    (re.compile(r"(?i)\bBdarpatch\b"), "Briarpatch"),
    (re.compile(r"(?i)\bBrlatpatch\b"), "Briarpatch"),
    (re.compile(r"(?i)\bWil1-0-Moor\b"), "Will-O-Moor"),
    (re.compile(r"(?i)\bWIndy\s+HIll\b"), "Windy Hill"),
    (re.compile(r"(?i)\bSugarbak8r\b"), "Sugarbaker"),
    (re.compile(r"(?i)\bFox\s+Ru;?I\b"), "Fox Run"),
    (re.compile(r"(?i)\bof\s+IUx\s+Run\b"), "of Fox Run"),
    (re.compile(r"(?i)\bRav8n9?wood\b"), "Ravenswood"),
    (re.compile(r"(?i)\bFig1t\b"), "Fight"),
    (re.compile(r"(?i)\bFrolle\b"), "Frolic"),
    (re.compile(r"(?i)\bL08t\s+Creek\b"), "Lost Creek"),
    (re.compile(r"(?i)\bRu8hill\s+Da8h\b"), "Rushill Dash"),
    (re.compile(r"(?i)\bJoyful\s+Nol9e\s+RIp\s+of\s+WhIte\s+Gate\b"), "Joyful Noise Rip of White Gate"),
    (re.compile(r"(?i)\bWlndover\b"), "Windover"),
    (re.compile(r"(?i)\bWlndormere\b"), "Windermere"),
    (re.compile(r"(?i)\bTEK\s+of\s+Windennere\b"), "Tek of Windermere"),
    (re.compile(r"(?i)\bTek\s+Of\s+WIndermere\b"), "Tek of Windermere"),
    (re.compile(r"(?i)\bThe\s+Hollow\s+Devon\s+of\s+IUx\s+Run\b"), "The Hollow Devon of Fox Run"),
    (re.compile(r"(?i)\bBeacon\s+Jangle\s+of\s+Rav8n9wood\b"), "Beacon Jangle of Ravenswood"),
    (re.compile(r"(?i)\bFoxtleld\s+Garth\s+of\s+L08t\s+Creek\b"), "Foxfield Garth of Lost Creek"),
    (re.compile(r"(?i)\bFox\s+Run\s+Frolic\s+of\s+MaefieId\b"), "Fox Run Frolic of Maefield"),
    (re.compile(r"(?i)\bCortenbaeh's\b"), "Cortenbach's"),
    (re.compile(r"(?i)\bPba8ant\s+Valley\s+Pistol\s+of\s+Brbrpateh\b"), "Pleasant Valley Pistol of Briarpatch"),
]


def looks_bad(name: str) -> bool:
    if name.startswith("_"):
        return False
    if re.search(r"\d", name):
        # allow years only as whole name
        if re.fullmatch(r"\d{4}", name):
            return False
        return True
    if re.search(
        r"(?i)(?:brbrpateh|brlarpateh|\bbrlarpatch\b|\bbdarpatch\b|\bbrlatpatch\b|"
        r"fox6eld|\bx6eld\b|foxfleld|foxtleld|pba8ant|sugarbak|wil1-0|"
        r"\blnrch|\bbogcach|\brav8n|fig1t|\bfrolle\b|\biux\s+run|"
        r"\bfox\s+rui\b|maefieid|\bfarrr|\bfarmdiff\b|windenn|wlndormere|"
        r"\bwlndover\b|ru8hill|nol9e|l08t)",
        name,
    ):
        return True
    if re.match(r"(?i)^s\s+\S", name):
        return True
    if re.search(r"(?i)\bof\s*$", name):
        return True
    if ";" in name or "\\" in name:
        return True
    return False


def polish_name(name: str) -> str:
    n = fix_ocr_li_confusion(name or "")
    for rx, repl in _PHRASE_FIXES:
        n = rx.sub(repl, n)
    parts = []
    for tok in n.split():
        raw = tok.strip(",.;:")
        low = raw.lower()
        if low in _TOKEN_FIXES:
            fixed = _TOKEN_FIXES[low]
            if "-" in fixed:
                parts.append("-".join(p[:1].upper() + p[1:] if p else "" for p in fixed.split("-")))
            else:
                parts.append(fixed[:1].upper() + fixed[1:] if raw[:1].isupper() else fixed)
        else:
            t2 = raw
            t2 = re.sub(r"(?i)bak8r$", "baker", t2)
            t2 = re.sub(r"(?i)^fig1t$", "Fight", t2)
            t2 = re.sub(r"(?i)^l08t$", "Lost", t2)
            t2 = re.sub(r"(?i)^da8h$", "Dash", t2)
            t2 = re.sub(r"(?i)^nol9e$", "Noise", t2)
            t2 = re.sub(r"(?i)^ru8hill$", "Rushill", t2)
            parts.append(t2)
    n = " ".join(parts)
    n = re.sub(r"\s+", " ", n).strip(" ,.;")
    # Canonical kennel casing
    for a, b in (
        ("Pleasant Valley", "Pleasant Valley"),
        ("Briarpatch", "Briarpatch"),
        ("Foxfield", "Foxfield"),
        ("Will-O-Moor", "Will-O-Moor"),
        ("Windy Hill", "Windy Hill"),
        ("Windermere", "Windermere"),
        ("Windover", "Windover"),
        ("Ravenswood", "Ravenswood"),
        ("Fox Run", "Fox Run"),
        ("Farmcliff", "Farmcliff"),
        ("Rushill", "Rushill"),
        ("White Gate", "White Gate"),
        ("Joyful Noise", "Joyful Noise"),
        ("Lost Creek", "Lost Creek"),
        ("Maefield", "Maefield"),
        ("Cortenbach's", "Cortenbach's"),
        ("Tek of Windermere", "Tek of Windermere"),
    ):
        n = re.sub(rf"(?i)\b{re.escape(a)}\b", b, n)
    return n


def safe_folder(name: str) -> str:
    n = polish_name(name)
    n = re.sub(r"[^A-Za-z0-9' \-]+", "", n)
    n = re.sub(r"\s+", " ", n).strip(" .-")
    return (n or "Unknown")[:80]


def merge_into(dest: Path, files: list[Path]) -> None:
    dest.mkdir(parents=True, exist_ok=True)
    for f in files:
        t = dest / f.name
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


def main() -> int:
    # Rehome every PNG by polishing its own dog_guess (unscramble bad merges)
    moves: dict[str, list[Path]] = {}
    sources = list(PHOTOS.rglob("*.source.txt"))
    print(f"source_files={len(sources)}", flush=True)
    for src in sources:
        if "_uncaptioned" in src.parts:
            continue
        meta = src.read_text(encoding="utf-8", errors="ignore")
        m = re.search(r"^dog_guess=(.*)$", meta, re.M)
        guess = (m.group(1).strip() if m else "") or src.parent.name
        target = safe_folder(guess)
        if not target or target == "Unknown":
            target = safe_folder(src.parent.name)
        png = src.with_name(src.name[: -len(".source.txt")])
        # src is name.png.source.txt → png is name.png
        if not png.exists():
            # pattern: foo.png.source.txt
            if src.name.endswith(".png.source.txt"):
                png = src.with_name(src.name[: -len(".source.txt")])
        files = [src]
        if png.exists():
            files.insert(0, png)
        moves.setdefault(target, []).extend(files)

    changed = 0
    for target, files in sorted(moves.items()):
        dest = PHOTOS / target
        # skip if all already there
        need = [f for f in files if f.parent.resolve() != dest.resolve()]
        if not need:
            continue
        print(f"REHOME {len(need)} files -> {target!r}", flush=True)
        merge_into(dest, need)
        changed += 1

    # Remove empty dirs
    for d in list(PHOTOS.iterdir()):
        if d.is_dir() and not d.name.startswith("_"):
            try:
                next(d.iterdir())
            except StopIteration:
                try:
                    d.rmdir()
                except OSError:
                    os.system(f'cmd /c rd /s /q "{d}"')

    bad = [
        d.name
        for d in PHOTOS.iterdir()
        if d.is_dir() and not d.name.startswith("_") and looks_bad(d.name)
    ]
    print(f"DONE rehomed_groups={changed} still_bad={len(bad)}", flush=True)
    for n in bad:
        print(f"  still: {n}", flush=True)
        # force polish folder name itself
        fixed = safe_folder(n)
        if fixed != n and not looks_bad(fixed):
            print(f"  FOLDER {n!r} -> {fixed!r}", flush=True)
            src = PHOTOS / n
            merge_into(PHOTOS / fixed, list(src.iterdir()))
            try:
                src.rmdir()
            except OSError:
                os.system(f'cmd /c rd /s /q "{src}"')
    bad2 = [
        d.name
        for d in PHOTOS.iterdir()
        if d.is_dir() and not d.name.startswith("_") and looks_bad(d.name)
    ]
    print(f"FINAL still_bad={len(bad2)}", flush=True)
    for n in bad2:
        print(f"  {n}", flush=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
