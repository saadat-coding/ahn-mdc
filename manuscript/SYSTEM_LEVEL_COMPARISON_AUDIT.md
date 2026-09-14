# System-Level Comparison Audit (Teammate Feedback Item 8)

**Feedback:** "Architecture/training/distillation differences are confounded;
the architecture comparison should be framed as a SYSTEM-LEVEL comparison; do
NOT imply the comparison causally isolates recurrent memory alone."

**Verdict: VALID — mostly already addressed; one sentence found and fixed.**

## Search

Searched all architecture-comparison prose (Abstract, Introduction, Related
Work, Methods, Results, Discussion, Conclusion) for causal constructions of the
form "recurrent memory {caused/causes/enables/produces/results in} X" and for
any sentence attributing an observed difference to "the recurrent mechanism"
or "the recurrent path" in isolation, rather than to the AHN system as a whole.

## Already-correct framing (no edit needed)

The confound is already stated explicitly and broadly, not narrowly:

- Methods §2.1: AHN modules "differ in parameter count by ~10% … and were
  self-distilled by the original authors; both are disclosed as confounds."
- Methods §2.4 (H3): "the contrast confounds a recurrent state with the AHN
  distillation recipe."
- Results §3.4: "The contrast confounds a recurrent state with the AHN
  distillation recipe; whether the behaviour reflects a signal in the
  recurrent state or a learned abstention policy cannot be determined from
  this design."
- Discussion §4.4: "the comparison confounds the presence of a recurrent
  state with the AHN training and distillation recipe."
- Discussion §4.6 (Limitations): "the AHN checkpoints differ from the control
  by recurrent-module training and distillation as well as by having a
  recurrent state, which limits causal attribution **for every
  AHN-vs-control contrast**" — this generalises the caveat beyond H3 to the
  whole comparison, as required.
- Related Work: "this contrast confounds a recurrent state with the AHN
  training and distillation recipe."
- Headline results consistently use system-level subjects: "the AHN arms
  preserve…" (Results [R14]), "the AHN variants retain…" (Abstract), "AHN
  arms are almost entirely abstention" ([R30]) — not "the recurrent memory
  preserves/retains."

## One sentence found and fixed

`manuscript/CONCLUSION.md` (before this pass) read:

> "The recurrent path preserves useful near-window retrieval longer than the
> control, but its accuracy transition is also broader … it reshapes the
> transition rather than translating a sharp cliff."

This attributes the near-window effect to **"the recurrent path"** specifically
— a mechanism-level subject — rather than to the AHN system, in the one
manuscript section that otherwise does not immediately restate the confound in
the same sentence (the confound sentence appears in the *next* paragraph,
about H3). A reader could take this sentence in isolation as implying the
recurrent mechanism alone (isolated from training/distillation) explains the
transition-shape result.

**Fixed** to:

> "The AHN variants preserve useful near-window retrieval longer than the
> control, but their accuracy transition is also broader, by an explicitly
> post-freeze width characterization: the AHN system reshapes the transition
> rather than translating a sharp cliff. **This is a system-level comparison
> and does not isolate the recurrent mechanism from architecture- or
> training-specific differences.**"

This changes only the grammatical subject ("the recurrent path" →
"the AHN variants" / "the AHN system") and adds the one caveat sentence
requested by the feedback, using language consistent with the rest of the
manuscript. No number, endpoint, or claim strength changed.

## Conclusion

The system-level framing is the manuscript's default and is stated repeatedly
and broadly (not narrowly scoped to H3 alone). One isolated sentence in the
Conclusion used mechanism-level language without a nearby caveat; it has been
corrected to match the rest of the manuscript.

**Classification: B — wording/consistency fix.** One minimal edit applied
(Conclusion, Edit Policy category A/B: naming/framing consistency + adding a
concise, already-evidenced caveat).
