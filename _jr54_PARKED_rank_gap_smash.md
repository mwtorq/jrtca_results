# JR-54 park notes: place-rank gaps + Agility/Racing smash

## Detector widen (FAIL always)

- `place_rank_gap`: ascending holes inside a class (e.g. 3rd then 5th)
- Peer regexes: `3rd_then_5th_no_4`, `2nd_then_4th_no_3`, `1st_then_3rd_no_2`
- `agility_racing_smash`: Agility into GTG Champion / Racing / Flat / Steeple; empty GTG Champ into Racing; page-top orphan place into Racing/Flat or into GTG Champ after Agility

## Inventory

See `_jr54_rank_gap_smash_inventory.md` / `.json` (99 hqmax scanned; 83 files with hits).

## Demotions

Prior B6b PASS vols that now FAIL under these codes: **78**
(`_jr54_demote_counts.json`). Already-FAIL with same codes: 5.

## HQ fixes this pass

- `Document_2026-11-04_124005`: removed page-10 Agility column-bleed orphans above Agility II; kept page-11 `6th: Highline Patch` before GTG Champ so smash still FAILs; park file `Document_2026-11-04_124005_PARKED_jr54.txt`. Sibling recovered Dogs 4th Duke / Kit Carson / Buggsy on page 9.

## Honest parks (no surname invention)

Remaining place-rank gaps and Agility/Racing smash hits across 1990-2001 stay FAIL until PDF/sibling OCR recovers missing places. Do not invent ranks or surnames. Odd-page orphans without evidence stay parked as FAIL.
