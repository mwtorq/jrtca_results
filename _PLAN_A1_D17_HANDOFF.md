# JRTCA Yearbook / Results Plan — Steps A1–D17 (handoff)

**Repo:** `c:\Users\mw\OneDrive - timberwilde.net\repos\jrtca_results`  
**Branch:** `ongoing` → PRs to `main`  
**Python:** `C:\Users\mw\AppData\Local\Python\bin\python3.exe`  
**Companion OCR ops notes:** `_HANDOFF_OCR_SESSION.md`  
**Cleanup defect catalog:** `_OCR_CLEANUP_CATALOG_HANDOFF.md`  
**Date of this handoff:** 2026-11-07  

## Goal (end state)
A trustworthy **PRIMARY** results path for 1984–2001 (and onward) built from HQ OCR baselines, with certificates, trial rows, dog links, and photos consistent; older/noisy OCR kept as **REFERENCE** only (see D17).

### 1997–2001 vs 1990–1996
- **1997–2001:** remediation — data already in DB/paths but **mangled by old OCR**. New `_ocr_baseline_v2` HQ text should be **substantially cleaner**; cleanup / update / reinsert year-by-year.
- **1990–1996 / A4–A5:** parked separately (not part of the live 97–01 parallel remediation).

### Year-parallel pipeline
Unit of progress = **year**. Orchestrator: `pipeline_advance_years.py` + manifest `_pipeline_year_manifest.json`.
A1 year complete → A2 (per-year `_a2_quality_gate_{year}.*`) → if **FAIL=0** (WARN OK) → B6 `--years` → **ingest quality audit** (catalog IDs) → optional C10 stage (no SQL until explicit apply).
Do **not** wait for all of 1999–2001 before advancing completed years. Tess: A1 keeps 2×10 workers; downstream is light; A3 ≤2 workers when free.

**Snapshot 2026-11-07 ~11:44:** 1997 `a1/a2/b6/b6b=done` (B6b WARN, unlocked); 1998 B6b **FAIL** on 1 vol (apply blocked) — see `_b6b_ingest_audit_1998.md`; A1 still running 1999+2001 / 2000.

## Operating rules (carry into next session)
- Write HQ OCR **only** under `_ocr_baseline_v2/` — never overwrite legacy scan-folder sidecars.
- No repo-wide grep/search (slow). Prefer known modules / targeted reads.
- OCR paste defects: **parent-inline** fixes in `yearbook_ocr.py` (no paste subagents unless asked). Smoke `finalize_results_ocr`; if code changed, restart OCR and report prior PPM (`.cursor/rules/ocr-restart-ppm.mdc`).
- Preserve empty classes; do not invent truncated surnames or missing class titles without image/ensemble evidence.
- **Top OCR debt:** recover dropped **class titles** from page-image interstitial re-OCR (not `[missing class header]` placeholders). See `_HANDOFF_OCR_SESSION.md`.
- Laptop load: default **two tracks** (currently 1999+2001 / 2000 @ 10 workers). Do not re-enable 4×10 without user OK.
- Commit/PR only when asked; prefer `ongoing` → `main`.

## Status legend
| Status | Meaning |
|--------|---------|
| DONE | Complete enough to leave alone unless regressions |
| IN PROGRESS | Actively underway / partial |
| BLOCKED | Waiting on prior step or known defect |
| PENDING | Not started |

---

## Phase A — HQ OCR baseline

### A1 — Force HQ re-OCR 1997–2001 into `_ocr_baseline_v2`
**Status:** IN PROGRESS  
**Intent:** Re-OCR yearbook PDFs for 1997–2001 with structure OCR (`ocr_pdf_hq` / `ocr_page_best`), font langs `jrtca_helv` / `jrtca_mono`, finalize+audit, into `_ocr_baseline_v2/yearbook_1990_2001/{year}/…`.  
**How:** `ocr_yearbook_baseline_v2.py --force --workers 10 --page-workers 2`  
**Tracks now:** `trackA=[1999, 2001]`, `trackB=[2000]` (1997–98 complete: 4 + 7 hqmax).  
**Snapshot:** 1997=4, 1998=7 hqmax DONE; 1999–2001 OCR running.  
**Exit:** All 1997–2001 volume PDFs have fresh `*_ocr_hqmax.txt` (+ `.meta.txt`); paste-driven defects largely cleaned on re-run.

