# Results

Every numerical statement carries a bracketed identifier (e.g. **[R12]**) traced
in `manuscript/RESULTS_TRACEABILITY.md`. Statistics are from the frozen analysis
(version 1.0) unless marked *post-freeze* (version 1.1; Methods §2.5). Bootstrap
p-values at the 2,000-resample resolution floor (0 exceedances) are reported as
**p < 0.001**; the H1 omnibus permutation test reports its add-one–corrected
value.

## 3.1 Experiment integrity

**[R1]** The locked artifact is the complete 4 architectures × 240 items × 8 seeds
× 12 intended pressure targets = 92,160-trial cross-product, 23,040 per
architecture, with no missing or duplicated cell. **[R2]** Independent re-scoring
of all 92,160 generations reproduced the recorded outcomes with 0 mismatches, and
the frozen analysis reproduced on all 53 audited quantities to ≈ 5.7 × 10⁻¹⁴
(Appendix A-REPRO).

**[R3]** With the target inside the exact-attention window (intended targets 150,
180), pooled strict production accuracy is ≈ 0.88 for every architecture; **[R4]**
by type it is ≥ 0.99 for numerical, contradictory, and entity-attribute, and lower
for compound-relational (0.84) and temporal (0.57, with a 0.38 abstention rate)
(Table 4). **[R5]** Realised `model_tokens_after_target` matches each intended
target to within a few tokens (Figure D).

## 3.2 H1 — Information types degrade non-uniformly

**Status: SUPPORTED** (claims register H1-1; ordering H1-2 partially supported).

The primary endpoint `A_transition` is the mean raw strict production accuracy over
intended transition targets 205–265, AHN arms pooled (Methods §2.4; n = 5,760 per
fact type).

**[R6]** The five `A_transition` values span a wide range: compound-relational
0.255, temporal 0.307, numerical 0.389, contradictory 0.520, entity-attribute
0.594 (Table 1, Figure 1). **[R7]** The label-permutation omnibus on the
dispersion of these means gives p = 5 × 10⁻⁴ (0 of 2,000 permutations reached the
observed SD of 0.127; add-one–corrected). **[R8]** All 10 pairwise fact-type
differences have Holm-adjusted 95% bootstrap intervals excluding zero; the
smallest is compound-relational versus temporal (−0.052, 95% CI [−0.099, −0.003],
Holm p = 0.037), and the other nine have Holm p < 0.001 (Table 2). The
pre-registered criterion for H1 is met.

**Ordering.** Compound-relational degrades fastest and entity-attribute is most
robust. **[R9]** The middle ranks are closer and partly metric-dependent: under
answered-valid accuracy the per-type values are compound-relational 0.669,
contradictory 0.817, numerical 0.824, entity-attribute 0.910, temporal 0.925, and
2 of the 10 contrasts (contradictory–numerical, entity-attribute–temporal) lose
Holm significance (Table 1; Appendix A-H1) — though compound-relational stays
lowest and entity-attribute among the highest under both metrics. **[R12]** The
ordering is identical in 7 of 8 seeds (the two lowest-ranked types swap in one
seed); per-type `A_transition` varies by ±0.03–0.05 across seeds.

**Sensitivities (Appendix A-H1).** **[R10]** Excluding temporal, all 6 remaining
contrasts stay Holm-significant. **[R11]** Excluding compound-relational
(*post-freeze*), all 6 remaining contrasts stay Holm-significant and the omnibus
over the four remaining types gives p = 5 × 10⁻⁴.

Because the strict metric counts abstention and malformed output as failure,
`A_transition` measures end-to-end task-performance degradation, not how much of
the target value remains recoverable from the model's state. **[R13]** The two
lowest-ranked types are also the two with elevated in-window abstention
(compound-relational 0.115, temporal 0.384; Table 4), so part of their low
`A_transition` is a greater tendency to abstain under pressure; the answered-valid
sensitivity is reported alongside the primary for this reason.

