"""Per-trial results contract.

The seam between the run pipeline and the three hypothesis analyses. One row = one
(item, architecture, pressure level, seed) trial. H1, H2 and H3 all read this, so
nobody may quietly rename a column.
"""

from __future__ import annotations

from dataclasses import dataclass

import pandas as pd


@dataclass(frozen=True)
class Column:
    name: str
    dtype: str
    description: str


IDENTITY = (
    Column("item_id", "string", "Stable id of the fact/query pair, identical across arms"),
    Column("architecture", "string", "mamba2 | deltanet | gated_deltanet | transformer"),
    Column("seed", "int64", "Seed controlling distractor sampling and ordering"),
)

DESIGN = (
    Column("tokens_after_target", "int64",
           "Distractor tokens after the target. The H1/H2 independent variable — "
           "not affected by prompt wording or the chat template. This is the "
           "*realised* count and overshoots the requested grid level because "
           "`dataset._fill` adds whole distractor facts"),
    Column("requested_tokens_after_target", "int64",
           "Nominal pressure grid level requested for this trial (the "
           "`build_trajectory` input). Optional: frames built before this column "
           "existed (the pilot CSV, older parquets) omit it and analyses key on "
           "`tokens_after_target` / `model_tokens_after_target` as before"),
    Column("model_tokens_after_target", "int64",
           "Every token after the target in the tokenised model input (distractors + "
           "question/instruction + chat-template suffix); the exact/recurrent boundary "
           "is measured against this, and it is the scientific pressure coordinate for "
           "the H1/H2/H3 curves"),
    Column("target_fact_tokens", "int64",
           "In-context tokenised length of the target sentence (`n_through_target - "
           "n_before_target` in `dataset.build_trajectory`). The target is a span, not "
           "a point; with `model_tokens_after_target`, `n_new_tokens` and "
           "`sliding_window` this locates the span relative to the compression "
           "boundary. Optional: absent from frames built before it existed"),
    Column("intended_model_tokens_after_target", "int64",
           "Pilot Pass 2 / model-tat-targeted grids only: the "
           "`model_tokens_after_target` level this trajectory was calibrated to hit. "
           "Absent for window-multiple grids (mini / pilot / full)"),
    Column("sliding_window", "int64", "Window length in force, for normalisation"),
    Column("memory_condition", "string", "exact_memory | recurrent_memory"),
    Column("fact_type", "string", "Category from config/facts.yaml"),
    Column("distractor_density", "string", "low | high"),
    Column("target_position", "string", "early | mid | late"),
    Column("context_tokens", "int64", "Total tokenised model input length"),
)

OUTCOME = (
    Column("correct", "int64", "1 if the canonicalised answer exactly equals the gold"),
    Column("abstained", "int64", "1 if the response was exactly an abstention ('I don't know')"),
    Column("malformed", "int64",
           "1 if the response is not exactly one recognised short answer "
           "(empty, negated, too long, bare mention, echo, or competing candidates)"),
    Column("answer_canonical", "string", "The single value the response selected, canonicalised"),
    Column("confidence", "float64", "Confidence of the generated answer, in [0, 1]"),
    Column("n_new_tokens", "int64", "Generated token count, for the max_new_tokens audit"),
    Column("prediction", "string", "Full raw generated text, verbatim — the audit trail for rescoring"),
    Column("gold", "string", "Gold answer"),
)

COLUMNS = IDENTITY + DESIGN + OUTCOME

# The minimum each hypothesis needs. Being explicit means an analysis keeps working
# when optional columns are added upstream.
REQUIRED = {
    "core": ("item_id", "architecture", "seed", "tokens_after_target", "sliding_window",
             "memory_condition", "correct"),
    "h1": ("fact_type",),
    "h2": ("model_tokens_after_target",),
    "h3": ("confidence",),
}

