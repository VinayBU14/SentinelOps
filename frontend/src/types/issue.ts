export interface ValidationIssue {
  id: number;
  batch_id: string;
  asset_record_id: number | null;
  row_number: number;
  asset_id: string | null;
  issue_code: string;
  severity: 'error' | 'warning' | 'info';
  blocking: boolean;
  field_name: string;
  observed_value: string | null;
  message: string;
  suggested_action: string;
  created_at: string;
}

export interface PaginatedIssues {
  items: ValidationIssue[];
  total: number;
  limit: number;
  offset: number;
}

