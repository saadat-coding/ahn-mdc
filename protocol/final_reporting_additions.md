# Required reporting additions — locked artifact only

Additions the manuscript **must** contain that are not in the frozen
`final_*` outputs. **All are computed from
`final_audit/FINAL_LOCKED/results_FINAL_92160.parquet` only** — no new generation,
no change to any frozen primary analysis. Each is classified:

- **[POST-FREEZE SENSITIVITY]** — a new inferential analysis that qualifies/supports a claim
- **[DESCRIPTIVE ROBUSTNESS]** — a descriptive cut that shows stability; no new inference
- **[LIMITATION / DISCLOSURE]** — a constraint on interpretation; prose, table optional

None may be inserted into a frozen primary analysis or presented as the primary.

Evidence labels: [A] from locked artifact · [B] frozen code/config · [C] interpretation · [D] team decision.

---

## 1. H1 sensitivity excluding compound-relational (`multi-hop`)

**Class: [POST-FREEZE SENSITIVITY].**
**Why:** `full_run.analyse` computes exclude-temporal and answered-valid sensitivities
but **not** exclude-multi-hop (`full_run.analyse` L513–515). Multi-hop is the
lowest-ranked type *and* the only control WARNING, so H1 robustness to its removal
must be shown.
**Result [A]** (`final_audit/AUDIT_OUTPUTS/repro_h1_excl_multihop.csv`, hierarchical
bootstrap n = 2000, Holm over the 6 remaining contrasts): **all 6 contrasts
Holm-significant** (contradictory–entity-attribute −0.074 [−0.107, −0.040];
contradictory–numerical 0.131 [0.100, 0.161]; contradictory–temporal 0.213
[0.177, 0.253]; entity-attribute–numerical 0.204 [0.170, 0.238];
entity-attribute–temporal 0.287 [0.245, 0.329]; numerical–temporal 0.083
[0.042, 0.124]). Omnibus over the remaining 4 types remains significant.
**Manuscript use:** one row in the H1 appendix sensitivity table; one sentence:
"H1 is unchanged when compound-relational is excluded (6/6 pairwise contrasts
remain significant after Holm)."

---

## 2. Residual fully-exact-through-generation failure table

**Class: [LIMITATION / DISCLOSURE] + [DESCRIPTIVE ROBUSTNESS].**
**Why:** `derive_boundary_conditions` (`src/ahnexp/schema.py`) marks a trial
`target_fully_exact_through_generation` when `model_tat + target_fact_tokens +
n_new_tokens ≤ W`, i.e. the target span is provably in the lossless KV cache for
the whole trial. **32.1 % of such trials still fail** — this is not in any frozen
output and it bounds the interpretation of the pressure coordinate.
**Result [A]** (`final_audit/AUDIT_OUTPUTS/phase8_residual_exact_failures.csv`;
recomputed here):

| stratum | fail / base | rate |
|---|---|---|
| overall | 11,236 / 34,975 | **32.1 %** |
| composition | abstained 46.2 % · malformed 38.5 % · wrong-valid 15.3 % | |
| fact type | temporal 51.6 % · multi-hop 41.2 % · numerical 33.9 % · contradictory 23.2 % · entity-attribute 11.9 % | |
| architecture | transformer 41.7 % · deltanet 30.0 % · mamba2 29.4 % · gated_deltanet 27.9 % | |
| intended target | 150: 12.0 % · 180: 11.8 % · **205: 34.0 % · 220: 59.9 % · 235: 55.3 %** · 250: 30.7 % | |
| seed | 29.7 %–34.7 % (uniform) | |

**Interpretation [C]:** the ≈ 12 % floor at intended 150/180 is the
temporal+multi-hop in-window abstention baseline; the **excess at intended
205–250** (34–60 %) is retrieval already failing while the target is arithmetically
still exact. Therefore near-window degradation cannot be attributed *solely* to the
exact→compressed transition — long-context attention dilution and/or
instruction-driven abstention contribute. **No mechanism is claimed [C].** Carried
forward from Pilot Pass 2 (`residual_fully_exact_failures`); not resolved.
**Manuscript use:** appendix table (the strata above) + a limitation paragraph in
the H2 discussion. The pressure axis is a *proxy* for compression pressure, not a
clean exact/recurrent switch.

---

## 3. Transformer malformed-behaviour disclosure

