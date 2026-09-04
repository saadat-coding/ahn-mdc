"""Temporal question candidate-order repair (open_decisions.md #7b).

The forced-baseline diagnostic found the old `temporal` wording put the gold
(the earlier arriver) first in every question, so "pick the first-listed name"
scored 100% with zero reasoning or memory (target-removed forced accuracy
100%, 36/36 first-listed).

Repair: `dataset.temporal(i, swap_candidates=...)` toggles the order the two
candidates are listed in the question, and `generate_items` drives it from
`(slot // 2) % 2` so the order is balanced 50/50 and independent of both the
gold and `distractor_density` (which is `slot % 2` for temporal).

Unchanged: fact text, gold, `answer_hint`, the scorer, distractor generation.

No GPU. `python -m unittest discover -s tests`.
"""

from __future__ import annotations

import re
import sys
import unittest
from collections import Counter
from pathlib import Path

_ROOT = Path(__file__).resolve().parents[1]
if str(_ROOT / "src") not in sys.path:
    sys.path.insert(0, str(_ROOT / "src"))

from ahnexp import dataset, evaluate

_PERSON = re.compile(r"Person_\d+")


def _temporal(items):
    return [it for it in items if it.fact.fact_type == "temporal"]


def _idx(item):
    return int(item.item_id.rsplit("_", 1)[1])


def _gold_is_first_listed(item):
    names = _PERSON.findall(item.fact.question)
    return names[0] == item.fact.answer


class TestTemporalGenerator(unittest.TestCase):
    def test_bare_call_default_is_pre_repair_wording(self):
        self.assertEqual(
            dataset.temporal(3),
            dataset.Fact("temporal", "Person_3 arrived before Person_4.",
                         "Who arrived first, Person_3 or Person_4?", "Person_3"))

    def test_swap_toggles_only_the_question_order(self):
        base = dataset.temporal(3)
        swap = dataset.temporal(3, swap_candidates=True)
        self.assertEqual(swap.text, base.text)            # fact unchanged
        self.assertEqual(swap.answer, base.answer)        # gold unchanged
        self.assertEqual(swap.fact_type, "temporal")
        self.assertEqual(swap.question, "Who arrived first, Person_4 or Person_3?")

    def test_gold_is_always_the_earlier_person_regardless_of_swap(self):
        for i in (0, 1, 7, 42, 137):
            self.assertEqual(dataset.temporal(i).answer, f"Person_{i}")
            self.assertEqual(dataset.temporal(i, swap_candidates=True).answer, f"Person_{i}")


class TestGeneratedTemporalItems(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.items = dataset.generate_items(n_items=200, seed=0, pool_size=200)
        cls.temporal = _temporal(cls.items)

    def test_fact_text_and_gold_unchanged(self):
        for it in self.temporal:
            i = _idx(it)
            self.assertEqual(it.fact.text, f"Person_{i} arrived before Person_{i + 1}.")
            self.assertEqual(it.fact.answer, f"Person_{i}")

    def test_question_names_both_candidates(self):
        for it in self.temporal:
            i = _idx(it)
            names = _PERSON.findall(it.fact.question)
            self.assertEqual(sorted(names), sorted([f"Person_{i}", f"Person_{i + 1}"]))
            self.assertTrue(it.fact.question.startswith("Who arrived first, "))

    def test_candidate_order_balanced(self):
        first = sum(_gold_is_first_listed(it) for it in self.temporal)
        n = len(self.temporal)
        # (slot // 2) % 2 is exactly 50/50 for n divisible by 4; allow a small band
        self.assertAlmostEqual(first / n, 0.5, delta=0.15,
                               msg=f"gold first-listed {first}/{n}")

    def test_candidate_order_independent_of_distractor_density(self):
        cells = Counter((it.distractor_density, _gold_is_first_listed(it)) for it in self.temporal)
        for density in ("low", "high"):
            f, s = cells[(density, True)], cells[(density, False)]
            self.assertGreater(f + s, 0)
            self.assertAlmostEqual(f / (f + s), 0.5, delta=0.2,
                                   msg=f"{density}: first={f} second={s}")

    def test_candidate_order_deterministic(self):
        again = _temporal(dataset.generate_items(n_items=200, seed=0, pool_size=200))
        self.assertEqual([it.fact.question for it in self.temporal],
                         [it.fact.question for it in again])

    def test_both_orders_actually_occur(self):
        firsts = {_gold_is_first_listed(it) for it in self.temporal}
        self.assertEqual(firsts, {True, False})


class TestScorerStillOrderAgnostic(unittest.TestCase):
    def test_gold_scored_correct_whichever_order_the_question_used(self):
        for swap in (False, True):
            f = dataset.temporal(11, swap_candidates=swap)
            self.assertEqual(evaluate.score_row(f.answer, f.answer, "temporal")["correct"], 1)
            self.assertEqual(evaluate.score_row("person_11", f.answer, "temporal")["correct"], 1)
            self.assertEqual(evaluate.score_row("Person 11", f.answer, "temporal")["correct"], 1)
            # the other candidate is wrong, not malformed
            other = evaluate.score_row("Person_12", f.answer, "temporal")
            self.assertEqual((other["correct"], other["abstained"], other["malformed"]), (0, 0, 0))

    def test_echoing_the_swapped_question_is_still_malformed(self):
        out = evaluate.score_row("Person_12 or Person_11", "Person_11", "temporal")
        self.assertEqual(out["malformed"], 1)


class TestDistractorGenerationUnaffected(unittest.TestCase):
    def test_temporal_distractors_keep_the_fact_form_and_no_swap(self):
        items = dataset.generate_items(n_items=15, seed=0, pool_size=300)
        for it in _temporal(items):
            for d in it.distractors:
                if d.fact_type == "temporal":
                    self.assertRegex(d.text, r"^Person_\d+ arrived before Person_\d+\.$")
            dataset.assert_no_collision(it)  # raises on a leak


if __name__ == "__main__":
    unittest.main(verbosity=2)
