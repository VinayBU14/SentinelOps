import React from 'react';
import { ImportBatch } from '../types/batch';
import { StatusBadge } from '../components/StatusBadge';
import { EmptyState } from '../components/EmptyState';
import { History, FileText } from 'lucide-react';
import { PageId } from '../components/Sidebar';

interface ImportHistoryPageProps {
  batches: ImportBatch[];
  selectedBatchId: string | null;
  onSelectBatch: (id: string) => void;
  onNavigate: (page: PageId) => void;
  onRefresh?: () => void;
}

export const ImportHistoryPage: React.FC<ImportHistoryPageProps> = ({
  batches,
  selectedBatchId,
  onSelectBatch,
  onNavigate,
  onRefresh,
}) => {
  return (
    <div>
      <div className="card-table-wrapper">
        <div className="table-toolbar">
          <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
            <History size={18} color="#0284c7" />
            <h3 style={{ fontSize: '1rem', fontWeight: 600 }}>Historical Import Batches</h3>
          </div>
          <div style={{ display: 'flex', gap: '0.5rem' }}>
            {onRefresh && (
              <button className="btn btn-secondary btn-sm" onClick={onRefresh}>
                Refresh List
              </button>
            )}
            <button className="btn btn-primary btn-sm" onClick={() => onNavigate('upload')}>
              Upload New Batch
            </button>
          </div>
        </div>

        {batches.length === 0 ? (
          <EmptyState
            title="No Import Batches Found"
            message="You have not uploaded any inventory batches yet."
            actionText="Upload First Batch"
            onAction={() => onNavigate('upload')}
          />
        ) : (
          <div style={{ overflowX: 'auto' }}>
            <table className="data-table">
              <thead>
                <tr>
                  <th>Filename</th>
                  <th>Format</th>
                  <th>Uploaded At</th>
                  <th>Status</th>
                  <th>Total Rows</th>
                  <th>Valid Rows</th>
                  <th>Warning Rows</th>
                  <th>Blocked Rows</th>
                  <th>SHA-256 Hash</th>
                  <th>Action</th>
                </tr>
              </thead>
              <tbody>
                {batches.map((batch) => {
                  const isCurrent = batch.id === selectedBatchId;
                  const s = batch.summary;
                  return (
                    <tr
                      key={batch.id}
                      style={isCurrent ? { backgroundColor: 'rgba(56, 189, 248, 0.06)' } : {}}
                      onClick={() => onSelectBatch(batch.id)}
                    >
                      <td>
                        <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
                          <FileText size={16} color="var(--text-muted)" />
                          <span style={{ fontWeight: 600 }}>{batch.original_filename}</span>
                          {isCurrent && (
                            <span
                              style={{
                                fontSize: '0.7rem',
                                backgroundColor: '#e0f2fe',
                                color: '#0369a1',
                                padding: '0.1rem 0.4rem',
                                borderRadius: '4px',
                                fontWeight: 600,
                              }}
                            >
                              ACTIVE
                            </span>
                          )}
                        </div>
                      </td>
                      <td className="mono">{batch.file_type.toUpperCase()}</td>
                      <td style={{ color: 'var(--text-muted)', fontSize: '0.8125rem' }}>
                        {new Date(batch.uploaded_at).toLocaleString()}
                      </td>
                      <td>
                        <StatusBadge status={batch.status} />
                      </td>
                      <td className="mono" style={{ fontWeight: 600 }}>{s.total_rows}</td>
                      <td style={{ color: '#047857' }}>{s.valid_rows}</td>
                      <td style={{ color: '#854d0e' }}>{s.warning_rows}</td>
                      <td style={{ color: s.blocked_rows > 0 ? '#b91c1c' : 'var(--text-muted)' }}>
                        {s.blocked_rows}
                      </td>
                      <td
                        className="mono"
                        style={{
                          fontSize: '0.75rem',
                          maxWidth: '120px',
                          overflow: 'hidden',
                          textOverflow: 'ellipsis',
                          color: 'var(--text-muted)',
                        }}
                        title={batch.file_sha256}
                      >
                        {batch.file_sha256 ? `${batch.file_sha256.substring(0, 12)}...` : '—'}
                      </td>
                      <td>
                        <button
                          className={`btn btn-sm ${isCurrent ? 'btn-secondary' : 'btn-primary'}`}
                          onClick={(e) => {
                            e.stopPropagation();
                            onSelectBatch(batch.id);
                            onNavigate('overview');
                          }}
                        >
                          {isCurrent ? 'View Overview' : 'Switch to Batch'}
                        </button>
                      </td>
                    </tr>
                  );
                })}
              </tbody>
            </table>
          </div>
        )}
      </div>
    </div>
  );
};
