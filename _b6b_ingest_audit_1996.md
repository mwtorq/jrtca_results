# B6b cleanup + ingest audit — 1996

Catalog: `_OCR_CLEANUP_CATALOG_HANDOFF.md`
Volumes: 30  cleaned=1  PASS=0  WARN=5  FAIL=25
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
| FAIL | False | 36 | 39 | S4/O×25,C1×14,O6×12,C6/O1×12,S1-S3×10,C6×2 | `1996 Vol 1 pg 111-160 back reversed_ocr_hqmax.txt` |
| FAIL | False | 25 | 38 | S4/O×25,O6×18,C6/O1×13,S1-S3×4,C1×3 | `1996 Vol 1 pg 111-160 back_ocr_hqmax.txt` |
| FAIL | False | 41 | 40 | O6×23,S4/O×21,C6/O1×18,S1-S3×11,C1×7,C6×1 | `1996 Vol 1 pg 111-160 front_ocr_hqmax.txt` |
| FAIL | False | 4 | 2 | O6×3,S4/O×2,C1×1 | `1996 Vol 1 pg 161-178 back reversed_ocr_hqmax.txt` |
| WARN | False | 0 | 1 | S4/O×1 | `1996 Vol 1 pg 161-178 back_ocr_hqmax.txt` |
| WARN | False | 0 | 5 | S4/O×5 | `1996 Vol 1 pg 161-178 front_ocr_hqmax.txt` |
| WARN | False | 0 | 29 | S4/O×25,C6/O1×4 | `1996 Vol 1 pg 21-60 back reversed_ocr_hqmax.txt` |
| FAIL | False | 4 | 22 | S4/O×17,C6/O1×5,C1×2,S1-S3×1,O6×1 | `1996 Vol 1 pg 21-60 back_ocr_hqmax.txt` |
| FAIL | False | 11 | 23 | S4/O×20,S1-S3×6,C1×5,C6/O1×3 | `1996 Vol 1 pg 21-60 front_ocr_hqmax.txt` |
| FAIL | False | 19 | 31 | S4/O×25,O6×10,C1×6,C6/O1×5,S1-S3×3,C6×1 | `1996 Vol 1 pg 61-110 back reversed_ocr_hqmax.txt` |
| FAIL | False | 15 | 13 | S4/O×12,O6×7,C1×7,S1-S3×1,C6×1 | `1996 Vol 1 pg 61-110 back_ocr_hqmax.txt` |
| FAIL | False | 25 | 33 | S4/O×25,O6×18,C6/O1×7,C1×6,S1-S3×1,C6×1 | `1996 Vol 1 pg 61-110 front_ocr_hqmax.txt` |
| FAIL | False | 10 | 26 | S4/O×18,S4×8,O6×7,C1×2,S1-S3×1 | `1996 Vol II pg 163-220 back reversed_ocr_hqmax.txt` |
| FAIL | False | 16 | 37 | S4/O×17,O6×14,C6/O1×11,S4×9,C1×2 | `1996 Vol II pg 163-220 back_ocr_hqmax.txt` |
| WARN | False | 0 | 51 | S4/O×24,C6/O1×12,S4×8,C6×4,?/4th_then_6th_no_5×3 | `1996 Vol II pg 163-220 front_ocr_hqmax.txt` |
| FAIL | False | 13 | 34 | C6/O1×22,S4/O×12,C1×7,S1-S3×3,O6×3 | `1996 Vol II pg 23-92 back reversed_ocr_hqmax.txt` |
| FAIL | False | 9 | 14 | C6/O1×10,O6×4,C1×4,S4/O×3,S1-S3×1,C6×1 | `1996 Vol II pg 23-92 back_ocr_hqmax.txt` |
| FAIL | False | 23 | 11 | C1×12,S4/O×10,O6×8,S1-S3×3,C6/O1×1 | `1996 Vol II pg 23-92 front (missing 1 pgs)_ocr_hqmax.txt` |
| FAIL | False | 14 | 24 | S4/O×21,S1-S3×8,C1×5,?/4th_then_6th_no_5×3,O6×1 | `1996 Vol II pg 23-92 front (missing 2 pgs)_ocr_hqmax.txt` |
| WARN | True | 0 | 32 | S4/O×25,C6/O1×4,C6×3 | `1996 Vol II pg 23-92 front_ocr_hqmax.txt` |
| FAIL | False | 21 | 30 | S4/O×25,C1×12,O6×6,C6/O1×4,S1-S3×3,C6×1 | `1996 Vol II pg 93-162 back reversed_ocr_hqmax.txt` |
| FAIL | False | 13 | 42 | C6/O1×25,S4/O×16,O6×8,C1×3,S1-S3×2,C6×1 | `1996 Vol II pg 93-162 back_ocr_hqmax.txt` |
| FAIL | False | 33 | 37 | S4/O×25,O6×15,C1×13,C6/O1×9,S1-S3×5,?/4th_then_6th_no_5×2,C6×1 | `1996 Vol II pg 93-162 front_ocr_hqmax.txt` |
| FAIL | False | 6 | 7 | O6×6,C6/O1×6,S4/O×1 | `Document_2026-11-04_144208_ocr_hqmax.txt` |
| FAIL | False | 4 | 5 | S4/O×5,O6×2,C1×2 | `Document_2026-11-04_144530_ocr_hqmax.txt` |
| FAIL | False | 2 | 1 | O6×2,C6×1 | `Document_2026-11-04_145355_ocr_hqmax.txt` |
| FAIL | False | 3 | 3 | C6/O1×3,O6×2,C1×1 | `Document_2026-11-04_145925_ocr_hqmax.txt` |
| FAIL | False | 1 | 10 | C6×10,O6×1 | `Document_2026-11-04_151058_ocr_hqmax.txt` |
| FAIL | False | 10 | 22 | S4/O×12,C6/O1×10,O6×9,S1-S3×1 | `Document_2026-11-04_152834_ocr_hqmax.txt` |
| FAIL | False | 7 | 21 | C6×10,S4×8,O6×4,C1×3,?/4th_then_6th_no_5×2,S4/O×1 | `Document_2026-11-04_153208_ocr_hqmax.txt` |

