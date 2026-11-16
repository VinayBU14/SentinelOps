# SentinelOps --- Antigravity Implementation Specification

## College Mini-Project \| Cyber Asset Inventory and Explainable Risk Analysis

**Document purpose:** This is the authoritative implementation brief for
building the current college mini-project version of SentinelOps. Follow
this document and the supplied AegisCorp CSV as the project
requirements. Implement the defined scope accurately; do not add
unrelated features.

------------------------------------------------------------------------

## 1. Project identity and strict boundaries

### Project name

**SentinelOps --- Cyber Asset Inventory and Explainable Risk Analysis**

### Core purpose

Build a lightweight, locally runnable web application that accepts an
organization's cyber asset inventory in CSV or JSON format, validates
its data quality, identifies inventory gaps, calculates transparent
rule-based risk scores for eligible assets, and presents the results in
an interactive dashboard.

### Important project separation

This project is **SentinelOps only**.

-   Do not confuse SentinelOps with **ATT&CKLens**.
-   Do not import ATT&CK mapping, MITRE ATT&CK tactics/techniques,
    incident-report processing, LLM event extraction, BM25, embeddings,
    semantic retrieval, Groq/Grok APIs, STIX processing, or any
    ATT&CKLens concepts.
-   SentinelOps is an **asset inventory validation and explainable risk
    prioritization** project.
-   Do not add AI/ML, LLMs, network packet analysis, live scanning, SIEM
    integrations, graph intelligence, or vulnerability discovery to the
    current mini-project.

### Current mini-project scope (Phase 1)

Implement only:

1.  CSV and JSON asset ingestion.
2.  Data-quality validation.
3.  Clear separation of blocking errors and non-blocking warnings.
4.  Identification of ownerless assets.
5.  Transparent weighted, rule-based risk scoring.
6.  Risk ranking and per-asset explanations.
7.  Local database persistence.
8.  React dashboard and validation/risk views.
9.  Tests for ingestion, validation, scoring, persistence, and API
    behaviour.

### Explicitly out of scope for Phase 1

Do not implement:

-   CVE/NVD API lookups or automated vulnerability enrichment.
-   CVSS or EPSS calculation/integration.
-   Automatic vulnerability scanning or asset discovery.
-   Live network monitoring or packet capture.
-   External company integrations or Censys/Shodan data collection.
-   User authentication, RBAC, multi-tenancy, or cloud deployment.
-   Neo4j, graph analytics, machine learning, LLMs, SHAP, or
    explainability models.
-   Automated correction or modification of uploaded source files.
-   Automatic merging/deduplication of asset records.
-   Complex microservices or message queues.

Keep the code modular so future features can be added, but do not build
Phase 2 now.

------------------------------------------------------------------------

## 2. Supplied dataset --- use this as the primary project dataset

The user will provide this file to Antigravity at the start:

**`aegiscorp_asset_inventory_1200.csv`**

Treat this as the primary clean sample dataset for SentinelOps. Locate
it in the project workspace (the user may place it in the repository
root or `datasets/`). Do not silently replace it, regenerate it, or
change its contents.

### Dataset facts

-   Fictional organization: AegisCorp.
-   1,200 asset records.
-   24 columns.
-   Synthetic data created for this academic project.
-   Asset IDs, hostnames, and IP addresses are unique in the supplied
    clean file.
-   IP addresses are private lab addresses.
-   Vulnerability severity and vulnerability count are simulated input
    attributes, not verified CVE findings.
-   Do not describe the data as real company data or real vulnerability
    intelligence.

### Exact CSV columns

Use the actual supplied file as the source of truth. Its columns are:

``` text
asset_id
hostname
ip_address
asset_type
sub_category
operating_system
os_version
owner_name
owner_email
department
environment
criticality
vulnerability_severity
vulnerability_count
internet_facing
data_classification
location
purchase_date
last_updated
lifecycle_status
backup_enabled
edr_enabled
organization
data_source
```

Do not rename these source columns during ingestion. Internally, use
consistent Python naming and map fields explicitly if needed.

### Asset category distribution in the supplied file

  Asset type                 Count
  -------------------- -----------
  Workstation                  400
  Server                       180
  Network Device               120
  Application                  120
  Cloud Asset                  120
  Database                      80
  IoT Device                    70
  Security Appliance            60
  Storage                       50
  **Total**              **1,200**

### CSV handling requirements

