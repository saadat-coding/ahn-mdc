#!/usr/bin/env python3
"""Final experiment — no-model calibration + grid dry run + frozen-design manifest.

Builds every final-run item x model-tat target with the REAL Qwen2.5 tokenizer
(no model, no GPU) and:

  1. calibrates a per-fact-type `requested_tokens_after_target` for each of the 12
     intended `model_tokens_after_target` targets  ->  config/final_calibration.json
     (search on `final.calibration_items_per_type` items; realised model-tat then
      verified on ALL 240 items)
  2. verifies intended vs realised model-tat, per-type mean/max error, band
     coverage, trajectory nesting
  3. exits non-zero if any transition-region target's median realised model-tat is
     off by more than final.calibration_tolerance_transition, or nesting is broken
  4. --manifest also (re)writes config/final_design_manifest.json (git commit,
     grid, seeds, arms, W, prompt hash, calibration hash, construct mapping, ...)

    python scripts/full_run_dryrun.py --repo .              # calibrate + verify
    python scripts/full_run_dryrun.py --verify-only         # re-check existing calibration
    python scripts/full_run_dryrun.py --manifest            # calibrate + verify + write manifest

Run this BEFORE any GPU generation.
"""

from __future__ import annotations

import argparse
import json
import os
import subprocess
import sys
from datetime import datetime, timezone
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
            f"Could not load the {base} tokenizer ({exc}). Run this where the "
            "tokenizer is cached (Colab), before GPU generation."
        )


def banner(t: str) -> None:
    print(f"\n{'=' * 78}\n{t}\n{'=' * 78}")


def _git_commit(root: Path) -> str:
    try:
        return subprocess.check_output(["git", "-C", str(root), "rev-parse", "HEAD"],
                                       text=True).strip()
    except Exception:  # noqa: BLE001
        return "unknown"


