"""Canonical scientific pressure grouping (Pilot Pass 2 hostile-audit issue #1).

Per-fact-type calibration means `requested_tokens_after_target` has many more
distinct values than the scientific grid has levels. `schema.pressure_group_key`
must collapse a per-type-calibrated frame back to one balanced cell per
`intended_model_tokens_after_target`, so K / width / monotonicity are computed on
the balanced grid, not on fragmented small groups.

No GPU. `python -m unittest discover -s tests`.
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
_INTENDED = [170, 200, 240, 300, 640]


def _calibrated_frame(arms=("deltanet", "gated_deltanet", "mamba2", "transformer"),
                      n_items_per_type=8, seed=0):
    """Model-tat-targeted grid with a DIFFERENT `requested` per fact type per target
    (so requested has ~5x11 distinct values), realised model_tat ~= intended."""
    rng = np.random.default_rng(seed)
    per_type_offset = {t: 55 + 4 * k for k, t in enumerate(_TYPES)}   # 55..71 tokens
    rows = []
    for arm in arms:
        for ti, ft in enumerate(_TYPES):
            for it in range(n_items_per_type):
                for target in _INTENDED:
                    requested = target - per_type_offset[ft]          # per-type calibration
                    model_tat = int(target + rng.integers(-6, 7))     # realised ~= intended
                    acc_p = 1.0 if model_tat < 210 else max(0.0, 1.0 - (model_tat - 210) / 60)
                    answered = rng.random() > (0.15 if model_tat < 230 else 0.85)
                    rows.append(dict(
                        item_id=f"{ft}_{ti*n_items_per_type+it:04d}", architecture=arm, seed=0,
                        fact_type=ft, distractor_density="high" if it % 2 else "low",
                        target_position="early",
                        tokens_after_target=requested + 4, requested_tokens_after_target=int(requested),
                        model_tokens_after_target=model_tat,
                        intended_model_tokens_after_target=int(target),
                        target_fact_tokens=12, context_tokens=200 + model_tat, sliding_window=256,
                        n_new_tokens=3, correct=int(answered and rng.random() < acc_p),
                        abstained=int(not answered), malformed=0, answer_canonical="x",
                        confidence=0.6, prediction="x", gold="x", scorer_version="1.0",
                    ))
    df = schema.derive_memory_condition(pd.DataFrame(rows))
    return schema.derive_boundary_conditions(df, strict=True)


class TestGroupKeySelection(unittest.TestCase):
    def test_intended_target_wins_when_present(self):
        df = _calibrated_frame()
        self.assertEqual(schema.pressure_group_key(df), "intended_model_tokens_after_target")
        self.assertGreater(df["requested_tokens_after_target"].nunique(), len(_INTENDED))

    def test_requested_fallback_when_no_intended(self):
        df = _calibrated_frame().drop(columns=["intended_model_tokens_after_target"])
        self.assertEqual(schema.pressure_group_key(df), "requested_tokens_after_target")

    def test_tokens_after_target_legacy_fallback(self):
        df = _calibrated_frame().drop(columns=["intended_model_tokens_after_target",
                                               "requested_tokens_after_target"])
        self.assertEqual(schema.pressure_group_key(df), "tokens_after_target")


class TestBalancedCollapse(unittest.TestCase):
    def setUp(self):
        self.df = _calibrated_frame()

    def test_knees_aggregate_one_cell_per_intended_target(self):
        kn = h2_threshold.knees(self.df)
        self.assertTrue((kn["n_levels"] == len(_INTENDED)).all(),
                        f"expected {len(_INTENDED)} balanced levels, got {kn['n_levels'].tolist()}")

    def test_knees_would_fragment_on_requested(self):
        # drop `intended` -> group_key falls to `requested` -> many more levels
        frag = h2_threshold.knees(self.df.drop(columns=["intended_model_tokens_after_target"]))
        self.assertTrue((frag["n_levels"] > len(_INTENDED)).all())

    def test_h1_curves_group_on_intended(self):
        c = h1_degradation.curves(self.df, by="fact_type")
        for _, levels in c.groupby("fact_type")["pressure_group"].apply(list).items():
            self.assertEqual(sorted(set(levels)), _INTENDED)

    def test_h3_by_pressure_groups_on_intended(self):
        bp = h3_calibration.by_pressure(self.df)
        self.assertEqual(sorted(bp["pressure_group"]), _INTENDED)

    def test_curve_x_is_realised_model_tat(self):
        c = h2_threshold.curves(self.df)
        for _, r in c.iterrows():
            self.assertAlmostEqual(r["pressure_windows"], r["model_tokens_after_target"] / 256.0, places=6)
            # realised model-tat mean within a few tokens of the intended target
            self.assertLess(abs(r["model_tokens_after_target"] - r["pressure_group"]), 10)


if __name__ == "__main__":
    unittest.main(verbosity=2)
