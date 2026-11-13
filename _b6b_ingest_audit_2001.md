# B6b cleanup + ingest audit — 2001

Catalog: `_OCR_CLEANUP_CATALOG_HANDOFF.md`
Volumes: 14  cleaned=12  PASS=8  WARN=0  FAIL=6
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
| PASS | True | 0 | 0 | — | `2001 Coal Tree Farm_ocr_hqmax.txt` |
| PASS | True | 0 | 0 | — | `2001 South Coast_ocr_hqmax.txt` |
| PASS | True | 0 | 0 | — | `2001 Troon Quarry_ocr_hqmax.txt` |
| FAIL | True | 51 | 0 | C1/C6×26,C7×25 | `2001 Vol I_ocr_hqmax.txt` |
| PASS | True | 0 | 0 | — | `2001 MWJRTC II Wheatland I & II_ocr_hqmax.txt` |
| PASS | True | 0 | 0 | — | `2001 OH-PA II_ocr_hqmax.txt` |
| FAIL | True | 7 | 0 | C7×5,C1/C6×2 | `2001 Paumanok Farmstead Dutchess County_ocr_hqmax.txt` |
| PASS | False | 0 | 0 | — | `2001 PNWJRTN_ocr_hqmax.txt` |
| PASS | False | 0 | 0 | — | `2001 Summer Celebration_ocr_hqmax.txt` |
| FAIL | True | 29 | 0 | C7×17,C1/C6×12 | `2001 Vol II pt 1_ocr_hqmax.txt` |
| FAIL | True | 40 | 0 | C7×25,C1/C6×15 | `2001 Vol II pt 2_ocr_hqmax.txt` |
| PASS | True | 0 | 0 | — | `2001 Yankee_ocr_hqmax.txt` |
| FAIL | True | 24 | 0 | C1/C6×15,C7×9 | `2001 Vol III pt 1_ocr_hqmax.txt` |
| FAIL | True | 21 | 0 | C7×12,C1/C6×9 | `2001 Vol III pt 2_ocr_hqmax.txt` |

## Sample residual hits (after cleanup)

### `2001 Vol I_ocr_hqmax.txt` (FAIL)
- `C1/C6` / `incomplete_entries`: Novice Adult                                                                 Ent | places=0/3 | Open Puppy                                             Entri
- `C1/C6` / `incomplete_entries`: Bitches, 1 yr. & older, 10 up to 1212" Entries: 15 | places=0/6 | Bitches, 1 yr. & older, over 12-15" Entries: 12
- `C1/C6` / `incomplete_entries`: Bitches, 1 yr. & older, over 12-15" Entries: 12 | places=0/6 | Judges: Sandra Ferber, Conformation; Mark Bijorkland, Go-to-
- `C1/C6` / `incomplete_entries`: 'hampionship Certificate, 10 up to 12 1/2" Entries: 13 | places=0/6 | Champion: Penelope, owned by Mike & Karen DiBernardo
- `C1/C6` / `incomplete_entries`: hampionship Certificate, 12: up to 15           - Entries: 14 | places=0/6 | Champion: Fox Cry Haley, owned by Mike & Lynda Trulock
- `C1/C6` / `incomplete_entries`: Pre-Novice Puppy                                              Entries: 4 | places=0/4 | Novice Puppy                                                
- `C1/C6` / `incomplete_entries`: "hampionship Certificate, 10 up to 123" Entries: 7 | places=0/6 | hampionship Certificate, 12% up to 15" Entries: 6
- `C1/C6` / `incomplete_entries`: hampionship Certificate, 12% up to 15" Entries: 6 | places=0/6 | eteran Championship Certificate                            E
- `C1/C6` / `incomplete_entries`: Ips, 6 up to 9 months, 10 up to 121" Entries: 3 | places=0/3 | Champion: Marley, owned by lan & Catherine Martin
- `C1/C6` / `incomplete_entries`: Advanced, On Lead                                            Entries: 8 | places=0/6 | Judges: Sandhi Rogerson, Conformation; Mike Bilbo & Stephani
- `C1/C6` / `incomplete_entries`: Veterans, 6 years & older, over 12¥:-15" Entries: 4 | places=0/4 | Judges: Kevin Allen, Conformation; Brenda Treuthardt, Go-to-
- `C1/C6` / `incomplete_entries`: Starters Off Lead, 10 up to 12 1/2" Entries: 4 | places=0/4 | Starters Off Lead, 12 1/2 up to 15" Entries: 1

