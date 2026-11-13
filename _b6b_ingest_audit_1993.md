# B6b cleanup + ingest audit — 1993

Catalog: `_OCR_CLEANUP_CATALOG_HANDOFF.md`
Volumes: 5  cleaned=0  PASS=1  WARN=0  FAIL=4
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
| FAIL | False | 8 | 0 | C1×3,S1-S3×3,O6×2 | `Document_2026-11-03_224445_ocr_hqmax.txt` |
| PASS | False | 0 | 0 | — | `Document_2026-11-03_230536_ocr_hqmax.txt` |
| FAIL | False | 5 | 0 | O6×4,S1-S3×1 | `Document_2026-11-03_231659_ocr_hqmax.txt` |
| FAIL | False | 5 | 0 | S1-S3×5 | `Document_2026-11-03_233615_ocr_hqmax.txt` |
| FAIL | False | 2 | 0 | O6×2 | `Document_2026-11-04_002601_ocr_hqmax.txt` |

## Sample residual hits (after cleanup)

### `Document_2026-11-03_224445_ocr_hqmax.txt` (FAIL)
- `C1` / `class_header_gap`: 4th: Tasha R:z
- `C1` / `class_header_gap`: 4th: White Spirits Orion, owned by Michelle Mezoe
- `C1` / `class_header_gap`: 4th: Three Oaks Britches, owned by Carolyn McGaughey
- `S1-S3` / `two_column_smash`: 6th: n Top Bill, owned by Florence Clark
- `S1-S3` / `two_column_smash`: 1st: po       1stt Hart's Farm Goblin, owned by Cheryl Hart
- `S1-S3` / `two_column_smash`: 2nd: photos from the
- `O6` / `owner_tail_trunc`: rton Hall Ace In The Hole of White Stockings, owned by
- `O6` / `owner_tail_trunc`: 2nd: Wyndhaven Lonestar, owned by

### `Document_2026-11-03_231659_ocr_hqmax.txt` (FAIL)
- `S1-S3` / `two_column_smash`: 2nd: LB, owned by Deborah Bickler
- `O6` / `owner_tail_trunc`: Eastlake, owned by
- `O6` / `owner_tail_trunc`: Conformation Champion & Best, owned by
- `O6` / `owner_tail_trunc`: Puppy Conformation Chamg, owned by
- `O6` / `owner_tail_trunc`: Reserve Puppy Confol, owned by

### `Document_2026-11-03_233615_ocr_hqmax.txt` (FAIL)
- `S1-S3` / `two_column_smash`: 1st: i1stt Wyndcroft Natasha, owned by K. Hunter/J. Finkernagel
- `S1-S3` / `two_column_smash`: 1st: fstt Ravenswood Javex, owned by Ben & Janet Sutcliffe
- `S1-S3` / `two_column_smash`: ly, owned by Judy Petty
- `S1-S3` / `two_column_smash`: pcorn, owned by Micki Smith
- `S1-S3` / `two_column_smash`: andit, owned by Kathleen Bryan

### `Document_2026-11-04_002601_ocr_hqmax.txt` (FAIL)
- `O6` / `owner_tail_trunc`: Buttor, owned by
- `O6` / `owner_tail_trunc`: Lobilol, owned by