-   The application must accept the supplied CSV through the UI; do not
    hardcode its records into the frontend or backend.
-   Include a small optional sample-file download link only if it can
    serve the supplied dataset from the backend safely.
-   The user may also upload JSON with equivalent field names.
-   Support UTF-8 CSV, including UTF-8 with BOM.
-   Validate headers before processing rows.
-   Handle empty files, malformed CSV/JSON, missing columns, extra
    columns, blank rows, and invalid data types gracefully.
-   Never execute uploaded content.
-   Do not trust uploaded filenames or use them directly as filesystem
    paths.
-   Apply a configurable upload-size limit (initial default: 10 MB).
-   Do not silently truncate records.
-   Preserve original source values for reporting; normalize values only
    in memory for validation/scoring.
-   Do not alter the original uploaded file.

------------------------------------------------------------------------

## 3. Technology stack and implementation approach

Use a straightforward monolithic application with a separate frontend
and backend.

### Backend

-   Python 3.11 or newer.
-   FastAPI for HTTP API.
-   Pydantic for request/response schemas.
-   Pandas for CSV/JSON tabular parsing where useful.
-   Python `ipaddress` module for IPv4/IPv6 validation.
-   SQLite for local persistence.
-   SQLAlchemy 2.x for database access and models.
-   Pytest and FastAPI TestClient for tests.

### Frontend

-   React with Vite.
-   TypeScript preferred.
-   React Router only if multiple pages/routes are useful.
-   Recharts for charts.
-   Lucide icons (or a consistent equivalent).
-   Native CSS modules or a clean component styling system. Do not
    introduce a large UI framework unless it materially improves
    consistency.

### Development

-   Git.
-   `.env` for configurable settings; commit `.env.example`, never
    secrets.
-   `README.md` with exact setup/run/test instructions.
-   Backend and frontend must run locally.

### Avoid unnecessary infrastructure

Do not use PostgreSQL, Docker, Redis, Celery, Kubernetes, or cloud
hosting as requirements for the mini-project. SQLite is sufficient and
keeps the application easy to run and demonstrate. Keep database access
behind a repository/service layer so SQLite can be replaced later if
necessary.

------------------------------------------------------------------------

## 4. Functional workflow

Implement this exact logical workflow:

``` text
User selects CSV/JSON file
          |
          v
File type, size and structure checks
          |
          v
Create import batch
          |
          v
Parse records and normalize values in memory
          |
          v
Validate schema and each record
          |
          +------------------------------+
          |                              |
          v                              v
Blocking errors                    Non-blocking warnings
          |                              |
          v                              v
Exclude affected record             Keep eligible record
from risk calculation               and retain warning
          |                              |
          +---------------+--------------+
                          |
                          v
             Risk assessment for eligible
                  records only
                          |
                          v
             Persist batch, assets, issues,
                scores and explanations
                          |
                          v
              React dashboard and reports
```

### Critical processing rules

1.  A record with a blocking error must not receive a risk score.
2.  A record with only non-blocking warnings can still receive a risk
    score.
3.  Missing ownership is a warning, not a blocking error. Ownerless
    assets must remain visible and be eligible for risk assessment.
4.  Duplicate asset IDs are ambiguous. Mark every row in a duplicate-ID
    group as blocked from scoring; do not arbitrarily choose one.
5.  Duplicate IP addresses are a warning by default, not an automatic
    block. They may represent shared services, NAT, virtual hosting, or
    data errors. Show all affected records for human review.
6.  Never silently discard a row. Every parsed row must be accounted for
    as valid, warning, or blocked, except fully blank rows which can be
    counted separately as skipped blank rows.
7.  Do not auto-correct or overwrite source values.
8.  A new upload creates a new import batch. Do not overwrite previous
    batch results.
9.  Risk scores must be reproducible from stored input values and the
    documented formula.

------------------------------------------------------------------------

## 5. Data schema and validation rules

### 5.1 Required and optional fields

Required for a record to be assessed: - `asset_id` - `hostname` -
`ip_address` - `asset_type` - `criticality` - `vulnerability_severity`

`owner_name` and `owner_email` are intentionally allowed to be empty so
that ownerless assets can be detected and scored with an ownership
penalty.

Other fields may be optional, but if supplied they must be validated
against their expected type or allowed values.

### 5.2 Allowed categorical values

Use case-insensitive comparison after trimming leading/trailing
whitespace. Preserve the original value for display where appropriate.

