# B6b cleanup + ingest audit — 1999

Catalog: `_OCR_CLEANUP_CATALOG_HANDOFF.md`
Volumes: 6  cleaned=1  PASS=0  WARN=0  FAIL=6
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
| FAIL | False | 27 | 0 | S1-S3×25,O6×2 | `1999 Vol I, pt 1_ocr_hqmax.txt` |
| FAIL | False | 21 | 0 | S1-S3×20,O6×1 | `1999 Vol I, pt 2_ocr_hqmax.txt` |
| FAIL | False | 19 | 0 | S1-S3×18,C1×1 | `1999 Vol II, pt 1_ocr_hqmax.txt` |
| FAIL | False | 5 | 0 | S1-S3×5 | `1999 Vol II, pt 2_ocr_hqmax.txt` |
| FAIL | False | 9 | 0 | S1-S3×9 | `1999 Vol III, pt 1_ocr_hqmax.txt` |
| FAIL | True | 19 | 0 | S1-S3×19 | `1999 Vol III, pt 2_ocr_hqmax.txt` |

## Sample residual hits (after cleanup)

### `1999 Vol I, pt 1_ocr_hqmax.txt` (FAIL)
- `O6` / `owner_tail_trunc`: 10-12 1/2"" Champion: White Stockings Miller Time, owned by ow
- `S1-S3` / `two_column_smash`: 4th: h: Snake River Law Di Dah, owned by Ryann Healy
- `S1-S3` / `two_column_smash`: 5th: h: Quick Silver Misty, owned by Bob & Barbara Ford
- `S1-S3` / `two_column_smash`: 4th: impressive Snoopy Lady, owned by Bonnie Veblen
- `S1-S3` / `two_column_smash`: 5th: i: Moon Rock Molly, owned by Kay Van Patter
- `S1-S3` / `two_column_smash`: 1st: t 3T's Terra, owned by Greg Boyland
- `S1-S3` / `two_column_smash`: 3rd: drd: Sweet Molly Jo, owned by Joseph & Josie Sanchez
- `S1-S3` / `two_column_smash`: 1st: tstt Circle Bar Stella, owned by Tracy Weeshoff
- `S1-S3` / `two_column_smash`: 3rd: drd: Marksworth Markka, owned by Barbara Mathis
- `S1-S3` / `two_column_smash`: 3rd: drd: R.A. Dixie, owned by Arnaldo Mellado
- `S1-S3` / `two_column_smash`: 3rd: lronwater Betsy, owned by Guy & Doris Baylor
- `S1-S3` / `two_column_smash`: 3rd: tstt Sparkle, owned by Autie Sumner

### `1999 Vol I, pt 2_ocr_hqmax.txt` (FAIL)
- `S1-S3` / `two_column_smash`: 4th: h: Loblolly Shameless, owned by Rich & Rebecca Paff
- `S1-S3` / `two_column_smash`: 5th: h: Piccadilly Roxie, owned by John & Judy Tyno
- `S1-S3` / `two_column_smash`: 6th: h: Ranch House Burrito, owned by Lonny Brooks
- `S1-S3` / `two_column_smash`: 6th: pth: Brandywine Hazel, owned by Kathy Standard
- `S1-S3` / `two_column_smash`: 1st: JR, owned by Jack Power
- `S1-S3` / `two_column_smash`: 3rd: drd: Ruff N' Tumble Ginger, owned by Jean Dunham
- `S1-S3` / `two_column_smash`: 4th: h: Arrowhead Anasazi, owned by Scott & Kathy Neus
- `S1-S3` / `two_column_smash`: 5th: h: Lucy, owned by Joe Shapiro
- `S1-S3` / `two_column_smash`: 2nd: wd: Round the Bend Wrinkle, owned by Michelle Ward
- `S1-S3` / `two_column_smash`: 4th: h: Windever Ruffles, owned by Todd & Paula Ryan
- `S1-S3` / `two_column_smash`: 5th: h: BRGR Squirt, owned by Georgia Bucci
- `S1-S3` / `two_column_smash`: 1st: stt Brandywine Sport, owned by Teresa Wellman

### `1999 Vol II, pt 1_ocr_hqmax.txt` (FAIL)
- `C1` / `class_header_gap`: 1st: Chase De Tail, owned by Jim & Kris Tracy
- `S1-S3` / `two_column_smash`: 1st: stt Wishbone, owned by Heather Reid
- `S1-S3` / `two_column_smash`: 1st: stt Black Watch Busy, owned by L.Maher/M.Sanders
- `S1-S3` / `two_column_smash`: 1st: stt Cedardale Oliver, owned by Jan Dale
- `S1-S3` / `two_column_smash`: 1st: stt Fox Run Faber, owned by Teresa Wellman
- `S1-S3` / `two_column_smash`: 1st: stt Westwood Jazz, owned by D. Peck/J. Kozak
- `S1-S3` / `two_column_smash`: 3rd: drd: R.A. Russell, owned by Mike & Linda Trulock
- `S1-S3` / `two_column_smash`: 1st: stt Terrier-ific Nike, owned by Pam Williams
- `S1-S3` / `two_column_smash`: 1st: stt Big Hickory Snickers, owned by Lynn Jerome
- `S1-S3` / `two_column_smash`: 4th: dth: Blackbay Athena, owned by George Anderson
- `S1-S3` / `two_column_smash`: 1st: fstt Skytop Squire, owned by Doug & Sue Tack
- `S1-S3` / `two_column_smash`: 4th: h: Arlins Dill Weed, owned by Alison Linstrum

### `1999 Vol II, pt 2_ocr_hqmax.txt` (FAIL)
- `S1-S3` / `two_column_smash`: 1st: pth: Farmington Charlie, owned by Paul Summers
- `S1-S3` / `two_column_smash`: 6th: pth: Loki, owned by Jerry Stoecklein
- `S1-S3` / `two_column_smash`: 3rd: drd: Farmcliff Chipper, owned by Bob Franklin
- `S1-S3` / `two_column_smash`: 1st: stt R.A. Puck, owned by Ron & Zoe Blair
- `S1-S3` / `two_column_smash`: 1st: stt Cyclone Sally, owned by Sammy & Danetta Hopewell

### `1999 Vol III, pt 1_ocr_hqmax.txt` (FAIL)
- `S1-S3` / `two_column_smash`: 1st: t 3T'sT.S. Eliot, owned by T.Ebert/T.Toriello
- `S1-S3` / `two_column_smash`: 1st: stt Charade Ivory, owned by Jim & Jan Brady
- `S1-S3` / `two_column_smash`: 4th: h: Pheasant Hill Rocki, owned by Scott & Susan Aeppli
- `S1-S3` / `two_column_smash`: 5th: h: Korikian Jasmine, owned by Robert Korikian
- `S1-S3` / `two_column_smash`: 6th: h: Marvelous Leapin' Lizzie, owned by Megan Walker
- `S1-S3` / `two_column_smash`: 1st: fst Seaview Solar Spot, owned by Didi Gough
- `S1-S3` / `two_column_smash`: 5th: JR, owned by Ken Sanders
- `S1-S3` / `two_column_smash`: 2nd: iootsie, owned by Teresa Russell
- `S1-S3` / `two_column_smash`: 1st: ibe Courtwood Crush, owned by Rusty & Debbie Graydon

### `1999 Vol III, pt 2_ocr_hqmax.txt` (FAIL)
- `S1-S3` / `two_column_smash`: 2nd: hunters Green Pluto, owned by Antonio & Barbara Sullo
- `S1-S3` / `two_column_smash`: 6th: pth: Windy View Questor, owned by William O'Brien
- `S1-S3` / `two_column_smash`: 4th: si: 3TsT.S. Eliot, owned by T.Ebert/T.Toriello
- `S1-S3` / `two_column_smash`: 1st: JR, owned by Pete & Linda Frey
- `S1-S3` / `two_column_smash`: 3rd: drd: Max, owned by Betsy Downing
- `S1-S3` / `two_column_smash`: 1st: dth: Sneaky Sid Lou, owned by Julie Grim
- `S1-S3` / `two_column_smash`: 1st: stt Lucy, owned by Robb & Susan Pieper
- `S1-S3` / `two_column_smash`: 4th: gt: Cedardale Jake, owned by Lindsey Moore
- `S1-S3` / `two_column_smash`: 1st: Bo, owned by Tamerie Ballance
- `S1-S3` / `two_column_smash`: 6th: pth: Harrison, owned by Erin Fitzgerald
- `S1-S3` / `two_column_smash`: 6th: gt: Badakhashan Tucker, owned by Mike & Sharon Roberts
- `S1-S3` / `two_column_smash`: 1st: jst: Ash Creek Lexus, owned by J.Goodman/T.Gottlieb
