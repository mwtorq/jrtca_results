# B6b cleanup + ingest audit — 1997

Catalog: `_OCR_CLEANUP_CATALOG_HANDOFF.md`
Volumes: 4  cleaned=0  PASS=0  WARN=0  FAIL=4
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
| FAIL | False | 25 | 0 | S1-S3×23,O6×2 | `1997 Vol I pt 1_ocr_hqmax.txt` |
| FAIL | False | 27 | 0 | S1-S3×26,C1×1 | `1997 Vol I pt 2_ocr_hqmax.txt` |
| FAIL | False | 23 | 0 | S1-S3×22,C1×1 | `1997 Vol II pt 1_ocr_hqmax.txt` |
| FAIL | False | 10 | 0 | S1-S3×10 | `1997 Vol II pt 2_ocr_hqmax.txt` |

## Sample residual hits (after cleanup)

### `1997 Vol I pt 1_ocr_hqmax.txt` (FAIL)
- `S1-S3` / `two_column_smash`: 1st: fst: Lost Creek Ruby, owned by Debbie McWilliams
- `S1-S3` / `two_column_smash`: 1st: pn            1stt Wheezer, owned by Suzie & Greg Barton
- `S1-S3` / `two_column_smash`: 1st: stt Texas, owned by Anne Detreville
- `S1-S3` / `two_column_smash`: 1st: an            1stt Maypole Crazy, owned by Sally Yancey
- `S1-S3` / `two_column_smash`: 1St: o€aview oabrina, owned by uldi Lough
- `S1-S3` / `two_column_smash`: 1st: stt Marksworth Jinx, owned by Stephanie Giddens
- `S1-S3` / `two_column_smash`: 1st: pi            1stt Deep Run Derek, owned by John & Vicky Brown
- `S1-S3` / `two_column_smash`: 6th: r=            6th. Ravenswood Rasp, owned by Ben & Janet Sutcliffe
- `S1-S3` / `two_column_smash`: 1st: stt R.A. Snickers, owned by Arnaldo Mellado
- `S1-S3` / `two_column_smash`: 3rd: stt Rascal, owned by Melissa Croft
- `S1-S3` / `two_column_smash`: 1st: stt Gunsmoke Fancy, owned by Kenneth & Rose Cox
- `S1-S3` / `two_column_smash`: 1st: fst Patimac Twister, owned by Railine Scott

### `1997 Vol I pt 2_ocr_hqmax.txt` (FAIL)
- `C1` / `class_header_gap`: 1st: Fox Run Scout, owned by Gerald & Joanne Von Essen
- `S1-S3` / `two_column_smash`: 1st: stt Conquest Gone West, owned by Neil & Pam Caine
- `S1-S3` / `two_column_smash`: 1st: stt Bowery Bud, owned by Michelle Davies
- `S1-S3` / `two_column_smash`: 3rd: drd: Luke MacTavish of Glenwood, owned by Bruce Glen
- `S1-S3` / `two_column_smash`: 4th: h: Killare Hunter, owned by Judi Bower
- `S1-S3` / `two_column_smash`: 5th: h: Fox Run Topper, owned by Rick & Mary Thornton
- `S1-S3` / `two_column_smash`: 6th: h: Briarpatch Zoe, owned by Roger & Tabby Shury
- `S1-S3` / `two_column_smash`: 5th: h: Riverview Calvin, owned by Karen Vernon
- `S1-S3` / `two_column_smash`: 6th: h: Elvis, owned by Susan Travaglini
- `S1-S3` / `two_column_smash`: 1st: stt Deep Run Derek, owned by John & Vicki Brown
- `S1-S3` / `two_column_smash`: 1st: stt The Folly Lucy, owned by Rick & Mary Thornton
- `S1-S3` / `two_column_smash`: 4th: h: Briarpatch Mohawk, owned by Chuck & Diana Hufnagel

### `1997 Vol II pt 1_ocr_hqmax.txt` (FAIL)
- `C1` / `class_header_gap`: 3rd: Farmliff Tackle, owned by Megan Johnson
- `S1-S3` / `two_column_smash`: 2nd: rarmciir crile, owned by py bob rrankliin
- `S1-S3` / `two_column_smash`: 6th: lino Jack, owned by George & Miwa lino
- `S1-S3` / `two_column_smash`: 5th: lino Jack, owned by George & Miwa lino
- `S1-S3` / `two_column_smash`: 3rd: lino Jack, owned by George & Miwa lino
- `S1-S3` / `two_column_smash`: 6th: lean, owned by Sharon Kelleher
- `S1-S3` / `two_column_smash`: 6th: windermere Tussle, owned by Linda Cowasjee
- `S1-S3` / `two_column_smash`: 5th: easton Point Skipper, owned by Sally Gay
- `S1-S3` / `two_column_smash`: 6th: est: Tortilla Flat Flurry, owned by Deborah Holly
- `S1-S3` / `two_column_smash`: 5th: h: Briarpatch Bultaco, owned by Karen Wass
- `S1-S3` / `two_column_smash`: 6th: h: Glynnsong Buddy, owned by Sue/Elizabeth Murphree
- `S1-S3` / `two_column_smash`: 4th: dth: DC Sweet Boy, owned by Bonita Knickmeyer

### `1997 Vol II pt 2_ocr_hqmax.txt` (FAIL)
- `S1-S3` / `two_column_smash`: 3rd: timber Ridge Rudger, owned by Jan Bell
- `S1-S3` / `two_column_smash`: 2nd: JR, owned by Pete Frey
- `S1-S3` / `two_column_smash`: 6th: lino Jack, owned by George & Miwa lino
- `S1-S3` / `two_column_smash`: 6th: rarmclilt Rudi, owned by Larey LUIS A SRE4 JF PS dE" 4 SNEED. LN ..4do® amu
- `S1-S3` / `two_column_smash`: 6th: Not Provided
- `S1-S3` / `two_column_smash`: Best: not provided by trial chairman
- `S1-S3` / `two_column_smash`: 5th: Not provided by Trial Chairperson i
- `S1-S3` / `two_column_smash`: 3rd: Not Provided by Trial Chairperson
- `S1-S3` / `two_column_smash`: 1st: i.
