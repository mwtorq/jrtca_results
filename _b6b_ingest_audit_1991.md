# B6b cleanup + ingest audit — 1991

Catalog: `_OCR_CLEANUP_CATALOG_HANDOFF.md`
Volumes: 4  cleaned=0  PASS=0  WARN=0  FAIL=4
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
| FAIL | False | 11 | 0 | C1/C6×8,C1×3 | `Document_2026-11-03_201758_ocr_hqmax.txt` |
| FAIL | False | 14 | 0 | C1/C6×10,C1×3,S1-S3×1 | `Document_2026-11-03_205014_ocr_hqmax.txt` |
| FAIL | False | 18 | 0 | C1/C6×16,C1×2 | `Document_2026-11-03_210248_ocr_hqmax.txt` |
| FAIL | False | 1 | 0 | C1/C6×1 | `Document_2026-11-03_211454_ocr_hqmax.txt` |

## Sample residual hits (after cleanup)

### `Document_2026-11-03_201758_ocr_hqmax.txt` (FAIL)
- `C1/C6` / `incomplete_entries`: Bitch Pups, 9 up to 12 months                                                    | places=2/5 | OPEN (Adults)                                               
- `C1/C6` / `incomplete_entries`: Bitches, 1 yr & over, 10--12-1/2" Entries: 14 | places=2/6 | Charles Sauter, Go-to-Ground
- `C1/C6` / `incomplete_entries`: Bitches, 1 yr & over, 12-1/2--15", br/r                                          | places=0/3 | Open Class
- `C1/C6` / `incomplete_entries`: Bitches, 1 yr & over, 12-1/2--15" Entries: 7 | places=2/6 | STEEPLECHASE RACES
- `C1/C6` / `incomplete_entries`: Bitch Pups, 6 up to 12 months, 12-1/2--15" Entries: 4 | places=2/4 | Dogs, 1 yr & over, 10--12-1/2" Entries: 5
- `C1/C6` / `incomplete_entries`: Bitches, 1 yr & over, 12-1/2--15" Entries: 6 | places=3/6 | RACING CHAMPIONS:
- `C1/C6` / `incomplete_entries`: Dogs, 1 yr & over, 10-12-1/2" Entries: 10 | places=0/6 | Judges:         Marcy Ortolano, Conformation; Richard Ortola
- `C1/C6` / `incomplete_entries`: Child Handler                                                      Entries: 4 | places=1/4 | Junior Handler                                              
- `C1` / `midclass_page_dropout`: Bitch Pups, 9 up to 12 months                                                    | after page got 2th expected 3 | 2nd: Rustler's Peggy Sue, owned by Brenda Swa
- `C1` / `midclass_page_dropout`: JRTCA Novice Class – Entries: 15 | after page got 4th expected 5 | 4th: River Run lvy, owned by Rom Roscioli
- `C1` / `midclass_page_dropout`: Family Class                                                           Entries:  | after page got 1th expected 6 | 1st: Winston of The Hollow, owned by The Holl

