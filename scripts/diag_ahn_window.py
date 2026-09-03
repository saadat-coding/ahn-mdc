#!/usr/bin/env python3
"""AHN window diagnostic — Task #1 (Saadat + Juan).

Proves, from a LIVE `gated_deltanet` checkpoint, that the AHN recurrent memory is
actually engaged and that our sliding-window override takes effect. It is a
diagnostic, not a paper experiment: one arm, two trajectories, two generations.

    # on Kaggle, after scripts/setup_kaggle.sh + kernel restart:
    python scripts/diag_ahn_window.py --repo /kaggle/working/ahn-mdc --ahn-repo /kaggle/working/AHN

    # logic-only check, no GPU / no model (runs anywhere):
    python scripts/diag_ahn_window.py --self-test

Answers, with evidence printed inline:
  1 checkpoint loads            5 effective window used by inference
  2 AHN modules present/active  6 trajectory with model_tokens_after_target < window
  3 window reported pre-override 7 trajectory with model_tokens_after_target >= window
  4 override takes effect       8 derive_memory_condition labels them exact / recurrent
                                9 one real retrieval trial in each condition

HARD GATE: at least one diagnostic trajectory must satisfy
    model_tokens_after_target >= effective_sliding_window
If not, the script stops before generating and does NOT interpret anything.
"""

from __future__ import annotations

import argparse
import json
import os
import sys
from pathlib import Path

ARM = "gated_deltanet"


def _bootstrap(repo: str | None) -> Path:
    root = Path(repo).expanduser().resolve() if repo else Path.cwd()
    if not (root / "config" / "experiment.yaml").is_file():
        raise SystemExit(f"--repo {root} is not the ahn-mdc checkout (no config/experiment.yaml)")
    os.chdir(root)  # config.project_root() resolves against cwd
    sys.path.insert(0, str(root / "src"))
    return root


def banner(n: int, title: str) -> None:
    print(f"\n{'=' * 78}\n[{n}] {title}\n{'=' * 78}")


# ---------------------------------------------------------------------------
# Non-GPU logic: trajectory straddling + the hard gate. Exercised by --self-test.
# ---------------------------------------------------------------------------

def build_straddling_trajectories(item, tokenizer, window: int, *, seed: int = 0):
    """One trajectory clearly inside the window, one clearly past it."""
    from ahnexp import dataset

    lo = dataset.build_trajectory(item, tokenizer, tokens_after_target=0, seed=seed)
    hi = dataset.build_trajectory(item, tokenizer, tokens_after_target=8 * window, seed=seed)
    return lo, hi


def classify(trajectories: list[dict], window: int):
    """Run the two rows through the real schema rule."""
    import pandas as pd

    from ahnexp import schema

    rows = [
        {
            "item_id": t["item_id"], "architecture": ARM, "seed": t["seed"],
            "fact_type": t["fact_type"], "sliding_window": window,
            "tokens_after_target": t["tokens_after_target"],
            "model_tokens_after_target": t["model_tokens_after_target"],
            "correct": 0,
        }
        for t in trajectories
    ]
    return schema.derive_memory_condition(pd.DataFrame(rows))


def assert_gate(trajectories: list[dict], window: int) -> None:
    ok = [t for t in trajectories if t["model_tokens_after_target"] >= window]
    print(
        f"\nHARD GATE  model_tokens_after_target >= effective_window ({window}):\n"
        + "\n".join(
            f"    {t['item_id']:>22}  ta={t['tokens_after_target']:>5}  "
            f"model_ta={t['model_tokens_after_target']:>5}  "
            f"{'>= window  PASS' if t['model_tokens_after_target'] >= window else '<  window'}"
            for t in trajectories
        )
    )
    if not ok:
        raise SystemExit(
            "\nGATE FAILED: no trajectory reaches the sliding window. Nothing was "
            "compressed, so there is no memory-degradation signal to measure. "
            "STOP — do not run or interpret Table 1."
        )
    print(f"    -> {len(ok)} trajectory(ies) cross the window. Gate passed.")


# ---------------------------------------------------------------------------
# self-test: prove the straddle + gate logic with a stub tokenizer, no model
# ---------------------------------------------------------------------------

class _StubTok:
    def __call__(self, text, **_):
        return {"input_ids": text.split()}

    def __len__(self):
        return 50_000


