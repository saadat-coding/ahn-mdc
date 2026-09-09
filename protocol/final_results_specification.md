# Final Results Specification — experiment → paper

**Status:** authoritative map from the locked 92,160-trial experiment to what the
manuscript may claim. Produced 2026-09-09 after the hostile final audit
(`final_audit/AUDIT_OUTPUTS/AUDIT_REPORT.md`).

**Locked artifact:** `final_audit/FINAL_LOCKED/results_FINAL_92160.parquet`
SHA-256 `a72fd43e87457a70c2833314e1443a794fa4189362ac8206c56275ef427fb62e` (verified).
**Frozen design:** `protocol/final_experiment_design.md`, `config/experiment.yaml` `final:`,
`config/final_design_manifest.json`.
**Analysis code:** `src/ahnexp/{h1_degradation,h2_threshold,h3_calibration,full_run}.py`,
`analysis_version = "1.0"`.

### Analysis-status vocabulary (used throughout)

| tag | meaning |
|---|---|
| **[FROZEN PRIMARY]** | pre-registered primary endpoint/test; result is what it is |
| **[FROZEN SECONDARY]** | pre-registered secondary analysis in `protocol/final_experiment_design.md` |
| **[POST-FREEZE SENSITIVITY]** | new analysis computed from the *locked* artifact only; supports/qualifies, never replaces a primary |
| **[POST-FREEZE REPORTING AMENDMENT]** | correction to a reporting *metric* that returned an undefined/misleading value; requires the decision document + team sign-off |
| **[LIMITATION]** | disclosed constraint on interpretation; no new analysis |

