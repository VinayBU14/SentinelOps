import React from 'react';
import { Inbox, AlertCircle } from 'lucide-react';

interface EmptyStateProps {
  title?: string;
  message?: string;
  actionText?: string;
  onAction?: () => void;
  icon?: React.ReactNode;
}

export const EmptyState: React.FC<EmptyStateProps> = ({
  title = 'No Records Found',
  message = 'There is no data to display for the current view or filters.',
  actionText,
  onAction,
  icon,
}) => {
  return (
    <div className="state-container">
      {icon || <Inbox size={48} color="#94a3b8" />}
      <h3 className="state-title">{title}</h3>
      <p style={{ maxWidth: '420px', fontSize: '0.875rem' }}>{message}</p>
      {actionText && onAction && (
        <button className="btn btn-primary btn-sm" onClick={onAction} style={{ marginTop: '0.5rem' }}>
          {actionText}
        </button>
      )}
    </div>
  );
};

export const LoadingSkeleton: React.FC<{ message?: string }> = ({ message = 'Loading SentinelOps data...' }) => {
  return (
    <div className="state-container">
      <div
        style={{
          width: '36px',
          height: '36px',
          border: '3px solid var(--border-color)',
          borderTopColor: 'var(--primary)',
          borderRadius: '50%',
          animation: 'spin 0.8s linear infinite',
        }}
      />
      <p style={{ fontSize: '0.875rem', color: 'var(--text-muted)' }}>{message}</p>
      <style>{`
        @keyframes spin {
          0% { transform: rotate(0deg); }
          100% { transform: rotate(360deg); }
        }
      `}</style>
    </div>
  );
};

export const ErrorState: React.FC<{ error: string; onRetry?: () => void }> = ({
  error,
  onRetry,
}) => {
  return (
    <div className="state-container">
      <AlertCircle size={44} color="#ef4444" />
      <h3 className="state-title" style={{ color: '#b91c1c' }}>Error Loading Data</h3>
      <p style={{ maxWidth: '450px', fontSize: '0.875rem' }}>{error}</p>
      {onRetry && (
        <button className="btn btn-secondary btn-sm" onClick={onRetry} style={{ marginTop: '0.5rem' }}>
          Retry
        </button>
      )}
    </div>
  );
};

