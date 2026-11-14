# B6b cleanup + ingest audit — 2000

Catalog: `_OCR_CLEANUP_CATALOG_HANDOFF.md`
Volumes: 5  cleaned=5  PASS=0  WARN=0  FAIL=5
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
| FAIL | True | 29 | 0 | C7×20,C1/C6×8,C1×1 | `2000 Vol I_ocr_hqmax.txt` |
| FAIL | True | 46 | 0 | C7×22,C1/C6×20,H8×3,S1-S3×1 | `2000 Vol II_ocr_hqmax.txt` |
| FAIL | True | 14 | 0 | C7×8,C1/C6×6 | `2000 vol 3 pt 1_ocr_hqmax.txt` |
| FAIL | True | 35 | 0 | C1/C6×21,C7×13,C1×1 | `2000 Vol III pt 1_ocr_hqmax.txt` |
| FAIL | True | 3 | 0 | C7×2,C1/C6×1 | `2000 Vol III pt 2_ocr_hqmax.txt` |

## Sample residual hits (after cleanup)

### `2000 Vol I_ocr_hqmax.txt` (FAIL)
- `C1/C6` / `incomplete_entries`: Youth Handler Entries: 5 | places=0/5 | Bitch Pups, 9 up to 12 months, r/br                       En
- `C1/C6` / `incomplete_entries`: Youth Handler Entries: 3 | places=0/3 | ADULT RACING CHAMPION & RESERVE
- `C1/C6` / `incomplete_entries`: Dog Pups, 6 up to 9 months, r/br . Entries: 14 | places=0/6 | Dog Pups, 9 up to 12 months, smooth                  Entries
- `C1/C6` / `incomplete_entries`: Youth Handler Entries: 5 | places=0/5 | Judges: Terri Batzer & Nancy Breakstone, Conformation: Larry
- `C1/C6` / `incomplete_entries`: Champienship Certificate, 12 up to 15" Entries: 15 | places=0/6 | Champion: Westmorland Best Bet Yet, owned by Allen Whitaker
- `C1/C6` / `incomplete_entries`: Bitches, 1 yr. & older, over 12!-15" Entries: 13 | places=0/6 | Veterans, 6 years & older, over 12/4-15" Entries: 2
- `C1/C6` / `incomplete_entries`: Novice Puppy                                                         Entries: 5 | places=0/5 | Novice Adult                                                
- `C1` / `midclass_page_dropout`: Open Puppy                                                           Entries: 10 | after page got 6th expected 1 | 6th: Jake, owner not provided
- `C7` / `best_reserve_missing_header`: Reserve: Fox Island Remy, owned by Lori Thompson
- `C7` / `best_reserve_missing_header`: Best: Charade Ivory, owned by Jim & Jan Brady
- `C7` / `best_reserve_missing_header`: Reserve: Terrier-ific Blue Jeans, handled by Danielle Schepman
- `C7` / `best_reserve_missing_header`: Reserve: Hopdiggity Victor, owned by Wendy Calvert

### `2000 Vol II_ocr_hqmax.txt` (FAIL)
- `H8` / `champ_abbrev`: serve: Shingle Oak Willow, owned by Diane Wright
- `H8` / `champ_abbrev`: serve: Fox Run Skye, owned by S. Ferber
- `C1/C6` / `incomplete_entries`: Bitches, 1 yr. & older, 10 up to 121%" Entries: 25 | places=0/6 | boorhivvy yi RM VIEL, IVUM ED 1272 Entries: 25 | 1st Farmcli
- `C1/C6` / `incomplete_entries`: Pre-Novice Puppy                                                   Entries: 4 | places=0/4 | Novice Puppy                                                
- `C1/C6` / `incomplete_entries`: Dogs, 1 yr & older, over 12 1/2-15" Entries: 15 | places=0/6 | Reserve: Prestige Farms Oliver, owned by Jennifer Gilligan
- `C1/C6` / `incomplete_entries`: Agility II, Off Lead Entries: 6 | places=0/6 | Novice Adult Entries: 6 1st: Farmcliff Spencer, owned by Gen
- `C1/C6` / `incomplete_entries`: tch Pups, 6 up to 9 months, r/br Entries: 5 | places=0/5 | ch Pups, 9 up to 12 months, smooth Entries: 3
- `C1/C6` / `incomplete_entries`: ch Pups, 9 up to 12 months, smooth Entries: 3 | places=0/3 | ch Pups, 9 up to 12 months, r/br Entries: 7
- `C1/C6` / `incomplete_entries`: Bitches, 1 yr. & older, 10 up to 12 1/2" Entries: 9 | places=0/6 | Bitches, 1 yr. & older, over 12 1/2-15" Entries: 10
- `C1/C6` / `incomplete_entries`: Bitches, 1 yr. & older, over 12 1/2-15" Entries: 10 | places=0/6 | erans, 6 years & older, 10 up to 1214" Entries: 2
- `C1/C6` / `incomplete_entries`: erans, 6 years & older, over 1215-15" Entries: 5 | places=0/5 | PY RACING CHAMPION & RESERVE
- `C1/C6` / `incomplete_entries`: Youth Handler Entries: 9 | places=0/6 | Bitches, 1 yr. & older, 10 up to 12 1/2", r/br Entries: 6 2n

