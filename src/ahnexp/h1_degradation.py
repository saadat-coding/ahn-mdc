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


_SPAN_MAX = 17   # max tokenised target span (compound relational), Pilot Pass 2
_GEN_MAX = 12    # max_new_tokens

def transition_band(df: pd.DataFrame) -> tuple[int, int]:
    """Pre-registered architectural transition interval in `model_tokens_after_target`.

    Geometry, NOT a fitted knee and NOT tuned to any pilot effect size:
    ``lower = round5(W - 2*(span_max + gen_max))``, ``upper = round5(W + gen_max)``.
    With W=256, span_max=17, gen_max=12 this is ``(200, 270)`` — the exact interval
    the frozen final design pins (``config.final()['transition_interval']``). The
    frozen run passes that value explicitly; this reproduces it from W.
    """
    w = int(df["sliding_window"].iloc[0])
    lo = int(round((w - 2 * (_SPAN_MAX + _GEN_MAX)) / 5) * 5)
    hi = int(round((w + _GEN_MAX) / 5) * 5)
    return (lo, hi)


def _a_transition_subset(df: pd.DataFrame, targets, arms) -> pd.DataFrame:
    """Rows for the H1 A_transition endpoint: chosen intended targets, chosen arms."""
    fcfg = config.final()
    targets = list(targets if targets is not None else fcfg["h1_transition_targets"])
    if arms is None:
        arms_cfg = config.experiment()["models"]["arms"]
        arms = [a for a in df["architecture"].unique()
                if arms_cfg.get(a, {}).get("ahn_implementation") is not None]
    key = schema.pressure_group_key(df)
    sub = df[df["architecture"].isin(list(arms)) & df[key].isin(targets)]
    if sub.empty:
        raise ValueError(f"No rows for targets {targets} / arms {list(arms)} on key {key!r}.")
    return sub


def a_transition(df: pd.DataFrame, targets=None, arms=None,
                 value: str = "strict") -> pd.DataFrame:
    """H1 primary endpoint: mean raw strict accuracy over the transition targets, per type.

    ``A_transition(type)`` = mean strict accuracy across the pre-registered intended
    model-tat targets (default ``config.final()['h1_transition_targets']`` =
    [205,220,235,250,265]), pooling the AHN arms (transformer excluded — it is a
    reference curve). ``value='answered_valid'`` substitutes answered-valid accuracy
    (temporal sensitivity B).
    """
    sub = _a_transition_subset(df, targets, arms)
    col = "correct"
    if value == "answered_valid":
        sub = metrics.answered_valid(sub)
    rows = []
    for ft, g in sub.groupby("fact_type"):
        rows.append({"fact_type": ft, "a_transition": float(g[col].mean()),
                     "n": int(len(g)), "n_items": int(g["item_id"].nunique())})
    return pd.DataFrame(rows).sort_values("a_transition").reset_index(drop=True)


def a_transition_contrasts(df: pd.DataFrame, targets=None, arms=None,
                           value: str = "strict", n_resamples: int | None = None) -> pd.DataFrame:
    """The 10 pairwise fact-type A_transition differences, hierarchical-bootstrap CI, Holm.

    H1 is supported if at least one Holm-adjusted 95% CI excludes zero.
    """
    sub = _a_transition_subset(df, targets, arms)
    if value == "answered_valid":
        sub = metrics.answered_valid(sub)
    types = sorted(sub["fact_type"].unique())

    def diff_stat(a: str, b: str):
        return lambda f: (f.loc[f["fact_type"] == a, "correct"].mean()
                          - f.loc[f["fact_type"] == b, "correct"].mean())

    rows = []
    for i, a in enumerate(types):
        for b in types[i + 1:]:
            pair = sub[sub["fact_type"].isin([a, b])]
            boot = stats.hierarchical_bootstrap(pair, diff_stat(a, b), n_resamples=n_resamples)
            # two-sided bootstrap p: 2 * min(mass below 0, mass above 0), approx via CI symmetry
            rows.append({
                "a": a, "b": b,
                "diff": boot["point"], "ci_low": boot["ci_low"], "ci_high": boot["ci_high"],
                "excludes_zero_raw": bool(boot["ci_low"] > 0 or boot["ci_high"] < 0),
                "p_approx": _boot_p(pair, diff_stat(a, b), n_resamples),
            })
    out = pd.DataFrame(rows)
    adj = stats.holm_adjust({f"{r.a}|{r.b}": r.p_approx for r in out.itertuples()})
    out["p_holm"] = [adj[f"{r.a}|{r.b}"] for r in out.itertuples()]
    out["significant_holm"] = out["p_holm"] < (1.0 - float(stats.settings()["ci"]))
    return out.sort_values("p_holm").reset_index(drop=True)


def _boot_p(frame: pd.DataFrame, statistic, n_resamples: int | None = None,
            item_col: str = "item_id", seed_col: str = "seed") -> float:
    """Two-sided hierarchical-bootstrap p for statistic == 0 (proportion of
    resamples on the far side of 0, doubled)."""
    cfg = stats.settings()
    n = int(n_resamples if n_resamples is not None else cfg["n_resamples"])
    frame = frame.reset_index(drop=True)
    items = np.unique(frame[item_col].to_numpy())
    if len(items) < 2:
        return float("nan")
    by_item = {v: [g.index.to_numpy() for _, g in s.groupby(seed_col, sort=False)]
               for v, s in frame.groupby(item_col, sort=False)}
    rng = np.random.default_rng(0)
    vals = np.empty(n)
    for b in range(n):
        picks = items[rng.integers(0, len(items), size=len(items))]
        chunks = []
        for it in picks:
            grp = by_item[it]
            for j in rng.integers(0, len(grp), size=len(grp)):
                chunks.append(grp[j])
        vals[b] = statistic(frame.loc[np.concatenate(chunks)])
    below = float(np.mean(vals <= 0))
    above = float(np.mean(vals >= 0))
    return float(min(1.0, 2.0 * min(below, above)))


def a_transition_omnibus(df: pd.DataFrame, targets=None, arms=None,
                         n_perm: int = 2000, random_state: int = 0) -> dict:
    """Companion omnibus: fact-type-label permutation test on the dispersion (SD)
    of the five A_transition means. Not the primary — the pairwise CIs are.

    Labels are permuted across items (each item carries exactly one fact type),
    preserving the per-type item count; p = P(null SD >= observed SD).
    """
    sub = _a_transition_subset(df, targets, arms)
    obs_means = sub.groupby("fact_type")["correct"].mean()
    stat_obs = float(obs_means.std(ddof=0))

    item_type = sub.drop_duplicates("item_id").set_index("item_id")["fact_type"]
    items = item_type.index.to_numpy()
    labels = item_type.to_numpy()
    corr = sub["correct"].to_numpy(float)
    pos: dict = {}
    for i, it in enumerate(sub["item_id"].to_numpy()):
        pos.setdefault(it, []).append(i)
    pos = {k: np.asarray(v) for k, v in pos.items()}

    rng = np.random.default_rng(random_state)
    null = np.empty(n_perm)
    for p in range(n_perm):
        perm = dict(zip(items, rng.permutation(labels)))
        groups: dict = {}
        for it in items:
            groups.setdefault(perm[it], []).append(corr[pos[it]])
        means = [np.concatenate(v).mean() for v in groups.values()]
        null[p] = float(np.std(means, ddof=0))
    p_value = float((np.sum(null >= stat_obs) + 1) / (n_perm + 1))
    return {"dispersion_sd": stat_obs, "p_value": p_value, "n_perm": n_perm,
            "means": {k: round(float(v), 4) for k, v in obs_means.items()}}


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