**`asset_type`:** - `Server` - `Workstation` - `Network Device` -
`Database` - `Application` - `Cloud Asset` - `Security Appliance` -
`Storage` - `IoT Device`

**`criticality`:** - `Critical` - `High` - `Medium` - `Low`

**`vulnerability_severity`:** - `Critical` - `High` - `Medium` - `Low` -
`Informational` - `None`

**`environment`:** - `Production` - `Staging` - `Development` -
`Testing`

**`internet_facing`, `backup_enabled`, `edr_enabled`:** - `Yes` - `No`

**`data_classification`:** - `Public` - `Internal` - `Confidential` -
`Restricted`

**`lifecycle_status`:** - `Active` - `Maintenance` - `Retiring`

Do not reject legitimate future values without reporting the exact field
and allowed values. For this mini-project, values outside the defined
lists should be validation errors where the field is used in logic, and
warnings for optional descriptive fields if appropriate.

### 5.3 Validation rules

Implement deterministic, field-level validation with stable issue codes.

  --------------------------------------------------------------------------------------------
  Code                            Field /         Severity       Blocking?      Expected
                                  condition                                     handling
  ------------------------------- --------------- -------------- -------------- --------------
  `MISSING_ASSET_ID`              Empty asset ID  Error          Yes            Block record

  `MISSING_HOSTNAME`              Empty hostname  Error          Yes            Block record

  `MISSING_IP`                    Empty IP        Error          Yes            Block record
                                  address                                       

  `INVALID_IP`                    IP is not valid Error          Yes            Block record
                                  IPv4 or IPv6                                  

  `MISSING_ASSET_TYPE`            Empty asset     Error          Yes            Block record
                                  type                                          

  `INVALID_ASSET_TYPE`            Asset type not  Error          Yes            Block record
                                  in allowed list                               

  `MISSING_CRITICALITY`           Empty           Error          Yes            Block record
                                  criticality                                   

  `INVALID_CRITICALITY`           Criticality not Error          Yes            Block record
                                  in allowed list                               

  `MISSING_SEVERITY`              Empty           Error          Yes            Block record
                                  vulnerability                                 
                                  severity                                      

  `INVALID_SEVERITY`              Severity not in Error          Yes            Block record
                                  allowed list                                  

  `DUPLICATE_ASSET_ID`            Same normalized Error          Yes            Block all rows
                                  asset ID occurs                               in duplicate
                                  more than once                                group
                                  in a batch                                    

  `DUPLICATE_IP`                  Same normalized Warning        No             Keep eligible;
                                  IP occurs more                                flag all
                                  than once                                     affected rows

  `MISSING_OWNER`                 Owner name is   Warning        No             Keep eligible;
                                  empty or                                      apply
                                  whitespace                                    ownership risk
                                                                                factor

  `MISSING_OWNER_EMAIL`           Owner exists    Warning        No             Keep eligible
                                  but email is                                  
                                  empty                                         

  `INVALID_OWNER_EMAIL`           Non-empty owner Warning        No             Keep eligible
                                  email has                                     
                                  invalid basic                                 
                                  email syntax                                  

  `INVALID_DATE`                  Supplied date   Warning        No             Keep eligible
                                  is not                                        
                                  parseable as                                  
                                  ISO                                           
                                  `YYYY-MM-DD`                                  

  `INVALID_VULNERABILITY_COUNT`   Supplied count  Error          Yes            Block record
                                  is not a                                      
                                  non-negative                                  
                                  integer                                       

  `INVALID_BOOLEAN_VALUE`         Yes/No field    Warning        No             Keep eligible;
                                  contains                                      show issue
                                  another value                                 

  `MISSING_OPTIONAL_FIELD`        Optional        Info           No             Keep eligible
                                  descriptive                                   
                                  field is empty                                
  --------------------------------------------------------------------------------------------

Additional validation: - Trim whitespace for comparisons. - Asset ID and
hostname duplicate checks should be case-insensitive after trimming. -
IP comparison should use canonical IP representation from
`ipaddress.ip_address`. - Validate `owner_email` only when non-empty. -
Validate dates only when non-empty; use `YYYY-MM-DD`. -
`vulnerability_count` must be an integer greater than or equal to
zero. - Blank rows should be counted as skipped, not treated as records
with 24 errors. - Distinguish file-level errors (unreadable file,
missing required headers) from row-level errors. - Do not use regex
alone to validate IP addresses; use Python's `ipaddress` module.

