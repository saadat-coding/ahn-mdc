#!/usr/bin/env python3
"""Run the approved post-freeze reporting amendments (analysis version 1.1).

READS the locked, immutable artifact. WRITES only to
`outputs/final_v1_1_reporting_amendment/`. Never touches FINAL_LOCKED, the frozen
v1.0 outputs, the scorer, the prompt, the dataset, the grid, seeds, or W.
No GPU.

    python scripts/run_reporting_amendment.py --repo .
    python scripts/run_reporting_amendment.py --repo . --nboot 400   # fast preview
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
import sys
from pathlib import Path

LOCKED_SHA256 = "a72fd43e87457a70c2833314e1443a794fa4189362ac8206c56275ef427fb62e"
DEFAULT_PARQUET = "final_audit/FINAL_LOCKED/results_FINAL_92160.parquet"
OUT_SUBDIR = "outputs/final_v1_1_reporting_amendment"


def _bootstrap(repo: str | None) -> Path:
    root = Path(repo).expanduser().resolve() if repo else Path.cwd()
    if not (root / "config" / "experiment.yaml").is_file():
        raise SystemExit(f"--repo {root} is not the ahn-mdc checkout")
    os.chdir(root)
    sys.path.insert(0, str(root / "src"))
    return root


def _sha256(p: Path) -> str:
    return hashlib.sha256(p.read_bytes()).hexdigest()


def _write(obj, out: Path, name: str) -> None:
    import pandas as pd
    p = out / name
    if isinstance(obj, pd.DataFrame):
        obj.to_csv(p if p.suffix else p.with_suffix(".csv"), index=False)
    else:
        p.with_suffix(".json").write_text(json.dumps(obj, indent=2, default=str) + "\n")
    print(f"  wrote {p.name if p.suffix else p.name + '.csv'}")


def _dump_dict(d: dict, out: Path, prefix: str) -> dict:
    import pandas as pd
    meta = {}
    for k, v in d.items():
        if isinstance(v, pd.DataFrame):
            _write(v, out, f"{prefix}__{k}.csv")
        else:
            meta[k] = v
    if meta:
        (out / f"{prefix}__meta.json").write_text(json.dumps(meta, indent=2, default=str) + "\n")
        print(f"  wrote {prefix}__meta.json")
    return meta


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--repo", default=os.environ.get("AHNEXP_ROOT"))
    ap.add_argument("--parquet", default=None)
    ap.add_argument("--nboot", type=int, default=2000)
    args = ap.parse_args()

    root = _bootstrap(args.repo)
    parq = Path(args.parquet).expanduser().resolve() if args.parquet else root / DEFAULT_PARQUET
    if not parq.is_file():
        raise SystemExit(f"locked artifact not found: {parq}")

    got = _sha256(parq)
    print(f"locked artifact: {parq}")
    print(f"  sha256 {got}")
    if got != LOCKED_SHA256:
        raise SystemExit(f"SHA-256 MISMATCH — expected {LOCKED_SHA256}. STOP.")
    print("  sha256 OK\n")

    import pandas as pd

    from ahnexp import config, dataset, full_run, reporting_amendment as ra

    df = pd.read_parquet(parq)
    assert len(df) == 92160, f"expected 92160 rows, got {len(df)}"
    items = dataset.generate_items(int(config.final()["n_items"]), seed=int(config.final()["seeds"][0]))

    out = root / OUT_SUBDIR
    out.mkdir(parents=True, exist_ok=True)
    print(f"analysis_version = {ra.ANALYSIS_VERSION}   (frozen full_run = {full_run.ANALYSIS_VERSION}, untouched)")
    print(f"writing to {out}\n")

    summary: dict = {
        "analysis_version": ra.ANALYSIS_VERSION,
        "frozen_analysis_version": full_run.ANALYSIS_VERSION,
        "locked_parquet": str(parq),
        "locked_sha256": got,
        "n_resamples": args.nboot,
        "width_reference_levels": [ra.WIDTH_LO_LEVEL, ra.WIDTH_HI_LEVEL],
    }

    # -- H2 AMENDMENT (Option A) -------------------------------------------------
    print("H2 amendment — Option A (per-eligible-fact-type 90->10 width)")
    elig = ra.h2_width_eligibility(df)
    _write(elig, out, "h2_amend__eligibility.csv")
    ge = ra.globally_eligible_fact_types(df)
    by_ft = ra.h2_width_by_facttype(df, n_resamples=args.nboot)
    _write(by_ft, out, "h2_amend__width_by_facttype.csv")
    wsum = ra.h2_width_summary(df, n_resamples=args.nboot)
    _write(wsum, out, "h2_amend__width_summary_median.csv")
    wseed = ra.h2_width_seed_sensitivity(df)
    _write(wseed, out, "h2_amend__width_seed_sensitivity.csv")
    summary["h2_globally_eligible_fact_types"] = ge
    summary["h2_ineligible"] = elig.loc[~elig["eligible"], ["architecture", "fact_type", "reason"]].to_dict("records")
    summary["h2_width_summary_median"] = wsum.to_dict("records")
    print(f"  globally eligible: {ge}\n")

    # -- C: H1 exclude compound-relational ------------------------------------
    print("H1 [POST-FREEZE SENSITIVITY] — exclude compound-relational")
    h1x = ra.h1_exclude_compound_relational(df, n_resamples=args.nboot)
    _dump_dict(h1x, out, "h1_sensitivity__exclude_compound_relational")
    summary["h1_exclude_compound_relational"] = {
        k: v for k, v in h1x.items() if not hasattr(v, "to_dict")}
    print(f"  {h1x['n_significant_holm']}/{h1x['n_contrasts']} Holm-sig; omnibus p={h1x['omnibus_p']:.5f}\n")

    # -- D: residual fully-exact failures ------------------------------------
    print("[DESCRIPTIVE ROBUSTNESS] — residual fully-exact-through-generation failures")
    resid = ra.residual_fully_exact_failures(df)
    _dump_dict(resid, out, "descriptive__residual_fully_exact_failures")

    # -- E: disclosure / robustness tables ---------------------------------
    print("[LIMITATION / DISCLOSURE + ROBUSTNESS] tables")
    _dump_dict(ra.transformer_malformed(df), out, "disclosure__transformer_malformed")
    _dump_dict(ra.deep_recurrent_retention(df), out, "sensitivity__deep_recurrent_retention")
    _dump_dict(ra.temporal_counterbalancing(df, items), out, "disclosure__temporal_counterbalancing")
    _dump_dict(ra.compound_relational_control_warning(df), out, "disclosure__compound_relational_control_warning")
    _dump_dict(ra.per_seed_headline_robustness(df), out, "robustness__per_seed_headline")
    gates = ra.reproduce_plumbing_gates(df, items)
    _write(gates, out, "reproduced__plumbing_gates.csv")
    summary["plumbing_gates_blocking"] = int((gates["verdict"] == "FAIL").sum())

    (out / "AMENDMENT_SUMMARY.json").write_text(json.dumps(summary, indent=2, default=str) + "\n")
    print(f"\n  wrote AMENDMENT_SUMMARY.json")
    print(f"\nDONE — v1.1 amendment outputs in {out}")
    print("FINAL_LOCKED untouched; frozen v1.0 outputs untouched.")


if __name__ == "__main__":
    main()
