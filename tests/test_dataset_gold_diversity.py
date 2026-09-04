"""Regression tests — categorical fact types must not collapse to a constant gold.

Guards the fix in ``ahnexp.dataset``: closed-set answers (colour / company / city)
are chosen from a per-fact-type counter, not ``LIST[index % 5]``, so they can no
longer phase-lock with the balanced fact-type assignment.

These run against the PRODUCTION generator and are expected to pass. If a future
change reintroduces a constant gold for any categorical type, they fail.

Read-only. Golds are independent of ``pool_size``, so a small pool keeps this fast.

    python -m unittest discover -s tests
"""

from __future__ import annotations

import sys
import unittest
from collections import Counter
from pathlib import Path

_ROOT = Path(__file__).resolve().parents[1]
for _p in (str(_ROOT), str(_ROOT / "src")):
    if _p not in sys.path:
        sys.path.insert(0, _p)

from ahnexp import dataset

# Fact types with a finite, enumerable answer space (facts.yaml: answer_form closed_set).
CATEGORICAL = ("entity-attribute", "multi-hop", "contradictory")
ANSWER_SPACE = {
    "entity-attribute": dataset.COLORS,
    "multi-hop": dataset.COMPANIES,
    "contradictory": dataset.CITIES_TO,
}
OPEN_ENDED = ("numerical", "temporal")

N_ITEMS = 500
SEEDS = (0, 1, 2)
POOL = 48  # gold answers do not depend on pool_size


def _golds_by_type(items):
    out: dict[str, list[str]] = {}
    for it in items:
        out.setdefault(it.fact.fact_type, []).append(it.fact.answer)
    return out


def _items(seed):
    return dataset.generate_items(n_items=N_ITEMS, seed=seed, pool_size=POOL)


class TestGoldDiversity(unittest.TestCase):
    """No categorical fact type may reduce to a single (or dominant) gold."""

    def test_no_categorical_type_collapses_to_one_gold(self):
        for seed in SEEDS:
            golds = _golds_by_type(_items(seed))
            for ft in CATEGORICAL:
                with self.subTest(seed=seed, fact_type=ft):
                    uniq = set(golds[ft])
                    self.assertGreater(
                        len(uniq), 1,
                        f"fact type {ft!r} has a single gold {uniq!r} across {len(golds[ft])} items",
                    )

    def test_categorical_types_cover_their_answer_space(self):
        for seed in SEEDS:
            golds = _golds_by_type(_items(seed))
            for ft in CATEGORICAL:
                with self.subTest(seed=seed, fact_type=ft):
                    self.assertEqual(
                        set(golds[ft]), set(ANSWER_SPACE[ft]),
                        f"{ft!r} uses {sorted(set(golds[ft]))}, expected the full "
                        f"space {sorted(set(ANSWER_SPACE[ft]))}",
                    )

    def test_most_common_gold_is_not_dominant(self):
        # Balanced over K options -> ~1/K each. Allow slack: <= 2x uniform.
        for seed in SEEDS:
            golds = _golds_by_type(_items(seed))
            for ft in CATEGORICAL:
                with self.subTest(seed=seed, fact_type=ft):
                    counts = Counter(golds[ft])
                    top_share = counts.most_common(1)[0][1] / sum(counts.values())
                    ceiling = 2.0 / len(ANSWER_SPACE[ft])
                    self.assertLessEqual(
                        top_share, ceiling,
                        f"{ft!r} most common gold holds {top_share:.1%} (blind-baseline "
                        f"accuracy); balanced ceiling is {ceiling:.1%}",
                    )

    def test_categorical_frequencies_approximately_balanced(self):
        # Every option within ceil(n/K) of every other.
        for seed in SEEDS:
            golds = _golds_by_type(_items(seed))
            for ft in CATEGORICAL:
                with self.subTest(seed=seed, fact_type=ft):
                    counts = Counter(golds[ft])
                    for opt in ANSWER_SPACE[ft]:
                        counts.setdefault(opt, 0)
                    spread = max(counts.values()) - min(counts.values())
                    self.assertLessEqual(
                        spread, 1,
                        f"{ft!r} answer counts not balanced (spread {spread}): {dict(counts)}",
                    )

    def test_every_fact_type_has_diverse_golds(self):
        for seed in SEEDS:
            golds = _golds_by_type(_items(seed))
            for ft in CATEGORICAL + OPEN_ENDED:
                with self.subTest(seed=seed, fact_type=ft):
                    self.assertGreater(len(set(golds[ft])), 1, f"{ft!r} collapsed to one gold")

    def test_balanced_fact_type_counts_preserved(self):
        counts = {ft: len(v) for ft, v in _golds_by_type(_items(0)).items()}
        self.assertEqual(len(counts), 5, f"expected 5 fact types, got {counts}")
        self.assertLessEqual(
            max(counts.values()) - min(counts.values()), 1,
            f"fact-type counts not balanced: {counts}",
        )

    def test_generation_is_deterministic(self):
        self.assertEqual(
            [it.fact.answer for it in _items(0)],
            [it.fact.answer for it in _items(0)],
            "same seed produced different golds",
        )

    def test_item_ids_unchanged_scheme(self):
        items = _items(0)
        self.assertEqual(items[0].item_id, "numerical_0000")
        self.assertEqual(items[1].item_id, "temporal_0001")
        self.assertEqual(items[2].item_id, "entity-attribute_0002")
        for it in items:
            self.assertTrue(it.item_id.startswith(it.fact.fact_type))
            self.assertRegex(it.item_id, r"_\d{4}$")

    def test_numerical_and_temporal_default_wording_unchanged(self):
        # numerical is untouched. temporal's DEFAULT (swap_candidates=False) is the
        # pre-repair wording; the question-order repair only takes effect via
        # generate_items — see tests/test_dataset_temporal_order.py.
        self.assertEqual(dataset.numerical(0), dataset.Fact(
            "numerical", "Person_0's employee ID is 100000.",
            "What is Person_0's employee ID?", "100000"))
        self.assertEqual(dataset.temporal(1), dataset.Fact(
            "temporal", "Person_1 arrived before Person_2.",
            "Who arrived first, Person_1 or Person_2?", "Person_1"))
        swapped = dataset.temporal(1, swap_candidates=True)
        self.assertEqual(swapped.question, "Who arrived first, Person_2 or Person_1?")
        self.assertEqual(swapped.answer, "Person_1")          # gold unchanged
        self.assertEqual(swapped.text, "Person_1 arrived before Person_2.")  # fact unchanged


