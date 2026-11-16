from sqlalchemy.orm import Session
from app.core.errors import BatchNotFoundException, BatchNotReadyException
from app.repositories.batch_repository import BatchRepository
from app.repositories.asset_repository import AssetRepository
from app.repositories.risk_repository import RiskRepository
from app.models.risk import RiskAssessment
from app.services.risk_engine import calculate_asset_risk
from app.schemas.risk import BatchAnalysisResponse, BatchAnalysisSummary

def run_batch_risk_analysis(db: Session, batch_id: str) -> BatchAnalysisResponse:
    """
    Run deterministic rule-based risk analysis on all eligible assets in a batch.
    - Idempotent: replaces any existing risk assessments for the batch.
    - Excludes blocked records; includes warning-only and valid records.
    """
    batch_repo = BatchRepository(db)
    batch = batch_repo.get_by_id(batch_id)
    if not batch:
        raise BatchNotFoundException(batch_id)

    if batch.status not in ["validated", "analyzed"]:
        raise BatchNotReadyException(
            f"Batch '{batch_id}' is in status '{batch.status}' and cannot be analyzed. "
            f"Batch must be validated first."
        )

    risk_repo = RiskRepository(db)
    asset_repo = AssetRepository(db)

    # Idempotent cleanup of prior assessments for this batch
    risk_repo.delete_by_batch(batch_id)

    # Fetch eligible assets (validation_status != 'blocked')
    eligible_assets = asset_repo.get_eligible_for_risk(batch_id)

    assessments = []
    for asset in eligible_assets:
        score_res = calculate_asset_risk(
            vulnerability_severity=asset.vulnerability_severity,
            criticality=asset.criticality,
            owner_name=asset.owner_name,
        )

        assessment = RiskAssessment(
            batch_id=batch_id,
            asset_record_id=asset.id,
            vulnerability_score=score_res.vulnerability_score,
            criticality_score=score_res.criticality_score,
            ownership_score=score_res.ownership_score,
            vulnerability_weight=score_res.vulnerability_weight,
            criticality_weight=score_res.criticality_weight,
            ownership_weight=score_res.ownership_weight,
            risk_score=score_res.risk_score,
            risk_level=score_res.risk_level,
            explanation=score_res.explanation,
        )
        assessments.append(assessment)

    if assessments:
        risk_repo.bulk_create(assessments)

    # Update batch status
    batch.status = "analyzed"
    db.commit()

    # Tally counts
    counts = risk_repo.get_batch_risk_counts(batch_id)

    summary = BatchAnalysisSummary(
        total_eligible=len(eligible_assets),
        scored_records=len(assessments),
        critical_count=counts.get("Critical", 0),
        high_count=counts.get("High", 0),
        medium_count=counts.get("Medium", 0),
        low_count=counts.get("Low", 0),
    )

    message = (
        f"Analyzed {len(assessments)} eligible assets successfully."
        if assessments
        else "No eligible assets found in batch to analyze."
    )

    return BatchAnalysisResponse(
        batch_id=batch_id,
        status="analyzed",
        summary=summary,
        message=message,
    )

