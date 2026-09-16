# Methods (Extended / Supplementary)

This is the full reproducibility version of the Methods. The main-paper Methods
(`manuscript/METHODS.md`) is a condensed form of this document; every design
choice, threshold, and provenance detail below is preserved here. Section
numbering (2.1–2.14) is retained for cross-reference. Nothing in this file is a
new analysis; it is the frozen protocol as executed.

All statements trace to the locked experiment artifact
(`final_audit/FINAL_LOCKED/results_FINAL_92160.parquet`, SHA-256
`a72fd43e87457a70c2833314e1443a794fa4189362ac8206c56275ef427fb62e`), the frozen
analysis outputs (`final_audit/FINAL_LOCKED/final_*`, analysis version 1.0), the
approved post-freeze reporting amendment
(`outputs/final_v1_1_reporting_amendment/`, analysis version 1.1), and the frozen
configuration and code. Numerical statements in this section are cross-referenced
in `manuscript/RESULTS_TRACEABILITY.md`.

Terminology note: one information type is referred to throughout the manuscript as
**compound-relational**. Its data key in the released artifact and code is
`multi-hop`; the key is retained for reproducibility and is not a claim about the
task (§2.4).

## 2.1 Research questions and hypotheses

We study how retrieval from an Artificial Hippocampus Network (AHN) recurrent memory
degrades as the target of a query is pushed out of the model's exact-attention
window, relative to a matched Transformer that has no recurrent memory. Three
pre-registered hypotheses were tested.

- **H1 (non-uniform degradation).** Different information types do not degrade at
  the same rate as memory pressure rises.
- **H2 (transition dynamics).** The retrieval-accuracy collapse is concentrated in
  a narrow pressure region rather than spread gradually, and the AHN recurrent
  path changes where the collapse occurs and how much accuracy survives near the
  window.
- **H3 (behavioural signalling).** As memory degrades, the model's behaviour
  increasingly signals that its memory is unreliable (through abstention rather
  than confident error), more so for AHN than for the no-recurrent-memory
  baseline.

The design, endpoints, analysis code, evaluation set, prompt, scorer, and the
sliding-window setting were frozen before the full run (frozen 2026-09-05;
`config/experiment.yaml` `final:` block; `config/final_design_manifest.json`;
`protocol/final_experiment_design.md`). One reporting metric was undefined on the
collected data and was corrected by a documented post-freeze amendment that did
not alter any raw evidence or any primary endpoint (§2.12).

## 2.2 AHN architectures and Transformer control

The base model is `Qwen/Qwen2.5-3B-Instruct`. AHN augments a Transformer with a
fixed-size recurrent state that summarises tokens evicted from a sliding
exact-attention window; the recurrent update is one of three published
mechanisms. We evaluate four arms:

| arm (manuscript) | recurrent mechanism | checkpoint | recurrent-module parameters |
|---|---|---|---|
| AHN-Mamba2 | Mamba2 | `ByteDance-Seed/AHN-Mamba2-for-Qwen-2.5-Instruct-3B` | 11.9 M |
| AHN-DeltaNet | DeltaNet | `ByteDance-Seed/AHN-DN-for-Qwen-2.5-Instruct-3B` | 11.8 M |
| AHN-GatedDeltaNet | GatedDeltaNet | `ByteDance-Seed/AHN-GDN-for-Qwen-2.5-Instruct-3B` | 13.0 M |
| Transformer (baseline) | none | base model, no AHN module | 0 |

Each AHN checkpoint is the published recurrent module merged onto the base
weights. The Transformer arm is the identical base model with the same forced
sliding-window setting (§2.3) and no recurrent module; past the window it has no
mechanism to access evicted tokens (pure truncation). All arms share
`torch_dtype = float16`, `attn_implementation = sdpa`, `ahn_position = prefix`,
`sliding_window_type = fixed`, and the decoding configuration in §2.5; the
recurrent mechanism is the only intended difference. The AHN parameter counts
differ by ~10% and the modules were self-distilled by the original authors; both
are disclosed as confounds \citep{ahn2025}.

## 2.3 Memory-pressure experimental design

