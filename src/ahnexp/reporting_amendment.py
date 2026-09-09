"""Post-freeze reporting amendments — analysis version 1.1.

APPROVED 2026-09-09 (protocol/amendment_h2_transition_width.md,
protocol/final_reporting_additions.md). Runs ONLY on the locked, immutable
92,160-row artifact. Does NOT import, call, or mutate any frozen v1.0 output;
`full_run.analyse` (v1.0) is untouched and stays reproducible.

Nothing here changes W, K, strict accuracy, the pressure coordinate, the grid,
seeds, the scorer, the prompt, the dataset, the gates, or the raw data. The H2
transition-width **amendment** is a *reporting* replacement for a frozen
descriptive statistic that is mathematically undefined for this dataset — it is
NOT a new frozen primary endpoint. The frozen shape test is preserved separately.

Contents
--------
H2 amendment (Option A):
  * `h2_width_eligibility`   — per (architecture, fact_type): the 90->10 estimator's
                               defined/undefined status, from its mathematical
                               requirements (predefined, not observed convenience)
  * `h2_width_by_facttype`   — per eligible (architecture, fact_type): isotonic
                               90->10 strict-accuracy width + hierarchical
                               (item -> seed) bootstrap CI + resample-stability
  * `h2_width_summary`       — per architecture: MEDIAN width across that arm's
                               globally-eligible fact types + bootstrap CI
  * `h2_width_seed_sensitivity` — per (seed, architecture) median eligible width

H1 sensitivity:
  * `h1_exclude_compound_relational` — [POST-FREEZE SENSITIVITY]

Descriptive robustness / disclosure tables:
  * `residual_fully_exact_failures`, `transformer_malformed`,
    `deep_recurrent_retention`, `temporal_counterbalancing`,
    `compound_relational_control_warning`, `per_seed_headline_robustness`,
    `reproduce_plumbing_gates`
"""

from __future__ import annotations

import re
from typing import Any

import numpy as np
import pandas as pd

from ahnexp import (
    config,
    dataset,
    full_run,
    h1_degradation,
    h2_threshold,
    metrics,
    schema,
    stats,
)

ANALYSIS_VERSION = "1.1"

# The 90->10 transition-width estimator's reference levels. FIXED — the amendment
# does not lower the band (that would be Option B); it restricts to fact types
# where these levels are attained.
WIDTH_LO_LEVEL = 0.90   # upper reference (fit must reach >= this)
WIDTH_HI_LEVEL = 0.10   # lower reference (fit must reach <= this)

_PERSON = re.compile(r"(?i)person[ _]?(\d+)")


# --------------------------------------------------------------------------- #
# shared: one isotonic strict-accuracy fit per (architecture, fact_type)
# --------------------------------------------------------------------------- #

def _facttype_curve(g: pd.DataFrame) -> pd.DataFrame:
    """One balanced cell per frozen pressure level (schema.pressure_group_key);
    x = realised model_tokens_after_target mean; strict accuracy; n."""
    key = schema.pressure_group_key(g)
    coord = schema.pressure_coordinate(g)
    return (g.groupby(key)
             .agg(x=(coord, "mean"), acc=("correct", "mean"), n=("correct", "size"))
             .reset_index()
             .sort_values("x"))


def _iso_fit(cell: pd.DataFrame) -> np.ndarray:
    return stats.isotonic_regression(cell["acc"].to_numpy(float),
                                     cell["n"].to_numpy(float), increasing=False)


def _width_9010(g: pd.DataFrame) -> float:
    """Isotonic 90->10 strict-accuracy drop width in model tokens for one
    (architecture, fact_type) frame. NaN if the fitted curve does not span
    [WIDTH_HI_LEVEL, WIDTH_LO_LEVEL] (the estimator is then undefined)."""
    cell = _facttype_curve(g)
    if len(cell) < 3:
        return float("nan")
    fit = _iso_fit(cell)
    x = cell["x"].to_numpy(float)
    return stats.crossing_x(x, fit, WIDTH_HI_LEVEL) - stats.crossing_x(x, fit, WIDTH_LO_LEVEL)


