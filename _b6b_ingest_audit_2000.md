# B6b cleanup + ingest audit — 2000

Catalog: `_OCR_CLEANUP_CATALOG_HANDOFF.md`
Volumes: 5  cleaned=0  PASS=0  WARN=0  FAIL=5
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
| FAIL | False | 39 | 15 | C1×25,O6×14,C6×7,S4/O×6,?/4th_then_6th_no_5×2 | `2000 Vol I_ocr_hqmax.txt` |
| FAIL | False | 31 | 26 | C1×25,S4/O×19,O6×6,C6/O1×3,S4×2,?/4th_then_6th_no_5×1,C6×1 | `2000 Vol II_ocr_hqmax.txt` |
| FAIL | False | 29 | 13 | C1×25,S4/O×10,O6×4,C6×2,S4×1 | `2000 vol 3 pt 1_ocr_hqmax.txt` |
| FAIL | False | 43 | 19 | C1×25,O6×18,S4/O×10,C6×7,?/4th_then_6th_no_5×2 | `2000 Vol III pt 1_ocr_hqmax.txt` |
| FAIL | False | 38 | 11 | C1×25,O6×13,S4/O×7,C6/O1×2,S4×1,?/4th_then_6th_no_5×1 | `2000 Vol III pt 2_ocr_hqmax.txt` |

## Sample residual hits (after cleanup)

### `2000 Vol I_ocr_hqmax.txt` (FAIL)
- `?` / `4th_then_6th_no_5`: 4th: Indian River Dr. Spencer Kovak, owned by Ernest Bilinski
6th: R.A. Sundance Kid, owned by Ernest Bilinski
- `O6` / `owner_tail_trunc`: 3rd: Button Top Texy, owned by Andre & Laura Nel
- `O6` / `owner_tail_trunc`: Champion: Arrowhead Norma Jean, owned by Scott & Kathy Net
- `O6` / `owner_tail_trunc`: 2nd: Jumping Koxa Roo, owned by Steve & Betty Roo
- `O6` / `owner_tail_trunc`: 4th: Calico Wrecks, owned by Char
- `O6` / `owner_tail_trunc`: 1st: R.A. Cyclone Sally, owned by Samuel & i
- `O6` / `owner_tail_trunc`: 121-15" Champion: R.A. Rowdy, owned by Mike & L
- `O6` / `owner_tail_trunc`: 6th: 12Y5-15" Champion: Indian River Dr. Spencer Kovak, owned by S
- `O6` / `owner_tail_trunc`: 4th: Redgie, owned by Mark Hit
- `O6` / `owner_tail_trunc`: 3rd: Jrd: Wild West Lucid, owned by Tiffany Van Tuy
- `O6` / `owner_tail_trunc`: 3rd: Wild West Lucid, owned by Tiffany Van Tuy
- `S4/O` / `missing_owned_by`: 6th: Pandemonium, Dana and Laura Mitchell

### `2000 Vol II_ocr_hqmax.txt` (FAIL)
- `S4` / `mangled_by`: 2nd: Gizmo, woend by John & Vicki Brown
- `?` / `4th_then_6th_no_5`: 4th: Donovan, owned by Jon & Elizabeth Sterling
6th: Farmcliff Liz, owned by Bob & Genie Franklin
- `O6` / `owner_tail_trunc`: 6th: Sass N' Dash Mickey, owned by Mary Webb N'
- `O6` / `owner_tail_trunc`: 1st: Northgate Chester, owned by Susan Gil
- `O6` / `owner_tail_trunc`: Zlid, Iditiiolitcadu Dvild, Uvwlitu Jy !Hiol ia val NU 3rd: Farmcliff Tea Cup, owned by Richard Minutello 4th. Rolla nwnoart hy Tara Foy
- `S4/O` / `missing_owned_by`: 2nd: Gizmo, woend by John & Vicki Brown
- `S4/O` / `missing_owned_by`: 1st: Jess DiBernardoouth Handling Agility, On Lead                          Entries: 3
- `S4/O` / `missing_owned_by`: 1st: Jeffrey Finkernagelouth Handling Agility, Off Lead                           Entries: 2
- `S4/O` / `missing_owned_by`: 2nd: Metro, owner unknown
- `S4/O` / `missing_owned_by`: 1st: Jeffrey Finkernagelouth Handling Agility, On Lead                         Entries: 4
- `S4/O` / `missing_owned_by`: 3rd: (Wendy Nyland, Owner)
- `S4/O` / `missing_owned_by`: 3rd: Sarah Cranorth: TarynLacyouth Handling Agility, On Lead                        Entries: 5

