# OmniRisk Architecture Specification

## Overview

OmniRisk is an explainable AI-assisted underwriting risk profile summarizer built for the **TCS Technology Day Challenge**. It unifies fragmented operational insurance tables into a single-agent decision-support brief.

```
┌────────────────────────────────────────────────────────┐
│             Primary Operational Dataset                │
│             data/raw/insurance_model.xlsx              │
└──────────────────────────┬─────────────────────────────┘
                           │
                           ▼
┌────────────────────────────────────────────────────────┐
│        Ingestion & Preprocessing Pipeline              │
│          scripts/preprocess_dataset.py                 │
│  - Strips PII (FirstName, LastName, DOB)               │
│  - Identifies DQ anomalies (Dates, Sum Insured)        │
│  - Normalizes relational structures                    │
└──────────────────────────┬─────────────────────────────┘
                           │
                           ▼
┌────────────────────────────────────────────────────────┐
│             Preprocessed Cache & Storage               │
│      data/processed/customer_profiles.json             │
│      data/processed/data_quality_report.json           │
└──────────────────────────┬─────────────────────────────┘
                           │
                           ▼
┌────────────────────────────────────────────────────────┐
│               OmniRisk Single-Agent Core               │
│                                                        │
│  1. Feature Engine (app/services/feature_engine.py)    │
│     - 20+ Actuarial risk features                      │
│     - Segregated valid vs anomalous records            │
│                                                        │
│  2. Deterministic Risk Engine (risk_engine.py)         │
│     - Bounded 0-100 mathematical score                 │
│     - Configurable weights (Settings.py)               │
│     - Strict additive point attribution                │
│                                                        │
│  3. Evidence Engine (evidence_engine.py)               │
│     - 100% Fact-grounded driver + evidence pairs       │
│     - Positive underwriting factor extraction          │
│                                                        │
│  4. GenAI Summarizer (summarizer.py)                   │
│     - Synthesis & plain-language brief                 │
│     - Gemini integration with deterministic fallback   │
└──────────────────────────┬─────────────────────────────┘
                           │
                           ▼
┌────────────────────────────────────────────────────────┐
│               FastAPI API & Web Interface              │
│            GET /health, POST /analyze                  │
│               frontend/index.html                      │
└────────────────────────────────────────────────────────┘
```

## Architectural Principles

1. **Single-Agent System**:
   A single cohesive risk profiling agent orchestrates internal domain services (Feature Engine, Risk Engine, Evidence Engine, GenAI Summarizer). No convoluted multi-agent overhead.

2. **Source of Truth Separation**:
   - The **Deterministic Risk Engine** owns arithmetic, counting, weight attribution, and numerical scoring.
   - The **GenAI Layer** acts strictly as the explanation and communication layer. The LLM is forbidden from inventing scores, changing risk classifications, or creating hallucinations.

3. **Sub-second Response Times**:
   Cached normalized representations eliminate repeated runtime Excel parsing, enabling latency < 1.0 second.

4. **Zero-Failure Fallback**:
   If GenAI API credentials are absent or remote calls encounter rate limits, the system automatically uses a deterministic underwriter rule generator that produces an identical response schema.
