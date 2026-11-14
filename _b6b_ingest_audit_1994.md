# B6b cleanup + ingest audit — 1994

Catalog: `_OCR_CLEANUP_CATALOG_HANDOFF.md`
Volumes: 8  cleaned=7  PASS=7  WARN=0  FAIL=1
Year verdict: **FAIL**  SQL-apply unlock: NO

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
| PASS | True | 0 | 0 | — | `Document_2026-11-04_082440_ocr_hqmax.txt` |
| FAIL | False | 1 | 0 | O6×1 | `Document_2026-11-04_083342_ocr_hqmax.txt` |
| PASS | True | 0 | 0 | — | `Document_2026-11-04_083655_ocr_hqmax.txt` |
| PASS | True | 0 | 0 | — | `Document_2026-11-04_084730_ocr_hqmax.txt` |
| PASS | True | 0 | 0 | — | `Document_2026-11-04_105927_ocr_hqmax.txt` |
| PASS | True | 0 | 0 | — | `Document_2026-11-04_111318_ocr_hqmax.txt` |
| PASS | True | 0 | 0 | — | `Document_2026-11-04_113633_ocr_hqmax.txt` |
| PASS | True | 0 | 0 | — | `Document_2026-11-04_114039_ocr_hqmax.txt` |

## Sample residual hits (after cleanup)

### `Document_2026-11-04_083342_ocr_hqmax.txt` (FAIL)
- `O6` / `owner_tail_trunc`: 5th: Raheen Doc Holiday, owned by Coffey & Cur
