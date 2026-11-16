import React, { useEffect, useState } from 'react';
import { Asset } from '../types/asset';
import { AssetRiskDetail } from '../types/risk';
import { ValidationIssue } from '../types/issue';
import { api } from '../services/api';
import { RiskBadge } from './RiskBadge';
import { StatusBadge } from './StatusBadge';
import { X } from 'lucide-react';

interface AssetDetailDrawerProps {
  asset: Asset | null;
  batchId: string;
  onClose: () => void;
}

export const AssetDetailDrawer: React.FC<AssetDetailDrawerProps> = ({
  asset,
  batchId,
  onClose,
}) => {
  const [riskDetail, setRiskDetail] = useState<AssetRiskDetail | null>(null);
  const [issues, setIssues] = useState<ValidationIssue[]>([]);

  useEffect(() => {
    if (!asset) return;

    let mounted = true;

    Promise.all([
      api.getAssetRiskDetail(batchId, asset.id).catch(() => null),
      api.getIssues(batchId, { limit: 100 }).catch(() => ({ items: [] })),
    ]).then(([detail, issuesRes]) => {
      if (!mounted) return;
      if (detail) setRiskDetail(detail);
      if (issuesRes && issuesRes.items) {
        // Filter issues matching this asset ID or row number
        const assetIssues = issuesRes.items.filter(
          (i) => i.asset_record_id === asset.id || i.row_number === asset.source_row_number
        );
        setIssues(assetIssues);
      }
    });

    return () => {
      mounted = false;
    };
  }, [asset, batchId]);

  if (!asset) return null;

  const r = riskDetail?.risk_assessment;

  return (
    <div className="drawer-overlay" onClick={onClose}>
      <div className="drawer" onClick={(e) => e.stopPropagation()}>
        <div className="drawer-header">
          <div>
            <div style={{ display: 'flex', alignItems: 'center', gap: '0.75rem' }}>
              <h2 style={{ fontSize: '1.25rem', fontWeight: 700 }} className="mono">
                {asset.asset_id || 'UNKNOWN ID'}
              </h2>
              <StatusBadge status={asset.validation_status} />
              {asset.risk_level && <RiskBadge level={asset.risk_level} score={asset.risk_score} showScore />}
            </div>
            <div style={{ fontSize: '0.8125rem', color: 'var(--text-muted)', marginTop: '0.2rem' }}>
              Row {asset.source_row_number} • Hostname: {asset.hostname || 'None'}
            </div>
          </div>
          <button className="btn btn-secondary btn-sm" onClick={onClose}>
            <X size={16} />
          </button>
        </div>

        <div className="drawer-body">
          {/* Explainable Risk Assessment */}
          <div className="drawer-section">
            <span className="section-title">Risk Scoring & Breakdown</span>
            {r ? (
              <div
                style={{
                  backgroundColor: 'var(--bg-subtle)',
                  padding: '1rem',
                  borderRadius: 'var(--radius-md)',
                  border: '1px solid var(--border-color)',
                  display: 'flex',
                  flexDirection: 'column',
                  gap: '0.75rem',
                }}
              >
                <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                  <span style={{ fontWeight: 600 }}>Total Weighted Risk Score</span>
                  <span style={{ fontSize: '1.5rem', fontWeight: 700 }} className="mono">
                    {r.risk_score.toFixed(1)} / 100
                  </span>
                </div>

                <div className="key-value-grid">
                  <span className="kv-key">Vulnerability (50%):</span>
                  <span className="kv-val">
                    {asset.vulnerability_severity} ({r.vulnerability_score} pts × 0.50 = {(r.vulnerability_score * 0.50).toFixed(1)} pts)
                  </span>

                  <span className="kv-key">Criticality (30%):</span>
                  <span className="kv-val">
                    {asset.criticality} ({r.criticality_score} pts × 0.30 = {(r.criticality_score * 0.30).toFixed(1)} pts)
                  </span>

                  <span className="kv-key">Ownership (20%):</span>
                  <span className="kv-val">
                    {r.ownership_score === 100 ? 'Owner Missing (100 pts × 0.20 = 20.0 pts)' : 'Owner Assigned (0 pts × 0.20 = 0.0 pts)'}
                  </span>
                </div>

                <div
                  style={{
                    backgroundColor: 'var(--bg-surface)',
                    padding: '0.75rem',
                    borderRadius: 'var(--radius-sm)',
                    border: '1px solid var(--border-color)',
                    fontSize: '0.8125rem',
                    color: 'var(--text-main)',
                    lineHeight: 1.4,
                  }}
                >
                  <strong style={{ color: 'var(--primary)' }}>Explanation: </strong>
                  {r.explanation}
                </div>
              </div>
            ) : asset.validation_status === 'blocked' ? (
              <div style={{ color: '#b91c1c', fontSize: '0.875rem' }}>
                This asset has blocking validation errors and is excluded from risk scoring.
              </div>
            ) : (
              <div style={{ color: 'var(--text-muted)', fontSize: '0.875rem' }}>
                Batch not yet analyzed. Click "Run Risk Analysis" to calculate scores.
              </div>
            )}
          </div>

          {/* Validation Issues */}
          {issues.length > 0 && (
            <div className="drawer-section">
              <span className="section-title">Validation Findings ({issues.length})</span>
              <div style={{ display: 'flex', flexDirection: 'column', gap: '0.5rem' }}>
                {issues.map((issue) => (
                  <div
                    key={issue.id}
                    style={{
                      borderLeft: `3px solid ${issue.blocking ? '#ef4444' : '#eab308'}`,
                      backgroundColor: 'var(--bg-subtle)',
                      padding: '0.75rem',
                      borderRadius: 'var(--radius-sm)',
                      fontSize: '0.8125rem',
                    }}
                  >
                    <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: '0.25rem' }}>
                      <span className="mono" style={{ fontWeight: 600 }}>{issue.issue_code}</span>
                      <StatusBadge status={issue.severity} />
                    </div>
                    <div style={{ color: 'var(--text-main)' }}>{issue.message}</div>
                    <div style={{ color: 'var(--text-muted)', marginTop: '0.25rem' }}>
                      Action: {issue.suggested_action}
                    </div>
                  </div>
                ))}
              </div>
            </div>
          )}

          {/* Identity & Network */}
          <div className="drawer-section">
            <span className="section-title">Identity & Network Attributes</span>
            <div className="key-value-grid">
              <span className="kv-key">Asset ID:</span>
              <span className="kv-val mono">{asset.asset_id || '—'}</span>

              <span className="kv-key">Hostname:</span>
              <span className="kv-val mono">{asset.hostname || '—'}</span>

              <span className="kv-key">IP Address:</span>
              <span className="kv-val mono">{asset.ip_address || '—'}</span>

              <span className="kv-key">Asset Type:</span>
              <span className="kv-val">{asset.asset_type || '—'}</span>

              <span className="kv-key">Sub Category:</span>
              <span className="kv-val">{asset.sub_category || '—'}</span>

              <span className="kv-key">OS / Version:</span>
              <span className="kv-val">{asset.operating_system} {asset.os_version}</span>
            </div>
          </div>

          {/* Ownership & Governance */}
          <div className="drawer-section">
            <span className="section-title">Ownership & Organization</span>
            <div className="key-value-grid">
              <span className="kv-key">Owner Name:</span>
              <span className="kv-val" style={!asset.owner_name ? { color: '#ef4444', fontWeight: 600 } : {}}>
                {asset.owner_name || 'UNASSIGNED (Warning)'}
              </span>

              <span className="kv-key">Owner Email:</span>
              <span className="kv-val">{asset.owner_email || '—'}</span>

              <span className="kv-key">Department:</span>
              <span className="kv-val">{asset.department || '—'}</span>

              <span className="kv-key">Organization:</span>
              <span className="kv-val">{asset.organization || '—'}</span>

              <span className="kv-key">Data Source:</span>
              <span className="kv-val">{asset.data_source || '—'}</span>
            </div>
          </div>

          {/* Contextual & Lifecycle Fields */}
          <div className="drawer-section">
            <span className="section-title">Environment & Security Controls</span>
            <div className="key-value-grid">
              <span className="kv-key">Environment:</span>
              <span className="kv-val">{asset.environment || '—'}</span>

              <span className="kv-key">Data Classification:</span>
              <span className="kv-val">{asset.data_classification || '—'}</span>

              <span className="kv-key">Location:</span>
              <span className="kv-val">{asset.location || '—'}</span>

              <span className="kv-key">Lifecycle Status:</span>
              <span className="kv-val">{asset.lifecycle_status || '—'}</span>

              <span className="kv-key">Internet Facing:</span>
              <span className="kv-val">{asset.internet_facing || '—'}</span>

              <span className="kv-key">Backup Enabled:</span>
              <span className="kv-val">{asset.backup_enabled || '—'}</span>

              <span className="kv-key">EDR Enabled:</span>
              <span className="kv-val">{asset.edr_enabled || '—'}</span>

              <span className="kv-key">Simulated Vuln Count:</span>
              <span className="kv-val">{asset.vulnerability_count ?? '—'}</span>

              <span className="kv-key">Purchase Date:</span>
              <span className="kv-val">{asset.purchase_date || '—'}</span>

              <span className="kv-key">Last Updated:</span>
              <span className="kv-val">{asset.last_updated || '—'}</span>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};
