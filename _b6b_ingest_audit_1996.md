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
| FAIL | False | 15 | 0 | S1-S3×14,O6×1 | `1996 Vol 1 pg 111-160 back reversed_ocr_hqmax.txt` |
| FAIL | False | 14 | 0 | S1-S3×10,C1×3,O6×1 | `1996 Vol 1 pg 111-160 back_ocr_hqmax.txt` |
| FAIL | False | 26 | 0 | S1-S3×25,C1×1 | `1996 Vol 1 pg 111-160 front_ocr_hqmax.txt` |
| FAIL | False | 11 | 0 | S1-S3×11 | `1996 Vol 1 pg 161-178 back reversed_ocr_hqmax.txt` |
| FAIL | False | 10 | 0 | S1-S3×10 | `1996 Vol 1 pg 161-178 back_ocr_hqmax.txt` |
| FAIL | False | 10 | 0 | S1-S3×10 | `1996 Vol 1 pg 161-178 front_ocr_hqmax.txt` |
| FAIL | False | 11 | 0 | S1-S3×11 | `1996 Vol 1 pg 21-60 back reversed_ocr_hqmax.txt` |
| FAIL | False | 15 | 0 | S1-S3×15 | `1996 Vol 1 pg 21-60 back_ocr_hqmax.txt` |
| FAIL | False | 15 | 0 | S1-S3×12,C1×2,O6×1 | `1996 Vol 1 pg 21-60 front_ocr_hqmax.txt` |
| FAIL | False | 27 | 0 | S1-S3×25,C1×2 | `1996 Vol 1 pg 61-110 back reversed_ocr_hqmax.txt` |
| FAIL | False | 26 | 0 | S1-S3×25,C1×1 | `1996 Vol 1 pg 61-110 back_ocr_hqmax.txt` |
| FAIL | False | 26 | 0 | S1-S3×25,O6×1 | `1996 Vol 1 pg 61-110 front_ocr_hqmax.txt` |
| FAIL | False | 11 | 0 | S1-S3×10,C1×1 | `1996 Vol II pg 163-220 back reversed_ocr_hqmax.txt` |
| FAIL | False | 19 | 0 | S1-S3×15,C1×3,O6×1 | `1996 Vol II pg 163-220 back_ocr_hqmax.txt` |
| FAIL | False | 20 | 0 | S1-S3×19,O6×1 | `1996 Vol II pg 163-220 front_ocr_hqmax.txt` |
| FAIL | False | 16 | 0 | S1-S3×16 | `1996 Vol II pg 23-92 back reversed_ocr_hqmax.txt` |
| FAIL | False | 20 | 0 | S1-S3×20 | `1996 Vol II pg 23-92 back_ocr_hqmax.txt` |
| FAIL | False | 30 | 0 | S1-S3×25,C1×5 | `1996 Vol II pg 23-92 front (missing 1 pgs)_ocr_hqmax.txt` |
| FAIL | False | 28 | 0 | S1-S3×25,C1×3 | `1996 Vol II pg 23-92 front (missing 2 pgs)_ocr_hqmax.txt` |
| FAIL | False | 30 | 0 | S1-S3×25,C1×3,O6×2 | `1996 Vol II pg 23-92 front_ocr_hqmax.txt` |
| FAIL | False | 25 | 0 | S1-S3×21,O6×2,C1×2 | `1996 Vol II pg 93-162 back reversed_ocr_hqmax.txt` |
| FAIL | False | 24 | 0 | S1-S3×22,O6×1,C1×1 | `1996 Vol II pg 93-162 back_ocr_hqmax.txt` |
| FAIL | False | 28 | 0 | S1-S3×25,O6×2,C1×1 | `1996 Vol II pg 93-162 front_ocr_hqmax.txt` |
| FAIL | False | 13 | 0 | S1-S3×11,C1×2 | `Document_2026-11-04_144208_ocr_hqmax.txt` |
| FAIL | False | 25 | 0 | S1-S3×25 | `Document_2026-11-04_144530_ocr_hqmax.txt` |
| PASS | False | 0 | 0 | — | `Document_2026-11-04_145355_ocr_hqmax.txt` |
| FAIL | False | 17 | 0 | S1-S3×17 | `Document_2026-11-04_145925_ocr_hqmax.txt` |
| PASS | False | 0 | 0 | — | `Document_2026-11-04_151058_ocr_hqmax.txt` |
| FAIL | False | 20 | 0 | S1-S3×20 | `Document_2026-11-04_152834_ocr_hqmax.txt` |
| FAIL | False | 8 | 0 | S1-S3×8 | `Document_2026-11-04_153208_ocr_hqmax.txt` |

## Sample residual hits (after cleanup)

### `1996 Vol 1 pg 111-160 back reversed_ocr_hqmax.txt` (FAIL)
- `O6` / `owner_tail_trunc`: 10-12 1/2" Champion: Camerton Hall BeBop, owned by ow
- `S1-S3` / `two_column_smash`: 1st: The Hollow fork, owned by The Hollow Terrers
- `S1-S3` / `two_column_smash`: 6th: Springcroft Augu:
- `S1-S3` / `two_column_smash`: 6th: Sow's Ear lasher, owned by Paul Hartman/ Karen McCarthy
- `S1-S3` / `two_column_smash`: 1st: Fox Valley Dylan of Chuck's Run, owned by Kathleen Hardy
- `S1-S3` / `two_column_smash`: 1st: Foxfield's Garth of Lost Creek, owned by Debbie McWilliams
- `S1-S3` / `two_column_smash`: 1st: Jesse James, owned by Joann Jurish
- `S1-S3` / `two_column_smash`: 2nd: Lost Creek Merlin, owned by Debbie McWilliams
- `S1-S3` / `two_column_smash`: 1st: Grant of Hideaway Farm, owned by Ken & Penny Baker
- `S1-S3` / `two_column_smash`: 1st: Calset Max, owned by Shannon Jones
- `S1-S3` / `two_column_smash`: 1st: BrandywineBruce, owned by Stephanie Taylor
- `S1-S3` / `two_column_smash`: 5th: Farmcliff Srowflz

