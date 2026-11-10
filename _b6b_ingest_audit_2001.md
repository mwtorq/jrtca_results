# B6b cleanup + ingest audit — 2001

Catalog: `_OCR_CLEANUP_CATALOG_HANDOFF.md`
Volumes: 14  cleaned=0  PASS=0  WARN=0  FAIL=14
Year verdict: **FAIL**  SQL-apply unlock: NO

## Intent
- Apply finalize/catalog cleanups to stored HQ text (backup `*.pre_b6b`).
- Re-OCR only if FAIL remains after cleanup — not as the default path.

## Policy
- FAIL (blocks apply/unlock): smash, height/place garble, **O6 owner_tail_trunc**, **C1 class_header_gap**, placeholders
- Re-OCR queued when FAIL includes REOCR_CODES (O6/C1/smash/height) — do not invent surnames/titles
- `handled by` lines excluded from mangled_by / missing_owned_by

## Per volume

| Verdict | Cleaned | Fail | Warn | Catalog | File |
|---------|---------|------|------|---------|------|
| FAIL | False | 19 | 6 | C1×17,C6×4,O6×2,S4/O×2 | `2001 Coal Tree Farm_ocr_hqmax.txt` |
| FAIL | False | 15 | 0 | C1×15 | `2001 South Coast_ocr_hqmax.txt` |
| FAIL | False | 10 | 1 | C1×9,O6×1,S4/O×1 | `2001 Troon Quarry_ocr_hqmax.txt` |
| FAIL | False | 33 | 42 | C1×25,C6×21,S4/O×17,O6×8,?/cutoff_racing×2,C6/O1×2 | `2001 Vol I_ocr_hqmax.txt` |
| FAIL | False | 22 | 4 | C1×22,S4/O×2,C6×2 | `2001 MWJRTC II Wheatland I & II_ocr_hqmax.txt` |
| FAIL | False | 5 | 0 | C1×4,O6×1 | `2001 OH-PA II_ocr_hqmax.txt` |
| FAIL | False | 30 | 3 | C1×25,O6×5,S4/O×3 | `2001 Paumanok Farmstead Dutchess County_ocr_hqmax.txt` |
| FAIL | False | 8 | 3 | C1×6,S4/O×3,O6×2 | `2001 PNWJRTN_ocr_hqmax.txt` |
| FAIL | False | 17 | 4 | C1×17,C6/O1×2,C6×2 | `2001 Summer Celebration_ocr_hqmax.txt` |
| FAIL | False | 43 | 28 | C1×25,C6×19,O6×18,S4/O×8,?/cutoff_racing×1 | `2001 Vol II pt 1_ocr_hqmax.txt` |
| FAIL | False | 36 | 18 | C1×25,O6×11,S4/O×9,C6×8,C6/O1×1 | `2001 Vol II pt 2_ocr_hqmax.txt` |
| FAIL | False | 21 | 6 | C1×15,O6×6,S4/O×4,S4×1,?/4th_then_6th_no_5×1 | `2001 Yankee_ocr_hqmax.txt` |
| FAIL | False | 35 | 15 | C1×25,O6×10,S4/O×10,C6×5 | `2001 Vol III pt 1_ocr_hqmax.txt` |
| FAIL | False | 31 | 18 | C1×25,S4/O×14,O6×6,?/4th_then_6th_no_5×2,C6×2 | `2001 Vol III pt 2_ocr_hqmax.txt` |

## Sample residual hits (after cleanup)

### `2001 Coal Tree Farm_ocr_hqmax.txt` (FAIL)
- `O6` / `owner_tail_trunc`: Reserve: Zorro, owned by La
- `O6` / `owner_tail_trunc`: 6th: ws? ur PEWMWML nll Wirwy, MY WU IYWIGT | Luidllyci 4th: Farmcliff Liz, owned by Bob Franklin Nine The Eallir Pinar Aauwmacd bar am: © Fal Tle
- `S4/O` / `missing_owned_by`: 3rd: Woods End Calico, Doug & Noreen Loranger
- `S4/O` / `missing_owned_by`: 3rd: BenDavisouth Handling Agility, On Lead                         Entries: 3
- `C6` / `orphan_entry_count`: 16
- `C6` / `orphan_entry_count`: 17
- `C6` / `orphan_entry_count`: 6
- `C6` / `orphan_entry_count`: 3
- `C1` / `class_header_gap`: 1st: Ash Creek Lexus, owned by Jill Goodman
- `C1` / `class_header_gap`: 1st: Shelmar White Diamond, owned by Reed & Jean Veazy
- `C1` / `class_header_gap`: 1st: Little Eden Flicka, owned by Jenn Carr & Michelle Ward
- `C1` / `class_header_gap`: 1st: Treetop Jester, owned by Catherine Brown

