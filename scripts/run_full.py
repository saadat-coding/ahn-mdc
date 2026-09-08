#!/usr/bin/env python3
"""Final inferential experiment runner (protocol/final_experiment_design.md).

FROZEN 2026-09-05. 4 arms x 240 items x 12 model-tat targets x 8 seeds = 92,160
generations. Same code path as every earlier run (`evaluate.run_grid`,
`evaluate.score_row`, `schema.validate`) with a per-fact-type `pressure_plan` from
config/final_calibration.json.

    # no GPU — fabricated frame through the gate + frozen analysis code:
    python scripts/run_full.py --self-test

    # re-check calibration + manifest only (no model):
    python scripts/run_full.py --preflight

    # real run in the isolated venv (Colab L4 / A40), staged one or more arms:
    python scripts/run_full.py --repo /content/ahn-mdc --ahn-repo /content/AHN --arms transformer
    python scripts/run_full.py --arms mamba2 deltanet gated_deltanet

Held fixed: benchmark items, production _PROMPT, scorer version, repaired temporal
generator, W = 256, max_new_tokens = 12. Hard plumbing gates
(`ahnexp.full_run.plumbing_gates`) exit non-zero on FAIL when all arms are present.
"""

from __future__ import annotations

import argparse
import json
import os
import sys
from pathlib import Path

MODE = "full"


def _bootstrap(repo: str | None) -> Path:
    root = Path(repo).expanduser().resolve() if repo else Path.cwd()
    if not (root / "config" / "experiment.yaml").is_file():
        raise SystemExit(f"--repo {root} is not the ahn-mdc checkout")
    os.chdir(root)
    sys.path.insert(0, str(root / "src"))
    return root


def banner(t: str) -> None:
    print(f"\n{'=' * 78}\n{t}\n{'=' * 78}")


def _check_manifest(root: Path) -> None:
    from ahnexp import config

    try:
        m = config.final_manifest()
    except FileNotFoundError as exc:
        raise SystemExit(f"{exc}\nRun scripts/full_run_dryrun.py --manifest first.")
    fcfg = config.final()
    problems = []
    if m["prompt_sha256"] != config.prompt_hash():
        problems.append("prompt hash drift — _PROMPT or an answer_hint changed since the freeze")
    if m["calibration_sha256"] != config.file_sha256(fcfg["calibration_file"]):
        problems.append("calibration hash drift — config/final_calibration.json changed since the manifest")
    if m["target_model_tat_grid"] != list(fcfg["target_model_tat"]):
        problems.append("grid drift")
    if m["seeds"] != list(fcfg["seeds"]):
        problems.append("seed drift")
    if problems:
        raise SystemExit("FROZEN-DESIGN MANIFEST MISMATCH:\n  - " + "\n  - ".join(problems))
    print(f"  manifest OK — analysis v{m['analysis_version']}, "
          f"{m['expected_generations']} generations, prompt {m['prompt_sha256'][:12]}")


def _preflight(root: Path, tok):
    from ahnexp import config, dataset, full_run, pilot_pass2

    fcfg = config.final()
    seed = int(fcfg["seeds"][0])
    items = dataset.generate_items(n_items=int(fcfg["n_items"]), seed=seed)
    calibration = config.load_final_calibration()
    plan = pilot_pass2.build_pressure_plan(calibration)
    verify = full_run.verify_grid(items, tok, plan, seed=seed)
    tol = {"calibration_tolerance_transition": fcfg["calibration_tolerance_transition"],
           "calibration_tolerance_other": fcfg["calibration_tolerance_other"]}
    rep = pilot_pass2.calibration_report(verify, fcfg["bands"], tolerances=tol)
    off = rep.loc[~rep["within_tolerance"]]
    nesting_bad = verify.loc[~verify["nested_ok"], "item_id"].unique().tolist()
    print(rep.to_string(index=False))
    transition = set(fcfg["bands"]["transition"])
    if not off[off["intended_model_tat"].isin(transition)].empty or nesting_bad:
        raise SystemExit(
            f"PRE-FLIGHT FAILED: {len(off)} (type,target) out of tolerance, "
            f"nesting broken for {nesting_bad}. Re-run scripts/full_run_dryrun.py."
        )
    print("\n  PRE-FLIGHT PASSED — grid calibration good; proceeding.")
    return items, plan, calibration, verify


