# Abstract — Hostile Review

Reviewer stance: a skeptical reviewer who has read **only the Abstract**
(`manuscript/ABSTRACT.md`, ~222 words) and is deciding whether the paper
overclaims. Verdicts: **PASS** · **WARN** (wording) · **BLOCKER**. Evaluated
after the one fix below.

| # | question | verdict | reading |
|---|---|---|---|
| 1 | What does this paper claim? | **PASS** | Legible from the Abstract alone: (a) end-to-end degradation is information-type dependent; (b) AHN preserves substantially more near-window strict accuracy than a matched control (+0.249 [0.233, 0.266]); (c) the AHN transition is later and — post-freeze — broader, not a shifted copy; (d) the empirical accuracy knee is below the attention window for every arch; (e) deep-recurrent production retrieval is essentially absent for all; (f) at high pressure AHN abstains where the control emits bad output; (g) a methodological takeaway. |
| 2 | Is every claim supported? | **PASS** | From the Abstract a reviewer cannot verify the numbers, but each claim is stated at a strength that matches the claims register (H1-1, H2-1, H2-5, H3-1/2) and the two figures (+0.249 [0.233, 0.266]; 92,160) trace to `RESULTS_TRACEABILITY.md` R14/R1. No claim is stated more strongly than the body supports. |
| 3 | Is the central contribution obvious? | **PASS** | Yes: a controlled characterization of *what* degrades, *when* (relative to the architectural window), and *how failure manifests* in a hybrid exact/compressed-memory system. The what/when/how is implicit in the ordering of sentences rather than named, which is acceptable at abstract length. |
| 4 | Does it sound like AHN successfully retrieves facts at deep recurrent pressure? | **PASS** | No. "At deep recurrent pressure, measurable target-specific factual retrieval under the production evaluation is essentially absent for all architectures." The near-window advantage (sentence 3) and the deep-recurrent null (sentence 5) are separate sentences and cannot be conflated. |
| 5 | Does it imply hidden-state information disappearance? | **PASS** | No. The deep-recurrent sentence is immediately qualified: "which does not establish that the recurrent state lacks the information." |
| 6 | Does it imply AHN knows when it forgets? | **PASS** | No. "a difference in failure mode, described behaviourally." No "knows / detects / aware / uncertainty encoded". |
| 7 | Does it overstate novelty? | **PASS** | No "first / novel / unique / unprecedented / state-of-the-art". The framing is "We characterize this process", not a priority claim. |
| 8 | Does it hide the deep-recurrent negative result? | **PASS** | It is a full, plainly worded sentence in the middle of the Abstract, not buried. |
| 9 | Does it distinguish near-window advantage from deep-memory retrieval? | **PASS** | Explicitly: "Through the near-window transition the AHN variants retain substantially higher strict accuracy" vs "At deep recurrent pressure … essentially absent for all architectures." |
| 10 | Is the Abstract too complicated? | **PASS** (was WARN) | The transition sentence was simplified ("is broader rather than a simple rightward shift of the control's sharper collapse" → "is also broader, rather than simply a rightward shift of the control's sharper collapse") and "empirical performance knee lies below the architectural window" → "empirical accuracy knee falls below the architectural attention window". Two mild-jargon terms remain undefined at abstract length — "post-freeze width characterization" and "empirical accuracy knee" — both are standard for a methods-heavy abstract and are defined on first use in the body; acceptable. |

## Verdict counts

**PASS 10 · WARN 0 · BLOCKER 0** (after 1 fix). Before: PASS 9 · WARN 1.

## Fix applied

- Sentence 4 lightened for readability; "performance knee" → "accuracy knee",
  "architectural window" → "architectural attention window" (clearer to a
  cold reader). No number or claim changed. Word count 222 → 223, still in the
  180–230 target.

## Residual notes (not blockers)

- "post-freeze width characterization" is unavoidable jargon if the Abstract is
  to disclose the amendment; keeping it is the honest choice.
- The what/when/how structure is implicit; a future compression pass could make
  it explicit in one clause if space allows.
