import os
from pathlib import Path
from app.services.ingestion import EXPECTED_COLUMNS

def test_api_health_check(client):
    res = client.get("/api/v1/health")
    assert res.status_code == 200
    assert res.json()["status"] == "ok"

def test_api_get_sample_dataset(client):
    res = client.get("/api/v1/sample-dataset")
    assert res.status_code == 200
    assert "aegiscorp_asset_inventory_1200.csv" in res.headers.get("content-disposition", "")
    assert len(res.content) > 1000

def test_api_upload_synthetic_csv(client):
    headers = ",".join(EXPECTED_COLUMNS)
    row = "AST-0001,srv1.corp,10.1.1.1,Server,Compute,Linux,1.0,Admin,admin@corp.com,IT,Production,High,Medium,2,No,Internal,DC1,2022-01-01,2023-01-01,Active,Yes,Yes,Corp,CMDB"
    csv_bytes = f"{headers}\n{row}\n".encode("utf-8")

    response = client.post(
        "/api/v1/uploads",
        files={"file": ("inventory.csv", csv_bytes, "text/csv")}
    )
    assert response.status_code == 200
    data = response.json()
    assert "batch_id" in data
    assert data["status"] == "validated"
    assert data["summary"]["total_rows"] == 1
    assert data["summary"]["valid_rows"] == 1
    assert data["summary"]["blocked_rows"] == 0

    batch_id = data["batch_id"]

    # Verify listing batch
    batches_res = client.get("/api/v1/batches")
    assert batches_res.status_code == 200
    batches = batches_res.json()
    assert any(b["id"] == batch_id for b in batches)

    # Verify assets endpoint
    assets_res = client.get(f"/api/v1/batches/{batch_id}/assets")
    assert assets_res.status_code == 200
    assets_data = assets_res.json()
    assert assets_data["total"] == 1
    assert assets_data["items"][0]["asset_id"] == "AST-0001"

def test_api_upload_aegiscorp_1200_csv(client):
    # Locate dataset
    csv_path = Path("datasets/aegiscorp_asset_inventory_1200.csv")
    if not csv_path.exists():
        csv_path = Path("aegiscorp_asset_inventory_1200.csv")

    assert csv_path.exists(), "Supplied AegisCorp CSV must exist in repository"

    with open(csv_path, "rb") as f:
        file_bytes = f.read()

    response = client.post(
        "/api/v1/uploads",
        files={"file": ("aegiscorp_asset_inventory_1200.csv", file_bytes, "text/csv")}
    )
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "validated"
    summary = data["summary"]
    # Check exact baseline metrics for the supplied clean file
    assert summary["total_rows"] == 1200
    assert summary["valid_rows"] == 1200
    assert summary["warning_rows"] == 0
    assert summary["blocked_rows"] == 0
    assert summary["error_count"] == 0
    assert summary["warning_count"] == 0
    assert summary["blank_rows"] == 0

    batch_id = data["batch_id"]

    # Verify pagination on 1200 assets
    page1 = client.get(f"/api/v1/batches/{batch_id}/assets?limit=50&offset=0").json()
    assert page1["total"] == 1200
    assert len(page1["items"]) == 50

    # Verify filtering by asset_type
    servers = client.get(f"/api/v1/batches/{batch_id}/assets?asset_type=Server").json()
    assert servers["total"] == 180

    workstations = client.get(f"/api/v1/batches/{batch_id}/assets?asset_type=Workstation").json()
    assert workstations["total"] == 400

    # Verify search
    search_res = client.get(f"/api/v1/batches/{batch_id}/assets?search={page1['items'][0]['asset_id']}").json()
    assert search_res["total"] >= 1

def test_api_batch_isolation(client):
    headers = ",".join(EXPECTED_COLUMNS)
    batch1_row = "AST-BATCH-1,srv1,10.0.0.1,Server,Compute,Linux,1.0,Admin,admin@corp.com,IT,Production,High,Medium,2,No,Internal,DC1,2022-01-01,2023-01-01,Active,Yes,Yes,Corp,CMDB"
    batch2_row = "AST-BATCH-2,srv2,10.0.0.2,Server,Compute,Linux,1.0,Admin,admin@corp.com,IT,Production,Low,Low,0,No,Internal,DC1,2022-01-01,2023-01-01,Active,Yes,Yes,Corp,CMDB"

    res1 = client.post("/api/v1/uploads", files={"file": ("b1.csv", f"{headers}\n{batch1_row}\n".encode(), "text/csv")}).json()
    res2 = client.post("/api/v1/uploads", files={"file": ("b2.csv", f"{headers}\n{batch2_row}\n".encode(), "text/csv")}).json()

    b1_id = res1["batch_id"]
    b2_id = res2["batch_id"]
    assert b1_id != b2_id

    b1_assets = client.get(f"/api/v1/batches/{b1_id}/assets").json()["items"]
    b2_assets = client.get(f"/api/v1/batches/{b2_id}/assets").json()["items"]

    assert len(b1_assets) == 1 and b1_assets[0]["asset_id"] == "AST-BATCH-1"
    assert len(b2_assets) == 1 and b2_assets[0]["asset_id"] == "AST-BATCH-2"

def test_api_corrupted_fixture_and_issues_endpoint(client):
    # Controlled corrupted fixture: duplicate asset ID, invalid IP, missing owner
    headers = ",".join(EXPECTED_COLUMNS)
    r1 = "AST-DUP,srv1,10.0.0.1,Server,Compute,Linux,1.0,,admin@corp.com,IT,Production,High,Medium,2,No,Internal,DC1,2022-01-01,2023-01-01,Active,Yes,Yes,Corp,CMDB"
    r2 = "AST-DUP,srv2,999.999.999.999,Server,Compute,Linux,1.0,Admin,admin@corp.com,IT,Production,High,Medium,2,No,Internal,DC1,2022-01-01,2023-01-01,Active,Yes,Yes,Corp,CMDB"
    r3 = "AST-VALID,srv3,10.0.0.3,Server,Compute,Linux,1.0,Admin,admin@corp.com,IT,Production,High,Medium,2,No,Internal,DC1,2022-01-01,2023-01-01,Active,Yes,Yes,Corp,CMDB"

    csv_data = f"{headers}\n{r1}\n{r2}\n{r3}\n".encode()
    res = client.post("/api/v1/uploads", files={"file": ("corrupted.csv", csv_data, "text/csv")})
    assert res.status_code == 200
    data = res.json()
    batch_id = data["batch_id"]

    # Both AST-DUP rows must be blocked!
    assert data["summary"]["blocked_rows"] == 2
    assert data["summary"]["valid_rows"] == 1
    assert data["summary"]["total_rows"] == 3

    # Query issues
    issues_res = client.get(f"/api/v1/batches/{batch_id}/issues")
    assert issues_res.status_code == 200
    issues = issues_res.json()["items"]
    codes = [i["issue_code"] for i in issues]
    assert "DUPLICATE_ASSET_ID" in codes
    assert "INVALID_IP" in codes
    assert "MISSING_OWNER" in codes

    # Filter issues by blocking=True
    blocking_res = client.get(f"/api/v1/batches/{batch_id}/issues?blocking=true")
    assert all(i["blocking"] is True for i in blocking_res.json()["items"])