# --------------------------------------------------------------------------- #
# a hierarchical (item -> seed) bootstrap that tolerates NaN resamples
# (identical resampling scheme to stats.hierarchical_bootstrap; NaN-safe CI)
# --------------------------------------------------------------------------- #

def _hier_bootstrap_nan(df: pd.DataFrame, statistic, *, item_col: str = "item_id",
                        seed_col: str = "seed", n_resamples: int | None = None,
                        ci: float | None = None, random_state: int = 0) -> dict:
    cfg = stats.settings()
    n_resamples = int(n_resamples if n_resamples is not None else cfg["n_resamples"])
    ci = float(ci if ci is not None else cfg["ci"])
    df = df.reset_index(drop=True)
    point = float(statistic(df))

    items = np.unique(df[item_col].to_numpy())
    if len(items) < 2:
        return {"point": point, "ci_low": float("nan"), "ci_high": float("nan"),
                "n_items": int(len(items)), "n_resamples": 0, "frac_finite": float("nan")}

    by_item = {v: [x.index.to_numpy() for _, x in s.groupby(seed_col, sort=False)]
               for v, s in df.groupby(item_col, sort=False)}
    rng = np.random.default_rng(random_state)
    vals = np.empty(n_resamples)
    for b in range(n_resamples):
        picks = items[rng.integers(0, len(items), size=len(items))]
        chunks = []
        for it in picks:
            grp = by_item[it]
            for j in rng.integers(0, len(grp), size=len(grp)):
                chunks.append(grp[j])
        vals[b] = statistic(df.loc[np.concatenate(chunks)])

    finite = np.isfinite(vals)
    frac = float(finite.mean())
    alpha = (1.0 - ci) / 2.0
    if finite.sum() < 2:
        lo = hi = float("nan")
    else:
        lo = float(np.nanquantile(vals[finite], alpha))
        hi = float(np.nanquantile(vals[finite], 1.0 - alpha))
    return {"point": point, "ci_low": lo, "ci_high": hi, "n_items": int(len(items)),
            "n_resamples": n_resamples, "frac_finite": frac}


# --------------------------------------------------------------------------- #
# H2 AMENDMENT — Option A
# --------------------------------------------------------------------------- #

def h2_width_eligibility(df: pd.DataFrame) -> pd.DataFrame:
    """Per (architecture, fact_type): whether the isotonic 90->10 width estimator
    is *mathematically defined*.

    RULE (predefined from the estimator, not from observed convenience): the
    90->10 width is the token distance between the fitted curve's first crossing
    of {WIDTH_LO_LEVEL}=0.90 and its first crossing of {WIDTH_HI_LEVEL}=0.10. It
    exists iff the fitted (non-increasing isotonic) strict-accuracy curve attains
    a value >= 0.90 somewhere (so a 0.90 crossing exists) AND a value <= 0.10
    somewhere (so a 0.10 crossing exists). Eligibility is checked on the fit, not
    on raw cell means.
    """
    rows = []
    for (arm, ft), g in df.groupby(["architecture", "fact_type"]):
        cell = _facttype_curve(g)
        if len(cell) < 3:
            rows.append(dict(architecture=arm, fact_type=ft, n_levels=len(cell),
                             fit_max=np.nan, fit_min=np.nan, reaches_lo=False,
                             reaches_hi=False, eligible=False,
                             x_at_0_90=np.nan, x_at_0_50=np.nan, x_at_0_10=np.nan,
                             width_point=np.nan,
                             reason="fewer than 3 pressure levels"))
            continue
        fit = _iso_fit(cell)
        x = cell["x"].to_numpy(float)
        fmax, fmin = float(fit.max()), float(fit.min())
        reaches_lo = fmax >= WIDTH_LO_LEVEL
        reaches_hi = fmin <= WIDTH_HI_LEVEL
        eligible = reaches_lo and reaches_hi
        reason = ("eligible" if eligible else
                  "; ".join(([f"fitted ceiling {fmax:.3f} < 0.90"] if not reaches_lo else [])
                            + ([f"fitted floor {fmin:.3f} > 0.10"] if not reaches_hi else [])))
        rows.append(dict(
            architecture=arm, fact_type=ft, n_levels=len(cell),
            fit_max=round(fmax, 4), fit_min=round(fmin, 4),
            reaches_lo=reaches_lo, reaches_hi=reaches_hi, eligible=eligible,
            x_at_0_90=round(stats.crossing_x(x, fit, 0.90), 2),
            x_at_0_50=round(stats.crossing_x(x, fit, 0.50), 2),
            x_at_0_10=round(stats.crossing_x(x, fit, 0.10), 2),
            width_point=round(_width_9010(g), 2),
            reason=reason))
    return pd.DataFrame(rows).sort_values(["fact_type", "architecture"]).reset_index(drop=True)