# Three pressure quantities, kept distinct:
#   * scientific group key  — the balanced pressure level to aggregate one cell per
#     (`pressure_group_key`). For a model-tat-targeted grid (Pilot Pass 2) this is
#     `intended_model_tokens_after_target`; per-fact-type calibration means
#     `requested_tokens_after_target` has many more distinct values than the grid
#     has levels, so grouping on it fragments balanced n cells into small ones.
#   * design lever          — what `build_trajectory` was actually asked for
#     (`pressure_design_key`); provenance / dedup identity of a trial.
#   * scientific x-axis     — what the model saw after the target
#     (`pressure_coordinate` = `model_tokens_after_target`); fit / plot against this.
# All fall back to `tokens_after_target` for legacy frames (pilot CSV, old parquets,
# synthetic fixtures) so mini / smoke / pilot behaviour is unchanged.
_GROUP_KEYS = ("intended_model_tokens_after_target", "requested_tokens_after_target")
_DESIGN_KEY = "requested_tokens_after_target"
_COORDINATE = "model_tokens_after_target"


def pressure_group_key(df: pd.DataFrame) -> str:
    """Column to aggregate ONE balanced cell per scientific pressure level.

    `intended_model_tokens_after_target` when present (model-tat-targeted grids),
    else `requested_tokens_after_target`, else `tokens_after_target`.
    """
    for key in _GROUP_KEYS:
        if key in df.columns:
            return key
    return "tokens_after_target"


def pressure_design_key(df: pd.DataFrame) -> str:
    """Column identifying a trial's requested pressure lever (provenance / dedup).

    Not the scientific grouping key — see `pressure_group_key`.
    """
    return _DESIGN_KEY if _DESIGN_KEY in df.columns else "tokens_after_target"


def pressure_coordinate(df: pd.DataFrame) -> str:
    """Column holding the realised pressure coordinate (the scientific x-axis)."""
    return _COORDINATE if _COORDINATE in df.columns else "tokens_after_target"


def deep_in_window_anchor(df: pd.DataFrame) -> pd.Series:
    """Boolean mask for the deepest in-window pressure anchor.

    The cleanest empirical control in a pressure sweep: the lowest scientific
    pressure level whose median `model_tokens_after_target` sits comfortably below
    the window (< 0.8 W), where every arm is near ceiling and the AHN recurrent
    kernel is inert. This is NOT a redefinition of `memory_condition` or of "exact
    memory" — it is one selected anchor, reported alongside the coarse and
    span-aware boundary flags.
    """
    key = pressure_group_key(df)
    coord = _COORDINATE if _COORDINATE in df.columns else "tokens_after_target"
    for level in sorted(df[key].unique()):
        sub = df[df[key] == level]
        w = float(sub["sliding_window"].median())
        if float(sub[coord].median()) < 0.8 * w:
            return df[key] == level
    return df[key] == sorted(df[key].unique())[0]


_BOUNDARY_PRIMITIVES = (
    "model_tokens_after_target", "target_fact_tokens", "n_new_tokens", "sliding_window",
)
_BOUNDARY_DERIVED = (
    "target_start_distance_prefill",
    "target_fully_exact_at_prefill",
    "target_partially_compressed_at_prefill",
    "target_end_compressed_at_prefill",
    "target_fully_exact_through_generation",
    "target_end_crosses_during_generation",
)


def empty_frame() -> pd.DataFrame:
    return pd.DataFrame({c.name: pd.Series(dtype=c.dtype) for c in COLUMNS})


def validate(df: pd.DataFrame, *, needs: tuple[str, ...] = ("core",)) -> pd.DataFrame:
    """Fail loudly on a malformed results frame, before it reaches a figure."""
    required: list[str] = []
    for group in needs:
        required.extend(REQUIRED[group])

    missing = [name for name in required if name not in df.columns]
    if missing:
        raise ValueError(f"Results frame is missing required columns: {missing}")
    if df.empty:
        raise ValueError("Results frame is empty.")

    for flag in ("correct", "abstained", "malformed"):
        if flag in df.columns:
            bad = set(df[flag].dropna().unique()) - {0, 1}
            if bad:
                raise ValueError(f"`{flag}` must be 0/1; found {sorted(bad)}")

    if "confidence" in df.columns:
        conf = df["confidence"].dropna()
        if not conf.between(0.0, 1.0).all():
            raise ValueError("`confidence` must lie in [0, 1].")

    duplicated = df.duplicated(
        subset=["item_id", "architecture", "seed", pressure_group_key(df)]
    )
    if duplicated.any():
        raise ValueError(f"{int(duplicated.sum())} duplicated trials in the results frame.")

    return df


