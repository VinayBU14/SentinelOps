from app.services.validation import validate_dataset

def _make_base_row(row_num=2, **overrides):
    row = {
        "source_row_number": row_num,
        "asset_id": f"AST-{row_num:04d}",
        "hostname": f"host-{row_num}.corp.local",
        "ip_address": f"10.0.{row_num // 256}.{row_num % 256 + 1}",
        "asset_type": "Server",
        "sub_category": "Compute",
        "operating_system": "Ubuntu",
        "os_version": "22.04",
        "owner_name": "Alice Smith",
        "owner_email": "alice@aegiscorp.com",
        "department": "Engineering",
        "environment": "Production",
        "criticality": "High",
        "vulnerability_severity": "Medium",
        "vulnerability_count": "3",
        "internet_facing": "No",
        "data_classification": "Confidential",
        "location": "US-East",
        "purchase_date": "2023-01-15",
        "last_updated": "2023-06-20",
        "lifecycle_status": "Active",
        "backup_enabled": "Yes",
        "edr_enabled": "Yes",
        "organization": "AegisCorp",
        "data_source": "CMDB",
    }
    row.update(overrides)
    return row

def test_valid_row():
    rows = [_make_base_row(2)]
    res = validate_dataset(rows)
    assert res.total_rows == 1
    assert res.valid_rows == 1
    assert res.warning_rows == 0
    assert res.blocked_rows == 0
    assert res.error_count == 0
    assert res.warning_count == 0

def test_missing_asset_id():
    rows = [_make_base_row(2, asset_id="")]
    res = validate_dataset(rows)
    assert res.blocked_rows == 1
    codes = [i.issue_code for i in res.all_issues]
    assert "MISSING_ASSET_ID" in codes
    assert any(i.blocking for i in res.all_issues)

def test_duplicate_asset_id_blocks_all_in_group():
    rows = [
        _make_base_row(2, asset_id="AST-DUP-1"),
        _make_base_row(3, asset_id="ast-dup-1"),  # Case-insensitive duplicate
        _make_base_row(4, asset_id="AST-UNIQUE"),
    ]
    res = validate_dataset(rows)
    # Both row 2 and row 3 must be blocked!
    assert res.row_statuses[2] == "blocked"
    assert res.row_statuses[3] == "blocked"
    assert res.row_statuses[4] == "valid"
    assert res.blocked_rows == 2
    assert res.valid_rows == 1
    dup_issues = [i for i in res.all_issues if i.issue_code == "DUPLICATE_ASSET_ID"]
    assert len(dup_issues) == 2

def test_duplicate_ip_warning_does_not_block():
    rows = [
        _make_base_row(2, ip_address="192.168.1.100"),
        _make_base_row(3, ip_address="192.168.1.100"),
    ]
    res = validate_dataset(rows)
    # Both rows get warning, but NOT blocked
    assert res.row_statuses[2] == "warning"
    assert res.row_statuses[3] == "warning"
    assert res.blocked_rows == 0
    assert res.warning_rows == 2
    ip_warnings = [i for i in res.all_issues if i.issue_code == "DUPLICATE_IP"]
    assert len(ip_warnings) == 2
    assert all(not i.blocking for i in ip_warnings)

def test_invalid_ip_blocks():
    rows = [_make_base_row(2, ip_address="999.999.999.999")]
    res = validate_dataset(rows)
    assert res.blocked_rows == 1
    codes = [i.issue_code for i in res.all_issues]
    assert "INVALID_IP" in codes

def test_missing_and_invalid_asset_type():
    res1 = validate_dataset([_make_base_row(2, asset_type="")])
    assert "MISSING_ASSET_TYPE" in [i.issue_code for i in res1.all_issues]
    assert res1.blocked_rows == 1

    res2 = validate_dataset([_make_base_row(2, asset_type="Toaster")])
    assert "INVALID_ASSET_TYPE" in [i.issue_code for i in res2.all_issues]
    assert res2.blocked_rows == 1

def test_missing_and_invalid_criticality():
    res1 = validate_dataset([_make_base_row(2, criticality="")])
    assert "MISSING_CRITICALITY" in [i.issue_code for i in res1.all_issues]
    assert res1.blocked_rows == 1

    res2 = validate_dataset([_make_base_row(2, criticality="SuperUrgent")])
    assert "INVALID_CRITICALITY" in [i.issue_code for i in res2.all_issues]
    assert res2.blocked_rows == 1

def test_missing_and_invalid_vulnerability_severity():
    res1 = validate_dataset([_make_base_row(2, vulnerability_severity="")])
    assert "MISSING_SEVERITY" in [i.issue_code for i in res1.all_issues]
    assert res1.blocked_rows == 1

    res2 = validate_dataset([_make_base_row(2, vulnerability_severity="Catastrophic")])
    assert "INVALID_SEVERITY" in [i.issue_code for i in res2.all_issues]
    assert res2.blocked_rows == 1

def test_missing_owner_is_warning_and_eligible():
    rows = [_make_base_row(2, owner_name="", owner_email="")]
    res = validate_dataset(rows)
    assert res.blocked_rows == 0
    assert res.warning_rows == 1
    codes = [i.issue_code for i in res.all_issues]
    assert "MISSING_OWNER" in codes
    assert not any(i.blocking for i in res.all_issues)

def test_missing_owner_email_when_owner_present():
    rows = [_make_base_row(2, owner_name="Bob Jones", owner_email="")]
    res = validate_dataset(rows)
    assert res.blocked_rows == 0
    assert res.warning_rows == 1
    codes = [i.issue_code for i in res.all_issues]
    assert "MISSING_OWNER_EMAIL" in codes

def test_invalid_owner_email():
    rows = [_make_base_row(2, owner_name="Bob Jones", owner_email="not-an-email")]
    res = validate_dataset(rows)
    assert res.blocked_rows == 0
    assert res.warning_rows == 1
    codes = [i.issue_code for i in res.all_issues]
    assert "INVALID_OWNER_EMAIL" in codes

def test_invalid_date():
    rows = [_make_base_row(2, purchase_date="2023/13/45")]
    res = validate_dataset(rows)
    assert res.blocked_rows == 0
    assert res.warning_rows == 1
    codes = [i.issue_code for i in res.all_issues]
    assert "INVALID_DATE" in codes

def test_invalid_vulnerability_count_blocks():
    # Negative count
    res1 = validate_dataset([_make_base_row(2, vulnerability_count="-1")])
    assert res1.blocked_rows == 1
    assert "INVALID_VULNERABILITY_COUNT" in [i.issue_code for i in res1.all_issues]

    # Non-integer
    res2 = validate_dataset([_make_base_row(2, vulnerability_count="three")])
    assert res2.blocked_rows == 1
    assert "INVALID_VULNERABILITY_COUNT" in [i.issue_code for i in res2.all_issues]

def test_invalid_boolean_values():
    rows = [_make_base_row(2, internet_facing="Maybe")]
    res = validate_dataset(rows)
    assert res.blocked_rows == 0
    assert res.warning_rows == 1
    codes = [i.issue_code for i in res.all_issues]
    assert "INVALID_BOOLEAN_VALUE" in codes

