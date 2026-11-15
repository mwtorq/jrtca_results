# B6b cleanup + ingest audit — 1995

Catalog: `_OCR_CLEANUP_CATALOG_HANDOFF.md`
Volumes: 5  cleaned=5  PASS=2  WARN=0  FAIL=3
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
| PASS | True | 0 | 0 | — | `Document_2026-11-04_124005_ocr_hqmax.txt` |
| FAIL | True | 1 | 0 | C1×1 | `Document_2026-11-04_124704_ocr_hqmax.txt` |
| PASS | True | 0 | 0 | — | `Document_2026-11-04_130318_ocr_hqmax.txt` |
| FAIL | True | 9 | 0 | C1×8,S1-S3×1 | `Document_2026-11-04_134403_ocr_hqmax.txt` |
| FAIL | True | 2 | 0 | C1×1,S1-S3×1 | `Document_2026-11-04_142425_ocr_hqmax.txt` |

## Sample residual hits (after cleanup)

### `Document_2026-11-04_124704_ocr_hqmax.txt` (FAIL)
- `C1` / `place_rank_gap`: Dogs, 1 yr & over, 12 1/2-15" Entries: 8 | 1th then 4th | 4th: Westwood Sparkle, owned by Alice Reynolds

### `Document_2026-11-04_134403_ocr_hqmax.txt` (FAIL)
- `C1` / `2nd_then_4th_no_3`: 2nd: Whispering Winds Heidi Ho, owned by Mary Winfield
4th: Down East Diamond in the Ruff, owned by Patty Cranmer
- `C1` / `2nd_then_4th_no_3`: 2nd: Foxport La:
4th: Big Sky An
- `C1` / `1st_then_3rd_no_2`: 1st: Thimble Farm Clever, owned by Val Wasch
3rd: Live Wire Mayhem, owned by C & J Kemp
- `C1` / `place_rank_gap`: Bitches, 1 yr & over, 12 1/2-15", r/br                       | 1th then 3th | 3rd: Max, owned by T. Beers
- `C1` / `place_rank_gap`: Novice Agility I, On-Lead                                    | 1th then 3th | 3rd: Courtland Moo Cow, owned by K. Morander & J. Jankowski
- `C1` / `place_rank_gap`: Bitch Pups, 6 up to 12 months, 12-1/2--15" Entries: 8 | 2th then 4th | 4th: Down East Diamond in the Ruff, owned by Patty Cranmer
- `C1` / `place_rank_gap`: Bitch Pups, 9 up to 12 months, 10-12 1/2" Entries: 5 | 1th then 3th | 3rd: Live Wire Mayhem, owned by C & J Kemp
- `C1` / `place_rank_gap`: Bitch Pups, 6 up to 9 months, smooth                         | 2th then 4th | 4th: Big Sky An
- `S1-S3` / `agility_racing_smash`: Go-to-Ground CHAMPION & RESERVE -> RACING DIVISION

### `Document_2026-11-04_142425_ocr_hqmax.txt` (FAIL)
- `C1` / `place_rank_gap`: Dogs, 1 yr & over, 10-12 1/2", r/br                          | 1th then 3th | 3rd: Camerton Hall Echo, owned by Jack & Pauline Fawkes
- `S1-S3` / `agility_racing_smash`: Go-to-Ground CHAMPION & RESERVE -> RACING DIVISION