### `1996 Vol 1 pg 111-160 back_ocr_hqmax.txt` (FAIL)
- `O6` / `owner_tail_trunc`: 10-12 1/2" Reserv: Fox Valley Dylan of Chucks Run, owned by ow
- `C1` / `class_header_gap`: 5th: Foxfield Flash, owned by Janet Sproles
- `C1` / `class_header_gap`: 5th: The Bowery Mst, owned by Teresa Wellman
- `C1` / `class_header_gap`: 2nd: Sow's Ear liberty, owned by Paul Hartman/ Karen McCarthy
- `S1-S3` / `two_column_smash`: 1st: BrandywineBruce, owned by Stephanie Taylor
- `S1-S3` / `two_column_smash`: 1st: Calset Max, owned by Shannon Jones
- `S1-S3` / `two_column_smash`: 1st: Grant of Hideaway Farm, owned by Ken & Penny Baker
- `S1-S3` / `two_column_smash`: 1st: Jesse James, owned by Joann Jurish
- `S1-S3` / `two_column_smash`: 2nd: Lost Creek Merlin, owned by Debbie McWilliams
- `S1-S3` / `two_column_smash`: 1st: Fox Valley Dylan of Chuck's Run, owned by Kathleen Hardy
- `S1-S3` / `two_column_smash`: 1st: Brandywine Butch, owned by Stephanie Taylor
- `S1-S3` / `two_column_smash`: 1st: The Hollow York, owned by The Hollow Terriers

### `1996 Vol 1 pg 111-160 front_ocr_hqmax.txt` (FAIL)
- `C1` / `class_header_gap`: 6th: Agnew, owned by Margo Weston
- `S1-S3` / `two_column_smash`: 5th: Bittersweet Belle, owned by Doug & Noreen Loranger
- `S1-S3` / `two_column_smash`: 6th: Farmstead Abby, owned by Richard & Annette Kent
- `S1-S3` / `two_column_smash`: 1st: Churchview Chase, owned by Debbie Neal
- `S1-S3` / `two_column_smash`: 2nd: Whispering Winds Sir William Mitchell, owned by Weslee Boehme
- `S1-S3` / `two_column_smash`: 5th: Old Glory Tory, owned by Jan Thomas
- `S1-S3` / `two_column_smash`: 6th: disqualified
- `S1-S3` / `two_column_smash`: 1st: Jasper, owned by Rebecca Green
- `S1-S3` / `two_column_smash`: 2nd: Weasel, owned by Raymond Hibbs
- `S1-S3` / `two_column_smash`: 3rd: Corkonian Sassafrass, owned by Sandra & Ian Hughes
- `S1-S3` / `two_column_smash`: 5th: Nettles Penny, owned by Eric & Nancy Kilby
- `S1-S3` / `two_column_smash`: 6th: Checkmates Jess, owned by Nadine Bleck

### `1996 Vol 1 pg 161-178 back reversed_ocr_hqmax.txt` (FAIL)
- `S1-S3` / `two_column_smash`: 1st: Westgate Rocet, owned by John Westgate & Barbara Jordan
- `S1-S3` / `two_column_smash`: 5th: Redwood Tyle of Impressive, owned by Doris Sneider
- `S1-S3` / `two_column_smash`: 1st: Simon, owned by Mary Sprakies
- `S1-S3` / `two_column_smash`: 1st: Chile, owned by Mary L. Gomez
- `S1-S3` / `two_column_smash`: 2nd: Little Lottie, owned by Julie Smith
- `S1-S3` / `two_column_smash`: 3rd: Belle Pepper, owned by Bob & Karen Stone
- `S1-S3` / `two_column_smash`: 1st: Brandywine Bruce, owned by Stephanie Taylor
- `S1-S3` / `two_column_smash`: 5th: Ravenswooi Raisin, owned by Lisa Drinkwater
- `S1-S3` / `two_column_smash`: 6th: Farmcliff Srowflake, owned by Genie Franklin
- `S1-S3` / `two_column_smash`: 1st: Fox Valley Dillon of Quick Chase, owned by K. Hardy
- `S1-S3` / `two_column_smash`: 2nd: Pine Hill Scioter, owned by Sandy Bassett

### `1996 Vol 1 pg 161-178 back_ocr_hqmax.txt` (FAIL)
- `S1-S3` / `two_column_smash`: 5th: Ravenswooi Raisin, owned by Lisa Drinkwater
- `S1-S3` / `two_column_smash`: 6th: Farmcliff Srowflake, owned by Genie Franklin
- `S1-S3` / `two_column_smash`: 1st: Fox Valley billon of Quick Chase, owned by K. Hardy
- `S1-S3` / `two_column_smash`: 2nd: Pine Hill Scioter, owned by Sandy Bassett
- `S1-S3` / `two_column_smash`: 1st: Brandywine Bruce, owned by Stephanie Taylor
- `S1-S3` / `two_column_smash`: 5th: Redwood Tyte of Impressive, owned by Doris Sneider
- `S1-S3` / `two_column_smash`: 2nd: Glynnsong Jie, owned by Jack Androvich/Jeanne Androvich
- `S1-S3` / `two_column_smash`: 1st: Chile, owned by Mary L. Gomez
- `S1-S3` / `two_column_smash`: 2nd: Little Lottie, owned by Julie Smith
- `S1-S3` / `two_column_smash`: 3rd: Belle Pepper, owned by Bob & Karen Stone

