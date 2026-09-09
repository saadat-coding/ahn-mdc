# Methods

All numerical statements trace to the locked experiment artifact
(`results_FINAL_92160.parquet`, SHA-256 `a72fd43e…`), the frozen analysis outputs
(version 1.0), or the approved post-freeze reporting amendment (version 1.1;
§2.5). Implementation, validation, and provenance detail omitted here for space is
in `manuscript/METHODS_EXTENDED.md`; per-number sourcing is in
`manuscript/RESULTS_TRACEABILITY.md`. One fact type is called
**compound-relational** throughout; its data key in the released artifact and code
is `multi-hop`, retained unchanged for reproducibility (§2.2).

## 2.1 Experimental setup and architectures

We study how retrieval from an Adaptive Hybrid Neural (AHN) recurrent memory
degrades as the target of a query is pushed out of the model's exact-attention
window, relative to a matched Transformer with no recurrent memory. Three
pre-registered hypotheses were tested:

- **H1 (non-uniform degradation).** Information types do not lose task accuracy at
  the same rate as memory pressure rises.
- **H2 (transition dynamics).** The accuracy collapse is concentrated in a narrow
  pressure region rather than spread gradually, and the AHN recurrent path changes
  where the collapse falls and how much accuracy survives near the window.
- **H3 (behavioural signalling).** As memory degrades, model behaviour
  increasingly signals unreliable memory through abstention rather than confident
  error, more so for AHN than for the no-recurrent-memory baseline.

The base model is `Qwen/Qwen2.5-3B-Instruct`. AHN augments a Transformer with a
fixed-size recurrent state that summarises tokens evicted from a sliding
exact-attention window. We evaluate four arms: the **Transformer baseline** (base
model, no recurrent module, pure truncation past the window) and three **AHN**
arms differing only in the published recurrent mechanism — **AHN-Mamba2**,
**AHN-DeltaNet**, and **AHN-GatedDeltaNet** (checkpoints
`ByteDance-Seed/AHN-{Mamba2,DN,GDN}-for-Qwen-2.5-Instruct-3B`, each the published
module merged onto the base weights). All arms share decoding settings and the
forced window (§2.2); the recurrent mechanism is the only intended difference. The
AHN modules differ in parameter count by ~10% (11.8–13.0 M) and were
self-distilled by the original authors; both are disclosed as confounds ([CITE]).

Design, endpoints, analysis code, evaluation set, prompt, scorer, and window
setting were frozen before the full run (2026-09-05). One reporting metric was
undefined on the collected data and was corrected by a documented post-freeze
amendment that altered no raw evidence and no primary endpoint (§2.5).

## 2.2 Evaluation tasks and memory pressure

**Tasks.** The evaluation set is **240 synthetic items**, generated
deterministically, 48 per fact type, balanced across a low/high distractor-density
factor and three target positions. Each item is one **target sentence** plus a
question over it; distractors never contain the target answer string. The five
fact types: **numerical** (exact digit string), **entity-attribute** (closed
colour set), **contradictory** (closed city set, "lived in X … now lives in Y"),
**temporal** (two-alternative order judgement), and **compound-relational** (closed
company set, "A manages B. B works for C.").

**Compound-relational is not a genuine multi-hop reasoning task.** Its target is a
single co-located two-clause sentence that moves through the context as one span;
answering requires resolving both clauses of that sentence, not retrieving two
facts at different positions. We disclose an in-window difficulty ceiling for it
(Results §3.6). The temporal type has a known directional response preference; its
two nuisance factors are counterbalanced 24/24 against the gold in an exact 2×2×2
design, so the preference nets to chance (Results §3.6).

**Memory pressure.** For every arm the sliding exact-attention window is forced to
**W = 256 tokens** and verified against the checkpoint at load time. **W is an
architectural reference, not a hypothesis about where retrieval fails**; a merged
AHN checkpoint otherwise inherits the base model's much larger native window.
Pressure is applied by inserting a block of whole distractor sentences after the
target and growing it to hit the intended pressure levels; trajectories are nested
(a lower level's block is a prefix of the next level's).