### `2000 vol 3 pt 1_ocr_hqmax.txt` (FAIL)
- `S4` / `mangled_by`: 2nd: North Country Petey, woend by Mary Lou Mogrovejo
- `O6` / `owner_tail_trunc`: 5th: Rimshot, owned by Christopher & Pamela Lum
- `O6` / `owner_tail_trunc`: 3rd: Wild Goose Jabelle, owned by Julie Dut
- `O6` / `owner_tail_trunc`: 2nd: Oakwood Marian, owned by Jim & Sally Sau
- `O6` / `owner_tail_trunc`: 6th: Long Hope Bambi, owned by Luting Pan
- `S4/O` / `missing_owned_by`: 4th: Fidget, owner unknown
- `S4/O` / `missing_owned_by`: 4th: Harley, owner unknown
- `S4/O` / `missing_owned_by`: 2nd: Noaz Jacks Gimme, owned y Susi Laswell
- `S4/O` / `missing_owned_by`: 3rd: Peanut, owner unknown
- `S4/O` / `missing_owned_by`: 3rd: Jennifer Phillipsth: Anne Dalmadgeth: Nichole Santosouth Handling Agility, On Lead                        Entries: 7
- `S4/O` / `missing_owned_by`: 4th: Big Hickory Captain Jack, owne dby Mary Campbell
- `S4/O` / `missing_owned_by`: 3rd: Cosmo, owner not known

### `2000 Vol III pt 1_ocr_hqmax.txt` (FAIL)
- `?` / `4th_then_6th_no_5`: 4th: George Jones, owned by Rebecca & Richard Paff
6th: Indian River Dr. Spencer Kovak, owned by M. & B. Bilinski
- `O6` / `owner_tail_trunc`: 1st: Shelmar White Stetson, owned by Jeana & Read Veaz
- `O6` / `owner_tail_trunc`: 1st: Underground Frenzy, owned by Kevin & Shannon Osb
- `O6` / `owner_tail_trunc`: 3rd: Shelmar White Diamond, owned by Jean & Reed Vea
- `O6` / `owner_tail_trunc`: 2nd: Muscle Russell Phantom, owned by Jim & Mandy Roi
- `O6` / `owner_tail_trunc`: 4th: Brandywine Gale, owned by Jim Sau
- `O6` / `owner_tail_trunc`: 6th: Long Hope Bambi, owned by Luting Pan
- `O6` / `owner_tail_trunc`: 5th: Rimshot, owned by Christopher & Pamela Lum
- `O6` / `owner_tail_trunc`: 3rd: Wild Goose Jabelle, owned by Julie Dut
- `O6` / `owner_tail_trunc`: 2nd: Oakwood Marian, owned by Jim & Sally Sau
- `O6` / `owner_tail_trunc`: 2nd: Falling Branch Checkers, owned by L
- `O6` / `owner_tail_trunc`: 3rd: Heaven Hill Nordik Wolf, owned by P

### `2000 Vol III pt 2_ocr_hqmax.txt` (FAIL)
- `S4` / `mangled_by`: 2nd: North Country Petey, woend by Mary Lou Mogrovejo
- `?` / `4th_then_6th_no_5`: 4th: Farmcliff Tea Cup, owned by Richard Minutello
6th: Schooner, owned by Sue Mishaw
- `O6` / `owner_tail_trunc`: Best: Avalon Savannah, owned by Charlie & Suzanne Bau
- `O6` / `owner_tail_trunc`: 1st: Northgate Chester, owned by Susan Gil
- `O6` / `owner_tail_trunc`: 2nd: Jazzy Stuf, owned by BJ Duty Ill
- `O6` / `owner_tail_trunc`: 1st: Jazzy Stuf, owned by BJ Duty Ill
- `O6` / `owner_tail_trunc`: 6th: Greenwood Smoots, owned by BJ Duty Ill
- `O6` / `owner_tail_trunc`: 6th: Gunsmoke Rubie, owned by BJ Duty Ill
- `O6` / `owner_tail_trunc`: 6th: Windswept Acres, owned by Johnny Brent Hopkins/Gary Wer
- `O6` / `owner_tail_trunc`: 1st: Wild Goose Deuce Coupe, owned by Mark Hit
- `O6` / `owner_tail_trunc`: 3rd: Hopdiggity Victor, owned by Liz Valles/Ali Hop
- `O6` / `owner_tail_trunc`: 1st: Hopdiggity Victor, owned by Liz Valles/Ali Hop
