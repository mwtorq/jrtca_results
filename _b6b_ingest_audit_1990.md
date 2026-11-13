# B6b cleanup + ingest audit — 1990

Catalog: `_OCR_CLEANUP_CATALOG_HANDOFF.md`
Volumes: 5  cleaned=0  PASS=2  WARN=0  FAIL=3
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
| FAIL | False | 1 | 0 | C1/C6×1 | `scan_ocr_hqmax.txt` |
| FAIL | False | 31 | 0 | C1/C6×26,C1×5 | `Document_2026-11-03_192526_ocr_hqmax.txt` |
| FAIL | False | 55 | 0 | C1/C6×26,S1-S3×15,C1×14 | `Document_2026-11-03_200401_ocr_hqmax.txt` |
| PASS | False | 0 | 0 | — | `Document_2026-11-03_201432_ocr_hqmax.txt` |
| PASS | False | 0 | 0 | — | `Document_2026-11-03_201547_ocr_hqmax.txt` |

## Sample residual hits (after cleanup)

### `scan_ocr_hqmax.txt` (FAIL)
- `C1/C6` / `incomplete_entries`: Bitch Pups, 6 up to 12 months, over 12 1/2" - 15" Entries: 8 | places=1/6 | Bitches, 1 year and over, 10" - 12 1/2" Entries: 22

### `Document_2026-11-03_192526_ocr_hqmax.txt` (FAIL)
- `C1` / `class_header_gap`: 1st: Rushill Rake of Jumping Jax and Rushill Shark, owned by Sally McKenney
- `C1/C6` / `incomplete_entries`: Child Handler                                                      Entries: 8 | places=3/6 | Junior Handler                                              
- `C1/C6` / `incomplete_entries`: Dog Pups, 6 up to 9 months, 12-1/2--15" Entries: 4 | places=2/4 | New York Bred                                               
- `C1/C6` / `incomplete_entries`: PRE-Novice PUPPIES                                                 Entries: 7 | places=2/6 | Novice (Puppies)                                            
- `C1/C6` / `incomplete_entries`: Novice (Puppies)                                                                 | places=1/6 | Novice (Adults)                                             
- `C1/C6` / `incomplete_entries`: American Bred Dog                                                          Entri | places=3/6 | Bitch Pups, 6 up to 12 months, 10-12-1/2" Entries: 5
- `C1/C6` / `incomplete_entries`: Bitch Pups, 6 up to 12 months, 12-1/2--15" Entries: 3 | places=0/3 | Dogs, 1 yr & over, 10--12-1/2" Entries: 6
- `C1/C6` / `incomplete_entries`: Dogs, 1 yr & over, 10--12-1/2" Entries: 6 | places=3/6 | Dogs, 1 yr & over, 12-1/2--15" Entries: 5
- `C1/C6` / `incomplete_entries`: Novice (Adults)                                                                  | places=3/6 | OPEN (Puppies & Adults)                                     
- `C1/C6` / `incomplete_entries`: OPEN (Puppies & Adults)                                                          | places=3/6 | CHAMPIONSHIP CERTIFICATE                                    
- `C1/C6` / `incomplete_entries`: Dog Pups, 6 up to 12 months, 12-1/2—-15" Entries: 5 | places=2/5 | Bitch Pups, 6 up to 12 months, 10--12-1/2" Entries: 6
- `C1/C6` / `incomplete_entries`: Bitch Pups, 6 up to 12 months, 10--12-1/2" Entries: 6 | places=3/6 | Bitch Pups, 6 up to 12 months, 12-1/2-15" Entries: 3

### `Document_2026-11-03_200401_ocr_hqmax.txt` (FAIL)
- `C1/C6` / `incomplete_entries`: Novice (Puppies)                                                                 | places=1/6 | Novice (Adults)                                             
- `C1/C6` / `incomplete_entries`: OPEN (Adults)                                                                    | places=0/6 | 1st: Raincliff's Smooth Gerald, owned by George Ridler
- `C1/C6` / `incomplete_entries`: Entries: 18 | places=0/6 | Entries: 11
- `C1/C6` / `incomplete_entries`: Entries: 11 | places=0/6 | Entries: 2
- `C1/C6` / `incomplete_entries`: Entries: 4 | places=0/4 | Dog Pups, 9 up to 12 months
- `C1/C6` / `incomplete_entries`: Entries: 7 | places=0/6 | Bitch Pups, 9 up to 12 months
- `C1/C6` / `incomplete_entries`: Bitch Pups, 6 up to 12 months, 12-1/2-15" Entries: 6 | places=3/6 | Dogs, 1 yr & over, 10-12-1/2" Entries: 7
- `C1/C6` / `incomplete_entries`: Dogs, 1 yr & over, 10-12-1/2" Entries: 7 | places=3/6 | Dogs, 1 yr & over, 12-1/2-15" Entries: 5
- `C1/C6` / `incomplete_entries`: Bitch Pups, 6 up to 12 months, 10-12-1/2" Entries: 7 | places=3/6 | Bitch Pups, 6 up to 12 months, 12-1/2--15" Entries: 4
- `C1/C6` / `incomplete_entries`: Dogs, 1 yr & over, 10-12-1/2" Entries: 6 | places=3/6 | Dogs, 1 yr & over, 12-1/2-15" Entries: 5
- `C1/C6` / `incomplete_entries`: Dogs, 1 yr & over, 12-1/2-15" Entries: 5 | places=2/5 | Judges:        Alf Edmunds, Conformation; Bill Breakstone, G
- `C1/C6` / `incomplete_entries`: Child Handler                                                                    | places=3/6 | Junior Handler
