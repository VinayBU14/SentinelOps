from typing import List, Optional, Tuple, Dict
from sqlalchemy import or_, and_, func
from sqlalchemy.orm import Session
from app.models.risk import RiskAssessment
from app.models.asset import Asset

class RiskRepository:
    def __init__(self, db: Session):
        self.db = db

    def delete_by_batch(self, batch_id: str) -> int:
        """Delete all risk assessments for a batch (for idempotent re-analysis)."""
        deleted = (
            self.db.query(RiskAssessment)
            .filter(RiskAssessment.batch_id == batch_id)
            .delete(synchronize_session=False)
        )
        self.db.commit()
        return deleted

    def bulk_create(self, assessments: List[RiskAssessment]) -> List[RiskAssessment]:
        self.db.add_all(assessments)
        self.db.commit()
        return assessments

    def get_by_asset_record_id(self, asset_record_id: int) -> Optional[RiskAssessment]:
        return (
            self.db.query(RiskAssessment)
            .filter(RiskAssessment.asset_record_id == asset_record_id)
            .first()
        )

    def list_ranked_risks(
        self,
        batch_id: str,
        limit: int = 50,
        offset: int = 0,
        risk_level: Optional[str] = None,
        asset_type: Optional[str] = None,
        department: Optional[str] = None,
        criticality: Optional[str] = None,
        vulnerability_severity: Optional[str] = None,
        owner_missing: Optional[bool] = None,
        search: Optional[str] = None,
    ) -> Tuple[List[RiskAssessment], int]:
        query = (
            self.db.query(RiskAssessment)
            .join(Asset, RiskAssessment.asset_record_id == Asset.id)
            .filter(RiskAssessment.batch_id == batch_id)
        )

        if search:
            s = f"%{search.strip()}%"
            query = query.filter(
                or_(
                    Asset.asset_id.ilike(s),
                    Asset.hostname.ilike(s),
                    Asset.ip_address.ilike(s),
                )
            )

        if risk_level:
            query = query.filter(RiskAssessment.risk_level.ilike(risk_level.strip()))

        if asset_type:
            query = query.filter(Asset.asset_type.ilike(asset_type.strip()))

        if department:
            query = query.filter(Asset.department.ilike(department.strip()))

        if criticality:
            query = query.filter(Asset.criticality.ilike(criticality.strip()))

        if vulnerability_severity:
            query = query.filter(Asset.vulnerability_severity.ilike(vulnerability_severity.strip()))

        if owner_missing is not None:
            if owner_missing:
                query = query.filter(or_(Asset.owner_name == None, Asset.owner_name == ""))
            else:
                query = query.filter(and_(Asset.owner_name != None, Asset.owner_name != ""))

        total = query.count()

        # Deterministic sorting: risk_score desc, then asset_id asc
        items = (
            query.order_by(RiskAssessment.risk_score.desc(), Asset.asset_id.asc())
            .offset(offset)
            .limit(limit)
            .all()
        )
        return items, total

    def get_batch_risk_counts(self, batch_id: str) -> Dict[str, int]:
        results = (
            self.db.query(RiskAssessment.risk_level, func.count(RiskAssessment.id))
            .filter(RiskAssessment.batch_id == batch_id)
            .group_by(RiskAssessment.risk_level)
            .all()
        )
        counts = {"Critical": 0, "High": 0, "Medium": 0, "Low": 0}
        for level, count in results:
            if level in counts:
                counts[level] = count
        return counts

