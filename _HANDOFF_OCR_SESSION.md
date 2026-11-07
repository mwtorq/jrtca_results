# Handoff — JRTCA yearbook HQ OCR (pick up here)

**Full A1–D17 plan + status:** [`_PLAN_A1_D17_HANDOFF.md`](_PLAN_A1_D17_HANDOFF.md)  
**OCR cleanup defect catalog:** [`_OCR_CLEANUP_CATALOG_HANDOFF.md`](_OCR_CLEANUP_CATALOG_HANDOFF.md)

## Repo / branch
- Path: `c:\Users\mw\OneDrive - timberwilde.net\repos\jrtca_results`
- Branch: `ongoing` → PRs into `main`
- Python: prefer `C:\Users\mw\AppData\Local\Python\pythoncore-3.14-64\python.exe` (also `…\Python\bin\python3.exe`)
- Do **not** use repo-wide grep/search (slow). Prefer targeted reads of known modules.
- Do **not** use Grok on Auto.

## Mission (standing plan)
OCR-first HQ baseline into `_ocr_baseline_v2/` only (never overwrite old scan-folder sidecars). Plan steps A1–D17.

**1997–2001 = remediation** (existing trial/cert data is mangled by old OCR; new HQ text must be substantially cleaner → cleanup / update / reinsert). **1990–96 parked** (A4/A5) for laptop load.

**Year-parallel tracks:** when a year finishes A1, advance A2→B6(+later C) for that year via `pipeline_advance_years.py` — do not wait for all of 1999–2001. Manifest: `_pipeline_year_manifest.json`.

## Current OCR run config
- CLI: `ocr_yearbook_baseline_v2.py --force --workers 10 --page-workers 2`
- Tracks (only these): `trackA=[1999, 2001]`, `trackB=[2000]` (~20 tess max)
- **1997–98 A1 DONE** (4 + 7 hqmax); A2 FAIL=0 unlocked; B6 year-harvest done (thin cert section counts — verify harvest patterns on 97+ layout)
- Logs: `_ocr_9701_trackA.log`, `_ocr_9701_trackB.log` (+ `_prev_*` archives)
- Tessdata: `tessdata_yearbook/jrtca_helv|mono.traineddata` + runtime `C:\Users\mw\AppData\Local\jrtca_tessdata`
- On every restart: wipe `*.partial.txt` under `_ocr_baseline_v2`, report **previous-run PPM** (rule `.cursor/rules/ocr-restart-ppm.mdc`)
- Downstream must **not** start a third full tess farm; A3 ≤2 workers when free

## Year pipeline CLIs
| Script | Role |
|--------|------|
| `pipeline_year_status.py` | A1 completeness → `_pipeline_year_manifest.json` |
| `assess_ocr_baseline_a2_gate.py --years YYYY` | Per-year A2 + rollup; FAIL=0 unlocks B6 (WARN OK) |
| `harvest_cert_sections_v2.py --years YYYY` | B6; 1997+ from `yearbook_1990_2001/{year}/` |
| `pipeline_advance_years.py --years …` | A1-complete → A2 → B6; optional `--advance-c10` stage (no SQL) |

```powershell
& "C:\Users\mw\AppData\Local\Python\pythoncore-3.14-64\python.exe" -u pipeline_advance_years.py --years 2000
```

## B6b — cleanup + ingest audit (prefer over re-OCR)
Applies `finalize_results_ocr` (catalog lessons) to HQ text, writes cleaned `*_ocr_hqmax.txt` (backup `*.pre_b6b`), then audits residuals.
```powershell
& "C:\Users\mw\AppData\Local\Python\pythoncore-3.14-64\python.exe" -u assess_ingest_quality_audit.py --years 1997 1998
```
FAIL after cleanup → fix finalize or targeted re-OCR that vol only. WARN (e.g. class_header_gap) OK for apply with eyes-on. Reports: `_b6b_ingest_audit_{year}.md`.

## User paste workflow (IMPORTANT)
- Rule: `.cursor/rules/ocr-paste-subagent.mdc`
- **Parent-inline only** for OCR pastes (subagents were too slow). Surgical edits in `yearbook_ocr.py`, smoke `finalize_results_ocr`, restart OCR if code changed.
- Triage pastes with `_OCR_CLEANUP_CATALOG_HANDOFF.md` cheat sheet.
- Preserve empty classes (`Entries: 0` / empty section headers).
- Do **not** invent truncated surnames.