### 5.4 Validation output

Each issue should include: - `issue_code` - `severity` (`error`,
`warning`, `info`) - `blocking` (boolean) - `row_number` (CSV row
number, accounting for header) - `asset_id` if available -
`field_name` - `observed_value` (safely truncated if very long) -
`message` - `suggested_action`

Provide a summary: - Total parsed rows. - Valid rows with no issues. -
Rows with warnings only. - Blocked rows. - Total errors. - Total
warnings. - Blank rows skipped.

A row with multiple issues counts once in the relevant row category, but
each issue is separately counted in issue totals.

------------------------------------------------------------------------

## 6. Risk scoring engine

The current mini-project uses a **deterministic weighted rule-based
formula**. Do not train a model or call an external service.

### 6.1 Formula

``` text
Risk Score = (0.50 × Vulnerability Score)
           + (0.30 × Asset Criticality Score)
           + (0.20 × Ownership Risk Score)
```

Each input factor is between 0 and 100. Final score is between 0 and
100.

### 6.2 Input mappings

**Vulnerability severity → Vulnerability Score**

  Severity          Score
  --------------- -------
  Critical            100
  High                 75
  Medium               50
  Low                  25
  Informational         0
  None                  0

**Asset criticality → Criticality Score**

  Criticality     Score
  ------------- -------
  Critical          100
  High               75
  Medium             50
  Low                25

**Ownership → Ownership Risk Score**

  Condition                      Score
  ---------------------------- -------
  `owner_name` present               0
  `owner_name` missing/blank       100

`owner_email` missing by itself does not trigger the 20% ownership
penalty if `owner_name` is present. It creates a data-quality warning
only.

### 6.3 Risk levels

Use these project-defined thresholds:

  Final score   Risk level
  ------------- ------------
  0--29.99      Low
  30--59.99     Medium
  60--79.99     High
  80--100       Critical

Do not present these thresholds as official industry standards. Label
them as SentinelOps project thresholds.

### 6.4 Worked example

For an asset with: - Vulnerability severity = High → 75 - Criticality =
Critical → 100 - Owner missing → 100

``` text
Risk = (0.50 × 75) + (0.30 × 100) + (0.20 × 100)
     = 37.5 + 30 + 20
     = 87.5
Risk level = Critical
```

### 6.5 Explanation generation

Generate explanations directly from the score components. Do not use an
LLM.

Example: \> Critical risk (87.5/100). The asset has a High
vulnerability-severity input (75/100), Critical business criticality
(100/100), and no assigned owner (100/100 ownership-risk input).

Each result should retain: - vulnerability input label and numeric
score; - criticality input label and numeric score; -
owner-present/missing status and ownership score; - formula weights; -
final score; - risk level; - human-readable explanation.

### 6.6 Important limitations

-   Vulnerability severity is supplied by the uploaded dataset.
    SentinelOps does not discover vulnerabilities or verify CVEs.
-   `vulnerability_count` is displayed as context but is **not** part of
    the Phase 1 risk formula.
-   `internet_facing`, backup status, EDR status, data classification,
    and environment are displayed as inventory context but are **not**
    part of the Phase 1 risk formula.
-   Do not silently add extra weights or change the formula.
-   Records with blocking validation errors do not receive a risk score.
-   Records with warnings only (including missing owner) can receive a
    score.

------------------------------------------------------------------------

## 7. Database design (SQLite)

Use SQLAlchemy models and migrations or a simple versioned schema
initializer. Store each upload as a separate batch.

### 7.1 `import_batches`

Suggested fields: - `id` (UUID/string primary key) - `original_filename`
(display metadata only; never use as a path) - `file_type` (`csv` or
`json`) - `uploaded_at` (UTC timestamp) - `status` (`uploaded`,
`validated`, `analyzed`, `failed`) - `total_rows` - `valid_rows` -
`warning_rows` - `blocked_rows` - `error_count` - `warning_count` -
`blank_rows` - `file_sha256` (optional integrity/deduplication metadata)

### 7.2 `assets`

Suggested fields: - `id` (database primary key) - `batch_id` (foreign
key) - `source_row_number` - all 24 source fields, using appropriate
nullable types - `validation_status` (`valid`, `warning`, `blocked`) -
`created_at`

