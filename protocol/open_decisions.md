# Open decisions and pending work

Everything that must be settled before the full run. Grouped by whether it blocks other
people. Owners follow the table split: Saadat (T1, core pipeline), Sumiya (T2, calibration),
Youssef (T3, robustness factors), Juan (T4, architectures & H2).

Status: `BLOCKER` · `OPEN` · `DONE`

---

## P0 — Blocks everything

### 1. Verify the target actually leaves the sliding window · `DONE` (2026-09-03) · Saadat + Juan

**PASSED with live runtime evidence** — see `protocol/task1_window_verification.md`.
`scripts/diag_ahn_window.py` on a real GatedDeltaNet checkpoint (Colab L4, torch 2.6 /
transformers 4.51 / prebuilt flash-attn): the merged checkpoint reports `sliding_window=256`,
loads as the **custom** `ahn.transformer.qwen2_ahn.Qwen2ForCausalLM` (36 × `Qwen2MemDecoderLayer`,
`.ahn` = `BaseAHN` / `GatedDeltaNet`), `_force_window` makes `effective_window == 256`, and
the AHN recurrent kernel fires **only** when the target is pushed past the window
(`ahn_layer0_num_cached_tokens`: 0 in-window vs 1906 past it; `ahn_kernel_forward_calls`:
0 vs 5). Compression is real and driven by `config.sliding_window = 256`. Two interpretation
notes (the ~49-token offset between `num_cached_tokens` and `expected_recurrent_positions`;
`confidence` on an abstention row) are documented in the verification record — documentation
only, no methodology change.

<details><summary>original blocker text (for the record)</summary>

The research doc commits to *"the inference sliding window deliberately shortened so that
target facts cross into compressed memory after a short, controlled offset"*. It is not clear
the pilot did this, and the evidence suggests it did not:

- AHN trains Qwen2.5-3B with `--sliding_window 256`, but the merged checkpoint loads through
  a stock `Qwen2ForCausalLM`, which carries Qwen2.5's own (much larger) window.
- The longest pilot prompt is 3,303 tokens. If the effective window is 4k or 32k, **every one
  of the 500 rows was answered from exact attention** and nothing was ever compressed.
- The pilot's own numbers fit that reading: 100% accuracy in-window, and a non-monotonic
  curve afterwards (14% at 25 facts, then 38% at 50, 39% at 100, 32% at 200). Genuine memory
  degradation does not recover as pressure increases; distractor interference does behave
  erratically like this.

**Action.** Print `model.config.sliding_window` and `use_sliding_window` on the merged
checkpoint, confirm the AHN path is active, and shorten the window explicitly at inference.
`ahn.models.load` takes `sliding_window=` and `ahn.report.gate_report` fails the run if the
pressure grid never clears it.

Until this is settled, **no pilot number means anything** — the 500 rows may be measuring
prompt length, not memory.

</details>

### 2. Results schema sign-off · `OPEN` · everyone

`src/ahn/schema.py` defines the per-trial contract all three hypotheses read. It was drafted
by one person. Half an hour of review now is cheaper than discovering mid-A40-run that
confidence is on a different scale than H3 expects.

---

## P1 — Blocks a specific hypothesis

