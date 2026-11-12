# B6b cleanup + ingest audit — 2000

Catalog: `_OCR_CLEANUP_CATALOG_HANDOFF.md`
Volumes: 5  cleaned=5  PASS=0  WARN=0  FAIL=5
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
| FAIL | True | 32 | 12 | C1×25,O6×7,C6×7,S4/O×5 | `2000 Vol I_ocr_hqmax.txt` |
| FAIL | True | 25 | 16 | C1×25,S4/O×10,C6/O1×3,S4×2,C6×1 | `2000 Vol II_ocr_hqmax.txt` |
| FAIL | True | 27 | 11 | C1×25,S4/O×7,O6×2,C6×2,S4×1,?/4th_then_2nd×1 | `2000 vol 3 pt 1_ocr_hqmax.txt` |
| FAIL | True | 36 | 15 | C1×25,O6×11,S4/O×8,C6×7 | `2000 Vol III pt 1_ocr_hqmax.txt` |
| FAIL | True | 27 | 8 | C1×25,S4/O×5,O6×2,C6/O1×2,S4×1 | `2000 Vol III pt 2_ocr_hqmax.txt` |

## Sample residual hits (after cleanup)

### `2000 Vol I_ocr_hqmax.txt` (FAIL)
- `O6` / `owner_tail_trunc`: 3rd: Button Top Texy, owned by Andre & Laura Nel
- `O6` / `owner_tail_trunc`: Champion: Arrowhead Norma Jean, owned by Scott & Kathy Net
- `O6` / `owner_tail_trunc`: 2nd: Jumping Koxa Roo, owned by Steve & Betty Roo
- `O6` / `owner_tail_trunc`: 1st: R.A. Cyclone Sally, owned by Samuel & i
- `S4/O` / `missing_owned_by`: 6th: Pandemonium, Dana and Laura Mitchell
- `S4/O` / `missing_owned_by`: 2nd: Tortilla Flat Moka Smudj, Patty Freimark
- `S4/O` / `missing_owned_by`: 1st: Raindance Apache, owned b Pam Shepherd
- `S4/O` / `missing_owned_by`: 4th: Pterodactyl Pandora, Dawn Kleninger
- `S4/O` / `missing_owned_by`: 3rd: Lost Creek Lexington, owner unknown
- `C6` / `orphan_entry_count`: 10
- `C6` / `orphan_entry_count`: 2
- `C6` / `orphan_entry_count`: 16

### `2000 Vol II_ocr_hqmax.txt` (FAIL)
- `S4` / `mangled_by`: 2nd: Gizmo, woend by John & Vicki Brown
- `S4/O` / `missing_owned_by`: 2nd: Gizmo, woend by John & Vicki Brown
- `S4/O` / `missing_owned_by`: 2nd: Metro, owner unknown
- `S4/O` / `missing_owned_by`: 3rd: (Wendy Nyland, Owner)
- `S4/O` / `missing_owned_by`: 4th: FFT LE FR Ur ar a ee rr ma Sol, Ly
- `S4/O` / `missing_owned_by`: 4th: LIME £aen Ray Vee, OWNea oy vapnne vuvall
- `S4/O` / `missing_owned_by`: 6th: Clementine, owner not known
- `S4/O` / `missing_owned_by`: 3rd: Hazzaro, owner not known
- `S4/O` / `missing_owned_by`: 5th: Taz, ownedbyT. J. Lavery
- `C6/O1` / `bare_entries`: Entries:
- `C6` / `orphan_entry_count`: 1
- `C1` / `class_header_gap`: 1st: Pheasant Hills Tracker, owned by Wendy Knake

### `2000 vol 3 pt 1_ocr_hqmax.txt` (FAIL)
- `S4` / `mangled_by`: 2nd: North Country Petey, woend by Mary Lou Mogrovejo
- `?` / `4th_then_2nd`: 4th: dth: Briarpatch Winnie, owned by Sharon Kress
2nd: North Country Pringle, owned by Kathy Larson
- `O6` / `owner_tail_trunc`: 5th: Rimshot, owned by Christopher & Pamela Lum
- `O6` / `owner_tail_trunc`: 6th: Long Hope Bambi, owned by Luting Pan
- `S4/O` / `missing_owned_by`: 4th: Fidget, owner unknown
- `S4/O` / `missing_owned_by`: 4th: Harley, owner unknown
- `S4/O` / `missing_owned_by`: 2nd: Noaz Jacks Gimme, owned y Susi Laswell
- `S4/O` / `missing_owned_by`: 3rd: Peanut, owner unknown
- `S4/O` / `missing_owned_by`: 4th: Big Hickory Captain Jack, owne dby Mary Campbell
- `S4/O` / `missing_owned_by`: 3rd: Cosmo, owner not known
- `S4/O` / `missing_owned_by`: 2nd: North Country Petey, woend by Mary Lou Mogrovejo
- `C6` / `orphan_entry_count`: 39

### `2000 Vol III pt 1_ocr_hqmax.txt` (FAIL)
- `O6` / `owner_tail_trunc`: 1st: Shelmar White Stetson, owned by Jeana & Read Veaz
- `O6` / `owner_tail_trunc`: 3rd: Shelmar White Diamond, owned by Jean & Reed Vea
- `O6` / `owner_tail_trunc`: 2nd: Muscle Russell Phantom, owned by Jim & Mandy Roi
- `O6` / `owner_tail_trunc`: 6th: Long Hope Bambi, owned by Luting Pan
- `O6` / `owner_tail_trunc`: 5th: Rimshot, owned by Christopher & Pamela Lum
- `O6` / `owner_tail_trunc`: 3rd: Heaven Hill Nordik Wolf, owned by P
- `O6` / `owner_tail_trunc`: 1st: Richochet Lucky Strike, owned by Hir
- `S4/O` / `missing_owned_by`: 4th: Big Hickory Captain Jack, owne dby Mary Campbell
- `S4/O` / `missing_owned_by`: 3rd: Cosmo, owner not known
- `S4/O` / `missing_owned_by`: 4th: Fidget, owner unknown
- `S4/O` / `missing_owned_by`: 4th: Harley, owner unknown
- `S4/O` / `missing_owned_by`: 2nd: Noaz Jacks Gimme, owned y Susi Laswell

### `2000 Vol III pt 2_ocr_hqmax.txt` (FAIL)
- `S4` / `mangled_by`: 2nd: North Country Petey, woend by Mary Lou Mogrovejo
- `O6` / `owner_tail_trunc`: 1st: Hopdiggity Rose, owned by Liz Valles/Ali Hop
- `O6` / `owner_tail_trunc`: 5th: Ruff 'N Tumble Sunny, owned by Linda Hoy
- `S4/O` / `missing_owned_by`: 2nd: North Country Petey, woend by Mary Lou Mogrovejo
- `S4/O` / `missing_owned_by`: 3rd: Tracker, Lisanne & Michael Gray
- `S4/O` / `missing_owned_by`: 1st: Timely, Theresa Kothstein
- `S4/O` / `missing_owned_by`: 6th: Duster, owner unknown
- `S4/O` / `missing_owned_by`: 3rd: John Parmenter, Ill
- `C6/O1` / `bare_entries`: Entries:
- `C1` / `class_header_gap`: 1st: Mustang, owned by Jill Goodman
- `C1` / `class_header_gap`: 1st: Buddy, owned by Lauren Petrakis
- `C1` / `class_header_gap`: 1st: Old Glory Dylan, owned by Sandy Brown
