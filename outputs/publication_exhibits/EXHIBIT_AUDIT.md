# Exhibit Audit — hostile pass

Auditor: Claude (Sonnet 5) · 2026-09-09 · read-only over the locked evidence.
Programmatic traceability check: `scripts/audit_publication_exhibits.py` — **ALL CHECKS PASS**
(every plotted/tabulated headline number reproduces from the locked parquet
SHA-256 `a72fd43e…`, the frozen v1.0 `final_*` files, or the approved v1.1
`final_v1_1_reporting_amendment/` files; every generated-file hash matches
`EXHIBIT_MANIFEST.json`).

Per-exhibit verdict against the 10 checks
(1 trace-to-evidence · 2 matches claims register · 3 allowed terminology ·
4 no prohibited implication · 5 W vs K distinct · 6 abstention/error/malformed
separated · 7 CI/stat annotations correct · 8 H2 v1.1 amendment disclosed ·
9 not cherry-picked · 10 skeptical-reviewer misread risk).

| exhibit | verdict | notes |
|---|---|---|
| **figD_experimental_design** | **PASS** | (1) grid + realised medians reproduce from parquet. (5) W drawn as a dashed line labelled "architectural sliding-window boundary (not a threshold)"; no K on this figure. (10) low risk — the intended-vs-realised panel makes the calibration explicit. |
| **fig1_h1_nonuniform_degradation** | **WARN** (cosmetic) | (1)(2)(7) A_transition values == frozen `final_h1_h1_a_transition.csv`; curve points reproduce from the parquet; omnibus p = 5×10⁻⁴ == `final_summary.json`. (3) "compound-relational" in the legend; internal `multi-hop` preserved in `fig1_h1_curves.csv`. (4) y-axis is "strict production accuracy" not "information retained" — a caption sentence to that effect is REQUIRED (in the exhibit `notes`). (5) W dashed line, no K. (6) abstention is not on this figure (accuracy only) — the shared story is in Fig 2 / Fig 3. (9) all 5 fact types shown, none omitted. (10) the shaded "A_transition region" label is partly overprinted by curves — a manuscript-time layout tweak; not misleading. |
| **tbl1_h1_primary** | **PASS** | (1) raw-strict A_transition + control columns == frozen; `A_transition_answered_valid` is recomputed from the locked parquet with frozen `h1_degradation.a_transition(value='answered_valid')` and is internally consistent with the frozen answered-valid contrasts (Δ match to 1e-3). (2) H1-1 / H1-2. (4) footnotes state raw strict is the frozen primary (Policy A) and the answered-valid column is a FROZEN SECONDARY sensitivity, not a replacement. (9) all 5 rows. |
| **tbl2_h1_contrasts** | **PASS** | (1) byte-identical to `final_h1_h1_contrasts.csv`. (7) annotation states hierarchical item→seed bootstrap, 2000 resamples, Holm over 10; the borderline row (compound-relational vs temporal, p_holm 0.037) is disclosed, not hidden. (9) all 10 contrasts. |
| **fig2_h2_architecture_curves** | **WARN** (cosmetic) | (1) accuracy curves == `final_h2_h2_curves.csv`; abstention reproduces from the parquet; K == `final_h2_h2_k_strict.csv`; gap == `final_summary.json`. (5) **W and K are distinct**: W is a black dashed vertical line; K is a diamond marker per arm on a horizontal CI strip below the accuracy panel — programmatic check confirms every K point < W. (4) the frozen pooled transition-width / "intermediate" label is deliberately ABSENT; a note points to Table 3 + Appendix A-H2a. No implication of retention past W (bottom panel + "A_recurrent ≈ 0" in the title). (10) the K strip sits between the two panels and could be mistaken for a third axis — a manuscript-time tweak (move it into the accuracy panel or a clear inset); the science is right. |
| **tbl3_h2_summary** | **PASS** | (1) K_strict / shape / A_recurrent == frozen; K_abstention recomputed from the parquet with frozen `h2_threshold.knees`; gap == `final_summary.json`. (5) footnote: "K is a DESCRIPTIVE empirical knee … NOT a threshold; W = 256 is the architectural window. Every K < W." (8) footnote discloses the pooled-width statistic is UNDEFINED and points to the amendment; the frozen "intermediate" verdict column is NOT included. (4) no prohibited implication. |
| **fig3_h3_behavioural_signalling** | **WARN** (caption) | (1) per-arm rates == `final_h3_h3_behavioral_per_arm.csv`; outcome composition reproduces from the parquet; the composition "abstained" fraction equals the frozen `appropriate_abstention_rate` for every arm (programmatic check). (6) **four outcomes are shown separately** — correct / incorrect-valid / malformed / abstention. (4) title says "abstains … answers or degenerates" — behavioural, no mechanism; H3-4 mechanism claim is not made. (7) contrast annotation "p_holm = 0, |Δ| ≈ 0.42, identical across 8 seeds" == `final_h3_h3_behavioral_contrasts.csv` + `robustness__per_seed_headline__*`. (10) the green "correct factual answer" segment is invisible in the bars because it is < 1 % for every arm past the window — a caption line stating this is REQUIRED so a reviewer does not think the category was dropped. |
| **tbl4_construct_control** | **PASS** | (1) in-window strict/answered-valid/abstention/malformed == `final_control_validity_control_validity.csv`; example/answer_form from `config/facts.yaml`. (3) compound-relational labelled; note states it is "a single co-located two-clause target — NOT multi-hop retrieval across separated facts". (2) VAL-1, VAL-2. (7) WARNING driver spelled out (strict 0.842 < 0.85 AND abstention 0.115 > 0.10; FAIL 0.70 not reached → retained in H1). |
| **tbl5_deep_recurrent** | **PASS** | (1) == v1.1 `sensitivity__deep_recurrent_retention__per_arm.csv`; deep correct counts (mamba2 1, deltanet 0, gated_deltanet 0) reproduce from the parquet. (6) shows n, strict_correct, strict_accuracy, **Wilson-95 low/high** (never a bare "0"), abstention, wrong-valid n — programmatic check confirms the Wilson columns are present and bracket the point. (2) approved wording verbatim in the note: "No measurable target-specific factual retention …"; and "Do NOT state 'AHN recurrent memory stores nothing'." (9) all 3 AHN arms + Transformer shown separately (Transformer 3/3542 is an informative comparator, not cherry-picking). |
| **appendix_A_H1_sensitivities** | **PASS** | (1)(2) exclude-temporal (frozen, 6/6), **exclude-compound-relational (POST-FREEZE SENSITIVITY, 6/6, omnibus p = 0.0005)** from v1.1, answered-valid all-types (frozen, 8/10), per-seed A_transition (v1.1). (3) note flags that the frozen "temporal_answered_valid" file is actually ALL types. (9) every sub-table included. |
| **appendix_A_H2a_transition_width_amendment** | **PASS** | (8) **the core disclosure**: header + note explain the pre-registered pooled width is mathematically UNDEFINED (pooled 5-type curve peaks ≈ 0.88 < 0.90), that the frozen code falls through to "intermediate", and that the frozen NaN result is preserved verbatim (`appAH2a_FROZEN_pooled_width_RECORD_all_NaN.csv` is shipped). (1) eligibility + widths + CIs == v1.1 `h2_amend__*`. (3)(4) labelled "POST-FREEZE REPORTING AMENDMENT (Option A)", "not a new frozen primary endpoint". (9) both eligible AND ineligible fact types shown, with the mathematical reason for ineligibility. |
| **appendix_A_H2b_residual_exact_failures** | **PASS** | (1) strata reproduce from the parquet via v1.1 `descriptive__residual_fully_exact_failures__*`. (4) labelled "[LIMITATION]"; "No mechanism is claimed"; "the pressure axis is a proxy". (2) VAL-4. (9) all four stratifications (type/arch/target/seed) shipped. |
| **appendix_A_H3_calibration_detail** | **PASS** | (6) gap_change on ANSWERED-VALID only; abstention-confidence kept in a separate sub-table with the note "confidence in emitting 'I don't know' — NEVER treated as factual confidence". (7) note flags that transformer gap_change CI contains 0 (no shift) and that deep-pressure ECE/CWR is small-n. (4) "'overconfident when wrong' is a small-n deep-pressure effect, not a headline". |
| **appendix_A_VAL_control_behaviour** | **PASS** | (6) transformer malformed shown **per arm** (39.6 % vs AHN 1.4–4.8 %); the pooled 12.6 % appears ONLY in the note, ALWAYS next to the split, with the instruction "NEVER cite the pooled malformed rate without the per-arm split". (4) "CONTROL BEHAVIOUR, NOT a pipeline problem" with the three distinguishing facts. Temporal bias described as counterbalanced model response bias, not a shortcut. |
| **appendix_A_REPRO_integrity** | **PASS** | (1) SHA verified this build; re-score mismatches computed live (0/92,160); 53/53 frozen reproduction; 0 blocking gates. (8) analysis versions (v1.0 + v1.1) and the amendment's scope stated. Runtime-commit `d29c6d8` gap disclosed with the 5 hash-equivalence mitigations. |