Do not make `asset_id` globally unique across all batches. It should be
unique only within a batch for duplicate validation purposes. Retain the
source row number.

### 7.3 `validation_issues`

Suggested fields: - `id` (database primary key) - `batch_id` (foreign
key) - `asset_record_id` (nullable foreign key to assets) -
`row_number` - `asset_id` (nullable) - `issue_code` - `severity` -
`blocking` - `field_name` - `observed_value` - `message` -
`suggested_action` - `created_at`

### 7.4 `risk_assessments`

Suggested fields: - `id` (database primary key) - `batch_id` (foreign
key) - `asset_record_id` (foreign key) - `vulnerability_score` -
`criticality_score` - `ownership_score` - `vulnerability_weight`
(0.50) - `criticality_weight` (0.30) - `ownership_weight` (0.20) -
`risk_score` - `risk_level` - `explanation` - `calculated_at`

Enforce foreign keys. Add indexes on `batch_id`, `asset_id`,
`risk_score`, and issue codes where appropriate.

------------------------------------------------------------------------

## 8. Backend API specification

Use a single FastAPI application with routers/services. Keep business
logic out of route handlers.

Suggested endpoints:

  ------------------------------------------------------------------------------------------------------
  Method                  Endpoint                                               Purpose
  ----------------------- ------------------------------------------------------ -----------------------
  `POST`                  `/api/v1/uploads`                                      Upload CSV/JSON, create
                                                                                 batch, parse and
                                                                                 validate

  `GET`                   `/api/v1/batches`                                      List previous import
                                                                                 batches

  `GET`                   `/api/v1/batches/{batch_id}`                           Batch summary and
                                                                                 status

  `GET`                   `/api/v1/batches/{batch_id}/assets`                    Paginated assets with
                                                                                 filters

  `GET`                   `/api/v1/batches/{batch_id}/issues`                    Paginated validation
                                                                                 issues

  `POST`                  `/api/v1/batches/{batch_id}/analyze`                   Calculate scores for
                                                                                 eligible records

  `GET`                   `/api/v1/batches/{batch_id}/risks`                     Paginated ranked risk
                                                                                 results

  `GET`                   `/api/v1/batches/{batch_id}/assets/{record_id}/risk`   Detailed score
                                                                                 breakdown

  `GET`                   `/api/v1/health`                                       Health check
  ------------------------------------------------------------------------------------------------------

### API behaviour

-   `POST /uploads` validates file type, size, parsing, headers and
    records. It creates a batch and persists the parsed records and
    issues.
-   The response includes `batch_id`, parsing/validation summary and
    batch status.
-   `POST /analyze` must reject batches that have not completed
    validation.
-   Analysis is idempotent: repeating it should replace/recalculate that
    batch's risk assessments consistently, not create duplicate scores.
-   Only records without blocking issues are scored.
-   A batch with zero eligible records should return a clear response;
    do not crash.
-   All list endpoints must support pagination (`limit`, `offset`) and
    deterministic sorting.
-   Risk endpoint default sort: risk score descending, then asset ID
    ascending.
-   Add filters for risk level, asset type, department, owner missing,
    validation status, and severity where appropriate.
-   Return consistent JSON error objects with useful messages.
-   Use appropriate HTTP status codes (400 malformed input, 413 too
    large, 415 unsupported type, 422 invalid file structure, 404 unknown
    batch/record, 500 unexpected server error).
-   Do not expose stack traces or internal filesystem paths to the
    frontend.

### Example upload response shape

``` json
{
  "batch_id": "uuid",
  "status": "validated",
  "filename": "aegiscorp_asset_inventory_1200.csv",
  "summary": {
    "total_rows": 1200,
    "valid_rows": 0,
    "warning_rows": 0,
    "blocked_rows": 0,
    "error_count": 0,
    "warning_count": 0,
    "blank_rows": 0
  },
  "message": "File uploaded and validated successfully."
}
```

The numbers above are placeholders illustrating the response structure.
Compute real counts from actual validation results; do not hardcode
them.

------------------------------------------------------------------------

## 9. Frontend design specification

Build a polished, modern cybersecurity analytics interface. The UI
should look like a professional security operations product, but remain
simple enough for a college mini-project demonstration.

### Visual direction

-   Product name: SentinelOps.
-   Style: clean enterprise cybersecurity dashboard.
-   Prefer a dark navy/slate sidebar with a light neutral main
    workspace, or a consistent dark theme if implemented carefully.
