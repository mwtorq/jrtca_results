# B6b cleanup + ingest audit — 1996

Catalog: `_OCR_CLEANUP_CATALOG_HANDOFF.md`
Volumes: 30  cleaned=29  PASS=11  WARN=0  FAIL=19
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
| PASS | True | 0 | 0 | — | `1996 Vol 1 pg 111-160 back reversed_ocr_hqmax.txt` |
| FAIL | True | 7 | 0 | C1×7 | `1996 Vol 1 pg 111-160 back_ocr_hqmax.txt` |
| FAIL | True | 2 | 0 | C1×2 | `1996 Vol 1 pg 111-160 front_ocr_hqmax.txt` |
| FAIL | True | 1 | 0 | C1×1 | `1996 Vol 1 pg 161-178 back reversed_ocr_hqmax.txt` |
| PASS | False | 0 | 0 | — | `1996 Vol 1 pg 161-178 back_ocr_hqmax.txt` |
| FAIL | True | 1 | 0 | C1×1 | `1996 Vol 1 pg 161-178 front_ocr_hqmax.txt` |
| FAIL | True | 2 | 0 | C1×2 | `1996 Vol 1 pg 21-60 back reversed_ocr_hqmax.txt` |
| FAIL | True | 4 | 0 | C1×4 | `1996 Vol 1 pg 21-60 back_ocr_hqmax.txt` |
| PASS | True | 0 | 0 | — | `1996 Vol 1 pg 21-60 front_ocr_hqmax.txt` |
| FAIL | True | 16 | 0 | C1×16 | `1996 Vol 1 pg 61-110 back reversed_ocr_hqmax.txt` |
| FAIL | True | 9 | 0 | C1×9 | `1996 Vol 1 pg 61-110 back_ocr_hqmax.txt` |
| FAIL | True | 23 | 0 | C1×22,S1-S3×1 | `1996 Vol 1 pg 61-110 front_ocr_hqmax.txt` |
| FAIL | True | 5 | 0 | C1×5 | `1996 Vol II pg 163-220 back reversed_ocr_hqmax.txt` |
| PASS | True | 0 | 0 | — | `1996 Vol II pg 163-220 back_ocr_hqmax.txt` |
| FAIL | True | 8 | 0 | C1×8 | `1996 Vol II pg 163-220 front_ocr_hqmax.txt` |
| FAIL | True | 5 | 0 | C1×5 | `1996 Vol II pg 23-92 back reversed_ocr_hqmax.txt` |
| PASS | True | 0 | 0 | — | `1996 Vol II pg 23-92 back_ocr_hqmax.txt` |
| FAIL | True | 6 | 0 | C1×6 | `1996 Vol II pg 23-92 front (missing 1 pgs)_ocr_hqmax.txt` |
| FAIL | True | 1 | 0 | C1×1 | `1996 Vol II pg 23-92 front (missing 2 pgs)_ocr_hqmax.txt` |
| FAIL | True | 5 | 0 | C1×5 | `1996 Vol II pg 23-92 front_ocr_hqmax.txt` |
| FAIL | True | 4 | 0 | C1×4 | `1996 Vol II pg 93-162 back reversed_ocr_hqmax.txt` |
| PASS | True | 0 | 0 | — | `1996 Vol II pg 93-162 back_ocr_hqmax.txt` |
| FAIL | True | 12 | 0 | C1×12 | `1996 Vol II pg 93-162 front_ocr_hqmax.txt` |
| PASS | True | 0 | 0 | — | `Document_2026-11-04_144208_ocr_hqmax.txt` |
| FAIL | True | 1 | 0 | C1×1 | `Document_2026-11-04_144530_ocr_hqmax.txt` |
| PASS | True | 0 | 0 | — | `Document_2026-11-04_145355_ocr_hqmax.txt` |
| PASS | True | 0 | 0 | — | `Document_2026-11-04_145925_ocr_hqmax.txt` |
| PASS | True | 0 | 0 | — | `Document_2026-11-04_151058_ocr_hqmax.txt` |
| PASS | True | 0 | 0 | — | `Document_2026-11-04_152834_ocr_hqmax.txt` |
| FAIL | True | 2 | 0 | C1×2 | `Document_2026-11-04_153208_ocr_hqmax.txt` |

