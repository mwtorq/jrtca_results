# B6b cleanup + ingest audit — 1996

Catalog: `_OCR_CLEANUP_CATALOG_HANDOFF.md`
Volumes: 30  cleaned=21  PASS=10  WARN=0  FAIL=20
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
| FAIL | True | 41 | 0 | O6×21,S4/O×13,S1-S3×4,C1×3 | `1996 Vol 1 pg 111-160 back_ocr_hqmax.txt` |
| FAIL | True | 58 | 0 | O6×25,S4/O×14,S1-S3×11,C1×8 | `1996 Vol 1 pg 111-160 front_ocr_hqmax.txt` |
| PASS | False | 0 | 0 | — | `1996 Vol 1 pg 161-178 back reversed_ocr_hqmax.txt` |
| PASS | False | 0 | 0 | — | `1996 Vol 1 pg 161-178 back_ocr_hqmax.txt` |
| PASS | False | 0 | 0 | — | `1996 Vol 1 pg 161-178 front_ocr_hqmax.txt` |
| PASS | True | 0 | 0 | — | `1996 Vol 1 pg 21-60 back reversed_ocr_hqmax.txt` |
| FAIL | True | 8 | 0 | S4/O×4,C1×2,S1-S3×1,O6×1 | `1996 Vol 1 pg 21-60 back_ocr_hqmax.txt` |
| FAIL | True | 28 | 0 | S4/O×16,S1-S3×6,C1×5,O6×1 | `1996 Vol 1 pg 21-60 front_ocr_hqmax.txt` |
| FAIL | True | 41 | 0 | S4/O×19,O6×13,C1×6,S1-S3×3 | `1996 Vol 1 pg 61-110 back reversed_ocr_hqmax.txt` |
| FAIL | False | 17 | 0 | O6×7,C1×7,S4/O×2,S1-S3×1 | `1996 Vol 1 pg 61-110 back_ocr_hqmax.txt` |
| FAIL | True | 45 | 0 | O6×24,S4/O×14,C1×6,S1-S3×1 | `1996 Vol 1 pg 61-110 front_ocr_hqmax.txt` |
| FAIL | True | 32 | 0 | S4/O×13,S4×8,O6×8,C1×2,S1-S3×1 | `1996 Vol II pg 163-220 back reversed_ocr_hqmax.txt` |
| FAIL | True | 37 | 0 | O6×16,S4×9,S4/O×9,C1×3 | `1996 Vol II pg 163-220 back_ocr_hqmax.txt` |
| FAIL | True | 28 | 0 | S4/O×17,S4×8,O6×1,C6×1,C1×1 | `1996 Vol II pg 163-220 front_ocr_hqmax.txt` |
| FAIL | True | 24 | 0 | S4/O×8,C1×7,O6×6,S1-S3×3 | `1996 Vol II pg 23-92 back reversed_ocr_hqmax.txt` |
| FAIL | True | 13 | 0 | C1×7,O6×5,S1-S3×1 | `1996 Vol II pg 23-92 back_ocr_hqmax.txt` |
| FAIL | True | 35 | 0 | C1×12,O6×11,S4/O×9,S1-S3×3 | `1996 Vol II pg 23-92 front (missing 1 pgs)_ocr_hqmax.txt` |
| FAIL | True | 30 | 0 | S4/O×12,S1-S3×8,O6×5,C1×5 | `1996 Vol II pg 23-92 front (missing 2 pgs)_ocr_hqmax.txt` |
| FAIL | True | 37 | 0 | S1-S3×11,S4/O×11,C1×11,O6×4 | `1996 Vol II pg 23-92 front_ocr_hqmax.txt` |
| FAIL | True | 53 | 0 | S4/O×25,C1×14,O6×11,S1-S3×3 | `1996 Vol II pg 93-162 back reversed_ocr_hqmax.txt` |
| FAIL | True | 27 | 0 | O6×13,S4/O×9,C1×3,S1-S3×2 | `1996 Vol II pg 93-162 back_ocr_hqmax.txt` |
| FAIL | True | 29 | 0 | S4/O×11,O6×10,S1-S3×5,C1×3 | `1996 Vol II pg 93-162 front_ocr_hqmax.txt` |
| PASS | True | 0 | 0 | — | `Document_2026-11-04_144208_ocr_hqmax.txt` |
| PASS | False | 0 | 0 | — | `Document_2026-11-04_144530_ocr_hqmax.txt` |
| PASS | False | 0 | 0 | — | `Document_2026-11-04_145355_ocr_hqmax.txt` |
| PASS | False | 0 | 0 | — | `Document_2026-11-04_145925_ocr_hqmax.txt` |
| PASS | False | 0 | 0 | — | `Document_2026-11-04_151058_ocr_hqmax.txt` |
| FAIL | True | 9 | 0 | S4/O×8,O6×1 | `Document_2026-11-04_152834_ocr_hqmax.txt` |
| FAIL | False | 16 | 0 | S4×8,O6×4,C1×3,S4/O×1 | `Document_2026-11-04_153208_ocr_hqmax.txt` |

