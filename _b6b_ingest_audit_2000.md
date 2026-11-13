# B6b cleanup + ingest audit — 2000

Catalog: `_OCR_CLEANUP_CATALOG_HANDOFF.md`
Volumes: 5  cleaned=1  PASS=0  WARN=0  FAIL=5
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
| FAIL | True | 28 | 0 | S1-S3×25,O6×2,C1×1 | `2000 Vol I_ocr_hqmax.txt` |
| FAIL | False | 28 | 0 | S1-S3×27,C1×1 | `2000 Vol II_ocr_hqmax.txt` |
| FAIL | False | 21 | 0 | S1-S3×21 | `2000 vol 3 pt 1_ocr_hqmax.txt` |
| FAIL | False | 25 | 0 | S1-S3×25 | `2000 Vol III pt 1_ocr_hqmax.txt` |
| FAIL | False | 11 | 0 | S1-S3×11 | `2000 Vol III pt 2_ocr_hqmax.txt` |

## Sample residual hits (after cleanup)

### `2000 Vol I_ocr_hqmax.txt` (FAIL)
- `C1` / `class_header_gap`: 4th: Hideaway Farms Hunter, owned by Ken & Penny Baker
- `S1-S3` / `two_column_smash`: 1st: stt Fox Tale Boone, owned by Dan & June Schepman
- `S1-S3` / `two_column_smash`: 4th: h: Crossewinds Riddle, owned by K.Lawson/L.Pobjecky
- `S1-S3` / `two_column_smash`: 5th: h: Millbrook Farms Tristen, owned by Jamie Arjona
- `S1-S3` / `two_column_smash`: 3rd: drd: George Costanza, owned by Ernest Bilinski
- `S1-S3` / `two_column_smash`: 4th: tt: Charade Ivory, owned by Jim & Jan Brady
- `S1-S3` / `two_column_smash`: 3rd: drd: Piccadilly Bailey, owned by John & Judy Tyno
- `S1-S3` / `two_column_smash`: 3rd: drd: Fox Run Ace, owned by Lori Thompson
- `S1-S3` / `two_column_smash`: 4th: ih: Smokey Mountain Crash, owned by Mary Clark
- `S1-S3` / `two_column_smash`: 3rd: drd: Westgate Rocket, owned by B. Jordan/J. Westgate
- `S1-S3` / `two_column_smash`: 3rd: drd: Quail Oak Montana, owned by Greg Boyland
- `S1-S3` / `two_column_smash`: 3rd: drd: Cotswold Rio, owned by Jo Paddison

### `2000 Vol II_ocr_hqmax.txt` (FAIL)
- `C1` / `class_header_gap`: 2nd: Cromwell Covergirl, owned by Jane McClay
- `S1-S3` / `two_column_smash`: 3rd: ord : ra rmcliff Kate, owned by Bob Franklin
- `S1-S3` / `two_column_smash`: 3rd: ord: Frarmclit Spritzer, owned by Scott & Valerie Bidwell
- `S1-S3` / `two_column_smash`: 3rd: dra: Farmcliff Spritzer, owned by Valerie & Scat Ridwell
- `S1-S3` / `two_column_smash`: 2nd: lth: Still River Misty Girl, owned by Donna Seckler
- `S1-S3` / `two_column_smash`: 1st: stt FoxiLoxi Codi, owned by Scott & Susan Aeppli
- `S1-S3` / `two_column_smash`: 1st: rarmclit Folland, owned by Doug & Sue Tack
- `S1-S3` / `two_column_smash`: 1st: stt Little Eden Obsession, owned by Michelle Ward
- `S1-S3` / `two_column_smash`: 1st: stt Little Eden Thriller, owned by Michelle Ward
- `S1-S3` / `two_column_smash`: 1st: ol. WIUSUIE RUSSEI Lamp, owned by Jill Goodman
- `S1-S3` / `two_column_smash`: 4th: ih: Tally M's Bo, owned by Tammy Carpenter
- `S1-S3` / `two_column_smash`: 4th: h: Russellville Emmit, owned by Barb & Mike Enright