def globally_eligible_fact_types(df: pd.DataFrame) -> list[str]:
    """Fact types eligible for the 90->10 width estimator for ALL architectures
    (so the cross-architecture comparison is like-for-like)."""
    elig = h2_width_eligibility(df)
    n_arms = df["architecture"].nunique()
    per = elig.groupby("fact_type")["eligible"].sum()
    return sorted(per[per == n_arms].index.tolist())


def h2_width_by_facttype(df: pd.DataFrame, n_resamples: int | None = None) -> pd.DataFrame:
    """Per eligible (architecture, fact_type): isotonic 90->10 width + hierarchical
    (item -> seed) bootstrap 95% CI + resample stability (`frac_finite`).

    Individual eligible widths — reported BEFORE any cross-type summary.
    """
    elig = h2_width_eligibility(df)
    rows = []
    for r in elig.itertuples():
        if not r.eligible:
            rows.append(dict(architecture=r.architecture, fact_type=r.fact_type,
                             eligible=False, width_tokens=np.nan, ci_low=np.nan,
                             ci_high=np.nan, frac_finite=np.nan, n_items=np.nan))
            continue
        g = df[(df["architecture"] == r.architecture) & (df["fact_type"] == r.fact_type)]
        boot = _hier_bootstrap_nan(g, _width_9010, n_resamples=n_resamples)
        rows.append(dict(architecture=r.architecture, fact_type=r.fact_type, eligible=True,
                         width_tokens=round(boot["point"], 2),
                         ci_low=round(boot["ci_low"], 2), ci_high=round(boot["ci_high"], 2),
                         frac_finite=round(boot["frac_finite"], 3),
                         n_items=int(g["item_id"].nunique())))
    return pd.DataFrame(rows).sort_values(["architecture", "fact_type"]).reset_index(drop=True)


def h2_width_summary(df: pd.DataFrame, n_resamples: int | None = None) -> pd.DataFrame:
    """Per architecture: MEDIAN 90->10 width across that architecture's
    globally-eligible fact types, with a hierarchical bootstrap CI on the median.

    MEDIAN (predetermined, not chosen from the data) because: (i) robust to a
    single anomalous fact type; (ii) the eligible set is small and discrete (3
    types) so a mean over few values is unstable; (iii) it makes no
    equal-precision-weighting assumption across types. Individual eligible widths
    (`h2_width_by_facttype`) are the primary report; this is a descriptive
    cross-type summary only.
    """
    ge = globally_eligible_fact_types(df)

    def median_width(f: pd.DataFrame) -> float:
        w = [_width_9010(f[f["fact_type"] == ft]) for ft in ge]
        w = [v for v in w if np.isfinite(v)]
        return float(np.median(w)) if w else float("nan")

    rows = []
    for arm, g in df[df["fact_type"].isin(ge)].groupby("architecture"):
        boot = _hier_bootstrap_nan(g, median_width, n_resamples=n_resamples)
        rows.append(dict(architecture=arm, summary="median", eligible_fact_types=", ".join(ge),
                         n_eligible=len(ge), median_width_tokens=round(boot["point"], 2),
                         ci_low=round(boot["ci_low"], 2), ci_high=round(boot["ci_high"], 2),
                         frac_finite=round(boot["frac_finite"], 3)))
    return pd.DataFrame(rows).sort_values("architecture").reset_index(drop=True)


