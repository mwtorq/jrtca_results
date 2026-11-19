# B6b cleanup + ingest audit — 2000

Catalog: `_OCR_CLEANUP_CATALOG_HANDOFF.md`
Volumes: 5  cleaned=5  PASS=0  WARN=0  FAIL=5
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
| FAIL | True | 57 | 0 | C1×57 | `2000 Vol I_ocr_hqmax.txt` |
| FAIL | True | 46 | 0 | C1×46 | `2000 Vol II_ocr_hqmax.txt` |
| FAIL | True | 35 | 0 | C1×35 | `2000 vol 3 pt 1_ocr_hqmax.txt` |
| FAIL | True | 43 | 0 | C1×43 | `2000 Vol III pt 1_ocr_hqmax.txt` |
| FAIL | True | 3 | 0 | C1×3 | `2000 Vol III pt 2_ocr_hqmax.txt` |

## Sample residual hits (after cleanup)

### `2000 Vol I_ocr_hqmax.txt` (FAIL)
- `C1` / `3rd_then_5th_no_4`: 3rd: Hart Farms Ruth, owned by Cheryl Hart
5th: PointofView Panda, owned by Ken Hart
- `C1` / `3rd_then_5th_no_4`: 3rd: Garden Path Frisco, owned by Todd & Cheryl Hart
5th: Flattridge Banner, owned by Kim DeRossett
- `C1` / `3rd_then_5th_no_4`: 3rd: Kensington Tess, owned by Lisa Richards
5th: Foxwarren Dolly, owned by Flo Clark
- `C1` / `3rd_then_5th_no_4`: 3rd: Run Away Farms Shiner, owned by Martha Milligan
5th: Last Maddox, owned by Rebekah Hawks
- `C1` / `3rd_then_5th_no_4`: 3rd: Pepper, owned by Judi Lovell
5th: Rosie La Rue, owned by Nancy Mitchell
- `C1` / `3rd_then_5th_no_4`: 3rd: Westmorland Sparky, owned by Dan Cox
5th: Rascal, owned by Tim & Melissa Croft
- `C1` / `3rd_then_5th_no_4`: 3rd: Quail Oak Montana, owned by Greg Boyland
5th: Yorick, owned by Sally McKenney
- `C1` / `3rd_then_5th_no_4`: 3rd: Highwater Fiddle of FC, owned by Bob Franklin
5th: Double D Blaze, owned by Dorothy Whiting
- `C1` / `3rd_then_5th_no_4`: 3rd: Fox Run Reba, owned by Sherri Rossmiller
5th: Rocky Mountian Choctaw, owned by Tonya Adams
- `C1` / `3rd_then_5th_no_4`: 3rd: Red Hill Rocky, owned by Sherry Faircloth
5th: R.A. Sundance Kid, owned by Mike & Betty Bilinski
- `C1` / `3rd_then_5th_no_4`: 3rd: Bridle Creek Ben, owned by Joe & Linda Hosmer
5th: Foxwarren Tay, owned by Sundowner Farms
- `C1` / `3rd_then_5th_no_4`: 3rd: Springwood Raven, owned by Tonja Walter
5th: Achin' Acres Gretchen, owned by Janet Sproles

### `2000 Vol II_ocr_hqmax.txt` (FAIL)
- `C1` / `3rd_then_5th_no_4`: 3rd: Little Eden Banshee, owned by Rick & Mary Thornton
5th: Farmstead Holly, owned by Kathy Hunter
- `C1` / `3rd_then_5th_no_4`: 3rd: Boggsborough Bizzie, owned by Robert & Linda Fleck
5th: Sweetgrass Emma, owned by Shirley Kostric
- `C1` / `3rd_then_5th_no_4`: 3rd: North Country Petey, owned by Jack & Mary Lou Mogrovejo
5th: The Folly Black Jack, owned by Rick Thornton
- `C1` / `2nd_then_4th_no_3`: 2nd: Brookside Snowbear, owned by Debbie LaMantia
4th: Farmcliff Dirk, owned by Bob Franklin
- `C1` / `2nd_then_4th_no_3`: 2nd: Rushill Spice, owned by J. Baker/J. Freimark
4th: Foxport Tex, owned by Tooie Crooks
- `C1` / `2nd_then_4th_no_3`: 2nd: Briarpatch A.J, owned by Beverly Hirt
4th: Katie Clover, owned by Natalene Lamming
- `C1` / `2nd_then_4th_no_3`: 2nd: Farmcliff. Fred, owned by Michelle Ward
4th: Natural Instinct Micro, owned by Ken & Kathy Bushell
- `C1` / `2nd_then_4th_no_3`: 2nd: Anne Dalmadgerd: Sarah Cranor
4th: Taryn Lacy
- `C1` / `2nd_then_4th_no_3`: 2nd: Westwood Jade, owned by Rick &Leslie Hemsing
4th: Risky, owned by Melissa Lowe
- `C1` / `2nd_then_4th_no_3`: 2nd: Round the Bend Dudley, owned by Carol Watson
4th: Muscle Russell Hustle, owned by Rick Thornton
- `C1` / `1st_then_3rd_no_2`: 1st: Fox Run Reba, owned by Sherri Rossmiller
3rd: Just Avery, owned by Shawn & Kari Gerdes
- `C1` / `1st_then_3rd_no_2`: 1st: Fox Run Skye, owned by Chris Levine
3rd: Long Hope Satin, owned by Nellie Niewola

