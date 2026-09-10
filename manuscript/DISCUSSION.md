# Discussion

We evaluated how retrieval degrades as a query target is driven out of a model's
exact-attention window (W = 256), comparing a Transformer with no recurrent
memory against three AHN architectures. Four observations organise the reading:
degradation is information-type dependent (H1); the AHN recurrent path reshapes
the near-window transition without changing the deep-retrieval outcome (H2); past
the transition the architectures differ mainly in *how* they fail (H3); and the
empirical performance knee sits below the architectural window for every arm.
Throughout, "degradation" means end-to-end task performance under a strict
production metric, not a direct measurement of hidden-state contents.

## 4.1 What degrades

Information types lose task accuracy at visibly different rates: the five
transition-region accuracies span ~ 0.26-0.59, far more than
label-permutation chance ([R6], [R7]). Compound-relational degrades fastest and
entity-attribute is most robust, but this ordering is only partly stable -
several middle-rank distinctions disappear under an answered-valid metric ([R9]),
and the two fastest-degrading types are also the two with elevated in-window
abstention ([R13]). The defensible claim is that *end-to-end* degradation is
information-type dependent and that the manifestation of failure is itself
type-dependent. We do not read this as differential decay of stored
representations, because the production metric cannot separate a lost value from a
model that declines to answer. Why types differ - answer-space structure, task
complexity, the model's answer prior, a type-specific abstention tendency, the
relational structure of the compound-relational query - is for controlled
follow-up. The compound-relational result in particular is confounded by a lower
in-window ceiling (~ 0.84, a control WARNING; [R39], [R40]).

## 4.2 AHN reshapes the near-window transition

The AHN arms preserve substantially more near-window accuracy than the control:
+0.249 more strict accuracy across the transition (95% CI [0.233, 0.266];
[R14]). It is tempting to summarise this as "AHN moves the cliff to the right,"
but the data do not support that. Both views of transition shape agree the
collapse is concentrated rather than gradual, yet also agree on an asymmetry: the
**control transition is earlier and narrower** while the **AHN transitions are
later and broader**. The post-freeze per-type width characterization puts the
control median 90->10 width near 32 tokens against 62-74 for AHN ([R22]);
the control's "concentrated" reading rests mainly on that narrow width, since its
frozen change-point margin is thin (AIC change ~ -0.7, vs -2.6 to
-8.3 for AHN; [R20]). AHN thus preserves useful task performance farther into
the near-window region *and* spreads its decline over a wider interval - a
qualitatively different transition, reported as observed task-performance
dynamics, not a mechanistic property.

This width characterization must be read with care. The pre-registered *pooled*
90->10 estimator was mathematically undefined on the collected data ([R21]).
The per-eligible-type analysis was introduced *after* the freeze, is analysis
version 1.1, and altered no raw artifact or frozen primary. It *characterizes* the
transition shape; it does not rescue a failed primary analysis and should not be
cited as pre-registered. The frozen AIC evidence and the amended widths are
complementary but independent.

## 4.3 No measurable deep-recurrent retrieval

Past the transition, the near-window advantage does not become sustained
retrieval. At realised pressure >= 2W, target-specific correct answers are
essentially absent - 0, 0, 1, and 3 correct of 3,542 trials per arm, Wilson
upper bounds <= 0.0025 ([R33], [R34]) - and no information type shows
retention ([R36]). The approved phrasing is deliberate: *no measurable
target-specific factual retention was observed at deep recurrent pressure under
the production evaluation.* This is one of the study's more consequential
findings: AHN is explicitly designed to carry information beyond the exact window,
so a null production result at depth is a real boundary on what the current system
delivers end-to-end, and it is consistent with the bounded, decaying recall that
analyses of state-space models describe
\citep{memmamba2025,recallmamba2026}. It does **not** establish that the recurrent
state contains no target information - a production failure is consistent with
information present but not recoverable by greedy generation from this prompt.
Representation probing, state decoding, forced-choice or alternative-prompt
evaluation, and targeted state interventions are the appropriate tests.

## 4.4 Failure mode and behavioural uncertainty signalling

