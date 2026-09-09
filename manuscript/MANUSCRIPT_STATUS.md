# Manuscript Status

Drafting stage: **Methods and Results only.** Introduction, Related Work,
Discussion, Abstract, and Conclusion are not yet written (deliberately).

| file | status | words |
|---|---|---|
| `METHODS.md` | draft complete | ~3,080 |
| `RESULTS.md` | draft complete (49 numbered numerical statements) | ~2,350 |
| `RESULTS_TRACEABILITY.md` | complete — 49/49 statements traced | — |
| `MANUSCRIPT_STATUS.md` | this file | — |

Analysis phase is closed: no models were run, no new experimental data created,
no endpoint changed, and the locked raw artifact
(SHA-256 `a72fd43e87457a70c2833314e1443a794fa4189362ac8206c56275ef427fb62e`),
frozen v1.0 outputs, and locked v1.1 outputs were not modified. The Methods and
Results draw only on the three approved sources (locked parquet, frozen v1.0,
approved v1.1 amendment).

Exhibits: 9 main + 6 appendix, `outputs/publication_exhibits/`. The three cosmetic
WARNs from the exhibit audit were resolved before drafting; the exhibit audit now
records all 15 exhibits as PASS (`outputs/publication_exhibits/EXHIBIT_AUDIT.md`),
and `scripts/audit_publication_exhibits.py` returns ALL CHECKS PASS.

---

## CLAIM AUDIT

Every substantive claim in `METHODS.md` and `RESULTS.md` was checked against
`protocol/final_claims_register.md`. The register's *Allowed wording* and
*Prohibited wording* fields are authoritative.

### Claims checked (by register ID)

| register ID | manuscript treatment | consistent with register? |
|---|---|---|
| **H1-1** (non-uniform degradation) | Results §3.2 [R6–R8]; framed as "degrade non-uniformly in task accuracy"; omnibus p reported; answered-valid sensitivity reported alongside ([R9]); status SUPPORTED | **Yes** |
| **H1-2** (fact-type ordering) | Results §3.2 "ordering" para [R6, R9, R12]; "compound-relational fastest, entity-attribute most robust; middle ranks closer together and partly metric-dependent"; status PARTIALLY SUPPORTED not overstated | **Yes** |
| **H2-1** (near-window advantage) | Results §3.3 [R14, R15]; "+0.249 [0.233, 0.266]"; baseline defined as no-recurrent-memory (Methods §2.2); part-of-gap-is-degeneration caveat via §3.6 VAL-3 cross-reference | **Yes** |
| **H2-2** (threshold-like shape) | Results §3.3 [R20, R22, R23]; "threshold-like" attributed to the AIC shape test + per-eligible-type widths, not to the frozen pooled width; status SUPPORTED | **Yes** |
| **H2-3** (transition width) | Results §3.3 [R21] (frozen undefined, preserved, not interpreted) + [R22, R23] (post-freeze amendment, explicitly labelled); "intermediate" never used | **Yes** |
| **H2-4** (W ≠ K) | Methods §2.6; Results §3.3 [R16–R19, R25]; "every K < W"; "K is a descriptive empirical knee, not a threshold"; "compression begins at K" never used; AHN K reported as a range with the seed-spread caveat [R18] | **Yes** |
| **H2-5** (deep-recurrent retention) | Results §3.5 [R33–R36]; approved wording verbatim: "No measurable target-specific factual retention was observed at deep recurrent pressure under the production evaluation"; counts, denominators, Wilson bounds reported; "stores nothing" never used | **Yes** |
| **H3-1** (appropriate abstention) | Results §3.4 [R26, R28, R29]; "93–95% vs 52%", p_holm ≈ 0, seed-stable; "AHN knows it has forgotten" never used | **Yes** |
| **H3-2** (unsignalled failure) | Results §3.4 [R27, R28, R30]; composition stated (baseline rate is mostly malformed output) | **Yes** |
| **H3-3** (factual calibration) | Results §3.4 [R31, R32]; "overconfident" scoped to "< 5% of past-window trials"; deep-pressure ECE/CWR not headlined; "AHN is well-calibrated" never used | **Yes** |
| **H3-4** (mechanism) — **PROHIBITED CLAIM** | Methods §2.11 and Results §3.4 closing paragraph explicitly state the contrast confounds recurrent state with distillation recipe and "cannot be determined from this design"; no mentalistic/mechanistic wording used | **Yes — prohibited claim not made** |
| **VAL-1** (temporal construct) | Results §3.6 [R37, R38]; "balanced order-retrieval task"; "documented directional response preference … nets to chance"; "positional shortcut" and "benchmark is invalid" never used | **Yes** |
| **VAL-2** (compound-relational construct) | Methods §2.4 and Results §3.6 [R39–R41]; "not a multi-hop reasoning benchmark" stated twice; "co-located two-clause target"; "task-difficulty ceiling"; "multi-hop reasoning" / "chained inference" only in explicit disavowals | **Yes** |
| **VAL-3** (transformer control behaviour) | Results §3.6 [R42–R45]; per-architecture split always shown; pooled 12.6% only alongside the split; "expected no-recurrent-memory degeneration … control behaviour"; "pipeline problem" not claimed | **Yes** |
| **VAL-4** (residual in-window failures) | Results §3.6 [R46–R48] and §3.3 [R25]; "pressure axis is a proxy"; "not attributable solely to the exact-to-compressed transition"; "No mechanism is claimed" | **Yes** |

