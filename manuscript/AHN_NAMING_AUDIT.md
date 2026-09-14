# AHN Naming Audit (Teammate Feedback Item 1)

**Feedback:** "Abstract/References use 'Artificial Hippocampus Networks'; Methods
allegedly uses 'Adaptive Hybrid Neural'; old research proposal uses 'Adaptive
Hybrid Neural Memory'."

**Verdict: VALID.** Two real inconsistencies found and fixed; one historical
(pre-manuscript) naming correctly identified as out of scope.

## Canonical manuscript-facing term

**Artificial Hippocampus Networks (AHN)** — this is the term used by the
system's own paper \citep{ahn2025} (`manuscript/REFERENCES_VERIFIED.bib`,
key `ahn2025`, title "Artificial Hippocampus Networks for Efficient
Long-Context Modeling"). It is the correct expansion and is now used
consistently everywhere AHN is first expanded.

## Every manuscript-facing occurrence of an AHN expansion (before this pass)

| file | line (pre-fix) | text | correct? |
|---|---|---|---|
| `manuscript/ABSTRACT.md` | 6 | "…in Artificial Hippocampus Networks (AHN), comparing…" | ✅ correct |
| `manuscript/INTRODUCTION.md` | 27 | "Artificial Hippocampus Networks (AHN) are one concrete instantiation…" | ✅ correct |
| `manuscript/RELATED_WORK.md` | 38 | "…Artificial Hippocampus Networks, the system we study, pair…" | ✅ correct |
| `manuscript/METHODS.md` | 16 | "…three **Adaptive Hybrid Neural (AHN)** architectures…" | ❌ **wrong expansion — fixed** |
| `manuscript/METHODS_EXTENDED.md` | 25 | "We study how retrieval from an **Adaptive Hybrid Neural (AHN)** recurrent memory…" | ❌ **wrong expansion — fixed** |
| `manuscript/RESULTS.md`, `DISCUSSION.md`, `CONCLUSION.md` | — | use the bare acronym "AHN" only (no re-expansion) | ✅ correct (expansion given once, upstream) |
| `paper_site/build.py` (`PAPER_TITLE` constant, used as the page `<title>` and `<h1>`) | 44 | "…Uncertainty Signalling in **Adaptive Hybrid Neural Memory**" | ❌ **wrong expansion, most prominent occurrence — fixed** |

## Fixes applied (naming-consistency edits, Edit Policy category A)

1. `manuscript/METHODS.md` — "three Adaptive Hybrid Neural (AHN) architectures"
   → "three Artificial Hippocampus Network (AHN) architectures".
2. `manuscript/METHODS_EXTENDED.md` — "an Adaptive Hybrid Neural (AHN) recurrent
   memory" → "an Artificial Hippocampus Network (AHN) recurrent memory".
3. `paper_site/build.py` — the site's `PAPER_TITLE` (rendered as the page
   `<title>` and the visible `<h1>`) said "…in Adaptive Hybrid Neural Memory";
   changed to "…in Artificial Hippocampus Networks". This was the single most
   visible instance of the error (page title + main heading of the team review
   page) and is regenerated into `paper_site/index.html` in this pass.

No other manuscript-facing file expands AHN incorrectly. `manuscript/
REFERENCES_VERIFIED.bib` correctly carries the AHN paper's own title.

## Historical / out-of-scope terminology (not fixed, correctly separated)

`README.md` (repository root, an early project-proposal document, not a
manuscript file) still reads: *"Characterizing Information Degradation and
Confidence Calibration in Adaptive Hybrid Neural Memory (AHN)"*. This is the
**original research-proposal title**, predating both the AHN system's own
released name and the study's final framing (it also says "Confidence
Calibration," which the final manuscript reframes as "Behavioural Uncertainty
Signalling" — a separate, already-resolved naming evolution, not part of this
feedback item). `README.md` is explicitly out of scope for a manuscript-facing
naming standardization: it documents the project's history, not the paper, and
rewriting it is a documentation-maintenance decision for the team, not a
manuscript edit. **Left unchanged; flagged here for team awareness.**

## Internal code identifiers (not renamed, per instruction)

The repository's Python package is `src/ahnexp/` and config keys such as
`ahn_position` are internal identifiers unrelated to the manuscript's prose
naming. Per instruction ("Do NOT rename internal code identifiers unless
necessary"), these are untouched — nothing in the naming inconsistency requires
a code rename.

## Resolution

**Classification: B (wording/consistency fix).** Applied. Manuscript-facing
terminology is now uniformly "Artificial Hippocampus Networks (AHN)" at every
point of first expansion (Abstract, Introduction, Related Work, Methods,
Methods Extended) and the bare acronym elsewhere. The team page title is
corrected. `README.md`'s old-proposal title is noted but intentionally left to
the team's discretion.
