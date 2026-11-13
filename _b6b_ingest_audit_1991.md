# B6b cleanup + ingest audit — 1991

Catalog: `_OCR_CLEANUP_CATALOG_HANDOFF.md`
Volumes: 4  cleaned=1  PASS=1  WARN=0  FAIL=3
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
| FAIL | False | 1 | 0 | C1/C6×1 | `Document_2026-11-03_201758_ocr_hqmax.txt` |
| FAIL | False | 3 | 0 | C1/C6×2,C1×1 | `Document_2026-11-03_205014_ocr_hqmax.txt` |
| FAIL | True | 3 | 0 | C1×2,C1/C6×1 | `Document_2026-11-03_210248_ocr_hqmax.txt` |
| PASS | False | 0 | 0 | — | `Document_2026-11-03_211454_ocr_hqmax.txt` |

## Sample residual hits (after cleanup)

### `Document_2026-11-03_201758_ocr_hqmax.txt` (FAIL)
- `C1/C6` / `incomplete_entries`: Dogs, 1 yr & over, 10-12-1/2" Entries: 10 | places=0/6 | Judges:         Marcy Ortolano, Conformation; Richard Ortola

### `Document_2026-11-03_205014_ocr_hqmax.txt` (FAIL)
- `C1/C6` / `incomplete_entries`: Novice (Puppies)                                                                 | places=1/6 | Novice (Adults)                                             
- `C1/C6` / `incomplete_entries`: Dog Pups, 6 up to 12 months, 12-1/2--15" Entries: 3 | places=0/3 | Bitch Pups, 6 up to 12 months, 10--12-1/2" Entries: 4
- `C1` / `midclass_page_dropout`: Dogs, 1 yr & over, 12-1/2--15" Entries: 16 | after page got 1th expected 4 | 1st: Raheen Lilac Magpie, owned by Jaci Jenson

### `Document_2026-11-03_210248_ocr_hqmax.txt` (FAIL)
- `C1/C6` / `incomplete_entries`: Novice (Puppies)                                                                 | places=1/6 | Novice (Adults)                                             
- `C1` / `midclass_page_dropout`: American Bred                                                                    | after page got 4th expected 7 | 4th: Raven, owned by Mia DiBenedetto
- `C1` / `midclass_page_dropout`: Dogs, 1 yr & over, 10--12-1/2", br'r                                             | after page got 5th expected 7 | 5th: The Hollow Mr. Belvedere, owned by Lauri
