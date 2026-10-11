"""
OmniRisk - Configuration Settings (Phase 2)
Centralized configuration for feature weights, risk score thresholds,
and GenAI runtime parameters (Gemini 3.5 Flash).
"""

import os
from pathlib import Path
from pydantic import BaseModel
from dotenv import load_dotenv

load_dotenv()

BASE_DIR = Path(__file__).resolve().parent.parent.parent


class RiskThresholds(BaseModel):
    # Score classification boundaries
    low_max: float = 39.0
    medium_max: float = 69.0
    # Values >= 70 are HIGH

    # Loss ratio thresholds
    loss_ratio_low: float = 0.50
    loss_ratio_medium: float = 1.00
    loss_ratio_high: float = 2.00

    # Claim frequency thresholds (claims per year)
    claim_freq_low: float = 0.5
    claim_freq_medium: float = 1.5

    # Claim recency thresholds (months)
    recent_months_cutoff: float = 12.0
    medium_recency_cutoff: float = 24.0


class RiskWeights(BaseModel):
    """
    Normalized weights allocating 100 maximum risk score points.
    Claim frequency & recency: 30%
    Loss ratio: 25%
    Claim severity: 20%
    Open/pending claims: 10%
    Policy stability: 10%
    Coverage / other indicators: 5%
    """
    claim_frequency_recency: float = 30.0
    loss_ratio: float = 25.0
    claim_severity: float = 20.0
    open_pending_claims: float = 10.0
    policy_stability: float = 10.0
    coverage_other: float = 5.0


class Settings:
    PROJECT_NAME: str = "OmniRisk - Insurance Automated Risk Profile Summarizer"
    VERSION: str = "2.0.0"

    # Paths
    PROCESSED_DATA_DIR: Path = BASE_DIR / "data" / "processed"
    REFERENCE_DATA_DIR: Path = BASE_DIR / "data" / "reference"
    CUSTOMER_PROFILES_PATH: Path = PROCESSED_DATA_DIR / "customer_profiles.json"
    DATA_QUALITY_REPORT_PATH: Path = PROCESSED_DATA_DIR / "data_quality_report.json"
    ISLAND_SEVERITY_PATH: Path = REFERENCE_DATA_DIR / "island_severity.json"

    # Risk Engine Configuration
    WEIGHTS: RiskWeights = RiskWeights()
    THRESHOLDS: RiskThresholds = RiskThresholds()

    # GenAI Configuration (Migrated to Gemini 3.5 Flash with Medium Thinking)
    GENAI_API_KEY: str = os.getenv("GENAI_API_KEY", os.getenv("GEMINI_API_KEY", ""))
    GENAI_MODEL: str = os.getenv("GENAI_MODEL", "gemini-3.5-flash")
    GENAI_TEMPERATURE: float = float(os.getenv("GENAI_TEMPERATURE", "0.2"))
    GENAI_THINKING_BUDGET: int = int(os.getenv("GENAI_THINKING_BUDGET", "1024"))

    # Reference snapshot date for temporal metrics
    SNAPSHOT_DATE: str = "2025-10-15"


settings = Settings()
