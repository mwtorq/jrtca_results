# Session note — OCR gate rework / full-page audit

- **Date:** 2026-11-08 (CST/CDT America/Chicago)
- **Repo:** `jrtca_results`
- **Parent / related session:** `ebd3ffaf-327e-42c1-9b81-4baabbd2e311`
- **Rule:** `.cursor/rules/cursor-transcripts.mdc` (alwaysApply) → log continuously here

## Scope (user)

- ~**3900 pages** yearbook **1990–2001**, plus **1984–1990** early packs.
- Must not require eyeballing all pages; automated audit of all pages required.
- **OCR cannot pass** for any user-pasted rework reason.
- Failures that need re-OCR must be **scheduled in process** (not WARN-unlock).

## User-pasted failure classes (this session)

### Right-edge owner cutoff (O6 / re-OCR)

1997 Vol I pt 1 examples: `Vincent Ste`, `Doug Steph`/`Stephel`, `Alte`, `Heather Crom`, `Mike & Bett`, `Linda Louc`, `Tony & Lir`, `Jack & Pz`, `George & Linc`, `Ed Rok`, `Martha Ler`, champ lines cut mid-owner.

### Smash / garble (1997 Vol I pt 2+)

Leading junk + place; mid-line smash; Championship Certificate smash; `1012 1/2"`, `12 172-15"`; `HunterfFinkemagel`.

### Gate miss root cause

O6/C1 were WARN; narrow `owner_tail_trunc` missed 3–4 letter stubs; unlock + C10 staged garbage.

---

## Action log

### ~20:14 — Transcript rule requested

- User: log all transcript content to repo; inherit for child sessions; folder `cursor-transcripts/`.
- Created `.cursor/rules/cursor-transcripts.mdc` (`alwaysApply: true`).
- Created `cursor-transcripts/README.md` + this session note (initial).

### ~20:22 — User: what are we doing to address failures?

- Honest gap: documentation only so far; began implementation.

### Code / policy changes (address failures)

1. **`assess_ingest_quality_audit.py`**
   - Policy: O6 + C1 are **FAIL** (block unlock).
   - `FAIL_CODES` += `owner_tail_trunc`, `class_header_gap`, `height_trunc_paren`, `place_rank_dust`.
   - `REOCR_CODES` set for image-recovery classes.
   - Each volume row: `reocr_required`, `reocr_codes`.
   - On FAIL: merge into **`_reocr_queue.json`**.
   - Report markdown policy text updated.

2. **`yearbook_ocr.py`**
   - Broadened `owner_tail_trunc` audit regex: `&` stubs up to 3 letters after; first+last 1–4 letters; named stubs `Steph|Crom|Louc|Lir|Alte|…`.

3. **`schedule_reocr_from_queue.py`** (new)
   - Maps queue HQ paths → source PDFs via `ocr_yearbook_baseline_v2.queue`.
   - Force `ocr_pdf_hq(..., force=True)` into baseline dest.
   - Logs: `_reocr_queue_run.log`.

4. **`_OCR_CLEANUP_CATALOG_HANDOFF.md`**
   - O6: FAIL + queue re-OCR (not audit-only).

### ~20:38 — B6b re-audit 1997 (dry-run then non-dry kicked)

- Command: `python -u assess_ingest_quality_audit.py --years 1997 --dry-run`
- Result: **FAIL=4 PASS=0 WARN=0** all 1997 vols.
- Queue: `_reocr_queue.json` = 4 volumes (Vol I pt1/pt2, Vol II pt1/pt2).
  - Dominant codes: `owner_tail_trunc` + `class_header_gap` (O6×25, C1×25 capped samples).
- Log: `_b6b_1997_failgate.out.log`

### ~20:40 — Force re-OCR 1997 started

- Command: `Start-Process … schedule_reocr_from_queue.py --years 1997 --workers 8 --page-workers 2`
- **PID:** 38764
- Logs: `_reocr_1997.out.log`, `_reocr_1997.err.log`, `_reocr_queue_run.log`
- First job: `Yearbook Scans\1997 Vol I\1997 Vol I pt 1.pdf` → baseline HQ (codes C1+O6).

### ~20:42 — User: transcript should be transcribing everything you're doing

