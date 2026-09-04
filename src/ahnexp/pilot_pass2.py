"""Pilot Pass 2 — model-tat-targeted four-arm plumbing + localization run.

Not inferential evidence. See protocol/pilot_pass2.md and
protocol/h2_threshold_decision_2026-09-04.md.

This module holds the reusable pieces:

  * `build_pressure_plan`   — calibration json -> run_grid `pressure_plan`
  * `verify_grid`           — no-model: build every (item, target) trajectory and
                              report intended vs realised model_tokens_after_target
  * `plumbing_gates`        — HARD pass/fail (missing trials, dup cells, unmatched
                              arms, scorer version, missing provenance columns,
                              trajectory nesting, temporal balance, leakage, schema,
                              grid realisation)
  * `scientific_warnings`   — never fail the run (low recurrent accuracy,
                              non-monotonic abstention, per-type knee spread, ...)
  * `analyse`               — H1 / H2 / H3 / knee tables + summary json
"""

from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd

from ahnexp import (
    config,
    dataset,
    evaluate,
    h2_threshold,
    h3_calibration,
    report,
    schema,
)

_PERSON = re.compile(r"(?i)person[ _]?(\d+)")
_PROVENANCE_COLUMNS = (
    "requested_tokens_after_target",
    "model_tokens_after_target",
    "target_fact_tokens",
    "n_new_tokens",
    "intended_model_tokens_after_target",
)


# ---------------------------------------------------------------------------
# Calibration -> pressure plan
# ---------------------------------------------------------------------------

def build_pressure_plan(calibration: dict[str, Any]) -> dict[str, dict[int, int]]:
    """`{fact_type: {intended_model_tat: requested_tokens_after_target}}`."""
    plan: dict[str, dict[int, int]] = {}
    for fact_type, entry in calibration["per_type"].items():
        plan[fact_type] = {
            int(target): int(requested)
            for target, requested in entry["requested_by_target"].items()
        }
    return plan


# ---------------------------------------------------------------------------
# No-model grid verification (the dry run)
# ---------------------------------------------------------------------------

def _ordered_distractors(item: dataset.Item, seed: int) -> list[dataset.Fact]:
    import random

    order = list(item.distractors)
    random.Random(seed).shuffle(order)
    return order


def verify_grid(
    items: list[dataset.Item],
    tokenizer,
    plan: dict[str, dict[int, int]],
    seed: int = 0,
) -> pd.DataFrame:
    """One row per (item, intended target): requested / intended / realised model-tat.

    Also carries `nested_ok` — the realised distractor block at this target is a
    prefix of the block at the next-larger target for the same item/seed.
    """
    rows: list[dict[str, Any]] = []
    for item in items:
        per_type = plan[item.fact.fact_type]
        targets = sorted(per_type)
        blocks: dict[int, list[str]] = {}
        for target in targets:
            requested = int(per_type[target])
            tj = dataset.build_trajectory(
                item, tokenizer, tokens_after_target=requested, seed=seed
            )
            order = _ordered_distractors(item, seed)
            after, _ = dataset._fill(order, tokenizer, requested, start=0)
            blocks[target] = [f.text for f in after]
            rows.append({
                "item_id": item.item_id,
                "fact_type": item.fact.fact_type,
                "intended_model_tat": int(target),
                "requested_tokens": requested,
                "realised_model_tat": int(tj["model_tokens_after_target"]),
                "realised_tokens_after_target": int(tj["tokens_after_target"]),
                "target_fact_tokens": int(tj["target_fact_tokens"]),
                "error": int(tj["model_tokens_after_target"]) - int(target),
            })
        for lo, hi in zip(targets, targets[1:]):
            prefix, longer = blocks[lo], blocks[hi]
            nested = longer[: len(prefix)] == prefix
            for r in rows:
                if r["item_id"] == item.item_id and r["intended_model_tat"] == lo:
                    r["nested_ok"] = bool(nested)
        for r in rows:
            if r["item_id"] == item.item_id and r["intended_model_tat"] == targets[-1]:
                r["nested_ok"] = True

    return pd.DataFrame(rows)


