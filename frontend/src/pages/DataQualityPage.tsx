import React, { useEffect, useState } from 'react';
import { ImportBatch } from '../types/batch';
import { ValidationIssue } from '../types/issue';
import { api } from '../services/api';
import { StatusBadge } from '../components/StatusBadge';
import { StatCard } from '../components/StatCard';
import { LoadingSkeleton, EmptyState, ErrorState } from '../components/EmptyState';
import {
  ShieldAlert,
  AlertTriangle,
  CheckCircle2,
  ChevronLeft,
  ChevronRight,
  FileCheck,
} from 'lucide-react';

interface DataQualityPageProps {
  batch: ImportBatch | null;
  onNavigateUpload: () => void;
}

export const DataQualityPage: React.FC<DataQualityPageProps> = ({
  batch,
  onNavigateUpload,
}) => {
  const [issues, setIssues] = useState<ValidationIssue[]>([]);
  const [total, setTotal] = useState(0);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  // Filters & Pagination
  const [limit, setLimit] = useState(50);
  const [offset, setOffset] = useState(0);
  const [severity, setSeverity] = useState('');
  const [blocking, setBlocking] = useState<string>('all');
  const [issueCode, setIssueCode] = useState('');

  const loadIssues = () => {
    if (!batch) return;
    setLoading(true);
    setError(null);

    const blockingParam =
      blocking === 'true' ? true : blocking === 'false' ? false : undefined;

    api.getIssues(batch.id, {
      limit,
      offset,
      severity: severity || undefined,
      blocking: blockingParam,
      issue_code: issueCode.trim() || undefined,
    })
      .then((res) => {
        setIssues(res.items);
        setTotal(res.total);
        setLoading(false);
      })
      .catch((err) => {
        setError(err.message || 'Failed to fetch validation issues');
        setLoading(false);
      });
  };

  useEffect(() => {
    setOffset(0);
  }, [severity, blocking, issueCode, limit]);

  useEffect(() => {
    loadIssues();
  }, [batch, limit, offset, severity, blocking, issueCode]);

  if (!batch) {
    return (
      <EmptyState
        title="No Active Inventory Batch"
        message="Upload a CSV or JSON file to view data quality findings."
        actionText="Upload Inventory"
        onAction={onNavigateUpload}
      />
    );
  }

  const s = batch.summary;
  const currentPageNum = Math.floor(offset / limit) + 1;
  const totalPages = Math.ceil(total / limit) || 1;

  return (
    <div>
      {/* KPI Counters */}
      <div className="stats-grid">
        <StatCard
          title="Clean / Valid Rows"
          value={s.valid_rows}
          subtext="Zero validation issues"
          icon={<CheckCircle2 size={20} />}
          highlightColor="#10b981"
        />
        <StatCard
          title="Rows with Warnings"
          value={s.warning_rows}
          subtext={`${s.warning_count} non-blocking issues`}
          icon={<AlertTriangle size={20} />}
          highlightColor="#eab308"
        />
        <StatCard
          title="Blocked Rows"
          value={s.blocked_rows}
          subtext={`${s.error_count} blocking errors`}
          icon={<ShieldAlert size={20} />}
          highlightColor="#ef4444"
        />
        <StatCard
          title="Total Validation Findings"
          value={s.error_count + s.warning_count}
          subtext="Detected across inventory"
          icon={<FileCheck size={20} />}
        />
      </div>

      {/* Issues Table */}
      <div className="card-table-wrapper">
        <div className="table-toolbar">
          <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
            <ShieldAlert size={18} color="#ef4444" />
            <h3 style={{ fontSize: '1rem', fontWeight: 600 }}>Validation Findings Log</h3>
          </div>

          <div className="filter-group">
            <select
              className="filter-select"
              value={severity}
              onChange={(e) => setSeverity(e.target.value)}
            >
              <option value="">All Severities</option>
              <option value="error">Error (Blocking)</option>
              <option value="warning">Warning (Non-Blocking)</option>
              <option value="info">Info</option>
            </select>

            <select
              className="filter-select"
              value={blocking}
              onChange={(e) => setBlocking(e.target.value)}
            >
              <option value="all">All Impact Levels</option>
              <option value="true">Blocking Only</option>
              <option value="false">Non-Blocking Only</option>
            </select>

            <input
              type="text"
              className="search-input"
              style={{ width: '200px', paddingLeft: '0.75rem' }}
              placeholder="Filter by issue code..."
              value={issueCode}
              onChange={(e) => setIssueCode(e.target.value)}
            />
          </div>
        </div>

        {loading ? (
          <LoadingSkeleton message="Loading validation issues..." />
        ) : error ? (
          <ErrorState error={error} onRetry={loadIssues} />
        ) : issues.length === 0 ? (
          <EmptyState
            icon={<CheckCircle2 size={48} color="#10b981" />}
            title="No Validation Issues Detected"
            message={
              s.error_count === 0 && s.warning_count === 0
                ? "This inventory batch passed 100% of data quality checks with 0 errors and 0 warnings!"
                : "No issues match the active filter criteria."
            }
          />
        ) : (
          <div style={{ overflowX: 'auto' }}>
            <table className="data-table">
              <thead>
                <tr>
                  <th>Row</th>
                  <th>Asset ID</th>
                  <th>Field</th>
                  <th>Issue Code</th>
                  <th>Severity</th>
                  <th>Blocking?</th>
                  <th>Observed Value</th>
                  <th>Validation Message</th>
                  <th>Remediation Action</th>
                </tr>
              </thead>
              <tbody>
                {issues.map((issue) => (
                  <tr key={issue.id} style={{ cursor: 'default' }}>
                    <td style={{ color: 'var(--text-muted)' }}>{issue.row_number}</td>
                    <td className="mono" style={{ fontWeight: 600 }}>
                      {issue.asset_id || '—'}
                    </td>
                    <td className="mono" style={{ color: 'var(--primary)' }}>{issue.field_name}</td>
                    <td className="mono" style={{ fontWeight: 600 }}>{issue.issue_code}</td>
                    <td>
                      <StatusBadge status={issue.severity} />
                    </td>
                    <td>
                      {issue.blocking ? (
                        <span style={{ color: '#b91c1c', fontWeight: 600, fontSize: '0.8125rem' }}>
                          Yes (Excluded)
                        </span>
                      ) : (
                        <span style={{ color: '#047857', fontSize: '0.8125rem' }}>
                          No (Scored)
                        </span>
                      )}
                    </td>
                    <td className="mono" style={{ maxWidth: '160px', overflow: 'hidden', textOverflow: 'ellipsis' }}>
                      {issue.observed_value !== null && issue.observed_value !== '' ? (
                        issue.observed_value
                      ) : (
                        <span style={{ color: 'var(--text-muted)', fontStyle: 'italic' }}>&lt;empty&gt;</span>
                      )}
                    </td>
                    <td style={{ maxWidth: '280px' }}>{issue.message}</td>
                    <td style={{ maxWidth: '240px', color: 'var(--text-muted)' }}>{issue.suggested_action}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}

        <div className="table-pagination">
          <div>
            Showing {total === 0 ? 0 : offset + 1} to {Math.min(offset + limit, total)} of {total.toLocaleString()} issues
          </div>

          <div className="pagination-controls">
            <select
              className="filter-select"
              value={limit}
              onChange={(e) => setLimit(Number(e.target.value))}
            >
              <option value={25}>25 per page</option>
              <option value={50}>50 per page</option>
              <option value={100}>100 per page</option>
            </select>

            <button
              className="btn btn-secondary btn-sm"
              disabled={offset === 0}
              onClick={() => setOffset(Math.max(0, offset - limit))}
            >
              <ChevronLeft size={14} />
            </button>
            <span style={{ padding: '0 0.5rem', fontWeight: 500 }}>
              Page {currentPageNum} of {totalPages}
            </span>
            <button
              className="btn btn-secondary btn-sm"
              disabled={offset + limit >= total}
              onClick={() => setOffset(offset + limit)}
            >
              <ChevronRight size={14} />
            </button>
          </div>
        </div>
      </div>
    </div>
  );
};
