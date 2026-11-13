# B6b cleanup + ingest audit — 2001

Catalog: `_OCR_CLEANUP_CATALOG_HANDOFF.md`
Volumes: 14  cleaned=2  PASS=2  WARN=0  FAIL=12
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
| FAIL | False | 1 | 0 | S1-S3×1 | `2001 Coal Tree Farm_ocr_hqmax.txt` |
| FAIL | False | 23 | 0 | S1-S3×23 | `2001 South Coast_ocr_hqmax.txt` |
| FAIL | False | 3 | 0 | S1-S3×2,C1×1 | `2001 Troon Quarry_ocr_hqmax.txt` |
| FAIL | False | 29 | 0 | S1-S3×25,C1×4 | `2001 Vol I_ocr_hqmax.txt` |
| PASS | False | 0 | 0 | — | `2001 MWJRTC II Wheatland I & II_ocr_hqmax.txt` |
| PASS | False | 0 | 0 | — | `2001 OH-PA II_ocr_hqmax.txt` |
| FAIL | False | 4 | 0 | S1-S3×4 | `2001 Paumanok Farmstead Dutchess County_ocr_hqmax.txt` |
| FAIL | False | 1 | 0 | S1-S3×1 | `2001 PNWJRTN_ocr_hqmax.txt` |
| FAIL | False | 4 | 0 | S1-S3×4 | `2001 Summer Celebration_ocr_hqmax.txt` |
| FAIL | False | 26 | 0 | S1-S3×25,C1×1 | `2001 Vol II pt 1_ocr_hqmax.txt` |
| FAIL | False | 29 | 0 | S1-S3×27,C1×2 | `2001 Vol II pt 2_ocr_hqmax.txt` |
| FAIL | False | 3 | 0 | S1-S3×2,O6×1 | `2001 Yankee_ocr_hqmax.txt` |
| FAIL | True | 25 | 0 | S1-S3×25 | `2001 Vol III pt 1_ocr_hqmax.txt` |
| FAIL | True | 20 | 0 | S1-S3×19,C1×1 | `2001 Vol III pt 2_ocr_hqmax.txt` |

## Sample residual hits (after cleanup)

### `2001 Coal Tree Farm_ocr_hqmax.txt` (FAIL)
- `S1-S3` / `two_column_smash`: 1st: stt Larches Pistol Pete, owned by Angela Chmura

### `2001 South Coast_ocr_hqmax.txt` (FAIL)
- `S1-S3` / `two_column_smash`: 1st: stt Land's End Bully, owned by Didi Gough
- `S1-S3` / `two_column_smash`: 5th: h: Treesbank Josie, owned by Carmen & Pat Tosto
- `S1-S3` / `two_column_smash`: 1st: stt Seaview Pippen, owned by Helen Button
- `S1-S3` / `two_column_smash`: 4th: h: Quail Oak Cooper, owned by Kathy & Taylor Wilkinson
- `S1-S3` / `two_column_smash`: 1st: stt: Runamuk Levi, owned by Bud & Sharon Green
- `S1-S3` / `two_column_smash`: 4th: h: Ivy Knoll K.L. Smith, owned by Steve & Pat Berry
- `S1-S3` / `two_column_smash`: 1st: stt Seaview Anubis, owned by Didi Gough
- `S1-S3` / `two_column_smash`: 4th: h: Seaview Geo, owned by David Tannin
- `S1-S3` / `two_column_smash`: 1st: stt Seaview Salty, owned by Didi Gough
- `S1-S3` / `two_column_smash`: 4th: h: Foxton Locks Tom, owned by Cheryl Costello
- `S1-S3` / `two_column_smash`: 5th: h: Foxton Locks Ringo, owned by Cheryl Costello
- `S1-S3` / `two_column_smash`: 1st: stt Salt Valley Top Kat, owned by Jan Finnerty

### `2001 Troon Quarry_ocr_hqmax.txt` (FAIL)
- `C1` / `class_header_gap`: 6th: Conquest Bali, owned by John Mohon
- `S1-S3` / `two_column_smash`: 4th: dth: Daytona Chaser, owned by Brenda Treuthardt
- `S1-S3` / `two_column_smash`: 1st: pth: Firethom Jinx, owned by Lloyd Wendland

