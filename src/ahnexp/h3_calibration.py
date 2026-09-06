"""H3 — miscalibration under compression.

Claim: confidence does not fully track declining accuracy. It falls more slowly,
widening the confidence–accuracy gap, and in the strongest case produces confidently
incorrect answers on facts the compressed memory has lost.

Three mutually exclusive analysis populations (`population=`):

  * ``answered_valid`` (default) — ``abstained == 0 and malformed == 0``. The only
    population where confidence is confidence in a *factual answer*. Factual
    ECE / Brier / CWR are computed here and nowhere else by default.
  * ``abstained`` — confidence here is confidence in emitting the "I don't know"
    string, NOT P(the factual answer is right). Reported separately by
    ``abstention_confidence``.
  * ``malformed`` — degenerate generations. Reported separately by ``malformed_report``.
  * ``all`` — every row; only for explicit diagnostics, never the calibration headline.

The headline evidence is the gap growing with pressure, not the overall ECE. A model
can have a small aggregate ECE and still be badly overconfident exactly where memory
has failed, because the well-calibrated in-window trials dominate the average.
"""

from __future__ import annotations

import numpy as np
import pandas as pd

from ahnexp import config, metrics, schema, stats

_POPULATIONS = ("answered_valid", "abstained", "malformed", "all")


def population_mask(df: pd.DataFrame, population: str) -> pd.Series:
    """Boolean mask for one of the three mutually exclusive analysis populations."""
    if population not in _POPULATIONS:
        raise ValueError(f"population must be one of {_POPULATIONS}; got {population!r}")
    has_abst = "abstained" in df.columns
    has_malf = "malformed" in df.columns
    if population == "all":
        return pd.Series(True, index=df.index)
    if population == "abstained":
        return df["abstained"] == 1 if has_abst else pd.Series(False, index=df.index)
    if population == "malformed":
        return df["malformed"] == 1 if has_malf else pd.Series(False, index=df.index)
    # answered_valid
    mask = pd.Series(True, index=df.index)
    if has_abst:
        mask &= df["abstained"] == 0
    if has_malf:
        mask &= df["malformed"] == 0
    return mask


def _pop(df: pd.DataFrame, population: str) -> pd.DataFrame:
    return df[population_mask(df, population)]


def by_pressure(df: pd.DataFrame, population: str = "answered_valid") -> pd.DataFrame:
    """Accuracy, confidence and the gap at each compression level.

    Factual calibration over `population` (default `answered_valid`). If the `gap`
    column grows from left to right, confidence is failing to track memory.
    """
    schema.validate(df, needs=("core", "h3"))
    group_key = schema.pressure_group_key(df)
    coord = schema.pressure_coordinate(df)
    src = df
    df = _pop(df, population)

    rows = []
    for level, group in df.groupby(group_key):
        window = int(group["sliding_window"].iloc[0])
        model_tat = float(group[coord].median())
        recurrent = (group["memory_condition"] == "recurrent_memory").mean()
        ece, _ = metrics.expected_calibration_error(group["confidence"], group["correct"])
        low, high = stats.bootstrap_statistic(
            [group], lambda g: g["confidence"].mean() - g["correct"].mean()
        )
        full = src[src[group_key] == level]
        rows.append(
            {
                "pressure_group": int(level),
                "tokens_after_target": int(group["tokens_after_target"].median()),
                "model_tokens_after_target": model_tat,
                "pressure_windows": model_tat / window if window else np.nan,
                "memory_condition": "recurrent_memory" if recurrent > 0.5 else "exact_memory",
                "population": population,
                "n_population": int(len(group)),
                "n_total": int(len(full)),
                "accuracy": metrics.accuracy(group),
                "confidence": float(group["confidence"].mean()),
                "gap": metrics.confidence_accuracy_gap(group),
                "gap_ci_low": low,
                "gap_ci_high": high,
                "ece": ece,
                "brier": metrics.brier_score(group["confidence"], group["correct"]),
                "cwr": metrics.confidently_wrong_rate(group),
            }
        )

    return pd.DataFrame(rows).sort_values("pressure_group").reset_index(drop=True)