**Class: [LIMITATION / DISCLOSURE].**
**Why:** the transformer (no-recurrent-memory control) produces malformed output on
**39.6 %** of its trials (`final_audit/AUDIT_OUTPUTS/phase4_*`). The frozen gate
correctly classifies this **CONTROL_BEHAVIOR** (non-blocking) and the frozen
pooled malformed figure is 12.6 % — which must never be cited alone.
**Result [A]:** overall 9,122 / 23,040 = 39.59 %; 0.0 % at the in-window control
anchors; rises 17.7 % (205) → 59.5 % (220) → 78.5 % (235), stays 48–71 % through
intended 380, falls to 9.8 % (520) and 2.8 % (760). Subtypes: too_long 4,580 ·
unrecognised_value 2,241 · empty 1,488 · negation 813 (frozen `score_row` branches).
Spread across all 240 items and all 8 seeds — not a broken-item/seed artefact.
AHN arms on byte-identical prompts: deltanet 4.7 %, mamba2 4.8 %, gated_deltanet
1.4 %.
**Interpretation [C]:** this is what "no recurrent memory" looks like once the
target is compressed out — the model does not cleanly abstain, it degenerates.
Distinguished from pipeline corruption by (i) 0 % at the anchors, (ii) the full
re-score is exact, (iii) AHN arms at 1.4–4.8 %.
**Manuscript use:** (a) always report malformed **per arm**, never the 12.6 %
pooled number; (b) one sentence in the control-arm description; (c) note that the
transformer's `unsignalled_failure_rate` (0.48, H3) is substantially malformed
output, which is the intended behaviour of that metric.

---

## 4. Deep-recurrent (≥ 2W) negative-retention result

**Class: [POST-FREEZE SENSITIVITY] — NEGATIVE RESULT.**
**Why:** `A_recurrent` (frozen) uses intended ≥ 315; a cleaner "is anything left
deep in the recurrent regime" test uses realised `model_tokens_after_target ≥ 512`
(= 2W) with an exact binomial (Wilson) interval.
**Result [A]** (`final_audit/AUDIT_OUTPUTS/phase9_deep_recurrent.csv`):

| arm | correct / n | strict acc | Wilson-95 upper | abstention |
|---|---|---|---|---|
| deltanet | 0 / 3,542 | 0.0000 | 0.11 % | 0.984 |
| gated_deltanet | 0 / 3,542 | 0.0000 | 0.11 % | 0.979 |
| mamba2 | 1 / 3,542 | 0.0003 | 0.16 % | 0.977 |
| transformer | 3 / 3,542 | 0.0008 | 0.21 % | — |

**Interpretation [C]:** **no credible evidence of target-specific factual retention
at ≥ 2W for any AHN arm.** The single mamba2 hit (a temporal item, 1/3,542) is
consistent with a 2-alternative lucky guess. Abstention ≈ 98 %.
**Manuscript use:** one clean negative sentence in H2 results + the table in an
appendix. Prevents any reader inferring "AHN keeps *some* information at depth".

---

## 5. Temporal response-bias / counterbalancing disclosure

**Class: [LIMITATION / DISCLOSURE].**
**Why:** temporal's low raw A_transition (0.307) and its 38 % in-window abstention
need context; the model has a documented directional response bias that is
counterbalanced by design.
**Result [A]** (`final_audit/AUDIT_OUTPUTS/phase10_temporal_subgroups.csv`):
nuisance balance in the final 48 temporal items is **exact** — gold_is_higher
24/24, gold_first_listed 24/24, density 24/24, full 2×2×2 = 6 per cell.
At the control anchors, answered-valid accuracy is 0.85 (gold = lower-numbered)
vs 0.99 (gold = higher); 0.87 (gold not first-listed) vs 1.00 (gold first-listed);
abstention 0.27 vs 0.50 by gold-first-listed. Pooled control answered-valid
accuracy 0.922 (`final_control_validity_control_validity.csv`).
**Interpretation [C]:** this is a **model response bias** (prefers higher-ID /
first-listed candidate), **not a dataset shortcut** — the nuisance factors are
counterbalanced against the gold, prior target-removed validation was ≈ chance
(`protocol/temporal_repair_validation.md`), and the bias nets out
(pooled answered-valid 0.905, `phase10`). Temporal remains scientifically usable.
**Manuscript use:** cite `protocol/temporal_repair_validation.md`; one paragraph
stating (i) the 2×2×2 is exactly balanced, (ii) the directional bias exists and is
counterbalanced, (iii) temporal's raw strict is abstention-dominated so its H1 rank
is reported with the answered-valid sensitivity beside it.

---

## 6. Compound-relational (`multi-hop`) control WARNING disclosure

