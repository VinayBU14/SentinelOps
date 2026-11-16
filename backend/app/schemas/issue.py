from datetime import datetime
from typing import Optional
from pydantic import BaseModel, ConfigDict

class ValidationIssueBase(BaseModel):
    row_number: int
    asset_id: Optional[str] = None
    issue_code: str
    severity: str  # 'error', 'warning', 'info'
    blocking: bool
    field_name: str
    observed_value: Optional[str] = None
    message: str
    suggested_action: str

class ValidationIssueCreate(ValidationIssueBase):
    batch_id: str
    asset_record_id: Optional[int] = None

class ValidationIssueResponse(ValidationIssueBase):
    id: int
    batch_id: str
    asset_record_id: Optional[int] = None
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)

