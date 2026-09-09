# Discussion

We evaluated how retrieval degrades when the target of a query is pushed out of a
model's exact-attention window (W = 256), comparing a Transformer with no
recurrent memory against three Adaptive Hybrid Neural (AHN) architectures that
add a fixed-size recurrent state. Four observations organise the interpretation:
degradation is information-type dependent (H1); the AHN recurrent path reshapes
the near-window transition without changing the deep-retrieval outcome (H2);
past the transition the architectures differ mainly in *how* they fail (H3); and
the empirical performance knee sits below the architectural window for every
arm. Throughout, "degradation" refers to end-to-end task performance under a
strict production metric, not to a direct measurement of hidden-state contents.

## 4.1 What degrades under memory pressure

Fact types lose task accuracy at visibly different rates as pressure rises: the
five transition-region accuracies span roughly 0.26 to 0.59, a spread far larger
than label-permutation chance ([R6], [R7]). Compound-relational targets degrade
fastest and entity-attribute targets are most robust. This ordering is only
partly stable: under an answered-valid metric that ignores abstention, several
middle-rank distinctions disappear ([R9]), and the two fastest-degrading types
are also the two with elevated in-window abstention ([R13]). The defensible claim
is therefore that *end-to-end* degradation is information-type dependent, and
that the manifestation of failure — wrong answer versus abstention versus
malformed output — is itself type-dependent and contributes to the ordering.

We do not interpret this as differential decay of stored representations, because
the production metric cannot separate a lost value from a model that declines to
answer. Why types differ remains open. Answer-space structure (closed set versus
open digit string), task complexity, the base model's answer prior, a
type-specific abstention tendency, the relational structure of the
compound-relational query, and retrieval–output interactions are all candidate
factors for controlled follow-up, not established mechanisms. The
compound-relational result in particular is confounded by a lower in-window
ceiling (≈ 0.84 strict, a control WARNING; [R39], [R40]), so its fast apparent
degradation should not be read as pure memory fragility.

## 4.2 AHN reshapes the near-window transition

The AHN arms preserve substantially more near-window accuracy than the
no-recurrent-memory control: across the transition interval they retain about 0.25
more strict accuracy (+0.249, 95% CI [0.233, 0.266]; [R14]). It is
tempting to summarise this as "AHN moves the cliff to the right," but the data do
not support that simplification. Both views of transition shape agree that the
collapse is concentrated rather than gradual, yet they also agree on an
asymmetry: the Transformer transition is **earlier and narrower** while the AHN
transitions are **later and broader**. The post-freeze per-type width
characterization puts the Transformer median 90→10 width near 32 tokens against
62–74 tokens for the AHN arms ([R22]) — so the Transformer's "concentrated"
characterization rests mainly on that narrow width, since its frozen change-point
margin is thin (ΔAIC ≈ −0.7, versus −2.6 to −8.3 for the AHN arms, which favour a
slope change at W more clearly; [R20]). AHN thus preserves useful task performance
farther into the near-window region *and* spreads its decline over a wider
pressure interval — a qualitatively different transition, not a translated copy of
the control's.

This width characterization must be read with care. The pre-registered pooled
90→10 estimator was mathematically undefined on the collected data, because the
five-type pooled accuracy curve never reaches the 0.90 reference ([R21]). The
per-eligible-type analysis was introduced *after* the freeze, is reported as
analysis version 1.1, and did not alter the raw artifact, the frozen primary
endpoints, or any design constant. It **characterizes** the transition shape; it
does not rescue a failed primary analysis, and it should not be cited as though
it were pre-registered. The frozen AIC evidence and the amended widths are
complementary but independent lines, and we keep them labelled as such.

## 4.3 No measurable deep-recurrent retrieval

Past the transition, the near-window advantage does not become sustained
retrieval. At realised pressure ≥ 2W, target-specific correct answers are
essentially absent — 0, 0, 1, and 3 correct of 3,542 trials per arm, Wilson upper
bounds at or below 0.0025 ([R33], [R34]) — and no fact type shows retention
([R36]). The approved phrasing is deliberate: *no measurable target-specific
factual retention was observed at deep recurrent pressure under the production
evaluation.* This is one of the study's more consequential findings: AHN is
explicitly designed to carry information beyond the exact window, so a null
production result at depth is a real boundary on what the current system delivers
end-to-end, not a footnote. It does **not** establish that the recurrent state
contains no target information — a production failure is consistent with
information that is present but not recoverable by greedy generation from this
prompt. Representation probing, state decoding, forced-choice or alternative-prompt
evaluation, and targeted state interventions are the appropriate tests, and are
outside this experiment's scope.

## 4.4 Failure mode and behavioural uncertainty signalling