## Graphical / reporting fixes applied during this audit
- All four figures: replaced the log x-axis (which produced overlapping minor-tick
  labels) with a clean linear model-tat axis, `minorticks_off`, `constrained_layout`;
  fixed title/subtitle collisions and cramped tick labels.
- Fig 2: moved the empirical-knee K markers onto a dedicated CI strip so W (dashed
  vertical line) and K (diamonds) are unambiguously different objects.
- Fig 3: separated the four outcomes into a stacked bar; shortened axis labels;
  removed the suptitle/subtitle overlap.
- Table 3: the A_transition-gap value was in an awkward extra row → moved to a
  footnote with its CI.

**No scientific problem was fixed by changing an endpoint.** Raw strict production
accuracy remains the H1/H2 primary; the H2 width is reported only via the approved
post-freeze amendment; H3 stays behavioural (no mechanism claim).

## Remaining WARN items (manuscript-time, not blockers)
1. **fig1 / fig3 captions** must include: (a) fig1 — "y-axis is end-to-end task
   accuracy and includes abstention, not a retrieval measure"; (b) fig3 — "correct
   factual answers are < 1 % for every architecture past the window (green segment
   not visible)".
2. **fig2 layout** — move the K CI strip inside the accuracy panel or into a labelled
   inset before final typesetting.
3. **fig1 layout** — the "A_transition region" annotation is partly overprinted;
   nudge it or convert to a bracket above the axis.

## BLOCKERS
**None.**

## Claims weakened
**None.** Every exhibit is consistent with `protocol/final_claims_register.md`.
H2-2 and H2-3 are reported at the strength the register already records after the
approved v1.1 amendment (SUPPORTED — concentrated); no claim was downgraded to
build an exhibit.
