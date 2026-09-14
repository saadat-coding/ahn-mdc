# Results Traceability

Every bracketed identifier in `manuscript/RESULTS.md` maps to a row below. Source
tables are under `outputs/publication_exhibits/source_tables/` unless a full path
is given; frozen v1.0 outputs are `final_audit/FINAL_LOCKED/final_*`; v1.1
amendment outputs are `outputs/final_v1_1_reporting_amendment/`. All frozen v1.0
values reproduce from the locked parquet
(SHA-256 `a72fd43e87457a70c2833314e1443a794fa4189362ac8206c56275ef427fb62e`) to
≤ 5.7 × 10⁻¹⁴ (`scripts/verify_frozen_v1_0.py`).

Columns: ID · statement (short) · claim-register ID · exhibit · source file ·
source field · statistic · value · CI / p · analysis version · status.

| ID | statement | claim | exhibit | source file | field | statistic | value | CI / p | ver | status |
|---|---|---|---|---|---|---|---|---|---|---|
| R1 | 92,160 trials; 23,040 / architecture; complete cross-product; no missing/dup cells | (design) | A-REPRO, figD | `final_audit/AUDIT_OUTPUTS/phase1_integrity.csv`; `EXHIBIT_MANIFEST.json` | row_count, rows_per_arch, exhaustive_cells, zero_duplicate_cells | exhaustive count | 92160; 23040×4; 0 missing; 0 dup | — | 1.0 | frozen |
| R2 | independent re-score 0 mismatch; frozen analysis reproduces to ≈5.7e-14 | (provenance) | A-REPRO | `final_audit/AUDIT_OUTPUTS/phase2_resume.csv`; `scripts/verify_frozen_v1_0.py` log | rescore==correct/abstained/malformed; max\|Δ\| | count; max abs diff | 0 / 92160; 5.7e-14 | — | 1.0 | frozen |
| R3 | in-window pooled strict accuracy ≈ 0.88 all arms | H2 context | fig2 | `fig2_h2_curves.csv` | accuracy at pressure_group 150/180 | cell mean | 0.879–0.883 | n=1920/cell | 1.0 | frozen |
| R4 | in-window control strict: num/contra/entity ≥ 0.99; compound-rel 0.84; temporal 0.57 (abst 0.38) | VAL-1, VAL-2 | tbl4 | `tbl4_construct_control.csv` / `final_control_validity_control_validity.csv` | in_window_strict, in_window_abstention | pooled anchors 150+180 | 0.999/0.994/1.000; 0.842; 0.568 (0.384) | n=3072/type | 1.0 | frozen |
| R5 | realised model-tat tracks intended to within a few tokens | (design) | figD | `figD_design_grid.csv` | realised_median vs intended_model_tat | median (IQR) | max median error ≈ 6 tok | IQR bars | 1.0 | frozen |
| R6 | A_transition: compound-rel 0.255 < temporal 0.307 < numerical 0.389 < contradictory 0.520 < entity-attr 0.594 | H1-1, H1-2 | tbl1, fig1 | `tbl1_h1_primary.csv` / `final_h1_h1_a_transition.csv` | A_transition_raw_strict | mean strict acc, targets 205–265, AHN pooled | 0.255/0.307/0.389/0.520/0.594 | n=5760/type | 1.0 | frozen |
| R7 | omnibus permutation p = 5e-4 (0/2000, add-one corrected); observed dispersion SD 0.127 | H1-1 | tbl1, fig1 | `final_summary.json` (`h1_omnibus_p`, `extras.h1_omnibus`) | p_value, dispersion_sd, n_perm | label-permutation on SD of 5 means; p = (0+1)/(2000+1) | p = 0.0004998; SD 0.1273 | 0/2000 | 1.0 | frozen |
| R8 | all 10 pairwise contrasts Holm-significant; weakest compound-rel vs temporal −0.052 [−0.099,−0.003] p_holm 0.037; other nine at bootstrap floor → reported p < 0.001 | H1-1 | tbl2 | `tbl2_h1_contrasts.csv` / `final_h1_h1_contrasts.csv` | diff, ci_low, ci_high, p_holm, significant_holm | pairwise A_transition diff; hierarchical bootstrap; Holm/10 | 10/10 sig; −0.052 | [−0.099, −0.003]; p_holm 0.037; nine p_approx=p_holm=0.0 (0/2000) reported as p < 0.001 | 1.0 | frozen |
| R9 | answered-valid A_transition: compound-rel 0.669, contradictory 0.817, numerical 0.824, entity-attr 0.910, temporal 0.925; 2/10 contrasts not sig | H1-1, H1-2 | tbl1, A-H1 | `tbl1_h1_primary.csv` (A_transition_answered_valid); `final_h1_h1_sensitivity_temporal_answered_valid.csv` | A_transition_answered_valid; significant_holm | mean answered-valid acc, targets 205–265, AHN pooled; pairwise diffs | 0.669/0.817/0.824/0.910/0.925; 8/10 sig | contra–num p_holm 1.0; entity–temporal p_holm 1.0 | 1.0 | frozen (per-type recomputed with frozen `a_transition(value='answered_valid')`) |
| R10 | exclude temporal: 6/6 contrasts Holm-significant | H1-1 | A-H1 | `final_h1_h1_sensitivity_excl_temporal.csv` | significant_holm | pairwise diffs; Holm/6 | 6/6 sig | all p_holm ≈ 0 | 1.0 | frozen |
| R11 | exclude compound-relational: 6/6 contrasts Holm-significant; omnibus p = 5e-4 | H1-1 | A-H1 | `h1_sensitivity__exclude_compound_relational__contrasts.csv` + `__meta.json` | n_significant_holm, omnibus_p, omnibus_dispersion_sd | pairwise diffs Holm/6; label-permutation on 4-type SD | 6/6; p = 0.0004998; SD 0.1115 | 0/2000 | 1.1 | **post-freeze sensitivity** |
| R12 | fact-type ordering identical in 7/8 seeds; one seed swaps compound-rel↔temporal; per-type A_transition ±0.03–0.05 across seeds | H1-2 | A-H1 | `robustness__per_seed_headline__a_transition_by_seed.csv` + `__meta.json` | per-seed A_transition; distinct_orderings | count of distinct orderings; per-seed range | 2 distinct orderings; range ≈ 0.03–0.05 | — | 1.1 | **post-freeze robustness** |
| R13 | compound-rel in-window abstention 0.115; temporal 0.384 | H1 caveat, VAL | tbl4 | `final_control_validity_control_validity.csv` | abstention_rate | pooled anchors 150+180 | 0.115; 0.384 | n=3072/type | 1.0 | frozen |
| R14 | A_transition gap (AHN pooled − baseline), [200,270] = +0.249 [0.233, 0.266]; positive every seed | H2-1 | fig2, tbl3 | `final_summary.json` (`h2_a_transition_gap`) | ahn_pooled_minus_transformer, ci_low, ci_high | hierarchical bootstrap, paired within (item,seed) | +0.2494 | [0.2331, 0.2660] | 1.0 | frozen |
| R15 | at intended 220: AHN strict 0.44–0.51 vs baseline 0.18; at 235: AHN 0.51–0.56 vs baseline 0.03 | H2-1 | fig2 | `fig2_h2_curves.csv` | accuracy | cell means per (arch, pressure_group) | 0.438/0.509/0.455 vs 0.184; 0.508/0.557/0.522 vs 0.029 | n=1920/cell | 1.0 | frozen |
| R16 | K_strict: baseline 208.3 [207.1,209.5]; DeltaNet 218.4; Mamba2 219.6; GatedDeltaNet 240.0 | H2-4 | fig2, tbl3 | `final_h2_h2_k_strict.csv` | k_strict_acc, ci_low, ci_high | isotonic 0.5-crossing of pooled strict acc; hierarchical bootstrap | 208.3 / 218.4 / 219.6 / 240.0 | baseline [207.1, 209.5]; GatedDN [220.4, 243.9] | 1.0 | frozen |
| R17 | every K < W = 256 | H2-4 | fig2, tbl3 | `final_h2_h2_k_strict.csv`; `config/experiment.yaml final.window_reference` | k_strict_acc vs 256 | comparison | all K in 208–240 < 256 | — | 1.0/B | frozen |
| R18 | AHN K across-seed spread 21–29 tok vs 1.9 for baseline; AHN K reported as range ≈ 218–240 | H2-4 | A-H2a | `robustness__per_seed_headline__k_strict_by_seed.csv` + `__meta.json` (`k_seed_spread`) | per-seed K; max−min | spread | 25.8 / 29.3 / 21.3 (AHN); 1.9 (baseline) | — | 1.1 | **post-freeze robustness** |
| R19 | abstention knee: AHN 247–251; baseline ≈ 422 | H2-4 | tbl3 | `tbl3_h2_summary.csv` (K_abstention) / recomputed via `h2_threshold.knees` | k_abstention | isotonic 0.5-crossing of abstention rate | 247 / 248 / 251; 422 | — | 1.0 | frozen (recomputed with frozen code from locked parquet) |
| R20 | AIC favours a slope change at W for all four arms; margin thin for baseline (ΔAIC −0.7) vs −2.6 to −8.3 AHN | H2-2 | tbl3 | `final_h2_h2_shape_break_at_W.csv` | verdict, aic_smooth, aic_piecewise | smooth vs break-at-W fit, AIC | change-point favoured ×4; ΔAIC −0.68 (transformer) / −2.64 (mamba2) / −7.41 (deltanet) / −8.28 (gated_deltanet) | point AIC (no CI) | 1.0 | frozen (confirmatory) |
| R21 | pre-registered pooled 90→10 width is non-finite for all four arms; preserved, not interpreted | H2-3 | A-H2a, tbl3 | `final_h2_h2_width.csv` (= `appAH2a_FROZEN_pooled_width_RECORD_all_NaN.csv`) | width_tokens, ci_low, ci_high | isotonic 90→10 width, pooled 5 types | NaN ×4 | — | 1.0 | frozen (record; UNDETERMINED) |
| R22 | per-eligible-type median 90→10 width: baseline 32.4 [30.5,36.8]; GatedDN 61.8; DeltaNet 71.4; Mamba2 73.8; individual widths 29–77 | H2-2, H2-3 | A-H2a | `h2_amend__width_summary_median.csv`; `h2_amend__width_by_facttype.csv` | median_width_tokens, ci_low, ci_high; width_tokens | isotonic 90→10 width per eligible fact type; hierarchical bootstrap; per-arm median | 32.4 / 61.8 / 71.4 / 73.8; range 29.4–77.0 | baseline [30.5, 36.8]; frac_finite 1.0 | 1.1 | **post-freeze reporting amendment** |
| R23 | all eligible widths < 128 (0.5 W); baseline width < every AHN width in every seed | H2-2 | A-H2a | `h2_amend__width_by_facttype.csv`; `h2_amend__width_seed_sensitivity.csv` | width_tokens; per-seed median | comparison to 128; per-seed ordering | max width 77 < 128; baseline lowest every seed | seed spreads 9.3 / 12.7 / 13.0 / 15.2 | 1.1 | **post-freeze reporting amendment** |
| R24 | A_recurrent (targets ≥ 315) 0.0001–0.005, CI reaches 0; all accuracy points at targets ≥ 285 ≤ 0.013 | H2-5 | tbl3, fig2 | `final_h2_h2_a_recurrent.csv`; `fig2_h2_curves.csv` | a_recurrent, ci_low, ci_high; accuracy | mean strict acc; hierarchical bootstrap; cell means | 0.0001 / 0.0007 / 0.0007 / 0.0047; ≤ 0.013 | CIs include 0 | 1.0 | frozen |
| R25 | K (208–240) < W (256); ≈ 32% of fully-in-window trials fail | H2-4, VAL-4 | tbl3, A-H2b | `final_h2_h2_k_strict.csv`; `descriptive__residual_fully_exact_failures__overall.csv` | k_strict_acc; fail_rate | comparison; residual failure rate | K < W; 0.3213 | — | 1.0 (K) / 1.1 (residual) | frozen / **post-freeze descriptive** |
| R26 | appropriate-abstention past W+16: DeltaNet 0.946, Mamba2 0.945, GatedDN 0.929; baseline 0.516 | H3-1 | fig3, A-H3 | `final_h3_h3_behavioral_per_arm.csv` | appropriate_abstention_rate | P(abstained \| model_tat ≥ 272) | 0.946 / 0.945 / 0.929 / 0.516 | n ≈ 10,091 / arm | 1.0 | frozen |
| R27 | unsignalled-failure past W+16: DeltaNet 0.054, Mamba2 0.052, GatedDN 0.071; baseline 0.480 | H3-2 | fig3 | `final_h3_h3_behavioral_per_arm.csv` | unsignalled_failure_rate | P(incorrect-valid ∨ malformed \| model_tat ≥ 272) | 0.054 / 0.052 / 0.071 / 0.480 | n ≈ 10,091 / arm | 1.0 | frozen |
| R28 | 6 AHN-vs-baseline contrasts, magnitude 0.41–0.43, Holm p < 0.001 | H3-1, H3-2 | fig3 | `final_h3_h3_behavioral_contrasts.csv` | diff, ci_low, ci_high, p_holm | AHN − baseline on each rate; hierarchical bootstrap; Holm/6 | \|diff\| 0.41–0.43; p_approx=p_holm=0.0 (0/2000) reported as p < 0.001 | e.g. DeltaNet−baseline abstention +0.430 [0.413, 0.446] | 1.0 | frozen |
| R29 | appropriate-abstention rate stable across seeds (AHN 0.92–0.95, baseline 0.49–0.53) | H3-1 | A-H3 | `robustness__per_seed_headline__h3_appropriate_abstention_by_seed.csv` | per-seed rate | per-seed appropriate-abstention rate | AHN 0.920–0.953; baseline 0.494–0.534 | — | 1.1 | **post-freeze robustness** |
| R30 | baseline past-window composition: 0.52 abstain / 0.45 malformed / 0.03 incorrect-valid / <0.01 correct; AHN mostly abstention, 0.04–0.07 incorrect-valid, ≤0.007 malformed | H3-2 | fig3 | `fig3_h3_outcome_composition_pastW16.csv` | correct, wrong_valid, malformed, abstained | per-trial outcome fractions, model_tat ≥ 272 | baseline 0.0036/0.032/0.448/0.516; AHN correct ≤0.0037 | n = 10,091 / arm | 1.0 | frozen (composition recomputed from locked parquet) |
| R31 | gap_change control→[200,270], answered-valid: baseline −0.018 [−0.051,0.013]; GatedDN −0.063; Mamba2 −0.108; DeltaNet −0.115 | H3-3 | A-H3 | `final_h3_h3_gap_change.csv` | gap_change, ci_low, ci_high | Δ(mean confidence − mean accuracy), answered-valid; hierarchical bootstrap | −0.018 / −0.063 / −0.108 / −0.115 | baseline [−0.051, 0.013] (contains 0); AHN CIs exclude 0 | 1.0 | frozen |
| R32 | answered-valid past window: n=853 pooled at target 265 (baseline n=1); gap ≈ +0.53; CWR 0.92–0.98; < 5% of past-window trials | H3-3 | A-H3 | `final_h3_h3_by_pressure_answered_valid.csv` | n_population, gap, cwr | descriptive on answered-valid trials | n 853; gap +0.527 (265), +0.586 (285); cwr 0.923 / 0.980 | small n | 1.0 | frozen |
| R33 | deep-recurrent (≥ 2W) correct counts: 0 / 0 / 1 / 3 (DeltaNet/GatedDN/Mamba2/baseline); n = 3,542 / arch | H2-5 | tbl5 | `tbl5_deep_recurrent.csv` / `sensitivity__deep_recurrent_retention__per_arm.csv` | correct, n | binomial count | 0 / 0 / 1 / 3; n = 3542 | — | 1.1 | **post-freeze sensitivity (negative result)** |
| R34 | Wilson 95% upper bound ≤ 0.0011 (DeltaNet, GatedDN), 0.0016 (Mamba2), 0.0025 (baseline) | H2-5 | tbl5 | `tbl5_deep_recurrent.csv` | wilson95_high | Wilson score interval, z = 1.96 | 0.00108 / 0.00108 / 0.0016 / 0.00249 | — | 1.1 | **post-freeze sensitivity** |
| R35 | abstention > 0.89 for all arms at ≥ 2W (AHN ≈ 0.98) | H2-5 | tbl5 | `tbl5_deep_recurrent.csv` | abstention_rate | mean | 0.9836 / 0.9788 / 0.9771 / 0.8899 | — | 1.1 | **post-freeze sensitivity** |
| R36 | no fact type shows retention at ≥ 2W; single Mamba2 correct is a temporal item | H2-5 | tbl5 | `sensitivity__deep_recurrent_retention__by_fact_type.csv` | correct by (arch, fact_type) | binomial count | Mamba2 temporal 1/710; all others 0 (AHN) | — | 1.1 | **post-freeze sensitivity** |
| R37 | temporal 2×2×2 exactly balanced (24/24 per factor; 6 items/cell) | VAL-1 | A-VAL | `disclosure__temporal_counterbalancing__balance.csv` | fully_balanced, cells_2x2x2 | design counts | balanced; 6 per cell | — | 1.1 | **post-freeze disclosure** (design property) |
| R38 | temporal control answered-valid: 0.849 (gold lower) vs 0.992 (gold higher); 0.868 (not first) vs 1.000 (first); pooled 0.922 | VAL-1 | A-VAL | `disclosure__temporal_counterbalancing__control_subgroups.csv` + `__meta.json` | answered_valid by subgroup; control_pooled_answered_valid | subgroup means, control anchors | 0.849 / 0.992; 0.868 / 1.000; 0.922 | n = 1,536 / cell | 1.1 | **post-freeze disclosure** |
| R39 | compound-rel in-window: strict 0.842, answered-valid 0.951, abstention 0.115, malformed 0 | VAL-2 | tbl4 | `final_control_validity_control_validity.csv` | strict_accuracy, answered_valid_accuracy, abstention_rate, malformed_rate | pooled anchors 150+180 | 0.842 / 0.951 / 0.115 / 0.0 | n = 3,072 | 1.0 | frozen |
| R40 | WARNING drivers: strict < 0.85 AND abstention > 0.10; FAIL threshold 0.70 not reached; retained in H1 | VAL-2 | tbl4 | `disclosure__compound_relational_control_warning__meta.json` | warning_drivers, fail_threshold_crossed, in_h1_primary | pre-registered gate | strict 0.842 < 0.85; abstention 0.115 > 0.10; fail=false; in_h1=true | — | 1.0/1.1 | frozen rule / **post-freeze disclosure** |
| R41 | WARNING holds 7/8 seeds (control strict 0.77–0.94); 2/48 items below 0.5 control strict | VAL-2 | A-VAL | `disclosure__compound_relational_control_warning__by_seed.csv`; `phase11_multihop_control_by_item.csv` | strict by seed; per-item strict | per-seed / per-item means | 7/8; 2/48 | — | 1.0/1.1 | frozen / **post-freeze disclosure** |
| R42 | Transformer malformed 39.6% overall vs 1.4–4.8% AHN | VAL-3 | A-VAL | `disclosure__transformer_malformed__per_arm.csv` | malformed_rate | per-architecture mean | 0.3959; 0.0136 / 0.0467 / 0.0477 | — | 1.1 | **post-freeze disclosure** |
| R43 | Transformer malformed 0.0% at control anchors; 18–79% at targets 205–380; 3–10% at 520/760 | VAL-3 | A-VAL | `disclosure__transformer_malformed__by_pressure.csv` | rate | per-target mean | 0.0/0.001; 0.177–0.785; 0.098 / 0.028 | n = 1,920 / target | 1.1 | **post-freeze disclosure** |
| R44 | malformed subtypes: over-length 4,580; unrecognised 2,241; empty 1,488; negation 813 | VAL-3 | A-VAL | `disclosure__transformer_malformed__subtypes.csv` | count | frozen scorer branch counts | 4580 / 2241 / 1488 / 813 | — | 1.1 | **post-freeze disclosure** |
| R45 | pooled-across-architecture malformed rate 12.6% reported only with per-arm split | VAL-3 | A-VAL | `disclosure__transformer_malformed__overall.csv` | pooled_across_arms | mean over all arms | 0.126 | — | 1.1 | **post-freeze disclosure** |
| R46 | fully-in-window trials (34,975): 32.1% fail (46% abstain / 39% malformed / 15% incorrect-valid) | VAL-4 | A-H2b | `descriptive__residual_fully_exact_failures__overall.csv` | base_n, fail_rate, share_abstained/malformed/wrong_valid | conditional failure rate + composition | 34,975; 0.3213; 0.462 / 0.385 / 0.153 | — | 1.1 | **post-freeze descriptive** |
| R47 | residual failure 12% at intended 150/180; 34% / 60% / 55% at 205 / 220 / 235; 30–34% every seed | VAL-4 | A-H2b | `descriptive__residual_fully_exact_failures__by_intended_model_tokens_after_target.csv`; `__by_seed` | fail_rate by target / seed | conditional failure rate | 0.120 / 0.118; 0.340 / 0.599 / 0.553; 0.297–0.347 | — | 1.1 | **post-freeze descriptive** |
| R48 | residual failure by type: entity-attr 12%, contradictory 23%, numerical 34%, compound-rel 41%, temporal 52% | VAL-4 | A-H2b | `descriptive__residual_fully_exact_failures__by_fact_type.csv` | fail_rate | conditional failure rate | 0.119 / 0.232 / 0.339 / 0.412 / 0.516 | — | 1.1 | **post-freeze descriptive** |
| R49 | plumbing gates reproduce with 0 blocking; Transformer malformed = control behaviour; compound-rel control = WARNING | (provenance) | A-REPRO | `reproduced__plumbing_gates.csv` | verdict | pre-registered gate outcomes | 0 blocking; CONTROL_BEHAVIOR; WARNING | — | 1.0/1.1 | frozen gate, reproduced |
| R50 | contradictory & numerical A_transition trajectory not strictly monotonic: partial rebound at intended 235 vs 220, consistent in 8/8 seeds and all 3 AHN arms | H1-2 (descriptive) | fig1 | recomputed from locked parquet (`results_FINAL_92160.parquet`), AHN arms pooled, grouped by (fact_type, intended_model_tokens_after_target) and by (seed, intended_model_tokens_after_target) | `correct` | cell mean strict accuracy | contradictory: 0.513→0.676; numerical: 0.333→0.560 (220→235); rebound present in 8/8 seeds and all 3 AHN architectures | n=144/seed·target cell (48 items × 3 arms) | 1.0 | **team-feedback descriptive verification** (recomputed from locked parquet with frozen scoring fields; no new inferential endpoint) |
| R51 | Transformer abstention non-monotonic in pressure: 0.52 (265) → 0.27 (315) → 0.26 (380) → 0.82 (520) → 0.95 (760), mirrored by malformed rate | VAL-3 (descriptive) | fig2 | recomputed from locked parquet, Transformer rows grouped by intended_model_tokens_after_target | `abstained`, `malformed`, `correct` | cell mean rate | abstained 0.518/0.322/0.268/0.263/0.821/0.946 at 265/285/315/380/520/760 | n=1,920/target | 1.0 | **team-feedback descriptive verification** (recomputed from locked parquet; no new inferential endpoint; does not alter the frozen H3 pooled statistic) |

