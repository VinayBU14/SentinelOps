from typing import List, Optional
from sqlalchemy.orm import Session
from app.models.batch import ImportBatch

class BatchRepository:
    def __init__(self, db: Session):
        self.db = db

    def create(self, batch: ImportBatch) -> ImportBatch:
        self.db.add(batch)
        self.db.commit()
        self.db.refresh(batch)
        return batch

    def get_by_id(self, batch_id: str) -> Optional[ImportBatch]:
        return self.db.query(ImportBatch).filter(ImportBatch.id == batch_id).first()

    def list_all(self, limit: int = 50, offset: int = 0) -> List[ImportBatch]:
        return (
            self.db.query(ImportBatch)
            .order_by(ImportBatch.uploaded_at.desc())
            .offset(offset)
            .limit(limit)
            .all()
        )

    def count_all(self) -> int:
        return self.db.query(ImportBatch).count()

    def update_status(self, batch_id: str, status: str) -> Optional[ImportBatch]:
        batch = self.get_by_id(batch_id)
        if batch:
            batch.status = status
            self.db.commit()
            self.db.refresh(batch)
        return batch

