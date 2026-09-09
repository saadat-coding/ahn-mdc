# Table 3 — H2 architecture summary

| architecture | K_strict | K_abstention | shape_vs_smooth | A_recurrent |
| --- | --- | --- | --- | --- |
| Transformer (no AHN) | 208.3 [207.1, 209.5] | 422 | threshold-like (ΔAIC -0.7) | 0.0047 [0.0022, 0.0078] |
| AHN-Mamba2 | 219.6 [217.2, 237.5] | 247 | threshold-like (ΔAIC -2.6) | 0.0007 [0.0000, 0.0017] |
| AHN-DeltaNet | 218.4 [215.9, 236.9] | 248 | threshold-like (ΔAIC -7.4) | 0.0001 [0.0000, 0.0005] |
| AHN-GatedDeltaNet | 240.0 [220.4, 243.9] | 251 | threshold-like (ΔAIC -8.3) | 0.0007 [0.0000, 0.0016] |

- A_transition gap (AHN pooled − Transformer) over [200, 270] = +0.249 [0.233, 0.266] (hierarchical bootstrap 95% CI; CI excludes 0).
- K is a DESCRIPTIVE empirical knee (0.5 crossing), NOT a threshold; W = 256 is the architectural window. Every K < W.
- The pre-registered pooled 90→10 transition-width statistic is UNDEFINED for this dataset (the pooled 5-type curve peaks ≈ 0.88, below the 0.90 reference) — see the post-freeze reporting amendment (Table A-H2a / protocol/amendment_h2_transition_width.md). It is not reported here and the frozen 'intermediate' label is not used.
- shape vs smooth: piecewise fit with break fixed at W = 256, AIC comparison (frozen v1.0).
- K_abstention recomputed from the locked parquet with frozen h2_threshold.knees.
