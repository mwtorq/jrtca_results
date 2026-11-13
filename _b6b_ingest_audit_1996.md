# B6b cleanup + ingest audit — 1996

Catalog: `_OCR_CLEANUP_CATALOG_HANDOFF.md`
Volumes: 30  cleaned=0  PASS=2  WARN=0  FAIL=28
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
| FAIL | False | 39 | 0 | S1-S3×34,O6×5 | `1996 Vol 1 pg 111-160 back reversed_ocr_hqmax.txt` |
| FAIL | False | 13 | 0 | S1-S3×12,O6×1 | `1996 Vol 1 pg 111-160 back_ocr_hqmax.txt` |
| FAIL | False | 30 | 0 | S1-S3×30 | `1996 Vol 1 pg 111-160 front_ocr_hqmax.txt` |
| FAIL | False | 1 | 0 | S1-S3×1 | `1996 Vol 1 pg 161-178 back reversed_ocr_hqmax.txt` |
| PASS | False | 0 | 0 | — | `1996 Vol 1 pg 161-178 back_ocr_hqmax.txt` |
| FAIL | False | 1 | 0 | O6×1 | `1996 Vol 1 pg 161-178 front_ocr_hqmax.txt` |
| FAIL | False | 25 | 0 | S1-S3×25 | `1996 Vol 1 pg 21-60 back reversed_ocr_hqmax.txt` |
| FAIL | False | 2 | 0 | S1-S3×2 | `1996 Vol 1 pg 21-60 back_ocr_hqmax.txt` |
| FAIL | False | 22 | 0 | S1-S3×21,O6×1 | `1996 Vol 1 pg 21-60 front_ocr_hqmax.txt` |
| FAIL | False | 16 | 0 | S1-S3×11,O6×5 | `1996 Vol 1 pg 61-110 back reversed_ocr_hqmax.txt` |
| FAIL | False | 4 | 0 | S1-S3×4 | `1996 Vol 1 pg 61-110 back_ocr_hqmax.txt` |
| FAIL | False | 22 | 0 | S1-S3×20,O6×2 | `1996 Vol 1 pg 61-110 front_ocr_hqmax.txt` |
| FAIL | False | 30 | 0 | S1-S3×30 | `1996 Vol II pg 163-220 back reversed_ocr_hqmax.txt` |
| FAIL | False | 10 | 0 | S1-S3×9,O6×1 | `1996 Vol II pg 163-220 back_ocr_hqmax.txt` |
| FAIL | False | 16 | 0 | S1-S3×16 | `1996 Vol II pg 163-220 front_ocr_hqmax.txt` |
| FAIL | False | 26 | 0 | S1-S3×24,O6×2 | `1996 Vol II pg 23-92 back reversed_ocr_hqmax.txt` |
| FAIL | False | 3 | 0 | S1-S3×3 | `1996 Vol II pg 23-92 back_ocr_hqmax.txt` |
| FAIL | False | 7 | 0 | S1-S3×6,O6×1 | `1996 Vol II pg 23-92 front (missing 1 pgs)_ocr_hqmax.txt` |
| FAIL | False | 22 | 0 | S1-S3×22 | `1996 Vol II pg 23-92 front (missing 2 pgs)_ocr_hqmax.txt` |
| FAIL | False | 17 | 0 | S1-S3×16,O6×1 | `1996 Vol II pg 23-92 front_ocr_hqmax.txt` |
| FAIL | False | 29 | 0 | S1-S3×28,O6×1 | `1996 Vol II pg 93-162 back reversed_ocr_hqmax.txt` |
| FAIL | False | 3 | 0 | S1-S3×2,O6×1 | `1996 Vol II pg 93-162 back_ocr_hqmax.txt` |
| FAIL | False | 12 | 0 | S1-S3×11,O6×1 | `1996 Vol II pg 93-162 front_ocr_hqmax.txt` |
| FAIL | False | 4 | 0 | S1-S3×3,O6×1 | `Document_2026-11-04_144208_ocr_hqmax.txt` |
| PASS | False | 0 | 0 | — | `Document_2026-11-04_144530_ocr_hqmax.txt` |
| FAIL | False | 4 | 0 | S1-S3×2,O6×2 | `Document_2026-11-04_145355_ocr_hqmax.txt` |
| FAIL | False | 3 | 0 | S1-S3×2,O6×1 | `Document_2026-11-04_145925_ocr_hqmax.txt` |
| FAIL | False | 2 | 0 | O6×2 | `Document_2026-11-04_151058_ocr_hqmax.txt` |
| FAIL | False | 4 | 0 | S1-S3×4 | `Document_2026-11-04_152834_ocr_hqmax.txt` |
| FAIL | False | 10 | 0 | S1-S3×10 | `Document_2026-11-04_153208_ocr_hqmax.txt` |

