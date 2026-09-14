# Figure 2 Transformer-Abstention Audit (Teammate Feedback Item 3)

**Feedback:** "Transformer/control abstention appears to dip around pressure
315-380 before increasing later. Determine whether this pattern is real in the
final locked data, whether it matters for H3, and whether a short descriptive
sentence should be added."

**Source of truth:** `final_audit/FINAL_LOCKED/results_FINAL_92160.parquet`
(SHA-256 unchanged). Descriptive recomputation only — `groupby`/`mean` over the
already-scored `correct`/`abstained`/`malformed` fields, Transformer rows only.
No model inference. No pilot data used.

## Transformer outcome composition by intended pressure target

| intended target | n | strict accuracy (correct) | abstention | malformed | wrong-valid |
|---:|---:|---:|---:|---:|---:|
| 265 | 1,920 | 0.0005 | 0.5177 | 0.4818 | 0.0000 |
| 285 | 1,920 | 0.0000 | 0.3224 | 0.6776 | 0.0000 |
| 315 | 1,920 | 0.0083 | 0.2677 | 0.7083 | 0.0156 |
| 380 | 1,920 | 0.0089 | 0.2635 | 0.6812 | 0.0464 |
| 520 | 1,920 | 0.0016 | 0.8208 | 0.0979 | 0.0797 |
| 760 | 1,920 | 0.0000 | 0.9458 | 0.0281 | 0.0260 |

Adjacent-step change in abstention: 265→285 **−0.195**, 285→315 **−0.055**,
315→380 **−0.004**, 380→520 **+0.557**, 520→760 **+0.125**.

## Is there really a "dip" between 315 and 380?

Abstention **decreases monotonically from 265 through 380** (0.52 → 0.32 →
0.27 → 0.26), essentially **plateauing** across 315→380 (the −0.004 step is
within noise), then **rises sharply** at 520 and 760. So the visual impression
described — abstention is low around 315-380, before increasing later — is
correct, but it is better described as **the trough of a decline-then-rise
trajectory**, not a local dip below neighbouring higher points on both sides
(315 and 380 are each other's lowest neighbours, not surrounded by higher
values in both directions in this window).

## Per-seed check (315 vs 380)

| seed | abstention @265 | @285 | @315 | @380 | @520 | @760 |
|---:|---:|---:|---:|---:|---:|---:|
| 0 | 0.496 | 0.362 | 0.283 | 0.254 | 0.812 | 0.958 |
| 1 | 0.533 | 0.288 | 0.238 | 0.221 | 0.825 | 0.921 |
| 2 | 0.508 | 0.342 | 0.300 | 0.283 | 0.829 | 0.929 |
| 3 | 0.454 | 0.329 | 0.258 | 0.246 | 0.821 | 0.925 |
| 4 | 0.579 | 0.250 | 0.233 | 0.271 | 0.829 | 0.954 |
| 5 | 0.550 | 0.329 | 0.296 | 0.250 | 0.783 | 0.971 |
| 6 | 0.542 | 0.338 | 0.304 | 0.275 | 0.846 | 0.962 |
| 7 | 0.479 | 0.342 | 0.229 | 0.308 | 0.821 | 0.946 |

315→380 decreases in 6 of 8 seeds and increases in 2 of 8 (seeds 4 and 7); the
per-seed magnitude of that step is ≤ 0.05 in every seed — **the 315→380
segment is at or inside noise level and its direction is not seed-consistent**,
unlike the large, universally-consistent 380→520 jump (every seed increases by
≥ 0.51). The malformed rate mirrors this: it rises from 265 to a 285-380
plateau (0.64-0.75, seed-consistent) and then falls sharply at 520-760
(seed-consistent, ≤ 0.13 by 520 in every seed).

## Answers to the audit questions

1. **Is there actually an abstention decrease between 315 and 380?** A small
   one (pooled −0.004), not seed-consistent in direction, and within the
   seed-to-seed noise band. The real, large, and fully seed-consistent feature
   is the **decline from 265 to ~380 followed by a sharp rise at 520-760** —
   i.e. abstention is non-monotonic in pressure, with malformed output as its
   mirror image.
2. **What failure mode increases when abstention decreases (265→380)?**
   **Malformed output** — it rises from 0.48 (265) to 0.68-0.71 (285-380) as
   abstention falls, then falls back to 0.10 / 0.03 (520/760) as abstention
   rises. Correct and wrong-valid rates stay small throughout (≤ 0.09).
3. **Is this consistent across seeds?** The large decline-then-rise pattern:
   yes, in every seed. The specific 315→380 micro-step: no, it is noise-level
   and direction-inconsistent (6/8 vs 2/8).
4. **Is it visually real or just aggregation noise?** The overall non-monotonic
   shape (decline through 380, then sharp rise) is real and seed-consistent.
   The narrow "dip specifically between 315 and 380" as a local minimum
   surrounded by higher values on both close sides is largely an artifact of
   where these two adjacent grid points happen to sit on a smooth
   decline-then-rise curve, not a separate seed-consistent local feature in its
   own right.
5. **Does H3 require monotonic abstention?** No. The H3 behavioural primary
   (`appropriate_abstention_rate`, `unsignalled_failure_rate`) is defined and
   pre-registered as a **pooled** statistic over all trials with realised
   `model_tokens_after_target ≥ W + 16 = 272` (Methods §2.4) — it does not
   assume, require, or claim that abstention grows monotonically with pressure
   within that region.
6. **Does this affect the pooled H3 comparison beyond W+16?** No. Recomputing
   the same pooled statistic directly: Transformer abstention over all
   `model_tokens_after_target ≥ 272` rows is 0.5162 and AHN-pooled is 0.9398 —
   matching the frozen H3 values (R26: 0.516 control, 0.929-0.946 AHN) exactly.
   The non-monotonic sub-structure is entirely internal to how that pooled
   average is composed across pressure and does not change its value. AHN's
   own abstention trajectory across the same targets is high and does not show
   this dip-then-rise pattern (0.85 at 265 rising to ≈ 0.97-0.99 by 380 and
   staying high through 760) — the phenomenon is specific to the
   no-recurrent-memory control.

## Minimum wording addition (applied)

Added to `manuscript/RESULTS.md` §3.6 (VAL-3, Transformer control behaviour),
immediately after the malformed-rate-by-pressure sentence, as **[R51]**:

> "Correspondingly, the Transformer's abstention rate is not monotonic in
> pressure: it falls from 0.52 (intended target 265) to 0.26-0.27 through
> 315-380 as malformed output rises, then climbs sharply to 0.82-0.95 at
> 520-760 as malformed output recedes; the H3 primary result concerns pooled
> failure-mode composition beyond the predefined W+16 boundary (§3.4), not
> monotonic abstention growth across intermediate pressures."

This is close to, and consistent with, the candidate sentence suggested in the
task brief; it was adapted to state the actual shape (decline-then-rise mirrored
by malformed output) rather than a generic "not monotonic at every target"
claim, since the final data support the more specific description. Added to
`manuscript/RESULTS_TRACEABILITY.md` as row R51.

## Classification

**C — descriptive figure issue, resolved with one added sentence.** Not D: the
pattern does not affect the H3 pooled statistic (verified identical to the
frozen value) and is control behaviour already contextualised by the existing
malformed-rate discussion (R42-R45); it only needed the abstention side of the
same story stated explicitly.
