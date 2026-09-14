# Conclusion

We characterized what degrades, when, and how, as a query target is driven from
exact attention into a compressed recurrent memory, using Artificial Hippocampus
Networks and a matched no-recurrent-memory control.

Loss of end-to-end task performance under memory pressure is information-type
dependent: the spread across our five information types is far larger than
label-permutation chance, and because the strict metric counts abstention and
malformed output as failure, this concerns task performance rather than how much
of a stored value remains in the model's state. The empirical performance knee
does not coincide with the exact-attention window - for every architecture it
sits below the window, and a substantial fraction of trials fail while the target
is still exact-attention eligible, so the transition is not a clean inside/outside
boundary. The AHN variants preserve useful near-window retrieval longer than
the control, but their accuracy transition is also broader, by an explicitly
post-freeze width characterization: the AHN system reshapes the transition
rather than translating a sharp cliff. This is a system-level comparison and
does not isolate the recurrent mechanism from architecture- or
training-specific differences. Beyond the transition, deep recurrent pressure yields
no measurable sustained target-specific factual retrieval under this production
evaluation for any architecture. Once retrieval becomes unreliable, the dominant
observed distinction between the AHN variants and the control is failure
behaviour: the AHN variants predominantly abstain while the control much more
often produces unsupported or malformed output.

These observations are bounded. A production-level retrieval failure does not
establish that the recurrent state holds no latent target information, and the
architecture contrast confounds a recurrent state with the AHN training and
distillation recipe, so we do not claim that the model internally detects
forgetting. The broader implication is methodological: compressed-memory systems
are better evaluated jointly on retrieval success, degradation dynamics across
information types, and failure behaviour. Whether a recurrent memory's shift
toward abstention reflects a signal in its state or a learned output policy is the
natural next question, and it requires training-matched and ablation-based
comparisons this study motivates but does not perform.
