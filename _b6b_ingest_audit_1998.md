# B6b cleanup + ingest audit — 1998

Catalog: `_OCR_CLEANUP_CATALOG_HANDOFF.md`
Volumes: 7  cleaned=0  PASS=1  WARN=0  FAIL=6
Year verdict: **FAIL**  SQL-apply unlock: NO

## Intent
- Apply finalize/catalog cleanups to stored HQ text (backup `*.pre_b6b`).
- Re-OCR only if FAIL remains after cleanup — not as the default path.

## Policy
- FAIL (blocks apply/unlock): smash, height/place garble, **O6 owner_tail_trunc**, **C1 class_header_gap**, placeholders
- Re-OCR queued when FAIL includes REOCR_CODES (O6/C1/smash/height) — do not invent surnames/titles
- `handled by` lines excluded from mangled_by / missing_owned_by

## Per volume

| Verdict | Cleaned | Fail | Warn | Catalog | File |
|---------|---------|------|------|---------|------|
| FAIL | False | 40 | 8 | C1×25,O6×15,C6×4,S4/O×3,C6/O1×1 | `1998 Vol I, pt 1_ocr_hqmax.txt` |
| PASS | False | 0 | 0 | — | `1998 Vol I, pt 2_ocr_hqmax.txt` |
| FAIL | False | 3 | 25 | C6×25,C1×3 | `1998 Vol I, pt 3_ocr_hqmax.txt` |
| FAIL | False | 33 | 10 | C1×25,O6×8,S4/O×7,C6×3 | `1998 Vol II, pt 1_ocr_hqmax.txt` |
| FAIL | False | 30 | 7 | C1×23,O6×7,S4/O×5,?/4th_then_6th_no_5×1,C6×1 | `1998 Vol II, pt 2_ocr_hqmax.txt` |
| FAIL | False | 33 | 4 | C1×25,O6×8,S4/O×2,C6×2 | `1998 Vol III, pt 1_ocr_hqmax.txt` |
| FAIL | False | 31 | 5 | C1×25,O6×6,S4/O×5 | `1998 Vol III, pt 2_ocr_hqmax.txt` |

## Sample residual hits (after cleanup)

### `1998 Vol I, pt 1_ocr_hqmax.txt` (FAIL)
- `O6` / `owner_tail_trunc`: 12 1/2-15" Champion: Arrowhead Micanopy, owned by Sc
- `O6` / `owner_tail_trunc`: 10-12 1/2" Reserve: Greenwood Lucy, owned by Bobby Joe Duty Ill
- `O6` / `owner_tail_trunc`: 6th: Double Duty Bernard, owned by Bobby Duty Ili
- `O6` / `owner_tail_trunc`: 1215" Champion: Arrowhead Margarita, owned by Scott & Kathy Net
- `O6` / `owner_tail_trunc`: 12 1/2-15" Champion: Arrowhead Margarita, owned by Scott & Kathy Net
- `O6` / `owner_tail_trunc`: 12 %:-15" Reserve: Arrowhead Margarita, owned by Scot
- `O6` / `owner_tail_trunc`: 1st: Wild Goose Black Toed Rosie, owned by Daniel & Alicia Mat
- `O6` / `owner_tail_trunc`: 1st: Jazzy Stuff, owned by Bobby Joe Duty Ill
- `O6` / `owner_tail_trunc`: 5th: Button Top Texy, owned by Andre & Laura Nel
- `O6` / `owner_tail_trunc`: 2nd: Button Top Pawsy, owned by Bobby Joe Duty Ili
- `O6` / `owner_tail_trunc`: 2nd: Wildgoose Nitro, owned by Bobby Joe Duty Iii
- `O6` / `owner_tail_trunc`: 3rd: Button Top Pawsy, owned by Bobby Joe Duty Ili

### `1998 Vol I, pt 3_ocr_hqmax.txt` (FAIL)
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
- `C1` / `class_header_gap`: 1st: BeSenisRamOL anhar, owned by B FrankliniC. Curtis

### `1998 Vol II, pt 1_ocr_hqmax.txt` (FAIL)
- `O6` / `owner_tail_trunc`: 12 5-15" Champion: Lost Acres Louise, owned by Lau
- `O6` / `owner_tail_trunc`: 3rd: Ravenswood Bella Donne, owned by Antonio & Barbara Sul
- `O6` / `owner_tail_trunc`: 10-12 1/2" Reserve: Westwood Jade, owned by Rick
- `O6` / `owner_tail_trunc`: 10-12 1/2" Champion: High & Low Goblin, owned by Mel
- `O6` / `owner_tail_trunc`: 12 1/2-15" Champion: Peck's Bad Boy JJ, owned by St
- `O6` / `owner_tail_trunc`: 5th: Long Hope Mickey, owned by Bob Franklin CTT EERE SE ES rr CEE LV ET TEE BET RI EEE MEY
- `O6` / `owner_tail_trunc`: 12 15" Champion: Terrier Turf Mayhem, owned by Kevin & Shannon Ost
- `O6` / `owner_tail_trunc`: 2nd: Montana Bunkhouse Tip McGee, owned by Beau & Kathleen Whi
- `S4/O` / `missing_owned_by`: 2nd: Peck's Bad Boy JJ, ow
- `S4/O` / `missing_owned_by`: 6th: Indian River Spencer, Mike & Betty Bilinski
- `S4/O` / `missing_owned_by`: 1st: Camerton Hall Allure, Ann Coffin
- `S4/O` / `missing_owned_by`: 3rd: Farmliff Scooter, Cindy DeMeis