### `2001 South Coast_ocr_hqmax.txt` (FAIL)
- `C1` / `class_header_gap`: 1st: Stetson, owned by Norman Daloisio
- `C1` / `class_header_gap`: 1st: Runamuk Macey, owned by Sue Bromley
- `C1` / `class_header_gap`: 1st: Oakfield Hoochi, owned by Didi Gough
- `C1` / `class_header_gap`: 1st: stt Land's End Bully, owned by Didi Gough
- `C1` / `class_header_gap`: 1st: stt Seaview Pippen, owned by Helen Button
- `C1` / `class_header_gap`: 1st: stt: Runamuk Levi, owned by Bud & Sharon Green
- `C1` / `class_header_gap`: 1st: Treesbank Blueprint, owned by Janet Sproles
- `C1` / `class_header_gap`: 1st: stt Seaview Anubis, owned by Didi Gough
- `C1` / `class_header_gap`: 1st: stt Seaview Salty, owned by Didi Gough
- `C1` / `class_header_gap`: 1st: stt Salt Valley Top Kat, owned by Jan Finnerty
- `C1` / `class_header_gap`: 1st: stt Seaview Stiletta, owned by Didi Gough
- `C1` / `class_header_gap`: 1st: stt Ruff N' Tumble Grizzle, owned by Don & Kathy Tait

### `2001 Troon Quarry_ocr_hqmax.txt` (FAIL)
- `O6` / `owner_tail_trunc`: 3rd: Mauser, owned by Tiffany Van Tuy
- `S4/O` / `missing_owned_by`: 2nd: Amalia Williamsouth Handling Agility, On Lead                         Entries: 4
- `C1` / `class_header_gap`: 1st: Red Oak Maddy, owned by James and Carolyn Tate
- `C1` / `class_header_gap`: 1st: Treesbank Josie, owned by pat and Carmen Tosto
- `C1` / `class_header_gap`: 1st: Sparky, owned by Ursula Schwalbe
- `C1` / `class_header_gap`: 1st: Poco Bailey, owned by Wayne Holleman
- `C1` / `class_header_gap`: 1st: Sweetgrass Sarah, owned by Sheri Rossmiller
- `C1` / `class_header_gap`: 1st: Amelia Finnerty
- `C1` / `class_header_gap`: 1st: JemdJon Buck, owned by Lyndy Banducci
- `C1` / `class_header_gap`: 1st: Firethom Jinx, owned by Mary E. Bayley

### `2001 Vol I_ocr_hqmax.txt` (FAIL)
- `?` / `cutoff_racing`: ACING DIVISION
- `O6` / `owner_tail_trunc`: 3rd: Hines Hill Whistle, owned by Scamper Hil
- `O6` / `owner_tail_trunc`: 5th: Sow's Ear Survivor, owned by Meaghan Ape
- `O6` / `owner_tail_trunc`: 6th: Edisons Prince Jake, owned by Tyno
- `O6` / `owner_tail_trunc`: Champion: Red Oak Maddie, owned by James & Carolyn Tat
- `O6` / `owner_tail_trunc`: 6th: Rey nard Harley, owned by ey
- `S4/O` / `missing_owned_by`: 1st: T.J. Fans Reality, Teresa Wellman
- `S4/O` / `missing_owned_by`: 3rd: Armowhead Norma Sue, Jack & Laurie Phillips
- `S4/O` / `missing_owned_by`: 6th: Heaven Hill Angel, Sammy & Danetta Hopewell
- `S4/O` / `missing_owned_by`: 1st: Jack's B' Quick Zeus, Travis & Cat Hallman
- `S4/O` / `missing_owned_by`: 5th: Amowhead Margarita, Kathy & Scott Neus
- `S4/O` / `missing_owned_by`: 3rd: Woods End Calico, Doug & Noreen Loranger

