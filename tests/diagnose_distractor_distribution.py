"""Diagnostic — distractor distributions on the production dataset path.

Read-only. Does not modify dataset.py / evaluate.py / configs. No torch, no GPU.

    python tests/diagnose_distractor_distribution.py [N] [POOL]     # default N=500, POOL=2000

Characterises, over N generated target items for seeds 0/1/2, the distractor pools
built by ``ahnexp.dataset.generate_items`` -> ``_distractor_pool`` (the exact
production path; the categorical generators run with slot=None there, i.e. the
old ``LIST[i % 5]`` selection).

Reports:
  * colour frequency among entity-attribute distractors
  * company frequency among multi-hop distractors
  * new-city and old-city frequency among contradictory distractors
  * distractor fact-type mix by target fact type
  * distractor fact-type mix by distractor-density condition
  * whether any categorical distractor value is substantially overrepresented
  * target-gold x distractor-value cross-tabs (is answer balancing correlated
    with a skewed distractor distribution?)
"""

from __future__ import annotations

import sys
from collections import Counter, defaultdict
from pathlib import Path

_ROOT = Path(__file__).resolve().parents[1]
if str(_ROOT / "src") not in sys.path:
    sys.path.insert(0, str(_ROOT / "src"))

from ahnexp import dataset

SEEDS = (0, 1, 2)
CATS = ["numerical", "temporal", "entity-attribute", "multi-hop", "contradictory"]
COLORS, COMPANIES = dataset.COLORS, dataset.COMPANIES
CITIES_FROM, CITIES_TO = dataset.CITIES_FROM, dataset.CITIES_TO


def _old_city(text: str) -> str:
    # "Person_X lived in <old>. Person_X now lives in <new>."
    return text.split(" lived in ", 1)[1].split(".", 1)[0]


def _pct_table(counter: Counter, space) -> str:
    total = sum(counter.get(k, 0) for k in space) or 1
    parts = [f"{k}={counter.get(k, 0)} ({100 * counter.get(k, 0) / total:5.1f}%)" for k in space]
    return "  ".join(parts)


def _uniformity(counter: Counter, space) -> tuple[float, float]:
    total = sum(counter.get(k, 0) for k in space)
    exp = total / len(space)
    if exp == 0:
        return 0.0, 0.0
    chi2 = sum((counter.get(k, 0) - exp) ** 2 / exp for k in space)
    max_dev = max(abs(100 * counter.get(k, 0) / total - 100 / len(space)) for k in space)
    return chi2, max_dev


def analyse_seed(seed: int, n_items: int, pool: int) -> dict:
    items = dataset.generate_items(n_items=n_items, seed=seed, pool_size=pool)

    color_all: Counter = Counter()
    company_all: Counter = Counter()
    newcity_all: Counter = Counter()
    oldcity_all: Counter = Counter()
    type_mix_by_target: dict[str, Counter] = defaultdict(Counter)
    same_share: dict[tuple, Counter] = defaultdict(Counter)  # (target_type, density) -> {same, tot}
    color_by_gold: dict[str, Counter] = defaultdict(Counter)
    company_by_gold: dict[str, Counter] = defaultdict(Counter)
    newcity_by_gold: dict[str, Counter] = defaultdict(Counter)
    gold_selfleak = Counter()          # same-type distractor whose value == target gold
    same_type_distractors = Counter()  # denominator for the above
    gold_x_density = defaultdict(Counter)
    n_distractors = 0

    for it in items:
        tt = it.fact.fact_type
        gold_x_density[tt][(it.fact.answer, it.distractor_density)] += 1
        for d in it.distractors:
            n_distractors += 1
            dt = d.fact_type
            type_mix_by_target[tt][dt] += 1
            same_share[(tt, it.distractor_density)]["tot"] += 1
            if dt == tt:
                same_type_distractors[tt] += 1
                same_share[(tt, it.distractor_density)]["same"] += 1
            if dt == "entity-attribute":
                color_all[d.answer] += 1
                if tt == "entity-attribute":
                    color_by_gold[it.fact.answer][d.answer] += 1
                    if d.answer == it.fact.answer:
                        gold_selfleak["entity-attribute"] += 1
            elif dt == "multi-hop":
                company_all[d.answer] += 1
                if tt == "multi-hop":
                    company_by_gold[it.fact.answer][d.answer] += 1
                    if d.answer == it.fact.answer:
                        gold_selfleak["multi-hop"] += 1
            elif dt == "contradictory":
                newcity_all[d.answer] += 1
                oldcity_all[_old_city(d.text)] += 1
                if tt == "contradictory":
                    newcity_by_gold[it.fact.answer][d.answer] += 1
                    if d.answer == it.fact.answer:
                        gold_selfleak["contradictory"] += 1

    return dict(
        seed=seed, n_items=len(items), n_distractors=n_distractors,
        color_all=color_all, company_all=company_all,
        newcity_all=newcity_all, oldcity_all=oldcity_all,
        type_mix_by_target=type_mix_by_target, same_share=same_share,
        color_by_gold=color_by_gold, company_by_gold=company_by_gold,
        newcity_by_gold=newcity_by_gold,
        gold_selfleak=gold_selfleak, same_type_distractors=same_type_distractors,
        gold_x_density=gold_x_density,
    )