### `2000 vol 3 pt 1_ocr_hqmax.txt` (FAIL)
- `C1` / `3rd_then_5th_no_4`: 3rd: Couriwood Rooter, owned by Debbie & Rusty Graydon
5th: Easton Point Nipper, owned by Sally Gay
- `C1` / `3rd_then_5th_no_4`: 3rd: Kitfox Brillo, owned by Forrest Ann Walling
5th: Forrestar Phoenix, owned by Forrest Ann Walling
- `C1` / `3rd_then_5th_no_4`: 3rd: Killare Birdie, owned by Rachelle Goldsmith
5th: Tarsia Rattle, owned by Mary Labrosse
- `C1` / `3rd_then_5th_no_4`: 3rd: Treesbank Josie, owned by Carmen & Patricia Tosto
5th: Foxton Locks Annie, owned by Jo Paddison
- `C1` / `3rd_then_5th_no_4`: 3rd: AliHopth: Anne Case-Haefertyth: Shelly Stachursk
5th: Jennifer Phillips
- `C1` / `3rd_then_5th_no_4`: 3rd: Hunter's Moon Eclipse, owned by Charlene Schlueter
5th: Thistledown Carlie, owned by Sandy Brown
- `C1` / `3rd_then_5th_no_4`: 3rd: Chynna Beech, owned by Jim & Jan Brady
5th: Falling Branch Angus, owned by Tom & Lucy Ramey
- `C1` / `3rd_then_5th_no_4`: 3rd: Northgate Hale, owned by Doug & Sue Tack
5th: Brandywine Rosita, owned by Tom Colmar
- `C1` / `3rd_then_5th_no_4`: 3rd: Bent Creek Carley, owned by Marc & Laura Cormier
5th: Gills Creek Scout, owned by Joe Shapiro/Brooks Kelley
- `C1` / `3rd_then_5th_no_4`: 3rd: Nenees Lexie, owned by Anita Herman
5th: Arrowhead Norma Sue, owned by Jack Phillips
- `C1` / `3rd_then_5th_no_4`: 3rd: Meadowlake Fidget, owned by Karen Fitzpatrick
5th: Kenswick Kayla, owned by Sandy McElearney
- `C1` / `1st_then_3rd_no_2`: 1st: Will-O-Moor Badger, owned by Scott Whittington
3rd: Munchkin, owned by Melissa Lowe

### `2000 Vol III pt 1_ocr_hqmax.txt` (FAIL)
- `C1` / `3rd_then_5th_no_4`: 3rd: AliHopth: Anne Case-Haefertyth: Shelly Stachursk
5th: Jennifer Phillips
- `C1` / `3rd_then_5th_no_4`: 3rd: Shelly Stachursk
5th: AliHop
- `C1` / `3rd_then_5th_no_4`: 3rd: The Folly Bella, owned by Dorothy Whiting
5th: Little Eden Folly, owned by George Anderson
- `C1` / `3rd_then_5th_no_4`: 3rd: White Phantom Chelsea, owned by Sandy Kiteley
5th: Live Wire Noa, owned by C. & J. Kemp
- `C1` / `3rd_then_5th_no_4`: 3rd: Long Hope Wee Won, owned by Nellie Niewola
5th: The Hollow Primrose, owned by Linda St. Quintin
- `C1` / `3rd_then_5th_no_4`: 3rd: Sow's Ear Seabee, owned by John Rentro
5th: Brandywine Truffles, owned by Cathy Hedberg
- `C1` / `3rd_then_5th_no_4`: 3rd: Killare Birdie, owned by Rachelle Goldsmith
5th: Tarsia Rattle, owned by Mary Labrosse
- `C1` / `3rd_then_5th_no_4`: 3rd: Mockingbird Hills KRKLN Rose, owned by Pam Larson
5th: Tybalt Cauplet, owned by Julie Anderson
- `C1` / `2nd_then_4th_no_3`: 2nd: Briar Patch Molly, owned by Richard & Jan Finnerty
4th: Tortilla Flat Fiesta, owned by Patti Freemark
- `C1` / `2nd_then_4th_no_3`: 2nd: Woods End Calico, owned by Doug & Noreen Loranger
4th: Little Eden Thriller, owned by Michelle Ward
- `C1` / `1st_then_3rd_no_2`: 1st: Will-O-Moor Badger, owned by Scott Whittington
3rd: Munchkin, owned by Melissa Lowe
- `C1` / `1st_then_3rd_no_2`: 1st: Button Top Stinger, owned by Debby Calloway
3rd: Anderson Acres Tater Bug, owned by Tony Anderson

### `2000 Vol III pt 2_ocr_hqmax.txt` (FAIL)
- `C1` / `place_rank_gap`: Suitability to Raccoon/Badger                            Ent | 1th then 4th | 4th: Natural Instinct Adonis, owned by Roxanne Friend
- `C1` / `place_rank_gap`: Dogs, 1 yr. & older, over 12%:-15" Entries: 2 | 2th then 4th | 4th: Farriers Point Racer X, owned by Paul & Tammie Davis
- `C1` / `place_rank_gap`: Suitability to Groundhog                                     | 2th then 4th | 4th: Thistle Ridge Schatzie, owned by Wendy Houtz
