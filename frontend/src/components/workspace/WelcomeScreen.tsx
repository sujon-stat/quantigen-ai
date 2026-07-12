import React from 'react';
import { 
  FolderOpen, 
  UploadCloud, 
  Sparkles, 
  History, 
  GraduationCap, 
  Star, 
  ArrowRight, 
  ShieldCheck, 
  Cpu, 
  FileText 
} from 'lucide-react';
import type { DatasetSummary, AnalysisResponse } from '../../types/statmind';

interface WelcomeScreenProps {
  onAction: (action: 'import' | 'ai' | 'resume' | 'learn' | 'projects') => void;
  dataset: DatasetSummary | null;
  recentAnalysis: AnalysisResponse | null;
  historyCount: number;
}

export const WelcomeScreen: React.FC<WelcomeScreenProps> = ({
  onAction,
  dataset,
  recentAnalysis,
  historyCount
}) => {
  const nRows = dataset?.total_rows || dataset?.n_rows || 0;
  const nCols = dataset?.total_columns || (dataset?.columns ? dataset.columns.length : 0) || dataset?.n_cols || 0;
  const dsName = dataset?.filename || (dataset as any)?.name || "Active Dataset";

  return (
    <div className="w-full max-w-6xl mx-auto py-8 px-4 sm:px-6 lg:px-8 space-y-10 animate-fade-in">
      {/* Top Welcome Banner */}
      <div className="relative overflow-hidden rounded-3xl bg-gradient-to-r from-slate-900 via-sky-950/80 to-indigo-950/90 border border-sky-400/30 p-8 sm:p-10 shadow-2xl shadow-sky-950/40">
        <div className="absolute top-0 right-0 -mt-10 -mr-10 w-80 h-80 bg-sky-500/10 rounded-full blur-3xl pointer-events-none" />
        <div className="absolute bottom-0 right-1/4 -mb-10 w-60 h-60 bg-emerald-500/10 rounded-full blur-3xl pointer-events-none" />
        
        <div className="relative z-10 space-y-4">
          <div className="inline-flex items-center gap-2 px-3 py-1 rounded-full bg-sky-500/20 border border-sky-400/40 text-sky-300 text-xs font-bold tracking-wide uppercase">
            <Sparkles className="w-3.5 h-3.5 text-amber-300 animate-spin-slow" />
            <span>StatAid Studio Workspace</span>
          </div>
          
          <h1 className="text-3xl sm:text-4xl md:text-5xl font-black text-white tracking-tight leading-tight">
            👋 Welcome back, <span className="text-transparent bg-clip-text bg-gradient-to-r from-sky-400 via-emerald-400 to-indigo-400">Sujon</span>.
          </h1>
          
          <p className="text-base sm:text-lg text-slate-300 max-w-2xl font-medium">
            What would you like to do today? Your intelligent scientific workspace is ready — from raw data to publication-ready science with complete transparency and zero black boxes.
          </p>

          {/* Quick Stats Pill Bar */}
          <div className="pt-4 flex flex-wrap items-center gap-4 text-xs font-semibold text-slate-300">
            <div className="flex items-center gap-1.5 px-3 py-1.5 rounded-xl bg-slate-800/80 border border-white/10">
              <ShieldCheck className="w-4 h-4 text-emerald-400" />
              <span>Assumption Shield Active</span>
            </div>
            <div className="flex items-center gap-1.5 px-3 py-1.5 rounded-xl bg-slate-800/80 border border-white/10">
              <Cpu className="w-4 h-4 text-sky-400" />
              <span>9 Modular Data & Statistical Engines</span>
            </div>
            <div className="flex items-center gap-1.5 px-3 py-1.5 rounded-xl bg-slate-800/80 border border-white/10">
              <Star className="w-4 h-4 text-amber-400" />
              <span>APA 7th & Q1 Journal Export Ready</span>
            </div>
          </div>
        </div>
      </div>

      {/* Primary Action Cards Grid */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-6">
        {/* Card 1: Import Dataset */}
        <div 
          onClick={() => onAction('import')}
          className="group relative overflow-hidden rounded-2xl bg-slate-900/90 border-2 border-sky-500/40 hover:border-sky-400 p-6 shadow-xl hover:shadow-sky-500/20 transition-all duration-300 cursor-pointer flex flex-col justify-between"
        >
          <div className="space-y-4">
            <div className="w-12 h-12 rounded-2xl bg-gradient-to-br from-sky-500 to-blue-600 flex items-center justify-center text-white shadow-lg shadow-sky-500/30 group-hover:scale-110 transition-transform">
              <UploadCloud className="w-6 h-6" />
            </div>
            <div>
              <h3 className="text-xl font-bold text-white group-hover:text-sky-300 transition-colors">
                📊 Import Dataset
              </h3>
              <p className="text-xs text-slate-400 mt-1.5 leading-relaxed">
                Upload CSV, Excel, SPSS (.sav), Stata (.dta), SAS, Parquet, RData, or Survey specifications. Instantly profiles numeric, binary, and missing distributions.
              </p>
            </div>
          </div>
          <div className="pt-6 flex items-center justify-between text-xs font-bold text-sky-400 group-hover:text-sky-300">
            <span>Launch Data Engine</span>
            <ArrowRight className="w-4 h-4 group-hover:translate-x-1 transition-transform" />
          </div>
        </div>

        {/* Card 2: Ask AI */}
        <div 
          onClick={() => onAction('ai')}
          className="group relative overflow-hidden rounded-2xl bg-slate-900/90 border-2 border-amber-500/40 hover:border-amber-400 p-6 shadow-xl hover:shadow-amber-500/20 transition-all duration-300 cursor-pointer flex flex-col justify-between"
        >
          <div className="space-y-4">
            <div className="w-12 h-12 rounded-2xl bg-gradient-to-br from-amber-400 to-orange-600 flex items-center justify-center text-slate-950 shadow-lg shadow-amber-500/30 group-hover:scale-110 transition-transform">
              <Sparkles className="w-6 h-6 animate-spin-slow" />
            </div>
            <div>
              <h3 className="text-xl font-bold text-white group-hover:text-amber-300 transition-colors">
                🧠 Ask AI Consultant
              </h3>
              <p className="text-xs text-slate-400 mt-1.5 leading-relaxed">
                Describe your research goal in plain English. Get instant method recommendations, hypothesis checks, VIF explanations, and APA 7th interpretations.
              </p>
            </div>
          </div>
          <div className="pt-6 flex items-center justify-between text-xs font-bold text-amber-400 group-hover:text-amber-300">
            <span>Open AI Drawer</span>
            <ArrowRight className="w-4 h-4 group-hover:translate-x-1 transition-transform" />
          </div>
        </div>

        {/* Card 3: Continue Last Analysis */}
        <div 
          onClick={() => onAction('resume')}
          className={`group relative overflow-hidden rounded-2xl p-6 shadow-xl transition-all duration-300 flex flex-col justify-between ${
            dataset || recentAnalysis
              ? 'bg-slate-900/90 border-2 border-emerald-500/40 hover:border-emerald-400 hover:shadow-emerald-500/20 cursor-pointer'
              : 'bg-slate-900/40 border border-white/10 opacity-70 cursor-not-allowed'
          }`}
        >
          <div className="space-y-4">
            <div className="w-12 h-12 rounded-2xl bg-gradient-to-br from-emerald-500 to-teal-600 flex items-center justify-center text-white shadow-lg shadow-emerald-500/30 group-hover:scale-110 transition-transform">
              <History className="w-6 h-6" />
            </div>
            <div>
              <div className="flex items-center justify-between">
                <h3 className="text-xl font-bold text-white group-hover:text-emerald-300 transition-colors">
                  📄 Continue Analysis
                </h3>
                {dataset && (
                  <span className="px-2 py-0.5 rounded-full bg-emerald-500/20 text-emerald-300 text-[10px] font-extrabold uppercase tracking-wider border border-emerald-500/30">
                    Active
                  </span>
                )}
              </div>
              <p className="text-xs text-slate-400 mt-1.5 leading-relaxed">
                {dataset 
                  ? `Resume working on ${dsName} (${nRows} rows × ${nCols} variables).`
                  : 'No active dataset in memory. Import a file to unlock continuous analysis preservation.'}
              </p>
            </div>
          </div>
          <div className="pt-6 flex items-center justify-between text-xs font-bold text-emerald-400 group-hover:text-emerald-300">
            <span>{dataset ? 'Resume Active Workspace' : 'Select a Dataset First'}</span>
            <ArrowRight className="w-4 h-4 group-hover:translate-x-1 transition-transform" />
          </div>
        </div>

        {/* Card 4: Open Project / Portfolio */}
        <div 
          onClick={() => onAction('projects')}
          className="group relative overflow-hidden rounded-2xl bg-slate-900/90 border border-white/10 hover:border-indigo-400/60 p-6 shadow-xl hover:shadow-indigo-500/10 transition-all duration-300 cursor-pointer flex flex-col justify-between"
        >
          <div className="space-y-4">
            <div className="w-12 h-12 rounded-2xl bg-gradient-to-br from-indigo-500 to-purple-600 flex items-center justify-center text-white shadow-lg shadow-indigo-500/30 group-hover:scale-110 transition-transform">
              <FolderOpen className="w-6 h-6" />
            </div>
            <div>
              <h3 className="text-xl font-bold text-white group-hover:text-indigo-300 transition-colors">
                📁 Projects & Portfolio
              </h3>
              <p className="text-xs text-slate-400 mt-1.5 leading-relaxed">
                Manage saved session models, compile multi-study publication suites, and export to Word (.doc), PDF, HTML, or reproducible RMarkdown (.Rmd).
              </p>
            </div>
          </div>
          <div className="pt-6 flex items-center justify-between text-xs font-bold text-indigo-400 group-hover:text-indigo-300">
            <span>{historyCount > 0 ? `${historyCount} Saved Analyses` : 'Open Project Manager'}</span>
            <ArrowRight className="w-4 h-4 group-hover:translate-x-1 transition-transform" />
          </div>
        </div>

        {/* Card 5: Learn Statistics */}
        <div 
          onClick={() => onAction('learn')}
          className="group relative overflow-hidden rounded-2xl bg-slate-900/90 border border-white/10 hover:border-purple-400/60 p-6 shadow-xl hover:shadow-purple-500/10 transition-all duration-300 cursor-pointer flex flex-col justify-between"
        >
          <div className="space-y-4">
            <div className="w-12 h-12 rounded-2xl bg-gradient-to-br from-purple-500 to-pink-600 flex items-center justify-center text-white shadow-lg shadow-purple-500/30 group-hover:scale-110 transition-transform">
              <GraduationCap className="w-6 h-6" />
            </div>
            <div>
              <h3 className="text-xl font-bold text-white group-hover:text-purple-300 transition-colors">
                🎓 Learn Statistics
              </h3>
              <p className="text-xs text-slate-400 mt-1.5 leading-relaxed">
                Interactive guides covering p-value common misconceptions, Welch vs Student t-tests, VIF multicollinearity limits, and Power/Sample size theory.
              </p>
            </div>
          </div>
          <div className="pt-6 flex items-center justify-between text-xs font-bold text-purple-400 group-hover:text-purple-300">
            <span>Explore Statistical Theory</span>
            <ArrowRight className="w-4 h-4 group-hover:translate-x-1 transition-transform" />
          </div>
        </div>

        {/* Card 6: Recent & Demo Datasets */}
        <div 
          onClick={() => onAction('import')}
          className="group relative overflow-hidden rounded-2xl bg-slate-900/90 border border-white/10 hover:border-teal-400/60 p-6 shadow-xl hover:shadow-teal-500/10 transition-all duration-300 cursor-pointer flex flex-col justify-between"
        >
          <div className="space-y-4">
            <div className="w-12 h-12 rounded-2xl bg-gradient-to-br from-teal-500 to-emerald-600 flex items-center justify-center text-white shadow-lg shadow-teal-500/30 group-hover:scale-110 transition-transform">
              <Star className="w-6 h-6" />
            </div>
            <div>
              <h3 className="text-xl font-bold text-white group-hover:text-teal-300 transition-colors">
                ⭐ Recent & Demo Data
              </h3>
              <p className="text-xs text-slate-400 mt-1.5 leading-relaxed">
                Load pre-configured clinical trial datasets, survey response weights, and regression benchmark tables to test diagnostic assumptions immediately.
              </p>
            </div>
          </div>
          <div className="pt-6 flex items-center justify-between text-xs font-bold text-teal-400 group-hover:text-teal-300">
            <span>Launch Benchmark Studio</span>
            <ArrowRight className="w-4 h-4 group-hover:translate-x-1 transition-transform" />
          </div>
        </div>
      </div>

      {/* Active Session Summary Banner */}
      {dataset && (
        <div className="rounded-2xl bg-slate-900/90 border border-emerald-500/30 p-6 shadow-xl flex flex-col sm:flex-row items-center justify-between gap-6">
          <div className="flex items-center gap-4">
            <div className="w-12 h-12 rounded-xl bg-emerald-500/20 border border-emerald-500/40 flex items-center justify-center text-emerald-400 flex-shrink-0">
              <FileText className="w-6 h-6" />
            </div>
            <div>
              <div className="flex items-center gap-2">
                <h4 className="font-bold text-white text-base">
                  Active Dataset: {dsName}
                </h4>
                <span className="px-2 py-0.5 rounded-full bg-emerald-500/20 text-emerald-300 text-[10px] font-bold border border-emerald-500/30">
                  Ready in Workspace
                </span>
              </div>
              <p className="text-xs text-slate-400 mt-1">
                {nRows} cases ({dataset.missing_values_total || 0} missing) × {nCols} variables profiled (`{dataset.columns?.slice(0, 4).map((v: any) => v.name || v.id || v).join(', ')}{nCols > 4 ? '...' : ''}`)
              </p>
            </div>
          </div>
          <button
            onClick={() => onAction('resume')}
            className="w-full sm:w-auto px-6 py-3 rounded-xl bg-gradient-to-r from-emerald-600 to-teal-600 hover:from-emerald-500 hover:to-teal-500 text-white font-bold text-sm shadow-lg shadow-emerald-600/30 transition-all flex items-center justify-center gap-2"
          >
            <span>Proceed to Workspace</span>
            <ArrowRight className="w-4 h-4" />
          </button>
        </div>
      )}
    </div>
  );
};
