# Manuscript Status

Drafting stage: **Methods and Results only.** Introduction, Related Work,
Discussion, Abstract, and Conclusion are not yet written (deliberately). This file
is current as of **Revision Pass 1** (see `manuscript/REVISION_PASS_1.md`).

| file | status | words (`wc -w`) |
|---|---|---|
| `METHODS.md` | main-paper Methods, §2.1–2.6 | ~1,880 |
| `METHODS_EXTENDED.md` | full reproducibility Methods, §2.1–2.14 (supplementary) | ~3,140 |
| `RESULTS.md` | draft, §3.1–3.6, 49 numbered numerical statements | ~2,140 |
| `RESULTS_TRACEABILITY.md` | complete — 49/49 statements traced | — |
| `REVISION_PASS_1.md` | revision memo | — |
| `MANUSCRIPT_STATUS.md` | this file | — |

Analysis phase is closed: no models were run, no new experimental data created,
no endpoint or statistic changed, and the locked raw artifact
(SHA-256 `a72fd43e87457a70c2833314e1443a794fa4189362ac8206c56275ef427fb62e`),
frozen v1.0 outputs, and locked v1.1 outputs were not modified. Methods and
Results draw only on the three approved sources (locked parquet, frozen v1.0,
approved v1.1 amendment). Revision Pass 1 was prose-only: condensation, the H2
framing fix, p-value formatting, and one section retitle — no number changed.

Exhibits: 9 main + 6 appendix, `outputs/publication_exhibits/`; all 15 PASS the
hostile exhibit audit and `scripts/audit_publication_exhibits.py` returns ALL
CHECKS PASS. Exhibits were not rebuilt in Revision Pass 1.

---

## CLAIM AUDIT (re-run at Revision Pass 1)

Every substantive claim in `METHODS.md`, `METHODS_EXTENDED.md`, and `RESULTS.md`
was checked against `protocol/final_claims_register.md` (its *Allowed wording* and
*Prohibited wording* fields are authoritative). Section numbers below are
main-paper Methods unless noted `EXT`.

### Claims checked (by register ID)

