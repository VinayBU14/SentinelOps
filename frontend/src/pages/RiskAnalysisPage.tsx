import React, { useEffect, useState } from 'react';
import { ImportBatch } from '../types/batch';
import { Asset } from '../types/asset';
import { RiskAssessment } from '../types/risk';
import { api } from '../services/api';
import { StatCard } from '../components/StatCard';
import { RiskBadge } from '../components/RiskBadge';
import { LoadingSkeleton, EmptyState, ErrorState } from '../components/EmptyState';
import {
  Flame,
  PlayCircle,
  Search,
  ChevronLeft,
  ChevronRight,
  HelpCircle,
} from 'lucide-react';

interface RiskAnalysisPageProps {
  batch: ImportBatch | null;
  onSelectAsset: (asset: Asset) => void;
  onOpenFormula: () => void;
  onRefresh: () => void;
  onNavigateUpload: () => void;
}

export const RiskAnalysisPage: React.FC<RiskAnalysisPageProps> = ({
  batch,
  onSelectAsset,
  onOpenFormula,
  onRefresh,
  onNavigateUpload,
}) => {
  const [risks, setRisks] = useState<RiskAssessment[]>([]);
  const [total, setTotal] = useState(0);
  const [loading, setLoading] = useState(false);
  const [analyzing, setAnalyzing] = useState(false);
  const [error, setError] = useState<string | null>(null);

  // Distribution counters
  const [counts, setCounts] = useState<{ critical: number; high: number; medium: number; low: number }>({
    critical: 0,
    high: 0,
    medium: 0,
    low: 0,
  });

  // Filters & Pagination
  const [limit, setLimit] = useState(50);
  const [offset, setOffset] = useState(0);
  const [riskLevel, setRiskLevel] = useState('');
  const [assetType, setAssetType] = useState('');
  const [criticality, setCriticality] = useState('');
  const [ownerMissing, setOwnerMissing] = useState('all');
  const [search, setSearch] = useState('');

  const loadRisks = () => {
    if (!batch) return;
    if (batch.status !== 'analyzed') {
      setRisks([]);
      setTotal(0);
      return;
    }

    setLoading(true);
    setError(null);

    const ownerMissingParam =
      ownerMissing === 'true' ? true : ownerMissing === 'false' ? false : undefined;

    Promise.all([
      api.getRankedRisks(batch.id, {
        limit,
        offset,
        risk_level: riskLevel || undefined,
        asset_type: assetType || undefined,
        criticality: criticality || undefined,
        owner_missing: ownerMissingParam,
        search: search.trim() || undefined,
      }),
      // Fetch distribution totals
      Promise.all([
        api.getRankedRisks(batch.id, { risk_level: 'Critical', limit: 1 }),
        api.getRankedRisks(batch.id, { risk_level: 'High', limit: 1 }),
        api.getRankedRisks(batch.id, { risk_level: 'Medium', limit: 1 }),
        api.getRankedRisks(batch.id, { risk_level: 'Low', limit: 1 }),
      ]),
    ])
      .then(([risksRes, [c, h, m, l]]) => {
        setRisks(risksRes.items);
        setTotal(risksRes.total);
        setCounts({
          critical: c.total,
          high: h.total,
          medium: m.total,
          low: l.total,
        });
        setLoading(false);
      })
      .catch((err) => {
        setError(err.message || 'Failed to fetch risk assessments');
        setLoading(false);
      });
  };

  useEffect(() => {
    setOffset(0);
  }, [riskLevel, assetType, criticality, ownerMissing, search, limit]);

  useEffect(() => {
    loadRisks();
  }, [batch, limit, offset, riskLevel, assetType, criticality, ownerMissing, search]);

  const handleRunAnalysis = async () => {
    if (!batch) return;
    try {
      setAnalyzing(true);
      await api.analyzeBatch(batch.id);
      onRefresh();
    } catch (err: any) {
      alert(`Analysis failed: ${err.message}`);
    } finally {
      setAnalyzing(false);
    }
  };

  if (!batch) {
    return (
      <EmptyState
        title="No Active Inventory Batch"
        message="Upload an asset inventory file to calculate and prioritize risk."
        actionText="Upload Inventory"
        onAction={onNavigateUpload}
      />
    );
  }

  const currentPageNum = Math.floor(offset / limit) + 1;
  const totalPages = Math.ceil(total / limit) || 1;

  return (
    <div>
      {/* Top Banner / Trigger Analysis */}
      <div
        style={{
          backgroundColor: 'var(--bg-surface)',
          border: '1px solid var(--border-color)',
          borderRadius: 'var(--radius-lg)',
          padding: '1.25rem 1.5rem',
          marginBottom: '1.5rem',
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'space-between',
          flexWrap: 'wrap',
          gap: '1rem',
          boxShadow: 'var(--shadow-sm)',
        }}
      >
        <div>
          <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
            <Flame size={20} color={batch.status === 'analyzed' ? '#f97316' : '#94a3b8'} />
            <h2 style={{ fontSize: '1.125rem', fontWeight: 700 }}>Explainable Risk Scoring Engine</h2>
          </div>
          <p style={{ fontSize: '0.8125rem', color: 'var(--text-muted)', marginTop: '0.25rem' }}>
            Formula: Risk = (0.50 × Vuln) + (0.30 × Crit) + (0.20 × Owner). Continuous full precision calculation.
          </p>
        </div>

        <div style={{ display: 'flex', alignItems: 'center', gap: '0.75rem' }}>
          <button className="btn btn-secondary btn-sm" onClick={onOpenFormula}>
            <HelpCircle size={15} />
            <span>How Scoring Works</span>
          </button>
          <button
            className="btn btn-primary"
            onClick={handleRunAnalysis}
            disabled={analyzing}
          >
            <PlayCircle size={16} />
            <span>{analyzing ? 'Calculating Scores...' : batch.status === 'analyzed' ? 'Recalculate Risk Scores' : 'Run Risk Analysis'}</span>
          </button>
        </div>
      </div>

      {batch.status !== 'analyzed' ? (
        <EmptyState
          icon={<Flame size={48} color="#f97316" />}
          title="Batch Not Yet Analyzed"
          message="Run risk analysis to calculate deterministic scores for eligible assets in this batch."
          actionText="Run Risk Analysis Now"
          onAction={handleRunAnalysis}
        />
      ) : (
        <>
          {/* Risk Level Stat Cards */}
          <div className="stats-grid">
            <StatCard
              title="Critical Risk"
              value={counts.critical}
              subtext="Score 80.0 – 100.0"
              highlightColor="#ef4444"
            />
            <StatCard
              title="High Risk"
              value={counts.high}
              subtext="Score 60.0 – 79.99"
              highlightColor="#f97316"
            />
            <StatCard
              title="Medium Risk"
              value={counts.medium}
              subtext="Score 30.0 – 59.99"
              highlightColor="#eab308"
            />
            <StatCard
              title="Low Risk"
              value={counts.low}
              subtext="Score 0.0 – 29.99"
              highlightColor="#10b981"
            />
          </div>

          {/* Ranked Risks Table Card */}
          <div className="card-table-wrapper">
            <div className="table-toolbar">
              <div className="search-input-wrapper">
                <Search size={16} className="search-icon" />
                <input
                  type="text"
                  className="search-input"
                  placeholder="Search asset ID, hostname, IP..."
                  value={search}
                  onChange={(e) => setSearch(e.target.value)}
                />
              </div>

              <div className="filter-group">
                <select
                  className="filter-select"
                  value={riskLevel}
                  onChange={(e) => setRiskLevel(e.target.value)}
                >
                  <option value="">All Risk Levels</option>
                  <option value="Critical">Critical (80–100)</option>
                  <option value="High">High (60–79.99)</option>
                  <option value="Medium">Medium (30–59.99)</option>
                  <option value="Low">Low (0–29.99)</option>
                </select>

                <select
                  className="filter-select"
                  value={assetType}
                  onChange={(e) => setAssetType(e.target.value)}
                >
                  <option value="">All Types</option>
                  <option value="Workstation">Workstation</option>
                  <option value="Server">Server</option>
                  <option value="Network Device">Network Device</option>
                  <option value="Database">Database</option>
                  <option value="Application">Application</option>
                  <option value="Cloud Asset">Cloud Asset</option>
                  <option value="IoT Device">IoT Device</option>
                </select>

                <select
                  className="filter-select"
                  value={criticality}
                  onChange={(e) => setCriticality(e.target.value)}
                >
                  <option value="">All Criticalities</option>
                  <option value="Critical">Critical</option>
                  <option value="High">High</option>
                  <option value="Medium">Medium</option>
                  <option value="Low">Low</option>
                </select>

                <select
                  className="filter-select"
                  value={ownerMissing}
                  onChange={(e) => setOwnerMissing(e.target.value)}
                >
                  <option value="all">All Ownership</option>
                  <option value="true">Owner Missing (+20 penalty)</option>
                  <option value="false">Owner Assigned</option>
                </select>
              </div>
            </div>

            {loading ? (
              <LoadingSkeleton message="Ranking assets by risk score..." />
            ) : error ? (
              <ErrorState error={error} onRetry={loadRisks} />
            ) : risks.length === 0 ? (
              <EmptyState
                title="No Matching Risk Records"
                message="No scored assets match the selected risk filters."
              />
            ) : (
              <div style={{ overflowX: 'auto' }}>
                <table className="data-table">
                  <thead>
                    <tr>
                      <th>Rank</th>
                      <th>Asset ID</th>
                      <th>Hostname</th>
                      <th>Type</th>
                      <th>Vuln Input</th>
                      <th>Crit Input</th>
                      <th>Owner Input</th>
                      <th>Final Risk Score</th>
                      <th>Risk Level</th>
                      <th>Explanation Summary</th>
                    </tr>
                  </thead>
                  <tbody>
                    {risks.map((r, idx) => {
                      const a = r.asset;
                      if (!a) return null;
                      const globalRank = offset + idx + 1;
                      return (
                        <tr key={r.id} onClick={() => onSelectAsset(a)}>
                          <td style={{ fontWeight: 600, color: 'var(--text-muted)' }}>
                            #{globalRank}
                          </td>
                          <td className="mono" style={{ fontWeight: 600 }}>{a.asset_id}</td>
                          <td className="mono">{a.hostname}</td>
                          <td>{a.asset_type}</td>
                          <td>
                            {a.vulnerability_severity} ({r.vulnerability_score} pts)
                          </td>
                          <td>
                            {a.criticality} ({r.criticality_score} pts)
                          </td>
                          <td>
                            {r.ownership_score === 100 ? (
                              <span style={{ color: '#ef4444', fontWeight: 600, fontSize: '0.8125rem' }}>
                                Missing (100 pts)
                              </span>
                            ) : (
                              <span style={{ color: 'var(--text-muted)', fontSize: '0.8125rem' }}>
                                Present (0 pts)
                              </span>
                            )}
                          </td>
                          <td className="mono" style={{ fontWeight: 700, fontSize: '0.9375rem' }}>
                            {r.risk_score.toFixed(1)}
                          </td>
                          <td>
                            <RiskBadge level={r.risk_level} />
                          </td>
                          <td
                            style={{
                              maxWidth: '240px',
                              overflow: 'hidden',
                              textOverflow: 'ellipsis',
                              whiteSpace: 'nowrap',
                              fontSize: '0.8125rem',
                              color: 'var(--text-muted)',
                            }}
                          >
                            {r.explanation}
                          </td>
                        </tr>
                      );
                    })}
                  </tbody>
                </table>
              </div>
            )}

            <div className="table-pagination">
              <div>
                Showing {total === 0 ? 0 : offset + 1} to {Math.min(offset + limit, total)} of {total.toLocaleString()} scored assets
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
        </>
      )}
    </div>
  );
};
