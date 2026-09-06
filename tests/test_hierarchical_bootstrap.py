"""Two-level cluster bootstrap (stats.hierarchical_bootstrap) — the PRIMARY
inferential resampler for the frozen final run.

Resamples item_id clusters, then seed realisations within each sampled item. Must
give more item-level clusters than the legacy seed-only bootstrap, keep a paired
contrast paired, and widen as the item-level signal gets noisier.

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

from ahnexp import stats


def _frame(n_items=60, seeds=(0, 1, 2, 3), item_effect=0.0, base=0.6, rng=None):
    rng = rng or np.random.default_rng(0)
    rows = []
    for i in range(n_items):
        p = float(np.clip(base + rng.normal(0, item_effect), 0.02, 0.98))
        for s in seeds:
            for arm in ("a", "b"):
                bump = 0.15 if arm == "a" else 0.0
                rows.append({"item_id": f"it_{i}", "seed": s, "architecture": arm,
                             "correct": int(rng.random() < min(0.98, p + bump))})
    return pd.DataFrame(rows)


class TestHierarchicalBootstrap(unittest.TestCase):
    def test_ci_brackets_point_and_reports_item_clusters(self):
        df = _frame()
        out = stats.hierarchical_bootstrap(df, lambda f: f["correct"].mean(),
                                           n_resamples=400, random_state=1)
        self.assertLessEqual(out["ci_low"], out["point"])
        self.assertLessEqual(out["point"], out["ci_high"])
        self.assertEqual(out["n_items"], 60)  # 60 item clusters, not 4 seeds

    def test_paired_contrast_excludes_zero_when_arm_effect_is_real(self):
        df = _frame(item_effect=0.05)
        stat = lambda f: (f.loc[f["architecture"] == "a", "correct"].mean()
                          - f.loc[f["architecture"] == "b", "correct"].mean())
        out = stats.hierarchical_bootstrap(df, stat, n_resamples=600, random_state=2)
        self.assertGreater(out["ci_low"], 0.0)  # arm a is reliably ahead

    def test_more_item_heterogeneity_widens_the_interval(self):
        tight = stats.hierarchical_bootstrap(
            _frame(item_effect=0.01, rng=np.random.default_rng(3)),
            lambda f: f["correct"].mean(), n_resamples=400, random_state=3)
        wide = stats.hierarchical_bootstrap(
            _frame(item_effect=0.20, rng=np.random.default_rng(3)),
            lambda f: f["correct"].mean(), n_resamples=400, random_state=3)
        self.assertGreater(wide["ci_high"] - wide["ci_low"],
                           tight["ci_high"] - tight["ci_low"])

    def test_single_item_gives_nan_ci(self):
        df = _frame(n_items=1)
        out = stats.hierarchical_bootstrap(df, lambda f: f["correct"].mean(), n_resamples=50)
        self.assertTrue(np.isnan(out["ci_low"]))


if __name__ == "__main__":
    unittest.main(verbosity=2)
