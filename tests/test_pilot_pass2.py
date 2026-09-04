"""Pilot Pass 2 — pressure plan wiring, calibration verification, hard gates,
scientific warnings, knee estimator (open_decisions.md #18).

No GPU. `python -m unittest discover -s tests`.
"""

from __future__ import annotations

import json
import sys
import unittest
from pathlib import Path

import numpy as np
import pandas as pd

_ROOT = Path(__file__).resolve().parents[1]
if str(_ROOT / "src") not in sys.path:
    sys.path.insert(0, str(_ROOT / "src"))

from ahnexp import config, dataset, evaluate, h2_threshold, pilot_pass2, schema, stats


class _PlainTokenizer:
    def __call__(self, text, **_):
        return {"input_ids": text.split()}

    def __len__(self):
        return 50_000


# ---------------------------------------------------------------------------
# calibration artifact (committed)
# ---------------------------------------------------------------------------

class TestCommittedCalibration(unittest.TestCase):
    def test_calibration_covers_every_type_and_target(self):
        calib = config.load_pass2_calibration()
        p2 = config.pilot_pass2()
        types = list(dataset.GENERATORS)
        self.assertEqual(set(calib["per_type"]), set(types))
        for entry in calib["per_type"].values():
            got = sorted(int(t) for t in entry["requested_by_target"])
            self.assertEqual(got, sorted(int(t) for t in p2["target_model_tat"]))

    def test_dry_run_summary_recorded_a_pass(self):
        out = _ROOT / config.experiment()["outputs"]["pass2_dryrun"]
        if not out.is_file():
            self.skipTest("dry-run summary not present")
        summ = json.loads(out.read_text())
        self.assertTrue(summ["transition_band_ok"])
        self.assertTrue(summ["trajectory_nesting_ok"])


# ---------------------------------------------------------------------------
# pressure plan wiring
# ---------------------------------------------------------------------------

class TestPressurePlan(unittest.TestCase):
    def test_build_pressure_plan_shape(self):
        plan = pilot_pass2.build_pressure_plan(config.load_pass2_calibration())
        self.assertEqual(set(plan), set(dataset.GENERATORS))
        for per_type in plan.values():
            self.assertTrue(all(isinstance(k, int) and isinstance(v, int) for k, v in per_type.items()))

    def test_trajectory_schedule_uses_per_type_requested_and_records_intended(self):
        items = dataset.generate_items(10, seed=0, pool_size=200)
        plan = {ft: {170: 90, 240: 150, 640: 560} for ft in dataset.GENERATORS}
        for it in items:
            sched = evaluate._trajectory_schedule(it, 256, "pilot_pass2", plan)
            self.assertEqual([intended for _, intended in sched], [170, 240, 640])
            self.assertEqual([req for req, _ in sched], [90, 150, 560])

    def test_trajectory_schedule_without_plan_is_the_window_grid(self):
        it = dataset.generate_items(5, seed=0, pool_size=120)[0]
        sched = evaluate._trajectory_schedule(it, 256, "mini", None)
        self.assertEqual([intended for _, intended in sched], [None, None, None, None])
        self.assertEqual([req for req, _ in sched], evaluate.pressure_levels(256, "mini"))

    def test_run_grid_rejects_plan_with_length_matched(self):
        with self.assertRaises(ValueError):
            evaluate.run_grid([], None, mode="pilot_pass2", length_matched=True,
                              pressure_plan={"numerical": {170: 90}})


# ---------------------------------------------------------------------------
# no-model grid verification
# ---------------------------------------------------------------------------

class TestVerifyGrid(unittest.TestCase):
    def setUp(self):
        self.items = dataset.generate_items(10, seed=0, pool_size=400)
        self.plan = {ft: {60: 0, 120: 60, 300: 240} for ft in dataset.GENERATORS}

    def test_every_item_target_is_reported_and_nested(self):
        v = pilot_pass2.verify_grid(self.items, _PlainTokenizer(), self.plan, seed=0)
        self.assertEqual(len(v), len(self.items) * 3)
        self.assertTrue(v["nested_ok"].all())
        self.assertEqual(sorted(v["intended_model_tat"].unique()), [60, 120, 300])

    def test_calibration_report_flags_tolerance(self):
        v = pilot_pass2.verify_grid(self.items, _PlainTokenizer(), self.plan, seed=0)
        rep = pilot_pass2.calibration_report(v, config.pilot_pass2()["bands"])
        self.assertIn("within_tolerance", rep.columns)
        self.assertIn("median_error", rep.columns)


# ---------------------------------------------------------------------------
# hard plumbing gates
# ---------------------------------------------------------------------------

def _good_frame():
    p2 = config.pilot_pass2()
    calib = config.load_pass2_calibration()
    items = dataset.generate_items(config.run_mode("pilot_pass2")["n_items"], seed=0)
    rng = np.random.default_rng(0)
    rows = []
    for arm in p2["arms"]:
        for it in items:
            for target in p2["target_model_tat"]:
                req = int(calib["per_type"][it.fact.fact_type]["requested_by_target"][str(target)])
                mtat = int(target)
                rows.append(dict(
                    item_id=it.item_id, architecture=arm, seed=0, fact_type=it.fact.fact_type,
                    distractor_density=it.distractor_density, target_position="early",
                    tokens_after_target=req + 4, requested_tokens_after_target=req,
                    model_tokens_after_target=mtat, intended_model_tokens_after_target=int(target),
                    target_fact_tokens=12, context_tokens=220 + mtat, sliding_window=256,
                    n_new_tokens=3, correct=int(mtat < 230), abstained=int(mtat >= 230),
                    malformed=0, answer_canonical="x", confidence=0.6,
                    prediction="x", gold="x", scorer_version=evaluate.SCORER_VERSION,
                ))
    df = schema.derive_boundary_conditions(schema.derive_memory_condition(pd.DataFrame(rows)), strict=True)
    return df, items, calib