### `2001 Paumanok Farmstead Dutchess County_ocr_hqmax.txt` (FAIL)
- `C1/C6` / `incomplete_entries`: Off Lead                                                   Entries: 7 | places=0/6 | Agility I, Off Lead Entries: 7
- `C1/C6` / `incomplete_entries`: "hampionship Certificate, 10 up to 121" Entries: 6 | places=0/6 | Champion: Kenswick Kayla, owned by Sandy McElearney
- `C7` / `best_reserve_missing_header`: RESERVE : Conquest Reset, owned by Chris Day
- `C7` / `best_reserve_missing_header`: Reserve: Fox Run Crew, owned by Sandy Ferber
- `C7` / `best_reserve_missing_header`: Reserve: Lickity Split Sassy;, owned by Bob Franklin Fr YTEEI OW YI a = Eaa_ 0 oa
- `C7` / `best_reserve_missing_header`: Best: Farmciiff Pegay, owned by Bob & Genie Franklin
- `C7` / `best_reserve_missing_header`: Reserve: Crosstuff Fuss, owned by Sandra Ferber

### `2001 Vol II pt 1_ocr_hqmax.txt` (FAIL)
- `C1/C6` / `incomplete_entries`: Norking Terrier Bitch, 10 up to r/br Entries: 6 | places=0/6 | JRTCA WORKING TERRIER CHAMPION & RESERVE
- `C1/C6` / `incomplete_entries`: re-Novice Puppy                                              Entries: 6 | places=0/6 | ovice Puppy                                                 
- `C1/C6` / `incomplete_entries`: ovice Puppy                                                    Entries: 12 | places=0/6 | ovice Adult                                                 
- `C1/C6` / `incomplete_entries`: hampionship Certificate, 10 up to 121." Entries: 13 | places=0/6 | Reserve: Amblegreen Breeze, owned by Cyndy Monk
- `C1/C6` / `incomplete_entries`: hampionship Certificate, 12/2 up to 15" Entries: 13 | places=0/6 | Reserve: Stafford Acres Cool Whip, owned by Tina Stafford
- `C1/C6` / `incomplete_entries`: ups, 9 up to 12 months, 10 up to 12 1/2" Entries: 5 | places=0/5 | ups, 9 up to 12 months, over 12 1/2-15" Entries: 6
- `C1/C6` / `incomplete_entries`: ogs, 1 yr. & older, over Entries: 34 | places=0/6 | ogs, 1 yr. & older, over 12-15" Entries: 34
- `C1/C6` / `incomplete_entries`: Suitability to Raccoon/Badger Entries: 10 | places=0/6 | Dog Pups, 6 up to 9 months, r/br                           E
- `C1/C6` / `incomplete_entries`: Veterans, 6 years & older, over 124-15" Entries: 7 | places=0/6 | 10-12 1/2"." Champion: Loon Cove Moxie Brooke, owned by B. J
- `C1/C6` / `incomplete_entries`: Working 1st Eastlake Terrier Willy, Dog, owned 12% up by to Robert 15", Van Der  | places=0/5 | re-Novice Puppy                                             
- `C1/C6` / `incomplete_entries`: Child Handler                                                    Entries: 5 | places=0/5 | Kami Camputh Handler Entries: 7
- `C1/C6` / `incomplete_entries`: Kami Camputh Handler Entries: 7 | places=0/6 | Judges: Sandra Ferber & John Broadhurst, Conformation; Yvonn

### `2001 Vol II pt 2_ocr_hqmax.txt` (FAIL)
- `C1/C6` / `incomplete_entries`: hampionship Certificate, 10 up to 121" Entries: 6 | places=0/6 | Champion: Kenswick Kayla, owned by Sandy McElearney
- `C1/C6` / `incomplete_entries`: Child Handler Entries: 4 | places=0/4 | Entries: 4
- `C1/C6` / `incomplete_entries`: Novice Puppy                                                    Entries: 4 | places=0/4 | Novice Adult                                                
- `C1/C6` / `incomplete_entries`: hampionship Certificate, 10 up to 12 1/2" Entries: 13 | places=0/6 | Reserve: Charade Galore, owned by Jim & Jan Brady
- `C1/C6` / `incomplete_entries`: hampionship Certificate, 12% up to 15" Entries: 3 | places=0/3 | Reserve: Blackfox Skittles, owned by Debbie O'Neill
- `C1/C6` / `incomplete_entries`: Starters Agility                                                  Entries: 16 | places=0/6 | AGILITY I Certificate                                       
- `C1/C6` / `incomplete_entries`: >hampionship Certificate, 12% up to 15" Entries: 11 | places=0/6 | Champion: Ballyblack Trey, owned by J. Gilligan & S. Geroux
- `C1/C6` / `incomplete_entries`: AANENRMATION DIVICION                                     Suitability to Gray Fo | places=0/4 | Dog Pups, 4 up to 6 months, smooth                    Entrie
- `C1/C6` / `incomplete_entries`: AAAMEADEEA TIAN DIVVICINN                                                        | places=0/6 | Dog Pups, 4 up to 6 months, smooth                    Entrie
- `C1/C6` / `incomplete_entries`: Veterans, 6 years & older, 10 up to 12 1/2" Entries: 5 | places=0/5 | Entries: 5
- `C1/C6` / `incomplete_entries`: Bitch Pups, 4 up to 6 months, r/br Entries: 7 | places=0/6 | Best: Rommeny Hellion, owned by Teresa Wellman
- `C1/C6` / `incomplete_entries`: Bitch Pups, 4 up to 6 months, r/br Entries: 6 | places=0/6 | Best: Rommeny Hellion, owned by Teresa Wellman