def _write_manifest(root: Path, calibration_ok: bool) -> Path:
    from ahnexp import config, evaluate

    fcfg = config.final()
    facts = config.facts()
    manifest = {
        "generated_by": "scripts/full_run_dryrun.py --manifest",
        "generated_on": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "git_commit_at_generation": _git_commit(root),
        "note": "The authoritative frozen commit is the freeze commit that adds/updates "
                "this file; git_commit_at_generation is the pre-write baseline.",
        "analysis_version": fcfg["analysis_version"],
        "scorer_version": evaluate.SCORER_VERSION,
        "window_W": int(fcfg["window_reference"]),
        "n_items": int(fcfg["n_items"]),
        "items_per_fact_type": int(fcfg["n_items"]) // len(facts["types"]),
        "seeds": list(fcfg["seeds"]),
        "arms": list(fcfg["arms"]),
        "target_model_tat_grid": list(fcfg["target_model_tat"]),
        "bands": {k: list(v) for k, v in fcfg["bands"].items()},
        "transition_interval": list(fcfg["transition_interval"]),
        "h1_transition_targets": list(fcfg["h1_transition_targets"]),
        "control_anchors": list(fcfg["control_anchors"]),
        "recurrent_from": int(fcfg["recurrent_from"]),
        "h3_signal_margin": int(fcfg["h3_signal_margin"]),
        "prompt_sha256": config.prompt_hash(),
        "calibration_sha256": config.file_sha256(fcfg["calibration_file"]),
        "calibration_within_tolerance": bool(calibration_ok),
        "fact_type_construct": {k: v.get("construct", k) for k, v in facts["types"].items()},
        "expected_generations": len(fcfg["arms"]) * int(fcfg["n_items"])
        * len(fcfg["target_model_tat"]) * len(fcfg["seeds"]),
    }
    path = root / fcfg["manifest_file"]
    path.write_text(json.dumps(manifest, indent=2) + "\n")
    return path


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--repo", default=os.environ.get("AHNEXP_ROOT"))
    ap.add_argument("--verify-only", action="store_true")
    ap.add_argument("--manifest", action="store_true")
    args = ap.parse_args()

    root = _bootstrap(args.repo)
    import importlib.util

    from ahnexp import config, dataset, pilot_pass2

    _spec = importlib.util.spec_from_file_location(
        "_p2_dryrun", root / "scripts" / "pilot_pass2_dryrun.py")
    _p2 = importlib.util.module_from_spec(_spec)
    _spec.loader.exec_module(_p2)
    calibrate = _p2.calibrate  # reuse the coarse+refine calibration sweep

    fcfg = config.final()
    targets = list(fcfg["target_model_tat"])
    seed = int(fcfg["seeds"][0])
    n_items = int(fcfg["n_items"])
    search_n = int(fcfg["calibration_items_per_type"])

    banner(f"Final dry run — {n_items} items x {len(targets)} model-tat targets (no model)")
    tok = _tokenizer()
    items = dataset.generate_items(n_items=n_items, seed=seed)
    by_type: dict[str, list] = {}
    for it in items:
        by_type.setdefault(it.fact.fact_type, []).append(it)
    print(f"  fact types: {[f'{k}:{len(v)}' for k, v in by_type.items()]}")
    search_by_type = {k: v[:search_n] for k, v in by_type.items()}

    calib_path = root / fcfg["calibration_file"]
    if args.verify_only:
        calibration = json.loads(calib_path.read_text())
        print(f"  loaded existing calibration {calib_path}")
    else:
        banner(f"calibrating requested_tokens_after_target per fact type ({search_n} items/type)")
        calibration = calibrate(search_by_type, tok, targets, seed)
        calibration["generated"] = "full_run_dryrun.py"
        calibration["n_items_verified"] = n_items
        calib_path.write_text(json.dumps(calibration, indent=2) + "\n")
        print(f"  wrote {calib_path}")
        for ft, entry in calibration["per_type"].items():
            print(f"    {ft:16} overhead={entry['overhead_tokens']:6.1f}  "
                  f"errors={list(entry['error_by_target'].values())}")

    banner("verifying intended vs realised model_tokens_after_target (all items)")
    plan = pilot_pass2.build_pressure_plan(calibration)
    verify = pilot_pass2.verify_grid(items, tok, plan, seed=seed)
    tol = {"calibration_tolerance_transition": fcfg["calibration_tolerance_transition"],
           "calibration_tolerance_other": fcfg["calibration_tolerance_other"]}
    rep = pilot_pass2.calibration_report(verify, fcfg["bands"], tolerances=tol)
    print(rep.to_string(index=False))

    g = verify.groupby("fact_type")["error"].agg(mean_abs=lambda s: s.abs().mean(),
                                                 max_abs=lambda s: s.abs().max())
    print("\nper fact type — abs error across items:")
    print(g.round(1).to_string())

    nesting_bad = verify.loc[~verify["nested_ok"], "item_id"].unique().tolist()
    off = rep.loc[~rep["within_tolerance"]]
    transition = set(fcfg["bands"]["transition"])
    transition_off = off[off["intended_model_tat"].isin(transition)]

    summary = {
        "n_items": n_items, "search_items_per_type": search_n, "targets": targets, "seed": seed,
        "per_type_mean_abs_error": {k: round(float(v["mean_abs"]), 2) for k, v in g.iterrows()},
        "per_type_max_abs_error": {k: int(v["max_abs"]) for k, v in g.iterrows()},
        "targets_out_of_tolerance": off[["fact_type", "intended_model_tat", "median_error", "tolerance"]]
        .to_dict("records"),
        "transition_region_ok": bool(transition_off.empty),
        "all_targets_ok": bool(off.empty),
        "trajectory_nesting_ok": not nesting_bad,
        "non_nested_items": nesting_bad,
    }
    out = root / config.experiment()["outputs"]["final_dryrun"]
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(summary, indent=2, default=str) + "\n")

    ok = transition_off.empty and not nesting_bad

    if args.manifest:
        banner("frozen-design manifest")
        config.clear_caches()
        mpath = _write_manifest(root, calibration_ok=bool(off.empty))
        print(f"  wrote {mpath}")

    banner("VERDICT")
    print(f"  trajectory nesting ok       : {not nesting_bad}")
    print(f"  transition region in tol(<= {fcfg['calibration_tolerance_transition']}): {transition_off.empty}")
    print(f"  all targets in tol          : {off.empty}")
    print(f"  wrote {out}")
    if not ok:
        print("\n  DRY RUN FAILED — improve calibration before GPU generation.")
        if not transition_off.empty:
            print(transition_off.to_string(index=False))
        raise SystemExit(1)
    print("\n  DRY RUN PASSED — calibration is good enough to generate.")


if __name__ == "__main__":
    main()
