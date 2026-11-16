from datetime import datetime, timezone
from sqlalchemy import Column, Integer, String, Text, Boolean, DateTime, ForeignKey, Index
from sqlalchemy.orm import relationship
from app.db.session import Base

class ValidationIssue(Base):
    __tablename__ = "validation_issues"

    id = Column(Integer, primary_key=True, autoincrement=True)
    batch_id = Column(String(36), ForeignKey("import_batches.id", ondelete="CASCADE"), nullable=False, index=True)
    asset_record_id = Column(Integer, ForeignKey("assets.id", ondelete="CASCADE"), nullable=True, index=True)
    row_number = Column(Integer, nullable=False)
    asset_id = Column(String(100), nullable=True, index=True)
    issue_code = Column(String(50), nullable=False, index=True)
    severity = Column(String(20), nullable=False)  # 'error', 'warning', 'info'
    blocking = Column(Boolean, nullable=False, default=False)
    field_name = Column(String(50), nullable=False)
    observed_value = Column(String(255), nullable=True)
    message = Column(Text, nullable=False)
    suggested_action = Column(Text, nullable=False)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), nullable=False)

    batch = relationship("ImportBatch", back_populates="issues")
    asset = relationship("Asset", back_populates="issues")

    __table_args__ = (
        Index("ix_issues_batch_severity", "batch_id", "severity"),
        Index("ix_issues_batch_blocking", "batch_id", "blocking"),
    )

