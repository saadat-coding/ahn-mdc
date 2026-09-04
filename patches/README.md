# Patch records

Retained as the reviewable record of a change and its rationale. Do not re-apply
a patch marked **APPLIED**.

---

## `matched-inference-config.patch` — **APPLIED 2026-09-03** — approved by **Juan** (open_decisions.md #12)

Frozen matched inference configuration: `sliding_window = 256`,
`sliding_window_type = fixed`, `ahn_position = prefix`, `num_attn_sinks = 0`.
Applied to `src/ahnexp/models.py`; guarded by `tests/test_matched_config.py`.
The unified diff below is the exact change, kept for provenance.

### What it changes
`src/ahnexp/models.py` only — `_force_window()` and `describe()`.

`_force_window()` additionally, right after it forces `sliding_window`:
- `model.config.sliding_window_type = matched["sliding_window_type"]`  (`"fixed"`)
- `model.config.ahn_position       = matched["ahn_position"]`          (`"prefix"`)
- `model.config.num_attn_sinks     = 0`
- `delattr` any `dy_sliding_window` / `dy_num_attn_sinks`
- the `verbose` line now prints the checkpoint's pre-normalisation values

`describe()` returns three new keys (`sliding_window_type`, `ahn_position`,
`num_attn_sinks`), which `assert_matched()` then compares across arms with no
change to `assert_matched()` itself.

`matched` comes from `config.experiment()["models"]["matched"]`, which already
declares `sliding_window_type: fixed` and `ahn_position: prefix`. `config` is
already imported in `models.py`. Nothing else is touched — no metrics, prompts,
dataset generation, H1/H2/H3 logic, or scoring.

### Why
The three AHN checkpoints ship the **training-time** values:

| field | GatedDeltaNet | Mamba2 | DeltaNet | matched (intended) |
|---|---|---|---|---|
| `sliding_window` | 256 | 256 | 256 | 256 (already forced) |
| `sliding_window_type` | `random` | `random` | `random` | `fixed` |
| `ahn_position` | `random` | `random` | `random` | `prefix` |
| `num_attn_sinks` | absent→0 | absent→0 | absent→0 | 0 |
| `dy_num_attn_sinks` (stale) | — | `128` | `128` | — |
| `dy_sliding_window` (stale) | — | — | `2048` | — |

So the loaded `model.config` objects are **not matched across arms**, and
`assert_matched()` does not currently look at any of these fields.

### Why it is safe (no inference-behaviour change)
Traced in `vendor/AHN` (all arms use `src/ahn/transformer/qwen2_ahn/qwen2_ahn.py`):

- `sliding_window_type` — read only at `qwen2_ahn.py:446`, inside
  `if self.training and self.layer_cls == "Qwen2MemDecoderLayer":` (`:444`).
- `ahn_position` — read only at `qwen2_ahn.py:474`, same `if self.training` block.
  Its only effect is choosing `num_attn_sinks`; at inference `num_attn_sinks`
  comes from `getattr(config, "num_attn_sinks", 0)` = 0, which is exactly what
  `ahn_position="prefix"` produces.
- `dy_sliding_window` / `dy_num_attn_sinks` — written and read only under
  `if self.training` (`:454/:457/:466`, `:676` under `:674`, `:871` under `:869`,
  `mem_forward_train`). Never read by `mem_forward_inference` or the inference
  branch of `pre_model_forward` (`:493`), both of which read `config.sliding_window`
  directly.

At `model.eval()` these fields are dead code. The patch is a config-integrity
normalisation that (a) makes the run log honest, (b) makes the arms byte-matched,
(c) removes the DeltaNet `dy_sliding_window: 2048` land-mine (inert today, one
eval-mode fallback away from giving DeltaNet a different window).

### Approval checklist (Juan)
- [ ] `fixed` / `prefix` is the intended inference protocol (not `linear`, and
      not a deliberate `random` for a robustness claim).
- [ ] `num_attn_sinks = 0` is correct for the exact/recurrent boundary rule.
- [ ] All three AHN checkpoints agree that these fields are training-time only
      (confirmed above from the checkpoint configs + source).
- [ ] OK to freeze these three fields and let `assert_matched()` enforce them.

