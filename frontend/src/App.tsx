import React, { useState, useEffect, Component } from 'react';
import type { ErrorInfo, ReactNode } from 'react';
import { Header } from './components/layout/Header';
import { LeftSidebarNav, type WorkspaceNavTab } from './components/workspace/LeftSidebarNav';
import { ProgressTrackerBanner } from './components/workspace/ProgressTrackerBanner';
import { WelcomeScreen } from './components/workspace/WelcomeScreen';
import { ResearchCanvas } from './components/workspace/ResearchCanvas';
import { DatasetViewSwitcher } from './components/dataset/DatasetViewSwitcher';
import { AutomaticDoctorWorkflow } from './components/analysis/AutomaticDoctorWorkflow';
import { UnifiedResultsDashboard } from './components/results/UnifiedResultsDashboard';
import { DatasetStudio } from './components/dataset/DatasetStudio';
import { AnalysisResultsSuite } from './components/analysis/AnalysisResultsSuite';
import { QuantigenAIChat } from './components/common/QuantigenAIChat';
import { QuantigenPowerStudio } from './components/power/QuantigenPowerStudio';
import { X, Sparkles, FolderOpen, Trash2, ArrowRight } from 'lucide-react';
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
    console.error('StatAid Studio UI Error Caught:', error, errorInfo);
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
  const [activeStep, setActiveStep] = useState<1 | 2 | 3 | 4>(() => {
    const saved = localStorage.getItem('quantigen_active_step');
    return saved ? (Number(saved) as 1 | 2 | 3 | 4) : 1;
  });
  const [activeTab, setActiveTab] = useState<WorkspaceNavTab>(() => {
    return (localStorage.getItem('quantigen_active_tab') as WorkspaceNavTab) || 'home';
  });
  const [workspaceMode, setWorkspaceMode] = useState<'beginner' | 'expert'>(() => {
    return (localStorage.getItem('quantigen_workspace_mode') as 'beginner' | 'expert') || 'beginner';
  });
  const [isNavCollapsed, setIsNavCollapsed] = useState<boolean>(false);
  const [showProjectsModal, setShowProjectsModal] = useState<boolean>(false);

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
    localStorage.setItem('quantigen_active_tab', activeTab);
  }, [activeTab]);

  useEffect(() => {
    localStorage.setItem('quantigen_workspace_mode', workspaceMode);
  }, [workspaceMode]);

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
    api.healthCheck()
      .then(() => setBackendConnected(true))
      .catch(() => setBackendConnected(false));

    const interval = setInterval(() => {
      api.healthCheck()
        .then(() => setBackendConnected(true))
        .catch(() => setBackendConnected(false));
    }, 15000);

    return () => clearInterval(interval);
  }, []);

  const handleDatasetLoaded = (summary: DatasetSummary) => {
    setDataset(summary);
    setAnalysisResponse(null);
    setAnalysisHistory([]);
    setActiveStep(1);
    setActiveTab('data');
  };

  const handleProceedToAnalysis = () => {
    if (dataset) {
      setActiveStep(2);
      setActiveTab('analysis');
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
    setActiveTab('tables');
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
    localStorage.removeItem('quantigen_active_tab');
    setDataset(null);
    setAnalysisResponse(null);
    setAnalysisHistory([]);
    setActiveStep(1);
    setActiveTab('home');
  };

  return (
    <div className="min-h-screen flex flex-col bg-[#0f172a] text-slate-100 selection:bg-sky-500 selection:text-white overflow-x-hidden">
      {/* Top Header & Navigation Bar */}
      <Header
        activeStep={activeStep}
        setActiveStep={(step) => {
          setActiveStep(step);
          if (step === 1) setActiveTab('data');
          else if (step === 2 || step === 3) setActiveTab(analysisResponse ? 'tables' : 'analysis');
          else if (step === 4) setActiveTab('settings');
        }}
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

      {/* Main One Workspace Shell (Minimal Left Sidebar + Center Progress Canvas + Right AI Drawer) */}
      <div className="flex-1 flex flex-row items-stretch w-full overflow-hidden">
        {/* Minimal Left Sidebar Navigation */}
        <LeftSidebarNav
          activeTab={activeTab}
          onSelectTab={(tab) => {
            setActiveTab(tab);
            if (tab === 'projects') setShowProjectsModal(true);
            if (tab === 'ai') setIsAiDrawerOpen(true);
          }}
          isCollapsed={isNavCollapsed}
          onToggleCollapse={() => setIsNavCollapsed((prev) => !prev)}
          mode={workspaceMode}
          onToggleMode={setWorkspaceMode}
          datasetLoaded={!!dataset}
          analysisCompleted={!!analysisResponse}
        />

        {/* Center Main Workspace Area */}
        <div className="flex-1 min-w-0 flex flex-col overflow-y-auto">
          {/* Main Progress Tracker Banner */}
          <ProgressTrackerBanner
            currentTab={activeTab}
            datasetLoaded={!!dataset}
            analysisCompleted={!!analysisResponse}
            onSelectStep={(tab) => setActiveTab(tab)}
          />

          {/* Dynamic Content Views based on activeTab */}
          <ErrorBoundary>
            <main className="flex-1 p-4 sm:p-6 lg:p-8 max-w-7xl mx-auto w-full transition-all duration-300">
              {/* Home Tab: Welcome Screen */}
              {activeTab === 'home' && (
                <WelcomeScreen
                  dataset={dataset}
                  recentAnalysis={analysisResponse}
                  historyCount={analysisHistory.length}
                  onAction={(action) => {
                    if (action === 'import') setActiveTab('data');
                    else if (action === 'ai') setIsAiDrawerOpen(true);
                    else if (action === 'resume') setActiveTab('analysis');
                    else if (action === 'projects') setShowProjectsModal(true);
                    else if (action === 'learn') setActiveStep(4);
                  }}
                />
              )}

              {/* Research Canvas Tab */}
              {activeTab === 'canvas' && (
                <ResearchCanvas
                  dataset={dataset}
                  analysisResponse={analysisResponse}
                  onNavigateTab={(tab) => setActiveTab(tab)}
                  onRerunAnalysis={() => setActiveTab('analysis')}
                />
              )}

              {/* Data & Cleaning Tabs */}
              {(activeTab === 'data' || activeTab === 'cleaning') && (
                <div className="space-y-6">
                  {dataset && (
                    <DatasetViewSwitcher
                      dataset={dataset}
                      onSelectVariable={(_varName) => {
                        // Focus on column exploration
                      }}
                    />
                  )}
                  <DatasetStudio
                    dataset={dataset}
                    onDatasetLoaded={handleDatasetLoaded}
                    onProceedToAnalysis={handleProceedToAnalysis}
                  />
                </div>
              )}

              {/* Analysis Tab: Automatic Doctor Workflow -> Analysis Studio */}
              {activeTab === 'analysis' && (
                <div className="space-y-8">
                  {dataset && !analysisResponse && (
                    <AutomaticDoctorWorkflow
                      dataset={dataset}
                      onExecuteRecommendation={(_methodId, _methodLabel) => {
                        setActiveStep(2);
                      }}
                    />
                  )}
                  {dataset && (
                    <AnalysisResultsSuite
                      dataset={dataset}
                      analysisResponse={analysisResponse}
                      onAnalysisCompleted={handleAnalysisCompleted}
                      analysisHistory={analysisHistory}
                      onRemoveHistoryItem={handleRemoveHistoryItem}
                      onClearHistory={handleClearHistory}
                      onSelectHistoryItem={(item) => {
                        setAnalysisResponse(item);
                        setActiveTab('tables');
                      }}
                      theme={theme}
                    />
                  )}
                  {!dataset && (
                    <div className="p-8 text-center glass-panel border border-amber-500/30 space-y-4">
                      <h3 className="text-xl font-bold text-amber-300">No Dataset Active</h3>
                      <p className="text-sm text-slate-300">Please import or select a dataset first to initiate statistical examination.</p>
                      <button
                        onClick={() => setActiveTab('data')}
                        className="btn-primary px-6 py-2.5 text-sm mx-auto"
                      >
                        Launch Dataset Studio
                      </button>
                    </div>
                  )}
                </div>
              )}

              {/* Tables, Figures, Reports, Code Tabs -> Unified Results Dashboard */}
              {(activeTab === 'tables' || activeTab === 'figures' || activeTab === 'reports' || activeTab === 'code') && (
                <div className="space-y-6">
                  {analysisResponse ? (
                    <UnifiedResultsDashboard
                      analysisResponse={analysisResponse}
                      dataset={dataset}
                      onNavigateTab={(tab) => setActiveTab(tab as any)}
                    />
                  ) : (
                    <div className="p-8 text-center glass-panel border border-sky-500/30 space-y-4">
                      <h3 className="text-xl font-bold text-white">Results & Publication Dashboard</h3>
                      <p className="text-sm text-slate-300">Execute an analysis or select a recent history item to unlock APA 7th tables, interactive figures, and multi-study reports.</p>
                      <button
                        onClick={() => setActiveTab('analysis')}
                        className="btn-primary px-6 py-2.5 text-sm mx-auto"
                      >
                        Run Statistical Analysis
                      </button>
                    </div>
                  )}
                </div>
              )}

              {/* Settings / Power Studio Tab */}
              {activeTab === 'settings' && (
                <QuantigenPowerStudio onClose={() => setActiveTab('home')} />
              )}
            </main>
          </ErrorBoundary>
        </div>

        {/* Right-Side AI Consultant Drawer Panel */}
        {isAiDrawerOpen && (
          <div className="w-80 sm:w-96 lg:w-[420px] flex-shrink-0 flex flex-col bg-slate-950 border-l-2 border-sky-400/60 shadow-2xl z-30 overflow-hidden">
            <div className="p-3.5 bg-gradient-to-r from-slate-900 via-sky-950/90 to-purple-950/80 border-b border-sky-400/30 flex items-center justify-between flex-shrink-0 shadow-lg">
              <div className="flex items-center gap-2.5">
                <div className="w-9 h-9 rounded-xl bg-gradient-to-br from-amber-400 to-amber-600 flex items-center justify-center text-slate-950 shadow-md shadow-amber-500/20">
                  <Sparkles className="w-5 h-5 animate-spin-slow" />
                </div>
                <div>
                  <div className="flex items-center gap-2">
                    <h3 className="font-black text-white text-sm sm:text-base tracking-wide">
                      Ask AI Consultant
                    </h3>
                    <span className="px-1.5 py-0.5 rounded-full bg-sky-500/20 text-sky-300 font-bold text-[10px] border border-sky-400/40">
                      Gemini 1.5
                    </span>
                  </div>
                  <p className="text-[11px] text-slate-300 font-medium">
                    Stateful Statistical Context • APA 7th Guidance
                  </p>
                </div>
              </div>
              <button
                onClick={() => setIsAiDrawerOpen(false)}
                title="Close AI Consultant Drawer"
                className="p-1.5 rounded-lg bg-white/10 hover:bg-rose-500/20 text-slate-300 hover:text-rose-300 border border-white/10 transition-all"
              >
                <X className="w-5 h-5 stroke-[2.5]" />
              </button>
            </div>

            <div className="flex-1 overflow-y-auto flex flex-col p-4 bg-slate-950/95 custom-scrollbar">
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
                  setActiveTab('analysis');
                }}
              />
            </div>
          </div>
        )}
      </div>

      {/* Projects Modal */}
      {showProjectsModal && (
        <div className="fixed inset-0 z-50 bg-slate-950/80 backdrop-blur-sm flex items-center justify-center p-4 animate-fade-in">
          <div className="bg-slate-900 border-2 border-indigo-500/60 rounded-3xl max-w-2xl w-full p-6 sm:p-8 shadow-2xl space-y-6">
            <div className="flex items-center justify-between border-b border-white/10 pb-4">
              <div className="flex items-center gap-3">
                <div className="w-10 h-10 rounded-2xl bg-gradient-to-br from-indigo-500 to-purple-600 flex items-center justify-center text-white shadow-lg">
                  <FolderOpen className="w-5 h-5" />
                </div>
                <div>
                  <h3 className="text-xl font-black text-white">Project Manager & Portfolio</h3>
                  <p className="text-xs text-slate-400">Saved Analysis History Sessions ({analysisHistory.length})</p>
                </div>
              </div>
              <button
                onClick={() => setShowProjectsModal(false)}
                className="p-2 rounded-xl bg-slate-800 hover:bg-rose-500/20 text-slate-300 hover:text-rose-300 border border-white/10 transition-all"
              >
                <X className="w-5 h-5" />
              </button>
            </div>

            <div className="space-y-3 max-h-96 overflow-y-auto custom-scrollbar pr-2">
              {analysisHistory.length === 0 ? (
                <div className="p-8 text-center bg-slate-950/60 rounded-2xl border border-white/10 space-y-2">
                  <p className="text-sm font-bold text-slate-400">No saved sessions found.</p>
                  <p className="text-xs text-slate-500">Run an analysis in the workspace to automatically save to your portfolio.</p>
                </div>
              ) : (
                analysisHistory.map((item) => (
                  <div
                    key={item.history_id}
                    onClick={() => {
                      setAnalysisResponse(item);
                      setShowProjectsModal(false);
                      setActiveTab('tables');
                    }}
                    className="p-4 rounded-2xl bg-slate-950/80 border border-white/10 hover:border-sky-400 flex items-center justify-between gap-4 cursor-pointer transition-all group"
                  >
                    <div>
                      <h4 className="font-bold text-white text-sm group-hover:text-sky-300">
                        {(item as any).method_name || 'Statistical Analysis'}
                      </h4>
                      <p className="text-xs text-slate-400 font-mono">
                        Saved: {item.timestamp} • N={(item as any).analysis_result?.sample_size || (item as any).sample_size || 0} cases
                      </p>
                    </div>
                    <div className="flex items-center gap-2">
                      <button
                        onClick={(e) => {
                          e.stopPropagation();
                          handleRemoveHistoryItem(item.history_id!);
                        }}
                        className="p-2 rounded-lg bg-rose-500/10 hover:bg-rose-500 text-rose-400 hover:text-white transition-all"
                        title="Delete session"
                      >
                        <Trash2 className="w-4 h-4" />
                      </button>
                      <span className="text-xs font-bold text-sky-400 group-hover:translate-x-1 transition-transform flex items-center gap-1">
                        Open <ArrowRight className="w-3.5 h-3.5" />
                      </span>
                    </div>
                  </div>
                ))
              )}
            </div>

            <div className="pt-4 border-t border-white/10 flex items-center justify-between">
              {analysisHistory.length > 0 && (
                <button
                  onClick={handleClearHistory}
                  className="px-4 py-2 rounded-xl bg-rose-500/20 hover:bg-rose-500 text-rose-300 hover:text-white text-xs font-bold transition-all"
                >
                  Clear All History
                </button>
              )}
              <button
                onClick={() => setShowProjectsModal(false)}
                className="px-6 py-2.5 rounded-xl bg-slate-800 hover:bg-slate-700 text-white font-bold text-xs ml-auto"
              >
                Close Project Manager
              </button>
            </div>
          </div>
        </div>
      )}

      {/* Footer */}
      <footer className="border-t border-white/10 py-5 mt-auto bg-slate-950/80 text-xs text-slate-500 z-20">
        <div className="max-w-7xl mx-auto px-6 flex flex-col sm:flex-row items-center justify-between gap-4">
          <div>
            <span className="font-bold text-slate-300">StatAid Studio</span> • The Research-First AI Platform (Notion + Canva + Power BI + VS Code Workflow)
          </div>
          <div className="flex items-center gap-4 text-slate-400">
            <span>Reliability • Assumption-First Shield • APA 7th Transparency</span>
          </div>
        </div>
      </footer>
    </div>
  );
};

export default App;