## 3.3 H2 — Transition dynamics under memory pressure

**Status: SUPPORTED** for the near-window architecture advantage (H2-1) and for a
concentrated, non-gradual collapse (H2-2); the pre-registered *pooled*
transition-width statistic was **UNDETERMINED** (H2-3), addressed by a post-freeze
reporting amendment.

### Near-window architecture advantage

**[R14]** Over the transition interval [200, 270], the three AHN architectures
retain **+0.249** more strict accuracy than the no-recurrent-memory baseline
(pooled AHN minus Transformer; 95% CI [0.233, 0.266]; positive in every seed)
(Figure 2, Table 3). **[R15]** At intended target 220, pooled AHN strict accuracy
is 0.44–0.51 versus 0.18 for the baseline; at 235, 0.51–0.56 versus 0.03. Part of
the gap is the baseline degenerating rather than abstaining (§3.6, VAL-3).

### Location of the knee: K is below W

**[R16]** The empirical performance knee K (isotonic 0.5-crossing of pooled strict
accuracy) is 208.3 for the baseline (95% CI [207.1, 209.5]) and 218.4, 219.6, and
240.0 for AHN-DeltaNet, AHN-Mamba2, and AHN-GatedDeltaNet (Table 3, Figure 2).
**[R17]** Every K lies **below** the architectural window reference W = 256.
**[R18]** The AHN knees are less precisely located than the baseline knee —
bootstrap intervals wide and asymmetric (e.g. AHN-GatedDeltaNet [220.4, 243.9]),
across-seed spread 21–29 tokens versus 1.9 for the baseline (Appendix A-H2a) — so
we report the AHN knee as a range (≈ 218–240) and claim no ordering among the AHN
knees. **[R19]** The abstention knee is far earlier for AHN (247–251) than for the
baseline (≈ 422): the AHN arms begin abstaining around the window while the
baseline keeps emitting answers well past it.

### Shape of the collapse

Performance degradation was **concentrated rather than gradual**, although
transition sharpness differed by architecture.

**[R20]** *Frozen change-point evidence.* An AIC comparison favours a slope change
at W = 256 over a smooth fit for all four architectures, but the margin differs
sharply: ΔAIC ≈ −0.7 for the baseline versus −2.6 to −8.3 for the AHN arms
(Table 3).

**[R21]** *Frozen pooled width.* The pre-registered pooled 90→10 transition-width
statistic is mathematically undefined here — the five-type pooled strict-accuracy
curve peaks at ≈ 0.88, below the 0.90 reference — so the frozen output is
non-finite for every architecture; it is preserved unchanged and not interpreted
(Methods §2.5, Appendix A-H2a).

**[R22]** *Post-freeze per-type width characterization.* For the three fact types
where the 90→10 width estimator is defined (contradictory, entity-attribute,
numerical — fitted curve attains ≥ 0.90 and ≤ 0.10), the per-architecture median
width is **32.4 model tokens** for the baseline (95% CI [30.5, 36.8]) and **61.8,
71.4, and 73.8** for AHN-GatedDeltaNet, AHN-DeltaNet, and AHN-Mamba2 (individual
eligible-type widths 29–77 tokens). **[R23]** Every width is well below half the
window (128 tokens), and the baseline transition is narrower than every AHN
transition in every seed (Appendix A-H2a). Compound-relational and temporal are
ineligible (fitted ceilings 0.862, 0.568), not because their transition is wide.

Both views agree the collapse is concentrated, and both show the **Transformer
transition is narrower and earlier than the AHN transitions**: the baseline fails
sooner and more abruptly (K ≈ 208, median width ≈ 32 tokens), while the AHN arms
preserve useful strict accuracy farther through the near-window region (K ≈
218–240) and degrade across a broader interval (median width ≈ 62–74 tokens). AHN
does not simply shift the Transformer cliff to the right. This is reported as
observed task-performance dynamics, not a mechanistic property of recurrent
memory.

