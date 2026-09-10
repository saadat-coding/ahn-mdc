# Conclusion

We set out to characterize what degrades, when, and how, as a query target is
driven from exact local attention into a compressed recurrent memory, using
Artificial Hippocampus Networks and a matched no-recurrent-memory control.

On *what* degrades: loss of end-to-end task performance under memory pressure is
information-type dependent. The spread across our five information types is far
larger than label-permutation chance, and because the strict production metric
counts abstention and malformed output as failure, this is a statement about
task performance rather than about how much of a stored value remains in the
model's state; the exact ordering is partly metric-dependent.

On *when*: the empirical performance knee does not coincide with the
architectural exact-attention window. For every architecture the knee sits below
the window, and a substantial fraction of trials fail while the target is still
arithmetically inside the lossless window, so the transition is not a clean
inside/outside boundary. The recurrent path preserves useful near-window
retrieval longer than the control, but its accuracy transition is also broader,
by an explicitly post-freeze width characterization — the recurrent memory
reshapes the transition rather than translating a sharp cliff. Beyond the
transition, deep recurrent pressure yields no measurable sustained
target-specific factual retrieval under this production evaluation for any
architecture.

On *how* failure manifests: once retrieval becomes unreliable, the dominant
observed distinction between the AHN variants and the control is failure
behaviour. The AHN variants predominantly abstain; the control much more often
produces unsupported or malformed output. We describe this as behavioural
uncertainty signalling.

These observations are bounded. A production-level retrieval failure does not
establish that the recurrent state holds no latent target information, and the
architecture contrast confounds the presence of a recurrent state with the AHN
training and distillation recipe, so we do not claim that the model internally
detects forgetting. Because the benchmark is synthetic and the study covers one
base model with three released checkpoints, the results should not be generalised
to other scales or memory designs.

The broader implication is methodological: compressed-memory systems are better
evaluated jointly on retrieval success, degradation dynamics across information
types, and failure behaviour, rather than on aggregate accuracy alone. Whether a
recurrent memory's shift toward abstention reflects a signal in its state or a
learned output policy is the natural next question, and it requires
training-matched and ablation-based comparisons that this study motivates but
does not perform.