def reliability(df: pd.DataFrame, condition: str | None = None,
                population: str = "answered_valid") -> pd.DataFrame:
    """Per-bin table behind the reliability diagram (Guo et al. 2017)."""
    subset = _pop(df, population)
    if condition:
        subset = subset[subset["memory_condition"] == condition]
    _, table = metrics.expected_calibration_error(subset["confidence"], subset["correct"])
    return table


def by_condition(df: pd.DataFrame, population: str = "answered_valid") -> pd.DataFrame:
    """Exact versus recurrent memory — the cleanest statement of H3.

    Factual calibration over `population` (default `answered_valid`). Abstention and
    malformed rates over the FULL frame are reported alongside for context.
    """
    src = df
    df = _pop(df, population)
    rows = []
    for condition, group in df.groupby("memory_condition"):
        ece, _ = metrics.expected_calibration_error(group["confidence"], group["correct"])
        full = src[src["memory_condition"] == condition]
        rows.append(
            {
                "memory_condition": condition,
                "population": population,
                "n_population": int(len(group)),
                "n_total": int(len(full)),
                "accuracy": metrics.accuracy(group),
                "confidence": float(group["confidence"].mean()),
                "gap": metrics.confidence_accuracy_gap(group),
                "ece": ece,
                "brier": metrics.brier_score(group["confidence"], group["correct"]),
                "cwr": metrics.confidently_wrong_rate(group),
                "abstention_rate": metrics.abstention_rate(full),
                "malformed_rate": metrics.malformed_rate(full),
            }
        )
    return pd.DataFrame(rows).sort_values("memory_condition").reset_index(drop=True)


def by_fact_type(df: pd.DataFrame, recurrent_only: bool = True,
                 population: str = "answered_valid") -> pd.DataFrame:
    """Where H1 and H3 meet: is the most-degraded fact type also the least calibrated?"""
    subset = _pop(df, population)
    if recurrent_only:
        subset = subset[subset["memory_condition"] == "recurrent_memory"]

    rows = []
    for fact_type, group in subset.groupby("fact_type"):
        ece, _ = metrics.expected_calibration_error(group["confidence"], group["correct"])
        rows.append(
            {
                "fact_type": fact_type,
                "population": population,
                "n": int(len(group)),
                "accuracy": metrics.accuracy(group),
                "confidence": float(group["confidence"].mean()),
                "gap": metrics.confidence_accuracy_gap(group),
                "ece": ece,
                "brier": metrics.brier_score(group["confidence"], group["correct"]),
                "cwr": metrics.confidently_wrong_rate(group),
            }
        )
    return pd.DataFrame(rows).sort_values("gap", ascending=False).reset_index(drop=True)


def abstention_confidence(df: pd.DataFrame) -> pd.DataFrame:
    """Confidence in emitting "I don't know", per pressure level — NOT factual confidence.

    Kept strictly apart from the factual calibration tables.
    """
    if "abstained" not in df.columns:
        return pd.DataFrame(columns=["pressure_group", "abstention_rate", "n_abstained"])
    group_key = schema.pressure_group_key(df)
    coord = schema.pressure_coordinate(df)
    rows = []
    for level, g in df.groupby(group_key):
        abst = g[g["abstained"] == 1]
        rows.append({
            "pressure_group": int(level),
            "model_tokens_after_target": float(g[coord].median()),
            "abstention_rate": float(g["abstained"].mean()),
            "n_abstained": int(len(abst)),
            "mean_confidence_on_abstention": float(abst["confidence"].mean()) if len(abst) else np.nan,
            "median_confidence_on_abstention": float(abst["confidence"].median()) if len(abst) else np.nan,
        })
    return pd.DataFrame(rows).sort_values("pressure_group").reset_index(drop=True)


