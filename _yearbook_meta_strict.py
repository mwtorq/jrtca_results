#!/usr/bin/env python3
"""Deprecated shim — use ``yearbook_ocr`` instead.

Kept so older one-off scripts that ``import _yearbook_meta_strict`` keep working.
"""
from __future__ import annotations

import warnings

warnings.warn(
    "Import yearbook_ocr (not _yearbook_meta_strict); this shim will be removed.",
    DeprecationWarning,
    stacklevel=2,
)

from yearbook_ocr import *  # noqa: F403
from yearbook_ocr import (  # noqa: F401 — explicit common names for star-import clarity
    audit_results_ocr_page,
    finalize_results_ocr,
    ocr_page_best,
    ocr_pdf_hq,
    report_ocr_page_audit,
)
