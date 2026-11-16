import React from 'react';
import { ImportBatch } from '../types/batch';
import { RefreshCw, Upload, HelpCircle } from 'lucide-react';
import { PageId } from './Sidebar';

interface TopBarProps {
  currentPage: PageId;
  batches: ImportBatch[];
  selectedBatchId: string | null;
  onSelectBatch: (id: string) => void;
  onNavigate: (page: PageId) => void;
  onRefresh: () => void;
  onOpenFormula: () => void;
  loading?: boolean;
}

const PAGE_TITLES: Record<PageId, string> = {
  overview: 'Overview Dashboard',
  upload: 'Upload & Ingest Inventory',
  inventory: 'Cyber Asset Inventory',
  'data-quality': 'Data Quality & Validation Issues',
  'risk-analysis': 'Explainable Risk Prioritization',
  history: 'Import Batches & History',
};

export const TopBar: React.FC<TopBarProps> = ({
  currentPage,
  batches,
  selectedBatchId,
  onSelectBatch,
  onNavigate,
  onRefresh,
  onOpenFormula,
  loading = false,
}) => {
  return (
    <header className="topbar">
      <div className="topbar-left">
        <h1 className="page-title">{PAGE_TITLES[currentPage]}</h1>

        {batches.length > 0 && currentPage !== 'upload' && currentPage !== 'history' && (
          <div className="batch-selector-wrapper">
            <span style={{ color: 'var(--text-muted)', fontSize: '0.8125rem' }}>Active Batch:</span>
            <select
              className="batch-select"
              value={selectedBatchId || ''}
              onChange={(e) => onSelectBatch(e.target.value)}
            >
              {batches.map((b) => (
                <option key={b.id} value={b.id}>
                  {b.original_filename} ({b.summary.total_rows} assets — {b.status})
                </option>
              ))}
            </select>
          </div>
        )}
      </div>

      <div className="topbar-actions">
        <button
          className="btn btn-secondary btn-sm"
          onClick={onOpenFormula}
          title="How SentinelOps calculates risk"
        >
          <HelpCircle size={15} />
          <span>Scoring Formula</span>
        </button>

        <button
          className="btn btn-secondary btn-sm"
          onClick={onRefresh}
          disabled={loading}
          title="Refresh current data"
        >
          <RefreshCw size={15} className={loading ? 'spin' : ''} />
          <span>Refresh</span>
        </button>

        <button className="btn btn-primary btn-sm" onClick={() => onNavigate('upload')}>
          <Upload size={15} />
          <span>Upload File</span>
        </button>
      </div>
    </header>
  );
};