A reporting amendment **may not** retroactively replace an inconvenient primary
endpoint. Raw strict production accuracy stays the H1/H2 primary accuracy endpoint
(#17 Policy A, `config/facts.yaml`, `protocol/final_experiment_design.md` §5).

Evidence-label key: **[A]** calculated from the locked artifact · **[B]** frozen
code/config · **[C]** interpretation · **[D]** unresolved / team decision.

---

# H1 — Non-uniform degradation across information types

| # | field | specification |
|---|---|---|
| 1 | **Scientific question** | Do different fact types lose retrievability at different rates as memory pressure rises? |
| 2 | **Exact hypothesis** | The five fact types do not degrade uniformly across the pre-registered transition region. |
| 3 | **Primary endpoint** | `A_transition(type)` = mean **raw strict production accuracy** over intended model-tat targets **[205, 220, 235, 250, 265]**, pooling the three AHN arms (transformer excluded — reference curve). [FROZEN PRIMARY] · `h1_degradation.a_transition` · `full_run.analyse` L506 |
| 4 | **Unit of analysis** | item cluster (240), with seed realisations nested within item; matched architecture × pressure rows travel with the (item, seed) unit. `stats.hierarchical_bootstrap` (`primary_cluster: item_id`, `secondary_cluster: seed`, `config/experiment.yaml statistics`). |
| 5 | **Pressure region** | intended targets 205–265 (five levels); realised `model_tokens_after_target` medians ≈ 202–267 (`final_h2_h2_curves.csv`). |
| 6 | **Statistical test** | Primary: 10 pairwise fact-type `A_transition` differences, 2-level hierarchical cluster bootstrap, 2000 resamples, percentile 95 % CI (`h1_degradation.a_transition_contrasts`). Companion: fact-type-label permutation test on the SD of the five means, 2000 permutations (`h1_degradation.a_transition_omnibus`). [FROZEN PRIMARY] + [FROZEN SECONDARY companion] |
| 7 | **Multiplicity** | Holm within the 10-contrast family. **H1 supported iff ≥ 1 Holm-adjusted CI excludes 0.** |
| 8 | **Uncertainty interval** | percentile 95 % hierarchical-bootstrap CI on each pairwise difference; `random_state = 0` (deterministic, reproduced exactly by the audit). |
| 9 | **Frozen headline result [A]** | omnibus dispersion SD **0.1273**, permutation **p = 0.0005** (0/2000) (`final_summary.json` `h1_omnibus_p`, `extras.h1_omnibus`). A_transition: multi-hop **0.255** < temporal **0.307** < numerical **0.389** < contradictory **0.520** < entity-attribute **0.594** (`final_h1_h1_a_transition.csv`). **All 10 pairwise Holm-adjusted CIs exclude 0**; weakest contrast multi-hop vs temporal, diff −0.052 [−0.099, −0.003], p_holm 0.037 (`final_h1_h1_contrasts.csv`). |
| 10 | **Approved interpretation** | "Under sustained memory pressure, fact types degrade non-uniformly **in end-to-end task accuracy**. Compound-relational targets degrade fastest and entity-attribute targets are most robust; the five-way spread is far larger than label-permutation chance (p = 5×10⁻⁴)." The degradation measured here is *task-performance* degradation — a compound of retrieval failure, abstention propensity, and (for the transformer, not pooled here) malformed output. It is **not** a pure measure of representational information loss. [C] |
| 11 | **Prohibited overinterpretation** | ✗ "fact types are *forgotten* / *lost from the representation* at different rates" (raw strict conflates retrieval loss with abstention — see §12). ✗ any ordering statement that ignores the answered-valid sensitivity. ✗ treating multi-hop's rank as pure memory decay (it inherits a lower in-window ceiling — VAL-2). ✗ introducing a chance baseline or chance-corrected primary (Policy A). ✗ describing temporal's low rank without stating its 38 % in-window abstention. |
| 12 | **Required sensitivity analyses** | (a) **exclude temporal** — [FROZEN SECONDARY], `final_h1_h1_sensitivity_excl_temporal.csv`: 6/6 contrasts Holm-significant. (b) **answered-valid A_transition, all types** — [FROZEN SECONDARY], `final_h1_h1_sensitivity_temporal_answered_valid.csv` (filename is misleading — it is *all-types* answered-valid, not temporal-only; see `amendment`/provenance): **8/10 significant**; contradictory≈numerical (p_holm 1.0) and entity-attribute≈temporal (p_holm 1.0) converge; multi-hop remains robustly lowest. (c) **exclude multi-hop** — [POST-FREEZE SENSITIVITY], `final_audit/AUDIT_OUTPUTS/repro_h1_excl_multihop.csv`: 6/6 contrasts Holm-significant. (d) **seed robustness** — [POST-FREEZE SENSITIVITY], `final_audit/AUDIT_OUTPUTS/phase13_a_transition_by_seed.csv`: fact-type ordering identical in 7/8 seeds; seed 3 swaps only the multi-hop↔temporal pair (0.271 vs 0.238); per-type A_transition varies ±0.03–0.05. |
| 13 | **Required limitation / disclosure** | [LIMITATION] Raw strict `A_transition` blends retrieval failure with abstention propensity. The two lowest-ranked types (multi-hop, temporal) are also the two with elevated in-window abstention (11.5 %, 38.4 % — `final_control_validity_control_validity.csv`). Under answered-valid the spread partially collapses. The manuscript must present sensitivity (b) beside the primary and frame H1 as task-accuracy degradation. [LIMITATION] Temporal raw strict is abstention-dominated (66 % abstention overall — `phase10_temporal_subgroups` / audit Phase 10). |
| 14 | **Supporting exhibits** | Table T1 (A_transition + 5-way, omnibus p); Figure F1 (per-type strict-accuracy curves vs realised model-tat); Table T2 (10 pairwise contrasts, Holm); appendix Table A-H1 (three sensitivities + per-seed). See `protocol/final_exhibit_plan.md`. |

**Manuscript terminology for `multi-hop`:** the internal key `multi-hop` is
**unchanged** in code, data, scorer, and `chance` map (reproducibility). Manuscript
language uses **"compound relational"** (already the `construct` field in
`config/facts.yaml` and `report.fact_type_label`). Rationale: the target is one
co-located two-clause sentence ("A manages B. B works for C." → *which company does
A's subordinate work for?*); the query needs both clauses of that single moving
span, **not** retrieval across separated facts. Do not silently rename stored data.

---

# H2 — Concentrated vs gradual collapse, and architecture comparison

| # | field | specification |
|---|---|---|
| 1 | **Scientific question** | Is the retrieval-accuracy collapse threshold-like or gradual, and does the AHN recurrent path change where/how much retrieval survives near the window? |
| 2 | **Exact hypothesis** | (shape) degradation is concentrated in a narrow transition region rather than distributed across pressure; (architecture) AHN recurrent memory shifts the transition and/or preserves more near-window accuracy than a no-recurrent-memory baseline. |
| 3 | **Primary endpoint(s)** | **(shape)** per-architecture isotonic 90→10 strict-accuracy transition **width** in model tokens, hierarchical-bootstrap CI, verdict {concentrated if CI-hi < 128; gradual if CI-lo > 256; else intermediate} — [FROZEN PRIMARY], `h2_threshold.transition_summary` `width`. **⚠ THIS ENDPOINT RETURNED UNDEFINED — see `protocol/amendment_h2_transition_width.md`.** **(architecture)** `A_transition(AHN pooled) − A_transition(transformer)` over `[200, 270]`, hierarchical-bootstrap CI — [FROZEN SECONDARY], `transition_summary` `a_transition_gap`. |
| 4 | **Unit of analysis** | item cluster → seed, `stats.hierarchical_bootstrap` (same as H1). Width/K statistics: isotonic fit over one balanced cell per intended target (`schema.pressure_group_key`), x = realised model-tat mean. |
| 5 | **Pressure region** | shape/K: full 12-level grid 150–760. gap: intended targets whose value ∈ [200, 270] = {205, 220, 235, 250, 265}. A_recurrent: intended ≥ 315. |
| 6 | **Statistical test** | width & K: isotonic (PAVA) strict-accuracy fit, 0.9/0.5/0.1 crossings, hierarchical-bootstrap 95 % CI. shape: smooth log-linear vs break-allowed fit with **break fixed at W = 256**, compared by AIC (`h2_threshold.shape_test`) — [FROZEN SECONDARY confirmatory]. gap & A_recurrent: hierarchical-bootstrap 95 % CI. |
| 7 | **Multiplicity** | none within H2 (each quantity reported with its own CI; no family test). |
| 8 | **Uncertainty interval** | percentile 95 % hierarchical-bootstrap CI, `random_state = 0`. |
| 9 | **Frozen headline results [A]** | **width: NaN / NaN / NaN for all four arms; verdict "intermediate" is a code fall-through, NOT a finding** (`final_h2_h2_width.csv`; `h2_threshold.transition_summary` L33–37; audit Phase 7). **K_strict** (0.5 crossing): transformer **208.3 [207.1, 209.5]**, deltanet 218.4 [215.9, 236.9], mamba2 219.6 [217.2, 237.5], gated_deltanet 240.0 [220.4, 243.9] (`final_h2_h2_k_strict.csv`). **K_abstention**: transformer **421.7**, AHN 247–251 (`final_audit/AUDIT_OUTPUTS/repro_h2_knees_by_arm.csv`). **shape test**: all four "threshold-like" (piecewise AIC < smooth); transformer margin thin (ΔAIC 0.68) (`final_h2_h2_shape_break_at_W.csv`). **A_transition gap (AHN − transformer, [200,270])**: **+0.2494 [0.2331, 0.2660]** (`final_summary.json` `h2_a_transition_gap`). **A_recurrent (≥ 315)**: deltanet 0.0001, gated_deltanet 0.0007, mamba2 0.0007, transformer 0.0047 — all ≈ 0 (`final_h2_h2_a_recurrent.csv`). |
| 10 | **Approved interpretation** | "AHN recurrent memory shifts the strict-accuracy collapse **≈ 10–35 model tokens later** than a no-recurrent-memory baseline (K 218–240 vs 208.3 [207.1, 209.5]) and preserves **≈ 0.25 more accuracy** in the near-window band [200, 270] (gap +0.249 [0.233, 0.266]). Past ≈ W all four architectures collapse to ≈ 0 retrieval (A_recurrent ≈ 0). Every architecture's collapse is threshold-like rather than gradual on all computable views (shape test 'threshold-like' for all four; per-closed-set-type 90→10 widths 33–69 tokens ≪ 0.5 W)." [C] |
| 11 | **Prohibited overinterpretation** | ✗ **"the transition is intermediate"** — the frozen width metric is undefined; the label is a bug (see amendment). ✗ any specific transition-width number as a frozen result. ✗ **"compression begins at K"** / "the memory threshold occurs at K" / "collapse occurs at W" — every K (208–240) is **below** W (256); K ≠ W. ✗ "AHN retains information past the window" — it does not (A_recurrent ≈ 0). ✗ attributing the near-window degradation **solely** to the exact→compressed transition (see VAL-4). ✗ "GatedDeltaNet has the latest knee" as a firm point estimate — its K is seed-bimodal (219–249). |
| 12 | **Required sensitivity analyses** | (a) **transition-width reporting amendment** — [POST-FREEZE REPORTING AMENDMENT], decision doc `protocol/amendment_h2_transition_width.md`, **team approval required before any width number is reported**. (b) **per-fact-type K & width** — [POST-FREEZE SENSITIVITY], `final_audit/AUDIT_OUTPUTS/auditorC_h2_per_facttype_transition_width.csv`: closed-set-type 90→10 widths transformer 33, AHN 62–69 tokens; K_strict transformer 207–220, AHN 216–254. (c) **seed robustness of K** — [POST-FREEZE SENSITIVITY], `phase13_k_by_seed.csv`: transformer K spread **1.9** tokens; AHN K spread **21–29** tokens (report AHN K as an interval, not a point). (d) **A_transition gap per AHN arm** (not just pooled) — [POST-FREEZE SENSITIVITY], recommended in the exhibit plan. |
| 13 | **Required limitation / disclosure** | [LIMITATION] **The frozen primary shape endpoint (transition width) returned an undefined value** because the pooled 5-type strict-accuracy curve peaks at ≈ 0.88 (temporal 38 % + multi-hop 11.5 % in-window abstention) and never reaches the 0.9 reference; the frozen code silently labelled this "intermediate". The scientifically defensible shape classification is **UNDETERMINED pending the amendment**; every computable alternative points to *concentrated / threshold-like*. [LIMITATION] **W ≠ K** — the empirical knee (208–240) sits below the architectural window (256); the paper describes the collapse as occurring *around / just below the window*, never *at a compression threshold T* (`config.compression_threshold(strict=True)` still raises by design). [LIMITATION] **VAL-4**: ≈ 32 % of trials in which the target span is arithmetically inside W through generation still fail (`phase8`), so near-window degradation is not attributable *solely* to the exact→compressed transition. |
| 14 | **Supporting exhibits** | Figure F2 (per-architecture strict-accuracy curves vs realised model-tat, W and per-arm K marked, abstention overlaid); Table T3 (K_strict, K_abstention, shape-test AIC, A_recurrent, A_transition gap — all per arm with CIs); appendix Figure A-H2 (per-fact-type curves); appendix Table A-H2 (per-seed K). |

**Independently valid H2 quantities preserved without amendment [A]:**
`A_transition(AHN pooled) − transformer` = +0.2494 **[0.2331, 0.2660]** ·
`K_strict` per arm (with CIs) · `K_abstention` per arm · `shape_test` AIC/RSS
(all "threshold-like") · `A_recurrent` per arm ≈ 0 · per-type K
(`repro_h2_knees_by_facttype.csv`) · seed robustness of all of the above.

> **H2 WIDTH AMENDMENT STATUS (2026-09-09):** the Option-A amendment in §12(a) / the
> decision doc is **APPROVED and IMPLEMENTED** (commit `626521a`;
> `protocol/amendment_h2_transition_width.md` §13). The frozen pooled width
> (`final_h2_h2_width.csv`) stays undefined and untouched. Reported instead:
> per-eligible-fact-type isotonic 90→10 width (eligible = contradictory,
> entity-attribute, numerical), per-arm **median** 32.4 [30.5, 36.8] (transformer)
> / 61.8–73.8 (AHN) model tokens, all ≪ 0.5 W. H2 shape status →
> **SUPPORTED — concentrated** (frozen shape test + amended widths agree). See
> `outputs/final_v1_1_reporting_amendment/h2_amend__*` and claims register H2-2 / H2-3.
> No previously approved claim is weakened.

---

# H3 — Does behavioural uncertainty signalling track retrieval failure?

Four strictly separated quantities (frozen design §8; `h3_calibration`):
**(1) behavioural uncertainty signalling** · **(2) factual calibration among
answered-valid responses** · **(3) confidence of abstention responses** ·
**(4) malformed output**. Sequence confidence on an abstention is confidence in
producing "I don't know" — **not** factual confidence in a wrong answer — and is
never pooled with (2).

| # | field | specification |
|---|---|---|
| 1 | **Scientific question** | As memory degrades, does the model's *behaviour* increasingly signal that its memory is unreliable? Does its *factual confidence* (when it does answer) stay calibrated? |
| 2 | **Exact hypothesis** | Behavioural signalling: past the window, appropriate abstention rises and unsignalled failure falls, more so for AHN than for a no-recurrent-memory baseline. Calibration: the confidence−accuracy gap on answered-valid trials widens from control to the transition region. |
| 3 | **Primary endpoint** | **Behavioural [FROZEN PRIMARY]**, region `model_tokens_after_target ≥ W + 16 = 272`: `appropriate_abstention_rate` = P(abstained); `unsignalled_failure_rate` = P(wrong-valid OR malformed), wrong-valid = answered ∧ ¬malformed ∧ correct = 0. Per arm + each AHN arm vs transformer. `h3_calibration.behavioral_signaling`. **Secondary calibration [FROZEN SECONDARY]**: `gap_change` = Δ(confidence − accuracy) on **answered-valid only**, from pooled control anchors {150, 180} to interval [200, 270], per arm. `h3_calibration.gap_change`. |
| 4 | **Unit of analysis** | item cluster → seed, `stats.hierarchical_bootstrap`. |
| 5 | **Pressure region** | behavioural: realised model-tat ≥ 272 (n = 10,091 per arm; 40,364 total — `final_h3_h3_behavioral_per_arm.csv`, `final_summary.json`). calibration: control anchors {150, 180} vs interval [200, 270]. descriptive ECE/Brier/CWR: all 12 levels (`final_h3_h3_by_pressure_answered_valid.csv`). |
| 6 | **Statistical test** | behavioural: hierarchical-bootstrap 95 % CI per rate; AHN-vs-transformer contrasts with two-sided bootstrap p, Holm within the 6-contrast family. calibration: hierarchical-bootstrap 95 % CI on `gap_change`. ECE (10 equal-width bins, Guo et al. 2017), Brier, CWR (threshold 0.5, PROVISIONAL) — descriptive, `config/experiment.yaml calibration`. |
| 7 | **Multiplicity** | Holm within the 6 behavioural AHN-vs-transformer contrasts. None on the descriptive calibration table. |
| 8 | **Uncertainty interval** | percentile 95 % hierarchical-bootstrap CI, `random_state = 0`. |
| 9 | **Frozen headline results [A]** | **Behavioural, past W+16** (`final_h3_h3_behavioral_per_arm.csv`): appropriate abstention — deltanet **0.946**, mamba2 **0.945**, gated_deltanet **0.929**, transformer **0.516**; unsignalled failure — deltanet **0.054**, mamba2 **0.052**, gated_deltanet **0.071**, transformer **0.480**. All 6 AHN-vs-transformer contrasts p_holm = 0, \|diff\| 0.41–0.43 (`final_h3_h3_behavioral_contrasts.csv`). **Calibration `gap_change`** (`final_h3_h3_gap_change.csv`): transformer −0.018 **[−0.051, 0.013]** (CI contains 0 — no shift); gated_deltanet −0.063 [−0.086, −0.038]; mamba2 −0.108 [−0.128, −0.088]; deltanet −0.115 [−0.136, −0.094] — AHN arms become **more under-confident (more cautious)** in the transition. **Answered-valid deep past W** (`final_h3_h3_by_pressure_answered_valid.csv`, pooled): at pressure_group 265 accuracy 0.069, confidence 0.596, gap **+0.527**, ECE 0.527, CWR 0.923 — **but n_population = 853 pooled** (transformer alone n = 1). |
| 10 | **Approved primary interpretation** | "As memory degrades past the sliding-window boundary, **AHN behaviour increasingly signals memory unreliability through abstention**: AHN arms abstain on 93–95 % of past-window trials and leave only 5–7 % of failures unsignalled, versus 52 % appropriate abstention and 48 % unsignalled failure for the no-recurrent-memory baseline (all contrasts p_holm = 0, effect ≈ 0.42, identical across all 8 seeds). On the trials where AHN arms *do* answer in the transition, they become **more conservative** (confidence − accuracy shifts −0.06 to −0.12), whereas the baseline does not shift." [C] |
| 11 | **Prohibited overinterpretation** | ✗ **"the recurrent state knows / is aware that it has forgotten"** — no mechanistic claim (frozen design §8). ✗ "AHN is well-calibrated" as a blanket statement — on the small answered-valid-past-W subpopulation all arms are badly overconfident (CWR 0.92–0.98). ✗ "the model is overconfident when wrong" without the scope qualifier — it applies to **< 5 %** of past-window trials (n ≈ 850 pooled of ≈ 40k); the dominant past-window behaviour is abstention. ✗ treating `mean_confidence_on_abstention` as factual confidence. ✗ citing ECE/CWR at deep pressure as a headline (tiny, selected n). |
| 12 | **Required sensitivity analyses** | (a) **per-seed behavioural rates** — [POST-FREEZE SENSITIVITY], `phase13_h3_abst_by_seed.csv`: AHN 0.92–0.95, transformer 0.49–0.53 every seed. (b) **length-normalised confidence** ECE sensitivity — [POST-FREEZE SENSITIVITY], only if computable from stored per-token data without a GPU rerun; `config.calibration.confidence = sequence_probability` is PROVISIONAL (`open_decisions.md` #6). Sequence-probability confidences span 6.4×10⁻⁹–1.0 (audit Phase 1). (c) **abstention-confidence table** — [FROZEN SECONDARY], `final_h3_h3_abstention_confidence.csv`, reported separately, never merged with (2). |
| 13 | **Required limitation / disclosure** | [LIMITATION] **Mechanism is unresolved [D]:** the transformer has *no* recurrent memory, so "AHN signals uncertainty better" cannot be separated here between (i) the recurrent state carrying a usable uncertainty signal and (ii) the AHN checkpoints having been distilled to abstain. State both. [LIMITATION] The "overconfident when wrong" observation is confined to the small answered-valid failure population past the window. [LIMITATION] Confidence = sequence probability (PROVISIONAL); ECE magnitudes reflect tokenisation as well as calibration. |
| 14 | **Supporting exhibits** | Table T4 (behavioural per-arm rates + 6 contrasts, Holm); Figure F3 (appropriate-abstention and unsignalled-failure vs realised model-tat, per arm); appendix Table A-H3 (gap_change, ECE/Brier/CWR by pressure, abstention-confidence, per-seed). |

---

# Cross-cutting: FROZEN vs POST-FREEZE ledger

| analysis | status | file |
|---|---|---|
| H1 A_transition (raw strict, AHN pooled) + 10 contrasts + Holm | [FROZEN PRIMARY] | `final_h1_h1_a_transition.csv`, `final_h1_h1_contrasts.csv` |
| H1 omnibus permutation | [FROZEN SECONDARY companion] | `final_summary.json` `extras.h1_omnibus` |
| H1 exclude-temporal | [FROZEN SECONDARY] | `final_h1_h1_sensitivity_excl_temporal.csv` |
| H1 answered-valid (all types; filename says "temporal") | [FROZEN SECONDARY] | `final_h1_h1_sensitivity_temporal_answered_valid.csv` |
| H1 exclude-compound-relational | [POST-FREEZE SENSITIVITY] — **implemented** `626521a` | `outputs/final_v1_1_reporting_amendment/h1_sensitivity__exclude_compound_relational__*` |
| H1 per-seed A_transition | [POST-FREEZE SENSITIVITY] | `AUDIT_OUTPUTS/phase13_a_transition_by_seed.csv`, `v1_1/robustness__per_seed_headline__*` |
| H1 temporal-only answered-valid (others stay raw strict, literal §6-B) | [POST-FREEZE SENSITIVITY] — not yet computed | team decision (optional) |
| H2 transition width + verdict (pooled) | [FROZEN PRIMARY] — **UNDEFINED (NaN); "intermediate" is a code fall-through; preserved untouched** | `final_h2_h2_width.csv` |
| H2 transition-width metric replacement (Option A) | [POST-FREEZE REPORTING AMENDMENT] — **approved + implemented** `626521a` | `protocol/amendment_h2_transition_width.md` §13; `v1_1/h2_amend__*` |
| H2 per-eligible-fact-type 90→10 width + per-arm median + CI + seed sensitivity | [POST-FREEZE REPORTING AMENDMENT] | `v1_1/h2_amend__{eligibility,width_by_facttype,width_summary_median,width_seed_sensitivity}.csv` |
| H2 K_strict / K_abstention / shape-test / A_recurrent / A_transition gap | [FROZEN SECONDARY], all valid | `final_h2_h2_*.csv`, `final_summary.json` |
| H2 per-seed K | [POST-FREEZE SENSITIVITY] | `AUDIT_OUTPUTS/phase13_k_by_seed.csv`, `v1_1/robustness__per_seed_headline__k_strict_by_seed.csv` |
| H3 behavioural per-arm + contrasts | [FROZEN PRIMARY] | `final_h3_h3_behavioral_*.csv` |
| H3 gap_change | [FROZEN SECONDARY] | `final_h3_h3_gap_change.csv` |
| H3 ECE/Brier/CWR by pressure, abstention-confidence | [FROZEN SECONDARY] | `final_h3_h3_by_pressure_answered_valid.csv`, `final_h3_h3_abstention_confidence.csv` |
| H3 per-seed behavioural rates | [POST-FREEZE SENSITIVITY] | `AUDIT_OUTPUTS/phase13_h3_abst_by_seed.csv` |
| Residual fully-exact failure table | [POST-FREEZE SENSITIVITY / LIMITATION] | `AUDIT_OUTPUTS/phase8_residual_exact_failures.csv` |
| Deep-recurrent (≥ 2W) negative-retention | [POST-FREEZE SENSITIVITY / NEGATIVE RESULT] | `AUDIT_OUTPUTS/phase9_deep_recurrent.csv` |
| Transformer malformed disclosure | [LIMITATION] | `AUDIT_OUTPUTS/phase4_*` |
| Temporal response-bias / counterbalancing | [LIMITATION] | `AUDIT_OUTPUTS/phase10_temporal_subgroups.csv` |
| Multi-hop / compound-relational control WARNING | [LIMITATION] | `final_control_validity_control_validity.csv`, `AUDIT_OUTPUTS/phase11_*` |
| Plumbing gates (0 blocking) | [FROZEN SECONDARY, not persisted in lock] | `AUDIT_OUTPUTS/repro_plumbing_gates.csv` |

**No frozen primary endpoint is replaced.** The only frozen primary that changes
status is the H2 transition-width verdict, which is being **corrected from an
undefined/misleading label**, not swapped for a more favourable metric — see the
amendment document.
