# B6b cleanup + ingest audit — 1996

Catalog: `_OCR_CLEANUP_CATALOG_HANDOFF.md`
Volumes: 30  cleaned=26  PASS=10  WARN=0  FAIL=20
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
| FAIL | True | 9 | 0 | C1/C6×7,C7×2 | `1996 Vol 1 pg 111-160 back reversed_ocr_hqmax.txt` |
| FAIL | True | 4 | 0 | C1/C6×3,C7×1 | `1996 Vol 1 pg 111-160 back_ocr_hqmax.txt` |
| FAIL | True | 11 | 0 | C7×5,H8×3,C1/C6×2,C1×1 | `1996 Vol 1 pg 111-160 front_ocr_hqmax.txt` |
| PASS | False | 0 | 0 | — | `1996 Vol 1 pg 161-178 back reversed_ocr_hqmax.txt` |
| PASS | False | 0 | 0 | — | `1996 Vol 1 pg 161-178 back_ocr_hqmax.txt` |
| PASS | False | 0 | 0 | — | `1996 Vol 1 pg 161-178 front_ocr_hqmax.txt` |
| FAIL | True | 20 | 0 | C1/C6×18,C7×2 | `1996 Vol 1 pg 21-60 back reversed_ocr_hqmax.txt` |
| PASS | True | 0 | 0 | — | `1996 Vol 1 pg 21-60 back_ocr_hqmax.txt` |
| FAIL | True | 6 | 0 | C1/C6×4,C7×2 | `1996 Vol 1 pg 21-60 front_ocr_hqmax.txt` |
| PASS | True | 0 | 0 | — | `1996 Vol 1 pg 61-110 back reversed_ocr_hqmax.txt` |
| PASS | True | 0 | 0 | — | `1996 Vol 1 pg 61-110 back_ocr_hqmax.txt` |
| FAIL | True | 8 | 0 | C7×7,C1/C6×1 | `1996 Vol 1 pg 61-110 front_ocr_hqmax.txt` |
| FAIL | True | 13 | 0 | C1/C6×7,C7×6 | `1996 Vol II pg 163-220 back reversed_ocr_hqmax.txt` |
| FAIL | True | 8 | 0 | C1/C6×4,C7×3,C1×1 | `1996 Vol II pg 163-220 back_ocr_hqmax.txt` |
| FAIL | True | 7 | 0 | C7×4,H8×1,C1×1,C1/C6×1 | `1996 Vol II pg 163-220 front_ocr_hqmax.txt` |
| FAIL | True | 6 | 0 | C7×5,H8×1 | `1996 Vol II pg 23-92 back reversed_ocr_hqmax.txt` |
| FAIL | True | 1 | 0 | C1/C6×1 | `1996 Vol II pg 23-92 back_ocr_hqmax.txt` |
| FAIL | True | 5 | 0 | C7×3,C1/C6×2 | `1996 Vol II pg 23-92 front (missing 1 pgs)_ocr_hqmax.txt` |
| FAIL | True | 7 | 0 | C7×5,C1/C6×2 | `1996 Vol II pg 23-92 front (missing 2 pgs)_ocr_hqmax.txt` |
| FAIL | True | 5 | 0 | C1/C6×3,C7×2 | `1996 Vol II pg 23-92 front_ocr_hqmax.txt` |
| FAIL | True | 19 | 0 | C1/C6×10,C7×8,H8×1 | `1996 Vol II pg 93-162 back reversed_ocr_hqmax.txt` |
| FAIL | True | 5 | 0 | C1/C6×4,H8×1 | `1996 Vol II pg 93-162 back_ocr_hqmax.txt` |
| FAIL | True | 6 | 0 | C1/C6×3,C7×2,C1×1 | `1996 Vol II pg 93-162 front_ocr_hqmax.txt` |
| PASS | True | 0 | 0 | — | `Document_2026-11-04_144208_ocr_hqmax.txt` |
| FAIL | True | 2 | 0 | C7×2 | `Document_2026-11-04_144530_ocr_hqmax.txt` |
| PASS | True | 0 | 0 | — | `Document_2026-11-04_145355_ocr_hqmax.txt` |
| PASS | True | 0 | 0 | — | `Document_2026-11-04_145925_ocr_hqmax.txt` |
| PASS | True | 0 | 0 | — | `Document_2026-11-04_151058_ocr_hqmax.txt` |
| FAIL | False | 3 | 0 | C7×2,C1/C6×1 | `Document_2026-11-04_152834_ocr_hqmax.txt` |
| FAIL | True | 5 | 0 | C1/C6×2,C7×2,H8×1 | `Document_2026-11-04_153208_ocr_hqmax.txt` |

