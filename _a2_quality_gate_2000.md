# A2 quality gate — 2000

Volumes scored: 5  PASS=0  WARN=5  FAIL=0
B6 unlock (FAIL=0): YES

## Thresholds
- owned_by per 10k chars ≥ 8 (or place ≥ 12)
- audit hits per 10k ≤ 25
- fail-code hits (class_header_gap/smash/heights) < 4 on sample
- no `[missing class header]` placeholders
- bare `Entries:` not excessive vs counted Entries

## Per volume

| Year | Verdict | Owned/10k | Place/10k | Audit/10k | Top codes | File |
|------|---------|-----------|-----------|-----------|-----------|------|
| 2000 | WARN:fail_codes | 149.13 | 136.95 | 0.48 | class_header_gap×8,missing_owned_by×3,orphan_entry_count×3,mangled_by×1,4th_then_6th_no_5×1,owner_tail_trunc×1 | `2000 Vol III pt 1_ocr_hqmax.txt` |
| 2000 | WARN:fail_codes | 150.25 | 138.11 | 0.72 | class_header_gap×8,missing_owned_by×6,mangled_by×1,4th_then_6th_no_5×1,bare_entries×1,orphan_entry_count×1 | `2000 Vol III pt 2_ocr_hqmax.txt` |
| 2000 | WARN:fail_codes | 150.01 | 137.01 | 1.02 | missing_owned_by×8,class_header_gap×8,mangled_by×6,4th_then_6th_no_5×1,owner_tail_trunc×1,orphan_entry_count×1 | `2000 vol 3 pt 1_ocr_hqmax.txt` |
| 2000 | WARN:fail_codes | 145.38 | 132.97 | 0.28 | class_header_gap×8,missing_owned_by×3,owner_tail_trunc×2,mangled_by×1,bare_entries×1 | `2000 Vol II_ocr_hqmax.txt` |
| 2000 | WARN:fail_codes | 147.45 | 134.79 | 0.28 | mangled_by×8,missing_owned_by×8,class_header_gap×8 | `2000 Vol I_ocr_hqmax.txt` |

## Next
- FAIL → A3 targeted fix + `--force` re-OCR that PDF only
- WARN → proceed B6 for this year; spot-check residual codes
- PASS/WARN with FAIL=0 → year-pipelined B6 (do not wait for other years)

CSV: `_a2_quality_gate_2000.csv`
