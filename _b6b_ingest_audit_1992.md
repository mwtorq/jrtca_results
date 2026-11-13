# B6b cleanup + ingest audit — 1992

Catalog: `_OCR_CLEANUP_CATALOG_HANDOFF.md`
Volumes: 6  cleaned=0  PASS=0  WARN=0  FAIL=6
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
| FAIL | False | 3 | 0 | S1-S3×2,O6×1 | `Document_2026-11-03_212153_ocr_hqmax.txt` |
| FAIL | False | 3 | 0 | S1-S3×3 | `Document_2026-11-03_212636_ocr_hqmax.txt` |
| FAIL | False | 2 | 0 | C1×1,S1-S3×1 | `Document_2026-11-03_213104_ocr_hqmax.txt` |
| FAIL | False | 2 | 0 | C1×1,S1-S3×1 | `Document_2026-11-03_220343_ocr_hqmax.txt` |
| FAIL | False | 1 | 0 | O6×1 | `Document_2026-11-03_220931_ocr_hqmax.txt` |
| FAIL | False | 1 | 0 | S1-S3×1 | `Document_2026-11-03_221749_ocr_hqmax.txt` |

## Sample residual hits (after cleanup)

### `Document_2026-11-03_212153_ocr_hqmax.txt` (FAIL)
- `S1-S3` / `two_column_smash`: 1st: in working terriers
- `S1-S3` / `two_column_smash`: 1st: precocious worker
- `O6` / `owner_tail_trunc`: CHAMPION: FARMCLIFF RAZZELLE OF HOPDIGGITY, owned by

### `Document_2026-11-03_212636_ocr_hqmax.txt` (FAIL)
- `S1-S3` / `two_column_smash`: od, owned by Linda Cranford
- `S1-S3` / `two_column_smash`: wne, owned by Kim Lavers Magnussen
- `S1-S3` / `two_column_smash`: tain, owned by Shirley Merrill

### `Document_2026-11-03_213104_ocr_hqmax.txt` (FAIL)
- `C1` / `class_header_gap`: 1st: Farmcliff Cookie Monster, owned by Bob Franklin & Russ Larsen
- `S1-S3` / `two_column_smash`: 2nd: windermere Tassle, owned by Linda Cowasjee

### `Document_2026-11-03_220343_ocr_hqmax.txt` (FAIL)
- `C1` / `class_header_gap`: 4th: Hannie, owned by David & Nancy Drown
- `S1-S3` / `two_column_smash`: 1st: a          1stt Spectacle of Loblolly, owned by Debra Ellis

### `Document_2026-11-03_220931_ocr_hqmax.txt` (FAIL)
- `O6` / `owner_tail_trunc`: Spects, owned by

### `Document_2026-11-03_221749_ocr_hqmax.txt` (FAIL)
- `S1-S3` / `two_column_smash`: 2nd: the Hudson Bay
