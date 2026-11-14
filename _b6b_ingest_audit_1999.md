# B6b cleanup + ingest audit — 1999

Catalog: `_OCR_CLEANUP_CATALOG_HANDOFF.md`
Volumes: 6  cleaned=6  PASS=0  WARN=0  FAIL=6
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
| FAIL | True | 16 | 0 | C7×10,C1/C6×6 | `1999 Vol I, pt 1_ocr_hqmax.txt` |
| FAIL | True | 9 | 0 | C7×6,C1/C6×2,C1×1 | `1999 Vol I, pt 2_ocr_hqmax.txt` |
| FAIL | True | 7 | 0 | C1/C6×4,C7×3 | `1999 Vol II, pt 1_ocr_hqmax.txt` |
| FAIL | True | 1 | 0 | C1/C6×1 | `1999 Vol II, pt 2_ocr_hqmax.txt` |
| FAIL | True | 12 | 0 | C7×10,C1/C6×2 | `1999 Vol III, pt 1_ocr_hqmax.txt` |
| FAIL | True | 11 | 0 | C7×6,C1/C6×3,H8×2 | `1999 Vol III, pt 2_ocr_hqmax.txt` |

## Sample residual hits (after cleanup)

### `1999 Vol I, pt 1_ocr_hqmax.txt` (FAIL)
- `C1/C6` / `incomplete_entries`: California Bred Dog                                       Entries: 3 | places=0/3 | California Bred Bitch                                    Ent
- `C1/C6` / `incomplete_entries`: Jumpers, 10 up to 12 1/2" Entries: 11 | places=0/6 | Jumpers, 10 up to 121." Entries: 11
- `C1/C6` / `incomplete_entries`: Dog Pups, 6 up to 9 months, r/br Entries: 4 | places=0/4 | Entries: 3
- `C1/C6` / `incomplete_entries`: Working Terrier Dog, 10 up to 122" Entries: 4 | places=0/4 | Reserve: Briarpatch Solomon, owned by Teresa Wellman
- `C1/C6` / `incomplete_entries`: Locating Adults                         Entries: 15 | places=0/6 | DIVISION
- `C1/C6` / `incomplete_entries`: {andling Agility, On Lead                    Entries: 7 | places=0/6 | Judges: John Broadhurst, Conformation; Robby Robson, Go-to-G
- `C7` / `best_reserve_missing_header`: Best: Runamuk Gnat, owned by Harry & Mary Abbott
- `C7` / `best_reserve_missing_header`: Best: Sow's Ear See Bee, owned by J & L Renfro/K. McCarthy
- `C7` / `best_reserve_missing_header`: Reserve: Runamuk Gnat, owned by Harry & Mary Abbott
- `C7` / `best_reserve_missing_header`: 12%:-15" Champion:
- `C7` / `best_reserve_missing_header`: 12Y2-15" Reserve:
- `C7` / `best_reserve_missing_header`: Reserve: Briarpatch Solomon, owned by Teresa Wellman

### `1999 Vol I, pt 2_ocr_hqmax.txt` (FAIL)
- `C1/C6` / `incomplete_entries`: Pups, 6 up to 9 months, 10 up to 1214" Entries: 12 | places=0/6 | Pups. 9 un to 12 monthe 10 un to 1
- `C1/C6` / `incomplete_entries`: Starters Agility, Off Lead, 10 up to 121" Entries: 5 | places=0/5 | Veterans, 6 years & older, over 12 1/2-15" Entries: 1 1st: M
- `C1` / `midclass_page_dropout`: Open Puppy Entries: 8 | after page got 6th expected 1 | 6th:
- `C7` / `best_reserve_missing_header`: Best: Fox Run Hustler, owned by Karen Fitzpatrick
- `C7` / `best_reserve_missing_header`: Reserve: Brandywine Shyster, owned by Carrie LaCombe
- `C7` / `best_reserve_missing_header`: Reserve: Hedgerow Chance, owned by Rhonda Rebhorn
- `C7` / `best_reserve_missing_header`: Reserve: Orchard Hill Dior, owned by Robby & Cheryl Robson
- `C7` / `best_reserve_missing_header`: Reserve: 3 T's Terra, owned by Greg Boyland
- `C7` / `best_reserve_missing_header`: Best: Del Sol Epic, owned by Darlene Gilmore

### `1999 Vol II, pt 1_ocr_hqmax.txt` (FAIL)
- `C1/C6` / `incomplete_entries`: Dog Pups, 6 up to 9 months Entries: 8 | places=0/6 | Dog Pups, 9 up to 12 months                             Entr
- `C1/C6` / `incomplete_entries`: 2s, 1 yr & older, over 121-15" Entries: 9 | places=0/6 | Y RACING CHAMPION & RESERVE
- `C1/C6` / `incomplete_entries`: Novice                                                            Entries: 8 | places=0/6 | Judges: Linda Cowasiee, Conformation; Rustom Cowasjee, Go-to
- `C1/C6` / `incomplete_entries`: Youth Handler                                                   Entries: 4 | places=0/4 | EOF
- `C7` / `best_reserve_missing_header`: Best: Black Watch Busy, owned by L.Maher/M.Sanders
- `C7` / `best_reserve_missing_header`: Best: Live Wire Super Bee, owned by Charles & Julie Kemp
- `C7` / `best_reserve_missing_header`: Best: Double D Tally Ho, owned by Dan & Dorothy Whiting

### `1999 Vol II, pt 2_ocr_hqmax.txt` (FAIL)
- `C1/C6` / `incomplete_entries`: Dog Pups, 9 up to 12 months, over 12-15" Entries: 3 | places=0/3 | Bitch Pups, 6 up to 9 months, 10 up to 1212" Entries: 5

### `1999 Vol III, pt 1_ocr_hqmax.txt` (FAIL)
- `C1/C6` / `incomplete_entries`: Child Handler Entries: 5 | places=0/5 | Entries: 5
- `C1/C6` / `incomplete_entries`: Sub Novice Entries: 16 | places=0/6 | Entries: 16
- `C7` / `best_reserve_missing_header`: Reserve: 3 T's Terra, owned by Greg Boyland
- `C7` / `best_reserve_missing_header`: Reserve: Sterling Bridge Awesome Uzi, owned by J. & A. Phillip:
- `C7` / `best_reserve_missing_header`: Reserve: Rebby Bassettee
- `C7` / `best_reserve_missing_header`: Reserve: Littlemoor Panda, owned by Jill Denker
- `C7` / `best_reserve_missing_header`: Best: Littlemoor Panda, owned by Jill Denker
- `C7` / `best_reserve_missing_header`: Reserve: Point of View Simon, owned by Bud & Judy Moomau
- `C7` / `best_reserve_missing_header`: Best: Brandywine Shyster, owned by Carrie LaCombe
- `C7` / `best_reserve_missing_header`: Reserve: Little Eden Reveille, owned by Michelle Ward
- `C7` / `best_reserve_missing_header`: Reserve: Foxfield Garth, owned by Debbie Verg
- `C7` / `best_reserve_missing_header`: Reserve: Del Sol Shine, owned by Beau & Kathleen White

### `1999 Vol III, pt 2_ocr_hqmax.txt` (FAIL)
- `H8` / `champ_abbrev`: serve: Marvelous Fergie, owned by Bill & Jill Poe
- `H8` / `champ_abbrev`: serve: Marvelous Helen, owned by Megan Walker
- `C1/C6` / `incomplete_entries`: Bitch Pups, 6 up to 9 months, r/br – Entries: 6 | places=0/6 | Entries: 6
- `C1/C6` / `incomplete_entries`: Dogs, 1st 1yr. Foxport & older, Tex, over owned 12-15" by Tooie Crooks Entries:  | places=0/4 | VETERAN RACING CHAMPION & RESERVE
- `C1/C6` / `incomplete_entries`: Bred by Exhibitor Bitch Entries: 25 Working Terrier Dog, 12' up to 15", smooth E | places=0/6 | Bred by Exhibitor Bitch Entries: 25
- `C7` / `best_reserve_missing_header`: Reserve: Boggsborough Bonsai, owned by Robert & Linda Fleck
- `C7` / `best_reserve_missing_header`: Best: Copper Horse Salty Dog, owned by David & Lisa McKinney
- `C7` / `best_reserve_missing_header`: Reserve: Thistledown Renegade, owned by C. & D. Hufnagel
- `C7` / `best_reserve_missing_header`: Reserve: Willie Biue Boy, owned by John & Valerie Tritt
- `C7` / `best_reserve_missing_header`: Best: Point of View Samara, owned by Bud & Judy Moomau
- `C7` / `best_reserve_missing_header`: Best: Fox Run Hustler, owned by Karen Fitzpatrick
