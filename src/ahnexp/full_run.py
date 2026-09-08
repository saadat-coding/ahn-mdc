"""Final inferential experiment — frozen design, gates and analysis.

FROZEN 2026-09-05 (protocol/final_experiment_design.md, config/final_design_manifest.json).

4 arms x 240 items x 12 model-tat targets x 8 seeds = 92,160 generations. Same code
path as every earlier run (`evaluate.run_grid`, `evaluate.score_row`,
`schema.validate`) with a per-fact-type `pressure_plan` from
config/final_calibration.json.

  * `pressure_plan`       — calibration json -> run_grid plan
  * `expected_trials`     — arms x items x targets x seeds
  * `control_validity`    — per-fact-type benchmark-control PASS / WARNING / FAIL
                            on the pooled control anchors (open_decisions #5a / #6)
  * `plumbing_gates`      — HARD pass/fail (trial count, schema, provenance, scorer
                            version, dup cells, matched design, targets realised,
                            nesting, grid realisation, temporal balance, leakage,
                            compression, malformed, control validity)
  * `scientific_warnings` — never block (reuses pilot_pass2.scientific_warnings)
  * `analyse`             — the FROZEN H1 / H2 / H3 endpoints + temporal
                            sensitivities + boundary table. No T-based table.

#17 is resolved FOR THIS INFERENTIAL PROTOCOL (Policy A): raw strict production
accuracy is the sole primary H1/H2 accuracy endpoint; temporal additionally
reports answered_valid_accuracy and abstention_rate; no baseline-adjusted primary,
no universal chance correction. This does not claim the general free-response-null
problem is theoretically solved.
"""

from __future__ import annotations

import json
import os
import re
import sys
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd

from ahnexp import (
    config,
    dataset,
    evaluate,
    h1_degradation,
    h2_threshold,
    h3_calibration,
    metrics,
    pilot_pass2,
    report,
    schema,
)

ANALYSIS_VERSION = "1.0"

_PERSON = re.compile(r"(?i)person[ _]?(\d+)")
_PROVENANCE_COLUMNS = pilot_pass2._PROVENANCE_COLUMNS


# ---------------------------------------------------------------------------
# Design
# ---------------------------------------------------------------------------

def pressure_plan(calibration: dict[str, Any] | None = None) -> dict[str, dict[int, int]]:
    """`{fact_type: {intended_model_tat: requested_tokens_after_target}}` for the final grid."""
    return pilot_pass2.build_pressure_plan(calibration or config.load_final_calibration())


def expected_trials(n_arms: int | None = None) -> int:
    fcfg = config.final()
    n_arms = len(fcfg["arms"]) if n_arms is None else n_arms
    return n_arms * int(fcfg["n_items"]) * len(fcfg["target_model_tat"]) * len(fcfg["seeds"])


def verify_grid(items, tokenizer, plan=None, seed: int = 0) -> pd.DataFrame:
    return pilot_pass2.verify_grid(items, tokenizer, plan or pressure_plan(), seed=seed)


# ---------------------------------------------------------------------------
# Resumable staged execution (persistence repair — NOT a scientific change)
# ---------------------------------------------------------------------------
#
# The canonical unique experimental-cell key. Every one of the 92,160 frozen cells
# is fully reproducible from these four values: dataset.build_trajectory seeds a
# fresh random.Random(seed) per call and decoding is greedy, so a cell's content
# never depends on iteration order. Resuming at cell (or seed) granularity is
# therefore identical to an uninterrupted run.
CELL_KEY = ["architecture", "item_id", "seed", "intended_model_tokens_after_target"]

# Columns that must agree when the same cell appears twice (prev + regenerated).
_OUTCOME_COLS = ("correct", "abstained", "malformed", "answer_canonical",
                 "prediction", "gold", "confidence", "n_new_tokens",
                 "model_tokens_after_target", "scorer_version")


def _read_cell_frame(raw_path: Path) -> pd.DataFrame:
    if not Path(raw_path).exists():
        return pd.DataFrame(columns=CELL_KEY)
    return pd.read_parquet(raw_path, columns=CELL_KEY)


def completed_cells(raw_path: Path) -> set[tuple[str, str, int, int]]:
    """The set of `(architecture, item_id, seed, intended_model_tat)` already persisted."""
    df = _read_cell_frame(raw_path)
    return {
        (str(a), str(i), int(s), int(t))
        for a, i, s, t in df.itertuples(index=False, name=None)
    }


