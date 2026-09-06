"""H1 frozen primary endpoint — A_transition (h1_degradation).

A_transition(type) = mean raw strict accuracy over the pre-registered intended
model-tat targets [205,220,235,250,265], AHN arms pooled, transformer excluded.
Primary: 10 pairwise fact-type contrasts with hierarchical-bootstrap CI + Holm.
Companion: fact-type-label permutation omnibus on the SD of the five means.

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

from ahnexp import config, h1_degradation, schema

_TARGETS = list(config.final()["target_model_tat"])
_TYPE_ACC = {  # strict accuracy in the transition region
    "numerical": 0.15, "multi-hop": 0.20, "entity-attribute": 0.55,
    "contradictory": 0.60, "temporal": 0.85,
}


def _frame(type_acc=None, n_items=16, seeds=(0, 1, 2, 3)):
    type_acc = type_acc or _TYPE_ACC
    rng = np.random.default_rng(0)
    rows = []
    for ft, acc in type_acc.items():
        for i in range(n_items):
            for seed in seeds:
                for arm in ("mamba2", "deltanet", "gated_deltanet", "transformer"):
                    for tgt in _TARGETS:
                        if tgt <= 190:
                            p = 0.95
                        elif tgt <= 270:
                            p = acc if arm != "transformer" else min(0.95, acc + 0.25)
                        else:
                            p = 0.02
                        rows.append(dict(
                            item_id=f"{ft}_{i:02d}", architecture=arm, seed=seed, fact_type=ft,
                            distractor_density="low", target_position="early",
                            tokens_after_target=tgt - 55, requested_tokens_after_target=tgt - 55,
                            model_tokens_after_target=tgt + int(rng.integers(-3, 4)),
                            intended_model_tokens_after_target=tgt,
                            target_fact_tokens=12, context_tokens=200 + tgt, sliding_window=256,
                            n_new_tokens=3, correct=int(rng.random() < p), abstained=0, malformed=0,
                            confidence=0.6, prediction="x", gold="x", scorer_version="1.0",
                        ))
    return schema.derive_boundary_conditions(schema.derive_memory_condition(pd.DataFrame(rows)), strict=True)


class TestATransition(unittest.TestCase):
    def test_a_transition_pools_ahn_and_excludes_transformer(self):
        df = _frame()
        a = h1_degradation.a_transition(df).set_index("fact_type")["a_transition"]
        self.assertAlmostEqual(a["numerical"], 0.15, delta=0.06)
        self.assertAlmostEqual(a["temporal"], 0.85, delta=0.06)
        # transformer curve is not folded in (would pull numerical up toward 0.4)
        self.assertLess(a["numerical"], 0.30)

    def test_contrasts_flag_a_real_difference_after_holm(self):
        df = _frame()
        c = h1_degradation.a_transition_contrasts(df, n_resamples=400)
        self.assertEqual(len(c), 10)  # 5 choose 2
        hit = c[((c["a"] == "numerical") & (c["b"] == "temporal"))
                | ((c["a"] == "temporal") & (c["b"] == "numerical"))].iloc[0]
        self.assertTrue(hit["significant_holm"])
        self.assertTrue(hit["ci_low"] > 0 or hit["ci_high"] < 0)
        self.assertTrue(c["significant_holm"].any())

    def test_flat_types_give_no_significant_contrast(self):
        flat = {k: 0.5 for k in _TYPE_ACC}
        c = h1_degradation.a_transition_contrasts(_frame(flat), n_resamples=400)
        self.assertFalse(c["significant_holm"].any())

    def test_omnibus_detects_dispersion(self):
        spread = h1_degradation.a_transition_omnibus(_frame(), n_perm=400)
        flat = h1_degradation.a_transition_omnibus(_frame({k: 0.5 for k in _TYPE_ACC}), n_perm=400)
        self.assertLess(spread["p_value"], 0.05)
        self.assertGreater(flat["p_value"], 0.05)


if __name__ == "__main__":
    unittest.main(verbosity=2)
