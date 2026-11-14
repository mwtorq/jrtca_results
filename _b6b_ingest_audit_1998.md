# B6b cleanup + ingest audit — 1998

Catalog: `_OCR_CLEANUP_CATALOG_HANDOFF.md`
Volumes: 7  cleaned=6  PASS=7  WARN=0  FAIL=0
Year verdict: **PASS**  SQL-apply unlock: YES

## Intent
- Apply finalize/catalog cleanups to stored HQ text (backup `*.pre_b6b`).
- Re-OCR only if FAIL remains after cleanup — not as the default path.

## Policy
- FAIL (blocks apply/unlock): smash, height/place, O6, C1, placeholders, **missing_owned_by**, **orphan_entry_count**, **bare_entries**, **mangled_by**, **cutoff_racing**, **4th_then_2nd**, **4th_then_6th_no_5**
- Re-OCR queued when FAIL includes REOCR_CODES (O6/C1/smash/height) — structural S4/O/C6 cleared in text; do not invent surnames/titles
- `handled by` / `handling` lines excluded from mangled_by / missing_owned_by

## Per volume

| Verdict | Cleaned | Fail | Warn | Catalog | File |
|---------|---------|------|------|---------|------|
| PASS | True | 0 | 0 | — | `1998 Vol I, pt 1_ocr_hqmax.txt` |
| PASS | False | 0 | 0 | — | `1998 Vol I, pt 2_ocr_hqmax.txt` |
| PASS | True | 0 | 0 | — | `1998 Vol I, pt 3_ocr_hqmax.txt` |
| PASS | True | 0 | 0 | — | `1998 Vol II, pt 1_ocr_hqmax.txt` |
| PASS | True | 0 | 0 | — | `1998 Vol II, pt 2_ocr_hqmax.txt` |
| PASS | True | 0 | 0 | — | `1998 Vol III, pt 1_ocr_hqmax.txt` |
| PASS | True | 0 | 0 | — | `1998 Vol III, pt 2_ocr_hqmax.txt` |

## Sample residual hits (after cleanup)
