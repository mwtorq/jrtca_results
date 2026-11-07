#!/usr/bin/env python3
"""Deprecated shim — use ``yearbook_cleanup_photo_names`` instead."""
from __future__ import annotations

import warnings

warnings.warn(
    "Import yearbook_cleanup_photo_names (not _yearbook_cleanup_photo_names); this shim will be removed.",
    DeprecationWarning,
    stacklevel=2,
)

from yearbook_cleanup_photo_names import *  # noqa: F403
