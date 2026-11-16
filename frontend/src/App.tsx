import React, { useState, useEffect } from 'react';
import { Sidebar, PageId } from './components/Sidebar';
import { TopBar } from './components/TopBar';
import { OverviewPage } from './pages/OverviewPage';
import { UploadPage } from './pages/UploadPage';
import { InventoryPage } from './pages/InventoryPage';
import { DataQualityPage } from './pages/DataQualityPage';
import { RiskAnalysisPage } from './pages/RiskAnalysisPage';
import { ImportHistoryPage } from './pages/ImportHistoryPage';
import { AssetDetailDrawer } from './components/AssetDetailDrawer';
import { ScoringFormulaModal } from './components/ScoringFormulaModal';
import { ImportBatch } from './types/batch';
import { Asset } from './types/asset';
import { api } from './services/api';
import './styles/main.css';

export const App: React.FC = () => {
  const [currentPage, setCurrentPage] = useState<PageId>('overview');
  const [batches, setBatches] = useState<ImportBatch[]>([]);
  const [selectedBatchId, setSelectedBatchId] = useState<string | null>(null);
  const [selectedAsset, setSelectedAsset] = useState<Asset | null>(null);
  const [isFormulaModalOpen, setIsFormulaModalOpen] = useState(false);
  const [loading, setLoading] = useState(false);

  const loadBatches = (preferredBatchId?: string) => {
    setLoading(true);
    api.getBatches()
      .then((data) => {
        setBatches(data);
        if (data.length > 0) {
          if (preferredBatchId && data.some((b) => b.id === preferredBatchId)) {
            setSelectedBatchId(preferredBatchId);
          } else if (!selectedBatchId || !data.some((b) => b.id === selectedBatchId)) {
            setSelectedBatchId(data[0].id);
          }
        } else {
          setSelectedBatchId(null);
        }
        setLoading(false);
      })
      .catch((err) => {
        console.error('Failed to load batches:', err);
        setLoading(false);
      });
  };

  useEffect(() => {
    loadBatches();
  }, []);

  const activeBatch = batches.find((b) => b.id === selectedBatchId) || null;

  const handleUploadSuccess = (newBatchId: string) => {
    loadBatches(newBatchId);
    setSelectedBatchId(newBatchId);
  };

  return (
    <div className="app-container">
      <Sidebar currentPage={currentPage} onNavigate={setCurrentPage} />

      <div className="main-wrapper">
        <TopBar
          currentPage={currentPage}
          batches={batches}
          selectedBatchId={selectedBatchId}
          onSelectBatch={setSelectedBatchId}
          onNavigate={setCurrentPage}
          onRefresh={() => loadBatches(selectedBatchId || undefined)}
          onOpenFormula={() => setIsFormulaModalOpen(true)}
          loading={loading}
        />

        <main className="content-body">
          {currentPage === 'overview' && (
            <OverviewPage
              batch={activeBatch}
              onNavigate={setCurrentPage}
              onSelectAsset={setSelectedAsset}
              onRefresh={() => loadBatches(selectedBatchId || undefined)}
            />
          )}

          {currentPage === 'upload' && (
            <UploadPage
              onUploadSuccess={handleUploadSuccess}
              onNavigate={setCurrentPage}
            />
          )}

          {currentPage === 'inventory' && (
            <InventoryPage
              batch={activeBatch}
              onSelectAsset={setSelectedAsset}
              onNavigateUpload={() => setCurrentPage('upload')}
            />
          )}

          {currentPage === 'data-quality' && (
            <DataQualityPage
              batch={activeBatch}
              onNavigateUpload={() => setCurrentPage('upload')}
            />
          )}

          {currentPage === 'risk-analysis' && (
            <RiskAnalysisPage
              batch={activeBatch}
              onSelectAsset={setSelectedAsset}
              onOpenFormula={() => setIsFormulaModalOpen(true)}
              onRefresh={() => loadBatches(selectedBatchId || undefined)}
              onNavigateUpload={() => setCurrentPage('upload')}
            />
          )}

          {currentPage === 'history' && (
            <ImportHistoryPage
              batches={batches}
              selectedBatchId={selectedBatchId}
              onSelectBatch={setSelectedBatchId}
              onNavigate={setCurrentPage}
              onRefresh={loadBatches}
            />
          )}
        </main>
      </div>

      {/* Asset Detail Drawer */}
      {selectedAsset && selectedBatchId && (
        <AssetDetailDrawer
          asset={selectedAsset}
          batchId={selectedBatchId}
          onClose={() => setSelectedAsset(null)}
        />
      )}

      {/* Scoring Formula Methodology Modal */}
      <ScoringFormulaModal
        isOpen={isFormulaModalOpen}
        onClose={() => setIsFormulaModalOpen(false)}
      />
    </div>
  );
};

