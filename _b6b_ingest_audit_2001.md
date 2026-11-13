# B6b cleanup + ingest audit — 2001

Catalog: `_OCR_CLEANUP_CATALOG_HANDOFF.md`
Volumes: 14  cleaned=6  PASS=4  WARN=0  FAIL=10
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
| FAIL | True | 3 | 0 | C6×3 | `2001 Coal Tree Farm_ocr_hqmax.txt` |
| PASS | False | 0 | 0 | — | `2001 South Coast_ocr_hqmax.txt` |
| PASS | False | 0 | 0 | — | `2001 Troon Quarry_ocr_hqmax.txt` |
| FAIL | True | 16 | 0 | C6×14,C6/O1×2 | `2001 Vol I_ocr_hqmax.txt` |
| FAIL | True | 1 | 0 | C6×1 | `2001 MWJRTC II Wheatland I & II_ocr_hqmax.txt` |
| PASS | False | 0 | 0 | — | `2001 OH-PA II_ocr_hqmax.txt` |
| FAIL | False | 1 | 0 | ?/4th_then_2nd×1 | `2001 Paumanok Farmstead Dutchess County_ocr_hqmax.txt` |
| PASS | False | 0 | 0 | — | `2001 PNWJRTN_ocr_hqmax.txt` |
| FAIL | False | 4 | 0 | C6/O1×2,C6×2 | `2001 Summer Celebration_ocr_hqmax.txt` |
| FAIL | True | 13 | 0 | C6×9,?/4th_then_2nd×2,S4/O×2 | `2001 Vol II pt 1_ocr_hqmax.txt` |
| FAIL | False | 13 | 0 | C6×8,S4/O×4,C6/O1×1 | `2001 Vol II pt 2_ocr_hqmax.txt` |
| FAIL | False | 4 | 0 | S4/O×3,S4×1 | `2001 Yankee_ocr_hqmax.txt` |
| FAIL | True | 11 | 0 | C6×6,S4/O×3,?/4th_then_2nd×1,?/4th_then_6th_no_5×1 | `2001 Vol III pt 1_ocr_hqmax.txt` |
| FAIL | True | 3 | 0 | S4/O×2,?/4th_then_6th_no_5×1 | `2001 Vol III pt 2_ocr_hqmax.txt` |

## Sample residual hits (after cleanup)

### `2001 Coal Tree Farm_ocr_hqmax.txt` (FAIL)
- `C6` / `orphan_entry_count`: 16
- `C6` / `orphan_entry_count`: 6
- `C6` / `orphan_entry_count`: 3

### `2001 Vol I_ocr_hqmax.txt` (FAIL)
- `C6/O1` / `bare_entries`: Entries:
- `C6` / `orphan_entry_count`: 3
- `C6` / `orphan_entry_count`: 6
- `C6` / `orphan_entry_count`: 2
- `C6` / `orphan_entry_count`: 5
- `C6` / `orphan_entry_count`: 38
- `C6` / `orphan_entry_count`: 21
- `C6` / `orphan_entry_count`: 15

### `2001 MWJRTC II Wheatland I & II_ocr_hqmax.txt` (FAIL)
- `C6` / `orphan_entry_count`: 9

### `2001 Paumanok Farmstead Dutchess County_ocr_hqmax.txt` (FAIL)
- `?` / `4th_then_2nd`: 4th: Arins Trax, owned by Alison Linstrum
2nd: Sows Ear Tuck, owned by Bob & Genie Franklin

### `2001 Summer Celebration_ocr_hqmax.txt` (FAIL)
- `C6/O1` / `bare_entries`: Entries:
- `C6` / `orphan_entry_count`: 18
- `C6` / `orphan_entry_count`: 12

### `2001 Vol II pt 1_ocr_hqmax.txt` (FAIL)
- `?` / `4th_then_2nd`: 4th: jth: Jake Man, owned by Steve & Sandy Langheld
2nd: Priscilla, owned by Kathy Hartsfield
- `S4/O` / `missing_owned_by`: 2nd: Farmcliff Holland, owried Dy Doug & Sue Tack
- `C6` / `orphan_entry_count`: 11
- `C6` / `orphan_entry_count`: 10
- `C6` / `orphan_entry_count`: 6
- `C6` / `orphan_entry_count`: 2
- `C6` / `orphan_entry_count`: 4
- `C6` / `orphan_entry_count`: 7

### `2001 Vol II pt 2_ocr_hqmax.txt` (FAIL)
- `S4/O` / `missing_owned_by`: 3rd: Washa Charlie, ownéd by Dani Phillips
- `S4/O` / `missing_owned_by`: 2nd: pov Creek Theft,  es Mary Lou Sa
- `S4/O` / `missing_owned_by`: 3rd:      Na TL Clementine, by Doug & Sue Tack
- `S4/O` / `missing_owned_by`: 3rd: Farmcliiff Clancy, owned 3 Lou a acy
- `C6/O1` / `bare_entries`: Entries:
- `C6` / `orphan_entry_count`: 3
- `C6` / `orphan_entry_count`: 4
- `C6` / `orphan_entry_count`: 7
- `C6` / `orphan_entry_count`: 22

### `2001 Yankee_ocr_hqmax.txt` (FAIL)
- `S4` / `mangled_by`: 4th:      Round the Bend Foxy pn ome by G.  Harvey & S. Ryan
- `S4/O` / `missing_owned_by`: 4th:   Farmcliff Duke, owned
- `S4/O` / `missing_owned_by`: 5th:      Northgate Hallie, we! Lom Doug & Sue Tack
- `S4/O` / `missing_owned_by`: 2nd: Foxhal Tasha,  Pd by Don 8 Gail Stock

### `2001 Vol III pt 1_ocr_hqmax.txt` (FAIL)
- `?` / `4th_then_2nd`: 4th: Seaview Chanel, owned by Didi Gough
2nd: Seaview Steletta, owned by Didi Gough
- `?` / `4th_then_6th_no_5`: 4th: 5" Winslow Genevieve, owned by Lisa Fitzgerald (tie)
6th: Picadilly Tally, owned by John & Judy Tyno
- `S4/O` / `missing_owned_by`: 3rd: A [ab lpr . PES RO PR Ls) aD Rs i SAREE J EN I Bx es rl . . >. DEAS : Tr ne Oe Dar pes, et Som Sheer or, i renoh RA FEE TTI RYT RI XT [ Eb Re iA BY? Phos E
- `S4/O` / `missing_owned_by`: 2nd: Farmcliff Mertin,-owned-by.Karin Franklin
- `S4/O` / `missing_owned_by`: Reserve: Farmcliff- Merlin, owned-by Karin Franklin»
- `C6` / `orphan_entry_count`: 2
- `C6` / `orphan_entry_count`: 15
- `C6` / `orphan_entry_count`: 6
- `C6` / `orphan_entry_count`: 1

### `2001 Vol III pt 2_ocr_hqmax.txt` (FAIL)
- `?` / `4th_then_6th_no_5`: 4th: Tortilla Flat Milo, owned by Joey Gerding
6th: Anderson Acres Ellie May, owned by Tony & Kim Anderson
- `S4/O` / `missing_owned_by`: 5th:     Pepper, pa by Richard Burfoot
- `S4/O` / `missing_owned_by`: 2nd: Farmeliftdoe, ownediby Bobi& Genie Franklin
