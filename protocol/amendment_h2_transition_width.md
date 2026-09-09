# Amendment (DECISION DOCUMENT) — H2 transition-width metric

**Type:** [POST-FREEZE REPORTING AMENDMENT] — correction of a reporting metric that
returned an undefined value and a misleading label.
**Status:** DECISION PENDING — requires team sign-off. **Nothing implemented.**
**Raised by:** hostile final audit, 2026-09-09 (`final_audit/AUDIT_OUTPUTS/AUDIT_REPORT.md` Phase 7).
**Does not touch:** the locked artifact, the frozen design, the primary accuracy
endpoint, the experiment. This amends *how one descriptive shape statistic is
reported*, not what was run or measured.

---

## 0. One-paragraph summary

The frozen H2 "primary descriptive quantity" is the isotonic 90→10 strict-accuracy
transition **width**, with a 3-way verdict {concentrated / gradual / intermediate}.
In the locked data this width is **undefined (NaN) for all four architectures**,
because the pooled five-fact-type strict-accuracy curve never reaches the 0.9
reference level (it peaks at ≈ 0.88, dragged down by temporal's 38 % and multi-hop's
11.5 % in-window abstention). The frozen code assigns the fall-through label
**"intermediate"** to a non-finite confidence interval. This is a
**metric-definition bug in the reporting layer**, not experimental corruption. Every
other H2 quantity (K, abstention-K, shape test, A_transition gap, A_recurrent,
per-type K, seed robustness) is valid and unaffected. This document proposes four
defensible alternatives, recommends one, and asks the team to approve it before it
is implemented and re-run on the locked artifact.

---

## 1. What the frozen metric intended to measure

`protocol/final_experiment_design.md` §7 and `h2_threshold.transition_summary`
docstring:

> "per-architecture isotonic 90→10 transition **width** … **Concentrated** if CI
> upper < 128 tokens (0.5 W); **gradual** if CI lower > 256 tokens (W);
> **intermediate** otherwise."

Intent: for each architecture, fit a monotone (non-increasing) strict-accuracy
curve against realised `model_tokens_after_target`, find the token distance between
where the fit crosses 0.9 and where it crosses 0.1, bootstrap a CI on that
distance, and classify the collapse as concentrated (narrow band), gradual (wide
band), or genuinely in between. A narrow width is the operational signature of a
"threshold-like" collapse.

## 2. Why it became undefined

`src/ahnexp/h2_threshold.py` `_iso_transition_width`:

```python
def _iso_transition_width(g, lo_level=0.9, hi_level=0.1):
    cell = g.groupby(pressure_group_key).agg(x=(coord,'mean'), acc=('correct','mean'), n=('correct','size'))...
    fit = stats.isotonic_regression(cell['acc'], cell['n'], increasing=False)
    return stats.crossing_x(x, fit, hi_level) - stats.crossing_x(x, fit, lo_level)
```

- `acc` is **raw strict accuracy pooled over all five fact types** at each intended
  pressure level. At the in-window anchors (intended 150, 180) this pooled value is
  **≈ 0.879** for every arm (`final_h2_h2_curves.csv`): the mean of entity-attribute
  1.00, numerical 1.00, contradictory 0.99, multi-hop 0.86, **temporal 0.57** (its
  38 % abstention makes raw strict low even in-window).
