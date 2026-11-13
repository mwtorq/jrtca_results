# B6b cleanup + ingest audit — 1998

Catalog: `_OCR_CLEANUP_CATALOG_HANDOFF.md`
Volumes: 7  cleaned=0  PASS=1  WARN=0  FAIL=6
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
| FAIL | False | 16 | 0 | S1-S3×13,O6×2,C1×1 | `1998 Vol I, pt 1_ocr_hqmax.txt` |
| PASS | False | 0 | 0 | — | `1998 Vol I, pt 2_ocr_hqmax.txt` |
| FAIL | False | 2 | 0 | S1-S3×2 | `1998 Vol I, pt 3_ocr_hqmax.txt` |
| FAIL | False | 8 | 0 | S1-S3×8 | `1998 Vol II, pt 1_ocr_hqmax.txt` |
| FAIL | False | 3 | 0 | S1-S3×3 | `1998 Vol II, pt 2_ocr_hqmax.txt` |
| FAIL | False | 14 | 0 | S1-S3×13,O6×1 | `1998 Vol III, pt 1_ocr_hqmax.txt` |
| FAIL | False | 6 | 0 | S1-S3×5,C1×1 | `1998 Vol III, pt 2_ocr_hqmax.txt` |

## Sample residual hits (after cleanup)

### `1998 Vol I, pt 1_ocr_hqmax.txt` (FAIL)
- `C1` / `class_header_gap`: 1st: New Market Dixie.
- `S1-S3` / `two_column_smash`: 6th: lino Jack, owned by George & Miwa lino
- `S1-S3` / `two_column_smash`: 3rd: lronwater Winchester, owned by Cedric & Sharon Lavender
- `S1-S3` / `two_column_smash`: 1st: v_th: Sadie, owned by Chris Fraley
- `S1-S3` / `two_column_smash`: 3rd: drd: Ransom, owned by Jeff Lyda
- `S1-S3` / `two_column_smash`: 1st: vist: Heaven Hill Jezebel, owned by Chris Fraley
- `S1-S3` / `two_column_smash`: 5th: lronhorse Money Penny, owned by Rae DesRochers
- `S1-S3` / `two_column_smash`: 3rd: JR, owned by Pete & Linda Frey
- `S1-S3` / `two_column_smash`: 4th: JR, owned by Pete & Linda Frey
- `S1-S3` / `two_column_smash`: 6th: JR, owned by Pete & Linda Frey
- `S1-S3` / `two_column_smash`: 1st: ora: Larry, owned by Diana Fiddler
- `S1-S3` / `two_column_smash`: 6th: Not Provided

### `1998 Vol I, pt 3_ocr_hqmax.txt` (FAIL)
- `S1-S3` / `two_column_smash`: 5th: lino Jack, owned by George & Miwa lino
- `S1-S3` / `two_column_smash`: 3rd: dni Manica Eire mearemm od Bee. P%' 3. 1 A a Fr FE

### `1998 Vol II, pt 1_ocr_hqmax.txt` (FAIL)
- `S1-S3` / `two_column_smash`: 3rd: rg: Katie Clover, owned by Natalene Luming
- `S1-S3` / `two_column_smash`: 1st: ofa: beep Run Razor, owned by Vicki Brown
- `S1-S3` / `two_column_smash`: 2nd: dill, owned by Tresa Ivins
- `S1-S3` / `two_column_smash`: 4th: h: Daytona Chaser, owned by Brenda Treuthardt
- `S1-S3` / `two_column_smash`: 5th: h: Badger Paw Dax, owned by Kirk Dickinson
- `S1-S3` / `two_column_smash`: 3rd: Not Provided
- `S1-S3` / `two_column_smash`: 1st: Not Provided by Trial Chairperson
- `S1-S3` / `two_column_smash`: 3rd: Not Provided by Trial Chairperson

### `1998 Vol II, pt 2_ocr_hqmax.txt` (FAIL)
- `S1-S3` / `two_column_smash`: 1st: rarmcitt Wendv, owned by bv Bob Franklin
- `S1-S3` / `two_column_smash`: 5th: Not Provided by Trial Chairperson
- `S1-S3` / `two_column_smash`: 4th: i271 nwwined hv M Tharntan/Q Cthrictanenn

### `1998 Vol III, pt 1_ocr_hqmax.txt` (FAIL)
- `S1-S3` / `two_column_smash`: 1st: JR, owned by Ron Chiles
- `S1-S3` / `two_column_smash`: 4th: h: Pine Creek Little Nemo, owned by Rhonda Rebhom
- `S1-S3` / `two_column_smash`: 5th: h: Gilbert, owned by Jane Griffin
- `S1-S3` / `two_column_smash`: 6th: h: Bowery Tuppence, owned by Rhonda Rebhorn
- `S1-S3` / `two_column_smash`: 3rd: J, owned by Marlene Berthault
- `S1-S3` / `two_column_smash`: 2nd: J, owned by Marlene Berthault
- `S1-S3` / `two_column_smash`: 3rd: J, owned by Marline Berthault
- `S1-S3` / `two_column_smash`: 3rd: h: Shilo, owned by Debbie Mutimer
- `S1-S3` / `two_column_smash`: 4th: h: Westgate Rocket, owned by J.Westgate/B.Jordan
- `S1-S3` / `two_column_smash`: 2nd: id: Pat's Jack, owned by Pat Harrington
- `S1-S3` / `two_column_smash`: 4th: h: Dashaway Piper, owned by S.Birdsall/V.Darrow
- `S1-S3` / `two_column_smash`: 4th: h: Hi-Flashun Angela, owned by Marilynn Pryor

### `1998 Vol III, pt 2_ocr_hqmax.txt` (FAIL)
- `C1` / `class_header_gap`: 16th: Annual JRTCA National Trial
- `S1-S3` / `two_column_smash`: ipper, owned by Pat Weber
- `S1-S3` / `two_column_smash`: ke, owned by Karen Fitzpatrick
- `S1-S3` / `two_column_smash`: 6th: lino Jack, owned by George lino
- `S1-S3` / `two_column_smash`: 1st: misty morning nodeo, owned by Ledric &« oliaron Lavenauer
