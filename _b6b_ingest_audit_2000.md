# B6b cleanup + ingest audit — 2000

Catalog: `_OCR_CLEANUP_CATALOG_HANDOFF.md`
Volumes: 5  cleaned=1  PASS=0  WARN=0  FAIL=5
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
| FAIL | True | 7 | 0 | C6×6,S4/O×1 | `2000 Vol I_ocr_hqmax.txt` |
| FAIL | False | 20 | 0 | S4/O×17,?/4th_then_2nd×2,?/4th_then_6th_no_5×1 | `2000 Vol II_ocr_hqmax.txt` |
| FAIL | False | 4 | 0 | S4/O×2,?/4th_then_2nd×1,C6×1 | `2000 vol 3 pt 1_ocr_hqmax.txt` |
| FAIL | False | 3 | 0 | S4/O×3 | `2000 Vol III pt 1_ocr_hqmax.txt` |
| FAIL | False | 3 | 0 | C6/O1×2,O6×1 | `2000 Vol III pt 2_ocr_hqmax.txt` |

## Sample residual hits (after cleanup)

### `2000 Vol I_ocr_hqmax.txt` (FAIL)
- `S4/O` / `missing_owned_by`: 5th: Working Terrier Dog, 10 up to 12 1/2", smooth         Entries:
- `C6` / `orphan_entry_count`: 10
- `C6` / `orphan_entry_count`: 2
- `C6` / `orphan_entry_count`: 16
- `C6` / `orphan_entry_count`: 3

### `2000 Vol II_ocr_hqmax.txt` (FAIL)
- `?` / `4th_then_2nd`: 4th: Fox Run Skye, owned by Chris Levine
2nd: Kenswick Kayla, owned by Sandy McElearney
- `?` / `4th_then_6th_no_5`: 4th: Rustler's Emma Peel, owned by Tony & Lina Marchlinski
6th: Prestwick Hot Shot, owned by Cheryl Johnson
- `S4/O` / `missing_owned_by`: 3rd: ,....-Farmcliff:Kerry,owned. by:Suanne-Mitchell-Jackson"
- `S4/O` / `missing_owned_by`: 3rd: ="Farmcliff-Tea-Cup,owned. by. Richard Minutello
- `S4/O` / `missing_owned_by`: 3rd: Farmcliff-Tackle, owned. by. Megan. Johnson
- `S4/O` / `missing_owned_by`: Champion: Muscle Russell Comet, by M. Mogrovejo
- `S4/O` / `missing_owned_by`: Reserve: Farmcliff Hutch, owned. by D. & M. McMahon'
- `S4/O` / `missing_owned_by`: 3rd: Fenton's Sweet Boy, owned:by Dick Fenton
- `S4/O` / `missing_owned_by`: 3rd: (Wendy Nyland, Owner)ei
- `S4/O` / `missing_owned_by`: 2nd: =Farmelif Holland, owned-by Doug'&Sue- Tack mm»
- `S4/O` / `missing_owned_by`: 3rd: =-Farmcliff-Holland, owned. by. Doug.& Sue-Tack
- `S4/O` / `missing_owned_by`: 3rd: Northgate Hank, owr y Bob Franklin

### `2000 vol 3 pt 1_ocr_hqmax.txt` (FAIL)
- `?` / `4th_then_2nd`: 4th: dth: Briarpatch Winnie, owned by Sharon Kress
2nd: North Country Pringle, owned by Kathy Larson
- `S4/O` / `missing_owned_by`: 2nd: Noaz Jacks Gimme, owned y Susi Laswell
- `S4/O` / `missing_owned_by`: 4th: Big Hickory Captain Jack, owne dby Mary Campbell
- `C6` / `orphan_entry_count`: 10

### `2000 Vol III pt 1_ocr_hqmax.txt` (FAIL)
- `S4/O` / `missing_owned_by`: 4th: Big Hickory Captain Jack, owne dby Mary Campbell
- `S4/O` / `missing_owned_by`: 2nd: Noaz Jacks Gimme, owned y Susi Laswell

### `2000 Vol III pt 2_ocr_hqmax.txt` (FAIL)
- `O6` / `owner_tail_trunc`: 3rd: John Parmenter, owned by Ill
- `C6/O1` / `bare_entries`: Entries:
