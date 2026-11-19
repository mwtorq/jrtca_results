# B6b cleanup + ingest audit — 2001

Catalog: `_OCR_CLEANUP_CATALOG_HANDOFF.md`
Volumes: 14  cleaned=14  PASS=3  WARN=0  FAIL=11
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
| FAIL | True | 12 | 0 | C1×12 | `2001 Coal Tree Farm_ocr_hqmax.txt` |
| PASS | True | 0 | 0 | — | `2001 South Coast_ocr_hqmax.txt` |
| FAIL | True | 1 | 0 | C1×1 | `2001 Troon Quarry_ocr_hqmax.txt` |
| FAIL | True | 55 | 0 | C1×55 | `2001 Vol I_ocr_hqmax.txt` |
| FAIL | True | 2 | 0 | C1×2 | `2001 MWJRTC II Wheatland I & II_ocr_hqmax.txt` |
| PASS | True | 0 | 0 | — | `2001 OH-PA II_ocr_hqmax.txt` |
| FAIL | True | 40 | 0 | C1×40 | `2001 Paumanok Farmstead Dutchess County_ocr_hqmax.txt` |
| PASS | True | 0 | 0 | — | `2001 PNWJRTN_ocr_hqmax.txt` |
| FAIL | True | 2 | 0 | C1×2 | `2001 Summer Celebration_ocr_hqmax.txt` |
| FAIL | True | 68 | 0 | C1×68 | `2001 Vol II pt 1_ocr_hqmax.txt` |
| FAIL | True | 53 | 0 | C1×53 | `2001 Vol II pt 2_ocr_hqmax.txt` |
| FAIL | True | 42 | 0 | C1×42 | `2001 Yankee_ocr_hqmax.txt` |
| FAIL | True | 47 | 0 | C1×47 | `2001 Vol III pt 1_ocr_hqmax.txt` |
| FAIL | True | 55 | 0 | C1×54,S1-S3×1 | `2001 Vol III pt 2_ocr_hqmax.txt` |

## Sample residual hits (after cleanup)

### `2001 Coal Tree Farm_ocr_hqmax.txt` (FAIL)
- `C1` / `3rd_then_5th_no_4`: 3rd: Karal Otter, owned by Alan & Karen Cooper
5th: Milton, owned by Barbara Barrett
- `C1` / `3rd_then_5th_no_4`: 3rd: Sow's Ear Einstein, owned by Rick & Mary Thomton
5th: Morgan Hill Dewey, owned by Don & Gail Stock
- `C1` / `3rd_then_5th_no_4`: 3rd: Northgate Hale, owned by Doug & Sue Tack
5th: Sows Ear Taltos, owned by Twila Decker
- `C1` / `2nd_then_4th_no_3`: 2nd: Brookside Brass, owned by Debbie LaMantia
4th: Silent Partner Tow Truck, owned by Heath Ogbum
- `C1` / `2nd_then_4th_no_3`: 2nd: The Larches Liam McGee, owned by Donald & Joan LaPlace
4th: Fox Run Topper, owned by Rick & Mary Thomton
- `C1` / `place_rank_gap`:  | 3th then 5th | 5th: Milton, owned by Barbara Barrett
- `C1` / `place_rank_gap`: Dog 1st Pups, Edgewater 4 up to Jalapena, 6 months, owned r/ | 2th then 4th | 4th: Silent Partner Tow Truck, owned by Heath Ogbum
- `C1` / `place_rank_gap`: Bitch Pups, 4 up to 6 months, smooth Entries: 7 | 1th then 3th | 3rd: Ash Creek Pin Up, owned by Mary Lou Cassone
- `C1` / `place_rank_gap`: Veteran Dog, 6 years & older Entries: 6 | 2th then 4th | 4th: Fox Run Topper, owned by Rick & Mary Thomton
- `C1` / `place_rank_gap`: Dog Pups, 9 up to 12 months, r/br                         En | 3th then 5th | 5th: Morgan Hill Dewey, owned by Don & Gail Stock
- `C1` / `place_rank_gap`: Bitches, 1yr. & older, 10 up to 12 1/2" Entries: 15 | 3th then 5th | 5th: The Folly Piper, owned by Mary & Rick Thomton
- `C1` / `place_rank_gap`: Dogs, 1 yr. & older, 10 up to 12 1/2" Entries: 8 | 3th then 5th | 5th: Sows Ear Taltos, owned by Twila Decker

