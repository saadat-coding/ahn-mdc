# Results

Every numerical statement carries a bracketed identifier (e.g. **[R12]**) and is
traced to its source in `manuscript/RESULTS_TRACEABILITY.md`. Statistics come
from the frozen analysis (version 1.0) unless marked *post-freeze* (version 1.1;
§Methods 2.12). Exhibits are as specified in `protocol/final_exhibit_plan.md` and
built by `scripts/build_publication_exhibits.py`
(`outputs/publication_exhibits/`).

## 3.1 Experiment integrity and overall behaviour

**[R1]** The locked artifact contains 92,160 trials — 4 architectures × 240 items
× 8 seeds × 12 intended pressure targets — with exactly 23,040 trials per
architecture, the complete cross-product, no missing and no duplicated cells.
**[R2]** Independent re-scoring of all 92,160 stored generations reproduced the
recorded correct / abstention / malformed outcomes with 0 mismatches, and the
frozen analysis reproduced on all 53 audited quantities to within
≈ 5.7 × 10⁻¹⁴ (Appendix A-REPRO).

**[R3]** With the target inside the exact-attention window (intended pressure
targets 150 and 180), pooled strict production accuracy is ≈ 0.88 for every
architecture; **[R4]** it is at or above 0.99 for the numerical, contradictory,
and entity-attribute types and lower for compound-relational (0.84) and temporal
(0.57, the latter driven by a 0.38 abstention rate) (Table 4). **[R5]** The
pressure grid is accurately calibrated: the median realised
`model_tokens_after_target` matches each intended target to within a few tokens
(Figure D).

## 3.2 H1 — Information types degrade non-uniformly

**Status: SUPPORTED** (claims register H1-1; H1-2 partially supported).

The primary endpoint is `A_transition`, the mean **raw strict production
accuracy** over intended transition targets 205–265, pooled over the three AHN
architectures (n = 5,760 per fact type; Transformer excluded).

**[R6]** The five `A_transition` values are: compound-relational 0.255, temporal
0.307, numerical 0.389, contradictory 0.520, entity-attribute 0.594 (Table 1,
Figure 1). **[R7]** The label-permutation omnibus on the dispersion of these five
means gives p = 5 × 10⁻⁴ (0 of 2,000 permutations reached the observed
dispersion of 0.127). **[R8]** All 10 pairwise fact-type differences have
Holm-adjusted 95% bootstrap intervals that exclude zero; the smallest difference
is compound-relational versus temporal (−0.052, 95% CI [−0.099, −0.003],
Holm-adjusted p = 0.037) and all others have Holm-adjusted p ≈ 0 (Table 2).
Because at least one adjusted interval excludes zero, the pre-registered
criterion for H1 is met.

**Ordering.** Compound-relational degrades fastest and entity-attribute is most
robust. **[R9]** The middle ranks are closer together and are partly
metric-dependent: under answered-valid accuracy the per-type `A_transition`
values are compound-relational 0.669, contradictory 0.817, numerical 0.824,
entity-attribute 0.910, temporal 0.925, and 2 of the 10 contrasts
(contradictory–numerical, entity-attribute–temporal) are no longer significant
after Holm adjustment (Table 1; Appendix A-H1). Under answered-valid accuracy
compound-relational remains the lowest and entity-attribute among the highest.

**Sensitivities (Appendix A-H1).** **[R10]** Excluding the temporal type, all 6
remaining contrasts stay Holm-significant. **[R11]** Excluding the
compound-relational type (*post-freeze*), all 6 remaining contrasts stay
Holm-significant and the omnibus over the remaining four types gives
p = 5 × 10⁻⁴. **[R12]** Across the 8 seeds the fastest-to-slowest ordering is
identical in 7 of 8 seeds; in one seed the two lowest-ranked types
(compound-relational, temporal) swap, and per-type `A_transition` varies by
about ±0.03–0.05 across seeds.

**Interpretation.** The strict production metric counts abstention and malformed
output as failure, so `A_transition` measures end-to-end task-performance
degradation; it is not a direct measure of how much of the target value remains
recoverable from the model's state. The two
lowest-ranked types are also the two with elevated in-window abstention
(**[R13]** compound-relational 0.115, temporal 0.384; Table 4), and part of
their low `A_transition` reflects a greater tendency to abstain under pressure
rather than faster loss of the stored value. The answered-valid sensitivity and
the control-validity table are reported alongside the primary for this reason.

