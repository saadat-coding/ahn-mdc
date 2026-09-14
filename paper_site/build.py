#!/usr/bin/env python3
"""
Build the internal team-review web page for the AHN memory-degradation paper draft.

Presentation layer only. Reads the manuscript Markdown, the verified bibliography,
and the frozen publication exhibits, and emits a single static `index.html`.
It does NOT modify or reinterpret any scientific content.

Usage:
    python3 paper_site/build.py            # from the repo root
    python3 build.py                       # from paper_site/

Output: paper_site/index.html  (+ figures already copied into paper_site/figures/)
"""
from __future__ import annotations
import html
import re
import subprocess
import datetime
import pathlib
import base64
import sys

HERE = pathlib.Path(__file__).resolve().parent
REPO = HERE.parent
MAN = REPO / "manuscript"
EXH = REPO / "outputs" / "publication_exhibits" / "main"

# ---------------------------------------------------------------------------
# repo / draft metadata
# ---------------------------------------------------------------------------
def sh(*args: str) -> str:
    try:
        return subprocess.check_output(args, cwd=REPO, text=True).strip()
    except Exception:
        return ""

COMMIT_SHORT = sh("git", "rev-parse", "--short", "HEAD") or "unknown"
COMMIT_FULL = sh("git", "rev-parse", "HEAD") or "unknown"
BRANCH = sh("git", "rev-parse", "--abbrev-ref", "HEAD") or "unknown"
BUILD_DATE = datetime.date.today().isoformat()

PAPER_TITLE = ("Characterizing Information Degradation and Behavioural "
               "Uncertainty Signalling in Artificial Hippocampus Networks")
PAPER_SUBTITLE = ("A controlled study of what degrades, when it degrades, and how "
                  "failure manifests as a query target is pushed from exact "
                  "attention into a compressed recurrent memory.")

# ---------------------------------------------------------------------------
# bibliography
# ---------------------------------------------------------------------------
def parse_bib(text: str) -> dict:
    entries: dict[str, dict] = {}
    for m in re.finditer(r"@(\w+)\{([^,]+),(.*?)\n\}", text, re.S):
        etype, key, body = m.group(1), m.group(2).strip(), m.group(3)
        fields: dict[str, str] = {"_type": etype}
        for fm in re.finditer(r"(\w+)\s*=\s*\{(.*?)\}\s*,?\s*\n", body, re.S):
            fields[fm.group(1).lower()] = " ".join(fm.group(2).split())
        entries[key] = fields
    return entries


def _deLatex(s: str) -> str:
    s = s.replace('{\\"i}', 'ï').replace("{\\'e}", 'é').replace('{\\"o}', 'ö')
    s = s.replace('{\\"a}', 'ä').replace("{\\'a}", 'á').replace("{\\'o}", 'ó')
    return s.replace("{", "").replace("}", "").strip()


def authors_list(raw: str) -> list[str]:
    return [_deLatex(a.strip()) for a in raw.split(" and ")]


def surname(full: str) -> str:
    full = _deLatex(full)
    return full.split(",")[0].strip() if "," in full else full.split()[-1].strip()


def name_natural(full: str) -> str:
    """'Fang, Yunhao' -> 'Yunhao Fang'; leaves already-natural names alone."""
    full = _deLatex(full)
    if "," in full:
        last, first = [p.strip() for p in full.split(",", 1)]
        return f"{first} {last}".strip()
    return full


def cite_label(key: str, bib: dict) -> str:
    e = bib.get(key)
    if not e:
        return key
    names = authors_list(e.get("author", ""))
    yr = e.get("year", "")
    if len(names) == 1:
        who = surname(names[0])
    elif len(names) == 2:
        who = f"{surname(names[0])} & {surname(names[1])}"
    else:
        who = f"{surname(names[0])} et al."
    return f"{who}, {yr}"


def ref_link(e: dict) -> str:
    if e.get("url", "").startswith("http"):
        return e["url"]
    if e.get("eprint"):
        return f"https://arxiv.org/abs/{e['eprint']}"
    if e.get("doi"):
        return f"https://doi.org/{e['doi']}"
    return ""


def render_references(bib: dict, order: list[str]) -> str:
    rows = []
    for key in order:
        e = bib.get(key)
        if not e:
            continue
        names = [name_natural(n) for n in authors_list(e.get("author", ""))]
        if len(names) > 8:
            auth = ", ".join(names[:8]) + ", et al"
        elif len(names) > 1:
            auth = ", ".join(names[:-1]) + ", and " + names[-1]
        elif names:
            auth = names[0]
        else:
            auth = ""
        title = _deLatex(e.get("title", ""))
        yr = e.get("year", "")
        venue = e.get("booktitle") or ""
        if venue:
            venue = _deLatex(venue)
        elif e.get("eprint"):
            venue = f"arXiv:{e['eprint']}"
        link = ref_link(e)
        meta = " &middot; ".join(x for x in [venue] if x)
        linkhtml = f' <a href="{html.escape(link)}" target="_blank" rel="noopener">link</a>' if link else ""
        rows.append(
            f'<li id="ref-{html.escape(key)}"><span class="ref-auth">{html.escape(auth)}</span>. '
            f'<span class="ref-yr">{html.escape(yr)}</span>. '
            f'<span class="ref-title">{html.escape(title)}</span>. '
            f'<span class="ref-venue">{html.escape(meta)}</span>.{linkhtml}</li>'
        )
    return '<ol class="reflist">\n' + "\n".join(rows) + "\n</ol>"


