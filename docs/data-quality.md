# OmniRisk Data Quality & Governance Policy

## Synthetic Inconsistencies Audit

The operational tables in `insurance_model.xlsx` contain inherent synthetic artifacts. OmniRisk addresses this through transparent data auditing:

| Audit Category | Identified Anomaly Count | Governance Treatment |
|---|---|---|
| **Claims Outside Policy Dates** | 135 claims | **Flagged & Segregated**: Excluded from temporal claim metrics (`claims_last_12_months`, `claims_last_24_months`, recency) while retained for total historical loss figures. |
| **Claims Exceeding Sum Insured** | 7 claims | **Flagged & Capped**: Highlighted in quality reports to prevent catastrophic ratio skew. |
| **Missing Relational Joins** | 0 records | Verified 100% integrity across Customer-Policy-Claim relationships. |
| **Unexpected Status Values** | 0 records | All statuses match standard enumerated values (`Settled`, `Pending`, `Open`, `Rejected`). |

## Segregation Rule

> **Rule**: Problematic records are **never silently deleted**. They are cataloged in `data/processed/data_quality_report.json`, exposed in the user interface, and selectively bypassed only for the specific analytical formulas they invalidate.

## User Interface Exposure

The application displays an explicit **Data Quality Notice** on every profile analysis:
- Highlights count of flagged records.
- Clarifies temporal metric exclusions.
- Full system audit available under the **Data Quality Audit** tab.
