#!/usr/bin/env python3
"""Yearbook OCR font matching — map year → Tesseract lang / training group.

Loads ``yearbook_fonts_by_year.json`` (visual font ID). Windows substitutes:
  Helvetica → Arial, Times-like → Times New Roman, mono → Courier New.
"""
from __future__ import annotations

import json
from functools import lru_cache
from pathlib import Path

ROOT = Path(r"c:\Users\mw\OneDrive - timberwilde.net\repos\jrtca_results")
FONTS_JSON = ROOT / "yearbook_fonts_by_year.json"
# Repo copy (versioned). Runtime dir must be path-without-spaces — tesseract
# --tessdata-dir / TESSDATA_PREFIX breaks on "OneDrive - timberwilde…".
TESSDATA_DIR = ROOT / "tessdata_yearbook"
TESSDATA_RUNTIME = Path(r"C:\Users\mw\AppData\Local\jrtca_tessdata")

# Tesseract lang codes we train (files: jrtca_helv.traineddata etc.)
GROUP_LANG = {
    "mono_typewriter": "jrtca_mono",
    "helvetica_yearbook": "jrtca_helv",
    # Legacy alias if older JSON still says mono_mid80s
    "mono_mid80s": "jrtca_mono",
    "serif_early": "jrtca_mono",  # 1984–85 results are mono; ads were serif
}

# Windows font files used for synthetic training
GROUP_FONTS = {
    "mono_typewriter": [
        (r"C:\Windows\Fonts\cour.ttf", "Courier New"),
        (r"C:\Windows\Fonts\courbd.ttf", "Courier New Bold"),
    ],
    "helvetica_yearbook": [
        (r"C:\Windows\Fonts\arial.ttf", "Arial"),
        (r"C:\Windows\Fonts\arialbd.ttf", "Arial Bold"),
    ],
}


@lru_cache(maxsize=1)
def _font_map() -> dict:
    if not FONTS_JSON.is_file():
        return {}
    return json.loads(FONTS_JSON.read_text(encoding="utf-8"))


def training_group_for_year(year: int | None) -> str:
    """Return training group key for a yearbook year."""
    data = _font_map()
    groups = data.get("ocr_training_groups") or {}
    if year is not None:
        for g, years in groups.items():
            if year in years:
                return g
        yinfo = (data.get("years") or {}).get(str(year)) or {}
        fam = (yinfo.get("family") or "").lower()
        if "mono" in fam or "typewriter" in fam or "courier" in fam or "daisy" in fam:
            return "mono_typewriter"
        if "serif" in fam or "times" in fam:
            # Rare typeset pages; default results training is still mono for early years
            return "mono_typewriter" if year is not None and year <= 1988 else "helvetica_yearbook"
    return "helvetica_yearbook"


def sync_runtime_tessdata() -> Path:
    """Copy jrtca_*.traineddata into no-space runtime dir; return that dir."""
    TESSDATA_RUNTIME.mkdir(parents=True, exist_ok=True)
    for src_dir in (TESSDATA_DIR, TESSDATA_RUNTIME):
        if not src_dir.is_dir():
            continue
        for src in src_dir.glob("jrtca_*.traineddata"):
            dst = TESSDATA_RUNTIME / src.name
            if src.resolve() == dst.resolve():
                continue
            if (
                not dst.is_file()
                or dst.stat().st_size != src.stat().st_size
                or dst.stat().st_mtime < src.stat().st_mtime
            ):
                import shutil

                shutil.copy2(src, dst)
    return TESSDATA_RUNTIME


def tesseract_lang_for_year(year: int | None, *, fallback: str = "eng") -> str:
    """Lang code for ``tesseract -l``. Prefers trained jrtca_* if present."""
    group = training_group_for_year(year)
    lang = GROUP_LANG[group]
    sync_runtime_tessdata()
    for base in (TESSDATA_RUNTIME, TESSDATA_DIR):
        trained = base / f"{lang}.traineddata"
        if trained.is_file() and trained.stat().st_size > 1000:
            return lang
    sys_td = Path(r"C:\Program Files\Tesseract-OCR\tessdata") / f"{lang}.traineddata"
    if sys_td.is_file() and sys_td.stat().st_size > 1000:
        return lang
    return fallback


def tessdata_dir_for_lang(lang: str) -> str | None:
    """Runtime tessdata dir for TESSDATA_PREFIX (no spaces)."""
    if not lang.startswith("jrtca_"):
        return None
    runtime = sync_runtime_tessdata()
    if (runtime / f"{lang}.traineddata").is_file():
        return str(runtime)
    return None