## Sample residual hits (after cleanup)

### `1996 Vol 1 pg 111-160 back reversed_ocr_hqmax.txt` (FAIL)
- `S1-S3` / `two_column_smash`: iin, owned by Karen Vernon
- `S1-S3` / `two_column_smash`: sc, owned by Chuck & Diana Hufnagel
- `S1-S3` / `two_column_smash`: apshot, owned by Clint Clayton
- `S1-S3` / `two_column_smash`: bmon, owned by Terry Wellman
- `S1-S3` / `two_column_smash`: ster, owned by Will Hahn
- `S1-S3` / `two_column_smash`: esoro, owned by Foxhall Terriers
- `S1-S3` / `two_column_smash`: nt, owned by Doug Tack & Sandra Ferber
- `S1-S3` / `two_column_smash`: an, owned by Elizabeth Gleason
- `S1-S3` / `two_column_smash`: nap, owned by Michelle Ward
- `S1-S3` / `two_column_smash`: phyr, owned by Tinker Tavern Terriers
- `S1-S3` / `two_column_smash`: avenswood, owned by Janet Sutcliffe
- `S1-S3` / `two_column_smash`: 6th: a, owned by Lisa Drinkwater

### `1996 Vol 1 pg 111-160 back_ocr_hqmax.txt` (FAIL)
- `S1-S3` / `two_column_smash`: leadowlake, owned by Karen Reavis
- `S1-S3` / `two_column_smash`: alth, owned by Stealth Terriers
- `S1-S3` / `two_column_smash`: dtree, owned by Bev Dalton
- `S1-S3` / `two_column_smash`: ny, owned by Joe & Becky Froias
- `S1-S3` / `two_column_smash`: owlake, owned by Karen Reavis
- `S1-S3` / `two_column_smash`: 1st: tstt Fox Run Sonc, owned by Sandra Ferber
- `S1-S3` / `two_column_smash`: Best: disqualified
- `S1-S3` / `two_column_smash`: 1st: disqualified
- `S1-S3` / `two_column_smash`: Champion: disqu:lified
- `S1-S3` / `two_column_smash`: 2nd: disqualified
- `O6` / `owner_tail_trunc`: 12 1/2-15" Reseve: Courtland Moo Cow, owned by

### `1996 Vol 1 pg 111-160 front_ocr_hqmax.txt` (FAIL)
- `S1-S3` / `two_column_smash`: 1st: lolly, owned by Mary Webb
- `S1-S3` / `two_column_smash`: jgie, owned by Karen Cooper
- `S1-S3` / `two_column_smash`: ipper, owned by Joe & Priscilla Testa
- `S1-S3` / `two_column_smash`: phy, owned by Joe & Priscilla Testa
- `S1-S3` / `two_column_smash`: mba, owned by Joe & Priscilla Testa
- `S1-S3` / `two_column_smash`: ck, owned by Mike Turley
- `S1-S3` / `two_column_smash`: nny, owned by Debbie LaMantia
- `S1-S3` / `two_column_smash`: sha, owned by Kathy Hunter
- `S1-S3` / `two_column_smash`: ohy, owned by Joe & Priscilla Testa
- `S1-S3` / `two_column_smash`: mba, owned by Joe & Priscilla Testa – Entries: 8
- `S1-S3` / `two_column_smash`: ap, owned by Michelle Ward
- `S1-S3` / `two_column_smash`: nber, owned by Nancy Breakstone

