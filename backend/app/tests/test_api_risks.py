from pathlib import Path
from app.services.ingestion import EXPECTED_COLUMNS

def test_analyze_and_retrieve_risks(client):
    headers = ",".join(EXPECTED_COLUMNS)
    # Row 1: High vuln (75), Critical crit (100), Owner missing (100) -> 87.5 (Critical)
    r1 = "AST-0001,host1,10.0.0.1,Server,Sub,Linux,1.0,,admin@corp.com,IT,Production,Critical,High,5,Yes,Restricted,DC1,2023-01-01,2023-06-01,Active,Yes,Yes,Corp,CMDB"
    # Row 2: Low vuln (25), Low crit (25), Owner present (0) -> 12.5 + 7.5 + 0 = 20.0 (Low)
    r2 = "AST-0002,host2,10.0.0.2,Workstation,Sub,Windows,11,Bob,bob@corp.com,HR,Production,Low,Low,1,No,Internal,DC1,2023-01-01,2023-06-01,Active,Yes,Yes,Corp,CMDB"
    # Row 3: Blocked row (Missing IP) -> should NOT be scored
    r3 = "AST-0003,host3,,Server,Sub,Linux,1.0,Carol,carol@corp.com,IT,Production,Critical,Critical,2,No,Internal,DC1,2023-01-01,2023-06-01,Active,Yes,Yes,Corp,CMDB"

    csv_data = f"{headers}\n{r1}\n{r2}\n{r3}\n".encode()
    upload_res = client.post("/api/v1/uploads", files={"file": ("inventory.csv", csv_data, "text/csv")}).json()
    batch_id = upload_res["batch_id"]

    # 1. Run analysis
    analyze_res = client.post(f"/api/v1/batches/{batch_id}/analyze")
    assert analyze_res.status_code == 200
    data = analyze_res.json()
    assert data["status"] == "analyzed"
    assert data["summary"]["total_eligible"] == 2
    assert data["summary"]["scored_records"] == 2
    assert data["summary"]["critical_count"] == 1
    assert data["summary"]["low_count"] == 1

    # 2. Query ranked risks
    risks_res = client.get(f"/api/v1/batches/{batch_id}/risks")
    assert risks_res.status_code == 200
    risks_data = risks_res.json()
    assert risks_data["total"] == 2
    items = risks_data["items"]
    # Check default sort: highest risk first
    assert items[0]["asset"]["asset_id"] == "AST-0001"
    assert items[0]["risk_score"] == 87.5
    assert items[0]["risk_level"] == "Critical"
    assert items[1]["asset"]["asset_id"] == "AST-0002"
    assert items[1]["risk_score"] == 20.0
    assert items[1]["risk_level"] == "Low"

    # 3. Check detailed single asset breakdown
    record_id_1 = items[0]["asset_record_id"]
    detail_res = client.get(f"/api/v1/batches/{batch_id}/assets/{record_id_1}/risk")
    assert detail_res.status_code == 200
    detail = detail_res.json()
    assert detail["asset"]["asset_id"] == "AST-0001"
    assert detail["risk_assessment"]["risk_score"] == 87.5
    assert "Critical risk" in detail["risk_assessment"]["explanation"]

    # 4. Filter by risk_level=Low
    low_res = client.get(f"/api/v1/batches/{batch_id}/risks?risk_level=Low")
    assert low_res.status_code == 200
    assert low_res.json()["total"] == 1
    assert low_res.json()["items"][0]["asset"]["asset_id"] == "AST-0002"

    # 5. Idempotency check: re-running analyze does NOT duplicate scores
    reanalyze_res = client.post(f"/api/v1/batches/{batch_id}/analyze")
    assert reanalyze_res.status_code == 200
    risks_after = client.get(f"/api/v1/batches/{batch_id}/risks").json()
    assert risks_after["total"] == 2

def test_analyze_full_aegiscorp_1200_dataset(client):
    csv_path = Path("datasets/aegiscorp_asset_inventory_1200.csv")
    if not csv_path.exists():
        csv_path = Path("aegiscorp_asset_inventory_1200.csv")

    with open(csv_path, "rb") as f:
        file_bytes = f.read()

    upload_res = client.post("/api/v1/uploads", files={"file": ("aegiscorp_asset_inventory_1200.csv", file_bytes, "text/csv")}).json()
    batch_id = upload_res["batch_id"]

    analyze_res = client.post(f"/api/v1/batches/{batch_id}/analyze")
    assert analyze_res.status_code == 200
    summary = analyze_res.json()["summary"]

    # Check exact metrics verified earlier from CSV inspection
    assert summary["total_eligible"] == 1200
    assert summary["scored_records"] == 1200
    assert summary["medium_count"] == 637
    assert summary["low_count"] == 422
    assert summary["high_count"] == 135
    assert summary["critical_count"] == 6

    # Verify ranked risks default order: highest score first
    top_risks = client.get(f"/api/v1/batches/{batch_id}/risks?limit=10").json()
    assert top_risks["items"][0]["risk_score"] == 80.0
    assert top_risks["items"][0]["risk_level"] == "Critical"

    # Verify asset listing now has populated risk_score and risk_level
    assets_page = client.get(f"/api/v1/batches/{batch_id}/assets?limit=5").json()
    for a in assets_page["items"]:
        assert a["risk_score"] is not None
        assert a["risk_level"] is not None

