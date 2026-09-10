# Pre-Compression Plan

Not executed. This document identifies where the page budget can be recovered
without touching Tier 1 claims (`manuscript/CLAIM_HIERARCHY.md`), the claims
register, or any number.

## Word budget (as of commit prior to compression)

| section | words (approx.) | notes |
|---|---:|---|
| Abstract | ~225 | in the 180–230 target; leave |
| Introduction | ~925 | in target (750–950); minor trim only |
| Related Work | ~1,000 | in target (850–1,100); leave or trim §2.4 |
| Methods (main) | ~1,950 | over the Revision-Pass-1 target of 1,300–1,700 |
| Results | ~2,150 | over the Revision-Pass-1 target of 1,500–1,800 — **largest single reduction target** |
| Discussion | ~1,730 | slightly over its 1,200–1,600 target |
| Conclusion | ~400 | in target (300–450); leave |
| **Total main text** | **~8,300–8,800** | measurement varies with markdown handling |
| Methods (Extended, supplementary) | ~3,300 | not in the page budget |

A typical ACL/NAACL body target is ~6,500–7,500 words excluding references, with
Limitations and appendices outside the count. **Reduction needed: ~1,200–2,000
words**, almost all from Results and Methods, with Discussion a secondary target.

## Tier 1 material that MUST survive compression (verbatim or near-verbatim)

- T1-1 information-type-dependent degradation: the five A_transition values, the
  omnibus p = 5×10⁻⁴, "at least one Holm-adjusted interval excludes zero".
- T1-2 near-window advantage: +0.249, 95% CI [0.233, 0.266], "positive in every
  seed".
- T1-3 deep-recurrent null: the approved sentence verbatim, the counts
  (0/0/1/3 of 3,542), the Wilson upper bounds.
- T1-4 abstention shift: the past-W+16 rates (0.929–0.946 vs 0.516; 0.052–0.071
  vs 0.480), effect ≈ 0.42, Holm p < 0.001, seed-stable, and the
  behavioural-only framing plus the two-alternatives caveat.
- The W ≠ K distinction and "every K < W" (T2-1) and the post-freeze flag on the
  transition-width comparison (T2-2).

## Tier 2 material that can move to an appendix or a table

| from | material | destination |
|---|---|---|
| Results §3.2 | answered-valid per-type `A_transition` values [R9], per-seed ordering detail [R12], exclude-temporal / exclude-compound-relational sensitivities [R10–R11] | Appendix A-H1 (already exists); keep one summary sentence in the body |
| Results §3.3 | the frozen pooled-width explanation [R21] (2 sentences → 1), the AIC ΔAIC values [R20] (keep the contrast, drop per-arm numbers), abstention-knee values [R19] | Table 3 / Appendix A-H2a; body keeps "K < W" and "later, broader" |
| Results §3.4 | calibration paragraph [R31–R32] (secondary; T2-6) — compress to 2 sentences | Appendix A-H3 |
| Results §3.6 | VAL-1/VAL-2/VAL-3/VAL-4 per-seed ranges, malformed subtype counts [R44], residual-failure by-target and by-seed breakdowns [R47] | Appendix A-VAL / A-H2b; body keeps one sentence per VAL finding |
| Methods §2.2 | the full fact-type example column, the temporal 2×2×2 counterbalancing sentence | already condensed vs Extended; move the temporal detail entirely to Extended, cite it |
| Methods §2.4 | the H1/H2/H3 sub-procedure detail (bootstrap mechanics, permutation mechanics) | Extended already has the long form; main can drop ~120 words |
| Methods §2.6 | the construct-check enumeration | one sentence + pointer to Extended |

## Repeated arguments across sections (candidates to state once)

1. **"strict accuracy is task performance, not representational loss"** — appears
   in Methods §2.3, Results §3.2, Discussion §4.1, Conclusion. Keep the full
   statement in Methods; make Results/Discussion/Conclusion one clause each.
2. **"the AHN-vs-control contrast confounds a recurrent state with the
   distillation recipe"** — Methods §2.4, Discussion §4.2 and §4.4, Conclusion,
   Related Work §2.3. Keep in Methods and Discussion §4.4; shorten the other three
   to a back-reference.
3. **"K is descriptive / not compression onset"** — Methods §2.3, Results §3.3
   [R25], Discussion §4.5. Keep in Methods and Discussion; Results keeps only
   "every K < W".
4. **"deep-recurrent null ≠ latent-information absence"** — Results §3.5,
   Discussion §4.3, Conclusion, Abstract. This one is load-bearing; keep it in
   all four but as a single clause outside the Discussion.
5. **"AHN does not simply shift the cliff right"** — Introduction, Results §3.3,
   Discussion §4.2, Conclusion. Keep in Discussion §4.2 (full) and Introduction
   (preview); Results and Conclusion one clause.

## Paragraphs likely removable or mergeable

- Results §3.1 [R3]–[R5]: the in-window control numbers partly duplicate Table 4
  and Methods; compress to one sentence, keep [R5] grid-calibration.
- Discussion §4.7 (Implications): five implications in one long sentence — can
  drop to three.
- Related Work §2.4 closest-work: four paper comparisons — can compress ATLAS +
  evidence2026 into one sentence and MemMamba + recall-scaling into one.
- Discussion §4.1 second paragraph (candidate factors list) — already one
  sentence; leave.

## Prose that a table/figure can replace

- Results §3.3 K values and abstention-knee values → already in **Table 3**;
  the body can cite the table instead of listing 8 numbers.
- Results §3.6 VAL-3 per-pressure malformed rates [R43] and subtypes [R44] →
  **Appendix A-VAL table**; body keeps "0% in-window, rising then falling".
- Results §3.4 outcome composition [R30] → **Figure 3** already shows it; body
  keeps the one-line summary.
- Methods §2.1 architecture list → a 4-row table (as in Extended) is denser than
  the current prose.

## Order of operations for the compression pass

1. Move Tier 2 detail from Results §3.2/§3.3/§3.4/§3.6 to the existing appendices
   (no new appendices needed). Target: Results → ~1,700.
2. Trim Methods §2.2/§2.4/§2.6 against the Extended version. Target: Methods →
   ~1,650.
3. De-duplicate the five repeated arguments. Target: −150 across Discussion +
   Conclusion + Related Work.
4. Re-run `WHOLE_PAPER_COHERENCE_AUDIT.md` and the traceability check after the
   cuts; every surviving number must still trace.

Projected total after the pass: ~6,600–7,000 words main text.