### `1996 Vol 1 pg 161-178 front_ocr_hqmax.txt` (FAIL)
- `S1-S3` / `two_column_smash`: 3rd: Lickity Split Lotta Sass, owned by Darlene Mclnnes
- `S1-S3` / `two_column_smash`: 4th: Lickity Split Lexus, owned by Darlene McInnes
- `S1-S3` / `two_column_smash`: 5th: Justa Joy Friesian, owned by Dermot Gilligan
- `S1-S3` / `two_column_smash`: 1st: Glynnsong Jake, owned by Jack Androvich/Jeanne Androvich
- `S1-S3` / `two_column_smash`: 5th: Max, owned by Kathy Rafe
- `S1-S3` / `two_column_smash`: 6th: Kibbles of Churchview, owned by Sandy & John Brown
- `S1-S3` / `two_column_smash`: 1st: Fox Valley Dillon, owned by K. Hardy
- `S1-S3` / `two_column_smash`: 1st: Farmcliff Duke, owned by Kim Hunter & Jim Hughes
- `S1-S3` / `two_column_smash`: 2nd: Long Hope Mickey, owned by Bob Franklin
- `S1-S3` / `two_column_smash`: 3rd: Courtland Moo Cow, owned by Jospeh Jankowski

### `1996 Vol 1 pg 21-60 back reversed_ocr_hqmax.txt` (FAIL)
- `S1-S3` / `two_column_smash`: 1st: T.F. Tavis MiGuire, owned by Robert Reardon
- `S1-S3` / `two_column_smash`: 5th: Blackland Bornie, owned by Lloyd & Shirley Cox
- `S1-S3` / `two_column_smash`: 6th: Blackland Malda
- `S1-S3` / `two_column_smash`: 1st: Hi-Flashun Alie Re
- `S1-S3` / `two_column_smash`: 5th: Blackiand Bomie, owned by Lloyd & Shiriey Cox
- `S1-S3` / `two_column_smash`: 6th: Gabriel, owned by Barbara & Tony Ziehler
- `S1-S3` / `two_column_smash`: 1st: Hi-Flashun Ala Romeo, owned by Rob Mokry
- `S1-S3` / `two_column_smash`: 5th: WestwoodJolie, owned by Alice Reynolds
- `S1-S3` / `two_column_smash`: 6th: Blackland Sheen:
- `S1-S3` / `two_column_smash`: 1st: FoxwarrenRaidel
- `S1-S3` / `two_column_smash`: 2nd: Show-Me Bernarc

### `1996 Vol 1 pg 21-60 back_ocr_hqmax.txt` (FAIL)
- `S1-S3` / `two_column_smash`: 5th: WestwoodJolie, owned by Alice Reynolds
- `S1-S3` / `two_column_smash`: 6th: Blackland Sheena, owned by Lloyd & Shirley Cox
- `S1-S3` / `two_column_smash`: 1st: FoxwarrenRaider, owned by Joann Vinelli
- `S1-S3` / `two_column_smash`: 2nd: Show-Me Bernard of Heartstone, owned by Lynn Jerome
- `S1-S3` / `two_column_smash`: 1st: Reyem's theMervster, owned by Ken Meyer
- `S1-S3` / `two_column_smash`: 5th: Blackland Bomie, owned by Lloyd & Shirley Cox
- `S1-S3` / `two_column_smash`: 6th: Gabriel, owned by Barbara & Tony Ziehler
- `S1-S3` / `two_column_smash`: 1st: Hi-Flashun Ala Romeo, owned by Rob Mokry
- `S1-S3` / `two_column_smash`: 1st: Seaview Shag, owned by Didi Gough
- `S1-S3` / `two_column_smash`: 5th: Blackland Bornie, owned by Lloyd & Shirley Cox
- `S1-S3` / `two_column_smash`: 6th: Blackland Matlda of Gunsmoke, owned by Kenneth & Rose Cox
- `S1-S3` / `two_column_smash`: 1st: Hi-Flashun Alie Romeo, owned by Rob Mokry

### `1996 Vol 1 pg 21-60 front_ocr_hqmax.txt` (FAIL)
- `O6` / `owner_tail_trunc`: Best: Foxfield Sprig, owned by ow
- `C1` / `class_header_gap`: 5th: Treehouse Cookie, owned by Julie Conner
- `C1` / `class_header_gap`: 4th: Hart Farm Hammer, owned by Cheryl Hart
- `S1-S3` / `two_column_smash`: 1st: Highland Bay Monster, owned by H. Cromwell
- `S1-S3` / `two_column_smash`: 2nd: Trebor Chase Pony, owned by B. Mathis
- `S1-S3` / `two_column_smash`: 1st: Camerton Hall Izod, owned by Pauline & Jack Fawkes
- `S1-S3` / `two_column_smash`: 5th: Trix, owned by Chris Fraley
- `S1-S3` / `two_column_smash`: 6th: Camerton Hall Fury, owned by Ginny Sloan
- `S1-S3` / `two_column_smash`: 5th: Undercover Scotty, owned by Lynn May-Measles
- `S1-S3` / `two_column_smash`: 6th: Foxfields Chase, owned by Julie & Kim Pagliaro
- `S1-S3` / `two_column_smash`: 1st: Hopdiggity Raider, owned by Liz & Pete Littman
- `S1-S3` / `two_column_smash`: 3rd: Wildgoose National, owned by C. J. Harris

