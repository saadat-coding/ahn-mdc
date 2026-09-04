"""Generation and deterministic scoring — one trial at a time, plus the grid runner.

Scoring (`score_row` / `rescore`) is a pure function of the stored raw generation:
a GPU run is scored once and can be re-scored offline without re-inference.
"""

from __future__ import annotations

import gc
import re
from pathlib import Path
from typing import Any, Iterable

import pandas as pd

from ahnexp import config, dataset, models, schema

SCORER_VERSION = "1.0"

# Matched against the WHOLE cleaned answer, never as a substring. The prompt asks
# the model to reply exactly "I don't know"; the rest are safety nets.
_ABSTENTIONS = frozenset({
    "i don't know", "i dont know", "i do not know", "idk", "unknown", "not known",
    "no answer", "not stated", "not given", "not sure", "i'm not sure", "im not sure",
    "cannot be determined", "can't tell",
})
_NEGATION = re.compile(r"(?i)\b(?:not|never|no longer|n't|isn'?t|wasn'?t|aren'?t|don'?t|doesn'?t|didn'?t)\b")
_LABEL = re.compile(r"(?i)^\s*(?:the\s+)?(?:answer|ans|a)\b\s*(?:is\b\s*|[:=]\s*)")
_PERSON = re.compile(r"(?i)person[ _]?(\d+)")
_NUMBER = re.compile(r"\d[\d,]*")
_MAX_ANSWER_WORDS = 4


def clean_answer(text: str) -> str:
    """First line of the generation, minus a leading label and wrapping/trailing punctuation."""
    if not text or not text.strip():
        return ""
    line = text.strip().splitlines()[0]
    line = _LABEL.sub("", line, count=1)
    line = line.strip(" \t`\"'*()[]{}<>")
    line = line.rstrip(".,;:!?").strip()
    return re.sub(r"\s+", " ", line)


def _one_from_set(low: str, options: Iterable[str]) -> str | None:
    present = sorted({o for o in options if re.search(rf"\b{re.escape(o)}\b", low)})
    return present[0] if len(present) == 1 else None


def _selected_answer(fact_type: str, cleaned: str) -> str | None:
    """The single value the response selects, or None if it is not exactly one."""
    low = cleaned.lower()
    if fact_type == "numerical":
        nums = {int(m.group().replace(",", "")) for m in _NUMBER.finditer(low)}
        return str(next(iter(nums))) if len(nums) == 1 else None
    if fact_type == "temporal":
        people = {f"person_{int(d)}" for d in _PERSON.findall(low)}
        return next(iter(people)) if len(people) == 1 else None
    if fact_type == "entity-attribute":
        return _one_from_set(low, (c.lower() for c in dataset.COLORS))
    if fact_type == "multi-hop":
        return _one_from_set(low, (c.lower() for c in dataset.COMPANIES))
    if fact_type == "contradictory":
        return _one_from_set(low, (c.lower() for c in (*dataset.CITIES_FROM, *dataset.CITIES_TO)))
    raise ValueError(f"Unknown fact_type {fact_type!r}")


def _canonical_gold(fact_type: str, gold: str) -> str:
    if fact_type == "numerical":
        return str(int(str(gold).replace(",", "").strip()))
    if fact_type == "temporal":
        m = _PERSON.search(str(gold))
        return f"person_{int(m.group(1))}" if m else str(gold).lower()
    return str(gold).strip().lower()


def score_row(prediction: str, gold: str, fact_type: str) -> dict[str, Any]:
    """Deterministic outcome for one trial. Pure: no model, no randomness.

    Returns `correct`, `abstained`, `malformed` (0/1) and `answer_canonical`. A row
    is exactly one of: correct, wrong, abstained, malformed. A malformed response
    (empty, a negation, too long, or not exactly one recognised value — which is
    where a bare gold mention, a question echo, and multiple competing candidates
    all land) scores `correct=0` and is also flagged for separate reporting.
    """
    cleaned = clean_answer(prediction)
    low = cleaned.lower()

    if low in _ABSTENTIONS:
        return {"correct": 0, "abstained": 1, "malformed": 0, "answer_canonical": ""}
    if not cleaned or len(cleaned.split()) > _MAX_ANSWER_WORDS or _NEGATION.search(cleaned):
        return {"correct": 0, "abstained": 0, "malformed": 1, "answer_canonical": ""}

    selected = _selected_answer(fact_type, cleaned)
    if selected is None:
        return {"correct": 0, "abstained": 0, "malformed": 1, "answer_canonical": ""}

    return {
        "correct": int(selected == _canonical_gold(fact_type, gold)),
        "abstained": 0,
        "malformed": 0,
        "answer_canonical": selected,
    }


