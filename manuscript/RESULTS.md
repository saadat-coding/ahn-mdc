# Results

Every numerical statement carries a bracketed identifier (e.g. **[R12]**) traced
in the results-traceability table. Statistics are from the frozen analysis
(version 1.0) unless marked *post-freeze* (version 1.1; Methods 2.5). Bootstrap
p-values at the 2,000-resample resolution floor are reported as p < 0.001; the
H1 omnibus permutation test reports its add-one-corrected value.

## 3.1 Experiment integrity

**[R1]** The locked artifact is the complete 4 architectures x 240 items
x 8 seeds x 12 intended pressure targets = 92,160-trial
cross-product, 23,040 per architecture, no missing or duplicated cell. **[R2]**
Independent re-scoring of all 92,160 generations reproduced the recorded outcomes
with 0 mismatches, and the frozen analysis reproduced on all 53 audited quantities
to ~ 5.7e-14. **[R3]** With the target inside the exact-attention
window (intended targets 150, 180), pooled strict production accuracy is
~ 0.88 for every architecture; **[R4]** by type it is >= 0.99 for
numerical, contradictory, and entity-attribute, and lower for compound-relational
(0.84) and temporal (0.57, with a 0.38 abstention rate) (Table 4). **[R5]**
Realised `model_tokens_after_target` matches each intended target to
within a few tokens (Figure D).

## 3.2 H1 - Information types degrade non-uniformly

**Status: SUPPORTED** (H1-1; ordering H1-2 partially supported). The primary
endpoint A_transition is the mean raw strict production accuracy over
intended transition targets 205-265, AHN arms pooled (n = 5,760 per type).

**[R6]** The five A_transition values span a wide range:
compound-relational 0.255, temporal 0.307, numerical 0.389, contradictory 0.520,
entity-attribute 0.594 (Table 1, Figure 1). **[R7]** The label-permutation omnibus
on their dispersion gives p = 5e-4 (0 of 2,000 permutations reached the
observed SD of 0.127). **[R8]** All 10 pairwise differences have Holm-adjusted 95%
bootstrap intervals excluding zero; the smallest is compound-relational vs
temporal (-0.052, 95% CI [-0.099, -0.003], Holm p = 0.037), the other nine
at p < 0.001 (Table 2). The pre-registered criterion for H1 is met. **[R50]**
Within the transition region the per-target trajectory is not strictly
monotonic for every type: contradictory and numerical both show a partial
rebound at intended target 235 relative to 220 that is consistent across all 8
seeds and all three AHN architectures (Figure 1); the primary endpoint
A_transition is the mean over the five transition targets and does not assume
or require a monotonic decline.

Compound-relational degrades fastest and entity-attribute is most robust. **[R9]**
The ordering is partly metric-dependent: under answered-valid accuracy (which
ignores abstention) 2 of the 10 contrasts lose Holm significance, though
compound-relational stays lowest and entity-attribute among the highest
(Appendix A-H1). **[R12]** The ordering is identical in 7 of 8 seeds (the two
lowest-ranked types swap in one), with per-type A_transition varying by
+/-0.03-0.05 across seeds. **[R10]** Excluding temporal, all 6 remaining
contrasts stay Holm-significant; **[R11]** excluding compound-relational
(*post-freeze*), all 6 stay significant and the four-type omnibus gives
p = 5e-4 (Appendix A-H1). Because the strict metric counts abstention
and malformed output as failure, A_transition measures end-to-end
task-performance degradation, not how much of the target value remains
recoverable; **[R13]** the two lowest-ranked types are also the two with elevated
in-window abstention (compound-relational 0.115, temporal 0.384; Table 4), so part
of their low A_transition is a greater tendency to abstain under
pressure.

## 3.3 H2 - Transition dynamics under memory pressure

**Status: SUPPORTED** for the near-window advantage (H2-1) and a concentrated,
non-gradual collapse (H2-2); the pre-registered *pooled* transition-width
statistic was **UNDETERMINED** (H2-3), addressed by a post-freeze amendment.

**[R14]** Over the transition interval [200, 270] the three AHN architectures
retain **+0.249** more strict accuracy than the no-recurrent-memory control
(pooled AHN minus Transformer; 95% CI [0.233, 0.266]; positive in every seed)
(Figure 2, Table 3). **[R15]** At intended target 220, pooled AHN strict accuracy
is 0.44-0.51 vs 0.18 for the control; at 235, 0.51-0.56 vs 0.03. Part of the gap
is the control degenerating rather than abstaining (Section 3.6).

