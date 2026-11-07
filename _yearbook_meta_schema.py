#!/usr/bin/env python3
"""Deprecated shim — use ``yearbook_meta_schema`` instead."""
from __future__ import annotations

import warnings

warnings.warn(
    "Import yearbook_meta_schema (not _yearbook_meta_schema); this shim will be removed.",
    DeprecationWarning,
    stacklevel=2,
)

from yearbook_meta_schema import *  # noqa: F403