| register ID | manuscript treatment | consistent? |
|---|---|---|
| **H1-1** (non-uniform degradation) | Results §3.2 [R6–R8]; "degrade non-uniformly in task accuracy"; omnibus p reported add-one–corrected; answered-valid sensitivity alongside ([R9]); SUPPORTED | **Yes** |
| **H1-2** (fact-type ordering) | Results §3.2 ordering para [R6, R9, R12]; "compound-relational fastest, entity-attribute most robust; middle ranks closer and partly metric-dependent"; PARTIALLY SUPPORTED, not overstated | **Yes** |
| **H2-1** (near-window advantage) | Results §3.3 [R14, R15]; "+0.249 [0.233, 0.266]"; baseline = no-recurrent-memory (Methods §2.1); part-of-gap-is-degeneration caveat via §3.6 VAL-3 | **Yes** |
| **H2-2** (concentrated/threshold-like shape) | Results §3.3 [R20–R23]; **reframed in Revision Pass 1** — "concentrated rather than gradual, although transition sharpness differed by architecture"; frozen change-point evidence (A) and post-freeze per-type widths (B) reported separately; the phrase "threshold-like on every computable view" removed; SUPPORTED | **Yes** |
| **H2-3** (transition width) | Results §3.3 [R21] (frozen undefined, preserved, not interpreted) + [R22, R23] (post-freeze amendment, explicitly labelled); "intermediate" / frozen verdict column never used | **Yes** |
| **H2-4** (W ≠ K) | Methods §2.3; Results §3.3 [R16–R19, R25]; "every K < W"; "K is a descriptive per-run quantity and is not W"; "compression begins at K" / "collapse occurs at W" never used; AHN K given as a range with the seed-spread caveat [R18] | **Yes** |
| **H2-5** (deep-recurrent retention) | Results §3.5 [R33–R36]; approved sentence verbatim ("No measurable target-specific factual retention was observed at deep recurrent pressure under the production evaluation"); counts, denominators, Wilson bounds reported; "stores nothing" / "information is gone" never used | **Yes** |
| **H3-1** (appropriate abstention) | Results §3.4 [R26, R28, R29]; "0.929–0.946 vs 0.516", p < 0.001, seed-stable; "AHN knows it has forgotten" never used | **Yes** |
| **H3-2** (unsignalled failure) | Results §3.4 [R27, R28, R30]; composition stated (baseline rate is mostly malformed output) | **Yes** |
| **H3-3** (factual calibration) | Results §3.4 [R31, R32]; secondary; "poor calibration" scoped to "fewer than 5% of past-window trials"; deep-pressure ECE/CWR not headlined; "AHN is well-calibrated" never used | **Yes** |
| **H3-4** (mechanism) — **PROHIBITED CLAIM** | Methods §2.4 and Results §3.4 closing paragraph state the contrast confounds a recurrent state with the distillation recipe and "cannot be determined from this design"; no mentalistic/mechanistic wording; H3→H3 "failure mode rather than sustained factual retrieval" is behavioural, not mechanistic | **Yes — prohibited claim not made** |
| **VAL-1** (temporal construct) | Results §3.6 [R37, R38]; "balanced order-retrieval task"; "documented directional response preference … nets to chance"; "positional shortcut" / "benchmark is invalid" never used | **Yes** |
| **VAL-2** (compound-relational construct) | Methods §2.2 and Results §3.6 [R39–R41]; "not a genuine multi-hop reasoning task" / "not a multi-hop reasoning benchmark"; "co-located two-clause target"; "task-difficulty ceiling"; "multi-hop reasoning" / "chained inference" only inside disavowals | **Yes** |
| **VAL-3** (transformer control behaviour) | Results §3.6 [R42–R45]; per-architecture split always shown; pooled 12.6% only alongside the split; **causal wording removed in Revision Pass 1** — now "the concentration of malformed outputs at higher pressure … supports treating this as control behaviour rather than pipeline corruption"; "expected … degeneration once the target is evicted" deleted | **Yes** |
| **VAL-4** (residual in-window failures) | Results §3.6 [R46–R48] and §3.3 [R25]; "pressure axis is a proxy"; "not attributable solely to the exact-to-compressed transition"; "No mechanism is claimed" | **Yes** |

### Violations found

**Revision Pass 1 pass:** 1 mandated framing fix (independent review Task 4) and
1 mandated causal-wording fix (Task 9), both applied.

1. **Results §3.3** stated "The collapse is threshold-like on every computable
   view." The independent review judged this to over-flatten two non-identical
   tests into one binary property. **Removed.** Replaced with "Performance
   degradation was concentrated rather than gradual, although transition sharpness
   differed by architecture," followed by an explicit A/B split (frozen
   change-point evidence; post-freeze per-type widths) and a statement that the
   Transformer transition is narrower and earlier than the AHN transitions.
2. **Results §3.6 (VAL-3)** stated "This is expected no-recurrent-memory
   degeneration once the target is evicted." The residual-exact analysis (VAL-4)
   blocks a clean causal attribution. **Reworded** to the evidence-bounded form
   above.

