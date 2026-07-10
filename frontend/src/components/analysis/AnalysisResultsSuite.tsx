import React, { useState, useEffect, useRef } from 'react';
import { LayoutGrid, ShieldCheck, Sparkles, GripVertical, BarChart3, MessageSquare } from 'lucide-react';
import type { DatasetSummary, AnalysisResponse } from '../../types/statmind';
import { AnalysisStudio } from './AnalysisStudio';
import { ResultsCenter } from '../results/ResultsCenter';
import { QuantigenAIChat } from '../common/QuantigenAIChat';

interface AnalysisResultsSuiteProps {
  dataset: DatasetSummary;
  analysisResponse: AnalysisResponse | null;
  onAnalysisCompleted: (response: AnalysisResponse) => void;
  analysisHistory: AnalysisResponse[];
  onRemoveHistoryItem: (historyId: string) => void;
  onClearHistory: () => void;
  onSelectHistoryItem: (item: AnalysisResponse) => void;
  theme: 'dark' | 'light';
}

export const AnalysisResultsSuite: React.FC<AnalysisResultsSuiteProps> = ({
  dataset,
  analysisResponse,
  onAnalysisCompleted,
  analysisHistory,
  onRemoveHistoryItem,
  onClearHistory,
  onSelectHistoryItem,
  theme,
}) => {
  // Left Pane SubTab ('studio' vs 'results')
  const [leftSubTab, setLeftSubTab] = useState<'studio' | 'results'>(() => {
    return analysisResponse ? 'results' : 'studio';
  });

  // Switch to results automatically when a new analysis is completed
  useEffect(() => {
    if (analysisResponse) {
      setLeftSubTab('results');
    }
  }, [analysisResponse]);

  // Resizable Split Screen Ratio (Left Pane width percentage)
  const [splitRatio, setSplitRatio] = useState<number>(() => {
    const saved = localStorage.getItem('quantigen_split_ratio');
    return saved ? Math.min(Math.max(Number(saved), 40), 82) : 66; // default 66% width for larger screen portion
  });
  const [isDragging, setIsDragging] = useState(false);
  const containerRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    if (!isDragging) return;

    const handleMouseMove = (e: MouseEvent) => {
      if (!containerRef.current) return;
      const rect = containerRef.current.getBoundingClientRect();
      const newRatio = ((e.clientX - rect.left) / rect.width) * 100;
      if (newRatio >= 40 && newRatio <= 82) {
        setSplitRatio(newRatio);
      }
    };

    const handleMouseUp = () => {
      setIsDragging(false);
      setSplitRatio((prev) => {
        localStorage.setItem('quantigen_split_ratio', String(Math.round(prev)));
        return prev;
      });
    };

    window.addEventListener('mousemove', handleMouseMove);
    window.addEventListener('mouseup', handleMouseUp);
    return () => {
      window.removeEventListener('mousemove', handleMouseMove);
      window.removeEventListener('mouseup', handleMouseUp);
    };
  }, [isDragging]);

  const handleMouseDown = (e: React.MouseEvent) => {
    e.preventDefault();
    setIsDragging(true);
  };

  const handleRunAndSwitch = (res: AnalysisResponse) => {
    onAnalysisCompleted(res);
    setLeftSubTab('results');
  };

  return (
    <div className="space-y-4 animate-fade-in">
      {/* Main Split-Screen Container with Distinguished Independent Scrolling */}
      <div
        ref={containerRef}
        className={`flex flex-col lg:flex-row items-stretch gap-0 lg:h-[calc(100vh-120px)] ${isDragging ? 'cursor-col-resize select-none' : ''}`}
      >
        {/* LEFT PANE: Larger Screen Portion (Studio & Results) - Independently Scrollable */}
        <div
          style={{ width: `${splitRatio}%` }}
          className="w-full lg:w-auto flex flex-col min-w-0 pr-0 lg:pr-3 transition-[width] duration-75 ease-out lg:h-full lg:overflow-y-auto custom-scrollbar"
        >
          {/* Top Navigation Switcher for Left Pane */}
          <div className="bg-slate-900/90 border border-white/10 p-2 rounded-2xl mb-5 shadow-lg flex flex-wrap items-center justify-between gap-3 flex-shrink-0">
            <div className="flex items-center gap-2">
              <button
                onClick={() => setLeftSubTab('studio')}
                className={`px-4 py-2.5 rounded-xl text-xs sm:text-sm font-bold flex items-center gap-2 transition-all select-none ${
                  leftSubTab === 'studio'
                    ? 'bg-gradient-to-r from-sky-500 to-blue-600 text-white shadow-md shadow-sky-500/20'
                    : 'text-slate-300 hover:text-white hover:bg-white/5'
                }`}
              >
                <LayoutGrid className="w-4 h-4" />
                <span>⚙️ 1. Method Studio & Variable Mapper</span>
              </button>

              <button
                onClick={() => {
                  if (analysisResponse) setLeftSubTab('results');
                }}
                disabled={!analysisResponse}
                className={`px-4 py-2.5 rounded-xl text-xs sm:text-sm font-bold flex items-center gap-2 transition-all select-none ${
                  !analysisResponse
                    ? 'text-slate-600 cursor-not-allowed bg-slate-950/40 border border-white/5'
                    : leftSubTab === 'results'
                    ? 'bg-gradient-to-r from-emerald-500 to-teal-600 text-white shadow-md shadow-emerald-500/20'
                    : 'text-emerald-400 hover:text-emerald-300 hover:bg-emerald-500/10 border border-emerald-500/30 animate-pulse'
                }`}
              >
                <ShieldCheck className="w-4 h-4" />
                <span>📊 2. Assumption Shield & Q1 Publication Results</span>
                {analysisResponse && (
                  <span className="ml-1 px-1.5 py-0.5 rounded text-[10px] font-mono bg-white/20 text-white">
                    Verified
                  </span>
                )}
              </button>
            </div>

            {analysisResponse && leftSubTab === 'results' && (
              <div className="flex items-center gap-2">
                <button
                  onClick={() => setLeftSubTab('studio')}
                  className="px-3 py-1.5 rounded-xl bg-sky-500/10 hover:bg-sky-500/20 text-sky-300 border border-sky-500/30 text-xs font-semibold flex items-center gap-1.5 transition-all"
                >
                  <Sparkles className="w-3.5 h-3.5" />
                  <span>+ Run Another Method</span>
                </button>
              </div>
            )}
          </div>

          {/* SubTab Content View - Left Pane */}
          <div className="flex-1 pb-6">
            {leftSubTab === 'studio' ? (
              <AnalysisStudio
                dataset={dataset}
                onAnalysisCompleted={handleRunAndSwitch}
                hideInlineChat={true}
              />
            ) : (
              analysisResponse ? (
                <ResultsCenter
                  response={analysisResponse}
                  dataset={dataset}
                  onAnalysisCompleted={handleRunAndSwitch}
                  onBackToAnalysis={() => setLeftSubTab('studio')}
                  analysisHistory={analysisHistory}
                  onRemoveHistoryItem={onRemoveHistoryItem}
                  onClearHistory={onClearHistory}
                  onSelectHistoryItem={onSelectHistoryItem}
                  theme={theme}
                  hideInlineChat={true}
                />
              ) : (
                <div className="glass-panel p-12 text-center space-y-4 border-dashed border-white/20">
                  <BarChart3 className="w-12 h-12 text-slate-500 mx-auto animate-bounce" />
                  <h3 className="text-lg font-bold text-white">No Verified Analysis Generated Yet</h3>
                  <p className="text-xs text-slate-400 max-w-md mx-auto">
                    Select a statistical method and map your variables in the Method Studio to run our Assumption-First engine and generate publication-ready APA tables.
                  </p>
                  <button
                    onClick={() => setLeftSubTab('studio')}
                    className="btn-primary px-6 py-2.5 text-sm"
                  >
                    Go to Method Studio
                  </button>
                </div>
              )
            )}
          </div>
        </div>

        {/* CENTER DRAGGABLE RESIZER BAR (Mouse Drag Splitter) */}
        <div
          onMouseDown={handleMouseDown}
          title="Drag left or right with your mouse to change the portion sizes"
          className={`hidden lg:flex flex-col items-center justify-center w-4 bg-slate-900/90 border-y border-x border-white/10 hover:border-sky-400/60 hover:bg-sky-500/20 active:bg-sky-500/40 cursor-col-resize transition-all select-none group relative rounded-xl my-0 mx-1 shadow-md self-stretch lg:h-full ${
            isDragging ? 'bg-sky-500/40 border-sky-400 shadow-xl shadow-sky-500/30 scale-x-110' : ''
          }`}
        >
          <div className="flex flex-col items-center justify-center gap-1.5 py-8">
            <GripVertical className={`w-4 h-6 transition-colors ${isDragging ? 'text-white' : 'text-slate-400 group-hover:text-sky-300'}`} />
            <div className={`w-1 h-1 rounded-full ${isDragging ? 'bg-white' : 'bg-slate-500 group-hover:bg-sky-300'}`} />
            <div className={`w-1 h-1 rounded-full ${isDragging ? 'bg-white' : 'bg-slate-500 group-hover:bg-sky-300'}`} />
            <div className={`w-1 h-1 rounded-full ${isDragging ? 'bg-white' : 'bg-slate-500 group-hover:bg-sky-300'}`} />
          </div>
        </div>

        {/* RIGHT PANE: AI Chatbot Portion - Independently Scrollable */}
        <div
          style={{ width: `${100 - splitRatio}%` }}
          className="w-full lg:w-auto flex flex-col min-w-0 pl-0 lg:pl-3 mt-8 lg:mt-0 transition-[width] duration-75 ease-out lg:h-full"
        >
          <div className="bg-slate-900/95 border border-white/10 rounded-2xl shadow-2xl overflow-hidden flex flex-col h-full min-h-[640px] lg:min-h-0">
            {/* AI Chatbot Header */}
            <div className="p-4 bg-gradient-to-r from-purple-900/60 via-indigo-900/50 to-sky-900/60 border-b border-white/10 flex items-center justify-between flex-shrink-0">
              <div className="flex items-center gap-3">
                <div className="w-9 h-9 rounded-xl bg-purple-500/20 border border-purple-400/40 flex items-center justify-center text-purple-300 shadow-md">
                  <MessageSquare className="w-5 h-5" />
                </div>
                <div>
                  <div className="flex items-center gap-2">
                    <h4 className="font-extrabold text-white text-sm sm:text-base tracking-wide">
                      AI Statistical Consultant
                    </h4>
                    <span className="px-1.5 py-0.5 rounded bg-purple-500/30 text-purple-200 font-mono text-[9px] border border-purple-400/30">Active 24/7</span>
                  </div>
                  <p className="text-[11px] text-purple-200/90 leading-tight">
                    Ask questions, verify assumptions, or get guidance
                  </p>
                </div>
              </div>

              <div className="flex items-center gap-1.5 text-xs text-slate-400">
                <span className="w-2 h-2 rounded-full bg-emerald-400 animate-pulse"></span>
                <span className="font-semibold text-slate-300 hidden sm:inline">Online</span>
              </div>
            </div>

            {/* AI Chatbot Body - Independently Scrollable */}
            <div className="flex-1 overflow-y-auto flex flex-col p-3 bg-slate-950/60 custom-scrollbar">
              <QuantigenAIChat
                title={analysisResponse ? `AI Consultant: ${(analysisResponse as any).method_name || 'Results'}` : "AI Statistical Consultant & Copilot"}
                subtitle="First asking clarifying questions, then suggesting exact statistical next steps according to your data"
                context={{
                  current_analysis: analysisResponse,
                  columns_metadata: dataset.columns || (dataset as any).variables || [],
                  dataset_id: dataset.dataset_id
                }}
                onExecuteMethod={(_mId) => {
                  setLeftSubTab('studio');
                }}
              />
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};
