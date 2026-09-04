# Task #1 — window / recurrent-memory verification: **PASSED**

**Owner:** Saadat + Juan · **Status:** `DONE` · **Date:** 2026-09-03
**Evidence:** live GPU run of `scripts/diag_ahn_window.py` (observe-only).

## Runtime environment

| | |
|---|---|
| platform | Google Colab, isolated Python 3.12 venv (`notebooks/colab_ahn_window_diagnostic.ipynb`) |
| GPU | NVIDIA **L4** (sm_89) |
| torch | 2.6.0+cu126 (CXX11-ABI-TRUE) |
| transformers | 4.51.0 |
| flash-attn | 2.8.3.post1 (prebuilt `cp312 torch2.6 abiTRUE` wheel; no source build) |
| triton | 3.2.0 |
| arm | `gated_deltanet` — `ByteDance-Seed/AHN-GDN-for-Qwen-2.5-Instruct-3B` merged onto `Qwen/Qwen2.5-3B-Instruct` |

## What the diagnostic established

| question | result |
|---|---|
| checkpoint loads | yes |
| AHN modules present & active | yes — 36 × `Qwen2MemDecoderLayer`, `layer[0].ahn` is `BaseAHN` with `fn = GatedDeltaNet`, `.ahn.` params present |
| model class | `ahn.transformer.qwen2_ahn.qwen2_ahn.Qwen2ForCausalLM` (custom, not stock) |
| window reported by the merged checkpoint (pre-override) | 256 |
| our override effective | yes — `effective_window(model) == 256`, `model.training == False` |
| matched inference config applied | `sliding_window_type=fixed`, `ahn_position=prefix`, `num_attn_sinks=0`, stale `dy_*` deleted (open_decisions #12) |
| exact/recurrent split correct | yes — below-window trajectory → `exact_memory`, above-window → `recurrent_memory` |
| **AHN recurrent path engaged only when the target is past the window** | **yes** — see the two trials below |
| both retrieval trials ran | yes |
| verdict | `PASS = true` |

## The two trials (item `numerical_0000`, gold `100000`)

| field | exact-memory trial | recurrent-memory trial |
|---|---|---|
| prediction | `100000` | `I don't know` |
| `answer_canonical` | `100000` | — |
| `correct` | 1 | 0 |
| `abstained` | 0 | 1 |
| `malformed` | 0 | 0 |
| `confidence` | — | 0.948433 |
| `ahn_layer0_num_cached_tokens` | **0** | **1906** |
| `ahn_kernel_forward_calls` | **0** | **5** |
| `ahn_kernel_positions` | — | `[1902, 1, 1, 1, 1]` |
| `expected_recurrent_positions` | — | 1853 |

The exact trial recalls the ID from the lossless window and the AHN recurrent kernel
never fires (`num_cached_tokens = 0`, `forward_calls = 0`). The recurrent trial pushes the
target ~2048 distractor tokens past the 256-token window; the AHN kernel processes ~1902
positions at prefill plus one per decode step. **The compression the whole experiment
depends on is real and is driven by `config.sliding_window = 256`.**

> **Prompt wording note (added 2026-09-03).** The two model responses quoted above
> (`100000`; `I don't know`) were generated under the prior shared abstention clause
> (`If the answer is not stated above, …`). That clause was reworded on 2026-09-03
> (`open_decisions.md` #7 / #7a) after the staged pilot. This artifact is **not**
> regenerated: the recurrent-path conclusion depends on token-count-driven signals
> (`ahn_kernel_forward_calls` 0 → 5, `ahn_layer0_num_cached_tokens` 0 → 1906), not on
> the generated text, and stands unchanged.

## Interpretation notes (audited 2026-09-03, no methodology change)

### 1. Why `num_cached_tokens` (1906) ≠ `expected_recurrent_positions` (1853) — a fixed 49-token offset

They measure different reference points; both are correct.

- **`ahn_layer0_num_cached_tokens` / `ahn_kernel_positions[0]`** — positions the AHN module
  actually processed = **`total_model_input_tokens − effective_window`** at prefill
  (`n_full − 256 = 1902`), plus 1 per decode step (`+4` → 1906). It is counted from the
  **start of the entire tokenised model input** (chat-template system/user prefix, the
  "You are given…" header, `"- "` + the target sentence, then everything after).
  In `mem_forward_inference` (`qwen2_ahn.py`): `in_ahn_seq_len = cur_cache_size − sliding_window − num_attn_sinks`,
  and `cur_cache_size` is the layer-0 KV-cache length = the full prompt length at prefill.

- **`expected_recurrent_positions`** — `model_tokens_after_target − effective_window`
  (`2109 − 256 = 1853`). `model_tokens_after_target` (`dataset.build_trajectory`) counts only
  the tokens **after the end of the target fact** (distractors-after + `Question:` + the
  answer instruction + `I don't know` line + chat-template suffix). It is the H1/H2
  independent variable's model-token twin; it deliberately excludes the tokens *before and
  including* the target.

The gap is exactly `n_full − model_tokens_after_target` = the tokenised length of
"[chat-template prefix] + [prompt header] + `- ` + [target sentence]" ≈ **49 tokens**. It is
**constant per trajectory** (independent of compression pressure), so it never distorts a
degradation curve — it is a fixed additive offset between "positions the AHN compressed" and
"query/distractor tokens past the target."

**Action:** documentation only. The diagnostic's `PASS` used `> 0` comparisons, not exact
equality, so nothing was mis-judged. When the diagnostic is next edited, add a companion
field `expected_ahn_positions_total = context_tokens − effective_window` (≈ `n_full − 256`)
and note that `num_cached_tokens` should match *that*, not the target-relative
`expected_recurrent_positions`. **Do not change model behavior.**

### 2. What `confidence = 0.948433` means when the answer is `"I don't know"`

`evaluate._confidence` (mode `sequence_probability`) returns
`exp(Σ log P(token_i | context, token_{<i}))` over the tokens the model actually generated,
with greedy decoding (`do_sample=False`, `num_beams=1`). So it is **`P(the model's own output string)`** — here, `P("I don't know") ≈ 0.948`: given the compressed context it cannot recall
the ID from, the model is very sure that *declining* is the right output.

It is **not** `P(gold answer is correct)` and **not** a probability about answer correctness
at all. For an **answered** trial, `confidence ≈ P(asserted value)` is a usable proxy for
"how sure the model is of the value it gave." For an **abstention**, it is confidence in
*declining*, which is orthogonal to whether `100000` was retrievable.

**Implication for H3 / Sumiya's calibration:** ECE / Brier / CWR must be computed on
**answered** trials only — rows with `abstained == 1` or `malformed == 1` are excluded and
their rates reported separately (already the agreed plan; see open_decisions #7 / #15). This
recurrent trial is a concrete example of why: including it would create a spurious
"confidently wrong" point (`correct = 0`, `confidence = 0.948`) when the model was in fact
*confidently abstaining*. The scorer already emits `abstained`; H3 just has to honour it.
(The sequence- vs length-normalised confidence question — open_decisions #6 — is unaffected
by this run.)

## Full run JSON

Commit the verbatim `outputs/diag_ahn_window.json` from the passing Colab run alongside this
file as `protocol/diag_ahn_window_PASS.json` (regenerated artifact; kept here as provenance).
