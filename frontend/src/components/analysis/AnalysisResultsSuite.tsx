import React, { useState, useEffect, useRef } from 'react';
import { LayoutGrid, ShieldCheck, Sparkles, GripVertical, CheckCircle2, BarChart3, MessageSquare } from 'lucide-react';
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
    <div className="space-y-6 animate-fade-in">
      {/* Top Suite Title Banner */}
      <div className="glass-panel p-5 border-l-4 border-l-sky-400 flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div>
          <div className="flex items-center gap-2">
            <span className="px-2.5 py-0.5 rounded-full bg-sky-500/10 border border-sky-400/30 text-sky-300 font-bold text-xs tracking-wide uppercase">
              Unified Step 2 Suite
            </span>
            <span className="text-xs font-mono text-slate-400">• Drag mouse center splitter (`⋮`) to resize pane portions</span>
          </div>
          <h2 className="text-xl sm:text-2xl font-extrabold text-white mt-1.5 flex items-center gap-2.5">
            <span>2. Analysis, Shield & Results Suite</span>
            <Sparkles className="w-5 h-5 text-amber-300" />
          </h2>
        </div>

        <div className="flex items-center gap-2 bg-slate-900/80 p-1.5 rounded-xl border border-white/10 text-xs">
          <span className="text-slate-400 font-medium px-2">Split Layout:</span>
          <span className="px-2.5 py-1 rounded-lg bg-sky-500/20 text-sky-300 font-bold border border-sky-400/30">
            {Math.round(splitRatio)}% Studio/Results
          </span>
          <span className="text-slate-500">:</span>
          <span className="px-2.5 py-1 rounded-lg bg-purple-500/20 text-purple-300 font-bold border border-purple-400/30">
            {Math.round(100 - splitRatio)}% AI Chatbot
          </span>
        </div>
      </div>

      {/* Main Split-Screen Container */}
      <div
        ref={containerRef}
        className={`flex flex-col lg:flex-row items-stretch gap-0 select-none ${isDragging ? 'cursor-col-resize' : ''}`}
      >
        {/* LEFT PANE: Larger Screen Portion (Studio & Results) */}
        <div
          style={{ width: `${splitRatio}%` }}
          className="w-full lg:w-auto flex flex-col min-w-0 pr-0 lg:pr-3 transition-[width] duration-75 ease-out"
        >
          {/* Top Navigation Switcher for Left Pane */}
          <div className="bg-slate-900/90 border border-white/10 p-2 rounded-2xl mb-5 shadow-lg flex flex-wrap items-center justify-between gap-3">
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
                  leftSubTab === 'results'
                    ? 'bg-gradient-to-r from-emerald-600 to-teal-600 text-white shadow-md shadow-emerald-500/20'
                    : !analysisResponse
                    ? 'text-slate-500 cursor-not-allowed opacity-60'
                    : 'text-slate-300 hover:text-white hover:bg-white/5'
                }`}
              >
                <ShieldCheck className="w-4 h-4" />
                <span>📊 2. Assumption Shield & Q1 Publication Results</span>
                {analysisResponse && (
                  <span className="px-1.5 py-0.5 rounded-full bg-emerald-500/20 text-emerald-300 font-mono text-[10px] border border-emerald-400/30 flex items-center gap-1">
                    <CheckCircle2 className="w-3 h-3" />
                    <span>Verified</span>
                  </span>
                )}
              </button>
            </div>

            {leftSubTab === 'results' && analysisResponse && (
              <button
                onClick={() => setLeftSubTab('studio')}
                className="text-xs text-sky-400 hover:text-sky-300 font-semibold px-3 py-1.5 rounded-lg bg-sky-500/10 border border-sky-400/20 transition-colors"
              >
                + Run Another Method
              </button>
            )}
          </div>

          {/* Left Pane Content Render */}
          <div className="flex-1 min-w-0">
            {leftSubTab === 'studio' && (
              <div className="animate-fade-in">
                <AnalysisStudio
                  dataset={dataset}
                  onAnalysisCompleted={handleRunAndSwitch}
                  hideInlineChat={true}
                />
              </div>
            )}

            {leftSubTab === 'results' && analysisResponse && (
              <div className="animate-fade-in">
                <ResultsCenter
                  response={analysisResponse}
                  dataset={dataset}
                  onAnalysisCompleted={handleRunAndSwitch}
                  onBackToAnalysis={() => setLeftSubTab('studio')}
                  theme={theme}
                  analysisHistory={analysisHistory}
                  onRemoveHistoryItem={onRemoveHistoryItem}
                  onClearHistory={onClearHistory}
                  onSelectHistoryItem={onSelectHistoryItem}
                  hideInlineChat={true}
                />
              </div>
            )}

            {leftSubTab === 'results' && !analysisResponse && (
              <div className="glass-panel p-12 text-center space-y-4 border-dashed border-2 border-white/20">
                <BarChart3 className="w-12 h-12 text-slate-500 mx-auto" />
                <h3 className="text-lg font-bold text-white">No Active Analysis Results Yet</h3>
                <p className="text-sm text-slate-400 max-w-md mx-auto">
                  Please switch to the <span className="text-sky-400 font-semibold">Method Studio & Variable Mapper</span> tab, select your variables, and click <span className="text-sky-400 font-semibold">Run Verified Statistical Analysis</span> to generate your publication-ready outputs.
                </p>
                <button
                  onClick={() => setLeftSubTab('studio')}
                  className="btn-primary px-6 py-2.5 text-sm"
                >
                  Go to Method Studio
                </button>
              </div>
            )}
          </div>
        </div>

        {/* CENTER DRAGGABLE RESIZER BAR (Mouse Drag Splitter) */}
        <div
          onMouseDown={handleMouseDown}
          title="Drag left or right with your mouse to change the portion sizes"
          className={`hidden lg:flex flex-col items-center justify-center w-4 bg-slate-900/90 border-y border-x border-white/10 hover:border-sky-400/60 hover:bg-sky-500/20 active:bg-sky-500/40 cursor-col-resize transition-all select-none group relative rounded-xl my-2 mx-1 shadow-md ${
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

        {/* RIGHT PANE: AI Chatbot Portion */}
        <div
          style={{ width: `${100 - splitRatio}%` }}
          className="w-full lg:w-auto flex flex-col min-w-0 pl-0 lg:pl-3 mt-8 lg:mt-0 transition-[width] duration-75 ease-out"
        >
          <div className="bg-slate-900/95 border border-white/10 rounded-2xl shadow-2xl overflow-hidden flex flex-col h-full min-h-[720px] max-h-[1200px] sticky top-24">
            {/* AI Chatbot Header */}
            <div className="p-4 bg-gradient-to-r from-purple-900/60 via-indigo-900/50 to-sky-900/60 border-b border-white/10 flex items-center justify-between">
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

            {/* AI Chatbot Body */}
            <div className="flex-1 overflow-y-auto flex flex-col p-3 bg-slate-950/60">
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
