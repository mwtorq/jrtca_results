# B6b cleanup + ingest audit — 1994

Catalog: `_OCR_CLEANUP_CATALOG_HANDOFF.md`
Volumes: 8  cleaned=8  PASS=3  WARN=0  FAIL=5
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
| FAIL | True | 2 | 0 | O6×1,C1×1 | `Document_2026-11-04_083342_ocr_hqmax.txt` |
| FAIL | True | 1 | 0 | C1×1 | `Document_2026-11-04_083655_ocr_hqmax.txt` |
| PASS | True | 0 | 0 | — | `Document_2026-11-04_084730_ocr_hqmax.txt` |
| FAIL | True | 3 | 0 | C1×3 | `Document_2026-11-04_105927_ocr_hqmax.txt` |
| FAIL | True | 1 | 0 | C1×1 | `Document_2026-11-04_111318_ocr_hqmax.txt` |
| PASS | True | 0 | 0 | — | `Document_2026-11-04_113633_ocr_hqmax.txt` |
| FAIL | True | 2 | 0 | C1×2 | `Document_2026-11-04_114039_ocr_hqmax.txt` |

## Sample residual hits (after cleanup)

### `Document_2026-11-04_083342_ocr_hqmax.txt` (FAIL)
- `O6` / `owner_tail_trunc`: 5th: Raheen Doc Holiday, owned by Coffey & Cur
- `C1` / `place_rank_gap`: Dogs, 1 yr & over, 12 1/2-15" Entries: 20 | 1th then 4th | 4th: Fox Run Contender of Kelleen, owned by Kelleen Rossman

### `Document_2026-11-04_083655_ocr_hqmax.txt` (FAIL)
- `C1` / `place_rank_gap`: Dog Pups, 9 up to 12 months, 10-12 1/2" Entries: 5 | 2th then 6th | 6th: Briarpatch Pepper, owned by Donna Sinderud

### `Document_2026-11-04_105927_ocr_hqmax.txt` (FAIL)
- `C1` / `place_rank_gap`: Open Puppies                                              En | 1th then 3th | 3rd: Falling Branch Raisin, owned by Phil & Debbie Johnson
- `C1` / `place_rank_gap`: Novice Adults                                                | 4th then 6th | 6th: Tree Top Huey, owned by Bruce & Trish Frankenberg
- `C1` / `place_rank_gap`: Dog Pups, 9 up to 12 months, r/br                            | 1th then 4th | 4th: Corky of Shenandoah, owned by Nancy Steele

### `Document_2026-11-04_111318_ocr_hqmax.txt` (FAIL)
- `C1` / `place_rank_gap`: Class 20: Obedience - Novice                                 | 4th then 6th | 6th: THIMBLE FARM TARGET, owned by Valerie Wasch

### `Document_2026-11-04_114039_ocr_hqmax.txt` (FAIL)
- `C1` / `place_rank_gap`: Stud Dog and Get                                             | 2th then 6th | 6th: Button Top Dudley, owned by Susan Aslop
- `C1` / `place_rank_gap`: Dog Pups, 9 up to 12 months, 10-12 1/2" Entries: 5 | 2th then 4th | 4th: Courtwood Chance of Wit's End, owned by Jane Griffin
