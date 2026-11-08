# A2 quality gate — OCR baseline v2 (rollup)

Years: 1997, 1998
Volumes scored: 11  PASS=2  WARN=9  FAIL=0

Per-year details: `_a2_quality_gate_{year}.md`

## Unlock doctrine (1997–2001 remediation)
- FAIL=0 for a year → unlock B6 for that year (WARN OK).
- Do not wait for all of 1999–2001 before advancing completed years.

## Per volume

| Year | Verdict | Owned/10k | Place/10k | Audit/10k | Top codes | File |
|------|---------|-----------|-----------|-----------|-----------|------|
| 1997 | WARN:fail_codes | 144.84 | 137.02 | 1.19 | mangled_by×8,owner_tail_trunc×8,missing_owned_by×8,class_header_gap×8,orphan_entry_count×6,dup_place×1 | `1997 Vol II pt 1_ocr_hqmax.txt` |
| 1997 | WARN:fail_codes | 151.51 | 141.8 | 1.15 | mangled_by×8,owner_tail_trunc×8,missing_owned_by×8,class_header_gap×8,orphan_entry_count×2 | `1997 Vol II pt 2_ocr_hqmax.txt` |
| 1997 | WARN:fail_codes | 149.15 | 141.46 | 0.92 | mangled_by×8,owner_tail_trunc×8,missing_owned_by×8,class_header_gap×8,orphan_entry_count×2 | `1997 Vol I pt 1_ocr_hqmax.txt` |
| 1997 | WARN:fail_codes | 149.33 | 140.73 | 1.62 | mangled_by×8,owner_tail_trunc×8,missing_owned_by×8,class_header_gap×8,dup_place×1,orphan_entry_count×1 | `1997 Vol I pt 2_ocr_hqmax.txt` |
| 1998 | WARN:fail_codes | 154.44 | 143.46 | 1.53 | mangled_by×8,owner_tail_trunc×8,missing_owned_by×8,class_header_gap×8,orphan_entry_count×3 | `1998 Vol III, pt 1_ocr_hqmax.txt` |
| 1998 | WARN:fail_codes | 151.04 | 136.53 | 1.33 | mangled_by×8,missing_owned_by×8,class_header_gap×8,owner_tail_trunc×4,height_pct×1 | `1998 Vol III, pt 2_ocr_hqmax.txt` |
| 1998 | WARN:fail_codes | 154.37 | 142.94 | 1.53 | mangled_by×8,missing_owned_by×8,class_header_gap×8,owner_tail_trunc×4,orphan_entry_count×1 | `1998 Vol II, pt 1_ocr_hqmax.txt` |
| 1998 | WARN:fail_codes | 148.58 | 135.16 | 2.12 | mangled_by×8,owner_tail_trunc×8,missing_owned_by×8,class_header_gap×8,orphan_entry_count×3,4th_then_6th_no_5×1 | `1998 Vol II, pt 2_ocr_hqmax.txt` |
| 1998 | WARN:fail_codes | 153.56 | 141.75 | 1.0 | mangled_by×8,missing_owned_by×8,class_header_gap×8,owner_tail_trunc×5,orphan_entry_count×4,bare_entries×1 | `1998 Vol I, pt 1_ocr_hqmax.txt` |
| 1998 | PASS | 134.71 | 129.87 | 0.81 | owner_tail_trunc×1 | `1998 Vol I, pt 2_ocr_hqmax.txt` |
| 1998 | PASS | 135.58 | 131.06 | 8.54 | orphan_entry_count×8,owner_tail_trunc×5,class_header_gap×3,missing_owned_by×1 | `1998 Vol I, pt 3_ocr_hqmax.txt` |

CSV: `_a2_quality_gate.csv`
