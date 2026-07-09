import React from 'react';
import { ShieldCheck, Database, Sparkles, BarChart3, CheckCircle2, Sun, Moon, RotateCcw } from 'lucide-react';
import { QuantigenLogo } from '../common/QuantigenLogo';

interface HeaderProps {
  activeStep: 1 | 2 | 3;
  setActiveStep: (step: 1 | 2 | 3) => void;
  datasetLoaded: boolean;
  analysisCompleted: boolean;
  backendConnected: boolean;
  theme: 'dark' | 'light';
  onToggleTheme: () => void;
  onResetSession: () => void;
}

export const Header: React.FC<HeaderProps> = ({
  activeStep,
  setActiveStep,
  datasetLoaded,
  analysisCompleted,
  backendConnected,
  theme,
  onToggleTheme,
  onResetSession,
}) => {
  return (
    <header className="sticky top-0 z-50 glass-panel border-0 border-b border-white/10 rounded-none px-6 py-3 mb-6">
      <div className="max-w-7xl mx-auto flex items-center justify-between gap-4">
        {/* Logo & Brand */}
        <div className="flex items-center gap-4">
          <QuantigenLogo size="lg" interactive={true} />
          <div>
            <div className="flex items-center gap-2">
              <span className="font-bold text-xl tracking-tight bg-gradient-to-r from-white via-sky-200 to-sky-400 bg-clip-text text-transparent">
                Quantigen AI
              </span>
              <span className="text-xs px-2 py-0.5 rounded-full bg-sky-500/10 border border-sky-400/30 text-sky-300 font-medium animate-pulse">
                No-Code Statistical Platform
              </span>
            </div>
            <p className="text-xs text-slate-400">
              Reliability Over Intelligence • Assumption-First Transparency
            </p>
          </div>
        </div>

        {/* Workflow Steps */}
        <div className="hidden md:flex items-center gap-2 bg-slate-900/60 p-1.5 rounded-xl border border-white/5">
          <button
            onClick={() => setActiveStep(1)}
            className={`flex items-center gap-2 px-4 py-2 rounded-lg text-sm font-medium transition-all ${
              activeStep === 1
                ? 'bg-sky-500 text-white shadow-md shadow-sky-500/20'
                : 'text-slate-300 hover:text-white hover:bg-white/5'
            }`}
          >
            <Database className="w-4 h-4" />
            <span>1. Dataset Studio</span>
            {datasetLoaded && <CheckCircle2 className="w-3.5 h-3.5 text-emerald-400 ml-1" />}
          </button>

          <button
            onClick={() => datasetLoaded && setActiveStep(2)}
            disabled={!datasetLoaded}
            className={`flex items-center gap-2 px-4 py-2 rounded-lg text-sm font-medium transition-all ${
              activeStep === 2
                ? 'bg-sky-500 text-white shadow-md shadow-sky-500/20'
                : datasetLoaded
                ? 'text-slate-300 hover:text-white hover:bg-white/5'
                : 'text-slate-600 cursor-not-allowed'
            }`}
          >
            <Sparkles className="w-4 h-4" />
            <span>2. Analysis & AI Consultant</span>
          </button>

          <button
            onClick={() => analysisCompleted && setActiveStep(3)}
            disabled={!analysisCompleted}
            className={`flex items-center gap-2 px-4 py-2 rounded-lg text-sm font-medium transition-all ${
              activeStep === 3
                ? 'bg-sky-500 text-white shadow-md shadow-sky-500/20'
                : analysisCompleted
                ? 'text-slate-300 hover:text-white hover:bg-white/5'
                : 'text-slate-600 cursor-not-allowed'
            }`}
          >
            <BarChart3 className="w-4 h-4" />
            <span>3. Assumption Shield & Results</span>
          </button>
        </div>

        {/* Backend Status, Theme Toggle & Reset Session */}
        <div className="flex items-center gap-2.5">
          {/* Day / Night Theme Toggle */}
          <button
            onClick={onToggleTheme}
            title={`Switch to ${theme === 'dark' ? 'Day (Light)' : 'Night (Dark)'} Mode`}
            className="p-2 rounded-lg bg-slate-900/80 border border-white/10 text-slate-300 hover:text-white hover:border-sky-400/50 transition-all flex items-center gap-1.5 text-xs font-semibold"
          >
            {theme === 'dark' ? (
              <>
                <Sun className="w-4 h-4 text-amber-400 animate-spin-slow" />
                <span className="hidden sm:inline">Day Mode</span>
              </>
            ) : (
              <>
                <Moon className="w-4 h-4 text-sky-400" />
                <span className="hidden sm:inline">Night Mode</span>
              </>
            )}
          </button>

          {/* Reset Session / Clear Data */}
          {datasetLoaded && (
            <button
              onClick={() => {
                if (window.confirm('Are you sure you want to clear imported data and start over?')) {
                  onResetSession();
                }
              }}
              title="Clear imported dataset and reset current session"
              className="p-2 rounded-lg bg-rose-500/10 border border-rose-500/20 text-rose-300 hover:bg-rose-500/20 transition-all flex items-center gap-1.5 text-xs font-semibold"
            >
              <RotateCcw className="w-3.5 h-3.5" />
              <span className="hidden lg:inline">Reset</span>
            </button>
          )}

          <div className="hidden xl:flex items-center gap-2 px-3 py-1.5 rounded-lg bg-slate-900/80 border border-white/10 text-xs">
            <div
              className={`w-2 h-2 rounded-full ${
                backendConnected ? 'bg-emerald-400 animate-pulse' : 'bg-rose-500'
              }`}
            />
            <span className="text-slate-300 font-medium">
              {backendConnected ? 'Engine Online' : 'Offline'}
            </span>
          </div>

          <div className="hidden lg:flex items-center gap-1.5 px-3 py-1.5 rounded-lg bg-emerald-500/10 border border-emerald-500/20 text-emerald-300 text-xs font-semibold">
            <ShieldCheck className="w-4 h-4 text-emerald-400" />
            <span>R Verified</span>
          </div>
        </div>
      </div>
    </header>
  );
};