## Sample residual hits (after cleanup)

### `1996 Vol 1 pg 111-160 back reversed_ocr_hqmax.txt` (FAIL)
- `C1/C6` / `incomplete_entries`: RIER AND RESERVE – Entries: 15 | places=0/6 | tch Solomon, owned by Terry Wellman – Entries: 3
- `C1/C6` / `incomplete_entries`: Dog Pups, 6 up to12 months, 10-12 1/2" – Entries: 4 | places=0/4 | ADULT RACING CHAMPION & RESERVE
- `C1/C6` / `incomplete_entries`: 6 months                                                                         | places=0/6 | 6 months                                                    
- `C1/C6` / `incomplete_entries`: ths Puppies – Entries: 10 | places=0/6 | Dog                                                         
- `C1/C6` / `incomplete_entries`: 6 months                                      Entries: 4 | places=0/4 | o 6 months                                                  
- `C1/C6` / `incomplete_entries`: rrier Dog, 12 1/2-15" Entries: 3 | places=0/3 | rrier Bitch, 10-12 1/2" Entries: 4
- `C1/C6` / `incomplete_entries`: rrier Bitch, 10-12 1/2" Entries: 4 | places=0/4 | rrier Bitch, 12 1/2-15" Entries: 1
- `C7` / `best_reserve_missing_header`: Best: Disqualified
- `C7` / `best_reserve_missing_header`: Best: Harfield Jill of Or

### `1996 Vol 1 pg 111-160 back_ocr_hqmax.txt` (FAIL)
- `C1/C6` / `incomplete_entries`: Junior Handler – Entries: 14 | places=0/6 | RACING DIVISION
- `C1/C6` / `incomplete_entries`: MPION AND RESERVE – Entries: 9 | places=0/6 | Entries: 2
- `C1/C6` / `incomplete_entries`: Dog Pups, 6 up to12 months, 10-12 1/2" Entries: 4 | places=0/4 | ADULT RACING CHAMPION & RESERVE
- `C7` / `best_reserve_missing_header`: Best: Vagabond Vsodoo of Little Eden, owned by Michelle Ward

### `1996 Vol 1 pg 111-160 front_ocr_hqmax.txt` (FAIL)
- `H8` / `champ_abbrev`: BEST BITCH & RESER
- `H8` / `champ_abbrev`: BEST BITCH & RESER!
- `C1` / `class_header_gap`: 1st: White Gate Johnn
- `C1/C6` / `incomplete_entries`: ION & RESERVE – Entries: 13 | places=0/6 | Dog Pups, 6 up to 12 months, 12 1/2-15" Entries: 7
- `C1/C6` / `incomplete_entries`: ON & RESERVE – Entries: 19 | places=0/6 | OBEDIENCE DIVISION
- `C7` / `best_reserve_missing_header`: Best: White Gate Bom!
- `C7` / `best_reserve_missing_header`: Best: Quarrystone Pit:
- `C7` / `best_reserve_missing_header`: Best: Ash Creek Ghillie
- `C7` / `best_reserve_missing_header`: Best: Windermere Sizz

