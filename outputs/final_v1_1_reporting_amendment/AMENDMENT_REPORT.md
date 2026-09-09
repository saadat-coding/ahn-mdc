# v1.1 Reporting-Amendment Implementation Report

Analysis-only. No GPU. Locked raw artifact never modified. No frozen output replaced.
Date: 2026-09-09.

---

### 1. Git commit before implementation
- Working HEAD before this work: **`64dc10c`** ("Make staged final generation crash-resumable").
- **Decision-preservation commit (the five protocol docs, made before any amendment code): `76e5207`** — "Protocol: final results specification + reporting-amendment decision documents".

### 2. Implementation commit(s)
- **`626521a`** — "Analysis v1.1: post-freeze reporting amendments (H2 width Option A + H1 sensitivity + disclosure tables)".
- **`1031b07`** — "Protocol: record the v1.1 reporting-amendment implementation" (records only; original rationale unchanged).

### 3. Files changed
| commit | files |
|---|---|
| `626521a` | **new:** `src/ahnexp/reporting_amendment.py` (509 L), `scripts/run_reporting_amendment.py`, `scripts/verify_frozen_v1_0.py`, `tests/test_reporting_amendment.py` (12 tests), `outputs/final_v1_1_reporting_amendment/` (36 result files). **No change** to `h1_degradation.py` / `h2_threshold.py` / `h3_calibration.py` / `full_run.py` / `metrics.py` / `schema.py` / `stats.py` / `config/` / scorer / prompt / dataset / gates / FINAL_LOCKED. |
| `1031b07` | `protocol/amendment_h2_transition_width.md` (+§13), `protocol/final_reporting_additions.md` (+status table), `protocol/final_claims_register.md` (H2-2, H2-3, H1-1), `protocol/final_results_specification.md` (ledger + status banner). |

### 4. Tests passed
- Full unit suite: **267 pass** (was 255; +12 `test_reporting_amendment.py`), no GPU, ~111 s.
- `python -m ahnexp._smoke`, `scripts/run_full.py --self-test`, `scripts/run_pilot_pass2.py --self-test` — all pass.
- `tests/test_reporting_amendment.py` proves: the eligibility rule is derived from the estimator's mathematics (not observed convenience); eligible widths + CIs + `frac_finite`; the median summary; exclude-compound-relational shape + Holm; deep-recurrent Wilson CIs; `full_run.ANALYSIS_VERSION == "1.0"` and `reporting_amendment.ANALYSIS_VERSION == "1.1"`; the amendment module never references FINAL_LOCKED or a frozen output; `WIDTH_LO/HI_LEVEL == (0.90, 0.10)` (not lowered).

### 5. Frozen-v1.0 reproduction comparison
`scripts/verify_frozen_v1_0.py --nboot 2000` recomputes every frozen H1/H2/H3/control
quantity from the locked parquet with the **current** code and diffs against
`final_audit/FINAL_LOCKED/final_*.csv`:

**53 / 53 quantities identical** (tolerance 1e-9; actual max \|Δ\| **5.7×10⁻¹⁴**).
`final_h2_h2_width.csv` still reproduces as all-NaN — the frozen result (and its
defect) is preserved exactly. `VERIFY EXIT 0`.

### 6. Locked-artifact SHA-256 comparison
| | value |
|---|---|
| expected | `a72fd43e87457a70c2833314e1443a794fa4189362ac8206c56275ef427fb62e` |
| computed (this run, `run_reporting_amendment.py` gate) | `a72fd43e87457a70c2833314e1443a794fa4189362ac8206c56275ef427fb62e` |
| **match** | **YES — unchanged** |

### 7. H2 eligibility table  (`h2_amend__eligibility.csv`)

Rule (predefined from the 90→10 estimator): eligible iff the fitted non-increasing
isotonic strict-accuracy curve attains **≥ 0.90** (so a 0.90 crossing exists) **and
≤ 0.10** (so a 0.10 crossing exists). Checked on the fit.

| fact type | fitted ceiling (max) | fitted floor (min) | reaches 0.90 | reaches 0.10 | **eligible (all 4 arms)** |
|---|---|---|---|---|---|
| contradictory | 1.000 | 0.000 | ✓ | ✓ | **YES** |
| entity-attribute | 1.000 | 0.000 | ✓ | ✓ | **YES** |
| numerical | 0.999 | 0.000 | ✓ | ✓ | **YES** |
| multi-hop | 0.862 | 0.000 | ✗ | ✓ | **NO** — ceiling 0.862 < 0.90 |
| temporal | 0.568 | 0.000/0.001 | ✗ | ✓ | **NO** — ceiling 0.568 < 0.90 |

Both ineligible types fail only the **upper** reference (their in-window strict
accuracy is capped by abstention: compound-relational task difficulty ≈ 0.84
strict, temporal ≈ 0.57 strict / 38 % abstention). Eligibility is identical across
all four architectures.

### 8. Amended H2 width results + CIs  (`h2_amend__width_by_facttype.csv`, `h2_amend__width_summary_median.csv`)

