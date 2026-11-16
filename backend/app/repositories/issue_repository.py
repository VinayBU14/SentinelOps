from typing import List, Optional, Tuple
from sqlalchemy.orm import Session
from app.models.issue import ValidationIssue

class IssueRepository:
    def __init__(self, db: Session):
        self.db = db

    def bulk_create(self, issues: List[ValidationIssue]) -> List[ValidationIssue]:
        self.db.add_all(issues)
        self.db.commit()
        return issues

    def list_by_batch(
        self,
        batch_id: str,
        limit: int = 50,
        offset: int = 0,
        severity: Optional[str] = None,
        blocking: Optional[bool] = None,
        issue_code: Optional[str] = None,
        field_name: Optional[str] = None,
    ) -> Tuple[List[ValidationIssue], int]:
        query = self.db.query(ValidationIssue).filter(ValidationIssue.batch_id == batch_id)

        if severity:
            query = query.filter(ValidationIssue.severity == severity.lower().strip())

        if blocking is not None:
            query = query.filter(ValidationIssue.blocking == blocking)

        if issue_code:
            query = query.filter(ValidationIssue.issue_code == issue_code.strip())

        if field_name:
            query = query.filter(ValidationIssue.field_name == field_name.strip())

        total = query.count()
        items = (
            query.order_by(ValidationIssue.row_number.asc(), ValidationIssue.id.asc())
            .offset(offset)
            .limit(limit)
            .all()
        )
        return items, total

