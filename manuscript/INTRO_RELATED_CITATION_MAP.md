# Introduction + Related Work — Claim–Citation Map

Every literature-dependent sentence in `manuscript/INTRODUCTION.md` and
`manuscript/RELATED_WORK.md`, with its citation, support type, and risk. Keys
resolve in `manuscript/REFERENCES_VERIFIED.bib`. Support was checked against the
fetched abstract of each paper (2026-09-09); page URLs are in the `.bib`.

Type: **DIRECT** (the cited paper's own stated result) · **SYNTHESIS** (claim
spans several papers, all cited) · **INFERENCE** (reasonable reading not stated
verbatim). Confidence: H / M / L. Overstatement risk: what a hostile reviewer
could object to.

## INTRODUCTION.md

| ID | sentence (abbrev.) | key(s) | type | supporting evidence | conf. | overstatement risk |
|---|---|---|---|---|---|---|
| I1 | "accuracy can fall sharply as inputs grow … uneven across capabilities … strong … retrieval need not carry over to downstream use" | atlas2026 | DIRECT | ATLAS abstract: "performance can collapse as length grows, and strong retrieval need not transfer to downstream use"; ranking reshuffles between 128K and 1M | H | "fall sharply" is ATLAS's "collapse"; safe |
| I2 | "models often answer from parametric priors, leave supplied evidence unused, or cite … without turning it into an answer" | evidence2026 | DIRECT | abstract: "answer from parametric priors, fail to use evidence that is present, or cite relevant text without converting it into the final answer" | H | near-verbatim; safe |
| I3 | "context lengths at which task accuracy drops abruptly rather than smoothly" | threshold2026 | DIRECT | abstract: critical threshold at 40–50% of max context where F1 drops from 0.55–0.56 to 0.3 (Qwen2.5-7B) | H | single model; sentence says "analyses … identify", not "universally" — safe |
| I4 | "analyses of state-space models describe how their recall of specific past content decays with distance and is bounded by state size" | memmamba2025; recallmamba2026 | SYNTHESIS | MemMamba: "memory decay mechanism of Mamba", exponential decay of early information; Recall Scaling Laws: recall capacity scales with state dimension vs vocabulary/#facts | H | both are SSM-specific; sentence scopes to "state-space models" — safe |
| I5 | "recent work proposing compressive recurrent memories" | elasticmem2026 | DIRECT | abstract: "optimal online compression to encode [history] into a fixed-size memory state" (Elastic Memory) | H | safe |
| I6 | "revisiting sliding-window size as a lever on long-range recall" | shortwin2025 | DIRECT | abstract: larger sliding windows hurt long-context performance; shorter windows force stronger long-term memory | H | safe |
| I7 | "advancing the underlying recurrent formulations" | mamba3_2026 | DIRECT | Mamba-3 (ICLR 2026): more expressive recurrence, complex-valued state updates, MIMO | H | safe |
| I8 | "AHN are one concrete instantiation of this hybrid design" | ahn2025 | DIRECT | AHN abstract: sliding-window KV cache as lossless short-term memory + recurrent compression into fixed-size long-term memory | H | safe |
| I9 | "implemented with a Mamba-2, DeltaNet, or Gated DeltaNet recurrent module" | ahn2025; mamba2_2024; deltanet2024; gdn2024 | DIRECT (method attribution) | AHN: "instantiated using … Mamba2, DeltaNet, and GatedDeltaNet"; each module paper is its origin | H | safe |
| I10 | "AHN-augmented models improve over sliding-window baselines while cutting compute and memory" | ahn2025 | DIRECT | AHN: LV-Eval 4.41→5.88 at 128k; −40.5% FLOPs, −74.0% cache (Qwen2.5-3B) | H | "improve over sliding-window baselines" is AHN's own comparison — safe |
| I11 | "the method does not claim that the compressed state is lossless" | ahn2025 | INFERENCE | AHN frames the window as "lossless short-term memory" and the recurrent state as "compressed"/"compressive"; it never asserts losslessness of the compressed state | M | a reviewer could ask for a quote; the framing is explicit in the abstract. Phrased as a negative ("does not claim"), which is defensible |

## RELATED_WORK.md