### Near-zero retrieval accuracy beyond the window

**[R24]** Past the window, strict accuracy is indistinguishable from zero for all
four architectures: `A_recurrent` (mean strict accuracy over intended targets
≥ 315) is 0.0001–0.005 with bootstrap intervals reaching zero (Table 3), and every
per-architecture accuracy point at intended targets ≥ 285 is ≤ 0.013 (Figure 2
source). The deeper regime is reported in §3.5.

**[R25]** The knee is not the window, and the transition is not a clean
exact-to-compressed switch: every K (208–240) lies below W (256), and about 32%
of trials whose target span is arithmetically inside the lossless window for the
whole trial still fail (§3.6, VAL-4). Pressure-related deterioration begins before
the binary exact-to-compressed boundary alone can explain it; no mechanism is
claimed here.

## 3.4 H3 — Behavioural signalling of memory unreliability

**Status: SUPPORTED** for behavioural signalling (H3-1, H3-2); **PARTIALLY
SUPPORTED** for factual calibration (H3-3).

Past the sliding-window reference (realised `model_tokens_after_target` ≥ 272;
n ≈ 10,091 per architecture), the principal difference between AHN and the
Transformer control is **failure mode**, not sustained factual retrieval (§3.5).

**[R26]** The appropriate-abstention rate (fraction of trials that are
abstentions) is 0.946, 0.945, and 0.929 for AHN-DeltaNet, AHN-Mamba2, and
AHN-GatedDeltaNet, versus **0.516** for the baseline (Figure 3). **[R27]** The
unsignalled-failure rate (incorrect valid answer or malformed output) is 0.054,
0.052, and 0.071 for the AHN arms versus **0.480** for the baseline. **[R28]** All
six AHN-versus-baseline contrasts (three architectures × two rates) have
magnitudes 0.41–0.43 with Holm p < 0.001. **[R29]** The per-architecture
appropriate-abstention rate is stable across seeds (AHN 0.92–0.95, baseline
0.49–0.53 in every seed; Appendix A-H3).

**[R30]** The baseline's past-window behaviour is 0.52 abstention, 0.45 malformed
output, 0.03 incorrect valid answer, < 0.01 correct (Figure 3 source); the AHN
arms are almost entirely abstention, with 0.04–0.07 incorrect valid answers and
≤ 0.007 malformed. The unsignalled-failure gap is therefore mostly the baseline
producing degenerate output where the AHN arms abstain.

**Factual calibration on answered trials (secondary).** **[R31]** On answered-valid
trials, the change in the (confidence − accuracy) gap from the control anchors to
the transition interval is −0.018 for the baseline (95% CI [−0.051, 0.013],
containing zero) and −0.063, −0.108, and −0.115 for the AHN arms (intervals
excluding zero): in the transition the AHN arms become more conservative while the
baseline does not shift. **[R32]** On the small subpopulation of past-window
trials where a model still answers (answered-valid n = 853 pooled at intended
target 265, baseline contributing 1), calibration is poor for all architectures
(gap ≈ +0.53, confidently-wrong rate 0.92–0.98) — fewer than 5% of past-window
trials, where the dominant behaviour is abstention.

The Transformer has no recurrent memory, so this contrast confounds a recurrent
state with the AHN distillation recipe; whether the behaviour reflects a signal
carried in the recurrent state or a learned abstention policy cannot be determined
from this design (claims register H3-4).

## 3.5 Deep-recurrent regime

**Status: NEGATIVE RESULT** (claims register H2-5). *(Post-freeze sensitivity;
Table 5.)*