### Violations found

**Initial pass:** 2 phrasings needed adjustment.

1. **Results §3.1** contained "The grid is well calibrated" — the phrase
   "well calibrated" is reserved in the register (H3-3 prohibits blanket
   calibration claims), and although this sentence was about the *pressure grid*
   and not model confidence, it invited misreading. **Corrected** to "The pressure
   grid is accurately calibrated".
2. **Results §3.2 interpretation** contained "not representational information
   loss in isolation" — the register (H1-1) prohibits "differential
   representational information loss" as a claim. The sentence was a disavowal,
   but to avoid the phrase entirely it was **reworded** to "it is not a direct
   measure of how much of the target value remains recoverable from the model's
   state".

### Corrections made

- 2 wording corrections as above (both in `RESULTS.md`).
- No change to any number, endpoint, or exhibit.

### Prohibited phrases searched (case-insensitive, `METHODS.md` + `RESULTS.md`)

`proves` · `prove that` · `knows it` · `knew it` · `aware that` · `recognis*` ·
`compression threshold` · `threshold T` · `multi-hop reasoning` ·
`multihop reasoning` · `remembers indefinitely` · `stores nothing` ·
`store nothing` · `forgotten at different` · `representational information loss` ·
`intermediate width` · `solves long-context` · `positional shortcut` ·
`benchmark is invalid` · `chained inference` · `chain of` · `because compression` ·
`compression causes` · `caused by compression` · `the model knows` ·
`the recurrent state knows` · `well-calibrated` · `well calibrated` ·
`clearly shows` · `demonstrates that` · `confirms that`

**Remaining matches after correction (all verified benign):**

| match | location | why it is not a violation |
|---|---|---|
| "recognised value" / "a recognised 'I don't know' form" / "unrecognised value" | Methods §2.7, Results §3.6 | scorer-definition terms; not a claim about the model |
| "we do not describe the collapse as occurring 'at' a compression threshold" | Methods §2.6 | explicit disavowal, required by H2-4 |
| "Compound-relational is not a multi-hop reasoning benchmark" (×2) | Methods §2.4, Results §3.6 | explicit disavowal, required by VAL-2 |
| "multi-hop reasoning" inside those disavowals | Methods §2.4, Results §3.6 | negated context |
| "`multi-hop`" as a data key | Methods §2.1, §2.4 | explicitly labelled as the retained internal key |

No unqualified use of any prohibited phrase remains.

### Unresolved issues

- **[D] Runtime-commit provenance gap.** The generation-runtime commit (`d29c6d8…`)
  is not in the released repository history. Methods §2.14 discloses this as a
  limitation with the hash-equivalence mitigation. Team decision: recover the
  commit from the generation environment if still available, or accept the
  disclosure as written. Does not affect any result.
- **[D] Literal temporal-only answered-valid sensitivity** (temporal switched to
  answered-valid, other types left on raw strict) was noted as optional in the
  results specification and was not computed. The reported answered-valid
  sensitivity switches all types. If a reviewer asks specifically for the
  temporal-only variant it can be produced from the locked parquet with frozen
  code (analysis-only). Not currently a gap in the draft.
