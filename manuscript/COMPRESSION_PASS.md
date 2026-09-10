# Compression Pass — Log

Main-paper compression + terminology standardization + citation integration.
**Not a scientific revision.** No models run; raw data, frozen v1.0, v1.1,
statistical endpoints, hypothesis statuses, the claims register, and the
publication exhibits were not touched. No claim was strengthened; no negative
result was removed. Baseline commit 8dd2188.

## Word counts

| section | before | after | Δ | target |
|---|---:|---:|---:|---|
| Abstract | 224 | 225 | +1 | 180–220 |
| Introduction | 931 | 802 | −129 | 700–800 |
| Related Work | 995 | 671 | −324 | 650–800 |
| Methods | 1,906 | 1,697 | −209 | 1,300–1,500 |
| Results | 2,078 | 1,814 | −264 | 1,500–1,700 |
| Discussion | 1,687 | 1,410 | −277 | 1,300–1,500 |
| Conclusion | 395 | 319 | −76 | 250–350 |
| **Total** | **8,216** | **6,938** | **−1,278** | 6,500–7,000 |

Reduction: **−1,278 words (−15.6%).** Methods and Results remain modestly above
their per-section guidelines; the total is inside the target and no required
content was cut, so they were not compressed further (task instruction: do not
force below the range at the cost of clarity).

## Citation integration

- `[CITE:key]` / `[CITE ...]` placeholders replaced with `\citep{key}` /
  `\citet{key}` (natbib, the ACL/NAACL convention) against
  `REFERENCES_VERIFIED.bib`. 17/17 bib keys are cited; every cited key resolves.
- `ece2017` (Guo et al., *On Calibration of Modern Neural Networks*, ICML 2017)
  added to the bib and cited once in Methods §2.4 — see §"ECE decision" below.
- `METHODS_EXTENDED.md`: `[CITE AHN paper]` → `\citep{ahn2025}`; `[CITE temporal
  repair note]` → an internal cross-reference to
  `protocol/temporal_repair_validation.md` (an internal record, not a
  publication).

## Terminology standardization

| change | scope |
|---|---|
| "fact type" → **"information type"** (5 benchmark categories) | Abstract, Introduction, Related Work, Methods, Results, Discussion, Conclusion, METHODS_EXTENDED — 0 manuscript-facing "fact type" remain; the code identifier `fact_type` and the data key `multi-hop` are unchanged |
| "arithmetically inside the lossless window" → **"exact-attention eligible"** (VAL-4 residual diagnostic) | Methods, Results, Discussion, Conclusion — same computed subset (34,975 trials), no value change |
| "lossless sliding window" (describing AHN) → "exact sliding-attention window" | Related Work §"Recurrent and compressed memory" |
| standardized on "exact-attention window" for $W$ and "exact attention" for the mechanism | all sections |
| "provably identical" → "multiple equivalence and reproduction checks … found no evidence of a scientifically relevant discrepancy" | Methods §2.6 and METHODS_EXTENDED §2.14 |

`compound-relational` is unchanged and is never called "multi-hop" outside the
data-key note and the explicit disavowals (Introduction, Methods §2.1/§2.2,
Discussion §4.1/§4.6).

## Meaningful cuts and moves (not ordinary copyediting)