## Sample residual hits (after cleanup)

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
- `O6` / `owner_tail_trunc`: 5th: Sand Countr Kelcey, owned by ow

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

### `1996 Vol 1 pg 21-60 back_ocr_hqmax.txt` (FAIL)
- `S1-S3` / `place_smash`: 1st: Trix, owned by Chris Fraleyond: Good Times Seminole Wind, owned by Barbara Spruill
- `O6` / `owner_tail_trunc`: Reserve: Good Tmes Seminole Wind, owned by Ba
- `S4/O` / `missing_owned_by`: 3rd: Abbey, own:d by Jan Black
- `S4/O` / `missing_owned_by`: 5th: Frenzy, own:d by Ed Barrett
- `S4/O` / `missing_owned_by`: 1st: Nevada, own:d by Laura O'Leary
- `S4/O` / `missing_owned_by`: 1st: T.J.Farm Jasmine, owne
- `C1` / `class_header_gap`: 1st: Wildgoose National, owned by C. J. Harris
- `C1` / `class_header_gap`: 1st: Rainland Juliet, owned by Robert & Linda Fleck

### `1996 Vol 1 pg 21-60 front_ocr_hqmax.txt` (FAIL)
- `S1-S3` / `place_smash`: s, owned by Doug Stephenson, owned by Doug Stephenson
- `S1-S3` / `place_smash`: ie, owned by Julie Felten, owned by Didi Gough
- `S1-S3` / `place_smash`: le, owned by Jeffrey Gibson, owned by Bob Franklin
- `S1-S3` / `place_smash`: Flat, owned by Jamie Sproles, owned by RA & Kris Mackay
- `S1-S3` / `place_smash`: a, owned by Jeffrey Gibson, owned by Bob Franklin
- `S1-S3` / `place_smash`: nberg, owned by Kathy Walker White, owned by Dan Peck
- `O6` / `owner_tail_trunc`: 3rd: Gin of Lunstarr, owned by ow
- `S4/O` / `missing_owned_by`: 2nd: Ms. Scarlett of Heaven Hill, own:
- `S4/O` / `missing_owned_by`: 5th: Farmcliff Donny, ov
- `S4/O` / `missing_owned_by`: Reserve: Top "E" Mill, c
- `S4/O` / `missing_owned_by`: 3rd: The Bowery Mist, c
- `S4/O` / `missing_owned_by`: 1st: Veronica, owned b

