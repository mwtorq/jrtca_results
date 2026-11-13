# B6b cleanup + ingest audit — 1992

Catalog: `_OCR_CLEANUP_CATALOG_HANDOFF.md`
Volumes: 6  cleaned=0  PASS=0  WARN=0  FAIL=6
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
| FAIL | False | 4 | 0 | C1/C6×4 | `Document_2026-11-03_212153_ocr_hqmax.txt` |
| FAIL | False | 25 | 0 | C1/C6×20,C1×5 | `Document_2026-11-03_212636_ocr_hqmax.txt` |
| FAIL | False | 7 | 0 | C1/C6×6,C1×1 | `Document_2026-11-03_213104_ocr_hqmax.txt` |
| FAIL | False | 12 | 0 | C1/C6×7,C1×5 | `Document_2026-11-03_220343_ocr_hqmax.txt` |
| FAIL | False | 5 | 0 | C1/C6×2,C1×2,O6×1 | `Document_2026-11-03_220931_ocr_hqmax.txt` |
| FAIL | False | 15 | 0 | C1/C6×11,C1×4 | `Document_2026-11-03_221749_ocr_hqmax.txt` |

## Sample residual hits (after cleanup)

### `Document_2026-11-03_212153_ocr_hqmax.txt` (FAIL)
- `C1/C6` / `incomplete_entries`: PRE-Novice PUPPIES                                                               | places=3/6 | Novice (Puppies)                                            
- `C1/C6` / `incomplete_entries`: Novice (Adults)                                                                  | places=2/6 | OPEN (Adults)                                               

### `Document_2026-11-03_212636_ocr_hqmax.txt` (FAIL)
- `C1/C6` / `incomplete_entries`: Dog Pups, 6 up to 12 months, 12-1/2--15" Entries: 10 | places=2/6 | Roger North, Conformation; Bill Breakstone, Go-to-Ground
- `C1/C6` / `incomplete_entries`: Dog Pups, 6 up to 12 months, 12-1/2-15" Entries: 5 | places=0/5 | Bitch Pups, 6 up to 12 months, 10-12-1/2" Entries: 6
- `C1/C6` / `incomplete_entries`: Dogs, 1 yr & over, 12-1/2--15" Entries: 21 | places=3/6 | Bitches, 1 yr & over, 10-12-1/2" Entries: 16
- `C1/C6` / `incomplete_entries`: Bitch Pups, 6 up to 12 months, 10-12-1/2" Entries: 5 | places=2/5 | Go-to-Ground
- `C1/C6` / `incomplete_entries`: Hollow Terriers – Entries: 13, owned by C.Tatum & S.Yancey | places=2/6 | Bitch Pups, 9 up to 12 months, 10-15", br/r                 
- `C1/C6` / `incomplete_entries`: Dog and Bitch Pups, 6 up to 12 months, 10--12-1/2" Entries: 6 | places=2/6 | Dog and Bitch Pups, 6 up to 12 months, 12-1/2--15" Entries: 
- `C1/C6` / `incomplete_entries`: PRE-Novice PUPPIES                                                               | places=3/6 | Novice (Puppies)                                            
- `C1/C6` / `incomplete_entries`: Bitches, 1 yr & over, 12-1/2--15" Entries: 16 | places=3/6 | STEEPLECHASE RACES
- `C1/C6` / `incomplete_entries`: Dog Pups, 6 up to 12 months, 12-1/2--15" Entries: 5 | places=2/5 | Bitch Pups, 6 up to 12 months, 10--12-1/2" Entries: 4
- `C1/C6` / `incomplete_entries`: Bitches, 1 yr & over, 10-12-1/2" Entries: 20 | places=3/6 | Bitches, 1 yr & over, 12-1/2-15" Entries: 10
- `C1/C6` / `incomplete_entries`: Bitches, 1 yr & over, 12-1/2-15" Entries: 10 | places=2/6 | Joan Stroh, Conformation; Jay Stroh, Go-to-Ground
- `C1/C6` / `incomplete_entries`: Novice (Puppies)                                                                 | places=1/6 | Novice (Adults)                                             

### `Document_2026-11-03_213104_ocr_hqmax.txt` (FAIL)
- `C1/C6` / `incomplete_entries`: Bitch Pups, 6 up to 12 months                                                    | places=3/6 | Dogs; 1 yr & over, 12-1/2--15" Entries: 16
- `C1/C6` / `incomplete_entries`: Novice (Puppies)                                                                 | places=3/6 | Novice (Adults)                                             
- `C1/C6` / `incomplete_entries`: OPEN (Puppies)                                                                   | places=1/4 | OPEN (Adults)                                               
- `C1/C6` / `incomplete_entries`: Entries: 12 | places=0/6 | Entries: 12
- `C1/C6` / `incomplete_entries`: Entries: 12 | places=1/6 | Dogs; 1 yr & over, 10--12-1/2", br/r                        
- `C1/C6` / `incomplete_entries`: Novice (Adults)                                                                  | places=2/6 | Bitches, 1 yr & over, 10-12-1/2" Entries: 13
- `C1` / `midclass_page_dropout`: Dogs, 1 yr & over, 12-1/2--15", br/r                                             | after page got 5th expected 3 | 5th: Katy Scarlett, owned by Michelle Clark

