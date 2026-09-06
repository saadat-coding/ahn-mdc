#!/usr/bin/env python3
"""Pilot Pass 2 runner — four-arm plumbing + localization (protocol/pilot_pass2.md).

40 items (8 per fact type) x 11 model-tat targets x 1 seed x 4 arms = 1,760 trials.
Not inferential evidence. Uses the SAME code path as the full run
(`evaluate.run_grid`, `evaluate.score_row`, `schema.validate`) with a per-fact-type
`pressure_plan` from config/pilot_pass2_calibration.json.

    # no GPU — fabricated frame through the gate + analysis code:
    python scripts/run_pilot_pass2.py --self-test

    # re-check calibration only (no model):
    python scripts/run_pilot_pass2.py --preflight

    # real run in the isolated venv (Colab L4):
    python scripts/run_pilot_pass2.py --repo /content/ahn-mdc --ahn-repo /content/AHN
    # staged (one or more arms at a time):
    python scripts/run_pilot_pass2.py --arms transformer gated_deltanet ...

Held fixed: max_new_tokens=12, scorer version, repaired temporal generator,
production _PROMPT, target/distractor construction. Hard plumbing gates
(`ahnexp.pilot_pass2.plumbing_gates`) exit non-zero on FAIL; scientific findings
are printed as warnings and never block.
"""

from __future__ import annotations

import argparse
import json
import os
import sys
from pathlib import Path

MODE = "pilot_pass2"


def _bootstrap(repo: str | None) -> Path:
    root = Path(repo).expanduser().resolve() if repo else Path.cwd()
    if not (root / "config" / "experiment.yaml").is_file():
        raise SystemExit(f"--repo {root} is not the ahn-mdc checkout")
    os.chdir(root)
    sys.path.insert(0, str(root / "src"))
    return root


def banner(t: str) -> None:
    print(f"\n{'=' * 78}\n{t}\n{'=' * 78}")


def _preflight(root: Path, tok):
    """No-model calibration re-check. Aborts before GPU if the grid is miscalibrated.

    Returns `(items, pressure_plan, calibration, verify_frame)` for the run.
    """
    from ahnexp import config, dataset, pilot_pass2

    p2 = config.pilot_pass2()
    seed = int(config.run_mode(MODE)["seeds"][0])
    items = dataset.generate_items(n_items=int(config.run_mode(MODE)["n_items"]), seed=seed)
    calibration = config.load_pass2_calibration()
    plan = pilot_pass2.build_pressure_plan(calibration)
    verify = pilot_pass2.verify_grid(items, tok, plan, seed=seed)
    rep = pilot_pass2.calibration_report(verify, p2["bands"])
    off = rep.loc[~rep["within_tolerance"]]
    nesting_bad = verify.loc[~verify["nested_ok"], "item_id"].unique().tolist()
    print(rep.to_string(index=False))
    if not off.empty or nesting_bad:
        raise SystemExit(
            f"PRE-FLIGHT FAILED: {len(off)} (type,target) out of tolerance, "
            f"nesting broken for {nesting_bad}. Re-run scripts/pilot_pass2_dryrun.py."
        )
    print("\n  PRE-FLIGHT PASSED — grid calibration good; proceeding to generation.")
    return items, plan, calibration, verify


