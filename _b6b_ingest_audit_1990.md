# B6b cleanup + ingest audit — 1990

Catalog: `_OCR_CLEANUP_CATALOG_HANDOFF.md`
Volumes: 5  cleaned=0  PASS=2  WARN=0  FAIL=3
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
| FAIL | False | 1 | 0 | S1-S3×1 | `scan_ocr_hqmax.txt` |
| FAIL | False | 11 | 0 | O6×7,S1-S3×3,C1×1 | `Document_2026-11-03_192526_ocr_hqmax.txt` |
| FAIL | False | 27 | 0 | S1-S3×16,O6×11 | `Document_2026-11-03_200401_ocr_hqmax.txt` |
| PASS | False | 0 | 0 | — | `Document_2026-11-03_201432_ocr_hqmax.txt` |
| PASS | False | 0 | 0 | — | `Document_2026-11-03_201547_ocr_hqmax.txt` |

## Sample residual hits (after cleanup)

### `scan_ocr_hqmax.txt` (FAIL)
- `S1-S3` / `two_column_smash`: 1st: i1stt REDBUD BEAU, owned by David & Sara Marcum

### `Document_2026-11-03_192526_ocr_hqmax.txt` (FAIL)
- `C1` / `class_header_gap`: 1st: Rushill Rake of Jumping Jax and Rushill Shark, owned by Sally McKenney
- `S1-S3` / `two_column_smash`: 1st: i1stt Woodluck Jennyanydots, owned by Karen Tritschier
- `S1-S3` / `two_column_smash`: 1st: tstt Farmdliff Snooper, owned by Bob Franklin
- `S1-S3` / `two_column_smash`: 1st: i1stt Foxmoor Maybelline, owned by Kathy Gregorieff
- `O6` / `owner_tail_trunc`: RESERVE: SASS N'DASH DANNY'S BLUE CHIP OF STONE'S THROW, owned by
- `O6` / `owner_tail_trunc`: RESERVE: NORTH FORK BLOSSOM OF WESTWOOD, owned by
- `O6` / `owner_tail_trunc`: CHAMPION: HAMMER & TONGS ABYGAIL OF HILLSIDE, owned by
- `O6` / `owner_tail_trunc`: 12-1/2--15' HORSEMASTERS SPROCKET OF GLEN ECHO, owned by
- `O6` / `owner_tail_trunc`: Reserve: HAMMER & TONGS ABIGAIL OF HILLSIDE, owned by
- `O6` / `owner_tail_trunc`: RESERVE: TREETOP ZENITH ACORN, owned by

### `Document_2026-11-03_200401_ocr_hqmax.txt` (FAIL)
- `S1-S3` / `two_column_smash`: kle, owned by Vail Juhring
- `S1-S3` / `two_column_smash`: bod, owned by A. Reynolds & D. Hekkala
- `S1-S3` / `two_column_smash`: OF PRESTWICK, owned by Sally Yancey
- `S1-S3` / `two_column_smash`: 3rd: i'oxmoor Hunter, owned by Kathy Gregorieff
- `S1-S3` / `two_column_smash`: 3rd: sper Willy, owned by Joyce Elder
- `S1-S3` / `two_column_smash`: 6th: olla of Farmstead, owned by Judy Ciccarello
- `S1-S3` / `two_column_smash`: sstan, owned by Laurie & Zen Wojcik
- `S1-S3` / `two_column_smash`: irney, owned by Bob Franklin
- `S1-S3` / `two_column_smash`: stin, owned by Kellyann Morander
- `S1-S3` / `two_column_smash`: ami, owned by Linda Toscano
- `S1-S3` / `two_column_smash`: etel, owned by Bob Franklin
- `S1-S3` / `two_column_smash`: ispell, owned by Daniel & Karen Kinsley