- The isotonic fit is therefore bounded above by ≈ 0.88 and **never reaches 0.9**.
- `stats.crossing_x(x, fit, 0.9)` returns `NaN` ("Returns NaN if the fit never
  reaches `level` within the sampled range" — its docstring).
- `_iso_transition_width` returns `NaN − (finite number) = NaN` for the point
  estimate; `stats.hierarchical_bootstrap` of a statistic that is NaN on every
  resample returns `point = NaN`, `ci_low = NaN`, `ci_high = NaN`.

Verified: `final_h2_h2_width.csv` — `width_tokens`, `ci_low`, `ci_high` all empty
for all four arms; audit `repro_h2_width.csv` reproduces this exactly at
n_resamples = 2000 ("WIDTH CI FINITE? {all False}").

## 3. Exact code path responsible for the misleading label

`src/ahnexp/h2_threshold.py`, `transition_summary`, width loop (≈ L29–39):

```python
for arm, g in df.groupby("architecture"):
    boot = stats.hierarchical_bootstrap(g, _iso_transition_width, n_resamples=n_resamples)
    lo, hi = boot["ci_low"], boot["ci_high"]           # both NaN
    verdict = "intermediate"                            # <-- default
    if np.isfinite(hi) and hi < 0.5 * w:  verdict = "concentrated"   # skipped: isfinite(NaN) is False
    elif np.isfinite(lo) and lo > w:      verdict = "gradual"        # skipped
    width_rows.append({"architecture": arm, "width_tokens": boot["point"],  # NaN
                       "ci_low": lo, "ci_high": hi, "verdict": verdict})     # "intermediate"
```

The `verdict = "intermediate"` initializer is reached whenever the CI is
non-finite, so an **undefined** width is reported with the same label as a width
that is genuinely between 0.5 W and W. `final_h1_h1_a_transition.csv` and
`final_summary.json` (`h2_width_verdict`) then propagate "intermediate" as if it
were a result.

## 4. Why this is a reporting / metric-definition problem, not experimental corruption

| evidence | source |
|---|---|
| SHA-256 of the artifact verified; 92,160 rows, 0 duplicate/missing cells | audit Phase 1 [A] |
| all 92,160 rows re-score identically with the frozen scorer | audit Phase 2 [A/B] |
| every *other* H2 quantity (K, shape, gap, A_recurrent) reproduces to \|Δ\| ≤ 1e-14 | `phase14_frozen_vs_repro_diffs.csv` [A] |
| the raw per-arm strict-accuracy curves are clean, monotone-ish, and clearly show a sharp drop | `final_h2_h2_curves.csv` [A] |
| the defect is a single `np.isfinite` fall-through on a statistic that is NaN by construction for this fact-type mix | code inspection [B] |

The data are sound. The metric's 0.9 anchor is simply incompatible with a pooled
curve whose ceiling is set by an abstention-heavy fact type. Fixing the reporting
metric changes no measured value.

## 5. Which quantities remain valid without amendment

All of these are computed from the locked artifact, reproduce bit-identically, and
require **no** change:

- `A_transition(AHN pooled) − A_transition(transformer)` over [200, 270] =
  **+0.2494 [0.2331, 0.2660]** (`final_summary.json`).
- `K_strict` per arm (0.5 crossing) with hierarchical CI: transformer
  **208.3 [207.1, 209.5]**, deltanet 218.4 [215.9, 236.9], mamba2 219.6
  [217.2, 237.5], gated_deltanet 240.0 [220.4, 243.9] (`final_h2_h2_k_strict.csv`).
- `K_abstention` per arm: transformer **421.7**, AHN 247–251
  (`repro_h2_knees_by_arm.csv`).
- `shape_test` (break fixed at W = 256): all four "threshold-like", piecewise
  AIC < smooth AIC (`final_h2_h2_shape_break_at_W.csv`).
- `A_recurrent` (intended ≥ 315): all arms ≈ 0 (`final_h2_h2_a_recurrent.csv`).
- per-fact-type K (`repro_h2_knees_by_facttype.csv`).
- seed robustness of K (`phase13_k_by_seed.csv`).
- deep-recurrent negative-retention (`phase9_deep_recurrent.csv`).

The **0.5 crossing (K)** is unaffected because the pooled curve *does* pass through
0.5 for every arm — only the 0.9 anchor is unreachable.

## 6. Candidate scientifically defensible alternatives

Each computes a transition-band width from the locked artifact only, without
altering the experiment or the primary accuracy endpoint. All would be labelled
**[POST-FREEZE REPORTING AMENDMENT]** in the manuscript.

**Option A — per-fact-type width on the closed-set types, then summarise.**
Compute the 90→10 isotonic width per (architecture, fact type) for the three
closed-set types whose in-window ceiling ≈ 1.0 (entity-attribute, contradictory,
numerical), where the 0.9 anchor *is* reachable; report the per-arm mean (or
distribution) and a bootstrap CI. Multi-hop and temporal (ceiling < 0.9) are
reported as "width undefined at 0.9 anchor; see K and per-type curve".
*Locked-data preview* (`auditorC_h2_per_facttype_transition_width.csv`, isotonic
point estimates, no CI yet): transformer mean **32.7**, deltanet 67.5,
gated_deltanet 62.2, mamba2 68.9 tokens.

**Option B — lower the reference band to the reachable range (e.g. 0.7→0.1 or
0.8→0.2) on the pooled curve.** Keep the pooled 5-type curve; replace 0.9 with a
level the pooled ceiling clears. *Locked-data preview* (pooled, isotonic, no CI):
0.8→0.2 width — transformer **32.1**, deltanet 67.7, gated_deltanet 67.1,
mamba2 66.7 tokens (`auditorC_h2_alt_transition_width_pooled.csv`).

**Option C — answered-valid pooled curve, keep 0.9→0.1.** Compute the width on
`answered_valid` strict accuracy (abstained/malformed removed), where the pooled
in-window ceiling is ≈ 0.97–1.0 and 0.9 is reachable. Changes the *population*, not
the anchor.

**Option D — report no single width; characterise shape from K + shape-test +
per-type curves only, and drop the width verdict entirely.** State "the collapse
is threshold-like (shape-test, all arms) and occurs over ≲ 70 tokens on every
computable view; no single pooled width is defined because one fact type
abstention-saturates below the 0.9 reference."

## 7. Advantages / disadvantages

| option | advantages | disadvantages |
|---|---|---|
| **A** (per-type, closed-set) | anchor genuinely reachable; no population change; matches the H1 unit of analysis; exposes real per-type heterogeneity | multi-hop & temporal still have no width; needs a summarisation rule (mean vs distribution); 3 numbers per arm |
| **B** (lower pooled band) | minimal change; keeps the pooled single-number framing; still on the frozen population | the band is chosen post hoc; 0.8→0.2 is not a "90→10" width and must be relabelled; still partly shaped by temporal's low floor |
| **C** (answered-valid pooled) | anchor reachable; single number per arm; population is already a frozen H3 concept | changes the population from the frozen H2 endpoint (raw strict); answered-valid n collapses sharply past the window (853 at intended 265 pooled — `final_h3_h3_by_pressure_answered_valid.csv`), so the low end of the fit is thin and the 0.1 crossing is noisy |
| **D** (no width) | most honest; nothing post hoc; the qualitative claim ("threshold-like") is already supported by the shape-test and curves | loses the quantitative "how narrow" that reviewers may ask for; asymmetric with H1/H3 which do report numbers |

## 8. Recommended alternative

**Option A (per-fact-type 90→10 width on the closed-set types) as the primary
replacement, reported alongside Option D's qualitative statement.**

Concretely, for the manuscript:
1. Report **K_strict** per arm with CI as the transition *location* (already
   frozen, valid).
2. Report the **shape-test** result (all arms "threshold-like") as the confirmatory
   shape statistic (already frozen, valid).
3. Report a **per-fact-type 90→10 width** table for the three closed-set types,
   with a fresh hierarchical-bootstrap CI, as the transition *sharpness* — and
   state explicitly that multi-hop and temporal abstention-saturate below the 0.9
   anchor so a pooled width is not defined.
4. Retire the frozen pooled `width` / `verdict` and its "intermediate" label
   entirely; replace with the sentence: *"On every computable view the collapse is
   concentrated (closed-set per-type 90→10 widths 33–69 model tokens, ≪ 0.5 W) and
   threshold-like (shape-test), not gradual."*

## 9. Why the recommendation is NOT chosen to maximise the observed result

- Option A is the **most conservative** of the "still reports a number" options: it
  restricts to the fact types where the metric is *validly defined* and refuses to
  impute a width for the two types where it is not.
- It does **not** move to `answered_valid` (Option C), which would systematically
  *shrink* every width (removing abstainers steepens the apparent drop) and would
  produce the most dramatic "concentrated" numbers — i.e. the self-serving choice.
- It does **not** lower the band on the pooled curve (Option B) to whatever level
  makes the number come out; the 0.9→0.1 definition is kept, only the population is
  restricted to where 0.9 exists.
- The per-type widths (33–69 tokens) are **wider** than what Option C would give,
  so choosing A is choosing the less extreme "concentrated" evidence.
- The qualitative conclusion is anchored on the **frozen, untouched** shape-test,
  not on the new width.

## 10. Does it change the qualitative H2 conclusion?

**No.** Under the frozen shape-test (untouched, all four arms "threshold-like"),
the frozen K values (208–240, all below W), the frozen A_transition gap
(+0.249 [0.233, 0.266]), and the frozen A_recurrent (≈ 0), the H2 conclusion is:

> "The retrieval-accuracy collapse is threshold-like for every architecture; the
> AHN recurrent path shifts it ≈ 10–35 tokens later and preserves ≈ 0.25 more
> near-window accuracy than a no-recurrent-memory baseline; nothing is retained
> past ≈ W."

The amendment only changes the *reported sharpness statistic* from an undefined
pooled width to a set of defined per-type widths. The direction "concentrated, not
gradual" is unchanged; the frozen "intermediate" label was never a valid finding.

## 11. How it should be disclosed in the manuscript

A dedicated methods/appendix paragraph, e.g.:

> "The pre-registered transition-width statistic (isotonic 90→10 strict-accuracy
> drop, pooled across fact types) is undefined for this dataset: the pooled
> strict-accuracy curve peaks at ≈ 0.88 because the temporal fact type
> abstention-saturates in-window (38 % abstention), so the 0.9 reference is never
> reached and the frozen implementation returns a non-finite interval that it
> labels 'intermediate'. This is a metric-definition artefact, not a property of
> the data (the raw per-architecture curves and the confirmatory shape test are
> unaffected). We therefore report, as a pre-specified post-freeze reporting
> amendment [cite this document], the 90→10 width per architecture for the three
> closed-set fact types whose in-window ceiling permits the statistic to be
> defined (widths 33–69 model tokens), together with the frozen shape test, and we
> do not report a pooled width or the 'intermediate' label."

The frozen `final_h2_h2_width.csv` stays in the locked bundle unchanged as a
record; the manuscript cites the amendment table instead.

## 12. What requires team approval before implementation

1. **Approve Option A** (or select B / C / D) as the reporting replacement.
2. **Approve the summarisation rule** for Option A: per-arm mean of the 3 closed-set
   widths vs report all 3 vs report min/median/max.
3. **Approve retiring the "intermediate" verdict** from all manuscript-facing text
   and figures (the locked CSV is untouched).
4. **Approve the disclosure paragraph** wording (§11).
5. **Approve the implementation plan:** add a `transition_width_closed_set()` helper
   (or a `population` / `levels` argument to `_iso_transition_width`) to
   `src/ahnexp/h2_threshold.py`, add unit tests, re-run analysis on the **locked**
   parquet only, write the new table into `final_audit/AUDIT_OUTPUTS/` (not into
   `FINAL_LOCKED/`). `analysis_version` bumps to `1.1` for the amended table;
   `1.0` outputs are retained.
6. **Decide** whether the code change lands on `saadat-pipeline-validation` as a
   normal commit (recommended) or a dedicated `analysis-amendments` branch.

**No code is written until items 1–6 are signed off.**