## 3.3 H2 — Transition dynamics under memory pressure

**Status: SUPPORTED for the architecture advantage (H2-1) and for the
threshold-like shape (H2-2); the pre-registered pooled transition-width
statistic was UNDETERMINED (H2-3) and is addressed by a post-freeze reporting
amendment.**

### Architecture advantage in the near-window band

**[R14]** Over the transition interval [200, 270], the three AHN architectures
retain +0.249 more strict accuracy than the no-recurrent-memory baseline
(pooled AHN minus Transformer; 95% CI [0.233, 0.266]; the interval is positive
in every seed) (Figure 2, Table 3). **[R15]** At intended target 220 (realised
model tokens ≈ 220), pooled AHN strict accuracy is 0.44–0.51 while the baseline
is 0.18; at intended 235 the AHN arms are 0.51–0.56 while the baseline is 0.03
(Figure 2 source table). Part of the gap is the baseline degenerating rather
than abstaining (§3.6, VAL-3).

### Location of the collapse: K is below W

**[R16]** The empirical performance knee K (isotonic 0.5-crossing of pooled
strict accuracy) is 208.3 for the baseline (95% CI [207.1, 209.5]) and 218.4,
219.6, and 240.0 for AHN-DeltaNet, AHN-Mamba2, and AHN-GatedDeltaNet (Table 3,
Figure 2). **[R17]** Every K lies below the architectural window reference
W = 256. **[R18]** The AHN knees are less precisely located than the baseline
knee: their bootstrap intervals are wide and asymmetric (e.g. AHN-GatedDeltaNet
[220.4, 243.9]) and their across-seed spread is 21–29 tokens, versus 1.9 tokens
for the baseline (Appendix A-H2a). We therefore report the AHN knees as a range
(roughly 218–240) rather than point values, and we do not claim a specific
ordering among the AHN knees.

**[R19]** The abstention knee is far earlier for the AHN arms (247–251) than for
the baseline (≈ 422) (Table 3): the AHN arms begin abstaining around the window,
whereas the baseline continues to emit answers well past it.

### Shape of the collapse

**[R20]** The AIC shape test favours a change-point fit (slope change fixed at
W = 256) over a smooth fit for all four architectures (ΔAIC ≈ −0.7 baseline,
−2.6 to −8.3 AHN), i.e. "threshold-like" for every arm; the baseline margin is
small (ΔAIC −0.7) (Table 3).

**[R21]** The pre-registered pooled 90→10 transition-width statistic is
mathematically undefined for this dataset: the strict-accuracy curve pooled over
all five fact types peaks at ≈ 0.88 (because the temporal and
compound-relational types abstention-saturate in-window) and never reaches the
0.90 reference, so the frozen output is non-finite for every architecture. That
frozen output is preserved unchanged and is not interpreted (Appendix A-H2a).

**[R22]** *(Post-freeze reporting amendment.)* Computed per fact type for the
three types where the 90→10 width estimator is defined (contradictory,
entity-attribute, numerical — the types whose fitted curve attains ≥ 0.90 and
≤ 0.10), the per-architecture median 90→10 width is 32.4 model tokens for the
baseline (95% CI [30.5, 36.8]) and 61.8, 71.4, and 73.8 for AHN-GatedDeltaNet,
AHN-DeltaNet, and AHN-Mamba2 (individual eligible-type widths range 29–77
tokens; `frac_finite` = 1.0 on the bootstrap). **[R23]** Every one of these
widths is well below half the window (128 tokens), and the baseline transition
is narrower than every AHN transition in every seed (Appendix A-H2a). The
compound-relational and temporal types are ineligible for this statistic
(fitted ceilings 0.862 and 0.568), not because their transition is wide.

### No retention past the window

**[R24]** Past the window, strict accuracy is indistinguishable from zero for all
four architectures: `A_recurrent` (mean strict accuracy over intended targets
≥ 315) is 0.0001–0.005 with bootstrap intervals reaching zero (Table 3),
and every per-architecture accuracy point at intended targets ≥ 285 is ≤ 0.013
(Figure 2 source table). The deep-recurrent result is reported separately in
§3.5.