## Sample residual hits (after cleanup)

### `1996 Vol 1 pg 111-160 back_ocr_hqmax.txt` (FAIL)
- `C1` / `1st_then_3rd_no_2`: 1st: Prestwick Belle, owned by Sally Yancey & Christi Tatum
3rd: Briarpatch Brash, owned by Jane Griffin
- `C1` / `1st_then_3rd_no_2`: 1st: The Hollow York, owned by The Hollow Terriers
3rd: Hillsdale Hanmer, owned by Lynn Eshleman
- `C1` / `place_rank_gap`: Novice, On Leal                                              | 2th then 5th | 5th: Six Pack, owned by Ken & Penny Baker
- `C1` / `place_rank_gap`: Open Class Entries: 6 | 1th then 3th | 3rd: Briarpatch Brash, owned by Jane Griffin
- `C1` / `place_rank_gap`: Open Class Entries: 6 | 3th then 5th | 5th: Oakfield Annie, owned by Albert & Heather Dickau
- `C1` / `place_rank_gap`: Bitch Pups, 6 up b 12 months, 10-12 1/2" Entries: 5 | 2th then 4th | 4th: Blue Moon Ema, owned by Anne Davis
- `C1` / `place_rank_gap`: Dog Pups, 4 up te 6 months | 1th then 3th | 3rd: Hillsdale Hanmer, owned by Lynn Eshleman

### `1996 Vol 1 pg 111-160 front_ocr_hqmax.txt` (FAIL)
- `C1` / `place_rank_gap`: Dogs, 1 yr & over, 12 1/2-15", smooth                        | 1th then 3th | 3rd: Briarpatch Snapshot of Arrow Fork, owned by Clint Clayton
- `C1` / `place_rank_gap`: Bitch Pups, 6 up to 9 months, r/br                           | 1th then 3th | 3rd: Larkswood Kellie, owned by Eastlake Terriers

### `1996 Vol 1 pg 161-178 back reversed_ocr_hqmax.txt` (FAIL)
- `C1` / `place_rank_gap`:  | 2th then 4th | 4th: Windy Viev Questor, owned by William & Guy O'Brien

### `1996 Vol 1 pg 161-178 front_ocr_hqmax.txt` (FAIL)
- `C1` / `place_rank_gap`: Starters Agility I, Off Lead                                 | 3th then 6th | 6th: Ash Creek Ghillie, owned by Marty & Teresa Gollteib

### `1996 Vol 1 pg 21-60 back reversed_ocr_hqmax.txt` (FAIL)
- `C1` / `1st_then_3rd_no_2`: 1st: FoxwarrenRaider, owned by Joann Vinelli
3rd: Show-Me Bernard of Heartstone, owned by Lynn Jerome
- `C1` / `place_rank_gap`: 9 months, 10-12 1/2" Entries: 0 | 1th then 3th | 3rd: Show-Me Bernard of Heartstone, owned by Lynn Jerome

### `1996 Vol 1 pg 21-60 back_ocr_hqmax.txt` (FAIL)
- `C1` / `1st_then_3rd_no_2`: 1st: Blackland Tirbo, owned by Doris Baylor
3rd: Bonnie Bee, owned by Gavin Corn
- `C1` / `place_rank_gap`: Dog Pups, 9 up to 12 months, r/lbr                           | 3th then 6th | 6th: Pine Hill Jeina, owned by Lisa Drinkwater
- `C1` / `place_rank_gap`: Advanced Certificate Class                                   | 2th then 6th | 6th: Tortilla Fiat Ivy, owned by Mick and Jean Kieselburg
- `C1` / `place_rank_gap`: Open Adults | 1th then 3th | 3rd: Bonnie Bee, owned by Gavin Corn