Isotonic 90→10 strict-accuracy transition width, model tokens; hierarchical
(item → seed) bootstrap 95 % CI, n = 2000, `random_state = 0`; `frac_finite = 1.000`
for **every** eligible cell.

| architecture | contradictory | entity-attribute | numerical | **per-arm MEDIAN** |
|---|---|---|---|---|
| transformer | 29.4 [27.7, 31.2] | 32.4 [30.4, 39.2] | 36.2 [34.7, 37.9] | **32.4 [30.5, 36.8]** |
| deltanet | 71.4 [68.6, 73.4] | 54.2 [50.6, 57.1] | 77.0 [75.3, 78.4] | **71.4 [68.2, 73.5]** |
| mamba2 | 73.8 [71.7, 75.7] | 58.3 [55.8, 64.8] | 74.6 [72.4, 76.3] | **73.8 [71.5, 75.0]** |
| gated_deltanet | 61.8 [59.1, 66.9] | 49.5 [42.2, 54.2] | 75.4 [73.4, 77.0] | **61.8 [58.9, 67.1]** |

Every value — individual and median — is far below **0.5 W = 128 tokens** →
**concentrated** by the frozen rule's own numeric criterion.

**Seed sensitivity** (`h2_amend__width_seed_sensitivity.csv`, per-seed median width):
transformer 30.0–39.3 (spread 9.3); deltanet 61.9–74.6 (12.7); mamba2 60.8–76.0
(15.2); gated_deltanet 57.8–70.8 (13.0). transformer < every AHN arm in **every**
seed.

**Frozen shape test (preserved separately, unchanged):** all four "threshold-like",
piecewise AIC < smooth AIC at break = W (`final_h2_h2_shape_break_at_W.csv`).

### 9. H1 exclude-compound-relational  ([POST-FREEZE SENSITIVITY], `h1_sensitivity__exclude_compound_relational__*`)

4 fact types (contradictory, entity-attribute, numerical, temporal). Multiplicity:
**Holm over the 6 pairwise contrasts** — identical treatment to the frozen
exclude-temporal sensitivity.

| contrast | diff | 95 % CI | p_holm | sig |
|---|---|---|---|---|
| contradictory − entity-attribute | −0.074 | [−0.108, −0.040] | 0.000 | ✓ |
| contradictory − numerical | 0.131 | [0.100, 0.161] | 0.000 | ✓ |
| contradictory − temporal | 0.213 | [0.177, 0.253] | 0.000 | ✓ |
| entity-attribute − numerical | 0.205 | [0.170, 0.238] | 0.000 | ✓ |
| entity-attribute − temporal | 0.287 | [0.245, 0.329] | 0.000 | ✓ |
| numerical − temporal | 0.082 | [0.042, 0.124] | 0.000 | ✓ |

**6 / 6 Holm-significant.** Omnibus label-permutation on the 4-type dispersion:
SD 0.1115, **p = 0.0005** (0 / 2000). `h1_still_supported = True`.

### 10. New robustness / disclosure tables (all in `outputs/final_v1_1_reporting_amendment/`)

| table | file prefix | headline [A] |
|---|---|---|
| Residual fully-exact failures | `descriptive__residual_fully_exact_failures__` | 11,236 / 34,975 = **32.1 %**; 46 % abstain / 38.5 % malformed / 15 % wrong-valid; by target 150→12 %, **220→59.9 %**, 235→55.3 %; by type temporal 51.6 % … entity-attribute 11.9 %; by arch transformer 41.7 %, AHN 27.9–30.0 % |
| Deep-recurrent ≥ 2W | `sensitivity__deep_recurrent_retention__` | deltanet 0/3542, gated_deltanet 0/3542, mamba2 1/3542, transformer 3/3542; Wilson-95 upper ≤ **0.25 %**; abstention 89–98 % → **NEGATIVE RESULT** |
| Transformer malformed | `disclosure__transformer_malformed__` | overall **39.6 %**; at control anchors **0.05 %**; pooled 12.6 %; per arm deltanet 4.7 % / mamba2 4.8 % / gated_deltanet 1.4 %; subtypes too_long 4580 / unrecognised 2241 / empty 1488 / negation 813 |
| Temporal counterbalancing | `disclosure__temporal_counterbalancing__` | 2×2×2 **exactly balanced**; control answered-valid 0.849 (gold lower) vs 0.992 (gold higher); 0.868 (gold not first) vs 1.000 (gold first); pooled control answered-valid **0.922** — model response bias, counterbalanced |
| Compound-relational control WARNING | `disclosure__compound_relational_control_warning__` | drivers: **strict 0.842 < 0.85 AND abstention 0.115 > 0.10**; `fail_threshold_crossed = false`; **`in_h1_primary = true`**; by seed 0.77–0.94 |
| Per-seed headline robustness | `robustness__per_seed_headline__` | H1: **2 distinct orderings / 8 seeds** (seed 3 swaps multi-hop↔temporal only); K spread transformer 1.9 / deltanet 25.8 / gated_deltanet 29.3 / mamba2 21.3; H3 abstention AHN 0.92–0.95, transformer 0.49–0.53 every seed |
| Reproduced plumbing gates | `reproduced__plumbing_gates.csv` | **0 blocking**; `malformed_control:transformer` = CONTROL_BEHAVIOR; `control_validity:multi-hop` = WARNING; `malformed_pooled` = REPORT |