# ---------------------------------------------------------------------------
# tiny Markdown -> HTML for the manuscript prose (no tables, no lists)
# ---------------------------------------------------------------------------
CITEP = re.compile(r"\\citep\{([^}]+)\}")
CITET = re.compile(r"\\citet\{([^}]+)\}")
RTAG = re.compile(r"\[(R\d+)\]")


def inline(text: str, bib: dict, cited: set) -> str:
    text = html.escape(text)
    # unescape our own markup markers we still need
    text = text.replace("&amp;", "&")  # keep real & rare; safe for this corpus

    def _citep(m):
        keys = [k.strip() for k in m.group(1).split(",")]
        for k in keys:
            cited.add(k)
        parts = [f'<a class="cite" href="#ref-{k}">{html.escape(cite_label(k, bib))}</a>' for k in keys]
        return "(" + "; ".join(parts) + ")"

    def _citet(m):
        k = m.group(1).strip()
        cited.add(k)
        lab = cite_label(k, bib)
        who, yr = lab.rsplit(", ", 1)
        return f'<a class="cite" href="#ref-{k}">{html.escape(who)} ({html.escape(yr)})</a>'

    text = CITEP.sub(_citep, text)
    text = CITET.sub(_citet, text)
    text = RTAG.sub(r'<span class="rtag" title="traceable result identifier">\1</span>', text)
    text = re.sub(r"\*\*(.+?)\*\*", r"<strong>\1</strong>", text)
    text = re.sub(r"(?<![\w*])\*(?!\s)(.+?)(?<!\s)\*(?![\w*])", r"<em>\1</em>", text)
    text = re.sub(r"`([^`]+)`", r"<code>\1</code>", text)
    return text


def md_to_html(md: str, bib: dict, cited: set, drop_h1: bool = True):
    """Return (html_body, first_h1_text)."""
    lines = md.splitlines()
    out: list[str] = []
    para: list[str] = []
    title = ""

    def flush():
        if para:
            out.append("<p>" + inline(" ".join(para), bib, cited) + "</p>")
            para.clear()

    for ln in lines:
        s = ln.rstrip()
        if not s.strip():
            flush()
            continue
        if s.startswith("### "):
            flush()
            out.append(f'<h4>{inline(s[4:], bib, cited)}</h4>')
        elif s.startswith("## "):
            flush()
            htxt = s[3:]
            hm = re.match(r"^3\.\d+\s+H([123])\b", htxt)
            if hm:
                hid = f"results-h{hm.group(1)}"
            else:
                hid = re.sub(r"[^a-z0-9]+", "-", htxt.lower()).strip("-")
            out.append(f'<h3 id="{hid}">{inline(htxt, bib, cited)}</h3>')
        elif s.startswith("# "):
            title = s[2:].strip()
            if not drop_h1:
                out.append(f"<h2>{inline(s[2:], bib, cited)}</h2>")
        else:
            para.append(s.strip())
    flush()
    return "\n".join(out), title


# ---------------------------------------------------------------------------
# exhibit tables -> clean HTML (values verbatim, terminology aligned to manuscript)
# ---------------------------------------------------------------------------
def md_table_to_html(path: pathlib.Path, *, columns: list[int] | None,
                     headers: list[str] | None,
                     rewrite: dict[str, str] | None = None,
                     exact_rewrite: dict[str, str] | None = None,
                     caption: str = "", notes: list[str] | None = None) -> str:
    """rewrite: substring replacements (textual columns only).
    exact_rewrite: applied only when the whole trimmed cell equals a key."""
    raw = path.read_text()
    rows = [r for r in raw.splitlines() if r.strip().startswith("|")]
    grid = [[c.strip() for c in r.strip().strip("|").split("|")] for r in rows]
    grid = [r for r in grid if not all(set(c) <= set("-: ") for c in r)]
    body = grid[1:]
    src_headers = grid[0]
    idx = columns if columns is not None else list(range(len(src_headers)))
    hdr = headers if headers is not None else [src_headers[i] for i in idx]
    notes = notes or []

    def fix(v: str) -> str:
        if exact_rewrite and v in exact_rewrite:
            return exact_rewrite[v]
        if rewrite:
            for a, b in rewrite.items():
                v = v.replace(a, b)
        return v

    thead = "".join(f"<th>{html.escape(h)}</th>" for h in hdr)
    trs = []
    for r in body:
        tds = "".join(f"<td>{html.escape(fix(r[i]))}</td>" for i in idx if i < len(r))
        trs.append(f"<tr>{tds}</tr>")
    notehtml = ""
    if notes:
        notehtml = '<ul class="tbl-notes">' + "".join(f"<li>{html.escape(n)}</li>" for n in notes) + "</ul>"
    return (f'<figure class="tbl"><figcaption>{html.escape(caption)}</figcaption>'
            f'<div class="tbl-scroll"><table><thead><tr>{thead}</tr></thead>'
            f'<tbody>{"".join(trs)}</tbody></table></div>{notehtml}</figure>')


