# Reference Recency Audit

Reference date: **September 9, 2026.** Required primary citation window:
**September 2025 – September 2026.** Source of record: `manuscript/REFERENCES_VERIFIED.bib`
and `manuscript/LITERATURE_MAP.md` (entries verified by live arXiv fetch on
2026-09-09).

This audit is **re-run after drafting** `INTRODUCTION.md` and `RELATED_WORK.md`,
and covers only references **actually cited** in the manuscript. Recency is
classified by **original (v1) release date**, never by a later revision date.

**A. Contemporary related work** = evidence base for the Introduction / Related
Work / positioning. The Algoverse recency target applies to this set.
**B. Method-attribution / foundational** = origin of a mechanism the study runs;
recency does not apply, older is correct.

---

## Set A — contemporary related work (13 cited)

| key | original release | age (mo, as of 2026-09-09) | bucket | in window? |
|---|---|---|---|---|
| `recallmamba2026` | 2026-09-07 | ~0.1 | ≤1mo | yes |
| `cic2026` | 2026-07-05 | ~2.1 | 1–3mo | yes |
| `evidence2026` | 2026-06-04 | ~3.2 | 3–6mo | yes |
| `atlas2026` | 2026-05-27 | ~3.4 | 3–6mo | yes |
| `calib2026` | 2026-04-03 | ~5.2 | 3–6mo | yes |
| `mamba3_2026` | 2026-03-16 | ~5.8 | 3–6mo | yes |
| `elasticmem2026` | 2026-02-11 | ~7.0 | 6–12mo | yes |
| `verbalconf2026` | 2026-01-12 | ~7.9 | 6–12mo | yes |
| `threshold2026` | 2026-01-07 | ~8.1 | 6–12mo | yes |
| `hesitation2025` | 2025-11-14 | ~9.9 | 6–12mo | yes |
| `ahn2025` | 2025-10-08 (rev 2025-12-17) | ~11.1 | 6–12mo | yes |
| `memmamba2025` | 2025-09-28 | ~11.4 | 6–12mo | yes |
| `shortwin2025` | 2025-09-29 (rev 2026-05-04) | ~11.4 by v1 | 6–12mo | yes |

**Note on revisions (per the audit rule):** `ahn2025` (v2 2025-12-17) and
`shortwin2025` (v3 2026-05-04) both carry later revisions; **both are classified
by their v1 date** and land in 6–12mo, not in a more-recent bucket. Neither is
counted as "recent" on the strength of a revision. Both v1 dates are still inside
the required window.

### Set A recency distribution

| bucket | count | keys |
|---|---|---|
| ≤ 1 month | 1 | `recallmamba2026` |
| 1–3 months | 1 | `cic2026` |
| 3–6 months | 4 | `evidence2026`, `atlas2026`, `calib2026`, `mamba3_2026` |
| 6–12 months | 7 | `elasticmem2026`, `verbalconf2026`, `threshold2026`, `hesitation2025`, `ahn2025`, `memmamba2025`, `shortwin2025` |
| > 12 months | 0 | — |

**Within the September 2025 – September 2026 window: 13 / 13 = 100%.**

---

## Set B — method-attribution / foundational (3 cited)

| key | original release | age (mo) | bucket | why retained; why not replaceable |
|---|---|---|---|---|
| `mamba2_2024` — Transformers are SSMs / SSD (Dao & Gu, ICML 2024) | 2024-05-31 | ~28 | >12mo (exception) | the **AHN-Mamba2 arm's recurrence is Mamba-2**; attribution must point to the mechanism's origin |
| `deltanet2024` — Parallelizing Linear Transformers with the Delta Rule (Yang et al., NeurIPS 2024) | 2024-06-10 | ~27 | >12mo (exception) | the **AHN-DeltaNet arm's recurrence is this delta-rule formulation** |
| `gdn2024` — Gated Delta Networks (Yang, Kautz & Hatamizadeh, ICLR 2025) | 2024-12-09 (rev 2025-03-06) | ~21 | >12mo (exception) | the **AHN-GatedDeltaNet arm's recurrence is the gated delta rule from this paper** |

All three are cited **once**, at the single sentence naming the AHN recurrent
modules (Introduction I9 / Related Work R10). None is used to position novelty.
No newer paper is the origin of these mechanisms, so none can be substituted for
recency.

---

## Combined view (for completeness only)

| set | in-window | total | % in window |
|---|---|---|---|
| **A — contemporary related work** | **13** | **13** | **100%** |
| B — method attribution | 0 | 3 | n/a (pre-window by necessity) |
| all cited references | 13 | 16 | 81% |

The number that governs the Algoverse recency expectation is **Set A: 100%
within the one-year window**, comfortably above the 80–90% target. Every
out-of-window reference is a Set B method attribution, cited once, for the
recurrent mechanisms the evaluated AHN checkpoints implement.

---

## Changes since the pre-drafting audit (commit c7f7410)

| ref | pre-drafting status | now | reason |
|---|---|---|---|
| `absence2025` (AbsenceBench, 2025-06-13, ~15mo) | listed as the one >12-month contemporary citation, flagged | **not cited** | the general "long-context models miss / misuse supplied evidence" point is carried by `evidence2026` + `atlas2026` (both in-window); the manuscript does not make the narrow "attention cannot represent an absence" argument, so the older citation is unnecessary |
| `mamba2023` (Mamba, 2023-12, ~33mo) | listed as a weak method-attribution candidate | **not cited** | the selective-SSM lineage is not spelled out in the manuscript; `mamba2_2024` + `mamba3_2026` cover the SSM context |
| `ece2017` (Guo et al., 2017) | listed as a metric-attribution exception | **deferred, not cited yet** | belongs in Methods §2.4 (which computes ECE) and Methods is frozen for this task; to be added when Methods citations are wired. Not yet fetch-verified. |

## Literature-verification status (updated 2026-09-09, this task)

- **WARN A (closest-work negative-scope claims) — CLOSED.** Full text of ATLAS
  (`atlas2026`) and Diagnosing Evidence Utilization (`evidence2026`) read and
  checked against nine specific scope questions (recurrent/compressed memory;
  hybrid exact/recurrent; exact-to-compressed transition; sliding-window
  manipulation; knee vs window; information-type degradation; abstention under
  pressure; failure-mode analysis; deep recurrent retrieval). Every manuscript
  differentiation statement about these two papers is confirmed. `evidence2026`
  *does* report failure/parse-failure diagnosis, which our Related Work already
  credits ("outcome-decomposition spirit"), so no overclaim. Citation map
  R16/R17 upgraded M→H. No manuscript wording change required.
- **WARN B (bibliography) — 16/16 verified.** Titles, author lists, arXiv IDs,
  and v1 dates verified against the arXiv abstract pages. Venues: `mamba2_2024`
  ICML 2024 (verified), `gdn2024` ICLR 2025 (verified), `mamba3_2026` ICLR 2026
  (verified), `deltanet2024` NeurIPS 2024 (author records; flagged for a final
  proceedings-page proof-read). `ahn2025` preprint only (OpenReview UUW0DHqs4f
  not reachable — no venue asserted). `evidence2026` under submission to JAIR.
  Residual: a mechanical proof-read of author-name spelling/diacritics against
  each publisher page (not blocking a draft review).

## Outstanding (non-blocking) actions before final submission

1. Final proceedings-page proof-read of `deltanet2024` venue and of author-name
   diacritics across all entries.
2. Verify `ece2017` (Guo et al. 2017) and add it to Methods §2.4 when Methods
   citations are wired.
3. Re-run the novelty searches close to submission; report any newer overlap.
