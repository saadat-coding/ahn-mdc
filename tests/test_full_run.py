"""Final inferential run — frozen design, gates, analysis (ahnexp.full_run).

Exercises the design plumbing (pressure plan, expected trial count), the
per-fact-type control-validity verdicts, the hard gate machinery, and the frozen
H1/H2/H3 analysis flow — including that NO deprecated-T / published-threshold
column reaches a final table.

No GPU. `python -m unittest discover -s tests`.
"""

from __future__ import annotations

import subprocess
import sys
import unittest
from pathlib import Path

import numpy as np
import pandas as pd

_ROOT = Path(__file__).resolve().parents[1]
if str(_ROOT / "src") not in sys.path:
    sys.path.insert(0, str(_ROOT / "src"))

from ahnexp import config, dataset, full_run, schema

_HAS_CALIB = (_ROOT / config.final()["calibration_file"]).is_file()


def _fake_final_frame(n_items=40, seeds=(0, 1, 2), arms=None, control_acc=None):
    fcfg = config.final()
    arms = arms or list(fcfg["arms"])
    calib = config.load_final_calibration()
    control_acc = control_acc or {}
    rng = np.random.default_rng(0)
    items = dataset.generate_items(n_items=n_items, seed=0)
    rows = []
    for arm in arms:
        for it in items:
            per_type = calib["per_type"][it.fact.fact_type]["requested_by_target"]
            for tgt in fcfg["target_model_tat"]:
                req = int(per_type[str(tgt)])
                for seed in seeds:
                    mtat = int(tgt + rng.integers(-5, 6))
                    if tgt <= 180:
                        p = control_acc.get(it.fact.fact_type, 0.95)
                    elif tgt <= 270:
                        p = 0.5 if arm != "transformer" else 0.7
                    else:
                        p = 0.03
                    answered = rng.random() > (0.08 if tgt <= 235 else 0.7)
                    rows.append({
                        "item_id": it.item_id, "architecture": arm, "seed": seed,
                        "fact_type": it.fact.fact_type, "distractor_density": it.distractor_density,
                        "target_position": "early",
                        "tokens_after_target": req + 4, "requested_tokens_after_target": req,
                        "model_tokens_after_target": mtat,
                        "intended_model_tokens_after_target": int(tgt),
                        "target_fact_tokens": 12, "context_tokens": 220 + mtat,
                        "sliding_window": 256, "n_new_tokens": 3,
                        "correct": int(answered and rng.random() < p),
                        "abstained": int(not answered), "malformed": 0,
                        "answer_canonical": "x" if answered else "",
                        "confidence": float(rng.uniform(0.3, 0.95)),
                        "prediction": "x" if answered else "I don't know", "gold": "x",
                        "scorer_version": "1.0",
                    })
    df = schema.derive_boundary_conditions(
        schema.derive_memory_condition(pd.DataFrame(rows)), strict=True)
    return df, items


class TestFrozenDesign(unittest.TestCase):
    def test_expected_generation_count(self):
        self.assertEqual(full_run.expected_trials(), 4 * 240 * 12 * 8)
        self.assertEqual(full_run.expected_trials(), 92_160)

    def test_final_block_is_frozen(self):
        fcfg = config.final()
        self.assertEqual(fcfg["status"], "FROZEN")
        self.assertEqual(fcfg["target_model_tat"],
                         [150, 180, 205, 220, 235, 250, 265, 285, 315, 380, 520, 760])
        self.assertEqual(fcfg["transition_interval"], [200, 270])
        self.assertEqual(fcfg["seeds"], [0, 1, 2, 3, 4, 5, 6, 7])
        self.assertEqual(fcfg["n_items"], 240)

    def test_240_items_are_balanced_and_temporal_is_factorial(self):
        from collections import Counter
        items = dataset.generate_items(240, seed=0)
        self.assertEqual(set(Counter(it.fact.fact_type for it in items).values()), {48})
        self.assertEqual(48 % 8, 0)


@unittest.skipUnless(_HAS_CALIB, "config/final_calibration.json not built yet")
class TestPressurePlan(unittest.TestCase):
    def test_plan_has_all_types_and_all_12_targets(self):
        plan = full_run.pressure_plan()
        self.assertEqual(set(plan), set(config.facts()["types"]))
        for ft, per_type in plan.items():
            self.assertEqual(sorted(per_type), sorted(config.final()["target_model_tat"]))


@unittest.skipUnless(_HAS_CALIB, "config/final_calibration.json not built yet")
class TestControlValidity(unittest.TestCase):
    def test_strong_control_passes_all_types(self):
        df, _ = _fake_final_frame()
        cv = full_run.control_validity(df).set_index("fact_type")
        self.assertTrue((cv["verdict"] != "FAIL").all())
        self.assertTrue(cv.loc["numerical", "in_h1_primary"])

    def test_broken_nontemporal_control_fails_and_leaves_h1_primary(self):
        df, _ = _fake_final_frame(control_acc={"numerical": 0.3})
        cv = full_run.control_validity(df).set_index("fact_type")
        self.assertEqual(cv.loc["numerical", "verdict"], "FAIL")
        self.assertFalse(cv.loc["numerical", "in_h1_primary"])
        self.assertTrue(cv.loc["entity-attribute", "in_h1_primary"])


@unittest.skipUnless(_HAS_CALIB, "config/final_calibration.json not built yet")
class TestFrozenAnalysis(unittest.TestCase):
    def test_analyse_produces_frozen_endpoints_and_no_T_table(self):
        df, items = _fake_final_frame()
        res = full_run.analyse(df, items=items, n_resamples=150)
        for name in ("h1_a_transition", "h1_contrasts", "h2_width", "h2_shape_break_at_W",
                     "h2_a_recurrent", "h3_behavioral_per_arm", "h3_behavioral_contrasts",
                     "h3_gap_change", "control_validity"):
            self.assertIn(name, res["tables"])
        # #17 Policy A + no published T
        self.assertTrue(res["summary"]["no_published_T"])
        self.assertIn("Policy A", res["summary"]["issue_17"])
        for tbl in res["tables"].values():
            if isinstance(tbl, pd.DataFrame):
                for col in tbl.columns:
                    self.assertNotIn("threshold", col.lower())
                    self.assertNotEqual(col, "T")
                    self.assertFalse(col.endswith("_T"))

    def test_h1_contrasts_are_ten_pairs_with_holm(self):
        df, items = _fake_final_frame()
        res = full_run.analyse(df, items=items, n_resamples=150)
        c = res["tables"]["h1_contrasts"]
        self.assertEqual(len(c), 10)
        self.assertIn("p_holm", c.columns)

    def test_h3_behavioral_region_is_W_plus_margin(self):
        df, items = _fake_final_frame()
        res = full_run.analyse(df, items=items, n_resamples=150)
        self.assertEqual(res["summary"]["h3_behavioral_region"], "model_tat >= 272")


class TestRunnerSelfTest(unittest.TestCase):
    @unittest.skipUnless(_HAS_CALIB, "config/final_calibration.json not built yet")
    def test_run_full_self_test(self):
        proc = subprocess.run(
            [sys.executable, str(_ROOT / "scripts" / "run_full.py"), "--self-test"],
            capture_output=True, text=True, cwd=_ROOT, timeout=300,
        )
        self.assertEqual(proc.returncode, 0, proc.stdout + proc.stderr)
        self.assertIn("SELF-TEST PASSED", proc.stdout)


if __name__ == "__main__":
    unittest.main(verbosity=2)
