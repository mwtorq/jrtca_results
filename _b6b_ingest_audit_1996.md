# B6b cleanup + ingest audit — 1996

Catalog: `_OCR_CLEANUP_CATALOG_HANDOFF.md`
Volumes: 30  cleaned=28  PASS=23  WARN=0  FAIL=7
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
| FAIL | True | 2 | 0 | O6×1,C1×1 | `1996 Vol 1 pg 111-160 back reversed_ocr_hqmax.txt` |
| PASS | True | 0 | 0 | — | `1996 Vol 1 pg 111-160 back_ocr_hqmax.txt` |
| PASS | True | 0 | 0 | — | `1996 Vol 1 pg 111-160 front_ocr_hqmax.txt` |
| PASS | False | 0 | 0 | — | `1996 Vol 1 pg 161-178 back reversed_ocr_hqmax.txt` |
| PASS | False | 0 | 0 | — | `1996 Vol 1 pg 161-178 back_ocr_hqmax.txt` |
| FAIL | True | 1 | 0 | C1/C6×1 | `1996 Vol 1 pg 161-178 front_ocr_hqmax.txt` |
| FAIL | True | 1 | 0 | C1/C6×1 | `1996 Vol 1 pg 21-60 back reversed_ocr_hqmax.txt` |
| PASS | True | 0 | 0 | — | `1996 Vol 1 pg 21-60 back_ocr_hqmax.txt` |
| PASS | True | 0 | 0 | — | `1996 Vol 1 pg 21-60 front_ocr_hqmax.txt` |
| PASS | True | 0 | 0 | — | `1996 Vol 1 pg 61-110 back reversed_ocr_hqmax.txt` |
| PASS | True | 0 | 0 | — | `1996 Vol 1 pg 61-110 back_ocr_hqmax.txt` |
| FAIL | True | 3 | 0 | S1-S3×2,O6×1 | `1996 Vol 1 pg 61-110 front_ocr_hqmax.txt` |
| PASS | True | 0 | 0 | — | `1996 Vol II pg 163-220 back reversed_ocr_hqmax.txt` |
| PASS | True | 0 | 0 | — | `1996 Vol II pg 163-220 back_ocr_hqmax.txt` |
| FAIL | True | 1 | 0 | C1×1 | `1996 Vol II pg 163-220 front_ocr_hqmax.txt` |
| PASS | True | 0 | 0 | — | `1996 Vol II pg 23-92 back reversed_ocr_hqmax.txt` |
| PASS | True | 0 | 0 | — | `1996 Vol II pg 23-92 back_ocr_hqmax.txt` |
| PASS | True | 0 | 0 | — | `1996 Vol II pg 23-92 front (missing 1 pgs)_ocr_hqmax.txt` |
| PASS | True | 0 | 0 | — | `1996 Vol II pg 23-92 front (missing 2 pgs)_ocr_hqmax.txt` |
| PASS | True | 0 | 0 | — | `1996 Vol II pg 23-92 front_ocr_hqmax.txt` |
| FAIL | True | 1 | 0 | C1×1 | `1996 Vol II pg 93-162 back reversed_ocr_hqmax.txt` |
| PASS | True | 0 | 0 | — | `1996 Vol II pg 93-162 back_ocr_hqmax.txt` |
| PASS | True | 0 | 0 | — | `1996 Vol II pg 93-162 front_ocr_hqmax.txt` |
| PASS | True | 0 | 0 | — | `Document_2026-11-04_144208_ocr_hqmax.txt` |
| PASS | True | 0 | 0 | — | `Document_2026-11-04_144530_ocr_hqmax.txt` |
| PASS | True | 0 | 0 | — | `Document_2026-11-04_145355_ocr_hqmax.txt` |
| PASS | True | 0 | 0 | — | `Document_2026-11-04_145925_ocr_hqmax.txt` |
| PASS | True | 0 | 0 | — | `Document_2026-11-04_151058_ocr_hqmax.txt` |
| PASS | True | 0 | 0 | — | `Document_2026-11-04_152834_ocr_hqmax.txt` |
| FAIL | True | 1 | 0 | O6×1 | `Document_2026-11-04_153208_ocr_hqmax.txt` |

## Sample residual hits (after cleanup)

### `1996 Vol 1 pg 111-160 back reversed_ocr_hqmax.txt` (FAIL)
- `O6` / `owner_tail_trunc`: 3rd: Wesworld Hamilton, owned by Christi Parkison & Suzi Utz
- `C1` / `class_header_gap`: 4th: Blue Moon Ena, owned by Anne Davis

### `1996 Vol 1 pg 161-178 front_ocr_hqmax.txt` (FAIL)
- `C1/C6` / `incomplete_entries`: PARKED jr54: Starters Agility Entries: 6 missing 4th-5th after Braque (OCR blank | places=0/6 | Agility I, Off Lead                                         

### `1996 Vol 1 pg 21-60 back reversed_ocr_hqmax.txt` (FAIL)
- `C1/C6` / `incomplete_entries`: # PARKED jr54: Arizona Bred 5th not printed on PDF (Entries: 7) | places=0/6 | PARKED jr54: Dog Pups 6-9 smooth 1st-5th on prior yearbook p

### `1996 Vol 1 pg 61-110 front_ocr_hqmax.txt` (FAIL)
- `O6` / `owner_tail_trunc`: 2nd: Bobby Duty, owned by Ill
- `S1-S3` / `two_column_smash`: Champion: not reported
- `S1-S3` / `two_column_smash`: Reserve: not reported

### `1996 Vol II pg 163-220 front_ocr_hqmax.txt` (FAIL)
- `C1` / `class_header_gap`: 3rd: Eyek of Rutgers Creek, owned by M. Storeken & A. Burigo

### `1996 Vol II pg 93-162 back reversed_ocr_hqmax.txt` (FAIL)
- `C1` / `class_header_gap`: 2nd: Fox Run Sonic, owned by Sandra Ferber

### `Document_2026-11-04_153208_ocr_hqmax.txt` (FAIL)
- `O6` / `owner_tail_trunc`: 4th: Russell-M-Up Cool Hand Luke, owned by
