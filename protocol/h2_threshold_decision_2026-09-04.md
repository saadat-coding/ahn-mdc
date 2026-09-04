# H2 methodology correction — decision record

**Date:** 2026-09-04 · **Owner:** Saadat · **Type:** team-owned methodology decision
(no supervisor sign-off required) · **Supersedes:** the "published anchor T ≈ 768"
framing in `protocol/h2_threshold.md` §1–§5 and `open_decisions.md` #3.

---

## 1. Why the 50-fact → 768-token conversion was rejected

The working H2 threshold was

```
T ≈ 50 facts × 15.37 tokens/fact ≈ 768 model tokens
```

The "50 facts" input was attributed to Khandelwal et al., *Sharp Nearby, Fuzzy Far
Away* (arXiv:1805.04623). On inspection that paper does not support it:

- It reports, for an **LSTM language model**, that word **order** stops affecting
  perplexity beyond roughly the most recent **~50 tokens**, and that usable context
  is on the order of **~200 tokens**. The unit is tokens, not facts.
- It is a context-ablation / perplexity study on an LSTM. It does not measure
  retrieval accuracy, does not concern AHN, and defines no recurrent-memory
  saturation threshold.

So the conversion multiplied a misread quantity (50 *tokens*, from a different
architecture and a different measurement) by a token/fact ratio to produce a
fact-after-target count, and then converted that back to tokens. There is no
published AHN retention-capacity threshold behind the 768 number.

**Decision:** `768` is retired as a *validated literature threshold*. It is not
deleted — its derivation and history stay in `config/experiment.yaml`
(`threshold:` block, now `status: DEPRECATED`) and in `protocol/h2_threshold.md`
Appendix A — but it is removed from primary H2 interpretation. No new "T" value is
minted. The ~50-token LSTM result is retained only as background/comparison and
only if a genuinely relevant AHN threshold source is found later.

## 2. Three quantities that must stay separate

| symbol | value | status | meaning |
|---|---|---|---|
| **W** | 256 model tokens | known, design-fixed | architectural sliding-window boundary. `models.sliding_window.force = 256`. Everything ≥ W tokens before the prompt end is compressed into the AHN recurrent state at prefill; one more position per decode step. |
| **K** | ≈ 242 model tokens (gated_deltanet, near-window diagnostic) | **exploratory, per-run empirical output** | the model-tat position where strict retrieval accuracy passes 0.5 in a monotone descriptive fit. Measured post hoc during grid localization. Not an architectural constant; expected to differ by arm and possibly by fact type. |
| literature context | ≈ 50 tokens (LSTM order-sensitivity) / ≈ 200 tokens (usable context) | background only | Khandelwal et al. 2018. Comparability to an AHN recurrent state is unestablished. Not used to predict AHN failure. |

`K ≈ W` was **observed** in the gated_deltanet diagnostic. It was not predicted.
Any statement of the form "H2 predicts collapse at W" is therefore wrong: W was not
named as a predicted break in any pre-registered protocol. A W-centred reading is
exploratory unless and until a protocol independently specifies it beforehand.

## 3. Why the near-window diagnostic is localization evidence, not confirmatory H2 evidence

The near-window diagnostic (gated_deltanet, ~180 trajectories around W) was run to
**locate** where accuracy changes so the Pilot Pass 2 grid could be placed
sensibly. It:

- used a single architecture;
- used a grid chosen *after* seeing earlier pilot behaviour;
- had one seed and 8 items per pressure cell (no clustered CI);
- reported a monotone descriptive fit, not a hypothesis test.

Reading a changepoint off that curve and then testing "is there a break there?" on
the same family of data is self-defining the threshold — exactly the failure mode
the original protocol's "take T from the literature" rule existed to avoid. The
diagnostic's K ≈ 242 and "floor by ≈ 300" are **design inputs to Pilot Pass 2**,
carried forward as exploratory observations, never as H2 results.

## 4. Revised H2 operational definition

**H2 primary question.** As target information moves away from exact attention and
into AHN recurrent memory, is retrieval degradation concentrated in a relatively
narrow transition region, or distributed gradually across increasing memory
pressure?

**Exploratory architecture question.** Do AHN recurrent mechanisms differ in where
the empirical transition occurs, or in how much retrieval remains after the target
leaves exact attention?

Operationalisation (all on `model_tokens_after_target`, the canonical scientific
pressure coordinate; `requested_tokens_after_target` is the design/matching key):

1. **Descriptive transition curve.** Per arm, strict accuracy against
   `model_tokens_after_target`, aggregated at the balanced requested levels, with a
   monotone (isotonic) descriptive fit. Report the 0.9→0.1 drop location and width.
   W is drawn as a labelled architectural reference line. No 768 line.
2. **Shape comparison (retained, reframed).** `h2_threshold.shape_test` still
   compares a single smooth log-linear fit against one allowed to change slope at a
   **stated** break. The break is now an explicit analysis parameter, disclosed as
   such — not "the published T". Primary break = W (the one non-self-defined
   reference we have); K is reported alongside as a sensitivity value. A narrower
   transition than the smooth fit predicts supports the "threshold-like" reading of
   the primary question; a gradual fit supports "distributed".
3. **Exploratory per-arm K.** `h2_threshold.knees` reports, per arm and pooled per
   fact type, the isotonic-fit 0.5 crossing for strict accuracy and (separately)
   for abstention rate, with the transition width as a descriptive pilot quantity.
   Labelled exploratory.
4. **Retention past exact attention.** Accuracy at the early- and deep-recurrent
   anchors, per arm, with Wilson intervals. Answers "does any recurrent mechanism
   retain measurable accuracy materially past W?".

What is **not** claimed: that degradation must collapse at any particular token
count; that the literature predicts an AHN break; that K is an architectural
constant.

## 5. What Pilot Pass 2 is meant to establish

Pilot Pass 2 is plumbing + localization for all four arms, not inferential H2
evidence. It should answer:

1. every architecture runs end-to-end over the final benchmark;
2. the intended `model_tokens_after_target` regions are actually realised;
3. the degradation transition is visible across arms;
4. whether any recurrent arm retains measurable accuracy materially past W;
5. whether fact-type differences are large enough to justify type-specific
   sampling in the full run;
6. whether production abstention tracks strict-accuracy collapse similarly across
   arms;
7. scorer / malformed / schema / data-quality anomalies;
8. cell sizes and matched design.

After Pilot Pass 2: methodology freeze → full experiment. The benchmark is not
redesigned again unless the dry run or Pilot Pass 2 exposes a demonstrable
construct-validity problem (leakage, invalid matching, scorer failure, compression
not occurring, schema/provenance failure). Surprising performance is a result, not
a trigger.
