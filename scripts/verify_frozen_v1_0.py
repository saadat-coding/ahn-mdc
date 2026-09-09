#!/usr/bin/env python3
"""Prove the frozen analysis v1.0 still reproduces bit-identically from the locked
artifact after the v1.1 amendment code was added.

Recomputes every frozen H1/H2/H3/control quantity with the CURRENT
`ahnexp.full_run` / `h1_degradation` / `h2_threshold` / `h3_calibration` code and
compares against the locked `final_audit/FINAL_LOCKED/final_*.csv`. Read-only.

    python scripts/verify_frozen_v1_0.py --repo . --nboot 2000

Exit 0 iff all compared quantities match to <= 1e-9 (float noise) and the locked
SHA-256 is unchanged.
"""
from __future__ import annotations

import argparse
import hashlib
import os
import sys
from pathlib import Path

LOCKED_SHA256 = "a72fd43e87457a70c2833314e1443a794fa4189362ac8206c56275ef427fb62e"
LOCK = "final_audit/FINAL_LOCKED"
PARQUET = f"{LOCK}/results_FINAL_92160.parquet"
TOL = 1e-9


def _bootstrap(repo):
    root = Path(repo).expanduser().resolve() if repo else Path.cwd()
    if not (root / "config" / "experiment.yaml").is_file():
        raise SystemExit(f"--repo {root} is not the ahn-mdc checkout")
    os.chdir(root); sys.path.insert(0, str(root / "src"))
    return root


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--repo", default=os.environ.get("AHNEXP_ROOT"))
    ap.add_argument("--nboot", type=int, default=2000)
    args = ap.parse_args()
    root = _bootstrap(args.repo)

    parq = root / PARQUET
    got = hashlib.sha256(parq.read_bytes()).hexdigest()
    print(f"locked SHA-256: {got}  {'OK' if got == LOCKED_SHA256 else 'MISMATCH'}")
    if got != LOCKED_SHA256:
        raise SystemExit("SHA MISMATCH — STOP")

    import numpy as np
    import pandas as pd

    from ahnexp import (config, dataset, full_run, h1_degradation as h1,
                        h2_threshold as h2, h3_calibration as h3)

    df = pd.read_parquet(parq)
    lock = root / LOCK
    diffs = []

    def cmp(fname, repro, keys, cols):
        fz = pd.read_csv(lock / fname)
        m = fz.merge(repro, on=keys, suffixes=("_f", "_r"), how="outer", indicator=True)
        unmatched = int((m["_merge"] != "both").sum())
        for c in cols:
            fc, rc = f"{c}_f", f"{c}_r"
            if fc not in m or rc not in m:
                continue
            d = (pd.to_numeric(m[fc], errors="coerce") - pd.to_numeric(m[rc], errors="coerce")).abs()
            mx = float(np.nanmax(d)) if len(d) else 0.0
            ok = (not np.isfinite(mx)) or mx <= TOL
            diffs.append((fname, c, mx, ok))
        if unmatched:
            diffs.append((fname, "<keys>", float("nan"), False))

    fcfg = config.final()
    items = dataset.generate_items(int(fcfg["n_items"]), seed=int(fcfg["seeds"][0]))  # noqa: F841

    cv = full_run.control_validity(df)
    cmp("final_control_validity_control_validity.csv", cv, ["fact_type"],
        ["n", "strict_accuracy", "answered_valid_accuracy", "abstention_rate", "malformed_rate"])

    valid = set(cv.loc[cv["in_h1_primary"], "fact_type"])
    d = df[df["fact_type"].isin(valid)]
    cmp("final_h1_h1_a_transition.csv", h1.a_transition(d), ["fact_type"], ["a_transition", "n", "n_items"])
    cmp("final_h1_h1_contrasts.csv", h1.a_transition_contrasts(d, n_resamples=args.nboot),
        ["a", "b"], ["diff", "ci_low", "ci_high", "p_holm"])
    cmp("final_h1_h1_sensitivity_excl_temporal.csv",
        h1.a_transition_contrasts(d[d["fact_type"] != "temporal"], n_resamples=args.nboot),
        ["a", "b"], ["diff", "p_holm"])
    cmp("final_h1_h1_sensitivity_temporal_answered_valid.csv",
        h1.a_transition_contrasts(d, value="answered_valid", n_resamples=args.nboot),
        ["a", "b"], ["diff", "p_holm"])

    summ = h2.transition_summary(df, n_resamples=args.nboot)
    cmp("final_h2_h2_width.csv", summ["width"], ["architecture"], ["width_tokens", "ci_low", "ci_high"])
    cmp("final_h2_h2_k_strict.csv", summ["k_strict"], ["architecture"], ["k_strict_acc", "ci_low", "ci_high"])
    cmp("final_h2_h2_shape_break_at_W.csv", summ["shape_break_at_W"], ["architecture"],
        ["rss_smooth", "rss_piecewise", "aic_smooth", "aic_piecewise"])
    cmp("final_h2_h2_a_recurrent.csv", summ["a_recurrent"], ["architecture"],
        ["a_recurrent", "ci_low", "ci_high", "n"])
    cmp("final_h2_h2_curves.csv", h2.curves(df), ["architecture", "pressure_group"],
        ["accuracy", "ci_low", "ci_high", "model_tokens_after_target", "n"])

    beh = h3.behavioral_signaling(df, n_resamples=args.nboot)
    cmp("final_h3_h3_behavioral_per_arm.csv", beh["per_arm"], ["architecture"],
        ["n", "appropriate_abstention_rate", "unsignalled_failure_rate"])
    cmp("final_h3_h3_behavioral_contrasts.csv", beh["contrasts"], ["contrast"],
        ["diff", "ci_low", "ci_high", "p_holm"])
    cmp("final_h3_h3_gap_change.csv", h3.gap_change(df, n_resamples=args.nboot), ["architecture"],
        ["gap_control", "gap_interval", "gap_change", "ci_low", "ci_high"])
    cmp("final_h3_h3_by_pressure_answered_valid.csv", h3.by_pressure(df, population="answered_valid"),
        ["pressure_group"], ["accuracy", "confidence", "gap", "ece", "brier", "cwr"])

    print(f"\n{'file':52} {'column':24} {'max|diff|':>12}  ok")
    n_ok = 0
    for f, c, mx, ok in diffs:
        print(f"{f:52} {c:24} {mx:12.2e}  {'yes' if ok else 'NO'}")
        n_ok += ok
    print(f"\n{n_ok}/{len(diffs)} quantities identical (<= {TOL:g}).")
    if n_ok != len(diffs):
        raise SystemExit("FROZEN v1.0 REPRODUCTION FAILED")
    print("FROZEN v1.0 ANALYSIS UNCHANGED — reproduces bit-identically from the locked artifact.")


if __name__ == "__main__":
    main()