class TestPlumbingGates(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.df, cls.items, cls.calib = _good_frame()

    def test_clean_frame_passes_every_hard_gate(self):
        gates = pilot_pass2.plumbing_gates(self.df, self.items, self.calib)
        self.assertTrue(pilot_pass2.blocking(gates).empty, gates.to_string())

    def test_missing_trials_fail(self):
        broken = self.df[self.df["intended_model_tokens_after_target"] != 640]
        gates = pilot_pass2.plumbing_gates(broken, self.items, self.calib)
        self.assertIn("trial_count", set(pilot_pass2.blocking(gates)["gate"]))
        self.assertIn("all_targets_present", set(pilot_pass2.blocking(gates)["gate"]))

    def test_duplicate_design_cell_fails(self):
        dup = pd.concat([self.df, self.df.iloc[[0]]], ignore_index=True)
        gates = pilot_pass2.plumbing_gates(dup, self.items, self.calib)
        self.assertIn("no_duplicate_cells", set(pilot_pass2.blocking(gates)["gate"]))

    def test_unmatched_arm_fails(self):
        drop = self.df[~((self.df["architecture"] == "mamba2")
                         & (self.df["item_id"] == self.df["item_id"].iloc[0]))]
        gates = pilot_pass2.plumbing_gates(drop, self.items, self.calib)
        self.assertIn("matched_design", set(pilot_pass2.blocking(gates)["gate"]))

    def test_wrong_scorer_version_fails(self):
        bad = self.df.copy()
        bad.loc[bad.index[:5], "scorer_version"] = "9.9"
        gates = pilot_pass2.plumbing_gates(bad, self.items, self.calib)
        self.assertIn("scorer_version", set(pilot_pass2.blocking(gates)["gate"]))

    def test_missing_provenance_column_fails(self):
        bad = self.df.drop(columns=["target_fact_tokens"])
        gates = pilot_pass2.plumbing_gates(bad, self.items, self.calib)
        self.assertIn("provenance:target_fact_tokens", set(pilot_pass2.blocking(gates)["gate"]))

    def test_null_provenance_value_fails(self):
        bad = self.df.copy()
        bad.loc[bad.index[0], "n_new_tokens"] = np.nan
        gates = pilot_pass2.plumbing_gates(bad, self.items, self.calib)
        self.assertIn("provenance:n_new_tokens", set(pilot_pass2.blocking(gates)["gate"]))


class TestScientificWarningsNeverBlock(unittest.TestCase):
    def test_warnings_are_advisory_only(self):
        df, items, calib = _good_frame()
        warns = pilot_pass2.scientific_warnings(df)
        self.assertIsInstance(warns, pd.DataFrame)
        # low deep-recurrent accuracy is present in the fabricated frame but is a
        # warning, not a gate
        gates = pilot_pass2.plumbing_gates(df, items, calib)
        self.assertTrue(pilot_pass2.blocking(gates).empty)


# ---------------------------------------------------------------------------
# isotonic + knee estimator
# ---------------------------------------------------------------------------

class TestIsotonic(unittest.TestCase):
    def test_non_increasing_fit_is_monotone_and_close(self):
        y = np.array([1.0, 0.9, 0.95, 0.4, 0.5, 0.1, 0.0])
        fit = stats.isotonic_regression(y, increasing=False)
        self.assertTrue(np.all(np.diff(fit) <= 1e-9))
        self.assertLess(np.abs(fit - y).mean(), 0.1)

    def test_crossing_x_interpolates(self):
        x = np.array([100.0, 200.0, 300.0])
        y = np.array([1.0, 0.5, 0.0])
        self.assertAlmostEqual(stats.crossing_x(x, y, 0.5), 200.0)
        self.assertAlmostEqual(stats.crossing_x(x, y, 0.75), 150.0)

    def test_crossing_x_returns_nan_when_never_reached(self):
        self.assertTrue(np.isnan(stats.crossing_x([1.0, 2.0], [0.9, 0.8], 0.5)))


class TestKnees(unittest.TestCase):
    def test_knees_reports_per_arm_and_per_type(self):
        df, _, _ = _good_frame()
        by_arm = h2_threshold.knees(df)
        self.assertEqual(set(by_arm["architecture"]), set(config.pilot_pass2()["arms"]))
        self.assertIn("k_strict_acc", by_arm.columns)
        self.assertIn("k_abstention", by_arm.columns)
        by_type = h2_threshold.knees(df, by="fact_type")
        self.assertEqual(set(by_type["fact_type"]), set(dataset.GENERATORS))


# ---------------------------------------------------------------------------
# config surface
# ---------------------------------------------------------------------------

class TestConfigSurface(unittest.TestCase):
    def test_threshold_is_deprecated_and_strict_raises_with_deprecation_message(self):
        self.assertEqual(config.experiment()["threshold"]["status"], "DEPRECATED")
        with self.assertRaises(ValueError) as cm:
            config.compression_threshold(strict=True)
        self.assertIn("DEPRECATED", str(cm.exception))

    def test_pilot_pass2_block_is_frozen(self):
        p2 = config.pilot_pass2()
        self.assertEqual(p2["status"], "FROZEN")
        self.assertEqual(len(p2["target_model_tat"]), 11)
        self.assertEqual(config.run_mode("pilot_pass2")["n_items"], 40)


if __name__ == "__main__":
    unittest.main(verbosity=2)