## Git / PRs (done)
- #44 merged — OCR pipeline + tessdata
- #45 merged — Yearbook Scans / Updated Yearbook Scans / Yearbook Photos / True Grit / jrtcabreeders.com via **Git LFS** (~7.2 GB)
- #46 open (or check): canon CLI promotions + OCR finalize repairs — https://github.com/mwtorq/jrtca_results/pull/46
- Canon renames: e.g. `remount_source_divisions.py`, `fill_from_parse.py`, `yearbook_meta_ingest.py`, `yearbook_extract_photos.py`, `truegrit_ingest.py` (+ `_` shims)

## Core module
`yearbook_ocr.py` — entry points:
- `ocr_pdf_hq` / `ocr_page_best` — structure OCR (header + two-column)
- `finalize_results_ocr` — gutter, smash unsmash, height rehome, class-gap mark, lexical
- `audit_results_ocr_page` — residual defect audit

### Fixes already in finalize (do not regress)
See full catalog `_OCR_CLEANUP_CATALOG_HANDOFF.md`. Highlights:
- Heights: `%2`, bare `2`, `10-1212`, `1212245`, glued place, Champ: expand, etc.
- Place dust: `ond`/`did`/`ist`/`Champ:`→Champion
- Smash: dual-owned-by → cleanest single dog+owner
- Adult racing height Champ/Reserve rehomed under `ADULT RACING CHAMPION & RESERVE`
- Steeple/racing header bleed stripped off owner lines
- Empty Family Class salvage; division/trial bleed noise
- Handler/Child/Junior keep-list; Entries collapse; letter-only EOL crumb; `n—` bleed
- **`[missing class header]`** is **last resort only** — user requires recovering titles from scan/ensemble

## ★ TOP PRIORITY — recover missing class TITLES (not markers)
User rejected placeholders: OCR must **FIND** dropped class titles between place blocks.

Example paste (1998, Bred by Exhibitor Bitch):
```
Bred by Exhibitor Bitch Entries: 2
1st/2nd … (complete for Entries: 2)
1st: Fox Chase Roxie …   ← class title missing above this
… more 1st–6th blocks without titles …
BEST OPEN BITCH & RESERVE
```

### Intended approach (started, not finished)
1. Detect place-rank gaps (already have `_mark_missing_class_headers`).
2. **With the column image** (in `ocr_page_best` / `_ocr_single_column` / `_ocr_leaf_fast` path — finalize has no image):
   - Use `pytesseract.image_to_data` line boxes (see existing `_ocr_columns_from_data`).
   - Locate Y of last place of prior class vs Y of new `1st:`.
   - Crop interstitial band; re-OCR with PSM 6/7 (+ mid/crisp preprocess).
   - If text looks like a class header (`Entries`, Open/Novice/Bred by, height band, Bitches/Dogs, etc.), **insert the recovered title** instead of `[missing class header]`.
3. Also mine ensemble peers in `_reconcile_trial_ocr_candidates` for short class-header lines discarded by scoring.
4. Keep `[missing class header]` only as last-resort audit when image recovery fails.
5. Smoke on the Bred-by-Exhibitor paste + a real 1998 page PDF once titles recover; then `--force` restart tracks.

Key hooks to wire:
- `ocr_page_best` → `_ocr_single_column` / `_ocr_leaf_fast` after text assembled
- `_ocr_columns_from_data` (already has boxes)
- Replace/extend `_mark_missing_class_headers` to accept optional recovered titles map, or do recovery before finalize

## Other open defect themes (from pastes / catalog)
- Column smash (partially fixed; still needs strong OCR peers) — catalog §3
- Truncated owner tails (`owner_tail_trunc`) — crop/ensemble, no hardcodes — §5 O6
- Orphan racing champs under Veteran — §4 C2
- Height glued to place — §1 H6
- Fragment crumb / next-trial bleed — §7 / §4 C5
- Class-title recovery must succeed on image — §4 C1

## Baseline layout
`_ocr_baseline_v2/yearbook_1990_2001/{year}/{vol}/…_ocr_hqmax.txt`  
1990/1991 tracks were killed (0–thin jobs under `Yearbook Scans` for some years; sources also in `Updated Yearbook Scans`).

## After code change
1. Smoke: `finalize_results_ocr` + if image path changed, OCR one known PDF page.
2. Kill `ocr_yearbook_baseline_v2` + tesseract; wipe partials; restart current tracks @ 10; report prior PPM.
3. Commit/PR only when user asks (ongoing→main).

## Do not
- Overwrite non-`_ocr_baseline_v2` OCR sidecars
- Re-enable 4×10 year tracks without user OK (laptop thrash)
- Spawn OCR-paste subagents unless user explicitly asks
- Invent class names or surnames without image/ensemble evidence
- Block year-parallel B6/C on unfinished sibling years when A2 FAIL=0
