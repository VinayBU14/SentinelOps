from typing import Optional, List
from fastapi import APIRouter, Depends, Query, HTTPException, status
from sqlalchemy.orm import Session
from pydantic import BaseModel
from app.db.session import get_db
from app.core.errors import BatchNotFoundException
from app.schemas.risk import (
    RiskAssessmentResponse,
    AssetRiskDetailResponse,
    BatchAnalysisResponse,
)
from app.schemas.asset import AssetResponse
from app.repositories.batch_repository import BatchRepository
from app.repositories.asset_repository import AssetRepository
from app.repositories.risk_repository import RiskRepository
from app.services.analysis_service import run_batch_risk_analysis

router = APIRouter(prefix="/batches/{batch_id}", tags=["Risk Analysis"])

class PaginatedRisksResponse(BaseModel):
    items: List[RiskAssessmentResponse]
    total: int
    limit: int
    offset: int

@router.post("/analyze", response_model=BatchAnalysisResponse)
def analyze_batch(
    batch_id: str,
    db: Session = Depends(get_db)
):
    """
    Calculate deterministic risk scores for eligible assets in the specified batch.
    Idempotent: repeating analysis updates risk assessments without duplicating records.
    """
    return run_batch_risk_analysis(db=db, batch_id=batch_id)

@router.get("/risks", response_model=PaginatedRisksResponse)
def list_ranked_risks(
    batch_id: str,
    limit: int = Query(50, ge=1, le=200),
    offset: int = Query(0, ge=0),
    risk_level: Optional[str] = Query(None, description="'Critical', 'High', 'Medium', 'Low'"),
    asset_type: Optional[str] = Query(None),
    department: Optional[str] = Query(None),
    criticality: Optional[str] = Query(None),
    vulnerability_severity: Optional[str] = Query(None),
    owner_missing: Optional[bool] = Query(None),
    search: Optional[str] = Query(None),
    db: Session = Depends(get_db)
):
    """
    Retrieve paginated risk assessments ranked by risk score descending, then asset ID ascending.
    """
    batch_repo = BatchRepository(db)
    batch = batch_repo.get_by_id(batch_id)
    if not batch:
        raise BatchNotFoundException(batch_id)

    risk_repo = RiskRepository(db)
    items, total = risk_repo.list_ranked_risks(
        batch_id=batch_id,
        limit=limit,
        offset=offset,
        risk_level=risk_level,
        asset_type=asset_type,
        department=department,
        criticality=criticality,
        vulnerability_severity=vulnerability_severity,
        owner_missing=owner_missing,
        search=search,
    )

    response_items = []
    for r in items:
        # Construct AssetResponse
        a = r.asset
        asset_resp = None
        if a:
            item_dict = {c.name: getattr(a, c.name) for c in a.__table__.columns}
            item_dict["risk_score"] = r.risk_score
            item_dict["risk_level"] = r.risk_level
            asset_resp = AssetResponse(**item_dict)

        resp = RiskAssessmentResponse(
            id=r.id,
            batch_id=r.batch_id,
            asset_record_id=r.asset_record_id,
            vulnerability_score=r.vulnerability_score,
            criticality_score=r.criticality_score,
            ownership_score=r.ownership_score,
            vulnerability_weight=r.vulnerability_weight,
            criticality_weight=r.criticality_weight,
            ownership_weight=r.ownership_weight,
            risk_score=r.risk_score,
            risk_level=r.risk_level,
            explanation=r.explanation,
            calculated_at=r.calculated_at,
            asset=asset_resp,
        )
        response_items.append(resp)

    return PaginatedRisksResponse(
        items=response_items,
        total=total,
        limit=limit,
        offset=offset,
    )

@router.get("/assets/{record_id}/risk", response_model=AssetRiskDetailResponse)
def get_asset_risk_detail(
    batch_id: str,
    record_id: int,
    db: Session = Depends(get_db)
):
    """
    Retrieve comprehensive risk breakdown and explainability report for a specific asset.
    """
    batch_repo = BatchRepository(db)
    batch = batch_repo.get_by_id(batch_id)
    if not batch:
        raise BatchNotFoundException(batch_id)

    asset_repo = AssetRepository(db)
    asset = asset_repo.get_by_id(record_id)
    if not asset or asset.batch_id != batch_id:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Asset record '{record_id}' not found in batch '{batch_id}'."
        )

    risk_repo = RiskRepository(db)
    assessment = risk_repo.get_by_asset_record_id(record_id)

    asset_dict = {c.name: getattr(asset, c.name) for c in asset.__table__.columns}
    if assessment:
        asset_dict["risk_score"] = assessment.risk_score
        asset_dict["risk_level"] = assessment.risk_level
    asset_resp = AssetResponse(**asset_dict)

    assessment_resp = (
        RiskAssessmentResponse.model_validate(assessment)
        if assessment
        else None
    )

    return AssetRiskDetailResponse(
        asset=asset_resp,
        risk_assessment=assessment_resp,
    )

