#!/usr/bin/env python3
"""Pilot Pass 2 — no-model calibration + grid dry run (Task F step 5).

Builds every Pilot Pass 2 item x model-tat target with the REAL Qwen2.5 tokenizer
(no model, no GPU) and:

  1. calibrates a per-fact-type `requested_tokens_after_target` for each intended
     `model_tokens_after_target` target  ->  config/pilot_pass2_calibration.json
  2. verifies intended vs realised model-tat, reports per-type mean/max error and
     whether every band is adequately hit, and checks trajectory nesting
  3. exits non-zero if a transition-band (200-300) target's median realised
     model-tat is off by more than pilot_pass2.calibration_tolerance_transition

    python scripts/pilot_pass2_dryrun.py --repo .            # calibrate + verify
    python scripts/pilot_pass2_dryrun.py --verify-only       # re-check an existing calibration

Run this BEFORE any GPU generation. If it fails, fix calibration first.
"""

from __future__ import annotations

import argparse
import json
import os
import sys
from pathlib import Path


def _bootstrap(repo: str | None) -> Path:
    root = Path(repo).expanduser().resolve() if repo else Path.cwd()
    if not (root / "config" / "experiment.yaml").is_file():
        raise SystemExit(f"--repo {root} is not the ahn-mdc checkout")
    os.chdir(root)
    sys.path.insert(0, str(root / "src"))
    return root


def _tokenizer():
    try:
        from transformers import AutoTokenizer
    except Exception as exc:  # noqa: BLE001
        raise SystemExit(f"transformers not importable: {exc}")
    from ahnexp import config

    base = config.experiment()["models"]["base"]
    try:
        return AutoTokenizer.from_pretrained(base)
    except Exception as exc:  # noqa: BLE001
        raise SystemExit(
            f"Could not load the {base} tokenizer ({exc}). Run this cell in Colab "
            "where the tokenizer is cached, before GPU generation."
        )


def banner(t: str) -> None:
    print(f"\n{'=' * 78}\n{t}\n{'=' * 78}")


def _median_model_tat(items, tok, requested: int, seed: int, cache: dict) -> float:
    key = (id(items), requested)
    if key in cache:
        return cache[key]
    from ahnexp import dataset

    vals = [
        dataset.build_trajectory(it, tok, tokens_after_target=requested, seed=seed)[
            "model_tokens_after_target"
        ]
        for it in items
    ]
    import statistics

    med = float(statistics.median(vals))
    cache[key] = med
    return med


