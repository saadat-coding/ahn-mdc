"""H2 — is degradation concentrated in a narrow transition or spread gradually?

Descriptive / localization framing (see `protocol/h2_threshold.md`, revised
2026-09-04). The old "published threshold T" framing is deprecated — no T is
restored here.

  * `curves`  — strict accuracy vs the realised pressure coordinate
    (`model_tokens_after_target`), one curve per architecture, aggregated ONE
    balanced cell per scientific pressure level (`schema.pressure_group_key` —
    `intended_model_tokens_after_target` for a model-tat-targeted grid).
  * `knees`   — exploratory per-run isotonic-fit 0.5 crossings of strict accuracy
    and (separately) abstention, plus the 0.9->0.1 strict-drop width. K is a
    per-run empirical output, NOT an architectural constant, and NOT the same
    quantity as the sliding-window boundary W.
  * `drop_at_threshold` / `shape_test` — retained for callers that pass an
    explicit break (W as the design reference, or a per-run knee for sensitivity).
    `config.compression_threshold()` still raises — the 768 derivation is not a
    valid input.

`_slopes` (recurrent-only, feeds `summary`) is LEGACY: when every clearly-recurrent
level is at the accuracy floor it returns ~0. That is a finding about the pressure
grid, not an H2 result; use `knees` / `h1_degradation.transition_slope` instead.
"""

from __future__ import annotations

import numpy as np
import pandas as pd

from ahnexp import config, metrics, models, schema, stats


def curves(df: pd.DataFrame) -> pd.DataFrame:
    """Accuracy against pressure, one curve per architecture.

    Grouped on the requested design level, plotted against the realised pressure
    coordinate `model_tokens_after_target`. All levels retained (level 0 included).
    """
    schema.validate(df, needs=("core", "h2"))
    group_key = schema.pressure_group_key(df)
    coord = schema.pressure_coordinate(df)

    rows = []
    for (arm, level), group in df.groupby(["architecture", group_key]):
        low, high = stats.cluster_bootstrap_ci(group)
        window = int(group["sliding_window"].iloc[0])
        model_tat = float(group[coord].median())
        recurrent = (group["memory_condition"] == "recurrent_memory").mean()
        rows.append(
            {
                "architecture": arm,
                "pressure_group": int(level),
                "requested_tokens_after_target": int(group[schema.pressure_design_key(group)].median()),
                "tokens_after_target": int(group["tokens_after_target"].median()),
                "model_tokens_after_target": model_tat,
                "model_tokens_after_target_mean": float(group[coord].mean()),
                "sliding_window": window,
                "pressure_windows": model_tat / window if window else np.nan,
                "memory_condition": "recurrent_memory" if recurrent > 0.5 else "exact_memory",
                "accuracy": metrics.accuracy(group),
                "ci_low": low,
                "ci_high": high,
                "n": int(len(group)),
            }
        )

    return (
        pd.DataFrame(rows)
        .sort_values(["architecture", "pressure_group"])
        .reset_index(drop=True)
    )


def drop_at_threshold(df: pd.DataFrame, threshold_tokens: int | None = None) -> pd.DataFrame:
    """Test 1: accuracy either side of T, per architecture."""
    threshold_tokens = (
        config.compression_threshold() if threshold_tokens is None else int(threshold_tokens)
    )

    coord = schema.pressure_coordinate(df)
    rows = []
    for arm, group in df.groupby("architecture"):
        below = group[group[coord] < threshold_tokens]
        above = group[group[coord] >= threshold_tokens]
        if below.empty or above.empty:
            raise ValueError(
                f"The pressure grid does not bracket T = {threshold_tokens} tokens for {arm}. "
                "Add grid points on both sides before testing H2."
            )

        low, high = stats.bootstrap_statistic(
            [below, above], lambda b, a: b["correct"].mean() - a["correct"].mean()
        )
        rows.append(
            {
                "architecture": arm,
                "threshold_tokens": threshold_tokens,
                "acc_below_T": metrics.accuracy(below),
                "acc_above_T": metrics.accuracy(above),
                "drop_at_T": metrics.accuracy(below) - metrics.accuracy(above),
                "ci_low": low,
                "ci_high": high,
                "n_below": int(len(below)),
                "n_above": int(len(above)),
            }
        )

    return pd.DataFrame(rows)