### `2001 Vol III pt 1_ocr_hqmax.txt` (FAIL)
- `C1/C6` / `incomplete_entries`: Trailing & Locating Adults Entries: 21 | places=0/6 | Champion: Riley, owned by William Haggerty
- `C1/C6` / `incomplete_entries`: Bitch Pups, 6 up to 9 months, smooth Entries: 6 | places=0/6 | Bitch Pups, 6 up to 9 months, r/br                        En
- `C1/C6` / `incomplete_entries`: Bitch Pups, 6 up to 9 months, r/br                        Entries: 10 | places=0/6 | Bitch Pups, 9 up to 12 months, smooth                 Entrie
- `C1/C6` / `incomplete_entries`: Youth Handling Agility, On Lead Entries: 6 | places=0/6 | CONFORMATION DIVISION
- `C1/C6` / `incomplete_entries`: teran Dogs, 6 years & older, over 12¥2-15" Entries: 9 | places=0/6 | steran Bitches, 6 years & older, 10 up to 12 1/2" Entries: 8
- `C1/C6` / `incomplete_entries`: steran Bitches, 6 years & older, 10 up to 12 1/2" Entries: 8 | places=0/6 | steran Bitches, 6 years & older, over 12 1/2-15" Entries: 5
- `C1/C6` / `incomplete_entries`: gs, 1 yr. & older, 10 up to 12 1/2" Entries: 19 | places=0/6 | gs, 1 yr. & older, over 12 1/2-15" Entries: 25
- `C1/C6` / `incomplete_entries`: gs, 1 yr. & older, over 12 1/2-15" Entries: 25 | places=0/6 | ches, 1 yr. & older, 10 up to 12 1/2" Entries: 21
- `C1/C6` / `incomplete_entries`: ches, 1 yr. & older, 10 up to 12 1/2" Entries: 21 | places=0/6 | tches, 1 yr. & older, over 12 1/2-15" Entries: 13
- `C1/C6` / `incomplete_entries`: tches, 1 yr. & older, over 12 1/2-15" Entries: 13 | places=0/6 | steran Bitches, 6 years & older, 10 upto 12%" —_ Entries: 9
- `C1/C6` / `incomplete_entries`: steran Bitches, 6 years & older, 10 upto 12%" —_ Entries: 9 | places=0/6 | steran Bitches, 6 years & older, over 12¥2-15" Entries: 6
- `C1/C6` / `incomplete_entries`: steran Bitches, 6 years & older, over 12¥2-15" Entries: 6 | places=0/6 | steran Dogs, 6 years & older, 10 up to 12/2" Entries: 5

### `2001 Vol III pt 2_ocr_hqmax.txt` (FAIL)
- `C1/C6` / `incomplete_entries`: Veterans Agility I, Off Lead                                    Entries: 4 | places=0/4 | AGILITY HIGH SCORE CHAMPION & RESERVE
- `C1/C6` / `incomplete_entries`: Christina Wagner 2outh Handling Agility, On Lead Entries: 3 | places=0/3 | Veterans, 6 years and older, 10 up to 12 2" Entries: 5
- `C1/C6` / `incomplete_entries`: Bitch, 10 up to 12 Entries: 12 | places=0/6 | Best: Cairnbrae Calamity, owned by Shirley Buist
- `C1/C6` / `incomplete_entries`: Bitch Pups, 4 up to 6 months, r/br Entries: 37 | places=0/6 | Best: Cairnbrae Shambles, owned by Shirley Buist
- `C1/C6` / `incomplete_entries`: Youth Handling Agility, On Lead                           Entries: 10 | places=0/6 | Champion: Ashley Boyd
- `C1/C6` / `incomplete_entries`: Bitch Pups, 4 up to 6 months, r/br Entries: 6 | places=0/6 | Best: Marksworth Emerald, owned by T. Clower/M. Bailiff
- `C7` / `best_reserve_missing_header`: Reserve: Firethorn Jinx, owned by Mary Bayley
- `C7` / `best_reserve_missing_header`: Best: Cairnbrae Calamity, owned by Shirley Buist
- `C7` / `best_reserve_missing_header`: Best: Cairnbrae Shambles, owned by Shirley Buist
- `C7` / `best_reserve_missing_header`: RESERVE : Kingmont Faust, owned by L. Banducci & T. Hofstrand
- `C7` / `best_reserve_missing_header`: Reserve: Naduah Nitro, owned by Sharon Kress
- `C7` / `best_reserve_missing_header`: Best: Live Wire Bark, owned by Charlie & Julie Kemp
