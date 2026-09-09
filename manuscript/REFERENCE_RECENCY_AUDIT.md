# Reference Recency Audit

Reference date: **September 2026.** Required primary citation window:
**September 2025 – September 2026.** Source of record: `manuscript/LITERATURE_MAP.md`
(all entries verified by live arXiv fetch on 2026-09-09).

"Contemporary related work" = citations that form the evidence base for the
Introduction / Related Work / novelty positioning (Section A of the map).
"Method-attribution / foundational" = citations retained only for accurate
attribution of a method or metric the study uses (Section B). The recency target
applies to the contemporary set.

---

## 1. Total references

**19** — 14 contemporary related work + 5 method-attribution / foundational.

## 2. References ≤ 1 month old

**1** (of 19; 1 of 14 contemporary)

- `recallmamba2026` — *On the Recall Scaling Laws in Mamba* — arXiv 2609.07681,
  released 2026-09-07 (~0.1 mo).

## 3. References 1–3 months old

**2** (of 19; 2 of 14 contemporary)

- `cic2026` — *Uncertainty-Aware Abstention in LLMs with Provable Alignment
  Guarantees* — arXiv 2607.04430, 2026-07-05 (~2.1 mo).
- `evidence2026` — *Diagnosing Evidence Utilization in Long-Context and RAG LMs
  under Matched Evidence Conditions* — arXiv 2606.06758, 2026-06-04, rev
  2026-06-08 (~3.0 mo).

## 4. References 3–6 months old

**4** (of 19; 4 of 14 contemporary)

- `shortwin2025` — *Short Window Attention Enables Long-Term Memorization* —
  arXiv 2509.24552; v1 2025-09-29, latest revision v3 2026-05-04 (~4.2 mo by
  latest revision; ~11.4 mo by v1).
- `atlas2026` — *ATLAS: All-round Testing of Long-context Abilities across
  Scales* — arXiv 2605.28079, 2026-05-27 (~3.5 mo).
- `calib2026` — *Confidence Calibration in Large Language Models* — arXiv
  2605.23909, 2026-04-03 (~5.2 mo).
- `mamba3-2026` — *Mamba-3: Improved Sequence Modeling using State Space
  Principles* — arXiv 2603.15569, 2026-03-16 (ICLR 2026) (~5.8 mo).

## 5. References 6–12 months old

**6** (of 19; 6 of 14 contemporary)

- `elasticmem2026` — *Towards Compressive and Scalable Recurrent Memory* — arXiv
  2602.11212, 2026-02-11 (~6.9 mo).
- `verbalconf2026` — *Are LLM Decisions Faithful to Verbal Confidence?* — arXiv
  2601.07767, 2026-01-12 (~7.9 mo).
- `threshold2026` — *Intelligence Degradation in Long-Context LLMs: Critical
  Threshold Determination* — arXiv 2601.15300, 2026-01-07 (~8.1 mo).
- `hesitation2025` — *Honesty over Accuracy: Trustworthy Language Models through
  Reinforced Hesitation* — arXiv 2511.11500, 2025-11-14 (~9.9 mo).
- `ahn2025` — *Artificial Hippocampus Networks for Efficient Long-Context
  Modeling* — arXiv 2510.07318, 2025-10-08, rev 2025-12-17 (~11.1 mo).
- `memmamba2025` — *MemMamba: Rethinking Memory Patterns in State Space Model* —
  arXiv 2510.03279, released 2025-09-28 (~11.4 mo).

## 6. References > 12 months old

**6** (of 19; **1 of 14 contemporary**, 5 method-attribution).

**Contemporary (1):**

| ref | date | age | why kept | replaceable by a recent source? |
|---|---|---|---|---|
| `absence2025` — AbsenceBench: Language Models Can't Tell What's Missing (arXiv 2506.11440) | 2025-06-13 | ~15 mo | The specific mechanistic point — a transformer has no token to attend to for an *absence*, so failure to notice missing context is expected — is load-bearing for the H3 discussion that an unsignalled failure is not a detected absence. | **Partially.** The general "long-context models misuse or miss supplied evidence" point is covered by `evidence2026` and `atlas2026` (both in-window). The *absence-has-no-token* argument specifically was not found in any Sept 2025 – Sept 2026 paper by the searches run. **Recommendation:** cite `evidence2026` for the general claim; keep `absence2025` only if the manuscript makes the narrow absence-representation argument, and label it a foundational exception at point of use. If the team prefers a clean window, drop the narrow argument and `absence2025` with it. |