**Prompt and generation.** Every trial uses one frozen prompt template (SHA-256
`5a67ce69…`: context sentences, the question, a one-line per-type answer hint, and
an instruction to reply exactly "I don't know" if the answer is not determinable).
Generation is greedy and deterministic (`max_new_tokens = 12`, stop on newline).
Confidence is the greedy sequence probability (provisional; §2.4).

## 2.3 Scoring and experimental grid

**Outcome classification.** Scoring is a deterministic function of the stored
generation (`evaluate.score_row`, version 1.0). The first non-empty line is
lightly cleaned and each trial is assigned **exactly one** of four outcomes:
**correct** (resolves to a single value equal to the canonical gold);
**incorrect valid answer** (resolves to a single non-gold value); **abstention**
(exactly a recognised "I don't know" form); **malformed** (empty, negation,
longer than four words, or not resolvable to one recognised value).

**Strict production accuracy** is the fraction scored *correct*; **abstentions and
malformed outputs both count as failures**. This is the pre-registered primary
accuracy endpoint for H1 and H2, with no chance correction and no baseline
adjustment. It measures end-to-end task performance and does not separate loss of
the stored value from a tendency to abstain; **answered-valid accuracy** (over
trials that produced a parseable answer) is a pre-registered secondary
sensitivity, never a replacement. Abstention confidence is analysed separately and
never pooled with factual confidence (§2.4).

**Grid.** The full grid is **4 architectures × 240 items × 8 seeds × 12 intended
pressure targets = 92,160 trials**. The 12 intended targets (model tokens) are
`[150, 180, 205, 220, 235, 250, 265, 285, 315, 380, 520, 760]`: two control
anchors (150, 180), six transition targets (205–285), four recurrent anchors
(315–760). They were chosen from architecture geometry, not tuned to any pilot.
The realised artifact is the complete cross-product with no missing or duplicated
cell and a constant scorer and window value (§2.6).

**Pressure coordinate.** Curves and fits use the **realised**
`model_tokens_after_target` — every token after the target span in the tokenised
input. `intended_model_tokens_after_target` is the grouping key only; realised
values track intended closely. Separately, an **empirical performance knee K** is
estimated from the data as the pressure at which pooled strict accuracy crosses
0.5. **K is a descriptive per-run quantity and is not W.** We do not describe the
collapse as occurring "at" a compression threshold and do not describe compression
as "beginning at K".

## 2.4 Statistical analyses

Uncertainty for all primary quantities is a **two-level cluster bootstrap** (2,000
resamples, percentile 95% intervals, deterministic seeding): item clusters (240)
are resampled, then seed realisations within each sampled item, with matched
architecture × pressure rows travelling with their (item, seed) unit. Two-sided
bootstrap p-values are Holm-adjusted within each test family. When 0 of 2,000
resamples exceed the observed statistic the resolution floor is reached and the
p-value is reported as **p < 0.001**.

**H1.** For each fact type, `A_transition` is the mean strict accuracy over
intended transition targets `[205, 220, 235, 250, 265]`, pooling the three AHN
arms (Transformer excluded). The primary test is the 10 pairwise fact-type
differences in `A_transition`; **H1 is supported if at least one Holm-adjusted
interval excludes zero**. A companion omnibus permutes fact-type labels across
items (2,000 permutations) and compares the observed dispersion (SD) of the five
means to the null; with 0 exceedances it reports the add-one–corrected
**p = (0+1)/(2000+1) = 5×10⁻⁴**. Pre-registered sensitivities: exclude temporal;
substitute answered-valid accuracy for all types. A post-freeze sensitivity also
excludes compound-relational.

**H2.** The **architecture endpoint** is `A_transition(AHN pooled) −
A_transition(Transformer)` over the transition interval, paired within (item,
seed). **Shape** is assessed two ways: a smooth log-linear fit compared by AIC
against a fit allowed to change slope at W = 256 (lower change-point AIC =
"concentrated"); and a per-architecture isotonic **transition width**, the token
distance between the 0.90 and 0.10 crossings of a non-increasing isotonic fit to
strict accuracy (**the pre-registered *pooled* width is mathematically undefined
on this dataset**; §2.5). **K** is the isotonic 0.5-crossing of pooled strict
accuracy per architecture (and, separately, of abstention rate). `A_recurrent` is
the mean strict accuracy over intended targets ≥ 315; a deep-regime check
restricts to realised `model_tokens_after_target ≥ 2W` (Wilson interval).