def _analyse_and_gate(root, df, items, calibration, verify) -> bool:
    from ahnexp import config, full_run

    exp = config.experiment()["outputs"]
    banner("HARD plumbing gates")
    gates = full_run.plumbing_gates(df, items, calibration, verify)
    print(gates.to_string(index=False))
    failed = full_run.blocking(gates)

    banner("scientific warnings (results, never block)")
    warns = full_run.scientific_warnings(df)
    print(warns.to_string(index=False) if len(warns) else "  (none)")

    banner("frozen analysis outputs")
    out = {
        "summary": root / exp["final_summary"],
        "h1": root / exp["final_h1"],
        "h2": root / exp["final_h2"],
        "h3": root / exp["final_h3"],
        "control": root / exp["final_control"],
    }
    res = full_run.analyse(df, items=items, out=out)
    for _, v in out.items():
        print(f"  wrote {v}*")
    print("\nsummary:")
    print(json.dumps(res["summary"], indent=2, default=str))

    passed = failed.empty
    banner("VERDICT")
    print(f"  hard plumbing gates: {'ALL PASS' if passed else 'FAIL'}")
    if not passed:
        print(failed.to_string(index=False))
    return passed


def self_test(root: Path) -> None:
    import numpy as np
    import pandas as pd

    from ahnexp import config, dataset, full_run, schema

    banner("SELF-TEST (no model) — final gate + frozen analysis on a fabricated frame")
    fcfg = config.final()
    seed0 = int(fcfg["seeds"][0])
    n_items = 40  # one small balanced slice per fact type is enough for the flow
    items = dataset.generate_items(n_items=n_items, seed=seed0)
    calibration = config.load_final_calibration()
    seeds = list(fcfg["seeds"])[:3]

    rng = np.random.default_rng(0)
    rows = []
    for arm in fcfg["arms"]:
        decay = {"gated_deltanet": 0.9, "mamba2": 1.0, "deltanet": 1.1, "transformer": 1.0}[arm]
        for it in items:
            per_type = calibration["per_type"][it.fact.fact_type]["requested_by_target"]
            for target in fcfg["target_model_tat"]:
                req = int(per_type[str(target)])
                for seed in seeds:
                    mtat = int(target + rng.integers(-6, 7))
                    p = 1.0 if mtat < 205 else max(0.0, 1.0 - decay * (mtat - 205) / 80)
                    answered = rng.random() > (0.1 if mtat < 235 else 0.75)
                    correct = int(answered and rng.random() < p)
                    rows.append({
                        "item_id": it.item_id, "architecture": arm, "seed": seed,
                        "fact_type": it.fact.fact_type, "distractor_density": it.distractor_density,
                        "target_position": "early",
                        "tokens_after_target": req + 4, "requested_tokens_after_target": req,
                        "model_tokens_after_target": mtat,
                        "intended_model_tokens_after_target": int(target),
                        "target_fact_tokens": 12, "context_tokens": 220 + mtat,
                        "sliding_window": 256, "n_new_tokens": 3,
                        "correct": correct, "abstained": int(not answered), "malformed": 0,
                        "answer_canonical": "x" if answered else "",
                        "confidence": float(rng.uniform(0.3, 0.95)),
                        "prediction": "x" if answered else "I don't know", "gold": "x",
                        "scorer_version": "1.0",
                    })
    df = schema.derive_boundary_conditions(
        schema.derive_memory_condition(pd.DataFrame(rows)), strict=True)

    # small n_resamples for speed; the flow is what is under test
    res = full_run.analyse(df, items=items, n_resamples=200)
    assert set(res["tables"]) >= {"h1_a_transition", "h1_contrasts", "h2_width",
                                  "h3_behavioral_per_arm", "control_validity"}
    assert "T" not in res["summary"] and res["summary"]["no_published_T"] is True
    gates = full_run.plumbing_gates(df, items, calibration, verify=None)
    # trial_count / grid_realised will not match a 40-item 3-seed fake frame; assert
    # the gate machinery runs and the non-count gates behave.
    assert "schema_valid" in set(gates["gate"])
    assert gates.loc[gates["gate"] == "schema_valid", "verdict"].iloc[0] == "PASS"
    print(gates.to_string(index=False))
    print("\nSELF-TEST PASSED — final gates + frozen H1/H2/H3 analysis flow are sound.")


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--repo", default=os.environ.get("AHNEXP_ROOT"))
    ap.add_argument("--ahn-repo", default=os.environ.get("AHN_REPO"))
    ap.add_argument("--arms", nargs="+", default=None, help="subset of arms (staged run)")
    ap.add_argument("--self-test", action="store_true")
    ap.add_argument("--preflight", action="store_true")
    args = ap.parse_args()

    root = _bootstrap(args.repo)
    from ahnexp import config, dataset, evaluate, full_run

    if args.self_test:
        self_test(root)
        return

    banner("frozen-design manifest check")
    _check_manifest(root)

    from transformers import AutoTokenizer
    tok = AutoTokenizer.from_pretrained(config.experiment()["models"]["base"])
    items, plan, calibration, verify = _preflight(root, tok)
    if args.preflight:
        return

    fcfg = config.final()
    arms = args.arms or list(fcfg["arms"])
    ahn_repo = str(Path(args.ahn_repo).expanduser().resolve()) if args.ahn_repo else None
    if ahn_repo:
        os.environ["AHN_REPO"] = ahn_repo

    import pandas as pd

    raw = root / config.experiment()["outputs"]["final_raw"]
    dataset.save_items(items, root / config.experiment()["outputs"]["final_items"],
                       seed=int(fcfg["seeds"][0]))

    # --- resume: inspect the existing artifact, skip cells already persisted -----
    if raw.exists():
        existing = pd.read_parquet(raw)
        full_run.assert_compatible_with_frozen_design(existing)
        done = full_run.completed_cells(raw)
    else:
        existing, done = pd.DataFrame(), set()
    skip = {c for c in done if c[0] in set(arms)}
    per_arm_cells = 240 * 12 * 8
    banner(f"Final run — arms={arms}  (resumable, one seed / {240 * 12} cells per checkpoint)")
    for arm in arms:
        have = sum(1 for c in skip if c[0] == arm)
        print(f"  {arm}: {have} / {per_arm_cells} cells already persisted "
              f"-> {per_arm_cells - have} to generate")
    other = sorted({c[0] for c in done} - set(arms))
    if other:
        print(f"  preserved (not regenerated): {other}")

    def _checkpoint(architecture, seed, chunk_frame):
        full_run.checkpoint_merge(chunk_frame, raw, architecture=architecture, seed=seed)

    df_new = evaluate.run_grid(items, None, ahn_repo=ahn_repo, mode=MODE, arms=arms,
                               pressure_plan=plan, skip_cells=skip, on_chunk=_checkpoint)
    # checkpoints already persisted every chunk; if nothing was pending, still
    # re-emit the artifact status so a no-op restart is legible.
    if raw.exists() and not len(df_new):
        full_run.checkpoint_merge(None, raw, architecture=arms[0] if len(arms) == 1 else None)
    merged = pd.read_parquet(raw)
    print(f"\nartifact: {raw}  ({len(merged)} / {full_run.expected_trials()} rows)")

    # --- gates + frozen analysis wait until all four arms are complete ----------
    prog = full_run.design_progress(merged)
    if not prog["complete"]:
        banner("staged run — analysis deferred")
        for arm, n in prog["per_arm_cells"].items():
            print(f"  {arm}: {n} / {prog['per_arm_target']} cells"
                  f"  (complete seeds {prog['seeds_complete'][arm]})")
        print("\n  H1/H2/H3 gates + analysis run only when all four complete "
              "architectures are present.")
        return

    banner("all four architectures complete — running gates + frozen analysis")
    passed = _analyse_and_gate(root, merged, items, calibration, verify)
    if not passed:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
