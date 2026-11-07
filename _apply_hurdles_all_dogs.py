#!/usr/bin/env python3
"""Deprecated shim — use ``apply_hurdles_all_dogs`` instead."""
from __future__ import annotations

import warnings

warnings.warn(
    "Import apply_hurdles_all_dogs (not _apply_hurdles_all_dogs); this shim will be removed.",
    DeprecationWarning,
    stacklevel=2,
)

from apply_hurdles_all_dogs import *  # noqa: F403
