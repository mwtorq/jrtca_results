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