### `Document_2026-11-03_205014_ocr_hqmax.txt` (FAIL)
- `C1/C6` / `incomplete_entries`: Novice (Puppies)Entries: 4 | places=2/4 | Novice (Adults)Entries: 8
- `C1/C6` / `incomplete_entries`: Puppies, 4 up to 6 months                                                        | places=3/6 | Dog Pups, 6 up to 12 months                                 
- `C1/C6` / `incomplete_entries`: Bitches, 1 yr & over, 12-1/2--15" Entries: 10 | places=3/6 | STEEPLECHASE RACES
- `C1/C6` / `incomplete_entries`: Dog Pups, 6 up to 12 months, 10--12-1/2" Entries: 4 | places=2/4 | Dog Pups, 6 up to 12 months, 12-1/2--15" Entries: 2
- `C1/C6` / `incomplete_entries`: Bitch Pups, 6 up to 12 months, 10--12-1/2" Entries: 4 | places=2/4 | Bitch Pups, 6 up to 12 months, 12-1/2--15" Entries: 3
- `C1/C6` / `incomplete_entries`: Novice (Puppies)                                                                 | places=1/6 | Novice (Adults)                                             
- `C1/C6` / `incomplete_entries`: Dog Pups, 6 up to 12 months, 12-1/2--15" Entries: 3 | places=0/3 | Bitch Pups, 6 up to 12 months, 10--12-1/2" Entries: 4
- `C1/C6` / `incomplete_entries`: Dogs, 1 yr & over, 10--12-1/2" Entries: 5 | places=2/5 | Dogs, 1 yr & over, 12-1/2--15" Entries: 16
- `C1/C6` / `incomplete_entries`: Bitches, 1 yr & over, 10--12-1/2" Entries: 4 | places=2/4 | Bitches, 1 yr & over, 12-1/2--15" Entries: 12
- `C1` / `midclass_page_dropout`: Source: Document_2026-11-03_205014.pdf | after page got 5th expected 1 | 5th: Beau Monde Ruff E Nuff, owned by Patti St. Clair
- `C1` / `midclass_page_dropout`: Bitch Pups, 6 up to 12 months                                                    | after page got 6th expected 4 | 6th: Ms. Scarlett of Hidden Hollow, owned by 
- `C1` / `midclass_page_dropout`: Dogs, 1 yr & over, 12-1/2--15" Entries: 16 | after page got 1th expected 4 | 1st: Raheen Lilac Magpie, owned by Jaci Jenson

### `Document_2026-11-03_210248_ocr_hqmax.txt` (FAIL)
- `C1/C6` / `incomplete_entries`: Novice (Puppies)                                                                 | places=1/6 | Novice (Adults)                                             
- `C1/C6` / `incomplete_entries`: Novice (Adults)                                                                  | places=3/6 | Bitch Pups, 6 up to 12 months                               
- `C1/C6` / `incomplete_entries`: Dogs, 1 yr & over, 10-—-12-1/2" Entries: 5 | places=2/5 | Dogs, 1 yr & over, 12-1/2--15" Entries: 6
- `C1/C6` / `incomplete_entries`: Dogs, 1 yr & over, 12-1/2--15" Entries: 6 | places=3/6 | Bitches, 1 yr & over, 10--12-1/2" Entries: 6
- `C1/C6` / `incomplete_entries`: Bitches, 1 yr & over, 12-1/2-15" Entries: 4 | places=1/4 | RACING CHAMPIONS:
- `C1/C6` / `incomplete_entries`: Bitches, 1 yr & over, 12-1/2-15" Entries: 9 | places=3/6 | STEEPLECHASE RACES
- `C1/C6` / `incomplete_entries`: Bitch Pups, 6 up to 12 months                                                    | places=3/6 | Huntington Beach, California, August 10-11, 1991
- `C1/C6` / `incomplete_entries`: Bitch Pups, 6 up to 12 months, 12-1/2-15" – Entries: 10 | places=2/6 | Dogs, 1 yr & over, 10--12-1/2" – Entries: 12
- `C1/C6` / `incomplete_entries`: Bitches, 1 yr & over, 12-1/2-15", smooth                                         | places=2/6 | CHAMPIONSHIP CERTIFICATE (10-12 1/2") Entries: 17
- `C1/C6` / `incomplete_entries`: Child & Junior Handler                                                           | places=2/6 | Bred by Exhibitor                                           
- `C1/C6` / `incomplete_entries`: Dog Pups, 6 up to 12 months                                                      | places=3/6 | Bitch Pups, 6 up to 12 months                               
- `C1/C6` / `incomplete_entries`: Dog Pups, 6 up to 12 months, 12-1/2-15" Entries: 4 | places=2/4 | Judges:        Molly Harsh, Conformation; Ken Chambers, Go-t

### `Document_2026-11-03_211454_ocr_hqmax.txt` (FAIL)
- `C1/C6` / `incomplete_entries`: PRE-Novice PUPPIES                                                   Entries: 9 | places=3/6 | Novice (Puppies)
