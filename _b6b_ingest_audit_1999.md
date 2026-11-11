# B6b cleanup + ingest audit — 1999

Catalog: `_OCR_CLEANUP_CATALOG_HANDOFF.md`
Volumes: 6  cleaned=6  PASS=0  WARN=0  FAIL=6
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
| FAIL | True | 28 | 3 | C1×25,O6×3,?/4th_then_2nd×1,S4/O×1,C6×1 | `1999 Vol I, pt 1_ocr_hqmax.txt` |
| FAIL | True | 34 | 4 | C1×25,O6×8,P2×2,S4/O×2,?/4th_then_6th_no_5×1 | `1999 Vol I, pt 2_ocr_hqmax.txt` |
| FAIL | True | 29 | 4 | C1×25,O6×4,S4/O×3,?/cutoff_racing×1 | `1999 Vol II, pt 1_ocr_hqmax.txt` |
| FAIL | True | 32 | 0 | C1×25,O6×7 | `1999 Vol II, pt 2_ocr_hqmax.txt` |
| FAIL | True | 28 | 2 | C1×25,O6×3,C6/O1×1,C6×1 | `1999 Vol III, pt 1_ocr_hqmax.txt` |
| FAIL | True | 27 | 9 | C1×25,S4/O×7,O6×2,C6/O1×1,C6×1 | `1999 Vol III, pt 2_ocr_hqmax.txt` |

## Sample residual hits (after cleanup)

### `1999 Vol I, pt 1_ocr_hqmax.txt` (FAIL)
- `?` / `4th_then_2nd`: 4th: Scruffy, owned by Audie Sumner 3
2nd: Southermost Sami D' Shark, owned by Jackie McLain 4
- `O6` / `owner_tail_trunc`: 2nd: Sun Dance, owned by Roy & Sandra Deo
- `O6` / `owner_tail_trunc`: 2nd: BF. Wishbone, owned by David, Jean & Kelley Rei
- `O6` / `owner_tail_trunc`: 5th: ~ B.F. Wishbone, owned by B.F. David, Jean & Kelley Rei
- `S4/O` / `missing_owned_by`: 1st: Nirvana Farms Madison, Peggy Dominico
- `C6` / `orphan_entry_count`: 27
- `C1` / `class_header_gap`: 1st: Golden Hills Smidge, owned by Brenda Benkly
- `C1` / `class_header_gap`: 1st: Briarpatch Britches, owned by Sherri Rossmiller
- `C1` / `class_header_gap`: 1st: Thimble Farm Fargo, owned by Gary & Donna Rich
- `C1` / `class_header_gap`: 1st: Golden Hills Rush, owned by Jeff & Connie McKee
- `C1` / `class_header_gap`: 1st: Runamuk Gnat, owned by Harry & Mary Abbott
- `C1` / `class_header_gap`: 1st: Sow's Ear See Bee, owned by John & Lisa Renfro

### `1999 Vol I, pt 2_ocr_hqmax.txt` (FAIL)
- `P2` / `place_rank_dust`: 1st:
1st: Hannah, owned by Pat & Steve Berry
- `P2` / `dup_place`: 1st:
1st: Hannah, owned by Pat & Steve Berry
- `?` / `4th_then_6th_no_5`: 4th: Rat Race Keely, owned by Lloyd & Ann Wendland
6th: Lickity Split Fancy, owned by Allen & Denise Wessel
- `O6` / `owner_tail_trunc`: 10-12'%" Reserve: R.A. Piker, owned by George & Lir
- `O6` / `owner_tail_trunc`: 1st: Paramount Ectasy, owned by Dennie Fee
- `O6` / `owner_tail_trunc`: Best: Paramount Ectasy, owned by Dennis Fee
- `O6` / `owner_tail_trunc`: Reserve: Paramount Ecstasy, owned by Dennie Fee
- `O6` / `owner_tail_trunc`: 3rd: Zack Van Noy, owned by Jim & Annie Van Noy
- `O6` / `owner_tail_trunc`: 6th: Button Top Texy, owned by Andre & Laura Nel
- `O6` / `owner_tail_trunc`: 4th: Button Top Texy, owned by Andre' & Laura Nel
- `O6` / `owner_tail_trunc`: 1st: Sundance, owned by Roy & Sandy Deo
- `S4/O` / `missing_owned_by`: 6th: Daniel, last name not provided