### `1996 Vol 1 pg 61-110 back reversed_ocr_hqmax.txt` (FAIL)
- `S1-S3` / `place_smash`: 2lli, owned by Barbara Tyler, owned by Bonnie Edison
- `S1-S3` / `place_smash`: 6th: Molly, owned by Ann Ingram, owned by Willow Hindle-Rennie
- `S1-S3` / `place_smash`: 'ma, owned by Ken Meyer, owned by Pam Molloy
- `O6` / `owner_tail_trunc`: 1st: Courtwood Nipper, owned by Lc
- `O6` / `owner_tail_trunc`: 1st: Button Top Btlle Star of Wild Goose, owned by C
- `O6` / `owner_tail_trunc`: 4th: Wild Goose Fentucky, owned by CJ & Ouida Har
- `O6` / `owner_tail_trunc`: 10-12 1/2" Champbn: Wild Goose National, owned by ow
- `O6` / `owner_tail_trunc`: 2nd: All Seasons Woody of Dutch Creek, owned by Be
- `O6` / `owner_tail_trunc`: 3rd: Wild Goose Dip Stick, owned by CJ & Ouida Har
- `O6` / `owner_tail_trunc`: 3rd: Firewheel Ptatom Jack of T-Vols, owned by Bill
- `O6` / `owner_tail_trunc`: 6th: Edgefield Trston, owned by Bob & Melissa Van
- `O6` / `owner_tail_trunc`: 3rd: Wild Goose National, owned by CJ & Ouida Har

### `1996 Vol 1 pg 61-110 back_ocr_hqmax.txt` (FAIL)
- `S1-S3` / `place_smash`: 1st: Lacey, owned by Margaret Stricklandond: Red Oak Blue Bonnet, owned by Kenneth
- `O6` / `owner_tail_trunc`: 3rd: Foxwarren Kely of Highland Bay, owned by Art
- `O6` / `owner_tail_trunc`: 2nd: Rustler Jingles Judy, owned by David & Lisa Mcl
- `O6` / `owner_tail_trunc`: 3rd: Balckland Tuno of Iron Water, owned by Guy
- `O6` / `owner_tail_trunc`: 1st: Good Times Pobr Snow Baby, owned by Stev
- `O6` / `owner_tail_trunc`: 4th: Reuans Veronia@ of Trebor Chase, owned by Rob
- `O6` / `owner_tail_trunc`: 2nd: TF Halftrack ofFox Tale, owned by Janice & Mar
- `O6` / `owner_tail_trunc`: 3rd: Good Times Polar Snow Baby, owned by Stev
- `S4/O` / `missing_owned_by`: 2nd: Gilbert, ownedoy Jane Griffin
- `S4/O` / `missing_owned_by`: 6th: Three Oals Johnny Reb of Good Times, ow!
- `C1` / `class_header_gap`: 1st: Riverview Calvin, owned by Karen Vernon
- `C1` / `class_header_gap`: 1st: Mavens Taibr of Briarpatch, owned by Jack & Terri Batzer

### `1996 Vol 1 pg 61-110 front_ocr_hqmax.txt` (FAIL)
- `S1-S3` / `place_smash`: 0, owned by Doris Sneider, owned by Dan & Sharon Steckline
- `O6` / `owner_tail_trunc`: 1st: Wamp, owned by p
- `O6` / `owner_tail_trunc`: Rose, owned by Mike
- `O6` / `owner_tail_trunc`: Reserve: Dole Mother, owned by Marchiinski Cheryl Wea
- `O6` / `owner_tail_trunc`: 3rd: Rustlerllie, owned by Mike & D
- `O6` / `owner_tail_trunc`: 4th: Sadie R OSe, owned by Mike
- `O6` / `owner_tail_trunc`: 6th: White T, owned by Jos
- `O6` / `owner_tail_trunc`: Petty, owned by ow
- `O6` / `owner_tail_trunc`: 6th: Tortilla Flat Reflex, owned by Mary Anne Maj
- `O6` / `owner_tail_trunc`: Reserve: Gold Hilld Rush, owned by Jeff & Con
- `O6` / `owner_tail_trunc`: Reserve: Shenanigans Will, owned by Mary Abb
- `O6` / `owner_tail_trunc`: Best: Foxfield Garth of Lost Creek, owned by Del

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
- `O6` / `owner_tail_trunc`: 5th: Hillside Chez, owned by ow
- `O6` / `owner_tail_trunc`: 5th:  Will-O-Mooi Rex, owned by Michelle Williams & Kimberly Hor

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

