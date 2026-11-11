# B6b cleanup + ingest audit — 1998

Catalog: `_OCR_CLEANUP_CATALOG_HANDOFF.md`
Volumes: 7  cleaned=2  PASS=1  WARN=5  FAIL=1
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
| WARN | True | 0 | 7 | S4/O×5,C6×2 | `1998 Vol II, pt 2_ocr_hqmax.txt` |
| WARN | True | 0 | 3 | S4/O×2,C6×1 | `1998 Vol III, pt 1_ocr_hqmax.txt` |
| FAIL | False | 7 | 6 | S4/O×6,C1×6,O6×1 | `1998 Vol III, pt 2_ocr_hqmax.txt` |

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

### `1998 Vol II, pt 2_ocr_hqmax.txt` (WARN)
- `S4/O` / `missing_owned_by`: Champion: Windriver Teal, Bev Dalton
- `S4/O` / `missing_owned_by`: 2nd: Fox Run Jackie, Sustell th BIC yk Fiore ty Mary Web
- `S4/O` / `missing_owned_by`: 5th: Goulden Ridge Courtney, handler not provided
- `S4/O` / `missing_owned_by`: 1st: B.J. Duty, Ill
- `S4/O` / `missing_owned_by`: 4th: Rock Rest Sadie, Judi Buckowski
- `C6` / `orphan_entry_count`: 11
- `C6` / `orphan_entry_count`: 10

### `1998 Vol III, pt 1_ocr_hqmax.txt` (WARN)
- `S4/O` / `missing_owned_by`: 1st: Marvelous Myron, Megan Walker
- `S4/O` / `missing_owned_by`: 2nd: Wootinhille Destiny, Tammy Short
- `C6` / `orphan_entry_count`: 4

### `1998 Vol III, pt 2_ocr_hqmax.txt` (FAIL)
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
- `C1` / `class_header_gap`: 1st: Prestige Farms Oliver, owned by Jennifer Gilligan
- `C1` / `class_header_gap`: 1st: Fox Run Jackie Oh What A Terror, owned by C.Costa/K.Flora
