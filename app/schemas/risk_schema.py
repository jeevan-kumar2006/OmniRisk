"""
OmniRisk - Pydantic Data & API Schemas (Phase 2)
Includes Risk Provenance, Execution Traces, What-If Simulation,
Claim Timelines, and Data Relevance Schemas.
"""

from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field


# ==========================================
# Domain Data Schemas
# ==========================================

class CoverageItem(BaseModel):
    coverage_id: str
    coverage_name: str
    coverage_sum: float


class PolicyItem(BaseModel):
    policy_id: str
    agent_id: Optional[str] = None
    product_id: Optional[str] = None
    product_name: Optional[str] = None
    product_category: Optional[str] = None
    policy_start_date: str
    policy_end_date: str
    policy_term_months: int
    annual_premium: float
    sum_insured: float
    status: str
    coverages: List[CoverageItem] = []


class ClaimItem(BaseModel):
    claim_id: str
    policy_id: str
    customer_id: str
    claim_date: str
    claim_amount: float
    claim_status: str
    settlement_date: Optional[str] = None
    severity: str
    is_date_valid: bool = True
    is_amount_valid: bool = True
    quality_flags: List[str] = []


class PaymentItem(BaseModel):
    payment_id: str
    policy_id: str
    customer_id: str
    payment_date: str
    premium_amount: float
    payment_method: str


class CustomerProfile(BaseModel):
    customer_id: str
    city: Optional[str] = None
    state: Optional[str] = None
    age_band: Optional[str] = None
    policies: List[PolicyItem] = []
    claims: List[ClaimItem] = []
    payments: List[PaymentItem] = []


# ==========================================
# Feature Engine & Timeline Schemas
# ==========================================

class ClaimTimelineItem(BaseModel):
    claim_id: str
    date: str
    amount: float
    severity: str
    status: str
    policy_id: str
    is_valid: bool
    flags: List[str] = []


class ClaimFeatures(BaseModel):
    valid_claim_count: int
    claims_last_12_months: int
    claims_last_24_months: int
    total_claim_amount: float
    average_claim_amount: float
    maximum_claim_amount: float
    claim_frequency: float = Field(..., description="Claims per year of tenure")
    claim_recency: Optional[float] = Field(None, description="Months since last claim")
    claim_trend: str = Field(..., description="'Increasing', 'Decreasing', 'Stable', or 'None'")


class SeverityFeatures(BaseModel):
    low_claim_count: int
    medium_claim_count: int
    high_claim_count: int
    critical_claim_count: int
    highest_severity: str


class FinancialFeatures(BaseModel):
    total_premium_paid: float
    total_claim_amount: float
    loss_ratio: float
    premium_to_sum_insured_ratio: float


class PolicyFeatures(BaseModel):
    policy_tenure: int = Field(..., description="Total tenure in months")
    policy_status: str
    sum_insured: float
    annual_premium: float
    coverage_count: int
    coverage_profile: List[str]


class ClaimStatusFeatures(BaseModel):
    open_claim_count: int
    pending_claim_count: int
    rejected_claim_count: int
    settled_claim_count: int


class PaymentFeatures(BaseModel):
    payment_count: int
    payment_methods: List[str]
    payment_consistency: str


class DataQualityFlags(BaseModel):
    excluded_temporal_claims_count: int
    excluded_amount_claims_count: int
    flagged_claims_count: int
    warnings: List[str] = []


class DataRelevance(BaseModel):
    total_source_records: int
    valid_source_records: int
    excluded_source_records: int
    features_supported: int
    features_unavailable: int
    relevance_score_percent: float
    impact_on_assessment: str


class EngineFeatures(BaseModel):
    claims: ClaimFeatures
    severity: SeverityFeatures
    financial: FinancialFeatures
    policy: PolicyFeatures
    claim_status: ClaimStatusFeatures
    payment: PaymentFeatures
    data_quality: DataQualityFlags
    data_relevance: DataRelevance
    claim_timeline: List[ClaimTimelineItem] = []


# ==========================================
# Provenance & Explainability Schemas
# ==========================================

class RiskProvenanceItem(BaseModel):
    factor: str
    points: float
    max_points: float
    feature_name: str
    supporting_evidence: str
    source_records: str
    json_path: str
    source_module: str


class RiskScoreContributor(BaseModel):
    factor: str
    points: float
    max_points: float
    description: str


class RiskDriver(BaseModel):
    factor: str
    impact: str  # HIGH, MEDIUM, LOW
    evidence: str


class UnderwriterBrief(BaseModel):
    summary: str
    key_indicators: List[str]
    positive_factors: List[str]
    risk_drivers: List[RiskDriver]
    recommended_action: str
    confidence: float


class AIExecutionTrace(BaseModel):
    data_loaded: bool = True
    features_generated: bool = True
    risk_calculated: bool = True
    evidence_extracted: bool = True
    pii_removed: bool = True
    prompt_constructed: bool = True
    gemini_api_called: bool = False
    structured_output_validated: bool = True
    fallback_used: bool = False
    provider: str
    model: str
    execution_mode: str  # 'LIVE GEMINI' or 'DETERMINISTIC FALLBACK'
    remote_genai_latency_ms: Optional[float] = None
    local_processing_latency_ms: float = 0.0
    input_field_count: int
    pii_field_count: int = 0
    output_schema_status: str = "VALIDATED"


class RiskAssessmentResult(BaseModel):
    customer_id: str
    risk_score: int
    risk_level: str  # LOW, MEDIUM, HIGH
    score_breakdown: List[RiskScoreContributor]
    provenance: List[RiskProvenanceItem] = []
    features: EngineFeatures
    underwriter_brief: UnderwriterBrief
    execution_trace: AIExecutionTrace
    claim_timeline: List[ClaimTimelineItem] = []
    latency_breakdown_ms: Dict[str, float]
    total_latency_sec: float
    data_quality: DataQualityFlags
    data_relevance: DataRelevance


# ==========================================
# Simulation & Portfolio Schemas
# ==========================================

class WhatIfRequest(BaseModel):
    customer_id: str
    claims_last_12_months_delta: Optional[int] = 0
    loss_ratio_override: Optional[float] = None
    open_claims_override: Optional[int] = None
    severity_override: Optional[str] = None  # None, Low, Medium, High, Critical


class WhatIfResult(BaseModel):
    customer_id: str
    before_score: int
    before_level: str
    after_score: int
    after_level: str
    score_delta: int
    changed_factors: List[str]
    simulation_notice: str = "Simulation only — source data unchanged."


class PortfolioItem(BaseModel):
    customer_id: str
    risk_score: int
    risk_level: str
    valid_claims: int
    loss_ratio: float
    highest_severity: str
    policy_status: str
    annual_premium: float
    city: Optional[str] = None


class PortfolioSummary(BaseModel):
    total_customers: int
    low_count: int
    medium_count: int
    high_count: int
    top_high_risk: List[PortfolioItem]
    all_customers: List[PortfolioItem]


# ==========================================
# API Request / Response Schemas
# ==========================================

class AnalyzeRequest(BaseModel):
    customer_id: Optional[str] = None
    profile: Optional[CustomerProfile] = None


class DemoProfileItem(BaseModel):
    risk_band: str
    customer_id: str
    summary_hint: str
    expected_score: int
    policy_id: str
    annual_premium: float
    total_claims: int


class HealthResponse(BaseModel):
    status: str
    project: str
    version: str
    dataset_loaded: bool
    total_profiles: int
