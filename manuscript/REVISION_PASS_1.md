# Revision Pass 1 — manuscript core (Methods + Results)

Scope: `manuscript/METHODS.md`, `manuscript/RESULTS.md`,
`manuscript/RESULTS_TRACEABILITY.md`, plus a new
`manuscript/METHODS_EXTENDED.md`. Prose-only revision in response to an
independent scientific review. **No data, endpoint, statistic, frozen v1.0
output, v1.1 output, or claims-register entry was changed.** No models were run.
Introduction, Related Work, Discussion, Abstract, and Conclusion remain unwritten.

## 1. Methods word count

| | words (`wc -w`) |
|---|---|
| Methods before | 3,081 |
| Methods after (`METHODS.md`, main paper) | **1,877** |
| `METHODS_EXTENDED.md` (full reproducibility version) | 3,137 |

The pre-revision Methods was copied verbatim to `METHODS_EXTENDED.md` (with a
header explaining the relationship) before any cutting, so no reproducibility
detail was lost. Target was 1,300–1,700; the main Methods landed slightly above at
~1,880 because the required-content list (architectures, benchmark,
memory-pressure design, W, pressure coordinate, scoring, grid, H1/H2/H3 analyses,
post-freeze H2 amendment) is dense and none of it was moved out.

## 2. Results word count

| | words (`wc -w`) |
|---|---|
| Results before | 2,347 |
| Results after | **2,123** |

Target was 1,500–1,800. Results landed at ~2,120. The reduction came from deleting
the four standalone "Interpretation" subsections and tightening connective prose;
it could not reach 1,800 without dropping conclusion-critical numbers — all 49
bracketed numerical statements are individually traced and register-relevant, and
each needs at least a clause. The interpretation that remains is only the minimum
needed to stop a statistic being misread (e.g. strict accuracy ≠ representational
loss; K ≠ W; the small answered-valid subpopulation for calibration).

## 3. Sections moved to `METHODS_EXTENDED.md`

Main Methods was reorganised from 14 subsections to 6
(2.1 Experimental setup and architectures · 2.2 Evaluation tasks and memory
pressure · 2.3 Scoring and experimental grid · 2.4 Statistical analyses ·
2.5 Post-freeze H2 reporting amendment · 2.6 Reproducibility and validation).
Detail retained only in the extended version:

- the full architecture table with per-module parameter counts and shared runtime
  flags (`torch_dtype`, `attn_implementation`, `ahn_position`, …);
- item-generation specifics (4,000-distractor pool, collision control, density
  strata, three target positions) and the temporal 2×2×2 nuisance construction;
- the exact scorer cleaning branches and the malformed sub-conditions;
- `intended` vs `realised` pressure-coordinate calibration mechanics;
- exact control-validity thresholds (PASS ≥ 0.85; WARNING band; FAIL < 0.70) and
  the per-check robustness-analysis catalogue;
- full package versions and the `d29c6d8` provenance-gap discussion with its
  hash-equivalence mitigations;
- implementation-level bootstrap prose and the amendment's numbered procedure in
  long form.

The **post-freeze H2 amendment stays in the main paper** as its own subsection
(§2.5), not in the supplement.

## 4. H2 framing changes (independent review Task 4 — mandatory)

- **Removed** the sentence "The collapse is threshold-like on every computable
  view."
- New umbrella statement: *"Performance degradation was concentrated rather than
  gradual, although transition sharpness differed by architecture."*
- The shape evidence is now presented as two explicitly distinct results, not one
  binary test repeated:
  - **A — Frozen change-point evidence** ([R20]): AIC favours a slope change at
    W for all four arms, but ΔAIC ≈ −0.7 for the Transformer (thin) vs −2.6 to
    −8.3 for the AHN arms.
  - **B — Post-freeze per-type width characterization** ([R21]–[R23]): frozen
    pooled width undefined and preserved; per-eligible-type median widths 32.4
    tokens (Transformer) vs 61.8–73.8 (AHN); individual eligible widths 29–77;
    all < 0.5 W.
- New synthesis paragraph states plainly: the **Transformer transition is narrower
  and earlier**; the AHN arms **preserve useful strict accuracy farther through
  the near-window region and degrade over a broader interval**; **AHN does not
  simply shift the Transformer cliff to the right.** Framed as observed
  task-performance dynamics, explicitly *not* a mechanistic property of recurrent
  memory.
