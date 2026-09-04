"""`report.gate_report` — the `exact_memory_by_fact_type` WARN check.

The per-arm `exact_memory_accuracy` gate pools all five fact types, so a single
weak category can hide behind a strong average (or read as "too easy"). This adds
a WARN — never a hard failure, never in `report.blocking()` — when any one fact
type falls below the defensible exact-memory floor.

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

from ahnexp import config, report

_TYPES = ["numerical", "temporal", "entity-attribute", "multi-hop", "contradictory"]


def _frame(per_arm_exact: dict[str, list[int]], arms=("deltanet", "gated_deltanet")) -> pd.DataFrame:
    """`per_arm_exact[ft]` = the 0/1 exact-memory outcomes for one arm (staged
    Pass 1 shape: 2 items x 2 exact levels = 4). Replicated across arms, so the
    pooled exact-memory count per fact type is len(list) * len(arms).

    Adds one recurrent trial per (item, arm) at level 512 so window_is_exceeded
    and the H-checks have data.
    """
    rows = []
    for arm in arms:
        for ft in _TYPES:
            outcomes = per_arm_exact[ft]
            for k, c in enumerate(outcomes):
                item = f"{ft}_{k // 2:04d}"          # 2 items: k=0,1 -> item 0 ; k=2,3 -> item 1
                lvl = [0, 128][k % 2]
                rows.append(dict(item_id=item, architecture=arm, seed=0, fact_type=ft,
                                 tokens_after_target=lvl, model_tokens_after_target=lvl + 50,
                                 sliding_window=256, memory_condition="exact_memory",
                                 correct=int(c), abstained=int(c == 0), malformed=0, confidence=0.5))
            for k in range(len(outcomes)):
                item = f"{ft}_{k // 2:04d}"
                rows.append(dict(item_id=item, architecture=arm, seed=0, fact_type=ft,
                                 tokens_after_target=512, model_tokens_after_target=562,
                                 sliding_window=256, memory_condition="recurrent_memory",
                                 correct=0, abstained=1, malformed=0, confidence=0.5))
    return pd.DataFrame(rows)


class TestExactMemoryByFactType(unittest.TestCase):
    def setUp(self):
        config.clear_caches()

    def test_warns_on_a_single_weak_type_that_the_pooled_gate_masks(self):
        # per arm: 3 types 4/4, contradictory 3/4, temporal 1/4  -> 16/20 = 0.80
        # -> the per-arm exact_memory_accuracy gate lands in the defensible band (PASS).
        # temporal pooled over 2 arms = 2/8 = 0.25 -> below the 0.70 floor -> WARN.
        df = _frame({
            "numerical": [1, 1, 1, 1], "entity-attribute": [1, 1, 1, 1], "multi-hop": [1, 1, 1, 1],
            "contradictory": [1, 1, 1, 0], "temporal": [1, 0, 0, 0],
        })
        gates = report.gate_report(df)
        g = gates.set_index(["gate", "scope"])["verdict"].to_dict()

        self.assertEqual(g.get(("exact_memory_accuracy", "deltanet")), "PASS")
        self.assertEqual(g.get(("exact_memory_accuracy", "gated_deltanet")), "PASS")

        warn = gates[gates["gate"] == "exact_memory_by_fact_type"]
        self.assertEqual(list(warn["scope"]), ["temporal"])
        self.assertEqual(list(warn["verdict"]), ["WARN"])
        self.assertIn("over 8 trials", warn.iloc[0]["detail"])

        blk = report.blocking(gates)
        self.assertTrue((blk["gate"] != "exact_memory_by_fact_type").all())

    def test_silent_when_every_type_clears_the_floor(self):
        ok = [1, 1, 1, 0]  # 3/4 per arm -> 6/8 pooled = 0.75 >= 0.70
        df = _frame({ft: ok for ft in _TYPES})
        gates = report.gate_report(df)
        self.assertTrue(gates[gates["gate"] == "exact_memory_by_fact_type"].empty)

    def test_skips_a_type_with_fewer_than_four_exact_trials(self):
        df = _frame({ft: [1, 1, 1, 1] for ft in _TYPES})
        tmp_exact = df.index[(df["fact_type"] == "temporal")
                             & (df["memory_condition"] == "exact_memory")]
        df = df.drop(index=tmp_exact[3:]).copy()          # leave 3 temporal exact rows
        df.loc[tmp_exact[:3], "correct"] = 0              # all wrong
        m = (df["fact_type"] == "temporal") & (df["memory_condition"] == "exact_memory")
        self.assertEqual(int(m.sum()), 3)
        gates = report.gate_report(df)
        self.assertTrue(gates[(gates["gate"] == "exact_memory_by_fact_type")
                              & (gates["scope"] == "temporal")].empty)

    def test_n8_operating_point_matches_staged_pass_1(self):
        df = _frame({
            "numerical": [1, 1, 1, 1], "entity-attribute": [1, 1, 1, 1], "multi-hop": [1, 1, 1, 1],
            "contradictory": [1, 1, 1, 1], "temporal": [1, 1, 0, 0],   # 4/8 pooled = 0.50
        })
        exact_temporal = df[(df.fact_type == "temporal") & (df.memory_condition == "exact_memory")]
        self.assertEqual(len(exact_temporal), 8)
        warn = report.gate_report(df)
        warn = warn[warn["gate"] == "exact_memory_by_fact_type"]
        self.assertEqual(list(warn["scope"]), ["temporal"])


if __name__ == "__main__":
    unittest.main(verbosity=2)
