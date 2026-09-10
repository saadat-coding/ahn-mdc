# Introduction

Language models are now routinely deployed over context windows of hundreds of
thousands of tokens, but a large nominal window does not guarantee that the
information inside it is used reliably. Recent evaluations across many models and
task families report that accuracy can fall sharply as inputs grow, that this
decline is uneven across capabilities, and that strong performance on
needle-style retrieval need not carry over to downstream use of the retrieved
content [CITE:atlas2026]. Complementary diagnostic work finds that long-context
and retrieval-augmented models often answer from parametric priors, leave
supplied evidence unused, or cite relevant text without turning it into an answer
[CITE:evidence2026], and length-distribution analyses identify context lengths at
which task accuracy drops abruptly rather than smoothly [CITE:threshold2026].
Nominal capacity and effective information use are therefore distinct properties,
and the gap between them is task- and architecture-dependent.

This gap is shaped by how a model stores context. Exact attention keeps every
past token directly addressable, but its memory and compute grow with sequence
length. Recurrent and compressed-memory mechanisms instead maintain a bounded
state, which removes the scaling cost but creates a different problem: a
fixed-size state cannot preserve arbitrary detail, and analyses of state-space
models describe how their recall of specific past content decays with distance
and is bounded by state size [CITE:memmamba2025][CITE:recallmamba2026]. This
trade-off between the efficiency of a compressive fixed-size memory and the
fidelity of a growing lossless one is an active design target, with recent work
proposing compressive recurrent memories [CITE:elasticmem2026], revisiting
sliding-window size as a lever on long-range recall [CITE:shortwin2025], and
advancing the underlying recurrent formulations [CITE:mamba3_2026].

Artificial Hippocampus Networks (AHN) are one concrete instantiation of this
hybrid design [CITE:ahn2025]. An AHN keeps a local sliding window of exact
attention as short-term memory and recurrently compresses information leaving
that window into a fixed-size long-term state, implemented with a Mamba-2
[CITE:mamba2_2024], DeltaNet [CITE:deltanet2024], or Gated DeltaNet
[CITE:gdn2024] recurrent module. On long-context benchmarks, AHN-augmented models
improve over sliding-window baselines while cutting compute and memory
[CITE:ahn2025]. These results are reported as aggregate scores, and the method
does not claim that the compressed state is lossless. What aggregate scores do
not show is how retrieval behaves as a query's target moves from the exact local
window into the compressed recurrent state: which kinds of information survive
that transition, where along the pressure axis performance falls, and what the
model does once it can no longer retrieve the target.

We organise these into three questions. *What* degrades: does end-to-end task
performance fall at the same rate for every kind of stored information, or is the
loss uneven across information types? *When* it degrades: does performance fall in
a concentrated pressure region, how does that region relate to the architectural
window, and does the recurrent path move or reshape it? *How* failure manifests:
once retrieval becomes unreliable, does the model abstain, answer incorrectly, or
produce malformed output, and does a recurrent memory change that behaviour?

To study these questions we run a controlled memory-pressure experiment on
`Qwen2.5-3B-Instruct`. We compare three AHN arms (Mamba-2, DeltaNet, Gated
DeltaNet) against a matched Transformer control whose sliding window is forced to
the same width and which has no recurrent module. A synthetic evaluation set of
240 items spans five information types (numerical, entity-attribute,
contradictory, temporal, and a compound-relational type that is a single
co-located two-clause target, not multi-hop reasoning over separated facts).
Memory pressure is applied by placing a growing block of distractor sentences
after the target, so that increasing pressure pushes the target out of the
forced exact-attention window W. We measure retrieval with a strict production
metric, estimate an empirical performance knee K from the pooled accuracy curve,
and classify every response as correct, incorrect, an abstention, or malformed so
that failure behaviour can be analysed alongside accuracy. Analyses were frozen
before the full run; one reporting metric was undefined on the collected data and
is corrected by a documented post-freeze amendment that changes no primary
result.

Across 92,160 trials we observe that task-performance degradation is
information-type dependent; that the AHN arms preserve substantially more
near-window strict accuracy than the Transformer control; that the AHN accuracy
transition is later than the control's and, by a post-freeze width analysis, also
*broader*, so the recurrent path does not simply shift a sharp cliff to the
right; that the empirical knee K lies
below the architectural window W for every architecture, with retrieval already
failing on a substantial fraction of trials whose target is still nominally
inside the window; that at deep recurrent pressure no measurable target-specific
factual retrieval is observed under the production evaluation for any
architecture; and that as pressure rises the AHN arms shift predominantly toward
abstention rather than unsupported or malformed output. This last result is
behavioural: it describes what the model emits, not an internal state, and the
experiment does not separate a signal in the recurrent state from a learned
abstention policy.

The paper makes three contributions.
**Information.** A controlled characterization of information-type-dependent
task-performance degradation under increasing memory pressure, with sensitivity
analyses separating retrieval failure from abstention propensity.
**Transition.** A characterization of the exact-to-recurrent transition that
keeps the architectural window W distinct from the empirical performance knee K,
shows K < W together with residual in-window failure, and identifies
architecture-dependent transition dynamics (an earlier, narrower control
transition versus later, broader AHN transitions).
**Failure behaviour.** A joint analysis of retrieval and behavioural uncertainty
signalling, showing that the AHN near-window retrieval advantage does not become
sustained deep-recurrent factual retrieval and that the dominant high-pressure
difference between AHN and the control is a shift toward abstention rather than
unsignalled failure.
