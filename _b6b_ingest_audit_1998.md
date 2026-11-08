# B6b cleanup + ingest audit — 1998

Catalog: `_OCR_CLEANUP_CATALOG_HANDOFF.md`
Volumes: 7  cleaned=6  PASS=1  WARN=6  FAIL=0
Year verdict: **WARN**  SQL-apply unlock: YES

## Intent
- Apply finalize/catalog cleanups to stored HQ text (backup `*.pre_b6b`).
- Re-OCR only if FAIL remains after cleanup — not as the default path.

## Policy
- FAIL (blocks apply): smash, placeholders, leftover height/place garble after cleanup
- WARN: class_header_gap / owner_tail_trunc / structure residuals (image recovery debt)
- `handled by` lines excluded from mangled_by / missing_owned_by

## Per volume

| Verdict | Cleaned | Fail | Warn | Catalog | File |
|---------|---------|------|------|---------|------|
| WARN | True | 0 | 34 | C1×25,C6×4,S4/O×3,O6×1,C6/O1×1 | `1998 Vol I, pt 1_ocr_hqmax.txt` |
| PASS | False | 0 | 0 | — | `1998 Vol I, pt 2_ocr_hqmax.txt` |
| WARN | True | 0 | 29 | C6×25,C1×3,O6×1 | `1998 Vol I, pt 3_ocr_hqmax.txt` |
| WARN | True | 0 | 35 | C1×25,S4/O×7,C6×3 | `1998 Vol II, pt 1_ocr_hqmax.txt` |
| WARN | True | 0 | 34 | C1×23,S4/O×5,O6×4,?/4th_then_6th_no_5×1,C6×1 | `1998 Vol II, pt 2_ocr_hqmax.txt` |
| WARN | True | 0 | 29 | C1×25,S4/O×2,C6×2 | `1998 Vol III, pt 1_ocr_hqmax.txt` |
| WARN | True | 0 | 30 | C1×25,S4/O×5 | `1998 Vol III, pt 2_ocr_hqmax.txt` |

## Sample residual hits (after cleanup)

### `1998 Vol I, pt 1_ocr_hqmax.txt` (WARN)
- `O6` / `owner_tail_trunc`: 12 1/2-15" Reserve: Wildgoose Trouble, owned by Tony & Kim
- `S4/O` / `missing_owned_by`: 2nd: Cody, Michele Southerland
- `S4/O` / `missing_owned_by`: 1st: Westmorland Best Bet Yet, Lisa Westmorland
- `S4/O` / `missing_owned_by`: 1st: Fair Oaks Texas, Anne de'Treville
- `C6/O1` / `bare_entries`: entries:
- `C6` / `orphan_entry_count`: 5
- `C6` / `orphan_entry_count`: 3
- `C6` / `orphan_entry_count`: 2
- `C1` / `class_header_gap`: 1st: His Audrey, owned by Chris & Chris Denning
- `C1` / `class_header_gap`: 1st: Blue Harbor Holly, owned by Doug Stephenson
- `C1` / `class_header_gap`: 1st: South Hunt Graessle, owned by Gail Blasingame
- `C1` / `class_header_gap`: 1st: Whirlwind Polo, owned by Terry Wellman

### `1998 Vol I, pt 3_ocr_hqmax.txt` (WARN)
- `O6` / `owner_tail_trunc`: 10-12 1/2" Champion: The Hollow Markham, owned by Bill & Kim
- `C6` / `orphan_entry_count`: 5
- `C6` / `orphan_entry_count`: 1
- `C6` / `orphan_entry_count`: 2
- `C6` / `orphan_entry_count`: 3
- `C6` / `orphan_entry_count`: 8
- `C6` / `orphan_entry_count`: 14
- `C6` / `orphan_entry_count`: 15
- `C6` / `orphan_entry_count`: 9
- `C6` / `orphan_entry_count`: 7
- `C6` / `orphan_entry_count`: 4
- `C1` / `class_header_gap`: 1st: Romney Victoria, owned by L.Godin/C.Elwood

### `1998 Vol II, pt 1_ocr_hqmax.txt` (WARN)
- `S4/O` / `missing_owned_by`: 2nd: Peck's Bad Boy JJ, ow
- `S4/O` / `missing_owned_by`: 6th: Indian River Spencer, Mike & Betty Bilinski
- `S4/O` / `missing_owned_by`: 1st: Camerton Hall Allure, Ann Coffin
- `S4/O` / `missing_owned_by`: 3rd: Farmliff Scooter, Cindy DeMeis
- `S4/O` / `missing_owned_by`: 1st: Pine Hill Chase, Alice Reynolds
- `S4/O` / `missing_owned_by`: Reserve: Farmstead Damage, D.Ellis/S.Ferber
- `S4/O` / `missing_owned_by`: 5th: Lost Creek Gabriel, Jennifer Frank
- `C6` / `orphan_entry_count`: 23
- `C6` / `orphan_entry_count`: 28
- `C6` / `orphan_entry_count`: 35
- `C1` / `class_header_gap`: 1st: Sunny Ridge Gypsy, owned by James Gupko
- `C1` / `class_header_gap`: 1st: Briarpatch Hasty, owned by Jack & Terri Batzer

