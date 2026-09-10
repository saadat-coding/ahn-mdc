# Compressed Manuscript — Hostile Review

Skeptical read of the compressed manuscript (`ABSTRACT` → `CONCLUSION`, ~6,900
words) against the pre-compression version at commit 8dd2188. Verdicts:
**PASS** · **WARN** (wording, fixed where resolvable) · **BLOCKER**.

| # | check | verdict | basis |
|---|---|---|---|
| 1 | Did compression make the contribution harder to understand? | **PASS** | The what/when/how framing survives (Introduction §"We organise these into three questions"; Discussion §4.1–4.4; Conclusion). The three contributions are one dense paragraph but each is intact. Abstract still opens with the problem and closes with the takeaway. |
| 2 | Was any negative result hidden? | **PASS** | The deep-recurrent null keeps its own Results subsection (§3.5), an Abstract sentence, a Discussion subsection (§4.3), and a Conclusion sentence; the approved wording is verbatim. The H2-3 UNDETERMINED status is stated in the Results §3.3 status line and [R21]. |
| 3 | Was any caveat lost? | **PASS** | Answered-valid caveat: Methods §2.3, Results §3.2, Discussion §4.1. Post-freeze label: Abstract, Introduction, Methods §2.5, Results [R21]/[R22], Discussion §4.2, Conclusion. Confound: Methods §2.4, Results §3.4, Discussion §4.4 and §4.6, Conclusion. Latent-absence: Abstract, Results §3.5, Discussion §4.3, Conclusion. "No mechanism claimed": Results §3.3, §3.6, Discussion. See `CLAIM_SURVIVAL_AUDIT.md`. |
| 4 | Did H2 accidentally become stronger? | **PASS** | Status line unchanged ("concentrated, non-gradual collapse … the pre-registered *pooled* transition-width statistic was UNDETERMINED"). The earlier-narrower-control / later-broader-AHN asymmetry is stated in Results §3.3, Discussion §4.2, Abstract, Introduction, Conclusion. No "AHN has a sharper transition". |
| 5 | Is post-freeze status still clear? | **PASS** | Every mention of the width carries "post-freeze" / "analysis version 1.1" / "should not be cited as pre-registered". Methods §2.5 is a dedicated subsection. |
| 6 | Is W distinct from K? | **PASS** | Methods §2.3 ("K is a descriptive per-run quantity and is not W"); Results [R17]/[R25]; Discussion §4.5; Abstract; Conclusion. "compression begins at K" appears only as the Methods disavowal. |
| 7 | Is production retrieval distinct from latent information? | **PASS** | Abstract ("does not establish that the recurrent state lacks the information"); Results §3.5 (approved sentence); Discussion §4.3 ("does not establish that the recurrent state contains no target information"); Conclusion. |
| 8 | Is H3 behavioural rather than mechanistic? | **PASS** | Results §3.4 ("whether the behaviour reflects a signal … or a learned abstention policy cannot be determined"); Discussion §4.4 (two-alternatives, "we … avoid any claim that the model 'knows' …"); Conclusion ("we do not claim that the model internally detects forgetting"). Introduction §P6 ("behavioural — it describes what the model emits, not an internal state"). |
| 9 | Is AHN represented fairly? | **PASS** | Introduction §P3 and Related Work: "improve over sliding-window baselines while cutting compute and memory", "these results are aggregate scores", "the method does not claim the compressed state is lossless". |
| 10 | Are recent competitors still acknowledged? | **PASS** | Related Work §"Closest work" names ATLAS, evidence-utilization, MemMamba, the recall scaling laws, Reinforced Hesitation, and risk-controlled selective answering, each with a specific difference. |
| 11 | Is Related Work sufficiently current? | **PASS** | 13 contemporary citations, all September 2025 – September 2026 (see `REFERENCE_RECENCY_AUDIT.md`); 4 method-attribution citations (Mamba-2, DeltaNet, Gated DeltaNet, ECE). |
| 12 | Is the manuscript repetitive? | **WARN → accepted** | The recurrent-state/distillation confound is stated in five places (Methods §2.4, Results §3.4, Discussion §4.4, Discussion §4.6, Conclusion). Each serves a distinct role (design disclosure / H3-4 boundary / mechanism discussion / limitation entry / bounding) and it is a load-bearing caveat; deliberately not cut. "Both views agree the collapse is concentrated" appears in Results §3.3 and Discussion §4.2 — finding vs interpretation, acceptable. No other material repetition. |
| 13 | Are Methods sufficient for evaluation? | **PASS** | Main Methods retains: base model, four arms with checkpoints, W = 256, five information types, 240 items, nested distractor pressure, 12 targets, 8 seeds, 92,160 trials, strict production accuracy, the four-outcome classification, realised `model_tokens_after_target`, K definition, H1/H2/H3 statistical definitions, the post-freeze amendment subsection, and a reproducibility paragraph pointing to `METHODS_EXTENDED.md`. |
| 14 | Are Results sufficient to support the Discussion? | **PASS** | Every Discussion claim cites an R-identifier present in the compressed Results with its headline figure. R9's per-type answered-valid values moved to Appendix A-H1, but the claim it supports (2 of 10 contrasts lose significance) is in the main Results and the Discussion only uses that claim. |
| 15 | Are limitations sufficient? | **PASS** | Discussion §4.6 has eight limitation categories (benchmark, scale/family, confounded comparison, metric, construct scope, H2 amendment, deep-recurrent null, provenance). |
| 16 | Are citations complete? | **WARN → noted** | Every literature-dependent sentence carries a `\citep{}`; 17/17 bib keys resolve and all are cited. `INTRO_RELATED_CITATION_MAP.md` was built against the pre-compression wording — the claims and keys are unchanged but the sentence-level quotes in that map are now stale and should be refreshed in the assembly pass. Not a manuscript defect. |
| 17 | Are all manuscript-facing categories called information types? | **PASS** | 0 occurrences of "fact type" in the seven sections or in `METHODS_EXTENDED.md`; the code identifier `fact_type` and data key `multi-hop` are untouched. |
| 18 | Is compound-relational correctly described? | **PASS** | "a single co-located two-clause target, not multi-hop reasoning over separated facts" (Introduction); "not a genuine multi-hop reasoning task" (Methods §2.2); "not separated-fact multi-hop reasoning" (Discussion §4.6). "multi-hop" appears nowhere else except the data-key note. |
| 19 | Did any unsupported causal wording appear? | **PASS** | Grep for `causes`, `because of`, `due to`, `leads to`, `drives`, `thereby` across the seven sections: one hit — Related Work "attributes … failures to distinct causes" — describing the cited paper's finding, not ours. The AHN-vs-control contrast is observational throughout. |
| 20 | Is any section now unnecessarily long? | **WARN → accepted** | Methods (~1,705) and Results (~1,770) sit ~150–250 words above their per-section guidelines, but the total (~6,900) is inside the 6,500–7,000 target and every required element is present. Further cuts would remove reproducibility detail or traced figures. Left as is per the task instruction not to force below the range at the cost of clarity. |