- H2 status line reworded from "SUPPORTED … for the threshold-like shape" to
  "SUPPORTED … for a concentrated, non-gradual collapse".

## 5. W / K / compression language (Task 5)

- Retained: W = architectural sliding-window reference; K = empirical
  strict-accuracy knee; W ≠ K; every K < W.
- Not used anywhere: "compression begins at K", "K is the compression threshold",
  "collapse occurs at W / when the target leaves the window".
- [R25] now reads: *"The knee is not the window, and the transition is not a
  clean exact-to-compressed switch: every K (208–240) lies below W (256), and
  about 32% of trials whose target span is arithmetically inside the lossless
  window for the whole trial still fail … Pressure-related deterioration begins
  before the binary exact-to-compressed boundary alone can explain it; no
  mechanism is claimed here."*
- The residual-fully-exact finding ([R46]–[R48], VAL-4) is cross-referenced from
  both §3.3 and §3.6 to block a "collapse = eviction" reading.

## 6. Deep-recurrent / "no retention" wording changes (Task 6)

- §3.3 subsection retitled **"No retention past the window" → "Near-zero retrieval
  accuracy beyond the window"**.
- Removed "neither the recurrent architectures nor the baseline retrieve the
  target". The near-zero regime is now stated only in production-evaluation terms
  ("strict accuracy is indistinguishable from zero for all four architectures").
- §3.5 keeps the approved sentence verbatim: *"No measurable target-specific
  factual retention was observed at deep recurrent pressure under the production
  evaluation."*
- Not used: "recurrent memory stores nothing", "the information is gone", "no
  information remains in the hidden state".

## 7. H3 narrative changes (Tasks 7, 8)

- §3.4 now opens by stating that past the window the **principal difference
  between AHN and the Transformer control is failure mode, not sustained factual
  retrieval** (cross-referencing the §3.5 negative result).
- Behavioural signalling leads: appropriate-abstention 0.929–0.946 (AHN) vs 0.516
  (Transformer); unsignalled-failure 0.052–0.071 vs 0.480; six contrasts
  |Δ| 0.41–0.43, p < 0.001, seed-stable.
- Calibration is explicitly labelled **secondary**; the "overconfident when wrong"
  result is kept but bounded to "fewer than 5% of past-window trials" and not
  headlined.
- Mechanism: the closing paragraph states the architecture contrast confounds a
  recurrent state with the AHN distillation recipe and that a learned abstention
  policy cannot be ruled out — the distillation alternative is preserved for
  Discussion, not resolved here. No mentalistic wording ("knows", "detects",
  "aware", "recognises its forgetting").

## 8. Transformer wording changes (Task 9)

- **Removed**: "This is expected no-recurrent-memory degeneration once the target
  is evicted".
- **Replaced with** the evidence-bounded form: *"The concentration of malformed
  outputs at higher pressure levels, together with their near-absence at the
  control anchors, supports treating this as control behaviour rather than
  pipeline corruption; the pre-registered gate classifies it as such."*
- Per-architecture malformed rates still lead; the pooled 12.6% still appears only
  beside the split.

## 9. p-value formatting changes (Task 10)

No test or estimator changed. Search for `p = 0`, `p ≈ 0`, `p≈0`:

- **H1 omnibus** ([R7]): unchanged value **p = (0+1)/(2000+1) = 5×10⁻⁴** — this is
  exactly the frozen `h1_omnibus_p = 0.0004997501…` (add-one–corrected
  permutation p with 0/2000 exceedances). Prose now notes the add-one correction.
- **H1 pairwise contrasts** ([R8]): the nine contrasts the frozen CSV records as
  `p_approx = p_holm = 0.0` (0/2000 hierarchical-bootstrap resamples) are now
  written **p < 0.001**; the one real value (compound-relational vs temporal,
  p_holm = 0.037) is unchanged.
- **H3 behavioural contrasts** ([R28]): all six `0.0` values now written
  **p < 0.001**.
- The Results preamble states the 2,000-resample bootstrap resolution floor once.
- Traceability rows R7, R8, R20, R28 updated to record the representation change
  (values unchanged); a "p-value representation" note added to
  `RESULTS_TRACEABILITY.md`.