## Sample residual hits (after cleanup)

### `1996 Vol 1 pg 111-160 back reversed_ocr_hqmax.txt` (FAIL)
- `S1-S3` / `place_smash`: e, owned by Joe & Evelyn Landini, owned by Michelle Ward & Gaye Redpath
- `S1-S3` / `place_smash`: ischief, owned by Andrew Walter, owned by Kathie Franklin
- `S1-S3` / `place_smash`: Brooke, owned by Joanna Proctor, owned by Joni Green
- `S1-S3` / `place_smash`: lee, owned by Rich Henry, owned by Linda Toscano
- `S1-S3` / `place_smash`: lvy, owned by Mark Thompson, owned by Kathryn Penn
- `S1-S3` / `place_smash`: Ivy, owned by Mark Thompson, owned by Kathryn Penn – Entries: 2
- `S1-S3` / `place_smash`: Sparky, owned by Julie Karagainis, owned by Robert McFarland
- `S1-S3` / `place_smash`: mp, owned by Bonnie Edison, owned by Teresa Wellman
- `S1-S3` / `place_smash`: ermit, owned by Bob Franklin, owned by Rhonda Yassin
- `S1-S3` / `place_smash`: a, owned by Lisa Drinkwater, owned by Bob Franklin
- `O6` / `owner_tail_trunc`: 4th: Killare Deaty of Old Glory, owned by Wendy Wyr
- `O6` / `owner_tail_trunc`: 1st: Hunters Rui Abigale, owned by Bill & Jackie Kell

### `1996 Vol 1 pg 111-160 back_ocr_hqmax.txt` (FAIL)
- `S1-S3` / `place_smash`: lake, owned by Karen Reavis, owned by James & Kelly Barbeau
- `S1-S3` / `place_smash`: lowlake, owned by Karen Reavis, owned by Bruce & Trish Frankenberg
- `S1-S3` / `place_smash`: Ith, owned by Stealth Terriers, owned by Bev Dalton
- `S1-S3` / `place_smash`: 5, owned by Gracie Bell, owned by Bev Dalton
- `O6` / `owner_tail_trunc`: 1st: Reyem Noxena, owned by Ken Meyer & Sig Sto
- `O6` / `owner_tail_trunc`: 3rd: Button Top Eelle Star of Wild Goose, owned by CJ & Oui
- `O6` / `owner_tail_trunc`: 12 1/2-15" Champion: Camerton Hall Brilliant, owned by Ke
- `O6` / `owner_tail_trunc`: 12 1/2-15" Reservz: Ardmore Run Wynona, owned by Bill
- `O6` / `owner_tail_trunc`: 10-12 1/2": Champon: Wild Goose National, owned by CJ
- `O6` / `owner_tail_trunc`: 12 1/2-15" Reserv: Button Top Belle Star, owned by CJ
- `O6` / `owner_tail_trunc`: 4th: Blue Moon Ema, owned by A
- `O6` / `owner_tail_trunc`: 6th: Tucker, owned by Paul & Det

### `1996 Vol 1 pg 111-160 front_ocr_hqmax.txt` (FAIL)
- `S1-S3` / `place_smash`: y, owned by Jeanette Hutchinson, owned by Bev Hirt
- `S1-S3` / `place_smash`: ester, owned by William & Gay O'Brien, owned by Bev Hirt
- `S1-S3` / `place_smash`: 7zle, owned by Sandra Ferber, owned by Doug Tack & Sandra Ferber
- `S1-S3` / `place_smash`: e, owned by Marty & Teresa Gottleib, owned by Nancy Bennett, owned by Lisa Johnson
- `S1-S3` / `place_smash`: rat, owned by Jan Moore, owned by Teresa & Martin Gottlieb
- `S1-S3` / `place_smash`: gie, owned by Jan Moore, owned by Dan Peck & Jeanne Kuzak
- `S1-S3` / `place_smash`: zle, owned by Sandra Ferber, owned by Debbie LaMantia
- `S1-S3` / `place_smash`: illon, owned by The Hollow Terriers, owned by Debbie LaMantia
- `S1-S3` / `place_smash`: r, owned by Eileen Koch, owned by Julie & Charlie Kemp
- `S1-S3` / `place_smash`: fotspot, owned by James Gupko, owned by Rick & Mary Thorton
- `S1-S3` / `place_smash`: Treat, owned by Lynn May Maasles, owned by Debbie McWilliams, owned by Janet Nugent, owned by Jim and Carey Ellison
- `O6` / `owner_tail_trunc`: 1st: Lilly, owned by Kz

