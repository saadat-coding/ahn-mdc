"""Synthetic fact generation and matched trajectory construction.

Cleaned up from the pilot (`notebooks/0_pilot_reference.ipynb`) with three fixes the
mentor's feedback requires:

1. Pressure is built to a **token** budget, not a fact count, so the x-axis is in the
   units the AHN module actually compresses.
2. Filler before the target is a separate knob, so target position and total prompt
   length stop being confounded with compression pressure.
3. Distractors are checked for answer collisions — a distractor that leaks the answer
   lets the model score correct without retrieving anything.
"""

from __future__ import annotations

import json
import random
import re
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Any, Callable

from ahnexp import config

COLORS = ["blue", "green", "red", "yellow", "purple"]
COMPANIES = ["Google", "Microsoft", "Amazon", "Meta", "Apple"]
CITIES_FROM = ["Paris", "Berlin", "Tokyo", "Delhi", "Sydney"]
CITIES_TO = ["London", "Madrid", "Beijing", "Toronto", "Dubai"]

# Fact types whose gold is drawn from a small fixed set. Their generators take an
# explicit answer `slot` so the choice can be driven by a per-fact-type counter
# instead of the global item index — the two must not share a modulus or every
# item of a type collapses to one gold. See tests/diagnose_constant_gold.py.
_CATEGORICAL_TYPES = ("entity-attribute", "multi-hop", "contradictory")


@dataclass
class Fact:
    fact_type: str
    text: str
    question: str
    answer: str


@dataclass
class Item:
    """One target fact with everything needed to build its trajectories."""

    item_id: str
    fact: Fact
    distractor_density: str
    distractors: list[Fact] = field(default_factory=list)

    def as_metadata(self) -> dict[str, Any]:
        return {
            "item_id": self.item_id,
            "fact_type": self.fact.fact_type,
            "distractor_density": self.distractor_density,
            "gold": self.fact.answer,
        }


# ---------------------------------------------------------------------------
# Fact generators — one per category in config/facts.yaml
# ---------------------------------------------------------------------------

def numerical(i: int) -> Fact:
    person, value = f"Person_{i}", str(100000 + i * 137)
    return Fact("numerical", f"{person}'s employee ID is {value}.",
                f"What is {person}'s employee ID?", value)


def temporal(i: int, swap_candidates: bool = False, earlier_is_higher: bool = False) -> Fact:
    lo, hi = f"Person_{i}", f"Person_{i + 1}"
    # `earlier_is_higher` sets which identity arrived first and is therefore the
    # gold (the higher- or the lower-numbered); `swap_candidates` sets whether the
    # gold is listed first or second in the question. Earlier direction determines
    # the gold's identity, candidate order its position; `generate_items` assigns
    # the two from a density-stratified, seed-shuffled balanced plan
    # (`_temporal_factor_plan`) so that the simple systematic Person-ID,
    # numeric-order, candidate-position, and density shortcuts identified by
    # validation are removed. Construct unchanged: one "<earlier> arrived before
    # <later>" relation, question "Who arrived first, A or B?".
    early, late = (hi, lo) if earlier_is_higher else (lo, hi)     # `early` == the gold
    first_q, second_q = (late, early) if swap_candidates else (early, late)
    return Fact("temporal", f"{early} arrived before {late}.",
                f"Who arrived first, {first_q} or {second_q}?", early)


def entity_attribute(i: int, slot: int | None = None) -> Fact:
    person = f"Person_{i}"
    color = COLORS[(i if slot is None else slot) % len(COLORS)]
    return Fact("entity-attribute", f"{person}'s favorite color is {color}.",
                f"What is {person}'s favorite color?", color)


def multi_hop(i: int, slot: int | None = None) -> Fact:
    a, b = f"Person_{i}", f"Person_{i + 1}"
    company = COMPANIES[(i if slot is None else slot) % len(COMPANIES)]
    return Fact("multi-hop", f"{a} manages {b}. {b} works for {company}.",
                f"Which company does {a}'s subordinate work for?", company)


def contradictory(i: int, slot: int | None = None) -> Fact:
    person = f"Person_{i}"
    pick = (i if slot is None else slot) % len(CITIES_TO)
    old, new = CITIES_FROM[pick], CITIES_TO[pick]
    assert old != new, "CITIES_FROM/CITIES_TO must stay disjoint: a fact supersedes a different city"
    return Fact("contradictory", f"{person} lived in {old}. {person} now lives in {new}.",
                f"Where does {person} live now?", new)


