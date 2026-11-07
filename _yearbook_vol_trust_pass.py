#!/usr/bin/env python3
"""Deprecated shim — use ``yearbook_vol_trust_pass`` instead."""
from __future__ import annotations

import warnings

warnings.warn(
    "Import yearbook_vol_trust_pass (not _yearbook_vol_trust_pass); this shim will be removed.",
    DeprecationWarning,
    stacklevel=2,
)

from yearbook_vol_trust_pass import *  # noqa: F403