def shape_test(df: pd.DataFrame, threshold_tokens: int | None = None) -> pd.DataFrame:
    """Test 2: is the collapse threshold-like or smooth?

    Compares a single log-linear fit against one allowed to change slope at T, by
    residual sum of squares with an AIC penalty for the two extra parameters. The
    break location is fixed at the published T, so nothing is fitted to the data.
    """
    threshold_tokens = (
        config.compression_threshold() if threshold_tokens is None else int(threshold_tokens)
    )

    group_key = schema.pressure_group_key(df)
    coord = schema.pressure_coordinate(df)

    rows = []
    for arm, group in df.groupby("architecture"):
        cell = group[group[group_key] > 0].groupby(group_key).agg(
            accuracy=("correct", "mean"),
            coordinate=(coord, "mean"),
            window=("sliding_window", "first"),
            n=("correct", "size"),
        ).reset_index()
        if len(cell) < 4:
            rows.append({"architecture": arm, "verdict": "too few pressure levels"})
            continue

        x = np.log2(cell["coordinate"].to_numpy(float) / cell["window"].to_numpy(float))
        y = stats.logit(cell["accuracy"].to_numpy(float))
        break_at = np.log2(threshold_tokens / cell["window"].iloc[0])

        smooth = _rss(x, y, np.polyfit(x, y, 1))
        piecewise = _piecewise_rss(x, y, break_at)

        rows.append(
            {
                "architecture": arm,
                "rss_smooth": smooth,
                "rss_piecewise": piecewise,
                "aic_smooth": _aic(smooth, len(x), 2),
                "aic_piecewise": _aic(piecewise, len(x), 4),
                "verdict": "threshold-like"
                if _aic(piecewise, len(x), 4) < _aic(smooth, len(x), 2)
                else "smooth",
            }
        )

    return pd.DataFrame(rows)


def _rss(x: np.ndarray, y: np.ndarray, coefficients) -> float:
    return float(np.sum((y - np.polyval(coefficients, x)) ** 2))


def _piecewise_rss(x: np.ndarray, y: np.ndarray, break_at: float) -> float:
    left, right = x < break_at, x >= break_at
    if left.sum() < 2 or right.sum() < 2:
        return float("inf")
    return _rss(x[left], y[left], np.polyfit(x[left], y[left], 1)) + _rss(
        x[right], y[right], np.polyfit(x[right], y[right], 1)
    )


def _aic(rss: float, n: int, k: int) -> float:
    if not np.isfinite(rss) or rss <= 0:
        return float("inf")
    return float(n * np.log(rss / n) + 2 * k)


def summary(df: pd.DataFrame) -> pd.DataFrame:
    """One row per architecture: the H2 / architecture-comparison table."""
    schema.validate(df, needs=("core", "h2"))
    stats.assert_matched_design(df)

    slope_by_arm = _slopes(df).set_index("architecture")
    try:
        drops = drop_at_threshold(df).set_index("architecture")
        shapes = shape_test(df).set_index("architecture")
        locked = True
    except ValueError:
        drops = shapes = pd.DataFrame()
        locked = False

    rows = []
    for arm, group in df.groupby("architecture"):
        exact = group[group["memory_condition"] == "exact_memory"]["correct"]
        recurrent = group[group["memory_condition"] == "recurrent_memory"]["correct"]
        acc_exact = float(exact.mean()) if len(exact) else np.nan
        acc_recurrent = float(recurrent.mean()) if len(recurrent) else np.nan

        row = {
            "architecture": arm,
            "label": models.arm(arm).label,
            "ahn_params_m": models.arm(arm).ahn_params / 1e6,
            "acc_exact": acc_exact,
            "acc_recurrent": acc_recurrent,
            "retention": acc_recurrent / acc_exact if acc_exact else np.nan,
            "slope": slope_by_arm.loc[arm, "slope"] if arm in slope_by_arm.index else np.nan,
            "n": int(len(group)),
        }
        if locked and arm in drops.index:
            row |= {
                "acc_below_T": drops.loc[arm, "acc_below_T"],
                "acc_above_T": drops.loc[arm, "acc_above_T"],
                "drop_at_T": drops.loc[arm, "drop_at_T"],
                "shape": shapes.loc[arm, "verdict"] if arm in shapes.index else None,
                "h2_status": "measured",
            }
        else:
            row |= {
                "acc_below_T": np.nan, "acc_above_T": np.nan, "drop_at_T": np.nan,
                "shape": None, "h2_status": "THRESHOLD_NOT_LOCKED",
            }
        rows.append(row)

    return pd.DataFrame(rows).sort_values("retention", ascending=False).reset_index(drop=True)