# ---------------------------------------------------------------------------
# static content blocks (written from the manuscript, not reinterpreted)
# ---------------------------------------------------------------------------
TLDR = (
    "AHN keeps recent tokens in an exact-attention window and folds older tokens "
    "into a fixed-size recurrent state. We push a query target out of that window "
    "under controlled memory pressure and ask <em>what</em> degrades, <em>when</em> "
    "it degrades, and <em>how</em> failure manifests, comparing three AHN variants "
    "against a matched Transformer control with no recurrent module across five "
    "information types (92,160 trials). End-to-end task-performance degradation is "
    "strongly information-type dependent. Through the near-window transition the AHN "
    "variants preserve substantially more strict accuracy than the control "
    "(+0.249, 95% CI [0.233, 0.266]); the empirical accuracy knee <em>K</em> sits "
    "below the exact-attention window <em>W</em> for every architecture. At deep "
    "recurrent pressure, measurable target-specific factual retrieval under the "
    "production evaluation is essentially absent for all architectures &mdash; which "
    "does not establish that the recurrent state lacks the information. As retrieval "
    "becomes unreliable the AHN variants predominantly abstain, whereas the control "
    "much more often produces unsupported or malformed output: a difference in "
    "failure mode, described behaviourally."
)

FINDINGS = [
    ("F1", "What degrades",
     "Information-type-dependent degradation",
     "End-to-end task performance falls at different rates for the five information "
     "types. The five-way spread of transition-region accuracy far exceeds "
     "label-permutation chance (omnibus p = 5&times;10<sup>&minus;4</sup>); all ten "
     "pairwise differences have Holm-adjusted intervals that exclude zero. This is a "
     "statement about task performance, not about how much of a stored value "
     "remains in the model's state.",
     "#results-h1"),
    ("F2", "Near-window advantage",
     "+0.249 strict-accuracy advantage over the control",
     "Across the transition interval the three AHN variants retain <strong>+0.249</strong> "
     "more strict accuracy than the matched no-recurrent-memory control "
     "(95% CI <strong>[0.233, 0.266]</strong>; positive in every seed). The AHN "
     "transition occurs later and &mdash; by a post-freeze width characterization &mdash; "
     "is also broader, not simply a rightward shift of the control's sharper collapse.",
     "#results-h2"),
    ("F3", "Deep recurrent retrieval",
     "No measurable target-specific factual retention at depth",
     "At realised pressure &ge; 2W, correct answers are essentially absent "
     "(0, 0, 1, and 3 of 3,542 trials per arm; Wilson 95% upper bounds &le; 0.0025). "
     "<em>No measurable target-specific factual retention was observed at deep "
     "recurrent pressure under the production evaluation.</em> This does not "
     "establish that the recurrent state contains no target information.",
     "#results-h2"),
    ("F4", "How failure changes",
     "A shift toward abstention (behavioural uncertainty signalling)",
     "Past the window, the AHN variants abstain on the large majority of trials and "
     "leave a small fraction of failures unsignalled; the control abstains on "
     "roughly half and fails without signalling on the other half, mostly through "
     "degenerate output (gap &asymp; 0.42 on both rates, seed-stable). We describe "
     "this as <strong>behavioural uncertainty signalling</strong> &mdash; a "
     "description of what the model emits, not evidence of an internal mechanism.",
     "#results-h3"),
]

WWH = [
    ("What degrades?",
     "Loss of end-to-end task performance under memory pressure is information-type "
     "dependent, and the way a failure manifests &mdash; wrong answer, abstention, or "
     "malformed output &mdash; is itself type-dependent. Because the strict production "
     "metric counts abstention and malformed output as failure, this concerns task "
     "performance, not differential decay of stored representations."),
    ("When does performance degrade?",
     "The empirical performance knee <em>K</em> does not coincide with the "
     "architectural exact-attention window <em>W</em> = 256: for every architecture "
     "<em>K</em> &lt; <em>W</em>, and about 32% of trials fail while the target is "
     "still exact-attention eligible. The recurrent path preserves useful "
     "near-window retrieval longer than the control, but its accuracy transition is "
     "also broader (post-freeze width characterization) &mdash; it reshapes the "
     "transition rather than translating a sharp cliff. Past the transition, deep "
     "recurrent pressure yields no measurable sustained factual retrieval for any "
     "architecture."),
    ("How does failure manifest?",
     "Once retrieval becomes unreliable, the dominant observed distinction between "
     "the AHN variants and the control is failure behaviour: the AHN variants "
     "predominantly abstain, while the control much more often produces unsupported "
     "or malformed output. The experiment cannot say whether this reflects a signal "
     "in the recurrent state or a learned abstention policy from the AHN training "
     "and distillation recipe."),
]

