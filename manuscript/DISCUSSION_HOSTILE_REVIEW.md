# Discussion — Hostile Review

Reviewer stance: a skeptical ML/NLP reviewer who assumes the authors want to
oversell a recurrent-memory architecture and will read every hedge as a loophole.
Verdicts: **PASS** (no change needed) · **WARN** (wording risk, fixed if
resolvable without changing science) · **BLOCKER** (must fix before the section
can stand).

Evaluated against `manuscript/DISCUSSION.md` after the fixes below were applied.

| # | question | verdict | basis |
|---|---|---|---|
| 1 | Does the Discussion overclaim hidden-state forgetting? | **PASS** | Intro defines "degradation" as end-to-end task performance "not … a direct measurement of hidden-state contents." §4.1: "We do not interpret this as differential decay of stored representations, because the production metric cannot separate a lost value from a model that declines to answer." §4.3: the null "does not establish that the recurrent state contains no target information." No sentence asserts representational loss. |
| 2 | Does it imply K = W? | **PASS** | Intro: "the empirical performance knee sits below the architectural window for every arm." §4.5: "For every architecture the empirical performance knee K … lies below the architectural window W = 256." K and W are never equated. |
| 3 | Does it imply K is compression onset? | **PASS** | §4.5: "K is an observed per-run quantity, not an architectural constant, and it does not mark the onset of compression," immediately reinforced by the residual fully-exact failure evidence. |
| 4 | Does it misrepresent AHN widths as sharper? | **PASS** | §4.2: "the Transformer transition is **earlier and narrower** while the AHN transitions are **later and broader**"; "AHN … spreads its decline over a wider pressure interval — a qualitatively different transition, not a translated copy." The naive "AHN moves the cliff to the right" reading is raised and rejected. |
| 5 | Does it hide that the widths are post-freeze? | **PASS** | §4.2 dedicated paragraph: "The per-eligible-type analysis was introduced *after* the freeze, is reported as analysis version 1.1 … It **characterizes** the transition shape; it does not rescue a failed primary analysis, and it should not be cited as though it were pre-registered." |
| 6 | Does it overstate the AIC evidence? | **PASS** (was WARN) | §4.2 now says the Transformer's "concentrated" characterization "rests mainly on that narrow width, since its frozen change-point margin is thin (ΔAIC ≈ −0.7 …)." The AIC and width lines are called "complementary but independent." |
| 7 | Does it imply H3 is mechanistic? | **PASS** | §4.4: "The experiment cannot say why." Two explanations (recurrent-state signal vs distilled abstention policy) given equal weight; "We therefore avoid any claim that the model 'knows' it has forgotten or that the recurrent state 'encodes uncertainty.'" Term used is "behavioural uncertainty signalling." |
| 8 | Does it overstate factual calibration? | **PASS** | §4.4: "Factual calibration is a secondary observation"; miscalibration is scoped to "fewer than 5% of past-window trials … a narrow selected subpopulation rather than a headline result." |
| 9 | Does it bury the deep-recurrent negative result? | **PASS** (was WARN) | Promoted to its own subsection **4.3 "No measurable deep-recurrent retrieval"**, flagged in the intro, and called "one of the study's more consequential findings … not a footnote." The only mention in Limitations is the correct caveat that a production null ≠ latent absence. |
| 10 | Does it adequately acknowledge benchmark limitations? | **PASS** | §4.6 "Benchmark" (synthetic, isolates memory pressure, no naturalistic claim) and "Construct scope" (compound-relational, temporal). |
| 11 | Does it generalize beyond one model family? | **PASS** | §4.6 "Model scale and family": one base model + three checkpoints, "should not be generalised to other scales, base-model families, or recurrent-memory designs." §4.7 opens "Read cautiously." |
| 12 | Does it explain why the result matters? | **PASS** | §4.3 (boundary on the system), §4.5 (window size ≠ predictor), §4.7 (five evaluation implications). The "so what" is explicit. |
| 13 | Does it merely repeat Results? | **PASS** (was WARN) | §4.4 numeric restatement trimmed to "the large majority" / "a small fraction" / "roughly half" with one anchoring figure (≈ 0.42). Elsewhere numbers appear only to anchor a specific interpretation. |
| 14 | Are alternative explanations treated fairly? | **PASS** | §4.1 lists six candidate factors for H1 with none privileged; §4.4 gives (A) and (B) equal weight and states they "cannot be separated here"; §4.5 lists five candidate contributors to residual failure as undistinguished. |
| 15 | Would a skeptical reviewer find an unsupported causal claim? | **PASS** (was WARN) | "confers a substantial near-window advantage" replaced with the register's own verb: "The AHN arms preserve substantially more near-window accuracy than the no-recurrent-memory control" (§4.2, cf. H2-1 allowed wording). Remaining causal-sounding language ("AHN reshapes the near-window transition") is about observed task-performance dynamics under a controlled architecture contrast, which the register licenses (H2-1, H2-2); mechanism is explicitly disclaimed for H3 and for the residual failures. |

