# H3 Behavioural Framing Feedback Audit (Teammate Feedback Item 6)

**Feedback:** "Keep H3 behavioral; AHN abstains more when factual retrieval
fails; do NOT claim AHN 'knows it forgot'."

**Verdict: ALREADY ADDRESSED — NO EDIT NEEDED.**

## Prohibited-phrase search

Searched `manuscript/ABSTRACT.md`, `INTRODUCTION.md`, `RELATED_WORK.md`,
`METHODS.md`, `RESULTS.md`, `DISCUSSION.md`, `CONCLUSION.md` for: "knows it
forgot," "knows it has forgotten," "detects forgetting," "detects its own,"
"self-aware," "self aware," "memory awareness," "internal uncertainty
monitor," "is aware that," "recognizes its own forgetting," "the model
knows," "the recurrent state knows."

**Zero matches.** None of these phrases, or close variants, appear anywhere in
the manuscript-facing text.

## Positive framing check — is H3 stated as behavioural?

Yes, at every level:

- Methods §2.4 (H3 definition): "**No mechanistic claim is made**: the
  Transformer has no recurrent memory, so the contrast confounds a recurrent
  state with the AHN distillation recipe, and whether a behavioural difference
  reflects a signal in the recurrent state or a learned abstention policy
  cannot be determined here."
- Results §3.4: "The contrast confounds a recurrent state with the AHN
  distillation recipe; whether the behaviour reflects a signal in the
  recurrent state or a learned abstention policy cannot be determined from
  this design (H3-4)."
- Discussion §4.4 (title: "Failure mode and behavioural uncertainty
  signalling"): "We describe this as behavioural uncertainty signalling…";
  "We therefore avoid any claim that the model 'knows' it has forgotten or
  that the recurrent state 'encodes uncertainty.'"
- Conclusion: "We describe this as behavioural uncertainty signalling," and
  "we do not claim that the model internally detects forgetting."
- Introduction: "This last result is behavioural — it describes what the
  model emits, not an internal state…"

## Are both mechanistic alternatives represented?

Yes, side by side, in every section that discusses mechanism:

| location | recurrent-state-signal alternative | learned/distilled-policy alternative |
|---|---|---|
| Methods §2.4 | "a signal in the recurrent state" | "a learned abstention policy" |
| Results §3.4 | "a signal in the recurrent state" | "a learned abstention policy" |
| Discussion §4.4 | "(A) the recurrent state carries a usable signal that the context is thin" | "(B) the AHN checkpoints were distilled with training that produced an abstention policy under sparse context" (cites `hesitation2025`) |
| Conclusion | "a signal in its state" | "a learned output policy" |

Neither alternative is favoured; both are stated as currently indistinguishable
given the confounded architecture/training comparison.

## Does the manuscript state that AHN abstains more precisely when retrieval fails?

Yes — this is the H3 headline itself, reported with counts and rates rather
than as a vague claim: past the window, AHN abstains on 92.9-94.6% of trials
vs 51.6% for the control, and leaves only 5.2-7.1% of failures unsignalled vs
48.0% for the control ([R26]-[R28]), with the composition of "what happens
instead" spelled out per architecture ([R30]).

## Conclusion

Every element of this feedback item is already satisfied: no mentalistic
phrasing exists anywhere in the manuscript, H3 is explicitly and repeatedly
labelled behavioural, and both candidate mechanistic explanations are stated
as open and undetermined rather than one being asserted.

**Classification: A — already addressed.** **Edit needed: none.**