## Untraceable numerical prose

**None.** Every numerical statement in `RESULTS.md` has a row above (51 statements,
51 traced). Five rows use values recomputed from the locked parquet with frozen
scoring fields rather than read directly from a frozen CSV (R9 per-type
answered-valid `A_transition`; R19 `K_abstention`; R30 outcome composition; R50
and R51, added in the team-feedback verification pass below) — these are marked
and reproduce deterministically. All post-freeze quantities are analysis version
1.1 and are labelled as post-freeze in `RESULTS.md`.

**Team-feedback verification pass (2026-09-13).** R50 and R51 were added in
response to teammate observations about apparent non-monotonicity in Figures 1
and 2. Both are **descriptive recomputations from the already-locked, already-
scored raw parquet** (`final_audit/FINAL_LOCKED/results_FINAL_92160.parquet`,
SHA-256 unchanged) using only the existing `correct`/`abstained`/`malformed`
fields and a `groupby`/`mean` — no new model inference, no new statistical test,
no new inferential endpoint, and no change to any frozen or post-freeze primary
result. See `manuscript/FIG1_TRANSITION_VARIABILITY_AUDIT.md` and
`manuscript/FIG2_CONTROL_ABSTENTION_AUDIT.md` for the full descriptive tables
(per-seed, per-architecture breakdowns) supporting R50/R51.

