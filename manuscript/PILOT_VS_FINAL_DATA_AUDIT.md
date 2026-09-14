# Pilot vs. Final Data Audit (Teammate Feedback Item 9 — Sumiya's pilot comments)

**Purpose:** make it impossible to accidentally mix any pilot artifact with the
final 92,160-trial study. This document classifies every pilot/dry-run artifact
found in the repository; **none of them were used to compute or revise any
claim in the current manuscript.**

## Canonical final artifact (source of truth for every claim in the manuscript)

| | |
|---|---|
| File | `final_audit/FINAL_LOCKED/results_FINAL_92160.parquet` |
| SHA-256 | `a72fd43e87457a70c2833314e1443a794fa4189362ac8206c56275ef427fb62e` (re-verified unchanged in this pass) |
| Design | 4 architectures × 240 items × 8 seeds × 12 pressure targets = **92,160 trials** |
| Architectures | Transformer control, AHN-Mamba2, AHN-DeltaNet, AHN-GatedDeltaNet |
| Status | **Frozen v1.0**, approved post-freeze reporting amendment **v1.1**. This is the only artifact this manuscript reports on. |

## Pilot / dry-run artifacts found, and their relationship to the final study

| artifact | rows / scale | architectures | purpose (as labelled in the artifact itself) | contributed to any reported manuscript claim? |
|---|---|---|---|---|
| `data/pilot_raw_results.csv` | 500 rows | not applicable (early schema: `fact_id`, `importance`, `facts_after_target`) | earliest prototype smoke test, pre-dates the current dataset schema (`item_id`, `fact_type`, `tokens_after_target`) entirely | **No.** Different schema; superseded before the design froze. |
| `outputs/results_pilot.parquet` + `outputs/items_pilot.json` | **50 rows** (10 items × 5 pressure levels, 1 seed) | **1 architecture only** (`gated_deltanet`) | earliest single-architecture smoke test of the harness | **No.** |
| `outputs/pilot_pass2_*` (parquet/CSV/MD under `outputs/`, config `config/pilot_pass2_calibration.json`, code `src/ahnexp/pilot_pass2.py`, protocol `protocol/pilot_pass2.md`) | **1,760 trials**, all 4 arms, but a **different, pre-freeze pressure grid** `[170,200,225,240,255,270,290,330,430,640,1024]` (not the frozen `[150,180,205,220,235,250,265,285,315,380,520,760]`) | all 4 | self-labelled in its own summary: **"Pilot Pass 2 — plumbing + localization, NOT inferential evidence"** — used to calibrate and localise the pressure grid *before* the design was frozen | **No** (by its own explicit label; also on a different pressure grid than the frozen design, so it is not even commensurable with final results). |
| `outputs/pilot_pass2_dryrun.json`, `scripts/pilot_pass2_dryrun.py` | n/a | n/a | dry-run harness check for Pilot Pass 2 | No |
| `notebooks/0_pilot_reference.ipynb`, `outputs/tables/*_pilot.md`, `outputs/figures/*_pilot.png` | n/a | n/a | exploratory pilot notebook and its exhibit drafts | No — never referenced by the manuscript or the publication exhibits pipeline |

## An artifact that looks like a pilot but is NOT one

| artifact | what it actually is |
|---|---|
| `outputs/final_dryrun.json` (and its archived copy `final_audit/FINAL_LOCKED/final_dryrun.json`) | A **pre-flight calibration check of the FINAL, frozen 240-item design** — `n_items: 240`, the frozen 12-target grid, confirming realised-vs-intended pressure calibration is within tolerance (`transition_region_ok: true`, `all_targets_ok: true`, `trajectory_nesting_ok: true`, 0 items out of tolerance) before the full run. It is part of the final study's own provenance record, not a separate pilot experiment, and is already referenced from the reproducibility material (Methods §2.6 / Extended §2.14). **Not a pilot artifact for the purposes of this audit** — it describes the final design, not a superseded one. |

## Sumiya's specific pilot observations — do they apply to the final study?