def _slopes(df: pd.DataFrame) -> pd.DataFrame:
    """LEGACY recurrent-only slope (see module docstring): ~0 when the recurrent
    region is at the accuracy floor. Kept for `summary` backward compatibility."""
    group_key = schema.pressure_group_key(df)
    coord = schema.pressure_coordinate(df)
    subset = df[(df["memory_condition"] == "recurrent_memory") & (df[group_key] > 0)]
    rows = []
    for arm, group in subset.groupby("architecture"):
        cell = group.groupby(group_key).agg(
            accuracy=("correct", "mean"),
            coordinate=(coord, "mean"),
            window=("sliding_window", "first"),
        ).reset_index()
        if len(cell) < 2:
            rows.append({"architecture": arm, "slope": np.nan})
            continue
        x = np.log2(cell["coordinate"].to_numpy(float) / cell["window"].to_numpy(float))
        rows.append({"architecture": arm, "slope": float(np.polyfit(x, stats.logit(cell["accuracy"]), 1)[0])})
    return pd.DataFrame(rows)


def knees(df: pd.DataFrame, by: str | None = None) -> pd.DataFrame:
    """Exploratory descriptive transition location (open_decisions #18 / #3).

    Per arm (and, with `by="fact_type"`, pooled per fact type across arms): the
    isotonic-fit 0.5 crossing of strict accuracy vs `model_tokens_after_target`, the
    same for abstention rate (separately — never collapsed), and the 0.9->0.1 strict
    drop width as a descriptive pilot quantity. Aggregated ONE balanced cell per
    scientific pressure level (`schema.pressure_group_key`); x is the realised
    model-tat mean within each level.

    NOT an H2 result. K is a per-run empirical output, not an architectural constant,
    and not the same quantity as W.
    """
    schema.validate(df, needs=("core", "h2"))
    group_key = schema.pressure_group_key(df)
    coord = schema.pressure_coordinate(df)
    group_cols = ["architecture"] if by is None else [by]

    rows = []
    for keys, block in df.groupby(group_cols):
        cell = block.groupby(group_key).agg(
            model_tat=(coord, "mean"),
            strict_accuracy=("correct", "mean"),
            abstention=("abstained", "mean") if "abstained" in block else ("correct", "mean"),
            n=("correct", "size"),
        ).reset_index().sort_values("model_tat")

        if len(cell) < 3:
            row = {"n_levels": int(len(cell)), "k_strict_acc": np.nan,
                   "k_abstention": np.nan, "strict_drop_width_90_10": np.nan}
        else:
            x = cell["model_tat"].to_numpy(float)
            w = cell["n"].to_numpy(float)
            acc_fit = stats.isotonic_regression(cell["strict_accuracy"], w, increasing=False)
            abst_fit = stats.isotonic_regression(cell["abstention"], w, increasing=True)
            row = {
                "n_levels": int(len(cell)),
                "k_strict_acc": stats.crossing_x(x, acc_fit, 0.5),
                "k_abstention": stats.crossing_x(x, abst_fit, 0.5),
                "strict_drop_width_90_10": stats.crossing_x(x, acc_fit, 0.1)
                - stats.crossing_x(x, acc_fit, 0.9),
                "acc_at_min_pressure": float(cell["strict_accuracy"].iloc[0]),
                "acc_at_max_pressure": float(cell["strict_accuracy"].iloc[-1]),
            }
        label = keys if isinstance(keys, str) else keys[0]
        rows.append({group_cols[0]: label, **row})

    return pd.DataFrame(rows).reset_index(drop=True)


def architecture_comparisons(df: pd.DataFrame) -> pd.DataFrame:
    """Paired arm-vs-arm gaps under recurrent memory.

    `deltanet` vs `gated_deltanet` is the cleanest pair: one mechanism apart, ~1%
    apart in parameters.
    """
    arms = sorted(set(df["architecture"]) - {"transformer"})
    pairs = [(a, b) for i, a in enumerate(arms) for b in arms[i + 1:]]
    pairs += [(a, "transformer") for a in arms if "transformer" in set(df["architecture"])]
    return pd.DataFrame([stats.paired_difference(df, a, b) for a, b in pairs])
