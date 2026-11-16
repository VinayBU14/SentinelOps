import { ImportBatch, UploadResponse } from '../types/batch';
import { PaginatedAssets } from '../types/asset';
import { PaginatedIssues } from '../types/issue';
import { PaginatedRisks, AssetRiskDetail, BatchAnalysisResponse } from '../types/risk';

const API_BASE = '/api/v1';

async function handleResponse<T>(res: Response): Promise<T> {
  if (!res.ok) {
    let errorDetail = `Request failed with status ${res.status}`;
    try {
      const data = await res.json();
      if (data && data.detail) {
        errorDetail = data.detail;
      }
    } catch {
      // ignore json parse error
    }
    throw new Error(errorDetail);
  }
  return res.json() as Promise<T>;
}

export const api = {
  // Batches
  async getBatches(limit = 50, offset = 0): Promise<ImportBatch[]> {
    const res = await fetch(`${API_BASE}/batches?limit=${limit}&offset=${offset}`);
    return handleResponse<ImportBatch[]>(res);
  },

  async getBatch(batchId: string): Promise<ImportBatch> {
    const res = await fetch(`${API_BASE}/batches/${batchId}`);
    return handleResponse<ImportBatch>(res);
  },

  // Upload
  async uploadFile(file: File): Promise<UploadResponse> {
    const formData = new FormData();
    formData.append('file', file);
    const res = await fetch(`${API_BASE}/uploads`, {
      method: 'POST',
      body: formData,
    });
    return handleResponse<UploadResponse>(res);
  },

  // Assets
  async getAssets(
    batchId: string,
    params: {
      limit?: number;
      offset?: number;
      search?: string;
      asset_type?: string;
      department?: string;
      criticality?: string;
      vulnerability_severity?: string;
      validation_status?: string;
      owner_missing?: boolean;
      risk_level?: string;
      sort_by?: string;
      sort_desc?: boolean;
    } = {}
  ): Promise<PaginatedAssets> {
    const query = new URLSearchParams();
    if (params.limit !== undefined) query.set('limit', params.limit.toString());
    if (params.offset !== undefined) query.set('offset', params.offset.toString());
    if (params.search) query.set('search', params.search);
    if (params.asset_type) query.set('asset_type', params.asset_type);
    if (params.department) query.set('department', params.department);
    if (params.criticality) query.set('criticality', params.criticality);
    if (params.vulnerability_severity) query.set('vulnerability_severity', params.vulnerability_severity);
    if (params.validation_status) query.set('validation_status', params.validation_status);
    if (params.owner_missing !== undefined) query.set('owner_missing', params.owner_missing.toString());
    if (params.risk_level) query.set('risk_level', params.risk_level);
    if (params.sort_by) query.set('sort_by', params.sort_by);
    if (params.sort_desc !== undefined) query.set('sort_desc', params.sort_desc.toString());

    const res = await fetch(`${API_BASE}/batches/${batchId}/assets?${query.toString()}`);
    return handleResponse<PaginatedAssets>(res);
  },

  // Validation Issues
  async getIssues(
    batchId: string,
    params: {
      limit?: number;
      offset?: number;
      severity?: string;
      blocking?: boolean;
      issue_code?: string;
      field_name?: string;
    } = {}
  ): Promise<PaginatedIssues> {
    const query = new URLSearchParams();
    if (params.limit !== undefined) query.set('limit', params.limit.toString());
    if (params.offset !== undefined) query.set('offset', params.offset.toString());
    if (params.severity) query.set('severity', params.severity);
    if (params.blocking !== undefined) query.set('blocking', params.blocking.toString());
    if (params.issue_code) query.set('issue_code', params.issue_code);
    if (params.field_name) query.set('field_name', params.field_name);

    const res = await fetch(`${API_BASE}/batches/${batchId}/issues?${query.toString()}`);
    return handleResponse<PaginatedIssues>(res);
  },

  // Risk Analysis
  async analyzeBatch(batchId: string): Promise<BatchAnalysisResponse> {
    const res = await fetch(`${API_BASE}/batches/${batchId}/analyze`, {
      method: 'POST',
    });
    return handleResponse<BatchAnalysisResponse>(res);
  },

  async getRankedRisks(
    batchId: string,
    params: {
      limit?: number;
      offset?: number;
      risk_level?: string;
      asset_type?: string;
      department?: string;
      criticality?: string;
      vulnerability_severity?: string;
      owner_missing?: boolean;
      search?: string;
    } = {}
  ): Promise<PaginatedRisks> {
    const query = new URLSearchParams();
    if (params.limit !== undefined) query.set('limit', params.limit.toString());
    if (params.offset !== undefined) query.set('offset', params.offset.toString());
    if (params.risk_level) query.set('risk_level', params.risk_level);
    if (params.asset_type) query.set('asset_type', params.asset_type);
    if (params.department) query.set('department', params.department);
    if (params.criticality) query.set('criticality', params.criticality);
    if (params.vulnerability_severity) query.set('vulnerability_severity', params.vulnerability_severity);
    if (params.owner_missing !== undefined) query.set('owner_missing', params.owner_missing.toString());
    if (params.search) query.set('search', params.search);

    const res = await fetch(`${API_BASE}/batches/${batchId}/risks?${query.toString()}`);
    return handleResponse<PaginatedRisks>(res);
  },

  async getAssetRiskDetail(batchId: string, recordId: number): Promise<AssetRiskDetail> {
    const res = await fetch(`${API_BASE}/batches/${batchId}/assets/${recordId}/risk`);
    return handleResponse<AssetRiskDetail>(res);
  },

  // Sample CSV URL
  getSampleCsvUrl(): string {
    return `${API_BASE}/sample-dataset`;
  },
};
