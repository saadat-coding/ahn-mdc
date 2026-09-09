# Appendix A-H2a — H2 transition width (POST-FREEZE REPORTING AMENDMENT, Option A)

| architecture | eligible_fact_types | n_eligible | median_width_tokens | ci_low | ci_high |
| --- | --- | --- | --- | --- | --- |
| AHN-DeltaNet | contradictory, entity-attribute, numerical | 3 | 71.37 | 68.22 | 73.48 |
| AHN-GatedDeltaNet | contradictory, entity-attribute, numerical | 3 | 61.78 | 58.91 | 67.09 |
| AHN-Mamba2 | contradictory, entity-attribute, numerical | 3 | 73.84 | 71.47 | 74.98 |
| Transformer (no AHN) | contradictory, entity-attribute, numerical | 3 | 32.41 | 30.45 | 36.78 |

- The pre-registered POOLED 90→10 width is mathematically UNDEFINED for this dataset: the pooled 5-type strict-accuracy curve peaks ≈ 0.88 and never reaches the 0.90 reference, so the frozen code returns a non-finite interval and falls through to the label 'intermediate'. The frozen result (appAH2a_FROZEN_pooled_width_RECORD_all_NaN.csv) is preserved verbatim.
- Amendment (approved 2026-09-09, commit 626521a; protocol/amendment_h2_transition_width.md): report the 90→10 width for the fact types where the estimator is DEFINED — i.e. the fitted isotonic curve attains ≥ 0.90 AND ≤ 0.10. Eligible for all four arms: contradictory, entity-attribute, numerical. INELIGIBLE: compound-relational (fitted ceiling 0.862 < 0.90) and temporal (0.568 < 0.90) — because their in-window accuracy is capped by abstention, not because of a wide transition.
- Per-arm MEDIAN eligible width (model tokens): Transformer 32.4 [30.5, 36.8]; AHN 61.8–73.8. All ≪ 0.5 W (128) → concentrated. Hierarchical (item→seed) bootstrap, n = 2000; frac_finite = 1.0.
- This is a REPORTING AMENDMENT, not a new frozen primary endpoint.
