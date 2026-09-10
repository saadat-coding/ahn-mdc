# Literature Map

Purpose: the reference backbone for the Introduction, Related Work, and novelty
positioning of the AHN memory-degradation study. Algoverse recency requirement:
the contemporary related-work base must sit in **September 2025 – September 2026**,
with method-attribution / foundational citations the only permitted older entries.

**Verification.** Every entry below was checked on **2026-09-09** by fetching the
live arXiv abstract page (`arxiv.org/abs/<id>`). Titles, author lists, and dates
are as returned by that fetch and still need one human proof-read before the
bibliography is finalised (author lists in particular). Nothing here is cited
from memory. Recency classification is relative to **September 2026**.

Recency buckets: `<=1mo` · `1–3mo` · `3–6mo` · `6–12mo` · `>12mo (exception)`.

---

## A. Contemporary related work (evidence base for positioning)

*Recency buckets in this table are indicative. `REFERENCE_RECENCY_AUDIT.md` is
authoritative and classifies every reference by its **v1 release date**, not by a
later revision (this moves `shortwin2025` and `ahn2025` to the 6–12mo bucket).*

| key | title / authors | arXiv | released | rev. | age (mo) | bucket | role in our paper |
|---|---|---|---|---|---|---|---|
| **ahn2025** | Artificial Hippocampus Networks for Efficient Long-Context Modeling — Fang, Yu, Zhong, Ye, Xiong, Wei | 2510.07318 | 2025-10-08 | 2025-12-17 | ~11 | 6–12mo | **the system under study** (we use their released Qwen2.5-3B AHN checkpoints); also method attribution |
| **shortwin2025** | Short Window Attention Enables Long-Term Memorization — Cabannes, Beck, Szilvasy, Douze, Lomeli, Copet, Mazaré, Synnaeve, Jégou | 2509.24552 | 2025-09-29 | 2026-05-04 | v1 ~12 / v3 ~4 | 3–6mo (latest rev) | prior evidence that *smaller* sliding windows can *improve* long-range recall — directly relevant to our W=256 forcing and to H2 |
| **memmamba2025** | MemMamba: Rethinking Memory Patterns in State Space Model — Y. Wang, Chen, Yan, Lu, Sun | 2510.03279 | 2025-09-28 | — | ~12 | 6–12mo | analyses Mamba's memory-decay mechanism; supports "recurrent state has bounded capacity" framing for H2 / deep-recurrent |
| **recallmamba2026** | On the Recall Scaling Laws in Mamba: A Theoretical and Mechanistic Study via Hashing — Koren, Ben-Kish, Giryes, Wolf, Zimerman | 2609.07681 | 2026-09-07 | — | ~0 | <=1mo | theory for how SSM recall capacity scales with state size / number of facts — frames why deep-recurrent retrieval can be ≈0 |
| **elasticmem2026** | Towards Compressive and Scalable Recurrent Memory (Elastic Memory) — Song, Kai, Lu, Qiu, Z. Lin | 2602.11212 | 2026-02-11 | — | ~7 | 6–12mo | recent compressive fixed-size recurrent memory; contemporary design point for the compressive-vs-lossless trade-off |
| **mamba3_2026** | Mamba-3: Improved Sequence Modeling using State Space Principles — Lahoti, K. Y. Li, B. Chen, C. Wang, Bick, Kolter, Dao, Gu | 2603.15569 | 2026-03-16 | — | ~6 | 3–6mo | ICLR 2026; current state of SSM recurrence — situates the Mamba2/DeltaNet/GDN arms as one generation of a fast-moving family |
| **atlas2026** | ATLAS: All-round Testing of Long-context Abilities across Scales — D. Huang et al. (Meituan) | 2605.28079 | 2026-05-27 | — | ~4 | 3–6mo | large multi-model long-context benchmark finding **task-specific decay** and that "strong retrieval need not transfer to downstream use" — closest contemporary support for H1's non-uniformity and for the retrieval≠task-performance distinction |
| **threshold2026** | Intelligence Degradation in Long-Context LLMs: Critical Threshold Determination via Natural Length Distribution Analysis — W. Wang, Min, Zou | 2601.15300 | 2026-01-07 | — | ~8 | 6–12mo | reports a "critical threshold" where F1 collapses on Qwen2.5-7B — contemporary framing for our empirical knee K (and a contrast: we keep K descriptive, not a claimed constant) |
| **evidence2026** | Diagnosing Evidence Utilization in Long-Context and Retrieval-Augmented Language Models under Matched Evidence Conditions — Xia | 2606.06758 | 2026-06-04 | 2026-06-08 | ~3 | 1–3mo | matched-condition diagnosis of long-context failure modes (parametric fallback, evidence present but unused, cite-without-answer) — method-design kin to our controlled pressure design and outcome classification |
| ~~**absence2025**~~ | AbsenceBench: Language Models Can't Tell What's Missing — Fu, Shrivastava, Moore, West, Tan, Holtzman | 2506.11440 | 2025-06-13 | — | ~15 | **>12mo** | **NOT CITED** (dropped 2026-09-09 during Intro/RW drafting): the general point is covered by `evidence2026` + `atlas2026`; the manuscript does not make the narrow "attention has no token for an absence" argument. Retained here only as a considered near-neighbour. |
| **hesitation2025** | Honesty over Accuracy: Trustworthy Language Models through Reinforced Hesitation — Mohamadi, T. Wang, Z. Li | 2511.11500 | 2025-11-14 | 2025-11-21 | ~10 | 6–12mo | trains abstention via ternary rewards — the **learned-abstention-policy** alternative explanation for H3 (§4.4 of the Discussion) |
| **calib2026** | Confidence Calibration in Large Language Models — N. Michael, BenShushan, Bien, D. A. Moore | 2605.23909 | 2026-04-03 | — | ~5 | 3–6mo | pre-registered calibration study; "hard–easy effect" (overconfidence concentrated on hard items) — directly supports our H3-3 observation that the small answered past-window population is badly overconfident |
| **cic2026** | Uncertainty-Aware Abstention in Large Language Models with Provable Alignment Guarantees — S. Dong, Shinnou | 2607.04430 | 2026-07-05 | — | ~2 | 1–3mo | risk-controlled selective answering — situates "calibrated abstention as a system property" in our Implications |
| **verbalconf2026** | Are LLM Decisions Faithful to Verbal Confidence? — J. Wang, Y. Zhou, Devic, D. Fu | 2601.07767 | 2026-01-12 | — | ~8 | 6–12mo | dissociation between stated confidence and abstention decisions — supports keeping H3 behavioural and not treating abstention as a confidence readout |