_FROZEN_ITEM_IDS: set[str] | None = None


def frozen_item_ids() -> set[str]:
    """The item_ids of the frozen 240-item set (memoised)."""
    global _FROZEN_ITEM_IDS
    if _FROZEN_ITEM_IDS is None:
        fcfg = config.final()
        _FROZEN_ITEM_IDS = {
            it.item_id for it in dataset.generate_items(int(fcfg["n_items"]),
                                                        seed=int(fcfg["seeds"][0]))
        }
    return _FROZEN_ITEM_IDS


def assert_compatible_with_frozen_design(df: pd.DataFrame, *, allow_incomplete: bool = True) -> None:
    """Fail loudly if any persisted row is not a valid frozen-design cell, or if a
    cell is duplicated. Does not require completeness unless `allow_incomplete` is
    False (then the full 92,160-cell design must be present exactly once each)."""
    if df.empty:
        return
    fcfg = config.final()
    valid_items = frozen_item_ids()
    problems: list[str] = []
    missing_cols = [c for c in CELL_KEY if c not in df.columns]
    if missing_cols:
        raise SystemExit(f"FROZEN-DESIGN CONFLICT: artifact is missing cell-key columns {missing_cols}")

    bad_arch = sorted(set(df["architecture"]) - set(fcfg["arms"]))
    bad_seed = sorted(set(int(s) for s in df["seed"]) - set(int(s) for s in fcfg["seeds"]))
    bad_tgt = sorted(set(int(t) for t in df["intended_model_tokens_after_target"])
                     - set(int(t) for t in fcfg["target_model_tat"]))
    bad_item = sorted(set(df["item_id"]) - valid_items)
    if bad_arch:
        problems.append(f"unknown architectures {bad_arch}")
    if bad_seed:
        problems.append(f"unknown seeds {bad_seed}")
    if bad_tgt:
        problems.append(f"unknown intended targets {bad_tgt}")
    if bad_item:
        problems.append(f"{len(bad_item)} item_ids not in the frozen 240-item set (e.g. {bad_item[:3]})")

    dup = df.duplicated(subset=CELL_KEY)
    if dup.any():
        sample = df.loc[dup, CELL_KEY].head(3).to_dict("records")
        problems.append(f"{int(dup.sum())} duplicated cells (e.g. {sample})")

    if not allow_incomplete:
        expected = expected_trials()
        if len(df) != expected:
            problems.append(f"{len(df)} rows, expected exactly {expected}")

    if problems:
        raise SystemExit("FROZEN-DESIGN CONFLICT:\n  - " + "\n  - ".join(problems))


def _assert_no_conflicting_dupes(merged: pd.DataFrame) -> None:
    """Same cell twice with a different scored outcome => stop (non-determinism or a
    silent design change). Identical duplicates are fine and get collapsed."""
    dup_mask = merged.duplicated(subset=CELL_KEY, keep=False)
    if not dup_mask.any():
        return
    cols = [c for c in _OUTCOME_COLS if c in merged.columns]
    conflicts = []
    for key, grp in merged.loc[dup_mask].groupby(CELL_KEY):
        if grp[cols].astype(str).nunique().gt(1).any():
            conflicts.append(dict(zip(CELL_KEY, key)))
    if conflicts:
        raise SystemExit(
            "CONFLICTING DUPLICATE CELLS (same cell, different result — refusing to "
            f"merge):\n  - " + "\n  - ".join(str(c) for c in conflicts[:5])
        )


def design_progress(df: pd.DataFrame) -> dict[str, Any]:
    """Per-arm completed-cell counts and whether the full frozen design is present."""
    fcfg = config.final()
    per_arm_target = int(fcfg["n_items"]) * len(fcfg["target_model_tat"]) * len(fcfg["seeds"])
    per_seed_target = int(fcfg["n_items"]) * len(fcfg["target_model_tat"])
    counts, seeds_done = {}, {}
    for arm in fcfg["arms"]:
        sub = df[df["architecture"] == arm] if not df.empty else df
        n = int(len(sub.drop_duplicates(subset=CELL_KEY))) if len(sub) else 0
        counts[arm] = n
        seeds_done[arm] = sorted(
            int(s) for s in (sub["seed"].unique() if len(sub) else [])
            if len(sub[sub["seed"] == s].drop_duplicates(subset=CELL_KEY)) == per_seed_target
        )
    total = int(len(df.drop_duplicates(subset=CELL_KEY))) if not df.empty else 0
    complete = (total == expected_trials()
                and all(counts[a] == per_arm_target for a in fcfg["arms"]))
    return {"per_arm_cells": counts, "per_arm_target": per_arm_target,
            "seeds_complete": seeds_done, "total_cells": total,
            "expected_total": expected_trials(), "complete": complete}