| # | source | ~words | tier | action | destination | reason | recoverable? |
|---|---|---:|---|---|---|---|---|
| 1 | Introduction P1–P2 | ~90 | context | condensed | — | overlap with Related Work §2.1–2.2; kept one sentence + citations per point | n/a (RW carries the detail) |
| 2 | Introduction P7 (contributions) | ~40 | T1 framing | condensed | — | three numbered contributions → one dense paragraph, wording preserved | yes (unchanged in substance) |
| 3 | Related Work §2.1–2.3 | ~200 | context | condensed | — | bullet-style multi-sentence per paper → thematic paragraphs; every citation and every differentiation clause kept | n/a |
| 4 | Related Work §2.4 closest-work | ~90 | differentiation | condensed | — | ATLAS/evidence2026/MemMamba/recall-scaling/abstention comparisons tightened to one clause each; all four negative-scope claims retained | n/a |
| 5 | Methods §2.2 prompt/generation | ~50 | reproducibility | condensed | METHODS_EXTENDED §2.5 (already present) | greedy decoding + stop rule kept; template wording detail dropped from main | yes |
| 6 | Methods §2.4 bootstrap/permutation mechanics | ~60 | reproducibility | condensed | METHODS_EXTENDED §2.9–2.11 (already present) | two-level bootstrap + Holm + add-one omnibus kept; per-hypothesis prose tightened | yes |
| 7 | Methods §2.6 construct-check enumeration | ~50 | Tier 2 method | condensed to a pointer | METHODS_EXTENDED §2.13; Results §3.6 | main keeps a one-line list; full procedures in Extended | yes |
| 8 | Results §3.1 [R3]–[R4] | ~40 | Tier 2 | condensed | Table 4 | in-window control numbers partly duplicate Table 4 and Methods | yes (Table 4) |
| 9 | Results §3.2 [R9] per-type answered-valid values | ~35 | Tier 2 | **moved** (values) | Appendix A-H1 | the "2 of 10 contrasts lose significance" claim stays in main text; the five per-type numbers now appendix-only | yes (Appendix A-H1) |
| 10 | Results §3.2 ordering/sensitivity prose | ~70 | Tier 2 | condensed | — | R10/R11/R12 to one sentence each; headline numbers retained | n/a |
| 11 | Results §3.3 knee/shape prose | ~90 | Tier 1/2 | condensed | Table 3 / Appendix A-H2a | K values, ΔAIC, widths all retained; connective prose cut; per-arm abstention-knee detail pointed to Table 3 | yes |
| 12 | Results §3.6 VAL-1…VAL-4 | ~110 | Tier 2 | condensed | Appendices A-VAL, A-H2b | one tight paragraph per VAL; per-seed ranges and subtype detail pointed to appendices; all headline rates kept in main | yes |
| 13 | Discussion §4.1–4.5 | ~180 | interpretation | condensed | — | repeated numbers cut to first mention; W-vs-K restated once; mechanism lists compressed to one sentence | n/a |
| 14 | Discussion §4.7 implications | ~90 | interpretation | condensed | — | five implications + future-work list → two sentences | n/a |
| 15 | Conclusion | ~76 | interpretation | condensed | — | what/when/how merged into two paragraphs; bounding + implication kept | n/a |
| 16 | Discussion | +30 | context | **added** | — | 3 citations wired in (`memmamba2025,recallmamba2026` for the deep-recurrent interpretation; `hesitation2025` for the learned-policy alternative; `calib2026` for the hard–easy calibration point) | n/a |

## ECE decision (task item 14)

Expected calibration error **is** named in Methods §2.4 and computed as a
descriptive calibration metric (reported in Appendix A-H3; the main Results
report `gap_change` and the confidently-wrong rate, not an ECE number). Because
the metric is named in the manuscript, its origin is attributed once:
`\citep{ece2017}` (Guo et al., ICML 2017; verified 2026-09-09). This is
method attribution, not a related-work citation, and is the reviewer-expected
treatment of a named metric. It is the manuscript's only pre-2021 citation
besides the three AHN recurrent-module papers.

## Post-freeze H2 disclosure (task item 15)

Preserved in every section that mentions the width: Abstract ("by an explicitly
post-freeze width characterization"), Introduction ("by a post-freeze width
analysis"), Methods §2.5 (dedicated subsection, "analysis version 1.1 … not a new
frozen primary endpoint"), Results §3.3 [R21]/[R22] ("*Frozen pooled width*" /
"*Post-freeze per-type width characterization*"), Discussion §4.2 ("introduced
*after* the freeze … should not be cited as pre-registered"), Conclusion ("by an
explicitly post-freeze width characterization"). No section presents the per-type
widths as pre-registered.

## Provenance (task item 16)

The runtime-commit gap is disclosed in Methods §2.6 (main) and METHODS_EXTENDED
§2.14 (full), both using the preferred "no evidence of a scientifically relevant
discrepancy" wording. "Provably identical" no longer appears anywhere.