### `1996 Vol 1 pg 61-110 back reversed_ocr_hqmax.txt` (FAIL)
- `C1` / `class_header_gap`: 4th: Badakhashan Celestial Haley, owned by Fay Craft
- `C1` / `class_header_gap`: 3rd: Foxwarren Kely of, owned by Heather Cromwell
- `S1-S3` / `two_column_smash`: 2nd: Sunset Valley Sassy, owned by Pat Timmons
- `S1-S3` / `two_column_smash`: 3rd: Good Times Polar Snow Baby, owned by Steve Spruill
- `S1-S3` / `two_column_smash`: 4th: Three OaksSukhou of Good Times, owned by Steve Spruill
- `S1-S3` / `two_column_smash`: 1st: Camerton Hall Nero, owned by Jack & Pauline Fawkes
- `S1-S3` / `two_column_smash`: Champion: Wood uff of Ruff N' Tumble, owned by Steve & Kathy Padilla
- `S1-S3` / `two_column_smash`: Reserve: Westgat: Molly, owned by Betsy Jordan
- `S1-S3` / `two_column_smash`: 1st: Impressive Winchester, owned by Carol Magetti
- `S1-S3` / `two_column_smash`: 6th: Fenton Scouts Honor, owned by Christy Parkison
- `S1-S3` / `two_column_smash`: 1st: Treesbank Fanagan, owned by Janet Sproles
- `S1-S3` / `two_column_smash`: 2nd: Golden HillsShady Lady Bug, owned by Didi Gough

### `1996 Vol 1 pg 61-110 back_ocr_hqmax.txt` (FAIL)
- `C1` / `class_header_gap`: 6th: Hitts Badger, owned by Mark Hitt
- `S1-S3` / `two_column_smash`: 1st: Lone Wolf Nurphy, owned by Theresa & Frank Bradley
- `S1-S3` / `two_column_smash`: 1st: Bevelwood Axl, owned by Scott Looper
- `S1-S3` / `two_column_smash`: 2nd: Bevelwood Cowboy, owned by Scott Looper
- `S1-S3` / `two_column_smash`: 1st: Hart Farm Buno, owned by Cheryl Hart
- `S1-S3` / `two_column_smash`: 2nd: Timely, owned by Teresa Kaufstein
- `S1-S3` / `two_column_smash`: 3rd: Nikki, owned by Debbie Vaiden
- `S1-S3` / `two_column_smash`: 5th: Qualyns Trinity, owned by Russell & Darlene Zampella
- `S1-S3` / `two_column_smash`: 6th: Lost Acres Revlon of Sow's Ear, owned by Paul Hartman & Karen McCarthy
- `S1-S3` / `two_column_smash`: 1st: Marcus, owned by J. Benintendo
- `S1-S3` / `two_column_smash`: 2nd: Sir Milos Magic, owned by Antonio Sullo
- `S1-S3` / `two_column_smash`: 1st: WillowbrookChalk, owned by Martin & Teresa Gottlieb

### `1996 Vol 1 pg 61-110 front_ocr_hqmax.txt` (FAIL)
- `O6` / `owner_tail_trunc`: 10-12 1/2" Champion: RA Piker, owned by ow
- `S1-S3` / `two_column_smash`: 1st: Sunset Valley Sassy, owned by Pat Timmons
- `S1-S3` / `two_column_smash`: 2nd: Heaven Hill Foxy, owned by Doug Stephenson
- `S1-S3` / `two_column_smash`: 3rd: Blackland Sheena, owned by Lloyd & Shirley Cox
- `S1-S3` / `two_column_smash`: 1st: Lost Creek Merlin, owned by Debbie McWilliams
- `S1-S3` / `two_column_smash`: 2nd: Sparks Will Fly, owned by Patricia Caschera
- `S1-S3` / `two_column_smash`: 3rd: Runamuk Magg, owned by Kathy & Mitchell Cohen
- `S1-S3` / `two_column_smash`: 4th: Harlene, owned by Heidi Ryan
- `S1-S3` / `two_column_smash`: 1st: Impressive Maxi, owned by Darrell & Teresa Payne
- `S1-S3` / `two_column_smash`: 2nd: Boomer, owned by Kathy Powell
- `S1-S3` / `two_column_smash`: 1st: Crossewinds Keswick, owned by Eastlake Terriers
- `S1-S3` / `two_column_smash`: 1st: Corn Row Calumet, owned by Pam Simmons

### `1996 Vol II pg 163-220 back reversed_ocr_hqmax.txt` (FAIL)
- `C1` / `class_header_gap`: Reserve: High& Low Hellion, owned by Melissa C. Lowe
- `S1-S3` / `two_column_smash`: 1st: Rolling Rock's Reno, owned by Wayne & De Brown
- `S1-S3` / `two_column_smash`: 4th: Bamber, owned by Martha Leroy
- `S1-S3` / `two_column_smash`: 1st: Loblolly Burbn, owned by Diana Decant
- `S1-S3` / `two_column_smash`: 1st: Lost Creek Tango, owned by Debbie McWilliams
- `S1-S3` / `two_column_smash`: 2nd: Kirby, owned by Patrick & Taya Johnson
- `S1-S3` / `two_column_smash`: 3rd: Tortilla FlatCrackers, owned by Mike Bilbo
- `S1-S3` / `two_column_smash`: 1st: Ticketyboo Angus, owned by Leslie Kelly
- `S1-S3` / `two_column_smash`: 1st: Russellvilles Hole Shot, owned by Chris Klonghen
- `S1-S3` / `two_column_smash`: 1st: HopdiggityRaider, owned by Liz Littmann
- `S1-S3` / `two_column_smash`: 1st: Russellvilles Salty Dog, owned by Marge & Bill Brubaker

