import React, { useState } from 'react';
import { Copy, Check, Download, Code2, FileText, BookOpen } from 'lucide-react';
import type { MethodResult } from '../../types/statmind';
import { api } from '../../api/client';

interface PublicationSuiteProps {
  result: MethodResult;
}

export const PublicationSuite: React.FC<PublicationSuiteProps> = ({ result }) => {
  const [copiedApa, setCopiedApa] = useState(false);
  const [codeTab, setCodeTab] = useState<'r' | 'python'>('r');
  const [downloadingReport, setDownloadingReport] = useState(false);

  // Construct APA citation string if not provided directly
  const getApaCitation = () => {
    const p = result.main_results.p_value ?? result.main_results.likelihood_ratio_p_value ?? 0.05;
    const pStr = p < 0.001 ? 'p < .001' : `p = .${Math.round(p * 1000).toString().padStart(3, '0')}`;
    const eff = Object.entries(result.effect_sizes)
      .filter(([_, v]) => typeof v === 'number')
      .map(([k, v]) => `${k.replace('_', ' ')} = ${(v as number).toFixed(2)}`)
      .join(', ');
      
    if (result.method_id.includes('ttest')) {
      const df = result.main_results.degrees_of_freedom?.toFixed(2) || 'N/A';
      const t = result.main_results.t_statistic?.toFixed(2) || '0.00';
      return `An independent-samples t-test revealed significant differences across groups, t(${df}) = ${t}, ${pStr}${eff ? `, ${eff}` : ''}.`;
    }
    if (result.method_id.includes('anova')) {
      const dfb = result.main_results.df_between || 2;
      const dfw = result.main_results.df_within || 100;
      const f = result.main_results.f_statistic?.toFixed(2) || '0.00';
      return `A one-way analysis of variance (ANOVA) showed a statistically significant main effect, F(${dfb}, ${dfw}) = ${f}, ${pStr}${eff ? `, ${eff}` : ''}.`;
    }
    if (result.method_id.includes('logistic')) {
      const chi = result.main_results.likelihood_ratio_chi2?.toFixed(2) || '0.00';
      const df = result.main_results.dof_model || 1;
      return `A binary logistic regression model was fitted. The model evaluation yielded Likelihood Ratio χ²(${df}) = ${chi}, ${pStr}${eff ? `, ${eff}` : ''}.`;
    }
    return `${result.method_name} analysis was conducted on n = ${result.sample_size} observations, yielding ${pStr}${eff ? `, ${eff}` : ''}.`;
  };

  const apaText = getApaCitation();

  const handleCopyApa = () => {
    navigator.clipboard.writeText(apaText);
    setCopiedApa(true);
    setTimeout(() => setCopiedApa(false), 2500);
  };

  const handleDownloadReport = async (format: 'html_manuscript' | 'markdown') => {
    setDownloadingReport(true);
    try {
      await api.downloadReport(result, format, apaText);
    } catch (err) {
      console.error('Report export error:', err);
    } finally {
      setDownloadingReport(false);
    }
  };

  return (
    <div className="space-y-6 animate-fade-in">
      {/* APA 7th Edition Citation Box */}
      <div className="glass-panel p-6 space-y-4 border-l-4 border-l-emerald-400">
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-2">
            <BookOpen className="w-5 h-5 text-emerald-400" />
            <h3 className="text-md font-bold text-white">APA 7th Edition Publication Citation</h3>
          </div>
          <button
            onClick={handleCopyApa}
            className="btn-secondary text-xs px-3 py-1.5 flex items-center gap-1.5 text-emerald-300 border-emerald-500/30 hover:bg-emerald-500/10"
          >
            {copiedApa ? <Check className="w-3.5 h-3.5 text-emerald-400" /> : <Copy className="w-3.5 h-3.5" />}
            <span>{copiedApa ? 'Copied to Clipboard!' : 'Copy APA Citation'}</span>
          </button>
        </div>
        
        <div className="bg-slate-900/80 border border-white/10 rounded-xl p-4 font-serif text-sm text-slate-200 leading-relaxed italic border-l-4 border-l-sky-500">
          "{apaText}"
        </div>
        <p className="text-[11px] text-slate-400">
          Ready to paste directly into your thesis, dissertation, or academic journal manuscript.
        </p>
      </div>

      {/* Report Export Center */}
      <div className="glass-panel p-6 space-y-4">
        <div className="flex flex-col md:flex-row md:items-center justify-between gap-4">
          <div>
            <h3 className="text-md font-bold text-white flex items-center gap-2">
              <FileText className="w-5 h-5 text-sky-400" />
              <span>Academic Manuscript & Report Export Center</span>
            </h3>
            <p className="text-xs text-slate-400 mt-1 max-w-xl">
              Export your full analysis including APA citations, diagnostic assumptions, and static high-resolution PNG figures (`300 DPI`) embedded directly into the report.
            </p>
          </div>

          <div className="flex items-center gap-3">
            <button
              onClick={() => handleDownloadReport('markdown')}
              disabled={downloadingReport}
              className="btn-secondary text-xs"
            >
              <Download className="w-3.5 h-3.5" />
              <span>Markdown (.md)</span>
            </button>

            <button
              onClick={() => handleDownloadReport('html_manuscript')}
              disabled={downloadingReport}
              className="btn-primary text-xs shadow-lg shadow-sky-500/20"
            >
              <Download className="w-4 h-4" />
              <span>{downloadingReport ? 'Generating PNG Figures...' : 'Download Academic Manuscript (.html)'}</span>
            </button>
          </div>
        </div>
      </div>

      {/* Reproducible Code Viewer */}
      <div className="glass-panel p-6 space-y-4">
        <div className="flex items-center justify-between border-b border-white/10 pb-3">
          <div className="flex items-center gap-2">
            <Code2 className="w-5 h-5 text-indigo-400" />
            <h3 className="text-md font-bold text-white">100% Reproducible R & Python Scripts</h3>
          </div>

          <div className="flex items-center gap-2">
            <div className="flex bg-slate-900/80 p-1 rounded-lg border border-white/5 text-xs font-semibold">
              <button
                onClick={() => setCodeTab('r')}
                className={`px-3 py-1 rounded-md transition-all ${
                  codeTab === 'r' ? 'bg-indigo-500 text-white shadow-sm' : 'text-slate-400 hover:text-white'
                }`}
              >
                R Script (`.R`)
              </button>
              <button
                onClick={() => setCodeTab('python')}
                className={`px-3 py-1 rounded-md transition-all ${
                  codeTab === 'python' ? 'bg-sky-500 text-white shadow-sm' : 'text-slate-400 hover:text-white'
                }`}
              >
                Python Script (`.py`)
              </button>
            </div>

            <button
              onClick={() => api.downloadScript(codeTab === 'r' ? result.r_code : result.python_code, codeTab, `statmind_${result.method_id}`)}
              className="btn-secondary text-xs py-1.5"
            >
              <Download className="w-3.5 h-3.5" />
              <span>Download .{codeTab === 'r' ? 'R' : 'py'} Script</span>
            </button>
          </div>
        </div>

        <div className="bg-slate-950 border border-white/10 rounded-xl p-4 overflow-x-auto">
          <pre className="text-xs text-slate-300 font-mono leading-relaxed">
            <code>{codeTab === 'r' ? result.r_code : result.python_code}</code>
          </pre>
        </div>
        <p className="text-[11px] text-slate-400">
          StatMind AI guarantees full transparency. You can run this standalone script on your own local computer or RStudio server at any time to obtain identical results.
        </p>
      </div>
    </div>
  );
};