def checkpoint_merge(new_rows: pd.DataFrame | None, raw_path: Path,
                     *, architecture: str | None = None, seed: int | None = None,
                     verbose: bool = True) -> pd.DataFrame:
    """Merge `new_rows` into `raw_path` atomically, preserving every previously
    completed architecture, deduplicating ONLY on `CELL_KEY`.

      1. read the existing artifact (if any); require identical columns
      2. concat; fail loudly on a conflicting duplicate cell; collapse exact dups
      3. validate every row against the frozen design (known arm/item/seed/target,
         no dup cells)
      4. write a temp parquet, re-read + validate it, then os.replace() into place
         (a crash mid-write cannot corrupt the existing artifact)
      5. print an explicit CHECKPOINT SAVED block and flush stdout

    Returns the merged frame.
    """
    raw_path = Path(raw_path)
    raw_path.parent.mkdir(parents=True, exist_ok=True)

    nothing_new = new_rows is None or not len(new_rows)
    if nothing_new and raw_path.exists():
        # a fully-skipped chunk on restart — do not rewrite the artifact
        merged = pd.read_parquet(raw_path)
        if verbose:
            _print_checkpoint(merged, architecture, seed, skipped=True)
        return merged

    if raw_path.exists():
        prev = pd.read_parquet(raw_path)
        if new_rows is not None and len(new_rows):
            if set(prev.columns) != set(new_rows.columns):
                only_prev = sorted(set(prev.columns) - set(new_rows.columns))
                only_new = sorted(set(new_rows.columns) - set(prev.columns))
                raise SystemExit(
                    "COLUMN MISMATCH between the existing artifact and the new rows "
                    f"(prev-only {only_prev}, new-only {only_new}). The existing "
                    "artifact was not produced by the current frozen code — refusing to merge."
                )
            merged = pd.concat([prev, new_rows[prev.columns]], ignore_index=True)
        else:
            merged = prev.copy()
    else:
        merged = (new_rows.copy() if new_rows is not None and len(new_rows)
                  else pd.DataFrame(columns=CELL_KEY))

    _assert_no_conflicting_dupes(merged)
    merged = merged.drop_duplicates(subset=CELL_KEY, keep="first").reset_index(drop=True)
    assert_compatible_with_frozen_design(merged)

    tmp = raw_path.with_name(raw_path.name + ".tmp")
    merged.to_parquet(tmp, index=False)
    check = pd.read_parquet(tmp)
    if len(check) != len(merged) or set(check.columns) != set(merged.columns) \
            or check.duplicated(subset=CELL_KEY).any():
        tmp.unlink(missing_ok=True)
        raise SystemExit("ATOMIC WRITE VALIDATION FAILED — temp parquet is not a "
                         "faithful copy; existing artifact left untouched.")
    os.replace(tmp, raw_path)

    if verbose:
        _print_checkpoint(merged, architecture, seed, skipped=False)
    return merged


def _print_checkpoint(merged: pd.DataFrame, architecture: str | None,
                      seed: int | None, *, skipped: bool) -> None:
    prog = design_progress(merged)
    arm = architecture or "?"
    print("\nCHECKPOINT SAVED" + ("  (no new rows — chunk already complete)" if skipped else ""))
    if architecture:
        note = f"  (just wrote seed {seed})" if seed is not None and not skipped else ""
        print(f"{arm} completed seeds: {prog['seeds_complete'].get(arm, [])}{note}")
        print(f"{arm} rows: {prog['per_arm_cells'].get(arm, 0)} / {prog['per_arm_target']}")
    print(f"total rows: {prog['total_cells']} / {prog['expected_total']}")
    sys.stdout.flush()