### `1996 Vol II pg 163-220 back_ocr_hqmax.txt` (FAIL)
- `O6` / `owner_tail_trunc`: 12 1/2-15" Chanpion: Single Track Hunter, owned by ow
- `C1` / `class_header_gap`: 5th: Ben of Windemere, owned by Linda J. Cowasjee
- `C1` / `class_header_gap`: 5th: Rustler's Daisy Bryant of Paw Print, owned by Irene Welch
- `C1` / `class_header_gap`: 2nd: Joyful Noise Bugsy, owned by Richard & Annette Kenx
- `S1-S3` / `two_column_smash`: 1st: Russellvilles Salty Dog, owned by Marge & Bill Brubaker
- `S1-S3` / `two_column_smash`: 1st: HopdiggityRaider, owned by Liz Littmann
- `S1-S3` / `two_column_smash`: 2nd: Lost Creeks Merlin, owned by Debbie McWilliams
- `S1-S3` / `two_column_smash`: 5th: Undercove Annie, owned by Lynn May Measles
- `S1-S3` / `two_column_smash`: 6th: Lost Creeks Tessa, owned by Tara Overton
- `S1-S3` / `two_column_smash`: 1st: Russellvilles Hole Shot, owned by Chris Klonghen
- `S1-S3` / `two_column_smash`: 1st: Craftifox Rebel Rouser, owned by Kelly & James Barbeau
- `S1-S3` / `two_column_smash`: 1st: Ticketyboo Angus, owned by Leslie Kelly

### `1996 Vol II pg 163-220 front_ocr_hqmax.txt` (FAIL)
- `O6` / `owner_tail_trunc`: Over 12 1/2" Reserve: Merlin of Lost Creek, owned by ow
- `S1-S3` / `two_column_smash`: 1st: Brandy of Rednek, owned by Boyd K.
- `S1-S3` / `two_column_smash`: 2nd: Lunstarr Jackie of Flying "A", owned by Lee Jean Stafford
- `S1-S3` / `two_column_smash`: 3rd: Wesworld Sheila, owned by Mark Shaw
- `S1-S3` / `two_column_smash`: 1st: Lost Creek Tango, owned by Debbie Mc)
- `S1-S3` / `two_column_smash`: 2nd: Eagles Nest Chase, owned by Marlow
- `S1-S3` / `two_column_smash`: 1st: Lunstarr Jackie of Flying "A", owned by Lee Jean Stafford
- `S1-S3` / `two_column_smash`: 2nd: Wesworld Sheila, owned by Mark Shaw
- `S1-S3` / `two_column_smash`: 1st: Crosswinds Loger, owned by Becky Crosse
- `S1-S3` / `two_column_smash`: 5th: High & Low Frostbite of Running Wild, owned by Bob Zeiner
- `S1-S3` / `two_column_smash`: 6th: Shenandoah of Eddie Haskek, owned by Ed Marucci
- `S1-S3` / `two_column_smash`: 1st: High & Low Banshee, owned by Melissa Howe

### `1996 Vol II pg 23-92 back reversed_ocr_hqmax.txt` (FAIL)
- `S1-S3` / `two_column_smash`: 2nd: Hunter Pont Dallas, owned by Karen Rankin
- `S1-S3` / `two_column_smash`: 3rd: Polar Snow Baby, owned by Steve Spruill
- `S1-S3` / `two_column_smash`: 1st: Foxhall Shbad, owned by Foxhall Terriers
- `S1-S3` / `two_column_smash`: 3rd: Jeep, owned by Greywood Farms
- `S1-S3` / `two_column_smash`: 1st: Razz Maazz of Wildwood, owned by Mary Proulx
- `S1-S3` / `two_column_smash`: 3rd: Pine Cresk Little Nemo, owned by Rhonda Rebhorn
- `S1-S3` / `two_column_smash`: 1st: Finbar Ruffian, owned by Mark & Missy Kulbacky
- `S1-S3` / `two_column_smash`: 3rd: Dutch Cree Classy, owned by Gordon Sanderson, ill
- `S1-S3` / `two_column_smash`: 4th: Poco Bailey, owned by Wayne Holleman
- `S1-S3` / `two_column_smash`: 1st: Prestwick Sambo, owned by Ray & Jean Derrick
- `S1-S3` / `two_column_smash`: 2nd: Three Oaks Hunter, owned by Curtis Reese
- `S1-S3` / `two_column_smash`: 5th: Rynward'sTeasel, owned by Sue Hardin