### `1996 Vol 1 pg 161-178 back reversed_ocr_hqmax.txt` (FAIL)
- `S1-S3` / `two_column_smash`: 1st: fst: Romney Kez, owned by Kim Hunter & Jim Hughes

### `1996 Vol 1 pg 161-178 front_ocr_hqmax.txt` (FAIL)
- `O6` / `owner_tail_trunc`: 5th: Russell-M-Up Cool Hand Luke, owned by

### `1996 Vol 1 pg 21-60 back reversed_ocr_hqmax.txt` (FAIL)
- `S1-S3` / `two_column_smash`: wford, owned by Michael Healy
- `S1-S3` / `two_column_smash`: tr, owned by Lloyd & Shirley Cox
- `S1-S3` / `two_column_smash`: sy, owned by Richard and Janette Finnerty
- `S1-S3` / `two_column_smash`: ina, owned by Aaron Davidson
- `S1-S3` / `two_column_smash`: iilie, owned by Roxanne Glass
- `S1-S3` / `two_column_smash`: itmeg, owned by Emily Hemple
- `S1-S3` / `two_column_smash`: lel, owned by Ellen S. Lesch
- `S1-S3` / `two_column_smash`: anna, owned by Didi Gough
- `S1-S3` / `two_column_smash`: fty, owned by Darlene McInnes
- `S1-S3` / `two_column_smash`: jah, owned by Susan Haldiman
- `S1-S3` / `two_column_smash`: zy, owned by Lynn May-Measles
- `S1-S3` / `two_column_smash`: tic, owned by Molly Martin

### `1996 Vol 1 pg 21-60 back_ocr_hqmax.txt` (FAIL)
- `S1-S3` / `two_column_smash`: 5th: lam Prancer, owned by Diana Decant
- `S1-S3` / `two_column_smash`: an, owned by Kathleen Hardy

### `1996 Vol 1 pg 21-60 front_ocr_hqmax.txt` (FAIL)
- `S1-S3` / `two_column_smash`: 3rd: AJ, owned by Westside
- `S1-S3` / `two_column_smash`: te, owned by Mark & Jan Bjorkiand – Entries: 12
- `S1-S3` / `two_column_smash`: 2nd: lam Prancer, owned by Diana Decant
- `S1-S3` / `two_column_smash`: eth, owned by L. McKinney & L. Grimsl
- `S1-S3` / `two_column_smash`: masina, owned by Patsy McConnell
- `S1-S3` / `two_column_smash`: sta, owned by Wanda Dyer
- `S1-S3` / `two_column_smash`: ne, owned by Ellen Kennedy & Terry
- `S1-S3` / `two_column_smash`: ss, owned by Ray Derrick
- `S1-S3` / `two_column_smash`: ner, owned by Sheila Higginbotham
- `S1-S3` / `two_column_smash`: yomerang, owned by Janet Sutcliffe
- `S1-S3` / `two_column_smash`: ke, owned by Barbara Tyler
- `S1-S3` / `two_column_smash`: 3rd: of Meadowlake, owned by Karen Reavis

### `1996 Vol 1 pg 61-110 back reversed_ocr_hqmax.txt` (FAIL)
- `S1-S3` / `two_column_smash`: 2nd: ievousMaybell, owned by Rebecca Quick
- `S1-S3` / `two_column_smash`: 3rd: n Little Bamber, owned by Martha Leroy
- `S1-S3` / `two_column_smash`: ine, owned by Ellen Kennedy & Terry Wellman
- `S1-S3` / `two_column_smash`: nd, owned by Sharon Pritchett
- `S1-S3` / `two_column_smash`: wv, owned by Roberts Lawrence
- `S1-S3` / `two_column_smash`: er, owned by Ken Meyer
- `S1-S3` / `two_column_smash`: tial, owned by Ken Meyer
- `S1-S3` / `two_column_smash`: nipper, owned by Doug Stephenson
- `S1-S3` / `two_column_smash`: npest, owned by Barbara Tyler
- `S1-S3` / `two_column_smash`: avez, owned by Jean & Ray Derrick
- `S1-S3` / `two_column_smash`: hdiac, owned by Mike & Betty Bilinski
- `O6` / `owner_tail_trunc`: 12 1/2-15" Champbn: Button Top Belle Star, owned by