def malformed_report(df: pd.DataFrame) -> pd.DataFrame:
    """Malformed rate and its (low) confidence, per pressure level — reported apart."""
    if "malformed" not in df.columns:
        return pd.DataFrame(columns=["pressure_group", "malformed_rate", "n_malformed"])
    group_key = schema.pressure_group_key(df)
    coord = schema.pressure_coordinate(df)
    rows = []
    for level, g in df.groupby(group_key):
        malf = g[g["malformed"] == 1]
        rows.append({
            "pressure_group": int(level),
            "model_tokens_after_target": float(g[coord].median()),
            "malformed_rate": float(g["malformed"].mean()),
            "n_malformed": int(len(malf)),
            "mean_confidence_on_malformed": float(malf["confidence"].mean()) if len(malf) else np.nan,
        })
    return pd.DataFrame(rows).sort_values("pressure_group").reset_index(drop=True)


def behavioral_signaling(df: pd.DataFrame, margin: int | None = None,
                         n_resamples: int | None = None) -> dict:
    """H3 behavioral primary (protocol/final_experiment_design.md).

    "Does behavioral uncertainty signaling track retrieval failure as memory
    pressure increases?" Over rows with ``model_tokens_after_target >= W + margin``
    (default ``config.final()['h3_signal_margin']`` = 16):

      * ``appropriate_abstention_rate`` = P(abstained)
      * ``unsignalled_failure_rate``    = P(wrong-valid OR malformed)
        (wrong-valid = answered, not malformed, ``correct == 0``)

    Per architecture, plus each AHN arm vs transformer (hierarchical bootstrap,
    Holm within this family). No "the model knows its memory is gone" phrasing —
    this is uncertainty / failure *signaling*.
    """
    schema.validate(df, needs=("core", "h3"))
    fcfg = config.final()
    margin = int(fcfg["h3_signal_margin"] if margin is None else margin)
    w = int(df["sliding_window"].iloc[0])
    coord = schema.pressure_coordinate(df)
    region = df[df[coord] >= w + margin].copy()
    if region.empty:
        return {"region": f"model_tat >= {w + margin}", "n": 0,
                "per_arm": pd.DataFrame(), "contrasts": pd.DataFrame()}

    has_malf = "malformed" in region.columns
    region["_unsignalled"] = (
        ((region["abstained"] == 0) & (region["correct"] == 0)
         & (~region["malformed"].astype(bool) if has_malf else True))
        | (region["malformed"].astype(bool) if has_malf else False)
    ).astype(int)

    per_arm = []
    for arm, g in region.groupby("architecture"):
        per_arm.append({
            "architecture": arm, "n": int(len(g)),
            "appropriate_abstention_rate": float(g["abstained"].mean()),
            "unsignalled_failure_rate": float(g["_unsignalled"].mean()),
        })
    per_arm_df = pd.DataFrame(per_arm)

    contrasts = []
    p_map: dict[str, float] = {}
    ahn = [a for a in region["architecture"].unique() if a != "transformer"]
    if "transformer" in set(region["architecture"]):
        for arm in sorted(ahn):
            pair = region[region["architecture"].isin([arm, "transformer"])]
            for metric_col in ("abstained", "_unsignalled"):
                stat = (lambda mc: lambda f: (f.loc[f["architecture"] == arm, mc].mean()
                                              - f.loc[f["architecture"] == "transformer", mc].mean()))(metric_col)
                boot = stats.hierarchical_bootstrap(pair, stat, n_resamples=n_resamples)
                p = _two_sided_boot_p(pair, stat, n_resamples)
                name = f"{arm}-transformer:{'abstention' if metric_col == 'abstained' else 'unsignalled'}"
                p_map[name] = p
                contrasts.append({"contrast": name, "diff": boot["point"],
                                  "ci_low": boot["ci_low"], "ci_high": boot["ci_high"], "p_approx": p})
    adj = stats.holm_adjust(p_map) if p_map else {}
    for row in contrasts:
        row["p_holm"] = adj.get(row["contrast"], float("nan"))

    return {"region": f"model_tat >= {w + margin}", "n": int(len(region)),
            "per_arm": per_arm_df, "contrasts": pd.DataFrame(contrasts)}


