#!/usr/bin/env python3
"""Deprecated shim — run ``ocr_yearbook_missing_vols.py`` instead."""
from __future__ import annotations

import warnings

warnings.warn(
    "Use ocr_yearbook_missing_vols.py (not _yearbook_ocr_missing_vols.py).",
    DeprecationWarning,
    stacklevel=2,
)

from ocr_yearbook_missing_vols import main

if __name__ == "__main__":
    raise SystemExit(main())
