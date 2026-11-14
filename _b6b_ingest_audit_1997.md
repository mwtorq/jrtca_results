# B6b cleanup + ingest audit — 1997

Catalog: `_OCR_CLEANUP_CATALOG_HANDOFF.md`
Volumes: 4  cleaned=4  PASS=3  WARN=0  FAIL=1
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
| FAIL | True | 22 | 0 | C7×9,C1/C6×8,C1×2,H8×1,?/4th_then_2nd×1,S4/O×1 | `1997 Vol I pt 1_ocr_hqmax.txt` |
| PASS | True | 0 | 0 | — | `1997 Vol I pt 2_ocr_hqmax.txt` |
| PASS | True | 0 | 0 | — | `1997 Vol II pt 1_ocr_hqmax.txt` |
| PASS | True | 0 | 0 | — | `1997 Vol II pt 2_ocr_hqmax.txt` |

## Sample residual hits (after cleanup)

### `1997 Vol I pt 1_ocr_hqmax.txt` (FAIL)
- `H8` / `champ_abbrev`: JRTCA WORKING TERRIER CONFORMATION CHAMPION & RESER\
- `?` / `4th_then_2nd`: 4th: Gunpowder Oaks Josie, owned by Bonnie Hurley
2nd: Thistledown Cheyenne, owned by Chuck & Diana Hufnagel
- `S4/O` / `missing_owned_by`: 1st: Fox Shadow Chiclet, own=d by Patricia Cranmer
- `C1` / `class_header_gap`: 1st: Ruff N' Tumble Rocket, owned by Don Tait
- `C1` / `class_header_gap`: 1st: R.A. Legacy, owned by Pam Williams
- `C1/C6` / `incomplete_entries`: Child Handler Entries: 9 | places=0/6 | Entries: 9
- `C1/C6` / `incomplete_entries`: Novice Puppies Entries: 23 hn ST j Bt GW | places=0/6 | ADULT RACING CHAMPION & RESERVE
- `C1/C6` / `incomplete_entries`: ADULTS – Entries: 10 | places=0/6 | 10-12 1/2" Champion: R.A. Piker, owned by George
- `C1/C6` / `incomplete_entries`: Family Class                                           Entries: 9 | places=0/6 | Stud Dog & Get
- `C1/C6` / `incomplete_entries`: Dogs, 1 yr & over, 10-12 1/2" Entries: 7 | places=0/6 | ADULT RACING CHAMPION & RESERVE
- `C1/C6` / `incomplete_entries`: Bitch Pups, 6 up to 9 months, under 12 1/2" Entries: 5 | places=0/5 | ADULT RACING CHAMPION & RESERVE
- `C1/C6` / `incomplete_entries`: Bitch Pups, 9 up to 12 months, r/br             Entries: 10 | places=0/6 | itLh T Wpo, 4 Up WU IL HIV, TTT entries: iv 1st: Farmliff Ho
