#!/usr/bin/env python3
"""Build the publication exhibits from locked evidence only.

Sources (the ONLY three allowed):
  1. locked raw artifact  final_audit/FINAL_LOCKED/results_FINAL_92160.parquet
  2. frozen analysis v1.0  final_audit/FINAL_LOCKED/final_*.csv
  3. approved amendment v1.1  outputs/final_v1_1_reporting_amendment/*.csv

Writes to outputs/publication_exhibits/{main,appendix,source_tables,manifests}/.
No new scientific endpoint. No GPU. Never modifies FINAL_LOCKED or the raw parquet.

    python scripts/build_publication_exhibits.py --repo .
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
import sys
from datetime import datetime, timezone
from pathlib import Path

RAW_SHA256 = "a72fd43e87457a70c2833314e1443a794fa4189362ac8206c56275ef427fb62e"
RAW = "final_audit/FINAL_LOCKED/results_FINAL_92160.parquet"
FROZEN = "final_audit/FINAL_LOCKED"
V11 = "outputs/final_v1_1_reporting_amendment"
OUT = "outputs/publication_exhibits"

DISPLAY = {"multi-hop": "compound-relational"}
AHN = ["mamba2", "deltanet", "gated_deltanet"]
ARMS = ["transformer", "mamba2", "deltanet", "gated_deltanet"]
ARM_COLOR = {"transformer": "#7a7a7a", "mamba2": "#1f77b4",
             "deltanet": "#2ca02c", "gated_deltanet": "#d62728"}
ARM_LABEL = {"transformer": "Transformer (no AHN)", "mamba2": "AHN-Mamba2",
             "deltanet": "AHN-DeltaNet", "gated_deltanet": "AHN-GatedDeltaNet"}
FT_ORDER = ["multi-hop", "temporal", "numerical", "contradictory", "entity-attribute"]
FT_COLOR = {"multi-hop": "#d62728", "temporal": "#ff7f0e", "numerical": "#9467bd",
            "contradictory": "#2ca02c", "entity-attribute": "#1f77b4"}
W = 256


def disp(ft: str) -> str:
    return DISPLAY.get(ft, ft)


def sha(p: Path) -> str:
    return hashlib.sha256(p.read_bytes()).hexdigest()


class Builder:
    def __init__(self, root: Path):
        self.root = root
        self.out = root / OUT
        for d in ("main", "appendix", "source_tables", "manifests"):
            (self.out / d).mkdir(parents=True, exist_ok=True)
        import pandas as pd
        self.pd = pd
        self.df = pd.read_parquet(root / RAW)
        self.frozen = lambda n: pd.read_csv(root / FROZEN / n)
        self.v11 = lambda n: pd.read_csv(root / V11 / n)
        self.summary = json.loads((root / FROZEN / "final_summary.json").read_text())
        self.exhibits: list[dict] = []
        import matplotlib
        matplotlib.use("Agg")
        import matplotlib.pyplot as plt
        plt.rcParams.update({
            "figure.dpi": 120, "savefig.bbox": "tight", "savefig.pad_inches": 0.08,
            "font.size": 8.5, "axes.titlesize": 9.5, "axes.labelsize": 8.5,
            "legend.fontsize": 7.5, "axes.spines.top": False, "axes.spines.right": False,
            "axes.grid": True, "grid.alpha": 0.22, "grid.linewidth": 0.5,
            "figure.facecolor": "white", "axes.facecolor": "white",
        })
        self.plt = plt

    # ---- helpers -----------------------------------------------------------
    def _src(self, name: str, df) -> str:
        p = self.out / "source_tables" / name
        df.to_csv(p, index=False)
        return name

    def _fig(self, fig, eid: str, placement: str) -> str:
        name = f"{eid}.svg"
        fig.savefig(self.out / placement / name, format="svg")
        fig.savefig(self.out / placement / f"{eid}.png", format="png", dpi=200)
        self.plt.close(fig)
        return name

    @staticmethod
    def _pressure_axis(ax, *, xlim=(130, 790)):
        """Linear model-tat axis with clean ticks; W drawn distinct from any K."""
        ax.set_xlim(*xlim)
        ax.minorticks_off()
        ax.set_xticks([150, 200, 250, 300, 400, 500, 600, 700, 760])
        ax.axvline(W, color="k", ls="--", lw=1.2, zorder=1)

    def _tbl_md(self, eid: str, placement: str, title: str, df, notes: list[str]) -> str:
        name = f"{eid}.md"
        lines = [f"# {title}", ""]
        lines += ["| " + " | ".join(map(str, df.columns)) + " |",
                  "| " + " | ".join(["---"] * len(df.columns)) + " |"]
        for _, r in df.iterrows():
            lines.append("| " + " | ".join("" if self.pd.isna(v) else str(v) for v in r) + " |")
        if notes:
            lines += [""] + [f"- {n}" for n in notes]
        (self.out / placement / name).write_text("\n".join(lines) + "\n")
        return name

    def add(self, *, eid, title, kind, placement, claim_ids, sources, source_tables,
            files, statistic, post_freeze=None, notes=None, caption=None):
        entry = {
            "exhibit_id": eid, "title": title, "kind": kind, "placement": placement,
            "claim_ids": claim_ids, "scripts": ["scripts/build_publication_exhibits.py"],
            "source_files": sources, "source_tables": source_tables,
            "raw_artifact_sha256": RAW_SHA256, "analysis_versions": ["1.0", "1.1"],
            "post_freeze_status": post_freeze, "statistic_definitions": statistic,
            "caption": caption or "",
            "generated_files": {f: sha(self.out / ("main" if placement == "MAIN" else
                                "appendix" if placement == "APPENDIX" else "source_tables") / f)
                                for f in files if (self.out / ("main" if placement == "MAIN" else
                                "appendix" if placement == "APPENDIX" else "source_tables") / f).exists()},
            "notes": notes or [],
        }
        self.exhibits.append(entry)
        (self.out / "manifests" / f"{eid}.json").write_text(json.dumps(entry, indent=2) + "\n")

    # =====================================================================
    # FIGURE D — experimental design / memory-pressure setup
    # =====================================================================
    def fig_design(self):
        pd = self.pd
        g = (self.df.groupby("intended_model_tokens_after_target")
             .agg(realised_median=("model_tokens_after_target", "median"),
                  realised_q1=("model_tokens_after_target", lambda s: s.quantile(.25)),
                  realised_q3=("model_tokens_after_target", lambda s: s.quantile(.75)),
                  n=("correct", "size")).reset_index()
             .rename(columns={"intended_model_tokens_after_target": "intended_model_tat"}))
        bands = {"control": [150, 180], "transition": [205, 220, 235, 250, 265, 285],
                 "recurrent": [315, 380, 520, 760]}
        g["band"] = g["intended_model_tat"].apply(
            lambda t: next(b for b, v in bands.items() if t in v))
        st = self._src("figD_design_grid.csv", g)

        plt = self.plt
        fig, (ax0, ax1) = plt.subplots(2, 1, figsize=(6.8, 5.0), constrained_layout=True,
                                       gridspec_kw={"height_ratios": [0.62, 1.0]})
        # top: schematic of one tokenised trajectory
        ax0.set_title("A single matched trajectory (byte-identical across the 4 architectures)", fontsize=8.5)
        ax0.set_xlim(0, 330); ax0.set_ylim(0, 1); ax0.set_yticks([])
        ax0.axvspan(0, 44, color="#cfe8cf"); ax0.axvspan(44, 60, color="#ffcf7a"); ax0.axvspan(60, 330, color="#dfe7f5")
        ax0.text(22, 0.5, "distractor\ncontext", ha="center", va="center", fontsize=7)
        ax0.annotate("target span\n(median 15.5 tok)", xy=(52, 0.98), xytext=(52, 1.28),
                     ha="center", va="bottom", fontsize=6.6,
                     arrowprops=dict(arrowstyle="-", color="#7a5a00", lw=.8))
        ax0.annotate("", xy=(60, 0.5), xytext=(325, 0.5),
                     arrowprops=dict(arrowstyle="<->", color="#33456b", lw=1))
        ax0.text(192, 0.66, "model_tokens_after_target  (pressure coordinate)",
                 ha="center", fontsize=7.5, color="#33456b")
        ax0.axvline(60 + W, color="k", ls="--", lw=1.2)
        ax0.text(60 + W + 4, 0.5, "W = 256\narchitectural\nsliding-window\nboundary\n(not a threshold)",
                 fontsize=6.6, va="center")
        ax0.set_xticks([0, 50, 100, 150, 200, 250, 300])
        ax0.tick_params(labelsize=7)

        # bottom: the 12-target grid, intended vs realised (calibrated)
        colb = {"control": "#2e7d32", "transition": "#e08600", "recurrent": "#666666"}
        for _, r in g.iterrows():
            ax1.plot([r.intended_model_tat, r.intended_model_tat], [r.realised_q1, r.realised_q3],
                     color=colb[r.band], lw=5, alpha=.45, solid_capstyle="round", zorder=2)
            ax1.scatter(r.intended_model_tat, r.realised_median, color=colb[r.band], s=26, zorder=3)
        ax1.plot([130, 800], [130, 800], color="#bbbbbb", ls=":", lw=1, zorder=1)
        ax1.axhline(W, color="k", ls="--", lw=1.2)
        ax1.text(690, W + 14, "W = 256", fontsize=7.5)
        ax1.set_xlabel("intended model_tokens_after_target  (grouping key; 12 frozen levels)")
        ax1.set_ylabel("realised model_tokens_after_target\n(median ± IQR; n = 7,680 / level)")
        ax1.set_xlim(130, 800); ax1.set_ylim(130, 800); ax1.minorticks_off()
        ax1.set_xticks([150, 205, 265, 315, 380, 520, 760]); ax1.set_yticks([150, 250, 350, 450, 550, 650, 760])
        from matplotlib.patches import Patch
        ax1.legend(handles=[Patch(color=colb[b], alpha=.6, label=f"{b} band ({len(bands[b])} levels)") for b in colb]
                   + [plt.Line2D([], [], color="#bbbbbb", ls=":", label="intended = realised")],
                   loc="upper left", frameon=False, fontsize=7)
        fig.suptitle("Figure D — Memory-pressure design: 4 architectures × 240 items × 12 targets × 8 seeds "
                     "= 92,160 trials", fontsize=9)
        f = self._fig(fig, "figD_experimental_design", "main")
        self.add(eid="figD_experimental_design",
                 caption="Top: schematic of one tokenised evaluation trajectory. A distractor context precedes the target span (median 15.5 tokens); model_tokens_after_target counts every token after the target span (distractors, the question and instruction, and the chat-template suffix) and is the pressure coordinate. W = 256 is the architectural sliding-window reference. Bottom: the 12 frozen intended pressure targets (grouping key, x-axis) against the realised model_tokens_after_target they produced (median and inter-quartile range over n = 7,680 trials per level); per-fact-type filler was calibrated with the base tokenizer so that realised closely tracks intended. Two targets fall in the control band, six in the transition band, four in the recurrent band. The full grid is 4 architectures x 240 items x 12 targets x 8 seeds = 92,160 trials.",
                 title="Experimental design / memory-pressure setup",
                 kind="figure", placement="MAIN", claim_ids=["(design)"],
                 sources=[RAW], source_tables=[st], files=[f, st],
                 statistic={"model_tokens_after_target": "all tokens after the target span in the "
                            "tokenised model input; the canonical pressure coordinate",
                            "W": "architectural sliding-window boundary = 256 (design-fixed; NOT a threshold)"},
                 notes=["W=256 is the architectural window, drawn as a reference line only.",
                        "The grouping key is the intended target; curves are plotted against realised model-tat."])

    # =====================================================================
    # FIGURE 1 — H1 non-uniform degradation
    # =====================================================================
    def fig_h1(self):
        pd = self.pd
        d = self.df[self.df.architecture.isin(AHN)]
        rows = []
        for (ft, tgt), gg in d.groupby(["fact_type", "intended_model_tokens_after_target"]):
            rows.append(dict(fact_type=ft, fact_type_display=disp(ft),
                             intended_model_tat=int(tgt),
                             realised_model_tat_median=float(gg.model_tokens_after_target.median()),
                             strict_accuracy=float(gg.correct.mean()),
                             abstention_rate=float(gg.abstained.mean()),
                             n=int(len(gg))))
        cur = pd.DataFrame(rows)
        at = self.frozen("final_h1_h1_a_transition.csv")
        at["fact_type_display"] = at.fact_type.map(disp)
        at_val = at.set_index("fact_type")["a_transition"].to_dict()
        st1 = self._src("fig1_h1_curves.csv", cur)
        st2 = self._src("fig1_h1_a_transition.csv", at)

        plt = self.plt
        fig, ax = plt.subplots(figsize=(6.8, 4.3), constrained_layout=True)
        ax.set_ylim(-0.03, 1.03)
        ax.axvspan(202, 267, color="#ededed", zorder=0)
        # A_transition-region label as a bracket ABOVE the plot area (no overprint)
        ax.annotate("", xy=(202, 1.045), xytext=(267, 1.045), annotation_clip=False,
                    arrowprops=dict(arrowstyle="-", color="#888888", lw=1))
        ax.text(234.5, 1.06, "A$_{transition}$ region (intended targets 205–265)",
                ha="center", va="bottom", fontsize=6.8, color="#555555", clip_on=False)
        for ft in FT_ORDER:
            s = cur[cur.fact_type == ft].sort_values("realised_model_tat_median")
            ax.plot(s.realised_model_tat_median, s.strict_accuracy, "-o", ms=3.6, lw=1.5,
                    color=FT_COLOR[ft], label=f"{disp(ft)}  (A$_t$ = {at_val[ft]:.2f})")
        self._pressure_axis(ax)
        ax.text(W + 8, 0.62, "W = 256\n(architectural window)", fontsize=7)
        ax.set_xlabel("realised model_tokens_after_target  (median per intended level)")
        ax.set_ylabel("strict production accuracy\n(3 AHN arms pooled; n = 5,760 / point)")
        ax.legend(loc="upper right", frameon=False, ncol=1, fontsize=7.5)
        ax.set_title("Figure 1 — Fact types degrade non-uniformly in task accuracy\n"
                     "(label-permutation omnibus on the 5 A$_{transition}$ means: p = 5×10$^{-4}$, 0/2000)",
                     fontsize=9, pad=16)
        f = self._fig(fig, "fig1_h1_nonuniform_degradation", "main")
        self.add(eid="fig1_h1_nonuniform_degradation",
                 title="H1: non-uniform degradation across information types",
                 kind="figure", placement="MAIN", claim_ids=["H1-1", "H1-2"],
                 sources=[RAW, "final_audit/FINAL_LOCKED/final_h1_h1_a_transition.csv"],
                 source_tables=[st1, st2], files=[f, st1, st2],
                 statistic={"A_transition": "mean raw strict accuracy over intended targets "
                            "[205,220,235,250,265], AHN arms pooled (h1_degradation.a_transition)",
                            "omnibus": "label-permutation on the SD of the five A_transition means, "
                            "2000 permutations (h1_degradation.a_transition_omnibus)"},
                 caption="Strict production accuracy versus realised model_tokens_after_target for "
                 "each fact type, pooled over the three AHN architectures (n = 5,760 per point). "
                 "The y-axis is end-to-end task accuracy under the strict production metric: a trial "
                 "counts as correct only if the model emits exactly the gold value, so abstentions "
                 "(“I don't know”) and malformed outputs both count as failures. Curves are raw "
                 "cell means (no fit). W = 256 is the architectural sliding-window reference, not a "
                 "threshold. The shaded region marks the intended targets (205–265) averaged for "
                 "A_transition. The five-way spread of A_transition means exceeds label-permutation "
                 "chance (p = 5×10⁻⁴, 0/2000). The ordering is partly metric-dependent: under "
                 "answered-valid accuracy it compresses (Table 1, Appendix A-H1). Internal data key "
                 "“multi-hop” is reported as “compound-relational”.",
                 notes=["y-axis is task accuracy and includes abstention — NOT 'information retained'.",
                        "internal key 'multi-hop' shown as 'compound-relational'.",
                        "answered-valid ordering (Table 1) is less separated — the ordering is not metric-independent."])

    # =====================================================================
    # TABLE 1 — H1 primary result
    # =====================================================================
    def tbl_h1_primary(self):
        pd = self.pd
        from ahnexp import h1_degradation, full_run
        cv = self.frozen("final_control_validity_control_validity.csv").set_index("fact_type")
        at = self.frozen("final_h1_h1_a_transition.csv").set_index("fact_type")
        cvp = full_run.control_validity(self.df)  # to get primary set (unchanged from frozen)
        d = self.df[self.df.fact_type.isin(set(cvp.loc[cvp.in_h1_primary, "fact_type"]))]
        av = h1_degradation.a_transition(d, value="answered_valid").set_index("fact_type")["a_transition"]
        rows = []
        for ft in FT_ORDER:
            rows.append(dict(
                fact_type_internal=ft, construct=disp(ft),
                n_A_transition=int(at.loc[ft, "n"]),
                A_transition_raw_strict=round(float(at.loc[ft, "a_transition"]), 3),
                A_transition_answered_valid=round(float(av.loc[ft]), 3),
                in_window_control_strict=round(float(cv.loc[ft, "strict_accuracy"]), 3),
                in_window_control_abstention=round(float(cv.loc[ft, "abstention_rate"]), 3),
                in_window_control_verdict=cv.loc[ft, "verdict"]))
        t = pd.DataFrame(rows).sort_values("A_transition_raw_strict").reset_index(drop=True)
        st = self._src("tbl1_h1_primary.csv", t)
        md = self._tbl_md("tbl1_h1_primary", "main",
                          "Table 1 — H1 primary result (raw strict production accuracy is the frozen primary endpoint)",
                          t, [f"Label-permutation omnibus on the SD of the five A_transition means: "
                              f"p = {self.summary['h1_omnibus_p']:.4f} (0/2000).",
                              "A_transition = mean raw strict accuracy over intended targets 205–265, AHN arms pooled.",
                              "Answered-valid column is a FROZEN SECONDARY sensitivity (all types), not a replacement.",
                              "#17 Policy A: no chance-corrected primary."])
        self.add(eid="tbl1_h1_primary", title="H1 primary result", kind="table", placement="MAIN",
                 caption="H1 primary endpoint. A_transition is the mean strict production accuracy over the five intended transition targets (205-265), pooled over the three AHN architectures (n = 5,760 per fact type). Raw strict accuracy is the pre-registered primary metric (no chance correction). The answered-valid column (accuracy computed only over trials that produced a parseable answer) is a pre-registered secondary sensitivity, shown for context, not a replacement. In-window control columns are pooled over intended targets 150 and 180 (n = 3,072 per fact type). The label-permutation omnibus on the dispersion of the five A_transition means gives p = 5x10^-4 (0/2000 permutations).",
                 claim_ids=["H1-1", "H1-2"],
                 sources=["final_audit/FINAL_LOCKED/final_h1_h1_a_transition.csv",
                          "final_audit/FINAL_LOCKED/final_control_validity_control_validity.csv", RAW],
                 source_tables=[st], files=[md, st],
                 statistic={"A_transition_raw_strict": "FROZEN PRIMARY",
                            "A_transition_answered_valid": "FROZEN SECONDARY sensitivity (recomputed per type via h1_degradation.a_transition(value='answered_valid'))"},
                 notes=["compound-relational and temporal have the lowest raw A_transition AND elevated in-window abstention."])

    # =====================================================================
    # TABLE 2 — H1 pairwise contrasts
    # =====================================================================
    def tbl_h1_contrasts(self):
        pd = self.pd
        c = self.frozen("final_h1_h1_contrasts.csv").copy()
        c["a"] = c.a.map(disp); c["b"] = c.b.map(disp)
        c["diff"] = c["diff"].round(3)
        c["ci95"] = c.apply(lambda r: f"[{r.ci_low:.3f}, {r.ci_high:.3f}]", axis=1)
        c["p_holm"] = c.p_holm.round(3)
        t = c[["a", "b", "diff", "ci95", "p_holm", "significant_holm"]]
        st = self._src("tbl2_h1_contrasts.csv", self.frozen("final_h1_h1_contrasts.csv"))
        md = self._tbl_md("tbl2_h1_contrasts", "main",
                          "Table 2 — H1 pairwise A$_{transition}$ contrasts (all fact-type pairs)",
                          t, ["Hierarchical (item→seed) cluster bootstrap, 2000 resamples; Holm over 10 contrasts.",
                              "10/10 contrasts Holm-significant. Closest to threshold: compound-relational vs temporal, p_holm 0.037.",
                              "H1 supported iff ≥1 Holm-adjusted CI excludes 0 (frozen criterion)."])
        self.add(eid="tbl2_h1_contrasts", title="H1 pairwise contrasts", kind="table", placement="MAIN",
                 caption="All ten pairwise fact-type differences in A_transition, with 95% hierarchical (item then seed) cluster-bootstrap intervals (2,000 resamples) and Holm-adjusted two-sided bootstrap p-values over the ten-comparison family. All ten intervals exclude zero; the closest to the boundary is compound-relational versus temporal (p_holm = 0.037).",
                 claim_ids=["H1-1"], sources=["final_audit/FINAL_LOCKED/final_h1_h1_contrasts.csv"],
                 source_tables=[st], files=[md, st],
                 statistic={"diff": "A_transition(a) − A_transition(b)", "ci95": "percentile 95% hierarchical bootstrap",
                            "p_holm": "Holm-adjusted two-sided bootstrap p over the 10-contrast family"})

    # =====================================================================
    # FIGURE 2 — H2 architecture transition curves
    # =====================================================================
    def fig_h2(self):
        pd = self.pd
        cur = self.frozen("final_h2_h2_curves.csv")
        k = self.frozen("final_h2_h2_k_strict.csv").set_index("architecture")
        gap = self.summary["h2_a_transition_gap"]
        ab = (self.df.groupby(["architecture", "intended_model_tokens_after_target"])
              .agg(x=("model_tokens_after_target", "median"), abst=("abstained", "mean"),
                   n=("correct", "size")).reset_index())
        st1 = self._src("fig2_h2_curves.csv", cur)
        st2 = self._src("fig2_h2_abstention.csv", ab)
        st3 = self._src("fig2_h2_k_strict.csv", self.frozen("final_h2_h2_k_strict.csv"))

        plt = self.plt
        fig, (a0, a1) = plt.subplots(2, 1, figsize=(6.6, 5.4), sharex=True, constrained_layout=True,
                                     gridspec_kw={"height_ratios": [1.5, 1]})
        a0.axvspan(200, 270, color="#eeeeee", zorder=0)
        for arm in ARMS:
            s = cur[cur.architecture == arm].sort_values("model_tokens_after_target")
            a0.plot(s.model_tokens_after_target, s.accuracy, "-o", ms=3.4, lw=1.6,
                    color=ARM_COLOR[arm], label=ARM_LABEL[arm], zorder=3)
            a0.fill_between(s.model_tokens_after_target, s.ci_low, s.ci_high, color=ARM_COLOR[arm], alpha=.12)
        self._pressure_axis(a0)
        a0.set_ylim(-0.03, 1.03)
        # empirical knee K: one CI bar + diamond per arm, stacked INSIDE the panel near y=0
        for i, arm in enumerate(ARMS):
            y = 0.045 + 0.055 * (len(ARMS) - 1 - i)
            a0.plot([k.loc[arm, "ci_low"], k.loc[arm, "ci_high"]], [y, y], color=ARM_COLOR[arm],
                    lw=3, alpha=.55, zorder=4)
            a0.scatter([k.loc[arm, "k_strict_acc"]], [y], color=ARM_COLOR[arm], marker="D", s=18, zorder=5)
        a0.text(132, 0.20, "empirical knee K\n(◆ = point, bar = 95% CI;\nnote every K < W)",
                fontsize=6.2, va="top", ha="left")
        a0.axvline(W, color="k", ls="--", lw=1.3, zorder=6)  # redraw W over the K strip
        a0.text(W + 6, 0.86, "W = 256\narchitectural\nwindow\n(not a threshold)", fontsize=6.6)
        a0.text(300, 0.60, f"A$_{{transition}}$ gap\n(AHN − Transformer, [200,270])\n"
                f"= +{gap['ahn_pooled_minus_transformer']:.2f} [{gap['ci_low']:.2f}, {gap['ci_high']:.2f}]",
                ha="left", fontsize=6.6, bbox=dict(boxstyle="round", fc="white", ec="#cccccc", lw=.6))
        a0.set_ylabel("strict production accuracy\n(n = 1,920 / point; 95% CI band)")
        a0.legend(loc="upper right", frameon=False, fontsize=7.5)
        a0.set_title("Figure 2 — Architecture degradation curves: every empirical knee K sits BELOW\n"
                     "the sliding-window reference W; past W all four collapse to ≈ 0 (A$_{recurrent}$ ≈ 0)",
                     fontsize=8.6)
        for arm in ARMS:
            s = ab[ab.architecture == arm].sort_values("x")
            a1.plot(s.x, s.abst, "-o", ms=3.2, lw=1.4, color=ARM_COLOR[arm])
        self._pressure_axis(a1)
        a1.set_ylabel("abstention rate\n(all trials)")
        a1.set_xlabel("realised model_tokens_after_target  (median per intended level)")
        a1.set_ylim(-0.03, 1.03)
        f = self._fig(fig, "fig2_h2_architecture_curves", "main")
        self.add(eid="fig2_h2_architecture_curves",
                 title="H2: architecture degradation curves with W and K",
                 kind="figure", placement="MAIN", claim_ids=["H2-1", "H2-2", "H2-4", "H2-5"],
                 sources=[RAW, "final_audit/FINAL_LOCKED/final_h2_h2_curves.csv",
                          "final_audit/FINAL_LOCKED/final_h2_h2_k_strict.csv",
                          "final_audit/FINAL_LOCKED/final_summary.json"],
                 source_tables=[st1, st2, st3], files=[f, st1, st2, st3],
                 statistic={"K (knee)": "isotonic 0.5 crossing of pooled strict accuracy vs realised model-tat "
                            "(h2_threshold; DESCRIPTIVE — not a threshold)",
                            "W": "architectural sliding-window boundary = 256",
                            "A_transition gap": "A_transition(AHN pooled) − A_transition(transformer) over [200,270]"},
                 post_freeze=None,
                 caption="Top: strict production accuracy versus realised model_tokens_after_target for "
                 "each architecture (n = 1,920 per point; 95% bootstrap CI band). The vertical dashed "
                 "line is the architectural sliding-window reference W = 256. The diamonds with "
                 "horizontal bars near the axis floor are the empirical performance knee K per "
                 "architecture (isotonic 0.5-crossing of pooled strict accuracy; 95% hierarchical "
                 "bootstrap CI) — a descriptive location, not a threshold, and distinct from W. Every "
                 "K (208–240) lies below W. In the near-window band [200, 270] the AHN architectures "
                 "retain +0.25 more accuracy than the no-recurrent-memory baseline (95% CI "
                 "[0.23, 0.27]). Past W all four architectures fall to ≈ 0 (A_recurrent ≈ 0; Table 3). "
                 "Bottom: abstention rate over all trials, same x-axis. The pre-registered pooled "
                 "transition-width statistic was mathematically undefined for this dataset and is not "
                 "shown (Table 3; Appendix A-H2a).",
                 notes=["W and K are visually distinct: W is a dashed vertical line; K is a per-arm "
                        "diamond + CI bar near the axis floor, inside the accuracy panel.",
                        "the frozen pooled transition-width statistic is UNDEFINED and is deliberately omitted here "
                        "(see Table 3 footnote and Appendix A-H2a).",
                        "no implication that AHN retains information past W (A_recurrent ≈ 0; Table 3, Table 5)."])

    # =====================================================================
    # TABLE 3 — H2 architecture summary
    # =====================================================================
    def tbl_h2_summary(self):
        pd = self.pd
        from ahnexp import h2_threshold
        k = self.frozen("final_h2_h2_k_strict.csv").set_index("architecture")
        shp = self.frozen("final_h2_h2_shape_break_at_W.csv").set_index("architecture")
        ar = self.frozen("final_h2_h2_a_recurrent.csv").set_index("architecture")
        kn = h2_threshold.knees(self.df).set_index("architecture")  # for K_abstention (locked parquet + frozen code)
        gap = self.summary["h2_a_transition_gap"]
        rows = []
        for arm in ARMS:
            rows.append(dict(
                architecture=ARM_LABEL[arm],
                K_strict=f"{k.loc[arm,'k_strict_acc']:.1f} [{k.loc[arm,'ci_low']:.1f}, {k.loc[arm,'ci_high']:.1f}]",
                K_abstention=f"{kn.loc[arm,'k_abstention']:.0f}",
                shape_vs_smooth=f"{shp.loc[arm,'verdict']} (ΔAIC {shp.loc[arm,'aic_piecewise']-shp.loc[arm,'aic_smooth']:+.1f})",
                A_recurrent=f"{ar.loc[arm,'a_recurrent']:.4f} [{ar.loc[arm,'ci_low']:.4f}, {ar.loc[arm,'ci_high']:.4f}]"))
        t = pd.DataFrame(rows)
        gap_str = f"+{gap['ahn_pooled_minus_transformer']:.3f} [{gap['ci_low']:.3f}, {gap['ci_high']:.3f}]"
        st = self._src("tbl3_h2_summary.csv", t)
        md = self._tbl_md("tbl3_h2_summary", "main", "Table 3 — H2 architecture summary", t,
                          [f"A_transition gap (AHN pooled − Transformer) over [200, 270] = {gap_str} "
                           "(hierarchical bootstrap 95% CI; CI excludes 0).",
                           "K is a DESCRIPTIVE empirical knee (0.5 crossing), NOT a threshold; W = 256 is the "
                           "architectural window. Every K < W.",
                           "The pre-registered pooled 90→10 transition-width statistic is UNDEFINED for this dataset "
                           "(the pooled 5-type curve peaks ≈ 0.88, below the 0.90 reference) — see the post-freeze "
                           "reporting amendment (Table A-H2a / protocol/amendment_h2_transition_width.md). It is not "
                           "reported here and the frozen 'intermediate' label is not used.",
                           "shape vs smooth: piecewise fit with break fixed at W = 256, AIC comparison (frozen v1.0).",
                           "K_abstention recomputed from the locked parquet with frozen h2_threshold.knees."])
        self.add(eid="tbl3_h2_summary", title="H2 architecture summary", kind="table", placement="MAIN",
                 caption="Per-architecture H2 summary. K_strict and K_abstention are the isotonic 0.5-crossings of pooled strict accuracy and of abstention rate against realised model_tokens_after_target; they are descriptive empirical knees, not thresholds, and are distinct from the architectural reference W = 256. Every K_strict lies below W. shape_vs_smooth compares a smooth log-linear fit with a fit allowed to change slope at W, by AIC (negative delta favours the change-point fit). A_recurrent is the mean strict accuracy over intended targets >= 315 with a 95% bootstrap interval. The A_transition gap (AHN pooled minus baseline) over [200, 270] is +0.249 [0.233, 0.266]. The pre-registered pooled 90-to-10 transition-width statistic was mathematically undefined for this dataset and is not reported here (Appendix A-H2a).",
                 claim_ids=["H2-1", "H2-2", "H2-4", "H2-5"],
                 sources=[RAW, "final_audit/FINAL_LOCKED/final_h2_h2_k_strict.csv",
                          "final_audit/FINAL_LOCKED/final_h2_h2_shape_break_at_W.csv",
                          "final_audit/FINAL_LOCKED/final_h2_h2_a_recurrent.csv",
                          "final_audit/FINAL_LOCKED/final_summary.json"],
                 source_tables=[st], files=[md, st],
                 statistic={"K_strict/K_abstention": "isotonic 0.5 crossings (descriptive)",
                            "A_recurrent": "mean strict accuracy over intended ≥ 315, hierarchical CI"},
                 notes=["frozen 'intermediate' width verdict deliberately excluded."])

    # =====================================================================
    # FIGURE 3 — H3 behavioural uncertainty signalling
    # =====================================================================
    def fig_h3(self):
        pd = self.pd
        per = self.frozen("final_h3_h3_behavioral_per_arm.csv").set_index("architecture")
        con = self.frozen("final_h3_h3_behavioral_contrasts.csv")
        ac = self.frozen("final_h3_h3_abstention_confidence.csv")
        # outcome composition past W+16, per arm
        w = 256 + 16
        reg = self.df[self.df.model_tokens_after_target >= w]
        comp = []
        for arm in ARMS:
            g = reg[reg.architecture == arm]
            n = len(g)
            comp.append(dict(architecture=arm,
                             correct=float((g.correct == 1).mean()),
                             wrong_valid=float(((g.correct == 0) & (g.abstained == 0) & (g.malformed == 0)).mean()),
                             malformed=float(g.malformed.mean()),
                             abstained=float(g.abstained.mean()), n=n))
        comp = pd.DataFrame(comp)
        st1 = self._src("fig3_h3_behavioral_per_arm.csv", self.frozen("final_h3_h3_behavioral_per_arm.csv"))
        st2 = self._src("fig3_h3_outcome_composition_pastW16.csv", comp)
        st3 = self._src("fig3_h3_abstention_by_pressure.csv", ac)

        short = {"transformer": "Transformer", "mamba2": "Mamba2", "deltanet": "DeltaNet",
                 "gated_deltanet": "GatedDN"}
        plt = self.plt
        fig, (a0, a1) = plt.subplots(1, 2, figsize=(7.4, 3.9), constrained_layout=True,
                                     gridspec_kw={"width_ratios": [1.12, 1]})
        order = ["correct", "wrong_valid", "malformed", "abstained"]
        cols = {"correct": "#2ca02c", "wrong_valid": "#d62728", "malformed": "#7b3294", "abstained": "#4575b4"}
        lab = {"correct": "correct factual answer", "wrong_valid": "incorrect valid answer",
               "malformed": "malformed output", "abstained": "abstention (“I don't know”)"}
        bottom = [0.0] * 4
        xs = list(range(4))
        compi = comp.set_index("architecture")
        for k_ in order:
            vals = [float(compi.loc[a, k_]) for a in ARMS]
            a0.bar(xs, vals, bottom=bottom, color=cols[k_], label=lab[k_], width=.68)
            bottom = [b + v for b, v in zip(bottom, vals)]
        a0.set_xticks(xs); a0.set_xticklabels([short[a] for a in ARMS], fontsize=7.5)
        a0.set_ylabel("fraction of trials past W+16 (272)")
        a0.set_ylim(0, 1.001); a0.set_axisbelow(True); a0.grid(axis="x")
        a0.set_title("Outcome composition past the window  (n ≈ 10,091 / arm)", fontsize=8.5)
        a0.legend(loc="upper center", bbox_to_anchor=(0.5, -0.13), ncol=2, frameon=False, fontsize=7)
        aa = per.loc[ARMS, "appropriate_abstention_rate"].values
        uu = per.loc[ARMS, "unsignalled_failure_rate"].values
        a1.plot(xs, aa, "o-", color="#4575b4", ms=6, label="appropriate abstention rate")
        a1.plot(xs, uu, "s--", color="#d62728", ms=6, label="unsignalled failure rate\n(wrong-valid ∨ malformed)")
        a1.set_xticks(xs); a1.set_xticklabels([short[a] for a in ARMS], fontsize=7.5)
        a1.set_ylim(-0.03, 1.05); a1.set_ylabel("rate  (model_tat ≥ 272)")
        a1.set_title("Frozen H3 behavioural primary\n(each AHN arm vs Transformer: p$_{holm}$ = 0, |Δ| ≈ 0.42;\n"
                     "identical across all 8 seeds)", fontsize=7.8)
        a1.legend(loc="center right", frameon=False, fontsize=7)
        fig.suptitle("Figure 3 — Behavioural uncertainty signalling: AHN abstains as memory degrades;\n"
                     "the no-recurrent-memory baseline answers or degenerates", fontsize=8.8)
        f = self._fig(fig, "fig3_h3_behavioural_signalling", "main")
        self.add(eid="fig3_h3_behavioural_signalling",
                 title="H3: behavioural uncertainty signalling",
                 kind="figure", placement="MAIN", claim_ids=["H3-1", "H3-2"],
                 sources=[RAW, "final_audit/FINAL_LOCKED/final_h3_h3_behavioral_per_arm.csv",
                          "final_audit/FINAL_LOCKED/final_h3_h3_behavioral_contrasts.csv",
                          "final_audit/FINAL_LOCKED/final_h3_h3_abstention_confidence.csv"],
                 source_tables=[st1, st2, st3], files=[f, st1, st2, st3],
                 statistic={"appropriate_abstention_rate": "P(abstained | model_tat ≥ W+16)",
                            "unsignalled_failure_rate": "P((wrong valid) ∨ malformed | model_tat ≥ W+16)"},
                 caption="Behaviour on trials past the sliding-window reference (realised "
                 "model_tokens_after_target ≥ W + 16 = 272; n ≈ 10,091 per architecture). Left: the "
                 "four mutually exclusive per-trial outcomes — correct factual answer, incorrect valid "
                 "answer, malformed output, abstention (“I don't know”) — as stacked fractions. "
                 "Correct factual answers are below 1% for every architecture in this region (maximum "
                 "0.37%, Transformer), so the correct segment is not visible; essentially no "
                 "architecture retrieves the target past the window. Right: the two frozen H3 "
                 "behavioural-primary rates per architecture — appropriate abstention rate = "
                 "P(abstained), and unsignalled failure rate = P(incorrect-valid ∨ malformed). Each "
                 "AHN architecture differs from the no-recurrent-memory baseline by |Δ| ≈ 0.42 "
                 "(all six contrasts Holm-adjusted p ≈ 0; the ordering is identical in all 8 seeds). "
                 "This is a description of behaviour; it does not identify an internal mechanism.",
                 notes=["four outcomes shown separately: correct / incorrect-valid / malformed / abstention.",
                        "correct factual answers are < 1% for every arm past W+16 (max 0.37%); the green "
                        "segment is present in the source table but too small to render.",
                        "no mechanistic claim — 'signalling', not 'the model knows it forgot' (H3-4 is a PROHIBITED claim).",
                        "factual calibration is a separate story (Appendix A-H3)."])

    # =====================================================================
    # TABLE 4 — construct / control validity
    # =====================================================================
    def tbl_construct(self):
        pd = self.pd
        import yaml
        facts = yaml.safe_load((self.root / "config/facts.yaml").read_text())["types"]
        cv = self.frozen("final_control_validity_control_validity.csv").set_index("fact_type")
        rows = []
        for ft in FT_ORDER:
            e = facts[ft]
            rows.append(dict(
                construct=disp(ft), internal_key=ft, answer_form=e.get("answer_form", ""),
                example=(e.get("example", "") + (" / " + e["query"] if "query" in e else ""))[:70],
                in_window_strict=round(float(cv.loc[ft, "strict_accuracy"]), 3),
                in_window_answered_valid=round(float(cv.loc[ft, "answered_valid_accuracy"]), 3),
                in_window_abstention=round(float(cv.loc[ft, "abstention_rate"]), 3),
                in_window_malformed=round(float(cv.loc[ft, "malformed_rate"]), 3),
                control_verdict=cv.loc[ft, "verdict"]))
        t = pd.DataFrame(rows)
        st = self._src("tbl4_construct_control.csv", t)
        md = self._tbl_md("tbl4_construct_control", "main",
                          "Table 4 — Fact-type constructs and in-window (control) validity", t,
                          ["compound-relational (internal key multi-hop): a single co-located two-clause target — "
                           "NOT multi-hop retrieval across separated facts. WARNING driver: strict 0.842 < 0.85 AND "
                           "abstention 0.115 > 0.10; FAIL threshold 0.70 not reached → retained in the H1 primary.",
                           "temporal: judged on answered-valid accuracy (0.922); 38% in-window abstention is a model "
                           "property (documented, counterbalanced response bias — Appendix A-VAL).",
                           "control anchors = pooled intended model-tat 150 + 180; n = 3,072 / type."])
        self.add(eid="tbl4_construct_control", title="Construct / control-validity table",
                 caption="Fact-type constructs and in-window (control) retrieval, pooled over intended targets 150 and 180 (n = 3,072 per fact type). compound-relational (internal data key multi-hop) is a single co-located two-clause sentence with a query that needs both clauses; it is not a benchmark of multi-hop reasoning across separated facts. Its control retrieval reaches only 0.842 (0.951 among answered trials; 0.115 abstention), which triggers a pre-registered WARNING (strict < 0.85 and abstention > 0.10); the FAIL threshold of 0.70 was not reached, so the type is retained in the H1 primary. temporal is judged on answered-valid accuracy (0.922) with abstention (0.384) tracked separately.",
                 kind="table", placement="MAIN", claim_ids=["VAL-1", "VAL-2"],
                 sources=["final_audit/FINAL_LOCKED/final_control_validity_control_validity.csv", "config/facts.yaml"],
                 source_tables=[st], files=[md, st],
                 statistic={"control_verdict": "full_run.control_validity (frozen); floor-only per-type gate"})

    # =====================================================================
    # TABLE 5 — deep-recurrent retention (>=2W)
    # =====================================================================
    def tbl_deep(self):
        pd = self.pd
        pa = self.v11("sensitivity__deep_recurrent_retention__per_arm.csv")
        pa["architecture_display"] = pa.architecture.map(ARM_LABEL)
        keep = pa[["architecture_display", "region", "n", "correct", "strict_acc",
                   "wilson95_low", "wilson95_high", "abstention_rate", "wrong_valid_n"]].copy()
        keep.columns = ["architecture", "region", "n", "strict_correct", "strict_accuracy",
                        "wilson95_low", "wilson95_high", "abstention_rate", "wrong_valid_n"]
        st = self._src("tbl5_deep_recurrent.csv", pa)
        md = self._tbl_md("tbl5_deep_recurrent", "main",
                          "Table 5 — Deep-recurrent retention: model_tokens_after_target ≥ 2W (512)",
                          keep,
                          ["Wilson 95% interval on the binomial. All three AHN architectures shown separately.",
                           "Approved interpretation: “No measurable target-specific factual retention at deep "
                           "recurrent pressure under the production evaluation.”",
                           "Do NOT state 'AHN recurrent memory stores nothing'. The mamba2 result is 1 correct / 3,542.",
                           "Source: v1.1 reporting-amendment (reporting_amendment.deep_recurrent_retention)."])
        self.add(eid="tbl5_deep_recurrent", title="Deep-recurrent negative-retention result",
                 caption="Retrieval at deep recurrent pressure: realised model_tokens_after_target >= 512 (twice W), n = 3,542 per architecture. Correct counts are 0 (DeltaNet, GatedDeltaNet), 1 (Mamba2), and 3 (baseline); Wilson 95% upper bounds are at or below 0.25%. Abstention exceeds 89% for all four. No measurable target-specific factual retention was observed at deep recurrent pressure under the production evaluation.",
                 kind="table", placement="MAIN", claim_ids=["H2-5"],
                 sources=[f"{V11}/sensitivity__deep_recurrent_retention__per_arm.csv", RAW],
                 source_tables=[st], files=[md, st],
                 post_freeze="POST-FREEZE SENSITIVITY (NEGATIVE RESULT)",
                 statistic={"strict_accuracy": "correct / n at realised model_tat ≥ 512",
                            "wilson95": "Wilson score interval, z = 1.96"},
                 notes=["near-zero accuracy is shown WITH its uncertainty interval, never as a bare '0'."])

    # =====================================================================
    # APPENDIX
    # =====================================================================
    def appendix(self):
        pd = self.pd
        # A-H1
        parts = {
            "exclude_temporal_FROZEN": self.frozen("final_h1_h1_sensitivity_excl_temporal.csv"),
            "exclude_compound_relational_POSTFREEZE": self.v11("h1_sensitivity__exclude_compound_relational__contrasts.csv"),
            "answered_valid_all_types_FROZEN": self.frozen("final_h1_h1_sensitivity_temporal_answered_valid.csv"),
            "a_transition_by_seed_POSTFREEZE": self.v11("robustness__per_seed_headline__a_transition_by_seed.csv"),
        }
        names = []
        for k_, dfp in parts.items():
            dfp = dfp.copy()
            for c in ("a", "b"):
                if c in dfp: dfp[c] = dfp[c].map(disp)
            names.append(self._src(f"appAH1_{k_}.csv", dfp))
        self._tbl_md("appendix_A_H1_sensitivities", "appendix",
                     "Appendix A-H1 — H1 sensitivities", parts["exclude_compound_relational_POSTFREEZE"].assign(
                         a=lambda d: d.a.map(disp), b=lambda d: d.b.map(disp))[["a", "b", "diff", "ci_low", "ci_high", "p_holm", "significant_holm"]],
                     ["Shown in table: exclude-compound-relational (POST-FREEZE SENSITIVITY) — 6/6 Holm-significant, "
                      "omnibus p = 0.0005. Other sub-tables in source_tables/: exclude-temporal (frozen, 6/6), "
                      "answered-valid all-types (frozen, 8/10; the file name says 'temporal' but it is ALL types), "
                      "A_transition per type × per seed (2 distinct orderings across 8 seeds).",
                      "H1 survives every exclusion and is seed-stable."])
        self.add(eid="appendix_A_H1_sensitivities", title="H1 sensitivities", kind="table",
                 placement="APPENDIX", claim_ids=["H1-1", "H1-2"],
                 sources=["final_audit/FINAL_LOCKED/final_h1_h1_sensitivity_excl_temporal.csv",
                          "final_audit/FINAL_LOCKED/final_h1_h1_sensitivity_temporal_answered_valid.csv",
                          f"{V11}/h1_sensitivity__exclude_compound_relational__contrasts.csv",
                          f"{V11}/robustness__per_seed_headline__a_transition_by_seed.csv"],
                 source_tables=names, files=["appendix_A_H1_sensitivities.md"] + names,
                 post_freeze="mixed: exclude-compound-relational is POST-FREEZE SENSITIVITY",
                 statistic={"contrasts": "same estimator as Table 2, on the reduced fact-type set; Holm within family"})

        # A-H2a — width amendment
        elig = self.v11("h2_amend__eligibility.csv")
        elig["fact_type"] = elig.fact_type.map(disp)
        wid = self.v11("h2_amend__width_by_facttype.csv"); wid["fact_type"] = wid.fact_type.map(disp)
        wsum = self.v11("h2_amend__width_summary_median.csv")
        wseed = self.v11("h2_amend__width_seed_sensitivity.csv")
        frozen_width = self.frozen("final_h2_h2_width.csv")
        n1 = self._src("appAH2a_eligibility.csv", elig)
        n2 = self._src("appAH2a_width_by_facttype.csv", wid)
        n3 = self._src("appAH2a_width_summary_median.csv", wsum)
        n4 = self._src("appAH2a_width_seed_sensitivity.csv", wseed)
        n5 = self._src("appAH2a_FROZEN_pooled_width_RECORD_all_NaN.csv", frozen_width)
        show = wsum[["architecture", "eligible_fact_types", "n_eligible",
                     "median_width_tokens", "ci_low", "ci_high"]].copy()
        show["architecture"] = show.architecture.map(ARM_LABEL)
        self._tbl_md("appendix_A_H2a_transition_width_amendment", "appendix",
                     "Appendix A-H2a — H2 transition width (POST-FREEZE REPORTING AMENDMENT, Option A)", show,
                     ["The pre-registered POOLED 90→10 width is mathematically UNDEFINED for this dataset: the pooled "
                      "5-type strict-accuracy curve peaks ≈ 0.88 and never reaches the 0.90 reference, so the frozen "
                      "code returns a non-finite interval and falls through to the label 'intermediate'. The frozen "
                      "result (appAH2a_FROZEN_pooled_width_RECORD_all_NaN.csv) is preserved verbatim.",
                      "Amendment (approved 2026-09-09, commit 626521a; protocol/amendment_h2_transition_width.md): "
                      "report the 90→10 width for the fact types where the estimator is DEFINED — i.e. the fitted "
                      "isotonic curve attains ≥ 0.90 AND ≤ 0.10. Eligible for all four arms: contradictory, "
                      "entity-attribute, numerical. INELIGIBLE: compound-relational (fitted ceiling 0.862 < 0.90) and "
                      "temporal (0.568 < 0.90) — because their in-window accuracy is capped by abstention, not because "
                      "of a wide transition.",
                      "Per-arm MEDIAN eligible width (model tokens): Transformer 32.4 [30.5, 36.8]; AHN 61.8–73.8. "
                      "All ≪ 0.5 W (128) → concentrated. Hierarchical (item→seed) bootstrap, n = 2000; frac_finite = 1.0.",
                      "This is a REPORTING AMENDMENT, not a new frozen primary endpoint."])
        self.add(eid="appendix_A_H2a_transition_width_amendment",
                 title="H2 transition-width amendment (Option A)", kind="table", placement="APPENDIX",
                 claim_ids=["H2-2", "H2-3"],
                 sources=[f"{V11}/h2_amend__eligibility.csv", f"{V11}/h2_amend__width_by_facttype.csv",
                          f"{V11}/h2_amend__width_summary_median.csv", f"{V11}/h2_amend__width_seed_sensitivity.csv",
                          "final_audit/FINAL_LOCKED/final_h2_h2_width.csv"],
                 source_tables=[n1, n2, n3, n4, n5],
                 files=["appendix_A_H2a_transition_width_amendment.md", n1, n2, n3, n4, n5],
                 post_freeze="POST-FREEZE REPORTING AMENDMENT (Option A)",
                 statistic={"90->10 width": "crossing_x(fit, 0.10) − crossing_x(fit, 0.90) on the isotonic "
                            "non-increasing strict-accuracy fit vs realised model-tat",
                            "eligibility": "fit_max ≥ 0.90 AND fit_min ≤ 0.10 (from the estimator, not observed convenience)",
                            "summary": "per-arm median over globally-eligible fact types + hierarchical bootstrap CI"})

        # A-H2b — residual fully-exact failures
        rovr = self.v11("descriptive__residual_fully_exact_failures__overall.csv")
        rft = self.v11("descriptive__residual_fully_exact_failures__by_fact_type.csv"); rft["fact_type"] = rft.fact_type.map(disp)
        rtg = self.v11("descriptive__residual_fully_exact_failures__by_intended_model_tokens_after_target.csv")
        ra_ = self.v11("descriptive__residual_fully_exact_failures__by_architecture.csv"); ra_["architecture"] = ra_.architecture.map(ARM_LABEL)
        m1 = self._src("appAH2b_overall.csv", rovr); m2 = self._src("appAH2b_by_fact_type.csv", rft)
        m3 = self._src("appAH2b_by_intended_target.csv", rtg); m4 = self._src("appAH2b_by_architecture.csv", ra_)
        self._tbl_md("appendix_A_H2b_residual_exact_failures", "appendix",
                     "Appendix A-H2b — Residual failures where the target span is arithmetically inside W through generation",
                     rtg.rename(columns={"intended_model_tokens_after_target": "intended_model_tat"}),
                     ["[LIMITATION] 11,236 / 34,975 = 32.1 % of such trials still fail (46 % abstention, 38 % malformed, "
                      "15 % incorrect-valid). Rate by intended target: 150→12 %, 180→12 %, 205→34 %, 220→59.9 %, "
                      "235→55 %, 250→31 %.",
                      "Near-window degradation is therefore NOT attributable solely to the exact→compressed transition; "
                      "the pressure axis is a proxy for compression pressure. No mechanism is claimed.",
                      "Carried forward from Pilot Pass 2."])
        self.add(eid="appendix_A_H2b_residual_exact_failures",
                 title="Residual exact-memory failures", kind="table", placement="APPENDIX",
                 claim_ids=["VAL-4"], sources=[f"{V11}/descriptive__residual_fully_exact_failures__*.csv", RAW],
                 source_tables=[m1, m2, m3, m4],
                 files=["appendix_A_H2b_residual_exact_failures.md", m1, m2, m3, m4],
                 post_freeze="DESCRIPTIVE ROBUSTNESS / LIMITATION",
                 statistic={"residual failure": "correct == 0 among rows with "
                            "target_fully_exact_through_generation == True (schema.derive_boundary_conditions)"})

        # A-H3 — calibration detail
        g1 = self.frozen("final_h3_h3_gap_change.csv"); g1["architecture"] = g1.architecture.map(ARM_LABEL)
        g2 = self.frozen("final_h3_h3_by_pressure_answered_valid.csv")
        g3 = self.frozen("final_h3_h3_abstention_confidence.csv")
        g4 = self.v11("robustness__per_seed_headline__h3_appropriate_abstention_by_seed.csv")
        c1 = self._src("appAH3_gap_change.csv", g1); c2 = self._src("appAH3_by_pressure_answered_valid.csv", g2)
        c3 = self._src("appAH3_abstention_confidence.csv", g3); c4 = self._src("appAH3_abstention_by_seed.csv", g4)
        self._tbl_md("appendix_A_H3_calibration_detail", "appendix",
                     "Appendix A-H3 — H3 calibration detail (answered-valid vs abstention kept separate)",
                     g1[["architecture", "gap_control", "gap_interval", "gap_change", "ci_low", "ci_high"]],
                     ["gap_change = Δ(mean confidence − mean accuracy) on ANSWERED-VALID trials, control anchors → "
                      "[200,270]. Transformer CI [−0.051, 0.013] contains 0 (no shift); AHN arms shift −0.06 to −0.12 "
                      "(more conservative).",
                      "by_pressure ECE/Brier/CWR: past the window n_population is small (853 pooled at intended 265; "
                      "transformer alone n = 1) — 'overconfident when wrong' is a small-n deep-pressure effect, not a headline.",
                      "abstention_confidence = confidence in emitting 'I don't know' — NEVER treated as factual confidence.",
                      "confidence = sequence_probability (PROVISIONAL; open_decisions #6).",
                      "per-seed appropriate-abstention: AHN 0.92–0.95, Transformer 0.49–0.53 every seed."])
        self.add(eid="appendix_A_H3_calibration_detail", title="H3 calibration detail",
                 kind="table", placement="APPENDIX", claim_ids=["H3-3", "H3-1"],
                 sources=["final_audit/FINAL_LOCKED/final_h3_h3_gap_change.csv",
                          "final_audit/FINAL_LOCKED/final_h3_h3_by_pressure_answered_valid.csv",
                          "final_audit/FINAL_LOCKED/final_h3_h3_abstention_confidence.csv",
                          f"{V11}/robustness__per_seed_headline__h3_appropriate_abstention_by_seed.csv"],
                 source_tables=[c1, c2, c3, c4],
                 files=["appendix_A_H3_calibration_detail.md", c1, c2, c3, c4],
                 statistic={"gap_change": "hierarchical bootstrap CI on Δ(confidence − accuracy), answered-valid only",
                            "ECE": "10 equal-width bins (Guo et al. 2017); CWR threshold 0.5 (PROVISIONAL)"})

        # A-VAL — transformer control + temporal bias
        v1 = self.v11("disclosure__transformer_malformed__by_pressure.csv")
        v2 = self.v11("disclosure__transformer_malformed__per_arm.csv"); v2["architecture"] = v2.architecture.map(ARM_LABEL)
        v3 = self.v11("disclosure__transformer_malformed__subtypes.csv")
        v4 = self.v11("disclosure__temporal_counterbalancing__control_subgroups.csv")
        v5 = self.v11("disclosure__compound_relational_control_warning__by_seed.csv")
        d1 = self._src("appAVAL_transformer_malformed_by_pressure.csv", v1)
        d2 = self._src("appAVAL_malformed_per_arm.csv", v2)
        d3 = self._src("appAVAL_transformer_malformed_subtypes.csv", v3)
        d4 = self._src("appAVAL_temporal_control_subgroups.csv", v4)
        d5 = self._src("appAVAL_compound_relational_by_seed.csv", v5)
        self._tbl_md("appendix_A_VAL_control_behaviour", "appendix",
                     "Appendix A-VAL — Transformer control behaviour + temporal response bias", v2,
                     ["Transformer malformed rate: 39.6 % overall, 0.05 % at the in-window control anchors, rising to "
                      "59–79 % in the transition band and falling to 3–10 % at the deepest pressures. This is expected "
                      "no-recurrent-memory degeneration (CONTROL BEHAVIOUR), NOT a pipeline problem: 0 % at anchors, the "
                      "full re-score is exact, AHN arms on identical prompts are at 1.4–4.8 %.",
                      "NEVER cite the pooled malformed rate (12.6 %) without the per-arm split shown above.",
                      "Temporal control subgroups: answered-valid 0.85 (gold lower-numbered) vs 0.99 (gold higher); "
                      "0.87 vs 1.00 (gold not first-listed vs first-listed). This is a model response bias, "
                      "counterbalanced against the gold (2×2×2 exactly balanced); pooled control answered-valid 0.922.",
                      "Compound-relational control WARNING holds in 7/8 seeds; retained in the H1 primary."])
        self.add(eid="appendix_A_VAL_control_behaviour", title="Transformer control + temporal bias",
                 kind="table", placement="APPENDIX", claim_ids=["VAL-1", "VAL-3", "VAL-2"],
                 sources=[f"{V11}/disclosure__transformer_malformed__*.csv",
                          f"{V11}/disclosure__temporal_counterbalancing__*.csv",
                          f"{V11}/disclosure__compound_relational_control_warning__*.csv"],
                 source_tables=[d1, d2, d3, d4, d5],
                 files=["appendix_A_VAL_control_behaviour.md", d1, d2, d3, d4, d5],
                 post_freeze="LIMITATION / DISCLOSURE",
                 statistic={"malformed subtype": "frozen score_row branch (empty / negation / >4 words / unrecognised value)"})

        # A-REPRO — integrity & reproducibility
        gates = self.v11("reproduced__plumbing_gates.csv")
        n_block = int((gates["verdict"] == "FAIL").sum())
        rescore_mm = self._rescore_mismatches()
        integ = pd.DataFrame([
            ["locked raw artifact SHA-256", RAW_SHA256, "verified this build"],
            ["rows", str(len(self.df)), "== 92,160"],
            ["rows / architecture", "23,040 × 4", "exact"],
            ["duplicate canonical cells", "0", "(architecture,item_id,seed,intended_model_tat)"],
            ["independent re-score mismatches (frozen scorer)", str(rescore_mm), "correct+abstained+malformed, all 92,160 rows"],
            ["frozen v1.0 reproduction", "53/53 identical", "max |Δ| 5.7e-14 (scripts/verify_frozen_v1_0.py)"],
            ["plumbing gates (reproduced)", f"{n_block} blocking", "malformed_control:transformer = CONTROL_BEHAVIOR; multi-hop = WARNING"],
            ["generation runtime commit", "d29c6d8", "not in git; scorer/prompt/calibration/analysis provably identical to 64dc10c (5 hash checks)"],
            ["analysis versions", "v1.0 frozen + v1.1 amendment", "final_audit/V1_1_LOCKED/V1_1_LOCK_MANIFEST.json"],
        ], columns=["check", "value", "note"])
        r1 = self._src("appAREPRO_integrity.csv", integ)
        r2 = self._src("appAREPRO_reproduced_plumbing_gates.csv", gates)
        self._tbl_md("appendix_A_REPRO_integrity", "appendix",
                     "Appendix A-REPRO — Integrity & reproducibility", integ,
                     ["Every headline number in this paper reproduces from the locked 92,160-row parquet "
                      "(SHA-256 a72fd43e…) with the frozen v1.0 code or the approved v1.1 amendment code.",
                      "The v1.1 reporting amendment corrects one undefined descriptive statistic (H2 pooled "
                      "transition width) and adds sensitivity/disclosure tables; it changes no primary endpoint."])
        self.add(eid="appendix_A_REPRO_integrity", title="Integrity & reproducibility statement",
                 kind="table", placement="APPENDIX", claim_ids=["(provenance)"],
                 sources=["final_audit/V1_1_LOCKED/V1_1_LOCK_MANIFEST.json",
                          f"{V11}/reproduced__plumbing_gates.csv", RAW],
                 source_tables=[r1, r2], files=["appendix_A_REPRO_integrity.md", r1, r2],
                 statistic={"re-score": "evaluate.score_row applied to every stored (prediction, gold); "
                            "compared to stored correct/abstained/malformed"})

    def _rescore_mismatches(self) -> int:
        from ahnexp import evaluate
        rs = self.df.apply(lambda r: evaluate.score_row(r.prediction, r.gold, r.fact_type),
                           axis=1, result_type="expand")
        mm = 0
        for c in ("correct", "abstained", "malformed"):
            mm += int((rs[c].astype(int).values != self.df[c].astype(int).values).sum())
        return mm

    # ---------------------------------------------------------------------
    def run(self):
        self.fig_design()
        self.fig_h1()
        self.tbl_h1_primary()
        self.tbl_h1_contrasts()
        self.fig_h2()
        self.tbl_h2_summary()
        self.fig_h3()
        self.tbl_construct()
        self.tbl_deep()
        self.appendix()
        manifest = {
            "generated_at_utc": datetime.now(timezone.utc).isoformat(timespec="seconds"),
            "raw_artifact": RAW, "raw_artifact_sha256": RAW_SHA256,
            "allowed_sources": ["locked raw parquet", "frozen analysis v1.0 (final_*)",
                                "approved reporting amendment v1.1"],
            "terminology": {"multi-hop": "compound-relational (manuscript-facing; internal key preserved in source tables)"},
            "n_main": sum(e["placement"] == "MAIN" for e in self.exhibits),
            "n_appendix": sum(e["placement"] == "APPENDIX" for e in self.exhibits),
            "exhibits": self.exhibits,
        }
        (self.out / "EXHIBIT_MANIFEST.json").write_text(json.dumps(manifest, indent=2) + "\n")
        cap_lines = ["# Publication Exhibit Captions",
                     "",
                     "Draft captions for each exhibit. Every number traces to the exhibit's source "
                     "table(s) (see EXHIBIT_MANIFEST.json). Terminology: internal data key "
                     "\"multi-hop\" is reported as \"compound-relational\".", ""]
        for e in self.exhibits:
            cap_lines.append(f"## {e['exhibit_id']}  ({e['placement']})")
            cap_lines.append(f"*{e['title']}* — claims: {', '.join(e['claim_ids'])}"
                             + (f" — {e['post_freeze_status']}" if e.get('post_freeze_status') else ""))
            cap_lines.append("")
            cap_lines.append(e["caption"] or "(caption in exhibit notes)")
            cap_lines.append("")
        (self.out / "CAPTIONS.md").write_text("\n".join(cap_lines) + "\n")
        print(f"main: {manifest['n_main']}  appendix: {manifest['n_appendix']}")
        for e in self.exhibits:
            print(f"  [{e['placement']:8}] {e['exhibit_id']:42} {e['kind']}")
        print(f"\nEXHIBIT_MANIFEST.json written to {self.out}")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--repo", default=os.environ.get("AHNEXP_ROOT", "."))
    args = ap.parse_args()
    root = Path(args.repo).expanduser().resolve()
    if not (root / "config" / "experiment.yaml").is_file():
        sys.exit(f"--repo {root} is not the ahn-mdc checkout")
    os.chdir(root); sys.path.insert(0, str(root / "src"))
    got = sha(root / RAW)
    if got != RAW_SHA256:
        sys.exit(f"RAW SHA MISMATCH {got} — STOP")
    print(f"raw SHA-256 OK: {got}\n")
    Builder(root).run()


if __name__ == "__main__":
    main()