class _StubTokenizer:
    """Whitespace tokenizer — enough for dataset.build_trajectory's length maths."""

    def __call__(self, text, **_):
        return {"input_ids": text.split()}

    def __len__(self):
        return 50000


class TestGeneratorPreservesPipelineInvariants(unittest.TestCase):
    """Every guarantee the run pipeline relies on still holds after the fix."""

    @classmethod
    def setUpClass(cls):
        cls.items = dataset.generate_items(n_items=60, seed=0, pool_size=POOL)
        cls.tok = _StubTokenizer()

    def test_collision_control_still_enforced(self):
        for it in self.items:
            dataset.assert_no_collision(it)  # raises on a leak

    def test_distractors_never_contain_the_gold(self):
        for it in self.items:
            for d in it.distractors:
                self.assertFalse(
                    dataset._leaks_answer(d.text, it.fact.answer),
                    f"{it.item_id}: distractor {d.text!r} leaks gold {it.fact.answer!r}",
                )

    def test_contradictory_supersedes_a_different_city(self):
        for it in self.items:
            if it.fact.fact_type != "contradictory":
                continue
            # "<p> lived in <old>. <p> now lives in <new>." — structure + old != new.
            self.assertRegex(it.fact.text, r"lived in .+\. .+ now lives in .+\.")
            old = it.fact.text.split("lived in ")[1].split(".")[0]
            self.assertNotEqual(old, it.fact.answer)

    def test_matched_trajectories_hold_the_target_constant(self):
        # Same item swept across compression pressure -> target sentence, question
        # and gold must be byte-identical at every level.
        for it in self.items[:15]:
            built = [
                dataset.build_trajectory(it, self.tok, tokens_after_target=p, seed=0)
                for p in (0, 5, 20, 80)
            ]
            self.assertEqual({b["gold"] for b in built}, {it.fact.answer})
            for b in built:
                self.assertIn(it.fact.text, b["prompt"])
                self.assertIn(it.fact.question, b["prompt"])
            realised = [b["tokens_after_target"] for b in built]
            self.assertEqual(realised, sorted(realised))


if __name__ == "__main__":
    unittest.main(verbosity=2)
