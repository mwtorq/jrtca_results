#!/usr/bin/env python3
"""Deprecated shim — run ``harvest_cert_sections_v2.py`` instead."""
from __future__ import annotations

import warnings

warnings.warn(
    "Use harvest_cert_sections_v2.py (not _harvest_cert_sections_v2.py).",
    DeprecationWarning,
    stacklevel=2,
)

from harvest_cert_sections_v2 import main

if __name__ == "__main__":
    raise SystemExit(main())
