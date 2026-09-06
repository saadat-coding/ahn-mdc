"""Reframed malformed gate (Pilot Pass 2 hostile-audit issue #4).

The 10% cap is the plumbing-smell threshold and stays. Applied per arm:
  * an AHN arm above the cap is a blocking FAIL;
  * a no-AHN hard-window CONTROL arm above the cap is CONTROL_BEHAVIOR
    (non-blocking) ONLY IF it is sane at the deep in-window anchor and rises with
    pressure — a real parser break is uniform, so it still FAILs;
  * a separate unconditional BLOCKER fires if >=2 arms exceed the cap at the deep
    in-window anchor.

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

from ahnexp import config, dataset, pilot_pass2, schema

_ARMS = ["transformer", "mamba2", "deltanet", "gated_deltanet"]
_TARGETS = [170, 200, 240, 300, 640]
_TYPES = ["numerical", "temporal", "entity-attribute", "multi-hop", "contradictory"]


def _frame(malformed_by_arm_target: dict[str, dict[int, float]]):
    """`malformed_by_arm_target[arm][intended_target]` = malformed probability."""
    rng = np.random.default_rng(0)
    rows = []
    for arm in _ARMS:
        for ti, ft in enumerate(_TYPES):
            for it in range(8):
                for target in _TARGETS:
                    p_malf = malformed_by_arm_target.get(arm, {}).get(target, 0.0)
                    malf = int(rng.random() < p_malf)
                    correct = int(not malf and target < 210)
                    rows.append(dict(
                        item_id=f"{ft}_{ti*8+it:04d}", architecture=arm, seed=0, fact_type=ft,
                        distractor_density="high" if it % 2 else "low", target_position="early",
                        tokens_after_target=target - 55, requested_tokens_after_target=target - 55,
                        model_tokens_after_target=target, intended_model_tokens_after_target=target,
                        target_fact_tokens=12, context_tokens=200 + target, sliding_window=256,
                        n_new_tokens=3, correct=correct,
                        abstained=int(not malf and not correct), malformed=malf,
                        answer_canonical="" if malf else "x", confidence=0.3 if malf else 0.7,
                        prediction="junk" if malf else "x", gold="x", scorer_version="1.0",
                    ))
    return schema.derive_boundary_conditions(schema.derive_memory_condition(pd.DataFrame(rows)), strict=True)


def _gates(df):
    items = dataset.generate_items(40, seed=0)
    return pilot_pass2.plumbing_gates(df, items, {"per_type": {}})


def _malformed_blocking(g):
    """FAIL verdicts among the malformed gate family only (the synthetic subset
    frame trips unrelated shape gates like trial_count / all_targets_present)."""
    blk = pilot_pass2.blocking(g)
    return blk[blk["gate"].str.startswith("malformed")]


class TestMalformedGate(unittest.TestCase):
    def test_control_only_after_window_is_control_behaviour_not_blocking(self):
        # transformer: 0 malformed in-window, ~55% past its window
        df = _frame({"transformer": {170: 0.0, 200: 0.02, 240: 0.55, 300: 0.55, 640: 0.05}})
        g = _gates(df)
        row = g[g["gate"] == "malformed_control:transformer"].iloc[0]
        self.assertEqual(row["verdict"], "CONTROL_BEHAVIOR")
        self.assertTrue(_malformed_blocking(g).empty)
        self.assertEqual(g[g["gate"] == "malformed_pooled"]["verdict"].iloc[0], "REPORT")

    def test_ahn_arm_over_cap_is_blocking_fail(self):
        df = _frame({"deltanet": {170: 0.0, 200: 0.05, 240: 0.30, 300: 0.20, 640: 0.10}})
        g = _gates(df)
        self.assertEqual(g[g["gate"] == "malformed_rate:deltanet"]["verdict"].iloc[0], "FAIL")
        self.assertIn("malformed_rate:deltanet", _malformed_blocking(g)["gate"].tolist())

    def test_control_with_high_in_window_malformed_is_a_fail(self):
        # uniform high malformed including the deep in-window anchor -> parser break
        df = _frame({"transformer": {t: 0.5 for t in _TARGETS}})
        g = _gates(df)
        self.assertEqual(g[g["gate"] == "malformed_control:transformer"]["verdict"].iloc[0], "FAIL")
        self.assertFalse(_malformed_blocking(g).empty)

    def test_parser_break_across_multiple_arms_blocks_unconditionally(self):
        df = _frame({a: {t: 0.4 for t in _TARGETS} for a in _ARMS})
        g = _gates(df)
        pb = g[g["gate"] == "malformed_no_parser_break"].iloc[0]
        self.assertEqual(pb["verdict"], "FAIL")
        self.assertIn("malformed_no_parser_break", _malformed_blocking(g)["gate"].tolist())

    def test_clean_run_all_pass(self):
        df = _frame({})
        g = _gates(df)
        m = g[g["gate"].str.startswith("malformed")]
        self.assertEqual(set(m["verdict"]) - {"PASS", "REPORT"}, set())
        self.assertTrue(_malformed_blocking(g).empty)

    def test_cap_constant_unchanged(self):
        self.assertEqual(pilot_pass2._MALFORMED_CAP, 0.10)


if __name__ == "__main__":
    unittest.main(verbosity=2)
