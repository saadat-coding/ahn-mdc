#!/usr/bin/env python3
"""Boundary mini-grid runner — Saadat's plumbing check before the full grid.

Runs `run_modes.mini` (config/experiment.yaml): 5 items (one per fact type) x
4 pressure levels [0, 128, 768, 2048] tokens_after_target x 1 seed x the
`gated_deltanet` arm = **20 trials**. Two levels land clearly exact, two clearly
recurrent.

    # after the window diagnostic passes, in the isolated 3.12 venv:
    python scripts/run_mini_grid.py --repo /content/ahn-mdc --ahn-repo /content/AHN

    # non-GPU flow check (no model):
    python scripts/run_mini_grid.py --self-test

It uses the SAME validated code path as the full grid (`evaluate.run_grid`,
`evaluate.score_row`, `schema.validate`, `report.gate_report`) and the SAME
analysis code (`h1_degradation`, `h3_calibration`). Nothing about window=256,
scoring, or H1/H2/H3 logic is touched. Output: `outputs/results_mini.parquet`
+ `outputs/mini_grid_summary.json`.

Hard acceptance (exit non-zero otherwise):
  * all 20 trials ran and scored, no unexpected exception
  * every item has BOTH an exact_memory and a recurrent_memory trial
  * gate `window_is_exceeded` == PASS
  * gate `matched_design`   == PASS
  * the `_mini` parquet re-loads and flows through H1 + H3 analysis code
Descriptive only (printed, never gated at n=20):
  * malformed rate (inspect the raw predictions listed below)
  * abstention rate / that abstained rows carry correct=0 + a confidence
  * exact-vs-recurrent accuracy difference
Expected non-blockers at this scale: `min_cell_size` FAIL, `threshold_locked`
BLOCKED, exact-memory-accuracy band noisy.
"""

from __future__ import annotations

import argparse
import json
import os
import sys
from pathlib import Path

ARM = "gated_deltanet"
MODE = "mini"


def _bootstrap(repo: str | None) -> Path:
    root = Path(repo).expanduser().resolve() if repo else Path.cwd()
    if not (root / "config" / "experiment.yaml").is_file():
        raise SystemExit(f"--repo {root} is not the ahn-mdc checkout (no config/experiment.yaml)")
    os.chdir(root)
    sys.path.insert(0, str(root / "src"))
    return root


def _ensure_mini_mode(root: Path) -> None:
    """Self-heal: add `pressure.mini_grid` and `run_modes.mini` to a checkout that
    predates them (idempotent, comment-preserving text inserts). No-op once present.
    """
    from ahnexp import config

    try:
        config.run_mode(MODE)
        return
    except (KeyError, Exception):  # noqa: BLE001
        pass

    path = root / "config" / "experiment.yaml"
    text = path.read_text()
    if "mini_grid:" not in text:
        anchor = "  pilot_grid: [0.0, 0.5, 1.0, 2.0]\n"
        assert anchor in text, "cannot locate pilot_grid line to insert mini_grid after"
        text = text.replace(anchor, anchor + "  mini_grid: [0.0, 0.5, 8.0]\n")
    if "\n  mini:\n" not in text:
        anchor = "run_modes:\n"
        assert anchor in text, "cannot locate run_modes: to insert mini mode"
        block = (
            "run_modes:\n"
            "  mini:\n"
            "    purpose: boundary / plumbing check before the full grid — never cited as a result\n"
            "    n_items: 5\n"
            "    seeds: [0]\n"
            "    grid: mini_grid\n"
            "    hardware: gpu\n"
            "    suffix: _mini\n"
        )
        text = text.replace(anchor, block)
    path.write_text(text)
    config.clear_caches()
    print(f"[mini] added run_modes.mini + pressure.mini_grid to {path}")


def banner(t: str) -> None:
    print(f"\n{'=' * 78}\n{t}\n{'=' * 78}")


# --------------------------------------------------------------------------------
# analysis-flow check (shared by the real run and --self-test)
# --------------------------------------------------------------------------------

