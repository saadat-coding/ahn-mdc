# Pilot Pass 2 — design, gates, analysis, stop conditions

**Owner:** Saadat · **Status:** `FROZEN (2026-09-04)`, GPU run pending · **open_decisions:** #18
**Depends on:** measurement-coordinate correction (`c3285a6`), temporal repair (`26613ba`),
H2 methodology correction (`protocol/h2_threshold_decision_2026-09-04.md`)

Pilot Pass 2 is a four-arm **plumbing + localization** run on the repaired benchmark
and the corrected measurement coordinate. It is **not inferential evidence**. After
it passes plumbing: methodology freeze → full experiment.

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
| `malformed_rate_sane` | > 10 % malformed (a scorer/data smell) |

### Scientific warnings (`pilot_pass2.scientific_warnings`) — never fail the run

Low recurrent accuracy · non-monotonic abstention · per-arm knee spread · per-type
knee spread · residual exact-memory failures · architecture differences ·
high/low empirical knees. **These are results, not plumbing errors.**

## 5. Analysis outputs (`pilot_pass2.analyse`)

Immutable raw: `outputs/pilot_pass2.parquet` (+ `outputs/pilot_pass2_items.json`).

| file | contents |
|---|---|
| `outputs/pilot_pass2_summary.json` | trial count, arms, K per arm (strict accuracy + abstention, separately), drop width, K per fact type, provenance notes |
| `outputs/pilot_pass2_h1*` | strict accuracy · abstention rate · answered-only accuracy (secondary) by architecture × fact type × pressure. **No baseline-adjusted metric** (open_decisions #17 still partially resolved). |
| `outputs/pilot_pass2_h2_curves*` | strict-accuracy curves on `model_tokens_after_target`, per arm; W as reference; **no 768 line** |
| `outputs/pilot_pass2_h2_anchors*` | accuracy at early- and deep-recurrent anchors, per arm, Wilson95 |
| `outputs/pilot_pass2_knees*` | per-arm and per-fact-type exploratory K (isotonic-fit 0.5 crossing), transition width (descriptive) |
| `outputs/pilot_pass2_h3_answered*` | calibration on **answered** responses only (descriptive) |
| `outputs/pilot_pass2_h3_abstention*` | abstention rate and mean confidence-on-abstention vs confidence-on-answered, kept **separate** (confidence in "I don't know" ≠ P(factual answer wrong)); descriptive only unless Sumiya's final H3 definition is ratified |

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