For every arm the model's sliding exact-attention window is forced to
**W = 256 tokens** and verified against the checkpoint at load time. **W is an
architectural reference, not a hypothesis about where retrieval fails.** A merged
AHN checkpoint otherwise inherits the base model's much larger native window, so
without this setting the target would never leave exact attention.

Memory pressure is applied by placing a block of distractor sentences after the
target sentence, so that increasing the block size pushes the target further out
of the exact window. The block is composed of whole distractor sentences drawn
from a per-item pool of 4,000 (§2.4); it is grown to hit a set of intended
pressure levels (§2.8). Trajectories are nested: for a given item and seed, the
distractor block at a lower pressure level is a prefix of the block at the next
level.

## 2.4 Evaluation dataset and information types

The evaluation set is 240 synthetic items, generated deterministically (seed 0),
48 per information type, balanced 120/120 across a low/high distractor-density factor and
across three target positions. Distractors never contain the target's answer
string (collision control). Each item is a single **target sentence** plus a
question over that sentence. The five information types:

| information type (manuscript) | data key | answer form | target / query example |
|---|---|---|---|
| numerical | `numerical` | exact digit string | "Person_0's employee ID is 100000." / "What is Person_0's employee ID?" |
| entity-attribute | `entity-attribute` | closed set (5 colours) | "Person_0's favourite colour is blue." / "…favourite colour?" |
| contradictory | `contradictory` | closed set (cities) | "Person_0 lived in Paris. Person_0 now lives in London." / "…where do they live now?" |
| temporal | `temporal` | one of two named entities | "Person_0 arrived before Person_1." / "Who arrived first?" |
| compound-relational | `multi-hop` | closed set (5 companies) | "Person_3 manages Person_4. Person_4 works for Google." / "Which company does Person_3's subordinate work for?" |

**Compound-relational is not a multi-hop reasoning benchmark.** Its target is one
co-located two-clause sentence ("A manages B. B works for C.") that moves through
the context as a single span; the query requires both clauses of that one
sentence, not retrieval of two facts at different positions. We report it as a
compound-relational retrieval task and disclose an in-window difficulty ceiling
(§2.13, Results §3.6).

The temporal type is a two-alternative choice. Its two nuisance factors — whether
the gold entity is the higher-numbered person, and whether it is listed first in
the question — are assigned from a density-stratified, seed-shuffled plan that
balances them 24/24 against the gold and produces an exact 2x2x2 design (6 items
per cell). The model has a documented directional response preference (favouring
the lower-numbered / first-listed candidate) that this counterbalancing nets to
chance; it is reported, not engineered away (§2.13; see the temporal-repair
validation record in `protocol/temporal_repair_validation.md`).

## 2.5 Prompting and generation

Every trial uses one frozen prompt template (SHA-256 of the template plus the
per-type answer hints: `5a67ce69…`, recorded in the design manifest). The
template lists the context sentences, states the question, appends a one-line
per-type answer hint ("Reply with only the …"), and instructs the model to reply
with exactly "I don't know" if the answer cannot be determined from the context.
The prompt is wrapped in the model's chat template.

Generation is greedy and deterministic: `do_sample = False`, `num_beams = 1`,
`max_new_tokens = 12`, stop on newline. Confidence for a generation is its
sequence probability (product of greedy token probabilities); this choice is
provisional (§2.11).

## 2.6 Pressure coordinates and the sliding-window reference

We distinguish three quantities.

- **`model_tokens_after_target`** (the pressure coordinate): every token after the
  target span in the tokenised model input — distractors plus the question and
  instruction block plus the chat-template suffix. Curves are plotted and fits are
  computed against this realised coordinate.
- **`intended_model_tokens_after_target`** (the grouping key): the pressure level a
  trajectory was calibrated to hit. Because per-information-type prompt overhead differs
  by ~10 tokens, each intended level maps to a different requested distractor-token
  count per information type; calibration was performed with the base tokenizer and no
  model, and realised values track intended values closely (§2.8, Figure D).
- **W = 256**: the architectural sliding-window reference.

Separately, an **empirical performance knee K** is estimated from the data (§2.10)
as the pressure at which pooled strict accuracy crosses 0.5. **K is a descriptive
per-run quantity and is not equal to W.** We do not describe the collapse as
occurring "at" a compression threshold, and we do not describe compression as
"beginning at K".