### `2000 vol 3 pt 1_ocr_hqmax.txt` (FAIL)
- `C1/C6` / `incomplete_entries`: Neutered Adult Dog Entries: 5 | places=0/5 | Spayed Adult Bitch                                          
- `C1/C6` / `incomplete_entries`: Bitches, 1 yr. & older, 10 up to 1212", smooth         Entries: 14 | places=0/6 | Bitches, 1 yr. & older, 10 up to 121", r/br              Ent
- `C1/C6` / `incomplete_entries`: Novice                                                             Entries: 5 | places=0/5 | Open                                                        
- `C1/C6` / `incomplete_entries`: Child Handler Go-to-Ground Entries: 6 | places=0/6 | Judges: Martyn & Elizabeth Hulme, Confirmation; Cheryl Hart,
- `C1/C6` / `incomplete_entries`: Child Handler Entries: 5 | places=0/5 | ADULT RACING CHAMPION & RESERVE
- `C1/C6` / `incomplete_entries`: Youth Handling Agility, On Lead                        Entries: 3 | places=0/3 | uth Handling Agility, Off Lead                         Entri
- `C7` / `best_reserve_missing_header`: Best: Brandywine Kona, owned by Jim & Sally Saul
- `C7` / `best_reserve_missing_header`: Reserve: Courtwood Caper, owned by Debbie & Rusty Graydon
- `C7` / `best_reserve_missing_header`: Reserve: Horsemasters Mick, owned by Paul McWilliams
- `C7` / `best_reserve_missing_header`: Best: Brandywine Swap, owned by Karen Fitzpatrick
- `C7` / `best_reserve_missing_header`: Reserve: Brandywine Swap, owned by Karen Fitzpatrick
- `C7` / `best_reserve_missing_header`: Reserve: Two Faces Cheeky, owned by Jan DeWinter

### `2000 Vol III pt 1_ocr_hqmax.txt` (FAIL)
- `C1/C6` / `incomplete_entries`: zhampionship Certificate, 10 up to 121." Entries: 7 | places=0/6 | Champion: Rainland Flurry, owned by Cathy Hedberg
- `C1/C6` / `incomplete_entries`: Novice                                                             Entries: 5 | places=0/5 | Open                                                        
- `C1/C6` / `incomplete_entries`: Child Handler Entries: 5 | places=0/5 | ADULT RACING CHAMPION & RESERVE
- `C1/C6` / `incomplete_entries`: 4 Dogs, 1st 1 Pheasant yr. & older, Hill 10 Rocki, up to owned 12" by Scott & Su | places=0/6 | 12/15" Reserve: Whippersnapper Samantha, owned by A. Cassity
- `C1/C6` / `incomplete_entries`: re-Novice Puppy Entries: 14 | places=0/6 | ovice Puppy                                                 
- `C1/C6` / `incomplete_entries`: Spayed Adult Bitch Entries: 5 | places=0/5 | bility To Red Fox Entries: 6
- `C1/C6` / `incomplete_entries`: bility To Red Fox Entries: 6 | places=0/6 | vility to Gray Fox Entries: 6
- `C1/C6` / `incomplete_entries`: vility to Gray Fox Entries: 6 | places=0/6 | ups, 6 up to 9 months, smooth Entries: 2
- `C1/C6` / `incomplete_entries`: ups, 6 up to 9 months, r/br Entries: 8 | places=0/6 | ups, 9 up to 12 months, smooth Entries: 3
- `C1/C6` / `incomplete_entries`: ups, 9 up to 12 months, smooth Entries: 3 | places=0/3 | ups, 9 up to 12 months, r/br Entries: 6
- `C1/C6` / `incomplete_entries`: 6 up to 9 months, 10 up to 12 1/2" Entries: 8 | places=0/6 | 6 up to 9 months, over 12/15" Entries: 5
- `C1/C6` / `incomplete_entries`: 6 up to 9 months, over 12/15" Entries: 5 | places=0/5 | Tanner, owned by Susan Riley,9 up to 12 months, 10 up to 121

### `2000 Vol III pt 2_ocr_hqmax.txt` (FAIL)
- `C1/C6` / `incomplete_entries`: Agility I Entries: 3 | places=0/3 | Champion: Fox Chase Maddy, owned by Linda Knowles
- `C7` / `best_reserve_missing_header`: Reserve: Gathering Storm Krakerjak, owned by J. Thole
- `C7` / `best_reserve_missing_header`: Reserve: Adam Conrad
