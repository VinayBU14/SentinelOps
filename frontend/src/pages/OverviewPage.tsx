import React, { useEffect, useState } from 'react';
import { ImportBatch } from '../types/batch';
import { Asset } from '../types/asset';
import { RiskAssessment } from '../types/risk';
import { api } from '../services/api';
import { StatCard } from '../components/StatCard';
import { RiskBadge } from '../components/RiskBadge';
import { StatusBadge } from '../components/StatusBadge';
import { LoadingSkeleton, EmptyState, ErrorState } from '../components/EmptyState';
import { PageId } from '../components/Sidebar';
import {
  Server,
  ShieldAlert,
  Flame,
  CheckCircle2,
  AlertTriangle,
  PlayCircle,
  ArrowRight,
  TrendingUp,
} from 'lucide-react';
import {
  BarChart,
  Bar,
  XAxis,
  YAxis,
  Tooltip,
  ResponsiveContainer,
  Cell,
} from 'recharts';

interface OverviewPageProps {
  batch: ImportBatch | null;
  onNavigate: (page: PageId) => void;
  onSelectAsset: (asset: Asset) => void;
  onRefresh: () => void;
}

export const OverviewPage: React.FC<OverviewPageProps> = ({
  batch,
  onNavigate,
  onSelectAsset,
  onRefresh,
}) => {
  const [topRisks, setTopRisks] = useState<RiskAssessment[]>([]);
  const [categoryCounts, setCategoryCounts] = useState<{ name: string; count: number }[]>([]);
  const [riskDistribution, setRiskDistribution] = useState<{ name: string; count: number; color: string }[]>([]);
  const [ownerlessCount, setOwnerlessCount] = useState<number>(0);
  const [analyzing, setAnalyzing] = useState(false);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    if (!batch) return;

    let mounted = true;
    setLoading(true);
    setError(null);

    const batchId = batch.id;

    // Load Category breakdown, top risks, and risk distribution
    Promise.all([
      api.getAssets(batchId, { limit: 200 }).catch(() => ({ items: [], total: 0 })),
      api.getAssets(batchId, { owner_missing: true, limit: 1 }).catch(() => ({ total: 0 })),
      batch.status === 'analyzed'
        ? api.getRankedRisks(batchId, { limit: 10 }).catch(() => ({ items: [] }))
        : Promise.resolve({ items: [] }),
    ])
      .then(([assetsRes, ownerlessRes, risksRes]) => {
        if (!mounted) return;

        // Group categories from loaded assets
        const counts: Record<string, number> = {};
        for (const a of assetsRes.items) {
          const type = a.asset_type || 'Unknown';
          counts[type] = (counts[type] || 0) + 1;
        }
        const catArray = Object.entries(counts)
          .map(([name, count]) => ({ name, count }))
          .sort((a, b) => b.count - a.count);
        setCategoryCounts(catArray);

        setOwnerlessCount(ownerlessRes.total || 0);
        setTopRisks(risksRes.items || []);

        if (batch.status === 'analyzed') {
          // Fetch risk level distribution
          Promise.all([
            api.getRankedRisks(batchId, { risk_level: 'Critical', limit: 1 }),
            api.getRankedRisks(batchId, { risk_level: 'High', limit: 1 }),
            api.getRankedRisks(batchId, { risk_level: 'Medium', limit: 1 }),
            api.getRankedRisks(batchId, { risk_level: 'Low', limit: 1 }),
          ]).then(([c, h, m, l]) => {
            if (!mounted) return;
            setRiskDistribution([
              { name: 'Critical', count: c.total, color: '#ef4444' },
              { name: 'High', count: h.total, color: '#f97316' },
              { name: 'Medium', count: m.total, color: '#eab308' },
              { name: 'Low', count: l.total, color: '#10b981' },
            ]);
          });
        }

        setLoading(false);
      })
      .catch((err) => {
        if (mounted) {
          setError(err.message || 'Failed to load overview data');
          setLoading(false);
        }
      });

    return () => {
      mounted = false;
    };
  }, [batch]);

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
        message="Upload a cyber asset inventory file (CSV or JSON) to inspect data quality and calculate explainable risk scores."
        actionText="Upload Inventory"
        onAction={() => onNavigate('upload')}
      />
    );
  }

  if (loading) return <LoadingSkeleton message="Compiling batch metrics..." />;
  if (error) return <ErrorState error={error} onRetry={onRefresh} />;

  const s = batch.summary;
  const eligibleRecords = s.total_rows - s.blocked_rows;

  return (
    <div>
      {/* Batch Header Banner */}
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
          boxShadow: 'var(--shadow-sm)',
        }}
      >
        <div>
          <div style={{ display: 'flex', alignItems: 'center', gap: '0.75rem' }}>
            <h2 style={{ fontSize: '1.125rem', fontWeight: 700 }}>{batch.original_filename}</h2>
            <StatusBadge status={batch.status} />
          </div>
          <div style={{ fontSize: '0.8125rem', color: 'var(--text-muted)', marginTop: '0.25rem' }}>
            Uploaded {new Date(batch.uploaded_at).toLocaleString()} • {batch.file_type.toUpperCase()} format • {batch.summary.total_rows} total parsed records
          </div>
        </div>

        {batch.status !== 'analyzed' ? (
          <button
            className="btn btn-primary"
            onClick={handleRunAnalysis}
            disabled={analyzing}
          >
            <PlayCircle size={16} />
            <span>{analyzing ? 'Analyzing Batch...' : 'Calculate Risk Scores'}</span>
          </button>
        ) : (
          <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem', color: '#047857', fontSize: '0.875rem', fontWeight: 600 }}>
            <CheckCircle2 size={18} />
            <span>Risk Scores Up-To-Date</span>
          </div>
        )}
      </div>

      {/* KPI Cards Grid */}
      <div className="stats-grid">
        <StatCard
          title="Total Parsed Assets"
          value={s.total_rows.toLocaleString()}
          subtext={`${s.blank_rows} blank rows skipped`}
          icon={<Server size={20} />}
        />
        <StatCard
          title="Eligible For Scoring"
          value={eligibleRecords.toLocaleString()}
          subtext="Valid & warning records"
          icon={<CheckCircle2 size={20} />}
          highlightColor="#10b981"
        />
        <StatCard
          title="Blocked Records"
          value={s.blocked_rows}
          subtext={`${s.error_count} blocking errors`}
          icon={<ShieldAlert size={20} />}
          highlightColor={s.blocked_rows > 0 ? '#ef4444' : undefined}
        />
        <StatCard
          title="Ownerless Assets"
          value={ownerlessCount}
          subtext="Assessed with +20 penalty"
          icon={<AlertTriangle size={20} />}
          highlightColor={ownerlessCount > 0 ? '#eab308' : undefined}
        />
      </div>

      {/* Visualizations Section */}
      <div className="charts-grid">
        {/* Risk Distribution Chart */}
        <div className="chart-card">
          <div className="chart-title">Risk Level Breakdown</div>
          {batch.status === 'analyzed' && riskDistribution.length > 0 ? (
            <div style={{ height: 240 }}>
              <ResponsiveContainer width="100%" height="100%">
                <BarChart data={riskDistribution}>
                  <XAxis dataKey="name" stroke="#64748b" fontSize={12} />
                  <YAxis stroke="#64748b" fontSize={12} />
                  <Tooltip />
                  <Bar dataKey="count" radius={[4, 4, 0, 0]}>
                    {riskDistribution.map((entry, index) => (
                      <Cell key={`cell-${index}`} fill={entry.color} />
                    ))}
                  </Bar>
                </BarChart>
              </ResponsiveContainer>
            </div>
          ) : (
            <div
              style={{
                height: 240,
                display: 'flex',
                flexDirection: 'column',
                alignItems: 'center',
                justifyContent: 'center',
                color: 'var(--text-muted)',
                gap: '0.75rem',
                textAlign: 'center',
              }}
            >
              <Flame size={32} color="#94a3b8" />
              <p style={{ fontSize: '0.875rem' }}>Risk scores have not been generated yet.</p>
              <button className="btn btn-secondary btn-sm" onClick={handleRunAnalysis} disabled={analyzing}>
                Run Analysis Now
              </button>
            </div>
          )}
        </div>

        {/* Category Distribution Chart */}
        <div className="chart-card">
          <div className="chart-title">Asset Inventory by Type</div>
          {categoryCounts.length > 0 ? (
            <div style={{ height: 240 }}>
              <ResponsiveContainer width="100%" height="100%">
                <BarChart data={categoryCounts.slice(0, 6)} layout="vertical">
                  <XAxis type="number" stroke="#64748b" fontSize={12} />
                  <YAxis type="category" dataKey="name" stroke="#64748b" fontSize={11} width={90} />
                  <Tooltip />
                  <Bar dataKey="count" fill="#38bdf8" radius={[0, 4, 4, 0]} />
                </BarChart>
              </ResponsiveContainer>
            </div>
          ) : (
            <div style={{ height: 240, display: 'flex', alignItems: 'center', justifyContent: 'center' }}>
              No categories
            </div>
          )}
        </div>
      </div>

      {/* Top 10 Highest Risk Assets Table */}
      <div className="card-table-wrapper">
        <div className="table-toolbar">
          <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
            <TrendingUp size={18} color="#ef4444" />
            <h3 style={{ fontSize: '1rem', fontWeight: 600 }}>Top Highest-Risk Assets</h3>
          </div>
          <button className="btn btn-secondary btn-sm" onClick={() => onNavigate('risk-analysis')}>
            <span>View All Ranked Risks</span>
            <ArrowRight size={14} />
          </button>
        </div>

        {topRisks.length > 0 ? (
          <table className="data-table">
            <thead>
              <tr>
                <th>Rank</th>
                <th>Asset ID</th>
                <th>Hostname</th>
                <th>Type</th>
                <th>Criticality</th>
                <th>Vulnerability</th>
                <th>Owner</th>
                <th>Risk Score</th>
                <th>Level</th>
              </tr>
            </thead>
            <tbody>
              {topRisks.map((risk, idx) => {
                const a = risk.asset;
                if (!a) return null;
                return (
                  <tr key={risk.id} onClick={() => onSelectAsset(a)}>
                    <td style={{ fontWeight: 600, color: 'var(--text-muted)' }}>#{idx + 1}</td>
                    <td className="mono" style={{ fontWeight: 600 }}>{a.asset_id}</td>
                    <td className="mono">{a.hostname}</td>
                    <td>{a.asset_type}</td>
                    <td>{a.criticality}</td>
                    <td>{a.vulnerability_severity}</td>
                    <td>
                      {a.owner_name ? (
                        a.owner_name
                      ) : (
                        <span style={{ color: '#ef4444', fontStyle: 'italic', fontSize: '0.8125rem' }}>
                          Missing Owner
                        </span>
                      )}
                    </td>
                    <td className="mono" style={{ fontWeight: 700 }}>
                      {risk.risk_score.toFixed(1)}
                    </td>
                    <td>
                      <RiskBadge level={risk.risk_level} />
                    </td>
                  </tr>
                );
              })}
            </tbody>
          </table>
        ) : (
          <div style={{ padding: '2rem', textAlign: 'center', color: 'var(--text-muted)', fontSize: '0.875rem' }}>
            {batch.status === 'analyzed'
              ? 'No high-risk assets detected in this batch.'
              : 'Calculate risk scores to see the highest-risk assets.'}
          </div>
        )}
      </div>
    </div>
  );
};
