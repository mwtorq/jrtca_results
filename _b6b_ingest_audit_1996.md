# B6b cleanup + ingest audit — 1996

Catalog: `_OCR_CLEANUP_CATALOG_HANDOFF.md`
Volumes: 30  cleaned=0  PASS=17  WARN=0  FAIL=13
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
| FAIL | False | 1 | 0 | O6×1 | `1996 Vol 1 pg 111-160 back reversed_ocr_hqmax.txt` |
| FAIL | False | 2 | 0 | O6×1,C1×1 | `1996 Vol 1 pg 111-160 back_ocr_hqmax.txt` |
| PASS | False | 0 | 0 | — | `1996 Vol 1 pg 111-160 front_ocr_hqmax.txt` |
| PASS | False | 0 | 0 | — | `1996 Vol 1 pg 161-178 back reversed_ocr_hqmax.txt` |
| PASS | False | 0 | 0 | — | `1996 Vol 1 pg 161-178 back_ocr_hqmax.txt` |
| PASS | False | 0 | 0 | — | `1996 Vol 1 pg 161-178 front_ocr_hqmax.txt` |
| PASS | False | 0 | 0 | — | `1996 Vol 1 pg 21-60 back reversed_ocr_hqmax.txt` |
| PASS | False | 0 | 0 | — | `1996 Vol 1 pg 21-60 back_ocr_hqmax.txt` |
| FAIL | False | 2 | 0 | O6×1,C1×1 | `1996 Vol 1 pg 21-60 front_ocr_hqmax.txt` |
| FAIL | False | 1 | 0 | C1×1 | `1996 Vol 1 pg 61-110 back reversed_ocr_hqmax.txt` |
| FAIL | False | 1 | 0 | C1×1 | `1996 Vol 1 pg 61-110 back_ocr_hqmax.txt` |
| FAIL | False | 1 | 0 | O6×1 | `1996 Vol 1 pg 61-110 front_ocr_hqmax.txt` |
| PASS | False | 0 | 0 | — | `1996 Vol II pg 163-220 back reversed_ocr_hqmax.txt` |
| FAIL | False | 2 | 0 | O6×1,S1-S3×1 | `1996 Vol II pg 163-220 back_ocr_hqmax.txt` |
| FAIL | False | 1 | 0 | O6×1 | `1996 Vol II pg 163-220 front_ocr_hqmax.txt` |
| PASS | False | 0 | 0 | — | `1996 Vol II pg 23-92 back reversed_ocr_hqmax.txt` |
| PASS | False | 0 | 0 | — | `1996 Vol II pg 23-92 back_ocr_hqmax.txt` |
| PASS | False | 0 | 0 | — | `1996 Vol II pg 23-92 front (missing 1 pgs)_ocr_hqmax.txt` |
| PASS | False | 0 | 0 | — | `1996 Vol II pg 23-92 front (missing 2 pgs)_ocr_hqmax.txt` |
| FAIL | False | 2 | 0 | O6×2 | `1996 Vol II pg 23-92 front_ocr_hqmax.txt` |
| FAIL | False | 2 | 0 | O6×2 | `1996 Vol II pg 93-162 back reversed_ocr_hqmax.txt` |
| FAIL | False | 1 | 0 | O6×1 | `1996 Vol II pg 93-162 back_ocr_hqmax.txt` |
| FAIL | False | 2 | 0 | O6×2 | `1996 Vol II pg 93-162 front_ocr_hqmax.txt` |
| FAIL | False | 1 | 0 | C1×1 | `Document_2026-11-04_144208_ocr_hqmax.txt` |
| PASS | False | 0 | 0 | — | `Document_2026-11-04_144530_ocr_hqmax.txt` |
| PASS | False | 0 | 0 | — | `Document_2026-11-04_145355_ocr_hqmax.txt` |
| PASS | False | 0 | 0 | — | `Document_2026-11-04_145925_ocr_hqmax.txt` |
| PASS | False | 0 | 0 | — | `Document_2026-11-04_151058_ocr_hqmax.txt` |
| PASS | False | 0 | 0 | — | `Document_2026-11-04_152834_ocr_hqmax.txt` |
| PASS | False | 0 | 0 | — | `Document_2026-11-04_153208_ocr_hqmax.txt` |

## Sample residual hits (after cleanup)

### `1996 Vol 1 pg 111-160 back reversed_ocr_hqmax.txt` (FAIL)
- `O6` / `owner_tail_trunc`: 10-12 1/2" Champion: Camerton Hall BeBop, owned by ow

### `1996 Vol 1 pg 111-160 back_ocr_hqmax.txt` (FAIL)
- `O6` / `owner_tail_trunc`: 10-12 1/2" Reserv: Fox Valley Dylan of Chucks Run, owned by ow
- `C1` / `class_header_gap`: 5th: The Bowery Mst, owned by Teresa Wellman

### `1996 Vol 1 pg 21-60 front_ocr_hqmax.txt` (FAIL)
- `O6` / `owner_tail_trunc`: Best: Foxfield Sprig, owned by ow
- `C1` / `class_header_gap`: 4th: Hart Farm Hammer, owned by Cheryl Hart

### `1996 Vol 1 pg 61-110 back reversed_ocr_hqmax.txt` (FAIL)
- `C1` / `class_header_gap`: 4th: Badakhashan Celestial Haley, owned by Fay Craft

### `1996 Vol 1 pg 61-110 back_ocr_hqmax.txt` (FAIL)
- `C1` / `class_header_gap`: 6th: Hitts Badger, owned by Mark Hitt

### `1996 Vol 1 pg 61-110 front_ocr_hqmax.txt` (FAIL)
- `O6` / `owner_tail_trunc`: 10-12 1/2" Champion: RA Piker, owned by ow

### `1996 Vol II pg 163-220 back_ocr_hqmax.txt` (FAIL)
- `O6` / `owner_tail_trunc`: 12 1/2-15" Chanpion: Single Track Hunter, owned by ow
- `S1-S3` / `two_column_smash`: RACING DIViSIOl

### `1996 Vol II pg 163-220 front_ocr_hqmax.txt` (FAIL)
- `O6` / `owner_tail_trunc`: Over 12 1/2" Reserve: Merlin of Lost Creek, owned by ow

### `1996 Vol II pg 23-92 front_ocr_hqmax.txt` (FAIL)
- `O6` / `owner_tail_trunc`: 10-12 1/2" Champion: Razz Matazz, owned by ow
- `O6` / `owner_tail_trunc`: 12 1/2-15" Champion: Turbo Charge, owned by ow

### `1996 Vol II pg 93-162 back reversed_ocr_hqmax.txt` (FAIL)
- `O6` / `owner_tail_trunc`: 12 1/2-15" Reserve: Horsemasters Willy, owned by ow
- `O6` / `owner_tail_trunc`: 12 1/2-15" Chanpion: Salishan Maggie, owned by ow

### `1996 Vol II pg 93-162 back_ocr_hqmax.txt` (FAIL)
- `O6` / `owner_tail_trunc`: 12 1/2-15" Reserve: Horsemasters Willy, owned by ow

### `1996 Vol II pg 93-162 front_ocr_hqmax.txt` (FAIL)
- `O6` / `owner_tail_trunc`: Under 12 1/2" Reserve: Heaven Hill Jezebel, owned by ow
- `O6` / `owner_tail_trunc`: Over 12 1/2" Champion: Three Oaks Hunter, owned by ow

### `Document_2026-11-04_144208_ocr_hqmax.txt` (FAIL)
- `C1` / `class_header_gap`: 4th: Hart Farm Hammer of Ravenswood, owned by Janet Sutcliffe
