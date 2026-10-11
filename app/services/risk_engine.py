"""
OmniRisk - Transparent Deterministic Risk Engine (Phase 2)
Computes a mathematically bounded (0-100) risk score, categorical level,
exact point contributors, full Risk Provenance ("Trace Risk"),
and demonstration What-If Risk Simulation.
"""

from typing import Any, Dict, List, Optional, Tuple
from app.config.settings import settings
from app.schemas.risk_schema import (
    CustomerProfile,
    EngineFeatures,
    RiskProvenanceItem,
    RiskScoreContributor,
    WhatIfResult,
)


class RiskEngine:
    @classmethod
    def calculate_risk(
        cls, features: EngineFeatures, profile: Optional[CustomerProfile] = None
    ) -> Tuple[int, str, List[RiskScoreContributor], List[RiskProvenanceItem]]:
        contributors: List[RiskScoreContributor] = []
        provenance: List[RiskProvenanceItem] = []
        weights = settings.WEIGHTS
        thresholds = settings.THRESHOLDS

        # 1. Claim Frequency & Recency (Max: 30 pts)
        freq_rec_pts = 0.0
        reasons_freq = []
        cf = features.claims.claim_frequency
        rec = features.claims.claim_recency

        if cf > 2.0:
            freq_rec_pts += 18.0
            reasons_freq.append(f"Elevated claim frequency ({cf:.1f}/yr)")
        elif cf > 1.0:
            freq_rec_pts += 12.0
            reasons_freq.append(f"Moderate claim frequency ({cf:.1f}/yr)")
        elif cf > 0.4:
            freq_rec_pts += 6.0
            reasons_freq.append(f"Low claim frequency ({cf:.1f}/yr)")
        else:
            reasons_freq.append("Negligible claim frequency")

        if rec is not None:
            if rec <= 6.0:
                freq_rec_pts += 12.0
                reasons_freq.append(f"Recent claim within {rec:.1f} months")
            elif rec <= 12.0:
                freq_rec_pts += 8.0
                reasons_freq.append(f"Claim within last {rec:.1f} months")
            elif rec <= 24.0:
                freq_rec_pts += 4.0
                reasons_freq.append("Claim within last 24 months")
            else:
                reasons_freq.append(f"No recent claims ({rec:.1f} months ago)")
        else:
            reasons_freq.append("Zero claims recorded")

        freq_rec_pts = min(weights.claim_frequency_recency, freq_rec_pts)
        contributors.append(RiskScoreContributor(
            factor="Claim Frequency & Recency",
            points=round(freq_rec_pts, 1),
            max_points=weights.claim_frequency_recency,
            description="; ".join(reasons_freq),
        ))

        claim_ids_recent = [c.claim_id for c in features.claim_timeline[:3]] if features.claim_timeline else []
        provenance.append(RiskProvenanceItem(
            factor="Claim Frequency & Recency",
            points=round(freq_rec_pts, 1),
            max_points=weights.claim_frequency_recency,
            feature_name="claim_frequency, claim_recency",
            supporting_evidence=f"Frequency: {cf:.2f}/yr, Recency: {rec if rec is not None else 'N/A'} mo",
            source_records=f"Claims: {', '.join(claim_ids_recent) if claim_ids_recent else 'None'}",
            json_path="customer_profile.claims[is_date_valid=true]",
            source_module="app/services/risk_engine.py -> RiskEngine.calculate_risk() [Weight: 30%]",
        ))

        # 2. Financial Loss Ratio (Max: 25 pts)
        lr = features.financial.loss_ratio
        lr_pts = 0.0
        desc_lr = ""

        if lr >= 3.0:
            lr_pts = 25.0
            desc_lr = f"Severe loss ratio ({lr:.2f}) - claims severely exceed premiums"
        elif lr >= 2.0:
            lr_pts = 20.0
            desc_lr = f"High loss ratio ({lr:.2f}) - claims double paid premium"
        elif lr >= 1.0:
            lr_pts = 15.0
            desc_lr = f"Unfavorable loss ratio ({lr:.2f}) - claims exceed premium"
        elif lr >= 0.6:
            lr_pts = 8.0
            desc_lr = f"Moderate loss ratio ({lr:.2f})"
        elif lr >= 0.3:
            lr_pts = 4.0
            desc_lr = f"Favorable low loss ratio ({lr:.2f})"
        else:
            lr_pts = 0.0
            desc_lr = f"Excellent loss ratio ({lr:.2f})"

        lr_pts = min(weights.loss_ratio, lr_pts)
        contributors.append(RiskScoreContributor(
            factor="Loss Ratio Impact",
            points=round(lr_pts, 1),
            max_points=weights.loss_ratio,
            description=desc_lr,
        ))

        provenance.append(RiskProvenanceItem(
            factor="Loss Ratio Impact",
            points=round(lr_pts, 1),
            max_points=weights.loss_ratio,
            feature_name="loss_ratio",
            supporting_evidence=f"Loss ratio: {lr:.2f} (Claims: ₹{features.financial.total_claim_amount:,.2f} / Paid: ₹{features.financial.total_premium_paid:,.2f})",
            source_records=f"Aggregated from {features.payment.payment_count} Payments and {features.claims.valid_claim_count} Claims",
            json_path="customer_profile.financial.loss_ratio",
            source_module="app/services/feature_engine.py -> FeatureEngine.calculate_features() [Weight: 25%]",
        ))

        # 3. Claim Severity (Max: 20 pts)
        sev_pts = 0.0
        highest_sev = features.severity.highest_severity

        if highest_sev == "Critical":
            sev_pts = 20.0
            desc_sev = f"Critical claims detected ({features.severity.critical_claim_count} claims >150k)"
        elif highest_sev == "High":
            sev_pts = 15.0
            desc_sev = f"High severity claims detected ({features.severity.high_claim_count} claims 50k-150k)"
        elif highest_sev == "Medium":
            sev_pts = 8.0
            desc_sev = f"Medium severity claims ({features.severity.medium_claim_count} claims 10k-50k)"
        elif highest_sev == "Low":
            sev_pts = 3.0
            desc_sev = "Low severity claims only (<10k)"
        else:
            sev_pts = 0.0
            desc_sev = "No claim severity recorded"

        sev_pts = min(weights.claim_severity, sev_pts)
        contributors.append(RiskScoreContributor(
            factor="Claim Severity",
            points=round(sev_pts, 1),
            max_points=weights.claim_severity,
            description=desc_sev,
        ))

        provenance.append(RiskProvenanceItem(
            factor="Claim Severity",
            points=round(sev_pts, 1),
            max_points=weights.claim_severity,
            feature_name="highest_severity, critical_claim_count",
            supporting_evidence=f"Highest: {highest_sev}, Peak Claim: ₹{features.claims.maximum_claim_amount:,.2f}",
            source_records="Claims evaluated against IslandSeverity reference taxonomy (data/reference/island_severity.json)",
            json_path="customer_profile.claims[].severity",
            source_module="app/services/feature_engine.py -> FeatureEngine.calculate_features() [Weight: 20%]",
        ))

        # 4. Open / Pending Claims Exposure (Max: 10 pts)
        op_count = features.claim_status.open_claim_count + features.claim_status.pending_claim_count
        op_pts = 0.0

        if op_count >= 2:
            op_pts = 10.0
            desc_op = f"Multiple unsettled claims ({features.claim_status.open_claim_count} open, {features.claim_status.pending_claim_count} pending)"
        elif op_count == 1:
            op_pts = 6.0
            desc_op = f"1 active unsettled claim ({features.claim_status.open_claim_count} open, {features.claim_status.pending_claim_count} pending)"
        else:
            op_pts = 0.0
            desc_op = "All claims settled or closed"

        op_pts = min(weights.open_pending_claims, op_pts)
        contributors.append(RiskScoreContributor(
            factor="Unsettled Claims Exposure",
            points=round(op_pts, 1),
            max_points=weights.open_pending_claims,
            description=desc_op,
        ))

        provenance.append(RiskProvenanceItem(
            factor="Unsettled Claims Exposure",
            points=round(op_pts, 1),
            max_points=weights.open_pending_claims,
            feature_name="open_claim_count, pending_claim_count",
            supporting_evidence=f"{features.claim_status.open_claim_count} Open, {features.claim_status.pending_claim_count} Pending",
            source_records="Claims sheet: ClaimStatus filter",
            json_path="customer_profile.claims[status IN ('Open', 'Pending')]",
            source_module="app/services/risk_engine.py -> RiskEngine.calculate_risk() [Weight: 10%]",
        ))

        # 5. Policy Stability & Status (Max: 10 pts)
        st_pts = 0.0
        status = features.policy.policy_status
        tenure = features.policy.policy_tenure

        if status == "Cancelled":
            st_pts = 10.0
            desc_st = "Policy status is Cancelled"
        elif status == "Lapsed":
            st_pts = 8.0
            desc_st = "Policy status is Lapsed"
        elif tenure < 6:
            st_pts = 4.0
            desc_st = f"Short policy tenure ({tenure} months)"
        else:
            st_pts = 0.0
            desc_st = f"Active policy with stable tenure ({tenure} months)"

        st_pts = min(weights.policy_stability, st_pts)
        contributors.append(RiskScoreContributor(
            factor="Policy Stability",
            points=round(st_pts, 1),
            max_points=weights.policy_stability,
            description=desc_st,
        ))

        provenance.append(RiskProvenanceItem(
            factor="Policy Stability",
            points=round(st_pts, 1),
            max_points=weights.policy_stability,
            feature_name="policy_status, policy_tenure",
            supporting_evidence=f"Status: {status}, Total Tenure: {tenure} months",
            source_records=f"Policies: {len(features.policy.coverage_profile)} Coverages attached",
            json_path="customer_profile.policies[].status",
            source_module="app/services/risk_engine.py -> RiskEngine.calculate_risk() [Weight: 10%]",
        ))

        # 6. Coverage & Behavioral Indicators (Max: 5 pts)
        oth_pts = 0.0
        oth_reasons = []

        if features.payment.payment_consistency == "Irregular":
            oth_pts += 3.0
            oth_reasons.append("Irregular payment cadence")
        if features.claims.claim_trend == "Increasing":
            oth_pts += 2.0
            oth_reasons.append("Upward claim frequency trend")
        if not oth_reasons:
            oth_reasons.append("Consistent payment history and stable coverage")

        oth_pts = min(weights.coverage_other, oth_pts)
        contributors.append(RiskScoreContributor(
            factor="Behavioral & Payment Cadence",
            points=round(oth_pts, 1),
            max_points=weights.coverage_other,
            description="; ".join(oth_reasons),
        ))

        provenance.append(RiskProvenanceItem(
            factor="Behavioral & Payment Cadence",
            points=round(oth_pts, 1),
            max_points=weights.coverage_other,
            feature_name="payment_consistency, claim_trend",
            supporting_evidence=f"Payment Cadence: {features.payment.payment_consistency}, Trend: {features.claims.claim_trend}",
            source_records=f"Payments sheet ({features.payment.payment_count} transactions via {', '.join(features.payment.payment_methods)})",
            json_path="customer_profile.payments[]",
            source_module="app/config/settings.py [Thresholds] -> app/services/risk_engine.py [Weight: 5%]",
        ))

        total_score = int(round(sum(c.points for c in contributors)))
        total_score = max(0, min(100, total_score))

        if total_score <= thresholds.low_max:
            risk_level = "LOW"
        elif total_score <= thresholds.medium_max:
            risk_level = "MEDIUM"
        else:
            risk_level = "HIGH"

        return total_score, risk_level, contributors, provenance

    @classmethod
    def simulate_what_if(
        cls,
        base_features: EngineFeatures,
        customer_id: str,
        claims_last_12_delta: int = 0,
        loss_ratio_override: Optional[float] = None,
        open_claims_override: Optional[int] = None,
        severity_override: Optional[str] = None,
    ) -> WhatIfResult:
        """
        Safe demonstration-only simulator.
        Recalculates deterministic score based on parameter variations without modifying source data.
        """
        base_score, base_level, _, _ = cls.calculate_risk(base_features)

        # Clone and modify feature state temporarily
        sim_features = base_features.model_copy(deep=True)
        changed_factors = []

        if claims_last_12_delta != 0:
            new_c12 = max(0, sim_features.claims.claims_last_12_months + claims_last_12_delta)
            sim_features.claims.claims_last_12_months = new_c12
            # Recompute frequency
            tenure_years = max(sim_features.policy.policy_tenure / 12.0, 0.5)
            sim_features.claims.claim_frequency = round((sim_features.claims.valid_claim_count + claims_last_12_delta) / tenure_years, 2)
            if claims_last_12_delta > 0:
                sim_features.claims.claim_recency = 2.0  # Simulated recent claim
            changed_factors.append(f"Recent Claims (last 12m): {base_features.claims.claims_last_12_months} ➔ {new_c12}")

        if loss_ratio_override is not None:
            sim_features.financial.loss_ratio = max(0.0, loss_ratio_override)
            changed_factors.append(f"Loss Ratio: {base_features.financial.loss_ratio:.2f} ➔ {loss_ratio_override:.2f}")

        if open_claims_override is not None:
            sim_features.claim_status.open_claim_count = max(0, open_claims_override)
            changed_factors.append(f"Open Claims: {base_features.claim_status.open_claim_count} ➔ {open_claims_override}")

        if severity_override and severity_override in ("None", "Low", "Medium", "High", "Critical"):
            sim_features.severity.highest_severity = severity_override
            changed_factors.append(f"Highest Claim Severity: {base_features.severity.highest_severity} ➔ {severity_override}")

        new_score, new_level, _, _ = cls.calculate_risk(sim_features)
        delta = new_score - base_score

        return WhatIfResult(
            customer_id=customer_id,
            before_score=base_score,
            before_level=base_level,
            after_score=new_score,
            after_level=new_level,
            score_delta=delta,
            changed_factors=changed_factors if changed_factors else ["No parameters modified"],
            simulation_notice="Simulation only — source data unchanged.",
        )


risk_engine = RiskEngine()
