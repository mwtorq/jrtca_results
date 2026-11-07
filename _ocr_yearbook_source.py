#!/usr/bin/env python3
"""Deprecated shim — use ``ocr_yearbook_source`` instead."""
from __future__ import annotations

import warnings

warnings.warn(
    "Import ocr_yearbook_source (not _ocr_yearbook_source); this shim will be removed.",
    DeprecationWarning,
    stacklevel=2,
)

from ocr_yearbook_source import *  # noqa: F403
