# B6b cleanup + ingest audit — 1997

Catalog: `_OCR_CLEANUP_CATALOG_HANDOFF.md`
Volumes: 4  cleaned=0  PASS=1  WARN=0  FAIL=3
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
| FAIL | False | 1 | 0 | C6×1 | `1997 Vol I pt 1_ocr_hqmax.txt` |
| PASS | False | 0 | 0 | — | `1997 Vol I pt 2_ocr_hqmax.txt` |
| FAIL | False | 4 | 0 | C6×3,S4/O×1 | `1997 Vol II pt 1_ocr_hqmax.txt` |
| FAIL | False | 2 | 0 | C6×2 | `1997 Vol II pt 2_ocr_hqmax.txt` |

## Sample residual hits (after cleanup)

### `1997 Vol I pt 1_ocr_hqmax.txt` (FAIL)
- `C6` / `orphan_entry_count`: 1

### `1997 Vol II pt 1_ocr_hqmax.txt` (FAIL)
- `S4/O` / `missing_owned_by`: 4th: Timber DiAd~s heameomr, mctim mA Le. OL PY 1
- `C6` / `orphan_entry_count`: 31
- `C6` / `orphan_entry_count`: 16
- `C6` / `orphan_entry_count`: 5

### `1997 Vol II pt 2_ocr_hqmax.txt` (FAIL)
- `C6` / `orphan_entry_count`: 10
- `C6` / `orphan_entry_count`: 12
