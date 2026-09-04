"""Temporal nuisance-factor repair (open_decisions.md #7b).

Validation of the order-only repair (03e68f0) failed: because the fact is always
`Person_i arrived before Person_{i+1}` with `gold = Person_i`, the gold was the
lower-numbered candidate on 12/12 items, so a name-only "pick the lower number"
policy stayed a perfect shortcut.

Revised repair: `dataset.temporal(i, swap_candidates, earlier_is_higher)` toggles
(a) which identity arrived first / is the gold and (b) the gold's question
position. `generate_items` assigns the two from `_temporal_factor_plan` — a
density-stratified, seed-shuffled balanced plan — so the systematic Person-ID,
numeric-order, candidate-position and density shortcuts are removed. Temporal
distractor facts also alternate relation direction (local counter, no extra
shared-RNG draw); the shared distractor RNG stream and every non-temporal
distractor are unchanged.

Unchanged: fact form, `answer_hint`, the scorer, the benchmark-wide distractor
RNG, the density assignment.

No GPU. `python -m unittest discover -s tests`.
"""

from __future__ import annotations

import re
import sys
import unittest
import unittest.mock as mock
from collections import Counter, defaultdict
from pathlib import Path

_ROOT = Path(__file__).resolve().parents[1]
if str(_ROOT / "src") not in sys.path:
    sys.path.insert(0, str(_ROOT / "src"))

from ahnexp import dataset, evaluate

_NUM = re.compile(r"(?i)person[ _]?(\d+)")


def _temporal(items):
    return [it for it in items if it.fact.fact_type == "temporal"]


def _nums(text):
    return [int(x) for x in _NUM.findall(text)]


def _gold_n(it):
    return int(_NUM.search(it.fact.answer).group(1))


def _gold_is_higher(it):
    return _gold_n(it) == max(_nums(it.fact.question))


def _gold_is_first_listed(it):
    return _nums(it.fact.question)[0] == _gold_n(it)


def _relation_dir(text):
    a, b = _nums(text)
    return "hi_first" if a > b else "lo_first"


class TestTemporalGenerator(unittest.TestCase):
    def test_bare_call_defaults_are_pre_repair_wording(self):
        self.assertEqual(
            dataset.temporal(3),
            dataset.Fact("temporal", "Person_3 arrived before Person_4.",
                         "Who arrived first, Person_3 or Person_4?", "Person_3"))

    def test_swap_toggles_only_the_question_order(self):
        base, swap = dataset.temporal(3), dataset.temporal(3, swap_candidates=True)
        self.assertEqual((swap.text, swap.answer, swap.fact_type),
                         (base.text, base.answer, "temporal"))
        self.assertEqual(swap.question, "Who arrived first, Person_4 or Person_3?")

    def test_earlier_is_higher_toggles_direction_and_gold(self):
        f = dataset.temporal(3, earlier_is_higher=True)
        self.assertEqual((f.text, f.question, f.answer),
                         ("Person_4 arrived before Person_3.",
                          "Who arrived first, Person_4 or Person_3?", "Person_4"))
        g = dataset.temporal(3, swap_candidates=True, earlier_is_higher=True)
        self.assertEqual((g.text, g.question, g.answer),
                         ("Person_4 arrived before Person_3.",
                          "Who arrived first, Person_3 or Person_4?", "Person_4"))

    def test_construct_unchanged_one_before_relation(self):
        for eih in (False, True):
            for sw in (False, True):
                f = dataset.temporal(7, swap_candidates=sw, earlier_is_higher=eih)
                self.assertRegex(f.text, r"^Person_\d+ arrived before Person_\d+\.$")
                self.assertTrue(f.question.startswith("Who arrived first, "))
                self.assertIn(f.answer, {f"Person_{7}", f"Person_{8}"})
                self.assertEqual(sorted(_nums(f.question)), sorted(_nums(f.text)))


