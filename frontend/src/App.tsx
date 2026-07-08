import React, { useState, useEffect } from 'react';
import { Header } from './components/layout/Header';
import { Sidebar } from './components/layout/Sidebar';
import { DatasetStudio } from './components/dataset/DatasetStudio';
import { AnalysisStudio } from './components/analysis/AnalysisStudio';
import { ResultsCenter } from './components/results/ResultsCenter';
import type { DatasetSummary, AnalysisResponse } from './types/statmind';
import { api } from './api/client';

export const App: React.FC = () => {
  const [activeStep, setActiveStep] = useState<1 | 2 | 3>(1);
  const [dataset, setDataset] = useState<DatasetSummary | null>(null);
  const [analysisResponse, setAnalysisResponse] = useState<AnalysisResponse | null>(null);
  const [backendConnected, setBackendConnected] = useState<boolean>(false);

  useEffect(() => {
    // Check backend connection on start
    api.healthCheck()
      .then(() => setBackendConnected(true))
      .catch(() => setBackendConnected(false));

    // Periodic heartbeat to make sure engine remains connected
    const interval = setInterval(() => {
      api.healthCheck()
        .then(() => setBackendConnected(true))
        .catch(() => setBackendConnected(false));
    }, 15000);

    return () => clearInterval(interval);
  }, []);

  const handleDatasetLoaded = (summary: DatasetSummary) => {
    setDataset(summary);
  };

  const handleProceedToAnalysis = () => {
    if (dataset) {
      setActiveStep(2);
    }
  };

  const handleAnalysisCompleted = (response: AnalysisResponse) => {
    setAnalysisResponse(response);
    setActiveStep(3);
  };

  return (
    <div className="min-h-screen flex flex-col bg-[#0f172a] text-slate-100 selection:bg-sky-500 selection:text-white">
      {/* Top Header & Navigation Bar */}
      <Header
        activeStep={activeStep}
        setActiveStep={setActiveStep}
        datasetLoaded={!!dataset}
        analysisCompleted={!!analysisResponse}
        backendConnected={backendConnected}
      />

      {/* Main Content Area */}
      <main className="flex-1 max-w-7xl w-full mx-auto px-4 sm:px-6 lg:px-8 flex flex-col md:flex-row gap-8 pb-16">
        {/* Main Workspace (Left Column) */}
        <div className="flex-1 min-w-0">
          {activeStep === 1 && (
            <DatasetStudio
              dataset={dataset}
              onDatasetLoaded={handleDatasetLoaded}
              onProceedToAnalysis={handleProceedToAnalysis}
            />
          )}

          {activeStep === 2 && dataset && (
            <AnalysisStudio
              dataset={dataset}
              onAnalysisCompleted={handleAnalysisCompleted}
            />
          )}

          {activeStep === 3 && (
            <ResultsCenter
              response={analysisResponse}
              onBackToAnalysis={() => setActiveStep(2)}
            />
          )}
        </div>

        {/* Educational Sidebar (Right Column) */}
        {activeStep !== 3 && <Sidebar />}
      </main>

      {/* Footer */}
      <footer className="border-t border-white/10 py-6 mt-auto bg-slate-950/60">
        <div className="max-w-7xl mx-auto px-6 flex flex-col sm:flex-row items-center justify-between gap-4 text-xs text-slate-500">
          <div>
            <span className="font-semibold text-slate-400">StatMind AI</span> • Built with React 18, Vite, TypeScript & Vanilla Glassmorphic CSS
          </div>
          <div className="flex items-center gap-4 text-slate-400">
            <span>Core Principles: Assumption-First • Educational • Reproducible</span>
          </div>
        </div>
      </footer>
    </div>
  );
};

export default App;
