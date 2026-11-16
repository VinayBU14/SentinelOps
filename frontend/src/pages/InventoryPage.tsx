import React, { useEffect, useState } from 'react';
import { ImportBatch } from '../types/batch';
import { Asset } from '../types/asset';
import { api } from '../services/api';
import { RiskBadge } from '../components/RiskBadge';
import { StatusBadge } from '../components/StatusBadge';
import { LoadingSkeleton, EmptyState, ErrorState } from '../components/EmptyState';
import { Search, ChevronLeft, ChevronRight } from 'lucide-react';

interface InventoryPageProps {
  batch: ImportBatch | null;
  onSelectAsset: (asset: Asset) => void;
  onNavigateUpload: () => void;
}

export const InventoryPage: React.FC<InventoryPageProps> = ({
  batch,
  onSelectAsset,
  onNavigateUpload,
}) => {
  const [assets, setAssets] = useState<Asset[]>([]);
  const [total, setTotal] = useState(0);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  // Pagination & Filters State
  const [limit, setLimit] = useState(50);
  const [offset, setOffset] = useState(0);
  const [search, setSearch] = useState('');
  const [assetType, setAssetType] = useState('');
  const [criticality, setCriticality] = useState('');
  const [vulnerabilitySeverity, setVulnerabilitySeverity] = useState('');
  const [validationStatus, setValidationStatus] = useState('');
  const [ownerMissing, setOwnerMissing] = useState<string>('all');
  const [riskLevel, setRiskLevel] = useState('');

  const loadAssets = () => {
    if (!batch) return;
    setLoading(true);
    setError(null);

    const ownerMissingParam =
      ownerMissing === 'true' ? true : ownerMissing === 'false' ? false : undefined;

    api.getAssets(batch.id, {
      limit,
      offset,
      search: search.trim() || undefined,
      asset_type: assetType || undefined,
      criticality: criticality || undefined,
      vulnerability_severity: vulnerabilitySeverity || undefined,
      validation_status: validationStatus || undefined,
      owner_missing: ownerMissingParam,
      risk_level: riskLevel || undefined,
    })
      .then((res) => {
        setAssets(res.items);
        setTotal(res.total);
        setLoading(false);
      })
      .catch((err) => {
        setError(err.message || 'Failed to fetch inventory assets');
        setLoading(false);
      });
  };

  useEffect(() => {
    setOffset(0);
  }, [search, assetType, criticality, vulnerabilitySeverity, validationStatus, ownerMissing, riskLevel, limit]);

  useEffect(() => {
    loadAssets();
  }, [batch, limit, offset, search, assetType, criticality, vulnerabilitySeverity, validationStatus, ownerMissing, riskLevel]);

  if (!batch) {
    return (
      <EmptyState
        title="No Active Inventory Batch"
        message="Upload a CSV or JSON asset inventory to view asset records."
        actionText="Upload Inventory"
        onAction={onNavigateUpload}
      />
    );
  }

  const currentPageNum = Math.floor(offset / limit) + 1;
  const totalPages = Math.ceil(total / limit) || 1;

  return (
    <div>
      {/* Table & Filters Card */}
      <div className="card-table-wrapper">
        <div className="table-toolbar">
          <div className="search-input-wrapper">
            <Search size={16} className="search-icon" />
            <input
              type="text"
              className="search-input"
              placeholder="Search ID, hostname, IP..."
              value={search}
              onChange={(e) => setSearch(e.target.value)}
            />
          </div>

          <div className="filter-group">
            <select
              className="filter-select"
              value={assetType}
              onChange={(e) => setAssetType(e.target.value)}
            >
              <option value="">All Asset Types</option>
              <option value="Workstation">Workstation</option>
              <option value="Server">Server</option>
              <option value="Network Device">Network Device</option>
              <option value="Database">Database</option>
              <option value="Application">Application</option>
              <option value="Cloud Asset">Cloud Asset</option>
              <option value="IoT Device">IoT Device</option>
              <option value="Security Appliance">Security Appliance</option>
              <option value="Storage">Storage</option>
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
              value={vulnerabilitySeverity}
              onChange={(e) => setVulnerabilitySeverity(e.target.value)}
            >
              <option value="">All Severities</option>
              <option value="Critical">Critical</option>
              <option value="High">High</option>
              <option value="Medium">Medium</option>
              <option value="Low">Low</option>
              <option value="Informational">Informational</option>
              <option value="None">None</option>
            </select>

            <select
              className="filter-select"
              value={ownerMissing}
              onChange={(e) => setOwnerMissing(e.target.value)}
            >
              <option value="all">All Ownership</option>
              <option value="true">Owner Missing</option>
              <option value="false">Owner Assigned</option>
            </select>

            <select
              className="filter-select"
              value={validationStatus}
              onChange={(e) => setValidationStatus(e.target.value)}
            >
              <option value="">All Statuses</option>
              <option value="valid">Valid</option>
              <option value="warning">Warning</option>
              <option value="blocked">Blocked</option>
            </select>

            {batch.status === 'analyzed' && (
              <select
                className="filter-select"
                value={riskLevel}
                onChange={(e) => setRiskLevel(e.target.value)}
              >
                <option value="">All Risk Levels</option>
                <option value="Critical">Critical Risk</option>
                <option value="High">High Risk</option>
                <option value="Medium">Medium Risk</option>
                <option value="Low">Low Risk</option>
              </select>
            )}
          </div>
        </div>

        {/* Data Table */}
        {loading ? (
          <LoadingSkeleton message="Fetching asset inventory records..." />
        ) : error ? (
          <ErrorState error={error} onRetry={loadAssets} />
        ) : assets.length === 0 ? (
          <EmptyState
            title="No Matching Assets"
            message="No assets match the active search criteria or filters."
          />
        ) : (
          <div style={{ overflowX: 'auto' }}>
            <table className="data-table">
              <thead>
                <tr>
                  <th>Row</th>
                  <th>Asset ID</th>
                  <th>Hostname</th>
                  <th>IP Address</th>
                  <th>Type</th>
                  <th>Owner</th>
                  <th>Department</th>
                  <th>Criticality</th>
                  <th>Severity</th>
                  <th>Status</th>
                  <th>Risk Score</th>
                </tr>
              </thead>
              <tbody>
                {assets.map((asset) => (
                  <tr key={asset.id} onClick={() => onSelectAsset(asset)}>
                    <td style={{ color: 'var(--text-muted)' }}>{asset.source_row_number}</td>
                    <td className="mono" style={{ fontWeight: 600 }}>{asset.asset_id || '—'}</td>
                    <td className="mono">{asset.hostname || '—'}</td>
                    <td className="mono">{asset.ip_address || '—'}</td>
                    <td>{asset.asset_type || '—'}</td>
                    <td>
                      {asset.owner_name ? (
                        asset.owner_name
                      ) : (
                        <span style={{ color: '#ef4444', fontStyle: 'italic', fontSize: '0.8125rem' }}>
                          Missing
                        </span>
                      )}
                    </td>
                    <td>{asset.department || '—'}</td>
                    <td>{asset.criticality || '—'}</td>
                    <td>{asset.vulnerability_severity || '—'}</td>
                    <td>
                      <StatusBadge status={asset.validation_status} />
                    </td>
                    <td>
                      {asset.risk_level ? (
                        <RiskBadge level={asset.risk_level} score={asset.risk_score} showScore />
                      ) : (
                        <span style={{ color: 'var(--text-muted)', fontSize: '0.8125rem' }}>—</span>
                      )}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}

        {/* Pagination Bar */}
        <div className="table-pagination">
          <div>
            Showing {total === 0 ? 0 : offset + 1} to {Math.min(offset + limit, total)} of {total.toLocaleString()} assets
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