### `1996 Vol 1 pg 61-110 back_ocr_hqmax.txt` (FAIL)
- `S1-S3` / `two_column_smash`: 3rd: not provided--ontact trial chairman
- `S1-S3` / `two_column_smash`: 4th: not provided—ontact trial chairman
- `S1-S3` / `two_column_smash`: 5th: not provided--ontact trial chairman
- `S1-S3` / `two_column_smash`: 6th: not provided—ontact trial chairman

### `1996 Vol 1 pg 61-110 front_ocr_hqmax.txt` (FAIL)
- `S1-S3` / `two_column_smash`: 6th: mite, owned by Carole McAurthus
- `S1-S3` / `two_column_smash`: 5th: adie, owned by Chri Advan
- `S1-S3` / `two_column_smash`: 3rd: d, owned by Steve Spruill
- `S1-S3` / `two_column_smash`: 5th: d Riddle, owned by Julie Conner
- `S1-S3` / `two_column_smash`: iesian, owned by Dermot Gilligan
- `S1-S3` / `two_column_smash`: heckers, owned by Liz & Pete Littman
- `S1-S3` / `two_column_smash`: hoenix, owned by Janet Rosselle
- `S1-S3` / `two_column_smash`: rocket, owned by Margaret Strohlein
- `S1-S3` / `two_column_smash`: ly, owned by Patricia Caschera
- `S1-S3` / `two_column_smash`: ggie, owned by Kathy & Mitchell Cohen
- `S1-S3` / `two_column_smash`: ly, owned by Betsy Jordan
- `S1-S3` / `two_column_smash`: der, owned by Liz & Pete Littman

### `1996 Vol II pg 163-220 back reversed_ocr_hqmax.txt` (FAIL)
- `S1-S3` / `two_column_smash`: 3rd: y Polo, owned by Foxhall Terriers
- `S1-S3` / `two_column_smash`: 4th: lee Won, owned by Nellie Niewola
- `S1-S3` / `two_column_smash`: 5th: ss, owned by Debbie LaMantia
- `S1-S3` / `two_column_smash`: ke, owned by Joe Landini
- `S1-S3` / `two_column_smash`: sto, owned by Rick & Mary Thornton
- `S1-S3` / `two_column_smash`: ke, owned by Megan Johnson
- `S1-S3` / `two_column_smash`: ubbles, owned by Judy Galterio
- `S1-S3` / `two_column_smash`: kle, owned by Debbie LaMantia
- `S1-S3` / `two_column_smash`: met, owned by Allison Linstrum & Rick Thornton
- `S1-S3` / `two_column_smash`: rook, owned by Doug & Noreen Loranger
- `S1-S3` / `two_column_smash`: ger, owned by Sandra Ferber
- `S1-S3` / `two_column_smash`: ncer, owned by Bob Franklin

### `1996 Vol II pg 163-220 back_ocr_hqmax.txt` (FAIL)
- `S1-S3` / `two_column_smash`: 6th: lka, owned by Candy Henderson
- `S1-S3` / `two_column_smash`: 2nd: wist Hughes o Loblolly, owned by Debra Ellis
- `S1-S3` / `two_column_smash`: 2nd: ncliff, owned by Bob Franklin
- `S1-S3` / `two_column_smash`: 4th: Not provided by Trial Chairperson, owned by Brenda Worley
- `S1-S3` / `two_column_smash`: 5th: Not provided by Trial Chairperson, owned by Brenda Worley
- `S1-S3` / `two_column_smash`: 3rd: Not provided by Trial Chairperson, owned by Brenda Worley
- `O6` / `owner_tail_trunc`: 12 1/2-15" Reserve: Courtland Moo Cow, owned by
- `S1-S3` / `two_column_smash`: Paut Finkernagel | Loranger | Franklin | Laura Harakaly

