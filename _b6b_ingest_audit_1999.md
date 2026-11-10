# B6b cleanup + ingest audit — 1999

Catalog: `_OCR_CLEANUP_CATALOG_HANDOFF.md`
Volumes: 6  cleaned=0  PASS=0  WARN=0  FAIL=6
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
| FAIL | False | 33 | 2 | C1×25,O6×8,S4/O×1,C6×1 | `1999 Vol I, pt 1_ocr_hqmax.txt` |
| FAIL | False | 35 | 2 | C1×25,O6×10,S4/O×2 | `1999 Vol I, pt 2_ocr_hqmax.txt` |
| FAIL | False | 30 | 4 | C1×25,O6×5,S4/O×3,?/cutoff_racing×1 | `1999 Vol II, pt 1_ocr_hqmax.txt` |
| FAIL | False | 32 | 0 | C1×25,O6×7 | `1999 Vol II, pt 2_ocr_hqmax.txt` |
| FAIL | False | 36 | 2 | C1×25,O6×11,C6/O1×1,C6×1 | `1999 Vol III, pt 1_ocr_hqmax.txt` |
| FAIL | False | 31 | 9 | C1×25,S4/O×7,O6×6,C6/O1×1,C6×1 | `1999 Vol III, pt 2_ocr_hqmax.txt` |

## Sample residual hits (after cleanup)

### `1999 Vol I, pt 1_ocr_hqmax.txt` (FAIL)
- `O6` / `owner_tail_trunc`: 2nd: Sun Dance, owned by Roy & Sandra Deo
- `O6` / `owner_tail_trunc`: 1st: Mauser, owned by Tiffany Van Tuy
- `O6` / `owner_tail_trunc`: 3rd: Jazzy Stuff, owned by Bobby Duty Ill
- `O6` / `owner_tail_trunc`: 3rd: Greenwood Green Day, owned by Bobby Duty Iii
- `O6` / `owner_tail_trunc`: 3rd: Wild Goose Nitro, owned by Bobbie Duty Ili
- `O6` / `owner_tail_trunc`: 2nd: Greenwood Green Day, owned by Bobby Duty Iii
- `O6` / `owner_tail_trunc`: 2nd: BF. Wishbone, owned by David, Jean & Kelley Rei
- `O6` / `owner_tail_trunc`: 5th: ~ B.F. Wishbone, owned by B.F. David, Jean & Kelley Rei
- `S4/O` / `missing_owned_by`: 1st: Nirvana Farms Madison, Peggy Dominico
- `C6` / `orphan_entry_count`: 27
- `C1` / `class_header_gap`: 1st: 3 T's Maverick, owned by Terri Wilson
- `C1` / `class_header_gap`: 1st: Golden Hills Smidge, owned by Brenda Benkly

### `1999 Vol I, pt 2_ocr_hqmax.txt` (FAIL)
- `O6` / `owner_tail_trunc`: 10-12'%" Reserve: R.A. Piker, owned by George & Lir
- `O6` / `owner_tail_trunc`: 1st: Paramount Ectasy, owned by Dennie Fee
- `O6` / `owner_tail_trunc`: Best: Paramount Ectasy, owned by Dennis Fee
- `O6` / `owner_tail_trunc`: Reserve: Paramount Ecstasy, owned by Dennie Fee
- `O6` / `owner_tail_trunc`: 3rd: Zack Van Noy, owned by Jim & Annie Van Noy
- `O6` / `owner_tail_trunc`: 3rd: Dashaway Dandy, owned by Toni Haigh You
- `O6` / `owner_tail_trunc`: 4th: Jazzy, owned by A.J. Duty Ill
- `O6` / `owner_tail_trunc`: 6th: Button Top Texy, owned by Andre & Laura Nel
- `O6` / `owner_tail_trunc`: 4th: Button Top Texy, owned by Andre' & Laura Nel
- `O6` / `owner_tail_trunc`: 1st: Sundance, owned by Roy & Sandy Deo
- `S4/O` / `missing_owned_by`: 6th: Daniel, last name not provided
- `S4/O` / `missing_owned_by`: 2nd: White Spirits Abbey Rose, Dan & Cindy McClary