### Interpretation

The AHN recurrent path shifts the strict-accuracy collapse roughly 10–30 tokens
later than the no-recurrent-memory baseline and preserves about a quarter more
accuracy in the near-window band; past the window neither the recurrent
architectures nor the baseline retrieve the target. The collapse is
threshold-like on every computable view. **[R25]** The empirical knee is not the
window: K (208–240) is below W (256), and about 32% of trials in which the
target span is arithmetically inside the lossless window for the whole trial
still fail (§3.6, VAL-4), so the near-window degradation is not attributable
solely to the exact-to-compressed memory transition.

## 3.4 H3 — Behavioural signalling of memory unreliability

**Status: SUPPORTED for behavioural signalling (H3-1, H3-2); PARTIALLY SUPPORTED
for factual calibration (H3-3).**

Past the sliding-window reference (realised `model_tokens_after_target` ≥ 272;
n ≈ 10,091 per architecture):

**[R26]** The appropriate-abstention rate (fraction of trials that are
abstentions) is 0.946, 0.945, and 0.929 for AHN-DeltaNet, AHN-Mamba2, and
AHN-GatedDeltaNet, versus 0.516 for the no-recurrent-memory baseline (Figure 3,
Table 3-adjacent source; frozen `final_h3_h3_behavioral_per_arm.csv`).
**[R27]** The unsignalled-failure rate (fraction that are an incorrect valid
answer or a malformed output) is 0.054, 0.052, and 0.071 for the AHN arms,
versus 0.480 for the baseline. **[R28]** All six AHN-versus-baseline contrasts
(three architectures × two rates) have magnitudes 0.41–0.43 with Holm-adjusted
p ≈ 0. **[R29]** The per-architecture appropriate-abstention rate is stable
across seeds (AHN 0.92–0.95, baseline 0.49–0.53 in every seed; Appendix A-H3).

**[R30]** Composition of the baseline's past-window behaviour: 0.52 abstention,
0.45 malformed output, 0.03 incorrect valid answer, and < 0.01 correct
(Figure 3 source table). The AHN arms are almost entirely abstention past the
window, with 0.04–0.07 incorrect valid answers and ≤ 0.007 malformed.

### Factual calibration on answered trials

**[R31]** On answered-valid trials, the change in the (confidence − accuracy) gap
from the control anchors to the transition interval [200, 270] is −0.018 for the
baseline (95% CI [−0.051, 0.013], containing zero — no detectable shift), and
−0.063, −0.108, and −0.115 for AHN-GatedDeltaNet, AHN-Mamba2, and AHN-DeltaNet
(intervals excluding zero) (Appendix A-H3): in the transition the AHN arms
become more conservative (confidence drops relative to accuracy) while the
baseline does not.

**[R32]** On the small subpopulation of past-window trials where a model does
still answer (answered-valid n = 853 pooled at intended target 265, of which the
baseline contributes only 1), factual calibration is poor for all architectures:
the confidence − accuracy gap is ≈ +0.53 and the confidently-wrong rate is
0.92–0.98 (Appendix A-H3). This describes fewer than 5% of past-window trials;
the dominant past-window behaviour is abstention.

### Interpretation

As memory degrades past the window, AHN behaviour increasingly signals memory
unreliability through abstention: AHN architectures abstain on 93–95% of
past-window trials and leave 5–7% of failures unsignalled, versus 52% abstention
and 48% unsignalled failure for the no-recurrent-memory baseline. Because the
baseline has no recurrent memory, this contrast confounds the presence of a
recurrent state with the recurrent-module distillation recipe; whether the
behaviour reflects a signal carried in the recurrent state or a learned
abstention policy cannot be determined from this design (claims register H3-4).

## 3.5 Deep-recurrent retention

**Status: NEGATIVE RESULT** (claims register H2-5). *(Post-freeze sensitivity;
Table 5.)*