### `2001 Troon Quarry_ocr_hqmax.txt` (FAIL)
- `C1` / `place_rank_gap`: Dogs, 1 yr. & older, 10 up to 12 1/2"." Entries: 5 | 3th then 5th | 5th: Lone Cactus Blackfoot, owned by G. Phipps/J. Sproles

### `2001 Vol I_ocr_hqmax.txt` (FAIL)
- `C1` / `3rd_then_5th_no_4`: 3rd: Westside Lucky, owned by Chris & Hana Smith
5th: R.A. Russell Trulock, owned by Mike & Lynda Trulock
- `C1` / `3rd_then_5th_no_4`: 3rd: 3d: Maggie, owned by Jeff & Cathy Arceneaux
5th: Reve, owned by Amy Allen
- `C1` / `3rd_then_5th_no_4`: 3rd: Smilin' Jack Striker, owned by Kelly & Jennifer Noordar
5th: Milton, owned by Barbara Barrett
- `C1` / `3rd_then_5th_no_4`: 3rd: Fox Run Topper, owned by Rick & Mary Thomton
5th: Riverview Calvin, owned by Karen Vemon
- `C1` / `3rd_then_5th_no_4`: 3rd: Sow's Ear Einstein, owned by Rick & Mary Thomton
5th: Long Hope Sabre, owned by Bob Franklin
- `C1` / `3rd_then_5th_no_4`: 3rd: Hart Farms Hunter II, owned by Sue & Don Wilson
5th: Tenier-fic Wild Child, owned by Sammy & Danetta Hopewell
- `C1` / `3rd_then_5th_no_4`: 3rd: Silver Valley Sally, owned by Richard & Rebecca Paff
5th: Cason's Quarters Tailor Made, owned by P. & P. McConville
- `C1` / `3rd_then_5th_no_4`: 3rd: Russell's Jack "RJ", owned by Sylvia Reams
5th: Terier-ific Snapdragon, owned by Kim & Nixy Morales
- `C1` / `3rd_then_5th_no_4`: 3rd: Beezer, owned by Diana Amador
5th: Badakashan Snaffles, owned by Rhonda Vega & Larry Carson
- `C1` / `3rd_then_5th_no_4`: 3rd: Northgate Hale, owned by Doug & Sue Tack
5th: Sow's Ear Taltos, owned by Twila Decker
- `C1` / `2nd_then_4th_no_3`: 2nd: Pepper, owned by Richard Buford
4th: Karal Roxi, owned by Karen Cooper
- `C1` / `2nd_then_4th_no_3`: 2nd: Kenswick Dottie, owned by Sandy & Joel McEleamey
4th: Famncliff Liz, owned by Bob Franklin

### `2001 MWJRTC II Wheatland I & II_ocr_hqmax.txt` (FAIL)
- `C1` / `3rd_then_5th_no_4`: 3rd: Lickity Split Spice Girl, owned by Lenora Erb
5th: Kingmont Fable, owned by J. Benoit & D. Holly
- `C1` / `place_rank_gap`: Suitability to Groundhog                                     | 3th then 5th | 5th: Kingmont Fable, owned by J. Benoit & D. Holly

### `2001 Paumanok Farmstead Dutchess County_ocr_hqmax.txt` (FAIL)
- `C1` / `3rd_then_5th_no_4`: 3rd: North Country Clementine, owned by Doug & Sue Tack
5th: Terra Fox Bella, owned by John & Cynthia Parmenter
- `C1` / `3rd_then_5th_no_4`: 3rd: Sow's Ear Sieko, owned by Tim Richardson
5th: Silent Partner Baltazar, owned by George Ridler
- `C1` / `3rd_then_5th_no_4`: 3rd: Fammcliff Holland, owned by Doug Tack
5th: The Hollow Zena, owned by Jill Goodman
- `C1` / `2nd_then_4th_no_3`: 2nd: The Foly Piper,  owned by Rick & Mary Thomton
4th: Long Hope Sabre, owned by Bob Franklin
- `C1` / `1st_then_3rd_no_2`: 1st: Silent Partner Rollback, owned by Heath Ogbum
3rd: Ash Creek Theft, owned by Mary Lou Cassone
- `C1` / `1st_then_3rd_no_2`: 1st: Kress Couniry Relentless, owned by Sharon Kress
3rd: Sadie, owned by Margaret Strickley
- `C1` / `1st_then_3rd_no_2`: 1st: Whispering oo  epsi, owned by M. & R Minutello
3rd: Willowbrook Tucker, owned by Kari Stricker
- `C1` / `1st_then_3rd_no_2`: 1st: Lickity Split Sassy, owned by Bob Franklin
3rd: Will-O-Moor Badger, owned by Scott & Christina Whittington
- `C1` / `1st_then_3rd_no_2`: 1st: Northgate Hale, owned by Doug Tack
3rd: Farmcliff Huich, owned by Dave & Marty McMahon
- `C1` / `1st_then_3rd_no_2`: 1st: Lost Acres Revlon, owned by Karen McCarthy
3rd: Bent Creek Carley, owned by Marc & Laura Cormier
- `C1` / `1st_then_3rd_no_2`: 1st: Leewinds Crush, owned by Linda Cowasiee
3rd: Brookside Brass, owned by Debbie LaMantia
- `C1` / `1st_then_3rd_no_2`: 1st: Thimble Farm Coyy, owned by Valerie Davis
3rd: Little Eden Sensation, owned by Michelle Ward