### `1999 Vol II, pt 1_ocr_hqmax.txt` (FAIL)
- `?` / `cutoff_racing`: ACING DIVISION
- `O6` / `owner_tail_trunc`: 6th: Bayview Twister, owned by Stan & Karen Kman
- `O6` / `owner_tail_trunc`: 5th: Treehouse Guiness, owned by Stan & Karen Kman
- `O6` / `owner_tail_trunc`: 4th: Underground Singe, owned by Kevin & Shannon Ost
- `S4/O` / `missing_owned_by`: 4th: Winslow Genevieve, Lisa Fitzgerald
- `S4/O` / `missing_owned_by`: 2nd: Disqualified, Exhibitor cross-entered in Open Division
- `S4/O` / `missing_owned_by`: 4th: Sweet B Sugar & Spice, owned B Candy Butterfield
- `C1` / `class_header_gap`: 1st: Westwood Lucas, owned by Alice Reynolds
- `C1` / `class_header_gap`: 1st: Hillside Josie, owned by Karen Vernon
- `C1` / `class_header_gap`: 1st: Bugsy, owned by Richard & Annette Kent
- `C1` / `class_header_gap`: 1st: Green Gate Tomba, owned by Joe & Priscilla Testa
- `C1` / `class_header_gap`: 1st: Fox Run Casey, owned by Cathy Potter

### `1999 Vol II, pt 2_ocr_hqmax.txt` (FAIL)
- `O6` / `owner_tail_trunc`: 4th: Treehouse Guiness, owned by Stan & Karen Kman
- `O6` / `owner_tail_trunc`: 6th: Treehouse Guinness, owned by Stan & Karen Kman
- `O6` / `owner_tail_trunc`: 5th: Treehouse Guinness, owned by Stan & Karen Kman
- `O6` / `owner_tail_trunc`: 1st: Muscle Russell Comet, owned by Jack & Ma
- `O6` / `owner_tail_trunc`: 3rd: Muscle Russell Tussle, owned by Rick & Mal
- `O6` / `owner_tail_trunc`: 12-15" Reserve: Northwoods O'Tally Oak, owned by Gary
- `C1` / `class_header_gap`: 1st: Corn Row Tucker, owned by Mark Thompson
- `C1` / `class_header_gap`: 1st: Westwood Jade, owned by Rick & Leslie Hemsing
- `C1` / `class_header_gap`: 1st: Deegan, owned by Doug & Sue Tack
- `C1` / `class_header_gap`: 1st: Long Hope Mickey, owned by Bob Franklin
- `C1` / `class_header_gap`: 1st: Laurel Run Jester, owned by Lisa Schmidt
- `C1` / `class_header_gap`: 1st: Fox Run Dazl, owned by Stephanie Taylor

### `1999 Vol III, pt 1_ocr_hqmax.txt` (FAIL)
- `O6` / `owner_tail_trunc`: 4th: Muscle Russell Phantom, owned by Jin
- `O6` / `owner_tail_trunc`: 6th: Westwood Higgins, owned by Art & Syl
- `O6` / `owner_tail_trunc`: 1st: Muscle Russell Zippity Zoe, owned by Jin
- `C6/O1` / `bare_entries`: Entries:
- `C6` / `orphan_entry_count`: 0
- `C1` / `class_header_gap`: 1st: J &J Sunshine, owned by J.Baker/J.Freimark
- `C1` / `class_header_gap`: 1st: Little Eden Chewbacca, owned by Julie Pagliaro
- `C1` / `class_header_gap`: 1st: High Range Jackson, owned by Beau & Kathleen White
- `C1` / `class_header_gap`: 1st: Com Row Tucker, owned by Mark Thompson
- `C1` / `class_header_gap`: 1st: Briarpatch Zoe, owned by Roger & Tabby Shury
- `C1` / `class_header_gap`: 1st: Troon Quarry Silver Bell, owned by Jeff & Teresa Rooney
- `C1` / `class_header_gap`: 1st: Desert Fox Polly, owned by Jeff & Teresa Rooney

### `1999 Vol III, pt 2_ocr_hqmax.txt` (FAIL)
- `O6` / `owner_tail_trunc`: 2nd: Angel's Den Tucker, owned by Jayleen Car
- `O6` / `owner_tail_trunc`: 1st: Baun Acres Phantom Jack, owned by Adam
- `S4/O` / `missing_owned_by`: 3rd: Trevor, last name not provided
- `S4/O` / `missing_owned_by`: 1st: Kristen Mogrovejo, handling North Country Petey
- `S4/O` / `missing_owned_by`: 2nd: Jessica Morrison, handling Cody
- `S4/O` / `missing_owned_by`: 3rd: Felicia Franklin, handling Gadget
- `S4/O` / `missing_owned_by`: 1st: Katie Fitzgerald, handling Winslow Genevieve
- `S4/O` / `missing_owned_by`: 2nd: Rocky Cassone, handling Muscle Russell Comet
- `S4/O` / `missing_owned_by`: 3rd: Amanda Mogrovejo, handling North Country Petey
- `C6/O1` / `bare_entries`: Entries:
- `C6` / `orphan_entry_count`: 10
- `C1` / `class_header_gap`: 1st: Heaven Hill Foxy, owned by Doug Stephenson
