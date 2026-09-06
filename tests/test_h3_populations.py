"""H3 confidence populations (Pilot Pass 2 hostile-audit issue #3 / #10).

Confidence on an abstention is confidence in emitting "I don't know"; confidence
on a malformed generation is confidence in a degeneration. Neither is confidence
in a factual answer. Factual ECE / Brier / CWR must default to the answered_valid
population (abstained == 0 AND malformed == 0) and must not silently include the
other two.

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

from ahnexp import h3_calibration, metrics, schema


def _frame():
    """20 answered-valid (well calibrated), 20 confident abstentions, 20 confident
    malformed. If abstentions/malformed leak into factual ECE it explodes."""
    rows = []
    def add(n, bucket, conf, corr):
        for i in range(n):
            rows.append(dict(
                item_id=f"{bucket}_{i}", architecture="mamba2", seed=0, fact_type="numerical",
                distractor_density="low", target_position="early",
                tokens_after_target=100, requested_tokens_after_target=100,
                model_tokens_after_target=150, intended_model_tokens_after_target=150,
                target_fact_tokens=12, context_tokens=300, sliding_window=256, n_new_tokens=3,
                correct=corr, abstained=int(bucket == "abst"), malformed=int(bucket == "malf"),
                confidence=conf, prediction="x", gold="x", scorer_version="1.0",
            ))
    add(20, "valid", 0.7, 1)       # calibrated: 0.7 conf, 100% correct-ish
    add(20, "abst", 0.95, 0)       # confident abstention -> would look "confidently wrong"
    add(20, "malf", 0.9, 0)        # confident malformed -> ditto
    return schema.derive_boundary_conditions(schema.derive_memory_condition(pd.DataFrame(rows)), strict=True)


class TestPopulationMask(unittest.TestCase):
    def setUp(self):
        self.df = _frame()

    def test_populations_are_mutually_exclusive_and_exhaustive(self):
        av = h3_calibration.population_mask(self.df, "answered_valid")
        ab = h3_calibration.population_mask(self.df, "abstained")
        mf = h3_calibration.population_mask(self.df, "malformed")
        self.assertEqual(int((av & ab).sum()), 0)
        self.assertEqual(int((av & mf).sum()), 0)
        self.assertEqual(int((ab & mf).sum()), 0)
        self.assertEqual(int((av | ab | mf).sum()), len(self.df))
        self.assertEqual(int(av.sum()), 20)


class TestFactualCalibrationExcludesByDefault(unittest.TestCase):
    def setUp(self):
        self.df = _frame()

    def test_by_condition_default_is_answered_valid(self):
        bc = h3_calibration.by_condition(self.df)
        self.assertEqual(bc["population"].unique().tolist(), ["answered_valid"])
        self.assertEqual(int(bc["n_population"].sum()), 20)
        self.assertLess(float(bc["ece"].iloc[0]), 0.35)         # calibrated
        self.assertLess(float(bc["cwr"].iloc[0]), 0.2)

    def test_by_condition_all_population_is_catastrophic(self):
        allp = h3_calibration.by_condition(self.df, population="all")
        self.assertGreater(float(allp["ece"].iloc[0]), 0.5)     # abstentions/malformed dominate
        self.assertGreater(float(allp["cwr"].iloc[0]), 0.6)

    def test_by_pressure_default_excludes_abstained_and_malformed(self):
        bp = h3_calibration.by_pressure(self.df)
        self.assertEqual(int(bp["n_population"].sum()), 20)
        self.assertEqual(int(bp["n_total"].sum()), 60)

    def test_by_fact_type_default_population(self):
        bf = h3_calibration.by_fact_type(self.df, recurrent_only=False)
        self.assertEqual(int(bf["n"].sum()), 20)

    def test_abstention_and_malformed_reported_separately(self):
        ac = h3_calibration.abstention_confidence(self.df)
        mr = h3_calibration.malformed_report(self.df)
        self.assertEqual(int(ac["n_abstained"].sum()), 20)
        self.assertAlmostEqual(float(ac["mean_confidence_on_abstention"].iloc[0]), 0.95, places=2)
        self.assertEqual(int(mr["n_malformed"].sum()), 20)

    def test_metrics_answered_valid_helper(self):
        self.assertEqual(len(metrics.answered_valid(self.df)), 20)


class TestBaselineAdjustedRequiresExplicitBaseline(unittest.TestCase):
    def test_scalar_dict_and_series_baselines(self):
        df = _frame()
        av = metrics.answered_valid(df)
        self.assertAlmostEqual(metrics.baseline_adjusted_accuracy(av, 0.0),
                               float(av["correct"].mean()), places=6)
        # temporal 0.5 must be passed explicitly; a dict baseline is honoured per type
        adj = metrics.baseline_adjusted_accuracy(av, {"numerical": 0.5})
        self.assertAlmostEqual(adj, (av["correct"].mean() - 0.5) / 0.5, places=6)

    def test_no_signature_that_reads_config_chance(self):
        import inspect
        src = inspect.getsource(metrics.baseline_adjusted_accuracy)
        self.assertNotIn("config.facts", src)
        self.assertNotIn('["chance"]', src)


if __name__ == "__main__":
    unittest.main(verbosity=2)
