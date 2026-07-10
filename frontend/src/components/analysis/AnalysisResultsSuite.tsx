import React, { useState, useEffect } from 'react';
import { LayoutGrid, Sparkles, BarChart3 } from 'lucide-react';
import type { DatasetSummary, AnalysisResponse } from '../../types/statmind';
import { AnalysisStudio } from './AnalysisStudio';
import { ResultsCenter } from '../results/ResultsCenter';

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

  const handleRunAndSwitch = (res: AnalysisResponse) => {
    onAnalysisCompleted(res);
    setLeftSubTab('results');
  };

  return (
    <div className="space-y-4 animate-fade-in">
      {/* Main Container with Full Screen Width & Scrolling */}
      <div className="flex flex-col w-full">
        {/* Larger Screen Portion (Studio & Results) */}
        <div className="w-full flex flex-col min-w-0 pr-0 transition-all duration-150">
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
                  if (!analysisResponse) {
                    alert("Please execute an analysis from the Method Studio first!");
                    setLeftSubTab('studio');
                  } else {
                    setLeftSubTab('results');
                  }
                }}
                className={`px-4 py-2.5 rounded-xl text-xs sm:text-sm font-bold flex items-center gap-2 transition-all select-none ${
                  leftSubTab === 'results'
                    ? 'bg-gradient-to-r from-emerald-500 to-teal-600 text-white shadow-md shadow-emerald-500/20'
                    : 'text-slate-300 hover:text-white hover:bg-white/5'
                }`}
              >
                <Sparkles className="w-4 h-4 text-amber-300" />
                <span>📊 2. Assumption Shield & Publication Results</span>
              </button>
            </div>

            {leftSubTab === 'results' && analysisResponse && (
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

          {/* SubTab Content View */}
          <div className="flex-1 pb-6 w-full">
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
      </div>
    </div>
  );
};
