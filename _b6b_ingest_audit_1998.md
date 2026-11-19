# B6b cleanup + ingest audit — 1998

Catalog: `_OCR_CLEANUP_CATALOG_HANDOFF.md`
Volumes: 7  cleaned=7  PASS=3  WARN=0  FAIL=4
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
| FAIL | True | 25 | 0 | C1×24,S1-S3×1 | `1998 Vol I, pt 1_ocr_hqmax.txt` |
| PASS | True | 0 | 0 | — | `1998 Vol I, pt 2_ocr_hqmax.txt` |
| PASS | True | 0 | 0 | — | `1998 Vol I, pt 3_ocr_hqmax.txt` |
| FAIL | True | 2 | 0 | C1×2 | `1998 Vol II, pt 1_ocr_hqmax.txt` |
| FAIL | True | 24 | 0 | C1×24 | `1998 Vol II, pt 2_ocr_hqmax.txt` |
| FAIL | True | 9 | 0 | C1×9 | `1998 Vol III, pt 1_ocr_hqmax.txt` |
| PASS | True | 0 | 0 | — | `1998 Vol III, pt 2_ocr_hqmax.txt` |

## Sample residual hits (after cleanup)

### `1998 Vol I, pt 1_ocr_hqmax.txt` (FAIL)
- `C1` / `3rd_then_5th_no_4`: 3rd: Rustler's Maggie Burns, owned by Jane Legard
5th: T.J. Farms File, owned by Jim & Mary Colbert
- `C1` / `3rd_then_5th_no_4`: 3rd: Hart Farms Buffalo, owned by Cheryl Hart
5th: T.J. Farms Typhoon, owned by T.Wellman/E.Kennedy
- `C1` / `3rd_then_5th_no_4`: 3rd: Roper, owned by Ashley Tomberg
5th: Camerton Hall Jake, owned by Robin Futch
- `C1` / `3rd_then_5th_no_4`: 3rd: Foxfield Flash, owned by Jim & Janet Sproles
5th: Mauser, owned by Tiffany Van Tuyl
- `C1` / `3rd_then_5th_no_4`: 3rd: Thistledown Roc, owned by Chuck & Diana Hufnagel
5th: Thistledown Cheyenne, owned by Chuck & Diana Hufnagel
- `C1` / `3rd_then_5th_no_4`: 3rd: Teeka, owned by Larry & Linda Morrison
5th: Rutgers Creek Sugar Magnolia, owned by Twila Decker
- `C1` / `3rd_then_5th_no_4`: 3rd: Ironhorse Money Penny, owned by Rae DesRochers
5th: Paxton Brittany, owned by J.Baker/J.Freimark
- `C1` / `3rd_then_5th_no_4`: 3rd: Cedarcrest Precocious, owned by Thelma Spencer
5th: Echowood Dallas, owned by Ann Sloan
- `C1` / `2nd_then_4th_no_3`: 2nd: Katie Cox
4th: Laurel Downs
- `C1` / `place_rank_gap`: California Bred                                   Entries: 1 | 2th then 4th | 4th: Wild West Hank, owned by Ann Wendland
- `C1` / `place_rank_gap`: Novice Adult                                           Entri | 3th then 5th | 5th: T.J. Farms File, owned by Jim & Mary Colbert
- `C1` / `place_rank_gap`: Youth Agility Entries: 13 | 3th then 5th | 5th: Vixen Trace Sandy, handled by Danielle Schepman

### `1998 Vol II, pt 1_ocr_hqmax.txt` (FAIL)
- `C1` / `2nd_then_4th_no_3`: 2nd: Lickity Split Sassy, owned by Bob Franklin
4th: Farmcliff Donny, owned by Kristen Tracy
- `C1` / `place_rank_gap`: Dog Pups, 9 up to 12 months, over 12-15" Entries: 3 | 2th then 4th | 4th: Farmcliff Donny, owned by Kristen Tracy

