# B6b cleanup + ingest audit — 1999

Catalog: `_OCR_CLEANUP_CATALOG_HANDOFF.md`
Volumes: 6  cleaned=6  PASS=0  WARN=0  FAIL=6
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
| FAIL | True | 27 | 0 | C1×27 | `1999 Vol I, pt 1_ocr_hqmax.txt` |
| FAIL | True | 18 | 0 | C1×18 | `1999 Vol I, pt 2_ocr_hqmax.txt` |
| FAIL | True | 22 | 0 | C1×22 | `1999 Vol II, pt 1_ocr_hqmax.txt` |
| FAIL | True | 15 | 0 | C1×15 | `1999 Vol II, pt 2_ocr_hqmax.txt` |
| FAIL | True | 2 | 0 | C1×2 | `1999 Vol III, pt 1_ocr_hqmax.txt` |
| FAIL | True | 32 | 0 | C1×32 | `1999 Vol III, pt 2_ocr_hqmax.txt` |

## Sample residual hits (after cleanup)

### `1999 Vol I, pt 1_ocr_hqmax.txt` (FAIL)
- `C1` / `3rd_then_5th_no_4`: 3rd: Lickity Split Nifty, owned by Darlene Mclnnes
5th: Sow's Ear See Bee, owned by John & Lisa Renfro
- `C1` / `3rd_then_5th_no_4`: 3rd: Nick Adams
5th: Matthew Wolosyn
- `C1` / `3rd_then_5th_no_4`: 3rd: Ranch House Weezer, owned by Scott & Dana Alguire
5th: Rainbow Pride Benzo, owned by Van der Heym/Trembly
- `C1` / `3rd_then_5th_no_4`: 3rd: Rustler's Roose Energizer, owned by Jackie Plaskowitz
5th: Monroe, owned by Karen Schultz
- `C1` / `3rd_then_5th_no_4`: 3rd: Hart Farms Elijah Blu, owned by Dan & Cindy McClary
5th: Arrowhead Annawake, owned by Cheryl Simmons
- `C1` / `3rd_then_5th_no_4`: 3rd: Southernmost Sami D'Shark, owned by Jackie McLain
5th: Westmorland Sampson, owned by Cedric & Sharon Lavender
- `C1` / `3rd_then_5th_no_4`: 3rd: Luck, owned by Joe Shapiro
5th: Hart Farms Elijah Blu, owned by Dan & Cindy McClary
- `C1` / `3rd_then_5th_no_4`: 3rd: Belgrove Jazz, owned by Fred Barnes
5th: Rampage, owned by Gayle Jennings
- `C1` / `1st_then_3rd_no_2`: 1st: Sims Run Figaro, owned by Amy & Wellsley Donofrio
3rd: Slat Valley Top Kat, owned by Richard & Jan Finnerty
- `C1` / `1st_then_3rd_no_2`: 1st: 5h: Stablemate English Muffin, owned by Diana Cookingham
3rd: Westgate Molly, owned by Elizabeth Jordan
- `C1` / `place_rank_gap`:  | 1th then 3th | 3rd: Slat Valley Top Kat, owned by Richard & Jan Finnerty
- `C1` / `place_rank_gap`:  | 1th then 3th | 3rd: Westgate Molly, owned by Elizabeth Jordan