### `1996 Vol 1 pg 161-178 back reversed_ocr_hqmax.txt` (FAIL)
- `O6` / `owner_tail_trunc`: Champion: Cotquest Minute, owned by Gaye Red
- `O6` / `owner_tail_trunc`: 1st: The Hollov Gallahad, owned by The Hollow Ter
- `O6` / `owner_tail_trunc`: 2nd: Meynell Re:het of Briarpatch, owned by Jack & T
- `S4/O` / `missing_owned_by`: 2nd: Shilo, ownedby Debbie Mutimer
- `S4/O` / `missing_owned_by`: 4th: The CormnerBully, ownedby Chris Watefield
- `C1` / `class_header_gap`: 1st: High & Low Risky, owned by Melissa Lowe

### `1996 Vol 1 pg 161-178 back_ocr_hqmax.txt` (WARN)
- `S4/O` / `missing_owned_by`: 2nd: Shilo, ownedby Debbie Mutimer

### `1996 Vol 1 pg 161-178 front_ocr_hqmax.txt` (WARN)
- `S4/O` / `missing_owned_by`: 1st: Russell-M-Up Pagan of Cottage Garden Climb, Daniel VanHorn
- `S4/O` / `missing_owned_by`: 3rd: Jack of Hearts Onimod, owned t
- `S4/O` / `missing_owned_by`: 4th: Hidden Valley Crumpet, owned t
- `S4/O` / `missing_owned_by`: 1st: Little Orbit of Cortenbach, ownec
- `S4/O` / `missing_owned_by`: 3rd: Ruff N Tumble Braque, owned b

### `1996 Vol 1 pg 21-60 back reversed_ocr_hqmax.txt` (WARN)
- `S4/O` / `missing_owned_by`: 4th: Razor, ownedby Ken Meyers
- `S4/O` / `missing_owned_by`: 1st: Trix, ownedby Fraley
- `S4/O` / `missing_owned_by`: 6th: Derby, ownedby Nona & Gary Carroll
- `S4/O` / `missing_owned_by`: 1st: Nevada, own:d by Laura O'Leary
- `S4/O` / `missing_owned_by`: 4th: Rudy, ownedby J.W. Woodward
- `S4/O` / `missing_owned_by`: 6th: Jack, ownedby Les Cook
- `S4/O` / `missing_owned_by`: 4th: Trix, ownedby Chris Fraley
- `S4/O` / `missing_owned_by`: 5th: Fury, ownedby Ginny Sloan
- `S4/O` / `missing_owned_by`: 5th: Blackland Toby, ou
- `S4/O` / `missing_owned_by`: 6th: Windsor Nails,owr
- `S4/O` / `missing_owned_by`: 3rd: Blackland Salty, ov
- `S4/O` / `missing_owned_by`: 5th: Iam Prancer, own

### `1996 Vol 1 pg 21-60 back_ocr_hqmax.txt` (FAIL)
- `S1-S3` / `place_smash`: 1st: Trix, owned by Chris Fraleyond: Good Times Seminole Wind, owned by Barbara Spruill
- `O6` / `owner_tail_trunc`: Reserve: Good Tmes Seminole Wind, owned by Ba
- `S4/O` / `missing_owned_by`: 3rd: Abbey, own:d by Jan Black
- `S4/O` / `missing_owned_by`: 2nd: Jake, ownedby Pam Malloy
- `S4/O` / `missing_owned_by`: 5th: Bear, ownedby Eddie Barrett
- `S4/O` / `missing_owned_by`: 3rd: Kate, ownedby John Chandler
- `S4/O` / `missing_owned_by`: 5th: Frenzy, own:d by Ed Barrett
- `S4/O` / `missing_owned_by`: 3rd: Zoe, ownedby Sue Wilson
- `S4/O` / `missing_owned_by`: 4th: Zoe, ownedby Sue Wilson
- `S4/O` / `missing_owned_by`: 4th: Diva, ownedby Julia McCarthy
- `S4/O` / `missing_owned_by`: 6th: Derby, ownedby Nona & Gary Carroll
- `S4/O` / `missing_owned_by`: 1st: Nevada, own:d by Laura O'Leary

### `1996 Vol 1 pg 21-60 front_ocr_hqmax.txt` (FAIL)
- `S1-S3` / `place_smash`: s, owned by Doug Stephenson, owned by Doug Stephenson
- `S1-S3` / `place_smash`: ie, owned by Julie Felten, owned by Didi Gough
- `S1-S3` / `place_smash`: le, owned by Jeffrey Gibson, owned by Bob Franklin
- `S1-S3` / `place_smash`: Flat, owned by Jamie Sproles, owned by RA & Kris Mackay
- `S1-S3` / `place_smash`: a, owned by Jeffrey Gibson, owned by Bob Franklin
- `S1-S3` / `place_smash`: nberg, owned by Kathy Walker White, owned by Dan Peck
- `S4/O` / `missing_owned_by`: 2nd: Ms. Scarlett of Heaven Hill, own:
- `S4/O` / `missing_owned_by`: 5th: Farmcliff Donny, ov
- `S4/O` / `missing_owned_by`: Reserve: Top "E" Mill, c
- `S4/O` / `missing_owned_by`: 2nd: Seaview Soozi, OW
- `S4/O` / `missing_owned_by`: 3rd: The Bowery Mist, c
- `S4/O` / `missing_owned_by`: 1st: Veronica, owned b

