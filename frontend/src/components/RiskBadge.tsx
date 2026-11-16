import React from 'react';

interface RiskBadgeProps {
  level?: string | null;
  score?: number | null;
  showScore?: boolean;
}

export const RiskBadge: React.FC<RiskBadgeProps> = ({ level, score, showScore = false }) => {
  if (!level) {
    return <span className="badge badge-info">Not Assessed</span>;
  }

  const normalized = level.toLowerCase();
  let badgeClass = 'badge-info';

  if (normalized === 'critical') badgeClass = 'badge-critical';
  else if (normalized === 'high') badgeClass = 'badge-high';
  else if (normalized === 'medium') badgeClass = 'badge-medium';
  else if (normalized === 'low') badgeClass = 'badge-low';

  return (
    <span className={`badge ${badgeClass}`}>
      {level}
      {showScore && score !== null && score !== undefined && (
        <span style={{ opacity: 0.85, fontWeight: 500, marginLeft: '0.25rem' }}>
          ({score.toFixed(1)})
        </span>
      )}
    </span>
  );
};

