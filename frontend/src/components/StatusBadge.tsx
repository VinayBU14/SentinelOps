import React from 'react';

interface StatusBadgeProps {
  status: 'valid' | 'warning' | 'blocked' | 'error' | 'info' | string;
}

export const StatusBadge: React.FC<StatusBadgeProps> = ({ status }) => {
  const normalized = status.toLowerCase();
  let badgeClass = 'badge-info';

  if (normalized === 'valid') badgeClass = 'badge-valid';
  else if (normalized === 'warning') badgeClass = 'badge-warning';
  else if (normalized === 'blocked' || normalized === 'error') badgeClass = 'badge-blocked';

  return <span className={`badge ${badgeClass}`}>{status}</span>;
};