## Verdict counts

**PASS 17 · WARN 3 · BLOCKER 0.**

- WARN 12 (confound stated 5×): accepted — a required caveat, each instance
  distinct in role.
- WARN 16 (citation map stale quotes): the map's keys/claims are correct; its
  sentence quotes need a refresh during submission-format assembly.
- WARN 20 (Methods/Results slightly over per-section guideline): accepted — total
  in target; no further safe cut.

## Fixes applied during this review

- Removed all LaTeX inline-math scaffolding (`$…$`, `\text{}`, `\vee`, `\geq`,
  `\S\ref{}`, `{#sec:}`) introduced earlier in the pass; the manuscript is back to
  plain readable Markdown with `\citep{}` the only markup, matching the rest of
  the project's manuscript files. No wording or number changed.
- `Results Results 3.6` → `Results 3.6`; `add-one--corrected` → `add-one-corrected`
  (rendering typos from the strip).

No BLOCKER found; no science, number, endpoint, or claim status changed.

## Central positioning statement (unchanged, re-verified against the register)

> Recent work has separately characterized long-context utilization and its
> degradation, the capacity and decay of recurrent memory, and abstention or
> confidence calibration under difficulty. This study connects these questions in
> a controlled evaluation of a hybrid exact/compressed-memory architecture:
> information-type-specific task-performance degradation, transition dynamics that
> keep the architectural window distinct from the empirical performance knee, and
> a shift in failure behaviour toward abstention as retrieval becomes unreliable.
> The behavioural differences do not establish that the recurrent state itself
> encodes uncertainty.

Every clause is at or below its register-allowed strength (H1-1, H2-1, H2-4,
H3-1/2, with H3-4 handled by the closing sentence). No priority language.
