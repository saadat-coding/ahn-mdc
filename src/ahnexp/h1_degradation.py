"""H1 — non-uniform degradation across information types.

Claim: retrieval accuracy declines at different rates for different fact types.

The degradation signal lives in the transition band (roughly the last ~80 tokens
before the window and the first ~35 after it). `slopes` — the original
recurrent-only fit — is LEGACY: once every clearly-recurrent level is at the
accuracy floor it returns ~0, which is a finding about the pressure grid, not a
per-type rate. Use `transition_slope` / `transition_drop`, which operate over an
EXPLICIT `model_tokens_after_target` band (default derived from W; the inferential
run must pre-register its band or grid independently of any pilot).

Everything aggregates ONE balanced cell per scientific pressure level
(`schema.pressure_group_key`), plotted / fitted against the realised coordinate
`model_tokens_after_target`.
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
    group_key = schema.pressure_group_key(df)
    coord = schema.pressure_coordinate(df)

    rows = []
    for (group_value, level), group in df.groupby([by, group_key]):
        low, high = stats.cluster_bootstrap_ci(group)
        window = int(group["sliding_window"].iloc[0])
        model_tat = float(group[coord].median())
        rows.append(
            {
                by: group_value,
                "pressure_group": int(level),
                "requested_tokens_after_target": int(group[schema.pressure_design_key(group)].median()),
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
        .sort_values([by, "pressure_group"])
        .reset_index(drop=True)
    )


def transition_band(df: pd.DataFrame) -> tuple[int, int]:
    """Default `model_tokens_after_target` window for degradation-rate analysis.

    Derived from W as `[W - 76, W + 34]` (≈ the last ~80 tokens before the window
    and the first ~35 after it), NOT a hypothesis constant. Callers doing an
    inferential analysis should pass an explicit band pre-registered from theory or
    the near-window diagnostic rather than rely on this pilot-analysis convenience.
    """
    w = int(df["sliding_window"].iloc[0])
    return (w - 76, w + 34)


def transition_slope(df: pd.DataFrame, by: str = "fact_type",
                     band: tuple[int, int] | None = None) -> pd.DataFrame:
    """Per-category degradation rate over an explicit `model_tokens_after_target` band.

    Slope of logit(accuracy) against `model_tokens_after_target`, aggregated one
    balanced cell per scientific pressure level whose realised model-tat mean lies
    in `band` (default `transition_band(df)`). Descriptive; the clustered CI is NaN
    with a single seed.
    """
    lo, hi = band or transition_band(df)
    group_key = schema.pressure_group_key(df)
    coord = schema.pressure_coordinate(df)

    def _fit(g: pd.DataFrame) -> float:
        cell = g.groupby(group_key).agg(accuracy=("correct", "mean"),
                                        x=(coord, "mean")).reset_index()
        cell = cell[cell["x"].between(lo, hi)]
        if len(cell) < 2:
            return float("nan")
        return float(np.polyfit(cell["x"].to_numpy(float),
                                stats.logit(cell["accuracy"].to_numpy(float)), 1)[0])

    rows = []
    for value, g in df.groupby(by):
        low, high = stats.bootstrap_statistic([g], lambda x: _fit(x))
        cell = g.groupby(group_key).agg(x=(coord, "mean")).reset_index()
        rows.append({
            by: value, "band_lo": lo, "band_hi": hi,
            "transition_slope": _fit(g), "ci_low": low, "ci_high": high,
            "n_levels_in_band": int(cell["x"].between(lo, hi).sum()),
            "n": int(len(g)),
        })
    return pd.DataFrame(rows).sort_values("transition_slope").reset_index(drop=True)


def transition_drop(df: pd.DataFrame, by: str = "fact_type",
                    band: tuple[int, int] | None = None) -> pd.DataFrame:
    """Accuracy at the low end of `band` minus accuracy at the high end.

    A slope-free descriptive fallback: always defined as long as the band contains
    at least one scientific pressure level on each side of its midpoint.
    """
    lo, hi = band or transition_band(df)
    group_key = schema.pressure_group_key(df)
    coord = schema.pressure_coordinate(df)
    mid = (lo + hi) / 2

    rows = []
    for value, g in df.groupby(by):
        cell = g.groupby(group_key).agg(accuracy=("correct", "mean"),
                                        x=(coord, "mean"), n=("correct", "size")).reset_index()
        inband = cell[cell["x"].between(lo, hi)]
        left = inband[inband["x"] <= mid]
        right = inband[inband["x"] > mid]
        acc_lo = float((left["accuracy"] * left["n"]).sum() / left["n"].sum()) if len(left) else np.nan
        acc_hi = float((right["accuracy"] * right["n"]).sum() / right["n"].sum()) if len(right) else np.nan
        rows.append({
            by: value, "band_lo": lo, "band_hi": hi,
            "acc_low_end": acc_lo, "acc_high_end": acc_hi,
            "transition_drop": acc_lo - acc_hi,
            "n_levels_in_band": int(len(inband)),
        })
    return pd.DataFrame(rows).sort_values("transition_drop", ascending=False).reset_index(drop=True)


def _dominant_condition(group: pd.DataFrame) -> str:
    """Majority `memory_condition` in a requested-level group (ties -> exact).

    A single requested level can straddle the boundary once per-item length jitter
    is accounted for; the curve row reports the majority label for description only.
    """
    recurrent = (group["memory_condition"] == "recurrent_memory").mean()
    return "recurrent_memory" if recurrent > 0.5 else "exact_memory"


def slopes(df: pd.DataFrame, by: str = "fact_type", recurrent_only: bool = True) -> pd.DataFrame:
    """LEGACY degradation rate per category (recurrent-only by default).

    Slope of logit(accuracy) against log2(pressure / window). Returns ~0 when every
    clearly-recurrent level is at the accuracy floor (Pilot Pass 2) — a finding
    about the grid, not a per-type rate. Prefer `transition_slope` / `transition_drop`.
    """
    group_key = schema.pressure_group_key(df)
    subset = df[df["memory_condition"] == "recurrent_memory"] if recurrent_only else df
    subset = subset[subset[group_key] > 0]

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
                "n_levels": int(group[group_key].nunique()),
                "n": int(len(group)),
            }
        )

    return pd.DataFrame(rows).sort_values("slope").reset_index(drop=True)


def _slope(group: pd.DataFrame) -> float:
    group_key = schema.pressure_group_key(group)
    coord = schema.pressure_coordinate(group)
    cell = group.groupby(group_key).agg(
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
