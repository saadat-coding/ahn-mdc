# Discussion Claim Map

Every substantive empirical interpretation, bounding statement, and future-work
hypothesis in `manuscript/DISCUSSION.md`, mapped to its Results support, the
claims register, and its allowed strength. Ordinary connective prose is not
listed.

Type key: **E** = empirical observation restated for synthesis · **I** =
interpretation of the evidence · **B** = bounding / disavowal (states what the
evidence does *not* license) · **F** = future-work hypothesis (explicitly open) ·
**M** = methodological disclosure.

| ID | Discussion sentence (abbrev.) | Results support | register ID | type | citation? | allowed strength | reviewer risk |
|---|---|---|---|---|---|---|---|
| D1 | End-to-end task-performance degradation is information-type dependent (5-way spread ≫ label-permutation chance). | R6, R7 | H1-1 | E | no | SUPPORTED — "degrade non-uniformly in task accuracy" | reading it as representational decay — mitigated by D4 |
| D2 | Ordering (compound-relational fastest, entity-attribute most robust) is only partly stable and partly metric-dependent. | R6, R9, R12 | H1-2 | E | no | PARTIALLY SUPPORTED — middle ranks "closer and partly metric-dependent" | over-firm ranking; caveat is explicit |
| D3 | The manifestation of failure (wrong / abstain / malformed) is itself type-dependent and contributes to the ordering. | R9, R13, R39 | H1-2, VAL-2 | I | no | supported as caveat, not as mechanism | none material |
| D4 | We do **not** interpret this as differential decay of stored representations. | — | H1-1 (prohibited wording) | B | no | required disavowal | none — this is the guard |
| D5 | Why types differ (answer-space structure, complexity, model prior, abstention tendency, relational structure, retrieval–output interaction) is open. | — | — | F | no | explicitly "candidate factors … not established mechanisms" | presenting a favourite as established — avoided by listing all as open |
| D6 | Compound-relational's fast apparent degradation is confounded by a lower in-window ceiling (≈0.84, control WARNING). | R39, R40 | VAL-2 | E+I | no | LIMITATION + WARNING as in register | none — matches register caveat |
| D7 | The AHN arms preserve substantially more near-window accuracy than the control (≈0.25 more strict accuracy, +0.249 [0.233, 0.266]). | R14, R15 | H2-1 | E | no | SUPPORTED — "≈0.25 more near-window retrieval accuracy (95% CI [0.23, 0.27])" | ignoring that both collapse past W — covered by D14 |
| D8 | AHN does **not** simply move the transition to the right; "cliff to the right" is not supported. | R14, R16, R20, R22 | H2-1, H2-2, H2-4 | I | no | supported by the width + K asymmetry | this is a *weakening* of a naive claim — low risk |
| D9 | The collapse is concentrated, not gradual, for every architecture. | R20, R22, R23 | H2-2 | E | no | SUPPORTED — "concentrated … not gradual" | conflating the two shape tests — handled by D12 |
| D10 | The Transformer transition is earlier and narrower; the AHN transitions are later and broader. | R16, R20, R22, R23 | H2-2, H2-4 | E | no | supported (K 208 vs 218–240; median width ≈32 vs 62–74) | claiming AHN is "sharper" — explicitly reversed here |
| D11 | AHN preserves useful task performance farther into the near-window region *and* spreads its decline over a wider pressure interval — a qualitatively different transition. | R14, R15, R16, R22 | H2-1, H2-2 | I | no | supported as description of task-performance dynamics; not mechanistic | reviewer may want "why" — deferred to D5/D32 |
| D12 | The per-type width analysis is post-freeze, *characterizes* rather than rescues the result, and must not be cited as pre-registered. | R21, R22 | H2-3 | M | cite `amendment_h2_transition_width.md` | required disclosure | hiding the post-freeze status — this sentence is the disclosure |
| D13 | The pre-registered pooled 90→10 estimator was mathematically undefined (pooled curve never reaches 0.90). | R21 | H2-3 | E+M | no | UNDETERMINED (frozen) | none |
| D14 | At deep recurrent pressure (≥2W), no measurable target-specific factual retention was observed under the production evaluation. | R33, R34, R36 | H2-5 | E | no | NEGATIVE RESULT — approved wording verbatim | overstatement to "stores nothing" — blocked by D15 |
| D15 | This null does **not** establish that the recurrent state contains no target information. | R33, R34 | H2-5 (prohibited wording) | B | no | required disavowal | none — this is the guard |
| D16 | The deep-recurrent null is informative because AHN is designed to carry information beyond the exact window. | R33, R36 | H2-5 | I | no | "so what" framing, evidence-bounded | mild — framed as a boundary on the system, not a mechanism |
| D17 | Past the window the clearest architecture difference is failure *mode*, not what is retrieved. | R26, R27, R30, R33 | H3-1, H3-2, H2-5 | I | no | supported — behavioural | reading it as retained-memory advantage — D14 blocks that |
| D18 | Beyond W+16 the AHN arms abstain on the large majority of trials and leave a small fraction of failures unsignalled; the control abstains on roughly half and fails without signalling on the other half (mostly degenerate output); gap ≈0.42 on both rates, Holm-significant, seed-stable. (Exact rates 0.929–0.946 vs 0.516 and 0.052–0.071 vs 0.480 are in Results, not repeated in the Discussion prose.) | R26, R27, R28, R29, R30 | H3-1, H3-2 | E | no | SUPPORTED — register allowed wording | none — qualitative in prose, exact numbers in Results |
| D19 | This is behavioural uncertainty signalling / failure-mode adaptation. | R26, R27 | H3-1 | I | no | allowed term ("behavioral uncertainty signalling") | slippage to mentalistic reading — blocked by D20, D21 |
| D20 | The experiment cannot separate (A) a recurrent-state signal from (B) a learned/distilled abstention policy. | — | H3-4 | B | no | required caveat — state both alternatives | none — this is the guard |
| D21 | No claim that the model "knows" it forgot or that the recurrent state "encodes uncertainty". | — | H3-4 (prohibited wording) | B | no | required disavowal | none |
| D22 | In the transition AHN arms become more conservative on answered trials; the control does not shift. | R31 | H3-3 | E | no | PARTIALLY SUPPORTED — "gap shifts −0.06 to −0.12 … baseline does not shift" | over-reading a secondary result — labelled secondary |
| D23 | On the small past-window answered population all architectures are badly miscalibrated (< 5% of past-window trials, not a headline). | R32 | H3-3 | E+B | no | allowed only with the < 5% scope qualifier | "overconfident when wrong" as headline — explicitly scoped down |
| D24 | Abstention confidence ≠ factual confidence; the sequence-probability measure is provisional. | — | H3-3, Methods §2.4 | M | no | required caveat | none |
| D25 | Every architecture's K lies below W = 256 (≈208 control, ≈218–240 AHN). | R16, R17 | H2-4 | E | no | SUPPORTED — "K 208–240 vs W = 256; distinct" | implying K = W — reversed here |
| D26 | K is an observed per-run quantity, not an architectural constant, and does not mark compression onset. | R16, R18 | H2-4 (prohibited wording) | B | no | required disavowal — "compression begins at K" forbidden | none — this is the guard |
| D27 | ≈32% of trials whose target is arithmetically inside the lossless window still fail, rising steeply across intended pressures 205–235. | R25, R46, R47 | VAL-4 | E | no | SUPPORTED — register allowed wording | none |
| D28 | Performance deterioration is already underway while the target is inside the window; the transition is not a binary inside/outside story. | R25, R46, R47, R48 | VAL-4 | I | no | approved — "the pressure axis is a proxy … not a clean exact/recurrent switch" | attributing to a mechanism — D29 blocks |
| D29 | Candidate contributors (context interference, attention competition, prompt/task effects, generation behaviour, span-boundary effects) are not distinguished by this design. | — | VAL-4 | F | no | required caveat — "no mechanism claimed" | naming a cause — all listed as undistinguished |
| D30 | Window size alone does not predict where empirical retrieval fails. | R16, R17, R25, R46 | H2-4, VAL-4 | I | no | supported implication | generalisation beyond this setting — hedged in D31 |
| D31 | Implications: evaluate by information type; characterize the transition region; window size insufficient; judge memory systems by how they fail; separate hidden-state-recoverable from production-retrievable information. | R6, R14, R16, R25, R26, R46 | H1-1, H2-1, H2-4, H3-1, VAL-4 | I | [CITE] for positioning | "implications, not proven universal laws" (stated) | over-generalisation — explicitly flagged as cautious |
| D32 | The central open question is mechanistic (recurrent-state signal vs learned output policy) and needs training-matched and ablation-based comparisons. | — | H3-4 | F | no | motivates future work; makes no mechanistic claim | none |

## Coverage check

- 32 substantive claims mapped.
- Empirical (E / E+…): D1, D2, D3, D6, D7, D9, D10, D13, D14, D18, D22, D23, D25,
  D27 (14).
- Interpretation (I / I+…): D3, D8, D11, D16, D17, D19, D28, D30, D31 (9).
- Bounding / disavowal (B): D4, D15, D20, D21, D23, D26 (6).
- Future hypothesis (F): D5, D29, D32 (3).
- Methodological disclosure (M): D12, D13, D24 (3).
- Citations required: D12 (internal amendment doc), D31 ([CITE] for literature
  positioning). No external citation is load-bearing for any empirical claim.
- Every empirical claim traces to at least one R-identifier already in
  `RESULTS_TRACEABILITY.md`; the Discussion introduces no new number.