-   Use restrained accent colours: blue/cyan for primary actions, green
    for low/healthy, amber for warnings/medium, red for blocking
    errors/critical risk.
-   Avoid excessive gradients, glowing effects, animated backgrounds,
    oversized cards, and decorative clutter.
-   Use a consistent spacing scale, typography hierarchy, border radius,
    icon style, and table design.
-   Use Lucide icons consistently.
-   Make the layout responsive for laptop and smaller screens.
-   Provide visible loading, empty, error, success, and disabled states.
-   Ensure accessible contrast, keyboard focus, labels, and semantic
    controls.

### Recommended application layout

**Sidebar** - SentinelOps logo/name. - Overview. - Asset Inventory. -
Data Quality. - Risk Analysis. - Import History. - Small footer showing
local/demo environment.

**Top bar** - Current page title and breadcrumb. - Active batch selector
or batch label. - Upload button. - Optional refresh action.

### Page 1 --- Overview dashboard

Show data only for the selected batch. If no batch exists, show a
helpful empty state with an upload CTA.

Summary cards: - Total assets parsed. - Eligible assets. - Blocked
records. - Assets with warnings / ownerless assets. - Critical and High
risk counts after analysis.

Charts: - Asset distribution by category (bar or donut). - Risk
distribution (Low/Medium/High/Critical). - Validation issue distribution
by issue code/severity.

Below charts: - Top 10 highest-risk assets. - Recent import batches. -
Clear batch status and last analyzed time.

Do not show risk charts before risk analysis has run. Show an
explanatory placeholder instead.

### Page 2 --- Upload / Import

-   Drag-and-drop and browse file control.
-   Clearly state supported formats: CSV and JSON.
-   Show max file size.
-   Show selected filename and size.
-   Explain that the source file is not modified.
-   Display upload and validation progress.
-   On completion, show batch summary and link to validation results.
-   Show friendly errors for unsupported files or missing headers.

### Page 3 --- Asset Inventory

A searchable, paginated table with: - Asset ID - Hostname - IP address -
Asset type - Owner - Department - Criticality - Vulnerability severity -
Validation status - Risk score / level (only after analysis)

Filters: - Asset type - Department - Criticality - Severity - Owner
missing - Validation status - Risk level (after analysis)

Clicking a row opens an asset detail drawer/page with all inventory
fields, validation issues and risk explanation.

### Page 4 --- Data Quality

Show: - Total parsed rows. - Rows with blocking errors. - Rows with
warnings only. - Rows without issues. - Total errors and warnings.

Issue table: - Row number - Asset ID - Field - Issue code - Severity -
Blocking status - Observed value - Explanation - Suggested action

Filters by severity, issue code, field, and blocking status.

Use clear badges: - Error / blocking - Warning / non-blocking - Info

Do not offer automatic correction. Provide guidance for correcting the
original file and re-uploading it.

### Page 5 --- Risk Analysis

Show: - Risk distribution. - Ranked assets table. - Score and risk
level. - Filters and sorting. - A detail view with all three component
scores, weights, formula, and generated explanation.

Make the formula discoverable in a small "How scoring works" panel.
Clearly state that scores are project-defined and use supplied severity
data.

### Page 6 --- Import History

Show previous batches with: - Filename - Upload date/time - Total rows -
Validation status - Analysis status - Error/warning totals - Open batch
action

Do not mix results from different batches in dashboard totals or charts.

### Design quality requirements

-   Use a consistent component system: `StatCard`, `DataTable`,
    `StatusBadge`, `RiskBadge`, `EmptyState`, `LoadingSkeleton`,
    `ErrorState`, `FilterBar`, `DetailDrawer`.
-   Tables must have readable density, sticky headers if useful, row
    hover, pagination and empty states.
-   Use tooltips for unfamiliar scoring terms.
-   Use charts with legends and labels; do not rely on colour alone.
-   Avoid fake live telemetry, fake alerts, fake users, and decorative
    metrics.
-   Every displayed number must come from API data for the active batch.
-   Never hardcode the example dashboard figures from mockups.

------------------------------------------------------------------------

## 10. Suggested repository structure

