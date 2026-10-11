"""
OmniRisk - Evidence Engine Service
Extracts verifiable, fact-grounded risk drivers and positive factors
derived strictly from calculated insurance features.
Guarantees 100% explainability without hallucinations.
"""

from typing import List, Tuple
from app.schemas.risk_schema import EngineFeatures, RiskDriver


class EvidenceEngine:
    @classmethod
    def extract_evidence(cls, features: EngineFeatures, risk_score: int, risk_level: str) -> Tuple[List[RiskDriver], List[str]]:
        drivers: List[RiskDriver] = []
        positive_factors: List[str] = []

        claims = features.claims
        sev = features.severity
        fin = features.financial
        pol = features.policy
        st = features.claim_status
        pay = features.payment

        # 1. Frequency & Recency Drivers
        if claims.claims_last_24_months >= 2:
            drivers.append(RiskDriver(
                factor="Elevated Recent Claim Frequency",
                impact="HIGH" if claims.claims_last_24_months >= 3 else "MEDIUM",
                evidence=f"{claims.claims_last_24_months} valid claims recorded in the last 24 months (annual frequency: {claims.claim_frequency:.1f}/yr)."
            ))
        elif claims.claims_last_12_months == 1:
            drivers.append(RiskDriver(
                factor="Recent Claim Activity",
                impact="LOW",
                evidence=f"1 claim recorded within the past 12 months (recency: {claims.claim_recency:.1f} months ago)."
            ))
        else:
            if claims.valid_claim_count == 0:
                positive_factors.append("Clean loss history: Zero recorded claims across policy tenure.")
            elif claims.claims_last_24_months == 0:
                positive_factors.append(f"No recent claims within the past 24 months (last claim {claims.claim_recency:.1f} months ago).")

        # 2. Financial Loss Ratio Drivers
        if fin.loss_ratio >= 1.5:
            drivers.append(RiskDriver(
                factor="Unfavorable Loss Ratio",
                impact="HIGH" if fin.loss_ratio >= 2.5 else "MEDIUM",
                evidence=f"Incurred claims of ₹{fin.total_claim_amount:,.2f} versus ₹{fin.total_premium_paid:,.2f} in paid premiums (Loss Ratio: {fin.loss_ratio:.2f})."
            ))
        elif fin.loss_ratio >= 0.8:
            drivers.append(RiskDriver(
                factor="Moderate Loss Ratio",
                impact="MEDIUM",
                evidence=f"Loss ratio stands at {fin.loss_ratio:.2f} (Total claims: ₹{fin.total_claim_amount:,.2f}, Premiums: ₹{fin.total_premium_paid:,.2f})."
            ))
        else:
            positive_factors.append(f"Favorable loss ratio of {fin.loss_ratio:.2f} (Total premiums ₹{fin.total_premium_paid:,.2f} comfortably exceed claims).")

        # 3. Severity Drivers
        if sev.critical_claim_count > 0:
            drivers.append(RiskDriver(
                factor="Critical Claim Severity",
                impact="HIGH",
                evidence=f"{sev.critical_claim_count} critical severity claim(s) exceeding ₹150,000 threshold (maximum claim: ₹{claims.maximum_claim_amount:,.2f})."
            ))
        elif sev.high_claim_count > 0:
            drivers.append(RiskDriver(
                factor="High Claim Severity",
                impact="HIGH" if sev.high_claim_count >= 2 else "MEDIUM",
                evidence=f"{sev.high_claim_count} high severity claim(s) between ₹50k-₹150k (maximum claim: ₹{claims.maximum_claim_amount:,.2f})."
            ))
        elif sev.medium_claim_count > 0:
            drivers.append(RiskDriver(
                factor="Moderate Claim Severity",
                impact="LOW",
                evidence=f"{sev.medium_claim_count} medium severity claim(s) in the ₹10k-₹50k range."
            ))
        else:
            if claims.valid_claim_count > 0 and sev.low_claim_count == claims.valid_claim_count:
                positive_factors.append("Low severity profile: All historical claims remained under ₹10,000.")

        # 4. Open / Pending Status
        if st.open_claim_count > 0 or st.pending_claim_count > 0:
            drivers.append(RiskDriver(
                factor="Outstanding Unsettled Claims",
                impact="HIGH" if (st.open_claim_count + st.pending_claim_count) >= 2 else "MEDIUM",
                evidence=f"{st.open_claim_count} open claim(s) and {st.pending_claim_count} pending claim(s) currently awaiting settlement."
            ))
        else:
            positive_factors.append("Zero pending or open claims: 100% resolution on historical claim events.")

        # 5. Policy Stability
        if pol.policy_status in ("Lapsed", "Cancelled"):
            drivers.append(RiskDriver(
                factor="Policy Inactive / Lapsed",
                impact="HIGH" if pol.policy_status == "Cancelled" else "MEDIUM",
                evidence=f"Policy status is currently {pol.policy_status}."
            ))
        else:
            positive_factors.append(f"Active policy standing with {pol.policy_tenure} months established relationship.")

        # 6. Payment & Behavioral Drivers
        if pay.payment_consistency == "Consistent":
            positive_factors.append(f"Regular premium payments confirmed ({pay.payment_count} transactions recorded via {', '.join(pay.payment_methods) or 'standard methods'}).")
        else:
            drivers.append(RiskDriver(
                factor="Payment Irregularity",
                impact="LOW",
                evidence=f"Payment cadence is irregular relative to policy duration ({pay.payment_count} recorded payments)."
            ))

        # Default fallback if empty drivers (e.g. pristine low risk)
        if not drivers:
            drivers.append(RiskDriver(
                factor="Baseline Actuarial Exposure",
                impact="LOW",
                evidence="Standard portfolio exposure with zero elevated risk flags."
            ))

        return drivers, positive_factors


evidence_engine = EvidenceEngine()
