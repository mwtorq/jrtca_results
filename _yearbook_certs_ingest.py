#!/usr/bin/env python3
"""Deprecated shim — use ``yearbook_certs_ingest`` instead."""
from __future__ import annotations

import warnings

warnings.warn(
    "Import yearbook_certs_ingest (not _yearbook_certs_ingest); this shim will be removed.",
    DeprecationWarning,
    stacklevel=2,
)

from yearbook_certs_ingest import *  # noqa: F403
