# Table 4 — Fact-type constructs and in-window (control) validity

| construct | internal_key | answer_form | example | in_window_strict | in_window_answered_valid | in_window_abstention | in_window_malformed | control_verdict |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| compound-relational | multi-hop | closed_set | Person_0 manages Person_1. Person_1 works for Google. / which company  | 0.842 | 0.951 | 0.115 | 0.0 | WARNING |
| temporal | temporal | entity | Person_0 arrived before Person_1. | 0.568 | 0.922 | 0.384 | 0.0 | PASS |
| numerical | numerical | exact_string | Person_0's employee ID is 100000. | 0.999 | 1.0 | 0.001 | 0.0 | PASS |
| contradictory | contradictory | closed_set | Person_0 lived in Paris. Person_0 now lives in London. | 0.994 | 1.0 | 0.005 | 0.001 | PASS |
| entity-attribute | entity-attribute | closed_set | Person_0's favorite color is blue. | 1.0 | 1.0 | 0.0 | 0.0 | PASS |

- compound-relational (internal key multi-hop): a single co-located two-clause target — NOT multi-hop retrieval across separated facts. WARNING driver: strict 0.842 < 0.85 AND abstention 0.115 > 0.10; FAIL threshold 0.70 not reached → retained in the H1 primary.
- temporal: judged on answered-valid accuracy (0.922); 38% in-window abstention is a model property (documented, counterbalanced response bias — Appendix A-VAL).
- control anchors = pooled intended model-tat 150 + 180; n = 3,072 / type.
