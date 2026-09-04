# H2 — Threshold-like vs gradual degradation in AHN recurrent memory

**Owner:** Juan / team · **Hypothesis:** H2 · **Status:** `OPERATIONALISED (2026-09-04)`,
Pilot Pass 2 pending

This protocol was revised on 2026-09-04. The earlier version anchored H2 on a
"published threshold T ≈ 768 model tokens" derived as `50 facts × 15.37 tokens/fact`.
That derivation is **unsupported** (see `protocol/h2_threshold_decision_2026-09-04.md`)
and has been retired from primary interpretation. Its history is preserved in
Appendix A and in `config/experiment.yaml` (`threshold: status: DEPRECATED`).

---

## 1. The scientific idea (unchanged)

Retrieval from AHN's compressed memory may degrade **non-linearly** — comparatively
stable while the target is near exact attention, then dropping over a relatively
narrow band of compression pressure — rather than smoothly across increasing
pressure. The recurrent architecture may change *where* that happens and *how much*
retrieval survives.

## 2. What we do **not** assume

- We do **not** assume degradation collapses at any particular token count.
- We do **not** claim any published result predicts an AHN failure point.
- `K ≈ 242` (the near-window diagnostic knee) was **observed**, not predicted; it is
  an exploratory per-run quantity, not an architectural constant, and it does not
  redefine anything.
- The sliding-window boundary **W = 256** is a known architectural reference. A
  hypothesis of the form "H2 predicts collapse at W" would be exploratory — no
  pre-registered protocol named W as a predicted break.

## 3. Three quantities, kept separate

| symbol | value | role |
|---|---|---|
| **W** | 256 model tokens | architectural sliding-window boundary (design-fixed). Drawn as a reference line on every H2 figure. |
| **K** | per-run empirical output (≈ 242 for gated_deltanet in the diagnostic) | isotonic-fit 0.5 crossing of strict accuracy vs `model_tokens_after_target`. Exploratory. Reported per arm and pooled per fact type. |
| literature context | ~50 tokens (LSTM order sensitivity), ~200 tokens (usable context) — Khandelwal et al. 2018 | background/comparison only. Not an AHN threshold. |

## 4. H2 as operationalised

Everything is measured on `model_tokens_after_target` (canonical scientific pressure
coordinate). `requested_tokens_after_target` is the design / matching key. All four
arms see byte-identical items; trajectories are nested (a lower-pressure distractor
block is a prefix of a higher-pressure one for the same item/seed).

### 4.1 Primary question

> As target information moves away from exact attention and into AHN recurrent
> memory, is retrieval degradation concentrated in a relatively narrow transition
> region or distributed gradually across increasing memory pressure?

**Analysis.**

| output | function | what it shows |
|---|---|---|
| strict-accuracy curve on model-tat, per arm | `h2_threshold.curves` | the descriptive degradation shape; W drawn as reference |
| monotone (isotonic) descriptive fit + 0.9→0.1 drop location & width | `h2_threshold.knees` | where and how sharply accuracy falls |
| smooth vs break-allowed fit (AIC) | `h2_threshold.shape_test` | narrower-than-smooth ⇒ "threshold-like"; comparable ⇒ "gradual". Break is an **explicit, disclosed analysis parameter** (primary: W; sensitivity: K), not a claimed published value. |

### 4.2 Exploratory architecture question

> Do AHN recurrent mechanisms differ in where the empirical transition occurs, or in
> how much retrieval remains after the target leaves exact attention?

**Analysis.**

| output | function | what it shows |
|---|---|---|
| per-arm exploratory K (strict accuracy 0.5 crossing; abstention 0.5 crossing, separately) | `h2_threshold.knees` | do arms transition at different model-tat? |
| accuracy at early-recurrent and deep-recurrent anchors, per arm, Wilson95 | `h2_threshold.summary` / knees table | does any recurrent mechanism retain measurable accuracy materially past W? |
| paired arm-vs-arm differences under conservative recurrent trials | `h2_threshold.architecture_comparisons` | ordered architecture effect (exploratory at pilot N) |

Strict retrieval accuracy is the memory-degradation outcome. Abstention rate is the
behavioural co-outcome — reported **beside** accuracy, never collapsed into it. If
their transitions differ materially, that difference is preserved and flagged to H3.

## 5. Deprecated `drop_at_threshold` semantics

`h2_threshold.drop_at_threshold` and `shape_test` still exist and still take a
`threshold_tokens` argument. After 2026-09-04 that argument is a **stated analysis
parameter** — the caller passes W (primary) or K (sensitivity) and the report
labels it as such. `config.compression_threshold(strict=True)` still raises (the
768 derivation is not a valid input); `strict=False` still returns the deprecated
768 value but only as a pressure-grid backstop for the legacy `mini` plumbing mode,
never as an H2 reference line.

## 6. Interaction with the accuracy targets

Unchanged from the mentor's constraint, enforced by `report.gate_report` for the
`full` run: exact-memory (control) accuracy 70–80 % defensible, ≤ 85 % acceptable,
≥ 90 % red flag. See `open_decisions.md` #5a for the proposed per-fact-type reframe
(separate decision, not part of this revision).

---

## Appendix A — Deprecated: the 50-fact / 768-token derivation (history)

Retained for the record. **Not** a valid H2 input.

The earlier protocol required T from a published paper and used a working value of
"50 facts after the target", converted once to tokens:

```
T ≈ 50 × threshold.tokens_per_fact.measured (15.37) ≈ 768 model tokens ≈ 3.0 W
```

`config/experiment.yaml` still carries `threshold: {facts: 50, tokens_per_fact:
{measured: 15.37}}` with `status: DEPRECATED` so the arithmetic is reproducible.

**Why it was retired (2026-09-04):** the "50" was attributed to Khandelwal et al.
2018 (arXiv:1805.04623), which actually reports ~50 *tokens* of order sensitivity in
an **LSTM** perplexity study — not 50 facts, not retrieval accuracy, not AHN, and
not a recurrent-memory saturation threshold. Full reasoning:
`protocol/h2_threshold_decision_2026-09-04.md`.

**Original verification checklist (never completed, kept for history):**

- [ ] Read the PDF, not the abstract.
- [ ] Top-tier venue.
- [ ] Number stated in the paper, not inferred from a figure.
- [ ] Unit recorded; fact→token conversion measured.
- [ ] T above one sliding window on the merged checkpoint.
- [ ] Same T applied to all four arms.
- [ ] Pressure grid brackets T on both sides.
- [ ] BibTeX added.

If a genuinely relevant published AHN (or long-context recurrent-memory) threshold
is found later, it can be added as a **secondary comparison line** — it does not
re-block H2.