**[R16]** The empirical performance knee K (isotonic 0.5-crossing of pooled
strict accuracy) is 208.3 for the control (95% CI [207.1, 209.5]) and 218.4,
219.6, and 240.0 for AHN-DeltaNet, AHN-Mamba2, and AHN-GatedDeltaNet (Table 3).
**[R17]** Every K lies **below** the exact-attention window W = 256. **[R18]**
The AHN knees are less precisely located (intervals wide and asymmetric,
across-seed spread 21-29 tokens vs 1.9 for the control; Appendix A-H2a), so we
report the AHN knee as a range (~ 218-240) and claim no ordering among
them. **[R19]** The abstention knee is far earlier for AHN (247-251) than for the
control (~ 422): the AHN arms begin abstaining around the window while the
control keeps answering well past it.

Performance degradation was **concentrated rather than gradual**, though
transition sharpness differed by architecture. **[R20]** *Frozen change-point
evidence:* an AIC comparison favours a slope change at W for all four
architectures, but marginally for the control (AIC change ~ -0.7
vs -2.6 to -8.3 for AHN; Table 3). **[R21]** *Frozen pooled width:*
mathematically undefined here — the five-type pooled curve peaks at ~ 0.88,
below the 0.90 reference — so the frozen output is non-finite and is preserved
unchanged, not interpreted (Methods 2.5, Appendix A-H2a). **[R22]**
*Post-freeze per-type width characterization:* for the three types where the
90->10 estimator is defined (contradictory, entity-attribute, numerical), the
per-architecture median width is **32.4 model tokens** for the control (95% CI
[30.5, 36.8]) and **61.8, 71.4, 73.8** for AHN-GatedDeltaNet, AHN-DeltaNet,
AHN-Mamba2 (individual eligible-type widths 29-77 tokens). **[R23]** Every width
is well below half the window (128 tokens), and the control transition is narrower
than every AHN transition in every seed (Appendix A-H2a); compound-relational and
temporal are ineligible (fitted ceilings 0.862, 0.568), not because their
transition is wide. Both views agree the collapse is concentrated, and both show
the **control transition is earlier and narrower** (K ~ 208, median width
~ 32) while the **AHN transitions are later and broader**
(K ~ 218-240, median width ~ 62-74): AHN reshapes the transition
rather than translating a sharp cliff. This is observed task-performance dynamics,
not a mechanistic property of recurrent memory.

**[R24]** Past the window, strict accuracy is indistinguishable from zero for all
four architectures (A_recurrent over intended targets >= 315 is
0.0001-0.005, bootstrap intervals reaching zero; every point at intended targets
>= 285 is <= 0.013) (Table 3); the deeper regime is Section 3.5. **[R25]** The
knee is not the window and the transition is not a clean inside/outside switch:
every K (208-240) lies below W (256), and about 32% of trials whose target
span is exact-attention eligible throughout the trial still fail (Section 3.6), so
deterioration begins before that boundary alone can explain it. No mechanism is
claimed.

## 3.4 H3 - Behavioural signalling of memory unreliability

**Status: SUPPORTED** for behavioural signalling (H3-1, H3-2); **PARTIALLY
SUPPORTED** for factual calibration (H3-3). Past the exact-attention window
(realised `model_tokens_after_target` >= 272; n ~ 10,091
per architecture), the principal difference between AHN and the control is
**failure mode**, not sustained retrieval (Section 3.5).

**[R26]** The appropriate-abstention rate is 0.946, 0.945, and 0.929 for
AHN-DeltaNet, AHN-Mamba2, AHN-GatedDeltaNet, vs **0.516** for the control
(Figure 3). **[R27]** The unsignalled-failure rate (incorrect valid answer or
malformed output) is 0.054, 0.052, 0.071 for the AHN arms vs **0.480** for the
control. **[R28]** All six AHN-vs-control contrasts have magnitudes 0.41-0.43 with
Holm p < 0.001; **[R29]** the per-architecture abstention rate is stable across
seeds (AHN 0.92-0.95, control 0.49-0.53 in every seed; Appendix A-H3). **[R30]**
The control's past-window behaviour is 0.52 abstention, 0.45 malformed, 0.03
incorrect valid, < 0.01 correct (Figure 3); the AHN arms are almost entirely
abstention. The unsignalled-failure gap is therefore mostly the control producing
degenerate output where the AHN arms abstain.

**Factual calibration (secondary).** **[R31]** On answered-valid trials the
(confidence minus accuracy) gap shifts by -0.018 for the control (95% CI
[-0.051, 0.013], containing zero) and -0.063 to -0.115 for the AHN arms
(intervals excluding zero): the AHN arms become more conservative in the
transition while the control does not shift. **[R32]** On the small past-window
population that still answers (answered-valid n = 853 pooled at intended target
265, control contributing 1), calibration is poor for all architectures (gap
~ +0.53, confidently-wrong rate 0.92-0.98) - fewer than 5% of
past-window trials, where the dominant behaviour is abstention (Appendix A-H3).
The contrast confounds a recurrent state with the AHN distillation recipe; whether
the behaviour reflects a signal in the recurrent state or a learned abstention
policy cannot be determined from this design (H3-4).