REVIEW_QUESTIONS = [
    "Is the central research question (what / when / how) clear from the abstract and intro alone?",
    "Are the WHAT / WHEN / HOW contributions convincing and distinct?",
    "Are any claims overstated relative to the evidence?",
    "Are important recent related works missing (the backbone is Sept 2025 &ndash; Sept 2026)?",
    "Are Figures 1&ndash;3 understandable without reading the full Results?",
    "Is the deep-recurrent negative result framed appropriately (production failure &ne; latent-information absence)?",
    "Is the abstention result clearly behavioural rather than mechanistic?",
    "Is the post-freeze H2 width characterization clearly separated from the frozen analyses?",
    "What would you attack first as a reviewer?",
]

EXPERIMENT = {
    "Architectures": ["Transformer control (no recurrent module)", "AHN-Mamba2",
                      "AHN-DeltaNet", "AHN-GatedDeltaNet"],
    "Information types": ["entity-attribute", "contradictory", "numerical",
                          "temporal", "compound-relational"],
    "Base model": ["Qwen2.5-3B-Instruct"],
    "Grid": ["240 items", "8 seeds", "12 intended pressure targets",
             "4 architectures", "= 92,160 trials"],
    "Exact-attention window": ["W = 256 tokens (forced, verified at load time)"],
}

FIGURES = [
    ("figD_experimental_design", "Figure D &mdash; Experimental design",
     "One tokenised evaluation trajectory (top) and the 12 frozen intended pressure "
     "targets against the realised <code>model_tokens_after_target</code> they "
     "produced (bottom). Pressure is applied by growing a distractor block after the "
     "target; W = 256 is the architectural exact-attention reference. The full grid "
     "is 4 architectures &times; 240 items &times; 12 targets &times; 8 seeds = 92,160 trials.",
     "#methods"),
    ("fig1_h1_nonuniform_degradation", "Figure 1 &mdash; H1: non-uniform degradation",
     "Strict production accuracy versus realised pressure for each information type, "
     "pooled over the three AHN architectures. The y-axis is end-to-end task "
     "accuracy: abstentions and malformed outputs both count as failures. Curves are "
     "raw cell means (no fit). The five-way spread of the transition-region means "
     "exceeds label-permutation chance (p = 5&times;10<sup>&minus;4</sup>). The "
     "ordering is partly metric-dependent (see the answered-valid column of Table 1).",
     "#results-h1"),
    ("fig2_h2_architecture_curves", "Figure 2 &mdash; H2: architecture curves, W and K",
     "Strict accuracy versus realised pressure per architecture (top) and abstention "
     "rate (bottom). The dashed vertical line is the architectural window W = 256; "
     "the markers near the axis floor are the empirical accuracy knee K per "
     "architecture &mdash; a descriptive location, distinct from W, with every K "
     "(208&ndash;240) below W. In the near-window band the AHN architectures retain "
     "+0.25 more accuracy than the control (95% CI [0.23, 0.27]); past W all four "
     "fall to &asymp; 0. The pre-registered pooled transition-width statistic was "
     "undefined for this dataset and is not shown (see the post-freeze amendment).",
     "#results-h2"),
    ("fig3_h3_behavioural_signalling", "Figure 3 &mdash; H3: behavioural uncertainty signalling",
     "Behaviour on trials past W + 16. Left: the four mutually exclusive per-trial "
     "outcomes as stacked fractions &mdash; correct answers are below 1% for every "
     "architecture here, so essentially no architecture retrieves the target past "
     "the window. Right: the two frozen H3 rates per architecture &mdash; appropriate "
     "abstention and unsignalled failure. Each AHN architecture differs from the "
     "control by |&Delta;| &asymp; 0.42 (all six contrasts Holm-adjusted p &lt; 0.001; "
     "identical direction in all 8 seeds). This describes behaviour; it does not "
     "identify an internal mechanism.",
     "#results-h3"),
]

