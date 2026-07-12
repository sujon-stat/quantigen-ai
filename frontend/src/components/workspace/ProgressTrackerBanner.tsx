import React from 'react';
import { Database, Filter, Activity, Table2, CheckCircle2 } from 'lucide-react';
import type { WorkspaceNavTab } from './LeftSidebarNav';

interface ProgressTrackerBannerProps {
  currentTab: WorkspaceNavTab;
  datasetLoaded: boolean;
  analysisCompleted: boolean;
  onSelectStep?: (tab: WorkspaceNavTab) => void;
}

export const ProgressTrackerBanner: React.FC<ProgressTrackerBannerProps> = ({
  currentTab,
  datasetLoaded,
  analysisCompleted,
  onSelectStep
}) => {
  const steps = [
    { id: 'data', label: '1. Import & Profile', icon: Database, tab: 'data' as WorkspaceNavTab, completed: datasetLoaded },
    { id: 'cleaning', label: '2. Assumption Shield', icon: Filter, tab: 'cleaning' as WorkspaceNavTab, completed: datasetLoaded },
    { id: 'analysis', label: '3. Statistical Engine', icon: Activity, tab: 'analysis' as WorkspaceNavTab, completed: analysisCompleted },
    { id: 'results', label: '4. APA Q1 Export', icon: Table2, tab: 'tables' as WorkspaceNavTab, completed: analysisCompleted }
  ];

  return (
    <div className="w-full bg-slate-900/90 border-b border-white/10 px-4 sm:px-6 py-3 shadow-md flex items-center justify-between gap-4 overflow-x-auto custom-scrollbar">
      <div className="flex items-center gap-2 text-xs font-bold text-slate-300">
        <span className="text-sky-400 uppercase tracking-wider font-mono text-[10px]">Pipeline Tracker</span>
        <span className="text-slate-600">•</span>
      </div>

      <div className="flex items-center gap-2 sm:gap-4 min-w-max">
        {steps.map((s, idx) => {
          const isActive = currentTab === s.tab || (s.id === 'results' && ['tables', 'figures', 'reports', 'code'].includes(currentTab));
          
          return (
            <React.Fragment key={s.id}>
              <button
                onClick={() => onSelectStep && onSelectStep(s.tab)}
                disabled={!datasetLoaded && idx > 0}
                className={`flex items-center gap-2 px-3.5 py-1.5 rounded-xl text-xs font-bold transition-all ${
                  isActive
                    ? 'bg-gradient-to-r from-sky-500 to-blue-600 text-white shadow-md shadow-sky-500/20 scale-105'
                    : s.completed
                    ? 'bg-emerald-500/10 text-emerald-300 border border-emerald-500/30 hover:bg-emerald-500/20'
                    : !datasetLoaded && idx > 0
                    ? 'bg-slate-950/40 text-slate-600 cursor-not-allowed border border-white/5'
                    : 'bg-slate-950 text-slate-400 hover:text-white border border-white/10'
                }`}
              >
                <s.icon className={`w-3.5 h-3.5 ${isActive ? 'text-white' : s.completed ? 'text-emerald-400' : 'text-slate-500'}`} />
                <span>{s.label}</span>
                {s.completed && !isActive && <CheckCircle2 className="w-3.5 h-3.5 text-emerald-400 ml-1" />}
              </button>
              {idx < steps.length - 1 && (
                <div className="w-4 sm:w-8 h-[2px] bg-white/10 rounded-full flex-shrink-0" />
              )}
            </React.Fragment>
          );
        })}
      </div>
    </div>
  );
};
