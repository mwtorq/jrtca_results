# OCR / finalize cleanup catalog (handoff)

**Repo:** `jrtca_results` · **Module:** `yearbook_ocr.py` · **Driver:** `ocr_yearbook_baseline_v2.py`  
**Related:** `_HANDOFF_OCR_SESSION.md`, `_PLAN_A1_D17_HANDOFF.md`  
**Date:** 2026-11-07  

This lists **defect types we had to clean** while building the HQ yearbook baseline. Use it when a user pastes bad OCR: match the pattern → apply/extend the fix class (do not invent surnames or class titles without evidence).

**Layers (do not invert):**
1. **OCR / ensemble** — preprocess, PSM, column split, peer reconcile, interstitial header recovery  
2. **Finalize** — `finalize_results_ocr` (gutter, heights, place dust, smash, rehome, markers)  
3. **Audit** — `audit_results_ocr_page` residual signatures after finalize  
4. **Name hardcodes** — `_OCR_NAME_PHRASES` last resort only  

---

## 1. Height / size-band garble

| ID | Symptom | Example | Fix locus |
|----|---------|---------|-----------|
| H1 | `%` for `1/2` | `10-12%`, `12%-15`, `12 %2 up to 15"` | `normalize_height_class_ocr` |
| H2 | `4/2` for `1/2` | `12 4/2-15"`, `10-12 4/2` | same |
| H3 | Leading `1→4` digit noise | `40-12 1/2"`, `42 1/2-15"`, `4211245` | same |
| H4 | Compact / smashed digits | `10-1212"`, `1212245"`, `121/215"`, `1042112`, `1012 10-12…` crumb | same |
| H5 | Bare `2` for `1/2` | `10-12 2"`, `12 2-15"`, `10-12 12"` | same (`height_bare2` audit) |
| H6 | Height glued to place | `12 1/2-15"1st: Name` | split height then place (finalize) |
| H7 | Truncated cert/class size | `(10-12 1)`, `(10-12 1 –)` | normalize + `height_trunc_paren` audit |
| H8 | `Champ:` abbreviation | `12 1/2-15" Champ:` | expand to `Champion:` |

**Audit keys:** `height_pct`, `height_4slash2`, `height_101212`, `height_bare2`, `height_40_42`, `height_trunc_paren`, `height_glued`, `champ_abbrev`

---

## 2. Place-rank dust / echo

| ID | Symptom | Example | Fix locus |
|----|---------|---------|-----------|
| P1 | Place-word echo after colon | `2nd: ond: Name`, `3rd: did: Name`, `ith:` | place-echo strip in finalize / `fix_place_rank_ocr` |
| P2 | Rank dust doubled | `1st: 1st. Name`, `2nd: 3rd Name` | strip; `place_rank_dust` / `dup_place` audit |
| P3 | Bang / junk after place | `1st: ! Farmstead`, `6th: — Name` | strip punctuation after place |
| P4 | Pipe / broken I | `\| Am Prancer` → `I Am…` | pipe normalize |
| P5 | Lost digit on ordinal | `st Sady Lady` → `1st: Sady Lady` | `^st` / `nd` / `rd` repair |
| P6 | Place prefix on height champ row | `4th: 10-12 1/2" Champion:` | strip ordinal; leave height role line |
| P7 | Misc OCR ordinals | `dnd:`, `3id:`, `9nd:`, `dst:`, `14st:`, bare `and:` | audits + repairs |

**Audit keys:** `place_ond`, `place_ith`, `place_bang`, `place_rank_dust`, `dup_place`, `place_dnd`, `place_3id`, `place_9nd`, `place_dst`, `place_14st`, `place_and`

---

## 3. Column smash / dual owned-by

