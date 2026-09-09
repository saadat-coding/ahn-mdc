# Final Claims Register

Every claim the manuscript may make about the locked 92,160-trial experiment, with
its exact evidence, uncertainty, required caveat, and the boundary between allowed
and prohibited wording. Fields = the requested columns (ID · Hypothesis · Claim ·
Status · Evidence · Statistic · Uncertainty · Sensitivity · Required caveat ·
Allowed wording · Prohibited wording).

**Status vocabulary:** SUPPORTED · PARTIALLY SUPPORTED · NEGATIVE RESULT ·
UNDETERMINED · LIMITATION · PROHIBITED CLAIM.
**Evidence labels:** [A] locked artifact · [B] frozen code/config · [C] interpretation · [D] team decision.
All statistics reproduce from the locked parquet to \|Δ\| ≤ 1e-14 (`final_audit/AUDIT_OUTPUTS/phase14_frozen_vs_repro_diffs.csv`).

---

### H1-1 — Non-uniform degradation

- **Hypothesis:** H1
- **Claim:** Fact types degrade non-uniformly in end-to-end task accuracy across the transition region.
- **Status:** **SUPPORTED**
- **Evidence [A]:** `final_summary.json` (`h1_omnibus_p`, `extras.h1_omnibus`); `final_h1_h1_contrasts.csv`.
- **Statistic:** label-permutation on the SD of the five A_transition means — SD = 0.1273, **p = 0.0005** (0/2000); **all 10** pairwise Holm-adjusted 95 % CIs exclude 0.
- **Uncertainty:** 2000-permutation p; percentile 95 % hierarchical-bootstrap CIs on each contrast; `random_state = 0`.
- **Sensitivity:** exclude-temporal 6/6 sig (`final_h1_h1_sensitivity_excl_temporal.csv`); exclude-multi-hop 6/6 sig (`repro_h1_excl_multihop.csv`); answered-valid all-types 8/10 sig (`final_h1_h1_sensitivity_temporal_answered_valid.csv`); ordering stable in 7/8 seeds (`phase13_a_transition_by_seed.csv`).
- **Required caveat:** the endpoint is raw strict accuracy, which blends retrieval failure with abstention propensity; report the answered-valid sensitivity beside it.
- **Allowed wording:** "fact types degrade non-uniformly in task accuracy"; "the five-way spread far exceeds label-permutation chance (p = 5×10⁻⁴)".
- **Prohibited wording:** "fact types are forgotten at different rates"; "differential representational information loss"; any claim without the answered-valid sensitivity.

### H1-2 — Fact-type ordering

- **Hypothesis:** H1
- **Claim:** Ordering from fastest- to slowest-degrading is compound-relational < temporal < numerical < contradictory < entity-attribute.
- **Status:** **PARTIALLY SUPPORTED** (robust under raw strict; compresses under answered-valid)
- **Evidence [A]:** `final_h1_h1_a_transition.csv` — A_transition 0.255 / 0.307 / 0.389 / 0.520 / 0.594.
- **Statistic:** raw-strict A_transition per type (n = 5760, 48 items each); pairwise contrasts all Holm-sig, weakest multi-hop vs temporal p_holm 0.037.
- **Uncertainty:** contrast CIs in `final_h1_h1_contrasts.csv`; per-seed range ± 0.03–0.05.
- **Sensitivity:** under **answered-valid**, contradictory ≈ numerical and entity-attribute ≈ temporal (p_holm = 1.0); compound-relational stays lowest; entity-attribute stays highest.
- **Required caveat:** the multi-hop↔temporal adjacency is the only seed-unstable pair (swaps in seed 3); temporal's position is abstention-influenced; compound-relational's position is partly a ceiling effect (VAL-2).
- **Allowed wording:** "compound-relational targets degrade fastest and entity-attribute targets are most robust; the middle ranks (temporal, numerical, contradictory) are closer together and partly metric-dependent".
- **Prohibited wording:** a rigid five-way ranking stated without the answered-valid caveat; "temporal is more fragile than numerical" as a memory claim (it is an abstention effect).

### H2-1 — AHN near-window advantage