**[R33]** Restricted to realised `model_tokens_after_target` ≥ 2W (512), with
3,542 trials per architecture, the correct counts are 0 (AHN-DeltaNet), 0
(AHN-GatedDeltaNet), 1 (AHN-Mamba2), and 3 (baseline). **[R34]** The Wilson 95%
upper bounds on accuracy are ≤ 0.0011 (AHN-DeltaNet, AHN-GatedDeltaNet), 0.0016
(AHN-Mamba2), and 0.0025 (baseline). **[R35]** Abstention exceeds 0.89 for all
four architectures in this regime (AHN ≈ 0.98). **[R36]** No fact type shows
retention; the single AHN-Mamba2 correct trial is a temporal (two-alternative)
item.

No measurable target-specific factual retention was observed at deep recurrent
pressure under the production evaluation.

## 3.6 Robustness and construct-validity findings

**Temporal construct (VAL-1).** **[R37]** The temporal 2×2×2 nuisance design is
exactly balanced (24/24 per factor; 6 items per cell). **[R38]** At the control
anchors, answered-valid accuracy differs by nuisance subgroup — 0.849 (gold
lower-numbered) vs 0.992 (gold higher-numbered), and 0.868 (gold not first-listed)
vs 1.000 (gold first-listed) — a documented directional response preference that
the counterbalancing nets to chance (pooled control answered-valid accuracy 0.922;
Appendix A-VAL). The temporal benchmark is a balanced order-retrieval task; its
raw strict accuracy is abstention-dominated, so its H1 rank is read with the
answered-valid sensitivity.

**Compound-relational construct (VAL-2).** **[R39]** In-window retrieval reaches
0.842 strict (0.951 among answered trials), with 0.115 abstention and 0 malformed.
**[R40]** This triggers the pre-registered control-validity WARNING (strict < 0.85
and abstention > 0.10); the FAIL threshold (0.70) is not reached, so the type is
retained in the H1 primary (Table 4). **[R41]** The WARNING holds in 7 of 8 seeds,
and only 2 of 48 items have control strict accuracy below 0.5 (Appendix A-VAL).
This is a task-difficulty ceiling for a co-located two-clause target, not a memory
or pipeline fault; the compound-relational type is not a multi-hop reasoning
benchmark.

**Transformer control behaviour (VAL-3).** **[R42]** The Transformer arm produces
malformed output on 39.6% of its trials overall, versus 1.4–4.8% for the AHN arms
on byte-identical prompts. **[R43]** Its malformed rate is 0.0% at the in-window
control anchors, rises to 18–79% across the transition and early-recurrent targets
(205–380), and falls to 3–10% at the deepest targets. **[R44]** By subtype the
malformed outputs are over-length (4,580), unrecognised value (2,241), empty
(1,488), and negation (813), spread across all items and seeds. The concentration
of malformed outputs at higher pressure levels, with their near-absence at the
control anchors, supports treating this as control behaviour rather than pipeline
corruption; the pre-registered gate classifies it as such. **[R45]** The
pooled-across-architecture malformed rate (12.6%) is reported only alongside the
per-architecture split, never alone.

**Residual in-window failures (VAL-4).** **[R46]** For the 34,975 trials whose
target span is arithmetically inside the lossless window for the whole trial,
32.1% still fail (46% abstentions, 39% malformed, 15% incorrect valid answers)
(Appendix A-H2b). **[R47]** This rate is 12% at intended targets 150 and 180 but
rises to 34%, 60%, and 55% at intended targets 205, 220, and 235 (30–34% across
all seeds). **[R48]** By fact type it is 12% (entity-attribute), 23%
(contradictory), 34% (numerical), 41% (compound-relational), and 52% (temporal).
Retrieval begins to fail at pressure levels where the target span is still
nominally within exact attention; the pressure axis is a proxy for compression
pressure, and near-window degradation is not attributable solely to the
exact-to-compressed transition. No mechanism is claimed.

**[R49]** The pre-registered plumbing gates reproduce with 0 blocking failures;
the Transformer malformed behaviour is flagged as control behaviour and the
compound-relational control validity is flagged WARNING, as above (Appendix
A-REPRO).