# ---------------------------------------------------------------------------
# Per-fact-type benchmark-control validity (open_decisions #5a / #6)
# ---------------------------------------------------------------------------

def control_validity(df: pd.DataFrame) -> pd.DataFrame:
    """Per fact type on the pooled control anchors (intended model-tat 150 + 180).

    Non-temporal: PASS if strict >= pass_strict; FAIL if strict < fail_strict
    (benchmark invalid -> excluded from H1 primary); WARNING for the middle band or
    malformed/abstention above their caps. Temporal: judged on answered_valid
    accuracy with abstention tracked separately (spirit of #5a — a retrievability
    FLOOR, no upper-bound red flag).
    """
    fcfg = config.final()
    cv = config.experiment()["acceptance"]["control_validity"]
    anchors = list(fcfg["control_anchors"])
    key = schema.pressure_group_key(df)
    ctrl = df[df[key].isin(anchors)]

    rows = []
    for ft, g in ctrl.groupby("fact_type"):
        strict = float(g["correct"].mean())
        abst = float(g["abstained"].mean()) if "abstained" in g else np.nan
        malf = float(g["malformed"].mean()) if "malformed" in g else np.nan
        av = metrics.answered_valid(g)
        av_acc = float(av["correct"].mean()) if len(av) else np.nan

        if ft == "temporal":
            t = cv["temporal"]
            lo, hi = t["warn_abstention"]
            if av_acc < t["fail_answered_valid"] or (abst == abst and abst > t["fail_abstention"]):
                verdict, why = "FAIL", f"answered_valid {av_acc:.2f} / abstention {abst:.2f}"
            elif av_acc >= t["pass_answered_valid"] and not (lo <= (abst if abst == abst else 0) <= hi):
                verdict, why = "PASS", f"answered_valid {av_acc:.2f}, abstention {abst:.2f}"
            elif lo <= (abst if abst == abst else 0) <= hi:
                verdict, why = "WARNING", f"abstention {abst:.2f} in [{lo}, {hi}]"
            else:
                verdict, why = "WARNING", f"answered_valid {av_acc:.2f} below {t['pass_answered_valid']}"
        else:
            n = cv["non_temporal"]
            if strict < n["fail_strict"]:
                verdict, why = "FAIL", f"strict {strict:.2f} < {n['fail_strict']}"
            elif strict >= n["pass_strict"] and (malf != malf or malf <= n["warn_malformed"]) \
                    and (abst != abst or abst <= n["warn_abstention"]):
                verdict, why = "PASS", f"strict {strict:.2f}"
            else:
                bits = [f"strict {strict:.2f}"]
                if malf == malf and malf > n["warn_malformed"]:
                    bits.append(f"malformed {malf:.2f}")
                if abst == abst and abst > n["warn_abstention"]:
                    bits.append(f"abstention {abst:.2f}")
                verdict, why = "WARNING", "; ".join(bits)

        rows.append({
            "fact_type": ft, "construct": report.fact_type_label(ft),
            "n": int(len(g)), "strict_accuracy": strict,
            "answered_valid_accuracy": av_acc, "abstention_rate": abst,
            "malformed_rate": malf, "verdict": verdict, "detail": why,
            "in_h1_primary": verdict != "FAIL",
        })
    return pd.DataFrame(rows).sort_values("fact_type").reset_index(drop=True)


# ---------------------------------------------------------------------------
# Hard plumbing gates
# ---------------------------------------------------------------------------

def _temporal_cells(items) -> dict[tuple, int]:
    from collections import Counter

    counts: Counter = Counter()
    for it in items:
        if it.fact.fact_type != "temporal":
            continue
        gold_n = int(_PERSON.search(it.fact.answer).group(1))
        q = [int(x) for x in _PERSON.findall(it.fact.question)]
        counts[(gold_n == max(q), q[0] == gold_n, it.distractor_density)] += 1
    return dict(counts)


