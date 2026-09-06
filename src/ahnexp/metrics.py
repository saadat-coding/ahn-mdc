"""Metrics, with their published definitions.

Every formula here is the one cited in the research doc. Do not "improve" them —
matching the published definition is the point.
"""

from __future__ import annotations

import numpy as np
import pandas as pd

from ahnexp import config


def accuracy(df: pd.DataFrame) -> float:
    return float(df["correct"].mean())


def answered_valid(df: pd.DataFrame) -> pd.DataFrame:
    """Rows that are a factual answer attempt: not an abstention, not malformed.

    The only population where `confidence` is confidence in a factual answer and
    where factual ECE / Brier / CWR are meaningful.
    """
    mask = pd.Series(True, index=df.index)
    if "abstained" in df.columns:
        mask &= df["abstained"] == 0
    if "malformed" in df.columns:
        mask &= df["malformed"] == 0
    return df[mask]


def baseline_adjusted_accuracy(df: pd.DataFrame, baseline) -> float:
    """`(accuracy - baseline) / (1 - baseline)`, negatives left unclipped.

    `baseline` is EXPLICIT and provenance-bearing — a scalar, a
    `{fact_type: float}` mapping, or a per-row Series. This function never reads a
    universal chance value from config. Temporal's mathematical 0.5 (two-alternative
    choice) must be passed explicitly and is NOT equivalent to the provisional
    free-response `chance` values (open_decisions #17).
    """
    acc = df["correct"].astype(float)
    if isinstance(baseline, dict):
        b = df["fact_type"].map(baseline).astype(float)
    elif isinstance(baseline, pd.Series):
        b = baseline.reindex(df.index).astype(float)
    else:
        b = pd.Series(float(baseline), index=df.index)
    return float(((acc - b) / (1.0 - b)).mean())


def retrieval_failure_rate(df: pd.DataFrame) -> float:
    """Wrong answers, excluding explicit abstentions.

    An abstention is a different failure from a confidently wrong retrieval, and
    lumping them together hides exactly the behaviour H3 is about.
    """
    answered = df[df["abstained"] == 0] if "abstained" in df.columns else df
    return float((1 - answered["correct"]).mean()) if len(answered) else float("nan")


def abstention_rate(df: pd.DataFrame) -> float:
    return float(df["abstained"].mean()) if "abstained" in df.columns else float("nan")


def malformed_rate(df: pd.DataFrame) -> float:
    """Fraction of responses that were not exactly one recognised short answer.

    Descriptive only. Malformed responses already score `correct=0`, so they are
    inside `accuracy` and `retrieval_failure_rate`; this reports them separately so
    a run can be checked for format collapse (e.g. rising with compression pressure).
    """
    return float(df["malformed"].mean()) if "malformed" in df.columns else float("nan")


def expected_calibration_error(
    confidence, correct, n_bins: int | None = None
) -> tuple[float, pd.DataFrame]:
    """ECE with equal-width bins.

    Guo, Pleiss, Sun & Weinberger 2017, "On Calibration of Modern Neural Networks",
    ICML (arXiv:1706.04599):

        ECE = sum_m (|B_m| / N) * | acc(B_m) - conf(B_m) |

    Returns the scalar and the per-bin table behind the reliability diagram.
    """
    cfg = config.experiment()["calibration"]
    n_bins = n_bins or int(cfg["ece_bins"])
    if cfg["ece_binning"] != "equal_width":
        raise NotImplementedError(
            f"Only equal-width binning is implemented; config asks for {cfg['ece_binning']!r}."
        )

    confidence = np.asarray(confidence, dtype=float)
    correct = np.asarray(correct, dtype=float)
    total = len(confidence)
    edges = np.linspace(0.0, 1.0, n_bins + 1)

    ece, rows = 0.0, []
    for b in range(n_bins):
        low, high = edges[b], edges[b + 1]
        mask = (confidence > low) & (confidence <= high) if b else (confidence >= low) & (confidence <= high)
        if not mask.any():
            continue
        bin_accuracy = correct[mask].mean()
        bin_confidence = confidence[mask].mean()
        weight = mask.sum() / total
        ece += weight * abs(bin_accuracy - bin_confidence)
        rows.append(
            {
                "bin": f"({low:.1f}, {high:.1f}]",
                "n": int(mask.sum()),
                "accuracy": float(bin_accuracy),
                "confidence": float(bin_confidence),
                "gap": float(bin_confidence - bin_accuracy),
            }
        )

    return float(ece), pd.DataFrame(rows)


def brier_score(confidence, correct) -> float:
    """Mean squared error between confidence and the 0/1 outcome.

    Brier 1950, "Verification of Forecasts Expressed in Terms of Probability",
    Monthly Weather Review 78(1): 1-3.

        BS = (1/N) * sum_i (p_i - o_i)^2
    """
    confidence = np.asarray(confidence, dtype=float)
    correct = np.asarray(correct, dtype=float)
    return float(np.mean((confidence - correct) ** 2))


def confidently_wrong_rate(df: pd.DataFrame, threshold: float | None = None) -> float:
    """Fraction of high-confidence answers that are wrong.

    The most direct evidence for H3: memory failure the model does not signal.
    The threshold is provisional — see `protocol/open_decisions.md` #5.

    Pass ``metrics.answered_valid(df)`` — an abstention scores ``correct=0`` while
    its confidence is confidence in "I don't know", so including abstentions /
    malformed here inflates the rate meaninglessly. `h3_calibration` does this by
    default.
    """
    threshold = threshold if threshold is not None else float(
        config.experiment()["calibration"]["cwr_threshold"]
    )
    confident = df[df["confidence"] >= threshold]
    return float(1.0 - confident["correct"].mean()) if len(confident) else float("nan")


def confidence_accuracy_gap(df: pd.DataFrame) -> float:
    """Mean confidence minus accuracy. Positive means overconfident."""
    return float(df["confidence"].mean() - df["correct"].mean())


def chance_corrected_accuracy(df: pd.DataFrame) -> float:
    """DEPRECATED (open_decisions #17) — reads the provisional `config/facts.yaml`
    `chance` block silently. The 0.2 free-response floors are unverified and
    probably wrong; temporal's 0.5 is a mathematical property that must not be
    treated as equivalent. Prefer `baseline_adjusted_accuracy(df, baseline)` with
    an explicit, provenance-bearing baseline. Kept only so existing H1 tables render.
    """
    chance = config.facts()["chance"]
    floors = df["fact_type"].map(chance).astype(float)
    corrected = (df["correct"] - floors) / (1.0 - floors)
    return float(corrected.mean())
