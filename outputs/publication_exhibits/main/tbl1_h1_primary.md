# Table 1 — H1 primary result (raw strict production accuracy is the frozen primary endpoint)

| fact_type_internal | construct | n_A_transition | A_transition_raw_strict | A_transition_answered_valid | in_window_control_strict | in_window_control_abstention | in_window_control_verdict |
| --- | --- | --- | --- | --- | --- | --- | --- |
| multi-hop | compound-relational | 5760 | 0.255 | 0.669 | 0.842 | 0.115 | WARNING |
| temporal | temporal | 5760 | 0.307 | 0.925 | 0.568 | 0.384 | PASS |
| numerical | numerical | 5760 | 0.389 | 0.824 | 0.999 | 0.001 | PASS |
| contradictory | contradictory | 5760 | 0.52 | 0.817 | 0.994 | 0.005 | PASS |
| entity-attribute | entity-attribute | 5760 | 0.594 | 0.91 | 1.0 | 0.0 | PASS |

- Label-permutation omnibus on the SD of the five A_transition means: p = 0.0005 (0/2000).
- A_transition = mean raw strict accuracy over intended targets 205–265, AHN arms pooled.
- Answered-valid column is a FROZEN SECONDARY sensitivity (all types), not a replacement.
- #17 Policy A: no chance-corrected primary.
