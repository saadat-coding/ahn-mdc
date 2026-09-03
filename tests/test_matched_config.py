"""Matched inference config — `_force_window` normalisation + `assert_matched` (open_decisions.md #12).

Guards the frozen matched configuration Juan approved:
    sliding_window = 256, sliding_window_type = fixed, ahn_position = prefix, num_attn_sinks = 0

No GPU / no torch: uses lightweight fakes for `model` / `tokenizer`.

    python -m unittest discover -s tests
"""

from __future__ import annotations

import sys
import unittest
from pathlib import Path
from types import SimpleNamespace

_ROOT = Path(__file__).resolve().parents[1]
if str(_ROOT / "src") not in sys.path:
    sys.path.insert(0, str(_ROOT / "src"))

from ahnexp import config, models

MATCHED = config.experiment()["models"]["matched"]
FORCE = int(config.experiment()["models"]["sliding_window"]["force"])


class _FakeParam:
    dtype = "torch.float16"


class _FakeModel:
    """Just enough surface for `_force_window` and `describe`."""

    def __init__(self, **config_kw):
        self.config = SimpleNamespace(
            sliding_window=32768, use_sliding_window=False,
            vocab_size=151936, hidden_size=2048, num_hidden_layers=36,
            **config_kw,
        )
        self._modules = [SimpleNamespace(sliding_window=32768) for _ in range(3)]

    def modules(self):
        return iter(self._modules)

    def parameters(self):
        return iter([_FakeParam()])


class _FakeTokenizer:
    def __len__(self):
        return 151936

    def __call__(self, text, **_):
        return {"input_ids": [ord(c) % 97 for c in text][:16]}


# GatedDeltaNet ships these; DeltaNet additionally ships dy_sliding_window=2048;
# Mamba2 + DeltaNet ship dy_num_attn_sinks=128.
def _gdn_model():
    return _FakeModel(sliding_window_type="random", ahn_position="random", _ahn_implementation="GatedDeltaNet")


def _deltanet_model():
    return _FakeModel(sliding_window_type="random", ahn_position="random",
                      _ahn_implementation="DeltaNet",
                      dy_sliding_window=2048, dy_num_attn_sinks=128)


def _mamba2_model():
    return _FakeModel(sliding_window_type="random", ahn_position="random",
                      _ahn_implementation="Mamba2", dy_num_attn_sinks=128)


class TestForceWindowNormalisation(unittest.TestCase):

    def test_frozen_matched_values_applied(self):
        m = _gdn_model()
        models._force_window(m, FORCE, verbose=False)
        self.assertEqual(m.config.sliding_window, 256)
        self.assertIs(m.config.use_sliding_window, True)
        self.assertEqual(m.config.sliding_window_type, "fixed")
        self.assertEqual(m.config.ahn_position, "prefix")
        self.assertEqual(m.config.num_attn_sinks, 0)
        for mod in m.modules():
            self.assertEqual(mod.sliding_window, 256)

    def test_stale_dy_keys_removed_deltanet(self):
        m = _deltanet_model()
        self.assertTrue(hasattr(m.config, "dy_sliding_window"))
        self.assertTrue(hasattr(m.config, "dy_num_attn_sinks"))
        models._force_window(m, FORCE, verbose=False)
        self.assertFalse(hasattr(m.config, "dy_sliding_window"), "dy_sliding_window not removed")
        self.assertFalse(hasattr(m.config, "dy_num_attn_sinks"), "dy_num_attn_sinks not removed")

    def test_stale_dy_num_attn_sinks_removed_mamba2(self):
        m = _mamba2_model()
        models._force_window(m, FORCE, verbose=False)
        self.assertFalse(hasattr(m.config, "dy_num_attn_sinks"))

    def test_no_dy_keys_is_a_noop_gdn(self):
        m = _gdn_model()
        models._force_window(m, FORCE, verbose=False)  # must not raise on absent dy_*
        self.assertFalse(hasattr(m.config, "dy_sliding_window"))

    def test_matches_juan_frozen_config(self):
        self.assertEqual(MATCHED["sliding_window_type"], "fixed")
        self.assertEqual(MATCHED["ahn_position"], "prefix")
        self.assertEqual(FORCE, 256)


class TestDescribeExposesMatchedFields(unittest.TestCase):

    def _describe(self, fake_model):
        models._force_window(fake_model, FORCE, verbose=False)
        return models.describe("gated_deltanet", fake_model, _FakeTokenizer())

    def test_describe_has_the_three_fields(self):
        d = self._describe(_gdn_model())
        for key in ("sliding_window_type", "ahn_position", "num_attn_sinks"):
            self.assertIn(key, d, f"describe() missing {key!r}")
        self.assertEqual(d["sliding_window_type"], "fixed")
        self.assertEqual(d["ahn_position"], "prefix")
        self.assertEqual(d["num_attn_sinks"], 0)
        self.assertEqual(d["sliding_window"], 256)

    def test_describe_identical_across_arms_after_normalisation(self):
        arms = {
            "gated_deltanet": _gdn_model(), "deltanet": _deltanet_model(), "mamba2": _mamba2_model(),
        }
        seen = []
        for name, fm in arms.items():
            models._force_window(fm, FORCE, verbose=False)
            d = models.describe(name, fm, _FakeTokenizer())
            seen.append({k: d[k] for k in ("sliding_window", "sliding_window_type", "ahn_position", "num_attn_sinks")})
        self.assertEqual(seen[0], seen[1])
        self.assertEqual(seen[1], seen[2])


class TestAssertMatchedChecksTheseFields(unittest.TestCase):
    """assert_matched compares every describe() key except _ALLOWED_TO_DIFFER."""

    def test_new_fields_are_not_exempt(self):
        for key in ("sliding_window_type", "ahn_position", "num_attn_sinks"):
            self.assertNotIn(key, models._ALLOWED_TO_DIFFER)

    def _base(self, **over):
        d = {
            "arm": "x", "sliding_window": 256, "sliding_window_type": "fixed",
            "ahn_position": "prefix", "num_attn_sinks": 0, "dtype": "torch.float16",
            "vocab_size": 151936, "tokenizer_hash": "abc", "hidden_size": 2048,
            "num_hidden_layers": 36, "ahn_params": 13_000_000,
        }
        d.update(over)
        return d

    def test_matched_arms_pass(self):
        models.assert_matched([self._base(arm="a"), self._base(arm="b", ahn_params=11_800_000)])

    def test_sliding_window_type_mismatch_raises(self):
        with self.assertRaises(AssertionError) as ctx:
            models.assert_matched([self._base(arm="a"), self._base(arm="b", sliding_window_type="random")])
        self.assertIn("sliding_window_type", str(ctx.exception))

    def test_ahn_position_mismatch_raises(self):
        with self.assertRaises(AssertionError) as ctx:
            models.assert_matched([self._base(arm="a"), self._base(arm="b", ahn_position="random")])
        self.assertIn("ahn_position", str(ctx.exception))

    def test_num_attn_sinks_mismatch_raises(self):
        with self.assertRaises(AssertionError) as ctx:
            models.assert_matched([self._base(arm="a"), self._base(arm="b", num_attn_sinks=128)])
        self.assertIn("num_attn_sinks", str(ctx.exception))


if __name__ == "__main__":
    unittest.main(verbosity=2)
