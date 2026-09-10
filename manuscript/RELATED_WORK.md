# Related Work

Recent work has examined long-context utilization and degradation,
recurrent-memory capacity, and abstention or calibration under difficulty largely
as separate questions. This study connects them in a hybrid exact/compressed-memory
system, characterizing what degrades, how the transition unfolds around the
exact-attention window, and how output behaviour changes as retrieval becomes
unreliable.

**Long-context utilization and degradation.** A large nominal window does not
imply uniform or reliable use of the information it holds. Length-scaled
benchmarking across many models finds that performance can collapse as inputs
grow, that the decline differs by task family, and that strong retrieval scores do
not transfer to downstream use \citep{atlas2026}. Matched-condition diagnosis
attributes long-context and retrieval-augmented failures to distinct causes —
answering from parametric priors, leaving present evidence unused, citing without
answering — and reports lower evidence recovery when the same evidence is embedded
in a long context rather than a compact one \citep{evidence2026}. Length-distribution
analyses identify context lengths at which accuracy drops abruptly
\citep{threshold2026}, and within hybrid architectures a shorter exact window can
strengthen a model's reliance on its long-term memory and improve long-range
recall \citep{shortwin2025}. These studies characterize degradation as a function
of context length, evidence placement, evidence use, or task category, mostly at
the level of aggregate scores. We instead manipulate memory pressure directly
around a hybrid architecture, holding the exact window fixed and moving the query
target across it, and resolve degradation by information type and failure mode.
Our residual in-window failures show that deterioration already begins while the
target is still exact-attention eligible, so we treat the pressure axis as related
to but not identical with a lossless-to-compressed switch.

**Recurrent and compressed memory.** Mechanistic and mathematical analyses of
state-space models describe how the contribution of earlier tokens decays through
recurrence and how recall of specific past content is constrained
\citep{memmamba2025}, and recall scaling laws relate an SSM's ability to retrieve
stored associations to its state size and the number of facts it holds
\citep{recallmamba2026}. Architecturally, recent work proposes compressive
fixed-size recurrent memories \citep{elasticmem2026} and refines the recurrent
formulations \citep{mamba3_2026}. Artificial Hippocampus Networks, the system we
study, pair an exact sliding-attention window with a recurrently compressed
fixed-size state instantiated as a Mamba-2 \citep{mamba2_2024}, DeltaNet
\citep{deltanet2024}, or Gated DeltaNet \citep{gdn2024} module, and report strong
aggregate long-context results \citep{ahn2025}. We do not propose a memory architecture; we characterize
how retrieval fails in an existing one, keeping architectural memory capacity
distinct from production-level target retrieval. Capacity analyses
\citep{memmamba2025,recallmamba2026} help interpret our deep-recurrent negative
result, but we do not present that result as evidence about the recurrent state's
contents.

**Uncertainty, abstention, and failure behaviour.** Methods have been proposed to
train abstention through reinforcement with rewards for hesitation
\citep{hesitation2025} and to wrap uncertainty estimates in selective-answering
procedures with statistical risk control \citep{cic2026}. Calibration studies find
systematic overconfidence concentrated on harder items \citep{calib2026}, and work
on verbalized confidence finds a model's stated confidence can be dissociated from
its decision to answer or abstain \citep{verbalconf2026}. We introduce no
abstention or calibration method; we observe how a model's spontaneous failure
behaviour changes as controlled memory pressure increases, comparing an AHN with a
matched no-recurrent-memory control. Because the control has no recurrent module,
this contrast confounds a recurrent state with the AHN training and distillation
recipe, so a recurrent-state signal and a learned abstention policy
\citep{hesitation2025} remain experimentally unresolved.

**Closest work.** ATLAS \citep{atlas2026} establishes task-specific long-context
decay and that retrieval need not transfer downstream, but at the benchmark
aggregate level, without a recurrent-memory contrast, an exact-attention boundary,
or an abstention analysis. The evidence-utilization diagnosis \citep{evidence2026}
shares our matched-condition methodology and outcome decomposition but is
Transformer- and retrieval-centric, with no recurrent memory or transition-shape
analysis. MemMamba \citep{memmamba2025} and the recall scaling laws
\citep{recallmamba2026} explain why a bounded recurrent state has limited,
decaying recall — which we use to interpret, not mechanistically explain, the
deep-recurrent null — but neither evaluates a deployed hybrid system under
controlled pressure or examines failure behaviour. Reinforced Hesitation
\citep{hesitation2025} and risk-controlled selective answering \citep{cic2026}
build abstention capabilities, whereas we measure an abstention shift that emerges
without any such intervention. This study brings these lines together on one
hybrid model with a matched control.