def _analyse(df, report_out: Path) -> dict:
    import pandas as pd

    from ahnexp import config, h1_degradation, h3_calibration, metrics, report, schema

    df = schema.validate(df, needs=("core", "h1", "h3"))
    levels = sorted(df["tokens_after_target"].unique().tolist())
    per_item_conditions = (
        df.groupby("item_id")["memory_condition"].apply(lambda s: set(s)).to_dict()
    )
    both_conditions = {
        k: {"exact_memory", "recurrent_memory"}.issubset(v) for k, v in per_item_conditions.items()
    }

    gates = report.gate_report(df)
    g = gates.set_index("gate")["verdict"].to_dict()

    banner("gates")
    print(gates.to_string(index=False))

    banner("malformed / abstention (descriptive — inspect the raw predictions below)")
    for cond, sub in df.groupby("memory_condition"):
        print(f"  {cond:16}  n={len(sub):2d}  "
              f"malformed_rate={metrics.malformed_rate(sub):.1%}  "
              f"abstention_rate={metrics.abstention_rate(sub):.1%}  "
              f"accuracy={metrics.accuracy(sub):.1%}")
    ab = df[df.get("abstained", 0) == 1]
    print(f"  abstained rows: {len(ab)}  "
          f"(all correct==0: {bool((ab['correct'] == 0).all()) if len(ab) else 'n/a'}; "
          f"all have confidence: {bool(ab['confidence'].notna().all()) if len(ab) else 'n/a'})")

    banner("raw predictions (all 20 — manual malformed/abstention inspection)")
    cols = ["item_id", "fact_type", "tokens_after_target", "memory_condition",
            "gold", "prediction", "answer_canonical", "correct", "malformed",
            "abstained", "n_new_tokens", "confidence"]
    cols = [c for c in cols if c in df.columns]
    print(df.sort_values(["item_id", "tokens_after_target"])[cols].to_string(index=False))

    exact_acc = metrics.accuracy(df[df["memory_condition"] == "exact_memory"])
    rec_acc = metrics.accuracy(df[df["memory_condition"] == "recurrent_memory"])
    banner("exact vs recurrent accuracy (DESCRIPTIVE ONLY — not a gate at n=20)")
    print(f"  exact_memory   accuracy = {exact_acc:.1%}")
    print(f"  recurrent_memory accuracy = {rec_acc:.1%}")
    print(f"  difference (exact - recurrent) = {exact_acc - rec_acc:+.1%}")

    banner("does the _mini frame flow through H1 + H3 analysis code?")
    h1_ok = h3_ok = False
    h1_err = h3_err = None
    try:
        c1 = h1_degradation.curves(df, by="fact_type")
        _ = h1_degradation.summary(df)
        print(f"  h1_degradation.curves / summary: OK  ({len(c1)} curve rows)")
        h1_ok = True
    except Exception as e:  # noqa: BLE001
        h1_err = f"{type(e).__name__}: {e}"
        print(f"  h1_degradation: FAIL  {h1_err}")
    try:
        bp = h3_calibration.by_pressure(df)
        bc = h3_calibration.by_condition(df)
        print(f"  h3_calibration.by_pressure / by_condition: OK  "
              f"({len(bp)} pressure rows, {len(bc)} condition rows)")
        h3_ok = True
    except Exception as e:  # noqa: BLE001
        h3_err = f"{type(e).__name__}: {e}"
        print(f"  h3_calibration: FAIL  {h3_err}")

    summary = {
        "arm": ARM, "mode": MODE, "n_trials": int(len(df)),
        "levels": levels,
        "every_item_has_both_conditions": both_conditions,
        "gates": g,
        "malformed_rate_overall": float(metrics.malformed_rate(df)),
        "abstention_rate_overall": float(metrics.abstention_rate(df)),
        "accuracy_exact": float(exact_acc),
        "accuracy_recurrent": float(rec_acc),
        "h1_analysis_ok": h1_ok, "h1_error": h1_err,
        "h3_analysis_ok": h3_ok, "h3_error": h3_err,
    }
    report_out.parent.mkdir(parents=True, exist_ok=True)
    report_out.write_text(json.dumps(summary, indent=2, default=str) + "\n")

    hard_pass = bool(
        len(df) == 20
        and all(both_conditions.values())
        and g.get("window_is_exceeded") == "PASS"
        and g.get("matched_design") == "PASS"
        and h1_ok and h3_ok
    )
    banner("VERDICT")
    print(f"  20 trials                 : {len(df) == 20}")
    print(f"  both conditions per item  : {all(both_conditions.values())}")
    print(f"  window_is_exceeded PASS   : {g.get('window_is_exceeded') == 'PASS'}")
    print(f"  matched_design PASS       : {g.get('matched_design') == 'PASS'}")
    print(f"  H1 analysis flows         : {h1_ok}")
    print(f"  H3 analysis flows         : {h3_ok}")
    print(f"\n  MINI-GRID {'PASSED' if hard_pass else 'FAILED — see above'}")
    summary["PASS"] = hard_pass
    report_out.write_text(json.dumps(summary, indent=2, default=str) + "\n")
    return summary


