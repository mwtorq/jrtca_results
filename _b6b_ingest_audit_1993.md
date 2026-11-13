# B6b cleanup + ingest audit — 1993

Catalog: `_OCR_CLEANUP_CATALOG_HANDOFF.md`
Volumes: 5  cleaned=1  PASS=1  WARN=0  FAIL=4
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
| FAIL | False | 25 | 0 | C1/C6×13,C1×10,O6×2 | `Document_2026-11-03_224445_ocr_hqmax.txt` |
| FAIL | False | 14 | 0 | C1/C6×9,C1×5 | `Document_2026-11-03_230536_ocr_hqmax.txt` |
| FAIL | True | 3 | 0 | C1×1,C1/C6×1,S1-S3×1 | `Document_2026-11-03_231659_ocr_hqmax.txt` |
| FAIL | False | 20 | 0 | C1/C6×14,C1×3,S1-S3×3 | `Document_2026-11-03_233615_ocr_hqmax.txt` |
| PASS | False | 0 | 0 | — | `Document_2026-11-04_002601_ocr_hqmax.txt` |

## Sample residual hits (after cleanup)

### `Document_2026-11-03_224445_ocr_hqmax.txt` (FAIL)
- `C1` / `class_header_gap`: 4th: Tasha R:z
- `C1` / `class_header_gap`: 4th: White Spirits Orion, owned by Michelle Mezoe
- `C1` / `class_header_gap`: 4th: Three Oaks Britches, owned by Carolyn McGaughey
- `C1/C6` / `incomplete_entries`: A Yearbook, Vol. I           19           JRTCNC Win – Entries: 14 | places=0/6 | Entries: 7
- `C1/C6` / `incomplete_entries`: Entries: 7 | places=0/6 | Entries: 11
- `C1/C6` / `incomplete_entries`: Entries: 11 | places=0/6 | Entries: 15
- `C1/C6` / `incomplete_entries`: Entries: 15 | places=0/6 | Entries: 12
- `C1/C6` / `incomplete_entries`: Entries: 12 | places=0/6 | Entries: 6
- `C1/C6` / `incomplete_entries`: Entries: 6 | places=3/6 | Dogs, 1 yr & over, 12-1/2--15" Entries: 0
- `C1/C6` / `incomplete_entries`: Entries: 6 | places=0/6 | Entries: 11
- `C1/C6` / `incomplete_entries`: Entries: 11 | places=0/6 | Entries: 4
- `C1/C6` / `incomplete_entries`: Entries: 4 | places=0/4 | OPEN (Adults)                                               

### `Document_2026-11-03_230536_ocr_hqmax.txt` (FAIL)
- `C1/C6` / `incomplete_entries`: PRE-Novice PUPPIES                                                          Entr | places=3/6 | Novice (Puppies)                                            
- `C1/C6` / `incomplete_entries`: Novice (Puppies)                                                                 | places=3/6 | Novice (Adults)                                             
- `C1/C6` / `incomplete_entries`: Novice (Adults)                                                                  | places=3/6 | Bitch Pups, 6 up to 9 months                                
- `C1/C6` / `incomplete_entries`: DIVISION A, CONFORMATION – Entries: 4 | places=0/4 | Dog Pups, 4 up to 6 months – Entries: 13
- `C1/C6` / `incomplete_entries`: Bitch Pups, 6 up to 12 months, 10--12-1/2" Entries: 5 | places=1/5 | Bitch Pups, 6 up to 12 months, 12-1/2--15" Entries: 6
- `C1/C6` / `incomplete_entries`: JRTCA Working Terrier Dog                                                        | places=3/6 | JRTCA Working Terrier Bitch                                 
- `C1/C6` / `incomplete_entries`: Dog Pups, 6 up to 9 months                                                  Entr | places=3/6 | Bitches, 1 yr & over, 10-12-1/2", br/r                      
- `C1/C6` / `incomplete_entries`: Bitches, 1 yr & over, 12-1/2--15" Entries: 8 | places=2/6 | EOF
- `C1` / `midclass_page_dropout`: CHAMPIONSHIP CERTIFICATE (12-1/2--15")                            Entries: 16 | after page got 2th expected 4 | 2nd: Lil Rascals Jackie, owned by John Benintend
- `C1` / `midclass_page_dropout`: Dog Pups, 6 up to 9 months                                                     E | after page got 3th expected 4 | 3rd: The Hollow Tracker, owned by The Hollow 
- `C1` / `midclass_page_dropout`: Novice (Adults)                                                                  | after page got 2th expected 4 | 2nd: North Country Penn, owned by Marilyn Pro
- `C1` / `midclass_page_dropout`: Veteran Class – Entries: 5 | after page got 4th expected 5 | 4th: The Manor Bally, owned by C.Young & D.Tarchini

### `Document_2026-11-03_231659_ocr_hqmax.txt` (FAIL)
- `C1` / `class_header_gap`: 1st: Wyndcroft Natasha, owned by K.Hunter & J.Finkernagel
- `C1/C6` / `incomplete_entries`: OPEN (Puppies) Entries: 4 | places=1/4 | OPEN (Adults)                                               
- `S1-S3` / `two_column_smash`: 2nd: LB, owned by Deborah Bickler

### `Document_2026-11-03_233615_ocr_hqmax.txt` (FAIL)
- `C1/C6` / `incomplete_entries`: PRE-Novice PUPPIES                                                               | places=2/6 | Novice (Puppies)                                            
- `C1/C6` / `incomplete_entries`: Bitch Pups, 6 up to 12 months, 10-12-12" Entries: 5 | places=0/5 | Bitch Pups, 6 up to 12 months, 12-1/2--15" Entries: 4
- `C1/C6` / `incomplete_entries`: Bitch Pups, 4 up to 6 months                         Entries: 7 | places=3/6 | Chiid Handler                                               
- `C1/C6` / `incomplete_entries`: California Bred                                                                  | places=3/6 | JRTCA Working Terrier                                       
- `C1/C6` / `incomplete_entries`: Dogs, 1 yr & over, 12-1/2--15" Entries: 12 | places=1/6 | Dog Pups, 6 up to 9 months – Entries: 8
- `C1/C6` / `incomplete_entries`: Entries: 7 | places=0/6 | Bitch Pups, 9 up to 12 months
- `C1/C6` / `incomplete_entries`: Entries: 12 | places=0/6 | Dogs, 1 yr & over, 12-1/2--15"
- `C1/C6` / `incomplete_entries`: Dog Pups, 6 up to 12 months                                                   En | places=3/6 | Bitch Pups, 6 up to 12 months                               
- `C1/C6` / `incomplete_entries`: Novice (Puppies)                                                            Entr | places=3/6 | Mike Bales, J.C. Chambers, Go-to-Ground
- `C1/C6` / `incomplete_entries`: Bitch Pups, 9 up to 12 months                                               Entr | places=3/6 | Bitches, 1 yr & ov
- `C1/C6` / `incomplete_entries`: NTAIL BEAR, owned by Susan McRae – Entries: 9 | places=0/6 | OPEN (Adults)                                               
- `C1/C6` / `incomplete_entries`: Dog Pups, 6 up to 12 months, 10--12-1/2" Entries: 4 | places=2/4 | Dog Pups, 6 up to 12 months, 12-1/2--15" Entries: 4