### `1996 Vol II pg 23-92 back_ocr_hqmax.txt` (FAIL)
- `S1-S3` / `two_column_smash`: 1st: Desert Fox Jerry Garcia, owned by Twila Decker
- `S1-S3` / `two_column_smash`: 2nd: Whisperiny Winds Munchee, owned by Ken & Mary Winfield
- `S1-S3` / `two_column_smash`: 3rd: Lil Jazzmiie, owned by Maureen McKernan
- `S1-S3` / `two_column_smash`: 5th: Rynward'sTeasel, owned by Sue Hardin
- `S1-S3` / `two_column_smash`: 6th: Farmcliff Showflake, owned by Bob & Genie Franklin
- `S1-S3` / `two_column_smash`: 1st: MaefieldOliver, owned by Elizabeth Gleason
- `S1-S3` / `two_column_smash`: 3rd: Dutch Cree Classy, owned by Gordon Sanderson, lll
- `S1-S3` / `two_column_smash`: 4th: Poco Bailey, owned by Wayne Holleman
- `S1-S3` / `two_column_smash`: 1st: Prestwick Sambo, owned by Ray & Jean Derrick
- `S1-S3` / `two_column_smash`: 2nd: Three Oaks Hunter, owned by Curtis Reese
- `S1-S3` / `two_column_smash`: 1st: Pine Hill Scooter, owned by Sandy Bassett
- `S1-S3` / `two_column_smash`: 1st: Finbarr Ruffian, owned by Mark & Missy Kulbacky

### `1996 Vol II pg 23-92 front (missing 1 pgs)_ocr_hqmax.txt` (FAIL)
- `C1` / `class_header_gap`: 3rd: Burrows Inn Biff, owned by Jennifer Minnick
- `C1` / `class_header_gap`: 3rd: Rocky, owned by Stacie Hoffman
- `C1` / `class_header_gap`: 4th: Whispering Winds Jake, owned by Jan & Mark Bjorkland
- `C1` / `class_header_gap`: 5th: Didger, owned by Chuck Bell
- `C1` / `class_header_gap`: 3rd: Willow Pond Spencer of Four Corners, owned by Gary & Sherry Alcock
- `S1-S3` / `two_column_smash`: 4th: Wynnewood Wade, owned by Anne Davis
- `S1-S3` / `two_column_smash`: 5th: Dutch Creek Nya, owned by Bonita Knickmeyer
- `S1-S3` / `two_column_smash`: 1st: Pork Chop, owned by Paul Sterrett
- `S1-S3` / `two_column_smash`: 3rd: Dutch Creek Nya, owned by Bonita Knickmeyer
- `S1-S3` / `two_column_smash`: 4th: Hunter Point Dallas, owned by Karen Rankin
- `S1-S3` / `two_column_smash`: 5th: All Seasons Fancy, owned by Brenda Roberts
- `S1-S3` / `two_column_smash`: 1st: High & Low Frostbite, owned by R. Worth Zeiher

### `1996 Vol II pg 23-92 front (missing 2 pgs)_ocr_hqmax.txt` (FAIL)
- `C1` / `class_header_gap`: 3rd: Rocky, owned by Stacie Hoffman
- `C1` / `class_header_gap`: 5th: Lightning, owned by Margaret & David Ashe
- `C1` / `class_header_gap`: 3rd: Willow Pond Spencer of Four Corners, owned by Gary & Sherry Alcock
- `S1-S3` / `two_column_smash`: 4th: Wynnewood Wade, owned by Anne Davis
- `S1-S3` / `two_column_smash`: 5th: Dutch Creek Nya, owned by Bonita Knickmeyer
- `S1-S3` / `two_column_smash`: 1st: Pork Chop, owned by Paul Sterrett
- `S1-S3` / `two_column_smash`: 3rd: Dutch Creek Nya, owned by Bonita Knickmeyer
- `S1-S3` / `two_column_smash`: 4th: Hunter Point Dallas, owned by Karen Rankin
- `S1-S3` / `two_column_smash`: 5th: All Seasons Fancy, owned by Brenda Roberts
- `S1-S3` / `two_column_smash`: 1st: High & Low Frostbite, owned by R. Worth Zeiher
- `S1-S3` / `two_column_smash`: 2nd: Badakhashan Bolt the Fox, owned by Fay Craft
- `S1-S3` / `two_column_smash`: 3rd: Pork Chop, owned by Paul Sterrett

### `1996 Vol II pg 23-92 front_ocr_hqmax.txt` (FAIL)
- `O6` / `owner_tail_trunc`: 10-12 1/2" Champion: Razz Matazz, owned by ow
- `O6` / `owner_tail_trunc`: 12 1/2-15" Champion: Turbo Charge, owned by ow
- `C1` / `class_header_gap`: 3rd: Burrows Inn Biff, owned by Jennifer Minnick
- `C1` / `class_header_gap`: 4th: Whispering Winds Jake, owned by Jan & Mark Bjorkland
- `C1` / `class_header_gap`: 5th: Over the Hill Barkley, owned by Mike & Betty Bilinski
- `S1-S3` / `two_column_smash`: 4th: Wynnewood Wade, owned by Anne Davis
- `S1-S3` / `two_column_smash`: 5th: Dutch Creek Nya, owned by Bonita Knickmeyer
- `S1-S3` / `two_column_smash`: 1st: Pork Chop, owned by Paul Sterrett
- `S1-S3` / `two_column_smash`: 3rd: Dutch Creek Nya, owned by Bonita Knickmeyer
- `S1-S3` / `two_column_smash`: 4th: Hunter Point Dallas, owned by Karen Rankin
- `S1-S3` / `two_column_smash`: 5th: All Seasons Fancy, owned by Brenda Roberts
- `S1-S3` / `two_column_smash`: 1st: High & Low Frostbite, owned by R. Worth Zeiher

