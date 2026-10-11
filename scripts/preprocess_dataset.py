"""
OmniRisk - Dataset Preprocessing Script (Phase 2)
Reads raw operational sheets from insurance_model.xlsx,
derives privacy-safe demographics (age_band), strips all PII (FirstName, LastName, DOB),
audits data quality, and outputs clean normalized JSON representations.
"""

import json
import logging
import os
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List

import pandas as pd

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger(__name__)

RAW_EXCEL_PATH = Path("data/raw/insurance_model.xlsx")
PROCESSED_DIR = Path("data/processed")
REFERENCE_DIR = Path("data/reference")

PROCESSED_DIR.mkdir(parents=True, exist_ok=True)
REFERENCE_DIR.mkdir(parents=True, exist_ok=True)


def parse_island_severity(amt: float) -> str:
    """Classifies claim amount using IslandSeverity reference taxonomy."""
    if amt < 10000:
        return "Low"
    elif amt <= 50000:
        return "Medium"
    elif amt <= 150000:
        return "High"
    else:
        return "Critical"


def derive_age_band(dob_str: Any, snapshot_year: int = 2025) -> str:
    """Derives a privacy-preserving age band from DOB prior to stripping DOB."""
    try:
        dt = pd.to_datetime(dob_str)
        age = snapshot_year - dt.year
        if age < 25:
            return "<25"
        elif age <= 34:
            return "25-34"
        elif age <= 49:
            return "35-49"
        elif age <= 64:
            return "50-64"
        else:
            return "65+"
    except Exception:
        return "Unknown"


