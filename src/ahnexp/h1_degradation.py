"""H1 — non-uniform degradation across information types.

Claim: retrieval accuracy declines at different rates for different fact types.
Test: per-type degradation slopes, and whether their intervals separate.
"""

from __future__ import annotations

import numpy as np
import pandas as pd

from ahnexp import config, metrics, schema, stats


def curves(df: pd.DataFrame, by: str = "fact_type") -> pd.DataFrame:
    """Accuracy against compression pressure, one curve per category.

    Grouped on the requested design level (`requested_tokens_after_target`), plotted
    against the realised pressure coordinate (`model_tokens_after_target`): the
    tokens the model actually saw after the target span, including the fixed
    question/instruction/template block. Every level is retained, level 0 included.
    """
    schema.validate(df, needs=("core", "h1"))
    design_key = schema.pressure_design_key(df)
    coord = schema.pressure_coordinate(df)

    rows = []
    for (group_value, level), group in df.groupby([by, design_key]):
        low, high = stats.cluster_bootstrap_ci(group)
        window = int(group["sliding_window"].iloc[0])
        model_tat = float(group[coord].median())
        rows.append(
            {
                by: group_value,
                "requested_tokens_after_target": int(level),
                "tokens_after_target": int(group["tokens_after_target"].median()),
                "model_tokens_after_target": model_tat,
                "model_tokens_after_target_mean": float(group[coord].mean()),
                "sliding_window": window,
                "pressure_windows": model_tat / window if window else np.nan,
                "memory_condition": _dominant_condition(group),
                "accuracy": metrics.accuracy(group),
                "chance_corrected": metrics.chance_corrected_accuracy(group)
                if by == "fact_type" else np.nan,
                "ci_low": low,
                "ci_high": high,
                "n": int(len(group)),
            }
        )

    return (
        pd.DataFrame(rows)
        .sort_values([by, "requested_tokens_after_target"])
        .reset_index(drop=True)
    )


def _dominant_condition(group: pd.DataFrame) -> str:
    """Majority `memory_condition` in a requested-level group (ties -> exact).

    A single requested level can straddle the boundary once per-item length jitter
    is accounted for; the curve row reports the majority label for description only.
    """
    recurrent = (group["memory_condition"] == "recurrent_memory").mean()
    return "recurrent_memory" if recurrent > 0.5 else "exact_memory"


def slopes(df: pd.DataFrame, by: str = "fact_type", recurrent_only: bool = True) -> pd.DataFrame:
    """Degradation rate per category, with a clustered CI.

    Slope of logit(accuracy) against log2(pressure / window). Normalising the x-axis
    by the window makes the rate comparable across checkpoints; the logit keeps a
    drop from 0.9 to 0.8 from looking like a drop from 0.5 to 0.4.
    """
    design_key = schema.pressure_design_key(df)
    subset = df[df["memory_condition"] == "recurrent_memory"] if recurrent_only else df
    subset = subset[subset[design_key] > 0]

    rows = []
    for group_value, group in subset.groupby(by):
        point = _slope(group)
        low, high = stats.bootstrap_statistic([group], lambda g: _slope(g))
        rows.append(
            {
                by: group_value,
                "slope": point,
                "ci_low": low,
                "ci_high": high,
                "n_levels": int(group[design_key].nunique()),
                "n": int(len(group)),
            }
        )

    return pd.DataFrame(rows).sort_values("slope").reset_index(drop=True)


def _slope(group: pd.DataFrame) -> float:
    design_key = schema.pressure_design_key(group)
    coord = schema.pressure_coordinate(group)
    cell = group.groupby(design_key).agg(
        accuracy=("correct", "mean"),
        coordinate=(coord, "mean"),
        window=("sliding_window", "first"),
    ).reset_index()
    if len(cell) < 2:
        return float("nan")
    x = np.log2(cell["coordinate"].to_numpy(float) / cell["window"].to_numpy(float))
    y = stats.logit(cell["accuracy"].to_numpy(float))
    return float(np.polyfit(x, y, 1)[0])


def separation(slopes_table: pd.DataFrame, by: str = "fact_type") -> pd.DataFrame:
    """Which category pairs have non-overlapping slope intervals.

    A coarse screen, not a test: non-overlapping intervals imply a difference, but
    overlapping ones do not imply equality. Enough to see whether H1 has any signal
    before spending A40 time on it.
    """
    table = slopes_table.dropna(subset=["ci_low", "ci_high"])
    rows = []
    for i, a in table.iterrows():
        for _, b in table.loc[i + 1:].iterrows():
            disjoint = a["ci_high"] < b["ci_low"] or b["ci_high"] < a["ci_low"]
            rows.append(
                {
                    "a": a[by],
                    "b": b[by],
                    "slope_a": a["slope"],
                    "slope_b": b["slope"],
                    "intervals_disjoint": disjoint,
                }
            )
    return pd.DataFrame(rows)


def summary(df: pd.DataFrame) -> pd.DataFrame:
    """One row per fact type: the H1 table."""
    caveats = {name: entry.get("caveat") for name, entry in config.facts()["types"].items()}

    rows = []
    for fact_type, group in df.groupby("fact_type"):
        exact = group[group["memory_condition"] == "exact_memory"]
        recurrent = group[group["memory_condition"] == "recurrent_memory"]
        acc_exact = metrics.accuracy(exact) if len(exact) else np.nan
        acc_recurrent = metrics.accuracy(recurrent) if len(recurrent) else np.nan
        rows.append(
            {
                "fact_type": fact_type,
                "chance": config.facts()["chance"][fact_type],
                "acc_exact": acc_exact,
                "acc_recurrent": acc_recurrent,
                "retention": acc_recurrent / acc_exact if acc_exact else np.nan,
                "chance_corrected_recurrent": metrics.chance_corrected_accuracy(recurrent)
                if len(recurrent) else np.nan,
                "retrieval_failure_rate": metrics.retrieval_failure_rate(recurrent)
                if len(recurrent) else np.nan,
                "n": int(len(group)),
                "caveat": caveats.get(fact_type),
            }
        )

    return pd.DataFrame(rows).sort_values("retention").reset_index(drop=True)