**p-value representation (Revision Pass 1).** No statistical test or estimator
changed. Bootstrap contrast p-values that the frozen analysis records as `0.0`
(0 of 2,000 resamples exceeding the observed statistic; R8 nine of ten contrasts,
R28 all six contrasts) are now written in prose as **p < 0.001** rather than
"p ≈ 0". The H1 omnibus (R7) keeps its frozen add-one–corrected permutation value
**p = (0+1)/(2000+1) = 5×10⁻⁴** (0 of 2,000 permutations). Underlying values in
the frozen CSVs are unchanged.

**Revision Pass 1 — numerical claims.** Old count 49, new count 49; 0 numerical
statements deleted; 0 numerical values changed. Wording-only changes at fixed
value: R7 (note add-one correction), R8 and R28 (p ≈ 0 → p < 0.001), R20 (drop the
word "threshold-like" for the AIC test; report the ΔAIC magnitudes and the thin
baseline margin), R24/R25 (section retitled "Near-zero retrieval accuracy beyond
the window"; "neither … retrieve the target" replaced by a production-evaluation–
bounded statement). Section cross-reference for the H2 amendment updated from
Methods §2.12 to §2.5 (main Methods was condensed; full text in
`METHODS_EXTENDED.md`).

**Compression pass (main-paper compression).** Old count 49, new count 49; **0
numerical statements deleted; 0 numerical values changed.** All 49 R-identifiers
remain in `RESULTS.md`. Terminology: "fact type" → "information type" throughout
`RESULTS.md`; the residual-window diagnostic is now phrased "target span
exact-attention eligible" (was "arithmetically inside the lossless window") — same
computed subset (VAL-4, 34,975 trials), no value change. Detail whose *numeric
values* now live only in the appendix rather than the main prose (the claim and
its appendix pointer remain in the main text): **R9** per-type answered-valid
`A_transition` values (0.669/0.817/0.824/0.910/0.925 → Appendix A-H1; the "2 of 10
contrasts lose significance" statement stays in main text). Every other R-row's
headline figure is still stated in the main Results with an added
"(Appendix …)" source pointer. No surviving numerical statement is untraceable.
