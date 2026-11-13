# B6b cleanup + ingest audit — 1995

Catalog: `_OCR_CLEANUP_CATALOG_HANDOFF.md`
Volumes: 5  cleaned=0  PASS=0  WARN=0  FAIL=5
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
| FAIL | False | 17 | 0 | O6×11,S1-S3×5,S4/O×1 | `Document_2026-11-04_124005_ocr_hqmax.txt` |
| FAIL | False | 6 | 0 | O6×5,S4/O×1 | `Document_2026-11-04_124704_ocr_hqmax.txt` |
| FAIL | False | 11 | 0 | O6×9,S1-S3×2 | `Document_2026-11-04_130318_ocr_hqmax.txt` |
| FAIL | False | 12 | 0 | S1-S3×7,C1×3,O6×1,S4/O×1 | `Document_2026-11-04_134403_ocr_hqmax.txt` |
| FAIL | False | 31 | 0 | S1-S3×14,O6×10,C1×7 | `Document_2026-11-04_142425_ocr_hqmax.txt` |

## Sample residual hits (after cleanup)

### `Document_2026-11-04_124005_ocr_hqmax.txt` (FAIL)
- `S1-S3` / `place_smash`: y, owned by Bob Franklin, owned by Sandy Brown
- `O6` / `owner_tail_trunc`: 5th: Abby, owned by Annette & Richard Ker
- `O6` / `owner_tail_trunc`: 1st: Whispering Winds Sony, owned by Wt
- `O6` / `owner_tail_trunc`: 4th: South Hunt Cupid, owned by Jerry & E
- `O6` / `owner_tail_trunc`: 4th: Briarwood Ace, owned by Cindy & Dav
- `O6` / `owner_tail_trunc`: 3rd: Greengate Tomba, owned by Joe & Pri
- `O6` / `owner_tail_trunc`: 3rd: Westwood Jade, owned by Rick & Les
- `S4/O` / `missing_owned_by`: 2nd: Whispering Winds Heido Ho, owned b!
- `S1-S3` / `two_column_smash`: 5th: hree Oaks Double D, owned by Carolyn McGaughey
- `S1-S3` / `two_column_smash`: 5th: JR, owned by Neal Damron
- `S1-S3` / `two_column_smash`: ver, owned by Val Wasch
- `S1-S3` / `two_column_smash`: Best: disqualified

### `Document_2026-11-04_124704_ocr_hqmax.txt` (FAIL)
- `O6` / `owner_tail_trunc`: 10-12 1/2" Reserve: TF Half Track, owned by Jin
- `O6` / `owner_tail_trunc`: 1st: Drambuie, owned by Jin
- `O6` / `owner_tail_trunc`: 2nd: Undercover Annie, owned by ow
- `O6` / `owner_tail_trunc`: 3rd: Wild Goose Maryland, owned by ow
- `O6` / `owner_tail_trunc`: 3rd: Wild Goose Fancy, owned by ow
- `S4/O` / `missing_owned_by`: Champion: Big Valley Sudsy, t

### `Document_2026-11-04_130318_ocr_hqmax.txt` (FAIL)
- `O6` / `owner_tail_trunc`: 5. wis BB     i, owned by Sanc
- `O6` / `owner_tail_trunc`: Truffle, owned by Kevi
- `O6` / `owner_tail_trunc`: Whirlwind, owned by Debt
- `O6` / `owner_tail_trunc`: 1st: a, owned by Didi
- `O6` / `owner_tail_trunc`: 2nd: Ce, owned by Pam
- `O6` / `owner_tail_trunc`: 3rd:, owned by Kelly & Ja
- `S1-S3` / `two_column_smash`: 1st: a, owned by Didi
- `S1-S3` / `two_column_smash`: 2nd: Ce, owned by Pam
- `O6` / `owner_tail_trunc`: A     They, owned by
- `O6` / `owner_tail_trunc`: Falcon of Blue Barns, owned by
- `O6` / `owner_tail_trunc`: North Country Polo, owned by

### `Document_2026-11-04_134403_ocr_hqmax.txt` (FAIL)
- `O6` / `owner_tail_trunc`: 3rd: Becky, owned by ow
- `S4/O` / `missing_owned_by`: 1st: Rummy, oy
- `C1` / `class_header_gap`: 1st: Loblolly La
- `C1` / `class_header_gap`: 1st: Foxport La
- `C1` / `class_header_gap`: 1st: Round the
- `S1-S3` / `two_column_smash`: Reserve: Ty, owned by Carolyn Churton
- `S1-S3` / `two_column_smash`: hloe, owned by Vanna Teschner
- `S1-S3` / `two_column_smash`: 3rd: drd: Ridgeview Bon Bon, owned by Didi Gough
- `S1-S3` / `two_column_smash`: 3rd: llow Scamper, owned by Margaret Wheeler
- `S1-S3` / `two_column_smash`: 4th: y' Annie, owned by Doug & Sue Tack
- `S1-S3` / `two_column_smash`: 5th: wder Oaks Josie of Timbre Ridge, owned by Bonnie Hurley
- `S1-S3` / `two_column_smash`: 6th: ce Eden, owned by Will Hahn

### `Document_2026-11-04_142425_ocr_hqmax.txt` (FAIL)
- `O6` / `owner_tail_trunc`: 4th: Bowser, owned by ow
- `O6` / `owner_tail_trunc`: 1st: Windermere Turner of Stealth, owned by Stez
- `O6` / `owner_tail_trunc`: 4th: Seaview Scooter, owned by Didi Gough & Liz
- `O6` / `owner_tail_trunc`: 1st: Morganfield Eve, owned by Karen Reavis & T
- `O6` / `owner_tail_trunc`: 1st: Wesworld Hamilton, owned by Christy Parkison & Suzie Utz
- `C1` / `class_header_gap`: 4th: Little Rascals Spike, owned by The Benintendo Gang
- `C1` / `class_header_gap`: 1st: Windermere Pistol, owned by Sandy & Joel
- `C1` / `class_header_gap`: 1st: Popy of Farmstead, owned by Judy Galterio
- `C1` / `class_header_gap`: 1st: The Larches Pick, owned by Joan & Donald
- `C1` / `class_header_gap`: 1st: The Larches Pic
- `C1` / `class_header_gap`: 1st: Windy Hill Suga
- `C1` / `class_header_gap`: 1st: Morganfield Eve, owned by Karen Reavis & T
