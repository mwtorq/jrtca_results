# B6b cleanup + ingest audit — 1993

Catalog: `_OCR_CLEANUP_CATALOG_HANDOFF.md`
Volumes: 5  cleaned=2  PASS=2  WARN=0  FAIL=3
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
| FAIL | True | 11 | 0 | C1/C6×8,C1×2,O6×1 | `Document_2026-11-03_224445_ocr_hqmax.txt` |
| FAIL | False | 6 | 0 | C1×5,C1/C6×1 | `Document_2026-11-03_230536_ocr_hqmax.txt` |
| PASS | False | 0 | 0 | — | `Document_2026-11-03_231659_ocr_hqmax.txt` |
| FAIL | False | 6 | 0 | C1/C6×5,C1×1 | `Document_2026-11-03_233615_ocr_hqmax.txt` |
| PASS | True | 0 | 0 | — | `Document_2026-11-04_002601_ocr_hqmax.txt` |

## Sample residual hits (after cleanup)

### `Document_2026-11-03_224445_ocr_hqmax.txt` (FAIL)
- `C1/C6` / `incomplete_entries`: A Yearbook, Vol. I           19           JRTCNC Win – Entries: 14 | places=0/6 | Entries: 7
- `C1/C6` / `incomplete_entries`: Entries: 7 | places=0/6 | Entries: 11
- `C1/C6` / `incomplete_entries`: Entries: 11 | places=0/6 | Entries: 15
- `C1/C6` / `incomplete_entries`: Entries: 15 | places=0/6 | Entries: 12
- `C1/C6` / `incomplete_entries`: Entries: 12 | places=0/6 | Entries: 6
- `C1/C6` / `incomplete_entries`: Entries: 6 | places=0/6 | Entries: 6
- `C1/C6` / `incomplete_entries`: Puppies, 9 up to 12 months                                                  Entr | places=0/6 | Dogs, 1 yr & over, 10--12-1/2" Entries: 7
- `C1/C6` / `incomplete_entries`: Dog Pups, 6 up to 12 months                                           Entries: 1 | places=0/6 | Dog Pups, 6 up to 12 months                                 
- `C1` / `midclass_page_dropout`: and the Bluegrass Working Terrier Ass | after page got 30th expected 1 | 30rd: Sandercox        Deb McWilliams
- `C1` / `midclass_page_dropout`: Pups, 6 up to 9 months                                                           | after page got 5th expected 6 | 5th: Orchard Hill Elvis Pupsley, owned by Rob
- `O6` / `owner_tail_trunc`: 2nd: Wyndhaven Lonestar, owned by

### `Document_2026-11-03_230536_ocr_hqmax.txt` (FAIL)
- `C1/C6` / `incomplete_entries`: DIVISION A, CONFORMATION – Entries: 4 | places=0/4 | Dog Pups, 4 up to 6 months – Entries: 13
- `C1` / `midclass_page_dropout`: CHAMPIONSHIP CERTIFICATE (12-1/2--15")                            Entries: 16 | after page got 2th expected 4 | 2nd: Lil Rascals Jackie, owned by John Benintend
- `C1` / `midclass_page_dropout`: Dog Pups, 6 up to 9 months                                                     E | after page got 3th expected 4 | 3rd: The Hollow Tracker, owned by The Hollow 
- `C1` / `midclass_page_dropout`: Novice (Adults)                                                                  | after page got 2th expected 4 | 2nd: North Country Penn, owned by Marilyn Pro
- `C1` / `midclass_page_dropout`: Veteran Class – Entries: 5 | after page got 4th expected 5 | 4th: The Manor Bally, owned by C.Young & D.Tarchini
- `C1` / `midclass_page_dropout`: Bitches, 1 yr & over, 10--12-1/2", smooth                                        | after page got 4th expected 5 | 4th: Windermere Jazz, owned by Iris Mensing

### `Document_2026-11-03_233615_ocr_hqmax.txt` (FAIL)
- `C1/C6` / `incomplete_entries`: Bitch Pups, 6 up to 12 months, 10-12-12" Entries: 5 | places=0/5 | Bitch Pups, 6 up to 12 months, 12-1/2--15" Entries: 4
- `C1/C6` / `incomplete_entries`: Dog Pups, 6 up to 9 months                                                       | places=0/3 | Dog Pups, 6 up to 9 months
- `C1/C6` / `incomplete_entries`: Entries: 7 | places=0/6 | Bitch Pups, 9 up to 12 months
- `C1/C6` / `incomplete_entries`: Entries: 12 | places=0/6 | Dogs, 1 yr & over, 12-1/2--15"
- `C1/C6` / `incomplete_entries`: NTAIL BEAR, owned by Susan McRae – Entries: 9 | places=0/6 | OPEN (Adults)                                               
- `C1` / `midclass_page_dropout`: Bitch Pups, 6 up to 9 months                                                  En | after page got 2th expected 7 | 2nd: Heaven Hill