## 2.7 Answer scoring and output classification

Scoring is a pure deterministic function of the stored raw generation
(`evaluate.score_row`, scorer version 1.0). The first non-empty line of the
generation is cleaned (a leading "the answer is" label and wrapping punctuation
removed). Each trial is assigned **exactly one** of four outcomes:

- **abstention** — the cleaned response is exactly a recognised "I don't know"
  form.
- **malformed** — the cleaned response is empty, contains a negation, is longer
  than four words, or does not resolve to exactly one recognised value for the
  information type (this also catches a bare mention of the gold, a question echo, and
  multiple competing candidates).
- **correct** — the response resolves to a single value and that value equals the
  canonicalised gold.
- **incorrect valid answer** — resolves to a single value that is not the gold.

**Strict production accuracy** is the fraction of trials scored *correct*.
Abstentions and malformed outputs both count as failures. This is the
pre-registered primary accuracy endpoint for H1 and H2; there is no chance
correction and no baseline-adjusted primary (`config/facts.yaml`;
`protocol/final_experiment_design.md` §5). It is a measure of end-to-end task
performance, and it deliberately does not attempt to isolate representational
information loss from a model's tendency to abstain. Where relevant we also report
**answered-valid accuracy** — accuracy computed only over trials that produced a
parseable answer (correct or incorrect valid) — as a secondary, pre-registered
sensitivity, never as a replacement for the primary.

For calibration analyses (§2.11) the confidence of a *correct/incorrect-valid*
response is treated as factual confidence, and the confidence of an *abstention*
response (confidence in emitting "I don't know") is analysed separately and never
pooled with factual confidence.

## 2.8 Experimental grid and replication

The full grid is **4 architectures × 240 items × 8 seeds × 12 intended pressure
targets = 92,160 trials**. The 12 intended targets are
`[150, 180, 205, 220, 235, 250, 265, 285, 315, 380, 520, 760]` model tokens,
grouped as two control anchors (150, 180), six transition targets
(205–285), and four recurrent anchors (315–760). A seed controls only distractor
sampling and ordering; given (architecture, item, seed, intended target) a
trajectory is fully determined, so replication across seeds is independent. The
grid and the target set were chosen from architecture geometry (window size, the
observed maximum target span, and the generation length), not tuned to any pilot
result.

The realised artifact is complete and internally consistent: 92,160 rows, exactly
23,040 per architecture, the full 4 × 240 × 8 × 12 cross-product with no missing
and no duplicated cell, a constant scorer version and sliding-window value, and no
missing values in any scored field (§2.14).

## 2.9 H1 analysis

**Endpoint.** For each information type, `A_transition` is the mean strict production
accuracy over the five intended transition targets `[205, 220, 235, 250, 265]`,
pooling the three AHN architectures; the Transformer is a reference curve and is
excluded from the pooled endpoint. `A_transition` was computed only for information types
that passed the pre-registered in-window control-validity check (§2.13); all five
types passed the retain-in-primary threshold.

**Test.** The primary test is the set of 10 pairwise information-type differences in
`A_transition`. Uncertainty is a two-level cluster bootstrap: item clusters (240)
are resampled with replacement, then seed realisations are resampled within each
sampled item; matched architecture × pressure rows travel with their (item, seed)
unit. 2,000 resamples, percentile 95% intervals, deterministic seeding. Two-sided
bootstrap p-values are adjusted by Holm within the 10-comparison family. **H1 is
supported if at least one Holm-adjusted interval excludes zero.** A companion
omnibus test permutes the information-type labels across items (2,000 permutations) and
compares the observed dispersion (standard deviation) of the five `A_transition`
means to the permutation null.

**Pre-registered sensitivities:** (a) repeat the analysis excluding the temporal
type; (b) repeat with answered-valid accuracy substituted for all types. A
post-freeze sensitivity (§2.12) additionally repeats the analysis excluding the
compound-relational type. Per-seed `A_transition` values are reported for
robustness.

## 2.10 H2 analysis

