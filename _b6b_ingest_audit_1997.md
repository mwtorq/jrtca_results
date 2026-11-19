# B6b cleanup + ingest audit — 1997

Catalog: `_OCR_CLEANUP_CATALOG_HANDOFF.md`
Volumes: 4  cleaned=4  PASS=0  WARN=0  FAIL=4
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
| FAIL | True | 36 | 0 | C1×35,S1-S3×1 | `1997 Vol I pt 1_ocr_hqmax.txt` |
| FAIL | True | 29 | 0 | C1×29 | `1997 Vol I pt 2_ocr_hqmax.txt` |
| FAIL | True | 43 | 0 | C1×42,S1-S3×1 | `1997 Vol II pt 1_ocr_hqmax.txt` |
| FAIL | True | 2 | 0 | C1×2 | `1997 Vol II pt 2_ocr_hqmax.txt` |

## Sample residual hits (after cleanup)

### `1997 Vol I pt 1_ocr_hqmax.txt` (FAIL)
- `C1` / `3rd_then_5th_no_4`: 3rd: Horsemasters Josey, owned by Linda Cranford
5th: Full Cry Butch, owned by Christie Tatum
- `C1` / `3rd_then_5th_no_4`: 3rd: Briaroaks Star Trekker, owned by Kenneth & Cheryl Wallace
5th: T.J. Farm Little Guy, owned by Frank & Vickey Hines
- `C1` / `3rd_then_5th_no_4`: 3rd: Chubby, owned by Debbie McWilliams
5th: Broken Arrow Shanna, owned by Phillip & Lori Aaron
- `C1` / `3rd_then_5th_no_4`: 3rd: Jennifer Smith
5th: Ashley Tomberg
- `C1` / `3rd_then_5th_no_4`: 3rd: Blackland Lucky, owned by Doug Stephenson
5th: Cornow Conner, owned by Pam & Mike Malloy
- `C1` / `3rd_then_5th_no_4`: 3rd: Bowery Tilly, owned by Cheryl Edwards
5th: Hollyridge Panda, owned by Will Hahn
- `C1` / `3rd_then_5th_no_4`: 3rd: White Stockings Cork, owned by Pam Molloy
5th: Gracie, owned by Joe & Mary Colbert
- `C1` / `3rd_then_5th_no_4`: 3rd: Xanadu's First Star, owned by Steven Timmons
5th: Sac-N-Fox Susie Q, owned by Donnie & Rebecca Cox
- `C1` / `3rd_then_5th_no_4`: 3rd: Spike, owned by S.W.J.R.T.N. Russell Rescue
5th: Paradise Rastus, owned by Tina Sales
- `C1` / `3rd_then_5th_no_4`: 3rd: Kimberly Robin
5th: Christopher Nosenzo
- `C1` / `3rd_then_5th_no_4`: 3rd: Kimberwicke Hotshot, owned by Joyce Robin
5th: The Folly Roscoe, owned by Dave Russell
- `C1` / `3rd_then_5th_no_4`: 3rd: Farmliff Justin, owned by Kelly Morander F Fe YC ore vic 3rd Li: Chm smile 0 Crim Tan!
5th: Singletrack Hunter, owned by Mark & Lisa Green