def plumbing_gates(df: pd.DataFrame, items, calibration: dict[str, Any],
                   verify: pd.DataFrame | None = None) -> pd.DataFrame:
    """HARD pass/fail for the final run. A FAIL means the run is not analysable."""
    checks: list[dict[str, Any]] = []

    def add(gate: str, ok: bool, detail: str) -> None:
        checks.append({"gate": gate, "verdict": "PASS" if ok else "FAIL", "detail": detail})

    fcfg = config.final()
    arms = list(fcfg["arms"])
    targets = list(fcfg["target_model_tat"])
    n_items = int(fcfg["n_items"])
    seeds = list(fcfg["seeds"])
    got_arms = sorted(df["architecture"].unique())
    staged = set(got_arms) != set(arms)
    expected = len(got_arms) * n_items * len(targets) * len(seeds)

    add("trial_count", len(df) == expected,
        f"{len(df)} rows; expected {len(got_arms)}x{n_items}x{len(targets)}x{len(seeds)} = {expected}")

    try:
        schema.validate(df, needs=("core", "h1", "h2", "h3"))
        add("schema_valid", True, "core/h1/h2/h3 columns present, flags 0/1, no dup design cells")
    except Exception as exc:  # noqa: BLE001
        add("schema_valid", False, f"{type(exc).__name__}: {exc}")

    for col in _PROVENANCE_COLUMNS:
        present = col in df.columns and df[col].notna().all()
        add(f"provenance:{col}", present, "present, no nulls" if present else "missing or has nulls")

    want = evaluate.SCORER_VERSION
    got = sorted(df["scorer_version"].unique()) if "scorer_version" in df else []
    add("scorer_version", got == [want], f"got {got}, expected ['{want}']")

    key = ["architecture", "item_id", "seed", "intended_model_tokens_after_target"]
    dups = int(df.duplicated(subset=key).sum()) if set(key) <= set(df.columns) else -1
    add("no_duplicate_cells", dups == 0, f"{dups} duplicate (arm,item,seed,target) rows")

    try:
        cells = df.groupby("architecture").apply(
            lambda g: set(zip(g["item_id"], g["intended_model_tokens_after_target"], g["seed"])),
            include_groups=False,
        )
        ref = cells.iloc[0]
        mismatch = {a: len(ref ^ cells[a]) for a in cells.index if cells[a] != ref}
        add("matched_design", not mismatch,
            "all arms see identical (item,target,seed) cells" if not mismatch else f"unmatched: {mismatch}")
    except Exception as exc:  # noqa: BLE001
        add("matched_design", False, f"{type(exc).__name__}: {exc}")

    got_targets = sorted(int(t) for t in df["intended_model_tokens_after_target"].dropna().unique())
    add("all_targets_present", got_targets == sorted(int(t) for t in targets), f"got {got_targets}")

    add("seeds_present", sorted(int(s) for s in df["seed"].unique()) == sorted(int(s) for s in seeds),
        f"got {sorted(int(s) for s in df['seed'].unique())}, expected {seeds}")

    if verify is not None and "nested_ok" in verify.columns:
        bad = verify.loc[~verify["nested_ok"], "item_id"].unique().tolist()
        add("trajectory_nesting", not bad,
            "lower-pressure block is a prefix of the higher-pressure block" if not bad
            else f"non-nested items: {bad[:5]}")

    if verify is not None:
        tol = {"calibration_tolerance_transition": fcfg["calibration_tolerance_transition"],
               "calibration_tolerance_other": fcfg["calibration_tolerance_other"]}
        rep = pilot_pass2.calibration_report(verify, fcfg["bands"], tolerances=tol)
        off = rep.loc[~rep["within_tolerance"]]
        add("grid_realised", off.empty,
            "every (fact_type, target) median model-tat within band tolerance" if off.empty else
            "; ".join(f"{r.fact_type}@{r.intended_model_tat}: {r.median_error:+.0f} (tol {r.tolerance})"
                      for r in off.itertuples()))

    tcells = _temporal_cells(items)
    n_temporal = sum(1 for it in items if it.fact.fact_type == "temporal")
    per_cell = n_temporal // 8
    balanced = len(tcells) == 8 and set(tcells.values()) == {per_cell}
    add("temporal_factorial_balance", balanced,
        f"8 cells x {per_cell} (direction x position x density)" if balanced else f"cells: {tcells}")

    leaks = []
    for it in items:
        try:
            dataset.assert_no_collision(it)
        except ValueError as exc:  # noqa: BLE001
            leaks.append(str(exc))
    add("no_answer_leakage", not leaks,
        "assert_no_collision clean for all items" if not leaks else f"{len(leaks)} leaks: {leaks[:2]}")

    w = int(df["sliding_window"].iloc[0])
    past = int((df["model_tokens_after_target"] >= w).sum())
    add("compression_occurred", past > 0, f"{past}/{len(df)} trials at model_tat >= W={w}")

    if "malformed" in df.columns:
        pilot_pass2._malformed_gates(df, add, checks)

    # control validity — a non-temporal FAIL is a hard gate (benchmark invalid for
    # that type); WARNING / temporal outcomes are reported, never blocking.
    if not staged:
        cv = control_validity(df)
        for r in cv.itertuples():
            if r.verdict == "FAIL" and r.fact_type != "temporal":
                add(f"control_validity:{r.fact_type}", False,
                    f"{r.detail} — benchmark invalid for this type; excluded from H1 primary")
            else:
                checks.append({"gate": f"control_validity:{r.fact_type}",
                               "verdict": r.verdict if r.verdict != "PASS" else "PASS",
                               "detail": r.detail})

    return pd.DataFrame(checks)