### A2 — Quality gate on baseline samples
**Status:** IN PROGRESS (year-pipelined)  
**Intent:** Sample pages/trials from baseline v2; score place lines, heights, smash, class headers, owned-by; compare to known-good pastes / DB.  
**How:** `assess_ocr_baseline_a2_gate.py --years YYYY` → `_a2_quality_gate_{year}.md/.csv` + rollup `_a2_quality_gate.md`. Or `pipeline_advance_years.py --years …`.  
**Unlock:** FAIL=0 → B6 for that year (WARN OK). Re-gate each year when its A1 completes — do not block on other years.  
**Exit:** Written gate checklist + pass/fail per year or volume; list of residual defect classes.

### A3 — Targeted fix + re-OCR bad volumes if gate fails
**Status:** PENDING  
**Intent:** Fix `yearbook_ocr.py` (or crop/PSM) for gate failures; `--force` re-OCR only failing PDFs.  
**Exit:** Failed vols re-pass A2 samples.

### A4 — HQ baseline 1990–96 yearbook volumes
**Status:** PENDING (parked — laptop thrash at 4 tracks)  
**Intent:** Same pipeline as A1 for 1990–1996. Sources: `Yearbook Scans` + `Updated Yearbook Scans`.  
**Note:** Prior trackC/D (1990–96) killed; trackD had 0 jobs for some years — verify folder naming under `Yearbook Scans`.  
**Exit:** `_ocr_baseline_v2/yearbook_1990_2001/{1990–96}/…` populated.

### A5 — HQ OCR 1984–90 non-yearbook (early packs)
**Status:** PENDING  
**Intent:** OCR early non-yearbook / special packs (`EARLY` folders in `yearbook_ocr.py`, Updated Yearbook Scans 1984–89, etc.) into baseline v2 layout.  
**Exit:** Baseline coverage for 1984–1990 sources used by TrialList.

---

## Phase B — Certificates (NHC / TrialCertificates)

### B6 — Re-harvest cert sections from baseline v2
**Status:** IN PROGRESS (year-pipelined; **1997–98 B6 done** in manifest — section counts thin, verify 97+ header patterns)  
**Intent:** Run cert harvest against `_ocr_baseline_v2` (canon: `harvest_cert_sections_v2.py --years …`), not old sidecars. 1997+ reads HQ under `yearbook_1990_2001/{year}/`.  
**Exit:** Harvested cert section corpus for available years; advance more years as A1+A2 complete.

### B6b / ingest gate — Catalog cleanup + audit (required on ANY ingest)
**Status:** DONE for **1997–98** (FAIL=0, WARN eyes-on / C1 residual plateau; unlocked + C10 staged). Other years follow A1 completion.  
**Intent:** Apply finalize/catalog lessons to stored HQ text (backup `*.pre_b6b`), then audit residuals. Re-OCR only if FAIL remains after cleanup. WARN OK for image-recovery debt (class titles).  
**How:** `assess_ingest_quality_audit.py --years YYYY` → writes cleaned `*_ocr_hqmax.txt` + `_b6b_ingest_audit_{year}.*`; via `pipeline_advance_years.py` after B6. Taxonomy: `_OCR_CLEANUP_CATALOG_HANDOFF.md`.  
**Exit:** Cleaned baseline + report + manifest `b6b_unlocked`; `--apply` blocked unless FAIL=0.

### B7 — Tighten NHC + TrialCertificates parsers
**Status:** IN PROGRESS  
**Intent:** Harden parsers for height garble, truncated cert sizes, name OCR; align with finalize vocabulary + catalog §1/§5.  
**How:** `harvest_cert_sections_v2.py` (stricter heads — no Championship/Bronze-Class false hits) + `parse_cert_sections.py --spot-check`. Note: **1997–98 HQ baseline currently has no NHC list pages** (search zero); spot-check on 1990–96 harvest.  
**Exit:** Parser tests / spot samples clean on harvested text.

### B8 — Ingest NHC / TrialCertificates with Dog links
**Status:** PENDING (depends B6b audit gate)  
**Intent:** `yearbook_certs_ingest.py` (and related) into SQL with Dog FK / match — **only after** catalog audit on the harvest corpus.  
**Exit:** Certs linked; orphan rate measured.

### B9 — Spot-check certs; fix orphans
**Status:** PENDING  
**Intent:** Manual/SQL spot-check; rematch orphans; document residual.  
**Exit:** Orphan list closed or accepted with notes.

---

## Phase C — Trial results rebuild / rematch

