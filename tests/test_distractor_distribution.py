"""Regression tests — distractor pools must stay unbiased.

Guards two properties of ``ahnexp.dataset._distractor_pool`` on the production path:

1. Categorical distractor *values* (colour / company / city) are ~uniform in
   aggregate, and no value is substantially overrepresented. This holds only
   because target golds are balanced; if target balancing regresses, the
   per-target collision filter stops being symmetric and these fail.
2. Collision control still removes the target's own gold from its same-type
   distractors (0 self-leaks).

Read-only. Small pool keeps the suite fast; distractor draws are i.i.d. so the
distribution shape does not depend on pool_size.

    python -m unittest discover -s tests
"""

from __future__ import annotations

import sys
import unittest
from collections import Counter, defaultdict
from pathlib import Path

_ROOT = Path(__file__).resolve().parents[1]
if str(_ROOT / "src") not in sys.path:
    sys.path.insert(0, str(_ROOT / "src"))

from ahnexp import dataset

SEEDS = (0, 1, 2)
N_ITEMS = 500
POOL = 500

SPACES = {
    "entity-attribute": dataset.COLORS,
    "multi-hop": dataset.COMPANIES,
    "contradictory": dataset.CITIES_TO,
}
MAX_DEV_PTS = 3.0      # max |observed% - uniform%| tolerated in aggregate
MAX_CHI2 = 40.0        # df=4; the constant-gold bug produced chi2 in the thousands


def _old_city(text: str) -> str:
    return text.split(" lived in ", 1)[1].split(".", 1)[0]


class _Tally:
    def __init__(self, seed):
        self.items = dataset.generate_items(n_items=N_ITEMS, seed=seed, pool_size=POOL)
        self.value_all = defaultdict(Counter)          # dtype -> Counter(value)
        self.oldcity_all = Counter()
        self.value_by_gold = defaultdict(lambda: defaultdict(Counter))  # dtype -> gold -> Counter
        self.selfleak = Counter()
        self.same_type = Counter()
        self.gold_density = defaultdict(Counter)        # dtype -> Counter((gold, density))
        for it in self.items:
            tt = it.fact.fact_type
            self.gold_density[tt][(it.fact.answer, it.distractor_density)] += 1
            for d in it.distractors:
                dt = d.fact_type
                if dt == tt:
                    self.same_type[tt] += 1
                if dt in SPACES:
                    self.value_all[dt][d.answer] += 1
                    if dt == "contradictory":
                        self.oldcity_all[_old_city(d.text)] += 1
                    if dt == tt:
                        self.value_by_gold[dt][it.fact.answer][d.answer] += 1
                        if d.answer == it.fact.answer:
                            self.selfleak[tt] += 1


def _chi2_dev(counter: Counter, space):
    total = sum(counter.get(k, 0) for k in space)
    exp = total / len(space)
    chi2 = sum((counter.get(k, 0) - exp) ** 2 / exp for k in space)
    dev = max(abs(100 * counter.get(k, 0) / total - 100 / len(space)) for k in space)
    return chi2, dev


class TestDistractorDistribution(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        cls.tallies = {s: _Tally(s) for s in SEEDS}

    def test_categorical_distractor_values_uniform_in_aggregate(self):
        for s, t in self.tallies.items():
            for dt, space in SPACES.items():
                with self.subTest(seed=s, distractor_type=dt):
                    chi2, dev = _chi2_dev(t.value_all[dt], space)
                    self.assertLess(chi2, MAX_CHI2, f"{dt} chi2={chi2:.1f}: {dict(t.value_all[dt])}")
                    self.assertLessEqual(dev, MAX_DEV_PTS, f"{dt} max deviation {dev:.2f} pts")

    def test_contradictory_old_city_uniform_in_aggregate(self):
        for s, t in self.tallies.items():
            with self.subTest(seed=s):
                chi2, dev = _chi2_dev(t.oldcity_all, dataset.CITIES_FROM)
                self.assertLess(chi2, MAX_CHI2, f"old-city chi2={chi2:.1f}: {dict(t.oldcity_all)}")
                self.assertLessEqual(dev, MAX_DEV_PTS)

    def test_no_categorical_distractor_value_overrepresented(self):
        for s, t in self.tallies.items():
            for dt, space in SPACES.items():
                counts = t.value_all[dt]
                total = sum(counts.values())
                for v in space:
                    with self.subTest(seed=s, distractor_type=dt, value=v):
                        share = counts.get(v, 0) / total
                        self.assertLessEqual(
                            share, 1.25 / len(space),
                            f"{dt} value {v!r} holds {share:.1%} (> 1.25x uniform)",
                        )

    def test_target_gold_not_correlated_with_distractor_distribution(self):
        # Off-diagonal (gold != distractor value) rows must be ~uniform, and every
        # value's column total ~equal -> answer balancing did not skew the pool.
        for s, t in self.tallies.items():
            for dt, space in SPACES.items():
                col = Counter()
                for gold in space:
                    row = t.value_by_gold[dt][gold]
                    off = [row.get(v, 0) for v in space if v != gold]
                    tot = sum(off) or 1
                    with self.subTest(seed=s, distractor_type=dt, gold=gold):
                        dev = max(abs(100 * c / tot - 100 / (len(space) - 1)) for c in off)
                        self.assertLessEqual(dev, 4.0, f"{dt} gold={gold} off-diagonal skew {dev:.1f} pts")
                    for v in space:
                        col[v] += row.get(v, 0)
                grand = sum(col.values())
                dev = max(abs(100 * col[v] / grand - 100 / len(space)) for v in space)
                with self.subTest(seed=s, distractor_type=dt, check="column totals"):
                    self.assertLessEqual(dev, MAX_DEV_PTS, f"{dt} column-total skew {dev:.1f} pts")

    def test_collision_control_excludes_gold_from_same_type_distractors(self):
        for s, t in self.tallies.items():
            for ft in SPACES:
                with self.subTest(seed=s, fact_type=ft):
                    self.assertEqual(
                        t.selfleak[ft], 0,
                        f"{t.selfleak[ft]} / {t.same_type[ft]} same-type distractors carry the target gold",
                    )

    def test_target_gold_independent_of_density(self):
        for s, t in self.tallies.items():
            for ft in SPACES:
                cells = t.gold_density[ft]
                golds = {g for g, _ in cells}
                for g in golds:
                    with self.subTest(seed=s, fact_type=ft, gold=g):
                        lo, hi = cells.get((g, "low"), 0), cells.get((g, "high"), 0)
                        self.assertLessEqual(abs(lo - hi), 2, f"{ft} gold={g}: {lo} low vs {hi} high")


if __name__ == "__main__":
    unittest.main(verbosity=2)
