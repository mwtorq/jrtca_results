# OCR viability — 1997–2001 HQ (pickup pulse)

- **When:** 2026-11-09 ~18:10 America/Chicago (Ldahsar)
- **Question:** Are newly OCR’d results viable enough to unlock/ingest?
- **Short answer:** **No — still blocked for unlock/SQL apply.** Bulk place-lines look readable, but B6b remains FAIL-heavy (C1 + real O6). 98–01 force re-OCR has not finished any volume yet.

## 1) Live re-OCR pulse

| Item | State |
|---|---|
| PID | **32312** `schedule_reocr_from_queue.py --years 1998 1999 2000 2001` — alive |
| Progress | **1/31** — still on `1998 Vol I, pt 1` |
| Pages | OCR page ~**40** (climbing); `*.partial.txt` ~193 KB @ 18:08 |
| PPM | ~**0.73** (40 pp / ~54.5 min wall) |
| Tess | ~6–10 |
| Completed in this 98–01 run | **0** volumes (`ok` lines = 0) |

1997 prior force re-OCR: **DONE ok=4** (`_reocr_1997.out.log` ~13:35Z). Not re-run in current job.

## 2) Spot-check (HQ text quality)

### 1997 (force-reOCR completed earlier; hqmax present)

Path example: `_ocr_baseline_v2\yearbook_1990_2001\1997\1997_Vol_I\1997 Vol I pt 1_ocr_hqmax.txt`

- **Good:** Class headers + `Entries: N` + ranked place lines with full-looking owners are mostly coherent (e.g. `1st: Flashpoint Jake, owned by Linda Nash`; height bands like `Dog Pups, 9-12 months, over 12 1/2"`).
- **Bad / residual:** Right-edge owner stubs still present per B6b samples (`Vincent Ste`, `Doug Steph`, `Alte`, `Heather Crom`, `Linda Louc`, `Joanne Van`, `Lynda Kru`). Cover/champ lines can still clip (`G-T-G Champion (under): Cromwell St`). Height OCR noise (`upto 121/2"`, `12 12"`).
- **C1:** Still saturating audit caps (C1×25 per vol in B6b) — missing/weak class titles before `1st:`.

### 1998 Vol I pt 1 (in-flight partial only)

Path: `...\1998\1998_Vol_I\1998 Vol I, pt 1_ocr_hqmax.partial.txt`

- Mid-file place samples look structurally fine (owners complete on many puppy/handler lines).
- Live page audits on `_reocr_9801_run.log` still flag **C1** and occasional **O6**/`missing_owned_by` (e.g. pages 25–38).

### 1999–2001

No new force-reOCR completions yet this run. On-disk hqmax mtimes are mostly **pre** this queue job (Nov 8 A1 / Nov 9 ~17:00 B6b touch). Do **not** treat as “new force-reOCR results.”

## 3) Gates / queue (pre- vs post-reOCR)

| Source | Mtime (America/Chicago) | Scope vs force re-OCR | Verdict |
|---|---|---|---|
| `_b6b_ingest_audit_1997.md` | 2026-11-09 ~17:11 | **Post** 1997 force re-OCR; **pre** 98–01 job | **FAIL=4 / PASS=0 / unlock NO** (fail hits 29–50/vol; O6+C1) |
| `_b6b_ingest_audit_1998.md` … `2001.md` | ~17:11–17:13 | **Pre** current 98–01 force re-OCR | Years **FAIL**; unlock NO. 1998 alone: FAIL=6 PASS=1 (pt2) |
| `_reocr_queue.json` | ~17:13 | Built from those B6b runs | **35** vols; codes C1×35, O6×31 |
| `_a2_quality_gate_*.md` | Nov 7–8 | Older A2; not post-reOCR | Stale vs current FAIL policy |

**Important:** There is **no post-reOCR B6b** yet for any 1998–2001 volume from the live queue. 1997 is the only year with force-reOCR **and** a subsequent B6b — and it still failed unlock.

## 4) Verdict

| Use | Viable? | Why |
|---|---|---|
| Unlock / SQL ingest (policy) | **No** | Unlock requires FAIL=0; 1997 post-reOCR B6b still FAIL=4; 98–01 not finished |
| Human eyeball / debugging samples | **Partially yes** | Many place/owner/class lines are readable; useful for finalize/C1 work |
| Declare 98–01 “new OCR success” | **No** | Still **1/31**; zero `ok` completions this run |

**Bottom line:** Newly OCR’d text is **directionally useful but not ingest-viable**. Standing blocker is **C1 image title recovery** plus residual **true O6** right-edge cuts. Next evidence gate: finish queue → re-run B6b per finished year → unlock only FAIL=0.

## Paths cited

- `c:\Users\mw\OneDrive - timberwilde.net\repos\jrtca_results\_reocr_9801_run.log`
- `c:\Users\mw\OneDrive - timberwilde.net\repos\jrtca_results\_reocr_1997.out.log`
- `c:\Users\mw\OneDrive - timberwilde.net\repos\jrtca_results\_reocr_queue.json`
- `c:\Users\mw\OneDrive - timberwilde.net\repos\jrtca_results\_b6b_ingest_audit_1997.md` (and 1998–2001 siblings)
- `c:\Users\mw\OneDrive - timberwilde.net\repos\jrtca_results\_ocr_baseline_v2\yearbook_1990_2001\1997\...\*_ocr_hqmax.txt`
- `c:\Users\mw\OneDrive - timberwilde.net\repos\jrtca_results\_ocr_baseline_v2\yearbook_1990_2001\1998\1998_Vol_I\1998 Vol I, pt 1_ocr_hqmax.partial.txt`
