export interface Asset {
  id: number;
  batch_id: string;
  source_row_number: number;
  asset_id: string | null;
  hostname: string | null;
  ip_address: string | null;
  asset_type: string | null;
  sub_category: string | null;
  operating_system: string | null;
  os_version: string | null;
  owner_name: string | null;
  owner_email: string | null;
  department: string | null;
  environment: string | null;
  criticality: string | null;
  vulnerability_severity: string | null;
  vulnerability_count: number | null;
  internet_facing: string | null;
  data_classification: string | null;
  location: string | null;
  purchase_date: string | null;
  last_updated: string | null;
  lifecycle_status: string | null;
  backup_enabled: string | null;
  edr_enabled: string | null;
  organization: string | null;
  data_source: string | null;
  validation_status: 'valid' | 'warning' | 'blocked';
  created_at: string;
  risk_score?: number | null;
  risk_level?: string | null;
}

export interface PaginatedAssets {
  items: Asset[];
  total: number;
  limit: number;
  offset: number;
}