### C10 — Normalize baseline to `trial_results/`
**Status:** PARTIAL — **1997–98 staged** under `_ocr_baseline_v2/trial_results_norm/{year}/` via `pipeline_advance_years.py --advance-c10`.  
**Intent:** Export/normalize baseline OCR into a stable `trial_results/` (or agreed) tree for parsers.  
**Exit:** Normalized text per trial/year ready for `process_trial` / fill pipeline.

### C11 — Parse + validate sample trials 1990 / 1997 / 2001
**Status:** PENDING  
**Intent:** Parse three anchor years; compare placement counts, champs, racing vs conf.; run **B6b catalog audit** on samples.  
**Exit:** Validation report; no silent smash/missing-class disasters on samples.

### C12 — Full rebuild trial rows from baseline
**Status:** PENDING (year-pipelined remediation for 1997–2001; requires B6b audit before `--apply`)  
**Intent:** Rebuild/update TrialResults from cleaner baseline-normalized text for in-scope years (replace mangled OCR-derived rows).  
**Exit:** Rows rebuilt; counts vs prior documented; audit report attached per year.

### C13 — Rematch `process_trial` vs TrialList 1984–2001
**Status:** PENDING  
**Intent:** Remount/rematch sources to TrialList; canon CLI `remount_source_divisions.py` / `fill_from_parse.py`.  
**Exit:** TrialList coverage matrix; unmatched trials listed.

### C14 — Fill/correct 1984–1996 from baseline
**Status:** PENDING (depends A4/A5 + C12/C13)  
**Intent:** Prefer baseline OCR over weak legacy fills for early years.  
**Exit:** 1984–1996 gaps filled or explicitly waived.

---

## Phase D — Photos + consistency + handoff doctrine

### D15 — Yearbook Photos crop + caption
**Status:** PARTIAL  
**Intent:** Crop/caption pipeline (`yearbook_extract_photos.py`, cleanup/map helpers).  
**Done:** `Yearbook Photos/` exists and was pushed via Git LFS (PR #45).  
**Remaining:** Quality pass on crops/captions; align names with Dog catalog; drop bad folders if any recur.

### D16 — Final consistency pass
**Status:** PENDING  
**Intent:** Cross-check dogs, certs, placements, photos, breeders; fix systematic mismatches.  
**Exit:** Short consistency report; known issues filed.

### D17 — Handoff note PRIMARY vs REFERENCE
**Status:** PENDING (this doc is operational; D17 is product doctrine)  
**Intent:** Document what is **PRIMARY** (baseline v2 + rebuilt rows) vs **REFERENCE** (legacy sidecars, old fills, True Grit, archive HTML).  
**Exit:** Checked-in note (e.g. `OCR_PIPELINE.md` or expand this file) used by all future ingest.

---

## Suggested next-session order
1. Let **A1** 1999–2001 tracks finish (`trackA=[1999,2001]`, `trackB=[2000]`).  
2. Re-run **A2** gate including 1999–2001; **A3** only for FAIL volumes.  
3. **A4/A5** when machine load allows.  
4. **B6→B9**, then **C10→C14**, then **D15–D17**.

## Key CLIs / modules
| Role | Path |
|------|------|
| HQ OCR core | `yearbook_ocr.py` |
| Baseline driver | `ocr_yearbook_baseline_v2.py` |
| Source helpers | `ocr_yearbook_source.py`, `yearbook_ocr_fonts.py`, `ocr_font_train.py` |
| Cert harvest/ingest | `harvest_cert_sections_v2.py`, `yearbook_certs_ingest.py` |
| Meta ingest | `yearbook_meta_ingest.py`, `yearbook_meta_schema.py` |
| Fill / remount | `fill_from_parse.py`, `remount_source_divisions.py` |
| Photos | `yearbook_extract_photos.py`, `yearbook_map_photos.py`, … |
| Tessdata | `tessdata_yearbook/jrtca_{helv,mono}.traineddata` |

## Git / data (as of handoff)
- PR **#44** merged — OCR pipeline + tessdata  
- PR **#45** merged — scans/photos/True Grit/jrtcabreeders via Git LFS  
- PR **#46** — canon promotions + OCR finalize (verify open/merged)  
- Temp `_*.py` one-offs culled; keep thin `_` shims + yearbook audit CSV/JSON + `_ocr_baseline_v2` + `_font_train`

## Explicit non-goals / do not
- Overwrite non-baseline OCR sidecars  
- Fabricate class titles or owner surnames  
- 4 parallel year tracks @ 10 workers without user approval  
- Treat True Grit / jrtcabreeders HTML as PRIMARY trial results  
