# B6b cleanup + ingest audit — 1995

Catalog: `_OCR_CLEANUP_CATALOG_HANDOFF.md`
Volumes: 5  cleaned=3  PASS=1  WARN=0  FAIL=4
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
| FAIL | True | 1 | 0 | C1×1 | `Document_2026-11-04_124005_ocr_hqmax.txt` |
| FAIL | True | 4 | 0 | C1/C6×4 | `Document_2026-11-04_124704_ocr_hqmax.txt` |
| PASS | True | 0 | 0 | — | `Document_2026-11-04_130318_ocr_hqmax.txt` |
| FAIL | False | 10 | 0 | C1/C6×7,C1×3 | `Document_2026-11-04_134403_ocr_hqmax.txt` |
| FAIL | False | 3 | 0 | C1/C6×2,C1×1 | `Document_2026-11-04_142425_ocr_hqmax.txt` |

## Sample residual hits (after cleanup)

### `Document_2026-11-04_124005_ocr_hqmax.txt` (FAIL)
- `C1` / `midclass_page_dropout`: Agility I--Off Lead                                                              | after page got 1th expected 2 | 1st: Crossruff Palmer, owned by Deborah Holly

### `Document_2026-11-04_124704_ocr_hqmax.txt` (FAIL)
- `C1/C6` / `incomplete_entries`: Bitches, 1 yr & over, 12 1/2-15" Entries: 16 | places=0/6 | Bitch Pups, 6 up to 9 months, 10-12 1/2" Entries: 4
- `C1/C6` / `incomplete_entries`: Bitch Pups, 6 up to 9 months, 10-12 1/2" Entries: 4 | places=0/4 | Bitch Pups, 6 up to 9 months, 12 1/2-15" Entries: 2
- `C1/C6` / `incomplete_entries`: Bitch Pups, 6 up to 9 months, 10-12 1/2" Entries: 5 | places=0/5 | Dog Pups, 6 up to 9 months, r/br                            
- `C1/C6` / `incomplete_entries`: Dogs, 1 yr & over, 10-12 1/2", smooth                                          E | places=0/3 | Bitches, 1 yr & over, 10-12 1/2"

### `Document_2026-11-04_134403_ocr_hqmax.txt` (FAIL)
- `C1/C6` / `incomplete_entries`: Yearbook, Vol. Il                                 99                  Buckeye St | places=0/4 | Entries: 7
- `C1/C6` / `incomplete_entries`: Entries: 7 | places=0/6 | Entries: 4
- `C1/C6` / `incomplete_entries`: Entries: 4 | places=0/4 | Entries: 9
- `C1/C6` / `incomplete_entries`: Entries: 9 | places=0/6 | Entries: 11
- `C1/C6` / `incomplete_entries`: Entries: 11 | places=0/6 | Entries: 3
- `C1/C6` / `incomplete_entries`: Entries: 3 | places=0/3 | Entries: 10
- `C1/C6` / `incomplete_entries`: Entries: 10 | places=0/6 | EOF
- `C1` / `midclass_page_dropout`: Novice, On Lead                                                             Entr | after page got 3th expected 7 | 3rd: Tortilla Flat Streak, owned by Gaye Ann 
- `C1` / `midclass_page_dropout`: Bitches, 1 yr & over 12 1/2-15" Entries: 13 | after page got 3th expected 6 | 3rd: Thimble Farm Rocket, owned by Val Wasch
- `C1` / `midclass_page_dropout`: Bitch Pups, 6 up to 9 months, smooth                                        Entr | after page got 2th expected 6 | 2nd: Foxport La:

### `Document_2026-11-04_142425_ocr_hqmax.txt` (FAIL)
- `C1/C6` / `incomplete_entries`: Entries: 7 | places=0/6 | Entries: 12
- `C1/C6` / `incomplete_entries`: Entries: 12 | places=0/6 | Entries: 12
- `C1` / `midclass_page_dropout`: Jasmine, owned by Rick & Leslie Hemsing – Entries: 0 | after page got 4th expected 1 | 4th: Fiona, owned by Missy Kulbacky