## 10. Construct-validity material moved / condensed (Task 12)

§3.6 kept in the main Results but tightened to the four interpretation-critical
findings: temporal response bias is counterbalanced (VAL-1); compound-relational
carries a control WARNING / lower ceiling and is retained in H1 (VAL-2);
Transformer malformed output is architecture-specific control behaviour, not a
pooled pipeline artefact (VAL-3); residual fully-exact failures complicate a
simple boundary explanation (VAL-4). Detailed malformed-subtype counts, per-seed
ranges, exact gate mechanics, and per-item breakdowns remain in the appendix
exhibits (A-VAL, A-H2b) and `METHODS_EXTENDED.md`; none were deleted from the
project.

## 11. Numerical claims old / new

| | count |
|---|---|
| numerical statements before | 49 |
| numerical statements after | **49** |
| deleted | 0 |
| values changed | 0 |
| wording-only changes at fixed value | R7, R8, R20, R28 (p-value representation); R24/R25 (section retitle + bounded phrasing) |

No numerical statement became untraceable. Renumbering was not needed — R1…R49
are unchanged identifiers.

## 12. Traceability status

`manuscript/RESULTS_TRACEABILITY.md`: 49/49 statements traced to the locked
parquet (SHA-256 `a72fd43e…`), frozen v1.0, or approved v1.1 outputs. Rows R7,
R8, R20, R28 were edited to reflect the p-value representation and the R20 wording
change; the "Untraceable numerical prose" section still reads **None**; a
"p-value representation (Revision Pass 1)" note and a "Revision Pass 1 — numerical
claims" note were appended. Three rows (R9, R19, R30) continue to note values
recomputed deterministically from the locked parquet with frozen code.

## 13. Claim-audit status

Re-run against `protocol/final_claims_register.md` (see
`manuscript/MANUSCRIPT_STATUS.md` → CLAIM AUDIT). All 15 register IDs (H1-1, H1-2,
H2-1…H2-5, H3-1…H3-4, VAL-1…VAL-4) consistent with the manuscript; the H3-4
prohibited mechanism claim is explicitly not made. Prohibited-phrase scan (≈ 40
patterns, including the review's explicit list): **0 unqualified uses**; all
matches are required disavowals or scorer-definition terms. Violations found and
fixed in this pass: 2 (the H2 "threshold-like on every computable view" sentence;
the VAL-3 "expected … degeneration once the target is evicted" causal clause).
Violations remaining: **0**.

## 14. Items from the independent review that were NOT adopted, and why

1. **"Rename §3.5 'Deep-recurrent retention'."** The review's Task 6 named the
   §3.3 subsection ("No retention past the window"), which was renamed. The §3.5
   heading was changed to "Deep-recurrent regime" (dropping "retention") but the
   section was **kept** — it is the pre-registered NEGATIVE RESULT (H2-5) and the
   claims register requires it to be reported with counts, denominators, and
   Wilson bounds, which it does. Not a rejection of the review, a scoping note.
2. **Results target of 1,500–1,800 words.** Not met (landed ~2,120). Cutting
   further would require removing traced numbers or register-mandated caveats,
   which the review itself forbids ("without omitting conclusion-critical
   results", "do not strengthen claims to make the story cleaner", "do not delete
   inconvenient findings"). The standalone Interpretation subsections — the
   review's specific target — were removed. Flagged here for the next pass to
   decide whether any §3.6 detail should move wholesale to an appendix.
3. **Methods target of 1,300–1,700 words.** Landed ~1,880. The remaining excess is
   the required-content list, which was kept intact in the main paper per the
   review's own instruction ("Do not sacrifice information necessary to
   understand …"). The extended version carries everything else.
4. **"A concise Results sentence may state … 'the principal observed difference
   between AHN and the Transformer control is therefore failure mode rather than
   sustained factual retrieval.'"** Adopted in substance, with "therefore"
   dropped and the claim tied to the §3.5 evidence, so it reads as an observation
   rather than an inference.

Nothing else from the review was declined.

---

### Final integrity check

- data changed: **no**
- statistical endpoint changed: **no**
- hypothesis status changed: **no**
- frozen v1.0 changed: **no**
- v1.1 changed: **no**
- claims register changed: **no**
- locked raw SHA-256: **`a72fd43e…` unchanged**
