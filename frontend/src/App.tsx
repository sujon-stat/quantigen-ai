import React, { useState, useEffect, Component } from 'react';
import type { ErrorInfo, ReactNode } from 'react';
import { Header } from './components/layout/Header';
import { Sidebar } from './components/layout/Sidebar';
import { DatasetStudio } from './components/dataset/DatasetStudio';
import { AnalysisStudio } from './components/analysis/AnalysisStudio';
import { ResultsCenter } from './components/results/ResultsCenter';
import type { DatasetSummary, AnalysisResponse } from './types/statmind';
import { api } from './api/client';

interface Props {
  children?: ReactNode;
}

interface State {
  hasError: boolean;
  error?: Error;
}

class ErrorBoundary extends Component<Props, State> {
  public state: State = {
    hasError: false
  };

  public static getDerivedStateFromError(error: Error): State {
    return { hasError: true, error };
  }

  public componentDidCatch(error: Error, errorInfo: ErrorInfo) {
    console.error('Quantigen UI Error Caught:', error, errorInfo);
  }

  public render() {
    if (this.state.hasError) {
      return (
        <div className="flex-1 max-w-3xl mx-auto my-12 p-8 glass-panel border-l-4 border-l-rose-500 text-center space-y-4 animate-fade-in">
          <h2 className="text-2xl font-bold text-rose-400">Application View Recovery</h2>
          <p className="text-sm text-slate-300">
            A temporary display issue occurred while rendering this interface component:
            <br />
            <code className="text-xs text-rose-300 bg-rose-950/40 px-2 py-1 rounded mt-2 inline-block">
              {this.state.error?.message || 'Rendering fault'}
            </code>
          </p>
          <div className="pt-4">
            <button
              onClick={() => {
                this.setState({ hasError: false, error: undefined });
              }}
              className="btn-primary px-6 py-2.5 text-sm"
            >
              Resume & Reset View
            </button>
          </div>
        </div>
      );
    }
    return this.props.children;
  }
}

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
      <ErrorBoundary>
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
      </ErrorBoundary>

      {/* Footer */}
      <footer className="border-t border-white/10 py-6 mt-auto bg-slate-950/60">
        <div className="max-w-7xl mx-auto px-6 flex flex-col sm:flex-row items-center justify-between gap-4 text-xs text-slate-500">
          <div>
            <span className="font-semibold text-slate-400">Quantigen AI</span> • Built with React 18, Vite, TypeScript & Vanilla Glassmorphic CSS
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