### `2001 Summer Celebration_ocr_hqmax.txt` (FAIL)
- `C1` / `3rd_then_5th_no_4`: 3rd: Emily Fincher
5th: Emily Reese
- `C1` / `place_rank_gap`: Child Handler | 3th then 5th | 5th: Emily Reese

### `2001 Vol II pt 1_ocr_hqmax.txt` (FAIL)
- `C1` / `3rd_then_5th_no_4`: 3rd: Double D Tally Ho, owned by Dorothy Whiting
5th: Luke, owned by Tracy Luggiero
- `C1` / `3rd_then_5th_no_4`: 3rd: East Grinstead Luther, owned by Stacy Kovak
5th: Round the Bend Dudiey, owned by Sarah Watson
- `C1` / `3rd_then_5th_no_4`: 3rd: Andlin Czar War, owned by Rob & Amy McCaslin
5th: Hunters Green Stokes, owned by Antonio & Barbara Sullo
- `C1` / `3rd_then_5th_no_4`: 3rd: Kenswick Kayla, owned by Sandy McEleamey
5th: Farmcliff Holland, owned by Doug & Sue Tack
- `C1` / `3rd_then_5th_no_4`: 3rd: Kettle Creek Kaileigh, owned by Christine Bolser
5th: Renegade Scout, owned by Mandy Johnson
- `C1` / `3rd_then_5th_no_4`: 3rd: Lil' Cookee's Miracle, owned by Billie Witcher & Caria Hair
5th: Sassy Britt, owned by Billie Roach
- `C1` / `3rd_then_5th_no_4`: 3rd: Hillside Josie, owned by Karen Vemon
5th: Sass N'Dash Molly, owned by Mary Webb
- `C1` / `3rd_then_5th_no_4`: 3rd: Deep Run Derek, owned by John & Vicki Brown
5th: Ash Creek Sock, owned by Kari Streicher & Teresa Gottlieb
- `C1` / `3rd_then_5th_no_4`: 3rd: Adam Smith
5th: Courtney Curr
- `C1` / `3rd_then_5th_no_4`: 3rd: Kit, owned by Don Tait
5th: Highland Trace, owned by Molly Rombach
- `C1` / `3rd_then_5th_no_4`: 3rd: Chipper, owned by Teresa Russell
5th: 3 T's Maverick, owned by Teri Wilson
- `C1` / `2nd_then_4th_no_3`: 2nd: Hines Hill Carlton, owned by Sherri Leatherman
4th:      Ash Creek Theft, owned by Marylou Cassone

