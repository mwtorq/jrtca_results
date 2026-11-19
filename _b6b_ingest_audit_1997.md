# B6b cleanup + ingest audit — 1997

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
| PASS | True | 0 | 0 | — | `1997 Vol I pt 1_ocr_hqmax.txt` |
| FAIL | True | 3 | 0 | S4×1,C1×1,C1/C6×1 | `1997 Vol I pt 2_ocr_hqmax.txt` |
| PASS | True | 0 | 0 | — | `1997 Vol II pt 1_ocr_hqmax.txt` |
| PASS | True | 0 | 0 | — | `1997 Vol II pt 2_ocr_hqmax.txt` |

## Sample residual hits (after cleanup)

### `1997 Vol I pt 2_ocr_hqmax.txt` (FAIL)
- `S4` / `mangled_by`: 4th: Not reported by Trial Chairperson
- `C1` / `class_header_gap`: 1st: Little Eden Snap, owned by Michelle Ward
- `C1/C6` / `incomplete_entries`: Bitch Pups, 6 up to 9 months, upto 12%" Entries: 7 | places=0/6 | Bitch Pups, 9 up to 12 months, upto 12," Entries: 6
