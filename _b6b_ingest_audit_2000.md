# B6b cleanup + ingest audit — 2000

Catalog: `_OCR_CLEANUP_CATALOG_HANDOFF.md`
Volumes: 5  cleaned=2  PASS=0  WARN=4  FAIL=1
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
| FAIL | True | 28 | 12 | C1×25,C6×7,S4/O×5,O6×3 | `2000 Vol I_ocr_hqmax.txt` |
| WARN | True | 0 | 27 | S4/O×22,S4×2,?/4th_then_2nd×2,?/4th_then_6th_no_5×1 | `2000 Vol II_ocr_hqmax.txt` |
| WARN | False | 0 | 11 | S4/O×7,C6×2,S4×1,?/4th_then_2nd×1 | `2000 vol 3 pt 1_ocr_hqmax.txt` |
| WARN | False | 0 | 15 | S4/O×8,C6×7 | `2000 Vol III pt 1_ocr_hqmax.txt` |
| WARN | False | 0 | 6 | S4/O×4,C6/O1×2 | `2000 Vol III pt 2_ocr_hqmax.txt` |

## Sample residual hits (after cleanup)

### `2000 Vol I_ocr_hqmax.txt` (FAIL)
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
- `C6` / `orphan_entry_count`: 3
- `C1` / `class_header_gap`: 1st: Marksworth Beau, owned by Catherine Tobias

### `2000 Vol II_ocr_hqmax.txt` (WARN)
- `S4` / `mangled_by`: 2nd: Gizmo, woend by John & Vicki Brown
- `?` / `4th_then_2nd`: 4th: Fox Run Skye, owned by Chris Levine
2nd: Kenswick Kayla, owned by Sandy McElearney
- `?` / `4th_then_6th_no_5`: 4th: Rustler's Emma Peel, owned by Tony & Lina Marchlinski
6th: Prestwick Hot Shot, owned by Cheryl Johnson
- `S4/O` / `missing_owned_by`: 2nd: Gizmo, woend by John & Vicki Brown
- `S4/O` / `missing_owned_by`: 3rd: ,....-Farmcliff:Kerry,owned. by:Suanne-Mitchell-Jackson"
- `S4/O` / `missing_owned_by`: 3rd: ="Farmcliff-Tea-Cup,owned. by. Richard Minutello
- `S4/O` / `missing_owned_by`: 3rd: Farmcliff-Tackle, owned. by. Megan. Johnson
- `S4/O` / `missing_owned_by`: Champion: Muscle Russell Comet, by M. Mogrovejo
- `S4/O` / `missing_owned_by`: Reserve: Farmcliff Hutch, owned. by D. & M. McMahon'
- `S4/O` / `missing_owned_by`: 2nd: Metro, owner unknown YOUTH DIVISION
- `S4/O` / `missing_owned_by`: 3rd: Fenton's Sweet Boy, owned:by Dick Fenton
- `S4/O` / `missing_owned_by`: 3rd: (Wendy Nyland, Owner)ei

### `2000 vol 3 pt 1_ocr_hqmax.txt` (WARN)
- `S4` / `mangled_by`: 2nd: North Country Petey, woend by Mary Lou Mogrovejo
- `?` / `4th_then_2nd`: 4th: dth: Briarpatch Winnie, owned by Sharon Kress
2nd: North Country Pringle, owned by Kathy Larson
- `S4/O` / `missing_owned_by`: 4th: Fidget, owner unknown
- `S4/O` / `missing_owned_by`: 4th: Harley, owner unknown
- `S4/O` / `missing_owned_by`: 2nd: Noaz Jacks Gimme, owned y Susi Laswell
- `S4/O` / `missing_owned_by`: 3rd: Peanut, owner unknown
- `S4/O` / `missing_owned_by`: 4th: Big Hickory Captain Jack, owne dby Mary Campbell
- `S4/O` / `missing_owned_by`: 3rd: Cosmo, owner not known
- `S4/O` / `missing_owned_by`: 2nd: North Country Petey, woend by Mary Lou Mogrovejo
- `C6` / `orphan_entry_count`: 39
- `C6` / `orphan_entry_count`: 10

### `2000 Vol III pt 1_ocr_hqmax.txt` (WARN)
- `S4/O` / `missing_owned_by`: 4th: Big Hickory Captain Jack, owne dby Mary Campbell
- `S4/O` / `missing_owned_by`: 3rd: Cosmo, owner not known
- `S4/O` / `missing_owned_by`: 4th: Fidget, owner unknown
- `S4/O` / `missing_owned_by`: 4th: Harley, owner unknown
- `S4/O` / `missing_owned_by`: 2nd: Noaz Jacks Gimme, owned y Susi Laswell
- `S4/O` / `missing_owned_by`: 3rd: Peanut, owner unknown
- `C6` / `orphan_entry_count`: 10
- `C6` / `orphan_entry_count`: 13
- `C6` / `orphan_entry_count`: 22
- `C6` / `orphan_entry_count`: 33

### `2000 Vol III pt 2_ocr_hqmax.txt` (WARN)
- `S4/O` / `missing_owned_by`: 3rd: Tracker, Lisanne & Michael Gray
- `S4/O` / `missing_owned_by`: 1st: Timely, Theresa Kothstein
- `S4/O` / `missing_owned_by`: 6th: Duster, owner unknown
- `S4/O` / `missing_owned_by`: 3rd: John Parmenter, Ill
- `C6/O1` / `bare_entries`: Entries:
