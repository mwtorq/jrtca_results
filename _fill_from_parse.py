#!/usr/bin/env python3
"""Deprecated shim — use ``fill_from_parse`` instead."""
from __future__ import annotations

import warnings

warnings.warn(
    "Import fill_from_parse (not _fill_from_parse); this shim will be removed.",
    DeprecationWarning,
    stacklevel=2,
)

from fill_from_parse import *  # noqa: F403
