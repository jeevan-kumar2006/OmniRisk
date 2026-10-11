"""
OmniRisk - Data Loader Service (Phase 2)
Provides fast cached access to preprocessed profiles, data quality audits,
portfolio-level summaries, and full enriched customer JSON explorer data.
"""

import json
import logging
from typing import Any, Dict, List, Optional

from app.config.settings import settings
from app.schemas.risk_schema import CustomerProfile, PortfolioItem, PortfolioSummary
from scripts.preprocess_dataset import preprocess

logger = logging.getLogger(__name__)


class DataLoader:
    _profiles_cache: Optional[Dict[str, dict]] = None
    _dq_report_cache: Optional[dict] = None
    _portfolio_cache: Optional[PortfolioSummary] = None

    @classmethod
    def initialize(cls):
        """Loads cached JSON profiles into memory or runs preprocessing if missing."""
        if not settings.CUSTOMER_PROFILES_PATH.exists() or not settings.DATA_QUALITY_REPORT_PATH.exists():
            logger.info("Processed dataset missing. Executing preprocessing pipeline...")
            preprocess()

        with open(settings.CUSTOMER_PROFILES_PATH, "r", encoding="utf-8") as f:
            cls._profiles_cache = json.load(f)

        with open(settings.DATA_QUALITY_REPORT_PATH, "r", encoding="utf-8") as f:
            cls._dq_report_cache = json.load(f)

        cls._portfolio_cache = None  # reset portfolio cache
        logger.info("Loaded %d customer profiles into memory cache.", len(cls._profiles_cache))

    @classmethod
    def get_profile(cls, customer_id: str) -> Optional[CustomerProfile]:
        if cls._profiles_cache is None:
            cls.initialize()

        data = cls._profiles_cache.get(customer_id)
        if not data:
            return None
        return CustomerProfile(**data)

    @classmethod
    def list_customer_ids(cls) -> List[str]:
        if cls._profiles_cache is None:
            cls.initialize()
        return sorted(list(cls._profiles_cache.keys()))

    @classmethod
    def get_all_profiles(cls) -> Dict[str, dict]:
        if cls._profiles_cache is None:
            cls.initialize()
        return cls._profiles_cache

    @classmethod
    def get_data_quality_report(cls) -> dict:
        if cls._dq_report_cache is None:
            cls.initialize()
        return cls._dq_report_cache

    @classmethod
    def get_portfolio_summary(cls) -> PortfolioSummary:
        """Computes portfolio-wide risk profile distribution across all 120 customers."""
        if cls._portfolio_cache is not None:
            return cls._portfolio_cache

        from app.services.feature_engine import feature_engine
        from app.services.risk_engine import risk_engine

        profiles = cls.get_all_profiles()
        items: List[PortfolioItem] = []
        low_count = 0
        med_count = 0
        high_count = 0

        for cid in sorted(profiles.keys()):
            prof = cls.get_profile(cid)
            feats = feature_engine.calculate_features(prof)
            score, level, _, _ = risk_engine.calculate_risk(feats, prof)

            if level == "LOW":
                low_count += 1
            elif level == "MEDIUM":
                med_count += 1
            else:
                high_count += 1

            items.append(PortfolioItem(
                customer_id=cid,
                risk_score=score,
                risk_level=level,
                valid_claims=feats.claims.valid_claim_count,
                loss_ratio=feats.financial.loss_ratio,
                highest_severity=feats.severity.highest_severity,
                policy_status=feats.policy.policy_status,
                annual_premium=feats.policy.annual_premium,
                city=prof.city,
            ))

        # Sort top high risk descending by score
        top_high = sorted([i for i in items if i.risk_level == "HIGH"], key=lambda x: -x.risk_score)
        if len(top_high) < 5:
            top_high = sorted(items, key=lambda x: -x.risk_score)[:5]

        cls._portfolio_cache = PortfolioSummary(
            total_customers=len(items),
            low_count=low_count,
            medium_count=med_count,
            high_count=high_count,
            top_high_risk=top_high,
            all_customers=items,
        )
        return cls._portfolio_cache

    @classmethod
    def get_enriched_customer_json(cls, customer_id: str) -> Optional[Dict[str, Any]]:
        """
        Builds the complete enriched JSON structure for the Customer JSON Explorer,
        connecting source records to calculated indicators and risk scores.
        """
        prof = cls.get_profile(customer_id)
        if not prof:
            return None

        from app.services.feature_engine import feature_engine
        from app.services.risk_engine import risk_engine
        from app.services.evidence_engine import evidence_engine

        feats = feature_engine.calculate_features(prof)
        score, level, contribs, provenance = risk_engine.calculate_risk(feats, prof)
        drivers, positive_factors = evidence_engine.extract_evidence(feats, score, level)

        return {
            "customer_id": prof.customer_id,
            "anonymized_profile": {
                "age_band": prof.age_band or "Unknown",
                "city": prof.city,
                "state": prof.state,
                "pii_redaction_status": "CONFIRMED (FirstName, LastName, DOB Stripped)",
            },
            "policy_profile": {
                "total_policies": len(prof.policies),
                "dominant_status": feats.policy.policy_status,
                "total_tenure_months": feats.policy.policy_tenure,
                "total_sum_insured": feats.policy.sum_insured,
                "annual_premium": feats.policy.annual_premium,
                "policies": [p.model_dump() for p in prof.policies],
            },
            "claim_history": {
                "valid_claim_count": feats.claims.valid_claim_count,
                "claims_last_12_months": feats.claims.claims_last_12_months,
                "claims_last_24_months": feats.claims.claims_last_24_months,
                "total_claim_amount": feats.claims.total_claim_amount,
                "average_claim_amount": feats.claims.average_claim_amount,
                "maximum_claim_amount": feats.claims.maximum_claim_amount,
                "claim_frequency_per_year": feats.claims.claim_frequency,
                "claim_recency_months": feats.claims.claim_recency,
                "claim_trend": feats.claims.claim_trend,
                "highest_severity": feats.severity.highest_severity,
                "timeline": [t.model_dump() for t in feats.claim_timeline],
            },
            "payment_indicators": {
                "payment_count": feats.payment.payment_count,
                "payment_methods": feats.payment.payment_methods,
                "payment_consistency": feats.payment.payment_consistency,
                "total_premium_paid": feats.financial.total_premium_paid,
            },
            "coverage_profile": {
                "coverage_count": feats.policy.coverage_count,
                "unique_coverages": feats.policy.coverage_profile,
            },
            "financial_indicators": {
                "loss_ratio": feats.financial.loss_ratio,
                "premium_to_sum_insured_ratio": feats.financial.premium_to_sum_insured_ratio,
                "net_incurred_claims": feats.financial.total_claim_amount,
            },
            "risk_assessment": {
                "risk_score": score,
                "risk_level": level,
                "score_decomposition": [c.model_dump() for c in contribs],
                "risk_provenance": [p.model_dump() for p in provenance],
                "top_risk_drivers": [d.model_dump() for d in drivers],
                "positive_factors": positive_factors,
            },
            "data_quality_flags": {
                "excluded_temporal_claims": feats.data_quality.excluded_temporal_claims_count,
                "excluded_amount_claims": feats.data_quality.excluded_amount_claims_count,
                "flagged_claims_total": feats.data_quality.flagged_claims_count,
                "warnings": feats.data_quality.warnings,
            },
            "data_relevance": feats.data_relevance.model_dump(),
        }


data_loader = DataLoader()
