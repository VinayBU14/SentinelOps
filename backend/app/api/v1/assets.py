from typing import Optional, List
from fastapi import APIRouter, Depends, Query, HTTPException, status
from sqlalchemy.orm import Session
from pydantic import BaseModel
from app.db.session import get_db
from app.core.errors import BatchNotFoundException
from app.schemas.asset import AssetResponse
from app.repositories.batch_repository import BatchRepository
from app.repositories.asset_repository import AssetRepository

router = APIRouter(prefix="/batches/{batch_id}/assets", tags=["Assets"])

class PaginatedAssetsResponse(BaseModel):
    items: List[AssetResponse]
    total: int
    limit: int
    offset: int

@router.get("", response_model=PaginatedAssetsResponse)
def list_assets(
    batch_id: str,
    limit: int = Query(50, ge=1, le=200),
    offset: int = Query(0, ge=0),
    search: Optional[str] = Query(None, description="Search asset_id, hostname, ip"),
    asset_type: Optional[str] = Query(None),
    department: Optional[str] = Query(None),
    criticality: Optional[str] = Query(None),
    vulnerability_severity: Optional[str] = Query(None),
    validation_status: Optional[str] = Query(None, description="'valid', 'warning', 'blocked'"),
    owner_missing: Optional[bool] = Query(None, description="True for ownerless assets"),
    risk_level: Optional[str] = Query(None, description="'Critical', 'High', 'Medium', 'Low'"),
    sort_by: str = Query("source_row_number"),
    sort_desc: bool = Query(False),
    db: Session = Depends(get_db)
):
    """List assets for a given batch with filtering, searching, and pagination."""
    batch_repo = BatchRepository(db)
    batch = batch_repo.get_by_id(batch_id)
    if not batch:
        raise BatchNotFoundException(batch_id)

    asset_repo = AssetRepository(db)
    items, total = asset_repo.list_by_batch(
        batch_id=batch_id,
        limit=limit,
        offset=offset,
        search=search,
        asset_type=asset_type,
        department=department,
        criticality=criticality,
        vulnerability_severity=vulnerability_severity,
        validation_status=validation_status,
        owner_missing=owner_missing,
        risk_level=risk_level,
        sort_by=sort_by,
        sort_desc=sort_desc,
    )

    response_items = []
    for a in items:
        # Populate risk_score and risk_level from relation if present
        r_score = a.risk_assessment.risk_score if a.risk_assessment else None
        r_level = a.risk_assessment.risk_level if a.risk_assessment else None

        item_dict = {c.name: getattr(a, c.name) for c in a.__table__.columns}
        item_dict["risk_score"] = r_score
        item_dict["risk_level"] = r_level
        response_items.append(AssetResponse(**item_dict))

    return PaginatedAssetsResponse(
        items=response_items,
        total=total,
        limit=limit,
        offset=offset,
    )