### `2001 Vol II pt 2_ocr_hqmax.txt` (FAIL)
- `C1` / `3rd_then_5th_no_4`: 3rd: Pheasant Hill Magpie, owned by Steve & Eileen Reese
5th: Fox Loxi Kitti, owned by Scott & Sue Aeppli
- `C1` / `3rd_then_5th_no_4`: 3rd: Ally McBeal, owned by Jill Lowry
5th: Munchie, owned by Lisa & Barry Bigaoutte
- `C1` / `3rd_then_5th_no_4`: 3rd: Rooson Mandy, owned by Carl & Patty Nocek
5th: Wild Goose Kerm, owned by Charlene Schlueter
- `C1` / `3rd_then_5th_no_4`: 3rd:      Na TL Clementine, owned by Doug & Sue Tack
5th:      Terra Fox Bella, owned by John & Cynthia Parmenter
- `C1` / `3rd_then_5th_no_4`: 3rd: Sows Ear Sieko, owned by Tim Richardson
5th: Silent Partner Baltazar, owned by George Ridler
- `C1` / `3rd_then_5th_no_4`: 3rd: Windyview Questor, owned by Bill O'Brien
5th: Fox Run Scout, owned by Gerard Von Essen
- `C1` / `3rd_then_5th_no_4`: 3rd: Chas d'Tail, owned by Kris Tracy
5th: Heart-N-Soul McSorley, owned by Walt & Marla Lutter
- `C1` / `3rd_then_5th_no_4`: 3rd: Farmcliff Holland, owned by Doug Tack
5th: The Hollow Zena, owned by Jill Goodman
- `C1` / `3rd_then_5th_no_4`: 3rd: Northgate Duckett, owned by Doug & Sue Tack
5th: Sow's Ear Taltos, owned by T. Decker & K. McCarthy
- `C1` / `3rd_then_5th_no_4`: 3rd: Little Eden Sensation, owned by Michelle Ward
5th: Northgate Hallie, owned by Doug & Sue Tack
- `C1` / `3rd_then_5th_no_4`: 3rd: Blue Bams Charlie, owned by Michael & Tammy Durante
5th: Starphyre Katie Mae, owned by Pam Smith
- `C1` / `3rd_then_5th_no_4`: 3rd: Northgate Hallie, owned by Doug & Sue Tack
5th: Sophie, owned by J. Guilmain & J. Marchetti

### `2001 Yankee_ocr_hqmax.txt` (FAIL)
- `C1` / `3rd_then_5th_no_4`: 3rd: Double D Tally Ho, owned by Dorothy Whiting
5th: Luke, owned by Tracy Luggiero
- `C1` / `3rd_then_5th_no_4`: 3rd: Andlin Czar War, owned by Rob & Amy McCaslin
5th: Hunters Green Stokes, owned by Antonio & Barbara Sullo
- `C1` / `2nd_then_4th_no_3`: 2nd: Goulden Ridge Darlin' Darla, owned by Sharon Cudd Wirant
4th: EEE SpeTtErnwRE din IGE ERE anklin
- `C1` / `2nd_then_4th_no_3`: 2nd: NCW Crigldila Bic voy .... Enmies. 1st" 'Faimiliff-Sean;, owned by Bob & Genie FRKiir F 5 Tp IN LiImmrd KI Crs Rly I Atzirmacs lair Lammiftae
4th: Whisperi
- `C1` / `2nd_then_4th_no_3`: 2nd: Hines Hill Carlton, owned by Sherri Leatherman
4th: Ash Creek Theft, owned by Marylou Cassone
- `C1` / `2nd_then_4th_no_3`: 2nd: Northgate Hallie, owned by Doug & Sue Tack
4th: Edgewater Habaneros, owned by Twila Decker
- `C1` / `2nd_then_4th_no_3`: 2nd: Ash Creek Theft, owned by Marylou Cassone
4th: Foxport Ting, owned by Sharon Cudd Wirant
- `C1` / `2nd_then_4th_no_3`: 2nd: Lost Acres Revlon, owned by Karen McCarthy
4th: Lakeshore Jiminy Cricket, owned by Kathy Larson
- `C1` / `1st_then_3rd_no_2`: 1st: Highwater Banjo, owned by Ann Shepard
3rd: Arins Boo, owned by Alison Linstrum
- `C1` / `1st_then_3rd_no_2`: 1st: Round the Bend Dar,  owned by Kay Sadowsky
3rd: Ash Creek Theft, owned by Marylou Cassone
- `C1` / `1st_then_3rd_no_2`: 1st: The Larches Spit, owned by Virginia Mei rar
3rd: Round the Bend Comet, owned by Sandra Ryan
- `C1` / `1st_then_3rd_no_2`: 1st: Natural Instinct Jewel, owned by Ken & Kathy Bushell
3rd: Farmcliff Joe, owned by Bob & Genie Franklin Ail. Fe: mad dla Donen omem re | medics mrsrvamed In