# ---------------------------------------------------------------------------
# assemble
# ---------------------------------------------------------------------------
def main() -> None:
    bib = parse_bib((MAN / "REFERENCES_VERIFIED.bib").read_text())
    cited: set[str] = set()

    sections = {}
    for name, fn in [
        ("Abstract", "ABSTRACT.md"), ("Introduction", "INTRODUCTION.md"),
        ("Related Work", "RELATED_WORK.md"), ("Methods", "METHODS.md"),
        ("Results", "RESULTS.md"), ("Discussion", "DISCUSSION.md"),
        ("Conclusion", "CONCLUSION.md"),
    ]:
        body, _ = md_to_html((MAN / fn).read_text(), bib, cited)
        sections[name] = body

    # limitations: pull the "## 4.6 Limitations" paragraph out of the Discussion md
    disc_md = (MAN / "DISCUSSION.md").read_text()
    m = re.search(r"## 4\.6 Limitations\s*(.+?)\n## ", disc_md, re.S)
    lim_body, _ = md_to_html((m.group(1).strip() if m else ""), bib, cited)
    lim_html = (
        '<p class="muted">Extracted verbatim from Discussion &sect;4.6 of the manuscript.</p>'
        + lim_body
    )

    term_rewrite = {
        "fact_type_internal": "internal key", "multi-hop": "compound-relational",
        "threshold-like (": "change-point favoured (", "p ≈ 0": "p < 0.001",
        "Transformer (no AHN)": "Transformer control",
    }

    tbl1 = md_table_to_html(
        EXH / "tbl1_h1_primary.md",
        columns=[1, 3, 4, 5, 6], headers=["information type", "A_transition (strict)",
        "A_transition (answered-valid)", "in-window control (strict)", "in-window abstention"],
        rewrite=term_rewrite,
        caption="Table 1 — H1 primary result. A_transition = mean strict accuracy over intended "
                "targets 205–265, AHN arms pooled (n = 5,760 per type). Raw strict accuracy is the "
                "frozen primary; the answered-valid column is a pre-registered secondary sensitivity.",
        notes=["Label-permutation omnibus on the dispersion of the five A_transition means: p = 5×10⁻⁴ (0 of 2,000).",
               "No chance correction (Policy A)."])
    tbl2 = md_table_to_html(
        EXH / "tbl2_h1_contrasts.md",
        columns=[0, 1, 2, 3, 4], headers=["type A", "type B", "difference", "95% CI", "Holm p"],
        rewrite={"multi-hop": "compound-relational"},
        exact_rewrite={"0.0": "< 0.001"},
        caption="Table 2 — All ten pairwise A_transition contrasts. Hierarchical (item→seed) "
                "cluster bootstrap, 2,000 resamples; Holm-adjusted over the ten-comparison family. "
                "'Holm p' cells shown as '< 0.001' are recorded as 0.0 in the frozen output "
                "(0 of 2,000 resamples exceeded the observed statistic).",
        notes=["All ten intervals exclude zero; the closest to the boundary is compound-relational vs temporal (Holm p = 0.037).",
               "H1 is supported if at least one Holm-adjusted interval excludes zero (frozen criterion)."])
    tbl3 = md_table_to_html(
        EXH / "tbl3_h2_summary.md",
        columns=[0, 1, 2, 3, 4], headers=["architecture", "K (strict)", "K (abstention)",
        "shape vs smooth (AIC)", "A_recurrent"],
        rewrite={"Transformer (no AHN)": "Transformer control", "threshold-like": "change-point favoured"},
        caption="Table 3 — Per-architecture H2 summary. K is a descriptive empirical knee "
                "(isotonic 0.5-crossing), not a threshold, and is distinct from the architectural "
                "window W = 256; every K < W. Negative ΔAIC favours the change-point (concentrated) fit.",
        notes=["A_transition gap (AHN pooled − control) over [200, 270] = +0.249 [0.233, 0.266] (95% bootstrap CI, excludes 0).",
               "The pre-registered pooled 90→10 transition-width statistic is mathematically undefined for this dataset "
               "(the pooled five-type curve peaks ≈ 0.88, below the 0.90 reference). See the post-freeze reporting amendment; "
               "the frozen 'intermediate' label is not used."])
    tbl4 = md_table_to_html(
        EXH / "tbl4_construct_control.md",
        columns=[0, 4, 5, 6, 7, 8], headers=["information type", "in-window strict",
        "in-window answered-valid", "in-window abstention", "in-window malformed", "control verdict"],
        rewrite={"multi-hop": "compound-relational"},
        caption="Table 4 — Information-type constructs and in-window (control) retrieval, pooled "
                "over intended targets 150 and 180 (n = 3,072 per type).",
        notes=["compound-relational is a single co-located two-clause target — not multi-hop retrieval across separated facts. "
               "Its control retrieval (0.842) triggers a pre-registered WARNING; the FAIL threshold (0.70) is not reached, "
               "so the type is retained in the H1 primary.",
               "temporal is judged on answered-valid accuracy (0.922); its 38% in-window abstention is a documented, "
               "counterbalanced model response bias."])
    tbl5 = md_table_to_html(
        EXH / "tbl5_deep_recurrent.md",
        columns=[0, 2, 3, 4, 6, 7], headers=["architecture", "n", "correct", "strict accuracy",
        "Wilson 95% upper", "abstention rate"],
        rewrite={"Transformer (no AHN)": "Transformer control"},
        exact_rewrite={"3542": "3,542"},
        caption="Table 5 — Deep-recurrent retrieval: realised model_tokens_after_target ≥ 2W (512), "
                "n = 3,542 per architecture. Post-freeze sensitivity (negative result).",
        notes=["Wilson 95% interval on the binomial; all three AHN architectures shown separately.",
               "Approved interpretation: “No measurable target-specific factual retention was observed at deep recurrent "
               "pressure under the production evaluation.” The one AHN-Mamba2 correct trial is 1 of 3,542."])

    RESULTS_SNAPSHOT = f"""
<div class="snapshot">
  <div class="snap-col">
    <h4>Primary findings <span class="badge badge-frozen">frozen analysis v1.0</span></h4>
    <ul>
      <li><strong>H1 &mdash; SUPPORTED.</strong> Information types degrade non-uniformly in
        end-to-end task accuracy. Transition-region accuracy: compound-relational 0.255,
        temporal 0.307, numerical 0.389, contradictory 0.520, entity-attribute 0.594;
        omnibus p = 5&times;10<sup>&minus;4</sup>; 10/10 Holm-adjusted pairwise intervals exclude zero.</li>
      <li><strong>H2 &mdash; SUPPORTED (near-window advantage).</strong> Pooled AHN &minus; control
        A<sub>transition</sub> gap = <strong>+0.249</strong>, 95% CI <strong>[0.233, 0.266]</strong>,
        positive in every seed. Empirical knee K = 208.3 (control), 218.4 / 219.6 / 240.0 (AHN);
        every K &lt; W = 256.</li>
      <li><strong>H2 &mdash; NEGATIVE RESULT (deep recurrent).</strong> At &ge; 2W, 0 / 0 / 1 / 3
        correct of 3,542 per arm; Wilson 95% upper bounds &le; 0.0025. No measurable
        target-specific factual retention under the production evaluation.</li>
      <li><strong>H3 &mdash; SUPPORTED (behavioural).</strong> Past W + 16, appropriate-abstention
        rate 0.929&ndash;0.946 (AHN) vs 0.516 (control); unsignalled-failure rate 0.052&ndash;0.071
        vs 0.480. Six contrasts |&Delta;| &asymp; 0.42, Holm p &lt; 0.001, seed-stable.</li>
    </ul>
  </div>
  <div class="snap-col">
    <h4>Secondary / post-freeze characterizations <span class="badge badge-pf">post-freeze v1.1</span></h4>
    <ul>
      <li><strong>Transition width (post-freeze characterization).</strong> The pre-registered
        <em>pooled</em> 90&rarr;10 width was mathematically undefined. A post-freeze per-type
        analysis (analysis version 1.1) gives per-architecture median widths of 32.4 model tokens
        (control) vs 61.8&ndash;73.8 (AHN) &mdash; the control transition is earlier and narrower,
        the AHN transitions later and broader. <em>This is not a pre-registered primary analysis.</em></li>
      <li><strong>H1-2 ordering &mdash; PARTIALLY SUPPORTED.</strong> compound-relational fastest,
        entity-attribute most robust; middle ranks compress under an answered-valid metric.</li>
      <li><strong>H3-3 calibration &mdash; PARTIALLY SUPPORTED (secondary).</strong> AHN arms become
        more conservative on answered trials in the transition; the small past-window answered
        population (&lt; 5% of past-window trials) is badly calibrated for all architectures.</li>
      <li><strong>VAL-4 residual in-window failure.</strong> ~32% of trials whose target is
        exact-attention eligible throughout still fail, rising steeply across intended pressures
        205&ndash;235.</li>
    </ul>
  </div>
</div>
"""

    order = [k for k in bib if k in cited] + [k for k in bib if k not in cited]
    refs_html = render_references(bib, [k for k in bib])  # full verified list, stable order

    nav = [("Overview", "overview"), ("Key findings", "key-findings"),
           ("Figures", "figures"), ("Results snapshot", "results-snapshot"),
           ("Full paper", "paper"), ("Methods", "methods"),
           ("Discussion", "discussion"), ("Limitations", "limitations"),
           ("References", "references")]
    navhtml = "".join(f'<a href="#{t}">{n}</a>' for n, t in nav)

    findings_html = "".join(
        f'<a class="finding" href="{link}"><span class="finding-k">{k}</span>'
        f'<span class="finding-tag">{tag}</span><h3>{headline}</h3><p>{body}</p></a>'
        for (k, tag, headline, body, link) in FINDINGS)

    wwh_html = "".join(
        f'<div class="wwh-card"><h3>{q}</h3><p>{a}</p></div>' for (q, a) in WWH)

    exp_html = ""
    for k, vs in EXPERIMENT.items():
        exp_html += f'<div class="exp-row"><div class="exp-k">{k}</div><div class="exp-v">' + \
                    "".join(f"<span>{html.escape(v)}</span>" for v in vs) + "</div></div>"

    fig_html = ""
    for slug, title, expl, anchor in FIGURES:
        fig_html += f"""
<figure class="fig" id="fig-{slug}">
  <a href="figures/{slug}.png" target="_blank" rel="noopener" title="Open full size">
    <img src="figures/{slug}.png" alt="{re.sub('&[a-z]+;', '', title)}" loading="lazy">
  </a>
  <figcaption><strong>{title}.</strong> {expl}
    <span class="fig-links"><a href="figures/{slug}.png" target="_blank" rel="noopener">PNG</a>
    &middot; <a href="figures/{slug}.svg" target="_blank" rel="noopener">SVG</a>
    &middot; <a href="{anchor}">Results &rarr;</a></span></figcaption>
</figure>"""

    review_html = "".join(f"<li>{q}</li>" for q in REVIEW_QUESTIONS)

    paper_html = ""
    for name in ["Abstract", "Introduction", "Related Work", "Methods", "Results",
                 "Discussion", "Conclusion"]:
        sid = name.lower().replace(" ", "-")
        extra = ""
        if name == "Results":
            extra = ('\n<h3 id="result-tables">Result tables</h3>\n' + tbl1 + tbl2 + tbl3 + tbl4 + tbl5)
        paper_html += f'<section class="ms" id="{sid}"><h2>{name}</h2>{sections[name]}{extra}</section>\n'
    paper_html += f'<section class="ms" id="limitations"><h2>Limitations</h2>{lim_html}</section>\n'

    toc = "".join(
        f'<a href="#{n.lower().replace(" ", "-")}">{n}</a>'
        for n in ["Abstract", "Introduction", "Related Work", "Methods", "Results",
                  "Discussion", "Conclusion", "Limitations", "References"])

    page = TEMPLATE.format(
        title=html.escape(PAPER_TITLE),
        subtitle=html.escape(PAPER_SUBTITLE),
        commit_short=COMMIT_SHORT, commit_full=COMMIT_FULL, branch=BRANCH,
        build_date=BUILD_DATE, nav=navhtml, tldr=TLDR,
        findings=findings_html, wwh=wwh_html, experiment=exp_html,
        figures=fig_html, results_snapshot=RESULTS_SNAPSHOT,
        review=review_html, paper=paper_html, toc=toc, references=refs_html,
        n_refs=len(bib),
    )
    (HERE / "index.html").write_text(page)
    print(f"wrote {HERE/'index.html'}  ({len(page):,} bytes)")
    print(f"draft commit {COMMIT_SHORT} on {BRANCH}, built {BUILD_DATE}")
    print(f"references: {len(bib)}   figures: {len(FIGURES)}   tables: 5")

    for i, arg in enumerate(sys.argv):
        if arg == "--artifact":
            out = pathlib.Path(sys.argv[i + 1]) if i + 1 < len(sys.argv) else HERE / "artifact.html"
            _write_artifact(page, out)
            break