def rescore(df: pd.DataFrame) -> pd.DataFrame:
    """Recompute outcome columns from the stored raw `prediction`. No GPU needed."""
    missing = {"prediction", "gold", "fact_type"} - set(df.columns)
    if missing:
        raise ValueError(f"Cannot rescore: frame is missing {sorted(missing)}")
    out = df.copy()
    scored = out.apply(
        lambda r: score_row(r["prediction"], r["gold"], r["fact_type"]),
        axis=1, result_type="expand",
    )
    for col in ("correct", "abstained", "malformed", "answer_canonical"):
        out[col] = scored[col]
    out["scorer_version"] = SCORER_VERSION
    return out


def run_trial(model, tokenizer, trajectory: dict[str, Any]) -> dict[str, Any]:
    """Generate one trajectory from a fresh state. Returns the RAW generation, its
    confidence and the new-token count only — scoring happens in `score_row`.

    Each call is an independent forward pass, which satisfies the state-reset
    commitment: no probe can influence a later one.
    """
    import numpy as np
    import torch

    generation = config.experiment()["models"]["matched"]["generation"]
    device = getattr(model, "device", None) or next(model.parameters()).device
    inputs = tokenizer(trajectory["prompt"], return_tensors="pt", truncation=False).to(device)
    prompt_len = inputs["input_ids"].shape[1]

    stop_strings = generation.get("stop_strings")
    stop_kwargs = {"stop_strings": stop_strings, "tokenizer": tokenizer} if stop_strings else {}
    with torch.no_grad():
        output = model.generate(
            **inputs,
            max_new_tokens=generation["max_new_tokens"],
            do_sample=generation["do_sample"],
            num_beams=generation["num_beams"],
            return_dict_in_generate=True,
            output_scores=True,
            pad_token_id=tokenizer.eos_token_id,
            **stop_kwargs,
        )

    generated = output.sequences[0, prompt_len:]
    prediction = tokenizer.decode(generated, skip_special_tokens=True)  # verbatim, not stripped

    scores = model.compute_transition_scores(output.sequences, output.scores, normalize_logits=True)
    log_probs = scores[0][: len(generated)]

    return {
        "prediction": prediction,
        "gold": trajectory["gold"],
        "confidence": _confidence(log_probs, np),
        "n_new_tokens": int(len(generated)),
    }


def _confidence(log_probs, np) -> float:
    """Sequence probability, or its length-normalised form.

    Sequence probability penalises long answers — the pilot's values span six orders
    of magnitude, which distorts every calibration bin. Which one we use is still an
    open decision (open_decisions.md #6), so both live behind the config switch.
    """
    mode = config.experiment()["calibration"]["confidence"]
    total = float(log_probs.sum())
    if mode == "sequence_probability":
        return float(np.exp(total))
    if mode == "length_normalised":
        return float(np.exp(total / max(len(log_probs), 1)))
    raise ValueError(f"Unknown confidence mode {mode!r}")


# ---------------------------------------------------------------------------
# Grid runner
# ---------------------------------------------------------------------------

def _trajectory_schedule(
    item: dataset.Item,
    window: int,
    mode: str,
    pressure_plan: dict[str, dict[int, int]] | None,
) -> list[tuple[int, int | None]]:
    """`(requested_tokens_after_target, intended_model_tat | None)` for one item.

    Without a plan: the window-multiple grid, `intended` is None. With a plan: the
    per-fact-type calibrated requested values for this item's fact type.
    """
    if pressure_plan is None:
        return [(level, None) for level in pressure_levels(window, mode)]
    per_type = pressure_plan.get(item.fact.fact_type)
    if not per_type:
        raise KeyError(f"pressure_plan has no entry for fact_type {item.fact.fact_type!r}")
    return [(int(per_type[target]), int(target)) for target in sorted(per_type)]


