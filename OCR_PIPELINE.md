# Yearbook OCR pipeline (canonical scripts)

**Fix order:** OCR ensemble + token voting first → structural finalize → name hardcodes last (fallback only). Do not add a name hardcode until OCR/voting has been tried.

**Fonts (not in PDF metadata — visual ID):** see `yearbook_fonts_by_year.json`.
- **1984–88 results body:** monospace typewriter / daisy-wheel (Courier-like). Magazine ads/titles may be serif or Helvetica Bold — ignore those for results OCR.
- **1989+:** Helvetica-like; **1990–2001** Helvetica Regular/Bold.

## 1997–2001 remediation doctrine

1997–2001 trial/cert data **already exists** but is mangled by old OCR. HQ re-OCR into `_ocr_baseline_v2/` should be **substantially cleaner** and become PRIMARY for cleanup / update / reinsert. **1990–1996** (A4) stays parked separately.

**Year-parallel tracks:** unit of progress is a **year**. When A1 finishes a year, advance A2 → B6 (and later C) for that year without waiting for the rest of A1. Live A1 keeps the two 10-worker tess pools; downstream steps are CPU-light and must not start a third full OCR farm. A3 re-OCR (FAIL vols only) uses at most workers=2 when tess capacity is free.

| Script | Role |
|--------|------|
| `yearbook_ocr.py` | HQ OCR + `finalize_results_ocr` / page audit |
| `ocr_yearbook_source.py` | Tesseract config, PDF render, year derive |
| `yearbook_meta_schema.py` | Meta DB schema helpers |
| `ocr_yearbook_baseline_v2.py` | **A1** — force HQ OCR 1997–2001 → `_ocr_baseline_v2/` |
| `ocr_yearbook_missing_vols.py` | OCR listed missing Updated Yearbook vols |
| `assess_ocr_baseline_a2_gate.py` | **A2** — per-year gate + rollup; FAIL=0 unlocks B6 (WARN OK) |
| `pipeline_year_status.py` | A1 completeness + `_pipeline_year_manifest.json` |
| `pipeline_advance_years.py` | Advance A2→B6→B6b(+optional C10 stage) per completed year |
| `harvest_cert_sections_v2.py` | **B6** — cert section harvest (`--years` for scope) |
| `assess_ingest_quality_audit.py` | **B6b** — catalog ingest audit (FAIL blocks SQL apply) |
| `assess_yearbook_1997_2001.py` | Quality assessment CSV/report |

## Run A1

```powershell
cd "c:\Users\mw\OneDrive - timberwilde.net\repos\jrtca_results"
& "C:\Users\mw\AppData\Local\Python\bin\python3.exe" -u ocr_yearbook_baseline_v2.py --force
```

## Advance completed years (while A1 continues)

```powershell
& "C:\Users\mw\AppData\Local\Python\pythoncore-3.14-64\python.exe" -u pipeline_advance_years.py --years 1997 1998 --force-a2 --force-b6
# Later, when a year finishes A1:
& "C:\Users\mw\AppData\Local\Python\pythoncore-3.14-64\python.exe" -u pipeline_advance_years.py --years 2000
```

Manifest: `_pipeline_year_manifest.json`. Log: `_pipeline_advance.log`.

Output stays under `_ocr_baseline_v2/` (data dir name unchanged). Legacy `_yearbook_meta_strict.py` and `_ocr_baseline_v2_yearbook_9701.py` are deprecation shims only.

## D17 — PRIMARY vs REFERENCE (DONE 2026-11-14)

**Status:** Cutover for **1990–2001**. Future ingest / rebuild / remount MUST use PRIMARY only.

### PRIMARY (source of truth)

- Committed `Updated Yearbook Scans/**/*_ocr_hqmax.txt` after `finalize_results_ocr`
- Local audit mirror: `_ocr_baseline_v2/` (gitignored; keep in sync; do not treat as the commit path)
- Manifest stamp: `_pipeline_year_manifest.json` → `d17.status=DONE`, per-year `primary=eligible`

### REFERENCE only (cite; never overwrite PRIMARY)

- Legacy scan-folder OCR sidecars / pre-baseline text
- True Grit / archive HTML / old fills
- Non-hqmax or pre-finalize dumps

### PRIMARY exceptions (accepted 2026-11-14 — do not invent surnames)

These volumes stay **PRIMARY**. B6b still reports FAIL=1 on the residual line; cutover proceeds with the hole documented. SQL apply for that year may proceed under this exception; do not fabricate the missing owner text.

| Year | File | Residual | Evidence |
|------|------|----------|----------|
| **1993** | `Document_2026-11-03_224445_ocr_hqmax.txt` | `2nd: Wyndhaven Lonestar, owned by` (blank) | Force re-OCR + page-24 band: print owner field empty |
| **1994** | `Document_2026-11-04_083342_ocr_hqmax.txt` | `5th: Raheen Doc Holiday, owned by Coffey & Cur` | Force re-OCR + page-2 band: print-edge trunc |

**Cleared (not an exception):** 2001 Jon Go / John Go — page-39 surname **Go** is complete; allowlisted; B6b 2001 FAIL=0.

### Operator rules after cutover

1. Ingest/rebuild from PRIMARY hqmax only.
2. Never copy REFERENCE sidecars over PRIMARY.
3. Do not “fix” Lonestar/Coffey by inventing surnames; only replace if new PDF/page evidence appears.
4. Year-by-year B6b `--apply` is allowed for FAIL=0 years; for 1993/1994 only under the exceptions above.

See `_PLAN_A1_D17_HANDOFF.md` §D17.