def _data_uri(path: pathlib.Path) -> str:
    mime = {"png": "image/png", "svg": "image/svg+xml"}[path.suffix.lstrip(".")]
    b64 = base64.b64encode(path.read_bytes()).decode("ascii")
    return f"data:{mime};base64,{b64}"


def _write_artifact(page: str, out: pathlib.Path) -> None:
    """Repackage the built index.html as a single self-contained file for the
    Claude Artifact tool: no <!doctype>/<html>/<head>/<body>, <title>+<style> at
    the top, every asset inlined. Rendered content is byte-identical to the
    committed page; only the delivery packaging changes."""
    css = (HERE / "style.css").read_text()
    js = (HERE / "app.js").read_text()

    body = page
    body = body.split("<body id=\"top\">", 1)[1]
    body = body.rsplit("<script src=\"app.js\"></script>", 1)[0]
    body = body.replace("</body>", "").replace("</html>", "").strip()

    for slug, *_ in FIGURES:
        for ext in ("png", "svg"):
            f = HERE / "figures" / f"{slug}.{ext}"
            if f.exists():
                body = body.replace(f"figures/{slug}.{ext}", _data_uri(f))

    art = (
        "<title>AHN Memory Degradation</title>\n"
        "<style>\n" + css + "\n</style>\n"
        '<a id="top"></a>\n'
        + body + "\n"
        "<script>\n" + js + "\n</script>\n"
    )
    out.write_text(art)
    print(f"wrote {out}  ({len(art):,} bytes, self-contained)")


