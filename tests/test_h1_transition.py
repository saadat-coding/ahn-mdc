"""H1 transition-band degradation rate (Pilot Pass 2 hostile-audit issue #2).

The legacy recurrent-only `slopes` returns ~0 when every clearly-recurrent level
is at the accuracy floor. `transition_slope` / `transition_drop` operate over an
explicit `model_tokens_after_target` band and must distinguish a sharp transition
from a gradual one, and tolerate an all-floor recurrent region.

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

from ahnexp import h1_degradation, schema

_LEVELS = [160, 190, 210, 230, 250, 270, 300, 340, 480, 900]


def _frame(shape: dict[str, str], seeds=(0, 1)):
    """`shape[fact_type]` in {"sharp", "gradual", "flat_floor"}."""
    rng = np.random.default_rng(0)
    rows = []
    for ft, kind in shape.items():
        for seed in seeds:
            for it in range(8):
                for lvl in _LEVELS:
                    model_tat = lvl + int(rng.integers(-4, 5))
                    if kind == "sharp":
                        p = 1.0 if model_tat < 235 else (0.0 if model_tat > 255 else 0.5)
                    elif kind == "gradual":
                        p = float(np.clip(1.0 - (model_tat - 170) / 260, 0.0, 1.0))
                    else:  # flat_floor: fine in-window, 0 everywhere recurrent
                        p = 0.9 if model_tat < 256 else 0.0
                    rows.append(dict(
                        item_id=f"{ft}_{it}", architecture="mamba2", seed=seed, fact_type=ft,
                        distractor_density="low", target_position="early",
                        tokens_after_target=lvl - 55, requested_tokens_after_target=lvl - 55,
                        model_tokens_after_target=model_tat, intended_model_tokens_after_target=lvl,
                        target_fact_tokens=12, context_tokens=200 + model_tat, sliding_window=256,
                        n_new_tokens=3, correct=int(rng.random() < p), abstained=0, malformed=0,
                        confidence=0.6, prediction="x", gold="x", scorer_version="1.0",
                    ))
    return schema.derive_boundary_conditions(schema.derive_memory_condition(pd.DataFrame(rows)), strict=True)


class TestTransitionBand(unittest.TestCase):
    def test_default_band_derives_from_window(self):
        df = _frame({"numerical": "sharp"})
        self.assertEqual(h1_degradation.transition_band(df), (256 - 76, 256 + 34))

    def test_sharp_transition_has_steeper_drop_than_gradual(self):
        df = _frame({"numerical": "sharp", "temporal": "gradual"})
        drop = h1_degradation.transition_drop(df).set_index("fact_type")["transition_drop"]
        self.assertGreater(drop["numerical"], drop["temporal"])
        slope = h1_degradation.transition_slope(df).set_index("fact_type")["transition_slope"]
        self.assertLess(slope["numerical"], slope["temporal"])   # more negative = steeper

    def test_flat_floor_recurrent_gives_near_zero_legacy_slope_but_a_real_transition_drop(self):
        df = _frame({"numerical": "flat_floor"})
        legacy = h1_degradation.slopes(df).set_index("fact_type")["slope"]
        self.assertLess(abs(legacy["numerical"]), 0.05)               # recurrent-only slope is ~0
        drop = h1_degradation.transition_drop(df).set_index("fact_type")["transition_drop"]
        self.assertGreater(drop["numerical"], 0.35)                   # the transition IS visible

    def test_explicit_band_is_respected(self):
        df = _frame({"numerical": "gradual"})
        wide = h1_degradation.transition_drop(df, band=(160, 900)).set_index("fact_type")
        narrow = h1_degradation.transition_drop(df, band=(200, 260)).set_index("fact_type")
        self.assertNotEqual(round(wide.loc["numerical", "transition_drop"], 3),
                            round(narrow.loc["numerical", "transition_drop"], 3))
        self.assertEqual(int(narrow.loc["numerical", "band_lo"]), 200)


if __name__ == "__main__":
    unittest.main(verbosity=2)