def calibration_report(verify: pd.DataFrame, bands: dict[str, list[int]]) -> pd.DataFrame:
    """Per-(fact_type, intended target): median realised model-tat and error, plus
    whether the band tolerance is met (median across items, the runner uses one
    requested per (type, target))."""
    p2 = config.pilot_pass2()
    tol_transition = int(p2["calibration_tolerance_transition"])
    tol_other = int(p2["calibration_tolerance_other"])
    transition = set(bands["transition"])

    rows = []
    for (fact_type, target), block in verify.groupby(["fact_type", "intended_model_tat"]):
        med = float(block["realised_model_tat"].median())
        band_tol = tol_transition if int(target) in transition else tol_other
        rows.append({
            "fact_type": fact_type,
            "intended_model_tat": int(target),
            "band": _band_of(int(target), bands),
            "requested_tokens": int(block["requested_tokens"].iloc[0]),
            "realised_model_tat_median": med,
            "realised_model_tat_min": int(block["realised_model_tat"].min()),
            "realised_model_tat_max": int(block["realised_model_tat"].max()),
            "median_error": med - int(target),
            "max_abs_item_error": int(block["error"].abs().max()),
            "tolerance": band_tol,
            "within_tolerance": abs(med - int(target)) <= band_tol,
        })
    return pd.DataFrame(rows).sort_values(["fact_type", "intended_model_tat"]).reset_index(drop=True)


def _band_of(target: int, bands: dict[str, list[int]]) -> str:
    for name, members in bands.items():
        if target in members:
            return name
    return "?"


# ---------------------------------------------------------------------------
# Hard plumbing gates
# ---------------------------------------------------------------------------

def _temporal_factor_counts(items: list[dataset.Item]) -> dict[tuple, int]:
    from collections import Counter

    def nums(text: str) -> list[int]:
        return [int(x) for x in _PERSON.findall(text)]

    counts: Counter = Counter()
    for it in items:
        if it.fact.fact_type != "temporal":
            continue
        gold_n = int(_PERSON.search(it.fact.answer).group(1))
        q = nums(it.fact.question)
        gold_is_higher = gold_n == max(q)
        gold_is_first = q[0] == gold_n
        counts[(gold_is_higher, gold_is_first, it.distractor_density)] += 1
    return dict(counts)