def _analyse_and_gate(root, df, items, calibration, verify) -> bool:
    from ahnexp import config, pilot_pass2

    exp = config.experiment()["outputs"]

    banner("HARD plumbing gates")
    gates = pilot_pass2.plumbing_gates(df, items, calibration, verify)
    print(gates.to_string(index=False))
    failed = pilot_pass2.blocking(gates)

    banner("scientific warnings (NOT plumbing errors — results, never block)")
    warns = pilot_pass2.scientific_warnings(df)
    print(warns.to_string(index=False) if len(warns) else "  (none)")

    banner("analysis outputs")
    out = {
        "summary": root / exp["pass2_summary"],
        "h1": root / exp["pass2_h1"],
        "h2": root / exp["pass2_h2"],
        "h3": root / exp["pass2_h3"],
        "knees": root / exp["pass2_knees"],
    }
    res = pilot_pass2.analyse(df, out=out, items=items)
    for k, v in out.items():
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

    from ahnexp import config, dataset, schema

    banner("SELF-TEST (no model) — pass2 gate + analysis flow on a fabricated frame")
    p2 = config.pilot_pass2()
    mode = config.run_mode(MODE)
    seed = int(mode["seeds"][0])
    items = dataset.generate_items(n_items=int(mode["n_items"]), seed=seed)
    calibration = config.load_pass2_calibration()

    rng = np.random.default_rng(0)
    rows = []
    for arm in p2["arms"]:
        for it in items:
            ov = calibration["per_type"][it.fact.fact_type]["overhead_tokens"]
            for target in p2["target_model_tat"]:
                req = int(calibration["per_type"][it.fact.fact_type]["requested_by_target"][str(target)])
                mtat = int(target + rng.integers(-8, 9))
                # plausible degradation shape around the diagnostic knee
                p = 1.0 if mtat < 210 else max(0.0, 1.0 - (mtat - 210) / 90)
                answered = rng.random() > (0.15 if mtat < 230 else 0.8)
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
                    "correct": correct, "abstained": int(answered is False),
                    "malformed": 0, "answer_canonical": "" if not answered else "x",
                    "confidence": float(rng.uniform(0.2, 0.95)),
                    "prediction": "I don't know" if not answered else "x", "gold": "x",
                    "scorer_version": "1.0",
                })
    df = schema.derive_boundary_conditions(
        schema.derive_memory_condition(pd.DataFrame(rows)), strict=True
    )
    verify = None
    try:
        from ahnexp import pilot_pass2
        from transformers import AutoTokenizer
        tok = AutoTokenizer.from_pretrained(config.experiment()["models"]["base"])
        verify = pilot_pass2.verify_grid(items, tok, pilot_pass2.build_pressure_plan(calibration), seed=seed)
    except Exception as exc:  # noqa: BLE001
        print(f"  (tokenizer unavailable — nesting/grid gates skipped in self-test: {exc})")

    ok = _analyse_and_gate(root, df, items, calibration, verify)
    assert ok, "self-test frame should pass every hard gate"
    print("\nSELF-TEST PASSED — pass2 gates + H1/H2/H3/knee analysis flow are sound.")


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--repo", default=os.environ.get("AHNEXP_ROOT"))
    ap.add_argument("--ahn-repo", default=os.environ.get("AHN_REPO"))
    ap.add_argument("--arms", nargs="+", default=None, help="subset of arms (staged run)")
    ap.add_argument("--self-test", action="store_true")
    ap.add_argument("--preflight", action="store_true")
    args = ap.parse_args()

    root = _bootstrap(args.repo)
    from ahnexp import config, dataset, evaluate, pilot_pass2

    if args.self_test:
        self_test(root)
        return

    from transformers import AutoTokenizer
    tok = AutoTokenizer.from_pretrained(config.experiment()["models"]["base"])
    items, plan, calibration, verify = _preflight(root, tok)
    if args.preflight:
        return

    p2 = config.pilot_pass2()
    arms = args.arms or list(p2["arms"])
    ahn_repo = str(Path(args.ahn_repo).expanduser().resolve()) if args.ahn_repo else None
    if ahn_repo:
        os.environ["AHN_REPO"] = ahn_repo

    banner(f"Pilot Pass 2 — arms={arms}  ({len(items)} items x {len(p2['target_model_tat'])} targets)")
    dataset.save_items(items, root / config.experiment()["outputs"]["pass2_items"],
                       seed=int(config.run_mode(MODE)["seeds"][0]))
    df = evaluate.run_grid(items, None, ahn_repo=ahn_repo, mode=MODE, arms=arms, pressure_plan=plan)

    raw = root / config.experiment()["outputs"]["pass2_raw"]
    if raw.exists() and args.arms:
        import pandas as pd
        prev = pd.read_parquet(raw)
        df = pd.concat([prev[~prev["architecture"].isin(arms)], df], ignore_index=True)
    df.to_parquet(raw, index=False)
    print(f"\nwrote {raw}  ({len(df)} trials)")

    full = df["architecture"].nunique() == len(p2["arms"])
    passed = _analyse_and_gate(root, df, items, calibration, verify)
    if full and not passed:
        raise SystemExit(1)
    if not full:
        print(f"\n  staged run ({df['architecture'].nunique()}/{len(p2['arms'])} arms) — "
              "gates re-evaluated when all arms are present.")


if __name__ == "__main__":
    main()
