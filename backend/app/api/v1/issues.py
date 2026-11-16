from typing import Optional, List
from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from pydantic import BaseModel
from app.db.session import get_db
from app.core.errors import BatchNotFoundException
from app.schemas.issue import ValidationIssueResponse
from app.repositories.batch_repository import BatchRepository
from app.repositories.issue_repository import IssueRepository

router = APIRouter(prefix="/batches/{batch_id}/issues", tags=["Issues"])

class PaginatedIssuesResponse(BaseModel):
    items: List[ValidationIssueResponse]
    total: int
    limit: int
    offset: int

@router.get("", response_model=PaginatedIssuesResponse)
def list_validation_issues(
    batch_id: str,
    limit: int = Query(50, ge=1, le=200),
    offset: int = Query(0, ge=0),
    severity: Optional[str] = Query(None, description="'error', 'warning', 'info'"),
    blocking: Optional[bool] = Query(None),
    issue_code: Optional[str] = Query(None),
    field_name: Optional[str] = Query(None),
    db: Session = Depends(get_db)
):
    """List validation issues detected in a batch with filtering and pagination."""
    batch_repo = BatchRepository(db)
    batch = batch_repo.get_by_id(batch_id)
    if not batch:
        raise BatchNotFoundException(batch_id)

    issue_repo = IssueRepository(db)
    items, total = issue_repo.list_by_batch(
        batch_id=batch_id,
        limit=limit,
        offset=offset,
        severity=severity,
        blocking=blocking,
        issue_code=issue_code,
        field_name=field_name,
    )

    return PaginatedIssuesResponse(
        items=[ValidationIssueResponse.model_validate(item) for item in items],
        total=total,
        limit=limit,
        offset=offset,
    )

