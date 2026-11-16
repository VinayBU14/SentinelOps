from datetime import datetime, timezone
from sqlalchemy import Column, Integer, String, Float, Text, DateTime, ForeignKey, Index
from sqlalchemy.orm import relationship
from app.db.session import Base

class RiskAssessment(Base):
    __tablename__ = "risk_assessments"

    id = Column(Integer, primary_key=True, autoincrement=True)
    batch_id = Column(String(36), ForeignKey("import_batches.id", ondelete="CASCADE"), nullable=False, index=True)
    asset_record_id = Column(Integer, ForeignKey("assets.id", ondelete="CASCADE"), nullable=False, index=True)

    vulnerability_score = Column(Float, nullable=False)
    criticality_score = Column(Float, nullable=False)
    ownership_score = Column(Float, nullable=False)
    vulnerability_weight = Column(Float, nullable=False, default=0.50)
    criticality_weight = Column(Float, nullable=False, default=0.30)
    ownership_weight = Column(Float, nullable=False, default=0.20)
    risk_score = Column(Float, nullable=False, index=True)
    risk_level = Column(String(20), nullable=False)  # 'Low', 'Medium', 'High', 'Critical'
    explanation = Column(Text, nullable=False)
    calculated_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), nullable=False)

    batch = relationship("ImportBatch", back_populates="risk_assessments")
    asset = relationship("Asset", back_populates="risk_assessment")

    __table_args__ = (
        Index("ix_risks_batch_score", "batch_id", "risk_score"),
        Index("ix_risks_batch_level", "batch_id", "risk_level"),
    )

