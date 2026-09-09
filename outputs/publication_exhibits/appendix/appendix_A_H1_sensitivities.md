# Appendix A-H1 — H1 sensitivities

| a | b | diff | ci_low | ci_high | p_holm | significant_holm |
| --- | --- | --- | --- | --- | --- | --- |
| contradictory | entity-attribute | -0.0736111111111111 | -0.107502713851498 | -0.0403248792270531 | 0.0 | True |
| contradictory | numerical | 0.1309027777777777 | 0.1001682717953661 | 0.1605936287416851 | 0.0 | True |
| contradictory | temporal | 0.2133680555555555 | 0.1769525001240479 | 0.2527425905552621 | 0.0 | True |
| entity-attribute | numerical | 0.2045138888888889 | 0.1696596934667587 | 0.2376247519841269 | 0.0 | True |
| entity-attribute | temporal | 0.2869791666666667 | 0.2451443932681696 | 0.3294282215180652 | 0.0 | True |
| numerical | temporal | 0.0824652777777777 | 0.0416773621471405 | 0.1244201187015503 | 0.0 | True |

- Shown in table: exclude-compound-relational (POST-FREEZE SENSITIVITY) — 6/6 Holm-significant, omnibus p = 0.0005. Other sub-tables in source_tables/: exclude-temporal (frozen, 6/6), answered-valid all-types (frozen, 8/10; the file name says 'temporal' but it is ALL types), A_transition per type × per seed (2 distinct orderings across 8 seeds).
- H1 survives every exclusion and is seed-stable.