| ID | Symptom | Example | Fix locus |
|----|---------|---------|-----------|
| S1 | Two dogs + two owners in one line | `1st: DogA, DogB, owned, owned by X by Y` | `_place_line_is_smashed` / `_unsmash_place_body` / `_repair_smashed_place_lines`; ensemble peer replace (−score on smash) |
| S2 | Interleaved `owned` mid-name | `Hunt's owned Comet, by Gayle owned Jennings by Dan` | same unsmash → cleanest single dog+owner |
| S3 | `owned by owned owned … by … by …` | Triple-owned chains | same |
| S4 | Trailing `by` crumbs | `owned by Will Hahn by` | mangled_by / owned-by normalize |

**Policy:** Prefer one clean `Dog, owned by Owner`. **Do not invent** missing 2nd/3rd place rows without evidence.  
**Audit keys:** `place_smash`, `mangled_by`, `missing_owned_by` (when used), `owend_by`

---

## 4. Missing / wrong section structure

| ID | Symptom | Example | Fix locus |
|----|---------|---------|-----------|
| C1 | Class title dropped between place blocks | After `Entries: 2` + 1st/2nd, next `1st:` with no header | **Must FIND title** via column-image interstitial OCR / peer headers (`_ocr_interstitial_class_header`, `_inject_peer_class_headers`, `_inject_headers_from_column_boxes`). Placeholder `[missing class header]` is **last resort only** (user rejected markers-as-solution). |
| C2 | Racing height champs under wrong class | Veteran places then `10-12 1/2" Champion:` then empty `ADULT RACING…` | `_rehome_orphan_adult_height_champs` |
| C3 | Section header glued to owner | `owned by Alte STEEPLECHASE RACES`, `… Alta RACING CHAMPIONS` | strip header to own line; block surname rejoin |
| C4 | Division + next-column bleed | `CONFORMATION DIVISION    : Fanmilv Class Entricer 0` | keep `CONFORMATION DIVISION`; salvage `Family Class Entries: N` if present (preserve empty classes) |
| C5 | Folio / next-trial bleed | `39    SWUJRTN Fall Harvest`, `1997 JRTCA Yearbook, Vol. I`, `Gold Coast Terrier Trial` after crumbs | `_is_ocr_noise_line` / trial_bleed |
| C6 | Orphan Entries / lift to header | Bare `Entries:` or count on wrong line | `_lift_trailing_entries_to_class_header`, `_join_class_header_with_entries`, `_reattach_orphan_entry_counts` |
| C7 | Puppy championship block order | Places mixed with champ lines | `_reorder_puppy_championship_block` |

**Audit keys:** `trial_bleed`, `class_header_gap` (if marker remains), `bare_entries`, `champ_reserve_split`, `entriess`, `cert_entries_glue`

---

## 5. Owned-by / entries lexical

| ID | Symptom | Example | Fix locus |
|----|---------|---------|-----------|
| O1 | `Entriess` / missing colon | `Entriess 5`, `Entries 5` | Entries normalize |
| O2 | `Entricer` | `Entricer 0` | → `Entries: 0` |
| O3 | Missing comma before owned by | `Kid owned by` | insert `, owned by` |
| O4 | Gutter letter between commas | `Ringlet,t, owned by` | strip |
| O5 | OCR owned typos | `owend by`, `owned hy` | `_normalize_owned_by_ocr` |
| O6 | Truncated owner tail (column crop) | `owned by George & Linda Louc`, `& Lir`, `Donna Pi`, `Vincent Ste`, `Doug Steph` | **Do not invent**; **FAIL** `owner_tail_trunc` → queue re-OCR / wider crop / ensemble (`_reocr_queue.json`) |
| O7 | Incomplete `owned by` EOL | `Champion: Jezebel, owned by` | leave incomplete; don’t fabricate |

---

## 6. Class-header / glyph dust

| ID | Symptom | Example | Fix locus |
|----|---------|---------|-----------|
| G1 | Currency/glyph before Entries | `Novice Puppies ¥    Entries:` | strip ¥£€ etc. before Entries |
| G2 | Cutoff class words | `3itches`, `Jog Pups`, `nder 12`, `ACING` | cutoff repairs + audits |
| G3 | Coat abbrev | `ribr` / `rlbr` | `normalize_coat_ocr` |
| G4 | Agility pipe | `Agility \|` | strip; audit `agility_pipe` |
| G5 | Judges junk / JUQGES | mangled judges lines | noise + audits `judges_junk`, `juqges`, `juages` |