### `1999 Vol II, pt 1_ocr_hqmax.txt` (FAIL)
- `?` / `cutoff_racing`: ACING DIVISION
- `O6` / `owner_tail_trunc`: 6th: Bayview Twister, owned by Stan & Karen Kman
- `O6` / `owner_tail_trunc`: 5th: Treehouse Guiness, owned by Stan & Karen Kman
- `O6` / `owner_tail_trunc`: 4th: Hideaway Farms Hunter, owned by Ken & Penny Bak
- `O6` / `owner_tail_trunc`: 4th: Underground Singe, owned by Kevin & Shannon Ost
- `S4/O` / `missing_owned_by`: 4th: Winslow Genevieve, Lisa Fitzgerald
- `S4/O` / `missing_owned_by`: 2nd: Disqualified, Exhibitor cross-entered in Open Division
- `S4/O` / `missing_owned_by`: 4th: Sweet B Sugar & Spice, owned B Candy Butterfield
- `C1` / `class_header_gap`: 1st: Brandywine Pilot, owned by Jim & Sally Saul
- `C1` / `class_header_gap`: 1st: T.J. Farms Trevor, owned by B.Kelley/J.Shapiro
- `C1` / `class_header_gap`: 1st: Hillside Josie, owned by Karen Vernon
- `C1` / `class_header_gap`: 1st: Bugsy, owned by Richard & Annette Kent

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
- `C1` / `class_header_gap`: 1st: Rusty, owned by Tom Arnold
- `C1` / `class_header_gap`: 1st: Fox Run Felon, owned by Wayne & Dee Brown

### `1999 Vol III, pt 1_ocr_hqmax.txt` (FAIL)
- `O6` / `owner_tail_trunc`: 2nd: Northgate Chester, owned by Susan Gil
- `O6` / `owner_tail_trunc`: 1st: Baun Acres Phantom Jack, owned by Adam & Kelley Cam
- `O6` / `owner_tail_trunc`: 1st: Northgate Chester, owned by Susan Gil
- `O6` / `owner_tail_trunc`: 3rd: Sow's Ear Julien, owned by Karen McC
- `O6` / `owner_tail_trunc`: 4th: Muscle Russell Phantom, owned by Jin
- `O6` / `owner_tail_trunc`: 6th: Westwood Higgins, owned by Art & Syl
- `O6` / `owner_tail_trunc`: 3rd: Crossewinds Tess, owned by David & A
- `O6` / `owner_tail_trunc`: 1st: Muscle Russell Zippity Zoe, owned by Ji
- `O6` / `owner_tail_trunc`: 4th: Whispering Winds Hiedi Ho, owned by k
- `O6` / `owner_tail_trunc`: 5th: Farmstead Abby, owned by Richard & A
- `O6` / `owner_tail_trunc`: 4th: Whispering Winds Munchie, owned by K
- `C6/O1` / `bare_entries`: Entries:

### `1999 Vol III, pt 2_ocr_hqmax.txt` (FAIL)
- `O6` / `owner_tail_trunc`: 2nd: Angel's Den Tucker, owned by Jayleen Car
- `O6` / `owner_tail_trunc`: 1st: Baun Acres Phantom Jack, owned by Adam
- `O6` / `owner_tail_trunc`: 3rd: Greenwood Big Hungry, owned by B.J. Duty Ill
- `O6` / `owner_tail_trunc`: 4th: Snake River Pahsimeroi Peasley, owned by A. & B. Millward Acl
- `O6` / `owner_tail_trunc`: 3rd: Northgate Chester, owned by Susan Gil
- `O6` / `owner_tail_trunc`: 12Y%-15" Champion: Willie Blue Boy, owned by John & Valerie Tri
- `S4/O` / `missing_owned_by`: 3rd: Trevor, last name not provided
- `S4/O` / `missing_owned_by`: 1st: Kristen Mogrovejo, handling North Country Petey
- `S4/O` / `missing_owned_by`: 2nd: Jessica Morrison, handling Cody
- `S4/O` / `missing_owned_by`: 3rd: Felicia Franklin, handling Gadget
- `S4/O` / `missing_owned_by`: 1st: Katie Fitzgerald, handling Winslow Genevieve
- `S4/O` / `missing_owned_by`: 2nd: Rocky Cassone, handling Muscle Russell Comet