def self_test(root: Path) -> None:
    from ahnexp import dataset

    banner(0, "SELF-TEST (no GPU, no model) — trajectory straddle + hard gate")
    window = 256
    items = dataset.generate_items(n_items=5, seed=0, pool_size=600)
    item = items[0]
    lo, hi = build_straddling_trajectories(item, _StubTok(), window)
    for tag, t in (("below", lo), ("above", hi)):
        print(f"  {tag:<6} tokens_after_target={t['tokens_after_target']:>5}  "
              f"model_tokens_after_target={t['model_tokens_after_target']:>5}")
    table = classify([lo, hi], window)
    print("\n  derive_memory_condition:")
    print(table[["item_id", "tokens_after_target", "model_tokens_after_target", "memory_condition"]]
          .to_string(index=False))
    assert list(table["memory_condition"]) == ["exact_memory", "recurrent_memory"], table
    assert_gate([lo, hi], window)
    print("\nSELF-TEST PASSED — straddle construction and gate logic are sound.")


# ---------------------------------------------------------------------------
# full diagnostic (GPU)
# ---------------------------------------------------------------------------

def _find_layers(model):
    import torch.nn as nn

    inner = getattr(model, "model", model)
    layers = getattr(inner, "layers", None)
    if isinstance(layers, nn.ModuleList):
        return list(layers)
    for module in model.modules():
        if isinstance(module, nn.ModuleList) and len(module) > 1 and hasattr(module[0], "self_attn"):
            return list(module)
    raise RuntimeError("could not locate the decoder layer list")


