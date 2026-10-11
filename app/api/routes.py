"""
OmniRisk - FastAPI Application Routes (Phase 2)
REST endpoints for underwriting analysis, JSON explorer, What-If simulation,
portfolio management, data quality, and actuarial benchmark evaluation.
"""

import time
import logging
from typing import Any, Dict, List, Optional
from fastapi import APIRouter, HTTPException, Query

from app.config.settings import settings
from app.schemas.risk_schema import (
    AnalyzeRequest,
    CustomerProfile,
    DemoProfileItem,
    HealthResponse,
    PortfolioSummary,
    RiskAssessmentResult,
    WhatIfRequest,
    WhatIfResult,
)
from app.services.data_loader import data_loader
from app.services.feature_engine import feature_engine
from app.services.risk_engine import risk_engine
from app.services.evidence_engine import evidence_engine
from app.services.summarizer import summarizer_service
from app.services.evaluation import evaluation_service

logger = logging.getLogger(__name__)
router = APIRouter()


@router.get("/health", response_model=HealthResponse, tags=["System"])
def health_check():
    """Health check endpoint validating service status and cached profile dataset."""
    all_profiles = data_loader.get_all_profiles()
    return HealthResponse(
        status="healthy",
        project=settings.PROJECT_NAME,
        version=settings.VERSION,
        dataset_loaded=bool(all_profiles),
        total_profiles=len(all_profiles),
    )


@router.get("/api/demo-profiles", response_model=List[DemoProfileItem], tags=["Demo"])
def get_demo_profiles():
    """Returns curated Low, Medium, and High risk demo profiles sourced directly from insurance_model.xlsx."""
    return [
        DemoProfileItem(
            risk_band="LOW",
            customer_id="CUST1005",
            summary_hint="Zero claim history, stable Active Homeowners policy, full payment compliance.",
            expected_score=0,
            policy_id="POL3082",
            annual_premium=14860.0,
            total_claims=0,
        ),
        DemoProfileItem(
            risk_band="MEDIUM",
            customer_id="CUST1025",
            summary_hint="Multi-policy holder (Travel & Homeowners) with moderate loss ratio and 3 claims.",
            expected_score=52,
            policy_id="POL3021 / POL3137",
            annual_premium=21320.0,
            total_claims=3,
        ),
        DemoProfileItem(
            risk_band="HIGH",
            customer_id="CUST1003",
            summary_hint="Multi-line exposure across 4 policies with Critical claim severity and high claim frequency.",
            expected_score=77,
            policy_id="POL3010 / POL3072 / POL3100 / POL3102",
            annual_premium=70885.0,
            total_claims=7,
        ),
    ]


@router.get("/api/customers", response_model=List[str], tags=["Data"])
def list_customers():
    """Returns all 120 customer identifiers available in the authoritative operational dataset."""
    return data_loader.list_customer_ids()


@router.get("/api/portfolio", response_model=PortfolioSummary, tags=["Portfolio"])
def get_portfolio():
    """Returns portfolio distribution across LOW, MEDIUM, and HIGH risk bands and top high-risk profiles."""
    return data_loader.get_portfolio_summary()


@router.get("/api/customer-json/{customer_id}", tags=["Explorer"])
def get_customer_json(customer_id: str):
    """Returns fully structured, enriched JSON object for the Customer JSON Explorer."""
    data = data_loader.get_enriched_customer_json(customer_id)
    if not data:
        raise HTTPException(status_code=404, detail=f"Customer '{customer_id}' not found.")
    return data


@router.get("/api/data-quality", tags=["Data Quality"])
def get_data_quality():
    """Returns the comprehensive dataset audit and data-cleaning exclusion report."""
    return data_loader.get_data_quality_report()


@router.get("/api/evaluation", tags=["Evaluation"])
def get_evaluation():
    """Returns Actuarial Rubric Alignment Benchmark results and ML challenger comparisons."""
    return evaluation_service.evaluate_benchmark()


@router.post("/analyze", response_model=RiskAssessmentResult, tags=["Analysis"])
def analyze_risk(request: AnalyzeRequest):
    """
    Consolidates fragmented customer data, executes feature engineering,
    calculates deterministic risk score, extracts evidence, traces provenance,
    and synthesizes an underwriter brief via Gemini 3.5 Flash / Fallback.
    """
    start_total = time.perf_counter()
    latency_breakdown: Dict[str, float] = {}

    # 1. Resolve Profile
    t0 = time.perf_counter()
    profile: Optional[CustomerProfile] = None

    if request.profile is not None:
        profile = request.profile
    elif request.customer_id:
        profile = data_loader.get_profile(request.customer_id)
        if not profile:
            raise HTTPException(
                status_code=404,
                detail=f"Customer ID '{request.customer_id}' not found in processed dataset."
            )
    else:
        raise HTTPException(
            status_code=400,
            detail="Either 'customer_id' or 'profile' payload must be provided."
        )
    latency_breakdown["data_lookup_ms"] = round((time.perf_counter() - t0) * 1000, 2)

    # 2. Feature Engineering
    t1 = time.perf_counter()
    features = feature_engine.calculate_features(profile)
    latency_breakdown["feature_engineering_ms"] = round((time.perf_counter() - t1) * 1000, 2)

    # 3. Deterministic Risk Engine + Provenance Trace
    t2 = time.perf_counter()
    risk_score, risk_level, score_contributors, provenance = risk_engine.calculate_risk(features, profile)
    latency_breakdown["risk_calculation_ms"] = round((time.perf_counter() - t2) * 1000, 2)

    # 4. Evidence Extraction
    t3 = time.perf_counter()
    drivers, positive_factors = evidence_engine.extract_evidence(features, risk_score, risk_level)
    latency_breakdown["evidence_extraction_ms"] = round((time.perf_counter() - t3) * 1000, 2)

    # 5. GenAI Underwriter Synthesis (Gemini 3.5 Flash or Fallback)
    t4 = time.perf_counter()
    brief, execution_trace = summarizer_service.generate_brief(
        profile=profile,
        features=features,
        risk_score=risk_score,
        risk_level=risk_level,
        drivers=drivers,
        positive_factors=positive_factors,
    )
    latency_breakdown["summarizer_ms"] = round((time.perf_counter() - t4) * 1000, 2)

    total_latency_sec = round(time.perf_counter() - start_total, 3)

    return RiskAssessmentResult(
        customer_id=profile.customer_id,
        risk_score=risk_score,
        risk_level=risk_level,
        score_breakdown=score_contributors,
        provenance=provenance,
        features=features,
        underwriter_brief=brief,
        execution_trace=execution_trace,
        claim_timeline=features.claim_timeline,
        latency_breakdown_ms=latency_breakdown,
        total_latency_sec=total_latency_sec,
        data_quality=features.data_quality,
        data_relevance=features.data_relevance,
    )


@router.post("/api/simulate", response_model=WhatIfResult, tags=["Simulation"])
def simulate_what_if(req: WhatIfRequest):
    """
    Demonstration-only What-If Risk Simulator.
    Simulates parameter variations on the deterministic risk engine without altering source records.
    """
    profile = data_loader.get_profile(req.customer_id)
    if not profile:
        raise HTTPException(status_code=404, detail=f"Customer ID '{req.customer_id}' not found.")

    base_features = feature_engine.calculate_features(profile)
    result = risk_engine.simulate_what_if(
        base_features=base_features,
        customer_id=req.customer_id,
        claims_last_12_delta=req.claims_last_12_months_delta or 0,
        loss_ratio_override=req.loss_ratio_override,
        open_claims_override=req.open_claims_override,
        severity_override=req.severity_override,
    )
    return result