**H3.** Restricted to realised `model_tokens_after_target ≥ W + 16 = 272`:
`appropriate_abstention_rate` = P(abstention) and `unsignalled_failure_rate` =
P(incorrect-valid ∨ malformed), per architecture and as six AHN-minus-Transformer
contrasts (Holm within the family). Secondary calibration (answered-valid trials
only): `gap_change`, the shift in (mean confidence − mean accuracy) from the
control anchors to the transition interval; ECE, Brier score, and a
confidently-wrong rate are descriptive by pressure level. **No mechanistic claim
is made**: the Transformer has no recurrent memory, so the contrast confounds a
recurrent state with the AHN distillation recipe, and whether a behavioural
difference reflects a signal in the recurrent state or a learned abstention policy
cannot be determined here.

## 2.5 Post-freeze H2 reporting amendment (transition width)

The pre-registered *pooled* 90→10 transition-width statistic returned a non-finite
value for every architecture — a metric-definition issue, not a data issue. The
isotonic fit is applied to strict accuracy pooled over all five fact types, and
that pooled curve peaks near 0.88 because the temporal and compound-relational
types abstention-saturate while the target is still in the window; with no point
at or above the 0.90 reference the 0.90 crossing does not exist, and the frozen
code falls through to a default verdict label. The raw per-architecture curves and
the AIC shape test are unaffected.

The correction (approved and implemented 2026-09-09, commit `626521a`;
`protocol/amendment_h2_transition_width.md`) is **reporting-only**. The frozen
all-NaN output is **preserved verbatim** and its verdict label is discarded. The
90→10 width is then computed **per fact type per architecture** and reported only
where the estimator is mathematically defined — **eligibility requires the fitted
isotonic curve to attain a value ≥ 0.90 and a value ≤ 0.10**, a rule derived from
the estimator, not chosen from the observed widths. Eligible for all four arms:
**contradictory, entity-attribute, numerical** (fitted ceilings ≈ 1.0); ineligible:
**compound-relational** (ceiling 0.862) and **temporal** (0.568), each failing
only the upper reference because in-window accuracy is capped by abstention.
Per-type widths use the same hierarchical bootstrap as the other H2 quantities;
the per-architecture summary is the pre-declared **median** of eligible-type
widths.

The amendment touched no raw evidence and changed no design constant (W, K, strict
accuracy, pressure coordinate, grid, seeds, scorer, prompt, dataset). It is
analysis version 1.1, reported alongside the unchanged version 1.0 outputs,
identified as post-freeze wherever it appears, and is not a new frozen primary
endpoint.

## 2.6 Reproducibility and validation (brief)

The raw artifact is content-addressed (SHA-256 `a72fd43e…`). Independent
re-scoring of all 92,160 stored generations with the frozen scorer reproduces the
stored outcome fields with **0 mismatches**; the frozen analysis reproduces from
the locked artifact to ≤ 5.7×10⁻¹⁴ on all 53 audited quantities; the
pre-registered plumbing gates reproduce with 0 blocking failures.

Pre-registered construct and robustness checks (Results §3.6; full detail in
`METHODS_EXTENDED.md`): a per-fact-type in-window **control-validity** gate
(PASS / WARNING / FAIL, a FAIL excluding a type from the H1 primary); temporal
2×2×2 balance; a per-architecture (never pooled) **Transformer malformed-rate**
classification; a **residual in-window failure** analysis (target span
arithmetically inside the lossless window throughout the trial); a
**deep-recurrent** analysis (realised `model_tokens_after_target ≥ 2W`, Wilson
intervals); and per-seed robustness of the headline quantities.

Generation ran on an NVIDIA L4 GPU (Python 3.12, torch 2.6.0). The
generation-runtime commit (`d29c6d8…`) is recorded in the artifact provenance but
absent from the released repository history; its scientifically relevant code is
provably identical to the released design commit (matching scorer output, prompt
hash, calibration hash, and every reproduced analysis quantity), and the gap is
disclosed as a limitation. Frozen v1.0 and v1.1 outputs and per-file hashes are
archived under `final_audit/FINAL_LOCKED/` and `final_audit/V1_1_LOCKED/`.
