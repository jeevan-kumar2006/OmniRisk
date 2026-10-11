# OmniRisk Data Schema Specification

## Operational Source Tables

The application ingests the normalized operational tables from `insurance_model.xlsx`:

| Sheet | Purpose | Primary Keys / Foreign Keys |
|---|---|---|
| `Customers` | Account records (PII stripped at ingestion) | `CustomerID` |
| `Policies` | Policy contracts, term, sum insured, premium | `PolicyID`, `CustomerID`, `AgentID`, `ProductID` |
| `Claims` | Individual loss events, amount, dates, status | `ClaimID`, `PolicyID`, `CustomerID` |
| `Payments` | Historical premium payments | `PaymentID`, `PolicyID`, `CustomerID` |
| `Products` | Product catalog and standard sum insured limits | `ProductID` |
| `Coverages` | Coverage taxonomy names | `CoverageID` |
| `PolicyCoverages` | Policy-to-coverage mappings and insured limits | `PolicyID`, `CoverageID` |
| `IslandSeverity` | Reference taxonomy for claim severity tiers | `SeverityID` |

> **Note**: `WidePolicies` is intentionally **not** used as an authoritative source due to known aggregate discrepancies with the underlying `Claims` table.

## IslandSeverity Reference Taxonomy

| Severity Level | Claim Amount Range | Interpretation |
|---|---|---|
| **Low** | `< ₹10,000` | Minor claim event |
| **Medium** | `₹10,000 - ₹50,000` | Moderate claim event |
| **High** | `₹50,000 - ₹150,000` | Substantial loss claim |
| **Critical** | `> ₹150,000` | Catastrophic loss claim |

## Normalized JSON Profile Schema

```json
{
  "customer_id": "CUST1003",
  "city": "Jaipur",
  "state": "DL",
  "policies": [
    {
      "policy_id": "POL3010",
      "agent_id": "AG201",
      "product_id": "PR12",
      "product_name": "Motor Own Damage",
      "policy_start_date": "2023-01-01",
      "policy_end_date": "2024-01-01",
      "policy_term_months": 12,
      "annual_premium": 16939.0,
      "sum_insured": 1000000.0,
      "status": "Active",
      "coverages": [
        {
          "coverage_id": "COV10",
          "coverage_name": "Accidental",
          "coverage_sum": 100000.0
        }
      ]
    }
  ],
  "claims": [
    {
      "claim_id": "CL7003",
      "policy_id": "POL3010",
      "claim_date": "2023-05-12",
      "claim_amount": 165000.0,
      "claim_status": "Settled",
      "severity": "Critical",
      "is_date_valid": true,
      "is_amount_valid": true,
      "quality_flags": []
    }
  ],
  "payments": [
    {
      "payment_id": "PAY5012",
      "policy_id": "POL3010",
      "payment_date": "2023-01-02",
      "premium_amount": 16939.0,
      "payment_method": "NetBanking"
    }
  ]
}
```