GENERATORS: dict[str, Callable[..., Fact]] = {
    "numerical": numerical,
    "temporal": temporal,
    "entity-attribute": entity_attribute,
    "multi-hop": multi_hop,
    "contradictory": contradictory,
}


# ---------------------------------------------------------------------------
# Temporal nuisance-factor plan
# ---------------------------------------------------------------------------

_TEMPORAL_QUAD = ((False, False), (False, True), (True, False), (True, True))
# (earlier_is_higher, swap_candidates)


def _temporal_factor_plan(n_temporal: int, seed: int) -> list[tuple[bool, bool]]:
    """(earlier_is_higher, swap_candidates) per temporal item, indexed by slot.

    `generate_items` keeps its density rule unchanged, which gives temporal item
    `slot` density `low` when slot is even and `high` when slot is odd. This
    function stratifies by that split and, within each stratum, lays down blocks
    of the four (earlier_is_higher, swap_candidates) cells, each block shuffled
    with an RNG keyed on (seed, stratum, block). Within each density level the
    four cells are exactly equal when the stratum count is divisible by 4 (so the
    earlier-identity x gold-position x density design is a balanced 2x2x2 when
    `n_temporal` is divisible by 8), and each marginal is exact when the stratum
    count is even.

    The assignment is seed-shuffled and balanced so that the simple systematic
    Person-ID, numeric-order, candidate-position, and density shortcuts identified
    by validation are removed. Deterministic for a seed; a different seed
    reshuffles while keeping the balance. `n_temporal == 2` (the pilot) is too
    small to stratify; pilot temporal is never cited as a result.
    """
    plan: list[tuple[bool, bool] | None] = [None] * n_temporal
    for stratum in ("low", "high"):
        slots = [k for k in range(n_temporal) if (k % 2) == (stratum == "high")]
        cells: list[tuple[bool, bool]] = []
        full, rem = divmod(len(slots), 4)
        for block in range(full):
            quad = list(_TEMPORAL_QUAD)
            random.Random(f"ahn-temporal-factors:{seed}:{stratum}:{block}").shuffle(quad)
            cells.extend(quad)
        if rem:
            rng_rem = random.Random(f"ahn-temporal-factors:{seed}:{stratum}:{full}")
            if rem == 2:                                   # keep both marginals balanced
                tail = [(False, False), (True, True)]
                rng_rem.shuffle(tail)
            else:                                          # rem 1 or 3: a seed-random subset
                quad = list(_TEMPORAL_QUAD)
                rng_rem.shuffle(quad)
                tail = quad[:rem]
            cells.extend(tail)
        for slot, cell in zip(slots, cells):
            plan[slot] = cell
    assert all(c is not None for c in plan), plan
    return plan  # type: ignore[return-value]


# ---------------------------------------------------------------------------
# Items
# ---------------------------------------------------------------------------

