"""Multi-hop construct rename (Pilot Pass 2 hostile-audit issue #6) + temporal
response-bias reporting (issue #7).

The raw `fact_type` value "multi-hop" is unchanged in data / scorer / chance map;
a display/construct name is added for paper-facing output.

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

from ahnexp import config, dataset, evaluate, report, schema


class TestConstructNaming(unittest.TestCase):
    def test_fact_type_value_unchanged_in_generator_and_scorer(self):
        items = dataset.generate_items(20, seed=0)
        mh = [it for it in items if it.fact.fact_type == "multi-hop"]
        self.assertTrue(mh)
        # scorer still keys on the raw value
        f = mh[0].fact
        self.assertEqual(evaluate.score_row(f.answer, f.answer, "multi-hop")["correct"], 1)
        # chance map still keys on the raw value
        self.assertIn("multi-hop", config.facts()["chance"])

    def test_display_label_is_the_construct_name(self):
        label = report.fact_type_label("multi-hop")
        self.assertNotEqual(label, "multi-hop")
        self.assertIn("compound", label.lower())
        # unknown / plain types pass through
        self.assertEqual(report.fact_type_label("numerical"), report.fact_type_label("numerical"))

    def test_with_construct_labels_adds_a_column_without_renaming(self):
        t = pd.DataFrame({"fact_type": ["multi-hop", "numerical"], "acc": [0.2, 0.3]})
        out = report.with_construct_labels(t)
        self.assertEqual(list(out["fact_type"]), ["multi-hop", "numerical"])
        self.assertIn("construct", out.columns)
        self.assertIn("compound", out.loc[0, "construct"].lower())

    def test_historical_parquet_values_still_parse(self):
        # a frame carrying the historical fact_type value flows through analysis
        rows = [dict(item_id=f"multi-hop_{i}", architecture="mamba2", seed=0, fact_type="multi-hop",
                     tokens_after_target=100, requested_tokens_after_target=100,
                     model_tokens_after_target=150, sliding_window=256,
                     correct=1, abstained=0, malformed=0, confidence=0.6, gold="Google",
                     prediction="Google") for i in range(4)]
        df = schema.derive_memory_condition(pd.DataFrame(rows))
        schema.validate(df, needs=("core", "h1", "h3"))
        self.assertEqual(report.fact_type_label(df["fact_type"].iloc[0]).lower().count("compound"), 1)


class TestTemporalResponseTable(unittest.TestCase):
    def test_reconstructs_balanced_factors_and_reports_outcomes(self):
        items = dataset.generate_items(40, seed=0)
        rows = []
        for it in items:
            if it.fact.fact_type != "temporal":
                continue
            for arm in ("mamba2", "transformer"):
                for lvl in (170, 240):
                    rows.append(dict(
                        item_id=it.item_id, architecture=arm, seed=0, fact_type="temporal",
                        tokens_after_target=100, requested_tokens_after_target=100,
                        model_tokens_after_target=lvl, intended_model_tokens_after_target=lvl,
                        sliding_window=256, correct=1, abstained=0, malformed=0,
                        confidence=0.6, gold=it.fact.answer, prediction=it.fact.answer,
                        distractor_density=it.distractor_density, target_position="early",
                    ))
        df = schema.derive_memory_condition(pd.DataFrame(rows))
        t = report.temporal_response_table(df, items=items)
        self.assertEqual(len(t), 8)
        for f in ("gold_is_higher", "gold_first_listed"):
            self.assertEqual(int(t[f].sum()), 4)          # counterbalanced 4/4
        self.assertIn("answered_valid_accuracy", t.columns)
        self.assertIn("marginals", t.attrs)

    def test_raises_when_factors_cannot_be_reconstructed(self):
        df = pd.DataFrame([dict(item_id="temporal_9999", architecture="mamba2", seed=0,
                                fact_type="temporal", tokens_after_target=1,
                                model_tokens_after_target=150, sliding_window=256,
                                correct=0, abstained=1, malformed=0, confidence=0.9,
                                gold="Person_1", prediction="I don't know")])
        with self.assertRaises(ValueError):
            report.temporal_response_table(df)


if __name__ == "__main__":
    unittest.main(verbosity=2)
