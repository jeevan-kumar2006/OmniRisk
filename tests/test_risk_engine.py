"""
Unit tests for deterministic risk scoring, provenance, and simulation (Phase 2).
"""

from app.schemas.risk_schema import (
    CustomerProfile,
    PolicyItem,
    ClaimItem,
    PaymentItem,
)
from app.services.feature_engine import feature_engine
from app.services.risk_engine import risk_engine
from app.services.evidence_engine import evidence_engine


def test_deterministic_scoring_and_provenance():
    clean_profile = CustomerProfile(
        customer_id="TEST_LOW",
        age_band="25-34",
        policies=[
            PolicyItem(
                policy_id="P1",
                policy_start_date="2023-01-01",
                policy_end_date="2025-01-01",
                policy_term_months=24,
                annual_premium=20000.0,
                sum_insured=500000.0,
                status="Active",
            )
        ],
        claims=[],
        payments=[
            PaymentItem(
                payment_id="PAY1",
                policy_id="P1",
                customer_id="TEST_LOW",
                payment_date="2023-01-02",
                premium_amount=20000.0,
                payment_method="NetBanking",
            )
        ],
    )
    feats = feature_engine.calculate_features(clean_profile)
    score, level, contribs, provenance = risk_engine.calculate_risk(feats, clean_profile)

    assert 0 <= score <= 100
    assert level == "LOW"
    total_points = sum(c.points for c in contribs)
    assert int(round(total_points)) == score

    # Check provenance
    assert len(provenance) == len(contribs)
    for p in provenance:
        assert p.factor
        assert p.feature_name
        assert "app/" in p.source_module


def test_what_if_simulation():
    profile = CustomerProfile(
        customer_id="TEST_SIM",
        age_band="35-49",
        policies=[
            PolicyItem(
                policy_id="P_SIM",
                policy_start_date="2024-01-01",
                policy_end_date="2025-01-01",
                policy_term_months=12,
                annual_premium=10000.0,
                sum_insured=200000.0,
                status="Active",
            )
        ],
        claims=[],
        payments=[
            PaymentItem(
                payment_id="PAY_SIM",
                policy_id="P_SIM",
                customer_id="TEST_SIM",
                payment_date="2024-01-02",
                premium_amount=10000.0,
                payment_method="UPI",
            )
        ],
    )
    feats = feature_engine.calculate_features(profile)
    base_score, _, _, _ = risk_engine.calculate_risk(feats, profile)

    # Simulate 2 claims + High severity + 2.5 loss ratio
    sim_result = risk_engine.simulate_what_if(
        base_features=feats,
        customer_id="TEST_SIM",
        claims_last_12_delta=2,
        loss_ratio_override=2.5,
        open_claims_override=1,
        severity_override="High",
    )

    assert sim_result.before_score == base_score
    assert sim_result.after_score > base_score
    assert sim_result.score_delta > 0
    assert len(sim_result.changed_factors) >= 4
