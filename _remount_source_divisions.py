#!/usr/bin/env python3
"""Deprecated shim — use ``remount_source_divisions`` instead."""
from __future__ import annotations

import warnings

warnings.warn(
    "Import remount_source_divisions (not _remount_source_divisions); this shim will be removed.",
    DeprecationWarning,
    stacklevel=2,
)

from remount_source_divisions import *  # noqa: F403
