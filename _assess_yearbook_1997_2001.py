#!/usr/bin/env python3
"""Deprecated shim — run ``assess_yearbook_1997_2001.py`` instead."""
from __future__ import annotations

import warnings

warnings.warn(
    "Use assess_yearbook_1997_2001.py (not _assess_yearbook_1997_2001.py).",
    DeprecationWarning,
    stacklevel=2,
)

from assess_yearbook_1997_2001 import main

if __name__ == "__main__":
    raise SystemExit(main())