## Verdict counts

- After fixes: **PASS 15 · WARN 0 · BLOCKER 0**
- Before fixes: PASS 11 · WARN 4 (#6, #9, #13, #15) · BLOCKER 0

## Fixes applied

1. **#9 (deep-recurrent prominence).** Split the old §4.2 into **4.2 "AHN reshapes
   the near-window transition"** and a new standalone **4.3 "No measurable
   deep-recurrent retrieval"**; added an intro pointer and the sentence "one of
   the study's more consequential findings … not a footnote." Subsections 4.3–4.6
   renumbered to 4.4–4.7.
2. **#6 (AIC framing).** Reworded §4.2 so the Transformer's "concentrated"
   characterization is explicitly carried by its narrow width, with the thin
   ΔAIC ≈ −0.7 margin stated in the same sentence; AIC and width described as
   independent lines.
3. **#13 (Results repetition).** §4.4 behavioural numbers replaced with qualitative
   magnitudes plus the single ≈ 0.42 effect-size anchor; the exact rates remain
   in Results [R26], [R27].
4. **#15 (causal verb).** "The AHN recurrent path confers a substantial
   near-window advantage" → "The AHN arms preserve substantially more near-window
   accuracy than the no-recurrent-memory control" (the register's own verb).

No BLOCKER was found; no science changed; no number changed; Methods, Results,
the claims register, and the exhibits were not touched.

## Wording weakened during hostile review

- "confers a substantial near-window advantage" → "preserve substantially more
  near-window accuracy than the no-recurrent-memory control" (§4.2).
- Exact behavioural percentages in §4.4 → qualitative magnitudes + one anchor.
- No claim's *status* was weakened; every register status is reported at the
  strength the register records.

---

## Task 4 — Central claim test

**Strongest defensible one-paragraph summary of the paper:**

> Under increasing memory pressure, end-to-end task performance degrades
> non-uniformly across information types, and the way a failure manifests —
> wrong answer, abstention, or malformed output — is itself type-dependent. Adding
> an AHN recurrent memory to a matched Transformer is associated with a
> substantial near-window task-performance advantage (about 0.25 more strict
> accuracy across the transition region) and with a later, broader accuracy
> transition rather than a simple rightward shift of the same cliff; for every
> architecture the empirical performance knee lies below the architectural
> exact-attention window, and retrieval already fails on about a third of trials
> whose target is arithmetically inside that window, so the transition is not a
> clean inside/outside boundary. At deep recurrent pressure, no measurable
> target-specific factual retrieval was observed under the production evaluation
> for any architecture — a boundary on what the current system delivers
> end-to-end, though not evidence that the recurrent state holds no target
> information. Where retrieval becomes unreliable, the AHN system's principal
> observed distinction from the control shifts from retrieving more to failing
> differently: it predominantly abstains rather than emitting unsupported output.
> This is behavioural uncertainty signalling, and the present design cannot
> determine whether it reflects information in the recurrent state or a learned
> abstention policy from the AHN training and distillation recipe.

**Check against `protocol/final_claims_register.md`:**

| paragraph clause | register basis | consistent? |
|---|---|---|
| "degrades non-uniformly across information types … way a failure manifests … is type-dependent" | H1-1 SUPPORTED; H1-2 PARTIALLY SUPPORTED (required caveat: raw strict blends retrieval with abstention) | **Yes** |
| "associated with a substantial near-window task-performance advantage (about 0.25 …)" | H2-1 SUPPORTED; allowed wording "≈ 0.25 more … (95% CI [0.23, 0.27])" | **Yes** |
| "later, broader accuracy transition rather than a simple rightward shift" | H2-2 SUPPORTED (concentrated); H2-4; Revision Pass 1 framing; no "sharper" claim | **Yes** |
| "empirical performance knee lies below the architectural exact-attention window" | H2-4 SUPPORTED; "K 208–240 vs W = 256; distinct" | **Yes** |
| "retrieval already fails on about a third of trials whose target is … inside that window … not a clean inside/outside boundary" | VAL-4 LIMITATION; allowed wording "≈ 32% … the pressure axis is … not a clean exact/recurrent switch" | **Yes** |
| "no measurable target-specific factual retrieval … under the production evaluation … not evidence that the recurrent state holds no target information" | H2-5 NEGATIVE RESULT; approved wording; prohibited "stores nothing" avoided | **Yes** |
| "predominantly abstains rather than emitting unsupported output" | H3-1, H3-2 SUPPORTED; allowed wording | **Yes** |
| "behavioural uncertainty signalling … cannot determine whether it reflects information in the recurrent state or a learned abstention policy" | H3-4 PROHIBITED CLAIM handled — both alternatives stated, no mechanistic claim | **Yes** |
| (calibration) — deliberately omitted from the central paragraph | H3-3 PARTIALLY SUPPORTED, secondary; register warns against headlining it | **Yes — correctly not headlined** |

No clause of the central paragraph exceeds its register-allowed strength.