### 11. Did H1 status change?
**No.** H1 remains **SUPPORTED** (raw strict primary, omnibus p = 5×10⁻⁴, all 10
contrasts Holm-significant). The exclude-compound-relational sensitivity (6/6,
omnibus p = 5×10⁻⁴) **adds robustness**; it is a POST-FREEZE SENSITIVITY, not a
change to the primary. Terminology decision applied: manuscript uses
"compound-relational"; internal key `multi-hop` unchanged in code/data.

### 12. Did H2 status change?
**Yes — a correction, not a reversal, and no approved claim is weakened.**
- **H2-3 (transition width):** frozen v1.0 = **UNDETERMINED** (pooled 90→10 width
  is mathematically undefined; "intermediate" was a code fall-through). v1.1
  amendment = **SUPPORTED — concentrated**: per-eligible-type widths 29–77 tokens,
  per-arm median 32 (transformer) / 62–74 (AHN), all ≪ 0.5 W.
- **H2-2 (threshold-like shape):** **PARTIALLY SUPPORTED → SUPPORTED** — now backed
  by the frozen shape test **and** the amended widths.
- **H2-1 (near-window advantage), H2-4 (W ≠ K), H2-5 (no deep retention):**
  **unchanged.** The frozen `final_h2_h2_width.csv` (all-NaN) is preserved and
  cited as the record; it was not overwritten.
- Overall H2 verdict: from **PARTIALLY SUPPORTED (shape undetermined)** →
  **PARTIALLY SUPPORTED → the shape sub-claim is now resolved as concentrated**;
  the one remaining "partial" is the thin transformer AIC margin (ΔAIC 0.68) on the
  shape test, which is a pre-existing frozen observation, not introduced here.

### 13. Did H3 status change?
**No.** H3 remains **SUPPORTED for behavioural uncertainty signalling** /
**PARTIALLY SUPPORTED for factual calibration**. Framing confirmed: "AHN behaviour
increasingly signals memory unreliability through abstention"; **no mechanistic
"the model knows it forgot" claim**; training/distillation-induced abstention
remains an explicit alternative explanation. Per-seed robustness table confirms the
behavioural contrast is identical across all 8 seeds.

### 14. Remaining publication blockers
**None that require code, data, or a re-run.** Open items are drafting-time
decisions / prose:
1. **[D]** `final_runtime_commit d29c6d8` still not recovered — provably scorer/
   prompt/calibration/analysis-identical to `64dc10c` via 5 hash checks
   (`final_audit/AUDIT_OUTPUTS/provenance_investigation.md`); recover from Colab or
   add a `RUNTIME_COMMIT_NOTE`.
2. **[D]** Whether to also compute the *literal* temporal-only answered-valid
   sensitivity (others stay raw strict) — optional; the all-types version is
   already reported.
3. **[D]** Whether to persist `reproduced__plumbing_gates.csv` and the v1.1 outputs
   into a versioned lock bundle alongside FINAL_LOCKED (team decision;
   FINAL_LOCKED itself stays immutable).
4. **[housekeeping]** Commit or discard the pre-existing +13-line
   `tests/test_full_run_resume.py` modification.
5. **[D]** Remote `main` (`82039f3`) is a stale parallel lineage; the freeze +
   amendment work lives only on `saadat-pipeline-validation`.

### 15. READY / NOT READY for publication exhibits
**READY.** Every exhibit in `protocol/final_exhibit_plan.md` can now be built from
the locked artifact + `final_audit/FINAL_LOCKED/final_*` + `outputs/final_v1_1_reporting_amendment/`,
including the previously-blocked H2 shape/width exhibits (Table 3, Appendix A-H2a)
which now have the amended per-eligible-type widths with CIs. No exhibit depends on
an unresolved decision.

### 16. READY / NOT READY for manuscript drafting
**READY.** Both blocking decisions from the previous readiness check are resolved:
- H1 framing — **approved** (raw strict primary; answered-valid + exclude-multi-hop
  as reported secondaries).
- H2 transition-width amendment — **approved, implemented, verified**.

`protocol/final_claims_register.md` fixes the allowed/prohibited wording per claim;
`protocol/final_results_specification.md` maps each claim to its statistic and
source file. Drafting can begin against those two documents. The five open items in
§14 are disclosures/housekeeping, not drafting blockers.

---

## Confirmations
- No GPU / model generation. ✓
- Locked raw artifact `results_FINAL_92160.parquet` unmodified; SHA-256 `a72fd43e…` verified. ✓
- No frozen v1.0 output file overwritten or hidden; `final_h2_h2_width.csv` preserved as the record. ✓
- Frozen analysis v1.0 reproduces bit-identically (53/53, max \|Δ\| 5.7×10⁻¹⁴). ✓
- Amendment products written only to `outputs/final_v1_1_reporting_amendment/`. ✓
- `main` untouched; all commits on `saadat-pipeline-validation`. ✓
