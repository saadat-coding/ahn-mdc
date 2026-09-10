# Conclusion — Hostile Review

Reviewer stance: a skeptical reviewer checking whether the Conclusion
(`manuscript/CONCLUSION.md`, ~396 words) is stronger than the Discussion, repeats
the Abstract, or slips in new claims. Verdicts: **PASS** · **WARN** · **BLOCKER**.

| # | check | verdict | reading |
|---|---|---|---|
| 1 | Stronger than the Discussion? | **PASS** | Every substantive sentence has a matching Discussion sentence at the same or greater hedging. "the dominant observed distinction … is failure behaviour" = Discussion §4.4; "no measurable sustained target-specific factual retrieval … under this production evaluation" = §4.3 + approved wording; "its accuracy transition is also broader, by an explicitly post-freeze width characterization … reshapes the transition rather than translating a sharp cliff" = §4.2; "does not establish that the recurrent state holds no latent target information" = §4.3; "the architecture contrast confounds the presence of a recurrent state with the AHN training and distillation recipe" = §4.2/§4.4; "should not be generalised to other scales or memory designs" = §4.6. |
| 2 | Repeats the Abstract? | **PASS** | Overlapping findings, different function. The Abstract states the results; the Conclusion is organised as what/when/how/boundary/implication and foregrounds the *bounding* clauses and the methodological implication. No sentence is copied. The Conclusion carries no numeric figures (the Abstract carries two); the Abstract has no "these observations are bounded" paragraph. |
| 3 | Introduces new literature? | **PASS** | No citations; no paper named. |
| 4 | Introduces new results? | **PASS** | Every factual statement maps to an existing Results identifier: information-type dependence (R6–R8), K < W and residual in-window failure (R16–R17, R25, R46), later/broader transition (R16, R20, R22), deep-recurrent null (R33–R36), abstention vs unsupported/malformed (R26–R30). "far larger than label-permutation chance" = R7 qualitatively; no new number. |
| 5 | W vs K distinct; K not compression onset? | **PASS** | "the empirical performance transition does not coincide cleanly with the architectural exact-attention window … For every architecture the knee sits below the window". No onset/threshold language. |
| 6 | Deep-recurrent: production failure vs latent absence? | **PASS** | "deep recurrent pressure yields no measurable sustained target-specific factual retrieval under this production evaluation" and, in the bounding paragraph, "A production-level retrieval failure does not establish that the recurrent state holds no latent target information." |
| 7 | H3 behavioural, not mechanistic? | **PASS** | "the dominant observed distinction … is failure behaviour … We describe this as behavioural uncertainty signalling," then "we do not claim that the model internally detects forgetting." |
| 8 | H2: AHN broader not sharper; post-freeze visible? | **PASS** | "its accuracy transition is also broader, by an explicitly post-freeze width characterization". No "sharper". |
| 9 | Novelty / priority language? | **PASS** | None. "the natural next question" is future-work framing, not a priority claim. |
| 10 | Causal overreach? | **PASS** | "preserves useful near-window retrieval longer" and "reshapes the transition" are observational descriptions of task-performance dynamics; the confound is stated explicitly in the bounding paragraph. |
| 11 | Future work concise? | **PASS** | One sentence: training-matched and ablation-based comparisons to separate a recurrent-state signal from a learned output policy. |

## Verdict counts

**PASS 11 · WARN 0 · BLOCKER 0.** No fix required.

## Note

The Conclusion's opening sentence ("We set out to characterize what degrades,
when, and how …") restates the Introduction's framing verbatim in spirit; this is
intentional bookending and not flagged.