def plumbing_gates(
    df: pd.DataFrame,
    items: list[dataset.Item],
    calibration: dict[str, Any],
    verify: pd.DataFrame | None = None,
) -> pd.DataFrame:
    """HARD pass/fail. A FAIL here means the run is not analysable — stop and fix."""
    checks: list[dict[str, Any]] = []

    def add(gate: str, ok: bool, detail: str) -> None:
        checks.append({"gate": gate, "verdict": "PASS" if ok else "FAIL", "detail": detail})

    p2 = config.pilot_pass2()
    arms = list(p2["arms"])
    targets = list(p2["target_model_tat"])
    n_items = int(config.run_mode("pilot_pass2")["n_items"])
    seeds = list(config.run_mode("pilot_pass2")["seeds"])
    expected = len(arms) * n_items * len(targets) * len(seeds)

    # 1. trial count
    add("trial_count", len(df) == expected,
        f"{len(df)} rows, expected {len(arms)}x{n_items}x{len(targets)}x{len(seeds)} = {expected}")

    # 2. schema validates for all three hypotheses
    try:
        schema.validate(df, needs=("core", "h1", "h2", "h3"))
        add("schema_valid", True, "core/h1/h2/h3 required columns present, flags 0/1, no dup design cells")
    except Exception as exc:  # noqa: BLE001
        add("schema_valid", False, f"{type(exc).__name__}: {exc}")

    # 3. provenance columns present and non-null
    for col in _PROVENANCE_COLUMNS:
        present = col in df.columns and df[col].notna().all()
        add(f"provenance:{col}", present,
            "present, no nulls" if present else "missing or has nulls")

    # 4. scorer version frozen
    want = evaluate.SCORER_VERSION
    got = sorted(df["scorer_version"].unique()) if "scorer_version" in df else []
    add("scorer_version", got == [want], f"got {got}, expected ['{want}']")

    # 5. duplicate design cells
    key = ["architecture", "item_id", "seed", "intended_model_tokens_after_target"]
    dups = int(df.duplicated(subset=key).sum()) if set(key) <= set(df.columns) else -1
    add("no_duplicate_cells", dups == 0, f"{dups} duplicate (arm,item,seed,target) rows")

    # 6. matched design across arms (item x intended target x seed)
    try:
        cells = df.groupby("architecture").apply(
            lambda g: set(zip(g["item_id"], g["intended_model_tokens_after_target"], g["seed"])),
            include_groups=False,
        )
        ref = cells.iloc[0]
        mismatch = {a: len(ref ^ cells[a]) for a in cells.index if cells[a] != ref}
        add("matched_design", not mismatch, "all arms see identical (item,target,seed) cells"
            if not mismatch else f"unmatched: {mismatch}")
    except Exception as exc:  # noqa: BLE001
        add("matched_design", False, f"{type(exc).__name__}: {exc}")

    # 7. every intended target realised for every arm
    got_targets = sorted(int(t) for t in df["intended_model_tokens_after_target"].dropna().unique())
    add("all_targets_present", got_targets == sorted(int(t) for t in targets),
        f"got {got_targets}")

    # 8. trajectory nesting (from the dry-run verify frame if supplied)
    if verify is not None and "nested_ok" in verify.columns:
        bad = verify.loc[~verify["nested_ok"], "item_id"].unique().tolist()
        add("trajectory_nesting", not bad,
            "lower-pressure distractor block is a prefix of the higher-pressure block"
            if not bad else f"non-nested items: {bad}")

    # 9. grid realisation within tolerance (median error per (type,target) band)
    if verify is not None:
        rep = calibration_report(verify, p2["bands"])
        off = rep.loc[~rep["within_tolerance"]]
        add("grid_realised", off.empty,
            "every (fact_type, target) median model-tat within band tolerance"
            if off.empty else
            "; ".join(f"{r.fact_type}@{r.intended_model_tat}: {r.median_error:+.0f} (tol {r.tolerance})"
                      for r in off.itertuples()))

    # 10. temporal factorial balance (n_temporal = 8 -> exact direction x position x density 2x2x2)
    tcounts = _temporal_factor_counts(items)
    balanced = len(tcounts) == 8 and set(tcounts.values()) == {1}
    add("temporal_factorial_balance", balanced,
        "8 cells x 1 (direction x position x density)" if balanced else f"cells: {tcounts}")

    # 11. no target-answer leakage in any realised distractor block
    leaks = []
    for it in items:
        try:
            dataset.assert_no_collision(it)
        except ValueError as exc:  # noqa: BLE001
            leaks.append(str(exc))
    add("no_answer_leakage", not leaks, "assert_no_collision clean for all items"
        if not leaks else f"{len(leaks)} leaks: {leaks[:2]}")

    # 12. compression actually occurred (some trials past W in model-tat)
    w = int(df["sliding_window"].iloc[0])
    past = int((df["model_tokens_after_target"] >= w).sum())
    add("compression_occurred", past > 0, f"{past}/{len(df)} trials at model_tat >= W={w}")

    # 13. malformed rate not pathological (a scorer/data smell, not a science result)
    if "malformed" in df.columns:
        rate = float(df["malformed"].mean())
        add("malformed_rate_sane", rate <= 0.10, f"{rate:.1%} malformed (hard cap 10%)")

    return pd.DataFrame(checks)


def blocking(gates: pd.DataFrame) -> pd.DataFrame:
    return gates[gates["verdict"] == "FAIL"]


# ---------------------------------------------------------------------------
# Scientific warnings — never fail the run
# ---------------------------------------------------------------------------

