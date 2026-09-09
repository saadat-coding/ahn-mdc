# Appendix A-REPRO — Integrity & reproducibility

| check | value | note |
| --- | --- | --- |
| locked raw artifact SHA-256 | a72fd43e87457a70c2833314e1443a794fa4189362ac8206c56275ef427fb62e | verified this build |
| rows | 92160 | == 92,160 |
| rows / architecture | 23,040 × 4 | exact |
| duplicate canonical cells | 0 | (architecture,item_id,seed,intended_model_tat) |
| independent re-score mismatches (frozen scorer) | 0 | correct+abstained+malformed, all 92,160 rows |
| frozen v1.0 reproduction | 53/53 identical | max |Δ| 5.7e-14 (scripts/verify_frozen_v1_0.py) |
| plumbing gates (reproduced) | 0 blocking | malformed_control:transformer = CONTROL_BEHAVIOR; multi-hop = WARNING |
| generation runtime commit | d29c6d8 | not in git; scorer/prompt/calibration/analysis provably identical to 64dc10c (5 hash checks) |
| analysis versions | v1.0 frozen + v1.1 amendment | final_audit/V1_1_LOCKED/V1_1_LOCK_MANIFEST.json |

- Every headline number in this paper reproduces from the locked 92,160-row parquet (SHA-256 a72fd43e…) with the frozen v1.0 code or the approved v1.1 amendment code.
- The v1.1 reporting amendment corrects one undefined descriptive statistic (H2 pooled transition width) and adds sensitivity/disclosure tables; it changes no primary endpoint.
