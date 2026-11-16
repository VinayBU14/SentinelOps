import React, { useState, useRef } from 'react';
import { api } from '../services/api';
import { UploadResponse } from '../types/batch';
import { PageId } from '../components/Sidebar';
import {
  UploadCloud,
  AlertCircle,
  Download,
  CheckCircle2,
  ArrowRight,
} from 'lucide-react';

interface UploadPageProps {
  onUploadSuccess: (batchId: string) => void;
  onNavigate: (page: PageId) => void;
}

export const UploadPage: React.FC<UploadPageProps> = ({ onUploadSuccess, onNavigate }) => {
  const [dragActive, setDragActive] = useState(false);
  const [selectedFile, setSelectedFile] = useState<File | null>(null);
  const [uploading, setUploading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [result, setResult] = useState<UploadResponse | null>(null);
  const inputRef = useRef<HTMLInputElement>(null);

  const handleFiles = (files: FileList | null) => {
    if (!files || files.length === 0) return;
    const file = files[0];
    const lowerName = file.name.toLowerCase();
    if (!lowerName.endsWith('.csv') && !lowerName.endsWith('.json')) {
      setError('Please select a valid .csv or .json asset inventory file.');
      setSelectedFile(null);
      return;
    }
    setError(null);
    setSelectedFile(file);
    setResult(null);
  };

  const handleDrag = (e: React.DragEvent) => {
    e.preventDefault();
    e.stopPropagation();
    if (e.type === 'dragenter' || e.type === 'dragover') {
      setDragActive(true);
    } else if (e.type === 'dragleave') {
      setDragActive(false);
    }
  };

  const handleDrop = (e: React.DragEvent) => {
    e.preventDefault();
    e.stopPropagation();
    setDragActive(false);
    handleFiles(e.dataTransfer.files);
  };

  const handleUpload = async () => {
    if (!selectedFile) return;
    try {
      setUploading(true);
      setError(null);
      const res = await api.uploadFile(selectedFile);
      setResult(res);
      onUploadSuccess(res.batch_id);
    } catch (err: any) {
      setError(err.message || 'File upload failed');
    } finally {
      setUploading(false);
    }
  };

  return (
    <div style={{ maxWidth: '840px', margin: '0 auto' }}>
      {/* Upload Box Card */}
      <div
        style={{
          backgroundColor: 'var(--bg-surface)',
          border: '1px solid var(--border-color)',
          borderRadius: 'var(--radius-lg)',
          padding: '2rem',
          boxShadow: 'var(--shadow-sm)',
          marginBottom: '2rem',
        }}
      >
        <div style={{ marginBottom: '1.5rem', textAlign: 'center' }}>
          <h2 style={{ fontSize: '1.25rem', fontWeight: 700, marginBottom: '0.5rem' }}>
            Ingest Cyber Asset Inventory
          </h2>
          <p style={{ fontSize: '0.875rem', color: 'var(--text-muted)' }}>
            Upload your organization's CSV or JSON asset inventory to run automated data quality validation
            and explainable risk scoring.
          </p>
        </div>

        {/* Drag & Drop Area */}
        <div
          onDragEnter={handleDrag}
          onDragOver={handleDrag}
          onDragLeave={handleDrag}
          onDrop={handleDrop}
          onClick={() => inputRef.current?.click()}
          style={{
            border: `2px dashed ${dragActive ? 'var(--primary)' : 'var(--border-color)'}`,
            borderRadius: 'var(--radius-lg)',
            padding: '3rem 2rem',
            textAlign: 'center',
            backgroundColor: dragActive ? 'rgba(37, 99, 235, 0.04)' : 'var(--bg-subtle)',
            cursor: 'pointer',
            transition: 'all 0.2s ease',
            display: 'flex',
            flexDirection: 'column',
            alignItems: 'center',
            gap: '1rem',
          }}
        >
          <input
            ref={inputRef}
            type="file"
            accept=".csv,.json"
            style={{ display: 'none' }}
            onChange={(e) => handleFiles(e.target.files)}
          />

          <UploadCloud size={48} color={dragActive ? '#2563eb' : '#94a3b8'} />

          <div>
            <div style={{ fontSize: '1rem', fontWeight: 600 }}>
              {selectedFile ? selectedFile.name : 'Click to browse or drag and drop file here'}
            </div>
            <div style={{ fontSize: '0.8125rem', color: 'var(--text-muted)', marginTop: '0.25rem' }}>
              {selectedFile
                ? `${(selectedFile.size / 1024).toFixed(1)} KB • Click to change file`
                : 'Supports UTF-8 CSV (with or without BOM) and JSON • Max size: 10 MB'}
            </div>
          </div>
        </div>

        {/* Action Bar */}
        <div
          style={{
            marginTop: '1.5rem',
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'space-between',
            flexWrap: 'wrap',
            gap: '1rem',
          }}
        >
          <a
            href={api.getSampleCsvUrl()}
            download="aegiscorp_asset_inventory_1200.csv"
            className="btn btn-secondary btn-sm"
            onClick={(e) => e.stopPropagation()}
          >
            <Download size={14} />
            <span>Download AegisCorp Sample CSV (1,200 Rows)</span>
          </a>

          <button
            className="btn btn-primary"
            disabled={!selectedFile || uploading}
            onClick={handleUpload}
          >
            {uploading ? 'Processing & Validating...' : 'Validate and Import Inventory'}
          </button>
        </div>

        {/* Error Notice */}
        {error && (
          <div
            style={{
              marginTop: '1.25rem',
              padding: '0.85rem 1rem',
              backgroundColor: 'var(--critical-bg)',
              border: '1px solid var(--critical-border)',
              borderRadius: 'var(--radius-md)',
              color: '#b91c1c',
              fontSize: '0.875rem',
              display: 'flex',
              alignItems: 'center',
              gap: '0.5rem',
            }}
          >
            <AlertCircle size={18} />
            <span>{error}</span>
          </div>
        )}

        <div style={{ marginTop: '1.5rem', fontSize: '0.75rem', color: 'var(--text-muted)', textAlign: 'center' }}>
          Security Guarantee: Uploaded files are parsed safely in memory and preserved as read-only.
          Source files are never modified or overwritten.
        </div>
      </div>

      {/* Upload Success & Summary Card */}
      {result && (
        <div
          style={{
            backgroundColor: 'var(--bg-surface)',
            border: '1px solid #a7f3d0',
            borderRadius: 'var(--radius-lg)',
            padding: '1.5rem',
            boxShadow: 'var(--shadow-sm)',
            animation: 'fadeIn 0.3s ease',
          }}
        >
          <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem', color: '#047857', marginBottom: '1rem' }}>
            <CheckCircle2 size={22} />
            <h3 style={{ fontSize: '1.125rem', fontWeight: 700 }}>{result.message}</h3>
          </div>

          <div
            style={{
              display: 'grid',
              gridTemplateColumns: 'repeat(auto-fit, minmax(130px, 1fr))',
              gap: '1rem',
              marginBottom: '1.5rem',
            }}
          >
            <div style={{ background: 'var(--bg-subtle)', padding: '0.75rem', borderRadius: 'var(--radius-sm)' }}>
              <div style={{ fontSize: '0.75rem', color: 'var(--text-muted)' }}>Total Parsed</div>
              <div style={{ fontSize: '1.25rem', fontWeight: 700 }}>{result.summary.total_rows}</div>
            </div>
            <div style={{ background: 'var(--bg-subtle)', padding: '0.75rem', borderRadius: 'var(--radius-sm)' }}>
              <div style={{ fontSize: '0.75rem', color: '#047857' }}>Valid Rows</div>
              <div style={{ fontSize: '1.25rem', fontWeight: 700, color: '#047857' }}>{result.summary.valid_rows}</div>
            </div>
            <div style={{ background: 'var(--bg-subtle)', padding: '0.75rem', borderRadius: 'var(--radius-sm)' }}>
              <div style={{ fontSize: '0.75rem', color: '#854d0e' }}>Rows with Warnings</div>
              <div style={{ fontSize: '1.25rem', fontWeight: 700, color: '#854d0e' }}>{result.summary.warning_rows}</div>
            </div>
            <div style={{ background: 'var(--bg-subtle)', padding: '0.75rem', borderRadius: 'var(--radius-sm)' }}>
              <div style={{ fontSize: '0.75rem', color: '#b91c1c' }}>Blocked Rows</div>
              <div style={{ fontSize: '1.25rem', fontWeight: 700, color: '#b91c1c' }}>{result.summary.blocked_rows}</div>
            </div>
          </div>

          <div style={{ display: 'flex', gap: '0.75rem', flexWrap: 'wrap' }}>
            <button className="btn btn-primary btn-sm" onClick={() => onNavigate('overview')}>
              <span>View Overview</span>
              <ArrowRight size={14} />
            </button>
            <button className="btn btn-secondary btn-sm" onClick={() => onNavigate('inventory')}>
              Browse Asset Inventory
            </button>
            <button className="btn btn-secondary btn-sm" onClick={() => onNavigate('data-quality')}>
              Inspect Data Quality Issues ({result.summary.error_count + result.summary.warning_count})
            </button>
          </div>
        </div>
      )}
    </div>
  );
};
