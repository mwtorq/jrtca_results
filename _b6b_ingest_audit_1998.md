# B6b cleanup + ingest audit — 1998

Catalog: `_OCR_CLEANUP_CATALOG_HANDOFF.md`
Volumes: 7  cleaned=6  PASS=2  WARN=0  FAIL=5
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
| FAIL | True | 7 | 0 | C7×5,C1/C6×1,C1×1 | `1998 Vol I, pt 1_ocr_hqmax.txt` |
| PASS | False | 0 | 0 | — | `1998 Vol I, pt 2_ocr_hqmax.txt` |
| PASS | True | 0 | 0 | — | `1998 Vol I, pt 3_ocr_hqmax.txt` |
| FAIL | True | 2 | 0 | C7×2 | `1998 Vol II, pt 1_ocr_hqmax.txt` |
| FAIL | True | 4 | 0 | C7×3,C1/C6×1 | `1998 Vol II, pt 2_ocr_hqmax.txt` |
| FAIL | True | 7 | 0 | C7×4,C1/C6×3 | `1998 Vol III, pt 1_ocr_hqmax.txt` |
| FAIL | True | 6 | 0 | C1/C6×3,C7×3 | `1998 Vol III, pt 2_ocr_hqmax.txt` |

## Sample residual hits (after cleanup)

### `1998 Vol I, pt 1_ocr_hqmax.txt` (FAIL)
- `C1/C6` / `incomplete_entries`: Dogs, 1 yr & older, over 12 1/2-15" Entries: 19 | places=0/6 | ADULT RACING CHAMPION & RESERVE
- `C1` / `midclass_page_dropout`: Bitch Pups, 9 up to 12 months, sm                Entries: 7 | after page got 4th expected 1 | 4th: Eox Run Adlih cwnadbhuDohiloadal
- `C7` / `best_reserve_missing_header`: Reserve: The Hollow Kite, owned by Bob & Nancy Lundmark
- `C7` / `best_reserve_missing_header`: 12 %.-15" Reserve:
- `C7` / `best_reserve_missing_header`: Reserve: Arrowhead Margarita, owned by Scott
- `C7` / `best_reserve_missing_header`: Reserve: Mike To Cory, owned by Rudy Mullis
- `C7` / `best_reserve_missing_header`: Reserve: Tortilla Flat Crunch, owned by Deborah Holly

### `1998 Vol II, pt 1_ocr_hqmax.txt` (FAIL)
- `C7` / `best_reserve_missing_header`: Reserve: Katie Clover, owned by Natalene Lamming
- `C7` / `best_reserve_missing_header`: Best: Token Jones, owned by Nancy Adamson

### `1998 Vol II, pt 2_ocr_hqmax.txt` (FAIL)
- `C1/C6` / `incomplete_entries`: Bitches, 1 yr & older, 10 up to 12 12" Entries: 15 | places=0/6 | 10-12 5" Champion: Lickity Split Sassy, owned by Bob Frankli
- `C7` / `best_reserve_missing_header`: Reserve: Jeffrey Finkernagel
- `C7` / `best_reserve_missing_header`: Reserve: Farmcliff Wendy, owned by Bob Franklin 1 4) amir MHA] ow wre. mr tt. CC dk: BE ole ml PN. rumea Baa
- `C7` / `best_reserve_missing_header`: Best: Northwood Simon, owned by Linda Cranford

### `1998 Vol III, pt 1_ocr_hqmax.txt` (FAIL)
- `C1/C6` / `incomplete_entries`: Veteran Entries: 7 | places=0/6 | Family Class                                              En
- `C1/C6` / `incomplete_entries`: YOUTH Agility                                             Entries: 4 | places=0/4 | CONFORMATION DIVISION
- `C1/C6` / `incomplete_entries`: Veteran Entries: 8 | places=0/6 | Family Class                                              En
- `C7` / `best_reserve_missing_header`: Reserve: Hedgerow Mustang Sally, owned by Rhonda Rebhorn
- `C7` / `best_reserve_missing_header`: Reserve: Rolling Rock Mia Diamond, owned by Carol Voyles
- `C7` / `best_reserve_missing_header`: Reserve: Rainland Rae, owned by Robert & Linda Fleck
- `C7` / `best_reserve_missing_header`: Reserve: Rainier Jasper, owned by Ann Heneghan

### `1998 Vol III, pt 2_ocr_hqmax.txt` (FAIL)
- `C1/C6` / `incomplete_entries`: ced, On Lead Entries: 5 | places=0/5 | s Agility, Off Lead, 10 up to 12 1" Entries: 5
- `C1/C6` / `incomplete_entries`: s Agility, Off Lead, 10 up to 12 1" Entries: 5 | places=0/5 | I Certificate, Off Lead, 10up to 12%." Entries: 1
- `C1/C6` / `incomplete_entries`: AALEADR ATIAM DIVICION                                                           | places=0/6 | Dog Pups, 4 up to 6 months, smooth             Entries: 2
- `C7` / `best_reserve_missing_header`: Reserve: White Zoo Gyp, owned by Roger & Tabitha Shury
- `C7` / `best_reserve_missing_header`: Best: Copper Horse Salty Dog, owned by David & Lisa McKinney
- `C7` / `best_reserve_missing_header`: Best: Fox Run Rigby, owned by Dub & Jan Dale