The clearest architecture difference past the window is not in what is retrieved
but in what happens when retrieval fails. Beyond W + 16 the AHN arms abstain on
the large majority of trials and leave only a small fraction of failures
unsignalled, whereas the control abstains on roughly half and fails without
signalling on the other half — mostly through degenerate output rather than
confident wrong answers ([R26], [R27], [R30]). The gap is about 0.42 on both
rates, Holm-significant, and identical in direction across all eight seeds ([R28],
[R29]). We describe this as behavioural uncertainty signalling, or failure-mode
adaptation: as its memory becomes unreliable, the AHN system increasingly declines
to answer instead of producing unsupported text.

The experiment cannot say why. At least two explanations are consistent with the
data: (A) the recurrent state carries a usable signal that the context is thin,
which the model acts on; or (B) the AHN checkpoints were distilled with training
that produced an abstention policy under sparse context. Because the Transformer
control has no recurrent module at all, the comparison confounds the presence of
a recurrent state with the AHN training and distillation recipe, and these
alternatives cannot be separated here. We therefore avoid any claim that the
model "knows" it has forgotten or that the recurrent state "encodes uncertainty."
Distinguishing (A) from (B) needs designs this study did not run — training- or
distillation-matched controls, recurrent-state ablation on an otherwise identical
checkpoint, uncertainty probes on the recurrent state, or comparison against an
explicit retrieval-confidence head.

Factual calibration is a secondary observation. In the transition the AHN arms
become somewhat more conservative on the trials where they still answer, while
the control does not shift ([R31]); on the small past-window population that still
answers (fewer than 5% of past-window trials) all architectures are badly
miscalibrated ([R32]), a statement about a narrow selected subpopulation rather
than a headline result. Two quantities must not be conflated: the probability of
emitting "I don't know" is not the confidence attached to a factual answer. The
sequence-probability measure is provisional; length-normalised confidence,
token-level calibration, an explicit answer-versus-abstain probability, and
risk–coverage analysis are natural next steps.

## 4.5 Why K < W matters

For every architecture the empirical performance knee K (the pooled strict-
accuracy 0.5-crossing) lies below the architectural window W = 256: about 208 for
the control and roughly 218–240 for the AHN arms ([R16], [R17]). K is an observed
per-run quantity, not an architectural constant, and it does not mark the onset
of compression. The point is reinforced by residual failures: on trials where the
target span is arithmetically inside the lossless window for the entire trial,
about 32% still fail, and this rate climbs steeply across intended pressures
205–235 even though the target is nominally available to exact attention ([R25],
[R46], [R47]). Performance deterioration is therefore already underway while the
target is still inside the window, so the transition cannot be reduced to a
binary "inside the window = remembered, outside = compressed" story. Context
interference, attention competition among many distractors, prompt and task
effects, generation behaviour, and target-span boundary effects are all candidate
contributors; the present design does not distinguish them. The practical
implication is that window size alone does not predict where empirical retrieval
fails.

## 4.6 Limitations

**Benchmark.** The evaluation set is synthetic and built to isolate memory
pressure; it does not establish behaviour on naturalistic long-context tasks.
**Model scale and family.** All results are for `Qwen2.5-3B-Instruct` with three
published AHN checkpoints; they should not be generalised to other scales,
base-model families, or recurrent-memory designs. **Confounded comparison.** The
AHN checkpoints differ from the control not only by having a recurrent state but
by the recurrent module's training and distillation, which limits causal
attribution for every AHN-versus-control contrast, H3 included. **Metric.**
Strict production accuracy deliberately counts abstention and malformed output as
failure, mixing retrieval success with output policy; the answered-valid
sensitivity partly addresses this but changes the estimand. **Construct scope.**
Compound-relational is a single co-located two-clause target, not separated-fact
multi-hop reasoning, and carries a lower in-window ceiling; the temporal type has
a counterbalanced directional response bias and abstention-dominated raw strict
performance. **H2 amendment.** The pre-registered pooled transition-width
estimator was undefined; the per-type width analysis is post-freeze and is
identified as such wherever it appears. **Window boundary.** Residual
fully-exact failures show the simple window-boundary account is incomplete.
**Confidence measure.** Sequence probability is provisional and the past-window
answered-valid population is small and selected. **Deep-recurrent null.** A
production-level retrieval failure at depth does not establish that the recurrent
state lacks latent target information. **Provenance.** The exact
generation-runtime commit (`d29c6d8…`) is not in the released repository history,
though the locked generations were independently re-scored with 0 mismatches and
the frozen analysis reproduced to floating-point tolerance.

## 4.7 Implications and future work

Read cautiously, the results suggest that long-context memory systems are better
evaluated by information type than by aggregate accuracy alone; that the
transition region deserves explicit characterization rather than a single knee or
width; that window size is insufficient to predict empirical retrieval failure;
and that a memory system should be judged not only by what it retrieves but by
how it behaves when retrieval fails, where selective prediction and calibrated
abstention become relevant properties. Deep-context benchmarks would benefit from
separating information recoverable from hidden state from information retrievable
in production. The central open question is mechanistic: whether AHN's shift
toward abstention under memory pressure reflects a signal in the recurrent state
or a learned output policy. Resolving it requires training-matched and
ablation-based comparisons that this study motivates but does not perform.