## B. Method-attribution / foundational exceptions (>12 months — retained for correct attribution only)

| key | title / authors | arXiv | released | age (mo) | why a recent citation cannot replace it |
|---|---|---|---|---|---|
| **mamba2_2024** | Transformers are SSMs: Generalized Models and Efficient Algorithms Through Structured State Space Duality (Mamba-2) — Dao, Gu | 2405.21060 | 2024-05 | ~28 | The **AHN-Mamba2 arm literally is this recurrence.** Method attribution; ICML 2024. No later paper is the origin of the mechanism we run. |
| **deltanet2024** | Parallelizing Linear Transformers with the Delta Rule over Sequence Length (DeltaNet) — S. Yang, B. Wang, Y. Zhang, Shen, Y. Kim | 2406.06484 | 2024-06 | ~27 | The **AHN-DeltaNet arm is this recurrence.** Method attribution; NeurIPS 2024. |
| **gdn2024** | Gated Delta Networks: Improving Mamba2 with Delta Rule (GatedDeltaNet) — S. Yang, Kautz, Hatamizadeh | 2412.06464 | 2024-12 | ~21 | The **AHN-GatedDeltaNet arm is this recurrence.** Method attribution; ICLR 2025. |
| ~~**mamba2023**~~ | Mamba: Linear-Time Sequence Modeling with Selective State Spaces — Gu, Dao | 2312.00752 | 2023-12 | ~33 | **NOT CITED** (dropped 2026-09-09): the manuscript does not spell out the selective-SSM lineage; `mamba3_2026` + `mamba2_2024` cover the SSM context. |
| **ece2017** | On Calibration of Modern Neural Networks (expected calibration error, reliability diagrams) — Guo, Pleiss, Sun, Weinberger | 1706.04599 | 2017-07 | ~110 | Method attribution for the **ECE / reliability-diagram metric** used in H3-3. A recent survey could be added alongside but is not the origin of the estimator. *(Not yet verified via fetch — standard reference.)* |

Standard statistical tools used in the analysis (isotonic regression / PAVA,
Wilson score interval, Holm step-down, two-level cluster bootstrap,
label-permutation test) are cited to textbook / original-statistics sources, not
to ML literature, and are not part of the recency budget.

---

## C. Novelty audit (September 2025 – September 2026 priority)

**Question:** does a recent paper already do what this study does — a controlled
characterization of the exact-to-compressed memory transition on a deployed
hybrid recurrent-memory model, resolved by information type, together with
behavioural uncertainty signalling as memory degrades?

