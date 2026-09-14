# Malformed Output Feedback Audit (Teammate Feedback Item 5)

**Feedback:** "Report malformed-output behavior distinctly; do not implicitly
treat malformed output as equivalent to ordinary wrong-valid answers;
architectures may have different failure modes."

**Verdict: ALREADY ADDRESSED — NO EDIT NEEDED.**

## The four outcomes are defined as mutually exclusive from the outset

Methods §2.3: "each trial is assigned **exactly one** of four outcomes:
**correct** …, **incorrect valid answer** …, **abstention** …, or
**malformed** …" Verified against the locked parquet: the `correct` /
`abstained` / `malformed` indicator columns never co-occur (0 rows with more
than one flag set), and 4,826 rows have none set (= incorrect valid answer),
confirming the four categories partition the data exactly as documented.

## Is malformed output independently visible in Results?

Yes, at multiple points, always as its own named rate, never merged into
"wrong-valid":

- [R30]: baseline past-window composition given as four separate numbers —
  "0.52 abstention, 0.45 malformed, 0.03 incorrect valid, < 0.01 correct."
- [R42]-[R45]: a dedicated VAL-3 paragraph reports the Transformer malformed
  rate (39.6% overall vs 1.4-4.8% for the AHN arms — i.e., **architectures do
  have different failure-mode rates**, exactly as the feedback anticipates),
  its by-pressure profile, its subtype breakdown (over-length, unrecognised
  value, empty, negation), and states the pooled-across-architecture rate
  (12.6%) is "reported only alongside the per-architecture split."
- [R46]-[R48] (VAL-4): residual in-window failures are broken into "46%
  abstentions, 39% malformed, 15% incorrect valid answers" — three separate
  shares, not a merged "failure" bucket.
- New in this pass, [R51]: the Transformer's malformed rate is reported
  alongside its abstention rate at every pressure target (285-380: malformed
  0.68-0.71; 520-760: malformed 0.03-0.10), keeping the two visibly distinct
  across the full pressure range, not just at the pooled H3 boundary.

## Is it visible in Figure 3 / relevant tables?

Yes. Figure 3's own caption (`outputs/publication_exhibits/CAPTIONS.md`)
states: "the four mutually exclusive per-trial outcomes — correct factual
answer, incorrect valid answer, malformed output, abstention ('I don't
know') — as stacked fractions." Table 4 (construct/control validity) carries a
separate `in_window_malformed` column. The site's rendered Results (Table 2/
Table 4/Table 5 area) preserves this separation.

## Is strict accuracy's treatment of malformed output stated clearly?

Yes. Methods §2.3: "**Strict production accuracy** is the fraction scored
*correct*; **abstentions and malformed outputs both count as failures**." This
sentence is repeated in substance in Results ([R13], "Because the strict
metric counts abstention and malformed output as failure…") and Discussion
(§4.6 Limitations, "Metric: strict production accuracy counts abstention and
malformed output as failure, mixing retrieval success with output policy").

## Does any sentence accidentally equate malformed with ordinary wrong answers?

No such sentence was found. The one place the two are pooled by design is the
pre-registered **H3 composite** `unsignalled_failure_rate` = P(incorrect-valid
∨ malformed) — but this is a deliberate, disclosed, pre-registered definition
(Methods §2.4), and every time it is reported the manuscript also gives the
underlying composition separately ([R30]: baseline 0.45 malformed vs 0.03
incorrect-valid — a 15:1 ratio, explicitly visible, not hidden inside the
composite).

## Is the Transformer's malformed behaviour framed as control behaviour, not data corruption?

Yes: [R44]-[R45] state "the concentration of malformed outputs at higher
pressure levels, together with their near-absence at the control anchors,
supports treating this as control behaviour rather than pipeline corruption;
the pre-registered gate classifies it as such." This framing was previously
verified (Revision Pass 1) to remove causal language ("expected … degeneration
once the target is evicted") in favour of this evidence-bounded statement.

## Conclusion

All five audit questions resolve to "yes, already handled": malformed output
is independently visible in Results and the exhibit captions, the strict
accuracy definition is explicit that it counts as failure, no prose equates it
with wrong-valid answers, and architecture-specific failure-mode differences
are already the headline of VAL-3.

**Classification: A — already addressed.** **Edit needed: none** (R51, added
for Item 3, additionally reinforces this by reporting the Transformer's
malformed rate alongside abstention at every pressure target).