def scientific_warnings(df: pd.DataFrame) -> pd.DataFrame:
    """Results, not plumbing errors. Printed for inspection; never block."""
    notes: list[dict[str, Any]] = []

    def note(topic: str, detail: str) -> None:
        notes.append({"topic": topic, "detail": detail})

    w = int(df["sliding_window"].iloc[0])
    deep = df[df["model_tokens_after_target"] >= 2 * w]
    for arm, g in deep.groupby("architecture"):
        acc = float(g["correct"].mean()) if len(g) else float("nan")
        if len(g) and acc < 0.05:
            note("low_deep_recurrent_accuracy", f"{arm}: {acc:.1%} strict at model_tat >= 2W (n={len(g)})")

    kn = h2_threshold.knees(df)
    if kn["k_strict_acc"].notna().sum() >= 2:
        spread = float(np.nanmax(kn["k_strict_acc"]) - np.nanmin(kn["k_strict_acc"]))
        note("per_arm_knee_spread", f"strict-accuracy K spans {spread:.0f} model tokens across arms")

    per_type = h2_threshold.knees(df, by="fact_type")
    if per_type["k_strict_acc"].notna().sum() >= 2:
        spread = float(np.nanmax(per_type["k_strict_acc"]) - np.nanmin(per_type["k_strict_acc"]))
        note("per_type_knee_spread", f"strict-accuracy K spans {spread:.0f} model tokens across fact types")

    # non-monotonic abstention (per arm, over the requested-level curve)
    if "abstained" in df.columns:
        design_key = schema.pressure_design_key(df)
        coord = schema.pressure_coordinate(df)
        for arm, g in df.groupby("architecture"):
            curve = g.groupby(design_key).agg(x=(coord, "mean"), a=("abstained", "mean")).sort_values("x")
            a = curve["a"].to_numpy()
            if len(a) >= 3 and np.any(np.diff(a) < -0.15):
                note("non_monotonic_abstention", f"{arm}: abstention rate dips >0.15 as pressure rises")

    # residual exact-memory failures (target fully in window through generation)
    if "target_fully_exact_through_generation" in df.columns:
        safe = df[df["target_fully_exact_through_generation"].fillna(False)]
        for arm, g in safe.groupby("architecture"):
            if len(g) >= 8:
                acc = float(g["correct"].mean())
                if acc < 0.9:
                    note("residual_exact_memory_failure",
                         f"{arm}: {acc:.1%} strict with target fully inside W through generation (n={len(g)})")

    return pd.DataFrame(notes) if notes else pd.DataFrame(columns=["topic", "detail"])


# ---------------------------------------------------------------------------
# Analysis outputs
# ---------------------------------------------------------------------------

def _answered_only(df: pd.DataFrame) -> pd.DataFrame:
    if "abstained" not in df.columns:
        return df
    return df[df["abstained"] == 0]


