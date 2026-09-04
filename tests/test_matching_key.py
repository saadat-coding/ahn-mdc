"""Measurement-coordinate correction: design/matching keys use
`requested_tokens_after_target`, not the realised `tokens_after_target`.

Realised distractor-block length overshoots the requested level by whole facts,
and two different requested levels can land on the same realised count for a given
item. The design identity of a trial is what the grid asked for.

No GPU. `python -m unittest discover -s tests`.
"""

from __future__ import annotations

import sys
import unittest
from pathlib import Path

import pandas as pd

_ROOT = Path(__file__).resolve().parents[1]
if str(_ROOT / "src") not in sys.path:
    sys.path.insert(0, str(_ROOT / "src"))

from ahnexp import schema, stats


class TestValidateDedup(unittest.TestCase):
    def test_two_requested_levels_with_equal_realised_count_are_not_duplicates(self):
        df = schema.derive_memory_condition(pd.DataFrame([
            dict(item_id="x", architecture="a", seed=0, fact_type="numerical",
                 requested_tokens_after_target=128, tokens_after_target=150,
                 model_tokens_after_target=205, sliding_window=256, correct=1, abstained=0, confidence=0.5),
            dict(item_id="x", architecture="a", seed=0, fact_type="numerical",
                 requested_tokens_after_target=192, tokens_after_target=150,
                 model_tokens_after_target=205, sliding_window=256, correct=0, abstained=0, confidence=0.5),
        ]))
        schema.validate(df, needs=("core", "h1", "h3"))   # must not raise

    def test_identical_design_cells_are_flagged(self):
        df = schema.derive_memory_condition(pd.DataFrame([
            dict(item_id="x", architecture="a", seed=0, fact_type="numerical",
                 requested_tokens_after_target=128, tokens_after_target=150,
                 model_tokens_after_target=205, sliding_window=256, correct=1, abstained=0, confidence=0.5),
            dict(item_id="x", architecture="a", seed=0, fact_type="numerical",
                 requested_tokens_after_target=128, tokens_after_target=151,
                 model_tokens_after_target=206, sliding_window=256, correct=0, abstained=0, confidence=0.5),
        ]))
        with self.assertRaises(ValueError):
            schema.validate(df, needs=("core", "h1", "h3"))


class TestMatchedDesign(unittest.TestCase):
    def _rows(self, arm, requested_levels):
        out = []
        for lvl in requested_levels:
            out.append(dict(item_id="x", architecture=arm, seed=0, fact_type="numerical",
                            requested_tokens_after_target=lvl, tokens_after_target=300,
                            model_tokens_after_target=lvl + 55, sliding_window=256,
                            correct=1, abstained=0, confidence=0.5))
        return out

    def test_arms_matched_on_requested_level_even_when_realised_collides(self):
        df = schema.derive_memory_condition(pd.DataFrame(
            self._rows("a", [128, 192]) + self._rows("b", [128, 192])
        ))
        stats.assert_matched_design(df)   # must not raise

    def test_unmatched_requested_levels_are_caught(self):
        df = schema.derive_memory_condition(pd.DataFrame(
            self._rows("a", [128, 192]) + self._rows("b", [128, 256])
        ))
        with self.assertRaises(AssertionError):
            stats.assert_matched_design(df)


class TestPairedDifference(unittest.TestCase):
    def test_pairs_are_keyed_on_requested_level(self):
        rows = []
        for arm in ("deltanet", "gated_deltanet"):
            for seed in (0, 1, 2):
                for lvl in (512, 640):        # both recurrent, same realised count
                    rows.append(dict(item_id="x", architecture=arm, seed=seed, fact_type="numerical",
                                     requested_tokens_after_target=lvl, tokens_after_target=700,
                                     model_tokens_after_target=lvl + 55, sliding_window=256,
                                     memory_condition="recurrent_memory",
                                     correct=1 if arm == "deltanet" else 0,
                                     abstained=0, confidence=0.5))
        df = pd.DataFrame(rows)
        res = stats.paired_difference(df, "deltanet", "gated_deltanet")
        # 3 seeds x 2 requested levels = 6 pairs; keying on tokens_after_target (700)
        # would have collapsed them to 3.
        self.assertEqual(res["n_pairs"], 6)
        self.assertEqual(res["mean_difference"], 1.0)


if __name__ == "__main__":
    unittest.main(verbosity=2)
