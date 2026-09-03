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
