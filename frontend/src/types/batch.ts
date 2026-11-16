export interface BatchSummary {
  total_rows: number;
  valid_rows: number;
  warning_rows: number;
  blocked_rows: number;
  error_count: number;
  warning_count: number;
  blank_rows: number;
}

export interface ImportBatch {
  id: string;
  original_filename: string;
  file_type: string;
  uploaded_at: string;
  status: 'uploaded' | 'validated' | 'analyzed' | 'failed';
  summary: BatchSummary;
  file_sha256?: string;
}

export interface UploadResponse {
  batch_id: string;
  status: string;
  filename: string;
  summary: BatchSummary;
  message: string;
}

