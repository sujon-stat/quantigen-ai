import React, { useState, useEffect, Component } from 'react';
import type { ErrorInfo, ReactNode } from 'react';
import { Header } from './components/layout/Header';
import { DatasetStudio } from './components/dataset/DatasetStudio';
import { AnalysisResultsSuite } from './components/analysis/AnalysisResultsSuite';
import { QuantigenAIChat } from './components/common/QuantigenAIChat';
import { X, Sparkles } from 'lucide-react';
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
  const [activeStep, setActiveStep] = useState<1 | 2 | 3>(() => {
    const saved = localStorage.getItem('quantigen_active_step');
    return saved ? (Number(saved) as 1 | 2 | 3) : 1;
  });
  const [dataset, setDataset] = useState<DatasetSummary | null>(() => {
    const saved = localStorage.getItem('quantigen_dataset');
    try { return saved ? JSON.parse(saved) : null; } catch { return null; }
  });
  const [analysisResponse, setAnalysisResponse] = useState<AnalysisResponse | null>(() => {
    const saved = localStorage.getItem('quantigen_analysis_response');
    try { return saved ? JSON.parse(saved) : null; } catch { return null; }
  });
  const [analysisHistory, setAnalysisHistory] = useState<AnalysisResponse[]>(() => {
    const saved = localStorage.getItem('quantigen_analysis_history');
    try {
      const parsed = saved ? JSON.parse(saved) : [];
      if (parsed.length > 0) return parsed;
    } catch { /* fallback */ }
    const singleSaved = localStorage.getItem('quantigen_analysis_response');
    try {
      if (singleSaved) {
        const item: AnalysisResponse = JSON.parse(singleSaved);
        if (!item.history_id) item.history_id = 'hist_' + Date.now();
        if (!item.timestamp) item.timestamp = new Date().toLocaleTimeString();
        return [item];
      }
    } catch { /* fallback */ }
    return [];
  });
  const [theme, setTheme] = useState<'dark' | 'light'>(() => {
    return (localStorage.getItem('quantigen_theme') as 'dark' | 'light') || 'dark';
  });
  const [backendConnected, setBackendConnected] = useState<boolean>(false);
  const [isAiDrawerOpen, setIsAiDrawerOpen] = useState<boolean>(false);

  useEffect(() => {
    localStorage.setItem('quantigen_active_step', String(activeStep));
  }, [activeStep]);

  useEffect(() => {
    if (dataset) localStorage.setItem('quantigen_dataset', JSON.stringify(dataset));
    else localStorage.removeItem('quantigen_dataset');
  }, [dataset]);

  useEffect(() => {
    if (analysisResponse) localStorage.setItem('quantigen_analysis_response', JSON.stringify(analysisResponse));
    else localStorage.removeItem('quantigen_analysis_response');
  }, [analysisResponse]);

  useEffect(() => {
    if (analysisHistory.length > 0) {
      localStorage.setItem('quantigen_analysis_history', JSON.stringify(analysisHistory));
    } else {
      localStorage.removeItem('quantigen_analysis_history');
    }
  }, [analysisHistory]);

  useEffect(() => {
    localStorage.setItem('quantigen_theme', theme);
    if (theme === 'light') {
      document.documentElement.classList.add('light-mode');
      document.documentElement.classList.remove('dark');
    } else {
      document.documentElement.classList.remove('light-mode');
      document.documentElement.classList.add('dark');
    }
  }, [theme]);

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
    const histId = response.history_id || 'hist_' + Date.now() + '_' + Math.random().toString(36).substring(2, 6);
    const ts = response.timestamp || new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' });
    const enrichedResponse: AnalysisResponse = {
      ...response,
      history_id: histId,
      timestamp: ts,
    };
    setAnalysisResponse(enrichedResponse);
    setAnalysisHistory((prev) => {
      const exists = prev.some((item) => item.history_id === histId);
      if (exists) {
        return prev.map((item) => (item.history_id === histId ? enrichedResponse : item));
      }
      return [...prev, enrichedResponse];
    });
    setActiveStep(3);
  };

  const handleRemoveHistoryItem = (historyId: string) => {
    setAnalysisHistory((prev) => prev.filter((item) => item.history_id !== historyId));
    if (analysisResponse?.history_id === historyId) {
      setAnalysisResponse(null);
    }
  };

  const handleClearHistory = () => {
    setAnalysisHistory([]);
    localStorage.removeItem('quantigen_analysis_history');
  };

  const handleToggleTheme = () => {
    setTheme((prev) => (prev === 'dark' ? 'light' : 'dark'));
  };

  const handleResetSession = () => {
    localStorage.removeItem('quantigen_active_step');
    localStorage.removeItem('quantigen_dataset');
    localStorage.removeItem('quantigen_analysis_response');
    localStorage.removeItem('quantigen_analysis_history');
    setDataset(null);
    setAnalysisResponse(null);
    setAnalysisHistory([]);
    setActiveStep(1);
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
        theme={theme}
        onToggleTheme={handleToggleTheme}
        onResetSession={handleResetSession}
        analysisHistoryCount={analysisHistory.length}
        isAiConsultantOpen={isAiDrawerOpen}
        onToggleAiConsultant={() => setIsAiDrawerOpen((prev) => !prev)}
      />

      {/* Main Content Area */}
      <ErrorBoundary>
        <main className="flex-1 max-w-7xl w-full mx-auto px-4 sm:px-6 lg:px-8 flex flex-col gap-8 pb-16">
          {/* Main Workspace (Full Screen Width) */}
          <div className="flex-1 min-w-0 w-full">
            {activeStep === 1 && (
              <DatasetStudio
                dataset={dataset}
                onDatasetLoaded={handleDatasetLoaded}
                onProceedToAnalysis={handleProceedToAnalysis}
              />
            )}

            {(activeStep === 2 || activeStep === 3) && dataset && (
              <AnalysisResultsSuite
                dataset={dataset}
                analysisResponse={analysisResponse}
                onAnalysisCompleted={handleAnalysisCompleted}
                analysisHistory={analysisHistory}
                onRemoveHistoryItem={handleRemoveHistoryItem}
                onClearHistory={handleClearHistory}
                onSelectHistoryItem={(item) => setAnalysisResponse(item)}
                theme={theme}
              />
            )}
          </div>
        </main>
      </ErrorBoundary>

      {/* Global Right-Side AI Statistical Consultant Drawer */}
      {isAiDrawerOpen && (
        <div className="fixed inset-0 z-[100] overflow-hidden">
          <div
            className="absolute inset-0 bg-black/50 backdrop-blur-sm transition-opacity"
            onClick={() => setIsAiDrawerOpen(false)}
          />
          <div className="fixed inset-y-0 right-0 max-w-full flex pl-10">
            <div className="w-screen max-w-md sm:max-w-lg bg-slate-950 border-l border-white/10 shadow-2xl flex flex-col overflow-hidden animate-slide-in-right">
              {/* Drawer Header */}
              <div className="p-4 bg-gradient-to-r from-purple-900/80 via-indigo-900/70 to-sky-900/80 border-b border-white/10 flex items-center justify-between flex-shrink-0 shadow-lg">
                <div className="flex items-center gap-3">
                  <div className="w-9 h-9 rounded-xl bg-purple-500/20 border border-purple-400/40 flex items-center justify-center text-purple-300 shadow-md">
                    <Sparkles className="w-5 h-5 text-amber-300 animate-pulse" />
                  </div>
                  <div>
                    <div className="flex items-center gap-2">
                      <h3 className="font-extrabold text-white text-base tracking-wide">
                        AI Statistical Consultant
                      </h3>
                      <span className="px-1.5 py-0.5 rounded bg-purple-500/30 text-purple-200 font-mono text-[10px] border border-purple-400/30">
                        Active 24/7
                      </span>
                    </div>
                    <p className="text-xs text-purple-200/90 leading-tight">
                      Stateful guidance • Context-aware explanations
                    </p>
                  </div>
                </div>
                <button
                  onClick={() => setIsAiDrawerOpen(false)}
                  title="Close AI Consultant"
                  className="p-1.5 rounded-lg bg-white/5 hover:bg-white/10 text-slate-300 hover:text-white transition-all"
                >
                  <X className="w-5 h-5" />
                </button>
              </div>

              {/* Drawer Body */}
              <div className="flex-1 overflow-y-auto flex flex-col p-4 bg-slate-950/90 custom-scrollbar">
                <QuantigenAIChat
                  hideHeader={true}
                  title={analysisResponse ? `AI Consultant: ${(analysisResponse as any).method_name || 'Results'}` : "AI Statistical Consultant"}
                  subtitle="Interactive statistical guidance and next steps"
                  context={{
                    current_analysis: analysisResponse,
                    recent_analysis: analysisResponse ? {
                      method: (analysisResponse as any).method_name,
                      vars: (analysisResponse as any).variables_used || (analysisResponse as any).columns_used || [],
                      assumption_warning: (analysisResponse as any).assumption_results?.some((a: any) => !a.passed)
                        ? (analysisResponse as any).assumption_results.filter((a: any) => !a.passed).map((a: any) => `${a.assumption_name}: ${a.explanation}`).join('; ')
                        : "None"
                    } : null,
                    dataset_info: dataset ? {
                      name: dataset.filename || "Active Dataset",
                      rows: dataset.total_rows || (dataset as any).rows || 0,
                      cols: dataset.total_columns || (dataset.columns || (dataset as any).variables || []).length || 0
                    } : null,
                    variable_registry: dataset ? (dataset.columns || (dataset as any).variables || []).map((c: any) => ({
                      name: c.name || c.id || c,
                      type: c.type || c.inferred_type || c.data_type || "continuous",
                      stats: c.mean !== undefined ? `Mean: ${c.mean}` : c.unique_values !== undefined ? `${c.unique_values} levels` : ""
                    })) : [],
                    columns_metadata: dataset ? (dataset.columns || (dataset as any).variables || []) : [],
                    dataset_id: dataset?.dataset_id
                  }}
                  onExecuteMethod={(_methodId) => {
                    setIsAiDrawerOpen(false);
                    setActiveStep(2);
                  }}
                />
              </div>
            </div>
          </div>
        </div>
      )}

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
