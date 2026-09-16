# Team Feedback Resolution Table

Verification pass against the current manuscript and the canonical final
experiment (4 architectures × 240 items × 8 seeds × 12 pressure targets =
92,160 trials, `final_audit/FINAL_LOCKED/results_FINAL_92160.parquet`, SHA-256
`a72fd43e…`, re-verified unchanged). No new model inference. No frozen
endpoint, hypothesis status, or locked artifact changed.

| # | Feedback item | Source | Valid? | Final-data evidence | Already addressed? | Edit needed? | Action | Scientific impact |
|---|---|---|---|---|---|---|---|---|
| 1 | AHN naming inconsistency (Abstract/RW correct; Methods wrong; old proposal wrong) | teammate | **Yes** | n/a (naming, not data) | No — 2 real errors found | Yes | Fixed `METHODS.md`, `METHODS_EXTENDED.md`, and `paper_site/build.py` `PAPER_TITLE` to "Artificial Hippocampus Network(s) (AHN)"; `README.md`'s old-proposal title left as historical, flagged. See `AHN_NAMING_AUDIT.md`. | NONE (naming only) |
| 2 | Figure 1 jagged/non-monotonic transition curves (numerical, contradictory dip/rebound) | teammate | **Yes** | Rebound at intended target 235 vs 220, consistent in 8/8 seeds and all 3 AHN architectures; not a calibration or subset artifact | Partially — H1 doesn't assume monotonicity, but the pattern wasn't stated | Yes (one sentence) | Added [R50] to `RESULTS.md` §3.2 + traceability row. See `FIG1_TRANSITION_VARIABILITY_AUDIT.md`. | WORDING ONLY (H1 mean-based endpoint unaffected) |
| 3 | Figure 2 Transformer abstention dip around 315-380 | teammate | **Yes** (as a decline-then-rise trajectory; the narrow 315→380 step itself is noise-level) | Abstention falls 265→380 (seed-consistent), jumps sharply at 520-760 (seed-consistent); mirrored by malformed rate; pooled H3 statistic (≥272) reproduces exactly (0.516 control, 0.940 AHN) | Partially — malformed-rate profile already discussed, abstention side was not | Yes (one sentence) | Added [R51] to `RESULTS.md` §3.6 + traceability row. See `FIG2_CONTROL_ABSTENTION_AUDIT.md`. | WORDING ONLY (H3 pooled statistic unchanged) |
| 4 | W is not a hard failure point; W ≠ K; degradation begins before window boundary | teammate | Yes (as a standing requirement) | K < W for every architecture; ~32% residual exact-eligible failures already reported | **Yes — fully already addressed** | No | None. See `W_K_FEEDBACK_AUDIT.md`. | NONE |
| 5 | Malformed output must be reported distinctly from wrong-valid; architectures differ | teammate | Yes (as a standing requirement) | 4 outcomes verified mutually exclusive in the locked parquet (0 overlap rows); malformed reported separately at every point; Transformer 39.6% vs AHN 1.4-4.8% | **Yes — fully already addressed** | No | None. See `MALFORMED_OUTPUT_FEEDBACK_AUDIT.md`. | NONE |
| 6 | H3 must stay behavioural; no "knows it forgot" | teammate | Yes (as a standing requirement) | 0 matches for any mentalistic phrase across the manuscript; both mechanistic alternatives stated in 4 sections | **Yes — fully already addressed** | No | None. See `H3_TEAM_FEEDBACK_AUDIT.md`. | NONE |
| 7 | Temporal answer-position effect / construct validity | teammate | Yes (as a standing requirement) | Position effect measured (0.868 vs 1.000 answered-valid), controlled by a balanced 2×2×2 design, correctly scoped as "nets to chance" (not "eliminated") | **Addressed** | No | None. See `TEMPORAL_CONSTRUCT_FEEDBACK_AUDIT.md`. | NONE |
| 8 | AHN vs Transformer comparison must be system-level, not causal-isolation of recurrent memory | teammate | **Yes** | Confound already stated broadly in Methods/Results/Discussion/Related Work; one Conclusion sentence used mechanism-level subject ("the recurrent path") | Mostly — 1 sentence was not | Yes (one sentence + subject fix) | Fixed `CONCLUSION.md`: "the recurrent path" → "the AHN variants" / "the AHN system," added explicit system-level-comparison sentence. See `SYSTEM_LEVEL_COMPARISON_AUDIT.md`. | WORDING ONLY |
| 9 | Sumiya's pilot comments (50-row pilot, 68% lowest confidence bin, length_normalised, H2/H3 concerns) | teammate (Sumiya) | Valid **for the pilot artifact**; **not applicable** to the final study | `results_pilot.parquet` = 50 rows, 1 architecture (`gated_deltanet`), 1 seed — confirmed superseded; confidence-bin skew confirmed real *for that file* only; final config uses `sequence_probability` (not length-normalised), already flagged "provisional" in Methods/Discussion | Confidence-provisional caveat: **yes, already addressed**. Pilot H2/H3 concerns: **not applicable** (different, pre-freeze grid; self-labelled "NOT inferential evidence") | No | None to the manuscript. Documented classification in `PILOT_VS_FINAL_DATA_AUDIT.md` so the team cannot conflate the 50-row / 1,760-row pilots with the 92,160-trial final study. | NONE |
| 10 | Youssef: Table 4's stated WARNING rule (strict<0.85 or abstention>0.10) appears to apply to temporal (abstention 0.384) but Table 4 reports temporal PASS | teammate (Youssef) | **Yes** (documentation gap) | Rule is pre-registered separately for temporal (`protocol/final_experiment_design.md` §3, commit `356cfef`, 2026-09-05, predates the final GPU run) and correctly implemented (`config/experiment.yaml`, `src/ahnexp/full_run.py::control_validity`); independently recomputed from the locked parquet: temporal answered-valid 0.9218, abstention 0.3841 → PASS, exactly as reported. No bug, no rule violation | Partially — the manuscript stated temporal uses answered-valid accuracy but never disclosed the specific asymmetric abstention threshold ([0.40,0.60] vs. >0.10) that resolves the apparent contradiction | Yes (one sentence + traceability row + Methods/exhibit/site clarification) | Added [R52] to `RESULTS.md` §3.6 + traceability row; clarified `METHODS_EXTENDED.md` §2.13, `tbl4_construct_control` exhibit footnote/caption, `paper_site` Table 4 caption, and the VAL-1 caveat in `final_claims_register.md`. See `manuscript/RESULTS_TRACEABILITY.md` (2026-09-15 documentation clarification pass). | WORDING ONLY (rule, thresholds, code, config, and all frozen/post-freeze numbers unchanged; VAL-1 status unchanged) |

## Summary

- **10 / 10 feedback items resolved** (classified and, where warranted, addressed).
- **4 items required a manuscript edit**: #1 (naming, 3 files), #2 (one sentence
  + traceability row), #3 (one sentence + traceability row), #8 (one sentence +
  subject correction in an already-drafted sentence), #10 (one sentence +
  traceability row + Methods/exhibit/site clarification).
- **5 items were already fully addressed** with no edit needed: #4, #5, #6, #7,
  and the non-pilot-applicable parts of #9.
- **0 items required escalation as a genuine scientific issue (category D).**
- **0 items were false positives requiring no classification** — every item
  mapped to categories A, B, C, or E as defined in the task.
- **No hypothesis status, statistical endpoint, or locked/frozen artifact was
  changed.** Three new descriptive result rows (R50, R51, R52) were added; all
  are recomputations/clarifications from the already-locked, already-scored raw
  parquet and pre-registered protocol documents, not new inferential endpoints.