``` text
SentinelOps/
├── README.md
├── SENTINELOPS_SPEC.md
├── .gitignore
├── .env.example
├── datasets/
│   └── aegiscorp_asset_inventory_1200.csv
│
├── backend/
│   ├── requirements.txt
│   ├── app/
│   │   ├── main.py
│   │   ├── core/
│   │   │   ├── config.py
│   │   │   └── errors.py
│   │   ├── api/
│   │   │   └── v1/
│   │   │       ├── uploads.py
│   │   │       ├── batches.py
│   │   │       ├── assets.py
│   │   │       ├── issues.py
│   │   │       └── risks.py
│   │   ├── schemas/
│   │   │   ├── batch.py
│   │   │   ├── asset.py
│   │   │   ├── issue.py
│   │   │   └── risk.py
│   │   ├── models/
│   │   │   ├── batch.py
│   │   │   ├── asset.py
│   │   │   ├── issue.py
│   │   │   └── risk.py
│   │   ├── services/
│   │   │   ├── ingestion.py
│   │   │   ├── normalization.py
│   │   │   ├── validation.py
│   │   │   ├── risk_engine.py
│   │   │   └── reporting.py
│   │   ├── repositories/
│   │   │   ├── batch_repository.py
│   │   │   ├── asset_repository.py
│   │   │   └── risk_repository.py
│   │   ├── db/
│   │   │   ├── session.py
│   │   │   └── init_db.py
│   │   └── tests/
│   │       ├── test_ingestion.py
│   │       ├── test_validation.py
│   │       ├── test_risk_engine.py
│   │       ├── test_api.py
│   │       └── test_database.py
│   └── data/                 # SQLite database; gitignored
│
└── frontend/
    ├── package.json
    ├── vite.config.ts
    └── src/
        ├── app/
        ├── components/
        ├── pages/
        ├── services/
        ├── hooks/
        ├── types/
        ├── utils/
        └── styles/
```

This is a suggested structure, not a reason to create empty files for
every item. Build modules as needed, but keep ingestion, validation,
scoring, persistence and API concerns separated.

------------------------------------------------------------------------

## 11. Testing and reliability requirements

Testing is mandatory. Do not consider the application complete merely
because the dashboard renders.

### Ingestion tests

-   Upload the supplied 1,200-row CSV.
-   Upload equivalent JSON.
-   Reject unsupported file types.
-   Reject oversized files.
-   Handle empty file.
-   Handle malformed CSV and JSON.
-   Handle missing required headers.
-   Handle UTF-8 BOM.
-   Handle blank rows.
-   Handle extra columns without crashing.

### Validation tests

Create small controlled test fixtures for: - Missing asset ID. - Missing
hostname. - Missing/invalid IP. - Invalid asset type. - Invalid
criticality. - Invalid severity. - Duplicate asset ID (verify every row
in group is blocked). - Duplicate IP (verify warning, not block). -
Missing owner (verify warning and still eligible). - Missing owner
email. - Invalid email. - Invalid date. - Negative or non-integer
vulnerability count. - Invalid Yes/No field.

### Risk engine tests

Test every mapping and boundary: -
Critical/High/Medium/Low/Informational/None severity. -
Critical/High/Medium/Low criticality. - Owner present and missing. -
Scores at or near 29.99/30, 59.99/60, 79.99/80. - Score never below 0 or
above 100. - Formula and weights match this specification exactly. -
Blocked rows never receive a risk score. - Warning-only rows can receive
a score.

### Integration tests

-   Upload -\> validate -\> analyze -\> fetch risk results.
-   Repeat analysis and verify no duplicate assessments.
-   Upload two batches and verify their records/results remain separate.
-   Verify pagination and filters.
-   Verify zero eligible records are handled gracefully.

### Data integrity checks

For the supplied clean AegisCorp CSV: - Exactly 1,200 rows should be
parsed. - The nine asset categories should match the distribution in
Section 2. - Asset IDs, hostnames and IP addresses should be unique. -
Do not hardcode expected risk counts; calculate them from the CSV and
formula. - If the file fails these checks, report the discrepancy rather
than silently changing it.

### Definition of done

The mini-project is complete only when: 1. The supplied CSV uploads
successfully. 2. All rows are accounted for. 3. Validation findings are
accurate and traceable to source row numbers. 4. Ownerless assets are
retained with warnings. 5. Duplicate asset-ID groups are blocked
consistently. 6. Risk scores match manual calculations. 7. The dashboard
displays API-backed data for the selected batch. 8. A second upload does
not overwrite the first. 9. Automated tests pass. 10. Setup instructions
work on a fresh local environment.