- **Hypothesis:** H2
- **Claim:** AHN recurrent memory preserves substantially more retrieval accuracy than a no-recurrent-memory baseline in the near-window band [200, 270].
- **Status:** **SUPPORTED**
- **Evidence [A]:** `final_summary.json` `h2_a_transition_gap`; `final_h2_h2_curves.csv`.
- **Statistic:** A_transition(AHN pooled) − A_transition(transformer) over intended [205–265] = **+0.2494**.
- **Uncertainty:** hierarchical-bootstrap 95 % CI **[0.2331, 0.2660]**; positive in every seed.
- **Sensitivity:** per-arm gap (recommended, exhibit plan); per-fact-type curves (`repro_h2_knees_by_facttype.csv`).
- **Required caveat:** "baseline" = the same Qwen2.5-3B with W forced to 256 and no AHN module (pure truncation past W); part of the gap is the transformer degenerating (39.6 % malformed) rather than abstaining (VAL-3).
- **Allowed wording:** "AHN recurrent memory preserves ≈ 0.25 more near-window retrieval accuracy than a no-recurrent-memory baseline (95 % CI [0.23, 0.27])".
- **Prohibited wording:** "AHN solves long-context retrieval"; any framing that ignores that both collapse past W (H2-5).

### H2-2 — Threshold-like shape

- **Hypothesis:** H2
- **Claim:** The retrieval-accuracy collapse is threshold-like (concentrated), not gradual, for every architecture.
- **Status:** **PARTIALLY SUPPORTED** (confirmatory shape test yes; frozen width metric undefined)
- **Evidence [A]:** `final_h2_h2_shape_break_at_W.csv` (all four "threshold-like", piecewise AIC < smooth); `auditorC_h2_per_facttype_transition_width.csv` (closed-set 90→10 widths 33–69 tokens); `final_h2_h2_curves.csv`.
- **Statistic:** smooth vs break-at-W fit, ΔAIC favours piecewise for all four (transformer margin thin, ΔAIC 0.68); closed-set per-type widths ≪ 0.5 W.
- **Uncertainty:** shape test is a point AIC comparison (no CI); per-type widths need a fresh bootstrap CI (post-freeze).
- **Sensitivity:** covered by `protocol/amendment_h2_transition_width.md` (Options A–D).
- **Required caveat:** the pre-registered pooled transition-width statistic returned **undefined** (see H2-3); "threshold-like" rests on the shape test + per-type widths + raw curves, not on the frozen width.
- **Allowed wording:** "on every computable view the collapse is concentrated (closed-set per-type 90→10 widths 33–69 model tokens) and threshold-like (shape test), not gradual".
- **Prohibited wording:** "the transition width is X tokens" as a frozen result; "intermediate".

### H2-3 — Transition width

- **Hypothesis:** H2
- **Claim:** (frozen) per-architecture isotonic 90→10 transition width and its {concentrated/gradual/intermediate} verdict.
- **Status:** **UNDETERMINED** (frozen metric is undefined for this dataset)
- **Evidence [A]:** `final_h2_h2_width.csv` — `width_tokens` / `ci_low` / `ci_high` all NaN; verdict "intermediate" is a `np.isfinite` fall-through (`h2_threshold.transition_summary`; audit Phase 7).
- **Statistic:** none valid — the pooled 5-type strict-accuracy curve peaks at ≈ 0.88 and never reaches the 0.9 anchor.
- **Uncertainty:** N/A (non-finite).
- **Sensitivity:** `protocol/amendment_h2_transition_width.md` — recommended replacement = per-closed-set-type 90→10 width; **needs team sign-off**.
- **Required caveat:** disclose as a metric-definition artefact, not a data property.
- **Allowed wording:** "the pre-registered pooled transition-width statistic is undefined for this dataset because one fact type abstention-saturates below the 0.9 reference; we report per-type widths and the shape test instead (post-freeze reporting amendment [cite])".
- **Prohibited wording:** "the transition is intermediate"; "intermediate width"; any use of the frozen `verdict` column.

### H2-4 — W vs K