def h2_width_seed_sensitivity(df: pd.DataFrame) -> pd.DataFrame:
    """Per (seed, architecture): median 90->10 width across globally-eligible fact
    types (point estimate only — descriptive seed sensitivity)."""
    ge = globally_eligible_fact_types(df)
    rows = []
    for (seed, arm), g in df[df["fact_type"].isin(ge)].groupby(["seed", "architecture"]):
        w = [_width_9010(g[g["fact_type"] == ft]) for ft in ge]
        w = [v for v in w if np.isfinite(v)]
        rows.append(dict(seed=int(seed), architecture=arm,
                         median_width_tokens=round(float(np.median(w)), 2) if w else np.nan,
                         n_eligible_finite=len(w)))
    out = pd.DataFrame(rows)
    piv = out.pivot(index="seed", columns="architecture", values="median_width_tokens")
    piv.loc["seed_spread"] = piv.max() - piv.min()
    return piv.reset_index()


# --------------------------------------------------------------------------- #
# C — H1 sensitivity: exclude compound-relational  [POST-FREEZE SENSITIVITY]
# --------------------------------------------------------------------------- #

def h1_exclude_compound_relational(df: pd.DataFrame, n_resamples: int | None = None) -> dict:
    """H1 A_transition analysis with the internal `multi-hop` (compound-relational)
    fact type removed. Multiplicity: Holm over the remaining 6 pairwise contrasts
    — identical treatment to the frozen exclude-temporal sensitivity
    (`full_run.analyse` `sens_excl_temporal`).
    """
    cv = full_run.control_validity(df)
    primary_types = set(cv.loc[cv["in_h1_primary"], "fact_type"]) - {"multi-hop"}
    sub = df[df["fact_type"].isin(primary_types)]

    a_transition = h1_degradation.a_transition(sub)
    contrasts = h1_degradation.a_transition_contrasts(sub, n_resamples=n_resamples)
    omnibus = h1_degradation.a_transition_omnibus(sub, n_perm=int(n_resamples or 2000))
    return {
        "label": "POST-FREEZE SENSITIVITY — H1 excluding compound-relational (multi-hop)",
        "fact_types": sorted(primary_types),
        "a_transition": a_transition,
        "contrasts": contrasts,
        "n_contrasts": int(len(contrasts)),
        "n_significant_holm": int(contrasts["significant_holm"].sum()),
        "omnibus_dispersion_sd": omnibus["dispersion_sd"],
        "omnibus_p": omnibus["p_value"],
        "h1_still_supported": bool(contrasts["significant_holm"].any()),
    }


# --------------------------------------------------------------------------- #
# D — residual fully-exact-through-generation failures  [DESCRIPTIVE ROBUSTNESS]
# --------------------------------------------------------------------------- #

def residual_fully_exact_failures(df: pd.DataFrame) -> dict:
    flag = "target_fully_exact_through_generation"
    base = df[df[flag].astype(bool)]
    fail = base[base["correct"] == 0]
    strata = {}
    for by in ("fact_type", "architecture", "intended_model_tokens_after_target", "seed"):
        z = fail.groupby(by).size().rename("fail_n").to_frame()
        z["base_n"] = base.groupby(by).size()
        z["fail_rate"] = (z["fail_n"] / z["base_n"]).round(4)
        strata[by] = z.reset_index()
    overall = pd.DataFrame([{
        "flag": flag, "base_n": int(len(base)), "fail_n": int(len(fail)),
        "fail_rate": round(len(fail) / len(base), 4),
        "share_abstained": round(float(fail["abstained"].mean()), 4),
        "share_malformed": round(float(fail["malformed"].mean()), 4),
        "share_wrong_valid": round(float(((fail["abstained"] == 0) & (fail["malformed"] == 0)).mean()), 4),
    }])
    return {"label": "DESCRIPTIVE ROBUSTNESS — not a primary analysis; no mechanism claimed",
            "overall": overall, **{f"by_{k}": v for k, v in strata.items()}}