**[R33]** Restricted to realised `model_tokens_after_target` ≥ 2W (512), with
3,542 trials per architecture, the correct counts are 0 (AHN-DeltaNet), 0
(AHN-GatedDeltaNet), 1 (AHN-Mamba2), and 3 (baseline). **[R34]** The Wilson 95%
upper bounds on accuracy are ≤ 0.0011 for AHN-DeltaNet and AHN-GatedDeltaNet,
0.0016 for AHN-Mamba2, and 0.0025 for the baseline. **[R35]** Abstention exceeds
0.89 for all four architectures in this regime (AHN ≈ 0.98). **[R36]** No fact
type shows retention: the single AHN-Mamba2 correct trial is a temporal
(two-alternative) item (Table 5 by-fact-type source).

No measurable target-specific factual retention was observed at deep recurrent
pressure under the production evaluation.

## 3.6 Robustness and construct-validity findings

### Temporal construct (VAL-1)

**[R37]** The temporal 2x2x2 nuisance design is exactly balanced in the final
item set (24/24 on each factor; 6 items per cell). **[R38]** At the control
anchors, answered-valid accuracy differs by nuisance subgroup — 0.849 when the
gold is the lower-numbered entity versus 0.992 when it is the higher-numbered,
and 0.868 when the gold is not listed first versus 1.000 when it is — reflecting
a documented directional response preference that the counterbalancing nets to
chance (pooled control answered-valid accuracy 0.922; Appendix A-VAL). The
temporal benchmark is a balanced order-retrieval task; its raw strict accuracy
is abstention-dominated and its H1 rank is reported with the answered-valid
sensitivity.

### Compound-relational construct (VAL-2)

**[R39]** In-window (control-anchor) retrieval for the compound-relational type
reaches 0.842 strict (0.951 among answered trials), with 0.115 abstention and 0
malformed. **[R40]** This triggers the pre-registered control-validity WARNING
(strict < 0.85 and abstention > 0.10); the FAIL threshold (0.70) is not reached,
so the type is retained in the H1 primary (Table 4). **[R41]** The WARNING holds
in 7 of 8 seeds (per-seed control strict 0.77–0.94), and only 2 of 48 items have
control strict accuracy below 0.5 (Appendix A-VAL). This is a task-difficulty
ceiling for a co-located two-clause target — the model must resolve both clauses
of one sentence — not a memory or pipeline fault; the compound-relational type is
not a multi-hop reasoning benchmark.

### Transformer control behaviour (VAL-3)

**[R42]** The Transformer arm produces malformed output on 39.6% of its trials
overall, versus 1.4–4.8% for the AHN arms on byte-identical prompts (Appendix
A-VAL). **[R43]** The Transformer malformed rate is 0.0% at the in-window
control anchors, rises to 18–79% across the transition and early-recurrent
targets (205–380), and falls to 3–10% at the deepest targets (520, 760).
**[R44]** By subtype, the malformed outputs are over-length (4,580),
unrecognised value (2,241), empty (1,488), and negation (813). The malformed
rate is spread across all 240 items and all 8 seeds. This is expected
no-recurrent-memory degeneration once the target is evicted — the baseline emits
degenerate text rather than abstaining — and is classified as control behaviour
by the pre-registered gate; **[R45]** the pooled-across-architecture malformed
rate (12.6%) is reported only alongside the per-architecture split, never alone.

### Residual in-window failures (VAL-4)

**[R46]** For the subset of trials in which the target span is arithmetically
inside the lossless window for the whole trial (34,975 trials), 32.1% still fail
(46% of the failures are abstentions, 39% malformed, 15% incorrect valid
answers) (Appendix A-H2b). **[R47]** This failure rate is 12% at intended targets
150 and 180 but rises to 34%, 60%, and 55% at intended targets 205, 220, and 235,
and is 30–34% across all seeds. **[R48]** By fact type the residual failure rate
is 12% (entity-attribute), 23% (contradictory), 34% (numerical), 41%
(compound-relational), and 52% (temporal). Retrieval therefore begins to fail at
pressure levels where the target span is still nominally within exact attention;
the pressure axis is a proxy for compression pressure, and near-window
degradation is not attributable solely to the exact-to-compressed transition.
No mechanism is claimed.

### Reproduced plumbing gates

**[R49]** The pre-registered plumbing gates reproduce with 0 blocking failures;
the Transformer malformed behaviour is flagged as control behaviour and the
compound-relational control validity is flagged WARNING, as above (Appendix
A-REPRO).
