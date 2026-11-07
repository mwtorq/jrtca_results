#!/usr/bin/env python3
"""Deprecated shim — use ``truegrit_ingest`` instead."""
from __future__ import annotations

import warnings

warnings.warn(
    "Import truegrit_ingest (not _truegrit_ingest); this shim will be removed.",
    DeprecationWarning,
    stacklevel=2,
)

from truegrit_ingest import *  # noqa: F403