### `1998 Vol II, pt 2_ocr_hqmax.txt` (FAIL)
- `?` / `4th_then_6th_no_5`: 4th: Whispering Winds Sir Willie, owned by Ken & Mary Winfield
6th: Farmcliff Snowflake, owned by Genie Franklin AIL IZ 90 UT miiomm Ad bie: vrs IirmnlAarr
- `O6` / `owner_tail_trunc`: 10-12 1/2"" Champion: Northgate Scoundrel, owned by Doug & St
- `O6` / `owner_tail_trunc`: 2nd: Sims Run Whitnie, owned by Ivy Hil
- `O6` / `owner_tail_trunc`: 5th: Long Hope Mickey, owned by Bob Franklin MAIL. BA clic muss ed Lis LEH DAs Aes
- `O6` / `owner_tail_trunc`: 12 1/2-15" Champion: Blue Barns Willie, owned by John Tri
- `O6` / `owner_tail_trunc`: Best: Conquest Keno, owned by Jan Beli
- `O6` / `owner_tail_trunc`: 3rd: Vistara Ransom, owned by Lyda
- `O6` / `owner_tail_trunc`: 5th: Willowbend Bradford, owned by Sue Any
- `S4/O` / `missing_owned_by`: Champion: Windriver Teal, Bev Dalton
- `S4/O` / `missing_owned_by`: 2nd: Fox Run Jackie, Sustell th BIC yk Fiore ty Mary Web
- `S4/O` / `missing_owned_by`: 5th: Goulden Ridge Courtney, handler not provided
- `S4/O` / `missing_owned_by`: 1st: B.J. Duty, Ill

### `1998 Vol III, pt 1_ocr_hqmax.txt` (FAIL)
- `O6` / `owner_tail_trunc`: 5th: Green Gate Tomba, owned by Joe & Priscilla Tes
- `O6` / `owner_tail_trunc`: 6th: Button Top Pawsy, owned by Bobby Joe Duty Ili
- `O6` / `owner_tail_trunc`: 5th: Greenwood Lucky, owned by Bobby Joe Duty Ili
- `O6` / `owner_tail_trunc`: 2nd: Greenwood Lucky, owned by Bobby Joe Duty Ill
- `O6` / `owner_tail_trunc`: 4th: Jazzy Stuff, owned by Bobby Joe Duty Ili
- `O6` / `owner_tail_trunc`: 2nd: Zachary, owned by Jim & Ann Van Noy
- `O6` / `owner_tail_trunc`: 5th: Quickdraw Remington, owned by Jennifer Orr
- `O6` / `owner_tail_trunc`: 1st: Quickdraw Remington, owned by Jennifer Orr
- `S4/O` / `missing_owned_by`: 1st: Marvelous Myron, Megan Walker
- `S4/O` / `missing_owned_by`: 2nd: Wootinhille Destiny, Tammy Short
- `C6` / `orphan_entry_count`: 4
- `C6` / `orphan_entry_count`: 12

### `1998 Vol III, pt 2_ocr_hqmax.txt` (FAIL)
- `O6` / `owner_tail_trunc`: Reserve: Northwood Freddie, owned by Kevin & Shannon Ost
- `O6` / `owner_tail_trunc`: 1st: Conquest Keno, owned by Jan Beli
- `O6` / `owner_tail_trunc`: Reserve: Fenton Scout's Honor, owned by David & Cathy Eic
- `O6` / `owner_tail_trunc`: 4th: Wild Goose Nitro, owned by Bobby Duty Ili
- `O6` / `owner_tail_trunc`: 4th: Flattridge Flexy, owned by Bobby Joe Duty III
- `O6` / `owner_tail_trunc`: 2nd: Wildgoose Nitro, owned by Bobby Joe Duty Ili
- `S4/O` / `missing_owned_by`: 1st: Pine Meadow Gromit, David & Kerstin Barrette
- `S4/O` / `missing_owned_by`: 3rd: Hart Farm Elijah Blu, Dan & Cindy McClary
- `S4/O` / `missing_owned_by`: 2nd: Bay & Bolt Brandy, Donnie & Rebecca Cox
- `S4/O` / `missing_owned_by`: 1st: Whirlwind Nike, Larry & Debbie Mezoe
- `S4/O` / `missing_owned_by`: 1st: T-Ville Tank, Jeannine Teasley
- `C1` / `class_header_gap`: 1st: North Hills Rush, owned by Charlie & Julie Kemp