### `1996 Vol 1 pg 21-60 back reversed_ocr_hqmax.txt` (FAIL)
- `C1/C6` / `incomplete_entries`: 6 months                                                    Entries: 15 | places=0/6 | 5 PUPPY CHAMPION & RESERVE – Entries: 3
- `C1/C6` / `incomplete_entries`: 9 months,r/br                                                  Entries: 9 | places=0/6 | 12 months, smooth                                          E
- `C1/C6` / `incomplete_entries`: 12 months, smooth                                          Entries: 3 | places=0/3 | 12 months, ribnr                                            
- `C1/C6` / `incomplete_entries`: 12 months, ribnr                                               Entries: 9 | places=0/6 | ATION CHAMPION AND RESERVE
- `C1/C6` / `incomplete_entries`: smooth                                                  Entries: 10 | places=0/6 | 12", smooth                                                 
- `C1/C6` / `incomplete_entries`: 'months, 10" to 12 2            :              Entries: 7 | places=0/6 | 'months, 12 1/2" to 15" Entries: 3
- `C1/C6` / `incomplete_entries`: 'months, 12 1/2" to 15" Entries: 3 | places=0/3 | Dog Pups, 4 up to 6 m
- `C1/C6` / `incomplete_entries`: 9 months, rough/broken                                    Entries: 6 | places=0/6 | 12months, smooth                                          En
- `C1/C6` / `incomplete_entries`: 12months, smooth                                          Entries: 4 | places=0/4 | 12months, rough/broken                                   Ent
- `C1/C6` / `incomplete_entries`: 5", rough/broken                                             Entries: 16 | places=0/6 | 1/2", smooth                                                
- `C1/C6` / `incomplete_entries`: 1/2", smooth                                                      Entries: 6 | places=0/6 | Novice Adults                                               
- `C1/C6` / `incomplete_entries`: 5 months, smooth                                        Entries: 10 | places=0/6 | 6 months, r/br                                              

### `1996 Vol 1 pg 21-60 front_ocr_hqmax.txt` (FAIL)
- `C1/C6` / `incomplete_entries`: Dog Pups, 6 up to 12 months, 10-12 1/2" Entries: 4 | places=0/4 | ADULT RACING CHAMPION & RESERVE
- `C1/C6` / `incomplete_entries`: Agility, Off Lead                                                                | places=0/6 | Dog Pups, 6 up to 12 months
- `C1/C6` / `incomplete_entries`: 12 1/2", smooth – Entries: 11 | places=0/6 | JRTCA Working Terrier
- `C1/C6` / `incomplete_entries`: ON & RESERVE – Entries: 3 | places=0/3 | Entries: 20
- `C7` / `best_reserve_missing_header`: Best: Beano of Ravens:
- `C7` / `best_reserve_missing_header`: Best: Foxfield Sprig, owned by Rusty & Debbie Graydon

### `1996 Vol 1 pg 61-110 front_ocr_hqmax.txt` (FAIL)
- `C1/C6` / `incomplete_entries`: Sub Novice                                                                       | places=0/6 | AGILITY DIVISION
- `C7` / `best_reserve_missing_header`: Reserve: Shenanigans Will, owned by Mary Abbc
- `C7` / `best_reserve_missing_header`: Best: Windermere Witewitch of Sow's Ear
- `C7` / `best_reserve_missing_header`: Reserve: Bowery Bart, owned by Gene Foster
- `C7` / `best_reserve_missing_header`: Reserve: Foxport Laser of Little Eden, owned by Michelle Ward
- `C7` / `best_reserve_missing_header`: Reserve: Com Row Tyler, owned by Pam Simmons
- `C7` / `best_reserve_missing_header`: Reserve: Rustler Billy the Kid, owned by Brenda Swanson
- `C7` / `best_reserve_missing_header`: Reserve: Button Top Bill, owned by Flo Clark