Carried from the pre-revision claim audit (both already applied, still clean):
"well calibrated" wording (now removed entirely — R5 no longer characterises the
grid as calibrated, only "matches each intended target to within a few tokens");
"representational information loss" (the disavowal was reworded to "not how much
of the target value remains recoverable from the model's state").

No prohibited phrase is used unqualified anywhere in the current draft.

### p-value representation

The independent review (Task 10) required that no p-value be published as `0` or
`≈ 0`. Applied, no test changed:

- **H1 omnibus** ([R7]): keeps the frozen permutation value
  **p = (0+1)/(2000+1) = 5×10⁻⁴** (0 of 2,000 permutations; this is exactly how
  `full_run` defines `h1_omnibus_p` = `0.0004997501…`).
- **H1 pairwise contrasts** ([R8]): one real value (compound-relational vs
  temporal, p_holm = 0.037); the other nine have `p_approx = p_holm = 0.0`
  (0 of 2,000 hierarchical-bootstrap resamples) and are now written **p < 0.001**.
- **H3 behavioural contrasts** ([R28]): all six have `p_approx = p_holm = 0.0`;
  now written **p < 0.001**.

The bootstrap resolution floor is stated once in the Results preamble.

### Prohibited phrases searched (case-insensitive, all three Methods/Results files)

`proves` · `prove that` · `knows it` · `knew it` · `aware that` · `detects its` ·
`recognis*` · `compression threshold` · `compression begins` · `threshold T` ·
`threshold-like on every` · `at the window` · `multi-hop reasoning` ·
`multihop reasoning` · `chained inference` · `chain of` · `remembers indefinitely` ·
`stores nothing` · `store nothing` · `information is gone` ·
`no information remains` · `no retention` · `forgotten at different` ·
`representational information loss` · `intermediate width` · `solves long-context` ·
`positional shortcut` · `benchmark is invalid` · `because compression` ·
`compression causes` · `caused by compression` · `the model knows` ·
`the recurrent state knows` · `well-calibrated` · `well calibrated` ·
`expected .* degeneration once` · `once the target is evicted` · `p ≈ 0` ·
`p = 0` · `p≈0` · `clearly shows` · `demonstrates that` · `confirms that`

**Remaining matches (all verified benign — disavowals or scorer definitions):**

| match | location | why it is not a violation |
|---|---|---|
| "recognised value" / "recognised 'I don't know' form" / "unrecognised value" | Methods §2.3, EXT §2.7, Results §3.6 | scorer-definition terms; not a claim about the model |
| "we do not describe the collapse as occurring 'at' a compression threshold and do not describe compression as 'beginning at K'" | Methods §2.3, EXT §2.6 | explicit disavowal, required by H2-4 |
| "Compound-relational is not a genuine multi-hop reasoning task" / "not a multi-hop reasoning benchmark" | Methods §2.2, EXT §2.4, Results §3.6 | explicit disavowal, required by VAL-2 |
| "multi-hop reasoning" inside those disavowals | as above | negated context |
| "`multi-hop`" as a data key | Methods preamble, §2.2, EXT | explicitly labelled as the retained internal key |

### Unresolved issues

- **[D] Runtime-commit provenance gap** (`d29c6d8…` absent from released history) —
  disclosed as a limitation in Methods §2.6 / EXT §2.14 with the hash-equivalence
  mitigation. Team decision pending; affects no result.
- **[D] Temporal-only answered-valid sensitivity** (switch only temporal, leave
  other types on raw strict) was optional in the results specification and was not
  computed; the reported answered-valid sensitivity switches all types.
  Producible from the locked parquet with frozen code if a reviewer asks.
- **[future work] Length-normalised confidence** as an ECE sensitivity — noted in
  Methods §2.4; needs stored per-token data. Not blocking.
- **[CITE]** placeholders: AHN architecture paper; temporal-repair validation
  note; calibration-metric reference. To be filled when the bibliography is built.

---

## INTERNAL CONSISTENCY AUDIT (re-run at Revision Pass 1)

| item | required | manuscript state | ok? |
|---|---|---|---|
| total trials | 92,160 consistently | Methods §2.1, §2.3, §2.6; EXT §2.1/2.8/2.14; Results §3.1 [R1] — always "92,160" | **Yes** |
| grid factors | 4 arch / 240 items / 8 seeds / 12 targets | Methods §2.1 (4 arms), §2.2 (240 items, 48/type), §2.3 (8 seeds, 12 targets); Results [R1] — identical | **Yes** |
| W value | W = 256 everywhere | Methods §2.2, §2.3, §2.4; Results §3.2–3.5 — always 256; no other value | **Yes** |
| K ≠ W | K never equated with W | Methods §2.3 ("K … is not W"); Results §3.3 [R17, R25] ("every K < W"; "The knee is not the window") | **Yes** |
| H1 terminology | consistent fact-type names | Methods §2.2 + Results §3.2 / §3.6: numerical, entity-attribute, contradictory, temporal, compound-relational; internal key `multi-hop` only where flagged | **Yes** |
| compound-relational framing | never genuine multi-hop reasoning | Methods §2.2 and Results §3.6 both disavow; §3.2 attributes rank partly to a difficulty ceiling, not "chained inference" | **Yes** |
| H2 amendment identification | always post-freeze | Results [R22, R23] marked "*Post-freeze per-type width characterization*" / [R25 residual] "*post-freeze*"; Methods §2.5 dedicated subsection; traceability marks each v1.1 row | **Yes** |
| H2 shape framing | change-point evidence and per-type widths not presented as two identical binary tests | Results §3.3: [R20] "*Frozen change-point evidence*" (ΔAIC magnitudes, thin baseline margin), [R22] "*Post-freeze per-type width characterization*"; synthesis names the earlier/narrower Transformer vs later/broader AHN pattern | **Yes** |
| H3 behaviour vs mechanism | distinction preserved | Methods §2.4 and Results §3.4 closing paragraph state no mechanistic claim; "failure mode rather than sustained factual retrieval" ([R26]-adjacent) is behavioural | **Yes** |
| deep-recurrent wording | bounded negative result with counts + CIs | Results §3.5 [R33–R36]: counts 0/0/1/3, denominator 3,542, Wilson upper bounds; approved sentence; "stores nothing" / "information is gone" absent; §3.3 subsection retitled "Near-zero retrieval accuracy beyond the window" | **Yes** |
| Transformer malformed | not represented by the pooled rate | Results §3.6 [R42, R45]: per-architecture first; pooled 12.6% only "alongside the per-architecture split, never alone" | **Yes** |
| abstention vs malformed | not conflated | Methods §2.3 four mutually exclusive outcomes; Results [R30] and Figure 3 separate them; "unsignalled failure" defined as incorrect-valid ∨ malformed with composition stated ([R27, R30]) | **Yes** |
| abstention vs factual confidence | not conflated | Methods §2.3 / §2.4: abstention confidence analysed separately, never pooled with factual confidence; Results §3.4 calibration is answered-valid only | **Yes** |
| A_transition definition | consistent | Methods §2.4 and Results §3.2: mean raw strict accuracy over intended targets 205–265, AHN pooled, Transformer excluded | **Yes** |
| gap CI | one value | +0.249 [0.233, 0.266] in Methods §2.4 context, Results [R14], traceability R14 | **Yes** |
| K values | consistent | 208.3 / 218.4 / 219.6 / 240.0 in Results [R16], Table 3, traceability R16 | **Yes** |
| p-value representation | no "p = 0" / "p ≈ 0" | Results preamble states the floor once; [R7] omnibus 5×10⁻⁴ (add-one); [R8]/[R28] "p < 0.001" | **Yes** |
| exhibit numbering | figures D,1,2,3; tables 1–5; appendix A-H1/A-H2a/A-H2b/A-H3/A-VAL/A-REPRO | matches `final_exhibit_plan.md` and `EXHIBIT_MANIFEST.json` | **Yes** |
| Methods ↔ Extended | main Methods a strict subset of EXT; no contradictory numbers | §2.1–2.6 condense EXT §2.1–2.14; all shared constants identical; EXT header states the relationship | **Yes** |

### Consistency issues found / fixed

**None found.** The Revision Pass 1 changes (condensation, H2 reframe, p-value
formatting, one retitle, VAL-3 rewording) introduced no numeric, factor, W/K, or
terminology inconsistency across `METHODS.md`, `METHODS_EXTENDED.md`,
`RESULTS.md`, and `RESULTS_TRACEABILITY.md`.

---

## Readiness

| gate | verdict |
|---|---|
| Methods ready for scientific review | **READY** — main Methods ~1,880 words retains every required element (architectures, benchmark, memory-pressure design, W, pressure coordinate, scoring, grid, H1/H2/H3 analyses, the post-freeze H2 amendment as a dedicated §2.5); full reproducibility detail preserved in `METHODS_EXTENDED.md`; the runtime-commit gap is disclosed |
| Results ready for scientific review | **READY** — all 49 numerical statements traced 1:1 to locked evidence; every claim consistent with the register; H2 now communicates the earlier/narrower Transformer vs later/broader AHN transition explicitly; production-failure and information-absence are kept distinct; H3 leads with failure mode; no prohibited wording; no p-value published as zero; interpretation that belongs in Discussion has been removed |

Open items, none blocking: four `[CITE]` placeholders; the `[D]` runtime-commit
decision; the optional temporal-only answered-valid variant.
