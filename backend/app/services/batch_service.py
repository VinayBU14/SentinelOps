from sqlalchemy.orm import Session
from app.models.batch import ImportBatch
from app.models.asset import Asset
from app.models.issue import ValidationIssue
from app.services.ingestion import parse_uploaded_file
from app.services.validation import validate_dataset
from app.services.normalization import clean_str

def process_upload(
    db: Session,
    content_bytes: bytes,
    filename: str
) -> ImportBatch:
    """
    Ingest, validate, and persist a new asset batch.
    Creates records in import_batches, assets, and validation_issues.
    """
    # 1. Parse content
    rows, file_type, blank_rows, file_sha256 = parse_uploaded_file(content_bytes, filename)

    # 2. Run deterministic validation engine
    validation_res = validate_dataset(rows, blank_rows_count=blank_rows)

    # 3. Create import batch record
    batch = ImportBatch(
        original_filename=filename,
        file_type=file_type,
        status="validated",
        total_rows=validation_res.total_rows,
        valid_rows=validation_res.valid_rows,
        warning_rows=validation_res.warning_rows,
        blocked_rows=validation_res.blocked_rows,
        error_count=validation_res.error_count,
        warning_count=validation_res.warning_count,
        blank_rows=validation_res.blank_rows,
        file_sha256=file_sha256,
    )
    db.add(batch)
    db.flush()  # Flush to generate batch.id

    # 4. Create and persist asset records
    row_num_to_asset_id_map = {}
    asset_entities = []

    for row in rows:
        row_num = row.get("source_row_number", 0)
        status = validation_res.row_statuses.get(row_num, "valid")

        # Parse vuln_count as int if valid, else None
        raw_vc = clean_str(row.get("vulnerability_count"))
        vc_int = int(raw_vc) if raw_vc.isdigit() else None

        asset = Asset(
            batch_id=batch.id,
            source_row_number=row_num,
            asset_id=clean_str(row.get("asset_id")) or None,
            hostname=clean_str(row.get("hostname")) or None,
            ip_address=clean_str(row.get("ip_address")) or None,
            asset_type=clean_str(row.get("asset_type")) or None,
            sub_category=clean_str(row.get("sub_category")) or None,
            operating_system=clean_str(row.get("operating_system")) or None,
            os_version=clean_str(row.get("os_version")) or None,
            owner_name=clean_str(row.get("owner_name")) or None,
            owner_email=clean_str(row.get("owner_email")) or None,
            department=clean_str(row.get("department")) or None,
            environment=clean_str(row.get("environment")) or None,
            criticality=clean_str(row.get("criticality")) or None,
            vulnerability_severity=clean_str(row.get("vulnerability_severity")) or None,
            vulnerability_count=vc_int,
            internet_facing=clean_str(row.get("internet_facing")) or None,
            data_classification=clean_str(row.get("data_classification")) or None,
            location=clean_str(row.get("location")) or None,
            purchase_date=clean_str(row.get("purchase_date")) or None,
            last_updated=clean_str(row.get("last_updated")) or None,
            lifecycle_status=clean_str(row.get("lifecycle_status")) or None,
            backup_enabled=clean_str(row.get("backup_enabled")) or None,
            edr_enabled=clean_str(row.get("edr_enabled")) or None,
            organization=clean_str(row.get("organization")) or None,
            data_source=clean_str(row.get("data_source")) or None,
            validation_status=status,
        )
        asset_entities.append(asset)

    db.add_all(asset_entities)
    db.flush()  # Generates asset.id for all rows

    for asset in asset_entities:
        row_num_to_asset_id_map[asset.source_row_number] = asset.id

    # 5. Create validation issue entities linking to asset records
    issue_entities = []
    for issue_dto in validation_res.all_issues:
        asset_db_id = row_num_to_asset_id_map.get(issue_dto.row_number)
        issue_model = ValidationIssue(
            batch_id=batch.id,
            asset_record_id=asset_db_id,
            row_number=issue_dto.row_number,
            asset_id=issue_dto.asset_id,
            issue_code=issue_dto.issue_code,
            severity=issue_dto.severity,
            blocking=issue_dto.blocking,
            field_name=issue_dto.field_name,
            observed_value=issue_dto.observed_value,
            message=issue_dto.message,
            suggested_action=issue_dto.suggested_action,
        )
        issue_entities.append(issue_model)

    if issue_entities:
        db.add_all(issue_entities)

    db.commit()
    db.refresh(batch)
    return batch

