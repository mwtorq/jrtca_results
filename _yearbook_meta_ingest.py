#!/usr/bin/env python3
"""Deprecated shim — use ``yearbook_meta_ingest`` instead."""
from __future__ import annotations

import warnings

warnings.warn(
    "Import yearbook_meta_ingest (not _yearbook_meta_ingest); this shim will be removed.",
    DeprecationWarning,
    stacklevel=2,
)

from yearbook_meta_ingest import *  # noqa: F403