def run_diagnostic(root: Path, ahn_repo: str | None) -> dict:
    report: dict = {"arm": ARM, "repo": str(root)}

    # --- 0. environment -----------------------------------------------------
    banner(0, "Environment")
    import torch
    import transformers

    cuda_ok = torch.cuda.is_available()
    print(f"  python              {sys.version.split()[0]}")
    print(f"  torch               {torch.__version__}  (cuda build {torch.version.cuda})")
    print(f"  torch.cuda          available={cuda_ok}"
          + (f"  device={torch.cuda.get_device_name(0)}" if cuda_ok else ""))
    print(f"  transformers        {transformers.__version__}")
    if not cuda_ok:
        raise SystemExit("No CUDA GPU. This diagnostic needs a real GPU checkpoint.")
    if not transformers.__version__.startswith("4.51"):
        raise SystemExit(f"transformers {transformers.__version__} != 4.51.x — re-run setup_kaggle.sh and RESTART.")
    for mod in ("fla", "flash_attn"):
        try:
            m = __import__(mod)
            print(f"  import {mod:12}     OK  ({getattr(m, '__version__', '?')})")
        except Exception as exc:  # noqa: BLE001
            print(f"  import {mod:12}     FAIL: {type(exc).__name__}: {exc}")
            if mod == "flash_attn":
                print("     NOTE: the AHN self-attention hardcodes FlashAttention-2; inference will fail without it.")
    report["env"] = {"torch": torch.__version__, "cuda": torch.version.cuda,
                     "transformers": transformers.__version__,
                     "gpu": torch.cuda.get_device_name(0)}

    from ahnexp import config, dataset, evaluate, models, schema

    # --- 1. repo + arm identity ------------------------------------------------
    banner(1, "Repo / arm / checkpoint identity")
    spec = models.arm(ARM)
    exp = config.experiment()
    forced_window = int(exp["models"]["sliding_window"]["force"])
    matched = exp["models"]["matched"]
    print(f"  project_root        {config.project_root()}")
    print(f"  config version      {exp['version']}")
    print(f"  arm                 {ARM}  ({spec.label})")
    print(f"  base_repo           {spec.base_repo}")
    print(f"  checkpoint          {spec.checkpoint}")
    print(f"  ahn_implementation  {spec.ahn_implementation}")
    print(f"  config force window  {forced_window}")
    report["arm_spec"] = {"base": spec.base_repo, "checkpoint": spec.checkpoint,
                          "ahn_implementation": spec.ahn_implementation, "force_window": forced_window}

    if ahn_repo:
        os.environ["AHN_REPO"] = str(Path(ahn_repo).expanduser().resolve())
    print(f"  AHN repo            {config.ahn_repo()}")

    # --- 2. merge (once) + read the checkpoint config BEFORE any override ------
    banner(2, "Merge weights + checkpoint config (pre-override)")
    merged = models.ensure_merged(ARM)
    ck = json.loads((merged / "config.json").read_text())
    pre = {k: ck.get(k) for k in (
        "model_type", "architectures", "_ahn_implementation", "_layer_implementation",
        "sliding_window", "use_sliding_window", "sliding_window_type", "ahn_position",
        "max_position_embeddings", "num_hidden_layers", "hidden_size", "transformers_version",
    )}
    print(f"  merged checkpoint   {merged}")
    for k, v in pre.items():
        print(f"    {k:24} {v}")
    report["checkpoint_config_pre_override"] = pre

    # --- 3-5. load the arm the way the experiment does; window before/after ---
    banner(3, "Load the arm (models.load) — window override")
    model, tok = models.load(ARM)          # prints "checkpoint reports sliding_window=... -> forcing ..."
    eff = models.effective_window(model)
    post = {
        "sliding_window": getattr(model.config, "sliding_window", None),
        "use_sliding_window": getattr(model.config, "use_sliding_window", None),
        "sliding_window_type": getattr(model.config, "sliding_window_type", None),
        "ahn_position": getattr(model.config, "ahn_position", None),
        "num_attn_sinks": getattr(model.config, "num_attn_sinks", "<unset->0>"),
        "dy_sliding_window": getattr(model.config, "dy_sliding_window", "<unset>"),
        "dy_num_attn_sinks": getattr(model.config, "dy_num_attn_sinks", "<unset>"),
        "_ahn_implementation": getattr(model.config, "_ahn_implementation", None),
    }
    print("  after models.load / _force_window (NOT overridden by the diagnostic):")
    for k, v in post.items():
        print(f"    {k:24} {v}")
    print(f"  model.training                      : {model.training}")
    print(f"  reported pre-override sliding_window : {pre['sliding_window']}")
    print(f"  effective_window(model)             : {eff}")
    print("  NOTE  sliding_window_type / ahn_position / dy_* are read ONLY inside")
    print("        `if self.training` in qwen2_ahn.py (pre_model_forward L444, mem_forward_train).")
    print("        At inference every window read is `config.sliding_window`; num_attn_sinks")
    print("        defaults to 0. So the checkpoint's 'random'/'random' is inert here. This")
    print("        diagnostic is OBSERVE-ONLY: it runs EXACTLY what models.load produces and")
    print("        does not touch these fields (the production normalisation is a separate,")
    print("        unapplied patch: patches/matched-inference-config.patch).")
    report["window"] = {
        "reported": pre["sliding_window"], "forced": forced_window, "effective": eff,
        "post": post, "model_training": bool(model.training),
        "matched_declares": {k: matched[k] for k in ("sliding_window_type", "ahn_position")},
    }
    assert eff == forced_window, f"override did not take: effective {eff} != forced {forced_window}"
    assert model.training is False, "model must be in eval mode for this diagnostic"

    # --- model identity ---
    banner("3b", "Model / tokenizer identity")
    print(f"  model class         {type(model).__module__}.{type(model).__name__}")
    print(f"  config class        {type(model.config).__module__}.{type(model.config).__name__}")
    print(f"  model_type          {model.config.model_type}")
    print(f"  num_hidden_layers   {model.config.num_hidden_layers}")
    print(f"  tokenizer class     {type(tok).__name__}  len={len(tok)}")
    print(f"  tokenizer fingerprint {models._tokenizer_fingerprint(tok)}")
    print(f"  chat_template       {'present' if getattr(tok, 'chat_template', None) else 'MISSING'}")
    print(f"  eos                 {tok.eos_token!r} ({tok.eos_token_id})")
    gcfg = getattr(model, "generation_config", None)
    print(f"  generation_config.use_cache  {getattr(gcfg, 'use_cache', None)}  "
          f"(AHN sizes in_ahn_seq_len from the KV cache — must be True)")
    report["model_identity"] = {
        "class": f"{type(model).__module__}.{type(model).__name__}",
        "config_class": f"{type(model.config).__module__}.{type(model.config).__name__}",
        "tokenizer": type(tok).__name__, "tokenizer_fingerprint": models._tokenizer_fingerprint(tok),
    }

    # --- 2 (evidence). AHN modules present & active -----------------------------
    banner(2, "AHN modules present / active")
    layers = _find_layers(model)
    mem_layers = [l for l in layers if type(l).__name__ == "Qwen2MemDecoderLayer"]
    l0 = layers[0]
    has_ahn = hasattr(l0, "ahn")
    fn_cls = type(l0.ahn.fn).__name__ if has_ahn and hasattr(l0.ahn, "fn") else None
    ahn_params = [(n, p.numel()) for n, p in model.named_parameters() if ".ahn." in n]
    ahn_numel = sum(n for _, n in ahn_params)
    is_ahn_class = type(model).__module__.startswith("ahn.")
    print(f"  model class from ahn package        {is_ahn_class}")
    print(f"  decoder layers                      {len(layers)}  "
          f"({len(mem_layers)} x Qwen2MemDecoderLayer)")
    print(f"  layer[0] has .ahn                   {has_ahn}  "
          f"({type(l0.ahn).__name__ if has_ahn else '-'} / fn={fn_cls})")
    print(f"  parameters matching '.ahn.'         {len(ahn_params)}  "
          f"({ahn_numel/1e6:.2f} M params; config says {spec.ahn_params/1e6:.1f} M)")
    print(f"  example ahn params                  {[n for n, _ in ahn_params[:3]]}")
    report["ahn_modules"] = {
        "model_is_ahn_class": is_ahn_class, "n_layers": len(layers),
        "n_mem_layers": len(mem_layers), "layer0_has_ahn": has_ahn,
        "ahn_fn_class": fn_cls, "n_ahn_params": len(ahn_params), "ahn_numel": ahn_numel,
    }
    assert is_ahn_class and mem_layers and has_ahn and ahn_params, "AHN modules NOT active — loaded as stock Qwen2"

    # --- 6/7. straddling trajectories ---------------------------------------
    banner(6, "Trajectories straddling the effective window")
    items = dataset.generate_items(n_items=5, seed=0, pool_size=600)
    item = items[0]  # numerical, gold "100000"
    lo, hi = build_straddling_trajectories(item, tok, eff)
    for tag, t in (("below (exact)", lo), ("above (recurrent)", hi)):
        print(f"  {tag:<20} tokens_after_target={t['tokens_after_target']:>5}  "
              f"model_tokens_after_target={t['model_tokens_after_target']:>5}  "
              f"context_tokens={t['context_tokens']:>5}")
    report["trajectories"] = {
        "gold": item.fact.answer, "fact_type": item.fact.fact_type,
        "lo": {k: lo[k] for k in ("tokens_after_target", "model_tokens_after_target", "context_tokens")},
        "hi": {k: hi[k] for k in ("tokens_after_target", "model_tokens_after_target", "context_tokens")},
    }

    # --- 8. derive_memory_condition ---------------------------------------------
    banner(8, "derive_memory_condition")
    table = classify([lo, hi], eff)
    print(table[["item_id", "tokens_after_target", "model_tokens_after_target", "memory_condition"]]
          .to_string(index=False))
    conds = list(table["memory_condition"])
    assert conds == ["exact_memory", "recurrent_memory"], conds
    report["memory_conditions"] = conds

    # --- HARD GATE --------------------------------------------------------------
    assert_gate([lo, hi], eff)

    # --- 9. one real trial per condition (2 generations) ----------------------
    # Runtime signal for "recurrent memory engaged", from the AHN source:
    #   mem_forward_inference() calls self.ahn.update_cache(...) on EVERY forward
    #   (gate values only) but calls self.ahn(...)  ->  BaseAHN.forward ->
    #   self.ahn.fn(...) (the recurrent kernel)  ONLY inside `if in_ahn_seq_len > 0`,
    #   where in_ahn_seq_len = kv_cache_size - config.sliding_window - num_attn_sinks.
    #   BaseAHN.forward also does `self.num_cached_tokens += o.shape[1]`, and a fresh
    #   generate() resets it (MemCache is None -> layer.ahn.reset_cache()).
    # So per trial:  layer0.ahn.num_cached_tokens == 0  in the exact condition,
    #                                              ~= (prompt_tokens - window)  in recurrent.
    # Primary signal = that counter. Confirmation = a forward hook on layer0.ahn.fn
    # (the kernel) recording the q_states length it is handed.
    banner(9, "One retrieval trial per condition")
    kernel = {"calls": 0, "positions": []}

    def _kernel_hook(_m, args, kwargs, _out):
        kernel["calls"] += 1
        q = kwargs.get("q_states")
        if q is None and len(args) > 2:
            q = args[2]
        try:
            kernel["positions"].append(int(q.shape[1]))
        except Exception:  # noqa: BLE001
            pass

    try:
        handle = l0.ahn.fn.register_forward_hook(_kernel_hook, with_kwargs=True)
    except TypeError:  # torch < 2.0 has no with_kwargs
        handle = l0.ahn.fn.register_forward_hook(lambda m, i, o: kernel.__setitem__("calls", kernel["calls"] + 1))

    trials = []
    try:
        for cond, tj in (("exact_memory", lo), ("recurrent_memory", hi)):
            kernel["calls"] = 0
            kernel["positions"] = []
            try:
                gen = evaluate.run_trial(model, tok, tj)
                sc = evaluate.score_row(gen["prediction"], gen["gold"], tj["fact_type"])
                n_cached = int(getattr(l0.ahn, "num_cached_tokens", -1))
                row = {
                    "condition": cond, "ok": True,
                    "gold": gen["gold"], "prediction": gen["prediction"],
                    "answer_canonical": sc["answer_canonical"],
                    "correct": sc["correct"], "malformed": sc["malformed"],
                    "abstained": sc["abstained"], "n_new_tokens": gen["n_new_tokens"],
                    "confidence": round(float(gen["confidence"]), 6),
                    "ahn_layer0_num_cached_tokens": n_cached,           # primary signal
                    "ahn_kernel_forward_calls": kernel["calls"],        # confirmation
                    "ahn_kernel_positions": kernel["positions"][:4],
                    "expected_recurrent_positions": max(tj["model_tokens_after_target"] - eff, 0),
                }
            except Exception as exc:  # noqa: BLE001
                row = {"condition": cond, "ok": False, "error": f"{type(exc).__name__}: {exc}"}
            trials.append(row)
            print(f"  --- {cond} ---")
            for k, v in row.items():
                print(f"    {k:26} {v!r}" if k == "prediction" else f"    {k:26} {v}")
    finally:
        handle.remove()
    report["trials"] = trials

    # --- verdict --------------------------------------------------------------
    banner(10, "Verdict")
    exact_row = next(t for t in trials if t["condition"] == "exact_memory")
    rec_row = next(t for t in trials if t["condition"] == "recurrent_memory")
    ahn_engaged = (
        rec_row.get("ok")
        and rec_row.get("ahn_layer0_num_cached_tokens", 0) > 0
        and rec_row.get("ahn_kernel_forward_calls", 0) > 0
    )
    ahn_idle_when_exact = (
        exact_row.get("ok")
        and exact_row.get("ahn_layer0_num_cached_tokens", 1) == 0
        and exact_row.get("ahn_kernel_forward_calls", 1) == 0
    )
    both_ran = exact_row["ok"] and rec_row["ok"]
    verdict = {
        "checkpoint_loads": True,
        "ahn_modules_active": bool(mem_layers and ahn_params),
        "window_reported_pre_override": pre["sliding_window"],
        "override_effective": eff == forced_window,
        "effective_window": eff,
        "exact_trajectory_below_window": lo["model_tokens_after_target"] < eff,
        "recurrent_trajectory_above_window": hi["model_tokens_after_target"] >= eff,
        "memory_condition_split_correct": conds == ["exact_memory", "recurrent_memory"],
        "both_trials_ran": both_ran,
        "ahn_recurrent_path_engaged_in_recurrent_trial": bool(ahn_engaged),
        "ahn_recurrent_path_idle_in_exact_trial": bool(ahn_idle_when_exact),
    }
    for k, v in verdict.items():
        print(f"  {k:44} {v}")
    report["verdict"] = verdict
    report["PASS"] = bool(
        both_ran and verdict["override_effective"] and verdict["ahn_modules_active"]
        and verdict["recurrent_trajectory_above_window"] and ahn_engaged
    )
    print(f"\n  DIAGNOSTIC {'PASSED' if report['PASS'] else 'INCONCLUSIVE — see rows above'}")
    return report


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--repo", default=os.environ.get("AHNEXP_ROOT"),
                    help="path to the ahn-mdc checkout (default: $AHNEXP_ROOT or cwd)")
    ap.add_argument("--ahn-repo", default=os.environ.get("AHN_REPO"),
                    help="path to the ByteDance-Seed/AHN checkout")
    ap.add_argument("--self-test", action="store_true", help="run the no-GPU logic check and exit")
    ap.add_argument("--out", default=None, help="where to write the JSON report")
    args = ap.parse_args()

    root = _bootstrap(args.repo)
    if args.self_test:
        self_test(root)
        return

    report = run_diagnostic(root, args.ahn_repo)
    out = Path(args.out) if args.out else root / "outputs" / "diag_ahn_window.json"
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(report, indent=2, default=str) + "\n")
    print(f"\nwrote {out}")
    raise SystemExit(0 if report.get("PASS") else 2)


if __name__ == "__main__":
    main()