def blocking(gates: pd.DataFrame) -> pd.DataFrame:
    return gates[gates["verdict"] == "FAIL"]


scientific_warnings = pilot_pass2.scientific_warnings


# ---------------------------------------------------------------------------
# Frozen analysis
# ---------------------------------------------------------------------------

def analyse(df: pd.DataFrame, items=None, out: dict[str, Path] | None = None,
            n_resamples: int | None = None) -> dict[str, Any]:
    """The FROZEN H1 / H2 / H3 endpoints (protocol/final_experiment_design.md).

    Aggregates ONE balanced cell per intended model-tat target
    (`schema.pressure_group_key`); fits/plots against realised
    `model_tokens_after_target`. Raw strict production accuracy is the primary
    accuracy endpoint everywhere (#17 Policy A). No T-based / deprecated-threshold
    table is produced.
    """
    schema.validate(df, needs=("core", "h1", "h2", "h3"))
    fcfg = config.final()
    w = int(df["sliding_window"].iloc[0])
    interval = tuple(fcfg["transition_interval"])
    key = schema.pressure_group_key(df)

    cv = control_validity(df)
    valid_types = set(cv.loc[cv["in_h1_primary"], "fact_type"])
    h1_df = df[df["fact_type"].isin(valid_types)]

    # ---- H1: A_transition per type, 10 pairwise contrasts (+Holm), omnibus companion
    h1_a = h1_degradation.a_transition(h1_df)
    h1_contrasts = h1_degradation.a_transition_contrasts(h1_df, n_resamples=n_resamples)
    h1_omnibus = h1_degradation.a_transition_omnibus(
        h1_df, n_perm=int(n_resamples or 2000))
    h1_supported = bool(h1_contrasts["significant_holm"].any())
    # temporal sensitivities
    sens_excl_temporal = h1_degradation.a_transition_contrasts(
        h1_df[h1_df["fact_type"] != "temporal"], n_resamples=n_resamples)
    sens_temporal_av = h1_degradation.a_transition_contrasts(
        h1_df, value="answered_valid", n_resamples=n_resamples)

    # ---- H2: width / shape / A_transition gap / A_recurrent / descriptive K
    h2 = h2_threshold.transition_summary(df, interval=interval, n_resamples=n_resamples)
    h2_curves = h2_threshold.curves(df)

    # ---- H3: behavioral primary + answered-valid calibration secondary
    h3_behavioral = h3_calibration.behavioral_signaling(df, n_resamples=n_resamples)
    h3_gap_change = h3_calibration.gap_change(df, interval=interval, n_resamples=n_resamples)
    h3_by_pressure = h3_calibration.by_pressure(df, population="answered_valid")
    h3_abstention = pd.concat(
        [h3_calibration.abstention_confidence(g).assign(architecture=a)
         for a, g in df.groupby("architecture")], ignore_index=True,
    ) if "abstained" in df.columns else pd.DataFrame()

    # ---- descriptive strict accuracy by arch x type x intended target
    coord = schema.pressure_coordinate(df)
    grid_rows = []
    for (arm, ft, lvl), g in df.groupby(["architecture", "fact_type", key]):
        av = metrics.answered_valid(g)
        grid_rows.append({
            "architecture": arm, "fact_type": ft, "intended_model_tat": int(lvl),
            "model_tokens_after_target": float(g[coord].mean()),
            "strict_accuracy": float(g["correct"].mean()),
            "answered_valid_accuracy": float(av["correct"].mean()) if len(av) else np.nan,
            "abstention_rate": float(g["abstained"].mean()) if "abstained" in g else np.nan,
            "malformed_rate": float(g["malformed"].mean()) if "malformed" in g else np.nan,
            "n": int(len(g)),
        })
    grid = pd.DataFrame(grid_rows).sort_values(["architecture", "fact_type", "intended_model_tat"])

    temporal = (report.temporal_response_table(df, items=items)
                if "temporal" in set(df["fact_type"]) else pd.DataFrame())
    boundary = pilot_pass2._boundary_table(df)

    summary = {
        "purpose": "FINAL inferential experiment — frozen design (protocol/final_experiment_design.md)",
        "analysis_version": ANALYSIS_VERSION,
        "n_trials": int(len(df)),
        "arms": sorted(df["architecture"].unique().tolist()),
        "window_reference_W": w,
        "transition_interval": list(interval),
        "issue_17": "resolved for THIS inferential protocol (Policy A): raw strict "
                    "production accuracy is the sole primary H1/H2 accuracy endpoint; "
                    "temporal also reports answered_valid_accuracy + abstention_rate; "
                    "no baseline-adjusted primary, no universal chance correction.",
        "control_validity": cv.set_index("fact_type")["verdict"].to_dict(),
        "h1_types_in_primary": sorted(valid_types),
        "h1_supported": h1_supported,
        "h1_omnibus_p": h1_omnibus["p_value"],
        "h1_a_transition": h1_a.set_index("fact_type")["a_transition"].round(4).to_dict(),
        "h2_width_verdict": h2["width"].set_index("architecture")["verdict"].to_dict(),
        "h2_a_transition_gap": h2["a_transition_gap"],
        "h3_behavioral_region": h3_behavioral["region"],
        "grouping": "one balanced cell per intended model-tat target "
                    "(schema.pressure_group_key); x = realised model_tokens_after_target",
        "no_published_T": True,
    }

    tables = {
        "control_validity": cv,
        "grid": grid,
        "h1_a_transition": h1_a,
        "h1_contrasts": h1_contrasts,
        "h1_sensitivity_excl_temporal": sens_excl_temporal,
        "h1_sensitivity_temporal_answered_valid": sens_temporal_av,
        "h2_curves": h2_curves,
        "h2_width": h2["width"],
        "h2_k_strict": h2["k_strict"],
        "h2_shape_break_at_W": h2["shape_break_at_W"],
        "h2_a_recurrent": h2["a_recurrent"],
        "h3_behavioral_per_arm": h3_behavioral["per_arm"],
        "h3_behavioral_contrasts": h3_behavioral["contrasts"],
        "h3_gap_change": h3_gap_change,
        "h3_by_pressure_answered_valid": h3_by_pressure,
        "h3_abstention_confidence": h3_abstention,
        "temporal": temporal,
        "boundary": boundary,
        "warnings": scientific_warnings(df),
    }
    extras = {
        "h1_omnibus": h1_omnibus,
        "h2_a_transition_gap": h2["a_transition_gap"],
        "h3_behavioral_summary": {k: v for k, v in h3_behavioral.items()
                                  if k not in ("per_arm", "contrasts")},
    }

    if out:
        for name, prefix in out.items():
            prefix = Path(prefix)
            if name == "summary":
                prefix.write_text(json.dumps({**summary, "extras": extras}, indent=2, default=str) + "\n")
            elif name in tables:
                _write_table(tables[name], prefix, name)
            elif name in ("h1", "h2", "h3", "control"):
                for tname, tbl in tables.items():
                    if tname.startswith(name.replace("control", "control_validity")):
                        _write_table(tbl, Path(f"{prefix}_{tname}"), tname)
    return {"summary": summary, "tables": tables, "extras": extras}


def _write_table(tbl: pd.DataFrame, prefix: Path, name: str) -> None:
    if not (isinstance(tbl, pd.DataFrame) and len(tbl)):
        return
    prefix.parent.mkdir(parents=True, exist_ok=True)
    tbl.to_csv(f"{prefix}.csv", index=False)
    Path(f"{prefix}.md").write_text(
        report.to_markdown(tbl.round(4), f"Final — {name}", mode="full")
    )