| # | Decision | H | Owner | Status |
| --- | --- | --- | --- | --- |
| 3 | **H2 threshold T** from a published paper. Working value 50 facts. Never self-defined — that would force a sensitivity table we have no page budget for. See `h2_threshold.md`. | H2 | Juan | `BLOCKER` |
| 4 | **ECE formula** from a top-venue paper. Guo et al. 2017 (ICML) is already cited in the research doc; confirm bin count and binning strategy against the PDF and freeze them. | H3 | Sumiya | `OPEN` |
| 5 | **CWR threshold** — what confidence counts as *confidently* wrong. Same threshold everywhere. The pilot used 0.5 with no justification. | H3 | Sumiya | `OPEN` |
| 6 | **Confidence definition.** Pilot used full-sequence token probability, which penalises long answers: pilot confidences span 1.8e-06 to 0.99. Decide between sequence probability and length-normalised, apply one everywhere. | H3 | Sumiya | `OPEN` |
| 7 | **Answer matcher per fact type.** ~~Pilot scores `contradictory` at 0% and `temporal` at 90–100%.~~ Root cause was containment scoring + a constant-gold dataset bug. Fixed: constrained short-answer prompt + per-type deterministic canonicalised exact scorer (`evaluate.score_row` / `rescore`), raw generation preserved, `malformed` recorded separately. **Abstention clause reworded 2026-09-03** (see note below) — `not stated above` → `cannot be determined from the statements above`; scorer unchanged. | H1 | Saadat | `DONE` → `evaluate.py`, `config/facts.yaml`, `dataset.py` |
| 8 | **Fact-type taxonomy frozen** — numerical, temporal, entity-attribute, multi-hop, contradictory (research doc, Table 2). | H1 | Saadat | `DONE` → `config/facts.yaml` |
| 9 | **Random seeds.** How many, fixed across models and conditions. The pilot has 100 distinct `seed` values but one item each, so there is no replication and every clustered interval comes back empty. | all | Youssef | `BLOCKER` |
| 10 | **Distractor density** defined quantitatively, not as low/high labels. | all | Youssef | `OPEN` |
| 11 | **`importance` is currently a no-op.** The pilot tags facts high/low but never changes the text, so the variable cannot explain anything. Either manipulate it in the fact wording or drop it. | H1 | Youssef | `OPEN` |
| 12 | **Architecture configs frozen** — Mamba2 / DeltaNet / GatedDeltaNet matched so architecture is the only difference. Juan approved the frozen **matched inference configuration**: `sliding_window = 256`, `sliding_window_type = fixed`, `ahn_position = prefix`, `num_attn_sinks = 0`. The AHN checkpoints ship training-time values (`sliding_window_type`/`ahn_position` = `random`; DeltaNet also ships stale `dy_sliding_window = 2048`, Mamba2/DeltaNet `dy_num_attn_sinks = 128`) — all read only under `if self.training` in `qwen2_ahn.py`, so inert at inference. `models._force_window` now normalises every loaded config to the frozen values and deletes the stale `dy_*` keys; `models.describe` exposes the three fields so `models.assert_matched` enforces them across arms (`tests/test_matched_config.py`). | H2 | Juan | `DONE` → `config/experiment.yaml`, `src/ahnexp/models.py`, `patches/matched-inference-config.patch` |
| 13 | **Length-matched controls.** `tokens_after_target` must not be confounded with total prompt length or with the target landing at the start. The pilot puts the target first in every sequence. | all | Saadat | `OPEN` |

### 7a. Shared abstention clause reworded · `DONE` (2026-09-03) · Saadat

**What changed.** The one line in `dataset._PROMPT` shared by all five fact types:

> ~~If the answer is not stated above, reply with exactly: I don't know~~
> If the answer cannot be determined from the statements above, reply with exactly: I don't know

Nothing else — temporal fact wording, temporal question, every `answer_hint`, the
scorer / canonicalisation, answer spaces, `window = 256`, the matched AHN config,
the pressure grids, and the H1/H2/H3 analyses and confidence computation are
untouched. The literal abstention token string (`I don't know`) is unchanged, so
`evaluate.score_row` recognises abstentions exactly as before (`tests/test_abstention_wording.py`).

**Why.** Staged Pilot Pass 1 (100 trials, `deltanet` + `gated_deltanet`, seed 0)
replicated the mini-grid's n=1 temporal weakness at scale:

| fact type | exact-memory accuracy | exact-memory abstention |
| --- | --- | --- |
| contradictory / entity-attribute / multi-hop / numerical | 1.00 | 0.00 |
| **temporal** | **0.25** | **0.75** |

temporal is the only type whose gold is *entailed* (`Person_1 arrived before
Person_2` ⇒ Person_1 arrived first), not a verbatim span. The old clause was read
as "answer only a span that appears above", so the model emitted the abstention
string on a trivially-entailed answer even with the fact fully in-window and zero
distractors. `malformed = 0` and temporal exact wrong = 0 across the pilot — the
failures were clean `"I don't know"` outputs, not confusion. `cannot be determined
from` licenses a one-step entailment while still permitting abstention once the
fact is compressed away. `report.gate_report` gained a WARN-only
`exact_memory_by_fact_type` check (`a197779`) that flagged this correctly.

**Validation-run status.** The mini-grid (20 trials, `protocol/diag_ahn_window_PASS.json`
context) and staged Pilot Pass 1 (`outputs/results_pilot.parquet`, pre-repair) are
**pre-repair pipeline-validation runs only — not evidence for H1/H2/H3 and not
citable.** The re-pilot under the new wording supersedes them. `require_complete_grid`
comparability means every fact type and every arm is re-run together; no partial
reuse of pre-repair non-temporal data.

**Task #1 artifact.** `protocol/task1_window_verification.md` /
`protocol/diag_ahn_window_PASS.json` are **not** regenerated. The two quoted model
responses there were produced under the prior wording; the recurrent-path
conclusion (the AHN kernel engages only past the window — `ahn_kernel_forward_calls`
0 → 5, `num_cached_tokens` 0 → 1906) is token-count driven and stands unchanged.