def print_seed(r: dict) -> None:
    print(f"\n{'=' * 100}\nseed {r['seed']}  —  {r['n_items']} targets, {r['n_distractors']:,} distractor facts\n{'=' * 100}")

    print("\n[1] entity-attribute distractor COLOUR frequency (all targets)")
    print("   ", _pct_table(r["color_all"], COLORS))
    chi2, dev = _uniformity(r["color_all"], COLORS)
    print(f"    chi2(df=4)={chi2:6.2f}   max deviation from 20.0% = {dev:.2f} pts")

    print("\n[2] multi-hop distractor COMPANY frequency (all targets)")
    print("   ", _pct_table(r["company_all"], COMPANIES))
    chi2, dev = _uniformity(r["company_all"], COMPANIES)
    print(f"    chi2(df=4)={chi2:6.2f}   max deviation from 20.0% = {dev:.2f} pts")

    print("\n[3a] contradictory distractor NEW/current city frequency (all targets)")
    print("   ", _pct_table(r["newcity_all"], CITIES_TO))
    chi2, dev = _uniformity(r["newcity_all"], CITIES_TO)
    print(f"    chi2(df=4)={chi2:6.2f}   max deviation from 20.0% = {dev:.2f} pts")
    print("[3b] contradictory distractor OLD/superseded city frequency (all targets)")
    print("   ", _pct_table(r["oldcity_all"], CITIES_FROM))
    chi2, dev = _uniformity(r["oldcity_all"], CITIES_FROM)
    print(f"    chi2(df=4)={chi2:6.2f}   max deviation from 20.0% = {dev:.2f} pts")

    print("\n[4] distractor fact-type mix BY TARGET fact type (row-normalised %)")
    print(f"    {'target ↓':<18} " + "  ".join(f"{c[:9]:>9}" for c in CATS))
    for tt in CATS:
        row = r["type_mix_by_target"][tt]
        tot = sum(row.values()) or 1
        print(f"    {tt:<18} " + "  ".join(f"{100 * row.get(c, 0) / tot:8.1f}%" for c in CATS))

    print("\n[5] share of a target's distractors that are its OWN fact type, by density")
    print(f"    (design: P(same|low)=0.20, P(same|high)=0.8+0.2*0.2=0.84)")
    print(f"    {'target ↓':<18} {'low':>8} {'high':>8}")
    for tt in CATS:
        lo, hi = r["same_share"][(tt, "low")], r["same_share"][(tt, "high")]
        lo_p = 100 * lo["same"] / (lo["tot"] or 1)
        hi_p = 100 * hi["same"] / (hi["tot"] or 1)
        print(f"    {tt:<18} {lo_p:7.1f}% {hi_p:7.1f}%")

    print("\n[6] self-leak: same-type distractors whose value == the target's own gold")
    for ft in ("entity-attribute", "multi-hop", "contradictory"):
        denom = r["same_type_distractors"][ft]
        n = r["gold_selfleak"][ft]
        print(f"    {ft:<18} {n} / {denom:,} same-type distractors  ({100 * n / (denom or 1):.3f}%)")

    print("\n[7] target-gold  ×  distractor-value  (entity-attribute; row = target gold colour, % of that target's colour-distractors)")
    print(f"    {'gold ↓':<10} " + "  ".join(f"{c:>8}" for c in COLORS))
    for g in COLORS:
        row = r["color_by_gold"][g]
        tot = sum(row.values()) or 1
        print(f"    {g:<10} " + "  ".join(f"{100 * row.get(c, 0) / tot:7.1f}%" for c in COLORS))

    print("\n[8] target-gold  ×  density  (counts; is answer balancing correlated with density?)")
    for ft in ("entity-attribute", "multi-hop", "contradictory"):
        cells = r["gold_x_density"][ft]
        golds = sorted({g for g, _ in cells})
        line = "  ".join(f"{g}:{cells.get((g, 'low'), 0)}L/{cells.get((g, 'high'), 0)}H" for g in golds)
        print(f"    {ft:<18} {line}")


def main() -> None:
    n_items = int(sys.argv[1]) if len(sys.argv) > 1 else 500
    pool = int(sys.argv[2]) if len(sys.argv) > 2 else 2000

    print(f"production path: dataset.generate_items(n_items={n_items}, pool_size={pool}) for seeds {SEEDS}")
    worst_dev = 0.0
    results = []
    for seed in SEEDS:
        r = analyse_seed(seed, n_items, pool)
        results.append(r)
        print_seed(r)
        for counter, space in (
            (r["color_all"], COLORS), (r["company_all"], COMPANIES),
            (r["newcity_all"], CITIES_TO), (r["oldcity_all"], CITIES_FROM),
        ):
            _, dev = _uniformity(counter, space)
            worst_dev = max(worst_dev, dev)

    print(f"\n{'=' * 100}")
    print(f"worst aggregate categorical-value deviation from uniform, across all seeds: {worst_dev:.2f} pts")
    selfleak_total = sum(r["gold_selfleak"].total() if hasattr(r["gold_selfleak"], "total")
                         else sum(r["gold_selfleak"].values()) for r in results)
    print(f"total self-leaks (target gold appearing as its own same-type distractor): {selfleak_total}")
    print("=" * 100)


if __name__ == "__main__":
    main()
