from fastapi import APIRouter, Depends, UploadFile, File
from sqlalchemy.orm import Session
from app.db.session import get_db
from app.schemas.batch import UploadResponse, BatchSummary
from app.services.batch_service import process_upload

router = APIRouter(prefix="/uploads", tags=["Uploads"])

@router.post("", response_model=UploadResponse)
async def upload_asset_file(
    file: UploadFile = File(...),
    db: Session = Depends(get_db)
):
    """
    Upload CSV or JSON asset inventory. Validates file, runs data quality checks,
    creates a new import batch, and persists all assets and validation issues.
    """
    content_bytes = await file.read()
    filename = file.filename or "uploaded_inventory"

    batch = process_upload(db=db, content_bytes=content_bytes, filename=filename)

    summary = BatchSummary(
        total_rows=batch.total_rows,
        valid_rows=batch.valid_rows,
        warning_rows=batch.warning_rows,
        blocked_rows=batch.blocked_rows,
        error_count=batch.error_count,
        warning_count=batch.warning_count,
        blank_rows=batch.blank_rows,
    )

    return UploadResponse(
        batch_id=batch.id,
        status=batch.status,
        filename=batch.original_filename,
        summary=summary,
        message="File uploaded and validated successfully."
    )

