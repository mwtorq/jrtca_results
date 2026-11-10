# A2 quality gate — OCR baseline v2 (rollup)

Years: 1997, 1998, 1999, 2000, 2001
Volumes scored: 36  PASS=2  WARN=34  FAIL=0

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
| 1999 | WARN:fail_codes | 148.0 | 132.68 | 0.59 | class_header_gap×8,owner_tail_trunc×3,place_ond×2,missing_owned_by×2 | `1999 Vol III, pt 1_ocr_hqmax.txt` |
| 1999 | WARN:fail_codes | 147.86 | 134.31 | 0.96 | mangled_by×8,missing_owned_by×8,class_header_gap×8,place_ond×2,owner_tail_trunc×2,orphan_entry_count×1 | `1999 Vol III, pt 2_ocr_hqmax.txt` |
| 1999 | WARN:fail_codes | 149.34 | 133.93 | 1.46 | mangled_by×8,missing_owned_by×8,class_header_gap×8,cutoff_racing×1 | `1999 Vol II, pt 1_ocr_hqmax.txt` |
| 1999 | WARN:fail_codes | 149.94 | 136.2 | 1.6 | class_header_gap×8,mangled_by×7,missing_owned_by×7,owner_tail_trunc×2,orphan_entry_count×1 | `1999 Vol II, pt 2_ocr_hqmax.txt` |
| 1999 | WARN:fail_codes | 152.29 | 138.6 | 1.18 | mangled_by×8,missing_owned_by×8,class_header_gap×8,orphan_entry_count×2 | `1999 Vol I, pt 1_ocr_hqmax.txt` |
| 1999 | WARN:fail_codes | 147.88 | 135.3 | 1.39 | mangled_by×8,missing_owned_by×8,class_header_gap×8,owner_tail_trunc×2,orphan_entry_count×2,place_ond×1 | `1999 Vol I, pt 2_ocr_hqmax.txt` |
| 2000 | WARN:fail_codes | 149.13 | 136.95 | 0.48 | class_header_gap×8,missing_owned_by×3,orphan_entry_count×3,mangled_by×1,4th_then_6th_no_5×1,owner_tail_trunc×1 | `2000 Vol III pt 1_ocr_hqmax.txt` |
| 2000 | WARN:fail_codes | 150.25 | 138.11 | 0.72 | class_header_gap×8,missing_owned_by×6,mangled_by×1,4th_then_6th_no_5×1,bare_entries×1,orphan_entry_count×1 | `2000 Vol III pt 2_ocr_hqmax.txt` |
| 2000 | WARN:fail_codes | 150.01 | 137.01 | 1.02 | missing_owned_by×8,class_header_gap×8,mangled_by×6,4th_then_6th_no_5×1,owner_tail_trunc×1,orphan_entry_count×1 | `2000 vol 3 pt 1_ocr_hqmax.txt` |
| 2000 | WARN:fail_codes | 145.38 | 132.97 | 0.28 | class_header_gap×8,missing_owned_by×3,owner_tail_trunc×2,mangled_by×1,bare_entries×1 | `2000 Vol II_ocr_hqmax.txt` |
| 2000 | WARN:fail_codes | 147.45 | 134.79 | 0.28 | mangled_by×8,missing_owned_by×8,class_header_gap×8 | `2000 Vol I_ocr_hqmax.txt` |
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

CSV: `_a2_quality_gate.csv`
