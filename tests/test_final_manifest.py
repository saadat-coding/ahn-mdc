"""Frozen-design manifest (config/final_design_manifest.json) integrity.

The manifest is the hash/record the final run checks itself against. It must stay
consistent with the live `config.final()` block, the frozen prompt, and the
committed calibration file, so a silent drift is caught before GPU launch.

No GPU. `python -m unittest discover -s tests`.
"""

from __future__ import annotations

import sys
import unittest
from pathlib import Path

_ROOT = Path(__file__).resolve().parents[1]
if str(_ROOT / "src") not in sys.path:
    sys.path.insert(0, str(_ROOT / "src"))

from ahnexp import config

_MANIFEST = _ROOT / config.final()["manifest_file"]


@unittest.skipUnless(_MANIFEST.is_file(), "manifest not generated yet")
class TestFinalManifest(unittest.TestCase):
    def setUp(self):
        config.clear_caches()
        self.m = config.final_manifest()
        self.f = config.final()

    def test_design_fields_match_live_config(self):
        self.assertEqual(self.m["target_model_tat_grid"], list(self.f["target_model_tat"]))
        self.assertEqual(self.m["seeds"], list(self.f["seeds"]))
        self.assertEqual(self.m["arms"], list(self.f["arms"]))
        self.assertEqual(self.m["n_items"], self.f["n_items"])
        self.assertEqual(self.m["window_W"], self.f["window_reference"])
        self.assertEqual(self.m["transition_interval"], list(self.f["transition_interval"]))
        self.assertEqual(self.m["h1_transition_targets"], list(self.f["h1_transition_targets"]))
        self.assertEqual(self.m["recurrent_from"], self.f["recurrent_from"])
        self.assertEqual(self.m["h3_signal_margin"], self.f["h3_signal_margin"])
        self.assertEqual(self.m["analysis_version"], self.f["analysis_version"])

    def test_expected_generation_count(self):
        self.assertEqual(self.m["expected_generations"], 4 * 240 * 12 * 8)

    def test_prompt_hash_matches_frozen_prompt(self):
        self.assertEqual(self.m["prompt_sha256"], config.prompt_hash())

    def test_calibration_hash_matches_committed_file(self):
        self.assertEqual(self.m["calibration_sha256"],
                         config.file_sha256(self.f["calibration_file"]))

    def test_construct_mapping_matches_facts_yaml(self):
        live = {k: v.get("construct", k) for k, v in config.facts()["types"].items()}
        self.assertEqual(self.m["fact_type_construct"], live)

    def test_scorer_version_pinned(self):
        from ahnexp import evaluate
        self.assertEqual(self.m["scorer_version"], evaluate.SCORER_VERSION)


if __name__ == "__main__":
    unittest.main(verbosity=2)