### `1996 Vol II pg 163-220 front_ocr_hqmax.txt` (FAIL)
- `S4` / `mangled_by`: 4th: Not reported by Trial Chairperson
- `S4` / `mangled_by`: 3rd: Not reported by Trial Chairperson
- `S4` / `mangled_by`: 5th: Not reported by Trial Chairperson
- `S4` / `mangled_by`: 6th: Not reported by Trial Chairperson
- `O6` / `owner_tail_trunc`: Champion: Farmcliff T | 10-12 4 fon RPacarein: Didéaw T_ eddy, owned by ow
- `S4/O` / `missing_owned_by`: 4th: Three Oaks Penny of Green Acres, owner
- `S4/O` / `missing_owned_by`: 3rd: Duncan, name of owner not reported
- `S4/O` / `missing_owned_by`: 6th: Hooter, name of owner not reported
- `S4/O` / `missing_owned_by`: 5th: Norma Jean, name of owner not reported
- `S4/O` / `missing_owned_by`: 3rd: Duncan, name of own
- `S4/O` / `missing_owned_by`: 4th: Josee, name of owner not reported
- `S4/O` / `missing_owned_by`: 3rd: Heaven Hill Zodiac, 0

### `1996 Vol II pg 23-92 back reversed_ocr_hqmax.txt` (FAIL)
- `S1-S3` / `place_smash`: 5th: SpringateRuff-n-Tuff, owned by Amy, owned by Dog Pups, 9 up to 12 months
- `S1-S3` / `place_smash`: rip, owned by Marty & Teresa Gotttleib,0bb, owned by Linda Miller
- `S1-S3` / `place_smash`: yn, owned by Laura Harakaly, owned by Dan & Karen Kinsley
- `O6` / `owner_tail_trunc`: 5th: Big Sky Swlo, owned by ow
- `O6` / `owner_tail_trunc`: 4th: Molly, owned by Mary Web
- `O6` / `owner_tail_trunc`: 5th: Bonnie Bee, owned by Gavin Com
- `O6` / `owner_tail_trunc`: 3rd: Windsony Soda, owned by David & Susan Cra
- `O6` / `owner_tail_trunc`: 5th: Kettle Crek's Ripley's Belive It Or Not, owned by ow
- `O6` / `owner_tail_trunc`: 1st: Jera-yn, owned by ow
- `S4/O` / `missing_owned_by`: 2nd: Kilhaven Rudi, c
- `S4/O` / `missing_owned_by`: 4th: Fox Run Tyler, c
- `S4/O` / `missing_owned_by`: 2nd: Sparky, twned

