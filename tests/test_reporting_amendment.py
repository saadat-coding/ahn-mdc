"""Post-freeze reporting amendment v1.1 (`ahnexp.reporting_amendment`).

Proves: (a) the H2 90->10 width eligibility rule is derived from the estimator's
mathematical requirements, not observed convenience; (b) eligible widths + median
summary behave; (c) the H1 exclude-compound-relational sensitivity has the right
shape + multiplicity; (d) the frozen v1.0 analysis version/behaviour is untouched.

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

from ahnexp import full_run, reporting_amendment as ra, schema, stats

_TARGETS = [150, 180, 205, 220, 235, 250, 265, 285, 315, 380, 520, 760]
_TYPES = ["numerical", "temporal", "entity-attribute", "multi-hop", "contradictory"]


def _frame(ceilings, floors=None, n_items=12, seeds=(0, 1, 2, 3)):
    """Synthetic frozen-shaped frame. `ceilings[ft]` = in-window strict accuracy,
    `floors[ft]` = deep strict accuracy (default 0.0). Sharp drop across W."""
    floors = floors or {ft: 0.0 for ft in ceilings}
    rng = np.random.default_rng(0)
    rows = []
    for ft, ceil in ceilings.items():
        flr = floors[ft]
        for arm in ("transformer", "mamba2", "deltanet", "gated_deltanet"):
            for i in range(n_items):
                for s in seeds:
                    for t in _TARGETS:
                        mtat = t + int(rng.integers(-4, 5))
                        frac = np.clip((mtat - 200) / 70, 0, 1)  # 0 at <=200, 1 at >=270
                        p = ceil * (1 - frac) + flr * frac
                        ans = rng.random() > 0.05
                        rows.append(dict(
                            item_id=f"{ft}_{i:04d}", architecture=arm, seed=int(s), fact_type=ft,
                            distractor_density="low", target_position="early",
                            tokens_after_target=t - 55, requested_tokens_after_target=t - 55,
                            model_tokens_after_target=mtat, intended_model_tokens_after_target=t,
                            target_fact_tokens=12, context_tokens=200 + mtat, sliding_window=256,
                            n_new_tokens=3, correct=int(ans and rng.random() < p),
                            abstained=int(not ans), malformed=0,
                            answer_canonical="x" if ans else "", confidence=0.7,
                            prediction="x" if ans else "I don't know", gold="x",
                            scorer_version="1.0"))
    return schema.derive_boundary_conditions(
        schema.derive_memory_condition(pd.DataFrame(rows)), strict=True)


class TestWidthEligibility(unittest.TestCase):
    def test_rule_is_mathematical_not_observed(self):
        # numerical/contradictory reach 1.0 in-window and 0.0 deep -> eligible.
        # temporal ceiling 0.60 -> cannot reach 0.90 -> ineligible BY DEFINITION.
        df = _frame({"numerical": 1.0, "contradictory": 0.98, "temporal": 0.60,
                     "multi-hop": 0.85, "entity-attribute": 1.0})
        e = ra.h2_width_eligibility(df).set_index(["fact_type", "architecture"])
        self.assertTrue(e.loc[("numerical",), "eligible"].all())
        self.assertTrue(e.loc[("entity-attribute",), "eligible"].all())
        self.assertFalse(e.loc[("temporal",), "eligible"].any())
        self.assertFalse(e.loc[("multi-hop",), "eligible"].any())
        # reason names the failing mathematical requirement
        self.assertIn("< 0.90", e.loc[("temporal", "mamba2"), "reason"])

    def test_eligible_type_has_finite_width_ineligible_is_nan(self):
        df = _frame({"numerical": 1.0, "temporal": 0.55})
        g_ok = df[(df.architecture == "mamba2") & (df.fact_type == "numerical")]
        g_no = df[(df.architecture == "mamba2") & (df.fact_type == "temporal")]
        self.assertTrue(np.isfinite(ra._width_9010(g_ok)))
        self.assertTrue(np.isnan(ra._width_9010(g_no)))

    def test_globally_eligible_requires_all_arms(self):
        df = _frame({"numerical": 1.0, "contradictory": 1.0, "temporal": 0.5,
                     "multi-hop": 0.8, "entity-attribute": 1.0})
        ge = ra.globally_eligible_fact_types(df)
        self.assertEqual(set(ge), {"numerical", "contradictory", "entity-attribute"})


class TestWidthOutputs(unittest.TestCase):
    def setUp(self):
        self.df = _frame({"numerical": 1.0, "contradictory": 1.0, "entity-attribute": 1.0,
                          "temporal": 0.55, "multi-hop": 0.83})

    def test_by_facttype_reports_eligible_with_ci_and_stability(self):
        t = ra.h2_width_by_facttype(self.df, n_resamples=120)
        elig = t[t.eligible]
        self.assertEqual(sorted(elig.fact_type.unique()),
                         ["contradictory", "entity-attribute", "numerical"])
        self.assertEqual(len(elig), 12)  # 3 types x 4 arms
        for r in elig.itertuples():
            self.assertTrue(np.isfinite(r.width_tokens))
            self.assertLessEqual(r.ci_low, r.width_tokens + 1e-6)
            self.assertLessEqual(r.width_tokens - 1e-6, r.ci_high)
            self.assertGreaterEqual(r.frac_finite, 0.5)
        # ineligible types are present but NaN
        self.assertTrue(t[~t.eligible].width_tokens.isna().all())

    def test_summary_is_median_over_globally_eligible(self):
        s = ra.h2_width_summary(self.df, n_resamples=120)
        self.assertEqual(set(s.architecture), {"transformer", "mamba2", "deltanet", "gated_deltanet"})
        self.assertTrue((s["summary"] == "median").all())
        self.assertEqual(s["n_eligible"].unique().tolist(), [3])
        # median matches the median of the per-type point widths
        by = ra.h2_width_by_facttype(self.df, n_resamples=60)
        for arm in s.architecture:
            pts = by[(by.architecture == arm) & by.eligible].width_tokens.to_numpy()
            self.assertAlmostEqual(float(s[s.architecture == arm].median_width_tokens.iloc[0]),
                                   float(np.median(pts)), places=2)

    def test_seed_sensitivity_shape(self):
        w = ra.h2_width_seed_sensitivity(self.df)
        self.assertIn("seed_spread", w["seed"].astype(str).tolist())


class TestHierBootstrapNan(unittest.TestCase):
    def test_matches_frozen_hierarchical_bootstrap_on_finite_statistic(self):
        df = _frame({"numerical": 1.0, "contradictory": 1.0})
        g = df[(df.architecture == "mamba2") & (df.fact_type == "numerical")]
        stat = lambda f: f["correct"].mean()
        a = stats.hierarchical_bootstrap(g, stat, n_resamples=200, random_state=0)
        b = ra._hier_bootstrap_nan(g, stat, n_resamples=200, random_state=0)
        self.assertAlmostEqual(a["point"], b["point"], places=12)
        self.assertAlmostEqual(a["ci_low"], b["ci_low"], places=6)
        self.assertAlmostEqual(a["ci_high"], b["ci_high"], places=6)
        self.assertEqual(b["frac_finite"], 1.0)


class TestH1ExcludeCompoundRelational(unittest.TestCase):
    def test_drops_multihop_six_contrasts_holm(self):
        # all five types pass control validity (non-temporal strict >= 0.85); the
        # transition-region A_transition still differs by the `frac` ramp
        df = _frame({"numerical": 0.95, "temporal": 0.92, "entity-attribute": 0.99,
                     "multi-hop": 0.90, "contradictory": 0.97}, n_items=10)
        res = ra.h1_exclude_compound_relational(df, n_resamples=150)
        self.assertNotIn("multi-hop", res["fact_types"])
        self.assertEqual(len(res["fact_types"]), 4)
        self.assertEqual(res["n_contrasts"], 6)          # C(4,2)
        self.assertIn("p_holm", res["contrasts"].columns)
        self.assertIn("POST-FREEZE SENSITIVITY", res["label"])
        self.assertIsInstance(res["h1_still_supported"], bool)


class TestDeepRecurrentAndResidual(unittest.TestCase):
    def test_deep_recurrent_has_wilson_ci(self):
        df = _frame({ft: 0.9 for ft in _TYPES})
        d = ra.deep_recurrent_retention(df)
        pa = d["per_arm"]
        for col in ("wilson95_low", "wilson95_high", "strict_acc", "abstention_rate"):
            self.assertIn(col, pa.columns)
        self.assertTrue((pa["wilson95_low"] <= pa["strict_acc"] + 1e-9).all())
        self.assertIn("NEGATIVE RESULT", d["label"])

    def test_residual_table_strata(self):
        df = _frame({ft: 0.7 for ft in _TYPES})
        r = ra.residual_fully_exact_failures(df)
        self.assertIn("DESCRIPTIVE ROBUSTNESS", r["label"])
        for k in ("overall", "by_fact_type", "by_architecture",
                  "by_intended_model_tokens_after_target", "by_seed"):
            self.assertIn(k, r)
            self.assertGreater(len(r[k]), 0)


class TestFrozenV10Untouched(unittest.TestCase):
    def test_analysis_versions_distinct(self):
        self.assertEqual(full_run.ANALYSIS_VERSION, "1.0")
        self.assertEqual(ra.ANALYSIS_VERSION, "1.1")

    def test_amendment_does_not_import_or_touch_frozen_outputs(self):
        src = (_ROOT / "src" / "ahnexp" / "reporting_amendment.py").read_text()
        self.assertNotIn("FINAL_LOCKED", src)
        self.assertNotIn("final_summary.json", src)
        # width reference levels are fixed, not lowered
        self.assertEqual((ra.WIDTH_LO_LEVEL, ra.WIDTH_HI_LEVEL), (0.90, 0.10))


if __name__ == "__main__":
    unittest.main(verbosity=2)
