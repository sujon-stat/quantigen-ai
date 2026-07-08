import React, { useState } from 'react';
import { Sparkles, Play, ShieldAlert, CheckCircle2, MessageSquare, BookOpen, AlertTriangle } from 'lucide-react';
import type { DatasetSummary, IntentRecommendation, AnalysisResponse } from '../../types/statmind';
import { api } from '../../api/client';

interface AnalysisStudioProps {
  dataset: DatasetSummary;
  onAnalysisCompleted: (response: AnalysisResponse) => void;
}

export const AnalysisStudio: React.FC<AnalysisStudioProps> = ({
  dataset,
  onAnalysisCompleted,
}) => {
  const [activeTab, setActiveTab] = useState<'consultant' | 'registry'>('consultant');
  
  // Consultant State
  const [query, setQuery] = useState('');
  const [loadingRecommend, setLoadingRecommend] = useState(false);
  const [recommendation, setRecommendation] = useState<IntentRecommendation | null>(null);
  const [consultMessage, setConsultMessage] = useState<string | null>(null);

  // Manual Selection State
  const [_selectedMethodId, setSelectedMethodId] = useState<string>('ttest_independent');
  const [boundVariables, setBoundVariables] = useState<Record<string, any>>({});
  const [loadingExecute, setLoadingExecute] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const methodsRegistry = [
    {
      family: 'Group Comparisons',
      items: [
        { id: 'ttest_independent', name: 'Independent Samples T-Test', desc: 'Compares means of two independent groups on a continuous dependent variable.', req: ['dependent', 'grouping'] },
        { id: 'anova_oneway', name: 'One-Way ANOVA', desc: 'Compares means across three or more groups on a continuous dependent variable.', req: ['dependent', 'grouping'] },
        { id: 'mann_whitney_u', name: 'Mann-Whitney U Test', desc: 'Nonparametric comparison of two groups when normality assumption is violated.', req: ['dependent', 'grouping'] },
        { id: 'kruskal_wallis', name: 'Kruskal-Wallis H Test', desc: 'Nonparametric comparison across three or more groups when normality fails.', req: ['dependent', 'grouping'] },
      ]
    },
    {
      family: 'Correlation & Association',
      items: [
        { id: 'pearson_correlation', name: 'Pearson Correlation', desc: 'Evaluates linear relationships between two continuous variables.', req: ['var1', 'var2'] },
        { id: 'chi_square_independence', name: 'Chi-Square Test of Independence', desc: 'Assesses association between two categorical variables.', req: ['row_var', 'col_var'] },
      ]
    },
    {
      family: 'Regression Models',
      items: [
        { id: 'linear_regression', name: 'Simple Linear Regression', desc: 'Predicts a continuous outcome using a single continuous predictor.', req: ['dependent', 'independent'] },
        { id: 'multiple_linear_regression', name: 'Multiple Linear Regression', desc: 'Predicts a continuous outcome using multiple predictors with VIF diagnostics.', req: ['dependent', 'independent'] },
        { id: 'binary_logistic_regression', name: 'Binary Logistic Regression', desc: 'Predicts a binary outcome and outputs exact Odds Ratios and ROC curves.', req: ['dependent', 'independent'] },
      ]
    }
  ];

  const handleRecommend = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!query.trim()) return;
    setLoadingRecommend(true);
    setError(null);
    try {
      const cols = dataset.columns || (dataset as any).variables || [];
      const res = await api.recommendMethod(query, cols);
      setRecommendation(res.recommendation);
      setConsultMessage(res.message);
      setSelectedMethodId(res.recommendation.method_id);
      
      // Auto-populate bound variables from AI suggestion
      const autoBindings: Record<string, any> = {};
      Object.entries(res.recommendation.suggested_variables).forEach(([k, v]) => {
        if (v) autoBindings[k] = v;
      });
      setBoundVariables(autoBindings);
    } catch (err: any) {
      setError(err.response?.data?.detail?.message || 'Failed to generate recommendation');
    } finally {
      setLoadingRecommend(false);
    }
  };

  const handleExecute = async (methodIdToRun: string, variablesToBind: Record<string, any>) => {
    setLoadingExecute(true);
    setError(null);
    try {
      const res = await api.executeAnalysis(dataset.dataset_id, methodIdToRun, variablesToBind);
      onAnalysisCompleted(res);
    } catch (err: any) {
      setError(err.response?.data?.detail?.message || err.message || 'Analysis execution failed');
    } finally {
      setLoadingExecute(false);
    }
  };

  const handleVariableSelect = (key: string, value: string | string[]) => {
    setBoundVariables((prev) => ({
      ...prev,
      [key]: value,
    }));
  };

  return (
    <div className="space-y-6 animate-fade-in">
      {/* Mode Switcher Tabs */}
      <div className="flex items-center justify-between border-b border-white/10 pb-4">
        <div className="flex items-center gap-3">
          <button
            onClick={() => setActiveTab('consultant')}
            className={`flex items-center gap-2 px-5 py-2.5 rounded-xl font-semibold text-sm transition-all ${
              activeTab === 'consultant'
                ? 'bg-gradient-to-r from-sky-500 to-blue-600 text-white shadow-lg shadow-sky-500/20'
                : 'glass-panel text-slate-400 hover:text-white'
            }`}
          >
            <Sparkles className="w-4 h-4 text-amber-300" />
            <span>Natural Language AI Consultant (Recommended)</span>
          </button>

          <button
            onClick={() => setActiveTab('registry')}
            className={`flex items-center gap-2 px-5 py-2.5 rounded-xl font-semibold text-sm transition-all ${
              activeTab === 'registry'
                ? 'bg-gradient-to-r from-sky-500 to-blue-600 text-white shadow-lg shadow-sky-500/20'
                : 'glass-panel text-slate-400 hover:text-white'
            }`}
          >
            <BookOpen className="w-4 h-4" />
            <span>Method Explorer Registry (10 Methods)</span>
          </button>
        </div>
      </div>

      {error && (
        <div className="p-4 rounded-xl bg-rose-500/10 border border-rose-500/30 text-rose-300 text-sm flex items-center gap-3">
          <AlertTriangle className="w-5 h-5 flex-shrink-0" />
          <span>{error}</span>
        </div>
      )}

      {/* Tab 1: AI Consultant Mode */}
      {activeTab === 'consultant' && (
        <div className="space-y-6">
          <div className="glass-panel p-6 space-y-4 border-t-2 border-t-sky-400">
            <div className="flex items-center gap-3">
              <div className="w-10 h-10 rounded-xl bg-amber-400/10 border border-amber-400/30 flex items-center justify-center">
                <Sparkles className="w-5 h-5 text-amber-300" />
              </div>
              <div>
                <h3 className="text-lg font-bold text-white">Tell us what you want to discover in plain English</h3>
                <p className="text-xs text-slate-400">
                  Example: <span className="italic text-sky-300">"Check if salary differs across department groups"</span> or <span className="italic text-sky-300">"Find out if GPA and GRE predict graduate admission"</span>
                </p>
              </div>
            </div>

            <form onSubmit={handleRecommend} className="flex gap-3">
              <input
                type="text"
                value={query}
                onChange={(e) => setQuery(e.target.value)}
                placeholder="Type your statistical hypothesis or question here..."
                className="flex-1 bg-slate-900/80 border border-white/10 rounded-xl px-4 py-3 text-sm text-white placeholder-slate-500 focus:outline-none focus:border-sky-400 transition-all"
              />
              <button type="submit" disabled={loadingRecommend || !query.trim()} className="btn-primary px-6">
                <Sparkles className="w-4 h-4" />
                <span>{loadingRecommend ? 'Consulting Engine...' : 'Get Recommendation'}</span>
              </button>
            </form>
          </div>

          {/* AI Recommendation Card */}
          {recommendation && (
            <div className="glass-panel p-6 space-y-6 border-l-4 border-l-sky-400 animate-fade-in">
              <div className="flex flex-col md:flex-row md:items-center justify-between gap-4">
                <div>
                  <span className="badge-role mb-2 inline-block">{recommendation.method_family}</span>
                  <h3 className="text-2xl font-bold text-white flex items-center gap-2">
                    <span>Recommended: {recommendation.method_name}</span>
                    <CheckCircle2 className="w-6 h-6 text-emerald-400" />
                  </h3>
                  <p className="text-sm text-slate-300 mt-1">{recommendation.rationale}</p>
                  {consultMessage && <p className="text-xs text-sky-300 mt-2 bg-sky-500/10 p-2.5 rounded-lg border border-sky-500/20">{consultMessage}</p>}
                </div>

                <div className="flex items-center gap-2 bg-amber-500/10 border border-amber-500/30 px-3.5 py-2 rounded-xl text-xs text-amber-300">
                  <ShieldAlert className="w-4 h-4 flex-shrink-0" />
                  <span>Assumption Shield Active: Automatically verifies diagnostics before revealing $p$-values.</span>
                </div>
              </div>

              {/* Variable Binding Confirmation Box */}
              <div className="bg-slate-900/60 border border-white/5 rounded-xl p-5 space-y-4">
                <h4 className="text-sm font-bold text-white flex items-center gap-2">
                  <MessageSquare className="w-4 h-4 text-sky-400" />
                  <span>Confirm Suggested Variable Bindings</span>
                </h4>

                <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                  {/* Dependent / Outcome Variable */}
                  <div>
                    <label className="block text-xs font-semibold text-slate-300 mb-1">
                      Dependent / Outcome Variable
                    </label>
                    <select
                      value={boundVariables['dependent'] || boundVariables['var1'] || boundVariables['row_var'] || ''}
                      onChange={(e) => {
                        if (recommendation.method_id.includes('correlation')) handleVariableSelect('var1', e.target.value);
                        else if (recommendation.method_id.includes('chi_square')) handleVariableSelect('row_var', e.target.value);
                        else handleVariableSelect('dependent', e.target.value);
                      }}
                      className="w-full bg-slate-900 border border-white/10 rounded-lg p-2.5 text-xs text-white focus:outline-none focus:border-sky-400"
                    >
                      <option value="">-- Select Variable --</option>
                      {(dataset.columns || (dataset as any).variables || []).map((col: any) => (
                        <option key={col.name} value={col.name}>
                          {col.name} ({col.role})
                        </option>
                      ))}
                    </select>
                  </div>

                  {/* Grouping / Predictor Variable */}
                  <div>
                    <label className="block text-xs font-semibold text-slate-300 mb-1">
                      Grouping / Independent Variable(s)
                    </label>
                    {recommendation.method_id.includes('multiple') || (Array.isArray(boundVariables['independent']) && boundVariables['independent'].length > 1) ? (
                      <select
                        multiple
                        value={Array.isArray(boundVariables['independent']) ? boundVariables['independent'] : []}
                        onChange={(e) => {
                          const selected = Array.from(e.target.selectedOptions, (opt) => opt.value);
                          handleVariableSelect('independent', selected);
                        }}
                        className="w-full bg-slate-900 border border-white/10 rounded-lg p-2.5 text-xs text-white h-24 focus:outline-none focus:border-sky-400"
                      >
                        {(dataset.columns || (dataset as any).variables || []).map((col: any) => (
                          <option key={col.name} value={col.name}>
                            {col.name} ({col.role})
                          </option>
                        ))}
                      </select>
                    ) : (
                      <select
                        value={boundVariables['grouping'] || boundVariables['independent'] || boundVariables['var2'] || boundVariables['col_var'] || ''}
                        onChange={(e) => {
                          if (recommendation.method_id.includes('correlation')) handleVariableSelect('var2', e.target.value);
                          else if (recommendation.method_id.includes('chi_square')) handleVariableSelect('col_var', e.target.value);
                          else if (recommendation.method_id.includes('ttest') || recommendation.method_id.includes('anova') || recommendation.method_id.includes('mann') || recommendation.method_id.includes('kruskal')) handleVariableSelect('grouping', e.target.value);
                          else handleVariableSelect('independent', e.target.value);
                        }}
                        className="w-full bg-slate-900 border border-white/10 rounded-lg p-2.5 text-xs text-white focus:outline-none focus:border-sky-400"
                      >
                        <option value="">-- Select Variable --</option>
                        {(dataset.columns || (dataset as any).variables || []).map((col: any) => (
                          <option key={col.name} value={col.name}>
                            {col.name} ({col.role})
                          </option>
                        ))}
                      </select>
                    )}
                  </div>
                </div>

                <div className="pt-3 flex justify-end">
                  <button
                    onClick={() => handleExecute(recommendation.method_id, boundVariables)}
                    disabled={loadingExecute}
                    className="btn-primary px-8 py-3 text-sm shadow-xl shadow-sky-500/30"
                  >
                    <Play className="w-4 h-4 fill-current" />
                    <span>{loadingExecute ? 'Running Statistical & Diagnostic Checks...' : `Execute ${recommendation.method_name}`}</span>
                  </button>
                </div>
              </div>
            </div>
          )}
        </div>
      )}

      {/* Tab 2: Method Explorer Registry Mode */}
      {activeTab === 'registry' && (
        <div className="space-y-6 animate-fade-in">
          {methodsRegistry.map((group) => (
            <div key={group.family} className="space-y-3">
              <h3 className="text-md font-bold text-sky-400 tracking-wide uppercase text-xs flex items-center gap-2">
                <BookOpen className="w-4 h-4" />
                <span>{group.family}</span>
              </h3>
              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                {group.items.map((m) => (
                  <div
                    key={m.id}
                    onClick={() => {
                      setSelectedMethodId(m.id);
                      setActiveTab('consultant');
                      setQuery(`I want to run ${m.name}`);
                    }}
                    className="glass-card-interactive p-5 space-y-2"
                  >
                    <div className="flex items-center justify-between">
                      <h4 className="font-bold text-white text-base">{m.name}</h4>
                      <span className="text-[10px] px-2 py-0.5 rounded bg-white/5 border border-white/10 text-slate-300 font-mono">
                        {m.id}
                      </span>
                    </div>
                    <p className="text-xs text-slate-400 leading-relaxed">{m.desc}</p>
                    <div className="pt-2 flex items-center justify-between text-xs text-sky-300 font-medium">
                      <span>Requires: {m.req.join(', ')}</span>
                      <span>Select Method &rarr;</span>
                    </div>
                  </div>
                ))}
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  );
};