class TestNuisancePlan(unittest.TestCase):
    def test_deterministic_for_a_seed(self):
        self.assertEqual(dataset._temporal_factor_plan(40, 0),
                         dataset._temporal_factor_plan(40, 0))

    def test_different_seed_reshuffles_but_keeps_marginal_balance(self):
        p0 = dataset._temporal_factor_plan(40, 0)
        p1 = dataset._temporal_factor_plan(40, 1)
        self.assertNotEqual(p0, p1)
        for p in (p0, p1):
            self.assertEqual(sum(c[0] for c in p), 20)   # earlier_is_higher exactly 50%
            self.assertEqual(sum(c[1] for c in p), 20)   # swap_candidates exactly 50%

    def test_gold_direction_not_a_simple_slot_or_person_modulo_rule(self):
        eih = [c[0] for c in dataset._temporal_factor_plan(4000, seed=0)]
        for period in (2, 4, 8):
            for name, key in (("slot", lambda k: k), ("person", lambda k: 5 * k + 1)):
                by = defaultdict(list)
                for k, e in enumerate(eih):
                    by[key(k) % period].append(e)
                for r, es in by.items():
                    rate = sum(es) / len(es)
                    self.assertTrue(0.40 <= rate <= 0.60, f"{name}%{period}=={r}: {rate:.3f}")