def _two_sided_boot_p(frame: pd.DataFrame, statistic, n_resamples: int | None = None) -> float:
    from ahnexp.h1_degradation import _boot_p

    return _boot_p(frame, statistic, n_resamples)


def gap_change(df: pd.DataFrame, interval: tuple[int, int] | None = None,
               control_anchors=None, n_resamples: int | None = None) -> pd.DataFrame:
    """Secondary calibration primary test: change in the confidence-minus-accuracy
    gap (answered_valid only) from the pooled control anchors to the transition
    interval, per architecture, with a hierarchical-bootstrap CI.
    """
    fcfg = config.final()
    interval = tuple(interval or fcfg["transition_interval"])
    control_anchors = list(control_anchors or fcfg["control_anchors"])
    key = schema.pressure_group_key(df)
    av = _pop(df, "answered_valid").copy()
    av["_region"] = np.where(av[key].isin(control_anchors), "control",
                             np.where(av[key].between(*interval), "interval", "other"))
    scoped = av[av["_region"].isin(["control", "interval"])]

    def gap_delta(f: pd.DataFrame) -> float:
        ctrl = f[f["_region"] == "control"]
        intr = f[f["_region"] == "interval"]
        if not len(ctrl) or not len(intr):
            return float("nan")
        g_ctrl = float(ctrl["confidence"].mean() - ctrl["correct"].mean())
        g_intr = float(intr["confidence"].mean() - intr["correct"].mean())
        return g_intr - g_ctrl

    rows = []
    for arm, g in scoped.groupby("architecture"):
        boot = stats.hierarchical_bootstrap(g, gap_delta, n_resamples=n_resamples)
        ctrl, intr = g[g["_region"] == "control"], g[g["_region"] == "interval"]
        rows.append({
            "architecture": arm,
            "gap_control": float(ctrl["confidence"].mean() - ctrl["correct"].mean()) if len(ctrl) else np.nan,
            "gap_interval": float(intr["confidence"].mean() - intr["correct"].mean()) if len(intr) else np.nan,
            "gap_change": boot["point"], "ci_low": boot["ci_low"], "ci_high": boot["ci_high"],
        })
    return pd.DataFrame(rows).sort_values("gap_change", ascending=False).reset_index(drop=True)


def confidence_health(df: pd.DataFrame) -> pd.DataFrame:
    """Sanity checks on the confidence signal itself, before interpreting calibration.

    Sequence probability shrinks with answer length, so it can span orders of
    magnitude and pile every trial into the lowest bin. That produces a large ECE
    that says more about tokenisation than about the model's self-knowledge.
    See `protocol/open_decisions.md` #6.
    """
    confidence = df["confidence"]
    n_bins = int(config.experiment()["calibration"]["ece_bins"])
    occupied = pd.cut(confidence, np.linspace(0, 1, n_bins + 1), include_lowest=True).nunique()
    lowest = float((confidence <= 1.0 / n_bins).mean())

    return pd.DataFrame(
        [
            {"check": "mode", "value": config.experiment()["calibration"]["confidence"]},
            {"check": "min", "value": float(confidence.min())},
            {"check": "max", "value": float(confidence.max())},
            {"check": "median", "value": float(confidence.median())},
            {"check": "bins occupied", "value": f"{occupied}/{n_bins}"},
            {
                "check": "fraction in lowest bin",
                "value": f"{lowest:.1%}"
                + ("  <-- signal is degenerate, ECE is not interpretable" if lowest > 0.5 else ""),
            },
        ]
    )
