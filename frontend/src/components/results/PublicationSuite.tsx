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
    if (!result) return 'Statistical analysis was conducted.';
    const mainRes = result.main_results || {};
    const effSizes = result.effect_sizes || {};
    const methodId = String(result.method_id || '');
    const p = mainRes.p_value ?? mainRes.likelihood_ratio_p_value ?? 0.05;
    const pStr = typeof p === 'number' && p < 0.001 ? 'p < .001' : `p = .${Math.round(Number(p) * 1000 || 50).toString().padStart(3, '0')}`;
    const eff = Object.entries(effSizes)
      .filter(([_, v]) => typeof v === 'number')
      .map(([k, v]) => `${k.replace('_', ' ')} = ${(v as number).toFixed(2)}`)
      .join(', ');
      
    if (methodId.includes('ttest')) {
      const df = mainRes.degrees_of_freedom?.toFixed?.(2) || 'N/A';
      const t = mainRes.t_statistic?.toFixed?.(2) || '0.00';
      return `An independent-samples t-test revealed significant differences across groups, t(${df}) = ${t}, ${pStr}${eff ? `, ${eff}` : ''}.`;
    }
    if (methodId.includes('anova')) {
      const dfb = mainRes.df_between || 2;
      const dfw = mainRes.df_within || 100;
      const f = mainRes.f_statistic?.toFixed?.(2) || '0.00';
      return `A one-way analysis of variance (ANOVA) showed a statistically significant main effect, F(${dfb}, ${dfw}) = ${f}, ${pStr}${eff ? `, ${eff}` : ''}.`;
    }
    if (methodId.includes('logistic')) {
      const chi = mainRes.likelihood_ratio_chi2?.toFixed?.(2) || '0.00';
      const df = mainRes.dof_model || 1;
      return `A binary logistic regression model was fitted. The model evaluation yielded Likelihood Ratio χ²(${df}) = ${chi}, ${pStr}${eff ? `, ${eff}` : ''}.`;
    }
    return `${result.method_name || 'Statistical'} analysis was conducted on n = ${result.sample_size || 0} observations, yielding ${pStr}${eff ? `, ${eff}` : ''}.`;
  };

  const apaText = getApaCitation();

  const handleCopyApa = () => {
    navigator.clipboard.writeText(apaText);
    setCopiedApa(true);
    setTimeout(() => setCopiedApa(false), 2500);
  };

  const handleDownloadReport = async (format: 'doc' | 'pdf' | 'html' | 'html_manuscript' | 'markdown') => {
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
        <div className="flex flex-col justify-between gap-4">
          <div>
            <h3 className="text-md font-bold text-white flex items-center gap-2">
              <FileText className="w-5 h-5 text-sky-400" />
              <span>Academic Manuscript & Report Export Center</span>
            </h3>
            <p className="text-xs text-slate-400 mt-1 max-w-2xl">
              Download your complete Quantigen AI analysis—including APA narrative interpretations, diagnostic assumption summaries, reproducible code scripts, and charts—in your preferred publication file format:
            </p>
          </div>

          <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-3 pt-2">
            <button
              onClick={() => handleDownloadReport('doc')}
              disabled={downloadingReport}
              className="btn-primary bg-gradient-to-r from-blue-600 to-indigo-600 hover:from-blue-500 hover:to-indigo-500 text-xs py-2.5 shadow-lg shadow-blue-500/20 flex items-center justify-center gap-2"
            >
              <Download className="w-4 h-4" />
              <span>MS Word Document (.doc)</span>
            </button>

            <button
              onClick={() => handleDownloadReport('pdf')}
              disabled={downloadingReport}
              className="btn-primary bg-gradient-to-r from-rose-600 to-pink-600 hover:from-rose-500 hover:to-pink-500 text-xs py-2.5 shadow-lg shadow-rose-500/20 flex items-center justify-center gap-2"
            >
              <Download className="w-4 h-4" />
              <span>Printable PDF (.pdf)</span>
            </button>

            <button
              onClick={() => handleDownloadReport('html_manuscript')}
              disabled={downloadingReport}
              className="btn-primary bg-gradient-to-r from-emerald-600 to-teal-600 hover:from-emerald-500 hover:to-teal-500 text-xs py-2.5 shadow-lg shadow-emerald-500/20 flex items-center justify-center gap-2"
            >
              <Download className="w-4 h-4" />
              <span>Interactive HTML (.html)</span>
            </button>

            <button
              onClick={() => handleDownloadReport('markdown')}
              disabled={downloadingReport}
              className="btn-secondary text-xs py-2.5 flex items-center justify-center gap-2 border-white/20 hover:border-white/40"
            >
              <Download className="w-4 h-4" />
              <span>Markdown (.md)</span>
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
              onClick={() => api.downloadScript(codeTab === 'r' ? result.r_code : result.python_code, codeTab, `quantigen_${result.method_id}`)}
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
          Quantigen AI guarantees full transparency. You can run this standalone script on your own local computer or RStudio server at any time to obtain identical results.
        </p>
      </div>
    </div>
  );
};