TEMPLATE = r"""<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<meta name="robots" content="noindex, nofollow, noarchive, noimageindex">
<meta name="referrer" content="no-referrer">
<title>{title} — research draft</title>
<link rel="stylesheet" href="style.css">
</head>
<body id="top">
<div class="draftbar">RESEARCH DRAFT &mdash; FOR TEAM REVIEW &nbsp;·&nbsp; Not peer reviewed. Results and manuscript are subject to revision.</div>

<header class="hero">
  <div class="wrap">
    <div class="badges">
      <span class="badge badge-draft">DRAFT</span>
      <span class="badge">Internal team review</span>
      <span class="badge">Draft version {commit_short}</span>
      <span class="badge">Built {build_date}</span>
    </div>
    <h1>{title}</h1>
    <p class="lede">{subtitle}</p>
    <p class="team">AHN memory-degradation study &middot; author list withheld on this internal page (anonymous NAACL/ARR submission in preparation).</p>
    <nav class="topnav">{nav}</nav>
  </div>
</header>

<main class="wrap">

<section id="review" class="review">
  <h2>Review this draft</h2>
  <p>This page is a presentation layer over the current manuscript source
  (<code>manuscript/*.md</code>) at commit <code>{commit_short}</code>. It is for
  teammate review, not a submission. Suggested questions while you read:</p>
  <ol>{review}</ol>
  <p class="muted">There is no comment system on this page. Leave feedback wherever
  the team normally does (issue tracker / doc / chat), referencing section anchors or
  the <span class="rtag">R#</span> result identifiers.</p>
</section>

<section id="overview">
  <h2>Overview</h2>
  <p class="tldr">{tldr}</p>
  <div class="wwh">{wwh}</div>
</section>

<section id="key-findings">
  <h2>Key findings</h2>
  <div class="findings">{findings}</div>
  <p class="muted">Every quantitative claim on this page is taken verbatim from the
  manuscript and its results-traceability table; nothing is re-derived here.</p>
</section>

<section id="experiment">
  <h2>Experiment at a glance</h2>
  <div class="exp">{experiment}</div>
  <div class="wk-note">
    <p><strong>W</strong> is the architectural exact-attention boundary
    (W&nbsp;=&nbsp;256, forced for every arm).
    <strong>K</strong> is the empirical accuracy knee estimated from the data
    (isotonic 0.5-crossing of pooled strict accuracy).
    <strong>W&nbsp;&ne;&nbsp;K</strong>: every K (208&ndash;240) lies below W, and
    K is a descriptive per-run quantity &mdash; not a &ldquo;compression threshold&rdquo;
    and not the point where compression begins.</p>
  </div>
</section>

<section id="figures">
  <h2>Figures</h2>
  <p class="muted">Frozen publication exhibits (<code>outputs/publication_exhibits/</code>).
  Click a figure for the full-size image; SVG links give the vector version. Scientific
  values are unchanged; the explanations are drawn from the current manuscript.</p>
  {figures}
</section>

<section id="results-snapshot">
  <h2>Results snapshot</h2>
  <p class="muted">Verified values from the manuscript results-traceability table.
  Primary findings come from the frozen analysis (version 1.0). The H2 transition-width
  characterization is <strong>post-freeze</strong> (analysis version 1.1) and is marked
  as such &mdash; it is not a pre-registered primary analysis.</p>
  {results_snapshot}
  <p><a class="jump" href="#results-full">Read the full Results section &rarr;</a></p>
</section>

<section id="paper">
  <h2>Full paper</h2>
  <p class="muted">Complete current draft, rendered from the manuscript source at
  commit <code>{commit_short}</code>. Section numbering follows the manuscript.
  <span class="rtag">R#</span> markers are traceable result identifiers.</p>
  <div class="paper-layout">
    <aside class="toc"><div class="toc-inner"><strong>Contents</strong>{toc}</div></aside>
    <article class="paper-body" id="results-full">
      {paper}
      <section class="ms" id="references">
        <h2>References</h2>
        <p class="muted">{n_refs} verified references. Links open the arXiv abstract or
        the publisher record.</p>
        {references}
      </section>
    </article>
  </div>
</section>

<section id="draft-info" class="draft-info">
  <h2>Draft information</h2>
  <table>
    <tr><th>Branch</th><td><code>{branch}</code></td></tr>
    <tr><th>Commit</th><td><code>{commit_full}</code></td></tr>
    <tr><th>Draft version</th><td><code>{commit_short}</code></td></tr>
    <tr><th>Page built</th><td>{build_date}</td></tr>
    <tr><th>Scientific status</th><td>Frozen analysis (v1.0) + approved post-freeze
      amendment (v1.1); manuscript under revision</td></tr>
    <tr><th>Trials</th><td>92,160</td></tr>
    <tr><th>Status</th><td>Research draft &mdash; not peer reviewed, not a preprint,
      not a NAACL/ARR submission</td></tr>
  </table>
</section>

</main>

<footer class="foot">
  <div class="wrap">
    <p>Research draft for internal team review. Not peer reviewed; results and
    manuscript subject to revision. Generated from the manuscript source at
    commit {commit_short} on {build_date}. Not for public distribution while an
    anonymous NAACL/ARR submission is in preparation.</p>
  </div>
</footer>

<a href="#top" class="totop" aria-label="Back to top">&uarr;</a>
<script src="app.js"></script>
</body>
</html>
"""

if __name__ == "__main__":
    main()
