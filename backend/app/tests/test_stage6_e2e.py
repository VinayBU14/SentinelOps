import csv
import io
from pathlib import Path
from app.services.ingestion import EXPECTED_COLUMNS

def test_stage6_full_e2e_verification(client):
    # =========================================================================
    # PART 1: INGEST CLEAN AEGISCORP 1,200 RECORD DATASET (BATCH A)
    # =========================================================================
    csv_path = Path("datasets/aegiscorp_asset_inventory_1200.csv")
    if not csv_path.exists():
        csv_path = Path("aegiscorp_asset_inventory_1200.csv")

    with open(csv_path, "rb") as f:
        clean_csv_bytes = f.read()

    res_clean = client.post(
        "/api/v1/uploads",
        files={"file": ("aegiscorp_asset_inventory_1200.csv", clean_csv_bytes, "text/csv")}
    )
    assert res_clean.status_code == 200
    clean_batch = res_clean.json()
    batch_a_id = clean_batch["batch_id"]

    assert clean_batch["summary"]["total_rows"] == 1200
    assert clean_batch["summary"]["valid_rows"] == 1200
    assert clean_batch["summary"]["warning_rows"] == 0
    assert clean_batch["summary"]["blocked_rows"] == 0
    assert clean_batch["summary"]["error_count"] == 0
    assert clean_batch["summary"]["warning_count"] == 0

    # Analyze Batch A
    res_analyze_a = client.post(f"/api/v1/batches/{batch_a_id}/analyze")
    assert res_analyze_a.status_code == 200
    a_summary = res_analyze_a.json()["summary"]
    assert a_summary["total_eligible"] == 1200
    assert a_summary["scored_records"] == 1200
    assert a_summary["critical_count"] == 6
    assert a_summary["high_count"] == 135
    assert a_summary["medium_count"] == 637
    assert a_summary["low_count"] == 422

    # Spot check manual calculations on Batch A:
    # 1. Critical risk asset: Critical vuln (100) * 0.5 + Critical crit (100) * 0.3 + Owner present (0) * 0.2 = 50 + 30 + 0 = 80.0
    crit_risks = client.get(f"/api/v1/batches/{batch_a_id}/risks?risk_level=Critical").json()
    assert crit_risks["total"] == 6
    for item in crit_risks["items"]:
        assert item["risk_score"] == 80.0
        assert item["risk_level"] == "Critical"
        assert item["vulnerability_score"] == 100.0
        assert item["criticality_score"] == 100.0
        assert item["ownership_score"] == 0.0

    # 2. Low risk asset spot check: None vuln (0) * 0.5 + Low crit (25) * 0.3 + Owner (0) = 7.5
    low_risks = client.get(f"/api/v1/batches/{batch_a_id}/risks?risk_level=Low&limit=5").json()
    assert low_risks["total"] == 422
    # Verify score formula on low risk assets
    for item in low_risks["items"]:
        expected_score = round(0.50 * item["vulnerability_score"] + 0.30 * item["criticality_score"] + 0.20 * item["ownership_score"], 2)
        assert item["risk_score"] == expected_score

    # =========================================================================
    # PART 2: CONTROLLED CORRUPTED DATASET WITH KNOWN INJECTED DEFECTS (BATCH B)
    # =========================================================================
    corrupted_rows = [
        # 1. Clean reference row -> Valid (eligible)
        {
            "asset_id": "TEST-CLEAN-01",
            "hostname": "clean01.corp",
            "ip_address": "10.50.1.1",
            "asset_type": "Server",
            "sub_category": "Compute",
            "operating_system": "Linux",
            "os_version": "22.04",
            "owner_name": "Alice Admin",
            "owner_email": "alice@corp.com",
            "department": "Security",
            "environment": "Production",
            "criticality": "Critical",
            "vulnerability_severity": "High",
            "vulnerability_count": "2",
            "internet_facing": "Yes",
            "data_classification": "Restricted",
            "location": "US-East",
            "purchase_date": "2023-01-01",
            "last_updated": "2023-06-01",
            "lifecycle_status": "Active",
            "backup_enabled": "Yes",
            "edr_enabled": "Yes",
            "organization": "AegisCorp",
            "data_source": "CMDB",
        },
        # 2. Missing asset_id -> Blocking error (MISSING_ASSET_ID)
        {
            "asset_id": "",
            "hostname": "missing-id.corp",
            "ip_address": "10.50.1.2",
            "asset_type": "Server",
            "criticality": "High",
            "vulnerability_severity": "High",
            "owner_name": "Bob",
        },
        # 3. Duplicate asset ID group member 1 -> Blocking error (DUPLICATE_ASSET_ID)
        {
            "asset_id": "TEST-DUP-ID",
            "hostname": "dup1.corp",
            "ip_address": "10.50.1.3",
            "asset_type": "Workstation",
            "criticality": "Medium",
            "vulnerability_severity": "Medium",
            "owner_name": "Carol",
        },
        # 4. Duplicate asset ID group member 2 -> Blocking error (DUPLICATE_ASSET_ID)
        {
            "asset_id": "test-dup-id",  # Case-insensitive duplicate
            "hostname": "dup2.corp",
            "ip_address": "10.50.1.4",
            "asset_type": "Workstation",
            "criticality": "Medium",
            "vulnerability_severity": "Medium",
            "owner_name": "Dave",
        },
        # 5. Missing hostname -> Blocking error (MISSING_HOSTNAME)
        {
            "asset_id": "TEST-NO-HOST",
            "hostname": "",
            "ip_address": "10.50.1.5",
            "asset_type": "Database",
            "criticality": "High",
            "vulnerability_severity": "High",
            "owner_name": "Eve",
        },
        # 6. Missing IP -> Blocking error (MISSING_IP)
        {
            "asset_id": "TEST-NO-IP",
            "hostname": "no-ip.corp",
            "ip_address": "",
            "asset_type": "Database",
            "criticality": "High",
            "vulnerability_severity": "High",
            "owner_name": "Frank",
        },
        # 7. Invalid IP -> Blocking error (INVALID_IP)
        {
            "asset_id": "TEST-BAD-IP",
            "hostname": "bad-ip.corp",
            "ip_address": "300.500.700.900",
            "asset_type": "Server",
            "criticality": "Low",
            "vulnerability_severity": "Low",
            "owner_name": "Grace",
        },
        # 8. Duplicate IP group member 1 -> Warning (DUPLICATE_IP, Non-blocking, Eligible)
        {
            "asset_id": "TEST-SHARED-IP-1",
            "hostname": "shared1.corp",
            "ip_address": "10.50.1.100",
            "asset_type": "Application",
            "criticality": "High",
            "vulnerability_severity": "Low",
            "owner_name": "Heidi",
        },
        # 9. Duplicate IP group member 2 -> Warning (DUPLICATE_IP, Non-blocking, Eligible)
        {
            "asset_id": "TEST-SHARED-IP-2",
            "hostname": "shared2.corp",
            "ip_address": "10.50.1.100",
            "asset_type": "Application",
            "criticality": "High",
            "vulnerability_severity": "Low",
            "owner_name": "Ivan",
        },
        # 10. Invalid asset type -> Blocking error (INVALID_ASSET_TYPE)
        {
            "asset_id": "TEST-BAD-TYPE",
            "hostname": "bad-type.corp",
            "ip_address": "10.50.1.10",
            "asset_type": "SuperComputer",
            "criticality": "Medium",
            "vulnerability_severity": "Medium",
            "owner_name": "Judy",
        },
        # 11. Invalid criticality -> Blocking error (INVALID_CRITICALITY)
        {
            "asset_id": "TEST-BAD-CRIT",
            "hostname": "bad-crit.corp",
            "ip_address": "10.50.1.11",
            "asset_type": "Server",
            "criticality": "Urgent",
            "vulnerability_severity": "Medium",
            "owner_name": "Kevin",
        },
        # 12. Invalid vulnerability severity -> Blocking error (INVALID_SEVERITY)
        {
            "asset_id": "TEST-BAD-SEV",
            "hostname": "bad-sev.corp",
            "ip_address": "10.50.1.12",
            "asset_type": "Server",
            "criticality": "Medium",
            "vulnerability_severity": "Extreme",
            "owner_name": "Laura",
        },
        # 13. Negative vulnerability count -> Blocking error (INVALID_VULNERABILITY_COUNT)
        {
            "asset_id": "TEST-NEG-COUNT",
            "hostname": "neg-count.corp",
            "ip_address": "10.50.1.13",
            "asset_type": "Server",
            "criticality": "Medium",
            "vulnerability_severity": "Medium",
            "vulnerability_count": "-5",
            "owner_name": "Mallory",
        },
        # 14. Missing owner name -> Warning (MISSING_OWNER, Non-blocking, Eligible, +20 penalty)
        {
            "asset_id": "TEST-OWNERLESS",
            "hostname": "ownerless.corp",
            "ip_address": "10.50.1.14",
            "asset_type": "Server",
            "criticality": "Critical",          # 100 * 0.30 = 30
            "vulnerability_severity": "High",   # 75 * 0.50 = 37.5
            "owner_name": "",                   # Missing -> 100 * 0.20 = 20.0
            # Total = 37.5 + 30 + 20 = 87.5 (Critical)
        },
        # 15. Owner present, missing owner email -> Warning (MISSING_OWNER_EMAIL, Non-blocking, Eligible)
        {
            "asset_id": "TEST-NO-EMAIL",
            "hostname": "no-email.corp",
            "ip_address": "10.50.1.15",
            "asset_type": "Workstation",
            "criticality": "Low",
            "vulnerability_severity": "Low",
            "owner_name": "Niaj",
            "owner_email": "",
        },
        # 16. Owner present, invalid email -> Warning (INVALID_OWNER_EMAIL, Non-blocking, Eligible)
        {
            "asset_id": "TEST-BAD-EMAIL",
            "hostname": "bad-email.corp",
            "ip_address": "10.50.1.16",
            "asset_type": "Workstation",
            "criticality": "Low",
            "vulnerability_severity": "Low",
            "owner_name": "Oscar",
            "owner_email": "not-a-valid-email",
        },
        # 17. Invalid date -> Warning (INVALID_DATE, Non-blocking, Eligible)
        {
            "asset_id": "TEST-BAD-DATE",
            "hostname": "bad-date.corp",
            "ip_address": "10.50.1.17",
            "asset_type": "Workstation",
            "criticality": "Low",
            "vulnerability_severity": "Low",
            "owner_name": "Peggy",
            "purchase_date": "2024-99-99",
        },
        # 18. Invalid boolean value -> Warning (INVALID_BOOLEAN_VALUE, Non-blocking, Eligible)
        {
            "asset_id": "TEST-BAD-BOOL",
            "hostname": "bad-bool.corp",
            "ip_address": "10.50.1.18",
            "asset_type": "Workstation",
            "criticality": "Low",
            "vulnerability_severity": "Low",
            "owner_name": "Quinn",
            "internet_facing": "Maybe",
        },
    ]

    # Convert to CSV string with 2 blank lines to test skipped blanks
    output = io.StringIO()
    writer = csv.DictWriter(output, fieldnames=EXPECTED_COLUMNS)
    writer.writeheader()
    output.write("\n")  # Blank row 1
    for r in corrupted_rows:
        row_dict = {col: r.get(col, "") for col in EXPECTED_COLUMNS}
        writer.writerow(row_dict)
    output.write("\n")  # Blank row 2

    corrupted_csv_bytes = output.getvalue().encode("utf-8")

    res_corrupted = client.post(
        "/api/v1/uploads",
        files={"file": ("corrupted_test_fixture.csv", corrupted_csv_bytes, "text/csv")}
    )
    assert res_corrupted.status_code == 200
    corrupted_batch = res_corrupted.json()
    batch_b_id = corrupted_batch["batch_id"]

    # Verify blank rows skipped
    assert corrupted_batch["summary"]["blank_rows"] == 2
    assert corrupted_batch["summary"]["total_rows"] == len(corrupted_rows)

    # Count expected blocked vs warning vs valid:
    # Blocked rows:
    # Row 2 (missing id), Row 3 (dup id 1), Row 4 (dup id 2), Row 5 (no host),
    # Row 6 (no ip), Row 7 (bad ip), Row 10 (bad type), Row 11 (bad crit),
    # Row 12 (bad sev), Row 13 (neg count) = 10 blocked rows!
    assert corrupted_batch["summary"]["blocked_rows"] == 10

    # Warning rows:
    # Row 8 (shared ip 1), Row 9 (shared ip 2), Row 14 (missing owner),
    # Row 15 (no email), Row 16 (bad email), Row 17 (bad date), Row 18 (bad bool) = 7 warning rows!
    assert corrupted_batch["summary"]["warning_rows"] == 7

    # Valid rows:
    # Row 1 (clean) = 1 valid row!
    assert corrupted_batch["summary"]["valid_rows"] == 1

    # Eligible for scoring = valid_rows + warning_rows = 1 + 7 = 8 eligible rows!
    # Run analysis on Batch B
    res_analyze_b = client.post(f"/api/v1/batches/{batch_b_id}/analyze")
    assert res_analyze_b.status_code == 200
    b_summary = res_analyze_b.json()["summary"]
    assert b_summary["total_eligible"] == 8
    assert b_summary["scored_records"] == 8

    # Verify manual score for ownerless asset (Row 14: TEST-OWNERLESS):
    # Vuln: High (75 * 0.5 = 37.5) + Crit: Critical (100 * 0.3 = 30) + Owner missing (100 * 0.2 = 20) = 87.5 (Critical)
    ownerless_risk = client.get(f"/api/v1/batches/{batch_b_id}/risks?search=TEST-OWNERLESS").json()
    assert ownerless_risk["total"] == 1
    scored_ownerless = ownerless_risk["items"][0]
    assert scored_ownerless["risk_score"] == 87.5
    assert scored_ownerless["risk_level"] == "Critical"
    assert scored_ownerless["ownership_score"] == 100.0
    assert "no assigned owner" in scored_ownerless["explanation"]

    # Verify that NONE of the 10 blocked records received a risk score:
    blocked_assets = client.get(f"/api/v1/batches/{batch_b_id}/assets?validation_status=blocked").json()
    assert blocked_assets["total"] == 10
    for blocked_asset in blocked_assets["items"]:
        assert blocked_asset["risk_score"] is None
        assert blocked_asset["risk_level"] is None

    # =========================================================================
    # PART 3: BATCH ISOLATION VERIFICATION
    # =========================================================================
    # Batch A must remain strictly untouched and isolated!
    batch_a_after = client.get(f"/api/v1/batches/{batch_a_id}").json()
    assert batch_a_after["summary"]["total_rows"] == 1200
    assert batch_a_after["summary"]["valid_rows"] == 1200
    assert batch_a_after["summary"]["blocked_rows"] == 0
    assert batch_a_after["summary"]["error_count"] == 0

    batch_a_risks_after = client.get(f"/api/v1/batches/{batch_a_id}/risks").json()
    assert batch_a_risks_after["total"] == 1200

