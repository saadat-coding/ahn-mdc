# Team Feedback — Final Hostile Check

Question posed by the task: *"If a reviewer saw the raw curves and teammate
comments, could they reasonably accuse the paper of hiding non-monotonic
behavior, conflating W with K, conflating malformed answers with wrong-valid
answers, overstating H3, or claiming a causal architecture effect?"*

Evaluated against the manuscript **after** the minimal edits applied in this
pass (naming fixes; [R50]/[R51] added; Conclusion system-level wording fixed).
Verdicts: **PASS** / **WARN** / **BLOCKER**.

| # | issue | verdict | basis |
|---|---|---|---|
| 1 | Hiding non-monotonic behaviour in Figure 1 | **PASS** | [R50] states the contradictory/numerical rebound at target 235 explicitly, quantifies its reproducibility (8/8 seeds, 3/3 AHN architectures), and states H1's mean-based endpoint does not require monotonicity. A reviewer who plotted the raw per-target curves would find the manuscript already names and scopes exactly what they'd see. |
| 2 | Hiding non-monotonic behaviour in Figure 2 (Transformer abstention) | **PASS** | [R51] states the Transformer's abstention trajectory is not monotonic in pressure, gives the actual shape (decline through 380, sharp rise at 520-760) mirrored by malformed rate, and scopes the H3 pooled statistic explicitly. |
| 3 | Conflating W with K | **PASS** | Every co-occurrence of W and K states K < W and that K is descriptive, not architectural (Methods §2.3, Results [R17]/[R25], Discussion §4.5 title and body, Conclusion). No sentence equates them; the only "compression threshold" occurrence is the required disavowal. |
| 4 | Conflating malformed answers with wrong-valid answers | **PASS** | The four outcomes are defined as mutually exclusive (Methods §2.3) and verified mutually exclusive in the locked data (0 overlap rows, this pass). Malformed is reported as its own rate at every relevant point ([R30], [R42]-[R45], [R51]); the one place it is pooled with wrong-valid (the pre-registered `unsignalled_failure_rate` composite) always ships with the underlying split stated alongside it. |
| 5 | Overstating H3 | **PASS** | H3 is stated as behavioural at every level (Methods, Results, Discussion, Conclusion, Introduction); both mechanistic alternatives (recurrent-state signal vs. learned/distilled policy) are given explicitly and neither is favoured; H3-4 (mechanism) is treated as a prohibited claim throughout. Calibration (H3-3) remains explicitly secondary and scoped to < 5% of past-window trials. |
| 6 | Claiming a causal architecture effect (recurrent memory alone) | **PASS** (was WARN before this pass) | The confound (architecture + training/distillation + other system differences) is stated broadly in Methods, Results, Discussion §4.6, and Related Work — not narrowly scoped to H3 only. One Conclusion sentence ("the recurrent path preserves…") used a mechanism-level subject without a nearby caveat; fixed to "the AHN variants/system," with an explicit system-level-comparison sentence added in the same paragraph. |
| 7 | Pilot data accidentally presented as final evidence | **PASS** | `PILOT_VS_FINAL_DATA_AUDIT.md` traces every pilot/dry-run artifact in the repository and confirms none contributed to any manuscript claim; every `RESULTS.md` number traces to the frozen v1.0 / approved v1.1 outputs from the 92,160-trial locked parquet, per `RESULTS_TRACEABILITY.md` (52/52 traced). |
| 8 | AHN naming inconsistency undermining credibility | **PASS** | Standardized to "Artificial Hippocampus Networks (AHN)" at every point of first expansion across Abstract, Introduction, Related Work, Methods, Methods Extended, and the team page title. |
| 9 | Temporal construct validity insufficiently disclosed | **PASS** | The position effect is reported with exact numbers and correctly scoped ("nets to chance," not "eliminated"); no strengthening or weakening applied. |

## Verdict counts

**PASS: 9 · WARN: 0 · BLOCKER: 0.**

One item (causal architecture framing, Conclusion) was a **WARN prior to this
pass's edit** and is now **PASS** after the minimal wording fix documented in
`SYSTEM_LEVEL_COMPARISON_AUDIT.md`.

## What was deliberately NOT done, per the edit policy

- No hypothesis status changed.
- No statistical endpoint changed, and no post-hoc significance test added —
  [R50]/[R51] are descriptive means/rates from already-scored data, not new
  tests.
- No model inference run.
- No figure altered scientifically, smoothed, or had its non-monotonic
  behaviour removed — the raw exhibits (`outputs/publication_exhibits/main/
  fig1_*`, `fig2_*`) are untouched; the manuscript prose was extended to
  describe what they already show.
- No pressure target cherry-picked — the reported non-monotonicity is
  described using all five (Fig 1) / six (Fig 2) targets in the relevant
  range, not a selected subset.
- No pilot data reinterpreted as final evidence.
- No mechanism claimed for any observed pattern (the 235 rebound, the
  abstention/malformed mirroring) — both are reported descriptively, with
  candidate explanations explicitly left open where the manuscript already
  does so (H1 ordering discussion; H3 two-alternatives framing).
