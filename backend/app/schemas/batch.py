from datetime import datetime
from typing import Optional
from pydantic import BaseModel, ConfigDict

class BatchSummary(BaseModel):
    total_rows: int
    valid_rows: int
    warning_rows: int
    blocked_rows: int
    error_count: int
    warning_count: int
    blank_rows: int

class BatchResponse(BaseModel):
    id: str
    original_filename: str
    file_type: str
    uploaded_at: datetime
    status: str
    summary: BatchSummary
    file_sha256: Optional[str] = None

    model_config = ConfigDict(from_attributes=True)

class UploadResponse(BaseModel):
    batch_id: str
    status: str
    filename: str
    summary: BatchSummary
    message: str