### `1996 Vol II pg 163-220 back reversed_ocr_hqmax.txt` (FAIL)
- `C1/C6` / `incomplete_entries`: Puppy Champiorship                                              Entries: 7 | places=0/6 | Champion: Hunter's Run Abigail, owned by Billie & Jackie Kel
- `C1/C6` / `incomplete_entries`: Dog                                                            Entries: 3 | places=0/3 | Bitch                                                      E
- `C1/C6` / `incomplete_entries`: Bitch                                                      Entries: 7 | places=0/6 | Reserve: Badget, owned by Sandra Ferber & Judy Galterio
- `C1/C6` / `incomplete_entries`: Puppy Champicmship                                                               | places=0/6 | Champion: Smyky Mountain Scout, owned by Debby Calloway
- `C1/C6` / `incomplete_entries`: Pre-Novice Puppies                                                               | places=0/6 | Reserve: High& Low Hellion, owned by Melissa C. Lowe
- `C1/C6` / `incomplete_entries`: Bitches, 1 yr & over 12 1/2-15" Entries: 8 | places=0/6 | Judges: Conformation: Liz Littman; Go-to-Ground: Lynn May Me
- `C1/C6` / `incomplete_entries`: JRTCA WORKINS TERRIER CONFORMATION CHAI – Entries: 6 | places=0/6 | Best: Beano of Favenswood, owned by Ben & Jane
- `C7` / `best_reserve_missing_header`: Reserve: Badget, owned by Sandra Ferber & Judy Galterio
- `C7` / `best_reserve_missing_header`: Best: Maven's Tailor of Briarpatch, owned by Jack & Terri Batzer
- `C7` / `best_reserve_missing_header`: Reserve: High& Low Hellion, owned by Melissa C. Lowe
- `C7` / `best_reserve_missing_header`: Best: Beano of Favenswood, owned by Ben & Jane
- `C7` / `best_reserve_missing_header`: Best: Disqualified

### `1996 Vol II pg 163-220 back_ocr_hqmax.txt` (FAIL)
- `C1/C6` / `incomplete_entries`: Bitches, 1 yr & over 12 1/2-15" – Entries: 8 | places=0/6 | ADULT RACING CHAMPION & RESERVE
- `C1/C6` / `incomplete_entries`: Puppy Champicship                                                                | places=0/6 | Champion: Smuky Mountain Scout, owned by Debby Calloway
- `C1/C6` / `incomplete_entries`: HAMPION & RESERVE – Entries: 15 | places=0/6 | Entries: 5
- `C1/C6` / `incomplete_entries`: Puppy Champiorship                                                   Entries: 6 | places=0/6 | Champion: Dogwood Noisey, owned by L.B. Combs
- `C1` / `midclass_page_dropout`: Dogs, 1 yr & over, 10-12 1/2", r/br                                              | after page got 6th expected 1 | 6th: Ashley Zenos
- `C7` / `best_reserve_missing_header`: Reserve: High& Low Hellion, owned by Melissa C. Lowe
- `C7` / `best_reserve_missing_header`: Best: Maven's Tailor of Briarpatch, owned by Jack & Terri Batzer
- `C7` / `best_reserve_missing_header`: Best: Briarpatch Soot, owned by Terri Batzer

### `1996 Vol II pg 163-220 front_ocr_hqmax.txt` (FAIL)
- `H8` / `champ_abbrev`: PUPPY CONFORMATION CHAMPION AND RESER
- `C1` / `class_header_gap`: 4th: Courtwood Chili, owned by Janet Nugen
- `C1/C6` / `incomplete_entries`: AMPION & RESERVE – Entries: 37 | places=0/6 | Bitch Pups, 6 up to 12 months, over 12 1/2
- `C7` / `best_reserve_missing_header`: Best: Wesworld Chaps, owned by Christy Parkinson
- `C7` / `best_reserve_missing_header`: Best: Ash Creek Banshee, owned by Martin & Teresa Gottlieb
- `C7` / `best_reserve_missing_header`: Best: Briarpatch Soot, owned by Jack & Terri
- `C7` / `best_reserve_missing_header`: Best: Baybriar Rudie, owned by Jeannette Hutchison

### `1996 Vol II pg 23-92 back reversed_ocr_hqmax.txt` (FAIL)
- `H8` / `champ_abbrev`: BEST 4 - 6 MCNTHS PUPPY CHAMPION & RESER
- `C7` / `best_reserve_missing_header`: Best: Vagabond Voor
- `C7` / `best_reserve_missing_header`: Best: Quarrysbne P
- `C7` / `best_reserve_missing_header`: Best: Vagabord Voo
- `C7` / `best_reserve_missing_header`: Reserve: Conquest Minute, owned by Gaye Redpath
- `C7` / `best_reserve_missing_header`: Best: Maefield Oliver, owned by Elizabeth Gleaso

### `1996 Vol II pg 23-92 back_ocr_hqmax.txt` (FAIL)
- `C1/C6` / `incomplete_entries`: Open Puppies                                                  Entries: 3 | places=0/3 | Open Adults                                                 