### `1996 Vol 1 pg 61-110 back reversed_ocr_hqmax.txt` (FAIL)
- `C1` / `3rd_then_5th_no_4`: 3rd: Pully, owned by Sally Gay
5th: White Rose Gingersnap, owned by Tabby Shury
- `C1` / `1st_then_3rd_no_2`: 1st: Weavwoor Sprout, owned by Cheryl Weaver
3rd: White Gate Bracelet, owned by Jeanne Huston
- `C1` / `1st_then_3rd_no_2`: 1st: 0, owned by Janet Nugemt
3rd: Bluebonnet {naffle, owned by Judy Beard
- `C1` / `1st_then_3rd_no_2`: 1st: Kensington Jaylee of Paradise, owned by Tina Sales
3rd: Maggie, owned by Kerry Bishop
- `C1` / `1st_then_3rd_no_2`: 1st: Paxton Nick of Lost Creek, owned by Debbie McWilliams
3rd: Broken Arrow Spooke, owned by Phillip & Lori Aaron
- `C1` / `place_rank_gap`:  | 5th then 9th | 9th: Cottonwood Too Quick, owned by Ben Seago
- `C1` / `place_rank_gap`: Novice Adults | 1th then 3th | 3rd: White Gate Bracelet, owned by Jeanne Huston
- `C1` / `place_rank_gap`: Bitch Pups, 6 up to £2 months, 10-12 1/2" Entries: 16 | 5th then 9th | 9th: Duchess of Coliwater, owned by Karen & Robert Seals
- `C1` / `place_rank_gap`: Bitch Pups, 6 up to 12 months, 10-12 112°                    | 5th then 9th | 9th: Button Tep Stinger, owned by Deborah Calloway
- `C1` / `place_rank_gap`: Dog Pups, 6 up tc 12 months, 12 1/2-15" | 2th then 4th | 4th: Petey, owned by Raquel Warner
- `C1` / `place_rank_gap`: Bitch Pups, 4 w to 6 months, r/br                            | 5th then 9th | 9th: Button Top Molly, owned by Bobby Duty
- `C1` / `place_rank_gap`: Pre-Novice Puppits                                           | 1th then 3th | 3rd: Bluebonnet {naffle, owned by Judy Beard

### `1996 Vol 1 pg 61-110 back_ocr_hqmax.txt` (FAIL)
- `C1` / `1st_then_3rd_no_2`: 1st: 0, owned by Janet Nugemt
3rd: Bluebonnet Snaffle, owned by Judy Beard
- `C1` / `1st_then_3rd_no_2`: 1st: Kensington Jaylee of Paradise, owned by Tina Sales
3rd: Maggie, owned by Kerry Bishop
- `C1` / `1st_then_3rd_no_2`: 1st: Lacey, owned by Margaret Stricklandond: Red Oak Blue Bonnet
3rd: Crabtree Tally, owned by Rusty Womack
- `C1` / `1st_then_3rd_no_2`: 1st: Weavwoot Sprout, owned by Cheryl Weaver
3rd: White Gate Bracelet, owned by Jeanne Huston
- `C1` / `place_rank_gap`: Pre-Novice Puppits                                           | 1th then 3th | 3rd: Bluebonnet Snaffle, owned by Judy Beard
- `C1` / `place_rank_gap`: Novice Adults                                                | 1th then 3th | 3rd: Maggie, owned by Kerry Bishop
- `C1` / `place_rank_gap`:  | 1th then 7th | 7nd: Lost CreekSable, owned by Debbie McWilliams
- `C1` / `place_rank_gap`: Bitch Pups, 6 up to 12 months, 10-12 1/2" | 1th then 3th | 3rd: Crabtree Tally, owned by Rusty Womack

### `1996 Vol 1 pg 61-110 front_ocr_hqmax.txt` (FAIL)
- `C1` / `3rd_then_5th_no_4`: 3rd: Three Oaks Double D of Bili Brook, owned by Billy Shores
5th: Turbo of Ball Creek, owned by Ronnie & Wanda Dyer
- `C1` / `3rd_then_5th_no_4`: 3rd: Three Oaksth: Sukhoi of Good T, owned by Steve Spruill
5th: Sadie, owned by Chris Advani
- `C1` / `3rd_then_5th_no_4`: 3rd: Will-O-Moor Rex, owned by Kim Wentz
5th: Arlins Troy Built Riley, owned by Alison Linstrum
- `C1` / `3rd_then_5th_no_4`: 3rd: Farmcliff Becky, owned by Bob Franklin
5th: The Hollow Fioana, owned by Missy Kulback
- `C1` / `2nd_then_4th_no_3`: 2nd: Frisbee, owned by Dawn Pierson
4th: Petey, owned by Kathy Hunter
- `C1` / `1st_then_3rd_no_2`: 1st: S Rimshot, owned by Glenda Lewis
3rd: Three Oaks Joh, owned by Jason Echols
- `C1` / `1st_then_3rd_no_2`: 1st: Sarah Harsh
3rd: Luke Hitt
- `C1` / `1st_then_3rd_no_2`: 1st: Camelot Derby of Marksworth, owned by Terry Clower
3rd: Whirlwind Polo, owned by Terry Wellman
- `C1` / `1st_then_3rd_no_2`: 1st: Long Hope Mickey, owned by Bob Franklin
3rd: Courtland Moo Cow, owned by Joe Jankows
- `C1` / `1st_then_3rd_no_2`: 1st: Farmcliff Sugar, owned by Bob Franklin
3rd: Farmcliff Becky, owned by Bob Franklin
- `C1` / `place_rank_gap`: Dogs, 1 yr & over, 12 1/2-15", smooth                        | 3th then 5th | 5th: Turbo of Ball Creek, owned by Ronnie & Wanda Dyer
- `C1` / `place_rank_gap`:  | 2th then 5th | 5th:   Susie, owned by Donna Shamp

### `1996 Vol II pg 163-220 back reversed_ocr_hqmax.txt` (FAIL)
- `C1` / `1st_then_3rd_no_2`: 1st: Foxy Rosy, owned by David & Vincent Stephens
3rd: R.A. Annie, owned by Charline Williams
- `C1` / `1st_then_3rd_no_2`: 1st: Disqualifiedond: Wesmorlard Kallie, owned by Kirk Dickinson
3rd: RavenswooRed Riddle, owned by Julie Conner
- `C1` / `place_rank_gap`: Bitches, 1 yr & over 12 1/2-15" | 1th then 3th | 3rd: R.A. Annie, owned by Charline Williams
- `C1` / `place_rank_gap`: Novice, On Lead                                              | 5th then 9th | 9th: Sir Winston, owned by Charles & Sally Hickey
- `C1` / `place_rank_gap`: Bitches, 1 yr & orer, 10-12 1/2", smooth                     | 1th then 3th | 3rd: RavenswooRed Riddle, owned by Julie Conner

### `1996 Vol II pg 163-220 front_ocr_hqmax.txt` (FAIL)
- `C1` / `3rd_then_5th_no_4`: 3rd: Moonrunner Courtland My Keeper, owned by Joseph Clay Ackerman
5th: Violet, owned by Joan Valuzzo & William Bisch
- `C1` / `2nd_then_4th_no_3`: 2nd: Farmstead Keswick Itch, owned by Sandy Judy
4th: Hillside Kismit, owned by Laura Harakaly
- `C1` / `place_rank_gap`: Entries: 7 | 1th then 5th | 5th: Undercover Agent Newton, owned by Lisa Donovan
- `C1` / `place_rank_gap`: Judges: CONFORMATION Nancy Breakstone, DiVISION Conformation | 1th then 4th | 4th: Farmstead Jet, owned by Judy Galterio
- `C1` / `place_rank_gap`: Bitch 1st: Farmcliff Pups, 4 up Holland to 6 months of North | 2th then 4th | 4th: Hillside Kismit, owned by Laura Harakaly
- `C1` / `place_rank_gap`: Novice 1st: The - Folly Kismet, owned by Allison Linstrum En | 3th then 5th | 5th: Violet, owned by Joan Valuzzo & William Bisch
- `C1` / `place_rank_gap`: Dog Pups, 6 up to 9 months, smooth Entries: 4 | 4th then 8th | 8th: Pistol, owned by Sandy LaMantia & Joel McElearney & Sandra Ferber
- `C1` / `place_rank_gap`: Dog Pups, 9 up to 12 months, r/br                            | 4th then 6th | 6th: Green Acres Cotton Eyed Joe, owned by Michelle

### `1996 Vol II pg 23-92 back reversed_ocr_hqmax.txt` (FAIL)
- `C1` / `2nd_then_4th_no_3`: 2nd: Romney Kaz, owned by K. Hunter & J. Hughes
4th: Bangers ol Blue Barnes, owned by Gary LaValley
- `C1` / `place_rank_gap`: Youth Agility                                                | 1th then 6th | 6th: Farmstead Bubbles, owned by Judy Galterio
- `C1` / `place_rank_gap`: Advanced, On lead | 2th then 4th | 4th: Bangers ol Blue Barnes, owned by Gary LaValley
- `C1` / `place_rank_gap`: Open Adults                                                  | 5th then 8th | 8th: TJ Farm Chase, owned by Cassandra Appleman
- `C1` / `place_rank_gap`: Brood Bitch &Produce | 3th then 5th | 5th: BriarpatchMohawk, owned by Chuck & Diana Hufnagel

### `1996 Vol II pg 23-92 front (missing 1 pgs)_ocr_hqmax.txt` (FAIL)
- `C1` / `1st_then_3rd_no_2`: 1st: Amanda Bjorkland
3rd: Corey Kubber
- `C1` / `1st_then_3rd_no_2`: 1st: Ashley Tomberg
3rd: Robert Smith
- `C1` / `place_rank_gap`: New York State Bred                                          | 2th then 5th | 5th: Farmcliff Elsie, owned by Bob Franklin & Chuck Shobert
- `C1` / `place_rank_gap`: Child Handler | 1th then 3th | 3rd: Corey Kubber
- `C1` / `place_rank_gap`: Junior Handler                                       Eitries | 1th then 3th | 3rd: Robert Smith
- `C1` / `place_rank_gap`: Agility II, Off Lead                                         | 2th then 5th | 5th: Lightning, owned by Margaret & David Ashe

### `1996 Vol II pg 23-92 front (missing 2 pgs)_ocr_hqmax.txt` (FAIL)
- `C1` / `place_rank_gap`: New York State Bred                                          | 2th then 5th | 5th: Farmcliff Elsie, owned by Bob Franklin & Chuck Shobert

### `1996 Vol II pg 23-92 front_ocr_hqmax.txt` (FAIL)
- `C1` / `3rd_then_5th_no_4`: 3rd: Scooter, owned by Ben & Candace Wright
5th: Fox Tale Temo, owned by Theresa & Charle Gadoury
- `C1` / `place_rank_gap`: New York State Bred                                          | 2th then 5th | 5th: Farmcliff Elsie, owned by Bob Franklin & Chuck Shobert
- `C1` / `place_rank_gap`: Bred by Exhibitor Bitch Entri:s: 10 | 5th then 8th | 8th: Farmcliff Elsie, owned by Bob Franklin & Chuck Schobert
- `C1` / `place_rank_gap`: Pups, 9 up to 12 months, 10-12 1/2" Entries: 0 | 3th then 5th | 5th: Fox Tale Temo, owned by Theresa & Charle Gadoury
- `C1` / `place_rank_gap`: Advanced, On Lead – Entries: 2 | 3th then 6th | 6th: K.C, owned by Theresa Gadoury

### `1996 Vol II pg 93-162 back reversed_ocr_hqmax.txt` (FAIL)
- `C1` / `1st_then_3rd_no_2`: 1st: Lost Acres Revlon of Sow's Ear, owned by Karen McCarthy & Paul Hartman
3rd: Leewinds Celeste, owned by Terri & Richard Lee
- `C1` / `place_rank_gap`: Bitches 1 yr &over, 12 1/2-15", smooth – Entries: 0 | 1th then 3th | 3rd: Leewinds Celeste, owned by Terri & Richard Lee
- `C1` / `place_rank_gap`: Puppy Champitnship                                           | 3th then 6th | 6th: Redstone Rocket, owned by Kris Fierst
- `C1` / `place_rank_gap`:  | 3th then 5th | 5th: Farmcliff T:ddy, owned by Karin McKnight

### `1996 Vol II pg 93-162 front_ocr_hqmax.txt` (FAIL)
- `C1` / `3rd_then_5th_no_4`: 3rd: The Larches Knot Again, owned by Joan & Donald LaPlace
5th: Desert Fox Jerry Garcia, owned by Twila Decker
- `C1` / `3rd_then_5th_no_4`: 3rd: Riverview Calvin, owned by Karen Vernon
5th: Hillside Chaz, owned by Doug & Noreen Loranger
- `C1` / `2nd_then_4th_no_3`: 2nd: Megan Johnson
4th: Alex Loranger, owned by Christina Wagner
- `C1` / `2nd_then_4th_no_3`: 2nd: RuffN Tumble Grizzle, owned by Donald Tait
4th: Golden Hills Rush, owned by Jeff & Connie McKee
- `C1` / `place_rank_gap`: Bitch Pups, 9 up to 12 months, r/br                          | 3th then 5th | 5th: Jubilee Jones of Brackenridge, owned by Marilyn Johann
- `C1` / `place_rank_gap`: Dog Pups, 4 up to 6 months – Entries: 13 | 3th then 5th | 5th: Desert Fox Jerry Garcia, owned by Twila Decker
- `C1` / `place_rank_gap`: Junior Handler – Entries: 6 | 2th then 4th | 4th: Alex Loranger, owned by Christina Wagner
- `C1` / `place_rank_gap`: American Bred – Entries: 8 | 3th then 5th | 5th: Hillside Chaz, owned by Doug & Noreen Loranger
- `C1` / `place_rank_gap`: Dogs, 1 yr & over, 12 1/2-15", smooth – Entries: 7 | 2th then 4th | 4th: Golden Hills Rush, owned by Jeff & Connie McKee
- `C1` / `place_rank_gap`: Open Class Entries: 2 | 2th then 5th | 5th: Fenton's Powsheik Pirate, owned by Dick & Nancy Fenton
- `C1` / `place_rank_gap`:  | 4th then 6th | 6th: Joyful Noise Jz, owned by Judy Tuthill
- `C1` / `place_rank_gap`:  | 2th then 6th | 6th: Farmcliff Tackle, owned by Megan Johnson

### `Document_2026-11-04_144530_ocr_hqmax.txt` (FAIL)
- `C1` / `place_rank_gap`:  | 2th then 5th | 5th: Susie, owned by Donna Shamp

### `Document_2026-11-04_153208_ocr_hqmax.txt` (FAIL)
- `C1` / `place_rank_gap`: Dog Pups, 9 up to 12 months, r/br                            | 4th then 6th | 6th: Green Acres Cotton Eyed Joe, owned by Mike & Debbie Fulton
- `C1` / `place_rank_gap`: Sub Novice                                                   | 2th then 5th | 5th: Baybriar Tucker, owned by Jeannette Hutchison
