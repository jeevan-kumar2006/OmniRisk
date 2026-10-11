"""
Unit tests for feature engineering calculations.
"""

from app.schemas.risk_schema import CustomerProfile, PolicyItem, ClaimItem, PaymentItem
from app.services.feature_engine import feature_engine


def test_feature_calculations_clean_profile():
    profile = CustomerProfile(
        customer_id="TEST_CLEAN",
        city="Mumbai",
        state="MH",
        policies=[
            PolicyItem(
                policy_id="POL_1",
                policy_start_date="2024-01-01",
                policy_end_date="2025-01-01",
                policy_term_months=12,
                annual_premium=10000.0,
                sum_insured=200000.0,
                status="Active",
                coverages=[],
            )
        ],
        claims=[],
        payments=[
            PaymentItem(
                payment_id="PAY_1",
                policy_id="POL_1",
                customer_id="TEST_CLEAN",
                payment_date="2024-01-02",
                premium_amount=10000.0,
                payment_method="UPI",
            )
        ],
    )

    feats = feature_engine.calculate_features(profile)

    assert feats.claims.valid_claim_count == 0
    assert feats.claims.claim_frequency == 0.0
    assert feats.financial.loss_ratio == 0.0
    assert feats.financial.total_premium_paid == 10000.0
    assert feats.severity.highest_severity == "None"
    assert feats.policy.policy_status == "Active"


def test_feature_calculations_with_claims_and_severity():
    profile = CustomerProfile(
        customer_id="TEST_ADVERSE",
        city="Delhi",
        state="DL",
        policies=[
            PolicyItem(
                policy_id="POL_2",
                policy_start_date="2023-01-01",
                policy_end_date="2025-01-01",
                policy_term_months=24,
                annual_premium=15000.0,
                sum_insured=500000.0,
                status="Active",
                coverages=[],
            )
        ],
        claims=[
            ClaimItem(
                claim_id="CLM_1",
                policy_id="POL_2",
                customer_id="TEST_ADVERSE",
                claim_date="2024-06-01",
                claim_amount=160000.0,  # Critical (>150k)
                claim_status="Open",
                severity="Critical",
                is_date_valid=True,
                is_amount_valid=True,
                quality_flags=[],
            ),
            ClaimItem(
                claim_id="CLM_2",
                policy_id="POL_2",
                customer_id="TEST_ADVERSE",
                claim_date="2024-08-01",
                claim_amount=60000.0,  # High (50k-150k)
                claim_status="Pending",
                severity="High",
                is_date_valid=True,
                is_amount_valid=True,
                quality_flags=[],
            ),
        ],
        payments=[
            PaymentItem(
                payment_id="PAY_2",
                policy_id="POL_2",
                customer_id="TEST_ADVERSE",
                payment_date="2023-01-05",
                premium_amount=15000.0,
                payment_method="CreditCard",
            )
        ],
    )

    feats = feature_engine.calculate_features(profile)

    assert feats.claims.valid_claim_count == 2
    assert feats.severity.highest_severity == "Critical"
    assert feats.severity.critical_claim_count == 1
    assert feats.severity.high_claim_count == 1
    assert feats.claim_status.open_claim_count == 1
    assert feats.claim_status.pending_claim_count == 1
    assert feats.financial.total_claim_amount == 220000.0
    # Loss ratio: 220000 / 15000 = 14.67
    assert feats.financial.loss_ratio > 10.0