---

## 7. Gutter / fragment / crumb noise

| ID | Symptom | Example | Fix locus |
|----|---------|---------|-----------|
| N1 | Short multi-token crumbs | `eo nr re`, `TTT eee ee` | `_is_ocr_noise_line` |
| N2 | Trailing surname fragment page | `phenson` / `Carlier` / `1t Stephens` / `30` … next trial | `_drop_trailing_gutter_crumbs` / noise |
| N3 | Mid-gutter before place | `posi   1st:` | strip in `_strip_gutter_noise` |
| N4 | Underscore/tilde runs | `~~___~~` | gutter strip |

---

## 8. Name residuals (hardcodes — last)

Only after OCR+finalize. Examples used: `Qaldield`→`Oakfield`, `Bianquita`→`Blanquita`, `John Bait Badgwell`→`John & Betty Badgwell`, `RA.`→`R.A.`, Windy Hill / Briarpatch / etc. (`_OCR_NAME_PHRASES`).

**Do not** add speculative surname completions for truncated tails (Louc/Lir/Piel).

---

## 9. Pipeline / ops cleanups (not line-OCR)

| Item | What we did |
|------|-------------|
| Tessdata path | No-space runtime dir `jrtca_tessdata` + `TESSDATA_PREFIX` (blank pages from spaces in path) |
| Font langs | Train/wire `jrtca_helv` / `jrtca_mono` |
| Parallelism | In-page → page workers → year tracks; capped at 2 tracks × 10 workers |
| Sidecar policy | Write only `_ocr_baseline_v2/`; never clobber scan-folder OCR |
| Temp scripts | Deleted unneeded `_peek/_probe/_fix/…`; kept thin canon shims |
| Git LFS | Scans, photos, True Grit, jrtcabreeders in LFS (PRs #45+) |

---

## Paste triage cheat sheet

1. Heights look wrong → §1  
2. `ond:` / `did:` / `1st: 1st.` → §2  
3. Multiple `owned by` / two dogs one line → §3  
4. `1st:` repeats with no class title → §4 **C1 (recover from image)**  
5. Racing champ under Veteran/conformation → §4 **C2**  
6. `STEEPLECHASE` / `RACING CHAMPIONS` on owner → §4 **C3**  
7. Owner ends mid-word → §5 **O6** (**FAIL** + schedule re-OCR)  
8. Random crumb lines / trial name bleed → §7  

---

## Open / incomplete (next session)

1. **Class-title recovery must succeed on image** (helpers exist / in progress: interstitial box OCR + peer inject) — user requires finding titles, not logging gaps.  
2. Owner-tail truncation → OCR crop/ensemble, not finalize hardcodes.  
3. Smash still depends on peer quality when unsmash guesses wrong dog.  
4. Finish A1–D17 per `_PLAN_A1_D17_HANDOFF.md`.  

---

## Code map (quick)

| Concern | Symbols |
|---------|---------|
| Finalize entry | `finalize_results_ocr` |
| Heights | `normalize_height_class_ocr` |
| Smash | `_repair_smashed_place_lines`, `_unsmash_place_body`, reconcile smash penalty |
| Racing rehome | `_rehome_orphan_adult_height_champs` |
| Class gaps / headers | `_mark_missing_class_headers` (fallback), `_ocr_interstitial_class_header`, `_inject_peer_class_headers`, `_inject_headers_from_column_boxes` |
| Noise | `_is_ocr_noise_line`, `_strip_gutter_noise`, `_drop_trailing_gutter_crumbs` |
| Audit | `_OCR_AUDIT_PATTERNS`, `audit_results_ocr_page` |