- Strengthened rule: continuous append after each material tool batch (not summary-only).
- Rewrote this file with full action log above.

## Still TODO (next actions)

1. Confirm re-OCR PID 38764 progress; finish all 4×1997 PDFs.
2. Re-run B6b on 1997 after re-OCR; unlock only if FAIL=0.
3. Extend page-level audit + queue to **1998–2001** and A4 years as HQ appears (full ~3900 pages + 1984–90).
4. Keep appending here every batch.

## Related paths

- Canon: `_OCR_CLEANUP_CATALOG_HANDOFF.md`, `_plan_a1_d17_handoff.md`
- Queue: `_reocr_queue.json`
- Scheduler: `schedule_reocr_from_queue.py`
- A4 (parallel): `_ocr_a4_trackA.log`, `_ocr_a4_trackB.log`

### ~20:43 � Stale shell task notifications

- Batch of background shells finished (848869�848875): path/locate/catalog probes; two timed out earlier as `error`, others succeeded.
- Not new OCR work � already incorporated (catalog path, O6 recover APIs, transcript rule).
- Re-OCR 1997 still the active remediation job.

### ~20:45 � Dashboard must show re-OCR rework

- User: re-work must appear on dashboard.
- Added `reocr_queue_live()` in `pipeline_dashboard_status.py` (queue + PIDs + log page progress).
- HTML: new section **Re-OCR queue (FAIL ? force rework)** above Targeted OCR.
- Regenerated `_pipeline_dashboard_status.json`.

### ~20:52 � Shell notifications
- 848876 (start 1997 re-OCR) succeeded; 848877/848878 timed out (transcript append / HTML locate) � rework already on dashboard.


### ~20:53 � PPM wall clock fix
- Bug: elapsed_min divided wall by workers again (~3h showed as ~18m).
- Fix: elapsed = birth->now wall; worker_min = wall*N optional; UI no longer shows `/Nw` as divisor.


### ~21:03 � PPM fix verified
- Status regen: Track A elapsed 211.3 min, Track B 214.6 min (wall, not /10).


### ~16:55 CST 2026-11-09 � Status check

- A4 tracks **DONE**: A 49/49, B 14/14; no OCR PIDs alive.
- 1997 force re-OCR **DONE** ok=4 (finished ~13:35Z); queue file still lists 4 (not cleared).
- Manifest: 1997 still `b6b=FAIL unlock=False` � **needs B6b re-audit** on new HQ.
- 1998�2001 still old WARN unlock (pre O6/C1 FAIL promotion) � re-audit pending.
- Next: B6b 1997 (+98�01), clear/refresh `_reocr_queue.json`, then A5 / year-pipeline for A4 years.


### ~2026-11-09 16:58 CST � B6b re-audit start

- Queue refresh: audited years drop cleared entries (kept other years).
- Running: `assess_ingest_quality_audit.py --years 1997` then 1998-2001.


### ~2026-11-09 17:13 CST � B6b re-audit + O6 gate fix + re-OCR start

- Ran B6b on 1997 then 1998-2001; queue refresh drops cleared audited-year entries.
- O6 false-positive: surname regex matched any 2-5 letter last name (King/Smith/Hart). Replaced with `is_owner_tail_trunc_line` (stubs + short-unknown + Van/Der particles; complete-name allowlist).
- After fix: 1998 Vol I pt2 **PASS**; overall still FAIL-heavy on **C1 class_header_gap** (and residual real O6 stubs like Van/Kru/Pryc/Ost).
- Queue: 35 vols (1997:4 already force-reOCRed; 1998:6 1999:6 2000:5 2001:14).
- Starting `schedule_reocr_from_queue.py --years 1998 1999 2000 2001` (skip repeat 1997 for now).


### ~2026-11-09 17:23 CST � Re-OCR queue PPM parity

- Force re-OCR card now shows same PPM detail as Track A/B: `ppm` / `ppm_job` / pages / wall min / workers / tess-min.
- Status picks newest `_reocr*.log` with page lines (e.g. `_reocr_9801_run.log`).



### ~2026-11-09 17:27 CST � Re-OCR queue PPM parity