- **[future work] Length-normalised confidence** as an ECE sensitivity
  (`open_decisions.md` #6) — noted in Methods §2.11; would require the stored
  per-token data. Not blocking.
- **[CITE] placeholders**: the AHN architecture paper, the temporal-repair
  validation note, and calibration-metric references (Guo et al. for ECE) need
  bibliography entries when the reference list is assembled.

---

## INTERNAL CONSISTENCY AUDIT

| item | required | manuscript state | ok? |
|---|---|---|---|
| total trials | 92,160 used consistently | Methods §2.1, §2.8, §2.14; Results §3.1 [R1] — always "92,160" | **Yes** |
| grid factors | 4 architectures / 240 items / 8 seeds / 12 targets consistent | Methods §2.2 (4 arms), §2.4 (240 items, 48/type), §2.8 (8 seeds, 12 targets); Results §3.1 [R1] — identical everywhere | **Yes** |
| W value | W = 256 everywhere | Methods §2.3, §2.6, §2.10, §2.11; Results §3.2, §3.3, §3.4 — always 256; no other value used | **Yes** |
| K ≠ W | K never equated with W | Methods §2.6 ("K … is not equal to W"); Results §3.3 [R17, R25] ("every K < W", "The empirical knee is not the window"); no sentence equates them | **Yes** |
| H1 terminology | consistent fact-type names | Methods §2.4 table + Results §3.2 use: numerical, entity-attribute, contradictory, temporal, compound-relational — consistently; internal key `multi-hop` only where explicitly flagged | **Yes** |
| compound-relational framing | never described as genuine multi-hop reasoning | Methods §2.4 and Results §3.6 both state it is **not** a multi-hop reasoning benchmark; §3.2 attributes its rank partly to a difficulty ceiling, not "chained inference" | **Yes** |
| H2 amendment identification | always identified as post-freeze | Results [R22, R23, R25 residual] carry "*(Post-freeze reporting amendment)*" or "*post-freeze*"; Methods §2.12 is a dedicated subsection; the traceability table marks each v1.1 row | **Yes** |
| H3 behaviour vs mechanism | distinction preserved | Methods §2.11 and Results §3.4 closing paragraph state no mechanistic claim; H3-4 explicitly identified as a prohibited claim in the claim audit | **Yes** |
| deep-recurrent wording | appropriately bounded (negative result with counts + CIs) | Results §3.5 [R33–R36]: counts (0/0/1/3), denominators (3,542), Wilson upper bounds; approved sentence used; "stores nothing" absent | **Yes** |
| Transformer malformed | not represented by the pooled rate | Results §3.6 [R42, R45]: per-architecture rates given first; pooled 12.6% only "alongside the per-architecture split, never alone" | **Yes** |
| abstention vs malformed | not conflated | Methods §2.7 defines four mutually exclusive outcomes; Results §3.4 [R30] and Figure 3 separate them; "unsignalled failure" is explicitly defined as incorrect-valid ∨ malformed, and its composition is stated ([R27, R30]) | **Yes** |
| abstention confidence vs factual confidence | not conflated | Methods §2.7 and §2.11 state abstention confidence is analysed separately and never pooled with factual confidence; Results §3.4 calibration paragraphs are on answered-valid trials only | **Yes** |
| A_transition definition | consistent | Methods §2.9 and Results §3.2 both: mean raw strict accuracy over intended targets 205–265, AHN pooled, Transformer excluded | **Yes** |
| gap CI | consistent value | +0.249 [0.233, 0.266] in Methods §2.10 context, Results [R14], traceability R14 | **Yes** |
| K values | consistent | 208.3 / 218.4 / 219.6 / 240.0 in Results [R16], Table 3, traceability R16 | **Yes** |
| answered-valid ordering | stated where H1 ordering is discussed | Results §3.2 "Ordering" paragraph [R9] and Table 1 caption | **Yes** |
| exhibit numbering | figures D,1,2,3; tables 1–5; appendix A-H1/A-H2a/A-H2b/A-H3/A-VAL/A-REPRO | matches `protocol/final_exhibit_plan.md` and `EXHIBIT_MANIFEST.json` | **Yes** |

### Consistency issues found / fixed

**None found beyond the 2 wording corrections in the Claim Audit.** Number,
factor, W, and terminology usage are internally consistent across `METHODS.md`,
`RESULTS.md`, and `RESULTS_TRACEABILITY.md`.

---

## Readiness

| gate | verdict |
|---|---|
| Methods ready for scientific review | **READY** — reproducible-detail complete; the post-freeze amendment is disclosed in a dedicated subsection; the runtime-commit gap is disclosed |
| Results ready for scientific review | **READY** — all 49 numerical statements traced 1:1 to locked evidence; every claim consistent with the register; no prohibited wording; no speculation (mechanistic interpretation deferred to Discussion, not yet written) |

Open items for the review, none blocking: the four `[CITE]` placeholders; the
`[D]` runtime-commit decision; the optional temporal-only answered-valid variant.