------------------------------------------------------------------------

## 12. Implementation sequence

Build in this order. Do not start by polishing the dashboard before the
backend rules are correct.

### Stage 1 --- Inspect and establish the data contract

-   Locate `aegiscorp_asset_inventory_1200.csv`.
-   Read its actual header and sample rows.
-   Verify row count, 24 columns, category distribution, unique
    IDs/hostnames/IPs.
-   Do not alter the supplied file.
-   Implement the schema and parsing tests.

### Stage 2 --- Backend ingestion and validation

-   Create FastAPI application.
-   Implement safe CSV/JSON upload.
-   Implement normalization and deterministic validation.
-   Persist import batches, asset rows and issues.
-   Test all validation rules.

### Stage 3 --- Risk engine

-   Implement the exact weighted formula.
-   Implement risk thresholds and explanation generator.
-   Persist results.
-   Test mappings, boundaries and blocked-record behaviour.

### Stage 4 --- API completion

-   Implement batch, asset, issue and risk endpoints.
-   Add pagination, sorting and filters.
-   Test API responses and error handling.

### Stage 5 --- Frontend

-   Build the application shell and sidebar.
-   Implement upload flow.
-   Build overview, inventory, data-quality, risk-analysis and
    import-history pages.
-   Integrate real API data.
-   Add loading/error/empty states and responsive layout.

### Stage 6 --- End-to-end verification

-   Upload the supplied clean dataset.
-   Create a separate corrupted copy for controlled testing; never
    corrupt the original.
-   Verify the validation results against known injected errors.
-   Verify risk scores manually for selected records.
-   Test a second upload and batch isolation.
-   Fix defects before adding visual polish.

------------------------------------------------------------------------

## 13. Security, privacy and operational safeguards

Even though this is a local academic prototype: - Treat uploaded files
as untrusted input. - Restrict file extensions and verify parsing rather
than trusting MIME type alone. - Enforce upload-size limits. - Use
parameterized ORM/database operations. - Avoid rendering untrusted
values as HTML. - Do not log full uploaded records or owner emails
unnecessarily. - Do not expose local filesystem paths. - Do not execute
macros, scripts, formulas or embedded content from uploads. - Keep the
database file and temporary uploads out of Git. - Bind the local
development server to localhost by default. - Do not send uploaded data
to external APIs. - Make clear that the dataset is fictional and local.

------------------------------------------------------------------------

## 14. Future scope --- do not implement now

Keep these as future enhancements only: - CVE/NVD vulnerability
enrichment. - CVSS and EPSS-based prioritization. - External
attack-surface intelligence. - Asset relationship mapping. - Historical
risk trends. - Authentication and role-based access. - Enterprise
integrations. - Advanced analytics.

The current mini-project must remain focused on inventory ingestion,
validation, explainable rule-based risk scoring, and dashboard
presentation.

------------------------------------------------------------------------

## 15. Instructions to Antigravity --- execution discipline

1.  First inspect the existing repository and the supplied CSV. Do not
    overwrite existing work without understanding it.
2.  Treat this specification as the source of truth for Phase 1.
3.  Treat `aegiscorp_asset_inventory_1200.csv` as the primary clean test
    dataset. The user will provide it at project start. Locate it in the
    workspace and use it for actual ingestion and end-to-end testing.
4.  Do not fabricate validation results, risk counts, test outcomes, or
    screenshots.
5.  Do not hardcode asset rows, dashboard metrics, risk distributions,
    or sample API responses as production data.
6.  Use the same validation and risk-engine functions for uploaded data
    and automated tests.
7.  Keep business rules in backend services, not duplicated in React.
8.  Use typed API schemas and handle errors explicitly.
9.  Build incrementally. After each stage, run tests and fix failures
    before moving on.
10. If a requirement is ambiguous or the supplied CSV differs from this
    specification, inspect the file and report the discrepancy. Do not
    silently guess or alter the data contract.
11. Do not add Phase 2 features or ATT&CKLens concepts.
12. At completion, provide:
    -   implemented feature summary;
    -   final folder structure;
    -   setup and run commands;
    -   test commands and actual test results;
    -   known limitations;
    -   any deviations from this specification.

**Final product standard:** SentinelOps should be a reliable,
understandable, locally runnable asset-inventory validation and
explainable risk-analysis application. Correctness, traceability and
reproducibility take priority over feature count or visual effects.
