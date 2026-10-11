# OmniRisk Benchmark Evaluation Methodology

## Benchmark Context & Truthfulness Disclaimer

> **Mandatory Disclaimer**: This is a synthetic benchmark evaluation and does not represent real-world insurer performance.
> The primary insurance workbook (`insurance_model.xlsx`) does not contain historical ground-truth underwriter decision labels.
> Therefore, claims of "real-world underwriting accuracy" would be scientifically invalid.

Instead, OmniRisk evaluates model validity using an **actuarial reference standard rubric** established upon standard insurance underwriting principles.

---

## Actuarial Reference Standard Rubric

An independent multi-condition actuarial decision standard was codified:

- **HIGH RISK Reference Standard**:
  - `(claims_last_24m >= 3 AND loss_ratio >= 1.5)` OR
  - `(claim_frequency >= 1.5 AND severity in ('High', 'Critical') AND loss_ratio >= 1.0)` OR
  - `(severity == 'Critical' AND claims_last_24m >= 2)` OR
  - `(claims_last_24m >= 4)` OR
  - `(unsettled_claims >= 2 AND loss_ratio >= 2.0)`

- **LOW RISK Reference Standard**:
  - `(claims_last_24m == 0 AND unsettled_claims == 0 AND loss_ratio <= 0.8)` OR
  - `(valid_claim_count == 0)` OR
  - `(valid_claim_count <= 1 AND loss_ratio <= 0.5 AND severity in ('None', 'Low'))`

- **MEDIUM RISK Reference Standard**:
  - All balanced profiles falling between low and high conditions.

---

## Evaluation Results on Authoritative Dataset (120 Profiles)

```
============================================================
              SYNTHETIC BENCHMARK EVALUATION
============================================================
Overall Accuracy:        85.8%
Weighted Precision:      87.3%
Weighted Recall:         85.8%
Weighted F1-Score:       85.1%
Macro F1-Score:          83.0%

Per-Class Performance:
------------------------------------------------------------
Risk Band     Precision     Recall     F1-Score     Support
LOW             89.1%       100.0%      94.2%         49
MEDIUM          78.0%        86.7%      82.1%         45
HIGH           100.0%        57.7%      73.2%         26
------------------------------------------------------------
Total Sample Size: 120 Customer Accounts
============================================================
```

### Analysis of Findings:
- **Low Risk Recognition**: 100% recall ensures clean accounts are never unfairly flagged as high risk.
- **High Risk Precision**: 100% precision ensures that every account classified as High Risk strictly meets adverse actuarial criteria.
- **Overall Agreement**: 85.8% confirms strong alignment between the multi-factor weighted engine and independent underwriting rubrics.