### `Document_2026-11-03_220343_ocr_hqmax.txt` (FAIL)
- `C1` / `class_header_gap`: 4th: Hannie, owned by David & Nancy Drown
- `C1/C6` / `incomplete_entries`: OPEN (Puppies)                                                                   | places=2/4 | OPEN (Adults)                                               
- `C1/C6` / `incomplete_entries`: Dogs, 1 yr & over, 10--12-1/2" Entries: 9 | places=3/6 | Dogs, 1 yr & over, 12-1/2--15" Entries: 20
- `C1/C6` / `incomplete_entries`: Bitches, 1 yr & over, 12-1/2--15" Entries: 8 | places=2/6 | Bitch Pups, 6 up to 12 months                               
- `C1/C6` / `incomplete_entries`: Bitches, 1 yr & over, 12-1/2--15" Entries: 4 | places=1/4 | Tarheel Working Terrier Trial
- `C1/C6` / `incomplete_entries`: Child/Junior Handler                                           Entries: 7 | places=3/6 | Bred by Exhibitor Dog                                       
- `C1/C6` / `incomplete_entries`: Bitch Pups, 9 up to 12 months, smooth                                  Entries:  | places=2/5 | Bitch Pups, 9 up to 12 months, br/rough                     
- `C1/C6` / `incomplete_entries`: Dogs, 1 yr & over, 12-12-15", smooth                                    Entries: | places=2/6 | PRE-Novice PUPPIES                                          
- `C1` / `midclass_page_dropout`: Dog Pups, 9 up to 12 months                                                Entri | after page got 4th expected 7 | 4th: Hannie, owned by David & Nancy Drown
- `C1` / `midclass_page_dropout`: OPEN (Adults)                                                                Ent | after page got 2th expected 4 | 2nd: Goulden's Ridge Courtney, owned by Kelly
- `C1` / `midclass_page_dropout`: Bitch Pups, 6 up to 12 months, 10--12-1/2" Entries: 8 | after page got 6th expected 5 | 6th: Portadown Minx, owned by Ann Norton
- `C1` / `midclass_page_dropout`: Stud Dog and Get                                                               E | after page got 3th expected 6 | 3rd: Prestwick's Rattler, owned by Sally Yanc

### `Document_2026-11-03_220931_ocr_hqmax.txt` (FAIL)
- `C1/C6` / `incomplete_entries`: Pups, 4 up to 6 months                                                        En | places=3/6 | Child Handler                                               
- `C1/C6` / `incomplete_entries`: OPEN (Puppies)                                                                   | places=0/4 | OPEN (Adults)                                               
- `C1` / `midclass_page_dropout`: Source: Document_2026-11-03_220931.pdf | after page got 4th expected 1 | 4th: Farmcliff Kathy, owned by Bob & Genie Franklin
- `C1` / `midclass_page_dropout`: Dogs, 1 yr & over, 12-1/2--16" Entries: 10 | after page got 3th expected 7 | 3rd: JoJo of Blackiand, owned by Debra & John Cox
- `O6` / `owner_tail_trunc`: Spects, owned by

### `Document_2026-11-03_221749_ocr_hqmax.txt` (FAIL)
- `C1/C6` / `incomplete_entries`: Dogs, 1 yr & over, 10--12-1/2" Entries: 4 | places=2/4 | Dogs, 1 yr & over, 12-12-15" Entries: 7
- `C1/C6` / `incomplete_entries`: Dogs, 1 yr & over, 12-1/2--15" Entries: 9 | places=3/6 | Bitches, 1 yr & over, 10--12-1/2" Entries: 9
- `C1/C6` / `incomplete_entries`: Bitches, 1 yr & over, 12-1/2--15" Entries: 7 | places=3/6 | STEEPLECHASE RACES
- `C1/C6` / `incomplete_entries`: Pups, 6 up to 12 months, 10-12-1/2" Entries: 5 | places=1/5 | Pups, 6 up to 12 months, 12-1/2--15" Entries: 6
- `C1/C6` / `incomplete_entries`: Dogs, 1 yr & over, 12-1/2--156" Entries: 9 | places=3/6 | Bitches, 1 yr & over, 10-12-12" Entries: 8
- `C1/C6` / `incomplete_entries`: Novice (Pupples)                                                                 | places=1/6 | Judges:       Jack Batzer, Conformation; Louise Thomas, Go-t
- `C1/C6` / `incomplete_entries`: Dog Pups, 6 up to 12 months, 10--12-1/2" Entries: 4 | places=1/4 | Dog Pups, 6 up to 12 months, 12-1/2-16" Entries: 4
- `C1/C6` / `incomplete_entries`: Bitch Pups, 6 up to 12 months, 10--12-1/2" Entries: 3 | places=0/3 | Bitch Pups, 6 up to 12 months, 12-1/2--16" Entries: 1
- `C1/C6` / `incomplete_entries`: Novice (Puppies)                                                        Entries: | places=2/6 | Novice (Adults)                                             
- `C1/C6` / `incomplete_entries`: OPEN (Adults)                                                                    | places=2/6 | JUDGES:     Martyn Hulme, Conformation; Laurie Lewis, Go-to-
- `C1/C6` / `incomplete_entries`: Dog Pups, 6 up to 12 months, 10--12-1/2" Entries: 6 | places=3/6 | Pups, 6 up to 12 months, 12-1/2--15" Entries: 14
- `C1` / `midclass_page_dropout`: Dogs; 1 yr & over, 12-12--15" Entries: 7 | after page got 2th expected 4 | 2nd: Windermere Rev, owned by Fred Winbarg
