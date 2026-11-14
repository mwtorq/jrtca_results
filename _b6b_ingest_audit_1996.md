# B6b cleanup + ingest audit — 1996

Catalog: `_OCR_CLEANUP_CATALOG_HANDOFF.md`
Volumes: 30  cleaned=27  PASS=30  WARN=0  FAIL=0
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
| PASS | True | 0 | 0 | — | `1996 Vol 1 pg 111-160 back reversed_ocr_hqmax.txt` |
| PASS | True | 0 | 0 | — | `1996 Vol 1 pg 111-160 back_ocr_hqmax.txt` |
| PASS | True | 0 | 0 | — | `1996 Vol 1 pg 111-160 front_ocr_hqmax.txt` |
| PASS | False | 0 | 0 | — | `1996 Vol 1 pg 161-178 back reversed_ocr_hqmax.txt` |
| PASS | False | 0 | 0 | — | `1996 Vol 1 pg 161-178 back_ocr_hqmax.txt` |
| PASS | False | 0 | 0 | — | `1996 Vol 1 pg 161-178 front_ocr_hqmax.txt` |
| PASS | True | 0 | 0 | — | `1996 Vol 1 pg 21-60 back reversed_ocr_hqmax.txt` |
| PASS | True | 0 | 0 | — | `1996 Vol 1 pg 21-60 back_ocr_hqmax.txt` |
| PASS | True | 0 | 0 | — | `1996 Vol 1 pg 21-60 front_ocr_hqmax.txt` |
| PASS | True | 0 | 0 | — | `1996 Vol 1 pg 61-110 back reversed_ocr_hqmax.txt` |
| PASS | True | 0 | 0 | — | `1996 Vol 1 pg 61-110 back_ocr_hqmax.txt` |
| PASS | True | 0 | 0 | — | `1996 Vol 1 pg 61-110 front_ocr_hqmax.txt` |
| PASS | True | 0 | 0 | — | `1996 Vol II pg 163-220 back reversed_ocr_hqmax.txt` |
| PASS | True | 0 | 0 | — | `1996 Vol II pg 163-220 back_ocr_hqmax.txt` |
| PASS | True | 0 | 0 | — | `1996 Vol II pg 163-220 front_ocr_hqmax.txt` |
| PASS | True | 0 | 0 | — | `1996 Vol II pg 23-92 back reversed_ocr_hqmax.txt` |
| PASS | True | 0 | 0 | — | `1996 Vol II pg 23-92 back_ocr_hqmax.txt` |
| PASS | True | 0 | 0 | — | `1996 Vol II pg 23-92 front (missing 1 pgs)_ocr_hqmax.txt` |
| PASS | True | 0 | 0 | — | `1996 Vol II pg 23-92 front (missing 2 pgs)_ocr_hqmax.txt` |
| PASS | True | 0 | 0 | — | `1996 Vol II pg 23-92 front_ocr_hqmax.txt` |
| PASS | True | 0 | 0 | — | `1996 Vol II pg 93-162 back reversed_ocr_hqmax.txt` |
| PASS | True | 0 | 0 | — | `1996 Vol II pg 93-162 back_ocr_hqmax.txt` |
| PASS | True | 0 | 0 | — | `1996 Vol II pg 93-162 front_ocr_hqmax.txt` |
| PASS | True | 0 | 0 | — | `Document_2026-11-04_144208_ocr_hqmax.txt` |
| PASS | True | 0 | 0 | — | `Document_2026-11-04_144530_ocr_hqmax.txt` |
| PASS | True | 0 | 0 | — | `Document_2026-11-04_145355_ocr_hqmax.txt` |
| PASS | True | 0 | 0 | — | `Document_2026-11-04_145925_ocr_hqmax.txt` |
| PASS | True | 0 | 0 | — | `Document_2026-11-04_151058_ocr_hqmax.txt` |
| PASS | True | 0 | 0 | — | `Document_2026-11-04_152834_ocr_hqmax.txt` |
| PASS | True | 0 | 0 | — | `Document_2026-11-04_153208_ocr_hqmax.txt` |

## Sample residual hits (after cleanup)
