# Final Exhibit Plan

Compact plan mapping the locked experiment to manuscript tables/figures.
**No figures generated yet.** Venue budget (`config/experiment.yaml outputs.venue_budget`):
6 tables + 4 figures. Plan: **7 main exhibits + 6 appendix**.

All source paths are under `final_audit/FINAL_LOCKED/` (frozen) or
`final_audit/AUDIT_OUTPUTS/` (audit-reproduced / post-freeze). Every value
reproduces from the locked parquet to \|Δ\| ≤ 1e-14.

Conventions for every exhibit:
- x-axis for any pressure plot = **realised `model_tokens_after_target`** (median per intended level); the intended target is the grouping key.
- draw **W = 256** as a vertical reference line, labelled "architectural window (W)", never "threshold".
- if K is drawn, label it "empirical knee (K)" and show its CI as a band; **W and K are visually distinct**.
- accuracy = **raw strict** unless the caption says "answered-valid".

---

## MAIN EXHIBITS

### Figure 1 — Non-uniform degradation across fact types
- **Number/type:** Figure 1 (line plot, 1 panel, 5 lines; optional 5-panel small-multiple)
- **Hypothesis:** H1 (H1-1, H1-2)
- **Variables:** x = realised model-tat; y = strict accuracy; series = fact type; data = **3 AHN arms pooled** (transformer excluded, matches the frozen endpoint).
- **Source:** `final_audit/AUDIT_OUTPUTS/phase3_arch_x_pressure_x_facttype.csv` (filter AHN arms, pool) → or recompute; A_transition band [205–265] shaded.
- **Statistical annotations:** shade the transition targets 205–265; annotate each line's A_transition value (from `final_h1_h1_a_transition.csv`); footnote omnibus p = 0.0005.
- **Placement:** MAIN.
- **Reader should conclude:** the five curves separate clearly in the transition band — degradation rate depends on fact type; compound-relational collapses first, entity-attribute last.
- **Must NOT imply:** that the y-axis is "information retained" (it is task accuracy, includes abstention); that the ordering is metric-independent (see Table 1 answered-valid column).

### Table 1 — H1 primary result
- **Number/type:** Table 1
- **Hypothesis:** H1 (H1-1, H1-2)
- **Variables (rows = 5 fact types):** construct label · n (5760) · **A_transition (raw strict)** · A_transition (answered-valid) · in-window control strict · in-window abstention.
- **Source:** `final_h1_h1_a_transition.csv`; answered-valid column from `final_h1_h1_sensitivity_temporal_answered_valid.csv` recomputed as per-type means (or `AUDIT_OUTPUTS/repro_h1_temporal_av.csv`); control columns from `final_control_validity_control_validity.csv`.
- **Statistical annotations:** header note: "label-permutation omnibus on the SD of the five A_transition means: p = 5×10⁻⁴ (0/2000)"; footnote: raw strict is the frozen primary (Policy A).
- **Placement:** MAIN.
- **Reader should conclude:** the raw-strict spread (0.255–0.594) is large and significant; under answered-valid the spread narrows but compound-relational stays lowest.
- **Must NOT imply:** a chance-corrected metric exists; that temporal/multi-hop ranks are pure memory effects (control + abstention columns show otherwise).

### Table 2 — H1 pairwise contrasts
- **Number/type:** Table 2
- **Hypothesis:** H1 (H1-1)
- **Variables (10 rows):** fact-type pair · diff · 95 % CI · p_holm · significant.
- **Source:** `final_h1_h1_contrasts.csv`.
- **Statistical annotations:** "hierarchical (item→seed) cluster bootstrap, 2000 resamples; Holm over 10 contrasts"; bold the row that is closest to non-significance (multi-hop vs temporal, p_holm 0.037).
- **Placement:** MAIN (or fold into Table 1 as CI columns if space-tight).
- **Reader should conclude:** every pairwise fact-type difference survives multiplicity correction.
- **Must NOT imply:** that a single non-significant contrast anywhere would sink H1 (the omnibus + 9 others stand).

### Figure 2 — Architecture transition curves (H2 core)
- **Number/type:** Figure 2 (line plot, 4 arms; twin y for abstention OR a stacked 2-row panel: top = strict accuracy, bottom = abstention rate)
- **Hypothesis:** H2 (H2-1, H2-2, H2-4, H2-5)
- **Variables:** x = realised model-tat (150–760, log or broken axis); y_top = strict accuracy; y_bottom = abstention rate; series = architecture (4). W line; per-arm K_strict marker + CI band.
- **Source:** `final_h2_h2_curves.csv` (accuracy + CIs); abstention from `final_h3_h3_abstention_confidence.csv` or `AUDIT_OUTPUTS/phase3_arch_x_pressure.csv`; K from `final_h2_h2_k_strict.csv`.
- **Statistical annotations:** shade [200, 270]; annotate the A_transition gap "+0.25 [0.23, 0.27]" in that band; mark K for each arm; mark W; note "past W: all arms ≈ 0 (A_recurrent ≈ 0)".
- **Placement:** MAIN — this is the paper's key figure.
- **Reader should conclude:** all four collapse sharply just below/at W; AHN arms hold ≈ 0.25 more accuracy in [200,270] and their knee is ≈ 10–35 tokens later than the transformer's; nothing survives past W.
- **Must NOT imply:** a width/"intermediate" classification (omit the frozen width entirely); that K = W; that AHN retains anything past W.