class TestGeneratedTemporalItems(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.T16 = _temporal(dataset.generate_items(n_items=80, seed=0, pool_size=60))    # 16 temporal
        cls.T40 = _temporal(dataset.generate_items(n_items=200, seed=0, pool_size=60))   # 40 temporal

    def test_lower_higher_gold_exactly_50_50(self):
        for T in (self.T16, self.T40):
            self.assertEqual(sum(_gold_is_higher(it) for it in T), len(T) // 2)

    def test_first_second_gold_exactly_50_50(self):
        for T in (self.T16, self.T40):
            self.assertEqual(sum(_gold_is_first_listed(it) for it in T), len(T) // 2)

    def test_density_exactly_50_50(self):
        for T in (self.T16, self.T40):
            c = Counter(it.distractor_density for it in T)
            self.assertEqual(c["low"], c["high"])

    def test_2x2_balanced_within_each_density_and_full_2x2x2_when_N_div_8(self):
        for T in (self.T16, self.T40):
            key = lambda it: (_gold_is_higher(it), _gold_is_first_listed(it))
            for dens in ("low", "high"):
                q = Counter(key(it) for it in T if it.distractor_density == dens)
                self.assertEqual(len(q), 4)
                self.assertEqual(set(q.values()), {len(T) // 8})
            cells = Counter((*key(it), it.distractor_density) for it in T)
            self.assertEqual(len(cells), 8)
            self.assertEqual(set(cells.values()), {len(T) // 8})

    def test_deterministic_generation(self):
        again = _temporal(dataset.generate_items(n_items=80, seed=0, pool_size=60))
        self.assertEqual([(it.fact.text, it.fact.question) for it in self.T16],
                         [(it.fact.text, it.fact.question) for it in again])

    def test_fact_form_and_construct_unchanged(self):
        for it in self.T16:
            i = int(it.item_id.rsplit("_", 1)[1])
            self.assertIn(it.fact.text, {f"Person_{i} arrived before Person_{i + 1}.",
                                         f"Person_{i + 1} arrived before Person_{i}."})
            self.assertEqual(sorted(_nums(it.fact.question)), [i, i + 1])
            self.assertTrue(it.fact.question.startswith("Who arrived first, "))
            self.assertIn(it.fact.answer, {f"Person_{i}", f"Person_{i + 1}"})


class TestScorerUnchanged(unittest.TestCase):
    def test_gold_scored_correct_for_every_direction_x_order(self):
        for eih in (False, True):
            for sw in (False, True):
                f = dataset.temporal(11, swap_candidates=sw, earlier_is_higher=eih)
                gold_n = int(_NUM.search(f.answer).group(1))
                self.assertEqual(evaluate.score_row(f.answer, f.answer, "temporal")["correct"], 1)
                other = f"Person_{[n for n in _nums(f.question) if n != gold_n][0]}"
                r = evaluate.score_row(other, f.answer, "temporal")
                self.assertEqual((r["correct"], r["abstained"], r["malformed"]), (0, 0, 0))

    def test_echoing_the_question_is_still_malformed(self):
        out = evaluate.score_row("Person_12 or Person_11", "Person_11", "temporal")
        self.assertEqual(out["malformed"], 1)


class TestDistractorDirectionBalancing(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.items = dataset.generate_items(n_items=80, seed=0, pool_size=200)
        cls.tdist = [d for it in cls.items for d in it.distractors if d.fact_type == "temporal"]

    def test_both_temporal_relation_directions_occur_among_distractors(self):
        self.assertEqual({_relation_dir(d.text) for d in self.tdist}, {"lo_first", "hi_first"})

    def test_target_and_distractor_direction_distributions_comparable(self):
        T = _temporal(self.items)
        tgt_hi = sum(_relation_dir(it.fact.text) == "hi_first" for it in T) / len(T)
        dis_hi = sum(_relation_dir(d.text) == "hi_first" for d in self.tdist) / len(self.tdist)
        self.assertEqual(tgt_hi, 0.5)
        self.assertLess(abs(dis_hi - 0.5), 0.10)

    def test_no_distractor_determines_the_queried_temporal_relation(self):
        # Relational leakage check: a distractor leaks only if it names either
        # queried identity (and could therefore state / imply their order).
        for it in _temporal(dataset.generate_items(n_items=25, seed=0, pool_size=120)):
            queried = set(_nums(it.fact.question))          # {i, i+1}
            for d in it.distractors:
                self.assertEqual(queried & set(_nums(d.text)), set(),
                                 f"{it.item_id}: distractor {d.text!r} names a queried identity")
            dataset.assert_no_collision(it)


class TestSharedRNGAndNonTemporalDistractorsUnchanged(unittest.TestCase):
    """The only distractor-text difference the repair may introduce is the relation
    direction of temporal-typed distractor sentences. Non-temporal distractors, the
    sequence of Person ids drawn, and therefore the shared-RNG trajectory must be
    byte-identical to a run in which temporal distractors keep their old lower-first
    form."""

    def test_non_temporal_distractors_and_rng_stream_unchanged(self):
        real_temporal = dataset.temporal
        live = dataset.generate_items(n_items=80, seed=0, pool_size=40)
        with mock.patch.object(
            dataset, "temporal",
            lambda i, swap_candidates=False, earlier_is_higher=False:
                real_temporal(i, swap_candidates=swap_candidates, earlier_is_higher=False),
        ):
            base = dataset.generate_items(n_items=80, seed=0, pool_size=40)

        self.assertEqual(len(live), len(base))
        temporal_flips = 0
        for a, b in zip(live, base):
            self.assertEqual(a.item_id, b.item_id)
            self.assertEqual(a.fact, b.fact)                       # targets go through GENERATORS -> unpatched
            self.assertEqual(len(a.distractors), len(b.distractors))
            for da, db in zip(a.distractors, b.distractors):
                self.assertEqual(da.fact_type, db.fact_type)       # same generator chosen -> RNG stream intact
                self.assertEqual(sorted(_nums(da.text)), sorted(_nums(db.text)))  # same ids -> cursor intact
                if da.fact_type == "temporal":
                    temporal_flips += da.text != db.text
                else:
                    self.assertEqual(da.text, db.text)             # non-temporal: byte-identical
                    self.assertEqual((da.question, da.answer), (db.question, db.answer))
        self.assertGreater(temporal_flips, 0)                      # the repair does flip some directions


if __name__ == "__main__":
    unittest.main(verbosity=2)