### `1996 Vol II pg 23-92 back_ocr_hqmax.txt` (FAIL)
- `S1-S3` / `place_smash`: 5th: SpringateRuff-n-Tuff, owned by Amy, owned by Dog Pups, 9 up to 12 months
- `O6` / `owner_tail_trunc`: 5th: Bonnie Bee, owned by Gavin Com
- `O6` / `owner_tail_trunc`: 4th: Molly, owned by Mary Web
- `O6` / `owner_tail_trunc`: 3rd: AE die A mn: Céiimemtme aimed Bu William R (av OYRrien AgLity 1, owned by VIT Led
- `O6` / `owner_tail_trunc`: 4th: Mineral Sorings Indiana Bones, owned by Mari
- `O6` / `owner_tail_trunc`: 2nd: Ash Creek Matt, owned by Marty & Teresa Got
- `C1` / `class_header_gap`: 1st: Beacon Jagle of Ravenswood, owned by Ben & Janet Sutcliffe
- `C1` / `class_header_gap`: 1st: Lucy Mae, owned by J.Neff & J.Gay
- `C1` / `class_header_gap`: 1st: Jera-lyn, owned by Maureen McKernan
- `C1` / `class_header_gap`: 1st: All Seascns Woody, owned by Bontia Knickmeyer
- `C1` / `class_header_gap`: 1st: RA Dixie, owned by RA Terriers
- `C1` / `class_header_gap`: 1st: Farmstead Abby, owned by Richard & Annette

### `1996 Vol II pg 23-92 front (missing 1 pgs)_ocr_hqmax.txt` (FAIL)
- `S1-S3` / `place_smash`: Champion: Single Single Track Track Hunter, Kasey, owned by, owned by by Mark James & Lisa Titus Green
- `S1-S3` / `place_smash`: 12 12 1/2-15" Champion: Wyndcroft Will-O-Moor Natasha, Riley, owned by, owned by by Kathy Mark & Hunter Missy & Kulbacty Jeff Finkernagel
- `S1-S3` / `place_smash`: al, owned by Tony Mason, owned by Mark Thompson
- `O6` / `owner_tail_trunc`: 3rd: Deegan of Northgate, owned by Doug
- `O6` / `owner_tail_trunc`: 4th: Farmcliff Hampton, owned by Vicki Jot
- `O6` / `owner_tail_trunc`: 4th: Lickity Split Sassy, owned by Bob Fra
- `O6` / `owner_tail_trunc`: 10-12 1/2" Champion: Farmcliff Betty, owned by ow
- `O6` / `owner_tail_trunc`: 10-12 1/2" Reserve: Courtland Mi Girl, owned by ow
- `O6` / `owner_tail_trunc`: 12 1/2-15" Reserve: Romney Kaz, owned by ow
- `O6` / `owner_tail_trunc`: 2nd: Tucker, owned by Jc
- `O6` / `owner_tail_trunc`: 3rd: Rudy, owned by Jea
- `O6` / `owner_tail_trunc`: 1st: Haley's Comet, owned by Karen Rea

### `1996 Vol II pg 23-92 front (missing 2 pgs)_ocr_hqmax.txt` (FAIL)
- `S1-S3` / `place_smash`: irl, owned by J. Jankowski & K. Morande, owned by Genie Franklin
- `S1-S3` / `place_smash`: ton, owned by Vicki Johnson, owned by Doug & Sue Tack, owned by Bob Franklin
- `S1-S3` / `place_smash`: isha, owned by K. Hunter & P. Finkernag, owned by Kevin & Melissa McGrath
- `S1-S3` / `place_smash`: itewitch, owned by P. Hartman & K. McC, owned by R. & D. Zampella
- `S1-S3` / `place_smash`: rk, owned by Linda Cowasjee, owned by The Hollow Terriers
- `S1-S3` / `place_smash`: Baybriar, owned by Jeanette Hutchinsc, owned by Lisa Johnson, owned by Sandra Ferber
- `S1-S3` / `place_smash`: r, owned by Kate Bomberger, owned by Kate Bomberger, owned by Bob Franklin, owned by Margaret Strickland
- `S1-S3` / `place_smash`: t, owned by Phil Hawkins, owned by Joni, Dale & Becky Green
- `O6` / `owner_tail_trunc`: 3rd: Farmcliff Betty, owned by Franklin & Ci
- `O6` / `owner_tail_trunc`: 1st: Romney Kaz, owned by ow
- `O6` / `owner_tail_trunc`: 3rd: MLQH Muffin, owned by ow
- `O6` / `owner_tail_trunc`: 1st: Fox Run Risk, owned by ow

### `1996 Vol II pg 23-92 front_ocr_hqmax.txt` (FAIL)
- `S1-S3` / `place_smash`: Reserve: Sows Laurel Ear Liberty, Run Orry, owned by, owned by by Paul Kate Hartman Bomberger & Karen McCarthy
- `S1-S3` / `place_smash`: Buddy, owned by Andrew Burigo, owned by B. Franklin & C. Curtis
- `S1-S3` / `place_smash`: 1, owned by J. Jankowski & K. Morand, owned by Genie Franklin
- `S1-S3` / `place_smash`: on, owned by Vicki Johnson, owned by Bob Franklin
- `S1-S3` / `place_smash`: witch, owned by P. Hartman & K. McC, owned by R. & D. Zampella
- `S1-S3` / `place_smash`: cker, owned by Bud Carpenter, owned by Kristen Cusac, owned by Sandra Mims
- `S1-S3` / `place_smash`: k, owned by Leslie Woodcock, owned by Ken Chambers
- `S1-S3` / `place_smash`: te, owned by Bob Zeiher, owned by Phil Hawkins
- `S1-S3` / `place_smash`: f Little Eden, owned by Michelle Ward, owned by Mark Thompson, owned by Leslie Woodcock
- `S1-S3` / `place_smash`: 3, owned by Jeff Hamblin, owned by Gaye Redpath
- `S1-S3` / `place_smash`: tifox, owned by Kelly & James Baneau, owned by Sue Hardin
- `O6` / `owner_tail_trunc`: 1st: Bobby Duty, owned by Iif

### `1996 Vol II pg 93-162 back reversed_ocr_hqmax.txt` (FAIL)
- `S1-S3` / `place_smash`: gie, owned by Charlene Schlueter, owned by Aurora Rubel
- `S1-S3` / `place_smash`: hance, owned by Jill Nichols, owned by Kathy Oelrich
- `S1-S3` / `place_smash`: Jer, owned by Catherine Brown, owned by Doug & Sue Tack
- `O6` / `owner_tail_trunc`: 4th: Frost, owned by Andrea Vaz
- `O6` / `owner_tail_trunc`: 5th: Windtree (et, owned by ow
- `O6` / `owner_tail_trunc`: 3rd: Rooson Ciga, owned by ow
- `O6` / `owner_tail_trunc`: 2nd: Rooson Ciara, owned by ow
- `O6` / `owner_tail_trunc`: 1st: Tag, owned by Ka
- `O6` / `owner_tail_trunc`: 4th: Fox Run Kiam, owned by ow
- `O6` / `owner_tail_trunc`: 4th: Windermer Nitewitch of Sow's Ear, owned by Paul Hartman & Kai
- `O6` / `owner_tail_trunc`: 12 1/2-15" Champion: Qualyns Falcon of Blue Barns, owned by Ru
- `O6` / `owner_tail_trunc`: Reserve: Goliath, owned by Jim Yue

### `1996 Vol II pg 93-162 back_ocr_hqmax.txt` (FAIL)
- `S1-S3` / `place_smash`: land, owned by Lloyd & Shirley Cox, owned by Cheryl Hart
- `S1-S3` / `place_smash`: ns, owned by Teresa Wellman, owned by Jerry Roach
- `O6` / `owner_tail_trunc`: 12 1/2-15" Chanpion: Salishan Maggie, owned by ow
- `O6` / `owner_tail_trunc`: Reserve: Goliath, owned by Jim Yue
- `O6` / `owner_tail_trunc`: 1st: Goliath, owned by Jim Yue
- `O6` / `owner_tail_trunc`: 5th: Cortenbachs Moon Wizard of Oz, owned by Lis
- `O6` / `owner_tail_trunc`: 5th: Cortenbact's Moon Wizard of Oz, owned by Lis
- `O6` / `owner_tail_trunc`: 4th: Horsemaser's Willy, owned by Neil & Pam Cal
- `O6` / `owner_tail_trunc`: 1st: Beau Monle Paige of Coldwater, owned by Mi
- `O6` / `owner_tail_trunc`: 1st: Fox Run Ben, owned by Ker
- `O6` / `owner_tail_trunc`: 3rd: Willie Wonderful of T.F, owned by ow
- `O6` / `owner_tail_trunc`: 3rd: B.T. Willieof Hart Farms, owned by ow

### `1996 Vol II pg 93-162 front_ocr_hqmax.txt` (FAIL)
- `S1-S3` / `place_smash`: Ripley, owned by Kendal Makowicz, owned by Antonio & Barbara Sullo
- `S1-S3` / `place_smash`: Y, owned by Bob Franklin, owned by Chuck Schobert
- `S1-S3` / `place_smash`: gsy, owned by Richard & Annetee Ken:, owned by Kim Hunter & Jim Hughes, owned by Charlie & Julie Kemp
- `S1-S3` / `place_smash`: Farmcliff, owned by Doug & Sue Tack, owned by Bob Franklin
- `S1-S3` / `place_smash`: elsea, owned by Bety McArthur, owned by Nelliw Niewola – Entries: 6
- `O6` / `owner_tail_trunc`: 4th: Wyncroft Natasha, owned by K
- `O6` / `owner_tail_trunc`: 1st: Wyncroft Natasha, owned by K
- `O6` / `owner_tail_trunc`: 4th: Windyview Briar, owned by Eile
- `O6` / `owner_tail_trunc`: 3rd: Tabasco of Way More, owned by Shane & I
- `O6` / `owner_tail_trunc`: 5th: Loblolly Maggie Mai, owned by Dian
- `O6` / `owner_tail_trunc`: 5th: Red Oak Maddy of Gunsmoke, owned by ow
- `O6` / `owner_tail_trunc`: 3rd: Wesworld Hamilton, owned by Christy Parkinson & Suzi Utz

### `Document_2026-11-04_152834_ocr_hqmax.txt` (FAIL)
- `O6` / `owner_tail_trunc`: 4th: Holfield Jill lll of Orchard Hill, owned by Cher
- `S4/O` / `missing_owned_by`: 3rd: Duncan, name of owner not reported
- `S4/O` / `missing_owned_by`: 6th: Hooter, name of owner not reported
- `S4/O` / `missing_owned_by`: 5th: Norma Jean, name of owner not reported
- `S4/O` / `missing_owned_by`: 3rd: Duncan, name of owner not furnished by Trial Chairperson
- `S4/O` / `missing_owned_by`: 4th: Josee, name of owner not reported
- `S4/O` / `missing_owned_by`: 4th: Tamsyn, name of owner not reported
- `S4/O` / `missing_owned_by`: 5th: Lacey, name of owner not reported
- `S4/O` / `missing_owned_by`: 3rd: Toby, name of owner not reported

### `Document_2026-11-04_153208_ocr_hqmax.txt` (FAIL)
- `S4` / `mangled_by`: 4th: Not reported by Trial Chairperson
- `S4` / `mangled_by`: 3rd: Not reported by Trial Chairperson
- `S4` / `mangled_by`: 5th: Not reported by Trial Chairperson
- `S4` / `mangled_by`: 6th: Not reported by Trial Chairperson
- `O6` / `owner_tail_trunc`: Briarpatch, owned by Tere
- `O6` / `owner_tail_trunc`: White Gate, owned by Bill & Na
- `O6` / `owner_tail_trunc`: Vagabond V, owned by Mich
- `O6` / `owner_tail_trunc`: Eastlake E, owned by Wi
- `S4/O` / `missing_owned_by`: 1st: Polar Snow Baby of Good Times, 6wned by Steve Spruill
- `C1` / `class_header_gap`: 1st: Deegan of Northgate, owned by Douglas & Susan Tack
- `C1` / `class_header_gap`: 1st: Long Hope Mickey of Farmcliff, owned by Bob & Genie Franklin
- `C1` / `class_header_gap`: 1st: Undercover Cindy, owned by Lynn May Measles
