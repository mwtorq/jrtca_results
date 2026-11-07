#!/usr/bin/env python3
"""Deprecated shim — use ``truegrit_schema`` instead."""
from __future__ import annotations

import warnings

warnings.warn(
    "Import truegrit_schema (not _truegrit_schema); this shim will be removed.",
    DeprecationWarning,
    stacklevel=2,
)

from truegrit_schema import *  # noqa: F403
