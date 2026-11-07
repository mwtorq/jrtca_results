#!/usr/bin/env python3
"""Deprecated shim — use ``yearbook_vol_collective_audit`` instead."""
from __future__ import annotations

import warnings

warnings.warn(
    "Import yearbook_vol_collective_audit (not _yearbook_vol_collective_audit); this shim will be removed.",
    DeprecationWarning,
    stacklevel=2,
)

from yearbook_vol_collective_audit import *  # noqa: F403
