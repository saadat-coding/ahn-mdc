# Table 2 — H1 pairwise A$_{transition}$ contrasts (all fact-type pairs)

| a | b | diff | ci95 | p_holm | significant_holm |
| --- | --- | --- | --- | --- | --- |
| contradictory | entity-attribute | -0.074 | [-0.108, -0.040] | 0.0 | True |
| contradictory | compound-relational | 0.265 | [0.224, 0.309] | 0.0 | True |
| contradictory | numerical | 0.131 | [0.100, 0.161] | 0.0 | True |
| contradictory | temporal | 0.213 | [0.177, 0.253] | 0.0 | True |
| entity-attribute | compound-relational | 0.339 | [0.294, 0.384] | 0.0 | True |
| entity-attribute | numerical | 0.205 | [0.170, 0.238] | 0.0 | True |
| entity-attribute | temporal | 0.287 | [0.245, 0.329] | 0.0 | True |
| compound-relational | numerical | -0.135 | [-0.177, -0.092] | 0.0 | True |
| numerical | temporal | 0.082 | [0.042, 0.124] | 0.0 | True |
| compound-relational | temporal | -0.052 | [-0.099, -0.003] | 0.037 | True |

- Hierarchical (item→seed) cluster bootstrap, 2000 resamples; Holm over 10 contrasts.
- 10/10 contrasts Holm-significant. Closest to threshold: compound-relational vs temporal, p_holm 0.037.
- H1 supported iff ≥1 Holm-adjusted CI excludes 0 (frozen criterion).
