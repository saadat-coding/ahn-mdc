# Temporal benchmark repair — validation record

**Owner:** Saadat · **Status:** `DONE` · **Date:** 2026-09-04
**open_decisions:** #7b · **Repair commit:** `26613ba` · **Evidence:** 96-trial forced-answer GPU run (`gated_deltanet`)

---

## Why the repair was needed

The forced-baseline diagnostic (2026-09-03, 252 trials) showed the `temporal` fact
type was **target-independent**: its question listed the gold first on every item, so
"pick the first-listed name" scored ~100% with no fact present. The first repair
(`03e68f0`, question-order balancing) fixed the position half but the fact was still
always `Person_i arrived before Person_{i+1}` with `gold = Person_i` — the gold was
the **lower-numbered** candidate on 12/12 generated items, so "pick the
lower-numbered name" remained a perfect target-independent shortcut
(target-removed forced accuracy 0.83–0.92).

**Key distinction (methodology).**

1. **Dataset shortcut / leakage** — a nuisance feature predicts the gold *above
   chance* because of how the dataset is built. Benchmark-invalidating.
2. **Model response bias** — the model *prefers* a nuisance feature that is
   orthogonal / counterbalanced to the gold. A property of the model, to be
   reported, not engineered away.

The order-only design had #1. The revised design removes #1 and leaves #2 visible.

---

## Structural design (commit `26613ba`)

`temporal(i, swap_candidates, earlier_is_higher)`:

- `earlier_is_higher` — whether the earlier arriver (and gold) is the higher- or the
  lower-numbered identity.
- `swap_candidates` — whether the gold is listed first or second in the question.
- Construct unchanged: one `"<earlier> arrived before <later>"` relation, question
  `"Who arrived first, A or B?"`. Gold is `early`. Scorer unchanged (order- and
  magnitude-agnostic).

`_temporal_factor_plan(n_temporal, seed)` assigns `(earlier_is_higher,
swap_candidates)` per temporal item, **stratified by the existing low/high density
split** (`slot % 2`), shuffling blocks of the four cells with an RNG keyed on
`(seed, stratum, block)`:

- exact per-density 2×2 when a stratum count is divisible by 4;
- full `direction × position × density` 2×2×2 when `n_temporal` is divisible by 8;
- each marginal exact when a stratum count is even (the pilot's 100 and this run's 16
  both qualify);
- **not** a periodic function of the slot or the Person numbers (verified: `eih` rate
  by `slot % {2,4,8}` and `Person % {2,4,8}` = 0.47–0.54 across 4000 planned items);
- deterministic per seed; a different seed reshuffles while preserving balance.

**Distractor direction.** Temporal-typed distractor sentences alternate relation
direction via a local counter (`bool(temporal_dir % 2)`) — no extra shared-RNG draw.
The density gate and `_leaks_answer` decision are byte-identical, so the shared
distractor RNG trajectory and every non-temporal distractor are byte-identical
(regression test `test_non_temporal_distractors_and_rng_stream_unchanged`).

### Selected validation set — `generate_items(80, seed=0)`, 16 temporal items

| property | value |
|---|---|
| lower-gold / higher-gold | 8 / 8 |
| first-listed-gold / second-listed-gold | 8 / 8 |
| distractor density low / high | 8 / 8 |
| each `direction × position × density` cell | exactly 2 |
| temporal distractors (n≈1646 across the 16 pools) | 825 lo-first / 821 hi-first |
| distractors naming a queried identity (`Person_i` / `Person_{i+1}`) | **0** |
| `assert_no_collision` over all 16 | PASS |

---

## 96-trial validation (`gated_deltanet`, forced-answer prompt)

16 items × requested `{128, 384, 768}` × `{target_present_forced,
target_removed_forced}`. `target_present_forced` = production `_PROMPT` minus the
abstention line; `target_removed_forced` = the same, with the target sentence deleted
(question + distractors kept). Scorer / generation config unchanged.

### Construct — target present

| | accuracy | Wilson95 |
|---|---|---|
| present @128 (exact memory) | **15 / 16 = 93.75%** | [0.72, 0.99] |
| — subgroup `gold_is_higher = False` | 8 / 8 | |
| — subgroup `gold_is_higher = True` | 7 / 8 | (one miss; 12.5% subgroup gap, CIs overlap heavily) |

