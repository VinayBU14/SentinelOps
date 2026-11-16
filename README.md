# SentinelOps — Cyber Asset Inventory & Explainable Risk Analysis

SentinelOps is a lightweight, locally runnable cybersecurity analytics application that ingests an organization's cyber asset inventory in CSV or JSON format, validates its data quality against deterministic rules, identifies inventory gaps (such as ownerless assets and duplicate IDs), calculates transparent weighted risk scores, and presents the findings in an interactive React dashboard.

---

## 1. Feature Summary

* **Dual-Format Safe Ingestion**:
  * Ingests UTF-8 CSV (with or without BOM) and JSON formats (top-level array or `{ "assets": [...] }`).
  * Enforces a 10 MB upload limit.
  * Preserves source files in memory without modifying the original data on disk.
  * Accurately skips and tallies blank rows.
* **Deterministic Two-Pass Data Quality Validation**:
  * **Pass 1 (Batch-scoped duplicate detection)**: Blocks **every** row sharing a duplicate asset ID (`DUPLICATE_ASSET_ID`); flags shared IP addresses as non-blocking warnings (`DUPLICATE_IP`).
  * **Pass 2 (Field-level validation)**: Enforces required attributes (`asset_id`, `hostname`, `ip_address`, `asset_type`, `criticality`, `vulnerability_severity`, `vulnerability_count`).
  * Canonical IP address verification via Python's `ipaddress` module (IPv4 and IPv6).
  * Distinguishes blocking errors from non-blocking warnings (missing owners, unparseable dates, invalid booleans).
  * Retains ownerless assets with a `MISSING_OWNER` warning, keeping them eligible for risk prioritization with an ownership penalty.
* **Explainable, Rule-Based Risk Engine**:
  * Mathematical formula:
    $$\text{Risk Score} = (0.50 \times \text{Vulnerability Score}) + (0.30 \times \text{Criticality Score}) + (0.20 \times \text{Ownership Risk Score})$$
  * Vulnerability Score mapping: Critical = 100, High = 75, Medium = 50, Low = 25, Informational/None = 0.
  * Criticality Score mapping: Critical = 100, High = 75, Medium = 50, Low = 25.
  * Ownership Risk Score mapping: Owner assigned = 0, Owner missing = 100.
  * Project thresholds: Low (0.0–29.99), Medium (30.0–59.99), High (60.0–79.99), Critical (80.0–100.0).
  * Automatically generates human-readable per-asset risk explanations without any external AI or LLM dependency.
  * Idempotent re-analysis: re-evaluates batches without creating duplicate assessments.
* **Modern Six-Page Dashboard**:
  * **Overview Dashboard**: High-level KPI cards, Recharts visualizations for asset type and risk distribution, Top 10 highest-risk assets.
  * **Upload & Import**: Drag-and-drop interface, max-size indicator, live validation breakdown, and one-click sample CSV download.
  * **Asset Inventory**: Paginated, searchable, multi-filtered table (Asset Type, Criticality, Severity, Department, Ownership status, Validation status, Risk Level).
  * **Data Quality**: Dedicated finding log with row number, asset ID, issue code, severity, blocking status, observed value, and remediation action.
  * **Risk Analysis**: Ranked risk table sorted by risk score descending, risk level filters, and interactive scoring breakdown.
  * **Import History**: Complete record of all uploaded batches, row counts, timestamps, SHA-256 hashes, and active batch switcher.
  * **Asset Detail Drawer**: Slide-over drawer presenting all 24 inventory attributes, validation issues, component score contributions, and generated explanations.
  * **Scoring Methodology Modal**: Transparent popup detailing the mathematical weights and cutoff points.

---

## 2. Architecture & Folder Structure