### `1996 Vol II pg 163-220 front_ocr_hqmax.txt` (FAIL)
- `S1-S3` / `two_column_smash`: 1st: i et Edin! odSssy, owned by Bob Franklin
- `S1-S3` / `two_column_smash`: 2nd: ariel sugar, owned by Genie Franklin
- `S1-S3` / `two_column_smash`: 3rd: AJ, owned by Hugo Noa
- `S1-S3` / `two_column_smash`: 2nd: y Rose, owned by Dan & Cindy McClary
- `S1-S3` / `two_column_smash`: 6th: e, owned by Marlow & Joanne Jurisch
- `S1-S3` / `two_column_smash`: pinner, owned by Sara Lou Peck
- `S1-S3` / `two_column_smash`: or, owned by Kate Bomberger
- `S1-S3` / `two_column_smash`: lis, owned by Kate Bomberger
- `S1-S3` / `two_column_smash`: 3rd: not available
- `S1-S3` / `two_column_smash`: 5th: not available
- `S1-S3` / `two_column_smash`: 5th: Not provided by Trial Chairperson, owned by Brenda Worley
- `S1-S3` / `two_column_smash`: Champion: Not provided by Trial Chairperson, owned by Brenda Worley

### `1996 Vol II pg 23-92 back reversed_ocr_hqmax.txt` (FAIL)
- `S1-S3` / `two_column_smash`: 4th: nere Pistol, owned by Joel & Mary McElearney
- `S1-S3` / `two_column_smash`: 6th: s Inn Scatter, owned by Debra Ellis
- `S1-S3` / `two_column_smash`: idi, owned by Val Wasch
- `S1-S3` / `two_column_smash`: er, owned by Sandra Ferber
- `S1-S3` / `two_column_smash`: ant, owned by Doug & Sue Tack & Sandra Ferber
- `S1-S3` / `two_column_smash`: oe, owned by Roger Sherry
- `S1-S3` / `two_column_smash`: sie, owned by Bob Franklin
- `S1-S3` / `two_column_smash`: axter, owned by Frank Coletti – Entries: 0
- `S1-S3` / `two_column_smash`: 6th: s Bat, owned by Donald & Joan LaPlace
- `S1-S3` / `two_column_smash`: iberty, owned by P. Hartman & K. McCarthy
- `S1-S3` / `two_column_smash`: peedy, owned by Sarah & Terry Grainger
- `S1-S3` / `two_column_smash`: eke, owned by Joe & Evelyn Landini

### `1996 Vol II pg 23-92 back_ocr_hqmax.txt` (FAIL)
- `S1-S3` / `two_column_smash`: 1st: tstt Farmcliff Cuke, owned by K. Hunter & J. Hughes
- `S1-S3` / `two_column_smash`: 3rd: not provifed
- `S1-S3` / `two_column_smash`: 5th: not proviled

### `1996 Vol II pg 23-92 front (missing 1 pgs)_ocr_hqmax.txt` (FAIL)
- `S1-S3` / `two_column_smash`: 2nd: not provided by trial chairman, owned by Brenda Worley
- `S1-S3` / `two_column_smash`: 5th: not provided by trial chairman, owned by Brenda Worley
- `S1-S3` / `two_column_smash`: ey, owned by Bob Franklin
- `S1-S3` / `two_column_smash`: hase, owned by Dave & Sara Marcum
- `O6` / `owner_tail_trunc`: 10-12 1/2" Reserve: Lands End Nutmeg, owned by