def derive_memory_condition(df: pd.DataFrame) -> pd.DataFrame:
    """Recompute `memory_condition` from the mechanical rule.

    The target has left exact attention once the number of tokens after it reaches
    the window. That count is `model_tokens_after_target` (the real tokenised input)
    when available; older frames (the pilot CSV, synthetic fixtures) only carry
    `tokens_after_target` and fall back to it.
    """
    out = df.copy()
    after = (
        out["model_tokens_after_target"]
        if "model_tokens_after_target" in out.columns
        else out["tokens_after_target"]
    )
    out["memory_condition"] = (after >= out["sliding_window"]).map(
        {True: "recurrent_memory", False: "exact_memory"}
    )
    return out


def derive_boundary_conditions(df: pd.DataFrame, *, strict: bool = False) -> pd.DataFrame:
    """Span/prefill/generation boundary variables, from the recorded primitives.

    The target fact is a span of `target_fact_tokens`, not a point. During prefill
    the AHN kernel compresses everything more than `sliding_window` tokens before
    the prompt end; each decode step compresses one more position. These flags say
    where the target span sits relative to that moving boundary, using the *actual*
    `n_new_tokens` (`max_new_tokens` is only a conservative design bound).

    `strict=True` (the run pipeline) raises if any primitive is missing. `strict=
    False` (legacy parquet / exploratory) emits the derived columns as NA instead.
    Never called by `validate`; additive, and does not touch `memory_condition`.
    """
    out = df.copy()
    missing = [c for c in _BOUNDARY_PRIMITIVES if c not in out.columns]
    if missing:
        if strict:
            raise ValueError(
                "derive_boundary_conditions(strict=True) needs "
                f"{list(_BOUNDARY_PRIMITIVES)}; missing {missing}"
            )
        for name in _BOUNDARY_DERIVED:
            out[name] = pd.NA
        return out

    w = out["sliding_window"]
    mtat = out["model_tokens_after_target"]
    span = out["target_fact_tokens"]
    gen = out["n_new_tokens"]
    start_distance = mtat + span

    out["target_start_distance_prefill"] = start_distance
    out["target_fully_exact_at_prefill"] = start_distance <= w
    out["target_partially_compressed_at_prefill"] = (mtat < w) & (start_distance > w)
    out["target_end_compressed_at_prefill"] = mtat >= w
    out["target_fully_exact_through_generation"] = (mtat + span + gen) <= w
    out["target_end_crosses_during_generation"] = (mtat < w) & ((mtat + gen) >= w)
    return out


def describe() -> pd.DataFrame:
    """Human-readable schema, for the appendix and for onboarding."""
    return pd.DataFrame(
        [(c.name, c.dtype, c.description) for c in COLUMNS],
        columns=["column", "dtype", "description"],
    )


# ---------------------------------------------------------------------------
# Pilot adapter
# ---------------------------------------------------------------------------

_PILOT_RENAME = {"fact_id": "item_id", "ground_truth": "gold", "token_count": "context_tokens"}


def from_pilot_csv(path, architecture: str, sliding_window: int) -> pd.DataFrame:
    """Adapt `data/pilot_raw_results.csv` to the schema, for one arm.

    The pilot measured pressure in facts. `tokens_after_target` is recovered by
    differencing each item's context length against its own zero-pressure probe,
    then collapsed to the level median — the design variable is the nominal level,
    and per-item length jitter is realisation noise.

    The pilot predates the window fix (open_decisions.md #1), so `sliding_window`
    must be passed in explicitly and the resulting memory conditions are only as
    trustworthy as that number.
    """
    df = pd.read_csv(path).rename(columns=_PILOT_RENAME)

    baseline = df[df["facts_after_target"] == 0].set_index("item_id")["context_tokens"]
    missing = set(df["item_id"]) - set(baseline.index)
    if missing:
        raise ValueError(f"{len(missing)} items have no zero-pressure probe to difference against.")

    realised = df["context_tokens"] - df["item_id"].map(baseline)
    df["tokens_after_target"] = (
        realised.groupby(df["facts_after_target"]).transform("median").round().astype(int)
    )
    df["architecture"] = architecture
    df["sliding_window"] = int(sliding_window)
    df["target_position"] = "early"      # the pilot always placed the target first
    if "abstained" not in df.columns:
        # The pilot did not separate "declined to answer" from "answered wrong".
        df["abstained"] = 0

    return validate(derive_memory_condition(df), needs=("core", "h1", "h3"))
