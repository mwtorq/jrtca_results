# B6b cleanup + ingest audit — 1997

Catalog: `_OCR_CLEANUP_CATALOG_HANDOFF.md`
Volumes: 4  cleaned=4  PASS=0  WARN=1  FAIL=3
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
| FAIL | True | 20 | 6 | O6×11,C1×9,C6×3,S4/O×2,?/4th_then_2nd×1 | `1997 Vol I pt 1_ocr_hqmax.txt` |
| WARN | True | 0 | 2 | S4/O×2 | `1997 Vol I pt 2_ocr_hqmax.txt` |
| FAIL | True | 8 | 13 | C1×8,S4/O×7,C6×6 | `1997 Vol II pt 1_ocr_hqmax.txt` |
| FAIL | True | 8 | 6 | C1×5,O6×3,S4/O×3,C6×3 | `1997 Vol II pt 2_ocr_hqmax.txt` |

## Sample residual hits (after cleanup)

### `1997 Vol I pt 1_ocr_hqmax.txt` (FAIL)
- `?` / `4th_then_2nd`: 4th: Farmdliff Justin, owned by Kelly Morander oa rx tf «{ 1 ELL 4. I LC RTI ad. D1 Ye
2nd: Farmcliff Snow Flake, owned by Genie Franklin
- `O6` / `owner_tail_trunc`: 2nd: Foxy Roxy, owned by Dave & Vincent Ste
- `O6` / `owner_tail_trunc`: 4th: Heaven Hill Foxy, owned by Doug Steph
- `O6` / `owner_tail_trunc`: 6th: Camerton Hall Peggy Sue, owned by Alte
- `O6` / `owner_tail_trunc`: 4th: Rustler's Camilla Moon, owned by Tony
- `O6` / `owner_tail_trunc`: 2nd: Rustler's Emma Peel, owned by Tony & Lir
- `O6` / `owner_tail_trunc`: 6th: Heaven Hill Cody, owned by George & Linc
- `O6` / `owner_tail_trunc`: 6th: Camerton Hall Peggy Sue, owned by Alta
- `O6` / `owner_tail_trunc`: 12 1/2-15" Champion: Bamber, owned by Martha Ler
- `O6` / `owner_tail_trunc`: 4th: Scamper Tally Ho, owned by Brenda Zah
- `O6` / `owner_tail_trunc`: 1st: Farmcliff Monet, owned by Charles & Sally Hickey Tl: Eroclr lace stressed Bir BAA
- `O6` / `owner_tail_trunc`: 1st: Long Hope Mickey, owned by Bob Frankiin ~1 AN tT od RA a 8 i ism Lear Tareas KAArae Ase

### `1997 Vol I pt 2_ocr_hqmax.txt` (WARN)
- `S4/O` / `missing_owned_by`: 1st: High Mountain Lucy, Karen Vernon
- `S4/O` / `missing_owned_by`: 2nd: , Courtney Bottington

### `1997 Vol II pt 1_ocr_hqmax.txt` (FAIL)
- `S4/O` / `missing_owned_by`: 6th: Blue Barns Tracker, R. & D. Zampella
- `S4/O` / `missing_owned_by`: 4th: Timber DiAd~s heameomr, mctim mA Le. OL PY 1
- `S4/O` / `missing_owned_by`: 1st: Katlin Cortenbach, handling Little Orbit of Cortenbach
- `S4/O` / `missing_owned_by`: 3rd: Kari Carlsen, handling Westgate Ruffian
- `S4/O` / `missing_owned_by`: 1st: Ali Mae Hop, handling Hopdiggity Checkers
- `S4/O` / `missing_owned_by`: 2nd: Pat Martin, handling Bar-C Abilene Rose
- `S4/O` / `missing_owned_by`: 2nd: Matisse, Ruth Evans
- `C6` / `orphan_entry_count`: 8
- `C6` / `orphan_entry_count`: 31
- `C6` / `orphan_entry_count`: 16
- `C6` / `orphan_entry_count`: 17
- `C6` / `orphan_entry_count`: 5

### `1997 Vol II pt 2_ocr_hqmax.txt` (FAIL)
- `O6` / `owner_tail_trunc`: 4th: Scamper Tally-Ho, owned by Brenda Zeh
- `O6` / `owner_tail_trunc`: 4th: Rainland Hy Type, owned by Forrest & Ann Walling Tie
- `O6` / `owner_tail_trunc`: 1st: Farmcliff Becky, owned by D. Sturz/J.McCoy Ind Eav Bin Inf Airis bar Vialaria WA Ace
- `S4/O` / `missing_owned_by`: Champion: Blue Jeans, Donna Pierce
- `S4/O` / `missing_owned_by`: 5th: Button Top Jim Winston, Joel Pritchet
- `S4/O` / `missing_owned_by`: 6th: Showbizz Fizz, al Darlene Irvine
- `C6` / `orphan_entry_count`: 03
- `C6` / `orphan_entry_count`: 10
- `C6` / `orphan_entry_count`: 12
- `C1` / `class_header_gap`: 1st: Long Hope Minnie, owned by Nellie Niewola
- `C1` / `class_header_gap`: 1st: Sass N' Dash Darby, owned by Michael & Sally Murphy
- `C1` / `class_header_gap`: 1st: Mineral Springs Indiana Bones, owned by Marieliyn Zeock