### `1996 Vol II pg 23-92 front (missing 2 pgs)_ocr_hqmax.txt` (FAIL)
- `S1-S3` / `two_column_smash`: 2nd: not provided by trial chairman, owned by Brenda Worley
- `S1-S3` / `two_column_smash`: 5th: not provided by trial chairman, owned by Brenda Worley
- `S1-S3` / `two_column_smash`: er, owned by Bob Franlin
- `S1-S3` / `two_column_smash`: anor, owned by D. Tarchini & C. Young
- `S1-S3` / `two_column_smash`: or, owned by J. Jankowski & K. Morande
- `S1-S3` / `two_column_smash`: key, owned by Bob Franklin
- `S1-S3` / `two_column_smash`: byte, owned by K, Hunter & P. Finkerna
- `S1-S3` / `two_column_smash`: hgate, owned by Doug & Sue Tack
- `S1-S3` / `two_column_smash`: estor, owned by William & Gay O'Brien
- `S1-S3` / `two_column_smash`: ssy, owned by Bob Franklin
- `S1-S3` / `two_column_smash`: 1st: pper, owned by Sally Gay
- `S1-S3` / `two_column_smash`: er, owned by Doug & Noreen Lorange

### `1996 Vol II pg 23-92 front_ocr_hqmax.txt` (FAIL)
- `S1-S3` / `two_column_smash`: 2nd: not provided by trial chairman, owned by Brenda Worley
- `S1-S3` / `two_column_smash`: 5th: not provided by trial chairman, owned by Brenda Worley
- `S1-S3` / `two_column_smash`: 1st: fst: Sportster, owned by Judy Drake
- `S1-S3` / `two_column_smash`: 1st: cer, owned by Bob Franlin
- `S1-S3` / `two_column_smash`: 6th: i, owned by Rob & Jessica Lafreniere
- `S1-S3` / `two_column_smash`: or, owned by J. Jankowski & K. Moran:
- `S1-S3` / `two_column_smash`: key, owned by Bob Franklin
- `S1-S3` / `two_column_smash`: byte, owned by K, Hunter & P. Finkern
- `S1-S3` / `two_column_smash`: hgate, owned by Doug & Sue Tack
- `S1-S3` / `two_column_smash`: estor, owned by William & Gay O'Brien
- `S1-S3` / `two_column_smash`: ha, owned by K. Hunter & P. Finkerna
- `S1-S3` / `two_column_smash`: slyn, owned by Laura Harakaly

### `1996 Vol II pg 93-162 back reversed_ocr_hqmax.txt` (FAIL)
- `S1-S3` / `two_column_smash`: 2nd: eke, owned by Joe & Evelyn Landini
- `S1-S3` / `two_column_smash`: 3rd: ddy, owned by Laura Harakaly
- `S1-S3` / `two_column_smash`: 5th: usto, owned by Rick & Mary Thornton
- `S1-S3` / `two_column_smash`: gan, owned by Elizabeth Gleason
- `S1-S3` / `two_column_smash`: esar, owned by Laura Janney
- `S1-S3` / `two_column_smash`: ffian, owned by Missy Kulbacky
- `S1-S3` / `two_column_smash`: opper, owned by Shelly Steinmetz
- `S1-S3` / `two_column_smash`: gger, owned by Sandra Ferber
- `S1-S3` / `two_column_smash`: iper, owned by Theresa & Marty Gottlieb
- `S1-S3` / `two_column_smash`: eedy, owned by Terry Grainger
- `S1-S3` / `two_column_smash`: ally, owned by Kerry Streichler
- `S1-S3` / `two_column_smash`: isty, owned by Sarah & Terry Grainger

### `1996 Vol II pg 93-162 back_ocr_hqmax.txt` (FAIL)
- `S1-S3` / `two_column_smash`: 3rd: not provided
- `S1-S3` / `two_column_smash`: 4th: not provided
- `O6` / `owner_tail_trunc`: 12 1/2-15" Reseve: Camelot Dafne, owned by