### `2001 Vol I_ocr_hqmax.txt` (FAIL)
- `C1` / `class_header_gap`: 5th: Button Top Speed, owned by Flo Clark
- `C1` / `class_header_gap`: 3rd: Lakeshore Jiminy Cricket, owned by Dale & Cathy Larson
- `C1` / `class_header_gap`: 3rd: Stryder Quinn, owned by Daina Fiddler
- `C1` / `class_header_gap`: 6th: Conquest Bali, owned by John Mohon
- `S1-S3` / `two_column_smash`: 6th: h: Luke, owned by Tracey Luggiero
- `S1-S3` / `two_column_smash`: 4th: h: Heartstone Dax, owned by Lynn Jerome
- `S1-S3` / `two_column_smash`: 4th: h: Rain Dance Apache, owned by Pam Shepherd
- `S1-S3` / `two_column_smash`: 6th: h: Bandit, owned by Reece Bumsed
- `S1-S3` / `two_column_smash`: 2nd: lronwater Bubba Dillon, owned by Guy & Doris Baylor
- `S1-S3` / `two_column_smash`: 4th: dth: Terrier-ific Pharaoah, owned by Kimberly Morales
- `S1-S3` / `two_column_smash`: 2nd: hampion: DiBo's Den Lacie, owned by Anita Herman
- `S1-S3` / `two_column_smash`: 1st: hampion: Penelope, owned by Mike & Karen DiBernardo

### `2001 Paumanok Farmstead Dutchess County_ocr_hqmax.txt` (FAIL)
- `S1-S3` / `two_column_smash`: CONFORMATIONDIVISION
- `S1-S3` / `two_column_smash`: 1st: onc:    Whispering oo  epsi, owned by M. & R Minutello
- `S1-S3` / `two_column_smash`: 1st: hampion: Kenswick Kayla, owned by Sandy McElearney
- `S1-S3` / `two_column_smash`: 2nd: eserve: Double D Tally Ho, owned by Dorothy Whiting

### `2001 PNWJRTN_ocr_hqmax.txt` (FAIL)
- `S1-S3` / `two_column_smash`: 1st: oaiishan Inrasher, owned by Lois Clough

### `2001 Summer Celebration_ocr_hqmax.txt` (FAIL)
- `S1-S3` / `two_column_smash`: 2nd: ond Bridle Creek Britches, owned by Phil & Debbie Johnson
- `S1-S3` / `two_column_smash`: 4th: si: Heaven Hill Winder, owned by Billy Shores
- `S1-S3` / `two_column_smash`: 4th: si: Blue Grass Pepsi, owned by Teresa Baker
- `S1-S3` / `two_column_smash`: 2nd: ond GA Mountains Scamp, owned by Dotti Fryer

### `2001 Vol II pt 1_ocr_hqmax.txt` (FAIL)
- `C1` / `class_header_gap`: 4th: Skyline Orchard Harry Potter, owned by N. Cook & J. Ulrich
- `S1-S3` / `two_column_smash`: 4th: h: Taco Bill, owned by Ruth Evans
- `S1-S3` / `two_column_smash`: 5th: h: Luke, owned by Steve Bannon & Tracy Luggiero
- `S1-S3` / `two_column_smash`: 6th: h: Copper Horse Salty Dog, owned by David & Lisa McKinney
- `S1-S3` / `two_column_smash`: 4th: h: Chase D'Tail, owned by Jim & Kris Tracy
- `S1-S3` / `two_column_smash`: 5th: h: Indian River Dr. Spencer Kovak, owned by M. &E. Billinski
- `S1-S3` / `two_column_smash`: 1st: onc:      The Larches Spirit,  owned by Virginia Mei
- `S1-S3` / `two_column_smash`: 1st: di: Ash Creek Tally Ho, owned by Kari Streicher
- `S1-S3` / `two_column_smash`: 6th: pth: Somerstar KJ, owned by Ward & Renee Skinner
- `S1-S3` / `two_column_smash`: 4th: jth: Jake Man, owned by Steve & Sandy Langheld
- `S1-S3` / `two_column_smash`: 1st: mar rams Racee, owned by Dy Lneryl nar
- `S1-S3` / `two_column_smash`: 1st: stt MacKenzie Alexander, owned by Chris Diak & Nicole Roberts

