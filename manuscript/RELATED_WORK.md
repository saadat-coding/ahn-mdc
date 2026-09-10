# Related Work

Recent work has examined long-context utilization and degradation,
recurrent-memory capacity, and abstention or uncertainty under difficulty
largely as separate questions. We study their intersection in a hybrid
exact/compressed-memory system by characterizing what degrades, how the
performance transition unfolds around the architectural memory boundary, and how
output behaviour changes as retrieval becomes unreliable.

## 2.1 Long-context utilization and degradation

A consistent recent finding is that a large nominal context window does not
imply uniform or reliable use of the information it holds. Length-scaled
benchmarking across many models reports that performance can collapse as inputs
grow, that the decline differs by task family, and that strong retrieval scores
do not transfer to downstream use of the retrieved content [CITE:atlas2026].
Matched-condition diagnosis attributes long-context and retrieval-augmented
failures to distinct causes — answering from parametric priors, leaving present
evidence unused, or citing without answering — and shows reduced evidence
recovery when the same evidence is embedded in a long context rather than a
compact one [CITE:evidence2026]. Analyses of natural length distributions
identify context lengths at which accuracy drops abruptly, framing degradation as
having a threshold-like character rather than being purely gradual
[CITE:threshold2026]. Within hybrid architectures, the size of the exact
sliding window is itself a lever: shorter windows can push a model to rely on and
strengthen its long-term memory, improving long-range recall [CITE:shortwin2025].

These studies characterize degradation as a function of context length,
evidence placement, evidence use, or task category, typically at the level of
aggregate scores. Our experiment instead manipulates memory pressure directly
around a hybrid exact/recurrent-memory architecture, holding the exact window
fixed and moving the query target across it, and resolves the resulting
degradation by information type and by failure mode. We treat ordinary
long-context degradation and the exact-to-compressed transition as related but
not identical: our residual in-window failures show that performance already
deteriorates while the target is nominally inside the exact window, so we do not
equate the pressure axis with a clean switch from lossless to compressed memory.

## 2.2 Recurrent and compressed memory

A second line of work concerns the capacity and decay of bounded recurrent
state. Mechanistic and mathematical analyses of state-space models describe how
the contribution of earlier tokens decays through recurrence and how recall of
specific past content is constrained [CITE:memmamba2025], and recall scaling laws
relate an SSM's ability to retrieve stored associations to its state size and the
number of facts it must hold [CITE:recallmamba2026]. Architecturally, recent work
proposes compressive fixed-size recurrent memories that apply online compression
to a growing history [CITE:elasticmem2026] and continues to refine the recurrent
formulations themselves [CITE:mamba3_2026]. Artificial Hippocampus Networks,
the system we study, sit in this space: they pair a lossless sliding window with a
recurrently compressed fixed-size state instantiated as a Mamba-2
[CITE:mamba2_2024], DeltaNet [CITE:deltanet2024], or Gated DeltaNet
[CITE:gdn2024] module, and report strong aggregate long-context results
[CITE:ahn2025].

We do not propose a memory architecture. We characterize how retrieval fails in
an existing hybrid system as its query target is driven out of exact attention.
A key distinction we maintain is between theoretical or architectural memory
capacity and production-level target retrieval. Capacity analyses
[CITE:memmamba2025][CITE:recallmamba2026] help interpret our deep-recurrent
negative result — no measurable target-specific factual retrieval under the
production evaluation past roughly twice the window — but we do not present that
result as evidence about the recurrent state's contents: a production failure is
consistent with information that is present in the state yet not recoverable by
greedy generation from our prompt.

## 2.3 Uncertainty, abstention, and failure behaviour

A third line of work asks whether language models can decline to answer when
they should. Methods have been proposed to train abstention through reinforcement
with explicit rewards for hesitation [CITE:hesitation2025] and to wrap
uncertainty estimates in selective-answering procedures with statistical risk
control [CITE:cic2026]. Calibration studies find systematic overconfidence that
is concentrated on harder items — a hard–easy effect in which difficult tests
draw the largest overconfidence [CITE:calib2026] — and work on verbalized
confidence finds that a model's stated confidence can be dissociated from its
actual decision to answer or abstain [CITE:verbalconf2026].

We do not introduce an abstention method or a calibration technique. We observe
how a model's spontaneous failure behaviour — the mix of correct answers,
incorrect answers, abstentions, and malformed output — changes as controlled
memory pressure increases, and we compare that behaviour between an AHN and a
matched no-recurrent-memory control. Our finding that the AHN arms shift
predominantly toward abstention as retrieval becomes unreliable is described as
behavioural uncertainty signalling. Because the control has no recurrent module,
this contrast confounds the presence of a recurrent state with the AHN training
and distillation recipe; a signal carried in the recurrent state and a
learned or distilled abstention policy [CITE:hesitation2025] remain
experimentally unresolved alternatives, and the hard–easy calibration pattern
[CITE:calib2026] is why we treat the small population of past-window answers as
badly calibrated without making calibration a headline claim.

## 2.4 Closest work

The nearest neighbours to this study are ATLAS [CITE:atlas2026] and the
evidence-utilization diagnosis of [CITE:evidence2026] on the degradation side,
and MemMamba [CITE:memmamba2025] and Mamba recall scaling laws
[CITE:recallmamba2026] on the memory side. ATLAS establishes that long-context
performance is task-specific and that retrieval need not transfer downstream, but
it operates at the benchmark-aggregate level, does not contrast a
recurrent-memory architecture with a matched control, and does not manipulate an
exact-attention boundary or analyse abstention. The evidence-utilization work
shares our matched-condition methodology and outcome-decomposition spirit but is
Transformer- and retrieval-centric, without a recurrent memory or a
transition-shape analysis. MemMamba and the recall scaling laws explain why a
bounded recurrent state has limited and decaying recall, which we use to
interpret — not to mechanistically explain — the deep-recurrent negative result;
neither evaluates a deployed hybrid system under controlled pressure or examines
failure behaviour. On abstention, Reinforced Hesitation [CITE:hesitation2025] and
selective-answering with risk control [CITE:cic2026] build abstention
capabilities, whereas we measure an abstention shift that emerges without any
such intervention. This study brings these lines together:
information-type-resolved degradation, a transition characterization that
separates the architectural window from the empirical knee, and behavioural
uncertainty signalling, evaluated together on a hybrid exact/compressed-memory
model with a matched control.