**Class: [LIMITATION / DISCLOSURE].**
**Why:** `final_summary.json` / `final_control_validity_control_validity.csv` report
`control_validity: multi-hop = WARNING`; the manuscript must explain it.
**Result [A]:** pooled control anchors — strict **0.842**, answered-valid 0.951,
abstention **0.115**, malformed 0.0. **Both WARNING drivers fire**: strict
0.842 < 0.85 (pass threshold) AND abstention 0.115 > 0.10
(`config/experiment.yaml acceptance.control_validity.non_temporal`). By anchor:
150 → 0.862, 180 → 0.823. By seed: 0.77–0.94 (seed 0 is the high outlier; WARNING
holds in 7/8 seeds). By item: only 2/48 items below 0.5 strict — a broad ≈ 11–15 %
abstention, not a few broken items. **FAIL threshold (strict < 0.70) not reached
→ multi-hop retained in the H1 primary** (`full_run.control_validity` [B]).
**Interpretation [C]:** an ≈ 84 % in-window ceiling is a genuine **task-difficulty**
ceiling for a compound-relational target ("A manages B. B works for C." → *which
company does A's subordinate work for?*) — the model must resolve "A's subordinate"
= B then retrieve "B works for C" from one co-located sentence. It is **not** a
memory or pipeline fault. **Classification: task-difficulty limitation worth
disclosing (audit class B/C); not a blocker** — H1 omnibus and every
non-multi-hop contrast hold, and addition 1 (exclude-multi-hop) confirms 6/6.
**Manuscript use:** (a) label the type "compound relational" everywhere, state it
is a single co-located two-clause target, **not** multi-hop retrieval across
separated facts; (b) disclose the 0.84 control ceiling; (c) note multi-hop's
lowest A_transition (0.255) is partly inherited from its lower ceiling, not purely
faster memory decay — quantify via the answered-valid sensitivity
(compound-relational A_transition answered-valid still lowest but the gap to
temporal shrinks).

---

## 7. Per-seed robustness summary

**Class: [DESCRIPTIVE ROBUSTNESS].**
**Why:** eight seeds were run specifically to support clustered inference; the
manuscript should show the headline conclusions are not one-seed artefacts.
**Result [A]** (`final_audit/AUDIT_OUTPUTS/phase13_*`):

| quantity | per-seed behaviour |
|---|---|
| H1 fact-type ordering | identical in **7/8** seeds; seed 3 swaps only the closest pair (multi-hop 0.271 ↔ temporal 0.238). Per-type A_transition varies ± 0.03–0.05. |
| H1 omnibus | p = 0.0005 on the full data; per-seed dispersion always well above the permutation null. |
| H2 K_strict | transformer spread **1.9** tokens (207.2–209.1); AHN spread **21–29** tokens (deltanet 215.0–240.8; mamba2 217.1–238.4; gated_deltanet 219.6–248.9, bimodal ≈ 220 vs ≈ 243). |
| H2 A_transition gap | positive and CI-excludes-0 in every seed (recompute for the table). |
| H3 appropriate-abstention | AHN 0.92–0.95, transformer 0.49–0.53 **every** seed. |

**Interpretation [C]:** **no headline claim is one-seed-driven.** The only
seed-sensitive quantity is the exact AHN knee *location* — which is why K is
reported with a (wide) interval, not a point.
**Manuscript use:** a compact appendix table (H1 ordering per seed, K per arm per
seed, H3 abstention per arm per seed) + one sentence per hypothesis in the main
text ("stable across all 8 seeds").

---

## Summary table

| # | addition | class | source file |
|---|---|---|---|
| 1 | H1 exclude compound-relational | POST-FREEZE SENSITIVITY | `AUDIT_OUTPUTS/repro_h1_excl_multihop.csv` |
| 2 | residual fully-exact failures | LIMITATION/DISCLOSURE + DESCRIPTIVE ROBUSTNESS | `AUDIT_OUTPUTS/phase8_residual_exact_failures.csv` |
| 3 | transformer malformed | LIMITATION/DISCLOSURE | `AUDIT_OUTPUTS/phase4_transformer_malformed_by_*.csv` |
| 4 | deep-recurrent ≥ 2W negative | POST-FREEZE SENSITIVITY (negative) | `AUDIT_OUTPUTS/phase9_deep_recurrent.csv` |
| 5 | temporal response-bias | LIMITATION/DISCLOSURE | `AUDIT_OUTPUTS/phase10_temporal_subgroups.csv` |
| 6 | compound-relational control WARNING | LIMITATION/DISCLOSURE | `final_control_validity_control_validity.csv`, `AUDIT_OUTPUTS/phase11_multihop_control_by_item.csv` |
| 7 | per-seed robustness | DESCRIPTIVE ROBUSTNESS | `AUDIT_OUTPUTS/phase13_*.csv` |

Additions 1 and 4 need a hierarchical-bootstrap CI computed and a short code helper
(analysis-only, on the locked artifact); 2, 3, 5, 6, 7 are already fully computed —
they need prose and appendix tables, not code.