# --------------------------------------------------------------------------- #
# E — disclosure / robustness tables
# --------------------------------------------------------------------------- #

def _malformed_subtype(pred: str, fact_type: str) -> str:
    from ahnexp import evaluate
    c = evaluate.clean_answer(pred); low = c.lower()
    if low in evaluate._ABSTENTIONS:
        return "recognised_abstention"
    if not c:
        return "empty"
    if evaluate._NEGATION.search(c):
        return "negation"
    if len(c.split()) > evaluate._MAX_ANSWER_WORDS:
        return "too_long_gt_4_words"
    if evaluate._selected_answer(fact_type, c) is None:
        return "unrecognised_value"
    return "not_malformed"


def transformer_malformed(df: pd.DataFrame) -> dict:
    tx = df[df["architecture"] == "transformer"]
    by_pressure = (tx.groupby("intended_model_tokens_after_target")["malformed"]
                     .agg(rate="mean", n_malformed="sum", n="size").reset_index())
    by_fact = (tx.groupby("fact_type")["malformed"]
                 .agg(rate="mean", n_malformed="sum", n="size").reset_index())
    m = tx[tx["malformed"] == 1].copy()
    m["subtype"] = [_malformed_subtype(p, ft) for p, ft in zip(m["prediction"], m["fact_type"])]
    subtypes = m["subtype"].value_counts().rename_axis("subtype").reset_index(name="count")
    per_arm = df.groupby("architecture")["malformed"].mean().round(4).rename("malformed_rate").reset_index()
    anchors = tx[tx["intended_model_tokens_after_target"].isin(config.final()["control_anchors"])]
    overall = pd.DataFrame([{
        "overall_malformed_rate": round(float(tx["malformed"].mean()), 4),
        "at_control_anchors": round(float(anchors["malformed"].mean()), 4),
        "pooled_across_arms": round(float(df["malformed"].mean()), 4),
        "classification": "CONTROL BEHAVIOUR (no-recurrent-memory degeneration); "
                          "0% at in-window anchors; per-arm split mandatory, never cite pooled alone",
    }])
    return {"label": "LIMITATION / DISCLOSURE", "overall": overall, "by_pressure": by_pressure,
            "by_fact_type": by_fact, "subtypes": subtypes, "per_arm": per_arm}


def _wilson(k: int, n: int, z: float = 1.96) -> tuple[float, float]:
    if n == 0:
        return (float("nan"), float("nan"))
    p = k / n
    d = 1 + z * z / n
    c = (p + z * z / (2 * n)) / d
    h = z * np.sqrt(p * (1 - p) / n + z * z / (4 * n * n)) / d
    return (max(0.0, c - h), min(1.0, c + h))