### `1996 Vol 1 pg 61-110 back reversed_ocr_hqmax.txt` (FAIL)
- `S1-S3` / `place_smash`: 2lli, owned by Barbara Tyler, owned by Bonnie Edison
- `S1-S3` / `place_smash`: 6th: Molly, owned by Ann Ingram, owned by Willow Hindle-Rennie
- `S1-S3` / `place_smash`: 'ma, owned by Ken Meyer, owned by Pam Molloy
- `O6` / `owner_tail_trunc`: 1st: Courtwood Nipper, owned by Lc
- `O6` / `owner_tail_trunc`: 1st: Button Top Btlle Star of Wild Goose, owned by C
- `O6` / `owner_tail_trunc`: 4th: Wild Goose Fentucky, owned by CJ & Ouida Har
- `O6` / `owner_tail_trunc`: 2nd: All Seasons Woody of Dutch Creek, owned by Be
- `O6` / `owner_tail_trunc`: 3rd: Wild Goose Dip Stick, owned by CJ & Ouida Har
- `O6` / `owner_tail_trunc`: 3rd: Firewheel Ptatom Jack of T-Vols, owned by Bill
- `O6` / `owner_tail_trunc`: 6th: Edgefield Trston, owned by Bob & Melissa Van
- `O6` / `owner_tail_trunc`: 3rd: Wild Goose National, owned by CJ & Ouida Har
- `O6` / `owner_tail_trunc`: 2nd: Golden HillsShady Lady Bug, owned by Didi

### `1996 Vol 1 pg 61-110 back_ocr_hqmax.txt` (FAIL)
- `S1-S3` / `place_smash`: 1st: Lacey, owned by Margaret Stricklandond: Red Oak Blue Bonnet, owned by Kenneth
- `O6` / `owner_tail_trunc`: 3rd: Foxwarren Kely of Highland Bay, owned by Art
- `O6` / `owner_tail_trunc`: 2nd: Rustler Jingles Judy, owned by David & Lisa Mcl
- `O6` / `owner_tail_trunc`: 3rd: Balckland Tuno of Iron Water, owned by Guy
- `O6` / `owner_tail_trunc`: 1st: Good Times Pobr Snow Baby, owned by Stev
- `O6` / `owner_tail_trunc`: 4th: Reuans Veronia@ of Trebor Chase, owned by Rob
- `O6` / `owner_tail_trunc`: 2nd: TF Halftrack ofFox Tale, owned by Janice & Mar
- `O6` / `owner_tail_trunc`: 3rd: Good Times Polar Snow Baby, owned by Stev
- `S4/O` / `missing_owned_by`: 3rd: Eddie, ownedby Brian & Karen Wilson
- `S4/O` / `missing_owned_by`: 3rd: Kato, ownedby Ken Tate
- `S4/O` / `missing_owned_by`: 2nd: Mira, ownedby Jane Schreiner
- `S4/O` / `missing_owned_by`: 6th: Lilith, ownedby Phyllis Massey

### `1996 Vol 1 pg 61-110 front_ocr_hqmax.txt` (FAIL)
- `S1-S3` / `place_smash`: 0, owned by Doris Sneider, owned by Dan & Sharon Steckline
- `O6` / `owner_tail_trunc`: 1st: Wamp, owned by p
- `O6` / `owner_tail_trunc`: Rose, owned by Mike
- `O6` / `owner_tail_trunc`: Reserve: Dole Mother, owned by Marchiinski Cheryl Wea
- `O6` / `owner_tail_trunc`: 3rd: Rustlerllie, owned by Mike & D
- `O6` / `owner_tail_trunc`: 4th: Sadie R OSe, owned by Mike
- `O6` / `owner_tail_trunc`: 6th: White T, owned by Jos
- `O6` / `owner_tail_trunc`: 6th: Tortilla Flat Reflex, owned by Mary Anne Maj
- `O6` / `owner_tail_trunc`: Reserve: Gold Hilld Rush, owned by Jeff & Con
- `O6` / `owner_tail_trunc`: Reserve: Shenanigans Will, owned by Mary Abb
- `O6` / `owner_tail_trunc`: Best: Foxfield Garth of Lost Creek, owned by Del
- `O6` / `owner_tail_trunc`: 5th: Copper Horse Windy, owned by David & Lis