### `1998 Vol II, pt 2_ocr_hqmax.txt` (WARN)
- `?` / `4th_then_6th_no_5`: 4th: Whispering Winds Sir Willie, owned by Ken & Mary Winfield
6th: Farmcliff Snowflake, owned by Genie Franklin AIL IZ 90 UT miiomm Ad bie: vrs IirmnlAarr
- `O6` / `owner_tail_trunc`: 10-12 1/2"" Champion: Northgate Scoundrel, owned by Doug & St
- `O6` / `owner_tail_trunc`: 10-12 5" Champion: Big Sky Annie, owned by Doug & Sue
- `O6` / `owner_tail_trunc`: Reserve: Farmcliff Kermit, owned by Bob Franklin Es 19D" Fl Py EL, JLT 1 Ee EE
- `O6` / `owner_tail_trunc`: v FOr TT == 3rd: Farmclifft Snowflake, owned by Genie Franklin Al "To ow bewe be Tom micivm mead Ie, TY, om OM mle mille RA: sien bn ro om
- `S4/O` / `missing_owned_by`: Champion: Windriver Teal, Bev Dalton
- `S4/O` / `missing_owned_by`: 2nd: Fox Run Jackie, Sustell th BIC yk Fiore ty Mary Web
- `S4/O` / `missing_owned_by`: 5th: Goulden Ridge Courtney, handler not provided
- `S4/O` / `missing_owned_by`: 1st: B.J. Duty, Ill
- `S4/O` / `missing_owned_by`: 4th: Rock Rest Sadie, Judi Buckowski
- `C6` / `orphan_entry_count`: 11
- `C1` / `class_header_gap`: 1st: Copper, owned by Ken & Mary Winfield

### `1998 Vol III, pt 1_ocr_hqmax.txt` (WARN)
- `S4/O` / `missing_owned_by`: 1st: Marvelous Myron, Megan Walker
- `S4/O` / `missing_owned_by`: 2nd: Wootinhille Destiny, Tammy Short
- `C6` / `orphan_entry_count`: 4
- `C6` / `orphan_entry_count`: 12
- `C1` / `class_header_gap`: 1st: Fox Run Rivet, owned by Gaye Redpath
- `C1` / `class_header_gap`: 1st: North Fork Maggie, owned by Karen & Alan Cooper
- `C1` / `class_header_gap`: 1st: Farmcliff Holland, owned by Doug & Sue Tack
- `C1` / `class_header_gap`: 1st: Big Sky Annie, owned by Doug & Sue Tack
- `C1` / `class_header_gap`: 1st: Farmcliff Duke, owned by J.Hughes/K.Hunter
- `C1` / `class_header_gap`: 1st: Deegan, owned by Doug & Sue Tack
- `C1` / `class_header_gap`: 1st: Lizzie, owned by Rick & Mary Thornton
- `C1` / `class_header_gap`: 1st: Monterey Jack, owned by Gene Harvey

### `1998 Vol III, pt 2_ocr_hqmax.txt` (WARN)
- `S4/O` / `missing_owned_by`: 1st: Pine Meadow Gromit, David & Kerstin Barrette
- `S4/O` / `missing_owned_by`: 3rd: Hart Farm Elijah Blu, Dan & Cindy McClary
- `S4/O` / `missing_owned_by`: 2nd: Bay & Bolt Brandy, Donnie & Rebecca Cox
- `S4/O` / `missing_owned_by`: 1st: Whirlwind Nike, Larry & Debbie Mezoe
- `S4/O` / `missing_owned_by`: 1st: T-Ville Tank, Jeannine Teasley
- `C1` / `class_header_gap`: 1st: North Hills Rush, owned by Charlie & Julie Kemp
- `C1` / `class_header_gap`: 1st: Fox Run Casey, owned by Kathy Potter
- `C1` / `class_header_gap`: 1st: Spunky, owned by Trudy Winslow
- `C1` / `class_header_gap`: 1st: Northwood Sailor, owned by Martha Milligan
- `C1` / `class_header_gap`: 1st: Baybriar Mr. Timex, owned by Sandy Brown
- `C1` / `class_header_gap`: 1st: Rusty, owned by Tom Arnold
- `C1` / `class_header_gap`: 1st: White Gate Dutch, owned by Lynn May Measles
