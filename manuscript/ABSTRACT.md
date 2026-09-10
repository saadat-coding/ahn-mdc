# Abstract

Hybrid long-context architectures pair exact local attention with a compressed
recurrent memory, but aggregate benchmark scores do not show how reliability
changes as information comes under increasing memory pressure. We characterize
this process in Artificial Hippocampus Networks (AHN), comparing Mamba-2-,
DeltaNet-, and Gated DeltaNet-based AHN variants with a matched Transformer
control that has no recurrent module, across five information types and a
controlled pressure axis that moves a query target out of a fixed exact-attention
window (92,160 trials). End-to-end task-performance degradation is strongly
information-type dependent. Through the near-window transition the AHN variants
retain substantially higher strict accuracy than the control (pooled difference
+0.249, 95% CI [0.233, 0.266]); their transition occurs later and, by an
explicitly post-freeze width characterization, is also broader, rather than simply
a rightward shift of the control's sharper collapse. For every architecture the
empirical accuracy knee falls below the architectural attention window. At deep
recurrent
pressure, measurable target-specific factual retrieval under the production
evaluation is essentially absent for all architectures, which does not establish
that the recurrent state lacks the information. As retrieval becomes unreliable,
the AHN variants predominantly abstain while the control much more often emits
unsupported or malformed output — a difference in failure mode, described
behaviourally. Evaluations of compressed-memory systems should characterize not
only how long retrieval succeeds but what degrades and how systems behave once it
fails.
