# B6b cleanup + ingest audit — 1993

Catalog: `_OCR_CLEANUP_CATALOG_HANDOFF.md`
Volumes: 5  cleaned=3  PASS=4  WARN=0  FAIL=1
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
| FAIL | True | 1 | 0 | O6×1 | `Document_2026-11-03_224445_ocr_hqmax.txt` |
| PASS | False | 0 | 0 | — | `Document_2026-11-03_230536_ocr_hqmax.txt` |
| PASS | False | 0 | 0 | — | `Document_2026-11-03_231659_ocr_hqmax.txt` |
| PASS | True | 0 | 0 | — | `Document_2026-11-03_233615_ocr_hqmax.txt` |
| PASS | True | 0 | 0 | — | `Document_2026-11-04_002601_ocr_hqmax.txt` |

## Sample residual hits (after cleanup)

### `Document_2026-11-03_224445_ocr_hqmax.txt` (FAIL)
- `O6` / `owner_tail_trunc`: 2nd: Wyndhaven Lonestar, owned by
