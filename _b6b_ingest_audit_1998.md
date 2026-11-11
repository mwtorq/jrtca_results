# B6b cleanup + ingest audit — 1998

Catalog: `_OCR_CLEANUP_CATALOG_HANDOFF.md`
Volumes: 7  cleaned=0  PASS=1  WARN=3  FAIL=3
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
| WARN | False | 0 | 9 | C6×5,S4/O×3,C6/O1×1 | `1998 Vol I, pt 1_ocr_hqmax.txt` |
| PASS | False | 0 | 0 | — | `1998 Vol I, pt 2_ocr_hqmax.txt` |
| WARN | False | 0 | 25 | C6×25 | `1998 Vol I, pt 3_ocr_hqmax.txt` |
| WARN | False | 0 | 10 | S4/O×7,C6×3 | `1998 Vol II, pt 1_ocr_hqmax.txt` |
| FAIL | False | 12 | 8 | C1×8,S4/O×5,O6×4,C6×2,?/4th_then_6th_no_5×1 | `1998 Vol II, pt 2_ocr_hqmax.txt` |
| FAIL | False | 10 | 3 | C1×7,O6×3,S4/O×2,C6×1 | `1998 Vol III, pt 1_ocr_hqmax.txt` |
| FAIL | False | 9 | 6 | S4/O×6,C1×6,O6×3 | `1998 Vol III, pt 2_ocr_hqmax.txt` |

## Sample residual hits (after cleanup)

### `1998 Vol I, pt 1_ocr_hqmax.txt` (WARN)
- `S4/O` / `missing_owned_by`: 2nd: Cody, Michele Southerland
- `S4/O` / `missing_owned_by`: 1st: Westmorland Best Bet Yet, Lisa Westmorland
- `S4/O` / `missing_owned_by`: 1st: Fair Oaks Texas, Anne de'Treville
- `C6/O1` / `bare_entries`: entries:
- `C6` / `orphan_entry_count`: 5
- `C6` / `orphan_entry_count`: 3
- `C6` / `orphan_entry_count`: 2
- `C6` / `orphan_entry_count`: 4

### `1998 Vol I, pt 3_ocr_hqmax.txt` (WARN)
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

### `1998 Vol II, pt 2_ocr_hqmax.txt` (FAIL)
- `?` / `4th_then_6th_no_5`: 4th: Whispering Winds Sir Willie, owned by Ken & Mary Winfield
6th: Farmcliff Snowflake, owned by Genie Franklin AIL IZ 90 UT miiomm Ad bie: vrs IirmnlAarr
- `O6` / `owner_tail_trunc`: 10-12 1/2"" Champion: Northgate Scoundrel, owned by Doug & St
- `O6` / `owner_tail_trunc`: Best: Conquest Keno, owned by Jan Beli
- `O6` / `owner_tail_trunc`: 3rd: Vistara Ransom, owned by Lyda
- `O6` / `owner_tail_trunc`: 5th: Willowbend Bradford, owned by Sue Any
- `S4/O` / `missing_owned_by`: Champion: Windriver Teal, Bev Dalton
- `S4/O` / `missing_owned_by`: 2nd: Fox Run Jackie, Sustell th BIC yk Fiore ty Mary Web
- `S4/O` / `missing_owned_by`: 5th: Goulden Ridge Courtney, handler not provided
- `S4/O` / `missing_owned_by`: 1st: B.J. Duty, Ill
- `S4/O` / `missing_owned_by`: 4th: Rock Rest Sadie, Judi Buckowski
- `C6` / `orphan_entry_count`: 11
- `C6` / `orphan_entry_count`: 10

### `1998 Vol III, pt 1_ocr_hqmax.txt` (FAIL)
- `O6` / `owner_tail_trunc`: 2nd: Zachary, owned by Jim & Ann Van Noy
- `O6` / `owner_tail_trunc`: 5th: Quickdraw Remington, owned by Jennifer Orr
- `O6` / `owner_tail_trunc`: 1st: Quickdraw Remington, owned by Jennifer Orr
- `S4/O` / `missing_owned_by`: 1st: Marvelous Myron, Megan Walker
- `S4/O` / `missing_owned_by`: 2nd: Wootinhille Destiny, Tammy Short
- `C6` / `orphan_entry_count`: 4
- `C1` / `class_header_gap`: 1st: Fox Run Rivet, owned by Gaye Redpath
- `C1` / `class_header_gap`: 1st: Farmcliff Holland, owned by Doug & Sue Tack
- `C1` / `class_header_gap`: 1st: Monterey Jack, owned by Gene Harvey
- `C1` / `class_header_gap`: 1st: Conquest Chaos, owned by Michelle Ward
- `C1` / `class_header_gap`: 1st: Kintail Bear, owned by Susan McRea
- `C1` / `class_header_gap`: 1st: Big Sky Annie, owned by Doug & Sue Tack

### `1998 Vol III, pt 2_ocr_hqmax.txt` (FAIL)
- `O6` / `owner_tail_trunc`: Reserve: Northwood Freddie, owned by Kevin & Shannon Ost
- `O6` / `owner_tail_trunc`: 1st: Conquest Keno, owned by Jan Beli
- `O6` / `owner_tail_trunc`: Reserve: Fenton Scout's Honor, owned by David & Cathy Eic
- `S4/O` / `missing_owned_by`: 1st: Pine Meadow Gromit, David & Kerstin Barrette
- `S4/O` / `missing_owned_by`: 3rd: Hart Farm Elijah Blu, Dan & Cindy McClary
- `S4/O` / `missing_owned_by`: 2nd: Bay & Bolt Brandy, Donnie & Rebecca Cox
- `S4/O` / `missing_owned_by`: 1st: Whirlwind Nike, Larry & Debbie Mezoe
- `S4/O` / `missing_owned_by`: 1st: T-Ville Tank, Jeannine Teasley
- `S4/O` / `missing_owned_by`: 3rd: Double Duty Troubles, Bobby & Margie Duty
- `C1` / `class_header_gap`: 1st: North Hills Rush, owned by Charlie & Julie Kemp
- `C1` / `class_header_gap`: 1st: Farmcliff Duke, owned by J.Hughes/K.Hunter
- `C1` / `class_header_gap`: 1st: Winston, owned by Tammy Short