### `1999 Vol I, pt 2_ocr_hqmax.txt` (FAIL)
- `C1` / `3rd_then_5th_no_4`: 3rd: Arrowhead Norma Sue, owned by Jack & Laurie Phillips
5th: Edison Dixie Pixie, owned by Russell & Barbara Gilford
- `C1` / `3rd_then_5th_no_4`: 3rd: Zacchaus, owned by Donna Brown
5th: Bright Stars Hot Shot, owned by Judy Kuykendall
- `C1` / `3rd_then_5th_no_4`: 3rd: Autumnwood Shasta, owned by Dave & Cathy Eick
5th: Gills Creek Scout, owned by J.Shapiro/B.Kelley
- `C1` / `3rd_then_5th_no_4`: 3rd: Seagull Beetle Bailey, owned by Buddy & Cindi Anderson
5th: Lost Creek Doty, owned by P.Brock/L.M.Measles
- `C1` / `3rd_then_5th_no_4`: 3rd: Oliver, owned by Bryan Clyburn
5th: Margaret, owned by Meghan Marcus
- `C1` / `1st_then_3rd_no_2`: 1st: Shamplon: Sait Valley Kallie, owned by Richard & Jan Finnerty
3rd: Lost Creek Blossom, owned by Greg Boyland
- `C1` / `place_rank_gap`: Pups. 9 un to 12 monthe 10 un to 1 | 1th then 6th | 6th: Betti Jean, owned by Joe & Linda Hosmer
- `C1` / `place_rank_gap`: Bronze Medallion                                             | 2th then 4th | 4th:      Briarpatch Bourbon, owned by Jane Griffin
- `C1` / `place_rank_gap`: Youth Handling Agility, On Lead                       Entrie | 1th then 4th | 4th: Nickels, handled by Randi Lavender
- `C1` / `place_rank_gap`:  | 3th then 5th | 5th: Edison Dixie Pixie, owned by Russell & Barbara Gilford
- `C1` / `place_rank_gap`: Dogs, 1 yr & older, 10 up to 122", smooth            Entries | 3th then 5th | 5th: Bright Stars Hot Shot, owned by Judy Kuykendall
- `C1` / `place_rank_gap`: Bitches, 1 yr & older, 12% up to 15", smooth         Entries | 3th then 5th | 5th: Gills Creek Scout, owned by J.Shapiro/B.Kelley

### `1999 Vol II, pt 1_ocr_hqmax.txt` (FAIL)
- `C1` / `3rd_then_5th_no_4`: 3rd: R.A. Charley, owned by C. Ortiz/T. Hallman
5th: Scrappy Doo, owned by Mike & Sharon Roberts
- `C1` / `3rd_then_5th_no_4`: 3rd: Kenswick Pistol, owned by Sandy McElearney
5th: Killare Dearly, owned by Wendy Wynne-Willson
- `C1` / `3rd_then_5th_no_4`: 3rd: Andlin What A Joy, owned by George Anderson
5th: Treetop Buckeye, owned by Catherine Brown
- `C1` / `2nd_then_4th_no_3`: 2nd: Mac's Jacks Waldo Pepper, owned by Robert MacFarland
4th: Buster, owned by Russell & Mary Pollock
- `C1` / `2nd_then_4th_no_3`: 2nd: Sugar Creek Twigs, owned by Eddie & Jeanette Carter
4th: Brookmill Farms Bracken, owned by Martha LeRoy
- `C1` / `2nd_then_4th_no_3`: 2nd: Arlins Dill Weed, owned by Alison Linstrum
4th: High Mountain Echo, owned by Alison Linstrum
- `C1` / `1st_then_3rd_no_2`: 1st: Obajean, owned by Ruth Evans
3rd: Pip, owned by Eric Bartlett
- `C1` / `1st_then_3rd_no_2`: 1st: Big Sky Summit, owned by Dan & Karen Kinsley
3rd: Sass 'N Dash Molly, owned by Mary Webb
- `C1` / `place_rank_gap`: Youth Handler                                                | 3th then 6th | 6th: Austin Anthony
- `C1` / `place_rank_gap`: Neutered Adult Dog                                           | 1th then 3th | 3rd: Milo, owned by Philip DePalo
- `C1` / `place_rank_gap`:  | 1th then 3th | 3rd: Pip, owned by Eric Bartlett
- `C1` / `place_rank_gap`: Bitches, 1 yr & older, over 12 1/2-15" Entries: 17 | 3th then 5th | 5th: Scrappy Doo, owned by Mike & Sharon Roberts