def generate_items(n_items: int, seed: int = 0, pool_size: int = 4000) -> list[Item]:
    """Balanced item set: equal N per fact type, each with its own distractor pool.

    Generated once and cached, because every arm must see byte-identical prompts.
    """
    rng = random.Random(seed)
    types = list(GENERATORS)
    densities = ["low", "high"]
    # Position of the current item within its own fact type. Categorical answers
    # are chosen from this, not from `index`, so they cycle through the whole
    # answer space instead of phase-locking with `index % len(types)`.
    slot_counter: dict[str, int] = {}
    n_temporal = sum(1 for i in range(n_items) if types[i % len(types)] == "temporal")
    temporal_plan = _temporal_factor_plan(n_temporal, seed)

    items: list[Item] = []
    for index in range(n_items):
        fact_type = types[index % len(types)]
        density = densities[(index // len(types)) % len(densities)]   # unchanged, temporal included
        slot = slot_counter.get(fact_type, 0)
        slot_counter[fact_type] = slot + 1
        if fact_type in _CATEGORICAL_TYPES:
            target = GENERATORS[fact_type](index, slot)
        elif fact_type == "temporal":
            # Nuisance factors from a density-stratified, seed-shuffled balanced
            # plan; the stratum split (slot % 2) mirrors the density rule above.
            earlier_is_higher, swap_candidates = temporal_plan[slot]
            target = GENERATORS["temporal"](
                index, swap_candidates=swap_candidates, earlier_is_higher=earlier_is_higher)
        else:
            target = GENERATORS[fact_type](index)
        item = Item(
            item_id=f"{fact_type}_{index:04d}",
            fact=target,
            distractor_density=density,
            distractors=_distractor_pool(
                fact_type, density, index, rng, pool_size, forbidden=target.answer
            ),
        )
        assert_no_collision(item)
        items.append(item)

    return items


def save_items(
    items: list[Item],
    path: Path | str,
    *,
    seed: int = 0,
    pool_size: int = 4000,
) -> Path:
    """Persist the item catalog (facts + seed). Distractor pools are not stored —
    ``load_items`` regenerates them byte-identically from ``seed`` / ``pool_size``.
    """
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    payload = {
        "seed": int(seed),
        "pool_size": int(pool_size),
        "n_items": len(items),
        "items": [
            {
                "item_id": item.item_id,
                "distractor_density": item.distractor_density,
                "fact": asdict(item.fact),
                "n_distractors": len(item.distractors),
            }
            for item in items
        ],
    }
    path.write_text(json.dumps(payload, indent=2, ensure_ascii=False) + "\n")
    return path


def load_items(path: Path | str) -> list[Item]:
    """Reload items by regenerating with the saved seed (same prompts as the run)."""
    data = json.loads(Path(path).read_text())
    items = generate_items(
        n_items=int(data["n_items"]),
        seed=int(data["seed"]),
        pool_size=int(data.get("pool_size", 4000)),
    )
    saved_ids = [row["item_id"] for row in data["items"]]
    got_ids = [item.item_id for item in items]
    if saved_ids != got_ids:
        raise ValueError(
            f"Regenerated item_ids differ from {path}. "
            "Was generate_items / facts.yaml changed since the save?"
        )
    return items


def _leaks_answer(text: str, answer: str) -> bool:
    return bool(re.search(rf"(?<!\w){re.escape(answer)}(?!\w)", text, re.IGNORECASE))


def _distractor_pool(
    fact_type: str,
    density: str,
    offset: int,
    rng: random.Random,
    size: int,
    forbidden: str,
) -> list[Fact]:
    """High density concentrates distractors on the target's own type.

    Same-type distractors interfere more, which is the point of the density factor.
    Candidates that mention the target's answer as a whole token are skipped so the
    model cannot score correct from the distractor block.
    """
    types = list(GENERATORS)
    pool: list[Fact] = []
    cursor = 1
    attempts = 0
    temporal_dir = 0                       # local; balances temporal-distractor relation direction
    while len(pool) < size:
        attempts += 1
        if attempts > size * 40:
            raise ValueError(
                f"Could not fill a {size}-fact pool without leaking {forbidden!r}. "
                "Widen the answer space or lower pool_size."
            )
        dtype = fact_type if density == "high" and rng.random() < 0.8 else rng.choice(types)
        if dtype == "temporal":
            # ~50/50 lower-first / higher-first, so an `earlier_is_higher=True`
            # target is not against a uniform distractor prior. Local counter, no
            # extra RNG draw; the density gate above and the `_leaks_answer` test
            # below are byte-identical to before (both directions carry the same
            # two Person numbers), so every non-temporal distractor and the whole
            # shared-RNG trajectory are unchanged.
            candidate = temporal(offset + cursor * 7919, earlier_is_higher=bool(temporal_dir % 2))
            temporal_dir += 1
        else:
            candidate = GENERATORS[dtype](offset + cursor * 7919)
        cursor += 1
        if _leaks_answer(candidate.text, forbidden):
            continue
        pool.append(candidate)
    return pool


def assert_no_collision(item: Item) -> None:
    """A distractor must never contain the target's answer as a whole token.

    Substring matching is too coarse: `Person_1` is a prefix of `Person_15839`, so
    it would flag every later ID as a leak. `_leaks_answer` and the scorer's
    value extraction (`evaluate._selected_answer`) both match on word boundaries,
    so a distractor that would score as the answer is the one rejected here.
    """
    if not config.facts()["collision_control"]["enabled"]:
        return
    for distractor in item.distractors:
        if _leaks_answer(distractor.text, item.fact.answer):
            raise ValueError(
                f"{item.item_id}: distractor leaks the answer {item.fact.answer!r} "
                f"in {distractor.text!r}"
            )


# ---------------------------------------------------------------------------
# Trajectories
# ---------------------------------------------------------------------------

# Strengthened from "Answer with only the short answer." The per-type {answer_hint}
# comes from config/facts.yaml; the "I don't know" line is the exact abstention the
# scorer recognises. No option set is revealed (open_decisions.md #7).
#
# The abstention clause reads "cannot be determined from the statements above", not
# "not stated above": the staged pilot showed the earlier wording was read as
# "only answer a verbatim span", which uniquely broke temporal (its gold is
# entailed by "A arrived before B", not stated) — 25% exact accuracy / 75%
# abstention while the four verbatim types were 100%. "determined from" licenses a
# one-step entailment while still permitting abstention when the fact was
# compressed away. Applied identically to all five types (open_decisions.md #7).
_PROMPT = """You are given a set of factual statements.

{context}

Question:
{question}

{answer_hint} Give only that value, with no other words.
If the answer cannot be determined from the statements above, reply with exactly: I don't know
"""


def _to_model_input(tokenizer, body: str) -> str:
    """Wrap the prompt in the checkpoint's chat template when it has one.

    Qwen2.5-*-Instruct ships a chat template; feeding it a raw string leaves the
    model without its `<|im_start|>assistant` cue and it stops following the
    "answer only" instruction. Tokenizers without a template (or bare stubs in
    tests) fall through unchanged.
    """
    template = getattr(tokenizer, "chat_template", None)
    if not template or not hasattr(tokenizer, "apply_chat_template"):
        return body
    return tokenizer.apply_chat_template(
        [{"role": "user", "content": body}], tokenize=False, add_generation_prompt=True
    )


def build_trajectory(
    item: Item,
    tokenizer,
    tokens_after_target: int,
    seed: int,
    tokens_before_target: int = 0,
) -> dict[str, Any]:
    """One matched trajectory: fixed target and query, varying pressure.

    `tokens_before_target` is filler that moves the target later in the context
    without adding compression pressure. Holding `before + after` constant while
    sweeping `after` gives the length-matched control; leaving it at zero
    reproduces the pilot's target-first layout.

    Token accounting distinguishes three quantities (open_decisions.md #1):
      * `tokens_after_target`        — distractor tokens after the target. The H1/H2
                                       independent variable; unaffected by the
                                       prompt wording or the chat template.
      * `model_tokens_after_target`  — every token after the target in the actual
                                       tokenised model input: distractors + the
                                       question/instruction block + template suffix.
                                       The exact/recurrent boundary is measured
                                       against this.
      * `context_tokens`             — the whole tokenised model input.
    """
    rng = random.Random(seed)
    order = list(item.distractors)
    rng.shuffle(order)

    before, used = _fill(order, tokenizer, tokens_before_target, start=0)
    after, _ = _fill(order, tokenizer, tokens_after_target, start=used)

    context = "\n".join(f"- {f.text}" for f in [*before, item.fact, *after])
    hint = config.facts()["types"][item.fact.fact_type]["answer_hint"]
    body = _PROMPT.format(context=context, question=item.fact.question, answer_hint=hint)
    prompt = _to_model_input(tokenizer, body)

    realised = len(tokenizer(_block(after))["input_ids"]) if after else 0
    cut = prompt.index(item.fact.text) + len(item.fact.text)
    n_full = len(tokenizer(prompt)["input_ids"])
    n_through_target = len(tokenizer(prompt[:cut])["input_ids"])
    return {
        **item.as_metadata(),
        "seed": seed,
        "prompt": prompt,
        "tokens_after_target": realised,
        "requested_tokens_after_target": tokens_after_target,
        "model_tokens_after_target": n_full - n_through_target,
        "context_tokens": n_full,
        "target_position": _position(len(before), len(after)),
    }


def _fill(pool: list[Fact], tokenizer, budget: int, start: int) -> tuple[list[Fact], int]:
    """Take facts from the pool until the token budget is met."""
    if budget <= 0:
        return [], start

    taken, total, cursor = [], 0, start
    while total < budget and cursor < len(pool):
        fact = pool[cursor]
        cursor += 1
        taken.append(fact)
        total = len(tokenizer(_block(taken))["input_ids"])

    if total < budget:
        raise ValueError(
            f"Distractor pool exhausted at {total} tokens, short of the {budget} requested. "
            "Increase pool_size in generate_items."
        )
    return taken, cursor


def _block(facts: list[Fact]) -> str:
    return "\n".join(f"- {f.text}" for f in facts)


def _position(n_before: int, n_after: int) -> str:
    total = n_before + n_after
    if total == 0:
        return "early"
    fraction = n_before / total
    return "early" if fraction < 0.25 else "mid" if fraction < 0.75 else "late"