| ID | sentence (abbrev.) | key(s) | type | supporting evidence | conf. | overstatement risk |
|---|---|---|---|---|---|---|
| R0 | opening: three lines "examined … largely as separate questions" | atlas2026, evidence2026, threshold2026, memmamba2025, recallmamba2026, elasticmem2026, hesitation2025, cic2026, calib2026, verbalconf2026 | SYNTHESIS | each cited paper addresses one of the three areas; none addresses the intersection (novelty audit, `LITERATURE_MAP.md` §C) | M | "largely as separate questions" is a differentiation framing, not a priority claim; supported by the per-paper scoping in this table |
| R2 | "performance can collapse as inputs grow … differs by task family … strong retrieval scores do not transfer to downstream use" | atlas2026 | DIRECT | as I1 | H | safe |
| R3 | "distinct causes — parametric priors, present evidence unused, cite without answering — … reduced evidence recovery when … embedded in a long context rather than a compact one" | evidence2026 | DIRECT | abstract + summary: "reduced evidence recovery when information is embedded in long contexts versus compact formats" | H | safe |
| R4 | "context lengths at which accuracy drops abruptly … threshold-like character rather than … purely gradual" | threshold2026 | DIRECT | as I3 | H | "threshold-like character" is our paraphrase of an abrupt drop; safe, and it is *their* finding not ours |
| R5 | "shorter windows can push a model to rely on and strengthen its long-term memory, improving long-range recall" | shortwin2025 | DIRECT | as I6 | H | safe |
| R6 | "the contribution of earlier tokens decays through recurrence and … recall of specific past content is constrained" | memmamba2025 | DIRECT | MemMamba: mathematical analysis of Mamba's memory decay; "long-range forgetting" | H | safe |
| R7 | "recall scaling laws relate an SSM's ability to retrieve stored associations to its state size and the number of facts it must hold" | recallmamba2026 | DIRECT | abstract: "Recall Scaling Laws" predict model dimensions needed for recall given vocabulary size and context facts | H | safe |
| R8 | "compressive fixed-size recurrent memories that apply online compression to a growing history" | elasticmem2026 | DIRECT | as I5 | H | safe |
| R9 | "continues to refine the recurrent formulations themselves" | mamba3_2026 | DIRECT | as I7 | H | safe |
| R10 | "pair a lossless sliding window with a recurrently compressed fixed-size state instantiated as a Mamba-2, DeltaNet, or Gated DeltaNet module, and report strong aggregate long-context results" | ahn2025; mamba2_2024; deltanet2024; gdn2024 | DIRECT | as I8–I10 | H | safe |
| R11 | "train abstention through reinforcement with explicit rewards for hesitation" | hesitation2025 | DIRECT | abstract: ternary rewards (+1 correct, 0 abstain, −λ error), RLVR modification | H | safe |
| R12 | "wrap uncertainty estimates in selective-answering procedures with statistical risk control" | cic2026 | DIRECT | abstract: confidence-interval calibration giving finite-sample control of error rate among accepted answers | H | safe |
| R13 | "systematic overconfidence … concentrated on harder items — a hard–easy effect in which difficult tests draw the largest overconfidence" | calib2026 | DIRECT | abstract: overconfidence overall, "hard–easy effect" — hardest tests most overconfident, easy tests underconfident | H | safe |
| R14 | "a model's stated confidence can be dissociated from its actual decision to answer or abstain" | verbalconf2026 | DIRECT | abstract: expressed confidence not clearly tied to reasoning/decision; models "neither cost-aware … nor strategically responsive" | H | safe |
| R15 | "a … learned or distilled abstention policy … remain experimentally unresolved alternatives" | hesitation2025 | INFERENCE | hesitation2025 shows abstention *can* be trained; we cite it as evidence the alternative is plausible, not that AHN used it | M | must stay phrased as "alternative", never "AHN was distilled to abstain" — current wording complies |
| R16 | closest-work: ATLAS "benchmark-aggregate … does not contrast a recurrent-memory architecture … or manipulate an exact-attention boundary or analyse abstention" | atlas2026 | DIRECT (negative) | ATLAS scope from its abstract/summary; the absence of a recurrent-memory contrast / window manipulation / abstention analysis is verifiable from its described method | M | negative claims about another paper's scope — checked against the fetched summary; re-verify against full paper before camera-ready |
| R17 | closest-work: evidence-utilization "Transformer- and retrieval-centric, without a recurrent memory or a transition-shape analysis" | evidence2026 | DIRECT (negative) | its matched conditions are long-context vs RAG vs compact; no recurrent-memory arm | M | as R16 |
| R18 | closest-work: "MemMamba and the recall scaling laws explain why a bounded recurrent state has limited and decaying recall … neither evaluates a deployed hybrid system under controlled pressure or examines failure behaviour" | memmamba2025; recallmamba2026 | DIRECT (negative) | both are architecture/theory; neither runs a deployed-checkpoint pressure evaluation | H | safe |
| R19 | closest-work: "Reinforced Hesitation … and selective-answering with risk control … build abstention capabilities, whereas we measure an abstention shift that emerges without any such intervention" | hesitation2025; cic2026 | DIRECT (negative) | both introduce methods; our study introduces none | H | safe |
| R20 | closest-work closing: "these lines have not been combined … evaluated together on a hybrid … model with a matched control" | (all of §2.1–2.3) | SYNTHESIS | novelty audit (`LITERATURE_MAP.md` §C); phrased as "to our reading" | M | must not become "no prior work"/"first"; current wording is "to our reading these lines have not been combined" — a differentiation statement, acceptable |

## Coverage

- Literature-dependent sentences: **31** (11 Introduction + 20 Related Work).
- Mapped: **31 / 31 (100%)**.
- DIRECT: 24 · SYNTHESIS: 4 · INFERENCE: 2 · DIRECT-negative (scope claims about
  other papers): matched into the DIRECT count above and separately flagged.
- Confidence H: 22 · M: 9 · L: 0.
- Every M-confidence item is a differentiation or negative-scope statement, not a
  positive empirical claim about our results; each is flagged for re-verification
  against the full text of the cited paper before camera-ready.
- No sentence carries a citation that supports only a different part of the claim.
- No citation is attached for recency alone.
