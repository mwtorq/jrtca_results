# B6b cleanup + ingest audit — 1999

Catalog: `_OCR_CLEANUP_CATALOG_HANDOFF.md`
Volumes: 6  cleaned=2  PASS=0  WARN=2  FAIL=4
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
| FAIL | False | 12 | 2 | C1×9,O6×3,S4/O×1,C6×1 | `1999 Vol I, pt 1_ocr_hqmax.txt` |
| FAIL | False | 11 | 3 | C1×7,O6×4,S4/O×2,?/4th_then_6th_no_5×1 | `1999 Vol I, pt 2_ocr_hqmax.txt` |
| WARN | False | 0 | 3 | S4/O×2,?/cutoff_racing×1 | `1999 Vol II, pt 1_ocr_hqmax.txt` |
| FAIL | False | 20 | 0 | C1×18,O6×2 | `1999 Vol II, pt 2_ocr_hqmax.txt` |
| WARN | True | 0 | 3 | S4/O×1,C6/O1×1,C6×1 | `1999 Vol III, pt 1_ocr_hqmax.txt` |
| FAIL | True | 16 | 9 | C1×14,S4/O×7,O6×2,C6/O1×1,C6×1 | `1999 Vol III, pt 2_ocr_hqmax.txt` |

## Sample residual hits (after cleanup)

### `1999 Vol I, pt 1_ocr_hqmax.txt` (FAIL)
- `O6` / `owner_tail_trunc`: 2nd: Sun Dance, owned by Roy & Sandra Deo
- `O6` / `owner_tail_trunc`: 2nd: BF. Wishbone, owned by David, Jean & Kelley Rei
- `O6` / `owner_tail_trunc`: 5th: ~ B.F. Wishbone, owned by B.F. David, Jean & Kelley Rei
- `S4/O` / `missing_owned_by`: 1st: Nirvana Farms Madison, Peggy Dominico
- `C6` / `orphan_entry_count`: 27
- `C1` / `class_header_gap`: 1st: Runamuk Gnat, owned by Harry & Mary Abbott
- `C1` / `class_header_gap`: 1st: Annie, owned by Lynn May Measles
- `C1` / `class_header_gap`: 1st: Rootie Tootie, owned by Lynn May Measles
- `C1` / `class_header_gap`: 1st: Scruffy, owned by Audie Sumner
- `C1` / `class_header_gap`: 1st: The Hollow Blaze, owned by C.Boesel/C.Cswerko
- `C1` / `class_header_gap`: 1st: Windermere Roper, owned by Mike Molloy
- `C1` / `class_header_gap`: 1st: Istt Half Track, owned by Mark & Janice Bjorkland

### `1999 Vol I, pt 2_ocr_hqmax.txt` (FAIL)
- `?` / `4th_then_6th_no_5`: 4th: Rat Race Keely, owned by Lloyd & Ann Wendland
6th: Lickity Split Fancy, owned by Allen & Denise Wessel
- `O6` / `owner_tail_trunc`: 1st: Paramount Ectasy, owned by Dennie Fee
- `O6` / `owner_tail_trunc`: Best: Paramount Ectasy, owned by Dennis Fee
- `O6` / `owner_tail_trunc`: Reserve: Paramount Ecstasy, owned by Dennie Fee
- `O6` / `owner_tail_trunc`: 1st: Sundance, owned by Roy & Sandy Deo
- `S4/O` / `missing_owned_by`: 6th: Daniel, last name not provided
- `S4/O` / `missing_owned_by`: 2nd: White Spirits Abbey Rose, Dan & Cindy McClary
- `C1` / `class_header_gap`: 1st: Orchard Hill Dabble, owned by Robby & Cheryl Robson
- `C1` / `class_header_gap`: 1st: Deep Run Derek, owned by John & Vicki Brown
- `C1` / `class_header_gap`: 1st: Oakfield Hoochie, owned by Didi Gough
- `C1` / `class_header_gap`: 1st: White Gate Dutch, owned by Lynn May Measles
- `C1` / `class_header_gap`: 1st: Rootie-Tootie, owned by Lynn May Measles

### `1999 Vol II, pt 1_ocr_hqmax.txt` (WARN)
- `?` / `cutoff_racing`: ACING DIVISION
- `S4/O` / `missing_owned_by`: 4th: Winslow Genevieve, Lisa Fitzgerald
- `S4/O` / `missing_owned_by`: 2nd: Disqualified, Exhibitor cross-entered in Open Division

### `1999 Vol II, pt 2_ocr_hqmax.txt` (FAIL)
- `O6` / `owner_tail_trunc`: 1st: Muscle Russell Comet, owned by Jack & Ma
- `O6` / `owner_tail_trunc`: 12-15" Reserve: Northwoods O'Tally Oak, owned by Gary
- `C1` / `class_header_gap`: 1st: Corn Row Tucker, owned by Mark Thompson
- `C1` / `class_header_gap`: 1st: Long Hope Mickey, owned by Bob Franklin
- `C1` / `class_header_gap`: 1st: Fox Run Dazl, owned by Stephanie Taylor
- `C1` / `class_header_gap`: 1st: Wyndcroft Tiller, owned by Margaret Coleburn
- `C1` / `class_header_gap`: 1st: istt Deegan, owned by Doug & Sue Tack
- `C1` / `class_header_gap`: 1st: Skytop Renegade, owned by Sue & Elizabeth Murphree
- `C1` / `class_header_gap`: 1st: Farmcliff Holly, owned by K. Hunter/J. Hughes
- `C1` / `class_header_gap`: 1st: Hercules, owned by Carol King
- `C1` / `class_header_gap`: 1st: Farmliff Holland, owned by Doug & Sue Tack
- `C1` / `class_header_gap`: 1st: Hart Farms Reba, owned by Robert Van der Heym

### `1999 Vol III, pt 1_ocr_hqmax.txt` (WARN)
- `S4/O` / `missing_owned_by`: 4th: Wishbone, own ed by Heather Reid
- `C6/O1` / `bare_entries`: Entries:
- `C6` / `orphan_entry_count`: 0

### `1999 Vol III, pt 2_ocr_hqmax.txt` (FAIL)
- `O6` / `owner_tail_trunc`: 2nd: Angel's Den Tucker, owned by Jayleen Car
- `O6` / `owner_tail_trunc`: 1st: Baun Acres Phantom Jack, owned by Adam
- `S4/O` / `missing_owned_by`: 3rd: Trevor, last name not provided
- `S4/O` / `missing_owned_by`: 1st: Kristen Mogrovejo, handling North Country Petey
- `S4/O` / `missing_owned_by`: 2nd: Jessica Morrison, handling Cody
- `S4/O` / `missing_owned_by`: 3rd: Felicia Franklin, handling Gadget
- `S4/O` / `missing_owned_by`: 1st: Katie Fitzgerald, handling Winslow Genevieve
- `S4/O` / `missing_owned_by`: 2nd: Rocky Cassone, handling Muscle Russell Comet
- `S4/O` / `missing_owned_by`: 3rd: Amanda Mogrovejo, handling North Country Petey
- `C6/O1` / `bare_entries`: Entries:
- `C6` / `orphan_entry_count`: 10
- `C1` / `class_header_gap`: 1st: Angus, owned by Demetrius & Jennifer Stasinos
