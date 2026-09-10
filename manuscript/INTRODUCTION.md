# Introduction

Language models are routinely deployed over context windows of hundreds of
thousands of tokens, but a large nominal window does not guarantee that the
information inside it is used reliably. Recent evaluations report that accuracy
can fall sharply as inputs grow, that the decline is uneven across task families,
and that strong needle-style retrieval need not carry over to downstream use of
the retrieved content \citep{atlas2026}; that long-context and retrieval-augmented
models often answer from parametric priors, leave supplied evidence unused, or
cite text without turning it into an answer \citep{evidence2026}; and that some
context lengths produce abrupt rather than gradual accuracy drops
\citep{threshold2026}. Nominal capacity and effective information use are distinct
properties.

This gap is shaped by how a model stores context. Exact attention keeps every
past token directly addressable but scales in memory and compute with sequence
length. Recurrent and compressed-memory mechanisms instead maintain a bounded
state, which removes the scaling cost but cannot preserve arbitrary detail:
analyses of state-space models describe how recall of specific past content
decays with distance and is bounded by state size
\citep{memmamba2025,recallmamba2026}. Balancing a compressive fixed-size memory
against a lossless growing one is an active target, with recent work proposing
compressive recurrent memories \citep{elasticmem2026}, revisiting sliding-window
size as a lever on long-range recall \citep{shortwin2025}, and refining the
recurrent formulations \citep{mamba3_2026}.

Artificial Hippocampus Networks (AHN) are one concrete instantiation of this
hybrid design \citep{ahn2025}. An AHN keeps a local sliding window of exact
attention as short-term memory and recurrently compresses information leaving that
window into a fixed-size long-term state, implemented as a Mamba-2
\citep{mamba2_2024}, DeltaNet \citep{deltanet2024}, or Gated DeltaNet
\citep{gdn2024} module. AHN-augmented models improve over sliding-window baselines
while cutting compute and memory \citep{ahn2025}; these results are aggregate
scores, and the method does not claim the compressed state is lossless. Aggregate
scores do not show how retrieval behaves as a query target moves from the exact
window into the compressed state: which information types survive that transition,
where along the pressure axis performance falls, and what the model does once it
can no longer retrieve the target.

We organise these into three questions. *What* degrades: does end-to-end
task performance fall at the same rate for every information type? *When* it
degrades: is the fall concentrated, how does it relate to the exact-attention
window, and does the recurrent path move or reshape it? *How* failure
manifests: once retrieval is unreliable, does the model abstain, answer
incorrectly, or produce malformed output, and does a recurrent memory change
that?

To study these questions we run a controlled memory-pressure experiment on
`Qwen2.5-3B-Instruct`, comparing three AHN variants (Mamba-2, DeltaNet,
Gated DeltaNet) against a matched Transformer control whose sliding window is
forced to the same width and which has no recurrent module. A synthetic set of
240 items spans five information types (numerical, entity-attribute,
contradictory, temporal, and compound-relational — a single co-located two-clause
target, not multi-hop reasoning over separated facts). Pressure is applied by
growing a block of distractor sentences after the target so that it leaves the
forced exact-attention window W; we measure retrieval with a strict production
metric, estimate an empirical performance knee K from the pooled accuracy curve,
and classify every response as correct, incorrect, an abstention, or malformed.
Analyses were frozen before the full run; one reporting metric was undefined on
the collected data and is corrected by a documented post-freeze amendment that
changes no primary result.

Across 92,160 trials: task-performance degradation is information-type dependent;
the AHN variants preserve substantially more near-window strict accuracy than the
control; the AHN accuracy transition is later and, by a post-freeze width
analysis, broader, so the recurrent path does not simply shift a sharp cliff to
the right; K lies below W for every architecture, with retrieval already
failing on a substantial fraction of trials whose target is still exact-attention
eligible; at deep recurrent pressure no measurable target-specific factual
retrieval is observed under the production evaluation for any architecture; and as
pressure rises the AHN variants shift predominantly toward abstention rather than
unsupported or malformed output. This last result is behavioural — it describes
what the model emits, not an internal state — and the experiment does not separate
a signal in the recurrent state from a learned abstention policy.

We contribute: (i) a controlled characterization of information-type-dependent
task-performance degradation under memory pressure, with sensitivity analyses
separating retrieval failure from abstention propensity; (ii) a transition
characterization that keeps the exact-attention window W distinct from the
empirical performance knee K, shows K < W alongside residual in-window
failure, and identifies architecture-dependent dynamics (an earlier, narrower
control transition versus later, broader AHN transitions); and (iii) a joint
analysis of retrieval and behavioural uncertainty signalling, showing that the
AHN near-window advantage does not become sustained deep-recurrent retrieval and
that the dominant high-pressure difference from the control is a shift toward
abstention rather than unsignalled failure.
