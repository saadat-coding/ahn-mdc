"""`schema.derive_boundary_conditions` — span/prefill/generation boundary variables.

Measurement-coordinate correction (pre-Pilot-Pass-2). The target fact is a span of
`target_fact_tokens`, not a point; generation moves the compression boundary right
by the actual `n_new_tokens`. These flags are derived from the recorded primitives
and never touch `memory_condition`.

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

from ahnexp import schema

_PRIMS = ("model_tokens_after_target", "target_fact_tokens", "n_new_tokens", "sliding_window")


def _row(**kw):
    base = dict(item_id="x", architecture="a", seed=0,
                model_tokens_after_target=0, target_fact_tokens=12, n_new_tokens=3,
                sliding_window=256)
    base.update(kw)
    return base


class TestStrictMode(unittest.TestCase):
    def test_strict_raises_when_any_primitive_is_missing(self):
        for drop in _PRIMS:
            df = pd.DataFrame([_row()]).drop(columns=[drop])
            with self.assertRaises(ValueError) as cm:
                schema.derive_boundary_conditions(df, strict=True)
            self.assertIn(drop, str(cm.exception))

    def test_strict_passes_and_adds_every_derived_column(self):
        out = schema.derive_boundary_conditions(pd.DataFrame([_row()]), strict=True)
        for name in schema._BOUNDARY_DERIVED:
            self.assertIn(name, out.columns)


class TestLegacyMode(unittest.TestCase):
    def test_non_strict_emits_na_columns_and_leaves_the_frame_otherwise_unchanged(self):
        legacy = pd.DataFrame([dict(item_id="x", architecture="a", seed=0,
                                    tokens_after_target=300, sliding_window=256, correct=1)])
        out = schema.derive_boundary_conditions(legacy, strict=False)
        for name in schema._BOUNDARY_DERIVED:
            self.assertIn(name, out.columns)
            self.assertTrue(out[name].isna().all())
        # original columns untouched
        pd.testing.assert_frame_equal(out[legacy.columns], legacy)


class TestFormulas(unittest.TestCase):
    def test_regimes(self):
        rows = [
            # fully exact at prefill and through generation: 40 + 12 + 3 = 55 <= 256
            _row(item_id="exact", model_tokens_after_target=40),
            # partially compressed at prefill: 250 < 256 but 250 + 12 > 256
            _row(item_id="partial", model_tokens_after_target=250),
            # end crosses during generation: 254 < 256, 254 + 3 >= 256
            _row(item_id="cross", model_tokens_after_target=254),
            # fully recurrent: 400 >= 256
            _row(item_id="recurrent", model_tokens_after_target=400),
        ]
        out = schema.derive_boundary_conditions(pd.DataFrame(rows), strict=True).set_index("item_id")

        self.assertEqual(list(out["target_start_distance_prefill"]), [52, 262, 266, 412])

        self.assertTrue(out.loc["exact", "target_fully_exact_at_prefill"])
        self.assertTrue(out.loc["exact", "target_fully_exact_through_generation"])
        self.assertFalse(out.loc["exact", "target_end_compressed_at_prefill"])

        self.assertTrue(out.loc["partial", "target_partially_compressed_at_prefill"])
        self.assertFalse(out.loc["partial", "target_fully_exact_at_prefill"])
        self.assertFalse(out.loc["partial", "target_end_compressed_at_prefill"])

        self.assertTrue(out.loc["cross", "target_end_crosses_during_generation"])
        self.assertFalse(out.loc["cross", "target_fully_exact_through_generation"])

        self.assertTrue(out.loc["recurrent", "target_end_compressed_at_prefill"])
        self.assertFalse(out.loc["recurrent", "target_partially_compressed_at_prefill"])
        self.assertFalse(out.loc["recurrent", "target_end_crosses_during_generation"])

    def test_start_distance_never_below_model_tat(self):
        rows = [_row(model_tokens_after_target=m, target_fact_tokens=t)
                for m in (0, 100, 300) for t in (1, 10, 20)]
        out = schema.derive_boundary_conditions(pd.DataFrame(rows), strict=True)
        self.assertTrue((out["target_start_distance_prefill"] >= out["model_tokens_after_target"]).all())

    def test_idempotent(self):
        df = pd.DataFrame([_row(model_tokens_after_target=m) for m in (40, 250, 400)])
        once = schema.derive_boundary_conditions(df, strict=True)
        twice = schema.derive_boundary_conditions(once, strict=True)
        pd.testing.assert_frame_equal(once, twice)

    def test_does_not_touch_memory_condition(self):
        df = schema.derive_memory_condition(pd.DataFrame([
            dict(**_row(model_tokens_after_target=40), tokens_after_target=10),
            dict(**_row(item_id="y", model_tokens_after_target=400), tokens_after_target=380),
        ]))
        before = list(df["memory_condition"])
        after = schema.derive_boundary_conditions(df, strict=True)
        self.assertEqual(before, list(after["memory_condition"]))
        self.assertEqual(before, ["exact_memory", "recurrent_memory"])


if __name__ == "__main__":
    unittest.main(verbosity=2)