### `1998 Vol II, pt 2_ocr_hqmax.txt` (FAIL)
- `C1` / `3rd_then_5th_no_4`: 3rd: Whispering Winds Sir Willie, owned by K. & M. Winfield
5th: Farmcliff Duke, owned by K HunterJ.Hughes
- `C1` / `3rd_then_5th_no_4`: 3rd: High Mountain Echo, owned by Alison Linstrum
5th: Farmliff Elmo, owned by Bob Franklin
- `C1` / `3rd_then_5th_no_4`: 3rd: Joyful Noise Bugsy, owned by Richard & Annette Kent
5th: Long Hope Mickey, owned by Bob Franklin
- `C1` / `3rd_then_5th_no_4`: 3rd: Last Chance Rosie, owned by Gary & Donna Rich
5th: Salt Valley Wolfman, owned by Jan Finnerty
- `C1` / `3rd_then_5th_no_4`: 3rd: Fox Run Shocker, owned by R.Eckart /S.Taylor
5th: Brandywine Aftershock, owned by Wayne & Marla Robinson
- `C1` / `3rd_then_5th_no_4`: 3rd: Shelmar Loreal, owned by Jean Veazey
5th: Harriet, owned by Gauvin Bailey
- `C1` / `2nd_then_4th_no_3`: 2nd: Fox Run Jackie, owned by Sustell
4th: Moosemor Scarlet, owned by Natalie Lamming
- `C1` / `2nd_then_4th_no_3`: 2nd: Thimble Farm Siren, owned by Valerie Wasch
4th: Big Sky Annie, owned by Doug & Sue Tack
- `C1` / `1st_then_3rd_no_2`: 1st: Farmcliff Wendy, owned by Bob Franklin
3rd: Ravenswood Bella Donna, owned by B. & A. Sullo
- `C1` / `1st_then_3rd_no_2`: 1st: Big Sky Annie, owned by Doug & Sue Tack
3rd: Chelsea Rose, owned by Kay Sadowsky
- `C1` / `place_rank_gap`: New York State Bred                                   Entrie | 4th then 6th | 6th: Glen Coe Moose, owned by Holly Cipriano
- `C1` / `place_rank_gap`: Agility I Certificate                                   Entr | 2th then 4th | 4th: Moosemor Scarlet, owned by Natalie Lamming

### `1998 Vol III, pt 1_ocr_hqmax.txt` (FAIL)
- `C1` / `3rd_then_5th_no_4`: 3rd: Vixen Trace Barnacle, owned by Bill & Meredith Rennie
5th: Autumnwood Outlaw, owned by David & Susan Crawford
- `C1` / `3rd_then_5th_no_4`: 3rd: Mallory Finnerty
5th: Marcia Wicks
- `C1` / `1st_then_3rd_no_2`: 1st: IU. FIEsSIWIGA Rot ruage, owned by uarot 1immons
3rd: Buster, owned by Russ & Mary Pollock
- `C1` / `place_rank_gap`: Dogs, 1yr & older, 122 up to 15", smooth Entries: 7 | 1th then 3th | 3rd: Buster, owned by Russ & Mary Pollock
- `C1` / `place_rank_gap`: Dogs, 1 yr & older, over 12 '2-15" Entries: 1 | 1th then 3th | 3rd: Prestige Farms Oliver, owned by Jennifer Gilligan
- `C1` / `place_rank_gap`: Dog Pups, 4 up to 6 months, r/br                   Entries:  | 3th then 5th | 5th: Autumnwood Outlaw, owned by David & Susan Crawford
- `C1` / `place_rank_gap`: Child Handler                                             En | 3th then 5th | 5th: Marcia Wicks
- `C1` / `place_rank_gap`: Bitches, 1 yr & older, 12 1/2 up to 15", r/br        Entries | 1th then 3th | 3rd: Hines Hill Hillary, owned by Nancy Breakstone
