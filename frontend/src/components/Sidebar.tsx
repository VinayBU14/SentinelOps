import React from 'react';
import {
  LayoutDashboard,
  UploadCloud,
  Server,
  ShieldAlert,
  Flame,
  History,
  ShieldCheck,
} from 'lucide-react';

export type PageId =
  | 'overview'
  | 'upload'
  | 'inventory'
  | 'data-quality'
  | 'risk-analysis'
  | 'history';

interface SidebarProps {
  currentPage: PageId;
  onNavigate: (page: PageId) => void;
}

export const Sidebar: React.FC<SidebarProps> = ({ currentPage, onNavigate }) => {
  const navItems = [
    { id: 'overview' as PageId, label: 'Overview', icon: <LayoutDashboard size={18} /> },
    { id: 'upload' as PageId, label: 'Upload / Import', icon: <UploadCloud size={18} /> },
    { id: 'inventory' as PageId, label: 'Asset Inventory', icon: <Server size={18} /> },
    { id: 'data-quality' as PageId, label: 'Data Quality', icon: <ShieldAlert size={18} /> },
    { id: 'risk-analysis' as PageId, label: 'Risk Analysis', icon: <Flame size={18} /> },
    { id: 'history' as PageId, label: 'Import History', icon: <History size={18} /> },
  ];

  return (
    <aside className="sidebar">
      <div className="sidebar-brand">
        <ShieldCheck size={28} color="#38bdf8" />
        <div>
          <div className="brand-title">SentinelOps</div>
          <div className="brand-sub">Asset Risk Engine</div>
        </div>
      </div>

      <nav className="sidebar-nav">
        {navItems.map((item) => (
          <button
            key={item.id}
            className={`nav-item ${currentPage === item.id ? 'active' : ''}`}
            onClick={() => onNavigate(item.id)}
          >
            {item.icon}
            <span>{item.label}</span>
          </button>
        ))}
      </nav>

      <div className="sidebar-footer">
        <div className="env-pill">
          <span className="env-dot" />
          <span>Local Academic Build</span>
        </div>
        <div>AegisCorp Dataset Ready</div>
      </div>
    </aside>
  );
};