### `2001 Vol III pt 1_ocr_hqmax.txt` (FAIL)
- `C1` / `3rd_then_5th_no_4`: 3rd:      Whispering Winds Heidi Ho, owned by Ken Yield
5th:      Abby, owned by Richard 2 Annette Kent
- `C1` / `3rd_then_5th_no_4`: 3rd: The Folly Piper, owned by Rick & Mary Thomton
5th: The Folly Lucy, owned by Rick & Mary Thomton
- `C1` / `3rd_then_5th_no_4`: 3rd: Smilin' Jack Full Monty, owned by Lisa Decker/Scooter Mauck
5th: Katie Clover, owned by Naialene Lamming
- `C1` / `3rd_then_5th_no_4`: 3rd: Farrier Point Ranger, owned by Denise Neuner
5th: Nampara Bisket, owned by Mary Labrosse
- `C1` / `3rd_then_5th_no_4`: 3rd: Long Hope Teeni Weeni, owned by Nellie Niewola
5th: Highwater Banjo, owned by Ann Shephard
- `C1` / `3rd_then_5th_no_4`: 3rd: Arlins My Ty, owned by Michael Beach
5th:  Sow's Ear Taltos, owned by Twila Decker
- `C1` / `3rd_then_5th_no_4`: 3rd: Woods End Calico, owned by Doug & Noreen Loranger
5th: Long Hope Teeni Weeni, owned by Nellie Niewola
- `C1` / `3rd_then_5th_no_4`: 3rd: Winn Creek Jasper, owned by Tom Collmar
5th: Blue Dome Gimel, owned by George Ridler
- `C1` / `3rd_then_5th_no_4`: 3rd: >=~=Famneliff: Hutchy, owned by:Dave & Marti' McMahori
5th: Arlins My Ty, owned by Michael Beach
- `C1` / `3rd_then_5th_no_4`: 3rd: Jessie, owned by Sandy Brown
5th: Whispering Winds Pepsi, owned by R. & M. Minutello
- `C1` / `2nd_then_4th_no_3`: 2nd: Cody Waite
4th:
- `C1` / `2nd_then_4th_no_3`: 2nd: Stone's Throw Griffey, owned by Karen Merriman
4th: Jessie, owned by Sandy Brown

### `2001 Vol III pt 2_ocr_hqmax.txt` (FAIL)
- `C1` / `3rd_then_5th_no_4`: 3rd: Fox Island Sasha, owned by Zack & Tracy Waite
5th: Ash Creek Kelty, owned by Marty & Teresa Gottlieb
- `C1` / `3rd_then_5th_no_4`: 3rd: Pine Creek Little Nemo, owned by Rhonda Rebhorn
5th: Wolf Paw Gunner, owned by Dean & Beth Buchholz
- `C1` / `3rd_then_5th_no_4`: 3rd: Adins My Ty, owned by Michael Beach
5th: Hi & Low Belmont, owned by Richard & Margaret Minutello
- `C1` / `3rd_then_5th_no_4`: 3rd: Stealth Ranger, owned by Denise Neuner
5th: Rancho Amaz Sully's Quest, owned by Jill Goodman
- `C1` / `3rd_then_5th_no_4`: 3rd: Kerby's MacGyver, owned by Susan Hebert
5th: Farmstead Bella Faccia, owned by Tricia Candido
- `C1` / `3rd_then_5th_no_4`: 3rd:       Little Eden Vim, owned by Jessica Westbrooks
5th: Foxplay Racket,  owned by Cindy 0 Reily
- `C1` / `3rd_then_5th_no_4`: 3rd: Arlins My Ty, owned by Michael Beach
5th: Hi & Low Belmont, owned by Richard & Margaret Minutello
- `C1` / `3rd_then_5th_no_4`: 3rd: Athi=—-Old Glory Priscilla, owned by Pat Com!
5th: Westwood Jade, owned by Rick & Leslie Hemsing
- `C1` / `2nd_then_4th_no_3`: 2nd: Broken Ridge Snoopy Bear, owned by Kyle & Teresa Morrison
4th: Jaque Barker, owned by Rebecca Barker
- `C1` / `2nd_then_4th_no_3`: 2nd: Briamaich Soot, owned by Jack & Terri Batzer
4th: Sleepy Creek Spice, owned by D. Peck & J. Kozak
- `C1` / `2nd_then_4th_no_3`: 2nd:     Northgate Hallie, owned by Miche Bosch & Doug Tack
4th:      Morgan Hill Cecelia, owned by Don 2 Gail Stock
- `C1` / `2nd_then_4th_no_3`: 2nd: The Larches Bearette, owned by Rick & Mary Thomton
4th: Leewinds Sadie, owned by Margaret Strickler