**Claim: "`results_pilot.parquet` = 50 rows = 10 items × 5 checkpoints."**
Verified against the file: 50 rows, 10 items, **1** architecture
(`gated_deltanet`) — not 5 checkpoints. The factor-of-5 in "10 × 5 = 50" comes
from **5 pressure levels per item** (the file's `tokens_after_target` values
cluster into 5 bands), not 5 model checkpoints. Regardless of the exact
factorisation, this is a single-architecture, single-seed, 50-row smoke test —
**does not apply to the final study** (4 architectures, 8 seeds, 240 items,
92,160 trials).

**Claim: "68% in lowest confidence bin."**
Verified: binning this file's `confidence` column into five equal-width bins
gives 34/50 = **68%** in (0.0, 0.2] — the observation is numerically correct
**for this 50-row pilot file**. It reflects a real property of raw
sequence-probability confidence on a small, short-answer sample (long tail
toward zero because sequence probability penalises longer generations). It is
**not** a property that can be checked or refuted against the final
92,160-trial data by re-reading this file, because this file is not part of
the final study.

**Claim: concerns about `length_normalised`.**
`src/ahnexp/evaluate.py` implements a `_confidence()` function with two modes
behind a config switch, with the code comment: *"Sequence probability
penalises long answers — the pilot's values span six orders of magnitude,
which distorts every calibration bin. Which one we use is still an open
decision (`open_decisions.md` #6)."* `open_decisions.md` item 6, owned by
Sumiya, records exactly this pilot-driven concern. **Resolution for the final
study:** the frozen configuration (`config/experiment.yaml`, `calibration.
confidence`) sets **`sequence_probability`** (not length-normalised) for the
final 92,160-trial run, and the manuscript discloses this as a limitation
wherever confidence is discussed:

- Methods §2.4: "confidence is the greedy sequence probability (provisional)."
- Discussion §4.4: "the sequence-probability measure is provisional" and lists
  "length-normalised confidence… as natural next steps."
- Discussion §4.6 (Limitations): "Sequence probability is provisional."

So Sumiya's concern **directly caused** the manuscript's existing "provisional"
disclosure and the length-normalised option being built into the codebase —
but it does **not** mean the final study used length normalisation (it did
not), and it does not require any further edit: the caveat it motivated is
already in the manuscript.

**Claim: concerns about H2/H3 "from that run."**
Neither Pilot Pass 2 (1,760 trials, pre-freeze grid) nor the 50-row smoke test
computed anything resembling the frozen H2/H3 endpoints reported in the
manuscript. Pilot Pass 2's own summary explicitly disclaims inferential status
("NOT inferential evidence"); its `per_arm_strict_accuracy_K` and
`per_arm_strict_drop_width_90_10` values are **exploratory, pre-freeze,
different-grid quantities** used only to help design the final pressure grid,
not to draw or support any H2/H3 conclusion now in the manuscript. Any H2/H3
concern raised from that run either (a) was already resolved by redesigning
the final grid and freezing new endpoints before the full run, or (b) does not
transfer to the final data at all because the final run used a materially
different pressure grid, item count, seed count, and (for H2) a documented
post-freeze reporting amendment process that Pilot Pass 2 predates entirely.

## Explicit non-mixing statement

**No claim, number, figure, or table in the current manuscript (`manuscript/
ABSTRACT.md` through `CONCLUSION.md`) is derived from `results_pilot.parquet`,
`items_pilot.json`, `data/pilot_raw_results.csv`, any `pilot_pass2_*` artifact,
or any other pre-freeze/dry-run file except `final_dryrun.json`'s role as a
pre-flight calibration check of the final design.** Every numerical statement
in `RESULTS.md` traces to `final_audit/FINAL_LOCKED/results_FINAL_92160.parquet`
(frozen v1.0) or the approved post-freeze amendment (v1.1) — see
`manuscript/RESULTS_TRACEABILITY.md`.

## Classification

**E — based on an obsolete pilot artifact and therefore not applicable to the
final study**, for every concern that treats `results_pilot.parquet` or
`pilot_pass2_*` as evidence about H1/H2/H3. The one exception is the
confidence-definition concern, which is **A — already addressed** (the
"provisional" disclosure it motivated is already in the manuscript). No edit
required beyond this audit document itself.
