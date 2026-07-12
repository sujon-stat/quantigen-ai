import React from 'react';
import { 
  Home, 
  FolderOpen, 
  Database, 
  Sparkles, 
  Table2, 
  BarChart3, 
  FileText, 
  Code2, 
  Settings, 
  ChevronLeft, 
  ChevronRight, 
  ShieldAlert, 
  Filter, 
  Sliders 
} from 'lucide-react';

export type WorkspaceNavTab = 
  | 'home' 
  | 'projects' 
  | 'data' 
  | 'cleaning' 
  | 'analysis' 
  | 'ai' 
  | 'tables' 
  | 'figures' 
  | 'reports' 
  | 'code' 
  | 'settings'
  | 'canvas';

interface LeftSidebarNavProps {
  activeTab: WorkspaceNavTab;
  onSelectTab: (tab: WorkspaceNavTab) => void;
  isCollapsed: boolean;
  onToggleCollapse: () => void;
  mode: 'beginner' | 'expert';
  onToggleMode: (mode: 'beginner' | 'expert') => void;
  datasetLoaded: boolean;
  analysisCompleted: boolean;
}

export const LeftSidebarNav: React.FC<LeftSidebarNavProps> = ({
  activeTab,
  onSelectTab,
  isCollapsed,
  onToggleCollapse,
  mode,
  onToggleMode,
  datasetLoaded,
  analysisCompleted
}) => {
  const navItems = [
    { id: 'home', label: 'Home', icon: Home, badge: null, beginner: true },
    { id: 'canvas', label: 'Research Canvas', icon: Sliders, badge: 'NEW', beginner: true },
    { id: 'projects', label: 'Projects', icon: FolderOpen, badge: null, beginner: false },
    { id: 'data', label: 'Data', icon: Database, badge: datasetLoaded ? 'Ready' : null, beginner: true },
    { id: 'cleaning', label: 'Cleaning', icon: Filter, badge: null, beginner: false },
    { id: 'analysis', label: 'Analysis', icon: ShieldAlert, badge: analysisCompleted ? '✓' : null, beginner: true },
    { id: 'ai', label: 'AI Assistant', icon: Sparkles, badge: 'Gemini', beginner: true },
    { id: 'tables', label: 'Tables', icon: Table2, badge: null, beginner: true },
    { id: 'figures', label: 'Figures', icon: BarChart3, badge: null, beginner: true },
    { id: 'reports', label: 'Reports', icon: FileText, badge: null, beginner: true },
    { id: 'code', label: 'Generated Code', icon: Code2, badge: null, beginner: false },
    { id: 'settings', label: 'Settings', icon: Settings, badge: null, beginner: false },
  ];

  const visibleItems = mode === 'beginner' 
    ? navItems.filter(item => item.beginner || item.id === activeTab) 
    : navItems;

  return (
    <aside 
      className={`flex flex-col bg-slate-950/90 border-r border-white/10 transition-all duration-300 z-40 select-none ${
        isCollapsed ? 'w-16' : 'w-64'
      }`}
    >
      {/* Top Header Mode / Navigation Toggle Bar */}
      <div className="p-3 border-b border-white/10 flex items-center justify-between">
        {!isCollapsed && (
          <div className="flex items-center gap-1.5 px-2 py-1 rounded-lg bg-slate-900 border border-white/10 text-xs">
            <button
              onClick={() => onToggleMode('beginner')}
              className={`px-2 py-1 rounded font-bold transition-all ${
                mode === 'beginner' 
                  ? 'bg-sky-500 text-white shadow-sm' 
                  : 'text-slate-400 hover:text-white'
              }`}
            >
              Beginner
            </button>
            <button
              onClick={() => onToggleMode('expert')}
              className={`px-2 py-1 rounded font-bold transition-all ${
                mode === 'expert' 
                  ? 'bg-indigo-600 text-white shadow-sm' 
                  : 'text-slate-400 hover:text-white'
              }`}
            >
              Expert
            </button>
          </div>
        )}
        <button
          onClick={onToggleCollapse}
          title={isCollapsed ? 'Expand Navigation' : 'Collapse Navigation'}
          className="p-1.5 rounded-lg bg-slate-900 hover:bg-slate-800 text-slate-400 hover:text-white border border-white/10 mx-auto"
        >
          {isCollapsed ? <ChevronRight className="w-4 h-4" /> : <ChevronLeft className="w-4 h-4" />}
        </button>
      </div>

      {/* Mode Indicator Pill when Collapsed */}
      {isCollapsed && (
        <div className="px-2 py-2 border-b border-white/10 flex justify-center">
          <button
            onClick={() => onToggleMode(mode === 'beginner' ? 'expert' : 'beginner')}
            title={`Current Mode: ${mode.toUpperCase()} (Click to toggle)`}
            className={`w-10 h-7 rounded text-[10px] font-extrabold flex items-center justify-center transition-all ${
              mode === 'beginner' 
                ? 'bg-sky-500/20 text-sky-300 border border-sky-400/40' 
                : 'bg-indigo-500/20 text-indigo-300 border border-indigo-400/40'
            }`}
          >
            {mode === 'beginner' ? 'BEG' : 'EXP'}
          </button>
        </div>
      )}

      {/* Navigation List */}
      <div className="flex-1 overflow-y-auto py-3 px-2 space-y-1 custom-scrollbar">
        {visibleItems.map((item) => {
          const Icon = item.icon;
          const isActive = activeTab === item.id;
          return (
            <button
              key={item.id}
              onClick={() => onSelectTab(item.id as WorkspaceNavTab)}
              title={isCollapsed ? item.label : undefined}
              className={`w-full flex items-center gap-3 px-3 py-2.5 rounded-xl text-xs font-semibold transition-all group ${
                isActive
                  ? 'bg-gradient-to-r from-sky-500/20 to-blue-500/10 text-sky-300 border border-sky-400/40 shadow-sm'
                  : 'text-slate-300 hover:text-white hover:bg-white/5 border border-transparent'
              }`}
            >
              <Icon 
                className={`w-4 h-4 flex-shrink-0 transition-transform group-hover:scale-110 ${
                  isActive ? 'text-sky-400' : 'text-slate-400 group-hover:text-slate-200'
                }`} 
              />
              {!isCollapsed && (
                <div className="flex-1 flex items-center justify-between truncate">
                  <span className="truncate">{item.label}</span>
                  {item.badge && (
                    <span className={`px-1.5 py-0.5 rounded text-[10px] font-bold uppercase tracking-wider ${
                      item.badge === 'NEW' 
                        ? 'bg-emerald-500/20 text-emerald-300 border border-emerald-500/40' 
                        : item.badge === 'Gemini'
                        ? 'bg-amber-500/20 text-amber-300 border border-amber-500/40'
                        : item.badge === 'Ready' || item.badge === '✓'
                        ? 'bg-sky-500/20 text-sky-300 border border-sky-400/40'
                        : 'bg-slate-800 text-slate-300'
                    }`}>
                      {item.badge}
                    </span>
                  )}
                </div>
              )}
            </button>
          );
        })}
      </div>

      {/* Bottom Footer Mode Hint */}
      {!isCollapsed && (
        <div className="p-3 border-t border-white/10 bg-slate-900/60 text-[11px] text-slate-400 leading-snug">
          <div className="flex items-center gap-1.5 text-sky-300 font-bold mb-1">
            <Sparkles className="w-3.5 h-3.5 text-amber-300" />
            <span>{mode === 'beginner' ? 'Beginner Mode' : 'Expert Mode Active'}</span>
          </div>
          {mode === 'beginner' 
            ? 'Simplified view. Switch to Expert Mode anytime for tuning, Bayesian priors, & custom code syntax.'
            : 'Unrestricted view with full access to diagnostics, code generators, & hyperparameters.'}
        </div>
      )}
    </aside>
  );
};