**Searches run (2026-09-09)**, by topic not by famous-paper name: hybrid neural
memory · recurrent memory language models · compressed-memory LMs · memory
compression degradation · recurrent-state retrieval · long-context memory failure
· effective context length · context utilization · information retention in
long-context models · retrieval under context pressure · SSM / Mamba / DeltaNet /
Gated DeltaNet memory capacity and retrieval · AHN / Artificial Hippocampus
Networks · uncertainty under long context · confidence under context degradation
· abstention in long-context LMs · selective prediction 2026 · knowing when to
abstain · failure detection in LMs · uncertainty calibration in long-context LLMs.

### Nearest neighbours and how we differ

| paper | overlap with our study | what it does *not* do that we do |
|---|---|---|
| **atlas2026** (ATLAS) | task-specific long-context degradation across 26 models; retrieval decays and does not transfer to downstream use | no recurrent-memory architecture contrast; no exact-window / sliding-window manipulation; aggregate benchmark scoring, not a per-fact-type transition curve; no abstention / failure-mode analysis |
| **evidence2026** (Diagnosing Evidence Utilization) | matched-condition design; classifies failure modes (evidence present but unused, cite-without-answer) | Transformer-/RAG-centric; no recurrent memory; no sliding-window pressure axis; no transition-shape or knee analysis; abstention not a primary endpoint |
| **memmamba2025** / **recallmamba2026** | why an SSM's recurrent state has bounded / decaying recall capacity | architecture/theory papers, not an evaluation of a deployed hybrid system under controlled memory pressure; no information-type resolution; no behavioural/abstention analysis; no Transformer-control failure-mode contrast |
| **shortwin2025** (Short Window Attention) | sliding-window size vs long-range recall in a hybrid (SWA + xLSTM) model | training-time study of window scheduling; no per-fact-type degradation; no abstention / uncertainty signalling; not AHN; no exact-to-compressed transition characterization |
| **threshold2026** (Critical Threshold Determination) | an empirical context length where accuracy collapses | single aggregate threshold on one model; treats it as a property to find, whereas we keep K descriptive and show K < W plus residual in-window failure; no architecture contrast; no abstention |
| **absence2025** (AbsenceBench) | LMs fail to notice missing information; attention cannot represent an absence | short contexts (~5k); detection-of-omission task, not retrieval under memory pressure; no recurrent memory; no calibrated-abstention framing |
| **hesitation2025** (Reinforced Hesitation) / **cic2026** / **verbalconf2026** | abstention as a trained/'selective' behaviour; stated-confidence ≠ decision | general QA, not memory degradation; no long-context / window manipulation; they *build* abstention policies, we *observe* an abstention shift and explicitly cannot attribute it |

### Assessment

No September 2025 – September 2026 paper found combines all three of our axes:
(1) a controlled exact-attention-window vs compressed-recurrent-memory transition
on a **deployed hybrid architecture (AHN)** with a matched no-recurrent-memory
control; (2) **information-type-resolved** end-to-end degradation with a
transition-shape / knee characterization; (3) **behavioural uncertainty
signalling** (appropriate-abstention vs unsignalled-failure) as the memory
degrades, with the mechanism left explicitly unresolved.

The closest single competitor is **atlas2026** on axis (1)–(2) at the
benchmark-aggregate level, and **evidence2026** on the failure-mode-taxonomy
method; neither touches the recurrent-memory transition or abstention. The
deep-recurrent negative result (no measurable production retrieval past ≈2W for
AHN) has no direct contemporary counterpart and is consistent with the SSM
capacity theory in **memmamba2025** / **recallmamba2026**.

**Caveat (honesty requirement).** arXiv in this area is moving fast (several of
the papers above are < 3 months old). This audit reflects searches on
2026-09-09; a paper released after that date, or one not surfaced by these
queries, could narrow the gap. If such a paper is found it must be reported even
where it weakens the novelty story. No "first to…", "novel", or "state-of-the-art"
claim should be made in the manuscript until the Related Work section is written
against this map and re-checked.

### Wording discipline for Introduction / Related Work

- Do **not** yet write "first study", "first demonstration", "novel", "SOTA".
- Frame the contribution as: *a controlled, information-type-resolved
  characterization* of the transition, plus *the failure-mode / behavioural
  finding*, on *a specific released hybrid architecture*.
- Every empirical positioning sentence must cite a September 2025 – September 2026
  paper unless it is pure method attribution (Section B).
- Use `[CITE:key]` with the keys in this file; do not invent references.
