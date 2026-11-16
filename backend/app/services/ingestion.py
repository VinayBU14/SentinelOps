import csv
import hashlib
import io
import json
from typing import List, Dict, Any, Tuple
from app.core.config import settings
from app.core.errors import (
    FileTooLargeException,
    UnsupportedFileTypeException,
    InvalidFileStructureException,
)

EXPECTED_COLUMNS = [
    "asset_id",
    "hostname",
    "ip_address",
    "asset_type",
    "sub_category",
    "operating_system",
    "os_version",
    "owner_name",
    "owner_email",
    "department",
    "environment",
    "criticality",
    "vulnerability_severity",
    "vulnerability_count",
    "internet_facing",
    "data_classification",
    "location",
    "purchase_date",
    "last_updated",
    "lifecycle_status",
    "backup_enabled",
    "edr_enabled",
    "organization",
    "data_source",
]

def parse_uploaded_file(
    content_bytes: bytes,
    filename: str
) -> Tuple[List[Dict[str, Any]], str, int, str]:
    """
    Safely validate and parse uploaded CSV or JSON content.
    Returns:
        (parsed_rows, file_type, blank_rows_count, file_sha256)
    Raises appropriate SentinelOpsException on validation failure.
    """
    if len(content_bytes) > settings.MAX_UPLOAD_SIZE_BYTES:
        raise FileTooLargeException(settings.MAX_UPLOAD_SIZE_BYTES)

    if not content_bytes or len(content_bytes.strip()) == 0:
        raise InvalidFileStructureException("Uploaded file is empty.")

    file_sha256 = hashlib.sha256(content_bytes).hexdigest()
    lower_fn = filename.lower()

    if lower_fn.endswith(".csv"):
        file_type = "csv"
        rows, blank_rows = _parse_csv(content_bytes)
    elif lower_fn.endswith(".json"):
        file_type = "json"
        rows, blank_rows = _parse_json(content_bytes)
    else:
        raise UnsupportedFileTypeException(
            f"Unsupported file format for '{filename}'. SentinelOps accepts .csv and .json files."
        )

    return rows, file_type, blank_rows, file_sha256

def _parse_csv(content_bytes: bytes) -> Tuple[List[Dict[str, Any]], int]:
    # Decode using utf-8-sig to automatically handle UTF-8 BOM if present
    try:
        text = content_bytes.decode("utf-8-sig")
    except UnicodeDecodeError:
        try:
            text = content_bytes.decode("latin-1")
        except Exception as e:
            raise InvalidFileStructureException(f"Unable to decode CSV file content: {str(e)}")

    reader = csv.reader(io.StringIO(text))
    try:
        header_row = next(reader, None)
    except Exception as e:
        raise InvalidFileStructureException(f"Malformed CSV file: {str(e)}")

    if header_row is None:
        raise InvalidFileStructureException("CSV file contains no headers.")

    # Normalize header names (lowercase, trim)
    raw_headers = [h.strip() for h in header_row]
    lower_headers = [h.lower() for h in raw_headers]

    # Check for expected columns
    missing_columns = [col for col in EXPECTED_COLUMNS if col not in lower_headers]
    if missing_columns:
        raise InvalidFileStructureException(
            f"CSV is missing required inventory columns: {', '.join(missing_columns)}"
        )

    # Map column positions
    col_idx_map = {col: lower_headers.index(col) for col in EXPECTED_COLUMNS}

    parsed_rows: List[Dict[str, Any]] = []
    blank_rows = 0
    row_num = 1  # header is row 1, first data row is 2

    for raw_row in reader:
        row_num += 1
        # Check if entire row is empty or whitespace
        if not raw_row or all(c.strip() == "" for c in raw_row):
            blank_rows += 1
            continue

        row_dict: Dict[str, Any] = {"source_row_number": row_num}
        for col, idx in col_idx_map.items():
            val = raw_row[idx] if idx < len(raw_row) else ""
            row_dict[col] = val

        parsed_rows.append(row_dict)

    if not parsed_rows and blank_rows == 0:
        raise InvalidFileStructureException("CSV file contains header only with no data rows.")

    return parsed_rows, blank_rows

def _parse_json(content_bytes: bytes) -> Tuple[List[Dict[str, Any]], int]:
    try:
        text = content_bytes.decode("utf-8-sig")
        data = json.loads(text)
    except json.JSONDecodeError as e:
        raise InvalidFileStructureException(f"Malformed JSON: {str(e)}")
    except Exception as e:
        raise InvalidFileStructureException(f"Unable to read JSON: {str(e)}")

    raw_list = []
    if isinstance(data, list):
        raw_list = data
    elif isinstance(data, dict):
        if "assets" in data and isinstance(data["assets"], list):
            raw_list = data["assets"]
        else:
            raise InvalidFileStructureException(
                "JSON root object must be a list of assets or an object with an 'assets' array."
            )
    else:
        raise InvalidFileStructureException(
            "JSON structure must be an array of asset records or an object containing an 'assets' array."
        )

    parsed_rows: List[Dict[str, Any]] = []
    blank_rows = 0

    for idx, item in enumerate(raw_list, start=1):
        if not isinstance(item, dict) or not item:
            blank_rows += 1
            continue

        row_dict: Dict[str, Any] = {"source_row_number": idx}
        # Case-insensitive key lookup for JSON items
        item_lower = {k.lower().strip(): v for k, v in item.items()}

        for col in EXPECTED_COLUMNS:
            val = item_lower.get(col, "")
            row_dict[col] = "" if val is None else str(val)

        parsed_rows.append(row_dict)

    if not parsed_rows and blank_rows == 0:
        raise InvalidFileStructureException("JSON file contains no asset records.")

    return parsed_rows, blank_rows