```text
SentinelOps/
├── README.md
├── SENTINELOPS_ANTIGRAVITY_SPEC.md
├── LICENSE
├── .gitignore
├── .env.example
├── datasets/
│   └── aegiscorp_asset_inventory_1200.csv  # Primary clean baseline dataset (untouched)
│
├── backend/
│   ├── requirements.txt
│   ├── app/
│   │   ├── main.py                         # FastAPI app, CORS, exception handlers, health & sample endpoints
│   │   ├── core/
│   │   │   ├── config.py                   # Environment & storage settings
│   │   │   └── errors.py                   # Custom HTTP exceptions
│   │   ├── db/
│   │   │   ├── session.py                  # SQLAlchemy engine & SQLite session maker (PRAGMA foreign_keys=ON)
│   │   │   └── init_db.py                  # Database schema initializer
│   │   ├── models/
│   │   │   ├── batch.py                    # ImportBatch model
│   │   │   ├── asset.py                    # Asset model (24 inventory fields)
│   │   │   ├── issue.py                    # ValidationIssue model
│   │   │   └── risk.py                     # RiskAssessment model
│   │   ├── schemas/
│   │   │   ├── batch.py                    # Pydantic schemas for batches & uploads
│   │   │   ├── asset.py                    # Pydantic schemas for assets
│   │   │   ├── issue.py                    # Pydantic schemas for validation issues
│   │   │   └── risk.py                     # Pydantic schemas for risk assessments
│   │   ├── services/
│   │   │   ├── normalization.py            # Canonical IP, ISO date, email, string cleanup
│   │   │   ├── ingestion.py                # CSV (BOM, headers, blanks) & JSON parser
│   │   │   ├── validation.py               # Deterministic 2-pass validation engine
│   │   │   ├── risk_engine.py              # Full-precision weighted risk engine & explanation generator
│   │   │   ├── batch_service.py            # Upload orchestrator & persistence coordinator
│   │   │   └── analysis_service.py         # Batch scoring & idempotency service
│   │   ├── repositories/
│   │   │   ├── batch_repository.py         # Batch CRUD queries
│   │   │   ├── asset_repository.py         # Asset filtering & pagination
│   │   │   ├── issue_repository.py         # Issue filtering & pagination
│   │   │   └── risk_repository.py          # Ranked risk queries & aggregations
│   │   ├── api/
│   │   │   └── v1/
│   │   │       ├── uploads.py              # POST /api/v1/uploads
│   │   │       ├── batches.py              # GET /api/v1/batches, GET /api/v1/batches/{id}
│   │   │       ├── assets.py               # GET /api/v1/batches/{id}/assets
│   │   │       ├── issues.py               # GET /api/v1/batches/{id}/issues
│   │   │       └── risks.py                # POST /api/v1/batches/{id}/analyze, GET risks
│   │   └── tests/
│   │       ├── conftest.py                 # SQLite StaticPool in-memory test fixture
│   │       ├── test_ingestion.py           # Ingestion unit tests (BOM, CSV, JSON, headers)
│   │       ├── test_validation.py          # Validation engine unit tests (all 19 codes & boundaries)
│   │       ├── test_risk_engine.py         # Mathematical weights & threshold tests
│   │       ├── test_api_ingestion.py       # API integration tests & 1200 CSV baseline test
│   │       └── test_api_risks.py           # End-to-end risk analysis & idempotency tests
│   └── data/                               # Local SQLite database directory (gitignored)
│
└── frontend/
    ├── package.json
    ├── vite.config.ts                      # Vite configuration with API proxy to port 8000
    ├── tsconfig.json
    ├── index.html
    └── src/
        ├── App.tsx                         # Master application shell & state coordinator
        ├── main.tsx                        # React DOM root entry
        ├── types/                          # TypeScript interfaces
        ├── services/
        │   └── api.ts                      # REST client for all SentinelOps endpoints
        ├── styles/
        │   └── main.css                    # Cybersecurity dark/neutral enterprise design system
        ├── components/
        │   ├── Sidebar.tsx                 # 6-page navigation sidebar
        │   ├── TopBar.tsx                  # Active batch selector, refresh, upload CTA
        │   ├── StatCard.tsx                # Metric KPI card
        │   ├── RiskBadge.tsx               # Severity color badge
        │   ├── StatusBadge.tsx             # Validation status badge
        │   ├── AssetDetailDrawer.tsx       # Slide-over asset inspector with explanation
        │   ├── ScoringFormulaModal.tsx     # Interactive scoring methodology modal
        │   └── EmptyState.tsx              # Loading skeletons, empty & error states
        └── pages/
            ├── OverviewPage.tsx            # KPI cards, Recharts distributions, Top 10 risks
            ├── UploadPage.tsx              # Drag-and-drop ingestion with validation summary
            ├── InventoryPage.tsx           # Searchable, multi-filtered inventory table
            ├── DataQualityPage.tsx         # Issue logs, severity filters, remediation hints
            ├── RiskAnalysisPage.tsx        # Ranked risk assets, formula guide, score breakdowns
            └── ImportHistoryPage.tsx       # Historical batch switcher and audit logs
```

