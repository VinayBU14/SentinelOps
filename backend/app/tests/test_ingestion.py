import json
import pytest
from app.services.ingestion import parse_uploaded_file, EXPECTED_COLUMNS
from app.core.errors import (
    FileTooLargeException,
    UnsupportedFileTypeException,
    InvalidFileStructureException,
)

def test_parse_valid_csv():
    headers = ",".join(EXPECTED_COLUMNS)
    row = "AST-001,host1,10.0.0.1,Server,Sub1,Linux,1.0,Alice,alice@example.com,IT,Production,Critical,High,5,Yes,Restricted,DC1,2023-01-01,2023-06-01,Active,Yes,Yes,AegisCorp,Manual"
    content = f"{headers}\n{row}\n".encode("utf-8")

    rows, file_type, blank_rows, sha256 = parse_uploaded_file(content, "test.csv")
    assert file_type == "csv"
    assert len(rows) == 1
    assert blank_rows == 0
    assert rows[0]["asset_id"] == "AST-001"
    assert rows[0]["source_row_number"] == 2
    assert len(sha256) == 64

def test_parse_csv_with_utf8_bom():
    headers = ",".join(EXPECTED_COLUMNS)
    row = "AST-001,host1,10.0.0.1,Server,Sub1,Linux,1.0,Alice,alice@example.com,IT,Production,Critical,High,5,Yes,Restricted,DC1,2023-01-01,2023-06-01,Active,Yes,Yes,AegisCorp,Manual"
    content = b"\xef\xbb\xbf" + f"{headers}\n{row}\n".encode("utf-8")

    rows, file_type, blank_rows, _ = parse_uploaded_file(content, "test_bom.csv")
    assert file_type == "csv"
    assert len(rows) == 1
    assert rows[0]["asset_id"] == "AST-001"

def test_parse_csv_blank_rows():
    headers = ",".join(EXPECTED_COLUMNS)
    row = "AST-001,host1,10.0.0.1,Server,Sub1,Linux,1.0,Alice,alice@example.com,IT,Production,Critical,High,5,Yes,Restricted,DC1,2023-01-01,2023-06-01,Active,Yes,Yes,AegisCorp,Manual"
    content = f"{headers}\n\n  \n{row}\n\n".encode("utf-8")

    rows, file_type, blank_rows, _ = parse_uploaded_file(content, "test_blanks.csv")
    assert len(rows) == 1
    assert blank_rows == 3

def test_parse_missing_headers():
    content = b"asset_id,hostname,ip_address\nAST-001,host1,10.0.0.1\n"
    with pytest.raises(InvalidFileStructureException) as exc_info:
        parse_uploaded_file(content, "incomplete.csv")
    assert "missing required inventory columns" in str(exc_info.value.detail).lower()

def test_parse_empty_csv():
    with pytest.raises(InvalidFileStructureException):
        parse_uploaded_file(b"", "empty.csv")

def test_parse_unsupported_extension():
    with pytest.raises(UnsupportedFileTypeException):
        parse_uploaded_file(b"data", "file.xlsx")

def test_parse_valid_json_array():
    data = [{col: f"val_{col}" for col in EXPECTED_COLUMNS}]
    content = json.dumps(data).encode("utf-8")

    rows, file_type, blank_rows, _ = parse_uploaded_file(content, "inventory.json")
    assert file_type == "json"
    assert len(rows) == 1
    assert rows[0]["asset_id"] == "val_asset_id"

def test_parse_valid_json_wrapped_object():
    data = {"assets": [{col: f"val_{col}" for col in EXPECTED_COLUMNS}]}
    content = json.dumps(data).encode("utf-8")

    rows, file_type, blank_rows, _ = parse_uploaded_file(content, "inventory_wrapped.json")
    assert file_type == "json"
    assert len(rows) == 1
    assert rows[0]["asset_id"] == "val_asset_id"

def test_parse_malformed_json():
    with pytest.raises(InvalidFileStructureException):
        parse_uploaded_file(b"{assets: [invalid_json", "broken.json")