### `1996 Vol II pg 93-162 back reversed_ocr_hqmax.txt` (FAIL)
- `O6` / `owner_tail_trunc`: 12 1/2-15" Reserve: Horsemasters Willy, owned by ow
- `O6` / `owner_tail_trunc`: 12 1/2-15" Chanpion: Salishan Maggie, owned by ow
- `C1` / `class_header_gap`: 2nd: Rock Ledges Pinch, owned by P. Stellwag
- `C1` / `class_header_gap`: 2nd: Fox Run Soric, owned by Sandra Ferber
- `S1-S3` / `two_column_smash`: 1st: Reidell Megnum, owned by Bill Pinder
- `S1-S3` / `two_column_smash`: 1st: Hart FarmRebe of Wellington, owned by Robert VanDer Heym
- `S1-S3` / `two_column_smash`: 2nd: Earmcliff Annie, owned by Bob Franklin/Doug & Sue Tack
- `S1-S3` / `two_column_smash`: 1st: Fox Run Ben, owned by Kenneth Frazier
- `S1-S3` / `two_column_smash`: 1st: Heaven Hill Foxy, owned by Doug Stephenson
- `S1-S3` / `two_column_smash`: 2nd: Red OakDixie of Gunsmoke, owned by Kenneth & Rose Cox
- `S1-S3` / `two_column_smash`: 3rd: Hunters Point Dallas, owned by Karen Rankin
- `S1-S3` / `two_column_smash`: 1st: Miller Tine, owned by Laura O'Leary

### `1996 Vol II pg 93-162 back_ocr_hqmax.txt` (FAIL)
- `O6` / `owner_tail_trunc`: 12 1/2-15" Reserve: Horsemasters Willy, owned by ow
- `C1` / `class_header_gap`: 5th: Meynell Rickus, owned by Ray Derrick
- `S1-S3` / `two_column_smash`: 2nd: Farmstead Abby, owned by Ricard & Annette Kent
- `S1-S3` / `two_column_smash`: 3rd: Farmcliff Snowflake, owned by Genie Franklin
- `S1-S3` / `two_column_smash`: 3rd: Rainier Drat, owned by Molly Martin
- `S1-S3` / `two_column_smash`: 4th: Wiley, owned by Diana McClane
- `S1-S3` / `two_column_smash`: 1st: Goliath, owned by Jason & Sharon Ottman
- `S1-S3` / `two_column_smash`: 3rd: Rooter, owned by Nathan Greenbaum
- `S1-S3` / `two_column_smash`: 4th: Crossruff Kemden, owned by Deborah Holly
- `S1-S3` / `two_column_smash`: 3rd: Long Hope Wee Won, owned by Nellie Niewola
- `S1-S3` / `two_column_smash`: 1st: Maefield Giver, owned by Elizabeth Gleason
- `S1-S3` / `two_column_smash`: 1st: Rainland Force, owned by Robert & Linda Fleck

### `1996 Vol II pg 93-162 front_ocr_hqmax.txt` (FAIL)
- `O6` / `owner_tail_trunc`: Under 12 1/2" Reserve: Heaven Hill Jezebel, owned by ow
- `O6` / `owner_tail_trunc`: Over 12 1/2" Champion: Three Oaks Hunter, owned by ow
- `C1` / `class_header_gap`: Champion: Foxport Keeper, owned by Michelle Ward
- `S1-S3` / `two_column_smash`: 2nd: Rockridge Monterey Jack, owned by Gene Harvey
- `S1-S3` / `two_column_smash`: 3rd: Windermere Witewitch, owned by Karen McCarthy & Paul Hartman
- `S1-S3` / `two_column_smash`: 2nd: Romney Kaz, owned by Kim Hunter
- `S1-S3` / `two_column_smash`: 1st: The Larches Fuego, owned by Joan & Donald LaPlace
- `S1-S3` / `two_column_smash`: 5th: Will-O-Moor Rex, owned by Michelle Williams
- `S1-S3` / `two_column_smash`: 6th: Windermere Witewitch, owned by Karen McCarthy & Paul Hartman
- `S1-S3` / `two_column_smash`: 5th: Heaven Hill Zodiac, owned by Mike & Betty Bilinski
- `S1-S3` / `two_column_smash`: 6th: Wild Goose Bit-of-Honey, owned by Carol Frazier
- `S1-S3` / `two_column_smash`: 1st: Miller Time, owned by Laura O'Leary

### `Document_2026-11-04_144208_ocr_hqmax.txt` (FAIL)
- `C1` / `class_header_gap`: 5th: Treehouse Cookie, owned by Julie Conner
- `C1` / `class_header_gap`: 4th: Hart Farm Hammer of Ravenswood, owned by Janet Sutcliffe
- `S1-S3` / `two_column_smash`: 1st: Camerton Hall Izod, owned by Jack & Pauline Fawkes
- `S1-S3` / `two_column_smash`: 5th: Trix, owned by Chris Fraley
- `S1-S3` / `two_column_smash`: 6th: Camerton Hall Fury, owned by Ginny Sloa
- `S1-S3` / `two_column_smash`: 1st: Camerton Hall Nero, owned by Pauline Cromwell
- `S1-S3` / `two_column_smash`: 6th: Foxfields Chase, owned by Julie & Kim Pagliaro
- `S1-S3` / `two_column_smash`: 1st: Hopdiggity Raider, owned by Liz & Pete Littman
- `S1-S3` / `two_column_smash`: 2nd: Truffles, owned by Heidi & Kevin Manzi
- `S1-S3` / `two_column_smash`: 3rd: Wildgoose National, owned by C. J. Harris
- `S1-S3` / `two_column_smash`: 1st: Just a Joy Friesian, owned by Dermot Gilligan
- `S1-S3` / `two_column_smash`: 1st: Corn Row Calumet of Wootinhille, owned by Phillip Hawkins

