# B6b cleanup + ingest audit — 1991

Catalog: `_OCR_CLEANUP_CATALOG_HANDOFF.md`
Volumes: 4  cleaned=4  PASS=3  WARN=0  FAIL=1
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
| PASS | True | 0 | 0 | — | `Document_2026-11-03_201758_ocr_hqmax.txt` |
| FAIL | True | 3 | 0 | C1×3 | `Document_2026-11-03_205014_ocr_hqmax.txt` |
| PASS | True | 0 | 0 | — | `Document_2026-11-03_210248_ocr_hqmax.txt` |
| PASS | True | 0 | 0 | — | `Document_2026-11-03_211454_ocr_hqmax.txt` |

## Sample residual hits (after cleanup)

### `Document_2026-11-03_205014_ocr_hqmax.txt` (FAIL)
- `C1` / `place_rank_gap`: Bitch Pups, 6 up to 12 months                                | 3th then 6th | 6th: Ms. Scarlett of Hidden Hollow, owned by Marline Berthault
- `C1` / `place_rank_gap`: Bitches, 1 yr & over, 10--12-1/2" Entries: 6 | 1th then 6th | 6th: Fox Hollow Squiggy, owned by Sarah Wilcox
- `C1` / `place_rank_gap`:  | 2th then 5th | 5th: Meynell Trillium of Ravenswood, owned by Janet & Ben Sutcliffe
