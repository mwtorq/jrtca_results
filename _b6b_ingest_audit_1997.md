# B6b cleanup + ingest audit — 1997

Catalog: `_OCR_CLEANUP_CATALOG_HANDOFF.md`
Volumes: 4  cleaned=0  PASS=0  WARN=0  FAIL=4
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
| FAIL | False | 50 | 7 | O6×25,C1×25,S4/O×4,C6×3 | `1997 Vol I pt 1_ocr_hqmax.txt` |
| FAIL | False | 32 | 2 | C1×25,O6×7,S4/O×2 | `1997 Vol I pt 2_ocr_hqmax.txt` |
| FAIL | False | 29 | 14 | C1×25,S4/O×7,C6×6,O6×4,?/4th_then_6th_no_5×1 | `1997 Vol II pt 1_ocr_hqmax.txt` |
| FAIL | False | 45 | 6 | C1×25,O6×20,S4/O×3,C6×3 | `1997 Vol II pt 2_ocr_hqmax.txt` |

## Sample residual hits (after cleanup)

### `1997 Vol I pt 1_ocr_hqmax.txt` (FAIL)
- `O6` / `owner_tail_trunc`: 2nd: Foxy Roxy, owned by Dave & Vincent Ste
- `O6` / `owner_tail_trunc`: 4th: Heaven Hill Foxy, owned by Doug Steph
- `O6` / `owner_tail_trunc`: 6th: Camerton Hall Peggy Sue, owned by Alte
- `O6` / `owner_tail_trunc`: 2nd: Blackland Lucky, owned by Doug Stephel
- `O6` / `owner_tail_trunc`: 6th: Foxbolt Bugs, owned by Bob & Cindy Baz
- `O6` / `owner_tail_trunc`: 2nd: Camerton Hall Scholar, owned by Jack
- `O6` / `owner_tail_trunc`: 3rd: Katie of Camerton Hall, owned by Jack
- `O6` / `owner_tail_trunc`: 4th: Rustler's Camilla Moon, owned by Tony
- `O6` / `owner_tail_trunc`: 2nd: Cromwell Stimpy, owned by Heather Crom
- `O6` / `owner_tail_trunc`: 3rd: Heaven Hill Zodiac, owned by Mike & Bett
- `O6` / `owner_tail_trunc`: 6th: R.A. Bandit, owned by Mike & Betty Bilinsk
- `O6` / `owner_tail_trunc`: 1st: R.A. Piker, owned by George & Linda Louc

### `1997 Vol I pt 2_ocr_hqmax.txt` (FAIL)
- `O6` / `owner_tail_trunc`: 1st: Fox Run Scout, owned by Gerald & Joanne Van
- `O6` / `owner_tail_trunc`: 6th: Long Hope Tucker, owned by Lynda Kru
- `O6` / `owner_tail_trunc`: 5th: Hopdiggity Ginger, owned by Liz Littman & Ali Mae Hop
- `O6` / `owner_tail_trunc`: Reserve: Fox Run Dagger, owned by Sandra Ferber Sr
- `O6` / `owner_tail_trunc`: 3rd: Hopdiggity Ginger, owned by Liz Littman & Ali Mae Hop
- `O6` / `owner_tail_trunc`: 1st: Hopdiggity Ginger, owned by Liz Littman & Ali Mae Top
- `O6` / `owner_tail_trunc`: 5th: Pocoshock Sir Winston, owned by Charles & Sally Hickey Sir
- `S4/O` / `missing_owned_by`: 1st: High Mountain Lucy, Karen Vernon
- `S4/O` / `missing_owned_by`: 2nd: , Courtney Bottington
- `C1` / `class_header_gap`: 1st: Farmoliff Ben, owned by Bob Franklin
- `C1` / `class_header_gap`: 1st: Farmcliff Sassy, owned by Bob Franklin
- `C1` / `class_header_gap`: 1st: Lizzie, owned by Rick & Mary Thornton

### `1997 Vol II pt 1_ocr_hqmax.txt` (FAIL)
- `?` / `4th_then_6th_no_5`: 4th: 1 arv Varn niwined hu laa RaatidAin
6th: Lacy Vern, owned by Joe Beaudoin
- `O6` / `owner_tail_trunc`: 2nd: The Larches Fuego, owned by Donald & Joan LaPlace Brut
- `O6` / `owner_tail_trunc`: 4th: The Larches Fuego, owned by Donald & Joan LaPlace The
- `O6` / `owner_tail_trunc`: 1st: Iwi Ji Ww Villy 1 /4 vd od bw IW 4 IIS) Bm HILT Sr I» wv 1st: Lickity Split Vanna, owned by Didi Gough eo Jd. ™e' we Tmt mie ie me wd Lea, Tye be mem Ee EA
- `O6` / `owner_tail_trunc`: 4th: Magnolia Blossom, owned by Sharon Key
- `S4/O` / `missing_owned_by`: 6th: Blue Barns Tracker, R. & D. Zampella
- `S4/O` / `missing_owned_by`: 4th: Timber DiAd~s heameomr, mctim mA Le. OL PY 1
- `S4/O` / `missing_owned_by`: 1st: Katlin Cortenbach, handling Little Orbit of Cortenbach
- `S4/O` / `missing_owned_by`: 3rd: Kari Carlsen, handling Westgate Ruffian
- `S4/O` / `missing_owned_by`: 1st: Ali Mae Hop, handling Hopdiggity Checkers
- `S4/O` / `missing_owned_by`: 2nd: Pat Martin, handling Bar-C Abilene Rose
- `S4/O` / `missing_owned_by`: 2nd: Matisse, Ruth Evans

### `1997 Vol II pt 2_ocr_hqmax.txt` (FAIL)
- `O6` / `owner_tail_trunc`: Reserve: Boggsborough Billie, owned by Jack & Marilynn Pryc
- `O6` / `owner_tail_trunc`: 1st: Runamuk Phillida Erskine-Brown, owned by Richard & Patricia Vin
- `O6` / `owner_tail_trunc`: 1st: Kenswick Cannon, owned by Lea Bos
- `O6` / `owner_tail_trunc`: 3rd: Scamper Tally-Ho, owned by Brenda Zeh
- `O6` / `owner_tail_trunc`: 4th: Scamper Tally-Ho, owned by Brenda Zeh
- `O6` / `owner_tail_trunc`: 5th: Scamper Tally-Ho, owned by Brenda Zeh
- `O6` / `owner_tail_trunc`: 4th: Rainland Hy Type, owned by Forrest & Ann Walling Tie
- `O6` / `owner_tail_trunc`: Reserve: Farmstead Damage, owned by D.Ellis/S.Ferber Ses
- `O6` / `owner_tail_trunc`: 1st: Farmcliff Becky, owned by D. Sturz/J.McCoy Ind Eav Bin Inf Airis bar Vialaria WA Ace
- `O6` / `owner_tail_trunc`: 1st: Foxmoor Rudy Judy, owned by Ruth Cartier Sr
- `O6` / `owner_tail_trunc`: 5th: Greenwood Lucy, owned by Bobby Duty Ili
- `O6` / `owner_tail_trunc`: 6th: Button Top Pawsy, owned by Bobby Duty Ill