### `2001 Vol II pt 2_ocr_hqmax.txt` (FAIL)
- `C1` / `class_header_gap`: 6th: Jennifer Phillips
- `C1` / `class_header_gap`: 6th: Stafford Acres Cool Whip, owned by Tina Stafford
- `S1-S3` / `two_column_smash`: 1st: si: Kress Country Rebound, owned by Sharon Kress
- `S1-S3` / `two_column_smash`: 4th: h: Whispering Winds Pepsi, owned by M. & R. Minutello
- `S1-S3` / `two_column_smash`: 5th: h: Famstead Puzzle, owned by Judy Galterio
- `S1-S3` / `two_column_smash`: 6th: h: Tema Fox Bella, owned by Cindy Parmenter
- `S1-S3` / `two_column_smash`: 4th: try Relentless, owned by S. Kress
- `S1-S3` / `two_column_smash`: 4th: est: Salishan Sterling, owned by Lois Clough
- `S1-S3` / `two_column_smash`: 5th: leserve: Westgate BB, owned by B. Jordan & J. Westgate
- `S1-S3` / `two_column_smash`: 6th: hampion: Salishan Sterling, owned by Lois Clough
- `S1-S3` / `two_column_smash`: 6th: hampion: Salishan Seige, owned by Lois Clough
- `S1-S3` / `two_column_smash`: 1st: hampion: Amblegreen Breeze, owned by Cyndy Monk

### `2001 Yankee_ocr_hqmax.txt` (FAIL)
- `S1-S3` / `two_column_smash`: 3rd:    a, Creek Theft, owned by
- `S1-S3` / `two_column_smash`: 0st: a CharnpiamIERIS lit Sassyowned AYIBRRICH nk
- `O6` / `owner_tail_trunc`: 3rd:    a, Creek Theft, owned by

### `2001 Vol III pt 1_ocr_hqmax.txt` (FAIL)
- `S1-S3` / `two_column_smash`: 1st: i]     Jake Man, owned by Sandy & Steve Langheld
- `S1-S3` / `two_column_smash`: 1st: hampion: Paxton Imber, owned by Rick & Joy Helms
- `S1-S3` / `two_column_smash`: 2nd: eserve: Meadowlake Bagger, owned by Lisa Venske
- `S1-S3` / `two_column_smash`: 3rd: JR, owned by Sally Hall
- `S1-S3` / `two_column_smash`: 1st: gi: Hillside Josie, owned by Karen Vemon
- `S1-S3` / `two_column_smash`: 4th: h: Blackbum ZZ Top Dog, owned by Jerry Waelterman
- `S1-S3` / `two_column_smash`: 4th: h: Conquest Rouge, owned by Brooks Kelley & Joe Shapiro
- `S1-S3` / `two_column_smash`: 1st: stt Harts Farm Splash, owned by Cheryl Hart
- `S1-S3` / `two_column_smash`: 6th: i; Dudley, owned by Cathy Larson
- `S1-S3` / `two_column_smash`: 2nd: id: Abby, owned by Richard & Annette Kent
- `S1-S3` / `two_column_smash`: 3rd: d;-=Farmcliff- Snowflake;, owned by Bob:& Genie Franklin
- `S1-S3` / `two_column_smash`: 5th: ih: Whispering Winds Pepsi, owned by R. & M. Minutello

### `2001 Vol III pt 2_ocr_hqmax.txt` (FAIL)
- `C1` / `class_header_gap`: 5th: Lilly, owned by Donna Nolan
- `S1-S3` / `two_column_smash`: 6th: i:Farmcliff-Joe;, owned by Bob Franklin
- `S1-S3` / `two_column_smash`: 1st: stt Fartzach, owned by Mary Kuzmar/Paul Jayko
- `S1-S3` / `two_column_smash`: 6th: pth: Chase D' Tall, owned by Kris Tracy
- `S1-S3` / `two_column_smash`: 2nd: on:      Whispering Winds Danny, owned by Ken Winfield
- `S1-S3` / `two_column_smash`: 2nd: arc: Ashland Chaos, owned by Barbara Bancroft
- `S1-S3` / `two_column_smash`: 1st: stt Green Gate Tomba, owned by Joe & Priscilla Testa
- `S1-S3` / `two_column_smash`: 4th: thh Conasauga BeeBee, owned by Daphne Duval
- `S1-S3` / `two_column_smash`: 4th: jth: Terrier-ific Wolfman Jac, owned by Mary Cooper
- `S1-S3` / `two_column_smash`: 1st: stt Brown's Valley Mustang Sally, owned by L. & A. Wendland
- `S1-S3` / `two_column_smash`: 6th: gt: Circle G Carmel, owned by Diane Habel
- `S1-S3` / `two_column_smash`: 1st: jst: Kenswick Rigby, owned by Stephanie Archer
