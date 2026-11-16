import { Asset } from './asset';

export interface RiskAssessment {
  id: number;
  batch_id: string;
  asset_record_id: number;
  vulnerability_score: number;
  criticality_score: number;
  ownership_score: number;
  vulnerability_weight: number;
  criticality_weight: number;
  ownership_weight: number;
  risk_score: number;
  risk_level: 'Critical' | 'High' | 'Medium' | 'Low';
  explanation: string;
  calculated_at: string;
  asset?: Asset;
}

export interface PaginatedRisks {
  items: RiskAssessment[];
  total: number;
  limit: number;
  offset: number;
}

export interface AssetRiskDetail {
  asset: Asset;
  risk_assessment: RiskAssessment | null;
}

export interface BatchAnalysisResponse {
  batch_id: string;
  status: string;
  summary: {
    total_eligible: number;
    scored_records: number;
    critical_count: number;
    high_count: number;
    medium_count: number;
    low_count: number;
  };
  message: string;
}

