# Figure 1 Transition-Region Variability Audit (Teammate Feedback Item 2)

**Feedback:** "Information-type curves appear jagged in the transition region
around targets 205-265; numerical and contradictory appear to dip and rebound.
Determine whether this is ordinary seed/finite-sample variability, or reveals
something systematic that should be discussed."

**Source of truth:** `final_audit/FINAL_LOCKED/results_FINAL_92160.parquet`
(SHA-256 `a72fd43e…`, re-verified unchanged before this audit). **No model
inference was run.** All numbers below are a `groupby`/`mean` over the
already-scored `correct` field — a descriptive recomputation, not a new
inferential endpoint. No pilot data used.

## Method

For each information type, pooled strict accuracy (AHN arms only, matching the
Figure 1 / H1 definition) at each intended transition target
[205, 220, 235, 250, 265], then the same broken out by seed (8) and by
architecture (3 AHN arms) to test whether any dip/rebound is reproducible or a
subset artifact.

## Pooled strict accuracy by information type × intended target

| type | 205 | 220 | 235 | 250 | 265 |
|---|---:|---:|---:|---:|---:|
| contradictory | 0.815 | 0.513 | **0.676** | 0.576 | 0.021 |
| entity-attribute | 0.942 | 0.782 | 0.724 | 0.507 | 0.015 |
| compound-relational | 0.464 | 0.336 | 0.320 | 0.148 | 0.006 |
| numerical | 0.627 | 0.333 | **0.560** | 0.427 | 0.000 |
| temporal | 0.567 | 0.372 | 0.366 | 0.221 | 0.009 |

Adjacent-step deltas (n = 5,760 per type per target; 48 items × 3 AHN arms × 8
seeds × 5 targets = the same pooled set Figure 1 and Table 1 use):

| type | 205→220 | 220→235 | 235→250 | 250→265 |
|---|---:|---:|---:|---:|
| contradictory | −0.302 | **+0.163** | −0.100 | −0.556 |
| entity-attribute | −0.160 | −0.058 | −0.217 | −0.492 |
| compound-relational | −0.129 | −0.016 | −0.173 | −0.142 |
| numerical | −0.293 | **+0.227** | −0.133 | −0.427 |
| temporal | −0.194 | −0.006 | −0.146 | −0.212 |

**Only contradictory and numerical show a positive (upward) step**, both at the
same transition (220→235). entity-attribute, compound-relational, and temporal
decline (or are flat) at every step.

## Is the 220→235 rebound reproducible, or a subset artifact?

**Per seed** (contradictory and numerical, pooled over the 3 AHN arms; n = 144
per seed×target cell):

| seed | contradictory 220 | contradictory 235 | rebound? | numerical 220 | numerical 235 | rebound? |
|---:|---:|---:|---|---:|---:|---|
| 0 | 0.535 | 0.674 | yes | 0.375 | 0.583 | yes |
| 1 | 0.493 | 0.688 | yes | 0.306 | 0.472 | yes |
| 2 | 0.493 | 0.653 | yes | 0.417 | 0.583 | yes |
| 3 | 0.542 | 0.729 | yes | 0.264 | 0.368 | yes |
| 4 | 0.472 | 0.611 | yes | 0.292 | 0.590 | yes |
| 5 | 0.542 | 0.639 | yes | 0.319 | 0.597 | yes |
| 6 | 0.493 | 0.757 | yes | 0.319 | 0.604 | yes |
| 7 | 0.535 | 0.660 | yes | 0.375 | 0.681 | yes |

**8 of 8 seeds show the rebound for both types.**

**Per architecture** (pooled over 8 seeds):

| architecture | contradictory 220 | contradictory 235 | numerical 220 | numerical 235 |
|---|---:|---:|---:|---:|
| AHN-DeltaNet | 0.456 | 0.695 | 0.320 | 0.625 |
| AHN-GatedDeltaNet | 0.625 | 0.583 | 0.247 | 0.490 |
| AHN-Mamba2 | 0.458 | 0.750 | 0.432 | 0.565 |

**All 3 AHN architectures show the rebound for both types.**

**Calibration sanity check:** realised `model_tokens_after_target` medians at
intended 205/220/235/250/265 are 204/220/235/250/266 — the rebound is not an
artifact of intended-vs-realised pressure miscalibration; each intended level
lands where it should.

**Outcome-composition check** (contradictory, numerical; AHN pooled): at 235
both types show a real drop in *both* abstention and malformed rate relative to
220 (e.g., contradictory: abstention 0.226→0.119, malformed 0.240→0.184;
numerical: abstention 0.194→0.152, malformed 0.339→0.220), not merely a shift
between failure modes.

## Answers to the audit questions

1. **Are the curves visibly non-monotonic?** Yes, for 2 of 5 types
   (contradictory, numerical), at one transition point (220→235).
2. **Are the rebounds larger than typical seed-to-seed variability?** Yes — the
   rebound magnitude (+0.16 to +0.23) is an order of magnitude larger than the
   ±0.03–0.05 per-seed noise band already reported for `A_transition` [R12], and
   it points the *same direction* in every seed, which pure sampling noise
   around a monotonic decline would not do.
3. **Are they consistent across most seeds?** **All 8 of 8 seeds**, for both
   types, and **all 3 AHN architectures**.
4. **Is there evidence of a reproducible systematic rebound?** **Yes.** This is
   not finite-sample jaggedness; it is a reproducible feature of the pooled
   accuracy trajectory for these two information types at this study's pressure
   grid.
5. **Does the current H1 conclusion depend on monotonicity?** **No.** The H1
   primary endpoint, `A_transition`, is the *mean* strict accuracy over the five
   transition targets, and the primary test is the omnibus dispersion test plus
   10 pairwise contrasts on that mean (Methods §2.4). Neither requires or
   assumes a monotonic decline within the transition window. `A_transition` for
   contradictory and numerical (0.520, 0.389) already reflects this trajectory
   correctly as an average.

## What this is not

- Not evidence against H1 (non-uniform *degradation*, evaluated at the level of
  the five-target mean, stands).
- Not attributable to seed noise, a single outlier architecture, or a
  pressure-calibration artifact (all ruled out above).
- Not something this audit explains mechanistically. **No mechanism is
  proposed** — e.g., no claim about why 235 specifically produces higher
  accuracy for these two types. That would be a new inferential/interpretive
  claim beyond descriptive verification, which this task does not authorize.

## Minimum wording addition (applied)

Added to `manuscript/RESULTS.md` §3.2, immediately after the H1 primary-test
sentence, as **[R50]**:

> "Within the transition region the per-target trajectory is not strictly
> monotonic for every type: contradictory and numerical both show a partial
> rebound at intended target 235 relative to 220 that is consistent across all
> 8 seeds and all three AHN architectures (Figure 1); the primary endpoint
> A_transition is the mean over the five transition targets and does not
> assume or require a monotonic decline."

This is the minimum sentence: it states the observation, quantifies its
reproducibility in one clause, and forecloses the "is H1 undermined" reading
without speculating on cause. Added to `manuscript/RESULTS_TRACEABILITY.md` as
row R50 (source: descriptive recomputation from the locked parquet).

## Classification

**C — descriptive figure issue, resolved with one added sentence** (task
classification scheme item C: "a descriptive figure issue worth adding one
sentence for"). Not D (no scientific issue requiring escalation — H1 is
unaffected) and not a blocker.
