from typing import List
from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from app.db.session import get_db
from app.core.errors import BatchNotFoundException
from app.schemas.batch import BatchResponse, BatchSummary
from app.repositories.batch_repository import BatchRepository

router = APIRouter(prefix="/batches", tags=["Batches"])

def _map_batch_to_response(b) -> BatchResponse:
    return BatchResponse(
        id=b.id,
        original_filename=b.original_filename,
        file_type=b.file_type,
        uploaded_at=b.uploaded_at,
        status=b.status,
        summary=BatchSummary(
            total_rows=b.total_rows,
            valid_rows=b.valid_rows,
            warning_rows=b.warning_rows,
            blocked_rows=b.blocked_rows,
            error_count=b.error_count,
            warning_count=b.warning_count,
            blank_rows=b.blank_rows,
        ),
        file_sha256=b.file_sha256,
    )

@router.get("", response_model=List[BatchResponse])
def list_batches(
    limit: int = Query(50, ge=1, le=100),
    offset: int = Query(0, ge=0),
    db: Session = Depends(get_db)
):
    """List historical import batches ordered newest first."""
    repo = BatchRepository(db)
    batches = repo.list_all(limit=limit, offset=offset)
    return [_map_batch_to_response(b) for b in batches]

@router.get("/{batch_id}", response_model=BatchResponse)
def get_batch(
    batch_id: str,
    db: Session = Depends(get_db)
):
    """Retrieve details and validation summary for a specific batch."""
    repo = BatchRepository(db)
    batch = repo.get_by_id(batch_id)
    if not batch:
        raise BatchNotFoundException(batch_id)
    return _map_batch_to_response(batch)