- **Hypothesis:** H2
- **Claim:** The empirical performance knee K sits **below** the architectural sliding-window boundary W.
- **Status:** **SUPPORTED**
- **Evidence [A]:** `final_h2_h2_k_strict.csv` — transformer K 208.3, deltanet 218.4, mamba2 219.6, gated_deltanet 240.0; W = 256 (design-fixed, `config/experiment.yaml`, `config.compression_threshold(strict=True)` raises by design [B]).
- **Statistic:** isotonic 0.5-crossing of pooled strict accuracy vs realised model-tat, per arm.
- **Uncertainty:** hierarchical CI — transformer **[207.1, 209.5]** (tight); AHN wide/asymmetric (e.g. gated_deltanet [220.4, 243.9]); AHN K spread across seeds 21–29 tokens (`phase13_k_by_seed.csv`).
- **Sensitivity:** per-fact-type K 193–254 (`repro_h2_knees_by_facttype.csv`); per-seed K.
- **Required caveat:** K is a descriptive per-run quantity, not an architectural constant; AHN K must be given as an interval.
- **Allowed wording:** "the collapse occurs around and slightly before the sliding-window boundary (K 208–240 vs W = 256)"; "W is the architectural window; K is the observed knee — they are distinct".
- **Prohibited wording:** "compression begins at K"; "the memory threshold occurs at K"; "collapse occurs at W"; "K = W"; equating either with a published threshold T.

### H2-5 — Deep recurrent retention

- **Hypothesis:** H2
- **Claim:** No architecture retains measurable target-specific factual information past ≈ W (and none at ≥ 2W).
- **Status:** **NEGATIVE RESULT** (clean)
- **Evidence [A]:** `final_h2_h2_a_recurrent.csv` (A_recurrent, intended ≥ 315, all arms ≈ 0); `phase9_deep_recurrent.csv` (≥ 2W: 0/3542 deltanet & gated_deltanet, 1/3542 mamba2, 3/3542 transformer).
- **Statistic:** A_recurrent ≈ 0.0001–0.005; deep-regime binomial 0–3 correct out of 3,542.
- **Uncertainty:** hierarchical CI on A_recurrent includes 0; Wilson-95 upper at ≥ 2W ≤ 0.21 %.
- **Sensitivity:** by fact type (`phase9_deep_recurrent.csv`) — no type shows retention; the one mamba2 hit is a temporal 2AFC.
- **Required caveat:** the ≈ 2 % of deep trials that produce an answer are almost all wrong; abstention ≈ 98 %.
- **Allowed wording:** "past the sliding-window boundary, retrieval accuracy is indistinguishable from zero for all four architectures (A_recurrent ≈ 0; ≥ 2W upper 95 % bound ≤ 0.2 %)".
- **Prohibited wording:** "AHN retains partial / degraded information at depth"; inferring retention from the isolated mamba2 hit.

### H3-1 — Appropriate abstention

- **Hypothesis:** H3
- **Claim:** As memory degrades past the window, AHN behaviour increasingly signals memory unreliability through abstention, far more than a no-recurrent-memory baseline.
- **Status:** **SUPPORTED**
- **Evidence [A]:** `final_h3_h3_behavioral_per_arm.csv`, `final_h3_h3_behavioral_contrasts.csv`.
- **Statistic:** past model-tat ≥ 272 — appropriate_abstention_rate deltanet 0.946, mamba2 0.945, gated_deltanet 0.929, **transformer 0.516**; AHN-vs-transformer diff +0.41 to +0.43.
- **Uncertainty:** hierarchical CIs (e.g. deltanet–transformer +0.430 [0.413, 0.446]); all 6 contrasts p_holm = 0; identical across all 8 seeds (`phase13_h3_abst_by_seed.csv`).
- **Sensitivity:** per-seed (stable); per-pressure-level abstention curve (`final_h3_h3_abstention_confidence.csv`).
- **Required caveat:** mechanism unresolved (H3-4).
- **Allowed wording:** "AHN arms abstain on 93–95 % of past-window trials vs 52 % for the no-recurrent-memory baseline (effect ≈ 0.42, p_holm = 0, stable across 8 seeds)".
- **Prohibited wording:** "AHN knows it has forgotten"; "the recurrent state detects memory loss".

### H3-2 — Unsignalled failure

- **Hypothesis:** H3
- **Claim:** AHN arms leave only 5–7 % of past-window failures unsignalled (wrong-valid or malformed); the baseline leaves 48 %.
- **Status:** **SUPPORTED**
- **Evidence [A]:** `final_h3_h3_behavioral_per_arm.csv` — unsignalled_failure_rate deltanet 0.054, mamba2 0.052, gated_deltanet 0.071, transformer 0.480.
- **Statistic:** P(wrong-valid ∨ malformed) past model-tat ≥ 272; contrasts −0.41 to −0.43.
- **Uncertainty:** hierarchical CIs (e.g. deltanet–transformer −0.427 [−0.443, −0.409]); p_holm = 0 for all 6.
- **Sensitivity:** the transformer's 0.48 is substantially malformed output (VAL-3), which is the intended definition.
- **Required caveat:** "unsignalled failure" bundles confidently-wrong answers and malformed output by design; state the composition.
- **Allowed wording:** "the no-recurrent-memory baseline fails without signalling on ≈ 48 % of past-window trials (mostly degenerate output), vs 5–7 % for AHN".
- **Prohibited wording:** presenting the transformer's rate as purely "confidently wrong answers".

