# Claim Hierarchy

The paper's conclusions ranked by how firmly the evidence establishes them.
Classification follows `protocol/final_claims_register.md`. This document guides
the page-budget compression pass: **Tier 1 must survive intact; Tier 2 may be
compressed or moved to an appendix; Tier 3 is interpretation that can be
shortened; Tier 4 must never appear.**

---

## TIER 1 — Primary claims (the paper establishes these)

| # | claim | register | evidence | frozen? |
|---|---|---|---|---|
| **T1-1** | Loss of end-to-end task performance under memory pressure is **information-type dependent**. | H1-1 SUPPORTED | five transition-region accuracies span ≈0.26–0.59; label-permutation omnibus p = 5×10⁻⁴ (0/2000); all 10 Holm-adjusted pairwise intervals exclude zero (Results R6–R8) | frozen v1.0 |
| **T1-2** | Through the near-window transition the AHN variants **preserve substantially more strict accuracy** than a matched no-recurrent-memory control. | H2-1 SUPPORTED | pooled AHN − Transformer = +0.249, 95% CI [0.233, 0.266], positive in every seed (Results R14–R15) | frozen v1.0 |
| **T1-3** | At deep recurrent pressure (≥ 2W) **no measurable target-specific factual retrieval** is observed under the production evaluation, for every architecture. | H2-5 NEGATIVE RESULT | 0 / 0 / 1 / 3 correct of 3,542 per arm; Wilson-95 upper bounds ≤ 0.0025; no fact type shows retention (Results R33–R36) | v1.1 sensitivity (counts reproduce from locked parquet) |
| **T1-4** | As retrieval becomes unreliable, the AHN variants **shift toward abstention** rather than unsignalled failure, far more than the control. | H3-1, H3-2 SUPPORTED | past W+16: appropriate-abstention 0.929–0.946 (AHN) vs 0.516 (control); unsignalled-failure 0.052–0.071 vs 0.480; six contrasts |Δ|≈0.42, Holm p < 0.001, identical direction in all 8 seeds (Results R26–R30) | frozen v1.0 |

---

## TIER 2 — Secondary characterizations (sensitivity-, metric-, or amendment-dependent)

| # | claim | register | dependency |
|---|---|---|---|
| **T2-1** | The empirical performance knee **K lies below the architectural window W** for every architecture (K ≈ 208 control, ≈ 218–240 AHN; W = 256). | H2-4 SUPPORTED | K is a descriptive per-run quantity; the control knee is tightly located but the AHN knees are a seed-spread range, reported as an interval |
| **T2-2** | The AHN accuracy transition is **later and broader** than the control's — the recurrent path reshapes the transition rather than translating a sharp cliff. | H2-2 SUPPORTED (concentrated); H2-3 UNDETERMINED (frozen) / SUPPORTED–concentrated (v1.1) | "later" is frozen (K); "broader" rests on the **post-freeze** per-eligible-type 90→10 width amendment (v1.1) — median ≈32 tokens control vs ≈62–74 AHN — and must always be flagged post-freeze; the frozen AIC change-point test agrees on "concentrated" but is thin for the control (ΔAIC ≈ −0.7) |
| **T2-3** | The information-type **ordering** (compound-relational fastest, entity-attribute most robust). | H1-2 PARTIALLY SUPPORTED | middle ranks compress under answered-valid accuracy; the two lowest-ranked types have elevated in-window abstention; one seed swaps the two lowest |
| **T2-4** | Answered-valid accuracy (retrieval among parseable answers) as a sensitivity to the strict metric. | H1-1 required sensitivity | changes the estimand; a pre-registered secondary, never a replacement |
| **T2-5** | Retrieval already fails on **≈ 32% of trials whose target is arithmetically inside the lossless window**, rising steeply across intended pressures 205–235. | VAL-4 LIMITATION | v1.1 descriptive; no mechanism claimed; used to argue the transition is not a clean inside/outside boundary |
| **T2-6** | In the transition the AHN variants become **more conservative on answered trials** (confidence − accuracy shifts −0.06 to −0.12) while the control does not shift; the small past-window answered population is badly calibrated. | H3-3 PARTIALLY SUPPORTED | secondary; "badly calibrated" scoped to < 5% of past-window trials; sequence-probability confidence is provisional |
| **T2-7** | The control's high past-window malformed rate is architecture-specific control behaviour, not pipeline corruption. | VAL-3 LIMITATION/DISCLOSURE | per-architecture split always shown; pooled 12.6% never cited alone |
| **T2-8** | The temporal type has a counterbalanced directional response bias; compound-relational carries an in-window control WARNING (≈0.84 ceiling). | VAL-1 SUPPORTED (with disclosure); VAL-2 LIMITATION + WARNING | both types retained in the H1 primary; ranks read with the answered-valid sensitivity |