def deep_recurrent_retention(df: pd.DataFrame, window_multiple: float = 2.0) -> dict:
    w = int(df["sliding_window"].iloc[0])
    thr = int(window_multiple * w)
    coord = schema.pressure_coordinate(df)
    deep = df[df[coord] >= thr]
    rows = []
    for arm, g in deep.groupby("architecture"):
        k, n = int(g["correct"].sum()), int(len(g))
        lo, hi = _wilson(k, n)
        v = metrics.answered_valid(g)
        wrong = v[v["correct"] == 0]
        rows.append(dict(architecture=arm, region=f"model_tat >= {thr} (={window_multiple:g}W)",
                         n=n, correct=k, strict_acc=round(k / n, 5),
                         wilson95_low=round(lo, 5), wilson95_high=round(hi, 5),
                         abstention_rate=round(float(g["abstained"].mean()), 4),
                         malformed_rate=round(float(g["malformed"].mean()), 4),
                         wrong_valid_n=int(len(wrong)),
                         mean_conf_wrong_valid=round(float(wrong["confidence"].mean()), 4) if len(wrong) else np.nan))
    per_arm = pd.DataFrame(rows)
    by_type = []
    for (arm, ft), g in deep.groupby(["architecture", "fact_type"]):
        k, n = int(g["correct"].sum()), int(len(g))
        lo, hi = _wilson(k, n)
        by_type.append(dict(architecture=arm, fact_type=ft, n=n, correct=k,
                            strict_acc=round(k / n, 5), wilson95_high=round(hi, 5),
                            abstention_rate=round(float(g["abstained"].mean()), 4)))
    return {"label": "POST-FREEZE SENSITIVITY — NEGATIVE RESULT", "per_arm": per_arm,
            "by_fact_type": pd.DataFrame(by_type)}


def temporal_counterbalancing(df: pd.DataFrame, items=None) -> dict:
    fcfg = config.final()
    items = items or dataset.generate_items(int(fcfg["n_items"]), seed=int(fcfg["seeds"][0]))
    meta = {}
    for it in items:
        if it.fact.fact_type != "temporal":
            continue
        gold_n = int(_PERSON.search(it.fact.answer).group(1))
        q = [int(x) for x in _PERSON.findall(it.fact.question)]
        meta[it.item_id] = dict(gold_is_higher=gold_n == max(q),
                                gold_first_listed=q[0] == gold_n,
                                density=it.distractor_density)
    md = pd.DataFrame(meta).T
    balance = pd.DataFrame([{
        "gold_is_higher_TrueFalse": md["gold_is_higher"].value_counts().to_dict(),
        "gold_first_listed_TrueFalse": md["gold_first_listed"].value_counts().to_dict(),
        "density": md["density"].value_counts().to_dict(),
        "cells_2x2x2": md.groupby(["gold_is_higher", "gold_first_listed", "density"]).size().to_dict(),
        "fully_balanced": bool(md.groupby(["gold_is_higher", "gold_first_listed", "density"]).size().nunique() == 1),
    }])
    tmp = df[df["fact_type"] == "temporal"].merge(md, left_on="item_id", right_index=True)
    ctrl = tmp[tmp["intended_model_tokens_after_target"].isin(fcfg["control_anchors"])]
    subgroups = []
    for col in ("gold_is_higher", "gold_first_listed", "density"):
        z = ctrl.groupby(col).apply(lambda g: pd.Series(dict(
            n=len(g), strict=g["correct"].mean(),
            answered_valid=metrics.answered_valid(g)["correct"].mean(),
            abstention=g["abstained"].mean())), include_groups=False).reset_index()
        z.insert(0, "factor", col)
        z = z.rename(columns={col: "level"})
        subgroups.append(z)
    return {"label": "LIMITATION / DISCLOSURE — model response bias, counterbalanced",
            "balance": balance,
            "control_subgroups": pd.concat(subgroups, ignore_index=True),
            "control_pooled_answered_valid": round(float(metrics.answered_valid(ctrl)["correct"].mean()), 4)}