### `1996 Vol II pg 93-162 front_ocr_hqmax.txt` (FAIL)
- `S1-S3` / `two_column_smash`: 4th: dth: Thimble Farm Rodeo, owned by Angela Buszak & Erik Collins
- `S1-S3` / `two_column_smash`: 4th: finnie, owned by Nelly Niewola
- `S1-S3` / `two_column_smash`: 5th: y Chelsea, owned by Betty McArthur
- `S1-S3` / `two_column_smash`: elle, owned by Doug & Noreen Lorang
- `S1-S3` / `two_column_smash`: tch, owned by Tatty Shury
- `S1-S3` / `two_column_smash`: unter, owned by Mark & Lisa Green
- `S1-S3` / `two_column_smash`: mitt, owned by Richard Travisono
- `S1-S3` / `two_column_smash`: or, owned by Joe Jankowski & Kelly
- `S1-S3` / `two_column_smash`: ax, owned by Kendal Makowicz
- `S1-S3` / `two_column_smash`: 5th: g Lots Grabbit, owned by Alford & Leann McGregor
- `O6` / `owner_tail_trunc`: 10-12 1/2" Reserve: Farmcliff Donny, owned by
- `S1-S3` / `two_column_smash`: Ertries | Enries | 2nd

### `Document_2026-11-04_144208_ocr_hqmax.txt` (FAIL)
- `S1-S3` / `two_column_smash`: 3rd: AJ, owned by Westside
- `S1-S3` / `two_column_smash`: 3rd: drd: Farmcliff Becky, owned by Bob Franklin
- `S1-S3` / `two_column_smash`: 5th: not provided
- `O6` / `owner_tail_trunc`: 12 1/2-15" Reserve: Ay Jay of R.A, owned by

### `Document_2026-11-04_145355_ocr_hqmax.txt` (FAIL)
- `S1-S3` / `two_column_smash`: ay, owned by Cheryl Edwards
- `S1-S3` / `two_column_smash`: eof, owned by Sandra Ferber
- `O6` / `owner_tail_trunc`: Es ere OF WE, owned by
- `O6` / `owner_tail_trunc`: Westgate Rocket, owned by

### `Document_2026-11-04_145925_ocr_hqmax.txt` (FAIL)
- `S1-S3` / `two_column_smash`: 5th: lam Prancer, owned by Diana Decant
- `S1-S3` / `two_column_smash`: 2nd: bugs. Maybe
- `O6` / `owner_tail_trunc`: 1st: Red Oak Blue Bonnet of Gunsmoke, owned by

### `Document_2026-11-04_151058_ocr_hqmax.txt` (FAIL)
- `O6` / `owner_tail_trunc`: Lone Wolf Sophia, owned by
- `O6` / `owner_tail_trunc`: eo 2            a, owned by

### `Document_2026-11-04_152834_ocr_hqmax.txt` (FAIL)
- `S1-S3` / `two_column_smash`: 3rd: drd: Russellville Emmitt, owned by Barb Enright
- `S1-S3` / `two_column_smash`: 1st: fst: Windermere Sparkle, owned by Linda Cowasjee
- `S1-S3` / `two_column_smash`: 3rd: not available
- `S1-S3` / `two_column_smash`: 5th: not available

### `Document_2026-11-04_153208_ocr_hqmax.txt` (FAIL)
- `S1-S3` / `two_column_smash`: res, owned by Jack & Terri Batzer
- `S1-S3` / `two_column_smash`: yet, owned by Gaye Redpath
- `S1-S3` / `two_column_smash`: 5th: Not provided by Trial Chairperson, owned by Brenda Worley
- `S1-S3` / `two_column_smash`: Champion: Not provided by Trial Chairperson, owned by Brenda Worley
- `S1-S3` / `two_column_smash`: Reserve: Not provided by Trial Chairperson, owned by Brenda Worley
- `S1-S3` / `two_column_smash`: 2nd: Not provided by Trial Chairperson, owned by Brenda Worley
- `S1-S3` / `two_column_smash`: 6th: Not provided by Trial Chairperson, owned by Brenda Worley
- `S1-S3` / `two_column_smash`: 3rd: Not provided by Trial Chairperson, owned by Brenda Worley
