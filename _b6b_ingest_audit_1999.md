# B6b cleanup + ingest audit — 1999

Catalog: `_OCR_CLEANUP_CATALOG_HANDOFF.md`
Volumes: 6  cleaned=1  PASS=3  WARN=0  FAIL=3
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
| PASS | False | 0 | 0 | — | `1999 Vol I, pt 1_ocr_hqmax.txt` |
| FAIL | False | 1 | 0 | C6×1 | `1999 Vol I, pt 2_ocr_hqmax.txt` |
| PASS | False | 0 | 0 | — | `1999 Vol II, pt 1_ocr_hqmax.txt` |
| PASS | False | 0 | 0 | — | `1999 Vol II, pt 2_ocr_hqmax.txt` |
| FAIL | False | 2 | 0 | C6/O1×1,C6×1 | `1999 Vol III, pt 1_ocr_hqmax.txt` |
| FAIL | True | 5 | 0 | ?/4th_then_6th_no_5×3,C6×2 | `1999 Vol III, pt 2_ocr_hqmax.txt` |

## Sample residual hits (after cleanup)

### `1999 Vol I, pt 2_ocr_hqmax.txt` (FAIL)
- `C6` / `orphan_entry_count`: 3

### `1999 Vol III, pt 1_ocr_hqmax.txt` (FAIL)
- `C6/O1` / `bare_entries`: Entries:
- `C6` / `orphan_entry_count`: 0

### `1999 Vol III, pt 2_ocr_hqmax.txt` (FAIL)
- `?` / `4th_then_6th_no_5`: 4th: Wild Goose Maryland, owned by Darlene McCutcheon
6th: Stone River Frenzy, owned by Carrie LaCombe
- `?` / `4th_then_6th_no_5`: 4th: Munchie, owned by Barry & Lisa Bigaouette
6th: Terrier-ific Blue Jeans, owned by Donna Pierce
- `?` / `4th_then_6th_no_5`: 4th: Farmstead Holly, handled by Jeffrey Finkernagel
6th: Lona Hope Minnie, owned by Nellie Niewola
- `C6` / `orphan_entry_count`: 10
- `C6` / `orphan_entry_count`: 7
