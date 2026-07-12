import React, { useState, useEffect } from 'react';
import { api } from '../../api/client';
import Plot from 'react-plotly.js';
import { 
  Zap, 
  Target, 
  CheckCircle2, 
  Copy, 
  Sliders, 
  BarChart2, 
  AlertTriangle,
  RefreshCw,
  Users,
  TrendingUp,
  Award,
  BookOpen
} from 'lucide-react';

interface QuantigenPowerStudioProps {
  onClose?: () => void;
}

export const QuantigenPowerStudio: React.FC<QuantigenPowerStudioProps> = ({ onClose }) => {
  const [mode, setMode] = useState<'a_priori' | 'post_hoc'>('a_priori');
  const [testType, setTestType] = useState<string>('ttest_independent');
  const [effectSize, setEffectSize] = useState<number>(0.50);
  const [alpha, setAlpha] = useState<number>(0.05);
  const [targetPower, setTargetPower] = useState<number>(0.80);
  const [sampleSize, setSampleSize] = useState<number>(100);
  const [groups, setGroups] = useState<number>(2);
  const [predictors, setPredictors] = useState<number>(2);

  const [loading, setLoading] = useState<boolean>(false);
  const [result, setResult] = useState<any>(null);
  const [error, setError] = useState<string | null>(null);
  const [copied, setCopied] = useState<boolean>(false);

  // Standard Effect Size Benchmarks
  const benchmarks: Record<string, { small: number; medium: number; large: number; metric: string; name: string }> = {
    ttest_independent: { small: 0.20, medium: 0.50, large: 0.80, metric: "Cohen's d", name: "Independent Samples T-Test" },
    ttest_paired: { small: 0.20, medium: 0.50, large: 0.80, metric: "Cohen's d_z", name: "Paired Samples T-Test" },
    anova_oneway: { small: 0.10, medium: 0.25, large: 0.40, metric: "Cohen's f", name: "One-Way ANOVA (k Groups)" },
    chi_square: { small: 0.10, medium: 0.30, large: 0.50, metric: "Cohen's w", name: "Chi-Square Test (Contingency / GOF)" },
    regression_linear: { small: 0.02, medium: 0.15, large: 0.35, metric: "Cohen's f²", name: "Multiple Linear Regression" },
    correlation: { small: 0.10, medium: 0.30, large: 0.50, metric: "Pearson's r", name: "Pearson Correlation" },
  };

  const currentBench = benchmarks[testType] || benchmarks['ttest_independent'];

  // Handle preset effect size click
  const handlePresetClick = (val: number) => {
    setEffectSize(val);
  };

  // Run calculation on parameter change
  useEffect(() => {
    runCalculation();
  }, [mode, testType, effectSize, alpha, targetPower, sampleSize, groups, predictors]);

  const runCalculation = async () => {
    setLoading(true);
    setError(null);
    try {
      if (mode === 'a_priori') {
        const res = await api.calculateSamplePower({
          test_type: testType,
          effect_size: effectSize,
          alpha: alpha,
          power: targetPower,
          groups: groups,
          predictors: predictors,
        });
        if (res.status === 'success') {
          setResult(res.result);
        }
      } else {
        const res = await api.calculatePostHocPower({
          test_type: testType,
          sample_size: sampleSize,
          effect_size: effectSize,
          alpha: alpha,
          groups: groups,
          predictors: predictors,
        });
        if (res.status === 'success') {
          setResult(res.result);
        }
      }
    } catch (err: any) {
      setError(err.message || 'Failed to calculate power analysis');
    } finally {
      setLoading(false);
    }
  };

  const handleCopyJustification = () => {
    if (!result?.justification) return;
    navigator.clipboard.writeText(result.justification);
    setCopied(true);
    setTimeout(() => setCopied(false), 3000);
  };

  return (
    <div className="bg-slate-900/95 border border-sky-500/30 rounded-2xl p-6 sm:p-8 shadow-2xl backdrop-blur-xl text-slate-100 max-w-7xl mx-auto my-6 animate-in fade-in zoom-in duration-300">
      {/* Header Bar */}
      <div className="flex flex-col sm:flex-row justify-between items-start sm:items-center gap-4 pb-6 border-b border-slate-800">
        <div className="flex items-center gap-3.5">
          <div className="w-12 h-12 rounded-xl bg-gradient-to-tr from-sky-500 to-indigo-600 flex items-center justify-center shadow-lg shadow-sky-500/20 text-white">
            <Zap className="w-6 h-6 animate-pulse" />
          </div>
          <div>
            <div className="flex items-center gap-2">
              <h2 className="text-xl sm:text-2xl font-black text-white tracking-tight">Quantigen Power & Sample Size Studio</h2>
              <span className="px-2.5 py-0.5 rounded-full text-xs font-bold bg-sky-500/20 text-sky-300 border border-sky-500/40 uppercase tracking-wide">
                G*Power Engine
              </span>
            </div>
            <p className="text-sm text-slate-400 font-medium">
              Exact mathematical A-Priori sample size determination & Post-Hoc statistical sensitivity curves for clinical & academic grants.
            </p>
          </div>
        </div>

        {onClose && (
          <button
            onClick={onClose}
            className="px-4 py-2 rounded-xl bg-slate-800 hover:bg-slate-700 text-slate-300 font-semibold text-sm transition-all border border-slate-700"
          >
            ✕ Close Studio
          </button>
        )}
      </div>

      {/* Mode Switcher Tabs */}
      <div className="grid grid-cols-1 sm:grid-cols-2 gap-4 mt-6">
        <button
          onClick={() => setMode('a_priori')}
          className={`flex items-center justify-center gap-3 p-4 rounded-xl font-bold text-sm sm:text-base transition-all border ${
            mode === 'a_priori'
              ? 'bg-gradient-to-r from-sky-600 to-indigo-600 text-white border-sky-400/60 shadow-lg shadow-sky-500/25 ring-2 ring-sky-400/30'
              : 'bg-slate-800/80 text-slate-400 border-slate-700 hover:bg-slate-800 hover:text-slate-200'
          }`}
        >
          <Target className="w-5 h-5 text-amber-300" />
          <span>🎯 A-Priori Sample Size Determination (Required N)</span>
        </button>

        <button
          onClick={() => setMode('post_hoc')}
          className={`flex items-center justify-center gap-3 p-4 rounded-xl font-bold text-sm sm:text-base transition-all border ${
            mode === 'post_hoc'
              ? 'bg-gradient-to-r from-indigo-600 to-purple-600 text-white border-indigo-400/60 shadow-lg shadow-indigo-500/25 ring-2 ring-indigo-400/30'
              : 'bg-slate-800/80 text-slate-400 border-slate-700 hover:bg-slate-800 hover:text-slate-200'
          }`}
        >
          <TrendingUp className="w-5 h-5 text-emerald-300" />
          <span>🔍 Post-Hoc Statistical Power Assessment (1 - β)</span>
        </button>
      </div>

      {/* Main Grid: Parameters (Left) vs Results & Curve (Right) */}
      <div className="grid grid-cols-1 lg:grid-cols-12 gap-8 mt-8">
        {/* Left Column: Parameter Controls */}
        <div className="lg:col-span-5 bg-slate-950/80 border border-slate-800/80 rounded-2xl p-6 space-y-6">
          <div className="flex items-center justify-between pb-3 border-b border-slate-800">
            <h3 className="font-bold text-base text-slate-200 flex items-center gap-2">
              <Sliders className="w-4 h-4 text-sky-400" /> Statistical Parameters
            </h3>
            <span className="text-xs text-slate-500 font-mono">Real-time Recalculation</span>
          </div>

          {/* Test Family Selector */}
          <div className="space-y-2">
            <label className="text-xs font-bold text-slate-300 uppercase tracking-wider block">
              Test Family / Statistical Method
            </label>
            <select
              value={testType}
              onChange={(e) => {
                const newTest = e.target.value;
                setTestType(newTest);
                const bench = benchmarks[newTest] || benchmarks['ttest_independent'];
                setEffectSize(bench.medium);
              }}
              className="w-full bg-slate-900 border border-slate-700 rounded-xl px-3.5 py-2.5 text-sm font-semibold text-slate-200 focus:outline-none focus:border-sky-500 transition-colors shadow-inner"
            >
              <option value="ttest_independent">Independent Samples T-Test (Two Groups)</option>
              <option value="ttest_paired">Paired Samples T-Test (Within-Subjects)</option>
              <option value="anova_oneway">One-Way ANOVA (k Groups / Treatment Levels)</option>
              <option value="chi_square">Chi-Square Test (Contingency Table / Goodness-of-Fit)</option>
              <option value="regression_linear">Multiple Linear Regression (p Predictors)</option>
              <option value="correlation">Pearson Correlation Coefficient</option>
            </select>
          </div>

          {/* Conditional Groups / Predictors input */}
          {testType === 'anova_oneway' && (
            <div className="space-y-2 animate-in fade-in">
              <label className="text-xs font-bold text-slate-300 uppercase tracking-wider block">
                Number of Comparison Groups (k)
              </label>
              <input
                type="number"
                min={2}
                max={20}
                value={groups}
                onChange={(e) => setGroups(Math.max(2, parseInt(e.target.value) || 2))}
                className="w-full bg-slate-900 border border-slate-700 rounded-xl px-3.5 py-2 text-sm font-mono text-sky-300 font-bold focus:outline-none focus:border-sky-500"
              />
            </div>
          )}

          {testType === 'chi_square' && (
            <div className="space-y-2 animate-in fade-in">
              <label className="text-xs font-bold text-slate-300 uppercase tracking-wider block">
                Total Contingency Cells or Groups
              </label>
              <input
                type="number"
                min={2}
                max={50}
                value={groups}
                onChange={(e) => setGroups(Math.max(2, parseInt(e.target.value) || 2))}
                className="w-full bg-slate-900 border border-slate-700 rounded-xl px-3.5 py-2 text-sm font-mono text-sky-300 font-bold focus:outline-none focus:border-sky-500"
              />
              <p className="text-[11px] text-slate-500">Degrees of freedom df ≈ {Math.max(1, groups - 1)}</p>
            </div>
          )}

          {testType === 'regression_linear' && (
            <div className="space-y-2 animate-in fade-in">
              <label className="text-xs font-bold text-slate-300 uppercase tracking-wider block">
                Number of Independent Predictors (p)
              </label>
              <input
                type="number"
                min={1}
                max={30}
                value={predictors}
                onChange={(e) => setPredictors(Math.max(1, parseInt(e.target.value) || 1))}
                className="w-full bg-slate-900 border border-slate-700 rounded-xl px-3.5 py-2 text-sm font-mono text-sky-300 font-bold focus:outline-none focus:border-sky-500"
              />
            </div>
          )}

          {/* Effect Size Input & Presets */}
          <div className="space-y-3">
            <div className="flex justify-between items-center">
              <label className="text-xs font-bold text-slate-300 uppercase tracking-wider block">
                Effect Size ({currentBench.metric})
              </label>
              <span className="text-sm font-mono font-black text-sky-400 bg-sky-950/60 px-2 py-0.5 rounded border border-sky-500/30">
                {effectSize.toFixed(3)}
              </span>
            </div>

            <input
              type="range"
              min={0.02}
              max={1.50}
              step={0.01}
              value={effectSize}
              onChange={(e) => setEffectSize(parseFloat(e.target.value) || 0.5)}
              className="w-full accent-sky-500 cursor-pointer"
            />

            {/* Clickable Cohen Benchmarks */}
            <div className="grid grid-cols-3 gap-2 pt-1">
              {[
                { label: 'Small', val: currentBench.small, desc: 'Subtle Effect' },
                { label: 'Medium', val: currentBench.medium, desc: 'Standard Target' },
                { label: 'Large', val: currentBench.large, desc: 'Strong Signal' },
              ].map((p) => (
                <button
                  key={p.label}
                  onClick={() => handlePresetClick(p.val)}
                  className={`flex flex-col items-center justify-center p-2 rounded-lg border text-xs transition-all ${
                    Math.abs(effectSize - p.val) < 0.005
                      ? 'bg-sky-500/20 border-sky-400 text-sky-200 font-bold shadow'
                      : 'bg-slate-900 border-slate-800 text-slate-400 hover:border-slate-700 hover:text-slate-300'
                  }`}
                >
                  <span className="font-bold">{p.label} ({p.val})</span>
                  <span className="text-[10px] opacity-75">{p.desc}</span>
                </button>
              ))}
            </div>
          </div>

          {/* Alpha (Significance Level) */}
          <div className="space-y-2">
            <label className="text-xs font-bold text-slate-300 uppercase tracking-wider block">
              Significance Level (α / Type I Error Rate)
            </label>
            <div className="grid grid-cols-3 gap-2">
              {[0.01, 0.05, 0.10].map((a) => (
                <button
                  key={a}
                  onClick={() => setAlpha(a)}
                  className={`py-2 rounded-xl text-xs font-bold transition-all border ${
                    alpha === a
                      ? 'bg-indigo-600 text-white border-indigo-400 shadow-lg shadow-indigo-500/20'
                      : 'bg-slate-900 border-slate-800 text-slate-400 hover:bg-slate-800'
                  }`}
                >
                  α = {a} ({a === 0.05 ? 'Standard' : a === 0.01 ? 'Strict' : 'Liberal'})
                </button>
              ))}
            </div>
          </div>

          {/* Conditional Input: Target Power vs Sample Size */}
          {mode === 'a_priori' ? (
            <div className="space-y-2 animate-in fade-in">
              <label className="text-xs font-bold text-slate-300 uppercase tracking-wider block">
                Desired Statistical Power (1 - β / Sensitivity)
              </label>
              <div className="grid grid-cols-3 gap-2">
                {[0.80, 0.90, 0.95].map((pw) => (
                  <button
                    key={pw}
                    onClick={() => setTargetPower(pw)}
                    className={`py-2 rounded-xl text-xs font-bold transition-all border ${
                      targetPower === pw
                        ? 'bg-emerald-600 text-white border-emerald-400 shadow-lg shadow-emerald-500/20'
                        : 'bg-slate-900 border-slate-800 text-slate-400 hover:bg-slate-800'
                    }`}
                  >
                    {pw * 100}% ({pw === 0.80 ? 'Standard' : pw === 0.90 ? 'High' : 'Ultra'})
                  </button>
                ))}
              </div>
            </div>
          ) : (
            <div className="space-y-2 animate-in fade-in">
              <label className="text-xs font-bold text-slate-300 uppercase tracking-wider block">
                Achieved Total Sample Size (N)
              </label>
              <input
                type="number"
                min={3}
                max={50000}
                value={sampleSize}
                onChange={(e) => setSampleSize(Math.max(3, parseInt(e.target.value) || 10))}
                className="w-full bg-slate-900 border border-slate-700 rounded-xl px-3.5 py-2.5 text-base font-mono text-emerald-300 font-black focus:outline-none focus:border-emerald-500"
              />
            </div>
          )}
        </div>

        {/* Right Column: Live Results & Power Curve Graph */}
        <div className="lg:col-span-7 space-y-6">
          {loading ? (
            <div className="h-96 flex flex-col items-center justify-center bg-slate-950/60 rounded-2xl border border-slate-800 p-8 text-center gap-4">
              <RefreshCw className="w-10 h-10 text-sky-400 animate-spin" />
              <p className="text-sm font-semibold text-slate-300">Evaluating non-centrality parameters & exact power curves...</p>
            </div>
          ) : error ? (
            <div className="bg-rose-950/50 border border-rose-500/50 rounded-2xl p-6 text-rose-200 flex items-start gap-3">
              <AlertTriangle className="w-6 h-6 text-rose-400 shrink-0 mt-0.5" />
              <div>
                <h4 className="font-bold text-base text-rose-100">Calculation Error</h4>
                <p className="text-sm text-rose-300/90 mt-1">{error}</p>
              </div>
            </div>
          ) : result ? (
            <>
              {/* Top KPI Result Banner */}
              <div
                className={`p-6 rounded-2xl border backdrop-blur-xl shadow-xl transition-all ${
                  mode === 'a_priori'
                    ? 'bg-gradient-to-r from-sky-950/80 via-indigo-950/80 to-slate-900 border-sky-500/40 shadow-sky-500/10'
                    : result.post_hoc_power >= 0.80
                    ? 'bg-gradient-to-r from-emerald-950/80 via-teal-950/80 to-slate-900 border-emerald-500/40 shadow-emerald-500/10'
                    : 'bg-gradient-to-r from-amber-950/80 via-orange-950/80 to-slate-900 border-amber-500/40 shadow-amber-500/10'
                }`}
              >
                <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
                  <div>
                    <span className="text-xs font-black uppercase tracking-widest text-sky-400 block mb-1">
                      {mode === 'a_priori' ? 'G*Power Required Sample Size Output' : 'Post-Hoc Sensitivity Output'}
                    </span>
                    <h3 className="text-2xl sm:text-3xl font-black text-white flex items-center gap-3">
                      {mode === 'a_priori' ? (
                        <>
                          <Users className="w-8 h-8 text-amber-400" />
                          <span>Required Total N = {result.n_required}</span>
                        </>
                      ) : (
                        <>
                          <Award className="w-8 h-8 text-emerald-400" />
                          <span>Achieved Power = {result.power_percentage}%</span>
                        </>
                      )}
                    </h3>
                  </div>

                  {mode === 'a_priori' && result.n_per_group && (
                    <div className="bg-slate-900/80 border border-slate-700/80 px-4 py-3 rounded-xl text-right">
                      <span className="text-xs text-slate-400 font-medium block">Per Comparison Group</span>
                      <span className="text-lg font-mono font-bold text-sky-300">n = {result.n_per_group} participants</span>
                    </div>
                  )}

                  {mode === 'post_hoc' && (
                    <div className="bg-slate-900/80 border border-slate-700/80 px-4 py-3 rounded-xl text-right">
                      <span className="text-xs text-slate-400 font-medium block">Power Category</span>
                      <span
                        className="text-sm font-bold block"
                        style={{ color: result.color_hex || '#38bdf8' }}
                      >
                        {result.power_category}
                      </span>
                    </div>
                  )}
                </div>

                <div className="mt-4 pt-4 border-t border-slate-800/80 flex items-center justify-between text-xs text-slate-400 font-mono">
                  <span>Effect Metric: {result.effect_metric} = {result.effect_size.toFixed(3)}</span>
                  <span>Alpha α = {result.alpha}</span>
                  <span>{mode === 'a_priori' ? `Target Power = ${result.target_power * 100}%` : `Observed N = ${result.sample_size}`}</span>
                </div>
              </div>

              {/* Interactive Plotly Curve Graph */}
              <div className="bg-slate-950/90 border border-slate-800/80 rounded-2xl p-4 sm:p-6 shadow-xl">
                <div className="flex items-center justify-between pb-3 mb-4 border-b border-slate-800">
                  <h4 className="font-bold text-sm text-slate-200 flex items-center gap-2">
                    <BarChart2 className="w-4 h-4 text-indigo-400" />
                    {mode === 'a_priori' ? 'A-Priori Sample Size Power Curve' : 'Post-Hoc Power Sensitivity Curve'}
                  </h4>
                  <span className="text-xs text-slate-500">Hover graph to inspect exact coordinates</span>
                </div>

                {(result.power_curve_plot || result.sensitivity_plot) && (
                  <div className="w-full h-80 sm:h-96">
                    <Plot
                      data={(result.power_curve_plot || result.sensitivity_plot).data}
                      layout={{
                        ...(result.power_curve_plot || result.sensitivity_plot).layout,
                        autosize: true,
                        paper_bgcolor: 'rgba(0,0,0,0)',
                        plot_bgcolor: 'rgba(15,23,42,0.5)',
                      }}
                      config={{ responsive: true, displayModeBar: false }}
                      style={{ width: '100%', height: '100%' }}
                    />
                  </div>
                )}
              </div>

              {/* Academic Grant & IRB Justification Block */}
              <div className="bg-slate-900/90 border border-sky-500/30 rounded-2xl p-5 sm:p-6 shadow-xl space-y-3 relative overflow-hidden">
                <div className="flex items-center justify-between">
                  <div className="flex items-center gap-2 text-sky-400 font-bold text-sm">
                    <BookOpen className="w-4 h-4" /> Grant Proposal / IRB Protocol Justification Text
                  </div>
                  <button
                    onClick={handleCopyJustification}
                    className="flex items-center gap-1.5 px-3 py-1.5 rounded-lg bg-sky-500/20 hover:bg-sky-500/30 text-sky-300 text-xs font-semibold border border-sky-500/30 transition-all"
                  >
                    {copied ? <CheckCircle2 className="w-3.5 h-3.5 text-emerald-400" /> : <Copy className="w-3.5 h-3.5" />}
                    <span>{copied ? 'Copied Justification!' : 'Copy IRB Paragraph'}</span>
                  </button>
                </div>

                <div className="bg-slate-950/80 border border-slate-800 rounded-xl p-4 text-xs sm:text-sm text-slate-300 font-serif leading-relaxed italic border-l-4 border-l-sky-400">
                  "{result.justification}"
                </div>

                {result.formula_note && (
                  <p className="text-[11px] text-slate-500 font-mono pt-1">
                    Exact Derivation Note: {result.formula_note}
                  </p>
                )}
              </div>
            </>
          ) : null}
        </div>
      </div>
    </div>
  );
};