### `1996 Vol II pg 23-92 front (missing 1 pgs)_ocr_hqmax.txt` (FAIL)
- `C1/C6` / `incomplete_entries`: Dog Pups, 6 up to 12 months, up to 12 1/2" Entries: 4 | places=0/4 | ADULT RACING CHAMPION & RESERVE
- `C1/C6` / `incomplete_entries`: Bitches, 1 yr & over, 12 1/2-15" Entries: 16 | places=0/6 | ADULT RACING CHAMPION & RESERVE
- `C7` / `best_reserve_missing_header`: Best: Sows Ear Liberty, owned by Paul Hartman & Karen McCarthy
- `C7` / `best_reserve_missing_header`: Best: Vagabond Voodoo
- `C7` / `best_reserve_missing_header`: Best: Meadowlake Haley:

### `1996 Vol II pg 23-92 front (missing 2 pgs)_ocr_hqmax.txt` (FAIL)
- `C1/C6` / `incomplete_entries`: Dog Pups, 6 up to 12 months, up to 12 1/2" Entries: 4 | places=0/4 | ADULT RACING CHAMPION & RESERVE
- `C1/C6` / `incomplete_entries`: Bitches, 1 yr & over, 12 1/2-15" Entries: 16 | places=0/6 | ADULT RACING CHAMPION & RESERVE
- `C7` / `best_reserve_missing_header`: Best: Sows Ear Liberty, owned by Paul Hartman & Karen McCarthy
- `C7` / `best_reserve_missing_header`: Best: The Larches Liam McGee
- `C7` / `best_reserve_missing_header`: Best: The Hollow Blanca, owned by The Holl
- `C7` / `best_reserve_missing_header`: 12 1/2-15" Champion:
- `C7` / `best_reserve_missing_header`: Reserve: RA Piker, owned by George & Linda Louden

### `1996 Vol II pg 23-92 front_ocr_hqmax.txt` (FAIL)
- `C1/C6` / `incomplete_entries`: Dog Pups, 6 up to 12 months, up to 12 1/2" Entries: 4 | places=0/4 | ADULT RACING CHAMPION & RESERVE
- `C1/C6` / `incomplete_entries`: 12 1/2-15" Reserve: Rynwards Teasel, ow – Entries: 10 | places=0/6 | Entries: 3, owned by Sue Hardin
- `C1/C6` / `incomplete_entries`: Bitches, 1 yr & over, 12 1/2-15" Entries: 16 | places=0/6 | ADULT RACING CHAMPION & RESERVE
- `C7` / `best_reserve_missing_header`: Best: Vagabond Voodoo of Little Eden, owned by Michelle Ward
- `C7` / `best_reserve_missing_header`: Reserve: Sows Laurel Ear Liberty, Run Orry, owned by by Paul Kate Hartman Bomberger & Karen McCarthy

### `1996 Vol II pg 93-162 back reversed_ocr_hqmax.txt` (FAIL)
- `H8` / `champ_abbrev`: 10-12 1/2" Reser: Miller Time, owned by Laura O'Leary
- `C1/C6` / `incomplete_entries`: Dogs, 1 yr & ovr, 10-12 1/2", tlbr – Entries: 5 | places=0/5 | Dogs, yr & over, 12 1/2-15", smooth
- `C1/C6` / `incomplete_entries`: 12 1/2-15", smooth                                Entries: 8 | places=0/6 | BEST JRTCA WORKING TERRIER DOG AND RESERVE
- `C1/C6` / `incomplete_entries`: Puppy Champiynship                                                   Entries: 3 | places=0/3 | Champion: Jatholes Wild Oats Odie, owned by David Krakow
- `C1/C6` / `incomplete_entries`: 'errier Dog                                                     Entries: 8 | places=0/6 | errier Bitch, 10-12 1/2" Entries: 5
- `C1/C6` / `incomplete_entries`: errier Bitch, 10-12 1/2" Entries: 5 | places=0/5 | errier Bitch, 12 1/2-15" Entries: 3
- `C1/C6` / `incomplete_entries`: Sub Novice Entries: 9 | places=0/6 | ADULT RACING CHAMPION & RESERVE
- `C1/C6` / `incomplete_entries`: errier Bitch, 12 1/2-15", r/br                                Entries: 3 | places=0/3 | TERRIER CONFORMATION CHAMPION & RESERVE
- `C1/C6` / `incomplete_entries`: Puppy Champiotship                                                Entries: 7 | places=0/6 | Champion: Foxport Ivanhoe, owned by Lois Clough
- `C1/C6` / `incomplete_entries`: Dogs, 1 yr & over 12 1/2-15" Entries: 12 | places=0/6 | ADULT RACING CHAMPION & RESERVE
- `C1/C6` / `incomplete_entries`: PUPPIES – Entries: 6 | places=0/6 | 10-12 1/2" Champion: Farmcliff Spencer, owned by Bob Frankli
- `C7` / `best_reserve_missing_header`: Best: Farmcliff Fied of