def calibrate(items_by_type, tok, targets, seed: int) -> dict:
    from ahnexp import config

    per_type = {}
    for ft, items in items_by_type.items():
        cache: dict = {}
        overhead = _median_model_tat(items, tok, 0, seed, cache)
        # coarse sweep to bracket, then local refine per target
        coarse = {r: _median_model_tat(items, tok, r, seed, cache)
                  for r in range(0, 1160, 24)}
        req_by_target, realised, errors = {}, {}, {}
        for target in targets:
            # bracket from the coarse sweep
            near = min(coarse, key=lambda r: abs(coarse[r] - target))
            best_r, best_err = near, abs(coarse[near] - target)
            for r in range(max(0, near - 36), near + 37, 3):
                m = _median_model_tat(items, tok, r, seed, cache)
                if abs(m - target) < best_err:
                    best_r, best_err = r, abs(m - target)
            m = _median_model_tat(items, tok, best_r, seed, cache)
            req_by_target[str(target)] = int(best_r)
            realised[str(target)] = round(m, 1)
            errors[str(target)] = round(m - target, 1)
        per_type[ft] = {
            "overhead_tokens": round(overhead, 1),
            "requested_by_target": req_by_target,
            "realised_model_tat_by_target": realised,
            "error_by_target": errors,
        }
    return {
        "generated": "pilot_pass2_dryrun.py",
        "tokenizer": config.experiment()["models"]["base"],
        "seed": seed,
        "n_items_per_type": len(next(iter(items_by_type.values()))),
        "target_model_tat_grid": list(targets),
        "per_type": per_type,
    }


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--repo", default=os.environ.get("AHNEXP_ROOT"))
    ap.add_argument("--verify-only", action="store_true")
    args = ap.parse_args()

    root = _bootstrap(args.repo)
    from ahnexp import config, dataset, pilot_pass2

    p2 = config.pilot_pass2()
    mode = config.run_mode("pilot_pass2")
    targets = list(p2["target_model_tat"])
    seed = int(mode["seeds"][0])
    n_items = int(mode["n_items"])

    banner(f"Pilot Pass 2 dry run — {n_items} items x {len(targets)} model-tat targets (no model)")
    tok = _tokenizer()
    items = dataset.generate_items(n_items=n_items, seed=seed)
    by_type: dict[str, list] = {}
    for it in items:
        by_type.setdefault(it.fact.fact_type, []).append(it)
    print(f"  fact types: {[f'{k}:{len(v)}' for k, v in by_type.items()]}")

    calib_path = root / p2["calibration_file"]
    if args.verify_only:
        calibration = json.loads(calib_path.read_text())
        print(f"  loaded existing calibration {calib_path}")
    else:
        banner("calibrating requested_tokens_after_target per fact type")
        calibration = calibrate(by_type, tok, targets, seed)
        calib_path.write_text(json.dumps(calibration, indent=2) + "\n")
        print(f"  wrote {calib_path}")
        for ft, entry in calibration["per_type"].items():
            print(f"    {ft:16} overhead={entry['overhead_tokens']:6.1f}  "
                  f"errors={list(entry['error_by_target'].values())}")

    banner("verifying intended vs realised model_tokens_after_target")
    plan = pilot_pass2.build_pressure_plan(calibration)
    verify = pilot_pass2.verify_grid(items, tok, plan, seed=seed)
    rep = pilot_pass2.calibration_report(verify, p2["bands"])

    print(rep.to_string(index=False))
    print("\nper fact type — abs error across items:")
    g = verify.groupby("fact_type")["error"].agg(mean_abs=lambda s: s.abs().mean(),
                                                 max_abs=lambda s: s.abs().max())
    print(g.round(1).to_string())

    print("\nper band — median |error| over (fact_type x target):")
    print(rep.assign(abs_err=rep["median_error"].abs())
          .groupby("band")["abs_err"].agg(["mean", "max"]).round(1).to_string())

    nesting_bad = verify.loc[~verify["nested_ok"], "item_id"].unique().tolist()
    off = rep.loc[~rep["within_tolerance"]]
    transition_off = off[off["band"] == "transition"]

    summary = {
        "n_items": n_items, "targets": targets, "seed": seed,
        "per_type_mean_abs_error": {k: round(float(v["mean_abs"]), 2) for k, v in g.iterrows()},
        "per_type_max_abs_error": {k: int(v["max_abs"]) for k, v in g.iterrows()},
        "targets_out_of_tolerance": off[["fact_type", "intended_model_tat", "median_error", "tolerance"]]
        .to_dict("records"),
        "transition_band_ok": bool(transition_off.empty),
        "trajectory_nesting_ok": not nesting_bad,
        "non_nested_items": nesting_bad,
        "bands_covered": {b: sorted(rep.loc[rep["band"] == b, "intended_model_tat"].unique().tolist())
                          for b in p2["bands"]},
    }
    out = root / config.experiment()["outputs"]["pass2_dryrun"]
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(summary, indent=2, default=str) + "\n")

    banner("VERDICT")
    print(f"  trajectory nesting ok      : {not nesting_bad}")
    print(f"  transition band in tol (<= {p2['calibration_tolerance_transition']}) : {transition_off.empty}")
    print(f"  all targets in tol         : {off.empty}")
    print(f"  wrote {out}")

    ok = transition_off.empty and not nesting_bad
    if not ok:
        print("\n  DRY RUN FAILED — improve calibration before GPU generation.")
        if not transition_off.empty:
            print(transition_off.to_string(index=False))
        raise SystemExit(1)
    print("\n  DRY RUN PASSED — calibration is good enough to generate.")


if __name__ == "__main__":
    main()
