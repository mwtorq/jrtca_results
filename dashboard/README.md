# Pipeline dashboard

A1–D17 (+B6b) live status UI for `jrtca_results`.

## Run

From repo root:

```text
python -u dashboard/serve_pipeline_dashboard.py --port 8765
```

Open http://127.0.0.1:8765/_pipeline_dashboard.html (or `/`).

## Files

| File | Role |
|------|------|
| `serve_pipeline_dashboard.py` | HTTP server (stdlib); regenerates status JSON on each status GET |
| `pipeline_dashboard_status.py` | Gathers OCR tracks, C1/O6 recover, B6b, eras → status JSON |
| `_pipeline_dashboard.html` | Frontend |
| `_pipeline_dashboard_status.json` | Generated artifact (do not edit) |

Pipeline inputs (`_pipeline_year_manifest.json`, OCR logs, HQ baseline, …) remain at the **repo root**; only dashboard code and its generated JSON live here.
