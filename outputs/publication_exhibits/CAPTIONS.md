# Publication Exhibit Captions

Draft captions for each exhibit. Every number traces to the exhibit's source table(s) (see EXHIBIT_MANIFEST.json). Terminology: internal data key "multi-hop" is reported as "compound-relational".

## figD_experimental_design  (MAIN)
*Experimental design / memory-pressure setup* — claims: (design)

Top: schematic of one tokenised evaluation trajectory. A distractor context precedes the target span (median 15.5 tokens); model_tokens_after_target counts every token after the target span (distractors, the question and instruction, and the chat-template suffix) and is the pressure coordinate. W = 256 is the architectural sliding-window reference. Bottom: the 12 frozen intended pressure targets (grouping key, x-axis) against the realised model_tokens_after_target they produced (median and inter-quartile range over n = 7,680 trials per level); per-fact-type filler was calibrated with the base tokenizer so that realised closely tracks intended. Two targets fall in the control band, six in the transition band, four in the recurrent band. The full grid is 4 architectures x 240 items x 12 targets x 8 seeds = 92,160 trials.

## fig1_h1_nonuniform_degradation  (MAIN)
*H1: non-uniform degradation across information types* — claims: H1-1, H1-2

Strict production accuracy versus realised model_tokens_after_target for each fact type, pooled over the three AHN architectures (n = 5,760 per point). The y-axis is end-to-end task accuracy under the strict production metric: a trial counts as correct only if the model emits exactly the gold value, so abstentions (“I don't know”) and malformed outputs both count as failures. Curves are raw cell means (no fit). W = 256 is the architectural sliding-window reference, not a threshold. The shaded region marks the intended targets (205–265) averaged for A_transition. The five-way spread of A_transition means exceeds label-permutation chance (p = 5×10⁻⁴, 0/2000). The ordering is partly metric-dependent: under answered-valid accuracy it compresses (Table 1, Appendix A-H1). Internal data key “multi-hop” is reported as “compound-relational”.

## tbl1_h1_primary  (MAIN)
*H1 primary result* — claims: H1-1, H1-2

H1 primary endpoint. A_transition is the mean strict production accuracy over the five intended transition targets (205-265), pooled over the three AHN architectures (n = 5,760 per fact type). Raw strict accuracy is the pre-registered primary metric (no chance correction). The answered-valid column (accuracy computed only over trials that produced a parseable answer) is a pre-registered secondary sensitivity, shown for context, not a replacement. In-window control columns are pooled over intended targets 150 and 180 (n = 3,072 per fact type). The label-permutation omnibus on the dispersion of the five A_transition means gives p = 5x10^-4 (0/2000 permutations).

## tbl2_h1_contrasts  (MAIN)
*H1 pairwise contrasts* — claims: H1-1

All ten pairwise fact-type differences in A_transition, with 95% hierarchical (item then seed) cluster-bootstrap intervals (2,000 resamples) and Holm-adjusted two-sided bootstrap p-values over the ten-comparison family. All ten intervals exclude zero; the closest to the boundary is compound-relational versus temporal (p_holm = 0.037).

## fig2_h2_architecture_curves  (MAIN)
*H2: architecture degradation curves with W and K* — claims: H2-1, H2-2, H2-4, H2-5

Top: strict production accuracy versus realised model_tokens_after_target for each architecture (n = 1,920 per point; 95% bootstrap CI band). The vertical dashed line is the architectural sliding-window reference W = 256. The diamonds with horizontal bars near the axis floor are the empirical performance knee K per architecture (isotonic 0.5-crossing of pooled strict accuracy; 95% hierarchical bootstrap CI) — a descriptive location, not a threshold, and distinct from W. Every K (208–240) lies below W. In the near-window band [200, 270] the AHN architectures retain +0.25 more accuracy than the no-recurrent-memory baseline (95% CI [0.23, 0.27]). Past W all four architectures fall to ≈ 0 (A_recurrent ≈ 0; Table 3). Bottom: abstention rate over all trials, same x-axis. The pre-registered pooled transition-width statistic was mathematically undefined for this dataset and is not shown (Table 3; Appendix A-H2a).

## tbl3_h2_summary  (MAIN)
*H2 architecture summary* — claims: H2-1, H2-2, H2-4, H2-5

Per-architecture H2 summary. K_strict and K_abstention are the isotonic 0.5-crossings of pooled strict accuracy and of abstention rate against realised model_tokens_after_target; they are descriptive empirical knees, not thresholds, and are distinct from the architectural reference W = 256. Every K_strict lies below W. shape_vs_smooth compares a smooth log-linear fit with a fit allowed to change slope at W, by AIC (negative delta favours the change-point fit). A_recurrent is the mean strict accuracy over intended targets >= 315 with a 95% bootstrap interval. The A_transition gap (AHN pooled minus baseline) over [200, 270] is +0.249 [0.233, 0.266]. The pre-registered pooled 90-to-10 transition-width statistic was mathematically undefined for this dataset and is not reported here (Appendix A-H2a).

## fig3_h3_behavioural_signalling  (MAIN)
*H3: behavioural uncertainty signalling* — claims: H3-1, H3-2

Behaviour on trials past the sliding-window reference (realised model_tokens_after_target ≥ W + 16 = 272; n ≈ 10,091 per architecture). Left: the four mutually exclusive per-trial outcomes — correct factual answer, incorrect valid answer, malformed output, abstention (“I don't know”) — as stacked fractions. Correct factual answers are below 1% for every architecture in this region (maximum 0.37%, Transformer), so the correct segment is not visible; essentially no architecture retrieves the target past the window. Right: the two frozen H3 behavioural-primary rates per architecture — appropriate abstention rate = P(abstained), and unsignalled failure rate = P(incorrect-valid ∨ malformed). Each AHN architecture differs from the no-recurrent-memory baseline by |Δ| ≈ 0.42 (all six contrasts Holm-adjusted p ≈ 0; the ordering is identical in all 8 seeds). This is a description of behaviour; it does not identify an internal mechanism.

## tbl4_construct_control  (MAIN)
*Construct / control-validity table* — claims: VAL-1, VAL-2

Fact-type constructs and in-window (control) retrieval, pooled over intended targets 150 and 180 (n = 3,072 per fact type). compound-relational (internal data key multi-hop) is a single co-located two-clause sentence with a query that needs both clauses; it is not a benchmark of multi-hop reasoning across separated facts. Its control retrieval reaches only 0.842 (0.951 among answered trials; 0.115 abstention), which triggers a pre-registered WARNING (strict < 0.85 and abstention > 0.10); the FAIL threshold of 0.70 was not reached, so the type is retained in the H1 primary. Control-validity criteria were preregistered separately for temporal items: rather than the non-temporal WARNING rule above, temporal is judged on answered-valid accuracy (PASS >= 0.85), with abstention assessed separately against its own preregistered WARNING interval of [0.40, 0.60]. Temporal answered-valid accuracy (0.922) and abstention (0.384) both fall on the PASS side of this criterion (Results [R52]).

## tbl5_deep_recurrent  (MAIN)
*Deep-recurrent negative-retention result* — claims: H2-5 — POST-FREEZE SENSITIVITY (NEGATIVE RESULT)

Retrieval at deep recurrent pressure: realised model_tokens_after_target >= 512 (twice W), n = 3,542 per architecture. Correct counts are 0 (DeltaNet, GatedDeltaNet), 1 (Mamba2), and 3 (baseline); Wilson 95% upper bounds are at or below 0.25%. Abstention exceeds 89% for all four. No measurable target-specific factual retention was observed at deep recurrent pressure under the production evaluation.

## appendix_A_H1_sensitivities  (APPENDIX)
*H1 sensitivities* — claims: H1-1, H1-2 — mixed: exclude-compound-relational is POST-FREEZE SENSITIVITY

(caption in exhibit notes)

## appendix_A_H2a_transition_width_amendment  (APPENDIX)
*H2 transition-width amendment (Option A)* — claims: H2-2, H2-3 — POST-FREEZE REPORTING AMENDMENT (Option A)

(caption in exhibit notes)

## appendix_A_H2b_residual_exact_failures  (APPENDIX)
*Residual exact-memory failures* — claims: VAL-4 — DESCRIPTIVE ROBUSTNESS / LIMITATION

(caption in exhibit notes)

## appendix_A_H3_calibration_detail  (APPENDIX)
*H3 calibration detail* — claims: H3-3, H3-1

(caption in exhibit notes)

## appendix_A_VAL_control_behaviour  (APPENDIX)
*Transformer control + temporal bias* — claims: VAL-1, VAL-3, VAL-2 — LIMITATION / DISCLOSURE

(caption in exhibit notes)

## appendix_A_REPRO_integrity  (APPENDIX)
*Integrity & reproducibility statement* — claims: (provenance)

(caption in exhibit notes)

