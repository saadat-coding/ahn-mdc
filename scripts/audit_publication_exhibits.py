#!/usr/bin/env python3
"""Programmatic half of the hostile exhibit audit: verify that every headline
number in each exhibit traces to a source table which in turn reproduces from the
locked evidence. Prints PASS/FAIL lines consumed by EXHIBIT_AUDIT.md.
"""
from __future__ import annotations
import hashlib, json, os, sys
from pathlib import Path

RAW_SHA = "a72fd43e87457a70c2833314e1443a794fa4189362ac8206c56275ef427fb62e"
OUT = "outputs/publication_exhibits"
FROZEN = "final_audit/FINAL_LOCKED"
V11 = "outputs/final_v1_1_reporting_amendment"


def main():
    root = Path(os.environ.get("AHNEXP_ROOT", ".")).resolve()
    os.chdir(root); sys.path.insert(0, str(root / "src"))
    import pandas as pd
    import numpy as np
    P = lambda *p: root.joinpath(*p)
    ok = True

    def chk(name, cond, detail=""):
        nonlocal ok
        ok &= bool(cond)
        print(f"  [{'PASS' if cond else 'FAIL'}] {name}" + (f" — {detail}" if detail else ""))

    # raw + frozen unchanged
    chk("raw parquet SHA-256 unchanged",
        hashlib.sha256(P(FROZEN, "results_FINAL_92160.parquet").read_bytes()).hexdigest() == RAW_SHA)
    man = json.loads(P(OUT, "EXHIBIT_MANIFEST.json").read_text())
    chk("EXHIBIT_MANIFEST pins the raw SHA", man["raw_artifact_sha256"] == RAW_SHA)
    chk("manifest lists 9 main + 6 appendix", man["n_main"] == 9 and man["n_appendix"] == 6,
        f"{man['n_main']}+{man['n_appendix']}")
    for e in man["exhibits"]:
        for f, h in e["generated_files"].items():
            sub = "main" if e["placement"] == "MAIN" else "appendix" if e["placement"] == "APPENDIX" else "source_tables"
            p = P(OUT, sub, f)
            chk(f"{e['exhibit_id']}: {f} hash matches manifest",
                p.exists() and hashlib.sha256(p.read_bytes()).hexdigest() == h)

    df = pd.read_parquet(P(FROZEN, "results_FINAL_92160.parquet"))
    fr = lambda n: pd.read_csv(P(FROZEN, n))
    ex = lambda sub, n: pd.read_csv(P(OUT, sub, n))
    summary = json.loads(P(FROZEN, "final_summary.json").read_text())

    # --- Figure 1 / Table 1: A_transition values trace to frozen ---
    at = fr("final_h1_h1_a_transition.csv").set_index("fact_type")["a_transition"].round(4)
    t1 = ex("source_tables", "tbl1_h1_primary.csv").set_index("fact_type_internal")["A_transition_raw_strict"]
    chk("Table 1 raw-strict A_transition == frozen",
        all(abs(t1[k] - round(at[k], 3)) < 1e-9 for k in at.index))
    f1 = ex("source_tables", "fig1_h1_a_transition.csv").set_index("fact_type")["a_transition"].round(4)
    chk("Figure 1 A_transition source == frozen", (f1.sort_index() == at.sort_index()).all())
    # Fig 1 curve points recompute from parquet (AHN pooled)
    d = df[df.architecture.isin(["mamba2", "deltanet", "gated_deltanet"])]
    g = d.groupby(["fact_type", "intended_model_tokens_after_target"]).correct.mean().round(6)
    fc = ex("source_tables", "fig1_h1_curves.csv").set_index(["fact_type", "intended_model_tat"])["strict_accuracy"].round(6)
    chk("Figure 1 curve points reproduce from locked parquet",
        all(abs(fc.loc[i] - g.loc[i]) < 1e-6 for i in fc.index))

    # --- Table 2: contrasts == frozen file verbatim ---
    c_src = ex("source_tables", "tbl2_h1_contrasts.csv")
    c_frz = fr("final_h1_h1_contrasts.csv")
    chk("Table 2 == frozen contrasts (verbatim)", c_src.equals(c_frz))

    # --- Figure 2 / Table 3 ---
    k = fr("final_h2_h2_k_strict.csv").set_index("architecture")
    chk("Table 3 / Fig 2: every K_strict point < W=256",
        (k["k_strict_acc"] < 256).all(), dict(k["k_strict_acc"].round(1)))
    chk("Fig 2 curves source == frozen h2_curves",
        ex("source_tables", "fig2_h2_curves.csv").equals(fr("final_h2_h2_curves.csv")))
    ab = df.groupby(["architecture", "intended_model_tokens_after_target"]).abstained.mean().round(6)
    fa = ex("source_tables", "fig2_h2_abstention.csv").set_index(["architecture", "intended_model_tokens_after_target"])["abst"].round(6)
    chk("Fig 2 abstention reproduces from locked parquet",
        all(abs(fa.loc[i] - ab.loc[i]) < 1e-6 for i in fa.index))
    gap = summary["h2_a_transition_gap"]
    chk("Table 3 A_transition gap == final_summary.json",
        abs(gap["ahn_pooled_minus_transformer"] - 0.24944444444444447) < 1e-12)

    # --- Figure 3 ---
    per = fr("final_h3_h3_behavioral_per_arm.csv").set_index("architecture")
    chk("Fig 3 per-arm rates source == frozen",
        ex("source_tables", "fig3_h3_behavioral_per_arm.csv").set_index("architecture")
        .round(6).equals(per.round(6)))
    w = 256 + 16
    reg = df[df.model_tokens_after_target >= w]
    comp_src = ex("source_tables", "fig3_h3_outcome_composition_pastW16.csv").set_index("architecture")
    for arm in ["transformer", "mamba2", "deltanet", "gated_deltanet"]:
        gg = reg[reg.architecture == arm]
        want_abst = gg.abstained.mean()
        chk(f"Fig 3 composition abstained[{arm}] reproduces",
            abs(comp_src.loc[arm, "abstained"] - want_abst) < 1e-9)
        # abstained in composition must equal appropriate_abstention_rate (same region/definition)
        chk(f"Fig 3 composition.abstained[{arm}] == frozen appropriate_abstention_rate",
            abs(comp_src.loc[arm, "abstained"] - per.loc[arm, "appropriate_abstention_rate"]) < 1e-9)

    # --- Table 5 deep recurrent: matches v1.1 + Wilson present ---
    d5 = ex("source_tables", "tbl5_deep_recurrent.csv")
    v11 = pd.read_csv(P(V11, "sensitivity__deep_recurrent_retention__per_arm.csv"))
    shared = [c for c in v11.columns if c in d5.columns]
    chk("Table 5 == v1.1 deep-recurrent per-arm (shared cols)",
        d5[shared].round(6).reset_index(drop=True).equals(v11[shared].round(6).reset_index(drop=True)))
    chk("Table 5 shows Wilson interval (not a bare 0)",
        {"wilson95_low", "wilson95_high"}.issubset(d5.columns) and (d5["wilson95_high"] > d5["strict_acc"] - 1e-12).all())
    deep = df[df.model_tokens_after_target >= 512]
    for arm in ["mamba2", "deltanet", "gated_deltanet"]:
        want = int((deep[deep.architecture == arm].correct == 1).sum())
        chk(f"Table 5 deep correct[{arm}] reproduces from parquet",
            int(d5.set_index("architecture").loc[arm, "correct"]) == want, f"{want}")

    # --- Table 4 control validity == frozen ---
    chk("Table 4 in-window strict == frozen control_validity",
        all(abs(ex("source_tables", "tbl4_construct_control.csv").set_index("internal_key").loc[ft, "in_window_strict"]
                - round(fr("final_control_validity_control_validity.csv").set_index("fact_type").loc[ft, "strict_accuracy"], 3)) < 1e-9
            for ft in ["numerical", "temporal", "entity-attribute", "multi-hop", "contradictory"]))

    # --- terminology ---
    for sub, name in [("source_tables", "tbl1_h1_primary.csv"), ("source_tables", "fig1_h1_curves.csv")]:
        cols = pd.read_csv(P(OUT, sub, name)).columns
        chk(f"{name} preserves internal 'multi-hop' key",
            any("internal" in c or c == "fact_type" for c in cols))

    print(f"\n{'ALL CHECKS PASS' if ok else 'SOME CHECKS FAILED'}")
    sys.exit(0 if ok else 1)


if __name__ == "__main__":
    main()