**Pre-registered shape endpoint.** The pre-registered primary shape statistic is a
per-architecture isotonic transition **width**: fit a non-increasing (pool-adjacent
-violators) isotonic curve to pooled strict accuracy against realised
`model_tokens_after_target` (one balanced cell per intended target), and take the
token distance between where the fit crosses 0.90 and where it crosses 0.10, with
a hierarchical bootstrap interval. **This statistic is mathematically undefined on
the collected data** (the pooled five-type accuracy curve does not reach 0.90;
§2.12). The frozen output is preserved unchanged and is not interpreted; the shape
question is addressed instead by the amendment in §2.12 and by two auxiliary
frozen analyses:

- **Shape test.** A smooth log-linear fit is compared, by AIC, with a fit allowed
  to change slope at W = 256. A lower AIC for the change-point fit is reported as
  "threshold-like".
- **Empirical knee K.** The isotonic 0.5-crossing of pooled strict accuracy per
  architecture, with a hierarchical bootstrap interval; and, separately, the
  isotonic 0.5-crossing of abstention rate.

**Architecture endpoint.** `A_transition(AHN pooled) − A_transition(Transformer)`
over the transition interval [200, 270], with a hierarchical bootstrap interval
(paired within (item, seed)).

**Recurrent-regime accuracy.** `A_recurrent` is the mean strict accuracy over
intended targets ≥ 315, per architecture, with a hierarchical bootstrap interval;
and a deep-regime check restricts to realised `model_tokens_after_target ≥ 2W`
(512) with an exact Wilson interval on the binomial (§2.13).

## 2.11 H3 analysis

**Behavioural primary.** Restricted to trials with realised
`model_tokens_after_target ≥ W + 16 = 272`:

- `appropriate_abstention_rate` = P(the trial is an abstention);
- `unsignalled_failure_rate` = P(the trial is an incorrect valid answer or a
  malformed output).

Both rates are reported per architecture with hierarchical bootstrap intervals,
and as six contrasts (each AHN architecture minus the Transformer, on both rates),
with Holm adjustment within the 6-contrast family. Per-seed rates are reported for
robustness.

**Secondary calibration.** On answered-valid trials only, `gap_change` is the
change in (mean confidence − mean accuracy) from the pooled control anchors
{150, 180} to the transition interval [200, 270], per architecture, with a
hierarchical bootstrap interval. Expected calibration error (10 equal-width bins),
Brier score, and a confidently-wrong rate (confidence threshold 0.5, provisional)
are reported descriptively by pressure level on answered-valid trials. Confidence
on abstention responses is reported in a separate table and is never treated as
factual confidence. The sequence-probability confidence measure is provisional; a
length-normalised sensitivity is noted as future work.

**No mechanistic claim.** The Transformer arm has no recurrent memory, so the
architecture contrast confounds the presence of a recurrent state with the
recurrent-module distillation recipe. Any behavioural difference is reported as a
description of behaviour; whether it reflects a signal carried in the recurrent
state or a learned abstention policy cannot be determined from this design and is
stated as a limitation.

## 2.12 Post-freeze reporting amendment (H2 transition width)

The pre-registered pooled 90→10 transition-width statistic (§2.10) returned a
non-finite value for every architecture. The cause is a metric-definition issue,
not a data issue: the isotonic fit is applied to strict accuracy pooled over all
five information types, and that pooled curve peaks near 0.88 because the temporal and
compound-relational types abstention-saturate while the target is still inside the
window (temporal ≈ 0.38 in-window abstention; compound-relational ≈ 0.12). With no
point at or above 0.90, the 0.90 crossing does not exist, and the frozen
implementation then falls through to a default verdict label. The raw
per-architecture accuracy curves and the AIC shape test are unaffected.

The correction (approved 2026-09-09; implemented at commit `626521a`;
`protocol/amendment_h2_transition_width.md`) is a **reporting-only** change:

1. The frozen output (`final_h2_h2_width.csv`, all-NaN) is preserved verbatim and
   is reported as the record; the default verdict label is not used.
2. The 90→10 width is computed **per information type per architecture**, and reported
   only for information types where the estimator is mathematically defined —
   **eligibility requires the fitted isotonic curve to attain a value ≥ 0.90 and a
   value ≤ 0.10**. This rule is derived from the estimator, not chosen from the
   observed widths.
