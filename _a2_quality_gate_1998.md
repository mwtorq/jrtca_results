# A2 quality gate — 1998

Volumes scored: 7  PASS=2  WARN=5  FAIL=0
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
| 1998 | WARN:fail_codes | 154.44 | 143.46 | 1.53 | mangled_by×8,owner_tail_trunc×8,missing_owned_by×8,class_header_gap×8,orphan_entry_count×3 | `1998 Vol III, pt 1_ocr_hqmax.txt` |
| 1998 | WARN:fail_codes | 151.04 | 136.53 | 1.33 | mangled_by×8,missing_owned_by×8,class_header_gap×8,owner_tail_trunc×4,height_pct×1 | `1998 Vol III, pt 2_ocr_hqmax.txt` |
| 1998 | WARN:fail_codes | 154.37 | 142.94 | 1.53 | mangled_by×8,missing_owned_by×8,class_header_gap×8,owner_tail_trunc×4,orphan_entry_count×1 | `1998 Vol II, pt 1_ocr_hqmax.txt` |
| 1998 | WARN:fail_codes | 148.58 | 135.16 | 2.12 | mangled_by×8,owner_tail_trunc×8,missing_owned_by×8,class_header_gap×8,orphan_entry_count×3,4th_then_6th_no_5×1 | `1998 Vol II, pt 2_ocr_hqmax.txt` |
| 1998 | WARN:fail_codes | 153.56 | 141.75 | 1.0 | mangled_by×8,missing_owned_by×8,class_header_gap×8,owner_tail_trunc×5,orphan_entry_count×4,bare_entries×1 | `1998 Vol I, pt 1_ocr_hqmax.txt` |
| 1998 | PASS | 134.71 | 129.87 | 0.81 | owner_tail_trunc×1 | `1998 Vol I, pt 2_ocr_hqmax.txt` |
| 1998 | PASS | 135.58 | 131.06 | 8.54 | orphan_entry_count×8,owner_tail_trunc×5,class_header_gap×3,missing_owned_by×1 | `1998 Vol I, pt 3_ocr_hqmax.txt` |

## Next
- FAIL → A3 targeted fix + `--force` re-OCR that PDF only
- WARN → proceed B6 for this year; spot-check residual codes
- PASS/WARN with FAIL=0 → year-pipelined B6 (do not wait for other years)

CSV: `_a2_quality_gate_1998.csv`