### Table 3 — H2 architecture summary
- **Number/type:** Table 3
- **Hypothesis:** H2 (H2-1, H2-2, H2-4, H2-5)
- **Variables (rows = 4 arms):** K_strict [CI] · K_abstention · shape-test verdict (ΔAIC) · A_recurrent [CI] · (A_transition gap: single cell "AHN pooled − transformer = +0.249 [0.233, 0.266]").
- **Source:** `final_h2_h2_k_strict.csv`, `AUDIT_OUTPUTS/repro_h2_knees_by_arm.csv` (K_abstention), `final_h2_h2_shape_break_at_W.csv`, `final_h2_h2_a_recurrent.csv`, `final_summary.json` (gap).
- **Statistical annotations:** footnote: "transition width (pre-registered pooled 90→10 statistic) is undefined for this dataset — see [amendment]; shape is characterised by the shape test and per-type widths (Appendix)."; footnote: "K is a descriptive knee, not a threshold; W = 256 is the architectural window."
- **Placement:** MAIN.
- **Reader should conclude:** every K < W; shape is threshold-like for all; AHN abstention-knee is ≈ 170 tokens earlier than the transformer's; deep-recurrent accuracy ≈ 0.
- **Must NOT imply:** the frozen "intermediate" width verdict (do not include that column).

### Figure 3 — Behavioural uncertainty signalling (H3 headline)
- **Number/type:** Figure 3 (2 panels: appropriate-abstention rate and unsignalled-failure rate, each vs realised model-tat, 4 arms) — OR a bar chart of the two rates per arm in the ≥ W+16 region with CIs.
- **Hypothesis:** H3 (H3-1, H3-2)
- **Variables:** x = realised model-tat (or arm); y = rate; series = architecture.
- **Source:** `final_h3_h3_behavioral_per_arm.csv` (the ≥ 272 region point + CI); pressure-resolved abstention from `final_h3_h3_abstention_confidence.csv`.
- **Statistical annotations:** mark W + 16 = 272 (the frozen region boundary); annotate contrasts "AHN − transformer ≈ +0.42, p_holm = 0"; note "identical across all 8 seeds".
- **Placement:** MAIN.
- **Reader should conclude:** past the window, AHN arms overwhelmingly abstain (≈ 94 %) while the transformer answers/degenerates (≈ 52 % abstention, 48 % unsignalled failure).
- **Must NOT imply:** the recurrent state "knows" (H3-4); that AHN factual confidence is well calibrated (H3-3).

### Table 4 — Construct / control-validity table
- **Number/type:** Table 4
- **Hypothesis:** validation (VAL-1, VAL-2) + context for H1
- **Variables (rows = 5 fact types):** construct · example query · answer form · in-window strict · in-window answered-valid · in-window abstention · in-window malformed · control verdict.
- **Source:** `final_control_validity_control_validity.csv` + `config/facts.yaml` (example/form).
- **Statistical annotations:** flag multi-hop = WARNING with the driver ("strict 0.84 < 0.85 and abstention 0.115 > 0.10; retained in H1 primary, FAIL threshold 0.70 not reached"); flag temporal answered-valid 0.92 / abstention 0.38.
- **Placement:** MAIN (compact) — establishes construct validity before the results.
- **Reader should conclude:** four types have near-ceiling in-window retrieval; compound-relational has a task-difficulty ceiling (0.84); temporal has high in-window abstention.
- **Must NOT imply:** that multi-hop tests multi-hop reasoning; that temporal is invalid.

---

## APPENDIX / SUPPLEMENT

### Appendix A-H1 — H1 sensitivities
- **Hypothesis:** H1
- **Variables:** three sub-tables — exclude-temporal (6 contrasts), exclude-multi-hop (6 contrasts, **post-freeze**), answered-valid all-types (10 contrasts); plus A_transition per type × per seed (8×5).
- **Source:** `final_h1_h1_sensitivity_excl_temporal.csv`, `AUDIT_OUTPUTS/repro_h1_excl_multihop.csv`, `final_h1_h1_sensitivity_temporal_answered_valid.csv`, `AUDIT_OUTPUTS/phase13_a_transition_by_seed.csv`.
- **Annotations:** label exclude-multi-hop "[POST-FREEZE SENSITIVITY]"; note the answered-valid table is all-types (filename says "temporal" — it is not).
- **Reader should conclude:** H1 survives every exclusion and is seed-stable (7/8 orderings identical).

