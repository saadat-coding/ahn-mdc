# Claim-Survival Audit (post-compression)

Checks that every claim in `CLAIM_HIERARCHY.md` survived the compression pass at
the appropriate level. **No Tier 1 claim may be appendix-only.**

## Tier 1 — present and prominent?

| claim | present? | where | prominence |
|---|---|---|---|
| **T1-1** information-type-dependent end-to-end degradation | **YES** | Abstract (sentence 3); Introduction §"Across 92,160 trials"; Results §3.2 [R6]–[R8] with the omnibus $p = 5\times10^{-4}$ and "at least one Holm-adjusted interval excludes zero"; Discussion §4.1; Conclusion (paragraph 2) | headline result, stated in all seven sections; the omnibus statistic and the H1 criterion are in main-text Results |
| **T1-2** AHN near-window transition advantage, +0.249 [0.233, 0.266] | **YES** | Abstract ("pooled difference +0.249, 95% CI [0.233, 0.266]"); Introduction; Results §3.3 [R14] verbatim with "positive in every seed"; Discussion §4.2 (first sentence); Conclusion | the exact figure and CI appear in Abstract, Introduction, Results, and Discussion |
| **T1-3** no measurable deep-recurrent production retrieval | **YES** | Abstract ("essentially absent for all architectures, which does not establish that the recurrent state lacks the information"); Introduction §P6; Results §3.5 [R33]–[R36] with the approved sentence verbatim and the 0/0/1/3 counts + Wilson bounds; Discussion §4.3 (own subsection); Conclusion | own Results subsection; approved wording verbatim; the counts and Wilson bounds are in main-text Results |
| **T1-4** high-pressure AHN shift toward abstention vs unsignalled failure | **YES** | Abstract ("predominantly abstain, whereas the control much more often emits unsupported or malformed output — a difference in failure mode, described behaviourally"); Introduction §P6; Results §3.4 [R26]–[R30] with the rates and the six-contrast statistics; Discussion §4.4; Conclusion | own Results subsection; the past-W+16 rates, the ≈0.42 effect, Holm $p<0.001$, and seed stability are in main-text Results; behavioural-only framing and the two-alternatives caveat present in Results, Discussion, Conclusion |

**All four Tier 1 claims are present, in the main text, with their headline
statistics, and prominent (Abstract + a dedicated Results passage each).**

## Tier 2 — MAIN / APPENDIX / BOTH / REMOVED

| claim | status | detail |
|---|---|---|
| **T2-1** $K < W$ for every architecture; $K \approx 208$ control, $\approx 218$–240 AHN | **BOTH** | main: Abstract, Introduction, Results §3.3 [R16]–[R17], Discussion §4.5, Conclusion — the exact $K$ values and "every $K < W$" are in main-text Results; appendix: per-seed $K$ spread detail (A-H2a) |
| **T2-2** later + broader AHN transition; width post-freeze | **BOTH** | main: Results §3.3 [R20]–[R23] (ΔAIC contrast, the four median widths, the earlier-narrower/later-broader synthesis), Discussion §4.2, Abstract, Introduction, Conclusion — all with the post-freeze label; appendix: per-seed width sensitivity, eligibility diagnostics (A-H2a) |
| **T2-3** information-type ordering (compound-relational fastest, entity-attribute most robust) | **BOTH** | main: Results §3.2 (the five $A_\text{transition}$ values [R6], the ordering statement, the seed-stability [R12]); appendix: full pairwise contrast table, per-seed ordering (A-H1) |
| **T2-4** answered-valid accuracy sensitivity | **BOTH** | main: Results §3.2 [R9] ("2 of the 10 contrasts lose Holm significance … compound-relational stays lowest"), Methods §2.3, Discussion §4.1; appendix: the five per-type answered-valid values, the full re-analysis (A-H1) |
| **T2-5** ≈32% residual exact-attention-eligible failure, rising across 205–235 | **BOTH** | main: Results §3.6 [R46]–[R48] (32.1%, the by-target rates, the by-type rates), Discussion §4.5, Introduction, Conclusion; appendix: by-seed and by-architecture stratification (A-H2b) |
| **T2-6** transition-region conservatism ([R31]); small-population miscalibration ([R32]) | **BOTH** | main: Results §3.4 (gap shift $-0.018$ control vs $-0.063$ to $-0.115$ AHN; "fewer than 5% of past-window trials"; CWR 0.92–0.98), Discussion §4.4; appendix: full calibration tables, abstention-confidence table, deep-pressure ECE (A-H3) |
| **T2-7** Transformer malformed = control behaviour, not pooled pipeline corruption | **BOTH** | main: Results §3.6 [R42]–[R45] (39.6% vs 1.4–4.8%, the per-pressure profile, subtype counts, "12.6% only alongside the per-architecture split"); appendix: per-pressure table, per-item spread (A-VAL) |
| **T2-8** temporal counterbalancing ([R37]–[R38]); compound-relational WARNING ([R39]–[R41]) | **BOTH** | main: Results §3.6 (2×2×2 balanced, the subgroup accuracies, pooled 0.922; 0.842 strict / WARNING drivers / 7-of-8-seeds / 2-of-48-items); appendix: full subgroup and per-item tables (A-VAL) |

**No Tier 2 claim was REMOVED. No Tier 2 claim is APPENDIX-only** — each keeps at
least its headline figure and its interpretive caveat in the main text, with
finer stratification pointed to an existing appendix.

## Tier 3 — interpretations

All six Tier-3 interpretations survive, compressed:
- T3-1 (AHN preserves performance farther into the near-window region) — Discussion §4.2, Conclusion.
- T3-2 (the deep-recurrent null is consequential because AHN is designed for it) — Discussion §4.3.
- T3-3 (behavioural uncertainty signalling as a label) — Results §3.4, Discussion §4.4, Conclusion.
- T3-4 (why information types differ — open questions) — Discussion §4.1 (one sentence).
- T3-5 (residual-failure contributors — undistinguished) — Discussion §4.5 (one sentence).
- T3-6 (evaluate jointly on retrieval, dynamics, failure behaviour) — Discussion §4.7, Conclusion.

## Tier 4 — prohibited inferences

Grep of the seven manuscript sections for the T4 patterns: **none present except
as explicit disavowals** (`knows`/`detects`/`encodes uncertainty` → Discussion
§4.4 disavowal; `stores nothing`/`information is gone` → absent; `compression
begins`/`K = W`/`collapse occurs at W` → absent, Methods carries the disavowal;
`multi-hop reasoning` → only in disavowals; `first`/`novel`/`SOTA` → absent;
"intermediate width" / frozen verdict label → absent; "well-calibrated" (blanket)
→ absent). See `COMPRESSION_HOSTILE_REVIEW.md` checks 4–8, 17–19.

## Verdict

**All Tier 1 claims present, prominent, main-text. All Tier 2 claims retained
(BOTH). No Tier 4 inference introduced.** Compression did not change the claim
hierarchy.
