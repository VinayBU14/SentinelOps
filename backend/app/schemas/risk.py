from datetime import datetime
from typing import Optional
from pydantic import BaseModel, ConfigDict
from app.schemas.asset import AssetResponse

class RiskAssessmentResponse(BaseModel):
    id: int
    batch_id: str
    asset_record_id: int
    vulnerability_score: float
    criticality_score: float
    ownership_score: float
    vulnerability_weight: float
    criticality_weight: float
    ownership_weight: float
    risk_score: float
    risk_level: str
    explanation: str
    calculated_at: datetime
    asset: Optional[AssetResponse] = None

    model_config = ConfigDict(from_attributes=True)

class AssetRiskDetailResponse(BaseModel):
    asset: AssetResponse
    risk_assessment: Optional[RiskAssessmentResponse] = None

class BatchAnalysisSummary(BaseModel):
    total_eligible: int
    scored_records: int
    critical_count: int
    high_count: int
    medium_count: int
    low_count: int

class BatchAnalysisResponse(BaseModel):
    batch_id: str
    status: str
    summary: BatchAnalysisSummary
    message: str

