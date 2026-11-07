# A2 quality gate — 1997

Volumes scored: 4  PASS=0  WARN=4  FAIL=0
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
| 1997 | WARN:fail_codes | 144.84 | 137.02 | 1.19 | mangled_by×8,owner_tail_trunc×8,missing_owned_by×8,class_header_gap×8,orphan_entry_count×6,dup_place×1 | `1997 Vol II pt 1_ocr_hqmax.txt` |
| 1997 | WARN:fail_codes | 151.51 | 141.8 | 1.15 | mangled_by×8,owner_tail_trunc×8,missing_owned_by×8,class_header_gap×8,orphan_entry_count×2 | `1997 Vol II pt 2_ocr_hqmax.txt` |
| 1997 | WARN:fail_codes | 149.15 | 141.46 | 0.92 | mangled_by×8,owner_tail_trunc×8,missing_owned_by×8,class_header_gap×8,orphan_entry_count×2 | `1997 Vol I pt 1_ocr_hqmax.txt` |
| 1997 | WARN:fail_codes | 149.33 | 140.73 | 1.62 | mangled_by×8,owner_tail_trunc×8,missing_owned_by×8,class_header_gap×8,dup_place×1,orphan_entry_count×1 | `1997 Vol I pt 2_ocr_hqmax.txt` |

## Next
- FAIL → A3 targeted fix + `--force` re-OCR that PDF only
- WARN → proceed B6 for this year; spot-check residual codes
- PASS/WARN with FAIL=0 → year-pipelined B6 (do not wait for other years)

CSV: `_a2_quality_gate_1997.csv`
