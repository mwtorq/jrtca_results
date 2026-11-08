#!/usr/bin/env python3
"""Deprecated shim — run ``ocr_yearbook_baseline_v2.py`` instead."""
from __future__ import annotations

import warnings

warnings.warn(
    "Use ocr_yearbook_baseline_v2.py (not _ocr_baseline_v2_yearbook_9701.py).",
    DeprecationWarning,
    stacklevel=2,
)

from ocr_yearbook_baseline_v2 import main

if __name__ == "__main__":
    raise SystemExit(main())
