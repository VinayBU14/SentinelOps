from datetime import datetime
from typing import Optional, Union, Any
from pydantic import BaseModel, ConfigDict

class RawAssetInput(BaseModel):
    asset_id: Optional[Any] = None
    hostname: Optional[Any] = None
    ip_address: Optional[Any] = None
    asset_type: Optional[Any] = None
    sub_category: Optional[Any] = None
    operating_system: Optional[Any] = None
    os_version: Optional[Any] = None
    owner_name: Optional[Any] = None
    owner_email: Optional[Any] = None
    department: Optional[Any] = None
    environment: Optional[Any] = None
    criticality: Optional[Any] = None
    vulnerability_severity: Optional[Any] = None
    vulnerability_count: Optional[Any] = None
    internet_facing: Optional[Any] = None
    data_classification: Optional[Any] = None
    location: Optional[Any] = None
    purchase_date: Optional[Any] = None
    last_updated: Optional[Any] = None
    lifecycle_status: Optional[Any] = None
    backup_enabled: Optional[Any] = None
    edr_enabled: Optional[Any] = None
    organization: Optional[Any] = None
    data_source: Optional[Any] = None

class AssetResponse(BaseModel):
    id: int
    batch_id: str
    source_row_number: int
    asset_id: Optional[str] = None
    hostname: Optional[str] = None
    ip_address: Optional[str] = None
    asset_type: Optional[str] = None
    sub_category: Optional[str] = None
    operating_system: Optional[str] = None
    os_version: Optional[str] = None
    owner_name: Optional[str] = None
    owner_email: Optional[str] = None
    department: Optional[str] = None
    environment: Optional[str] = None
    criticality: Optional[str] = None
    vulnerability_severity: Optional[str] = None
    vulnerability_count: Optional[int] = None
    internet_facing: Optional[str] = None
    data_classification: Optional[str] = None
    location: Optional[str] = None
    purchase_date: Optional[str] = None
    last_updated: Optional[str] = None
    lifecycle_status: Optional[str] = None
    backup_enabled: Optional[str] = None
    edr_enabled: Optional[str] = None
    organization: Optional[str] = None
    data_source: Optional[str] = None
    validation_status: str
    created_at: datetime
    risk_score: Optional[float] = None
    risk_level: Optional[str] = None

    model_config = ConfigDict(from_attributes=True)