### H3-3 — Factual calibration

- **Hypothesis:** H3
- **Claim:** On trials where a model does give a factual answer, calibration behaviour differs by architecture and pressure.
- **Status:** **PARTIALLY SUPPORTED**
- **Evidence [A]:** `final_h3_h3_gap_change.csv`; `final_h3_h3_by_pressure_answered_valid.csv`.
- **Statistic:** Δ(confidence − accuracy) control → [200,270], answered-valid — transformer −0.018, gated_deltanet −0.063, mamba2 −0.108, deltanet −0.115. Deep past W (pooled, tiny n): gap +0.53, CWR 0.92–0.98.
- **Uncertainty:** transformer gap_change CI **[−0.051, 0.013] contains 0**; AHN CIs exclude 0 (negative). Deep-pressure n_population 853 (pooled) / 1 (transformer alone) at intended 265.
- **Sensitivity:** length-normalised confidence (post-freeze, if computable, `open_decisions.md` #6); confidence is `sequence_probability` = PROVISIONAL.
- **Required caveat:** "overconfident when wrong" applies to **< 5 %** of past-window trials (the answered-valid failures), not to degraded trials in general; ECE magnitudes reflect tokenisation.
- **Allowed wording:** "in the transition region AHN arms become more conservative on answered-valid trials (gap shifts −0.06 to −0.12) while the baseline does not shift"; "on the small subset of past-window trials where a model still answers, all architectures are badly miscalibrated (CWR 0.9+)".
- **Prohibited wording:** "AHN is well-calibrated"; "the model is overconfident when wrong" without the < 5 % scope qualifier; headlining deep-pressure ECE/CWR.

### H3-4 — Mechanism of uncertainty signalling

- **Hypothesis:** H3
- **Claim:** The recurrent state mechanistically represents that information has been lost.
- **Status:** **PROHIBITED CLAIM** (unresolved; [D])
- **Evidence:** none — the experiment cannot separate "recurrent state carries a usable uncertainty signal" from "the AHN checkpoints were distilled to abstain when context is thin". The transformer has no recurrent memory, so the contrast confounds architecture with training recipe.
- **Statistic:** N/A.
- **Uncertainty:** N/A.
- **Sensitivity:** would require a different design (recurrent-state probing, or an abstention-matched ablation) — **not to be run**.
- **Required caveat:** state both alternatives explicitly as a limitation.
- **Allowed wording:** "AHN behaviour increasingly signals memory unreliability through abstention; whether this reflects a signal in the recurrent state or a learned abstention policy from distillation cannot be determined from this experiment".
- **Prohibited wording:** "the recurrent state knows/detects/is aware"; "the model recognises its own forgetting"; any mentalistic or mechanistic framing.

### VAL-1 — Temporal construct

- **Hypothesis:** validation
- **Claim:** The repaired temporal benchmark measures order retrieval without a dataset shortcut.
- **Status:** **SUPPORTED** (with disclosure) / **LIMITATION** on raw strict
- **Evidence [A]:** `phase10_temporal_subgroups.csv` — 2×2×2 nuisance grid exactly balanced (6/cell); `protocol/temporal_repair_validation.md` (target-removed ≈ chance).
- **Statistic:** pooled control answered-valid accuracy 0.922; directional bias 0.85 vs 0.99 (gold higher), 0.87 vs 1.00 (gold first-listed), counterbalanced.
- **Uncertainty:** subgroup n = 1,536 per cell at control.
- **Sensitivity:** H1 exclude-temporal and answered-valid sensitivities.
- **Required caveat:** temporal raw strict is abstention-dominated (38 % in-window, 66 % overall); its H1 rank must be read with the answered-valid sensitivity.
- **Allowed wording:** "the temporal benchmark is a balanced two-alternative order task; the model has a documented directional response bias that is counterbalanced against the gold and nets to chance".
- **Prohibited wording:** "the temporal benchmark is invalid" (it is not); "the model exploits a positional shortcut" (counterbalanced).

### VAL-2 — Compound-relational construct

- **Hypothesis:** validation
- **Claim:** The `multi-hop` fact type tests retrieval of a compound-relational target, not multi-hop reasoning across separated facts.
- **Status:** **LIMITATION** (construct scope) + control **WARNING**
- **Evidence [A/B]:** `config/facts.yaml` `multi-hop.caveat`; `final_control_validity_control_validity.csv` (strict 0.842, abstention 0.115 → WARNING); `phase11_multihop_control_by_item.csv`.
- **Statistic:** in-window ceiling 0.842 (answered-valid 0.951); WARNING drivers: strict < 0.85 AND abstention > 0.10; FAIL threshold (0.70) not reached → retained in H1.
- **Uncertainty:** by seed 0.77–0.94 (7/8 show the WARNING); by item only 2/48 below 0.5.
- **Sensitivity:** H1 exclude-multi-hop (6/6 sig, `repro_h1_excl_multihop.csv`).
- **Required caveat:** the target is one co-located two-clause sentence; the ≈ 84 % ceiling is task difficulty.
- **Allowed wording:** "compound-relational targets ('A manages B. B works for C.') require resolving both clauses of a single sentence; even in-window the model reaches only ≈ 84 % (mostly via abstention), a task-difficulty ceiling we disclose".
- **Prohibited wording:** "multi-hop reasoning"; "retrieval across multiple facts"; "chained inference"; presenting compound-relational's fastest-degrading rank as pure memory decay.

### VAL-3 — Transformer control behaviour

- **Hypothesis:** validation
- **Claim:** The transformer control's high malformed rate past its window is expected no-recurrent-memory degeneration, not pipeline corruption.
- **Status:** **LIMITATION / DISCLOSURE** (behaviour is real and correctly handled)
- **Evidence [A]:** `phase4_transformer_malformed_by_pressure.csv` (0 % at anchors → 59–79 % in transition → 3–10 % deepest); `repro_plumbing_gates.csv` (`malformed_control:transformer` = CONTROL_BEHAVIOR, non-blocking); Phase 2 re-score exact.
- **Statistic:** overall 39.6 % (per arm); pooled across arms 12.6 %; AHN arms 1.4–4.8 % on identical prompts.
- **Uncertainty:** spread evenly across all 240 items and 8 seeds.
- **Sensitivity:** subtype taxonomy (too_long / unrecognised / empty / negation).
- **Required caveat:** never cite the 12.6 % pooled figure alone; always split by arm.
- **Allowed wording:** "the no-recurrent-memory control produces degenerate output rather than abstaining once the target is compressed away (39.6 % malformed, 0 % in-window); the frozen gate classifies this as expected control behaviour".
- **Prohibited wording:** "12.6 % of trials were malformed" without the per-arm split; "a parsing/pipeline problem".

### VAL-4 — Residual exact-memory failures

- **Hypothesis:** validation
- **Claim:** Near-window degradation is not attributable solely to the exact→compressed memory transition.
- **Status:** **LIMITATION** (unresolved empirical phenomenon)
- **Evidence [A]:** `phase8_residual_exact_failures.csv` — 32.1 % of trials with `target_fully_exact_through_generation == True` still fail; excess concentrated at intended 205–250 (34–60 %).
- **Statistic:** 11,236 / 34,975; composition 46 % abstain / 38.5 % malformed / 15 % wrong-valid; by type temporal 51.6 % → entity-attribute 11.9 %.
- **Uncertainty:** seed-uniform (29.7–34.7 %).
- **Sensitivity:** stratified by type / arch / pressure / seed (all in the CSV).
- **Required caveat:** no mechanism claimed; carried forward from Pilot Pass 2.
- **Allowed wording:** "even at pressures where the target span is arithmetically within the lossless window, retrieval already fails on ≈ 32 % of trials (rising to ≈ 60 % at intended model-tat 220), predominantly by abstention or degenerate output; the pressure axis is therefore a proxy for compression pressure, not a clean exact/recurrent switch".
- **Prohibited wording:** "all near-window failures are caused by compression"; attributing the residual failures to a specific mechanism (attention dilution, instruction effect) without evidence.