**Method-attribution / foundational (5)** — none of these positions our novelty;
each is the origin of a component the study runs or a metric it reports:

| ref | date | age | component | why a recent citation cannot replace it |
|---|---|---|---|---|
| `mamba2-2024` — Transformers are SSMs / SSD (arXiv 2405.21060, ICML 2024) | 2024-05 | ~28 mo | the **AHN-Mamba2** recurrent arm | the AHN-Mamba2 checkpoint's recurrence *is* Mamba-2; attribution must point to its origin, not to a later SSM paper |
| `deltanet2024` — Parallelizing Linear Transformers with the Delta Rule (arXiv 2406.06484, NeurIPS 2024) | 2024-06 | ~27 mo | the **AHN-DeltaNet** recurrent arm | same: the arm's recurrence is this delta-rule formulation |
| `gdn2024` — Gated Delta Networks (arXiv 2412.06464, ICLR 2025) | 2024-12 | ~21 mo | the **AHN-GatedDeltaNet** recurrent arm | same: the arm's recurrence is the gated delta rule from this paper |
| `mamba2023` — Mamba: Linear-Time Sequence Modeling with Selective State Spaces (arXiv 2312.00752) | 2023-12 | ~33 mo | selective-SSM lineage behind Mamba-2 | **weakest of the five — candidate to drop.** `mamba3-2026` + `mamba2-2024` can carry the lineage; keep only if the text explicitly traces selective SSMs. |
| `ece2017` — On Calibration of Modern Neural Networks (arXiv 1706.04599) | 2017-07 | ~110 mo | **expected calibration error / reliability diagram** used in H3-3 | the ECE estimator and reliability-diagram method originate here; a recent calibration survey (`calib2026` is a study, not a survey) can be added alongside but is not the metric's source. *(Standard reference; not fetched — verify before final bibliography.)* |

## 7. Percentage within the required one-year window

| set | in-window | total | % in window |
|---|---|---|---|
| **Contemporary related work (the number that matters)** | **13** | **14** | **92.9%** |
| Method-attribution / foundational | 0 | 5 | 0% (by design — all are pre-window method origins) |
| All references | 13 | 19 | 68.4% |

The contemporary related-work set meets the Algoverse target (≥ 80–90% within the
one-year window) at **92.9%**. The only >12-month contemporary citation
(`absence2025`) is flagged with a replacement recommendation. All older entries
in the full list are deliberate method-attribution exceptions.

## 8–10. Every > 12-month reference — necessity and replaceability

Consolidated from §6 above:

| ref | age | class | necessary because | recent replacement available? |
|---|---|---|---|---|
| `absence2025` | ~15 mo | contemporary (flagged) | narrow "attention cannot represent an absence" argument for H3 | partial — `evidence2026` covers the general point; keep only for the narrow argument, else drop |
| `mamba2-2024` | ~28 mo | method attribution | the AHN-Mamba2 arm's recurrence | no — method origin |
| `deltanet2024` | ~27 mo | method attribution | the AHN-DeltaNet arm's recurrence | no — method origin |
| `gdn2024` | ~21 mo | method attribution | the AHN-GatedDeltaNet arm's recurrence | no — method origin |
| `mamba2023` | ~33 mo | method attribution (weak) | selective-SSM lineage | yes in effect — coverable by `mamba2-2024` + `mamba3-2026`; **recommend drop unless lineage is spelled out** |
| `ece2017` | ~110 mo | method attribution (metric) | ECE / reliability-diagram estimator for H3-3 | no — metric origin; a recent survey may be cited additionally |

---

## Actions before the bibliography is finalised

1. Human proof-read of every author list and date against the arXiv pages
   (fetched values recorded in `LITERATURE_MAP.md`).
2. Decide `absence2025`: keep (foundational exception, narrow use) or drop with
   the narrow H3 argument.
3. Decide `mamba2023`: keep only if the selective-SSM lineage is stated in text.
4. Verify `ece2017` details (not fetched; standard reference).
5. Re-run the novelty searches close to submission; report any newer overlap even
   if it weakens the novelty story.
6. No "first / novel / SOTA" wording until Related Work is written against this
   audit.
