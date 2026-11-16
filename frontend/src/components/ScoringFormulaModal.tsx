import React from 'react';
import { X, ShieldCheck } from 'lucide-react';

interface ScoringFormulaModalProps {
  isOpen: boolean;
  onClose: () => void;
}

export const ScoringFormulaModal: React.FC<ScoringFormulaModalProps> = ({ isOpen, onClose }) => {
  if (!isOpen) return null;

  return (
    <div className="drawer-overlay" onClick={onClose}>
      <div
        className="drawer"
        style={{ width: '640px' }}
        onClick={(e) => e.stopPropagation()}
      >
        <div className="drawer-header">
          <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
            <ShieldCheck size={20} color="#0284c7" />
            <h2 style={{ fontSize: '1.125rem', fontWeight: 600 }}>SentinelOps Risk Scoring Methodology</h2>
          </div>
          <button className="btn btn-secondary btn-sm" onClick={onClose}>
            <X size={16} />
          </button>
        </div>

        <div className="drawer-body">
          <div className="drawer-section">
            <span className="section-title">Core Formula</span>
            <div
              style={{
                backgroundColor: 'var(--bg-subtle)',
                padding: '1rem',
                borderRadius: 'var(--radius-md)',
                fontFamily: 'JetBrains Mono, monospace',
                fontSize: '0.9rem',
                border: '1px solid var(--border-color)',
              }}
            >
              Risk Score = (0.50 × Vulnerability Score) + (0.30 × Criticality Score) + (0.20 × Ownership Risk Score)
            </div>
            <p style={{ fontSize: '0.8125rem', color: 'var(--text-muted)' }}>
              Deterministic, reproducible rule-based formula. Risk scores range from 0 to 100.
            </p>
          </div>

          <div className="drawer-section">
            <span className="section-title">Component 1: Vulnerability Severity (50% Weight)</span>
            <div className="key-value-grid">
              <span className="kv-key">Critical:</span><span className="kv-val">100 points</span>
              <span className="kv-key">High:</span><span className="kv-val">75 points</span>
              <span className="kv-key">Medium:</span><span className="kv-val">50 points</span>
              <span className="kv-key">Low:</span><span className="kv-val">25 points</span>
              <span className="kv-key">Informational / None:</span><span className="kv-val">0 points</span>
            </div>
          </div>

          <div className="drawer-section">
            <span className="section-title">Component 2: Asset Criticality (30% Weight)</span>
            <div className="key-value-grid">
              <span className="kv-key">Critical:</span><span className="kv-val">100 points</span>
              <span className="kv-key">High:</span><span className="kv-val">75 points</span>
              <span className="kv-key">Medium:</span><span className="kv-val">50 points</span>
              <span className="kv-key">Low:</span><span className="kv-val">25 points</span>
            </div>
          </div>

          <div className="drawer-section">
            <span className="section-title">Component 3: Asset Ownership (20% Weight)</span>
            <div className="key-value-grid">
              <span className="kv-key">Owner Assigned:</span><span className="kv-val">0 points (no penalty)</span>
              <span className="kv-key">Owner Missing:</span><span className="kv-val">100 points (+20 to final score)</span>
            </div>
            <p style={{ fontSize: '0.8125rem', color: 'var(--text-muted)' }}>
              Missing owner is a non-blocking warning. Ownerless assets remain visible and eligible for scoring with an ownership penalty.
            </p>
          </div>

          <div className="drawer-section">
            <span className="section-title">Project Risk Level Thresholds</span>
            <div className="key-value-grid">
              <span className="kv-key">Critical:</span><span className="kv-val" style={{ color: '#b91c1c', fontWeight: 600 }}>80.0 – 100.0</span>
              <span className="kv-key">High:</span><span className="kv-val" style={{ color: '#c2410c', fontWeight: 600 }}>60.0 – 79.99</span>
              <span className="kv-key">Medium:</span><span className="kv-val" style={{ color: '#854d0e', fontWeight: 600 }}>30.0 – 59.99</span>
              <span className="kv-key">Low:</span><span className="kv-val" style={{ color: '#047857', fontWeight: 600 }}>0.0 – 29.99</span>
            </div>
          </div>

          <div className="drawer-section">
            <span className="section-title">Eligibility Criteria</span>
            <ul style={{ fontSize: '0.8125rem', color: 'var(--text-muted)', paddingLeft: '1.25rem', display: 'flex', flexDirection: 'column', gap: '0.4rem' }}>
              <li>Records with <strong>blocking errors</strong> (e.g., missing ID, duplicate ID, invalid IP) do <strong>not</strong> receive a risk score.</li>
              <li>Records with only <strong>warnings</strong> (missing owner, non-ISO date) are fully scored.</li>
              <li>Calculations are continuous full precision and rounded to 2 decimal places for display.</li>
            </ul>
          </div>
        </div>
      </div>
    </div>
  );
};