def analyse(df: pd.DataFrame, out: dict[str, Path] | None = None) -> dict[str, Any]:
    """Build the H1 / H2 / H3 / knee tables and a summary dict. Writes files when
    `out` maps {name: path-prefix}."""
    schema.validate(df, needs=("core", "h1", "h2", "h3"))
    w = int(df["sliding_window"].iloc[0])

    # H1 — strict accuracy + abstention by architecture x fact_type x pressure
    design_key = schema.pressure_design_key(df)
    coord = schema.pressure_coordinate(df)
    h1_rows = []
    for (arm, ft, lvl), g in df.groupby(["architecture", "fact_type", design_key]):
        ans = _answered_only(g)
        h1_rows.append({
            "architecture": arm, "fact_type": ft,
            "requested_tokens_after_target": int(lvl),
            "model_tokens_after_target": float(g[coord].mean()),
            "strict_accuracy": float(g["correct"].mean()),
            "abstention_rate": float(g["abstained"].mean()) if "abstained" in g else np.nan,
            "answered_only_accuracy": float(ans["correct"].mean()) if len(ans) else np.nan,
            "n": int(len(g)), "n_answered": int(len(ans)),
        })
    h1 = pd.DataFrame(h1_rows).sort_values(["architecture", "fact_type", "requested_tokens_after_target"])

    # H2 — curves on model-tat, per-arm knees, transition width, anchors
    h2_curves = h2_threshold.curves(df)
    h2_knees = h2_threshold.knees(df)
    h2_type_knees = h2_threshold.knees(df, by="fact_type")
    bands = config.pilot_pass2()["bands"]
    anchor_targets = {"early_recurrent": bands["early_recurrent"], "deep_recurrent": bands["deep_recurrent"]}
    anchor_rows = []
    if "intended_model_tokens_after_target" in df.columns:
        for band, tgts in anchor_targets.items():
            sub = df[df["intended_model_tokens_after_target"].isin(tgts)]
            for arm, g in sub.groupby("architecture"):
                k = int(g["correct"].sum())
                n = int(len(g))
                lo, hi = _wilson(k, n)
                anchor_rows.append({"band": band, "architecture": arm, "k": k, "n": n,
                                    "accuracy": k / n if n else np.nan,
                                    "wilson_low": lo, "wilson_high": hi})
    h2_anchors = pd.DataFrame(anchor_rows)

    # H3 — descriptive calibration; answered-response confidence vs abstention kept
    # strictly separate (confidence in "I don't know" is not P(factual answer wrong)).
    h3_answered = h3_calibration.by_condition(_answered_only(df)) if len(_answered_only(df)) else pd.DataFrame()
    if "abstained" in df.columns:
        rows_abst = []
        for (arm, lvl), g in df.groupby(["architecture", design_key]):
            abst = g[g["abstained"] == 1]
            ans = g[g["abstained"] == 0]
            rows_abst.append({
                "architecture": arm, "requested_tokens_after_target": int(lvl),
                "model_tokens_after_target": float(g[coord].mean()),
                "abstention_rate": float(g["abstained"].mean()),
                "mean_confidence_on_abstention": float(abst["confidence"].mean()) if len(abst) else np.nan,
                "mean_confidence_on_answered": float(ans["confidence"].mean()) if len(ans) else np.nan,
                "n": int(len(g)),
            })
        h3_abstention = pd.DataFrame(rows_abst)
    else:
        h3_abstention = pd.DataFrame()

    summary = {
        "purpose": "Pilot Pass 2 — plumbing + localization, NOT inferential evidence",
        "n_trials": int(len(df)),
        "arms": sorted(df["architecture"].unique().tolist()),
        "fact_types": sorted(df["fact_type"].unique().tolist()),
        "window_reference_W": w,
        "intended_model_tat_grid": sorted(
            int(t) for t in df.get("intended_model_tokens_after_target", pd.Series(dtype=float)).dropna().unique()
        ),
        "per_arm_strict_accuracy_K": h2_knees.set_index("architecture")["k_strict_acc"].round(1).to_dict(),
        "per_arm_abstention_K": h2_knees.set_index("architecture")["k_abstention"].round(1).to_dict(),
        "per_arm_strict_drop_width_90_10": h2_knees.set_index("architecture")["strict_drop_width_90_10"].round(1).to_dict(),
        "per_type_strict_accuracy_K": h2_type_knees.set_index("fact_type")["k_strict_acc"].round(1).to_dict(),
        "notes": "K values are exploratory per-run descriptive quantities; W is an "
                 "architectural reference, never a predicted break. No baseline-adjusted "
                 "metric (open_decisions #17 still partially resolved).",
    }

    tables = {
        "h1": h1, "h2_curves": h2_curves, "h2_knees": h2_knees,
        "h2_type_knees": h2_type_knees, "h2_anchors": h2_anchors,
        "h3_answered": h3_answered, "h3_abstention": h3_abstention,
        "warnings": scientific_warnings(df),
    }

    if out:
        for name, prefix in out.items():
            if name == "summary":
                Path(prefix).write_text(json.dumps(summary, indent=2, default=str) + "\n")
            elif name in ("h1", "h2", "h3", "knees"):
                _write_group(name, tables, Path(prefix))
    return {"summary": summary, "tables": tables}


def _write_group(name: str, tables: dict[str, pd.DataFrame], prefix: Path) -> None:
    prefix.parent.mkdir(parents=True, exist_ok=True)
    members = {
        "h1": {"": "h1"},
        "h2": {"curves": "h2_curves", "anchors": "h2_anchors"},
        "h3": {"answered": "h3_answered", "abstention": "h3_abstention"},
        "knees": {"by_arm": "h2_knees", "by_fact_type": "h2_type_knees"},
    }[name]
    for suffix, key in members.items():
        tbl = tables[key]
        if not (isinstance(tbl, pd.DataFrame) and len(tbl)):
            continue
        stem = str(prefix) if not suffix else f"{prefix}_{suffix}"
        tbl.to_csv(f"{stem}.csv", index=False)
        Path(f"{stem}.md").write_text(
            report.to_markdown(tbl.round(4), f"Pilot Pass 2 — {name} {suffix}".strip(), mode="pilot")
        )


def _wilson(k: int, n: int, z: float = 1.96) -> tuple[float, float]:
    if n == 0:
        return (float("nan"), float("nan"))
    p = k / n
    denom = 1 + z**2 / n
    centre = (p + z**2 / (2 * n)) / denom
    half = z * np.sqrt(p * (1 - p) / n + z**2 / (4 * n**2)) / denom
    return (max(0.0, centre - half), min(1.0, centre + half))
