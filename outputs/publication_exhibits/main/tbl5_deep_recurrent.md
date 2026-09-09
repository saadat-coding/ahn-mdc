# Table 5 — Deep-recurrent retention: model_tokens_after_target ≥ 2W (512)

| architecture | region | n | strict_correct | strict_accuracy | wilson95_low | wilson95_high | abstention_rate | wrong_valid_n |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| AHN-DeltaNet | model_tat >= 512 (=2W) | 3542 | 0 | 0.0 | 0.0 | 0.00108 | 0.9836 | 58 |
| AHN-GatedDeltaNet | model_tat >= 512 (=2W) | 3542 | 0 | 0.0 | 0.0 | 0.00108 | 0.9788 | 75 |
| AHN-Mamba2 | model_tat >= 512 (=2W) | 3542 | 1 | 0.00028 | 5e-05 | 0.0016 | 0.9771 | 80 |
| Transformer (no AHN) | model_tat >= 512 (=2W) | 3542 | 3 | 0.00085 | 0.00029 | 0.00249 | 0.8899 | 177 |

- Wilson 95% interval on the binomial. All three AHN architectures shown separately.
- Approved interpretation: “No measurable target-specific factual retention at deep recurrent pressure under the production evaluation.”
- Do NOT state 'AHN recurrent memory stores nothing'. The mamba2 result is 1 correct / 3,542.
- Source: v1.1 reporting-amendment (reporting_amendment.deep_recurrent_retention).
