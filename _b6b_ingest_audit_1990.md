# B6b cleanup + ingest audit — 1990

Catalog: `_OCR_CLEANUP_CATALOG_HANDOFF.md`
Volumes: 5  cleaned=2  PASS=3  WARN=0  FAIL=2
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
| PASS | False | 0 | 0 | — | `scan_ocr_hqmax.txt` |
| FAIL | True | 8 | 0 | C1/C6×8 | `Document_2026-11-03_192526_ocr_hqmax.txt` |
| FAIL | False | 39 | 0 | C1/C6×26,C1×13 | `Document_2026-11-03_200401_ocr_hqmax.txt` |
| PASS | False | 0 | 0 | — | `Document_2026-11-03_201432_ocr_hqmax.txt` |
| PASS | True | 0 | 0 | — | `Document_2026-11-03_201547_ocr_hqmax.txt` |

## Sample residual hits (after cleanup)

### `Document_2026-11-03_192526_ocr_hqmax.txt` (FAIL)
- `C1/C6` / `incomplete_entries`: Bitch Pups, 6 up to 12 months, 12-1/2--15" Entries: 3 | places=0/3 | Dogs, 1 yr & over, 10--12-1/2" Entries: 6
- `C1/C6` / `incomplete_entries`: 5th: Dogs, Blencathra 1 yr & over, Bracken of Goulden by Ridge, owned by Nancy P | places=0/6 | Best Dog & Reserve
- `C1/C6` / `incomplete_entries`: Dogs, 1yr & over, 12-1 12-1 5", smooth Entries: 10 | places=0/6 | Dogs, 1 yr & over, 10--12-1/2", br/r                        
- `C1/C6` / `incomplete_entries`: Novice (Puppies)                                                          Entrie | places=0/6 | Novice (Adults)                                             
- `C1/C6` / `incomplete_entries`: fp ye id Ky: Fir ade hry |                  boy Pups, 6 up to 12 months          | places=0/6 | py © 4    Wel ANE     I we if             :         Dogs, 1 
- `C1/C6` / `incomplete_entries`: rane YT ey oo.                    Dogs, 1 yr & over, 12:1/2-15" Entries: 6 | places=0/6 | I'L Fut FTN Ma a Bitches, 1 yr & over, 10--12-1/2" Entries: 
- `C1/C6` / `incomplete_entries`: AS 4 io 3 { TT                           OPEN (Puppies)                          | places=0/6 | F                               A           ue              
- `C1/C6` / `incomplete_entries`: Dog Pups, 6 up to 9 months                                                       | places=0/6 | Go-to-Ground CHAMPIONS & RESERVES (Continued)

### `Document_2026-11-03_200401_ocr_hqmax.txt` (FAIL)
- `C1/C6` / `incomplete_entries`: OPEN (Adults)                                                                    | places=0/6 | 1st: Raincliff's Smooth Gerald, owned by George Ridler
- `C1/C6` / `incomplete_entries`: Entries: 18 | places=0/6 | Entries: 11
- `C1/C6` / `incomplete_entries`: Entries: 11 | places=0/6 | Entries: 2
- `C1/C6` / `incomplete_entries`: Entries: 4 | places=0/4 | Dog Pups, 9 up to 12 months
- `C1/C6` / `incomplete_entries`: Entries: 7 | places=0/6 | Bitch Pups, 9 up to 12 months
- `C1/C6` / `incomplete_entries`: Pups, 4 up to 6 months – Entries: 11 | places=0/6 | Child Handler
- `C1/C6` / `incomplete_entries`: PUPPY Conformation Champion & RESERVE – Entries: 3 | places=0/3 | CHAMPION: COTSWOLD REMINGTON, owned by KELLEEN ROSSMAN
- `C1/C6` / `incomplete_entries`: JRTCA Working Terrier Bitch                                                      | places=0/5 | Open Class
- `C1/C6` / `incomplete_entries`: Batzer – Entries: 13, owned by Malinda Kraus | places=0/6 | Judges:        Linda Cowasjes, Conformation; Rustom Cowasjee
- `C1/C6` / `incomplete_entries`: Dogs, 1 yr & over, 12-1/2-15" Entries: 10 | places=0/6 | DIVISION A, CONFORMATION
- `C1/C6` / `incomplete_entries`: Entries: 11 | places=0/6 | Entries: 5
- `C1/C6` / `incomplete_entries`: Entries: 5 | places=0/5 | Junior Handler award
