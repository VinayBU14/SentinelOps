from typing import List, Optional, Tuple
from sqlalchemy import or_, and_
from sqlalchemy.orm import Session
from app.models.asset import Asset
from app.models.risk import RiskAssessment

class AssetRepository:
    def __init__(self, db: Session):
        self.db = db

    def bulk_create(self, assets: List[Asset]) -> List[Asset]:
        self.db.add_all(assets)
        self.db.commit()
        return assets

    def get_by_id(self, asset_id: int) -> Optional[Asset]:
        return self.db.query(Asset).filter(Asset.id == asset_id).first()

    def list_by_batch(
        self,
        batch_id: str,
        limit: int = 50,
        offset: int = 0,
        search: Optional[str] = None,
        asset_type: Optional[str] = None,
        department: Optional[str] = None,
        criticality: Optional[str] = None,
        vulnerability_severity: Optional[str] = None,
        validation_status: Optional[str] = None,
        owner_missing: Optional[bool] = None,
        risk_level: Optional[str] = None,
        sort_by: str = "source_row_number",
        sort_desc: bool = False,
    ) -> Tuple[List[Asset], int]:
        query = self.db.query(Asset).outerjoin(RiskAssessment, Asset.id == RiskAssessment.asset_record_id).filter(Asset.batch_id == batch_id)

        if search:
            s = f"%{search.strip()}%"
            query = query.filter(
                or_(
                    Asset.asset_id.ilike(s),
                    Asset.hostname.ilike(s),
                    Asset.ip_address.ilike(s),
                )
            )

        if asset_type:
            query = query.filter(Asset.asset_type.ilike(asset_type.strip()))

        if department:
            query = query.filter(Asset.department.ilike(department.strip()))

        if criticality:
            query = query.filter(Asset.criticality.ilike(criticality.strip()))

        if vulnerability_severity:
            query = query.filter(Asset.vulnerability_severity.ilike(vulnerability_severity.strip()))

        if validation_status:
            query = query.filter(Asset.validation_status == validation_status.lower().strip())

        if owner_missing is not None:
            if owner_missing:
                query = query.filter(or_(Asset.owner_name == None, Asset.owner_name == ""))
            else:
                query = query.filter(and_(Asset.owner_name != None, Asset.owner_name != ""))

        if risk_level:
            query = query.filter(RiskAssessment.risk_level.ilike(risk_level.strip()))

        total = query.count()

        # Sorting
        if sort_by == "risk_score":
            order_col = RiskAssessment.risk_score
        elif hasattr(Asset, sort_by):
            order_col = getattr(Asset, sort_by)
        else:
            order_col = Asset.source_row_number

        if sort_desc:
            query = query.order_by(order_col.desc(), Asset.id.asc())
        else:
            query = query.order_by(order_col.asc(), Asset.id.asc())

        items = query.offset(offset).limit(limit).all()
        return items, total

    def get_eligible_for_risk(self, batch_id: str) -> List[Asset]:
        """Return assets without blocking issues for this batch."""
        return (
            self.db.query(Asset)
            .filter(
                Asset.batch_id == batch_id,
                Asset.validation_status != "blocked"
            )
            .order_by(Asset.source_row_number.asc())
            .all()
        )