def pressure_levels(sliding_window: int, mode: str = "pilot") -> list[int]:
    """Grid in tokens, from window multiples, with T inserted as its own point."""
    pressure = config.experiment()["pressure"]
    multiples = pressure[config.run_mode(mode)["grid"]]
    cap = int(pressure["max_context_tokens"])

    levels = {min(int(round(m * sliding_window)), cap) for m in multiples}
    if pressure["include_threshold"]:
        levels.add(min(config.compression_threshold(strict=False), cap))
    return sorted(levels)


def run_grid(
    items: Iterable[dataset.Item],
    tokenizer_for_items,
    ahn_repo: str | Path | None = None,
    mode: str = "pilot",
    arms: list[str] | None = None,
    length_matched: bool = False,
    pressure_plan: dict[str, dict[int, int]] | None = None,
) -> pd.DataFrame:
    """Replay the same items across every arm, at every pressure level.

    Arms load one at a time and are released before the next: three merged 3B
    checkpoints do not co-exist on a typical single GPU (Colab or laptop).

    `pressure_plan` (Pilot Pass 2): `{fact_type: {intended_model_tat: requested_tokens}}`.
    When given it replaces the window-multiple grid — each trajectory is built with
    the per-fact-type `requested_tokens` and the record carries
    `intended_model_tokens_after_target` (the model-tat level it was calibrated to
    hit). Incompatible with `length_matched`.
    """
    items = list(items)
    arms = arms or models.list_arms()
    seeds = config.run_mode(mode)["seeds"]
    # None → config.ahn_repo() (AHN_REPO / Colab / vendor/AHN)
    resolved_repo = config.ahn_repo(ahn_repo) if ahn_repo is not None else None

    if pressure_plan is not None and length_matched:
        raise ValueError("pressure_plan and length_matched are mutually exclusive.")

    records: list[dict[str, Any]] = []
    descriptions: list[dict[str, Any]] = []

    for name in arms:
        model, tokenizer = models.load(name, ahn_repo=resolved_repo)
        description = models.describe(name, model, tokenizer)
        descriptions.append(description)
        window = description["sliding_window"]
        budget = max(pressure_levels(window, mode)) if length_matched else 0

        for seed in seeds:
            for item in items:
                for requested, intended in _trajectory_schedule(
                    item, window, mode, pressure_plan
                ):
                    trajectory = dataset.build_trajectory(
                        item,
                        tokenizer,
                        tokens_after_target=requested,
                        seed=seed,
                        # Length matching trades filler for pressure so the total
                        # prompt stays constant across the sweep.
                        tokens_before_target=max(budget - requested, 0),
                    )
                    record = {
                        **{k: trajectory[k] for k in
                           ("item_id", "fact_type", "distractor_density", "target_position",
                            "tokens_after_target", "requested_tokens_after_target",
                            "model_tokens_after_target", "target_fact_tokens",
                            "context_tokens", "seed")},
                        "architecture": name,
                        "sliding_window": window,
                        **run_trial(model, tokenizer, trajectory),
                    }
                    if intended is not None:
                        record["intended_model_tokens_after_target"] = intended
                    record.update(
                        score_row(record["prediction"], record["gold"], record["fact_type"])
                    )
                    records.append(record)

        del model, tokenizer
        gc.collect()
        _empty_cuda_cache()

    models.assert_matched(descriptions)
    df = schema.derive_memory_condition(pd.DataFrame(records))
    df = schema.derive_boundary_conditions(df, strict=True)
    df["scorer_version"] = SCORER_VERSION
    return schema.validate(df, needs=("core", "h1", "h3"))


def _empty_cuda_cache() -> None:
    try:
        import torch

        if torch.cuda.is_available():
            torch.cuda.empty_cache()
    except ImportError:
        pass
