# B6b cleanup + ingest audit — 1998

Catalog: `_OCR_CLEANUP_CATALOG_HANDOFF.md`
Volumes: 7  cleaned=0  PASS=3  WARN=0  FAIL=4
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
| FAIL | False | 6 | 0 | C6×4,S4/O×1,C6/O1×1 | `1998 Vol I, pt 1_ocr_hqmax.txt` |
| PASS | False | 0 | 0 | — | `1998 Vol I, pt 2_ocr_hqmax.txt` |
| PASS | False | 0 | 0 | — | `1998 Vol I, pt 3_ocr_hqmax.txt` |
| FAIL | False | 3 | 0 | S4/O×2,C6×1 | `1998 Vol II, pt 1_ocr_hqmax.txt` |
| FAIL | False | 4 | 0 | C6×2,O6×1,S4/O×1 | `1998 Vol II, pt 2_ocr_hqmax.txt` |
| FAIL | False | 1 | 0 | C6×1 | `1998 Vol III, pt 1_ocr_hqmax.txt` |
| PASS | False | 0 | 0 | — | `1998 Vol III, pt 2_ocr_hqmax.txt` |

## Sample residual hits (after cleanup)

### `1998 Vol I, pt 1_ocr_hqmax.txt` (FAIL)
- `S4/O` / `missing_owned_by`: 1st: Fair Oaks Texas, Anne de'Treville
- `C6/O1` / `bare_entries`: entries:
- `C6` / `orphan_entry_count`: 5
- `C6` / `orphan_entry_count`: 3
- `C6` / `orphan_entry_count`: 2
- `C6` / `orphan_entry_count`: 4

### `1998 Vol II, pt 1_ocr_hqmax.txt` (FAIL)
- `S4/O` / `missing_owned_by`: 2nd: Peck's Bad Boy JJ, ow
- `S4/O` / `missing_owned_by`: Reserve: Farmstead Damage, D.Ellis/S.Ferber
- `C6` / `orphan_entry_count`: 28

### `1998 Vol II, pt 2_ocr_hqmax.txt` (FAIL)
- `O6` / `owner_tail_trunc`: 1st: B.J. Duty, owned by Ill
- `S4/O` / `missing_owned_by`: 2nd: Fox Run Jackie, Sustell th BIC yk Fiore ty Mary Web
- `C6` / `orphan_entry_count`: 11
- `C6` / `orphan_entry_count`: 10

### `1998 Vol III, pt 1_ocr_hqmax.txt` (FAIL)
- `C6` / `orphan_entry_count`: 4
