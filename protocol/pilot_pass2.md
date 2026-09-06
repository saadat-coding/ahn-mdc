# Pilot Pass 2 — design, gates, analysis, stop conditions

**Owner:** Saadat · **Status:** `COMPLETE + HOSTILE-AUDITED (2026-09-05)`; methodology
corrections applied; **superseded by the frozen final design →
`protocol/final_experiment_design.md`** · **open_decisions:** #18
**Depends on:** measurement-coordinate correction (`c3285a6`), temporal repair (`26613ba`),
H2 methodology correction (`protocol/h2_threshold_decision_2026-09-04.md`)

> The four BLOCKERs below (final grid, seed count, #17, exact-memory control) were
> all frozen on 2026-09-05 — see `protocol/final_experiment_design.md`,
> `config/experiment.yaml` `final:`, and `config/final_design_manifest.json`. This
> document is retained as the plumbing/localization record.

Pilot Pass 2 is a four-arm **plumbing + localization** run on the repaired benchmark
and the corrected measurement coordinate. It is **not inferential evidence**.

The 1,760-row run completed and passed the hostile audit for pipeline / provenance /
scorer / trajectories / all four architectures. Analysis-layer corrections landed on
`saadat-pipeline-validation` (see §8). Still **BLOCKER before the inferential run**:
the final grid, the seed count, and the #17 / exact-memory-control decisions. After
those: methodology freeze → full experiment.

---

## 1. Design (frozen)

| | |
|---|---|
| items | **40** — 8 per fact type. `n_temporal = 8` ⇒ the exact `direction × position × density` 2×2×2 factorial (one item per cell). |
| fact types | numerical, temporal, entity-attribute, multi-hop, contradictory |
| seeds | `[0]` (pilot; clustered CIs will be NaN — Wilson intervals per cell instead) |
| architecture arms | transformer (Qwen2.5-3B, no AHN) · mamba2 · deltanet · gated_deltanet |
| pressure grid | **11 levels, specified in `model_tokens_after_target`** (not window multiples): `[170, 200, 225, 240, 255, 270, 290, 330, 430, 640, 1024]` |
| **total trials** | 4 arms × 40 items × 11 levels × 1 seed = **1,760** |
| held fixed | `max_new_tokens = 12` · scorer version (`evaluate.SCORER_VERSION`) · repaired temporal generator · production `_PROMPT` · target/distractor construction |

### Why 40 items (8/type), not 50

- `n_temporal = 8` gives the **exact** temporal 2×2×2 factorial. `n_items = 50`
  (n_temporal = 10) breaks it — 10 is not divisible by 8 — for a 25 % cost increase
  with no pilot-stage design benefit.
- 8 items keeps any single item ≤ 12.5 % of a per-(type, pressure, arm) cell, so no
  one item determines a cell result.
- 1,760 trials at 12 new tokens is a few L4-hours — a pilot, diagnosable before the
  full run.
- `statistics.min_cell_size = 30` is a **full-run** gate; at pilot N it is
  informational (same as `mini` / `pilot`).

### Pressure-band structure

| band | targets (model-tat) | purpose |
|---|---|---|
| exact anchor | 170, 200 | target fully inside exact attention — control accuracy |
| transition | 225, 240, 255, 270, 290 | dense around the diagnostic knee K ≈ 242 and floor ≈ 300 |
| early recurrent | 330, 430 | just past the transition |
| deep recurrent | 640, 1024 | 2.5× / 4× W — retention floor |

Anchored on the gated_deltanet near-window diagnostic (exploratory, single arm):
`model_tat ~166 → 1.00 | ~200 → .95 | ~231 → .65 | ~242 → .50 | ~261 → .10 |
~298 → 0 | ~354+ → 0`. **W = 256 is drawn as an architectural reference on every
figure, never as a predicted break** (see `protocol/h2_threshold_decision_2026-09-04.md`).

## 2. Calibrated requested grid

The scientific grid is in model-tat space. The runner converts each target to a
**per-fact-type** `requested_tokens_after_target` via
`config/pilot_pass2_calibration.json`, built by `scripts/pilot_pass2_dryrun.py`
(no model — the real Qwen2.5 tokenizer only).

Per-fact-type overhead (`model_tokens_after_target` at `requested = 0`, i.e. the
fixed question/instruction/chat-template block) **materially differs** — 53
(entity-attribute) to 63 (temporal), a 10-token spread on the scale of the
transition-band tolerance — so a single global `requested ≈ target − 70` mapping is
**not** used.

Calibration quality (dry run, 2026-09-04, `outputs/pilot_pass2_dryrun.json`):

| fact type | overhead (tok) | max median-error over 11 targets (tok) |
|---|---|---|
| numerical | 57 | 5 |
| temporal | 63 | 4 |
| entity-attribute | 53 | 6 |
| multi-hop | 56 | 5 |
| contradictory | 59 | 9 |

Per-item spread (whole-fact `_fill` granularity) mean |error| ≈ 7 tok, max ≈ 27 tok.
Transition-band tolerance = **15 model tokens** (median across items per
(type, target)); other bands 30. All targets within tolerance; trajectory nesting
holds for every item. **Known minor wrinkle:** `contradictory @ 225` realises a
median ≈ 234 (+9) — contradictory facts are ~2 sentences, so `_fill` cannot land
between ~215 and ~234; still within tolerance and in the correct band.

**Before any GPU generation** the runner re-runs the no-model verification
(`--preflight`) and aborts if a transition-band target is off by more than the
tolerance or if nesting is broken. Re-run `scripts/pilot_pass2_dryrun.py` to
recalibrate if `generate_items`, the prompt, or the tokenizer changes.

## 3. What Pilot Pass 2 answers

1. Does every architecture run end-to-end over the final benchmark?
2. Are the intended `model_tokens_after_target` regions actually hit?
3. Is the degradation transition visible across arms?
4. Does any recurrent architecture retain measurable accuracy materially past W?
5. Are fact-type differences large enough to justify type-specific full-run sampling?
6. Does production abstention track strict-accuracy collapse similarly across arms?
7. Scorer / malformed / schema / data-quality anomalies?
8. Cell sizes and matched design?

## 4. Hard plumbing gates (`pilot_pass2.plumbing_gates`)

A **FAIL** here means the run is not analysable — stop and fix. Exit non-zero.

| gate | fails when |
|---|---|
| `trial_count` | rows ≠ arms × items × targets × seeds |
| `schema_valid` | core/h1/h2/h3 columns missing, flags not 0/1, or a duplicate design cell |
| `provenance:*` | `requested_tokens_after_target`, `model_tokens_after_target`, `target_fact_tokens`, `n_new_tokens`, or `intended_model_tokens_after_target` missing or null |
| `scorer_version` | any row is not the frozen `SCORER_VERSION` |
| `no_duplicate_cells` | duplicate `(arm, item, seed, intended target)` |
| `matched_design` | arms do not see identical `(item, target, seed)` cells |
| `all_targets_present` | the 11 intended targets are not all realised |
| `trajectory_nesting` | a lower-pressure distractor block is not a prefix of the higher-pressure block (from the dry-run verify frame) |
| `grid_realised` | a `(fact_type, target)` median `model_tat` is outside band tolerance |
| `temporal_factorial_balance` | the temporal `direction × position × density` 2×2×2 is not exactly one item per cell |
| `no_answer_leakage` | `assert_no_collision` fails for any item |
| `compression_occurred` | no trial reaches `model_tat ≥ W` |
| `malformed_rate:<AHN arm>` | an AHN arm > 10 % malformed |
| `malformed_control:<no-AHN arm>` | a hard-window control arm > 10 % malformed **and** not sane at the deep in-window anchor / not pressure-localised (a real parser break). > 10 % *with* a sane in-window anchor is `CONTROL_BEHAVIOR`, non-blocking (§8-E). |
| `malformed_no_parser_break` | ≥ 2 arms > 10 % malformed at the deep in-window anchor |

`malformed_pooled` is `REPORT` only (dominated by any hard-window control arm). The
10 % constant is unchanged — it is the plumbing-smell threshold.

### Scientific warnings (`pilot_pass2.scientific_warnings`) — never fail the run

Low recurrent accuracy · non-monotonic abstention (on the **balanced** grid) ·
per-arm knee spread (AHN arms; control K reported separately) · per-type knee
spread · residual exact-memory failures · architecture differences. **Results, not
plumbing errors.**

## 5. Analysis outputs (`pilot_pass2.analyse`)

Immutable raw: `outputs/pilot_pass2.parquet` (+ `outputs/pilot_pass2_items.json`).
All tables aggregate **one balanced cell per intended model-tat target**
(`schema.pressure_group_key`), plotted / fitted against realised
`model_tokens_after_target`.

| file | contents |
|---|---|
| `pilot_pass2_summary.json` | trials, arms, per-arm K (strict + abstention, separately), drop width, per-type K, grouping note |
| `pilot_pass2_h1*` | strict accuracy · abstention · malformed · **answered-valid** accuracy by arch × type × pressure. `_transition_drop` = per-type accuracy drop across `[W−76, W+34]`. **No baseline-adjusted metric** (#17 open). |
| `pilot_pass2_h2_curves*` / `_h2_anchors*` | strict-accuracy curves on model-tat; recurrent-anchor accuracy + Wilson95. W as reference; **no 768 line**. |
| `pilot_pass2_knees_by_arm* / _by_fact_type*` | exploratory K (isotonic 0.5 crossings, strict + abstention), 0.9→0.1 width. K ≠ W. |
| `pilot_pass2_knees_boundary*` | per-arm outcome rates across coarse `memory_condition`, the span-aware flags, and the deep-in-window anchor — the anchor is the cleanest empirical control (all arms ≈ ceiling, kernel inert), **not** a redefinition of "exact memory". |
| `pilot_pass2_knees_residual_fully_exact_failures*` | every row with `target_fully_exact_through_generation` yet `correct == 0`, listed (open audit finding — no mechanism attributed). |
| `pilot_pass2_knees_temporal*` | per temporal item: `gold_is_higher / gold_first_listed / distractor_density` × `strict / abstention / answered-valid` + factor marginals. Documents the counterbalanced model response bias. |
| `pilot_pass2_h3_answered_valid*` | factual ECE / Brier / CWR over **answered-valid only** (`abstained == 0 AND malformed == 0`). |
| `pilot_pass2_h3_abstention*` | abstention rate + confidence-in-"I don't know", **separate** — not factual confidence. |
| `pilot_pass2_h3_malformed*` | malformed rate + its (low) confidence, **separate**. |

## 6. Stop conditions (Task G)

Do **not** redesign the benchmark again unless the dry run or Pilot Pass 2 exposes:

- actual answer leakage;
- invalid matching / broken trajectory nesting;
- scorer failure;
- compression not occurring;
- schema / provenance failure;
- another **demonstrable construct-validity** problem.

Performance that is surprising is **not** itself a reason to change the benchmark.
Surprising performance is a result to report. The goal after Pilot Pass 2 is
**methodology freeze → full experiment**.

## 7. Running it

```bash
# no GPU — fabricated frame through gates + analysis
python scripts/run_pilot_pass2.py --self-test

# no GPU — recalibrate / re-verify the grid
python scripts/pilot_pass2_dryrun.py --repo .

# real run (Colab L4, isolated venv)
python scripts/run_pilot_pass2.py --repo /content/ahn-mdc --ahn-repo /content/AHN
# staged, one or more arms at a time (parquet is merged by arm):
python scripts/run_pilot_pass2.py --arms transformer gated_deltanet
```

## 8. Post-run methodology corrections (2026-09-05, hostile audit)

Applied on `saadat-pipeline-validation` (analysis layer only — items / prompt /
scorer semantics / temporal generator / W=256 all untouched):

- **A · Grouping.** Per-fact-type calibration gave `requested_tokens_after_target`
  ~36 distinct values for the 11-level grid; grouping on it fragmented balanced
  n=40 cells. New `schema.pressure_group_key` (`intended_model_tokens_after_target`
  → `requested_tokens_after_target` → `tokens_after_target`) — H1/H2/H3/warnings/
  stats now aggregate one balanced cell per intended target. Legacy mini/pilot/
  full frames unchanged.
- **B · H2.** On the balanced grid the artifact gives AHN K_strict **244–246**
  (per-arm spread ~2, not ~20), abstention K **250–252**, transformer K **213**,
  width **93 / 68**. `non_monotonic_abstention` no longer fires for the AHN arms.
  K stays distinct from W; no T restored.
- **C · H1.** New `h1_degradation.transition_slope` / `transition_drop` over an
  **explicit** `model_tokens_after_target` band (default `[W−76, W+34]`, a pilot
  convenience — **the inferential run must pre-register its band or grid**). Legacy
  recurrent-only `slopes` marked deprecated (returns ~0 at the accuracy floor).
- **D · H3.** Three populations: `answered_valid` (abst==0 & malformed==0),
  `abstained`, `malformed`. Factual ECE/Brier/CWR = answered_valid only by default.
  Answered-valid exact-memory ECE ≈ 0.08–0.12, CWR ≈ 0.05–0.15; all-row ECE
  (0.26–0.47) is meaningless.
- **E · Malformed gate reframe** (§4): per-arm; transformer control degeneration
  past its window is `CONTROL_BEHAVIOR`, non-blocking; a true parser break still
  BLOCKs. On the artifact: AHN PASS, transformer CONTROL_BEHAVIOR, blocking empty.
- **F · Boundary.** `schema.deep_in_window_anchor` + a boundary table; residual
  fully-exact failures kept visible.
- **G · "multi-hop" → "compound relational"** for paper-facing output
  (`report.fact_type_label`); raw `fact_type` value unchanged. It is a co-located
  two-clause target sentence, **not** distributed multi-hop reasoning.
- **H · Temporal response-bias table** (`report.temporal_response_table`).
- **I · `metrics.baseline_adjusted_accuracy(df, baseline)`** — explicit baseline,
  never reads config chance. `chance_corrected_accuracy` deprecated.

### Findings that must inform the final design (not yet actioned)

| finding | action needed before the inferential run |
|---|---|
| 6 / 11 grid levels at the accuracy floor; the AHN-vs-transformer transition (realised model-tat ~215–255) sampled by ~2 points | **freeze a denser transition grid** (candidate: `[150,175,195,210,220,230,240,250,260,275,300,340,480,850]` — NOT frozen; see #18) |
| 1 seed → every clustered CI NaN | full run needs ≥ 5 seeds (`run_modes.full` already `[0,1,2,3,4]`) |
| even `target_fully_exact_through_generation` fails 21–37 % | the exact-memory acceptance control = the deepest in-window level (realised model-tat ~170, all arms ≈ 0.90); apply the `#5a` reframe or its successor |
| temporal in-window over-abstention on 3 items (temporal_0001/_0026/_0036 — high-confidence "I don't know", identical across arms) | keep + report via the temporal table; **do not redesign temporal**; decide whether to investigate the wording interaction |
| #17 baseline/null unresolved | keep raw strict accuracy primary; `baseline_adjusted_accuracy` optional/explicit; temporal 0.5 ≠ free-response null |
| per-fact-type calibration makes group key and realised x diverge ±30 tok | the inferential run should use a single global requested grid **or** explicitly report the per-type model-tat drift |