- Force re-OCR card matches Track A/B: ppm / ppm_job / pages / wall min / Nw / tess-min.
- Log pick: live `_reocr*.log` (UTF-16 Tee-Object safe); verified `_reocr_9801_run.log` 1/31 @ ~1.07 ppm.


### ~17:38 CST 2026-11-09 — Cloud pickup on Ldahsar

- Confirmed healthy mid-flight: PID 32312 `schedule_reocr_from_queue.py --years 1998 1999 2000 2001`; log `_reocr_9801_run.log`; **1/31** (1998 Vol I pt1) ~OCR page 19; PPM ~0.82–1.13; tess active. Did **not** kill.
- Session canon IDs 1–3 = 4–6 (user). Extracted local transcripts to Project store `docs/sessions/` + repo mirror `cursor-transcripts/sessions/`:
  - `7f2c4e98…` BOD/committees
  - `ecfad28f…` Breezewood (non-JRTCA; no yearbook)
  - `4de7fbd5…` jrtcabreeders.com
- `ebd3ffaf…` parent id: no local agent-transcripts folder found.
- Material OCR deltas from those chats: **none** that supersede HANDOFF/gate-rework. Parallel enrichment only.
- Status write: Project store `docs/pickup-status.md`.
- Next: let 98–01 re-OCR finish → B6b re-audit → unlock FAIL=0 only. Top debt still C1.


### ~18:10 CST 2026-11-09 — OCR viability check (no restart)

- Pulse: PID 32312 alive; **1/31** 1998 Vol I pt1; ~page 40; ~0.73 ppm; tess ~6–10.
- 98–01 completed vols this run: **0**. 1997 force-reOCR earlier ok=4.
- B6b ~17:11 (post-1997 reOCR, pre-98–01 finish): 1997 FAIL=4 unlock NO; 1998 FAIL=6 PASS=1; 1999–2001 all FAIL. Queue 35 (C1×35 O6×31).
- Spot-check: many place/owner lines readable; residual true O6 stubs + C1 still dominate.
- Verdict: **not unlock/ingest viable yet**. Wrote Project store `docs/ocr-viability.md`.


### ~18:20 CST 2026-11-09 — Detach re-OCR from IDE for Agents

- PID 32312 was Cursor-job-bound (powershell temp script ← Cursor.exe); closing IDE would kill it.
- Prior PPM: ~0.77 (49 pages / ~63.7 min). Stopped 32312 after page ~49 flush; wiped 1 partial; relaunched via WMI Win32_Process.Create (schtasks failed path-not-found on OneDrive path).
- New PID 5560 parent chain cmd→WmiPrvSE→services (not Cursor). Tess active. Monitor `_reocr_9801_run.log` + `_reocr_queue_run.log`.
- User may close IDE for this OCR job. Docs: docs/reocr-detached-monitor.md + cursor-transcripts/reocr-detached-monitor.md.

### ~18:29 CST 2026-11-09 — Dual-track force re-OCR (A/B)

- Confirmed year sets non-overlapping: Track A `{1998,2000}`, Track B `{1999,2001}`.
- Stopped single-queue PID 5560; wiped partials; prior reliable PPM ~0.77 (49/63.7min).
- Launched WMI-detached: PID **46756** → `_reocr_9800_trackA.log` (1/11); PID **32668** → `_reocr_9901_trackB.log` (1/20); ~14–20 tess.
- Dashboard updated for dual force-reOCR track cards; regenerated `_pipeline_dashboard_status.json`.

### ~18:46 CST 2026-11-09 — Tune dual-track to 7 workers each

- Prior PPM (10w): A ~0.67 (13/19.3m); B ~0.68 (13/19.2m). Stopped 46756/32668; wiped 2 partials.
- Relaunched WMI-detached: PID **34328** A 1998/2000 w=7; PID **48468** B 1999/2001 w=7. underCursor=false.

### ~19:10 CST 2026-11-09 — Live workers + dashboard adjust API

- Status JSON/HTML: workers from cmdline (prefer) for baseline A/B + force re-OCR A/B; tess_live.
- POST `/api/track/set-workers` on serve_pipeline_dashboard (localhost); restart-based retune via `track_worker_control.py`.
- Dashboard server restarted (PID ~40480); force-reOCR tracks left up (34328/48468 @ 7w).
