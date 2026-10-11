# OmniRisk AI Logic & Explainability Architecture

## Division of Responsibilities

```
Deterministic Risk Engine (Backend)      ──►  Computes exact score (0-100)
Evidence Engine                          ──►  Extracts factual driver + evidence pairs
GenAI Underwriter Agent (Gemini)         ──►  Synthesizes context into actionable brief
```

The system strictly adheres to the principle that **the risk engine is the source of truth, and GenAI is the synthesis layer**.

### What GenAI IS Used For:
- Converting technical risk indicators into concise, readable natural language
- Contextualizing major risk drivers in underwriting terms
- Identifying mitigating positive factors
- Formulating review action proposals (e.g. required deductibles, senior referrals)

### What GenAI IS NOT Used For:
- Arithmetic or claim counting
- Inventing or modifying the risk score
- Inventing unsubstantiated evidence or causes
- Autonomously binding, accepting, or rejecting coverage

---

## Weighting & Scoring Heuristics

The multi-factor risk engine allocates up to 100 points across 6 calibrated actuarial dimensions:

| Dimension | Max Points | Weight | Key Thresholds |
|---|---|---|---|
| **Claim Frequency & Recency** | 30 pts | 30% | >2 claims/yr (+18), 1-2 claims/yr (+12); recency <6m (+12), <12m (+8), <24m (+4) |
| **Financial Loss Ratio** | 25 pts | 25% | LR ≥3.0 (+25), LR 2.0-3.0 (+20), LR 1.0-2.0 (+15), LR 0.6-1.0 (+8) |
| **Claim Severity** | 20 pts | 20% | Critical (>150k: +20), High (50k-150k: +15), Medium (10k-50k: +8), Low (+3) |
| **Unsettled Claims** | 10 pts | 10% | ≥2 Open/Pending (+10), 1 Open/Pending (+6), None (+0) |
| **Policy Stability** | 10 pts | 10% | Cancelled (+10), Lapsed (+8), Tenure <6 months (+4), Stable (+0) |
| **Behavioral & Other** | 5 pts | 5% | Irregular payment cadence (+3), Upward claim trend (+2) |

### Categorical Risk Levels:
- **LOW RISK**: 0 - 39 points
- **MEDIUM RISK**: 40 - 69 points
- **HIGH RISK**: 70 - 100 points

---

## Input Contract to GenAI

```json
{
  "customer_profile": {
    "customer_id": "CUST1003",
    "total_policies": 4,
    "total_claims_recorded": 7,
    "total_payments_recorded": 48
  },
  "policy_profile": {
    "dominant_status": "Active",
    "total_tenure_months": 48,
    "total_sum_insured": 3500000.0,
    "annual_premium": 70885.0
  },
  "risk_score": 77,
  "risk_level": "HIGH",
  "financial_indicators": {
    "loss_ratio": 6.53,
    "total_premium_paid": 70885.0,
    "total_claim_amount": 462719.0
  },
  "risk_drivers": [
    {
      "factor": "Elevated Recent Claim Frequency",
      "impact": "HIGH",
      "evidence": "4 valid claims recorded in the last 24 months (annual frequency: 1.8/yr)."
    }
  ]
}
```

## Structured GenAI Output Schema

The model responds strictly in validated JSON:

```json
{
  "summary": "Executive underwriting narrative summarizing findings.",
  "key_indicators": [
    "Overall Risk Score: 77/100 (HIGH RISK)",
    "Loss Ratio: 6.53",
    "Highest Claim Severity: Critical"
  ],
  "positive_factors": [
    "Established active policy relationship over 48 months."
  ],
  "risk_drivers": [
    {
      "factor": "Elevated Recent Claim Frequency",
      "impact": "HIGH",
      "evidence": "4 valid claims recorded in the last 24 months."
    }
  ],
  "recommended_action": "Refer to Senior Underwriter for risk review and loss control audit.",
  "confidence": 0.95
}
```