### `1996 Vol II pg 163-220 back reversed_ocr_hqmax.txt` (FAIL)
- `S1-S3` / `place_smash`: 6th: Ivin, owned by Karen Vernon, owned by Doug & Noreen Loranger
- `S4` / `mangled_by`: 4th: Not proviced by Trial Chairperson
- `S4` / `mangled_by`: 4th: Not reported by Trial Chairperson
- `S4` / `mangled_by`: 5th: Not reportei by Trial Chairperson
- `S4` / `mangled_by`: 6th: Not reportei by Trial Chairperson
- `S4` / `mangled_by`: 2nd: Daytona, ovner not reported by Trial Chairperson
- `S4` / `mangled_by`: 5th: Montana, ovner not reported by Trial Chairperson
- `S4` / `mangled_by`: 4th: Not reportel by Trial Chairperson
- `O6` / `owner_tail_trunc`: 10-12 1/2" Resene: Cromwell Stimpy, owned by H
- `O6` / `owner_tail_trunc`: 4th: White Stockings Cork, owned by Mike & Pam
- `O6` / `owner_tail_trunc`: 5th:  Will-O-Mooi Rex, owned by Michelle Williams & Kimberly Hor
- `O6` / `owner_tail_trunc`: 3rd: The Hollov Markham of Will-O-Moor, owned by Michelle Williams & Kimberly Hor

### `1996 Vol II pg 163-220 back_ocr_hqmax.txt` (FAIL)
- `S4` / `mangled_by`: 4th: Not reportel by Trial Chairperson
- `S4` / `mangled_by`: 5th: Not reportel by Trial Chairperson
- `S4` / `mangled_by`: 6th: Not reportel by Trial Chairperson
- `S4` / `mangled_by`: 2nd: Daytona, ovner not reported by Trial Chairperson
- `S4` / `mangled_by`: 5th: Montana, ovner not reported by Trial Chairperson
- `S4` / `mangled_by`: 4th: Not reportei by Trial Chairperson
- `S4` / `mangled_by`: 6th: Not provide by Trial Chairperson
- `S4` / `mangled_by`: 4th: Not proviced by Trial Chairperson
- `O6` / `owner_tail_trunc`: 5th: Lost Creeks Kacey, owned by Vine
- `O6` / `owner_tail_trunc`: 3rd: The Hollow Markham of Will-O-Moor, owned by Michelle Williams & Kimberly Hor
- `O6` / `owner_tail_trunc`: 6th: Will-O-Maor Rex, owned by Michelle Williams & Kimberly Hor
- `O6` / `owner_tail_trunc`: 5th: Will-O-Moa Rex, owned by Michelle Williams & Kimberly Hor

### `1996 Vol II pg 163-220 front_ocr_hqmax.txt` (WARN)
- `S4` / `mangled_by`: 4th: Not reported by Trial Chairperson
- `S4` / `mangled_by`: 3rd: Not reported by Trial Chairperson
- `S4` / `mangled_by`: 5th: Not reported by Trial Chairperson
- `S4` / `mangled_by`: 6th: Not reported by Trial Chairperson
- `?` / `4th_then_6th_no_5`: 4th: Risky of High & Low, owned by Mellisa Lowe
6th: High & Low Frostbite of Running Wild, owned by Bob Zeiner
- `?` / `4th_then_6th_no_5`: 4th: Bently, owned by Tabitha & Roger Shury
6th: Agnew, owned by Margo Weston
- `?` / `4th_then_6th_no_5`: 4th: Crossewinds Sarah, owned by Becky Crosse
6th: Willowbend Dalley Up, owned by Claudia Spra
- `S4/O` / `missing_owned_by`: 3rd: Merill's mountain Christmas Belle, owned
- `S4/O` / `missing_owned_by`: 4th: Three Oaks Penny of Green Acres, owner
- `S4/O` / `missing_owned_by`: 2nd: Trebor Chase Black Jack Daniels, owned b
- `S4/O` / `missing_owned_by`: Reserve: Crosswinds Puzzle of Orchard Hill, own
- `S4/O` / `missing_owned_by`: 3rd: Falling Branch Celia, owned b

### `1996 Vol II pg 23-92 back reversed_ocr_hqmax.txt` (FAIL)
- `S1-S3` / `place_smash`: 5th: SpringateRuff-n-Tuff, owned by Amy, owned by Dog Pups, 9 up to 12 months
- `S1-S3` / `place_smash`: rip, owned by Marty & Teresa Gotttleib,0bb, owned by Linda Miller
- `S1-S3` / `place_smash`: yn, owned by Laura Harakaly, owned by Dan & Karen Kinsley
- `O6` / `owner_tail_trunc`: 4th: Molly, owned by Mary Web
- `O6` / `owner_tail_trunc`: 5th: Bonnie Bee, owned by Gavin Com
- `O6` / `owner_tail_trunc`: 3rd: Windsony Soda, owned by David & Susan Cra
- `S4/O` / `missing_owned_by`: 2nd: Kilhaven Rudi, c
- `S4/O` / `missing_owned_by`: 4th: Fox Run Tyler, c
- `S4/O` / `missing_owned_by`: 2nd: Sparky, twned
- `S4/O` / `missing_owned_by`: 5th: Hillside Biddy, c
- `S4/O` / `missing_owned_by`: 4th: Hillside Jeslyn, o
- `S4/O` / `missing_owned_by`: 5th: Big Sky Swlo, ow