### `Document_2026-11-04_144530_ocr_hqmax.txt` (FAIL)
- `S1-S3` / `two_column_smash`: 1st: Corn Row Calumet, owned by Phil Hawkins
- `S1-S3` / `two_column_smash`: 2nd: Peirce of Cold Water, owned by Karen & Robert Seals
- `S1-S3` / `two_column_smash`: 3rd: Susie, owned by Donna Shamp
- `S1-S3` / `two_column_smash`: 1st: Camerton Hall Nero, owned by Jack & Pauline Fawkes
- `S1-S3` / `two_column_smash`: 1st: Sunset Valley Sassy, owned by Pat Timmons
- `S1-S3` / `two_column_smash`: 2nd: Heaven Hill Foxy, owned by Doug Stephenson
- `S1-S3` / `two_column_smash`: 3rd: Blackland Sheena, owned by Lloyd & Shirley Cox
- `S1-S3` / `two_column_smash`: 1st: Lost Creek Merlin, owned by Debbie McWilliams
- `S1-S3` / `two_column_smash`: 2nd: Windermere Witewitch of Sows Ear, owned by P. Hartman & K. McCarthy
- `S1-S3` / `two_column_smash`: 3rd: Lickity Split Lotta Sass, owned by Darlene Mclnnes
- `S1-S3` / `two_column_smash`: 1st: Impressive Maxie Moe, owned by Carol Magetti
- `S1-S3` / `two_column_smash`: 2nd: Boomer, owned by Kathy & Mitchell Cohen

### `Document_2026-11-04_145925_ocr_hqmax.txt` (FAIL)
- `S1-S3` / `two_column_smash`: 5th: Westwood Jolie, owned by Alice Reynolds
- `S1-S3` / `two_column_smash`: 6th: Blackland Sheena, owned by Lloyd & Shirley
- `S1-S3` / `two_column_smash`: 1st: Foxwarren Raider, owned by Joann Vinelli
- `S1-S3` / `two_column_smash`: 2nd: Show-Me Bernard of Heartstone, owned by Lynn Jerome
- `S1-S3` / `two_column_smash`: 6th: R.A. Bandit, owned by Mike & Betty Bilinski
- `S1-S3` / `two_column_smash`: 1st: Foxnorten Tyke of Meadowlake, owned by Karen Reavis
- `S1-S3` / `two_column_smash`: 1st: Reyem's the Mervster, owned by Ken Meyer
- `S1-S3` / `two_column_smash`: 5th: Blackland Bonnie, owned by Lloyd & Shirley Cox
- `S1-S3` / `two_column_smash`: 6th: Gabriel, owned by Barbara & Tony Ziehler
- `S1-S3` / `two_column_smash`: 1st: Hi-Flashun Alfa Romeo, owned by Rob Mokry
- `S1-S3` / `two_column_smash`: 1st: Seaview Shag, owned by Didi Gough
- `S1-S3` / `two_column_smash`: 6th: Blackland Matilda of Gunsmoke, owned by Kenneth & Rose Cox

### `Document_2026-11-04_152834_ocr_hqmax.txt` (FAIL)
- `S1-S3` / `two_column_smash`: 5th: Windermere Witewitch, owned by Paul Hartman & Karen McCarthy
- `S1-S3` / `two_column_smash`: 6th: Farmcliff Tackle, owned by Megan Johnson
- `S1-S3` / `two_column_smash`: 1st: Scotty Joe, owned by Diane Travers
- `S1-S3` / `two_column_smash`: 2nd: Farmcliff Donny, owned by Bob Franklin
- `S1-S3` / `two_column_smash`: 3rd: Courtland Trevor, owned by Joseph Jankowski & Kellyann Morander
- `S1-S3` / `two_column_smash`: 1st: Brandy of Rednek, owned by Boyd K. Jones
- `S1-S3` / `two_column_smash`: 2nd: Lunstarr Jackie of Flying "A", owned by Lee Jean Stafford
- `S1-S3` / `two_column_smash`: 3rd: Wesworld Sheila, owned by Mark Shaw
- `S1-S3` / `two_column_smash`: 1st: Lost Creek Tango, owned by Debbie McWilliams
- `S1-S3` / `two_column_smash`: 2nd: Eagles Nest Chase, owned by Marlow & Joanne Jurisch
- `S1-S3` / `two_column_smash`: 1st: Lunstarr Jackie of Flying "A", owned by Lee Jean Stafford
- `S1-S3` / `two_column_smash`: 2nd: Wesworld Sheila, owned by Mark Shaw

### `Document_2026-11-04_153208_ocr_hqmax.txt` (FAIL)
- `S1-S3` / `two_column_smash`: 1st: The Larches Knot Again, owned by Donald & Joan LaPlace
- `S1-S3` / `two_column_smash`: 5th: Farmliff Justin of Courtland, owned by Joseph Jankowski
- `S1-S3` / `two_column_smash`: 6th: Sass 'N Dash Peck's Dare Rett, owned by Sara Lou Peck
- `S1-S3` / `two_column_smash`: 1st: Farmcliff Spencer, owned by Bob & Genie Franklin
- `S1-S3` / `two_column_smash`: 1st: Undercover Cindy, owned by Lynn May Measles
- `S1-S3` / `two_column_smash`: 2nd: Ridgerunner Olivia, owned by Janet Nugent
- `S1-S3` / `two_column_smash`: 1st: Hopdiggity Raider, owned by Liz Littman
- `S1-S3` / `two_column_smash`: 2nd: Lost Creeks Merlin, owned by Debbie McWilliams