3. Eligible for all four architectures: **contradictory, entity-attribute,
   numerical** (fitted ceilings 1.000, 1.000, 0.999). Ineligible:
   **compound-relational** (fitted ceiling 0.862) and **temporal** (0.568); both
   fail only the upper reference, because their in-window accuracy is capped by
   abstention.
4. Per-information-type widths use the same hierarchical (item → seed) bootstrap as the
   other H2 quantities (2,000 resamples). A per-architecture cross-type summary is
   the **median** of the eligible-type widths (a fixed choice: robust to a single
   anomalous type, appropriate for a small discrete set, no equal-precision
   assumption).

This amendment did not touch the raw artifact, did not change any primary
endpoint, and did not change W, K, strict accuracy, the pressure coordinate, the
grid, the seeds, the scorer, the prompt, or the dataset. It is reported as
analysis version 1.1 alongside the unchanged version 1.0 outputs, and is
identified as post-freeze wherever it appears.

## 2.13 Robustness and construct-validity analyses

- **Per-information-type control validity.** For each information type, retrieval on the pooled
  control anchors (intended 150 and 180) is checked against pre-registered
  floors: for non-temporal types, PASS at strict accuracy ≥ 0.85, WARNING in
  [0.70, 0.85) or with abstention > 0.10 or malformed > 0.05, FAIL (benchmark
  invalid, excluded from the H1 primary) below 0.70; temporal is judged on
  answered-valid accuracy (PASS ≥ 0.85) instead of strict accuracy, with
  abstention assessed separately against its own preregistered WARNING
  interval of [0.40, 0.60] rather than the > 0.10 threshold used for
  non-temporal types (`config/experiment.yaml acceptance.control_validity`,
  `full_run.control_validity`; §3.6 [R52]).
- **Temporal counterbalancing.** The 2x2x2 nuisance design is verified balanced in
  the final item set, and answered-valid accuracy and abstention are reported by
  nuisance subgroup at the control anchors.
- **Transformer control behaviour.** The Transformer malformed rate is reported
  per architecture (never pooled across architectures) and by pressure level, with
  a malformed-subtype breakdown, and is classified against a pre-registered gate.
- **Residual in-window failures.** For the subset of trials in which the target
  span is arithmetically inside the lossless window for the whole trial
  (`model_tokens_after_target + target span + generated tokens ≤ W`), the failure
  rate is reported, stratified by information type, architecture, intended target, and
  seed.
- **Deep-recurrent retention.** Restricted to realised
  `model_tokens_after_target ≥ 2W` (512), correct counts, denominators, and Wilson
  95% intervals are reported per architecture and per information type.
- **Per-seed robustness.** `A_transition` per information type, K per architecture, and
  the H3 appropriate-abstention rate per architecture are reported for each of the
  8 seeds.

## 2.14 Reproducibility and provenance

The raw artifact is content-addressed: SHA-256
`a72fd43e87457a70c2833314e1443a794fa4189362ac8206c56275ef427fb62e`. Independent
re-scoring of all 92,160 stored generations with the frozen scorer reproduces the
stored `correct` / `abstained` / `malformed` fields with **0 mismatches**. The
frozen analysis (version 1.0) reproduces from the locked artifact to within
floating-point tolerance on all 53 audited quantities (maximum absolute difference
≈ 5.7 × 10⁻¹⁴). The pre-registered plumbing gates reproduce with 0 blocking
failures.

Generation ran on an NVIDIA L4 GPU with Python 3.12, torch 2.6.0+cu126,
transformers 4.51.0, flash-attn 2.8.3.post1, mamba-ssm 2.2.5. The exact
generation-runtime commit (`d29c6d8…`) is recorded in the artifact provenance but
is not present in the released repository history. Multiple equivalence and
reproduction checks — the scorer output, the prompt hash, the calibration hash,
and every reproduced analysis quantity — found no evidence of a scientifically
relevant discrepancy between the runtime code and the released design commit. This
provenance gap is disclosed as a limitation. The design commit,
frozen analysis outputs, the post-freeze amendment outputs, and per-file hashes
are archived in `final_audit/FINAL_LOCKED/` (frozen v1.0) and
`final_audit/V1_1_LOCKED/` (amendment v1.1).