### `1996 Vol II pg 23-92 back_ocr_hqmax.txt` (FAIL)
- `S1-S3` / `place_smash`: 5th: SpringateRuff-n-Tuff, owned by Amy, owned by Dog Pups, 9 up to 12 months
- `O6` / `owner_tail_trunc`: 5th: Bonnie Bee, owned by Gavin Com
- `O6` / `owner_tail_trunc`: 4th: Molly, owned by Mary Web
- `O6` / `owner_tail_trunc`: 4th: Mineral Sorings Indiana Bones, owned by Mari
- `O6` / `owner_tail_trunc`: 2nd: Ash Creek Matt, owned by Marty & Teresa Got
- `S4/O` / `missing_owned_by`: 3rd: Jill, ownedby Diana Bartells
- `S4/O` / `missing_owned_by`: 3rd: AE die A mn: Céiimemtme aimed Bu William R (av OYRrien AgLity 1, VIT Led
- `S4/O` / `missing_owned_by`: 5th: Megan Janson, Kelly Hosier, Erik Harakaly
- `C6/O1` / `bare_entries`: Entries:
- `C6` / `orphan_entry_count`: 4
- `C1` / `class_header_gap`: 1st: Lucy Mae, owned by J.Neff & J.Gay
- `C1` / `class_header_gap`: 1st: Jera-lyn, owned by Maureen McKernan

### `1996 Vol II pg 23-92 front (missing 1 pgs)_ocr_hqmax.txt` (FAIL)
- `S1-S3` / `place_smash`: Champion: Single Single Track Track Hunter, Kasey, owned by, owned by by Mark James & Lisa Titus Green
- `S1-S3` / `place_smash`: 12 12 1/2-15" Champion: Wyndcroft Will-O-Moor Natasha, Riley, owned by, owned by by Kathy Mark & Hunter Missy & Kulbacty Jeff Finkernagel
- `S1-S3` / `place_smash`: al, owned by Tony Mason, owned by Mark Thompson
- `O6` / `owner_tail_trunc`: 3rd: Deegan of Northgate, owned by Doug
- `O6` / `owner_tail_trunc`: 4th: Farmcliff Hampton, owned by Vicki Jot
- `O6` / `owner_tail_trunc`: 4th: Lickity Split Sassy, owned by Bob Fra
- `O6` / `owner_tail_trunc`: 2nd: Tucker, owned by Jc
- `O6` / `owner_tail_trunc`: 3rd: Rudy, owned by Jea
- `O6` / `owner_tail_trunc`: 1st: Haley's Comet, owned by Karen Rea
- `O6` / `owner_tail_trunc`: of Meadowlake, owned by Karen Rea
- `O6` / `owner_tail_trunc`: Haleys Comet, owned by Karen Rea
- `S4/O` / `missing_owned_by`: 1st: Bobby Duty, Ili

### `1996 Vol II pg 23-92 front (missing 2 pgs)_ocr_hqmax.txt` (FAIL)
- `S1-S3` / `place_smash`: irl, owned by J. Jankowski & K. Morande, owned by Genie Franklin
- `S1-S3` / `place_smash`: ton, owned by Vicki Johnson, owned by Doug & Sue Tack, owned by Bob Franklin
- `S1-S3` / `place_smash`: isha, owned by K. Hunter & P. Finkernag, owned by Kevin & Melissa McGrath
- `S1-S3` / `place_smash`: itewitch, owned by P. Hartman & K. McC, owned by R. & D. Zampella
- `S1-S3` / `place_smash`: rk, owned by Linda Cowasjee, owned by The Hollow Terriers
- `S1-S3` / `place_smash`: Baybriar, owned by Jeanette Hutchinsc, owned by Lisa Johnson, owned by Sandra Ferber
- `S1-S3` / `place_smash`: r, owned by Kate Bomberger, owned by Kate Bomberger, owned by Bob Franklin, owned by Margaret Strickland
- `S1-S3` / `place_smash`: t, owned by Phil Hawkins, owned by Joni, Dale & Becky Green
- `?` / `4th_then_6th_no_5`: 4th: Blue Moon Gunner, owned by Anne Davis
6th: Prestige Farms Pollywog, owned by D'arry Jone Frank
- `?` / `4th_then_6th_no_5`: 4th: TF Ivana Fox, owned by Willow Rennie
6th: K.C, owned by Theresa Gadoury
- `?` / `4th_then_6th_no_5`: 4th: Swift River Jasper, o
6th: Pine Hill Chase of, owned by Chuck & Diana Hufnagel
- `O6` / `owner_tail_trunc`: 3rd: Farmcliff Betty, owned by Franklin & Ci

### `1996 Vol II pg 23-92 front_ocr_hqmax.txt` (WARN)
- `S4/O` / `missing_owned_by`: 1st: Bobby Duty, Iif
- `S4/O` / `missing_owned_by`: Reserve: Foxfield Flash, owned b
- `S4/O` / `missing_owned_by`: 2nd: Alasia Sable, ow
- `S4/O` / `missing_owned_by`: 3rd: Tarzan, owned L
- `S4/O` / `missing_owned_by`: 5th: Mo Clilean, owne
- `S4/O` / `missing_owned_by`: 1st: Hillside Joslyn, o
- `S4/O` / `missing_owned_by`: 2nd: Sportster, owned
- `S4/O` / `missing_owned_by`: 5th: Casey Jones, owr
- `S4/O` / `missing_owned_by`: 3rd: Farmcliff Sugar, ov
- `S4/O` / `missing_owned_by`: 5th: Big Sky Annie, owr
- `S4/O` / `missing_owned_by`: 6th: Farmcliff Becky, ov
- `S4/O` / `missing_owned_by`: 3rd: MLQH Muffin, owne

### `1996 Vol II pg 93-162 back reversed_ocr_hqmax.txt` (FAIL)
- `S1-S3` / `place_smash`: gie, owned by Charlene Schlueter, owned by Aurora Rubel
- `S1-S3` / `place_smash`: hance, owned by Jill Nichols, owned by Kathy Oelrich
- `S1-S3` / `place_smash`: Jer, owned by Catherine Brown, owned by Doug & Sue Tack
- `O6` / `owner_tail_trunc`: 4th: Frost, owned by Andrea Vaz
- `O6` / `owner_tail_trunc`: 1st: Tag, owned by Ka
- `O6` / `owner_tail_trunc`: 4th: Windermer Nitewitch of Sow's Ear, owned by Paul Hartman & Kai
- `O6` / `owner_tail_trunc`: 12 1/2-15" Champion: Qualyns Falcon of Blue Barns, owned by Ru
- `O6` / `owner_tail_trunc`: Reserve: Goliath, owned by Jim Yue
- `O6` / `owner_tail_trunc`: 1st: Goliath, owned by Jim Yue
- `S4/O` / `missing_owned_by`: 5th: Jewel, own:d by Paula Hughes
- `S4/O` / `missing_owned_by`: 3rd: E. Carolita Eli, Shane & Deree Schilling
- `S4/O` / `missing_owned_by`: 4th: Wild Remain, owrbth: Eastlake Mejan o

### `1996 Vol II pg 93-162 back_ocr_hqmax.txt` (FAIL)
- `S1-S3` / `place_smash`: land, owned by Lloyd & Shirley Cox, owned by Cheryl Hart
- `S1-S3` / `place_smash`: ns, owned by Teresa Wellman, owned by Jerry Roach
- `O6` / `owner_tail_trunc`: Reserve: Goliath, owned by Jim Yue
- `O6` / `owner_tail_trunc`: 1st: Goliath, owned by Jim Yue
- `O6` / `owner_tail_trunc`: 5th: Cortenbachs Moon Wizard of Oz, owned by Lis
- `O6` / `owner_tail_trunc`: 5th: Cortenbact's Moon Wizard of Oz, owned by Lis
- `O6` / `owner_tail_trunc`: 4th: Horsemaser's Willy, owned by Neil & Pam Cal
- `O6` / `owner_tail_trunc`: 1st: Beau Monle Paige of Coldwater, owned by Mi
- `O6` / `owner_tail_trunc`: 1st: Fox Run Ben, owned by Ker
- `O6` / `owner_tail_trunc`: 4th: Frost, owned by Andrea Vaz
- `S4/O` / `missing_owned_by`: 1st: Roxi, ownedby Kim & Nick Pelych
- `S4/O` / `missing_owned_by`: 1st: Tag, ownedby Kathy Oelrich

### `1996 Vol II pg 93-162 front_ocr_hqmax.txt` (FAIL)
- `S1-S3` / `place_smash`: Ripley, owned by Kendal Makowicz, owned by Antonio & Barbara Sullo
- `S1-S3` / `place_smash`: Y, owned by Bob Franklin, owned by Chuck Schobert
- `S1-S3` / `place_smash`: gsy, owned by Richard & Annetee Ken:, owned by Kim Hunter & Jim Hughes, owned by Charlie & Julie Kemp
- `S1-S3` / `place_smash`: Farmcliff, owned by Doug & Sue Tack, owned by Bob Franklin
- `S1-S3` / `place_smash`: elsea, owned by Bety McArthur, owned by Nelliw Niewola – Entries: 6
- `?` / `4th_then_6th_no_5`: 4th: Vagabond Voodoo of Little Eden, owned by Michelle Ward
6th: Ash Creek Ghillie, owned by Marty & Theresa Gottlieb
- `?` / `4th_then_6th_no_5`: 4th: Patty, owned by T.L. Henslee
6th: Red Oak Maddy of Gunsmoke, ow
- `O6` / `owner_tail_trunc`: 4th: Wyncroft Natasha, owned by K
- `O6` / `owner_tail_trunc`: 1st: Wyncroft Natasha, owned by K
- `O6` / `owner_tail_trunc`: 3rd: Quarrystone Pita, owned by Nc
- `O6` / `owner_tail_trunc`: 4th: Windyview Briar, owned by Eile
- `O6` / `owner_tail_trunc`: 1st: Raven of Waymore, owned by Shane & De

### `Document_2026-11-04_144208_ocr_hqmax.txt` (FAIL)
- `O6` / `owner_tail_trunc`: 1st: Camerton Hall Izod, owned by Pauline & J
- `O6` / `owner_tail_trunc`: 1st: Camerton Hall Salute, owned by Jan & Mz
- `O6` / `owner_tail_trunc`: 2nd: T.F. Half Track, owned by Jan & Mark Bjo
- `O6` / `owner_tail_trunc`: 3rd: Three Oaks Dentilla, owned by Kesha Sar
- `O6` / `owner_tail_trunc`: 2nd: Lands End Bully, owned by Doris & Guy
- `O6` / `owner_tail_trunc`: 5th: Heaven Hill Guiness, owned by Shelly Hol
- `S4/O` / `missing_owned_by`: 2nd: Ms. Scarlett of Heaven Hill, owned b
- `C6/O1` / `bare_entries`: Entries:

### `Document_2026-11-04_144530_ocr_hqmax.txt` (FAIL)
- `O6` / `owner_tail_trunc`: 3rd: Camerton Hall Hookie, owned by Ste
- `O6` / `owner_tail_trunc`: 6th: Westside Design, owned by Hugo
- `S4/O` / `missing_owned_by`: 1st: Tortilla Flat Crispy Tortilla Jones, Diana Pappan
- `S4/O` / `missing_owned_by`: 2nd: Bobby Duty, Ill
- `S4/O` / `missing_owned_by`: 3rd: Brookmill Farm Little Bamber, owned
- `S4/O` / `missing_owned_by`: 4th: Sunset Valley Dottie of Iron Water, o
- `S4/O` / `missing_owned_by`: 1st: Treesbark Flannigan, owned b y Janet Sproles & Marcy Cross
- `C1` / `class_header_gap`: 1st: Impressive Dynamite, owned by Doris Sneider
- `C1` / `class_header_gap`: 1st: Lickity Split Nifty, owned by Darlene McInnes

### `Document_2026-11-04_145355_ocr_hqmax.txt` (FAIL)
- `O6` / `owner_tail_trunc`: Conquest, owned by Ga
- `O6` / `owner_tail_trunc`: Foxnorton, owned by Ka
- `C6` / `orphan_entry_count`: 3

### `Document_2026-11-04_145925_ocr_hqmax.txt` (FAIL)
- `O6` / `owner_tail_trunc`: 2nd: Show-Me Bernard of Heartstone, owned by Lyr
- `O6` / `owner_tail_trunc`: 1st: Clear Fork Rapid of Broken Arrow, owned by P
- `C6/O1` / `bare_entries`: Entries:
- `C1` / `class_header_gap`: 1st: Whiriwind Delilah, owned by Melanie Smaill

### `Document_2026-11-04_151058_ocr_hqmax.txt` (FAIL)
- `O6` / `owner_tail_trunc`: Fitaeroe SEEN, owned by Ralph & Bol
- `C6` / `orphan_entry_count`: 1
- `C6` / `orphan_entry_count`: 3
- `C6` / `orphan_entry_count`: 7
- `C6` / `orphan_entry_count`: 2

### `Document_2026-11-04_152834_ocr_hqmax.txt` (FAIL)
- `S1-S3` / `place_smash`: 5th: Easton, owned by Points Nipper, owned by Sally Gay
- `O6` / `owner_tail_trunc`: 2nd: Crosswinds Trask of Eastlake, owned by Will
- `O6` / `owner_tail_trunc`: 4th: Holfield Jill lll of Orchard Hill, owned by Cher
- `O6` / `owner_tail_trunc`: 3rd: Sundowner Farms Lacy Jane, owned by De
- `O6` / `owner_tail_trunc`: 5th: Sundowner Farms Tipster, owned by Alta
- `O6` / `owner_tail_trunc`: 6th: Sundowner Farms Pistol Pete, owned by Alta
- `O6` / `owner_tail_trunc`: 2nd: Darby's Paper Chase Penny, owned by Sa
- `O6` / `owner_tail_trunc`: 4th: Kerry O'Toole of Badakashan, owned by Fay
- `O6` / `owner_tail_trunc`: 5th: Badakashan Celestia Haley, owned by Fay
- `O6` / `owner_tail_trunc`: 4th: Rustler's Emma Peel, owned by Sloan's Ri
- `S4/O` / `missing_owned_by`: 1st: Bear Creek Maggie of Timber Ridge, owned
- `S4/O` / `missing_owned_by`: 2nd: Fornit, Gail Jennings

### `Document_2026-11-04_153208_ocr_hqmax.txt` (FAIL)
- `S4` / `mangled_by`: 4th: Not reported by Trial Chairperson
- `S4` / `mangled_by`: 3rd: Not reported by Trial Chairperson
- `S4` / `mangled_by`: 5th: Not reported by Trial Chairperson
- `S4` / `mangled_by`: 6th: Not reported by Trial Chairperson
- `?` / `4th_then_6th_no_5`: 4th: Briarpatch Skoal, owned by Carl Finglass
6th: Farmcliff Blaze, owned by Bob & Genie Franklin
- `?` / `4th_then_6th_no_5`: 4th: Lucifer, owned by Linda L. Nickel
6th: Green Gate Tomba, owned by Joe & Priscilla Testa
- `O6` / `owner_tail_trunc`: Briarpatch, owned by Tere
- `O6` / `owner_tail_trunc`: White Gate, owned by Bill & Na
- `O6` / `owner_tail_trunc`: Vagabond V, owned by Mich
- `O6` / `owner_tail_trunc`: Eastlake E, owned by Wi
- `S4/O` / `missing_owned_by`: 1st: Polar Snow Baby of Good Times, 6wned by Steve Spruill
- `C6` / `orphan_entry_count`: 24
