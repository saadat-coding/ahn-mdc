# Team Paper Page — Audit

A static internal review page (`paper_site/`) was built as a presentation layer
over the current manuscript. No scientific content was modified, no experiments or
analyses were run, and nothing was deployed.

## Provenance

| | |
|---|---|
| Source manuscript commit | `48af0bc` (`saadat-pipeline-validation`) — the compressed Methods–Conclusion draft |
| Website commit | this commit on `saadat-pipeline-validation` (adds `paper_site/` + this audit) |
| Page generator | `paper_site/build.py` (Python 3 stdlib only); reads `manuscript/*.md`, `manuscript/REFERENCES_VERIFIED.bib`, `outputs/publication_exhibits/main/` |
| Page stamps | draft version `48af0bc`, branch `saadat-pipeline-validation`, build date 2026-09-09 |
| `main` | untouched |

## Sections represented

| page section | source |
|---|---|
| Hero + draft badge + "Review this draft" | generated; commit + date + review questions |
| Overview / TL;DR | written from the manuscript (no new claims) |
| What / When / How | written from the manuscript |
| Key findings (4 cards) | F1–F4, values verbatim from `RESULTS_TRACEABILITY.md` |
| Experiment at a glance | architectures, 5 information types, 240 items, 8 seeds, 12 targets, 92,160 trials, W = 256, W ≠ K note |
| Figures | Figure D, 1, 2, 3 (PNG inline + PNG/SVG links) with manuscript-based explanations |
| Results snapshot | primary (frozen v1.0) vs secondary/post-freeze (v1.1) split, badged |
| Full paper | Abstract, Introduction, Related Work, Methods, Results (+ 5 result tables), Discussion, Conclusion — rendered verbatim from `manuscript/*.md` |
| Limitations | extracted verbatim from Discussion §4.6 |
| References | all 17 entries from `REFERENCES_VERIFIED.bib`, arXiv/DOI/proceedings links |
| Draft information panel | branch, full + short commit, build date, scientific status, trial count, "not a submission" |

All 7 manuscript sections + Limitations + References are present. Section
numbering follows the manuscript (2.1–2.6, 3.1–3.6, 4.1–4.7).

## Figures represented

| figure | file | on page |
|---|---|---|
| Figure D — experimental design | `figD_experimental_design.{png,svg}` | yes (inline PNG, links to PNG/SVG) |
| Figure 1 — H1 non-uniform degradation | `fig1_h1_nonuniform_degradation.{png,svg}` | yes |
| Figure 2 — H2 architecture curves, W and K | `fig2_h2_architecture_curves.{png,svg}` | yes |
| Figure 3 — H3 behavioural uncertainty signalling | `fig3_h3_behavioural_signalling.{png,svg}` | yes |

The 4 main figures are the frozen publication exhibits, copied byte-for-byte into
`paper_site/figures/`. The 6 appendix exhibits are not shown (they are referenced
by name in the rendered Results text and appendices). Figure explanations on the
page are drawn from the current manuscript, not from the older `CAPTIONS.md`
wording.

## Numerical claims checked (page vs manuscript / traceability)

| claim | manuscript | page | match |
|---|---|---|---|
| Total trials | 92,160 | 92,160 | ✔ |
| AHN − control transition-region gap | +0.249 | +0.249 | ✔ |
| Gap 95% CI | [0.233, 0.266] | [0.233, 0.266] | ✔ |
| H1 omnibus p | 5×10⁻⁴ (0/2000) | 5×10⁻⁴ | ✔ |
| A_transition by type | 0.255 / 0.307 / 0.389 / 0.520 / 0.594 | same | ✔ |
| K (strict) | 208.3 / 218.4 / 219.6 / 240.0 | same | ✔ |
| W | 256 | 256 | ✔ |
| Post-freeze median widths | 32.4 (control), 61.8 / 71.4 / 73.8 (AHN) | same | ✔ |
| Deep-recurrent correct counts | 0 / 0 / 1 / 3 of 3,542 | same | ✔ |
| Wilson 95% upper bounds | ≤ 0.0025 | ≤ 0.0025 (table shows 0.00108 / 0.0016 / 0.00249) | ✔ |
| H3 appropriate-abstention (AHN vs control) | 0.929–0.946 vs 0.516 | same | ✔ |
| H3 unsignalled-failure (AHN vs control) | 0.052–0.071 vs 0.480 | same | ✔ |
| H3 contrast effect / p | ≈ 0.42, Holm p < 0.001, seed-stable | same | ✔ |
| Residual in-window failure | ≈ 32% (32.1%) | ≈ 32% / 32.1% | ✔ |
| Table 2 Holm p = 0.0 cells | reported as "< 0.001" in prose | table cells rendered "< 0.001" with a footnote that the frozen value is 0.0 | ✔ (representation, not value) |

**No numerical value on the page differs from the manuscript / traceability
table.** The only transformations are (a) "< 0.001" for frozen `p = 0.0` bootstrap
cells (with an explicit footnote), matching the manuscript's own convention, and
(b) a thousands separator added to the raw `n` in Table 5.

## Scientific wording differences (page vs manuscript)

The page uses the **current manuscript** terminology, which differs from the older
exhibit `.md` files it also draws on:

| exhibit source wording | page wording | reason |
|---|---|---|
| "fact type" / `fact_type_internal` | "information type" | manuscript standardization (compression pass) |
| internal key `multi-hop` shown in table rows | "compound-relational" | manuscript-facing term; the data-key note is kept in the rendered Methods |
| "threshold-like (ΔAIC …)" | "change-point favoured (ΔAIC …)" | matches the manuscript's reframed H2 wording |
| "p ≈ 0" | "p < 0.001" | matches the manuscript's p-value convention |
| "Transformer (no AHN)" | "Transformer control" | consistent label |

No page summary is **stronger** than the manuscript. Checked explicitly:
- deep-recurrent result carries the approved sentence verbatim **and** the
  "does not establish that the recurrent state lacks the information" caveat;
- H3 is labelled "behavioural uncertainty signalling" with "a description of what
  the model emits, not evidence of an internal mechanism"; no "knows" / "self-aware";
- the H2 transition-width characterization is badged **post-freeze v1.1** and
  described as "not a pre-registered primary analysis" in three places;
- W ≠ K is stated in the experiment panel, the TL;DR, and the rendered Results;
  K is explicitly "not a compression threshold and not the point where
  compression begins".

## Link / asset check

- Internal anchors: 0 unresolved (nav, TOC, finding cards, figure "Results →"
  links, and all 47 in-text citation links resolve).
- Duplicate element ids: 0.
- Figures: all 4 PNGs serve (HTTP 200, `image/png`); SVG links serve.
- External reference links: 17/17 (arXiv abstract pages, one NeurIPS proceedings
  page); all taken from the verified `.bib`, none invented.
- No mixed content, no external scripts/fonts/CDNs (fully self-contained;
  system-font stack).

## Responsive / rendering status

| | status |
|---|---|
| Desktop (1280px) | PASS — no horizontal overflow; sticky TOC appears ≥ 1000px; figures and tables full width |
| Mobile (375px) | PASS — no horizontal document overflow; hero, badges, finding cards, experiment panel stack; result tables scroll horizontally inside their own container |
| Print | CSS `@media print` hides the draft bar / nav / review box / TOC / back-to-top and de-colours links |
| No-JS | PASS — page is fully readable; JS only adds TOC active-section highlighting |
| Special characters | diacritics in author names render (Loïc Cabannes, Pierre-Emmanuel Mazaré, Hervé Jégou); ≈ ≠ ≥ ≤ → ± Δ render as HTML entities |
| Math notation | the manuscript uses prose/ASCII math only (no LaTeX in the body); no MathJax needed |

## Deployment recommendation

**Do not deploy publicly.** Build and view locally, or share by one of the
private options in `paper_site/README.md`. Recommended:

1. **`python3 -m http.server` during a team call / screen-share**, or **zip
   `paper_site/` and share the folder** — nothing leaves a trusted machine.
2. If a single shareable URL is wanted: a **private Claude Artifact**
   (default-private, link shared only with named teammates, `noindex`), or a
   **password / access-gated** Netlify/Vercel/Cloudflare Pages deploy.
3. **Not GitHub Pages** — GitHub Pages is publicly served even from a private
   repository, and there is no per-viewer access control on the free/Pro tiers.

If the team later publishes a **non-anonymous preprint** (permitted by current
ARR policy, below), a public version of this page could accompany it — but that
is a separate, deliberate decision, not this task.

## ARR / NAACL anonymity risk assessment

Checked against the current ACL Rolling Review anonymity policy
(<https://aclrollingreview.org/anonymity/>, effective February 2024, still current
Sept 2026) and the ACL author guidelines.

**Policy facts:**
- There is **no anonymity period**: authors "are free to post and discuss
  non-anonymous preprints at any time" while a paper is under review.
- The **submission itself** must be anonymized: no author names/affiliations, no
  identifying self-references, and **no links to file hosts that can track
  downloads** (Dropbox etc.); supplementary material and repository links in the
  submission must be anonymized.
- Anonymous submission is **incentivised** (special awards; priority for
  borderline papers). Choosing the binding "no non-anonymous preprint" option
  commits the authors to not preprinting until meta-reviews, on penalty of desk
  rejection.
- Reviewers are instructed not to search for the authors' identity.

**Assessment for this page:**
- The page is an **internal review page, not a preprint**, and carries no author
  names (there is no canonical author list in the repository; the git history
  shows two contributors but the page deliberately withholds authorship). It is
  `noindex`/`noarchive` and served with a disallow-all `robots.txt`.
- Hosting it **publicly with author identities** before/during review would not
  violate the letter of the current policy, **but**:
  - it forfeits the anonymous-submission incentives if the team wants them;
  - it is incompatible with the binding no-preprint option;
  - a public, identifiable, indexed page makes it materially easier for an
    assigned reviewer to deanonymize the work, which undercuts double-blind
    review in spirit even if not in rule;
  - the page must never be used as the submission's supplementary link (it would
    be a non-anonymized, download-observable link).
- **Meaningful anonymity risk exists** for a public identifiable deployment.
  Therefore: **private / access-controlled sharing only**, per the recommendation
  above, until the team makes an explicit, separate decision about a
  non-anonymous preprint.

**Nothing was published or deployed in this task.**