### Appendix A-H2a — H2 shape detail (post-freeze amendment table)
- **Hypothesis:** H2 (H2-2, H2-3)
- **Variables:** per-(architecture, closed-set fact type) isotonic 90→10 width + fresh bootstrap CI; per-fact-type K; per-seed K per arm.
- **Source:** `AUDIT_OUTPUTS/auditorC_h2_per_facttype_transition_width.csv`, `AUDIT_OUTPUTS/repro_h2_knees_by_facttype.csv`, `AUDIT_OUTPUTS/phase13_k_by_seed.csv`.
- **Annotations:** header: "The pre-registered pooled width is undefined (Appendix A-H2a note / [amendment]). Reported here: 90→10 width for the three fact types whose in-window ceiling permits it." Show the frozen `final_h2_h2_width.csv` (all NaN) verbatim as the record.
- **Reader should conclude:** on every defined view the collapse is concentrated (widths 33–69 tokens); AHN K is seed-variable (spread 21–29) so it is an interval, not a point.

### Appendix A-H2b — Residual exact-memory failures (VAL-4)
- **Hypothesis:** validation (VAL-4)
- **Variables:** residual-failure rate among `target_fully_exact_through_generation == True`, stratified by fact type, architecture, intended target, seed; composition (abstain/malformed/wrong-valid).
- **Source:** `AUDIT_OUTPUTS/phase8_residual_exact_failures.csv` (+ the summary strata in `protocol/final_reporting_additions.md` §2).
- **Annotations:** "[LIMITATION]"; highlight intended 220 = 59.9 %.
- **Reader should conclude:** the pressure axis is a proxy — near-window failure is not solely the exact→compressed transition.

### Appendix A-H3 — H3 calibration detail
- **Hypothesis:** H3 (H3-3)
- **Variables:** gap_change per arm [CI]; ECE / Brier / CWR / gap by pressure (answered-valid, pooled); abstention-confidence by pressure per arm; behavioural rates per seed per arm.
- **Source:** `final_h3_h3_gap_change.csv`, `final_h3_h3_by_pressure_answered_valid.csv`, `final_h3_h3_abstention_confidence.csv`, `AUDIT_OUTPUTS/phase13_h3_abst_by_seed.csv`.
- **Annotations:** flag the deep-pressure rows as "n_population small; not a headline"; note confidence = sequence_probability (PROVISIONAL).
- **Reader should conclude:** behavioural signalling is seed-stable; "overconfident when wrong" is a small-n deep-pressure effect.

### Appendix A-VAL — Transformer control + temporal bias
- **Hypothesis:** validation (VAL-1, VAL-3)
- **Variables:** transformer malformed rate by intended pressure + by fact type + subtype counts; temporal answered-valid accuracy / abstention by nuisance subgroup at control.
- **Source:** `AUDIT_OUTPUTS/phase4_transformer_malformed_by_pressure.csv`, `phase4_transformer_malformed_by_facttype.csv`, `phase4_transformer_malformed_rows.csv` (subtype), `phase10_temporal_subgroups.csv`.
- **Annotations:** "transformer malformed = expected no-memory degeneration; 0 % at anchors; per-arm split (never pooled)"; "temporal bias counterbalanced".
- **Reader should conclude:** neither is a pipeline problem.

### Appendix A-REPRO — Integrity & reproducibility statement
- **Hypothesis:** none — provenance
- **Variables:** SHA-256; row/arm/cell counts; re-score mismatch count (0/92,160); frozen-vs-reproduced max \|Δ\| (5.7e-14); plumbing gates (0 blocking); runtime-commit note.
- **Source:** `AUDIT_OUTPUTS/phase1_integrity.csv`, `phase2_resume.csv`, `phase14_frozen_vs_repro_diffs.csv`, `repro_plumbing_gates.csv`, `AUDIT_REPORT.md`.
- **Annotations:** state the `d29c6d8` runtime-commit gap and the three hash-equivalence mitigations.
- **Reader should conclude:** the artifact is verified and the analysis is deterministically reproducible.

---

## Exhibit count check

| slot | exhibits |
|---|---|
| MAIN figures | F1, F2, F3 (3 of 4 budgeted) |
| MAIN tables | T1, T2, T3, T4 (4 of 6 budgeted) — T2 can merge into T1 if needed |
| APPENDIX | A-H1, A-H2a, A-H2b, A-H3, A-VAL, A-REPRO |

Room for one more main figure if a reviewer wants a per-seed forest plot of the
H1 contrasts or the H3 behavioural contrasts.
