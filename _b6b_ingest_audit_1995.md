# B6b cleanup + ingest audit — 1995

Catalog: `_OCR_CLEANUP_CATALOG_HANDOFF.md`
Volumes: 5  cleaned=0  PASS=1  WARN=0  FAIL=4
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
| FAIL | False | 6 | 0 | C1/C6×5,C1×1 | `Document_2026-11-04_124005_ocr_hqmax.txt` |
| FAIL | False | 8 | 0 | C1/C6×7,C1×1 | `Document_2026-11-04_124704_ocr_hqmax.txt` |
| PASS | False | 0 | 0 | — | `Document_2026-11-04_130318_ocr_hqmax.txt` |
| FAIL | False | 21 | 0 | C1/C6×11,C1×6,H8×3,C7×1 | `Document_2026-11-04_134403_ocr_hqmax.txt` |
| FAIL | False | 10 | 0 | C1/C6×7,C1×3 | `Document_2026-11-04_142425_ocr_hqmax.txt` |

## Sample residual hits (after cleanup)

### `Document_2026-11-04_124005_ocr_hqmax.txt` (FAIL)
- `C1/C6` / `incomplete_entries`: Dogs, 1 yr & over, 10-12 1/2", br/r                                              | places=1/6 | BEST DOG & RESERVE
- `C1/C6` / `incomplete_entries`: Open Adults, 10-12 1/2" Entries: 7 | places=1/6 | Bitch Pups, 6 up to 9 months, 10-12 1/2" Entries: 7
- `C1/C6` / `incomplete_entries`: Dog Pups, 6 up to 9 months, 12 1/2-15" Entries: 4 | places=2/4 | Dog Pups, 6 up to 9 months, 12 1/2-15"
- `C1/C6` / `incomplete_entries`: Bitch Pups, 9 up to 12 months, r/br                                              | places=3/6 | Bitches, 1 yr & over, 10-12 1/2"
- `C1/C6` / `incomplete_entries`: Novice Obedience                                                                 | places=3/6 | Agility, On Lead I--Novice                                  
- `C1` / `midclass_page_dropout`: Agility I--Off Lead                                                              | after page got 1th expected 2 | 1st: Crossruff Palmer, owned by Deborah Holly

### `Document_2026-11-04_124704_ocr_hqmax.txt` (FAIL)
- `C1/C6` / `incomplete_entries`: Dogs, 1 yr & over, 12-1/2-15", br/r                                           En | places=3/6 | RACING CHAMPIONS:
- `C1/C6` / `incomplete_entries`: Bitches, 1 yr & over, 12 1/2-15" Entries: 16 | places=0/6 | Bitch Pups, 6 up to 9 months, 10-12 1/2" Entries: 4
- `C1/C6` / `incomplete_entries`: Bitch Pups, 6 up to 9 months, 10-12 1/2" Entries: 4 | places=0/4 | Bitch Pups, 6 up to 9 months, 12 1/2-15" Entries: 2
- `C1/C6` / `incomplete_entries`: Bitch Pups, 6 up to 9 months, 10-12 1/2" Entries: 5 | places=0/5 | Dog Pups, 6 up to 9 months, r/br                            
- `C1/C6` / `incomplete_entries`: Dogs, 1 yr & over, 10-12 1/2", smooth                                          E | places=0/3 | Bitches, 1 yr & over, 10-12 1/2"
- `C1/C6` / `incomplete_entries`: Open Adults                                                                      | places=3/6 | PUPPY CHAMPIONSHIP                                          
- `C1/C6` / `incomplete_entries`: Dog Pups, 6 up to 9 months                                                       | places=2/5 | Dog Pups, 9 up to 12 months                                 
- `C1` / `midclass_page_dropout`: Dogs, 1 yr & over, 12 1/2-15" Entries: 8 | after page got 4th expected 2 | 4th: Westwood Sparkle, owned by Alice Reynolds

### `Document_2026-11-04_134403_ocr_hqmax.txt` (FAIL)
- `H8` / `champ_abbrev`: 12 1/2-15" Cham
- `H8` / `champ_abbrev`: serve: Wild Goose National, owned by CJ & Ouida Harris
- `H8` / `champ_abbrev`: serve: Dutch Creek Classy, owned by Bonita Knickmeyer
- `C1/C6` / `incomplete_entries`: Pups, 6 up to 9 months, 12 1/2-15" Entries: 4 | places=2/4 | Pups, 9 up to 12 months, 10-12 1/2" Entries: 4
- `C1/C6` / `incomplete_entries`: Pups, 9 up to 12 months, 10-12 1/2" Entries: 4 | places=1/4 | Dogs, 1 yr & over, 10-12 1/2" Entries: 17
- `C1/C6` / `incomplete_entries`: Dog Pups, 9 up to 12 months, smooth                                          Ent | places=2/4 | Dogs, 1 yr & over, 12 1/2-15" r & br                        
- `C1/C6` / `incomplete_entries`: Yearbook, Vol. Il                                 99                  Buckeye St | places=0/4 | Entries: 7
- `C1/C6` / `incomplete_entries`: Entries: 7 | places=0/6 | Entries: 4
- `C1/C6` / `incomplete_entries`: Entries: 4 | places=0/4 | Entries: 9
- `C1/C6` / `incomplete_entries`: Entries: 9 | places=0/6 | Entries: 11
- `C1/C6` / `incomplete_entries`: Entries: 11 | places=0/6 | Entries: 3
- `C1/C6` / `incomplete_entries`: Entries: 3 | places=0/3 | Entries: 10

### `Document_2026-11-04_142425_ocr_hqmax.txt` (FAIL)
- `C1/C6` / `incomplete_entries`: Bitch Pups, 9 up to 12 months, r/br                                              | places=1/6 | AGILITY
- `C1/C6` / `incomplete_entries`: JRTCA Working Terrier Bitch                                                      | places=3/6 | CONFORMATION DIVISION
- `C1/C6` / `incomplete_entries`: Entries: 7 | places=0/6 | Entries: 12
- `C1/C6` / `incomplete_entries`: Entries: 12 | places=0/6 | Entries: 12
- `C1/C6` / `incomplete_entries`: Bitches, 1 yr & over 12 1/2-15" Entries: 11 | places=1/6 | JRTCA Working Terrier
- `C1/C6` / `incomplete_entries`: Agility I, Off Lead, 10-12 1/2" Entries: 4 | places=2/4 | Agility I, Off Lead, 12 12/-15" Entries: 6
- `C1/C6` / `incomplete_entries`: Bitch Pups, 6 up to 12 months                                                Ent | places=3/6 | Dogs, 1 yr & over, 10-12 1/2" Entries: 13
- `C1` / `midclass_page_dropout`: Source: Document_2026-11-04_142425.pdf | after page got 5th expected 1 | 5th: White Gate Jackie, owned by Patricia Hafen
- `C1` / `midclass_page_dropout`: Jasmine, owned by Rick & Leslie Hemsing – Entries: 0 | after page got 4th expected 1 | 4th: Fiona, owned by Missy Kulbacky
- `C1` / `midclass_page_dropout`: Dogs, 1 yr & over, 10-12 1/2", r/br                                              | after page got 3th expected 2 | 3rd: Camerton Hall Echo, owned by Jack & Paul
