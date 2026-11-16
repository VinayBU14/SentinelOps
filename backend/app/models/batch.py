import uuid
from datetime import datetime, timezone
from sqlalchemy import Column, String, Integer, DateTime
from sqlalchemy.orm import relationship
from app.db.session import Base

class ImportBatch(Base):
    __tablename__ = "import_batches"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    original_filename = Column(String(255), nullable=False)
    file_type = Column(String(10), nullable=False)  # 'csv' or 'json'
    uploaded_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), nullable=False)
    status = Column(String(20), default="uploaded", nullable=False)  # 'uploaded', 'validated', 'analyzed', 'failed'
    
    total_rows = Column(Integer, default=0, nullable=False)
    valid_rows = Column(Integer, default=0, nullable=False)
    warning_rows = Column(Integer, default=0, nullable=False)
    blocked_rows = Column(Integer, default=0, nullable=False)
    error_count = Column(Integer, default=0, nullable=False)
    warning_count = Column(Integer, default=0, nullable=False)
    blank_rows = Column(Integer, default=0, nullable=False)
    file_sha256 = Column(String(64), nullable=True)

    assets = relationship("Asset", back_populates="batch", cascade="all, delete-orphan")
    issues = relationship("ValidationIssue", back_populates="batch", cascade="all, delete-orphan")
    risk_assessments = relationship("RiskAssessment", back_populates="batch", cascade="all, delete-orphan")

