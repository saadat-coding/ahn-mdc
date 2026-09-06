"""Measurement-coordinate correction: the H1/H2/H3 curves and the H2 threshold
split key on the canonical quantities.

  * scientific group key    = schema.pressure_group_key (intended target -> requested
                              -> tokens_after_target); one balanced cell per level
  * scientific x-coordinate  = model_tokens_after_target

Frames here carry `requested_tokens_after_target` but not `intended_model_tokens_
after_target`, so `pressure_group_key` falls back to `requested_tokens_after_target`
and behaviour is unchanged. Legacy frames without either fall back to
`tokens_after_target`. No GPU. `python -m unittest discover -s tests`.
"""

from __future__ import annotations

import sys
import unittest
from pathlib import Path

import numpy as np
import pandas as pd

_ROOT = Path(__file__).resolve().parents[1]
if str(_ROOT / "src") not in sys.path:
    sys.path.insert(0, str(_ROOT / "src"))

from ahnexp import h1_degradation, h2_threshold, h3_calibration, schema

_TYPES = ["numerical", "temporal", "entity-attribute", "multi-hop", "contradictory"]


def _frame(arms=("deltanet", "gated_deltanet"), levels=(0, 128, 256, 512, 1024), seeds=(0, 1, 2)):
    """Matched multi-arm frame. model_tokens_after_target = requested + a per-item
    offset (45..75) so a single requested level straddles the 256 boundary."""
    rng = np.random.default_rng(0)
    rows = []
    for arm in arms:
        for lvl in levels:
            for seed in seeds:
                for i in range(6):
                    ft = _TYPES[i % len(_TYPES)]
                    offset = 45 + (i * 6)                      # 45..75, item-specific, arm-invariant
                    model_tat = lvl + offset
                    correct = int(rng.random() < (0.85 if model_tat < 256 else 0.15))
                    rows.append(dict(
                        item_id=f"{ft}_{i:03d}", architecture=arm, seed=seed, fact_type=ft,
                        distractor_density="high" if i % 2 else "low", target_position="early",
                        tokens_after_target=lvl + 5, requested_tokens_after_target=lvl,
                        model_tokens_after_target=model_tat, target_fact_tokens=12,
                        context_tokens=200 + model_tat, sliding_window=256, n_new_tokens=3,
                        correct=correct, abstained=0, malformed=0, confidence=0.6,
                        prediction="x", gold="x",
                    ))
    df = schema.derive_memory_condition(pd.DataFrame(rows))
    return schema.derive_boundary_conditions(df, strict=True)


class TestH2Curves(unittest.TestCase):
    def setUp(self):
        self.df = _frame()

    def test_one_row_per_arm_and_requested_level_including_zero(self):
        c = h2_threshold.curves(self.df)
        self.assertEqual(len(c), 2 * 5)
        self.assertEqual(sorted(c["requested_tokens_after_target"].unique()), [0, 128, 256, 512, 1024])

    def test_pressure_windows_is_model_tat_not_distractor_tokens(self):
        c = h2_threshold.curves(self.df)
        for _, r in c.iterrows():
            self.assertAlmostEqual(r["pressure_windows"], r["model_tokens_after_target"] / 256.0, places=6)
            # model_tat exceeds the distractor-block count by the fixed question block
            self.assertGreater(r["model_tokens_after_target"], r["tokens_after_target"])

    def test_boundary_level_is_retained_on_the_continuous_curve(self):
        c = h2_threshold.curves(self.df)
        # requested 128 -> model_tat 173..203, all still "exact" by the binary rule,
        # but the row is present and carries its realised coordinate
        row = c[(c["architecture"] == "deltanet") & (c["requested_tokens_after_target"] == 128)]
        self.assertEqual(len(row), 1)
        self.assertTrue(170 <= row.iloc[0]["model_tokens_after_target"] <= 205)


class TestH2DropSplitsOnModelTat(unittest.TestCase):
    def test_split_follows_model_tokens_after_target_not_tokens_after_target(self):
        # Group L: tokens_after_target = 800 (>= T) but model_tat = 700 (< T=768).
        # Group H: tokens_after_target = 730 (<  T) but model_tat = 900 (>= T).
        # Keying on tokens_after_target would put L above and H below; the corrected
        # code keys on model_tat and does the opposite.
        rows = []
        for seed in (0, 1, 2):
            for tag, tat, mtat, corr in (("L", 800, 700, 1), ("H", 730, 900, 0)):
                for i in range(8):
                    rows.append(dict(
                        item_id=f"{tag}_{i:03d}", architecture="deltanet", seed=seed,
                        fact_type="numerical", distractor_density="low", target_position="early",
                        tokens_after_target=tat, requested_tokens_after_target=mtat - 55,
                        model_tokens_after_target=mtat, target_fact_tokens=12,
                        context_tokens=mtat + 200, sliding_window=256, n_new_tokens=3,
                        correct=corr, abstained=0, malformed=0, confidence=0.5,
                        prediction="x", gold="x",
                    ))
        df = schema.derive_memory_condition(pd.DataFrame(rows))
        out = h2_threshold.drop_at_threshold(df, threshold_tokens=768)
        r = out.iloc[0]
        self.assertEqual(int(r["n_below"]), 24)   # group L (model_tat 700)
        self.assertEqual(int(r["n_above"]), 24)   # group H (model_tat 900)
        self.assertEqual(r["acc_below_T"], 1.0)   # L is the correct group
        self.assertEqual(r["acc_above_T"], 0.0)


class TestH1AndH3GroupOnRequested(unittest.TestCase):
    def setUp(self):
        self.df = _frame(arms=("gated_deltanet",))

    def test_h1_curves_group_on_requested_level(self):
        c = h1_degradation.curves(self.df, by="fact_type")
        self.assertIn("requested_tokens_after_target", c.columns)
        self.assertIn("model_tokens_after_target", c.columns)
        per_type_levels = c.groupby("fact_type")["requested_tokens_after_target"].apply(list)
        for levels in per_type_levels:
            self.assertEqual(sorted(levels), [0, 128, 256, 512, 1024])

    def test_h3_by_pressure_groups_on_the_scientific_pressure_level(self):
        bp = h3_calibration.by_pressure(self.df)   # frame has no intended target -> groups on requested
        self.assertEqual(sorted(bp["pressure_group"]), [0, 128, 256, 512, 1024])
        for _, r in bp.iterrows():
            self.assertAlmostEqual(r["pressure_windows"], r["model_tokens_after_target"] / 256.0, places=6)


class TestLegacyFallback(unittest.TestCase):
    def test_frame_without_requested_or_model_columns_still_flows(self):
        rows = []
        for lvl in (0, 128, 512, 1024):
            for seed in (0, 1, 2):
                for i in range(4):
                    rows.append(dict(
                        item_id=f"n_{i}", architecture="deltanet", seed=seed, fact_type="numerical",
                        tokens_after_target=lvl, sliding_window=256,
                        correct=int(lvl < 256), abstained=0, confidence=0.5,
                    ))
        df = schema.derive_memory_condition(pd.DataFrame(rows))
        self.assertEqual(schema.pressure_design_key(df), "tokens_after_target")
        self.assertEqual(schema.pressure_coordinate(df), "tokens_after_target")
        c = h1_degradation.curves(df, by="fact_type")   # must not raise
        self.assertEqual(sorted(c["requested_tokens_after_target"]), [0, 128, 512, 1024])


if __name__ == "__main__":
    unittest.main(verbosity=2)
