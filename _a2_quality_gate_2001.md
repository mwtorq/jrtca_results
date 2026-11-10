# A2 quality gate — 2001

Volumes scored: 14  PASS=0  WARN=14  FAIL=0
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
| 2001 | WARN:fail_codes | 148.8 | 137.77 | 0.44 | class_header_gap×8,missing_owned_by×5,orphan_entry_count×2 | `2001 Vol III pt 1_ocr_hqmax.txt` |
| 2001 | WARN:fail_codes | 148.62 | 133.19 | 0.44 | class_header_gap×8,missing_owned_by×4,orphan_entry_count×2,4th_then_6th_no_5×1,owner_tail_trunc×1 | `2001 Vol III pt 2_ocr_hqmax.txt` |
| 2001 | WARN:fail_codes+bare_entries | 148.49 | 132.23 | 2.05 | class_header_gap×8,missing_owned_by×2,orphan_entry_count×2 | `2001 MWJRTC II Wheatland I & II_ocr_hqmax.txt` |
| 2001 | WARN:fail_codes+bare_entries | 143.84 | 125.86 | 3.93 | class_header_gap×4,owner_tail_trunc×3 | `2001 OH-PA II_ocr_hqmax.txt` |
| 2001 | WARN:fail_codes+bare_entries | 142.81 | 133.56 | 3.62 | class_header_gap×6,missing_owned_by×3 | `2001 PNWJRTN_ocr_hqmax.txt` |
| 2001 | WARN:fail_codes | 146.33 | 134.7 | 2.07 | class_header_gap×8,missing_owned_by×3,height_pct×1,owner_tail_trunc×1 | `2001 Paumanok Farmstead Dutchess County_ocr_hqmax.txt` |
| 2001 | WARN:fail_codes | 151.18 | 136.42 | 3.14 | class_header_gap×8,orphan_entry_count×3,bare_entries×2 | `2001 Summer Celebration_ocr_hqmax.txt` |
| 2001 | WARN:fail_codes | 148.9 | 135.22 | 0.48 | class_header_gap×8,orphan_entry_count×4,owner_tail_trunc×3,missing_owned_by×3 | `2001 Vol II pt 1_ocr_hqmax.txt` |
| 2001 | WARN:fail_codes | 144.37 | 131.91 | 0.33 | class_header_gap×8,orphan_entry_count×3 | `2001 Vol II pt 2_ocr_hqmax.txt` |
| 2001 | WARN:fail_codes+bare_entries | 139.92 | 132.37 | 3.33 | class_header_gap×8,missing_owned_by×3,owner_tail_trunc×2,mangled_by×1,4th_then_6th_no_5×1 | `2001 Yankee_ocr_hqmax.txt` |
| 2001 | WARN:fail_codes | 152.08 | 142.52 | 6.23 | class_header_gap×8,orphan_entry_count×5,missing_owned_by×2 | `2001 Coal Tree Farm_ocr_hqmax.txt` |
| 2001 | WARN:fail_codes | 148.22 | 131.57 | 3.33 | class_header_gap×8 | `2001 South Coast_ocr_hqmax.txt` |
| 2001 | WARN:fail_codes | 151.59 | 141.05 | 2.27 | class_header_gap×8,orphan_entry_count×2,missing_owned_by×1 | `2001 Troon Quarry_ocr_hqmax.txt` |
| 2001 | WARN:fail_codes | 147.76 | 133.17 | 0.37 | orphan_entry_count×8,class_header_gap×8,missing_owned_by×6,cutoff_racing×1,bare_entries×1 | `2001 Vol I_ocr_hqmax.txt` |

## Next
- FAIL → A3 targeted fix + `--force` re-OCR that PDF only
- WARN → proceed B6 for this year; spot-check residual codes
- PASS/WARN with FAIL=0 → year-pipelined B6 (do not wait for other years)

CSV: `_a2_quality_gate_2001.csv`
