"""Regression guard for the `mini` boundary run mode (config/experiment.yaml).

The mini grid is a 20-trial plumbing check (5 items x 4 levels x 1 seed x 1 arm)
that must straddle the 256-token window: 2 clearly-exact levels, 2 clearly-recurrent.
It must not disturb `grid` / `pilot_grid` / `full` / window / scoring config.

No GPU. `python -m unittest discover -s tests`.
"""

from __future__ import annotations

import subprocess
import sys
import unittest
from pathlib import Path

_ROOT = Path(__file__).resolve().parents[1]
if str(_ROOT / "src") not in sys.path:
    sys.path.insert(0, str(_ROOT / "src"))

from ahnexp import config, evaluate, schema


class TestMiniRunMode(unittest.TestCase):
    def setUp(self):
        config.clear_caches()
        self.exp = config.experiment()

    def test_mini_run_mode_shape(self):
        m = config.run_mode("mini")
        self.assertEqual(m["n_items"], 5)
        self.assertEqual(m["seeds"], [0])
        self.assertEqual(m["grid"], "mini_grid")
        self.assertEqual(m["suffix"], "_mini")

    def test_mini_grid_resolves_to_20_trials_straddling_the_window(self):
        levels = evaluate.pressure_levels(256, mode="mini")
        # 3 multiples [0, 0.5, 8.0]*256 + the auto-added published-T point (~768)
        self.assertEqual(levels, [0, 128, 768, 2048])
        n_trials = len(levels) * config.run_mode("mini")["n_items"] * len(config.run_mode("mini")["seeds"])
        self.assertEqual(n_trials, 20)  # x1 arm

    def test_mini_levels_split_exact_vs_recurrent(self):
        import pandas as pd
        levels = evaluate.pressure_levels(256, mode="mini")
        df = pd.DataFrame([
            {"item_id": "x", "architecture": "gated_deltanet", "seed": 0, "fact_type": "numerical",
             "sliding_window": 256, "tokens_after_target": ta,
             "model_tokens_after_target": ta + 50, "correct": 0}
            for ta in levels
        ])
        conds = schema.derive_memory_condition(df)["memory_condition"].tolist()
        self.assertEqual(conds, ["exact_memory", "exact_memory", "recurrent_memory", "recurrent_memory"])

    def test_mini_output_paths_get_the_mini_suffix(self):
        self.assertEqual(config.output_path("raw", "mini").name, "results_mini.parquet")
        self.assertEqual(config.table_path("h1_degradation", "mini").name, "h1_degradation_mini.md")

    def test_other_run_modes_and_grids_unchanged(self):
        p = self.exp["pressure"]
        self.assertEqual(p["grid"], [0.0, 0.25, 0.5, 1.0, 2.0, 4.0, 8.0, 16.0])
        self.assertEqual(p["pilot_grid"], [0.0, 0.5, 1.0, 2.0])
        self.assertIs(p["include_threshold"], True)
        self.assertEqual(self.exp["models"]["sliding_window"]["force"], 256)
        self.assertEqual(config.run_mode("pilot")["n_items"], 10)
        # `full` is the frozen inferential run: 240 items, 8 seeds (config.final())
        self.assertEqual(config.run_mode("full")["seeds"], [0, 1, 2, 3, 4, 5, 6, 7])
        self.assertEqual(config.run_mode("full")["n_items"], 240)
        cal = self.exp["calibration"]
        self.assertEqual(cal["confidence"], "sequence_probability")
        self.assertEqual(cal["cwr_threshold"], 0.5)


class TestMiniGridRunner(unittest.TestCase):
    """`scripts/run_mini_grid.py --self-test` — no GPU: fabricates a mini-shaped
    frame and drives it through the real gate + H1 + H3 analysis code."""

    def test_runner_self_test_passes(self):
        proc = subprocess.run(
            [sys.executable, str(_ROOT / "scripts" / "run_mini_grid.py"), "--self-test"],
            capture_output=True, text=True, cwd=_ROOT, timeout=120,
        )
        self.assertEqual(proc.returncode, 0, proc.stdout + proc.stderr)
        self.assertIn("SELF-TEST PASSED", proc.stdout)
        self.assertIn("MINI-GRID PASSED", proc.stdout)


if __name__ == "__main__":
    unittest.main(verbosity=2)