## 3.5 Deep-recurrent regime

**Status: NEGATIVE RESULT** (H2-5). *(Post-freeze sensitivity; Table 5.)*
**[R33]** Restricted to realised `model_tokens_after_target` >= 2W
(512), with 3,542 trials per architecture, the correct counts are 0
(AHN-DeltaNet), 0 (AHN-GatedDeltaNet), 1 (AHN-Mamba2), 3 (control). **[R34]** The
Wilson 95% upper bounds on accuracy are <= 0.0011 (AHN-DeltaNet,
AHN-GatedDeltaNet), 0.0016 (AHN-Mamba2), 0.0025 (control). **[R35]** Abstention
exceeds 0.89 for all four architectures (AHN ~ 0.98). **[R36]** No
information type shows retention; the single AHN-Mamba2 correct trial is a
temporal (two-alternative) item.

No measurable target-specific factual retention was observed at deep recurrent
pressure under the production evaluation.

## 3.6 Robustness and construct-validity findings

**Temporal (VAL-1).** **[R37]** The temporal 2x2x2 nuisance design is
exactly balanced. **[R38]** At the control anchors, answered-valid accuracy
differs by nuisance subgroup (0.849 vs 0.992 by gold rank; 0.868 vs 1.000 by
gold list position) - a documented directional response preference that the
counterbalancing nets to chance (pooled control answered-valid accuracy 0.922;
Appendix A-VAL). Its raw strict accuracy is abstention-dominated, so its H1 rank is
read with the answered-valid sensitivity.

**Compound-relational (VAL-2).** **[R39]** In-window retrieval reaches 0.842
strict (0.951 among answered trials), with 0.115 abstention and 0 malformed.
**[R40]** This triggers the pre-registered control-validity WARNING (strict
< 0.85 and abstention > 0.10); the FAIL threshold (0.70) is not reached, so the
type is retained in the H1 primary. **[R41]** The WARNING holds in 7 of 8 seeds,
and only 2 of 48 items have control strict accuracy below 0.5 (Appendix A-VAL).
This is a task-difficulty ceiling for a co-located two-clause target, not a memory
or pipeline fault.

**Transformer control behaviour (VAL-3).** **[R42]** The Transformer arm produces
malformed output on 39.6% of its trials overall, vs 1.4-4.8% for the AHN arms
on byte-identical prompts. **[R43]** Its malformed rate is 0.0% at the in-window
control anchors, rises to 18-79% across the transition and early-recurrent
targets, and falls to 3-10% at the deepest targets. **[R51]** Correspondingly,
the Transformer's abstention rate is not monotonic in pressure: it falls from
0.52 (intended target 265) to 0.26-0.27 through 315-380 as malformed output
rises, then climbs sharply to 0.82-0.95 at 520-760 as malformed output recedes;
the H3 primary result concerns pooled failure-mode composition beyond the
predefined W+16 boundary (Section 3.4), not monotonic abstention growth across
intermediate pressures. **[R44]** By subtype the
malformed outputs are over-length (4,580), unrecognised value (2,241), empty
(1,488), and negation (813), spread across all items and seeds (Appendix A-VAL).
The concentration at higher pressure with near-absence at the control anchors
supports treating this as control behaviour rather than pipeline corruption; the
pre-registered gate classifies it as such. **[R45]** The pooled-across-architecture
malformed rate (12.6%) is reported only alongside the per-architecture split.

**Residual in-window failures (VAL-4).** **[R46]** For the 34,975 trials whose
target span is exact-attention eligible throughout the trial, 32.1% still fail
(46% abstentions, 39% malformed, 15% incorrect valid answers). **[R47]** This
rate is 12% at intended targets 150 and 180 but rises to 34%, 60%, and 55% at
intended targets 205, 220, and 235 (30-34% across all seeds). **[R48]** By type
it is 12% (entity-attribute), 23% (contradictory), 34% (numerical), 41%
(compound-relational), and 52% (temporal) (Appendix A-H2b). Retrieval begins to
fail where the target is still exact-attention eligible, so the pressure axis is a
proxy for compression pressure and near-window degradation is not attributable
solely to the exact-to-compressed transition. No mechanism is claimed. **[R49]**
The pre-registered plumbing gates reproduce with 0 blocking failures
(Appendix A-REPRO).