# --------------------------------------------------------------------------------
# self-test: fabricate a mini-shaped frame, exercise the analysis flow, no model
# --------------------------------------------------------------------------------

def self_test(root: Path) -> None:
    import numpy as np
    import pandas as pd

    from ahnexp import schema

    banner("SELF-TEST (no GPU, no model) — analysis flow on a fabricated mini frame")
    rng = np.random.default_rng(0)
    types = ["numerical", "temporal", "entity-attribute", "multi-hop", "contradictory"]
    rows = []
    for it, ft in enumerate(types):
        for ta in (0, 128, 768, 2048):
            recurrent = ta >= 256
            correct = int(rng.random() < (0.3 if recurrent else 0.8))
            abst = int(recurrent and correct == 0 and rng.random() < 0.4)
            rows.append({
                "item_id": f"{ft}_{it:04d}", "architecture": ARM, "seed": 0,
                "fact_type": ft, "distractor_density": "low", "target_position": "early",
                "tokens_after_target": ta, "model_tokens_after_target": ta + 50,
                "sliding_window": 256, "context_tokens": 200 + ta,
                "correct": 0 if abst else correct, "abstained": abst, "malformed": 0,
                "answer_canonical": "" if abst else "x",
                "confidence": float(rng.uniform(0.2, 0.98)), "n_new_tokens": 3,
                "prediction": "I don't know" if abst else "x", "gold": "x",
                "scorer_version": "1.0",
            })
    import tempfile

    df = schema.derive_memory_condition(pd.DataFrame(rows))
    s = _analyse(df, Path(tempfile.gettempdir()) / "mini_grid_summary_selftest.json")
    assert s["n_trials"] == 20 and s["h1_analysis_ok"] and s["h3_analysis_ok"], s
    print("\nSELF-TEST PASSED — gate + H1/H3 flow + summary logic are sound.")


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--repo", default=os.environ.get("AHNEXP_ROOT"))
    ap.add_argument("--ahn-repo", default=os.environ.get("AHN_REPO"))
    ap.add_argument("--self-test", action="store_true")
    args = ap.parse_args()

    root = _bootstrap(args.repo)
    if args.self_test:
        self_test(root)
        return

    _ensure_mini_mode(root)
    ahn_repo = None
    if args.ahn_repo:
        ahn_repo = str(Path(args.ahn_repo).expanduser().resolve())
        os.environ["AHN_REPO"] = ahn_repo

    from ahnexp import config, dataset, evaluate

    banner(f"run_modes.{MODE}  (arm={ARM})")
    m = config.run_mode(MODE)
    window = int(config.experiment()["models"]["sliding_window"]["force"])
    print(f"  n_items={m['n_items']}  seeds={m['seeds']}  grid={m['grid']}")
    print(f"  pressure_levels = {evaluate.pressure_levels(window, MODE)}  (tokens_after_target)")

    items = dataset.generate_items(n_items=m["n_items"], seed=m["seeds"][0])
    df = evaluate.run_grid(items, None, ahn_repo=ahn_repo, mode=MODE, arms=[ARM])

    raw = config.output_path("raw", MODE)
    df.to_parquet(raw, index=False)
    print(f"\nwrote {raw}  ({len(df)} trials)")

    # re-load from disk to prove the parquet round-trips into analysis code
    import pandas as pd

    from ahnexp import schema
    df2 = schema.derive_memory_condition(pd.read_parquet(raw))
    summary = _analyse(df2, root / "outputs" / "mini_grid_summary.json")
    raise SystemExit(0 if summary.get("PASS") else 2)


if __name__ == "__main__":
    main()