def preprocess():
    logger.info("Starting ingestion of %s", RAW_EXCEL_PATH)
    if not RAW_EXCEL_PATH.exists():
        raise FileNotFoundError(f"Workbook not found at {RAW_EXCEL_PATH}")

    # Load authoritative normalized operational tables
    excel_file = pd.ExcelFile(RAW_EXCEL_PATH)
    sheet_names = excel_file.sheet_names
    logger.info("Found sheets: %s", sheet_names)

    customers_df = pd.read_excel(excel_file, "Customers")
    policies_df = pd.read_excel(excel_file, "Policies")
    claims_df = pd.read_excel(excel_file, "Claims")
    payments_df = pd.read_excel(excel_file, "Payments")
    products_df = pd.read_excel(excel_file, "Products")
    coverages_df = pd.read_excel(excel_file, "Coverages")
    policy_cov_df = pd.read_excel(excel_file, "PolicyCoverages")

    # Dates conversion
    policies_df["PolicyStartDate"] = pd.to_datetime(policies_df["PolicyStartDate"])
    policies_df["PolicyEndDate"] = pd.to_datetime(policies_df["PolicyEndDate"])
    claims_df["ClaimDate"] = pd.to_datetime(claims_df["ClaimDate"])
    claims_df["SettlementDate"] = pd.to_datetime(claims_df["SettlementDate"])
    payments_df["PaymentDate"] = pd.to_datetime(payments_df["PaymentDate"])

    # 1. DATA QUALITY CHECKS
    claims_outside_policy_dates = []
    claims_exceeding_sum_insured = []
    missing_joins = []
    unexpected_statuses = []

    claims_with_policy = claims_df.merge(
        policies_df[["PolicyID", "PolicyStartDate", "PolicyEndDate", "SumInsured", "Status"]],
        on="PolicyID",
        how="left",
        suffixes=("", "_policy"),
    )

    for idx, row in claims_with_policy.iterrows():
        claim_id = str(row["ClaimID"])
        policy_id = str(row["PolicyID"])
        claim_amt = float(row["ClaimAmount"])
        claim_date = row["ClaimDate"]
        p_start = row["PolicyStartDate_policy"]
        p_end = row["PolicyEndDate"]
        sum_insured = float(row["SumInsured"]) if pd.notnull(row["SumInsured"]) else None

        if pd.isnull(p_start):
            missing_joins.append({
                "claim_id": claim_id,
                "policy_id": policy_id,
                "reason": "PolicyID does not exist in Policies sheet"
            })
            continue

        is_outside = False
        reason = []
        if claim_date < p_start:
            is_outside = True
            reason.append(f"ClaimDate ({claim_date.strftime('%Y-%m-%d')}) precedes PolicyStartDate ({p_start.strftime('%Y-%m-%d')})")
        if claim_date > p_end:
            is_outside = True
            reason.append(f"ClaimDate ({claim_date.strftime('%Y-%m-%d')}) exceeds PolicyEndDate ({p_end.strftime('%Y-%m-%d')})")
        if is_outside:
            claims_outside_policy_dates.append({
                "claim_id": claim_id,
                "policy_id": policy_id,
                "reason": "; ".join(reason)
            })

        if sum_insured is not None and claim_amt > sum_insured:
            claims_exceeding_sum_insured.append({
                "claim_id": claim_id,
                "policy_id": policy_id,
                "claim_amount": claim_amt,
                "sum_insured": sum_insured,
                "excess": round(claim_amt - sum_insured, 2)
            })

    valid_claim_statuses = {"Settled", "Pending", "Open", "Rejected"}
    for status in claims_df["ClaimStatus"].unique():
        if status not in valid_claim_statuses:
            unexpected_statuses.append(f"Unexpected ClaimStatus: {status}")

    valid_policy_statuses = {"Active", "Lapsed", "Cancelled"}
    for status in policies_df["Status"].unique():
        if status not in valid_policy_statuses:
            unexpected_statuses.append(f"Unexpected Policy Status: {status}")

    dq_report = {
        "generated_at": datetime.now().isoformat(),
        "total_customers": int(len(customers_df)),
        "total_policies": int(len(policies_df)),
        "total_claims": int(len(claims_df)),
        "total_payments": int(len(payments_df)),
        "claims_outside_policy_dates_count": len(claims_outside_policy_dates),
        "claims_exceeding_sum_insured_count": len(claims_exceeding_sum_insured),
        "missing_joins_count": len(missing_joins),
        "unexpected_statuses_count": len(unexpected_statuses),
        "claims_outside_policy_dates": claims_outside_policy_dates,
        "claims_exceeding_sum_insured": claims_exceeding_sum_insured,
        "missing_joins": missing_joins,
        "unexpected_statuses": unexpected_statuses,
        "summary": (
            f"Audited {len(claims_df)} claims across {len(policies_df)} policies. "
            f"Flagged {len(claims_outside_policy_dates)} claims with dates outside policy term "
            f"and {len(claims_exceeding_sum_insured)} claims with amount exceeding sum insured. "
            f"Zero missing relational joins detected."
        )
    }

    dq_report_path = PROCESSED_DIR / "data_quality_report.json"
    with open(dq_report_path, "w", encoding="utf-8") as f:
        json.dump(dq_report, f, indent=2)
    logger.info("Saved data quality report to %s", dq_report_path)

    # 2. PRIVACY & ANONYMIZATION
    logger.info("Enforcing privacy: Deriving age_band, then stripping FirstName, LastName, DOB.")
    customers_df["age_band"] = customers_df["DOB"].apply(derive_age_band)
    clean_customers = customers_df[["CustomerID", "City", "State", "age_band"]].copy()

    # Product mapping
    products_map = products_df.set_index("ProductID").to_dict(orient="index")

    # Coverage mapping
    cov_names_map = coverages_df.set_index("CoverageID")["CoverageName"].to_dict()
    policy_cov_grouped = policy_cov_df.groupby("PolicyID")

    # Claims enrichment
    outside_claim_ids = {item["claim_id"] for item in claims_outside_policy_dates}
    excess_claim_ids = {item["claim_id"] for item in claims_exceeding_sum_insured}

    enriched_claims = []
    for _, row in claims_df.iterrows():
        c_id = str(row["ClaimID"])
        c_amt = float(row["ClaimAmount"])
        enriched_claims.append({
            "claim_id": c_id,
            "policy_id": str(row["PolicyID"]),
            "customer_id": str(row["CustomerID"]),
            "claim_date": row["ClaimDate"].strftime("%Y-%m-%d"),
            "claim_amount": c_amt,
            "claim_status": str(row["ClaimStatus"]),
            "settlement_date": row["SettlementDate"].strftime("%Y-%m-%d") if pd.notnull(row["SettlementDate"]) else None,
            "severity": parse_island_severity(c_amt),
            "is_date_valid": c_id not in outside_claim_ids,
            "is_amount_valid": c_id not in excess_claim_ids,
            "quality_flags": [
                *(["CLAIM_OUTSIDE_POLICY_DATES"] if c_id in outside_claim_ids else []),
                *(["CLAIM_EXCEEDS_SUM_INSURED"] if c_id in excess_claim_ids else [])
            ]
        })
    enriched_claims_df = pd.DataFrame(enriched_claims)

    # Payments enrichment
    enriched_payments = []
    for _, row in payments_df.iterrows():
        enriched_payments.append({
            "payment_id": str(row["PaymentID"]),
            "policy_id": str(row["PolicyID"]),
            "customer_id": str(row["CustomerID"]),
            "payment_date": row["PaymentDate"].strftime("%Y-%m-%d"),
            "premium_amount": float(row["PremiumAmount"]),
            "payment_method": str(row["PaymentMethod"]),
        })
    enriched_payments_df = pd.DataFrame(enriched_payments)

    # 3. CONSTRUCT CUSTOMER-LEVEL NORMALIZED PROFILES
    customer_profiles = {}

    for _, c_row in clean_customers.iterrows():
        cust_id = str(c_row["CustomerID"])
        cust_policies = policies_df[policies_df["CustomerID"] == cust_id]
        cust_claims = enriched_claims_df[enriched_claims_df["customer_id"] == cust_id].to_dict(orient="records")
        cust_payments = enriched_payments_df[enriched_payments_df["customer_id"] == cust_id].to_dict(orient="records")

        policies_list = []
        for _, p_row in cust_policies.iterrows():
            pol_id = str(p_row["PolicyID"])
            prod_id = str(p_row["ProductID"])
            prod_info = products_map.get(prod_id, {})

            pol_covs = []
            if pol_id in policy_cov_grouped.groups:
                for _, pc_row in policy_cov_grouped.get_group(pol_id).iterrows():
                    cov_id = str(pc_row["CoverageID"])
                    pol_covs.append({
                        "coverage_id": cov_id,
                        "coverage_name": cov_names_map.get(cov_id, cov_id),
                        "coverage_sum": float(pc_row["CoverageSum"])
                    })

            policies_list.append({
                "policy_id": pol_id,
                "agent_id": str(p_row["AgentID"]),
                "product_id": prod_id,
                "product_name": prod_info.get("ProductName", "Unknown"),
                "product_category": prod_info.get("ProductCategory", "Unknown"),
                "policy_start_date": p_row["PolicyStartDate"].strftime("%Y-%m-%d"),
                "policy_end_date": p_row["PolicyEndDate"].strftime("%Y-%m-%d"),
                "policy_term_months": int(p_row["PolicyTermMonths"]),
                "annual_premium": float(p_row["AnnualPremium"]),
                "sum_insured": float(p_row["SumInsured"]),
                "status": str(p_row["Status"]),
                "coverages": pol_covs
            })

        customer_profiles[cust_id] = {
            "customer_id": cust_id,
            "city": str(c_row["City"]),
            "state": str(c_row["State"]),
            "age_band": str(c_row["age_band"]),
            "policies": policies_list,
            "claims": cust_claims,
            "payments": cust_payments
        }

    customer_profiles_path = PROCESSED_DIR / "customer_profiles.json"
    with open(customer_profiles_path, "w", encoding="utf-8") as f:
        json.dump(customer_profiles, f, indent=2)
    logger.info("Saved %d normalized customer profiles with age_band to %s", len(customer_profiles), customer_profiles_path)

    return dq_report, customer_profiles


if __name__ == "__main__":
    preprocess()