### `1997 Vol I pt 2_ocr_hqmax.txt` (FAIL)
- `C1` / `3rd_then_5th_no_4`: 3rd: Foxnorton Willow, owned by Karen Reavis Fitzpatrick
5th: Farmstead Gadget, owned by J. Galterio & S. Ferber
- `C1` / `3rd_then_5th_no_4`: 3rd: Jane Carrey
5th: Sabrina Baker
- `C1` / `3rd_then_5th_no_4`: 3rd: Hills Dale Eliza, owned by Larry & Linda Morrison
5th: Farmstead Zoey, owned by Dee Margetis
- `C1` / `3rd_then_5th_no_4`: 3rd: Farmoliff Holland, owned by Doug & Sue Tack
5th: Big Sky Solo, owned by Dan & Karen Kinsley
- `C1` / `3rd_then_5th_no_4`: 3rd: Orchard Hill Jodeco, owned by Cheryl & Robby Robson
5th: Farmcliff Ben, owned by Bob Franklin
- `C1` / `3rd_then_5th_no_4`: 3rd: Ridgeview Jefferson, owned by Lynn May Measles
5th: C. Fred Higgins, owned by Lee & Sherry Crosley
- `C1` / `3rd_then_5th_no_4`: 3rd: Ravenswood Blondie, owned by David & Susan Crawford
5th: Farmcliff Kermit, owned by Bob Franklin
- `C1` / `3rd_then_5th_no_4`: 3rd: Foxport Maverick, owned by Mike Dander & Leslie Woodcock
5th: Sass N' Dash Darby, owned by Michale & Sally Murphy
- `C1` / `2nd_then_4th_no_3`: 2nd: Eunice, owned by Cheryl Hart
4th: Farmliff Ben, owned by Bob Frankiin
- `C1` / `1st_then_3rd_no_2`: 1st: Stephanie Eshleman
3rd: John Rorsch
- `C1` / `1st_then_3rd_no_2`: 1st: Lickity Split Sassy, owned by Bob Franklin Tred: alr ey Earn miarrmerd ir 72 Fee cn"
3rd: Courtland Mi Girl, owned by Joseph Jankowski
- `C1` / `place_rank_gap`: Bitches, 1 yr & over, 12 1/2-15", r/br              Entries: | 3th then 5th | 5th: Farmstead Gadget, owned by J. Galterio & S. Ferber

### `1997 Vol II pt 1_ocr_hqmax.txt` (FAIL)
- `C1` / `3rd_then_5th_no_4`: 3rd: Woods End Thorn, owned by Doug & Noreen Loranger
5th: Woods End Sega, owned by Doug & Noreen Loranger
- `C1` / `3rd_then_5th_no_4`: 3rd: Woods End Sega, owned by Doug & Noreen Loranger
5th: Woods End Dutch, owned by Doug & Noreen Loranger
- `C1` / `3rd_then_5th_no_4`: 3rd: Farmcliff Donny, owned by Bob Fran hin
5th: Farmliff Elmo, owned by Bob Franklin
- `C1` / `3rd_then_5th_no_4`: 3rd: Long Hope Mickey, owned by Bob Franklin
5th: Rancho Arnez Sully's Quest, owned by Jill Goodman
- `C1` / `3rd_then_5th_no_4`: 3rd: Colton's Ricochet Rocket, owned by John & Anita Phillips
5th: Brown's Valley Mustang Sally, owned by Ann Wendland
- `C1` / `3rd_then_5th_no_4`: 3rd: DeVerdon Tri Star, owned by Ben & Janet Sutcliffe
5th: Westwood Fancy, owned by Diane Wright
- `C1` / `3rd_then_5th_no_4`: 3rd: Kettle Creek Clipper, owned by Judi Bower
5th: Falling Branch Zack, owned by D. Calloway & J. Longendorfer
- `C1` / `3rd_then_5th_no_4`: 3rd: Good Connections Abigail, owned by Kent Ellsworth
5th: Seaview Shanghai, owned by Didi Gough
- `C1` / `3rd_then_5th_no_4`: 3rd: Puddingston Rooby, owned by Antonio & Barbara Sullo
5th: Taz, owned by Jonathan & Tracey Lavery
- `C1` / `3rd_then_5th_no_4`: 3rd: Farmliff Kermit, owned by Bob Franklin
5th: Steepe View Stretch, owned by Marcia Eaton
- `C1` / `3rd_then_5th_no_4`: 3rd: Evergreen Clover, owned by George Ridler
5th: Sows Ear Legacy, owned by A .Burigo/M.Stoveken
- `C1` / `3rd_then_5th_no_4`: 3rd: The Folly Zoe, owned by The O'Hallarans
5th: Live Wire Loch Ness, owned by Charlie & Julie Kemp

### `1997 Vol II pt 2_ocr_hqmax.txt` (FAIL)
- `C1` / `3rd_then_5th_no_4`: 3rd: Buddy, owned by Kenny & Sherry Cox
5th: Broken Arrow's Charlsie, owned by Phillip Aaron
- `C1` / `place_rank_gap`: Pups, 6 up to 9 months, up to 12 1" Entries: 6 | 3th then 5th | 5th: Broken Arrow's Charlsie, owned by Phillip Aaron
