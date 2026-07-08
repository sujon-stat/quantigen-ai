import React from 'react';
import Plot from 'react-plotly.js';
import { BarChart3, Download, Sparkles, ArrowLeft, Layers } from 'lucide-react';
import type { AnalysisResponse } from '../../types/statmind';
import { AssumptionShield } from './AssumptionShield';
import { PublicationSuite } from './PublicationSuite';
import { api } from '../../api/client';

interface ResultsCenterProps {
  response: AnalysisResponse | null;
  onBackToAnalysis: () => void;
}

export const ResultsCenter: React.FC<ResultsCenterProps> = ({
  response,
  onBackToAnalysis,
}) => {
  if (!response) {
    return (
      <div className="glass-panel p-10 text-center text-slate-400">
        No analysis results available yet. Please execute an analysis from the Analysis & AI Consultant tab.
      </div>
    );
  }

  const { analysis_result: res, assumptions } = response;

  return (
    <div className="space-y-8 animate-fade-in pb-12">
      {/* Top Bar with Back Button */}
      <div className="flex items-center justify-between">
        <button onClick={onBackToAnalysis} className="btn-secondary text-xs">
          <ArrowLeft className="w-4 h-4" />
          <span>Back to Analysis Studio</span>
        </button>

        <div className="flex items-center gap-2">
          <span className="badge-role">{res.method_family}</span>
          <span className="text-xs text-slate-400">Sample Size: <strong className="text-white">N = {res.sample_size}</strong></span>
        </div>
      </div>

      {/* Assumption Shield Diagnostic Header */}
      <AssumptionShield assumptions={assumptions} methodName={res.method_name} />

      {/* Main Statistical Summary Banner */}
      <div className="glass-panel p-6 space-y-4 border-t-4 border-t-sky-400">
        <div className="flex items-start justify-between">
          <div>
            <h2 className="text-2xl font-bold text-white tracking-tight">{res.method_name} Results</h2>
            <p className="text-xs text-slate-400 mt-1">{res.description}</p>
          </div>
        </div>

        {/* Core Metrics Grid */}
        <div className="grid grid-cols-2 md:grid-cols-4 gap-4 pt-2">
          {Object.entries(res.main_results).map(([key, val]) => (
            <div key={key} className="bg-slate-900/70 border border-white/5 rounded-xl p-4 space-y-1">
              <span className="text-[11px] font-semibold uppercase tracking-wider text-slate-400 block">
                {key.replace(/_/g, ' ')}
              </span>
              <span className="text-xl font-bold text-white font-mono">
                {typeof val === 'number'
                  ? key.includes('p_value')
                    ? val < 0.001
                      ? '< 0.001*'
                      : val.toFixed(4)
                    : val.toFixed(3)
                  : String(val || 'N/A')}
              </span>
            </div>
          ))}
          
          {Object.entries(res.effect_sizes).map(([key, val]) => (
            <div key={key} className="bg-sky-500/10 border border-sky-500/30 rounded-xl p-4 space-y-1">
              <span className="text-[11px] font-semibold uppercase tracking-wider text-sky-300 block">
                Effect Size ({key.replace(/_/g, ' ')})
              </span>
              <span className="text-xl font-bold text-white font-mono">
                {typeof val === 'number' ? val.toFixed(3) : String(val)}
              </span>
            </div>
          ))}
        </div>

        {/* Narrative Interpretation */}
        <div className="bg-gradient-to-br from-slate-900 to-slate-900/90 border border-white/10 rounded-xl p-5 mt-4 space-y-2">
          <div className="flex items-center gap-2 text-sky-300 font-semibold text-sm">
            <Sparkles className="w-4 h-4 text-amber-400" />
            <span>StatMind Narrative Interpretation</span>
          </div>
          <p className="text-sm text-slate-200 leading-relaxed font-serif">
            {res.interpretation}
          </p>
        </div>
      </div>

      {/* Interactive Plotly Charts Suite */}
      {res.plots_json && res.plots_json.length > 0 && (
        <div className="space-y-6">
          <div className="flex items-center justify-between">
            <h3 className="text-lg font-bold text-white flex items-center gap-2">
              <BarChart3 className="w-5 h-5 text-sky-400" />
              <span>Interactive Data Visualizations & High-Res PNG Export</span>
            </h3>
            <span className="text-xs text-slate-400">
              Hover over data points to inspect values. Click button to download `300 DPI` static manuscript figure.
            </span>
          </div>

          <div className="grid grid-cols-1 gap-6">
            {res.plots_json.map((plotJson: any, idx: number) => (
              <div key={idx} className="glass-panel p-6 space-y-4 overflow-hidden">
                <div className="flex items-center justify-between border-b border-white/10 pb-3">
                  <span className="font-bold text-sm text-white flex items-center gap-2">
                    <Layers className="w-4 h-4 text-sky-400" />
                    <span>Figure {idx + 1}: {plotJson?.layout?.title?.text || `${res.method_name} Visualization`}</span>
                  </span>
                  <button
                    onClick={() => api.downloadChartPNG(plotJson, `statmind_figure_${idx + 1}`)}
                    className="btn-primary text-xs py-1.5 px-3"
                  >
                    <Download className="w-3.5 h-3.5" />
                    <span>Download 300 DPI Publication PNG</span>
                  </button>
                </div>

                <div className="w-full min-h-[420px] flex items-center justify-center bg-slate-950/60 rounded-xl p-2">
                  <Plot
                    data={plotJson.data || []}
                    layout={{
                      ...plotJson.layout,
                      autosize: true,
                      paper_bgcolor: 'transparent',
                      plot_bgcolor: 'transparent',
                      font: { family: 'Inter, sans-serif', color: '#f8fafc' },
                      margin: { t: 50, r: 30, l: 60, b: 60 },
                    }}
                    config={{
                      responsive: true,
                      displayModeBar: true,
                      displaylogo: false,
                    }}
                    style={{ width: '100%', height: '420px' }}
                  />
                </div>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Publication Suite (APA, Code, Reports) */}
      <PublicationSuite result={res} />
    </div>
  );
};
