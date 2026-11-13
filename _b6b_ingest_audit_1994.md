# B6b cleanup + ingest audit — 1994

Catalog: `_OCR_CLEANUP_CATALOG_HANDOFF.md`
Volumes: 8  cleaned=0  PASS=0  WARN=0  FAIL=8
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
| FAIL | False | 4 | 0 | S1-S3×2,O6×2 | `Document_2026-11-04_082440_ocr_hqmax.txt` |
| FAIL | False | 10 | 0 | O6×10 | `Document_2026-11-04_083342_ocr_hqmax.txt` |
| FAIL | False | 3 | 0 | S1-S3×2,O6×1 | `Document_2026-11-04_083655_ocr_hqmax.txt` |
| FAIL | False | 7 | 0 | O6×6,S1-S3×1 | `Document_2026-11-04_084730_ocr_hqmax.txt` |
| FAIL | False | 16 | 0 | S1-S3×13,O6×3 | `Document_2026-11-04_105927_ocr_hqmax.txt` |
| FAIL | False | 2 | 0 | S1-S3×2 | `Document_2026-11-04_111318_ocr_hqmax.txt` |
| FAIL | False | 7 | 0 | O6×5,S1-S3×2 | `Document_2026-11-04_113633_ocr_hqmax.txt` |
| FAIL | False | 3 | 0 | S1-S3×3 | `Document_2026-11-04_114039_ocr_hqmax.txt` |

## Sample residual hits (after cleanup)

### `Document_2026-11-04_082440_ocr_hqmax.txt` (FAIL)
- `S1-S3` / `two_column_smash`: dley, owned by Susan Alsop
- `S1-S3` / `two_column_smash`: 3rd: Not provided
- `O6` / `owner_tail_trunc`: 2nd: Clayton Clark, owned by
- `O6` / `owner_tail_trunc`: 4th: Brody, owned by

### `Document_2026-11-04_083342_ocr_hqmax.txt` (FAIL)
- `O6` / `owner_tail_trunc`: 5th: Raheen Doc Holiday, owned by Coffey & Cur
- `O6` / `owner_tail_trunc`: 10-12 1/2" Reserve: Lickity Split Lexus, owned by
- `O6` / `owner_tail_trunc`: Fenton', owned by
- `O6` / `owner_tail_trunc`: J, owned by
- `O6` / `owner_tail_trunc`: Three Oaks, owned by
- `O6` / `owner_tail_trunc`: Conformation Champio, owned by
- `O6` / `owner_tail_trunc`: Glenh, owned by
- `O6` / `owner_tail_trunc`: Beacon Be:, owned by
- `O6` / `owner_tail_trunc`: Maven''s T, owned by
- `O6` / `owner_tail_trunc`: Conformation Champion & Best, owned by

### `Document_2026-11-04_083655_ocr_hqmax.txt` (FAIL)
- `S1-S3` / `two_column_smash`: 2nd: jack of Hearts Alfa, owned by Jeff & Connie McKee
- `S1-S3` / `two_column_smash`: 3rd: erry Clower
- `O6` / `owner_tail_trunc`: 12 1/2-15" Champion: Lickity Split Lotta Sass, owned by

### `Document_2026-11-04_084730_ocr_hqmax.txt` (FAIL)
- `S1-S3` / `two_column_smash`: 2nd: s-Rammeliffsi<emtin, owned by Bob Franklin®
- `O6` / `owner_tail_trunc`: Eastlak, owned by
- `O6` / `owner_tail_trunc`: Merrills Mou, owned by
- `O6` / `owner_tail_trunc`: Hopdiggi, owned by
- `O6` / `owner_tail_trunc`: Baybriar's Mr. Ti, owned by
- `O6` / `owner_tail_trunc`: Windy Hill Sug:, owned by
- `O6` / `owner_tail_trunc`: George Jone, owned by

### `Document_2026-11-04_105927_ocr_hqmax.txt` (FAIL)
- `S1-S3` / `two_column_smash`: 4th: nere Solo, owned by Ken Chambers
- `S1-S3` / `two_column_smash`: 5th: patch Jame of Wrenwood, owned by Kimmy Hubbard
- `S1-S3` / `two_column_smash`: 6th: ks Hotspur of Fox Brush, owned by Becker & Trimmer
- `S1-S3` / `two_column_smash`: im, owned by Debra Ellis
- `S1-S3` / `two_column_smash`: ur, owned by Eddy Barrett
- `S1-S3` / `two_column_smash`: ister, owned by Marion Curtis
- `S1-S3` / `two_column_smash`: on, owned by Dwain & Yvonne Moore
- `S1-S3` / `two_column_smash`: oblolly, owned by Debra Ellis
- `S1-S3` / `two_column_smash`: is, owned by Jack & Pauline Fawkes
- `S1-S3` / `two_column_smash`: 2nd: d Steady, owned by Ed Loomis
- `S1-S3` / `two_column_smash`: 6th: rry Chase Dakota, owned by Rick Brennan
- `S1-S3` / `two_column_smash`: ailey, owned by Wayne Holleman

### `Document_2026-11-04_111318_ocr_hqmax.txt` (FAIL)
- `S1-S3` / `two_column_smash`: 1st: t: FOX RUN DEMON, owned by Sandra Ferber
- `S1-S3` / `two_column_smash`: 1st: t: WHITE GATE BOMBER, owned by Nancy & Bill Breakstone

### `Document_2026-11-04_113633_ocr_hqmax.txt` (FAIL)
- `S1-S3` / `two_column_smash`: 1st: pe      1stt Three Oaks Zodiac, owned by Carolyn McGaughey
- `S1-S3` / `two_column_smash`: 1st: a        1stt Wildgoose National, owned by CJ & Ouida Harris
- `O6` / `owner_tail_trunc`: Three Oaks, owned by
- `O6` / `owner_tail_trunc`: Windover Sc, owned by
- `O6` / `owner_tail_trunc`: Reserve Puppy Conforrr, owned by
- `O6` / `owner_tail_trunc`: Rancho Arma, owned by
- `O6` / `owner_tail_trunc`: P:, owned by

### `Document_2026-11-04_114039_ocr_hqmax.txt` (FAIL)
- `S1-S3` / `two_column_smash`: arms, owned by Cheryl Hart
- `S1-S3` / `two_column_smash`: 2nd: of picturesque thoroughbred horse farms, owned by outside
- `S1-S3` / `two_column_smash`: 3rd: julia Brion
