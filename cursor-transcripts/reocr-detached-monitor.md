# Re-OCR detached dual tracks

- **When:** 2026-11-09 ~18:46 America/Chicago (tuned)
- **Can close Cursor IDE:** YES

## Tracks (non-overlapping)

| Track | Years | PID | Log | Workers |
|---|---|---|---|---|
| A | 1998, 2000 | 34328 | `_reocr_9800_trackA.log` | 7 (+ page-workers 2) |
| B | 1999, 2001 | 48468 | `_reocr_9901_trackB.log` | 7 (+ page-workers 2) |

## Prior PPM before tune (10w each)

- A ~**0.67** (13 pages / 19.3 min)
- B ~**0.68** (13 pages / 19.2 min)

## Monitor

- WMI-detached (not under Cursor)
- Dashboard force-reOCR A/B cards at top of re-OCR box
- Do not restart while healthy; report prior PPM if restarting

## Dashboard worker display + adjust (2026-11-09 ~19:10 CT)

- Live `workers` / `workers_cmdline` / `tess_live` on baseline OCR Track A/B and force re-OCR Track A/B cards.
- Apply button → `POST http://127.0.0.1:8765/api/track/set-workers` `{kind: baseline|reocr, track: A|B, workers: N}` (localhost only).
- Adjust **restarts** that track (WMI-detached), wipes `*.partial.txt`, reports prior PPM in API response + log banner.
- Baseline Apply needs a live `ocr_yearbook_baseline_v2` process; force re-OCR Apply works on current dual tracks.
