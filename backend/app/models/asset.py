from datetime import datetime, timezone
from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, Index
from sqlalchemy.orm import relationship
from app.db.session import Base

class Asset(Base):
    __tablename__ = "assets"

    id = Column(Integer, primary_key=True, autoincrement=True)
    batch_id = Column(String(36), ForeignKey("import_batches.id", ondelete="CASCADE"), nullable=False, index=True)
    source_row_number = Column(Integer, nullable=False)

    # 24 inventory fields (nullable in case of malformed / missing inputs)
    asset_id = Column(String(100), nullable=True)
    hostname = Column(String(255), nullable=True)
    ip_address = Column(String(50), nullable=True)
    asset_type = Column(String(50), nullable=True)
    sub_category = Column(String(100), nullable=True)
    operating_system = Column(String(100), nullable=True)
    os_version = Column(String(50), nullable=True)
    owner_name = Column(String(150), nullable=True)
    owner_email = Column(String(150), nullable=True)
    department = Column(String(100), nullable=True)
    environment = Column(String(50), nullable=True)
    criticality = Column(String(50), nullable=True)
    vulnerability_severity = Column(String(50), nullable=True)
    vulnerability_count = Column(Integer, nullable=True)
    internet_facing = Column(String(10), nullable=True)
    data_classification = Column(String(50), nullable=True)
    location = Column(String(150), nullable=True)
    purchase_date = Column(String(30), nullable=True)
    last_updated = Column(String(30), nullable=True)
    lifecycle_status = Column(String(50), nullable=True)
    backup_enabled = Column(String(10), nullable=True)
    edr_enabled = Column(String(10), nullable=True)
    organization = Column(String(150), nullable=True)
    data_source = Column(String(100), nullable=True)

    validation_status = Column(String(20), nullable=False, default="valid")  # 'valid', 'warning', 'blocked'
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), nullable=False)

    batch = relationship("ImportBatch", back_populates="assets")
    issues = relationship("ValidationIssue", back_populates="asset", cascade="all, delete-orphan")
    risk_assessment = relationship("RiskAssessment", back_populates="asset", uselist=False, cascade="all, delete-orphan")

    __table_args__ = (
        Index("ix_assets_batch_asset_id", "batch_id", "asset_id"),
    )