### Apply
```bash
git apply patches/matched-inference-config.patch
uv run python -m unittest discover -s tests      # 84 pass, unchanged
uv run python -m ahnexp._smoke                   # blocking: 1, unchanged
```
Verified locally: applies cleanly, compiles, all 84 tests pass, `models.py` is the
only file changed.

### Relationship to the diagnostic
`scripts/diag_ahn_window.py` stays **observe-only** and does **not** apply this
patch at runtime. If you run the diagnostic before this patch lands, it reports
`sliding_window_type: random` / `ahn_position: random` in the pre/post block and
notes they are inert — that is expected and correct.

---

## `exact-memory-gate-reframe.patch` — **PROPOSED, NOT APPLIED** — awaiting **Juan**

Reframes the exact-memory acceptance gate from a pooled band that *penalises*
high accuracy to a **per-fact-type retrievability minimum** plus a
**target-removed validity check**. open_decisions.md #5a (new).

### What it changes
- `config/experiment.yaml` — `acceptance:` block:
  - `exact_memory_accuracy: {defensible: [0.70, 0.80], acceptable_max: 0.85, red_flag_at: 0.90}`
    → `exact_memory: {retrievability_min: 0.85, soft_floor: 0.70}` (no upper bound)
  - new `target_removed_validity:` with the frozen forced-baseline results
    (numerical / entity-attribute / multi-hop / contradictory = PASS; temporal = PENDING).
- `src/ahnexp/report.py` — `gate_report()`:
  - per-arm `exact_memory_accuracy` band + the `exact_memory_by_fact_type` WARN
    → per-fact-type `exact_memory_retrievability` (PASS ≥ 0.85 / WARN [0.70, 0.85) /
    FAIL < 0.70 / SKIP < 4 trials) + per-fact-type `target_removed_validity`
    (reads the config `validated` map) + `exact_memory_pooled` (verdict `REPORT`,
    never gated).
  - `_band_verdict` → `_retrievability_verdict` + `_validity_verdict`.
  - `blocking()` drops `RED_FLAG` (retired) → `["FAIL", "BLOCKED"]`.
- `tests/test_report_gates.py` — rewritten for the new gate names/semantics.

Nothing else — no prompts, dataset, scorer, metrics, window, matched config, or
H1/H2/H3 analysis.

### Why
The forced-baseline diagnostic showed that for numerical / entity-attribute /
multi-hop / contradictory, **exact-memory 100 % with target-removed forced
accuracy ≈ 0 is the ideal control** — it makes recurrent failures attributable to
compression, not baseline incompetence. The old `red_flag_at: 0.90` ("task
already solved by existing models") is a benchmark-*hardness* criterion; this
project's deliverable is mechanistic H1/H2/H3 claims. Pooling the five types also
hid temporal's 25–50 % exact-memory failure inside a ~0.85–0.90 average.

The right requirement is: (a) per type, the model can do the task in-window
(minimum, not maximum); (b) per type, removing the target collapses accuracy to
chance (validity / no shortcut). `target_removed_validity` is fed by the
forced-baseline diagnostics, not recomputed per run.

### Approval checklist (Juan)
- [ ] Replace the mentor's 70–80 % band with a per-type ≥ 0.85 retrievability
      minimum for this study (a high, *valid* baseline is desirable here).
- [ ] `soft_floor: 0.70` / `retrievability_min: 0.85` are the right cut points.
- [ ] `max_removed_forced_accuracy` 0.30 (free-response) / 0.65 (two-way) is a
      reasonable validity bound.
- [ ] OK to retire `RED_FLAG` from `blocking()`.
- [ ] The four `validated` PASS rows correctly reflect the forced-baseline result.

### Apply (after approval)
```bash
git apply patches/exact-memory-gate-reframe.patch
uv run python -m unittest discover -s tests      # 134 pass
uv run python -m ahnexp._smoke                   # blocking: 1, unchanged
```
Verified locally: applies cleanly, all 134 tests pass, `_smoke` `blocking: 1`
unchanged (synthetic `_smoke` accuracies ~0.75–0.80 now surface as
`exact_memory_retrievability` WARN, which does not block).
