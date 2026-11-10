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

## Synced status (OCR only on Ldahsar)

If this VM has repo artifacts/logs but not live OCR PIDs, default `live` mode still
shows log-derived PPM/queue/year cards. For a byte-identical status dump from the
Windows host:

```bash
# Copy Ldahsar's dashboard/_pipeline_dashboard_status.json here, then:
python -u dashboard/cloud/serve_cloud_dashboard.py --mode synced \
  --status-file /path/to/_pipeline_dashboard_status.json
```

Or:

```bash
export JRTCA_DASHBOARD_STATUS_JSON=/path/to/_pipeline_dashboard_status.json
python -u dashboard/cloud/serve_cloud_dashboard.py --mode synced
```

You can also drop a file at `dashboard/cloud/_synced_pipeline_dashboard_status.json`.

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
| `_pipeline_dashboard.html` | Full UI (cloud banner only additive) |
| `_pipeline_dashboard_status.json` | Generated artifact (do not edit) |

Pipeline inputs remain at the **repo root**.
