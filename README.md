# OmniRisk: Automated Insurance Underwriting Risk Profile Summarizer (v2.0)

> **TCS Technology Day Problem-Solving Challenge**  
> Explainable AI-assisted underwriting summarizer built with a single-agent architecture, deterministic mathematical risk engine, and fact-grounded Gemini 3.5 Flash synthesis with transparent zero-failure fallback.

---

## ⚡ 30-Second Code Navigation

| Component | Location | Responsibility |
|---|---|---|
| **API** | [`app/api/routes.py`](file:///c:/Users/Jeevan%20kumar/Documents/OmniRisk/app/api/routes.py) | FastAPI REST endpoints (`/health`, `/analyze`, `/api/simulate`, `/api/portfolio`, `/api/customer-json/{id}`) |
| **Data Ingestion** | [`app/services/data_loader.py`](file:///c:/Users/Jeevan%20kumar/Documents/OmniRisk/app/services/data_loader.py) | In-memory cached dataset loader, portfolio aggregator, and enriched JSON builder |
| **Feature Engineering** | [`app/services/feature_engine.py`](file:///c:/Users/Jeevan%20kumar/Documents/OmniRisk/app/services/feature_engine.py) | Calculates 20+ insurance features, generates claim timeline, and computes data relevance |
| **Risk Engine** | [`app/services/risk_engine.py`](file:///c:/Users/Jeevan%20kumar/Documents/OmniRisk/app/services/risk_engine.py) | Deterministic scoring (0-100), Risk Provenance ("Trace Risk"), and What-If simulator |
| **Evidence Engine** | [`app/services/evidence_engine.py`](file:///c:/Users/Jeevan%20kumar/Documents/OmniRisk/app/services/evidence_engine.py) | Extracts fact-grounded risk drivers and positive underwriting factors |
| **GenAI Summarizer** | [`app/services/summarizer.py`](file:///c:/Users/Jeevan%20kumar/Documents/OmniRisk/app/services/summarizer.py) | Gemini 3.5 Flash (medium thinking) with transparent deterministic fallback and trace checklist |
| **Evaluation** | [`app/services/evaluation.py`](file:///c:/Users/Jeevan%20kumar/Documents/OmniRisk/app/services/evaluation.py) | Actuarial Rubric Alignment Benchmark (85.8%) + ML Challenger comparison table |
| **Schemas** | [`app/schemas/risk_schema.py`](file:///c:/Users/Jeevan%20kumar/Documents/OmniRisk/app/schemas/risk_schema.py) | Pydantic domain models, input contracts, execution trace, and simulation schemas |
| **Frontend** | [`frontend/index.html`](file:///c:/Users/Jeevan%20kumar/Documents/OmniRisk/frontend/index.html) | Interactive web interface with JSON Explorer, Portfolio view, What-If simulator, and pipeline |
| **Dataset Preprocessing** | [`scripts/preprocess_dataset.py`](file:///c:/Users/Jeevan%20kumar/Documents/OmniRisk/scripts/preprocess_dataset.py) | Derives age bands, strips PII, audits data quality, and outputs clean normalized JSON |

---

## 🎯 Phase 2 Upgrades & Key Capabilities

1. **Gemini 3.5 Flash Migration & Transparent Telemetry**:
   - Upgraded to `gemini-3.5-flash` with medium thinking support (`thinking_budget=1024`).
   - Distinct execution modes: **`LIVE GEMINI`** vs **`DETERMINISTIC FALLBACK`**.
   - Fallback execution is **never falsely labeled as Gemini execution**.
   - Remote roundtrip API latency is tracked and reported separately from local processing latency.

2. **Customer JSON Explorer**:
   - Dedicated interactive JSON Explorer tab for inspecting any customer account from `data/processed/customer_profiles.json`.
   - Supports viewing, copying, JSON path navigation, and source-to-feature mapping.
   - PII protection: `FirstName`, `LastName`, and `DOB` are completely stripped. `age_band` (e.g. `35-49`) is derived before DOB removal.

3. **Risk Provenance ("Trace Risk")**:
   - Every score contributor maps back through the complete audit trail:
     `Risk Score ➔ Risk Factor ➔ Feature Name ➔ Supporting Evidence ➔ Source Records ➔ JSON Path ➔ Source Module`.

4. **Claim Timeline & Profile Deep-Dive**:
   - Chronological table of all customer loss events showing Claim ID, Date, Amount, IslandSeverity, Status, Policy, and Data Integrity flags.

5. **Data Quality vs. Data Relevance Separation**:
   - **Data Quality**: Intrinsic record validity (flagged anomalies, date boundary violations).
   - **Data Relevance**: Information coverage and completeness supporting underwriting decisions (relevance score %, supported features).

6. **Interactive What-If Risk Simulator**:
   - Demonstration-only simulator allowing underwriters to test sensitivity on recent claims, loss ratios, open claims, and severity.
   - Computes Before, After, Delta, and Changed factors without altering underlying records.

7. **Portfolio Overview (120 Profiles)**:
   - Aggregated portfolio dashboard: **55 Low**, **50 Medium**, **15 High** risk accounts.
   - Searchable directory with click-to-analyze navigation.

8. **AI Execution Trace & Governance**:
   - Transparent 8-point verification checklist (`Data Loaded`, `Features Generated`, `Risk Calculated`, `Evidence Extracted`, `PII Removed`, `Prompt Constructed`, `Gemini API Called`, `Output Schema Validated`).
   - Prompt injection defense: Freeform fields and identifiers are sanitized; customer attributes are treated as untrusted data.

9. **Actuarial Rubric Alignment Benchmark & ML Challengers**:
   - Honest labeling: Evaluates agreement against an independent actuarial standard.
   - Empirical 5-fold cross-validation table comparing the **Deterministic Rule Engine (85.8%)** against **Logistic Regression (93.3%)**, **XGBoost (90.8%)**, **Random Forest (88.3%)**, and **DummyClassifier (40.8%)**.

---

## 🚀 Quickstart Guide

### 1. Prerequisites
- Python 3.10+
- Installed packages: `fastapi`, `uvicorn`, `pydantic`, `pandas`, `openpyxl`, `scikit-learn`, `pytest`

### 2. Environment Setup (Optional for Live Gemini)
```bash
cp .env.example .env
# Set GENAI_API_KEY=your_gemini_api_key
```
*(If no API key is set, the system transparently runs in `DETERMINISTIC FALLBACK` mode).*

### 3. Preprocess Dataset
```bash
python scripts/preprocess_dataset.py
```

### 4. Run the Application
```bash
python -m uvicorn app.main:app --host 127.0.0.1 --port 8000 --reload
```
Open in browser:
- **Web Application**: [http://127.0.0.1:8000](http://127.0.0.1:8000)
- **Interactive API Docs**: [http://127.0.0.1:8000/docs](http://127.0.0.1:8000/docs)

### 5. Run Automated Tests
```bash
python -m pytest -v
```
*(All 16 unit and integration tests pass with 100% success).*

---

## 👥 Real Demo Profiles

| Risk Tier | Customer ID | Score | Age Band | Profile Highlights | Underwriting Action |
|---|---|---|---|---|---|
| 🟢 **LOW RISK** | `CUST1005` | **0 / 100** | 35-49 | 0 claims, ₹14,860 paid premium, Active Homeowners. | Fast-track standard renewal with preferred discount. |
| 🟡 **MEDIUM RISK** | `CUST1025` | **52 / 100** | 35-49 | 3 claims across 48mo tenure, Loss Ratio: 5.53, Active multi-line. | Standard renewal with claim documentation verification. |
| 🔴 **HIGH RISK** | `CUST1003` | **77 / 100** | 35-49 | 7 claims (Critical severity >₹150k), 4 policies, high frequency. | Senior Underwriter referral, +25% deductible, loss audit. |

---

## 🔄 What OmniRisk Does

```
Fragmented Insurance Data
        ↓
Data Quality & Privacy (PII Stripped, Age Band Derived)
        ↓
Feature Engineering (20+ Actuarial Indicators)
        ↓
Deterministic Risk Engine (0-100 Score & Additive Points)
        ↓
Evidence Extraction (Fact-Grounded Drivers & Mitigations)
        ↓
Customer JSON (Standardized Schema)
        ↓
Gemini 3.5 Flash (Synthesis Layer / Deterministic Fallback)
        ↓
Underwriter Brief (Actionable Summary)
        ↓
Human Decision (Underwriter Review & Approval)
```

> **Core Philosophy**: *"OmniRisk converts fragmented insurance records into an explainable, evidence-backed risk profile. The deterministic engine owns the risk score; Gemini converts verified evidence into an underwriter-ready summary."*
