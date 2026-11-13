# B6b cleanup + ingest audit — 1996

Catalog: `_OCR_CLEANUP_CATALOG_HANDOFF.md`
Volumes: 30  cleaned=7  PASS=17  WARN=0  FAIL=13
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
| PASS | False | 0 | 0 | — | `1996 Vol 1 pg 111-160 back reversed_ocr_hqmax.txt` |
| FAIL | False | 41 | 0 | O6×21,S4/O×13,S1-S3×4,C1×3 | `1996 Vol 1 pg 111-160 back_ocr_hqmax.txt` |
| FAIL | False | 58 | 0 | O6×25,S4/O×14,S1-S3×11,C1×8 | `1996 Vol 1 pg 111-160 front_ocr_hqmax.txt` |
| PASS | False | 0 | 0 | — | `1996 Vol 1 pg 161-178 back reversed_ocr_hqmax.txt` |
| PASS | False | 0 | 0 | — | `1996 Vol 1 pg 161-178 back_ocr_hqmax.txt` |
| PASS | False | 0 | 0 | — | `1996 Vol 1 pg 161-178 front_ocr_hqmax.txt` |
| PASS | False | 0 | 0 | — | `1996 Vol 1 pg 21-60 back reversed_ocr_hqmax.txt` |
| FAIL | False | 8 | 0 | S4/O×4,C1×2,S1-S3×1,O6×1 | `1996 Vol 1 pg 21-60 back_ocr_hqmax.txt` |
| FAIL | True | 2 | 0 | C1×2 | `1996 Vol 1 pg 21-60 front_ocr_hqmax.txt` |
| FAIL | False | 41 | 0 | S4/O×19,O6×13,C1×6,S1-S3×3 | `1996 Vol 1 pg 61-110 back reversed_ocr_hqmax.txt` |
| PASS | True | 0 | 0 | — | `1996 Vol 1 pg 61-110 back_ocr_hqmax.txt` |
| FAIL | False | 45 | 0 | O6×24,S4/O×14,C1×6,S1-S3×1 | `1996 Vol 1 pg 61-110 front_ocr_hqmax.txt` |
| FAIL | False | 32 | 0 | S4/O×13,S4×8,O6×8,C1×2,S1-S3×1 | `1996 Vol II pg 163-220 back reversed_ocr_hqmax.txt` |
| FAIL | False | 37 | 0 | O6×16,S4×9,S4/O×9,C1×3 | `1996 Vol II pg 163-220 back_ocr_hqmax.txt` |
| FAIL | False | 28 | 0 | S4/O×17,S4×8,O6×1,C6×1,C1×1 | `1996 Vol II pg 163-220 front_ocr_hqmax.txt` |
| PASS | True | 0 | 0 | — | `1996 Vol II pg 23-92 back reversed_ocr_hqmax.txt` |
| PASS | False | 0 | 0 | — | `1996 Vol II pg 23-92 back_ocr_hqmax.txt` |
| PASS | False | 0 | 0 | — | `1996 Vol II pg 23-92 front (missing 1 pgs)_ocr_hqmax.txt` |
| PASS | True | 0 | 0 | — | `1996 Vol II pg 23-92 front (missing 2 pgs)_ocr_hqmax.txt` |
| PASS | True | 0 | 0 | — | `1996 Vol II pg 23-92 front_ocr_hqmax.txt` |
| FAIL | True | 14 | 0 | C1×9,O6×4,S4/O×1 | `1996 Vol II pg 93-162 back reversed_ocr_hqmax.txt` |
| FAIL | False | 27 | 0 | O6×13,S4/O×9,C1×3,S1-S3×2 | `1996 Vol II pg 93-162 back_ocr_hqmax.txt` |
| FAIL | False | 29 | 0 | S4/O×11,O6×10,S1-S3×5,C1×3 | `1996 Vol II pg 93-162 front_ocr_hqmax.txt` |
| PASS | False | 0 | 0 | — | `Document_2026-11-04_144208_ocr_hqmax.txt` |
| PASS | False | 0 | 0 | — | `Document_2026-11-04_144530_ocr_hqmax.txt` |
| PASS | False | 0 | 0 | — | `Document_2026-11-04_145355_ocr_hqmax.txt` |
| PASS | False | 0 | 0 | — | `Document_2026-11-04_145925_ocr_hqmax.txt` |
| PASS | False | 0 | 0 | — | `Document_2026-11-04_151058_ocr_hqmax.txt` |
| FAIL | False | 9 | 0 | S4/O×8,O6×1 | `Document_2026-11-04_152834_ocr_hqmax.txt` |
| PASS | True | 0 | 0 | — | `Document_2026-11-04_153208_ocr_hqmax.txt` |

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
- `C1` / `class_header_gap`: 1st: Foxnorten Tyke of, owned by Karen Fitzpatrick
- `C1` / `class_header_gap`: 1st: Windermere Wend, owned by Pam Simmons

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

### `1996 Vol II pg 93-162 back reversed_ocr_hqmax.txt` (FAIL)
- `O6` / `owner_tail_trunc`: 4th: Frost, owned by Andrea Vaz
- `O6` / `owner_tail_trunc`: 4th: Windermer Nitewitch of Sow's Ear, owned by Paul Hartman & Kai
- `O6` / `owner_tail_trunc`: Reserve: Goliath, owned by Jim Yue
- `O6` / `owner_tail_trunc`: 1st: Goliath, owned by Jim Yue
- `S4/O` / `missing_owned_by`: 4th: Wild Remain, owrbth: Eastlake Mejan o
- `C1` / `class_header_gap`: 1st: Farmcliff Fred of, owned by Mark & Janice Bjorkland
- `C1` / `class_header_gap`: 1st: Wind Song Tracy, owned by Cheryl Hart
- `C1` / `class_header_gap`: 1st: T.F.Just-A-lirtc, owned by Pam Malloy
- `C1` / `class_header_gap`: 1st: Fox CreekAlyda, owned by Phil Hawkins
- `C1` / `class_header_gap`: 1st: Corn Row Tyler, owned by Pam Simmons
- `C1` / `class_header_gap`: 1st: Becky of Cluck's, owned by Kathleen Hardy
- `C1` / `class_header_gap`: 1st: Craftifox Retel Rc, owned by Kelly & James Barbeau

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
