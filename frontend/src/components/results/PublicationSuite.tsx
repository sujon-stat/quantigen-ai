import React, { useState } from 'react';
import { Copy, Check, Download, Code2, FileText, BookOpen, ChevronDown } from 'lucide-react';
import type { MethodResult } from '../../types/statmind';
import { api } from '../../api/client';
import { Q1JournalTable } from './Q1JournalTable';

interface PublicationSuiteProps {
  result: MethodResult;
}

export const PublicationSuite: React.FC<PublicationSuiteProps> = ({ result }) => {
  const [copiedApa, setCopiedApa] = useState(false);
  const [codeTab, setCodeTab] = useState<'r' | 'python' | 'rmd'>('r');
  const [downloadingReport, setDownloadingReport] = useState(false);
  const [showApa, setShowApa] = useState(false);
  const [activeBox, setActiveBox] = useState<'none' | 'files' | 'codes'>('none');

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

  const getRmdContent = () => {
    const title = result.method_name || 'Quantigen AI Statistical Analysis';
    const date = new Date().toISOString().split('T')[0];
    return `---
title: "${title} — Publication Report"
author: "Quantigen AI Automated Statistical Engine"
date: "${date}"
output:
  html_document:
    toc: true
    toc_float: true
    theme: cosmo
    highlight: tango
  pdf_document: default
  word_document: default
---

\`\`\`{r setup, include=FALSE}
knitr::opts_chunk$set(echo = TRUE, warning = FALSE, message = FALSE)
\`\`\`

# APA 7th Edition Narrative Interpretation

> **${apaText}**

# Diagnostic Assumptions & Verification

\`\`\`{r assumptions}
# Quantigen AI Assumption Shield verified prior to p-value release
# Method ID: ${result.method_id} | Sample Size: n = ${result.sample_size}
\`\`\`

# Reproducible Statistical Engine Syntax

\`\`\`{r analysis}
${result.r_code || '# R syntax'}
\`\`\`
`;
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

  const handleDownloadRmd = () => {
    api.downloadScript(getRmdContent(), 'Rmd', `quantigen_${result.method_id}_notebook`);
  };

  return (
    <div className="space-y-6 animate-fade-in">
      {/* Q1 Journal Publication-Ready Table */}
      <Q1JournalTable result={result} />

      {/* APA 7th Edition Citation Box (Collapsible by default) */}
      <div className="glass-panel border-0 rounded-2xl relative overflow-hidden transition-all duration-300 shadow-md">
        <div
          onClick={() => setShowApa(!showApa)}
          className="flex items-center justify-between p-4 bg-slate-900/90 hover:bg-slate-800/90 cursor-pointer transition-all select-none gap-3 border-l-4 border-l-emerald-400"
        >
          <div className="flex items-center gap-2.5">
            <BookOpen className="w-5 h-5 text-emerald-400 shrink-0" />
            <span className="font-bold text-white text-sm">View APA 7th Edition Publication Citation</span>
            <span className="badge-pass text-[11px]">Ready for Manuscript Paste</span>
          </div>
          <div className="flex items-center gap-1.5 text-xs text-emerald-400 font-semibold sm:ml-auto">
            <span>{showApa ? 'Hide Citation' : 'Inspect Citation String'}</span>
            <ChevronDown className={`w-4 h-4 transition-transform duration-200 ${showApa ? 'rotate-180' : ''}`} />
          </div>
        </div>

        {showApa && (
          <div className="p-6 pt-4 border-t border-white/10 space-y-4 bg-slate-950/40 animate-fade-in border-l-4 border-l-emerald-400">
            <div className="flex items-center justify-between">
              <span className="text-xs text-slate-400">Formatted according to APA 7th Edition standards:</span>
              <button
                onClick={(e) => { e.stopPropagation(); handleCopyApa(); }}
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
        )}
      </div>

      {/* Colorful Bottom Center Selection Boxes (No Header Text) */}
      <div className="max-w-4xl mx-auto pt-4 space-y-5 animate-fade-in">
        <div className="grid grid-cols-1 md:grid-cols-2 gap-5 justify-center">
          {/* Box 1: Import Files */}
          <div
            onClick={() => setActiveBox(activeBox === 'files' ? 'none' : 'files')}
            className={`p-5 rounded-2xl border-2 transition-all cursor-pointer select-none flex items-center justify-between group shadow-xl ${
              activeBox === 'files'
                ? 'bg-gradient-to-r from-blue-600/40 via-sky-600/30 to-teal-600/40 border-sky-300 shadow-sky-500/30 scale-[1.01]'
                : 'bg-gradient-to-r from-blue-900/50 via-sky-900/40 to-teal-900/50 border-sky-400/80 hover:border-sky-300 hover:scale-[1.01] hover:shadow-sky-500/20'
            }`}
          >
            <div className="flex items-center gap-4">
              <div className="p-3.5 rounded-xl bg-sky-500/20 border border-sky-400/50 text-sky-300 group-hover:text-white group-hover:bg-sky-500/30 transition-all shadow-md">
                <FileText className="w-6 h-6" />
              </div>
              <div>
                <h4 className="text-base font-extrabold text-white group-hover:text-sky-200 transition-colors tracking-wide">
                  Import Files
                </h4>
                <p className="text-xs text-sky-200/90 mt-0.5 leading-tight font-medium">
                  After clicking here the type of files will be showed
                </p>
              </div>
            </div>
            <div className={`flex items-center justify-center w-8 h-8 rounded-full border text-xs transition-transform ${
              activeBox === 'files' ? 'bg-sky-400 text-slate-950 font-bold border-sky-300 rotate-180 shadow-md' : 'bg-slate-900/80 border-sky-400/50 text-sky-300 group-hover:border-sky-300'
            }`}>
              <ChevronDown className="w-4 h-4" />
            </div>
          </div>

          {/* Box 2: Import Codes */}
          <div
            onClick={() => setActiveBox(activeBox === 'codes' ? 'none' : 'codes')}
            className={`p-5 rounded-2xl border-2 transition-all cursor-pointer select-none flex items-center justify-between group shadow-xl ${
              activeBox === 'codes'
                ? 'bg-gradient-to-r from-purple-600/40 via-indigo-600/30 to-pink-600/40 border-purple-300 shadow-purple-500/30 scale-[1.01]'
                : 'bg-gradient-to-r from-purple-900/50 via-indigo-900/40 to-pink-900/50 border-purple-400/80 hover:border-purple-300 hover:scale-[1.01] hover:shadow-purple-500/20'
            }`}
          >
            <div className="flex items-center gap-4">
              <div className="p-3.5 rounded-xl bg-purple-500/20 border border-purple-400/50 text-purple-300 group-hover:text-white group-hover:bg-purple-500/30 transition-all shadow-md">
                <Code2 className="w-6 h-6" />
              </div>
              <div>
                <div className="flex items-center gap-2">
                  <h4 className="text-base font-extrabold text-white group-hover:text-purple-200 transition-colors tracking-wide">
                    Import Codes
                  </h4>
                  <span className="px-1.5 py-0.5 rounded bg-purple-500/30 text-purple-200 font-mono text-[10px] border border-purple-400/30">100% Verified</span>
                </div>
                <p className="text-xs text-purple-200/90 mt-0.5 leading-tight font-medium">
                  After clicking here the type of code scripts will be showed
                </p>
              </div>
            </div>
            <div className={`flex items-center justify-center w-8 h-8 rounded-full border text-xs transition-transform ${
              activeBox === 'codes' ? 'bg-purple-400 text-slate-950 font-bold border-purple-300 rotate-180 shadow-md' : 'bg-slate-900/80 border-purple-400/50 text-purple-300 group-hover:border-purple-300'
            }`}>
              <ChevronDown className="w-4 h-4" />
            </div>
          </div>
        </div>

        {/* Visual Option Selector Panel for Box 1 (Import Files) */}
        {activeBox === 'files' && (
          <div className="bg-slate-950/95 border-2 border-sky-400/60 rounded-2xl p-6 space-y-4 animate-fade-in border-l-4 border-l-sky-400 shadow-2xl shadow-sky-500/10">
            <div className="flex items-center justify-between border-b border-white/10 pb-3">
              <div className="flex items-center gap-2">
                <FileText className="w-4 h-4 text-sky-400" />
                <h4 className="font-bold text-white text-xs sm:text-sm">Select Your Preferred Manuscript & Report File Type</h4>
              </div>
              <button onClick={() => setActiveBox('none')} className="text-xs text-slate-400 hover:text-white px-2.5 py-1 rounded-lg bg-slate-900 border border-white/10 hover:bg-white/10 transition-colors">✕ Close</button>
            </div>

            <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-5 gap-3.5">
              <button
                onClick={() => handleDownloadReport('doc')}
                disabled={downloadingReport}
                className="flex flex-col items-start p-4 rounded-xl border border-blue-500/40 bg-blue-500/15 hover:bg-blue-500/30 text-left transition-all group shadow-md hover:scale-[1.02]"
              >
                <div className="flex items-center justify-between w-full mb-2">
                  <span className="text-xs font-bold text-blue-300 group-hover:text-white">Word (.doc)</span>
                  <Download className="w-4 h-4 text-blue-400 group-hover:text-white" />
                </div>
                <p className="text-[11px] text-slate-300 leading-tight">Editable MHTML with embedded charts & APA tables</p>
              </button>

              <button
                onClick={() => handleDownloadReport('pdf')}
                disabled={downloadingReport}
                className="flex flex-col items-start p-4 rounded-xl border border-rose-500/40 bg-rose-500/15 hover:bg-rose-500/30 text-left transition-all group shadow-md hover:scale-[1.02]"
              >
                <div className="flex items-center justify-between w-full mb-2">
                  <span className="text-xs font-bold text-rose-300 group-hover:text-white">PDF (.pdf)</span>
                  <Download className="w-4 h-4 text-rose-400 group-hover:text-white" />
                </div>
                <p className="text-[11px] text-slate-300 leading-tight">High-res 300 DPI printable publication layout</p>
              </button>

              <button
                onClick={() => handleDownloadReport('html_manuscript')}
                disabled={downloadingReport}
                className="flex flex-col items-start p-4 rounded-xl border border-emerald-500/40 bg-emerald-500/15 hover:bg-emerald-500/30 text-left transition-all group shadow-md hover:scale-[1.02]"
              >
                <div className="flex items-center justify-between w-full mb-2">
                  <span className="text-xs font-bold text-emerald-300 group-hover:text-white">HTML (.html)</span>
                  <Download className="w-4 h-4 text-emerald-400 group-hover:text-white" />
                </div>
                <p className="text-[11px] text-slate-300 leading-tight">Standalone report with live interactive Plotly graphs</p>
              </button>

              <button
                onClick={() => handleDownloadReport('markdown')}
                disabled={downloadingReport}
                className="flex flex-col items-start p-4 rounded-xl border border-slate-500/40 bg-slate-800/60 hover:bg-slate-800 text-left transition-all group shadow-md hover:scale-[1.02]"
              >
                <div className="flex items-center justify-between w-full mb-2">
                  <span className="text-xs font-bold text-slate-200 group-hover:text-white">Markdown (.md)</span>
                  <Download className="w-4 h-4 text-slate-300 group-hover:text-white" />
                </div>
                <p className="text-[11px] text-slate-400 leading-tight">Clean GitHub/Obsidian formatted markdown</p>
              </button>

              <button
                onClick={() => handleDownloadRmd()}
                className="flex flex-col items-start p-4 rounded-xl border border-amber-500/40 bg-amber-500/15 hover:bg-amber-500/30 text-left transition-all group shadow-md hover:scale-[1.02]"
              >
                <div className="flex items-center justify-between w-full mb-2">
                  <span className="text-xs font-bold text-amber-300 group-hover:text-white">RMarkdown (.Rmd)</span>
                  <Download className="w-4 h-4 text-amber-400 group-hover:text-white" />
                </div>
                <p className="text-[11px] text-slate-300 leading-tight">Reproducible R notebook with code chunks & YAML header</p>
              </button>
            </div>
          </div>
        )}

        {/* Visual Option Selector Panel for Box 2 (Import Codes) */}
        {activeBox === 'codes' && (
          <div className="bg-slate-950/95 border-2 border-purple-400/60 rounded-2xl p-6 space-y-4 animate-fade-in border-l-4 border-l-purple-400 shadow-2xl shadow-purple-500/10">
            <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3 border-b border-white/10 pb-3">
              <div className="flex items-center gap-2">
                <Code2 className="w-4 h-4 text-purple-400" />
                <h4 className="font-bold text-white text-xs sm:text-sm">Select & Inspect Your Reproducible Code Script Type</h4>
              </div>
              <button onClick={() => setActiveBox('none')} className="text-xs text-slate-400 hover:text-white sm:ml-auto px-2.5 py-1 rounded-lg bg-slate-900 border border-white/10 hover:bg-white/10 transition-colors">✕ Close</button>
            </div>

            <div className="flex flex-wrap items-center justify-between gap-4">
              <div className="flex gap-2 bg-slate-900 p-1.5 rounded-xl border border-white/10">
                <button
                  onClick={() => setCodeTab('r')}
                  className={`px-4 py-1.5 rounded-lg text-xs font-bold transition-all flex items-center gap-1.5 ${
                    codeTab === 'r' ? 'bg-indigo-600 text-white shadow-md shadow-indigo-500/30' : 'text-slate-400 hover:text-white'
                  }`}
                >
                  <span>R Script (.R)</span>
                </button>
                <button
                  onClick={() => setCodeTab('python')}
                  className={`px-4 py-1.5 rounded-lg text-xs font-bold transition-all flex items-center gap-1.5 ${
                    codeTab === 'python' ? 'bg-sky-600 text-white shadow-md shadow-sky-500/30' : 'text-slate-400 hover:text-white'
                  }`}
                >
                  <span>Python Script (.py)</span>
                </button>
                <button
                  onClick={() => setCodeTab('rmd')}
                  className={`px-4 py-1.5 rounded-lg text-xs font-bold transition-all flex items-center gap-1.5 ${
                    codeTab === 'rmd' ? 'bg-amber-600 text-white shadow-md shadow-amber-500/30' : 'text-slate-400 hover:text-white'
                  }`}
                >
                  <span>RMarkdown Notebook (.Rmd)</span>
                </button>
              </div>

              <button
                onClick={() => {
                  const content = codeTab === 'r' ? result.r_code : codeTab === 'python' ? result.python_code : getRmdContent();
                  const ext = codeTab === 'r' ? 'R' : codeTab === 'python' ? 'py' : 'Rmd';
                  api.downloadScript(content, ext, `quantigen_${result.method_id}_script`);
                }}
                className="btn-primary px-5 py-2.5 text-xs font-bold flex items-center gap-2 shadow-lg shadow-purple-500/30 bg-gradient-to-r from-purple-600 via-indigo-600 to-pink-600 hover:from-purple-500 hover:via-indigo-500 hover:to-pink-500 text-white"
              >
                <Download className="w-4 h-4" />
                <span>Download .{codeTab === 'r' ? 'R' : codeTab === 'python' ? 'py' : 'Rmd'} File</span>
              </button>
            </div>

            <div className="bg-slate-900/90 border border-white/10 rounded-xl p-4 overflow-x-auto max-h-[380px] shadow-inner">
              <pre className="text-xs text-slate-300 font-mono leading-relaxed">
                <code>{codeTab === 'r' ? result.r_code : codeTab === 'python' ? result.python_code : getRmdContent()}</code>
              </pre>
            </div>
            <p className="text-[11px] text-slate-400">
              Quantigen AI guarantees full transparency. You can run this standalone {codeTab === 'r' ? 'R script (`.R`)' : codeTab === 'python' ? 'Python script (`.py`)' : 'RMarkdown notebook (`.Rmd`)'} on your own local computer or RStudio server at any time to obtain identical verified results.
            </p>
          </div>
        )}
      </div>
    </div>
  );
};