---

## 3. Setup and Run Commands

### Prerequisites
* Python 3.11+
* Node.js v18+ and npm

### Backend Setup
1. Create and activate a Python virtual environment:
   ```bash
   cd backend
   python3 -m venv venv
   source venv/bin/activate
   ```
2. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```
3. Start the FastAPI development server:
   ```bash
   uvicorn app.main:app --reload --host 127.0.0.1 --port 8000
   ```
   * The API will be available at: `http://127.0.0.1:8000`
   * Interactive Swagger documentation: `http://127.0.0.1:8000/docs`

### Frontend Setup
1. Navigate to `frontend/`:
   ```bash
   cd frontend
   npm install
   ```
2. Start the Vite development server:
   ```bash
   npm run dev
   ```
   * Open `http://localhost:5173` in your browser.

---

## 4. Test Commands and Actual Test Results

The backend contains a test suite covering ingestion, data validation rules, risk scoring boundaries, and end-to-end API workflows.

Run all tests from the repository root:
```bash
PYTHONPATH=backend backend/venv/bin/pytest backend/app/tests -v
```

### Actual Test Run Output
```text
============================= test session starts ==============================
platform linux -- Python 3.12.3, pytest-9.2.0, pluggy-1.7.0
rootdir: /home/vinay/Projects/SentinelOps
collected 39 items                                                             

backend/app/tests/test_api_ingestion.py::test_api_health_check PASSED    [  2%]
backend/app/tests/test_api_ingestion.py::test_api_get_sample_dataset PASSED [  5%]
backend/app/tests/test_api_ingestion.py::test_api_upload_synthetic_csv PASSED [  7%]
backend/app/tests/test_api_ingestion.py::test_api_upload_aegiscorp_1200_csv PASSED [ 10%]
backend/app/tests/test_api_ingestion.py::test_api_batch_isolation PASSED [ 13%]
backend/app/tests/test_api_ingestion.py::test_api_corrupted_fixture_and_issues_endpoint PASSED [ 15%]
backend/app/tests/test_api_risks.py::test_analyze_and_retrieve_risks PASSED [ 18%]
backend/app/tests/test_api_risks.py::test_analyze_full_aegiscorp_1200_dataset PASSED [ 21%]
backend/app/tests/test_ingestion.py::test_parse_valid_csv PASSED         [ 23%]
backend/app/tests/test_ingestion.py::test_parse_csv_with_utf8_bom PASSED [ 26%]
backend/app/tests/test_ingestion.py::test_parse_csv_blank_rows PASSED    [ 28%]
backend/app/tests/test_ingestion.py::test_parse_missing_headers PASSED   [ 31%]
backend/app/tests/test_ingestion.py::test_parse_empty_csv PASSED         [ 34%]
backend/app/tests/test_ingestion.py::test_parse_unsupported_extension PASSED [ 36%]
backend/app/tests/test_ingestion.py::test_parse_valid_json_array PASSED  [ 39%]
backend/app/tests/test_ingestion.py::test_parse_valid_json_wrapped_object PASSED [ 42%]
backend/app/tests/test_ingestion.py::test_parse_malformed_json PASSED    [ 44%]
backend/app/tests/test_risk_engine.py::test_vulnerability_severity_mappings PASSED [ 47%]
backend/app/tests/test_risk_engine.py::test_criticality_mappings PASSED  [ 50%]
backend/app/tests/test_risk_engine.py::test_spec_worked_example PASSED   [ 52%]
backend/app/tests/test_risk_engine.py::test_owner_present_no_penalty PASSED [ 55%]
backend/app/tests/test_risk_engine.py::test_boundary_conditions PASSED   [ 57%]
backend/app/tests/test_risk_engine.py::test_min_and_max_possible_scores PASSED [ 60%]
backend/app/tests/test_risk_engine.py::test_informational_severity PASSED [ 63%]
backend/app/tests/test_validation.py::test_valid_row PASSED              [ 65%]
backend/app/tests/test_validation.py::test_missing_asset_id PASSED       [ 68%]
backend/app/tests/test_validation.py::test_duplicate_asset_id_blocks_all_in_group PASSED [ 71%]
backend/app/tests/test_validation.py::test_duplicate_ip_warning_does_not_block PASSED [ 73%]
backend/app/tests/test_validation.py::test_invalid_ip_blocks PASSED      [ 76%]
backend/app/tests/test_validation.py::test_missing_and_invalid_asset_type PASSED [ 78%]
backend/app/tests/test_validation.py::test_missing_and_invalid_criticality PASSED [ 81%]
backend/app/tests/test_validation.py::test_missing_and_invalid_vulnerability_severity PASSED [ 83%]
backend/app/tests/test_validation.py::test_missing_owner_is_warning_and_eligible PASSED [ 86%]
backend/app/tests/test_validation.py::test_missing_owner_email_when_owner_present PASSED [ 89%]
backend/app/tests/test_validation.py::test_invalid_owner_email PASSED    [ 91%]
backend/app/tests/test_validation.py::test_invalid_date PASSED           [ 94%]
backend/app/tests/test_validation.py::test_invalid_vulnerability_count_blocks PASSED [ 97%]
backend/app/tests/test_validation.py::test_invalid_boolean_values PASSED [100%]

======================== 39 passed in 1.64s =========================
```

