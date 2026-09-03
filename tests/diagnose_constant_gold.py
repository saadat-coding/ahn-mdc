"""Diagnostic — gold-answer diversity of the production item generator.

Read-only. No torch, no GPU.

    python tests/diagnose_constant_gold.py [N]        # default N = 500

For seeds 0, 1, 2 it prints, per fact type: item count, unique gold count, the
gold->frequency table, the share held by the most common gold, and the accuracy a
blind "always predict the most common gold" baseline would score. Then it shows
the mechanism that used to make the three categorical types collapse and that the
fix (a per-fact-type answer slot) now avoids.

History: with ``fact_type = types[index % 5]`` feeding the global ``index`` into
generators that pick ``LIST[i % 5]``, every entity-attribute / multi-hop /
contradictory item shared one gold ('red' / 'Meta' / 'Dubai'). Fixed in
``ahnexp.dataset`` by choosing categorical answers from ``slot_counter[fact_type]``.
"""

from __future__ import annotations

import sys
from collections import Counter
from pathlib import Path

_ROOT = Path(__file__).resolve().parents[1]
if str(_ROOT / "src") not in sys.path:
    sys.path.insert(0, str(_ROOT / "src"))

from ahnexp import dataset

FACT_TYPES = ["numerical", "temporal", "entity-attribute", "multi-hop", "contradictory"]
CATEGORICAL = {"entity-attribute", "multi-hop", "contradictory"}
POOL_SIZE_FAST = 64  # gold answers are independent of pool_size; keep the diagnostic quick


def _report(items, label: str) -> dict[str, dict]:
    print(f"\n{'=' * 92}\n{label}\n{'=' * 92}")
    print(f"{'fact type':<18} {'items':>6} {'uniq':>5} {'top gold':>16} {'top n':>7} "
          f"{'top %':>8} {'blind acc':>10}")
    print("-" * 92)
    out: dict[str, dict] = {}
    for ft in FACT_TYPES:
        golds = [it.fact.answer for it in items if it.fact.fact_type == ft]
        freq = Counter(golds)
        n = len(golds)
        top_gold, top_n = freq.most_common(1)[0]
        top_pct = 100.0 * top_n / n
        out[ft] = {"n": n, "unique": len(freq), "freq": freq, "top_pct": top_pct}
        flag = "  <-- COLLAPSED" if len(freq) == 1 and ft in CATEGORICAL else ""
        print(f"{ft:<18} {n:>6} {len(freq):>5} {top_gold!r:>16} {top_n:>7} "
              f"{top_pct:>7.1f}% {top_pct:>9.1f}%{flag}")
    print("-" * 92)
    print("full gold distributions:")
    for ft in FACT_TYPES:
        freq = out[ft]["freq"]
        shown = ", ".join(f"{g}:{c}" for g, c in freq.most_common(8))
        more = "" if len(freq) <= 8 else f"  (+{len(freq) - 8} more unique golds)"
        print(f"  {ft:<18} {shown}{more}")
    return out


def _explain_mechanism(n_items: int) -> None:
    print(f"\n{'=' * 92}\nMECHANISM — why balanced fact-type assignment must not feed the generator index\n{'=' * 92}")
    types = list(dataset.GENERATORS)
    print(f"generate_items: fact_type = types[index % {len(types)}]   (types = {types})\n")

    print("1. indices per fact type, reduced mod len(types) — invariant within a type:")
    for ft in FACT_TYPES:
        idxs = [i for i in range(n_items) if types[i % len(types)] == ft]
        mods = sorted({i % len(types) for i in idxs})
        print(f"   {ft:<18} indices {idxs[:6]}...  ->  index % {len(types)} in {mods}")

    print("\n2. answer rule per generator:")
    print("   numerical(i)        -> str(100000 + i*137)   linear      -> varies")
    print("   temporal(i)         -> Person_i              linear      -> varies")
    print("   entity_attribute    -> COLORS[slot % 5]      slot-driven -> balanced (was i % 5 -> constant)")
    print("   multi_hop           -> COMPANIES[slot % 5]   slot-driven -> balanced (was i % 5 -> constant)")
    print("   contradictory       -> CITIES_TO[slot % 5]   slot-driven -> balanced (was i % 5 -> constant)")

    print("\n3. the fix: slot = slot_counter[fact_type] (0,1,2,... within each type).")
    print("   It is the within-type position, so it cannot be congruent to a fixed")
    print("   residue mod 5 the way the global index is. Counterfactual on the raw generators:")
    for ft in FACT_TYPES:
        idxs = [i for i in range(n_items) if types[i % len(types)] == ft]
        gen = dataset.GENERATORS[ft]
        as_index = {gen(i).answer for i in idxs}
        as_slot = {(gen(i, k).answer if ft in CATEGORICAL else gen(i).answer)
                   for k, i in enumerate(idxs)}
        print(f"   {ft:<18} unique golds  index-fed: {len(as_index):>3}   slot-fed: {len(as_slot):>3}")


def main() -> None:
    n_items = int(sys.argv[1]) if len(sys.argv) > 1 else 500

    stats_by_seed = {}
    for seed in (0, 1, 2):
        items = dataset.generate_items(n_items=n_items, seed=seed, pool_size=POOL_SIZE_FAST)
        stats_by_seed[seed] = _report(
            items, f"ahnexp.dataset.generate_items(n_items={n_items}, seed={seed})"
        )

    _explain_mechanism(n_items)

    collapsed = sorted(
        ft for ft in CATEGORICAL
        if any(stats_by_seed[s][ft]["unique"] == 1 for s in stats_by_seed)
    )
    print(f"\n{'=' * 92}")
    if collapsed:
        print(f"VERDICT: STILL COLLAPSED for {collapsed} on at least one seed")
        sys.exit(1)
    print("VERDICT: no categorical fact type collapses on seeds 0, 1, 2 — fix holds")
    print(f"{'=' * 92}")


if __name__ == "__main__":
    main()
