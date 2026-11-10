# Pipeline dashboard — Linux cloud alternate

Full-feature twin of the Windows/local dashboard under `dashboard/`, adapted so it
runs on this Linux cloud VM. **Does not replace** `dashboard/serve_pipeline_dashboard.py`
(port 8765) or `track_worker_control.py` on the OCR host.

## Feature parity

Same UI/API surface as the core dashboard:

- Status cards, plan steps A1–D17 (+B6b), years/eras
- Live baseline OCR tracks A/B (PPM, workers, page lines)
- Dual force re-OCR tracks A/B + FAIL→rework queue
- Targeted C1/O6 recover + B6b ingest audit
- Apply / `POST /api/track/set-workers` (same JSON body)

Worker retune on Linux: **remote-hint** (OCR PIDs on Ldahsar) or optional **proxy**
via `JRTCA_WORKER_CONTROL_PROXY` → Windows `:8765`.

## Run on this machine

From repo root:

```bash
python -u dashboard/cloud/serve_cloud_dashboard.py --port 8766
```

Open:

- http://127.0.0.1:8766/
- http://127.0.0.1:8766/_pipeline_dashboard.html
- http://127.0.0.1:8766/api/status

## Ldahsar status (default `--mode auto`)

OCR PIDs live on Ldahsar; this VM cannot resolve `ldahsar` by DNS. Auto mode prefers:

1. `JRTCA_DASHBOARD_STATUS_URL` → e.g. `http://HOST:8765/api/status`
2. Synced JSON file (`JRTCA_DASHBOARD_STATUS_JSON`, `dashboard/cloud/_synced_pipeline_dashboard_status.json`, or Project store `internal/ldahsar-pipeline-status.json`)
3. Local gather (fallback; OCR alive will be false)

### 1-minute sync (recommended)

On **Ldahsar** (do not stop re-OCR — run in a separate window / self-hosted agent):

```bat
cd /d "C:\Users\mw\OneDrive - timberwilde.net\repos\jrtca_results"
"C:\Users\mw\AppData\Local\Python\pythoncore-3.14-64\python.exe" -u dashboard\cloud\watch_export_ldahsar_status.py --interval 60
```

(OneDrive path may vary; any `jrtca_results` checkout on Ldahsar works. Equivalent PowerShell:)

```powershell
cd $env:USERPROFILE\OneDrive*\repos\jrtca_results
& "$env:LOCALAPPDATA\Python\pythoncore-3.14-64\python.exe" -u dashboard\cloud\watch_export_ldahsar_status.py --interval 60
```

On **this cloud VM** (already startable alongside `:8766`):

```bash
python -u dashboard/cloud/watch_pull_ldahsar_status.py --interval 60
```

Exporter writes Project store `internal/ldahsar-pipeline-status.json`; puller refreshes `:8766` runtime JSON each minute. Published Cursor app still needs an explicit republish to pick up a new `status.json` snapshot.

One-shot export on Ldahsar:

```bat
"C:\Users\mw\AppData\Local\Python\pythoncore-3.14-64\python.exe" -u dashboard\cloud\export_ldahsar_status.py
```

## Proxy Apply to Ldahsar

```bash
export JRTCA_WORKER_CONTROL_PROXY=http://ldahsar:8765
python -u dashboard/cloud/serve_cloud_dashboard.py --port 8766
```

`POST /api/track/set-workers` then forwards to the Windows control API.

## Files

| File | Role |
|------|------|
| `serve_cloud_dashboard.py` | HTTP server (port **8766**); live or synced status |
| `pipeline_dashboard_status.py` | Cloud gatherer (Linux `/proc` process scan; repo root = `../..`) |
| `track_worker_control.py` | Same Apply API; Linux → proxy / remote-hint |
| `index.html` | Publishable UI entry (Cursor web app) |
| `_pipeline_dashboard.html` | Same UI (underscore name kept for parity) |
| `status.json` | Publishable status snapshot (HTML fetches this) |
| `_pipeline_dashboard_status.json` | Runtime artifact (gitignored; mirrored from gather) |

Pipeline inputs remain at the **repo root**.

## Cursor web app publish

`dashboard/cloud/` is the publish folder (`index.html` + `status.json`). Local preview:
`http://127.0.0.1:8766/`. Published hosting serves the committed snapshot; re-gather with
`serve_cloud_dashboard.py` and re-publish (or sync `status.json`) for fresher data.