### Verification Against Primary AegisCorp Dataset (1,200 Records)
* **Ingested Rows**: 1,200
* **Data Quality Findings**: 0 Errors, 0 Warnings, 0 Blocked Rows (100% Valid clean baseline)
* **Risk Score Breakdown**:
  * Critical (80.0–100.0): 6 assets
  * High (60.0–79.99): 135 assets
  * Medium (30.0–59.99): 637 assets
  * Low (0.0–29.99): 422 assets
  * Total Scored Assets: 1,200

---

## 5. Known Limitations & Strict Boundaries

1. **Rule-Based Phase 1 Scope**: Risk scores are calculated exclusively from the deterministic Phase 1 formula: Vulnerability Severity (50%), Business Criticality (30%), and Ownership Status (20%). Contextual fields (`vulnerability_count`, `internet_facing`, `edr_enabled`, `backup_enabled`, etc.) are presented for operational awareness but do not alter the risk calculation.
2. **Local Academic Prototype**: User authentication, RBAC, and multi-tenancy are intentionally out of scope for Phase 1.
3. **Simulated Vulnerability Attributes**: Vulnerability severities and counts are synthetic inputs within the dataset and do not represent verified live CVE scans or active NVD enrichment.
4. **No Automated File Modification**: SentinelOps identifies data quality issues and provides suggested remediation, but does not alter uploaded files.

---

## 6. Specification Adherence & Deviations

* **Zero Deviations**: All architectural guidelines, database schemas, API routes, validation codes, scoring weights, and design directives specified in `SENTINELOPS_ANTIGRAVITY_SPEC.md` were implemented exactly as required.
* **Preservation of Baseline**: The supplied dataset `aegiscorp_asset_inventory_1200.csv` remains 100% pristine and unaltered.
* **Isolation of Concerns**: No ATT&CKLens concepts, NLP/LLM models, or external cloud dependencies were introduced.