### `1996 Vol II pg 93-162 back_ocr_hqmax.txt` (FAIL)
- `H8` / `champ_abbrev`: 10-12 1/2" Reser: Miller Time, owned by Laura O'Leary
- `C1/C6` / `incomplete_entries`: PUPPIES – Entries: 6 | places=0/6 | 10-12 1/2" Champidn: Farmcliff Spencer, owned by Bob Frankli
- `C1/C6` / `incomplete_entries`: Puppy Champioi ship                                                   Entries: 7 | places=0/6 | Champion: Foxprt lvanhoe, owned by Lois Clough
- `C1/C6` / `incomplete_entries`: Dogs, 1 yr & ove: 12 1/2-15" Entries: 12 | places=0/6 | ADULT RACING CHAMPION & RESERVE
- `C1/C6` / `incomplete_entries`: IAMPION & RESERVE – Entries: 9 | places=0/6 | Entries: 8

### `1996 Vol II pg 93-162 front_ocr_hqmax.txt` (FAIL)
- `C1` / `class_header_gap`: 1st: Long Hope Mickey, owned by Bob Franklin
- `C1/C6` / `incomplete_entries`: ADULTS – Entries: 5 | places=0/5 | 10-12 1/2" Champion:  Sparks Will Fly, owned by Patricia Cas
- `C1/C6` / `incomplete_entries`: Bitch – Entries: 23 | places=0/6 | Entries: 28
- `C1/C6` / `incomplete_entries`: Child Handler                                                               Entr | places=0/3 | Champion: Foxport Keeper, owned by Michelle Ward
- `C7` / `best_reserve_missing_header`: Reserve: Smokey Mountain Scout, owned by Debby Galloway
- `C7` / `best_reserve_missing_header`: Over 12 1/2" Champion:

### `Document_2026-11-04_144530_ocr_hqmax.txt` (FAIL)
- `C7` / `best_reserve_missing_header`: Reserve: Foxport Laser of Little Eden, owned by Michelle Ward
- `C7` / `best_reserve_missing_header`: Reserve: Corn Row Tyler, owned by Pam Simmons

### `Document_2026-11-04_152834_ocr_hqmax.txt` (FAIL)
- `C1/C6` / `incomplete_entries`: Dogs, 1 yr & over 12 1/2-15" Entries: 15 | places=0/6 | ADULT RACING CHAMPION & RESERVE
- `C7` / `best_reserve_missing_header`: Best: Crosswinds Trask, owned by Will Hahn
- `C7` / `best_reserve_missing_header`: Best: Loblolly Scandle, owned by Debra Ellis

### `Document_2026-11-04_153208_ocr_hqmax.txt` (FAIL)
- `H8` / `champ_abbrev`: Working Terier Cham
- `C1/C6` / `incomplete_entries`: Best Family                                                                      | places=0/4 | Best: Ash Creek Banshee, owned by Martin & Teresa Gottlieb
- `C1/C6` / `incomplete_entries`: Reserve Open Terrier-North American  Entries: 3 | places=0/3 | EOF
- `C7` / `best_reserve_missing_header`: Best: Ash Creek Banshee, owned by Martin & Teresa Gottlieb
- `C7` / `best_reserve_missing_header`: Best: Baybriar Rudie, owned by Jeannette Hutchison