### `1999 Vol II, pt 2_ocr_hqmax.txt` (FAIL)
- `C1` / `3rd_then_5th_no_4`: 3rd: Old Glory Heavy Chevy, owned by Sandy Brown
5th: Churchview Tobie, owned by Sandy Brown
- `C1` / `3rd_then_5th_no_4`: 3rd: Morgan Hill Paisley, owned by Don & Gail Stock
5th: Baybriar Cinder, owned by Jeanette Hutchison
- `C1` / `3rd_then_5th_no_4`: 3rd: Fox Run Ditto, owned by J. Robin/S. Ferber
5th: Glen Coe Murray, owned by Holly Cipriano
- `C1` / `3rd_then_5th_no_4`: 3rd: Farmstead Freddie, owned by Sal & Lynn Cianci
5th: Maxwell, owned by Ted Landers
- `C1` / `1st_then_3rd_no_2`: 1st: Farmington Charlie, owned by Paul Summers
3rd: Big Sky Annie, owned by Doug & Sue Tack
- `C1` / `place_rank_gap`: Veteran, 6 years & older                                     | 1th then 3th | 3rd: Big Sky Annie, owned by Doug & Sue Tack
- `C1` / `place_rank_gap`: Bitches, 1 yr & older, over 1214-15" Entries: 21 | 3th then 5th | 5th: Churchview Tobie, owned by Sandy Brown
- `C1` / `place_rank_gap`: Bitch Pups, 4 up to 6 months, smooth                  Entrie | 3th then 5th | 5th: Baybriar Cinder, owned by Jeanette Hutchison
- `C1` / `place_rank_gap`: Novice Adult                                                 | 3th then 5th | 5th: Russellville Sport, owned by Rob Fiss
- `C1` / `place_rank_gap`: Suitability To Red Fox                                    En | 2th then 4th | 4th: Lost Acres Louise, owned by Laura Harakaly
- `C1` / `place_rank_gap`: New York Bred                                                | 3th then 5th | 5th: Glen Coe Murray, owned by Holly Cipriano
- `C1` / `place_rank_gap`: Suitability to Raccoon/Badger                              E | 3th then 5th | 5th: Maxwell, owned by Ted Landers

### `1999 Vol III, pt 1_ocr_hqmax.txt` (FAIL)
- `C1` / `3rd_then_5th_no_4`: 3rd: Colton Ricci Rocket, owned by Anita Phillips
5th: Brown's Valley Mustang Sally, owned by Ann Wendland
- `C1` / `place_rank_gap`:  | 3th then 5th | 5th: Brown's Valley Mustang Sally, owned by Ann Wendland

### `1999 Vol III, pt 2_ocr_hqmax.txt` (FAIL)
- `C1` / `3rd_then_5th_no_4`: 3rd: Monti, owned by Robert McCaslin
5th: Hillsdale Korki, owned by Judith Blackman
- `C1` / `3rd_then_5th_no_4`: 3rd: Farrier Point Racer X, owned by Paul & Tammie Davis
5th: Mirabelle, owned by Sally Haney
- `C1` / `3rd_then_5th_no_4`: 3rd: Sakeondre Jiminy Cricket, owned by Dale & Cathy Larson
5th: Hillside Josie, owned by Karen Vernon
- `C1` / `3rd_then_5th_no_4`: 3rd: High Range Riley, owned by David & Susan Welch
5th: Windy Hollow Martini, owned by Jerrilyn Could
- `C1` / `3rd_then_5th_no_4`: 3rd: Foxglove Marcel Marceau, handled by Michael Steinmetz
5th: North Fork Maggie, owned by Al & Karen Cooper
- `C1` / `2nd_then_4th_no_3`: 2nd: Mousemoor Sweet Pea, owned by Melinda Koch
4th: Andlin Sandy, owned by Samantha Cather
- `C1` / `2nd_then_4th_no_3`: 2nd: Heaven Hill Ruby, owned by R.Vega/L.Carson
4th: Ripley, owned by Doug & Noreen Loranger
- `C1` / `2nd_then_4th_no_3`: 2nd: Lost Acres Louise, handled by James Harakaly
4th: Farli, owned by Terri Wilson
- `C1` / `1st_then_3rd_no_2`: 1st: Penelope, owned by Mike & Karen DiBernardo
3rd: Ziggy, owned by Tony Armer
- `C1` / `1st_then_3rd_no_2`: 1st: Sneaky Sid Lou, owned by Julie Grim
3rd: Farrier Point Racer X, owned by Paul & Tammie Davis
- `C1` / `place_rank_gap`:  | 1th then 3th | 3rd: Ziggy, owned by Tony Armer
- `C1` / `place_rank_gap`: Pups, 9 up to 12 months, 10 up to 12 1/2" Entries: 1 | 1th then 6th | 6th: Leap-N-Jack Spunky, owned by Seth McCutchin
