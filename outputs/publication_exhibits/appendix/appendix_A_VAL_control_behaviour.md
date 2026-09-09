# Appendix A-VAL — Transformer control behaviour + temporal response bias

| architecture | malformed_rate |
| --- | --- |
| AHN-DeltaNet | 0.0467 |
| AHN-GatedDeltaNet | 0.0136 |
| AHN-Mamba2 | 0.0477 |
| Transformer (no AHN) | 0.3959 |

- Transformer malformed rate: 39.6 % overall, 0.05 % at the in-window control anchors, rising to 59–79 % in the transition band and falling to 3–10 % at the deepest pressures. This is expected no-recurrent-memory degeneration (CONTROL BEHAVIOUR), NOT a pipeline problem: 0 % at anchors, the full re-score is exact, AHN arms on identical prompts are at 1.4–4.8 %.
- NEVER cite the pooled malformed rate (12.6 %) without the per-arm split shown above.
- Temporal control subgroups: answered-valid 0.85 (gold lower-numbered) vs 0.99 (gold higher); 0.87 vs 1.00 (gold not first-listed vs first-listed). This is a model response bias, counterbalanced against the gold (2×2×2 exactly balanced); pooled control answered-valid 0.922.
- Compound-relational control WARNING holds in 7/8 seeds; retained in the H1 primary.
