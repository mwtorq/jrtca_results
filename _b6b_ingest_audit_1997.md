# B6b cleanup + ingest audit — 1997

Catalog: `_OCR_CLEANUP_CATALOG_HANDOFF.md`
Volumes: 4  cleaned=1  PASS=0  WARN=4  FAIL=0
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
| WARN | True | 0 | 5 | C6×3,S4/O×2 | `1997 Vol I pt 1_ocr_hqmax.txt` |
| WARN | False | 0 | 2 | S4/O×2 | `1997 Vol I pt 2_ocr_hqmax.txt` |
| WARN | False | 0 | 13 | S4/O×7,C6×6 | `1997 Vol II pt 1_ocr_hqmax.txt` |
| WARN | False | 0 | 6 | S4/O×3,C6×3 | `1997 Vol II pt 2_ocr_hqmax.txt` |

## Sample residual hits (after cleanup)

### `1997 Vol I pt 1_ocr_hqmax.txt` (WARN)
- `S4/O` / `missing_owned_by`: 2nd: Kingmont Harlaquin, owr 3d by Lynda Banducci
- `S4/O` / `missing_owned_by`: 1st: Buster, ownedby Tim & Wendy Griffith
- `C6` / `orphan_entry_count`: 26
- `C6` / `orphan_entry_count`: 23
- `C6` / `orphan_entry_count`: 1

### `1997 Vol I pt 2_ocr_hqmax.txt` (WARN)
- `S4/O` / `missing_owned_by`: 1st: High Mountain Lucy, Karen Vernon
- `S4/O` / `missing_owned_by`: 2nd: , Courtney Bottington

### `1997 Vol II pt 1_ocr_hqmax.txt` (WARN)
- `S4/O` / `missing_owned_by`: 6th: Blue Barns Tracker, R. & D. Zampella
- `S4/O` / `missing_owned_by`: 4th: Timber DiAd~s heameomr, mctim mA Le. OL PY 1
- `S4/O` / `missing_owned_by`: 1st: Katlin Cortenbach, handling Little Orbit of Cortenbach
- `S4/O` / `missing_owned_by`: 3rd: Kari Carlsen, handling Westgate Ruffian
- `S4/O` / `missing_owned_by`: 1st: Ali Mae Hop, handling Hopdiggity Checkers
- `S4/O` / `missing_owned_by`: 2nd: Pat Martin, handling Bar-C Abilene Rose
- `S4/O` / `missing_owned_by`: 2nd: Matisse, Ruth Evans
- `C6` / `orphan_entry_count`: 8
- `C6` / `orphan_entry_count`: 31
- `C6` / `orphan_entry_count`: 16
- `C6` / `orphan_entry_count`: 17
- `C6` / `orphan_entry_count`: 5

### `1997 Vol II pt 2_ocr_hqmax.txt` (WARN)
- `S4/O` / `missing_owned_by`: Champion: Blue Jeans, Donna Pierce
- `S4/O` / `missing_owned_by`: 5th: Button Top Jim Winston, Joel Pritchet
- `S4/O` / `missing_owned_by`: 6th: Showbizz Fizz, al Darlene Irvine
- `C6` / `orphan_entry_count`: 03
- `C6` / `orphan_entry_count`: 10
- `C6` / `orphan_entry_count`: 12
