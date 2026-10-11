"""
Unit tests for data ingestion, privacy enforcement, and data quality checks.
"""

import json
from pathlib import Path
from scripts.preprocess_dataset import preprocess
from app.config.settings import settings


def test_preprocessing_and_privacy():
    dq_report, profiles = preprocess()

    assert dq_report is not None
    assert "total_customers" in dq_report
    assert dq_report["total_customers"] > 0
    assert dq_report["missing_joins_count"] == 0

    # Ensure PII is stripped
    sample_profile = next(iter(profiles.values()))
    assert "FirstName" not in sample_profile
    assert "LastName" not in sample_profile
    assert "DOB" not in sample_profile
    assert "customer_id" in sample_profile
    assert "policies" in sample_profile


def test_data_quality_anomalies_flagged():
    with open(settings.DATA_QUALITY_REPORT_PATH, "r", encoding="utf-8") as f:
        report = json.load(f)

    # Dataset contains known synthetic anomalies
    assert report["claims_outside_policy_dates_count"] > 0
    assert report["claims_exceeding_sum_insured_count"] > 0