def compound_relational_control_warning(df: pd.DataFrame) -> dict:
    fcfg = config.final()
    thr = config.experiment()["acceptance"]["control_validity"]["non_temporal"]
    mh = df[(df["fact_type"] == "multi-hop")
            & df["intended_model_tokens_after_target"].isin(fcfg["control_anchors"])]
    av = metrics.answered_valid(mh)
    pooled = pd.DataFrame([{
        "n": int(len(mh)), "strict_accuracy": round(float(mh["correct"].mean()), 4),
        "answered_valid_accuracy": round(float(av["correct"].mean()), 4),
        "abstention_rate": round(float(mh["abstained"].mean()), 4),
        "malformed_rate": round(float(mh["malformed"].mean()), 4),
    }])
    by_anchor = mh.groupby("intended_model_tokens_after_target").apply(
        lambda g: pd.Series(dict(n=len(g), strict=g["correct"].mean(),
                                 answered_valid=metrics.answered_valid(g)["correct"].mean(),
                                 abstention=g["abstained"].mean(),
                                 malformed=g["malformed"].mean())), include_groups=False).reset_index()
    by_seed = mh.groupby("seed").apply(
        lambda g: pd.Series(dict(strict=g["correct"].mean(),
                                 answered_valid=metrics.answered_valid(g)["correct"].mean(),
                                 abstention=g["abstained"].mean())), include_groups=False).reset_index()
    by_item = mh.groupby("item_id").apply(
        lambda g: pd.Series(dict(n=len(g), strict=g["correct"].mean(),
                                 abstention=g["abstained"].mean())), include_groups=False).sort_values("strict").reset_index()
    drivers = []
    s, m, a = mh["correct"].mean(), mh["malformed"].mean(), mh["abstained"].mean()
    if s < thr["pass_strict"]:
        drivers.append(f"strict {s:.3f} < pass_strict {thr['pass_strict']}")
    if m > thr["warn_malformed"]:
        drivers.append(f"malformed {m:.3f} > {thr['warn_malformed']}")
    if a > thr["warn_abstention"]:
        drivers.append(f"abstention {a:.3f} > warn_abstention {thr['warn_abstention']}")
    return {"label": "LIMITATION / DISCLOSURE — task-difficulty ceiling; retained in H1 primary",
            "pooled": pooled, "by_anchor": by_anchor, "by_seed": by_seed,
            "worst_items": by_item.head(12),
            "warning_drivers": drivers,
            "fail_threshold_crossed": bool(s < thr["fail_strict"]),
            "in_h1_primary": bool(s >= thr["fail_strict"])}


def per_seed_headline_robustness(df: pd.DataFrame) -> dict:
    a_by_seed, k_by_seed, h3_by_seed = {}, {}, {}
    for s, g in df.groupby("seed"):
        cv = full_run.control_validity(g)
        vt = set(cv.loc[cv["in_h1_primary"], "fact_type"])
        a_by_seed[int(s)] = h1_degradation.a_transition(g[g["fact_type"].isin(vt)]).set_index("fact_type")["a_transition"]
        k_by_seed[int(s)] = h2_threshold.knees(g).set_index("architecture")["k_strict_acc"]
        w = int(df["sliding_window"].iloc[0]); margin = int(config.final()["h3_signal_margin"])
        reg = g[g[schema.pressure_coordinate(g)] >= w + margin]
        h3_by_seed[int(s)] = reg.groupby("architecture")["abstained"].mean()
    A = pd.DataFrame(a_by_seed).T.sort_index()
    orderings = {tuple(row.sort_values().index) for _, row in A.iterrows()}
    K = pd.DataFrame(k_by_seed).T.sort_index()
    H3 = pd.DataFrame(h3_by_seed).T.sort_index()
    return {"label": "DESCRIPTIVE ROBUSTNESS",
            "a_transition_by_seed": A.round(4).reset_index().rename(columns={"index": "seed"}),
            "distinct_orderings": len(orderings),
            "k_strict_by_seed": K.round(2).reset_index().rename(columns={"index": "seed"}),
            "k_seed_spread": (K.max() - K.min()).round(2).to_dict(),
            "h3_appropriate_abstention_by_seed": H3.round(4).reset_index().rename(columns={"index": "seed"})}


def reproduce_plumbing_gates(df: pd.DataFrame, items=None, calibration=None) -> pd.DataFrame:
    fcfg = config.final()
    items = items or dataset.generate_items(int(fcfg["n_items"]), seed=int(fcfg["seeds"][0]))
    calibration = calibration or config.load_final_calibration()
    return full_run.plumbing_gates(df, items, calibration, verify=None)