### 7b. Temporal question candidate order balanced · `IMPLEMENTED, NOT VALIDATED` (2026-09-03) · Saadat

The forced-baseline diagnostic (`gated_deltanet`, 252 trials) found `dataset.temporal`
always listed the gold (the earlier arriver) **first** in the question, so "pick the
first-listed name" scored 100% with zero reasoning or memory — target-removed forced
accuracy **100% (36/36 first-listed)**. Temporal measured nothing and is **excluded
from evidentiary use** until the repair is validated.

**Repair (commit `03e68f0`).** `temporal(i, swap_candidates=False)` toggles only the
order the two candidates are listed in the question. `generate_items` drives
`swap_candidates` from `(slot // 2) % 2` for temporal items — balanced 50/50 and an
exact 2×2 balance with `distractor_density` (`slot % 2` for temporal), independent of
the gold. Fact text, gold (`Person_i`), `answer_hint`, the scorer (already
order-agnostic), and distractor generation are unchanged. `tests/test_dataset_temporal_order.py`.

**Pending.** The 72-trial temporal validation run (`gated_deltanet`, 12 repaired
temporal items × requested {128, 384, 768} × {present, removed} forced). PASS =
present@128 ≥ 0.85 (construct intact) **and** removed accuracy ∈ [0.30, 0.70] at
every level **and** removed first-listed-choice ∈ [0.30, 0.70] (shortcut killed, no
residual position bias). Then present-vs-removed recurrent Δ places temporal in H1
branch A or B alongside the four validated types.

### 5a. Exact-memory acceptance gate reframe · `PROPOSED, AWAITING JUAN` · Saadat → Juan

`patches/exact-memory-gate-reframe.patch` (not applied). Replaces the pooled
`exact_memory_accuracy` band (`red_flag_at: 0.90` — a benchmark-hardness criterion)
with a **per-fact-type retrievability minimum** (PASS ≥ 0.85 / WARN [0.70, 0.85) /
FAIL < 0.70; no upper bound) plus a **`target_removed_validity`** check fed by the
forced-baseline diagnostic (numerical / entity-attribute / multi-hop / contradictory
= PASS; temporal = PENDING). Pooled exact-memory accuracy → `REPORT`, never gated.
`RED_FLAG` retired from `report.blocking()`. Rationale: the forced-baseline diagnostic
showed exact-memory ≈ 100% with target-removed ≈ 0 is the **ideal** control for a
memory-degradation study; penalising a high, *valid* baseline is backwards, and
pooling hid temporal's 25–50% in-window failure. Approval checklist in
`patches/README.md`.

---

## P2 — Needed before submission, not before running

| # | Item | Owner | Status |
| --- | --- | --- | --- |
| 14 | Full evaluation set size; all tables must use the same underlying set. | Saadat | `OPEN` |
| 15 | Abstention detection — "I don't know" is not the same as retrieving the wrong thing. Pilot does not measure it. | Sumiya | `OPEN` |
| 16 | Second-stage validation on LongBench / LongBench v2, if the synthetic effect holds. | team | `OPEN` |
| 17 | **Chance baseline for the closed-set fact types.** `chance = 0.2` for entity-attribute / multi-hop / contradictory assumes a uniform pick over 5 options, but these are free-response — the model is never shown the options, and collision control removes the gold from the visible context, so the true uninformed rate is unknown and probably < 0.2. **Raw accuracy is the primary H1 metric**; `metrics.chance_corrected_accuracy` output is indicative only until resolved. Options: (A) keep 0.2 with an operational definition; (B) make it explicit 5-way multiple choice; (C) keep free response and measure a null (target-removed) baseline. Not resolved here; do not run the null experiment yet. | H1 | Saadat / team | `OPEN` |

---

## Fixed constraints

These came from the mentor and are not up for renegotiation.

**Accuracy targets.** 70–80% defensible, 85% acceptable upper bound, 90%+ signals the task
is already solved by existing models, 95–99% is indefensible at review. Applies to the
exact-memory control condition. Enforced by `ahn.report.gate_report`.

**Venue.** NAACL industry track: 6 pages, October deadline, 10 exhibits (6 tables + 4
graphs). Gautam adds his name only for the industry track, not the main track. The venue
locks once Tables 1–4 are done; Tables 5–10 get framed to fit afterwards. Framing adapts per
venue; numbers, hyperparameters and methodology stay fixed.

**Pilot compute.** 100–150 samples or 10% of data, on Colab GPU. A40 access is capped at two
days, which is not enough to validate a pipeline. Pilot runs verify plumbing and are never
cited as results. The 500-row pilot is sufficient for interpreting ECE.

**Published sources only** for the H2 threshold and the ECE formula — top-venue, and read
from the PDF rather than a summary.
