# B6b cleanup + ingest audit — 1992

Catalog: `_OCR_CLEANUP_CATALOG_HANDOFF.md`
Volumes: 6  cleaned=3  PASS=4  WARN=0  FAIL=2
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
| PASS | True | 0 | 0 | — | `Document_2026-11-03_212153_ocr_hqmax.txt` |
| FAIL | False | 5 | 0 | C1×4,C1/C6×1 | `Document_2026-11-03_212636_ocr_hqmax.txt` |
| PASS | False | 0 | 0 | — | `Document_2026-11-03_213104_ocr_hqmax.txt` |
| PASS | True | 0 | 0 | — | `Document_2026-11-03_220343_ocr_hqmax.txt` |
| PASS | False | 0 | 0 | — | `Document_2026-11-03_220931_ocr_hqmax.txt` |
| FAIL | True | 4 | 0 | C1×3,C1/C6×1 | `Document_2026-11-03_221749_ocr_hqmax.txt` |

## Sample residual hits (after cleanup)

### `Document_2026-11-03_212636_ocr_hqmax.txt` (FAIL)
- `C1/C6` / `incomplete_entries`: Dog Pups, 6 up to 12 months, 12-1/2-15" Entries: 5 | places=0/5 | Bitch Pups, 6 up to 12 months, 10-12-1/2" Entries: 6
- `C1` / `midclass_page_dropout`: Hollow Terriers – Entries: 13, owned by C.Tatum & S.Yancey | after page got 5th expected 1 | 5th: Ashcreek's Firefox Dottie, owned by Mr.& Mrs. Dickinson
- `C1` / `midclass_page_dropout`: Dogs and Bitches, 1 yr & over, 12-1/2—-15" Entries: 19 | after page got 2th expected 4 | 2nd: Windermere Tattle, owned by L.Cowasjee & D.Kratzer
- `C1` / `midclass_page_dropout`: Dog Pups, 9 up to 12 months, br/r                                                | after page got 5th expected 6 | 5th: Hillside Oliver Twist, owned by Laura Ha
- `C1` / `midclass_page_dropout`: Novice (Adults)                                                                  | after page got 4th expected 5 | 4th: L'il Effort Petey, owned by Kathy Hunter

### `Document_2026-11-03_221749_ocr_hqmax.txt` (FAIL)
- `C1/C6` / `incomplete_entries`: Bitch Pups, 6 up to 12 months, 10--12-1/2" Entries: 3 | places=0/3 | Bitch Pups, 6 up to 12 months, 12-1/2--16" Entries: 1
- `C1` / `midclass_page_dropout`: Dogs; 1 yr & over, 12-12--15" Entries: 7 | after page got 2th expected 4 | 2nd: Windermere Rev, owned by Fred Winbarg
- `C1` / `midclass_page_dropout`: Bitches, 1 yr & over, 12-1/2--15", smooth                                   Entr | after page got 3th expected 5 | 3rd: Hannie, owned by Nancy Drown
- `C1` / `midclass_page_dropout`: CHAMPIONSHIP CERTIFICATE (12-1/2--15")                              Entries: 37 | after page got 5th expected 7 | 5th: The Hollow Pippa of North Country, owned