### `2000 vol 3 pt 1_ocr_hqmax.txt` (FAIL)
- `S1-S3` / `two_column_smash`: 2nd: id: Hart Farms Isaac, owned by Cheryl Hart
- `S1-S3` / `two_column_smash`: 4th: h: Shenanigans Will, owned by Sue Zeiher
- `S1-S3` / `two_column_smash`: 2nd: id: Sow's Ear Julien, owned by Karen McCarthy
- `S1-S3` / `two_column_smash`: 1st: stt Highland Trace, owned by Molly Rombach
- `S1-S3` / `two_column_smash`: 1st: leserve: The Wild West Hank, owned by Lloyd & Ann Wendiand
- `S1-S3` / `two_column_smash`: 4th: h: Jack of Hearts Ace, owned by Joan Hardie
- `S1-S3` / `two_column_smash`: 6th: h: Cotswold Cosmo, owned by Marney McGovern
- `S1-S3` / `two_column_smash`: 4th: h: Maggie, owned by Adam & Kelley Campbell
- `S1-S3` / `two_column_smash`: 4th: h: Glenhaven Belle, owned by Geri Morin
- `S1-S3` / `two_column_smash`: 5th: h: Limberwicke Scoop, owned by Joyce Robin
- `S1-S3` / `two_column_smash`: 6th: h: Little Eden Reveille, owned by Michelle Ward
- `S1-S3` / `two_column_smash`: 2nd: id: Kenswick Kayla, owned by Joel & Sandy McElearney

### `2000 Vol III pt 1_ocr_hqmax.txt` (FAIL)
- `S1-S3` / `two_column_smash`: 1st: hampion: Rainland Flurry, owned by Cathy Hedberg
- `S1-S3` / `two_column_smash`: 2nd: teserve: Yeha-Noha Simone, owned by Baker/Freimark/Campbell
- `S1-S3` / `two_column_smash`: 1st: hampion: Rainland Farm Fancy, owned by Shirley Kostric
- `S1-S3` / `two_column_smash`: 2nd: leserve: The Wild West Hank, owned by Lloyd & Ann Wendland
- `S1-S3` / `two_column_smash`: 1st: stt: Sweetgrass Nelson, owned by Roger & Caryn Funk
- `S1-S3` / `two_column_smash`: 1st: stt Sow's Ear Seabee, owned by John Renfro
- `S1-S3` / `two_column_smash`: 1st: stt Forest Run Tigger, owned by Doug & Heather Calhoun
- `S1-S3` / `two_column_smash`: 1st: stt Fox Run Abby, owned by Sara Jansen
- `S1-S3` / `two_column_smash`: 1st: stt Natural Instinct Jewel, owned by Ken & Kathy Bushell
- `S1-S3` / `two_column_smash`: 1st: stt Nick, owned by Carole Nicholson
- `S1-S3` / `two_column_smash`: 1st: pth: Button Top Stinger, owned by Debby Calloway
- `S1-S3` / `two_column_smash`: 6th: pth: Little Eden Reveille, owned by Michelle Ward

### `2000 Vol III pt 2_ocr_hqmax.txt` (FAIL)
- `S1-S3` / `two_column_smash`: 4th: AJ, owned by Bev Hirt
- `S1-S3` / `two_column_smash`: 3rd: AJ, owned by Bev Hirt
- `S1-S3` / `two_column_smash`: 1st: ora: Farrier Point Ranger, owned by Denise Neuner
- `S1-S3` / `two_column_smash`: 4th: h: Brandywine Rosita, owned by Tom Colimar
- `S1-S3` / `two_column_smash`: 1st: tstt Little Eden Bristle, owned by Sandy Kitley
- `S1-S3` / `two_column_smash`: 1st: limber Ridge Rogue, owned by Wayne & Samara Deavers
- `S1-S3` / `two_column_smash`: 2nd: end: Impressive Maxie Mog, owned by Richard & Carol Maggetti
- `S1-S3` / `two_column_smash`: 3rd: didn't compete