The clearest architecture difference past the window is not what is retrieved but
what happens when retrieval fails. Beyond W+16 the AHN arms abstain on the
large majority of trials and leave a small fraction of failures unsignalled, while
the control abstains on roughly half and fails without signalling on the other
half - mostly through degenerate output ([R26], [R27], [R30]). The gap is about
0.42 on both rates, Holm-significant, and identical in direction across all eight
seeds ([R28], [R29]). We describe this as behavioural uncertainty signalling: as
its memory becomes unreliable, the AHN system increasingly declines to answer
rather than producing unsupported text.

The experiment cannot say why. Two explanations are consistent with the data: (A)
the recurrent state carries a usable signal that the context is thin, which the
model acts on; or (B) the AHN checkpoints were distilled with training that
produced an abstention policy under sparse context \citep{hesitation2025}. Because
the control has no recurrent module, the comparison confounds the presence of a
recurrent state with the AHN training and distillation recipe, and these cannot be
separated here. We therefore avoid any claim that the model "knows" it has
forgotten or that the recurrent state "encodes uncertainty." Distinguishing (A)
from (B) needs training- or distillation-matched controls, recurrent-state
ablation on an otherwise identical checkpoint, or uncertainty probes on the state.

Factual calibration is secondary. In the transition the AHN arms become somewhat
more conservative on the trials where they still answer, while the control does
not shift ([R31]); on the small past-window population that still answers (fewer
than 5% of past-window trials) all architectures are badly miscalibrated ([R32]),
consistent with the concentration of overconfidence on harder items reported for
LLM calibration generally \citep{calib2026}. The probability of emitting "I don't
know" is not the confidence attached to a factual answer, and the
sequence-probability measure is provisional.

## 4.5 Why K < W matters

For every architecture the empirical knee K lies below the exact-attention
window W = 256 (~ 208 control, ~ 218-240 AHN; [R16], [R17]).
K is an observed per-run quantity, not an architectural constant, and it does
not mark the onset of compression. Residual failures reinforce this: on trials
whose target span is exact-attention eligible for the entire trial, about 32%
still fail, rising steeply across intended pressures 205-235 ([R25], [R46],
[R47]). Deterioration is therefore already underway while the target is still
inside the window, so the transition cannot be reduced to a binary "inside =
remembered, outside = compressed" story. Context interference, attention
competition, prompt and task effects, generation behaviour, and target-span
boundary effects are candidate contributors that this design does not
distinguish. The practical implication is that window size alone does not predict
where empirical retrieval fails.

## 4.6 Limitations

**Benchmark:** the evaluation set is synthetic and isolates memory pressure; it
does not establish behaviour on naturalistic long-context tasks. **Model scale and
family:** all results are for `Qwen2.5-3B-Instruct` with three published AHN
checkpoints and should not be generalised to other scales or memory designs.
**Confounded comparison:** the AHN checkpoints differ from the control by
recurrent-module training and distillation as well as by having a recurrent state,
which limits causal attribution for every AHN-vs-control contrast. **Metric:**
strict production accuracy counts abstention and malformed output as failure,
mixing retrieval success with output policy; the answered-valid sensitivity partly
addresses this but changes the estimand. **Construct scope:** compound-relational
is a co-located two-clause target, not separated-fact multi-hop reasoning, and
carries a lower in-window ceiling; the temporal type has a counterbalanced
directional response bias. **H2 amendment:** the pre-registered pooled
transition-width estimator was undefined, and the per-type width analysis is
post-freeze. **Deep-recurrent null:** a production-level retrieval failure at depth
does not establish that the recurrent state lacks latent target information.
**Provenance:** the generation-runtime commit is not in the released repository
history, though multiple equivalence and reproduction checks found no evidence of
a scientifically relevant discrepancy.

## 4.7 Implications

Read cautiously, the results suggest that long-context memory systems are better
evaluated by information type than by aggregate accuracy alone; that the
transition region deserves explicit characterization rather than a single knee or
width; that window size is insufficient to predict empirical retrieval failure;
and that a memory system should be judged not only by what it retrieves but by how
it behaves when retrieval fails, where selective prediction and calibrated
abstention become relevant. The central open question is mechanistic - whether
AHN's shift toward abstention reflects a signal in the recurrent state or a
learned output policy - and it requires training-matched and ablation-based
comparisons that this study motivates but does not perform.
