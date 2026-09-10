# Introduction + Related Work — Hostile Review

Reviewer stance: a skeptical 2026 ML/NLP reviewer who assumes the authors want to
oversell novelty and under-cite competitors. Verdicts: **PASS** · **WARN**
(wording risk, fixed where resolvable without changing the science) · **BLOCKER**
(must fix). Evaluated after the fixes in "Fixes applied" were made.

| # | check | verdict | basis |
|---|---|---|---|
| 1 | Is novelty exaggerated? | **PASS** (was WARN) | The closing of Related Work now reads "This study brings these lines together: …" (was "To our reading these lines have not been combined"). Contributions are phrased as "A controlled characterization of…", not as a priority claim. |
| 2 | Does any sentence imply "first"? | **PASS** | Grep over both files for `first`, `first-ever`, `no prior`, `no previous`, `novel`, `unique`, `unprecedented`, `state[- ]of[- ]the[- ]art` → **zero matches**. |
| 3 | Is AHN represented fairly? | **PASS** | Intro §P3: AHN "improve over sliding-window baselines while cutting compute and memory", results "reported as aggregate scores", "the method does not claim that the compressed state is lossless". No straw-manning. |
| 4 | Are recent competing papers acknowledged? | **PASS** | Related Work §2.4 is a dedicated closest-work paragraph naming ATLAS, evidence2026, MemMamba, the Mamba recall-scaling paper, Reinforced Hesitation, and CIC, each with a specific difference. |
| 5 | Is ATLAS differentiated correctly? | **PASS** (WARN carried) | "operates at the benchmark-aggregate level, does not contrast a recurrent-memory architecture with a matched control, and does not manipulate an exact-attention boundary or analyse abstention." Defensible from ATLAS's described method; **carried WARN**: re-verify the negative-scope claim against the full paper before camera-ready (citation-map R16). |
| 6 | Is Diagnosing Evidence Utilization differentiated correctly? | **PASS** (WARN carried) | "Transformer- and retrieval-centric, without a recurrent memory or a transition-shape analysis." Its matched conditions (long-context vs RAG vs compact) contain no recurrent arm. Carried WARN: re-verify against full paper (citation-map R17). |
| 7 | Are MemMamba / Recall Scaling Laws differentiated correctly? | **PASS** | Framed as "explain why a bounded recurrent state has limited and decaying recall … neither evaluates a deployed hybrid system under controlled pressure or examines failure behaviour," and explicitly used "to interpret — not to mechanistically explain — the deep-recurrent negative result." |
| 8 | Are long-context degradation and compression kept distinct? | **PASS** | Related Work §2.1 closes: "We treat ordinary long-context degradation and the exact-to-compressed transition as related but not identical … we do not equate the pressure axis with a clean switch from lossless to compressed memory," with the residual-in-window-failure evidence cited as the reason. |
| 9 | Is theoretical memory capacity distinguished from production retrieval? | **PASS** | Related Work §2.2: "A key distinction we maintain is between theoretical or architectural memory capacity and production-level target retrieval … we do not present that result as evidence about the recurrent state's contents." |
| 10 | Is abstention novelty overstated? | **PASS** | Related Work §2.3: "We do not introduce an abstention method or a calibration technique. We observe how a model's spontaneous failure behaviour … changes." |
| 11 | Is H3 behavioural rather than mechanistic? | **PASS** | Intro §P6: "This last result is behavioural: it describes what the model emits, not an internal state, and the experiment does not separate a signal in the recurrent state from a learned abstention policy." Related Work §2.3 repeats the two-alternatives framing. |
| 12 | Does the Introduction accurately preview the actual results? | **PASS** | Each previewed finding in §P6 maps to a Results identifier: info-type dependence (R6–R9), near-window advantage (R14), later/broader transition (R20, R22), K<W + residual in-window failure (R16–R17, R25, R46), deep-recurrent ≈0 (R33–R34), abstention shift (R26–R27). No finding is previewed that Results does not contain. |
| 13 | Are post-freeze H2 widths accidentally presented as preregistered? | **PASS** (was WARN) | Intro §P5 discloses "one reporting metric was undefined … corrected by a documented post-freeze amendment"; §P6 now qualifies the "broader" preview as "by a post-freeze width analysis". Related Work does not mention widths at all. |
| 14 | Is K distinguished from W? | **PASS** | Intro §P5 ("estimate an empirical performance knee K"), §P6 ("the empirical knee K lies below the architectural window W"), Contribution 2 ("keeps the architectural window W distinct from the empirical performance knee K"); Related Work §2.4 ("separates the architectural window from the empirical knee"). |
| 15 | Does any citation fail to support its sentence? | **PASS** | All 31 literature-dependent sentences mapped (`INTRO_RELATED_CITATION_MAP.md`); 24 DIRECT, 4 SYNTHESIS (all constituent papers cited), 2 INFERENCE (I11 "does not claim lossless" — a negative about AHN's framing; R15 "learned/distilled abstention policy … alternative" — phrased as an alternative, never asserted of AHN). No citation supports only a different part of its claim. |
| 16 | References outside the one-year window without justification? | **PASS** | 3 cited references predate the window: `mamba2_2024`, `deltanet2024`, `gdn2024` — each the origin of one AHN recurrent arm, cited once at the sentence naming the modules. Justified in `REFERENCE_RECENCY_AUDIT.md` Set B. Contemporary set: 13/13 in window. |
| 17 | Are any bibliographic details unverified? | **WARN** (disclosed) | All 16 cited references were checked by fetching their arXiv abstract page on 2026-09-09; **venue lines** (ICML 2024, NeurIPS 2024, ICLR 2025, ICLR 2026) and **full author lists** still need a human proof-read against the ACL Anthology / OpenReview / PMLR / publisher page. This is stated in the `.bib` header and the recency audit's "Outstanding literature actions". Not a blocker for a draft; must be closed before submission. |
| 18 | Is Related Work a synthesis, not a paper-by-paper list? | **PASS** | §2.1–2.3 are organised by claim, each grouping multiple papers; §2.4 is an explicit closest-work comparison. No "Author (year) did X. Author (year) did Y." enumeration. |

## Verdict counts

- **PASS 16 · WARN 2 · BLOCKER 0** (both WARNs are process items — re-verify
  negative-scope claims #5/#6 against full texts, and proof-read venue/author
  lines #17 — not wording defects in the current draft).
- Before fixes: PASS 13 · WARN 5 · BLOCKER 0.

## Fixes applied

1. **#1 / #2 (novelty phrasing).** Related Work closing sentence changed from "To
   our reading these lines have not been combined: …" to "This study brings these
   lines together: …" — states the contribution without a coverage claim about
   the literature.
2. **#13 (post-freeze width).** Introduction §P6 "later but also *broader*" →
   "later than the control's and, by a post-freeze width analysis, also
   *broader*", tying the qualitative preview to the disclosure already in §P5.

No science changed; no number changed; Methods, Results, Discussion, the claims
register, and the exhibits were not touched.

## Wording weakened during hostile review

- "these lines have not been combined" → "This study brings these lines together"
  (removes an implicit coverage claim).
- "later but also broader" → "later … and, by a post-freeze width analysis, also
  broader" (adds the post-freeze qualifier).
- No claim status changed; no positive claim was strengthened.

## Carried WARNs (must close before submission, not before a draft review)

- Re-verify the negative-scope statements about ATLAS and evidence2026
  (citation-map R16–R18) against the full papers, not the abstracts.
- Human proof-read of every author list, date, and venue in
  `REFERENCES_VERIFIED.bib`.
- `ece2017` is not yet fetch-verified and is not cited (deferred to Methods).

---

## Final novelty / positioning statement (publication-safe)

> Recent work has separately characterized long-context utilization and its
> degradation, the capacity and decay of recurrent memory, and abstention or
> confidence calibration under difficulty. This study connects these questions in
> a controlled evaluation of a hybrid exact/compressed-memory architecture: we
> characterize information-type-specific task-performance degradation under
> increasing memory pressure, the dynamics of the performance transition around
> the architectural memory boundary — distinguishing the architectural window
> from the empirical performance knee — and how output behaviour changes as
> retrieval becomes unreliable, with a recurrent memory shifting failures toward
> abstention rather than unsupported output. We do not claim priority for any of
> the individual questions, and we do not attribute the behavioural shift to a
> mechanism.

**Check against the claims register and the literature map:**

| clause | support | safe? |
|---|---|---|
| "Recent work has separately characterized long-context utilization … recurrent memory … abstention/calibration" | atlas2026, evidence2026, threshold2026, shortwin2025 / memmamba2025, recallmamba2026, elasticmem2026, mamba3_2026 / hesitation2025, cic2026, calib2026, verbalconf2026 | yes — each area has ≥3 in-window citations |
| "controlled evaluation of a hybrid exact/compressed-memory architecture" | our design (Methods); ahn2025 for the architecture | yes |
| "information-type-specific task-performance degradation" | H1-1 SUPPORTED (register); Results R6–R9 | yes |
| "distinguishing the architectural window from the empirical performance knee" | H2-4 SUPPORTED; Results R16–R17, R25 | yes |
| "output behaviour changes … shifting failures toward abstention rather than unsupported output" | H3-1/H3-2 SUPPORTED; Results R26–R27, R30 | yes |
| "We do not claim priority … do not attribute the behavioural shift to a mechanism" | H3-4 PROHIBITED CLAIM handled | yes — this is the guard |

No clause asserts priority or a mechanism; every empirical clause is at or below
its register-allowed strength.