### `2001 MWJRTC II Wheatland I & II_ocr_hqmax.txt` (FAIL)
- `S4/O` / `missing_owned_by`: 2nd: Pups, 9 up to 12 months, 10 up to 12 1/2" Entries:
- `S4/O` / `missing_owned_by`: 2nd: Pups, 9 up to 12 months, 10 up to 12 1/2"." Entries: 3
- `C6` / `orphan_entry_count`: 9
- `C6` / `orphan_entry_count`: 29
- `C1` / `class_header_gap`: 1st: Button Top Lady Bug, owned by Ron & Linda Gruenwald
- `C1` / `class_header_gap`: 1st: Wootinhille Adena, owned by Phil & Sue Hawkins
- `C1` / `class_header_gap`: 1st: Meadowlake Token, owned by Ron & Tandee Morris
- `C1` / `class_header_gap`: 1st: Skytop Shimmer, owned by Chris Levine/Cheryl Ellsworth
- `C1` / `class_header_gap`: 1st: Ballyblack Trey, owned by Jennifer Gilligan
- `C1` / `class_header_gap`: 1st: Prestige Farms Oliver, owned by Jennifer Gilligan
- `C1` / `class_header_gap`: 1st: Green Gate Keeper, owned by Amanda Wuerstle
- `C1` / `class_header_gap`: 1st: Rocky Mountain Hazard, owned by S. Bamett & J. Hughe

### `2001 OH-PA II_ocr_hqmax.txt` (FAIL)
- `O6` / `owner_tail_trunc`: 4th: T.J. Farms Sonny, owned by Joe Shapiro & Brooks Kell
- `C1` / `class_header_gap`: 1st: Woods End Pistol Pete, owned by Russ & Trina Powell
- `C1` / `class_header_gap`: 1st: Bent Creek Carley, owned by Marc & Laura Cormier
- `C1` / `class_header_gap`: 1st: Mustang, owned by Jill Goodman

### `2001 Paumanok Farmstead Dutchess County_ocr_hqmax.txt` (FAIL)
- `O6` / `owner_tail_trunc`: 2nd: Glimmer, owned by Jan
- `O6` / `owner_tail_trunc`: 5th: Northgate Chester, owned by Susan Gil
- `O6` / `owner_tail_trunc`: 1st: Caimbrae Image, owned by Don & Gail Stock and Shirley Bui
- `O6` / `owner_tail_trunc`: 4th: White Gate Dodger, owned by y
- `S4/O` / `missing_owned_by`: 5th: Willowbrook Tucker, Kari Streicher
- `S4/O` / `missing_owned_by`: 5th: Silent Partner Baltazar, George Ridler
- `S4/O` / `missing_owned_by`: 5th: Pups, 6 up to 9 months, 10 up to 12 1/2" Entries: 7
- `C1` / `class_header_gap`: 1st: Kara Clancy, owned by Gerry Hevaghan
- `C1` / `class_header_gap`: 1st: Double D Tally Ho, owned by Dorothy Whiting
- `C1` / `class_header_gap`: 1st: Andiin Tessa, owned by Jane Collard
- `C1` / `class_header_gap`: 1st: The Folly Bella, owned by Dorothy Whiting
- `C1` / `class_header_gap`: 1st: Northgate Chester, owned by Susan Gill

### `2001 PNWJRTN_ocr_hqmax.txt` (FAIL)
- `O6` / `owner_tail_trunc`: 12 1/2-15" Reserve: Kingmont Finley, owned by Terry & Diane Tho
- `S4/O` / `missing_owned_by`: 4th: Sweetgrass Nelson, Rodger & Caryn Funk
- `S4/O` / `missing_owned_by`: 2nd: J&J Miniva, Judie Baker & Janice Freimark
- `C1` / `class_header_gap`: 1st: Vagabond Frost, owned by Lois Clough
- `C1` / `class_header_gap`: 1st: Fire Thom Hot Pepper, owned by Lloyd & Ann Wendland
- `C1` / `class_header_gap`: 1st: Crossruff Duel, owned by Lynn Hawley
- `C1` / `class_header_gap`: 1st: Little Eden Diva, owned by Wendy Calvert