---

## TIER 3 — Interpretations (evidence-consistent, not directly established)

| # | interpretation |
|---|---|
| **T3-1** | The recurrent path "preserves useful task performance farther into the near-window region" — a reading of T1-2 + T2-1 + T2-2 together. |
| **T3-2** | The deep-recurrent null (T1-3) is consequential *because* AHN is designed to carry information beyond the window — a "so what", not a result. |
| **T3-3** | The abstention shift (T1-4) constitutes "behavioural uncertainty signalling" / "failure-mode adaptation" — a labelling of the behaviour, not a mechanism. |
| **T3-4** | Candidate reasons information types differ (answer-space structure, task complexity, model prior, abstention tendency, relational structure, retrieval–output interaction) — open questions. |
| **T3-5** | Candidate contributors to residual in-window failure (context interference, attention competition, prompt/task effects, generation behaviour, span-boundary effects) — not distinguished by this design. |
| **T3-6** | Implication: compressed-memory systems should be evaluated jointly on retrieval, degradation dynamics, and failure behaviour. |

---

## TIER 4 — Prohibited inferences (must never appear, except as explicit disavowals)

| # | prohibited claim | why |
|---|---|---|
| **T4-1** | The recurrent state mechanistically represents / detects / is aware that information has been lost; "the model knows it forgot". | H3-4 PROHIBITED CLAIM — the architecture contrast confounds a recurrent state with the AHN distillation recipe |
| **T4-2** | "AHN stores nothing" / "the information is gone" / "no information remains in the recurrent state". | H2-5 — a production-retrieval null is not evidence about latent state contents |
| **T4-3** | "Compression begins at K" / "K is the compression threshold" / "collapse occurs at W" / "K = W". | H2-4 — K is descriptive and every K < W; residual in-window failure blocks a boundary story |
| **T4-4** | Compound-relational is genuine multi-hop reasoning / retrieval across separated facts / chained inference. | VAL-2 — it is a single co-located two-clause target |
| **T4-5** | Fact types are "forgotten" / "lost from the representation" at different rates. | H1-1 — raw strict blends retrieval loss with abstention propensity |
| **T4-6** | "AHN is well-calibrated" (blanket) / headline "overconfident when wrong" without the < 5% scope. | H3-3 |
| **T4-7** | The post-freeze per-type widths are a pre-registered / frozen primary endpoint; use of the frozen "intermediate" verdict label. | H2-3 |
| **T4-8** | "AHN solves long-context retrieval" / any framing that ignores that all arms collapse past W. | H2-1 |
| **T4-9** | Near-window degradation is caused solely by the exact→compressed transition. | VAL-4 |
| **T4-10** | The temporal benchmark is invalid / the model exploits a positional shortcut. | VAL-1 — the bias is counterbalanced |
| **T4-11** | Any "first / novel / unprecedented / state-of-the-art" framing. | not established; not required |

---

## Compression guidance

- **Keep verbatim:** T1-1…T1-4 with their headline statistics; the W≠K
  distinction (T2-1); the post-freeze flag on T2-2; the deep-recurrent
  approved sentence (T1-3); the behavioural framing of T1-4 (T3-3) and its
  two-alternatives caveat (T4-1 disavowal).
- **Compressible / appendix-movable:** T2-3…T2-8 detail (per-seed ranges,
  subtype counts, exact gate mechanics, calibration tables), T3-4/T3-5 lists.
- **Already minimal:** T3-1, T3-2, T3-6 — one sentence each; do not expand.
