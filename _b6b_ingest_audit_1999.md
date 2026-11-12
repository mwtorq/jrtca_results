# B6b cleanup + ingest audit — 1999

Catalog: `_OCR_CLEANUP_CATALOG_HANDOFF.md`
Volumes: 6  cleaned=2  PASS=1  WARN=5  FAIL=0
Year verdict: **WARN**  SQL-apply unlock: YES

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
| WARN | False | 0 | 2 | S4/O×1,C6×1 | `1999 Vol I, pt 1_ocr_hqmax.txt` |
| WARN | True | 0 | 3 | S4/O×2,C6×1 | `1999 Vol I, pt 2_ocr_hqmax.txt` |
| WARN | False | 0 | 3 | S4/O×2,?/cutoff_racing×1 | `1999 Vol II, pt 1_ocr_hqmax.txt` |
| PASS | False | 0 | 0 | — | `1999 Vol II, pt 2_ocr_hqmax.txt` |
| WARN | False | 0 | 3 | S4/O×1,C6/O1×1,C6×1 | `1999 Vol III, pt 1_ocr_hqmax.txt` |
| WARN | True | 0 | 12 | S4/O×7,?/4th_then_6th_no_5×3,C6×2 | `1999 Vol III, pt 2_ocr_hqmax.txt` |

## Sample residual hits (after cleanup)

### `1999 Vol I, pt 1_ocr_hqmax.txt` (WARN)
- `S4/O` / `missing_owned_by`: 1st: Nirvana Farms Madison, Peggy Dominico
- `C6` / `orphan_entry_count`: 27

### `1999 Vol I, pt 2_ocr_hqmax.txt` (WARN)
- `S4/O` / `missing_owned_by`: 6th: Daniel, last name not provided
- `S4/O` / `missing_owned_by`: 2nd: White Spirits Abbey Rose, Dan & Cindy McClary
- `C6` / `orphan_entry_count`: 3

### `1999 Vol II, pt 1_ocr_hqmax.txt` (WARN)
- `?` / `cutoff_racing`: ACING DIVISION
- `S4/O` / `missing_owned_by`: 4th: Winslow Genevieve, Lisa Fitzgerald
- `S4/O` / `missing_owned_by`: 2nd: Disqualified, Exhibitor cross-entered in Open Division

### `1999 Vol III, pt 1_ocr_hqmax.txt` (WARN)
- `S4/O` / `missing_owned_by`: 4th: Wishbone, own ed by Heather Reid
- `C6/O1` / `bare_entries`: Entries:
- `C6` / `orphan_entry_count`: 0

### `1999 Vol III, pt 2_ocr_hqmax.txt` (WARN)
- `?` / `4th_then_6th_no_5`: 4th: Wild Goose Maryland, owned by Darlene McCutcheon
6th: Stone River Frenzy, owned by Carrie LaCombe
- `?` / `4th_then_6th_no_5`: 4th: Munchie, owned by Barry & Lisa Bigaouette
6th: Terrier-ific Blue Jeans, owned by Donna Pierce
- `?` / `4th_then_6th_no_5`: 4th: Farmstead Holly, handled by Jeffrey Finkernagel
6th: Lona Hope Minnie, owned by Nellie Niewola
- `S4/O` / `missing_owned_by`: 3rd: Trevor, last name not provided
- `S4/O` / `missing_owned_by`: 1st: Kristen Mogrovejo, handling North Country Petey
- `S4/O` / `missing_owned_by`: 2nd: Jessica Morrison, handling Cody
- `S4/O` / `missing_owned_by`: 3rd: Felicia Franklin, handling Gadget
- `S4/O` / `missing_owned_by`: 1st: Katie Fitzgerald, handling Winslow Genevieve
- `S4/O` / `missing_owned_by`: 2nd: Rocky Cassone, handling Muscle Russell Comet
- `S4/O` / `missing_owned_by`: 3rd: Amanda Mogrovejo, handling North Country Petey
- `C6` / `orphan_entry_count`: 10
- `C6` / `orphan_entry_count`: 7