### `2001 Summer Celebration_ocr_hqmax.txt` (FAIL)
- `C6/O1` / `bare_entries`: Entries:
- `C6` / `orphan_entry_count`: 18
- `C6` / `orphan_entry_count`: 12
- `C1` / `class_header_gap`: 1st: Whirlwind Tempest, owned by Barbara Tyler
- `C1` / `class_header_gap`: 1st: Sueshi, owned by Jeff Rowe
- `C1` / `class_header_gap`: 1st: 5t: Red Collar Sebastian, owned by Randy & Donna Hastings
- `C1` / `class_header_gap`: 1st: Old 1yr. Glory & older, owned by 12%", Becky r/br Crosse Entries: 9
- `C1` / `class_header_gap`: 1st: Buckaroo, owned by Donna Pierce
- `C1` / `class_header_gap`: 1st: Red Oak Bella, owned by Billy Shores
- `C1` / `class_header_gap`: 1st: Heaven Hill Chipper, owned by Shelley Holland
- `C1` / `class_header_gap`: 1st: Heaven Hill Mollie, owned by Richard Stephenson
- `C1` / `class_header_gap`: 1st: Sparkle, owned by Audie Sumner

### `2001 Vol II pt 1_ocr_hqmax.txt` (FAIL)
- `?` / `cutoff_racing`: ACING DIVISION
- `O6` / `owner_tail_trunc`: 12 1/2-15" Champion: Willie Biue Boy, owned by John & Valerie Tri
- `O6` / `owner_tail_trunc`: 10-12 1/2"." Champion: Farmcliff Holland, owned by Doug & Sue Tac
- `O6` / `owner_tail_trunc`: 6th: Meadowlake Wicca, owned by Patricia Web
- `O6` / `owner_tail_trunc`: 1st: istt Little Eden Exile, owned by lan Hughes & S
- `O6` / `owner_tail_trunc`: 3rd: Northgate Chester, owned by Susan Gil
- `O6` / `owner_tail_trunc`: 6th: Northgate Chester, owned by Susan Gil
- `O6` / `owner_tail_trunc`: 1st: onc:      The Larches Spirit,  owned by Virginia Mel
- `O6` / `owner_tail_trunc`: 1st: Long Creek Twister, owned by Richard & Rebecca Pai
- `O6` / `owner_tail_trunc`: 10-12 1/2"" Reserve: Big Sky Annie, owned by Doug & Sue Tac
- `O6` / `owner_tail_trunc`: Best: Northgate Chester, owned by Susan Gil
- `S4/O` / `missing_owned_by`: 2nd: J&J Miniva, Judie Baker & Janice Freimark

### `2001 Vol II pt 2_ocr_hqmax.txt` (FAIL)
- `O6` / `owner_tail_trunc`: 1st: Tortilla Fiat Cheeky, owned by Mary Lou
- `O6` / `owner_tail_trunc`: 1st: Northgate Shannon, owned by Sandy Fei
- `O6` / `owner_tail_trunc`: 3rd: Northgate Chester, owned by Susan Gil
- `O6` / `owner_tail_trunc`: 2nd: Glimmer, owned by Jan
- `O6` / `owner_tail_trunc`: 2nd: Northgate Chester, owned by Susan Gil
- `O6` / `owner_tail_trunc`: 3rd: Little Eden Sensation, owned by Michelle War
- `O6` / `owner_tail_trunc`: 2nd: Big Sky Annie, owned by Doug & Su
- `S4/O` / `missing_owned_by`: 6th: Prestige Farms Oliver, owned b J. Gilligan/S. Geroux
- `S4/O` / `missing_owned_by`: 3rd: Washa Charlie, ownéd by Dani Phillips
- `S4/O` / `missing_owned_by`: 6th: Willowbrook Tucker, Kari Streicher
- `S4/O` / `missing_owned_by`: 2nd: pov Creek Theft,  es Mary Lou Sa
- `S4/O` / `missing_owned_by`: 3rd:      Na TL Clementine, by Doug & Sue Tack

### `2001 Yankee_ocr_hqmax.txt` (FAIL)
- `S4` / `mangled_by`: 4th:      Round the Bend Foxy pn ome by G.  Harvey & S. Ryan
- `?` / `4th_then_6th_no_5`: 4th: Springwood Jasmine, owned by Susan Riley
6th: Monterey Jack, owned by Gene Harvey
- `O6` / `owner_tail_trunc`: 3rd: Northgate Chester, owned by Susan Gil
- `O6` / `owner_tail_trunc`: 6th: Northgate Chester, owned by Susan Gil
- `O6` / `owner_tail_trunc`: Best: Northgate Chester, owned by Susan Gil
- `O6` / `owner_tail_trunc`: 10-12 1/2" Reserve: Big Sky Annie, owned by Doug & Sue Tac
- `S4/O` / `missing_owned_by`: 4th:   Farmcliff Duke, owned
- `S4/O` / `missing_owned_by`: 5th:      Northgate Hallie, we! Lom Doug & Sue Tack
- `S4/O` / `missing_owned_by`: 4th: CArnanmatar Habarmarne Asauamac Bye Turldle Dacnlyar = Id. 1481 LI ydis 1 Kalil, WV Id MY dd th LR JWT duly
- `S4/O` / `missing_owned_by`: 2nd: Foxhal Tasha,  Pd by Don 8 Gail Stock
- `C1` / `class_header_gap`: 1st: Eastlake Willy, owned by Robert Van der Heym
- `C1` / `class_header_gap`: 1st: Glenhaven Belle, owned by Geri Morin & Jean Veazey

### `2001 Vol III pt 1_ocr_hqmax.txt` (FAIL)
- `O6` / `owner_tail_trunc`: 1st: Falling Branch Checkers, owned by Marc
- `O6` / `owner_tail_trunc`: 2nd: Farrer Point Ranger, owned by Denise Net
- `O6` / `owner_tail_trunc`: 2nd: Falling Branch Checkers, owned by Marc
- `O6` / `owner_tail_trunc`: 3rd: Farrier Point Ranger, owned by Denise Net
- `O6` / `owner_tail_trunc`: 2nd: Smilin' Jack Fully Monty, owned by Lisa Decker/Scooter Mau
- `O6` / `owner_tail_trunc`: Champion: Green Gate Tomba, owned by Joe & Priscilla Tes
- `S4/O` / `missing_owned_by`: 3rd: Christine Rothth: Patrick Fitzgeraldouth Handling Agility, On Lead                        Entries: 4
- `S4/O` / `missing_owned_by`: 3rd: WadeEvansth: Amelia Finnertyth: Anne Dalmadgeth: Ben Amettfouth Handling Agility, On Lead                        Entries: 6
- `S4/O` / `missing_owned_by`: 5th: Agility Il, Off Lead, over 12/2-15" Entries: 5
- `S4/O` / `missing_owned_by`: 3rd: A [ab lpr . PES RO PR Ls) aD Rs i SAREE J EN I Bx es rl . . >. DEAS : Tr ne Oe Dar pes, et Som Sheer or, i renoh RA FEE TTI RYT RI XT [ Eb Re iA BY? Phos E
- `S4/O` / `missing_owned_by`: 2nd: Fammcliff:Spencer,:ownedsby:Bobr& Genie Franklin
- `S4/O` / `missing_owned_by`: 6th: Muscle Russell Dynamite, Heath Ogbum & Jill Goodman

### `2001 Vol III pt 2_ocr_hqmax.txt` (FAIL)
- `?` / `4th_then_6th_no_5`: 4th: Bent Creek Carley, owned by Marc & Laura Cormier
6th: Stone's Throw Griffey, owned by Karen Merriman
- `O6` / `owner_tail_trunc`: 6th: Sass 'N Dash Bailey, owned by Mike Mur
- `O6` / `owner_tail_trunc`: 2nd: Sass 'N Dash Bailey, owned by Mike Mur
- `O6` / `owner_tail_trunc`: 1st: Rat Race Remember When, owned by Gary & Donna Ric
- `S4/O` / `missing_owned_by`: 1st: Christina Wagner                                    2outh Handling Agility, On Lead                         Entries: 3
- `S4/O` / `missing_owned_by`: 1st: Sassy, owner unknown
- `S4/O` / `missing_owned_by`: 2nd: Andrew Howardscilla Testa                    Youth Handling Agility, Off Lead                          Entries: 2
- `S4/O` / `missing_owned_by`: 5th: Falling Branch Trumpet, Kathy & Bob Montbleau
- `S4/O` / `missing_owned_by`: 6th: Quitealot UdlSy, OWIicG Dy UcDla Ltuallv
- `S4/O` / `missing_owned_by`: 5th: Razzmatazz, owner unknown
- `S4/O` / `missing_owned_by`: 4th: Razzmatazz, owner unknown
- `S4/O` / `missing_owned_by`: 5th:     Pepper, pa by Richard Burfoot
