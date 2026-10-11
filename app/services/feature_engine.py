"""
OmniRisk - Feature Engineering Service (Phase 2)
Calculates domain-specific insurance risk features, builds claim timelines,
and computes both Data Quality and Data Relevance metrics.
"""

from datetime import datetime
from typing import List, Optional
import numpy as np

from app.config.settings import settings
from app.schemas.risk_schema import (
    CustomerProfile,
    EngineFeatures,
    ClaimFeatures,
    SeverityFeatures,
    FinancialFeatures,
    PolicyFeatures,
    ClaimStatusFeatures,
    PaymentFeatures,
    DataQualityFlags,
    DataRelevance,
    ClaimTimelineItem,
)


class FeatureEngine:
    SEVERITY_ORDER = {
        "None": 0,
        "Low": 1,
        "Medium": 2,
        "High": 3,
        "Critical": 4,
    }

    @classmethod
    def calculate_features(cls, profile: CustomerProfile) -> EngineFeatures:
        snapshot_dt = datetime.strptime(settings.SNAPSHOT_DATE, "%Y-%m-%d")

        # 1. Claim Timeline & Data Quality Audit
        timeline: List[ClaimTimelineItem] = []
        flagged_temporal = []
        flagged_amount = []
        flagged_all = []

        for c in profile.claims:
            is_valid = c.is_date_valid and c.is_amount_valid
            timeline.append(ClaimTimelineItem(
                claim_id=c.claim_id,
                date=c.claim_date,
                amount=c.claim_amount,
                severity=c.severity,
                status=c.claim_status,
                policy_id=c.policy_id,
                is_valid=is_valid,
                flags=c.quality_flags,
            ))
            if not c.is_date_valid:
                flagged_temporal.append(c)
            if not c.is_amount_valid:
                flagged_amount.append(c)
            if len(c.quality_flags) > 0:
                flagged_all.append(c)

        # Sort timeline chronologically
        timeline.sort(key=lambda x: x.date, reverse=True)

        warnings = []
        if flagged_temporal:
            warnings.append(
                f"{len(flagged_temporal)} claim(s) occurred outside policy dates and were excluded from temporal recency metrics."
            )
        if flagged_amount:
            warnings.append(
                f"{len(flagged_amount)} claim(s) exceeded the policy Sum Insured limit."
            )

        dq_flags = DataQualityFlags(
            excluded_temporal_claims_count=len(flagged_temporal),
            excluded_amount_claims_count=len(flagged_amount),
            flagged_claims_count=len(flagged_all),
            warnings=warnings,
        )

        # 2. Data Relevance (Distinct from Data Quality)
        total_source_records = len(profile.policies) + len(profile.claims) + len(profile.payments)
        excluded_records_count = len(flagged_all)
        valid_records_count = max(0, total_source_records - excluded_records_count)
        relevance_score = round((valid_records_count / total_source_records * 100), 1) if total_source_records > 0 else 100.0

        if excluded_records_count == 0:
            relevance_impact = "High: 100% of historical records are fully valid and actively support all risk dimensions."
        else:
            relevance_impact = (
                f"Moderate: {valid_records_count}/{total_source_records} records directly supported core features; "
                f"{excluded_records_count} records were excluded from temporal metrics to maintain actuarial integrity."
            )

        data_relevance = DataRelevance(
            total_source_records=total_source_records,
            valid_source_records=valid_records_count,
            excluded_source_records=excluded_records_count,
            features_supported=20,
            features_unavailable=0,
            relevance_score_percent=relevance_score,
            impact_on_assessment=relevance_impact,
        )

        # 3. Policy Features
        total_tenure_months = 0
        total_sum_insured = 0.0
        total_annual_premium = 0.0
        policy_statuses = []
        coverage_names = set()

        for p in profile.policies:
            total_tenure_months += p.policy_term_months
            total_sum_insured += p.sum_insured
            total_annual_premium += p.annual_premium
            policy_statuses.append(p.status)
            for cov in p.coverages:
                coverage_names.add(cov.coverage_name)

        if not total_tenure_months:
            total_tenure_months = 12

        if "Active" in policy_statuses:
            policy_status = "Active"
        elif "Lapsed" in policy_statuses:
            policy_status = "Lapsed"
        elif "Cancelled" in policy_statuses:
            policy_status = "Cancelled"
        else:
            policy_status = "Unknown"

        policy_feat = PolicyFeatures(
            policy_tenure=total_tenure_months,
            policy_status=policy_status,
            sum_insured=round(total_sum_insured, 2),
            annual_premium=round(total_annual_premium, 2),
            coverage_count=len(coverage_names),
            coverage_profile=sorted(list(coverage_names)),
        )

        # 4. Claims Analysis
        valid_claims = [c for c in profile.claims if c.claim_status != "Rejected"]
        valid_claim_count = len(valid_claims)

        claim_amounts = [c.claim_amount for c in valid_claims]
        total_claim_amount = sum(claim_amounts)
        avg_claim_amount = (total_claim_amount / valid_claim_count) if valid_claim_count > 0 else 0.0
        max_claim_amount = max(claim_amounts) if valid_claim_count > 0 else 0.0

        tenure_years = max(total_tenure_months / 12.0, 0.5)
        claim_frequency = round(valid_claim_count / tenure_years, 2)

        # Temporal metrics (using valid date claims)
        temporal_valid_claims = [c for c in valid_claims if c.is_date_valid]
        claims_last_12 = 0
        claims_last_24 = 0
        claim_dates = []

        for c in temporal_valid_claims:
            c_dt = datetime.strptime(c.claim_date, "%Y-%m-%d")
            claim_dates.append(c_dt)
            diff_days = (snapshot_dt - c_dt).days
            if 0 <= diff_days <= 365:
                claims_last_12 += 1
            if 0 <= diff_days <= 730:
                claims_last_24 += 1

        claim_recency = None
        if claim_dates:
            most_recent = max(claim_dates)
            days_since = (snapshot_dt - most_recent).days
            claim_recency = max(0.0, round(days_since / 30.4, 1))

        claims_prior_12 = claims_last_24 - claims_last_12
        if claims_last_12 > claims_prior_12:
            claim_trend = "Increasing"
        elif claims_last_12 < claims_prior_12 and claims_prior_12 > 0:
            claim_trend = "Decreasing"
        elif claims_last_12 == claims_prior_12 and claims_last_12 > 0:
            claim_trend = "Stable"
        else:
            claim_trend = "None"

        claim_feat = ClaimFeatures(
            valid_claim_count=valid_claim_count,
            claims_last_12_months=claims_last_12,
            claims_last_24_months=claims_last_24,
            total_claim_amount=round(total_claim_amount, 2),
            average_claim_amount=round(avg_claim_amount, 2),
            maximum_claim_amount=round(max_claim_amount, 2),
            claim_frequency=claim_frequency,
            claim_recency=claim_recency,
            claim_trend=claim_trend,
        )

        # 5. Severity Breakdown
        low_count = sum(1 for c in valid_claims if c.severity == "Low")
        med_count = sum(1 for c in valid_claims if c.severity == "Medium")
        high_count = sum(1 for c in valid_claims if c.severity == "High")
        crit_count = sum(1 for c in valid_claims if c.severity == "Critical")

        highest_sev = "None"
        if crit_count > 0:
            highest_sev = "Critical"
        elif high_count > 0:
            highest_sev = "High"
        elif med_count > 0:
            highest_sev = "Medium"
        elif low_count > 0:
            highest_sev = "Low"

        severity_feat = SeverityFeatures(
            low_claim_count=low_count,
            medium_claim_count=med_count,
            high_claim_count=high_count,
            critical_claim_count=crit_count,
            highest_severity=highest_sev,
        )

        # 6. Financial Features
        total_premium_paid = sum(p.premium_amount for p in profile.payments)
        loss_ratio = (total_claim_amount / total_premium_paid) if total_premium_paid > 0 else (
            1.5 if total_claim_amount > 0 else 0.0
        )
        prem_to_sum = (total_annual_premium / total_sum_insured) if total_sum_insured > 0 else 0.0

        financial_feat = FinancialFeatures(
            total_premium_paid=round(total_premium_paid, 2),
            total_claim_amount=round(total_claim_amount, 2),
            loss_ratio=round(loss_ratio, 2),
            premium_to_sum_insured_ratio=round(prem_to_sum, 4),
        )

        # 7. Claim Status Features
        open_count = sum(1 for c in profile.claims if c.claim_status == "Open")
        pending_count = sum(1 for c in profile.claims if c.claim_status == "Pending")
        rejected_count = sum(1 for c in profile.claims if c.claim_status == "Rejected")
        settled_count = sum(1 for c in profile.claims if c.claim_status == "Settled")

        status_feat = ClaimStatusFeatures(
            open_claim_count=open_count,
            pending_claim_count=pending_count,
            rejected_claim_count=rejected_count,
            settled_claim_count=settled_count,
        )

        # 8. Payment Features
        methods = sorted(list({p.payment_method for p in profile.payments}))
        pay_consistency = "Consistent" if len(profile.payments) >= (total_tenure_months // 6) else "Irregular"

        payment_feat = PaymentFeatures(
            payment_count=len(profile.payments),
            payment_methods=methods,
            payment_consistency=pay_consistency,
        )

        return EngineFeatures(
            claims=claim_feat,
            severity=severity_feat,
            financial=financial_feat,
            policy=policy_feat,
            claim_status=status_feat,
            payment=payment_feat,
            data_quality=dq_flags,
            data_relevance=data_relevance,
            claim_timeline=timeline,
        )


feature_engine = FeatureEngine()
