# A2 quality gate — 1999

Volumes scored: 6  PASS=0  WARN=6  FAIL=0
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
| 1999 | WARN:fail_codes | 148.0 | 132.68 | 0.59 | class_header_gap×8,owner_tail_trunc×3,place_ond×2,missing_owned_by×2 | `1999 Vol III, pt 1_ocr_hqmax.txt` |
| 1999 | WARN:fail_codes | 147.86 | 134.31 | 0.96 | mangled_by×8,missing_owned_by×8,class_header_gap×8,place_ond×2,owner_tail_trunc×2,orphan_entry_count×1 | `1999 Vol III, pt 2_ocr_hqmax.txt` |
| 1999 | WARN:fail_codes | 149.34 | 133.93 | 1.46 | mangled_by×8,missing_owned_by×8,class_header_gap×8,cutoff_racing×1 | `1999 Vol II, pt 1_ocr_hqmax.txt` |
| 1999 | WARN:fail_codes | 149.94 | 136.2 | 1.6 | class_header_gap×8,mangled_by×7,missing_owned_by×7,owner_tail_trunc×2,orphan_entry_count×1 | `1999 Vol II, pt 2_ocr_hqmax.txt` |
| 1999 | WARN:fail_codes | 152.29 | 138.6 | 1.18 | mangled_by×8,missing_owned_by×8,class_header_gap×8,orphan_entry_count×2 | `1999 Vol I, pt 1_ocr_hqmax.txt` |
| 1999 | WARN:fail_codes | 147.88 | 135.3 | 1.39 | mangled_by×8,missing_owned_by×8,class_header_gap×8,owner_tail_trunc×2,orphan_entry_count×2,place_ond×1 | `1999 Vol I, pt 2_ocr_hqmax.txt` |

## Next
- FAIL → A3 targeted fix + `--force` re-OCR that PDF only
- WARN → proceed B6 for this year; spot-check residual codes
- PASS/WARN with FAIL=0 → year-pipelined B6 (do not wait for other years)

CSV: `_a2_quality_gate_1999.csv`
