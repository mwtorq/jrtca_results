#!/usr/bin/env python3
"""Deprecated shim — use ``apply_racing_gaps_all`` instead."""
from __future__ import annotations

import warnings

warnings.warn(
    "Import apply_racing_gaps_all (not _apply_racing_gaps_all); this shim will be removed.",
    DeprecationWarning,
    stacklevel=2,
)

from apply_racing_gaps_all import *  # noqa: F403