### Target-removed forced accuracy (the empirical uninformed baseline)

| requested | accuracy | Wilson95 |
|---|---|---|
| 128 | 7 / 16 = 43.75% | [0.23, 0.66] |
| 384 | 8 / 16 = 50.00% | [0.28, 0.72] |
| 768 | 7 / 16 = 43.75% | [0.23, 0.66] |
| **pooled** | **22 / 48 = 45.83%** | **[0.326, 0.597]** |

Stable around chance across pressure; **statistically compatible with the two-way
chance rate of 0.5**.

### Target-removed accuracy by subgroup (pooled over levels)

| subgroup | accuracy |
|---|---|
| `gold_is_higher = False` (gold is lower) | 79.17% |
| `gold_is_higher = True` (gold is higher) | 12.50% |
| `gold_first_listed = True` | (elevated — see bias) |
| `gold_first_listed = False` | (depressed — see bias) |
| `distractor_density = low` | 45.83% |
| `distractor_density = high` | 45.83% |

The `gold_is_higher` split (79% vs 12.5%) is the model's lower-numbered preference
made visible **through a counterbalanced feature** — it averages to ~46% ≈ chance and
does not touch benchmark validity. Density has **exactly zero** effect.

### Documented model response bias (target-removed, pooled n=48)

| heuristic | rate |
|---|---|
| chose the **lower-numbered** candidate | **83.3%** |
| chose the **first-listed** candidate | **66.7%** |

Absent a determinative fact, `gated_deltanet` + Qwen2.5-3B-Instruct prefers the
lower-numbered / first-mentioned name under this prompt. Both features are exactly
counterbalanced against the gold in the dataset (8/8), so the bias nets to
chance-level accuracy and **does not bias the benchmark**. Reported here as a model
property; not to be removed.

### Recurrent retrieval advantage

| | present | removed | Δ |
|---|---|---|---|
| pooled @{384, 768} (recurrent) | 45.83% | 45.83% | **0.00** |
| item-bootstrap 95% CI on Δ | | | **[0.00, 0.00]** |

The compressed target confers **no measurable advantage** over having no target at
all, at the two sampled recurrent pressures (≈ 1.7× / 3.2× W in
`model_tokens_after_target`).

---

## Verdict

**`VALIDATED WITH DOCUMENTED RESPONSE BIAS`.**

- **Benchmark valid:** no nuisance feature (direction, position, density — all 8/8
  balanced) predicts the gold above chance; pooled target-removed accuracy does not
  exceed 0.5; no target leakage (relational check = 0). The construct works in-window
  (93.75%).
- **Response bias documented:** lower-numbered (83.3%) / first-listed (66.7%)
  preference, counterbalanced, net-to-chance.
- **Temporal is H1 branch A on `gated_deltanet`:** through this forced-answer
  interface, at these recurrent pressures, the AHN recurrent state carries **no
  usable target-specific temporal-ordering information** — the same outcome
  established for numerical, entity-attribute, multi-hop and contradictory.

**Scope.** One arm (`gated_deltanet`); two recurrent pressures; greedy decoding,
`max_new_tokens = 12`; n = 16 items; forced-answer prompt. "No measurable advantage"
is not "the state contains zero temporal information." In-window accuracy may partly
reflect a "name the first party in the stated relation" reading rather than reasoning
about *before*; this does not affect the degradation measurement (both require the
fact present). Cross-arm confirmation folds into Pilot Pass 2.

---

## Consequences

- **open_decisions #7b → `DONE`.** Temporal is back in the benchmark.
- **open_decisions #17** — this run confirms `temporal` theoretical chance 0.5 and
  supplies its empirical null (0.458). H1 cross-type comparison uses an empirical
  target-removed null per type, not a 0.2 free-response chance.
- **H1 reporting** — raw production strict accuracy and abstention rate stay primary;
  `baseline_adjusted_accuracy = (accuracy − empirical_null) / (1 − empirical_null)` is
  the cross-type comparability layer, defined on **forced / answered-only** accuracy
  (never on production strict accuracy, which folds in abstention). Under the
  production prompt temporal *abstains* past the window (strict accuracy → ~0, not
  0.5); the 0.458 floor is a forced-answer property and must be cited as such.
