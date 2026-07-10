import React, { useState } from 'react';
import { X, Check, FileText, FileSpreadsheet, Globe, Code2, Download, Layers, CheckCircle2, AlertCircle, ShieldCheck, Trash2, Eye } from 'lucide-react';
import type { AnalysisResponse, PortfolioItemRequest, PortfolioExportPayload } from '../../types/statmind';
import { api } from '../../api/client';

interface PortfolioBuilderModalProps {
  isOpen: boolean;
  onClose: () => void;
  analysisHistory: AnalysisResponse[];
  currentResponse: AnalysisResponse | null;
  theme?: 'dark' | 'light';
  onRemoveHistoryItem?: (id: string) => void;
  onSelectHistoryItem?: (item: AnalysisResponse) => void;
  onClearHistory?: () => void;
}

export const PortfolioBuilderModal: React.FC<PortfolioBuilderModalProps> = ({
  isOpen,
  onClose,
  analysisHistory,
  currentResponse,
  theme = 'dark',
  onRemoveHistoryItem,
  onSelectHistoryItem,
  onClearHistory,
}) => {
  // If history is empty, populate with current response
  const baseItems: AnalysisResponse[] = analysisHistory.length > 0
    ? analysisHistory
    : currentResponse
    ? [currentResponse]
    : [];

  const [selectedItems, setSelectedItems] = useState<Record<string, {
    included: boolean;
    include_table: boolean;
    include_graph: boolean;
    include_narrative: boolean;
    include_code: boolean;
    preferred_graph_type: 'pie' | 'bar' | 'box' | 'default';
  }>>(() => {
    const init: Record<string, any> = {};
    baseItems.forEach((item, index) => {
      const id = item.history_id || `run_${index}`;
      init[id] = {
        included: true,
        include_table: true,
        include_graph: true,
        include_narrative: true,
        include_code: true,
        preferred_graph_type: 'default',
      };
    });
    return init;
  });

  const [portfolioTitle, setPortfolioTitle] = useState('Quantigen AI — Comprehensive Academic Manuscript Portfolio');
  const [selectedFormat, setSelectedFormat] = useState<'pdf' | 'doc' | 'html' | 'rmarkdown'>('pdf');
  const [isExporting, setIsExporting] = useState(false);
  const [exportSuccess, setExportSuccess] = useState(false);
  const [errorMessage, setErrorMessage] = useState<string | null>(null);

  if (!isOpen) return null;

  const handleToggleItem = (id: string) => {
    setSelectedItems((prev) => ({
      ...prev,
      [id]: {
        ...prev[id],
        included: !prev[id]?.included,
      },
    }));
  };

  const handleToggleOption = (id: string, option: 'include_table' | 'include_graph' | 'include_narrative' | 'include_code') => {
    setSelectedItems((prev) => ({
      ...prev,
      [id]: {
        ...prev[id],
        [option]: !prev[id]?.[option],
      },
    }));
  };

  const handleChangeGraphType = (id: string, type: 'pie' | 'bar' | 'box' | 'default') => {
    setSelectedItems((prev) => ({
      ...prev,
      [id]: {
        ...prev[id],
        preferred_graph_type: type,
      },
    }));
  };

  const handleSelectAll = (select: boolean) => {
    setSelectedItems((prev) => {
      const next: typeof prev = {};
      Object.keys(prev).forEach((id) => {
        next[id] = { ...prev[id], included: select };
      });
      return next;
    });
  };

  const handleCompileAndDownload = async () => {
    setIsExporting(true);
    setErrorMessage(null);
    setExportSuccess(false);

    try {
      const itemsToExport: PortfolioItemRequest[] = [];
      baseItems.forEach((item, index) => {
        const id = item.history_id || `run_${index}`;
        const cfg = selectedItems[id];
        if (cfg && cfg.included) {
          const res = (item.analysis_result || (item as any).result || {}) as any;
          itemsToExport.push({
            history_id: id,
            method_name: res.method_name || 'Statistical Analysis',
            description: res.description || '',
            sample_size: res.sample_size || 0,
            interpretation: res.interpretation || '',
            r_code: res.r_code || '',
            python_code: res.python_code || '',
            apa_citation: res.apa_citation,
            assumption_summary: res.assumption_summary,
            plots_json: res.plots_json || res.plots || [],
            main_results: res.main_results,
            effect_sizes: res.effect_sizes,
            config: {
              history_id: id,
              include_table: cfg.include_table,
              include_graph: cfg.include_graph,
              include_narrative: cfg.include_narrative,
              include_code: cfg.include_code,
              preferred_graph_type: cfg.preferred_graph_type,
            },
          });
        }
      });

      if (itemsToExport.length === 0) {
        setErrorMessage('Please select at least one analysis run to include in your portfolio.');
        setIsExporting(false);
        return;
      }

      const payload: PortfolioExportPayload = {
        title: portfolioTitle,
        items: itemsToExport,
        format: selectedFormat,
      };

      await api.downloadPortfolio(payload);
      setExportSuccess(true);
      setTimeout(() => {
        setExportSuccess(false);
        onClose();
      }, 1800);
    } catch (err: any) {
      console.error('Failed to compile portfolio:', err);
      setErrorMessage(err?.message || 'Error compiling your portfolio document. Please check your network connection.');
    } finally {
      setIsExporting(false);
    }
  };

  const countSelected = Object.values(selectedItems).filter((i) => i.included).length;

  return (
    <div className="fixed inset-0 z-[100] flex items-center justify-center p-3 sm:p-6 bg-slate-950/85 backdrop-blur-md overflow-hidden animate-in fade-in">
      <div className={`w-full max-w-4xl max-h-[90vh] flex flex-col rounded-2xl shadow-2xl border overflow-hidden ${
        theme === 'light' ? 'bg-white border-slate-200 text-slate-800' : 'bg-slate-900 border-white/10 text-white'
      }`}>
        {/* Modal Header */}
        <div className="flex items-center justify-between px-6 py-5 border-b border-white/10 bg-slate-900/50 rounded-t-2xl">
          <div className="flex items-center gap-3">
            <div className="p-2.5 rounded-xl bg-sky-500/10 border border-sky-500/30 text-sky-400">
              <Layers className="w-6 h-6 animate-pulse" />
            </div>
            <div>
              <h2 className="text-lg font-bold text-white flex items-center gap-2">
                <span>Multi-Run Export & Portfolio Builder</span>
                <span className="text-xs px-2 py-0.5 rounded-full bg-sky-500/20 text-sky-300 font-semibold">
                  Q1 Journal Standard
                </span>
              </h2>
              <p className="text-xs text-slate-400">
                Curate your iterative exploration history. Select exact analyses, tables, charts, and formats before final download.
              </p>
            </div>
          </div>
          <button
            onClick={onClose}
            className="p-2 rounded-lg bg-white/5 hover:bg-white/10 text-slate-400 hover:text-white transition-all"
          >
            <X className="w-5 h-5" />
          </button>
        </div>

        {/* Modal Body Scroll Area */}
        <div className="flex-1 overflow-y-auto p-6 space-y-6">
          {/* Portfolio Title Input */}
          <div className="space-y-1.5">
            <label className="text-xs font-semibold text-slate-300 uppercase tracking-wider flex items-center gap-1.5">
              <FileText className="w-3.5 h-3.5 text-sky-400" />
              <span>Compiled Portfolio Document Title</span>
            </label>
            <input
              type="text"
              value={portfolioTitle}
              onChange={(e) => setPortfolioTitle(e.target.value)}
              placeholder="Enter manuscript or project report title..."
              className="w-full px-4 py-2.5 rounded-xl bg-slate-950 border border-white/15 text-white text-sm font-medium focus:outline-none focus:border-sky-500 transition-all shadow-inner"
            />
          </div>

          {/* Quick Select Buttons */}
          <div className="flex items-center justify-between bg-slate-950/60 px-4 py-3 rounded-xl border border-white/5">
            <span className="text-xs text-slate-300 font-medium">
              Saved Analyses in Session: <strong className="text-sky-400">{baseItems.length} runs</strong> ({countSelected} selected)
            </span>
            <div className="flex items-center gap-2">
              <button
                onClick={() => handleSelectAll(true)}
                className="px-3 py-1 text-xs font-semibold rounded-lg bg-sky-500/10 text-sky-300 hover:bg-sky-500/20 border border-sky-500/30 transition-all"
              >
                Select All
              </button>
              <button
                onClick={() => handleSelectAll(false)}
                className="px-3 py-1 text-xs font-semibold rounded-lg bg-slate-800 text-slate-400 hover:text-white transition-all"
              >
                Deselect All
              </button>
              {onClearHistory && baseItems.length > 0 && (
                <button
                  onClick={() => {
                    if (window.confirm('Clear all saved analysis runs from session history?')) {
                      onClearHistory();
                      onClose();
                    }
                  }}
                  className="px-3 py-1 text-xs font-semibold rounded-lg bg-rose-500/10 text-rose-400 hover:bg-rose-500/20 border border-rose-500/30 transition-all flex items-center gap-1"
                >
                  <Trash2 className="w-3.5 h-3.5" />
                  <span>Clear All</span>
                </button>
              )}
            </div>
          </div>

          {/* Checklist of Analysis Runs */}
          <div className="space-y-4">
            {baseItems.length === 0 ? (
              <div className="p-8 rounded-xl border border-dashed border-white/15 text-center text-slate-400 text-sm">
                No saved analysis runs found in your session yet. Execute an analysis first to build a multi-run portfolio!
              </div>
            ) : (
              baseItems.map((item, index) => {
                const id = item.history_id || `run_${index}`;
                const res = (item.analysis_result || (item as any).result || {}) as any;
                const cfg = selectedItems[id] || {
                  included: true,
                  include_table: true,
                  include_graph: true,
                  include_narrative: true,
                  include_code: true,
                  preferred_graph_type: 'default',
                };

                return (
                  <div
                    key={id}
                    className={`p-4 rounded-xl border transition-all ${
                      cfg.included
                        ? 'bg-slate-900/90 border-sky-500/40 shadow-lg shadow-sky-500/5'
                        : 'bg-slate-950/40 border-white/5 opacity-60'
                    }`}
                  >
                    <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3 border-b border-white/10 pb-3">
                      <div className="flex items-center gap-3">
                        <input
                          type="checkbox"
                          checked={cfg.included}
                          onChange={() => handleToggleItem(id)}
                          className="w-5 h-5 rounded border-white/30 text-sky-500 focus:ring-sky-500 cursor-pointer"
                        />
                        <div>
                          <h4 className="text-sm font-bold text-white flex items-center gap-2">
                            <span>{index + 1}. {res.method_name || 'Statistical Analysis'}</span>
                            <span className="text-[11px] font-normal px-2 py-0.5 rounded bg-white/5 text-slate-300">
                              N = {res.sample_size?.toLocaleString() || 'N/A'}
                            </span>
                          </h4>
                          <p className="text-xs text-slate-400 line-clamp-1 mt-0.5">
                            {res.description || 'Verified inference run with assumption diagnostics.'}
                          </p>
                        </div>
                      </div>

                      <div className="flex flex-wrap items-center gap-2">
                        {cfg.included && (
                          <div className="flex items-center gap-1.5 text-xs bg-slate-950 px-2.5 py-1.5 rounded-lg border border-white/5">
                            <span className="text-slate-400 font-medium">Chart:</span>
                            <select
                              value={cfg.preferred_graph_type}
                              onChange={(e) => handleChangeGraphType(id, e.target.value as any)}
                              className="bg-transparent text-sky-400 font-semibold focus:outline-none cursor-pointer"
                            >
                              <option value="default" className="bg-slate-900">Original Plot</option>
                              <option value="bar" className="bg-slate-900">Bar Diagram</option>
                              <option value="pie" className="bg-slate-900">Pie / Donut Chart</option>
                              <option value="box" className="bg-slate-900">Box & Whisker</option>
                            </select>
                          </div>
                        )}

                        {onSelectHistoryItem && (
                          <button
                            type="button"
                            onClick={() => {
                              onSelectHistoryItem(item);
                              onClose();
                            }}
                            title="Switch main screen to inspect this run"
                            className="p-1.5 rounded-lg bg-sky-500/10 border border-sky-500/20 text-sky-300 hover:bg-sky-500/20 transition-all text-xs flex items-center gap-1"
                          >
                            <Eye className="w-3.5 h-3.5" />
                            <span className="hidden md:inline">Inspect</span>
                          </button>
                        )}

                        {onRemoveHistoryItem && (
                          <button
                            type="button"
                            onClick={() => {
                              if (window.confirm('Remove this analysis run from your session history?')) {
                                onRemoveHistoryItem(id);
                              }
                            }}
                            title="Remove this run from session history"
                            className="p-1.5 rounded-lg bg-rose-500/10 border border-rose-500/20 text-rose-400 hover:bg-rose-500/20 transition-all text-xs flex items-center gap-1"
                          >
                            <Trash2 className="w-3.5 h-3.5" />
                          </button>
                        )}
                      </div>
                    </div>

                    {/* Section Toggles within Run */}
                    {cfg.included && (
                      <div className="grid grid-cols-2 sm:grid-cols-4 gap-3 pt-3">
                        <button
                          onClick={() => handleToggleOption(id, 'include_narrative')}
                          className={`flex items-center gap-2 p-2 rounded-lg border text-xs font-medium transition-all ${
                            cfg.include_narrative
                              ? 'bg-sky-500/15 border-sky-500/40 text-sky-300'
                              : 'bg-slate-950/60 border-white/5 text-slate-500 hover:text-slate-300'
                          }`}
                        >
                          <Check className={`w-3.5 h-3.5 ${cfg.include_narrative ? 'text-sky-400' : 'opacity-0'}`} />
                          <span>APA Narrative</span>
                        </button>

                        <button
                          onClick={() => handleToggleOption(id, 'include_table')}
                          className={`flex items-center gap-2 p-2 rounded-lg border text-xs font-medium transition-all ${
                            cfg.include_table
                              ? 'bg-sky-500/15 border-sky-500/40 text-sky-300'
                              : 'bg-slate-950/60 border-white/5 text-slate-500 hover:text-slate-300'
                          }`}
                        >
                          <Check className={`w-3.5 h-3.5 ${cfg.include_table ? 'text-sky-400' : 'opacity-0'}`} />
                          <span>Summary Table</span>
                        </button>

                        <button
                          onClick={() => handleToggleOption(id, 'include_graph')}
                          className={`flex items-center gap-2 p-2 rounded-lg border text-xs font-medium transition-all ${
                            cfg.include_graph
                              ? 'bg-sky-500/15 border-sky-500/40 text-sky-300'
                              : 'bg-slate-950/60 border-white/5 text-slate-500 hover:text-slate-300'
                          }`}
                        >
                          <Check className={`w-3.5 h-3.5 ${cfg.include_graph ? 'text-sky-400' : 'opacity-0'}`} />
                          <span>Diagnostic Figure</span>
                        </button>

                        <button
                          onClick={() => handleToggleOption(id, 'include_code')}
                          className={`flex items-center gap-2 p-2 rounded-lg border text-xs font-medium transition-all ${
                            cfg.include_code
                              ? 'bg-sky-500/15 border-sky-500/40 text-sky-300'
                              : 'bg-slate-950/60 border-white/5 text-slate-500 hover:text-slate-300'
                          }`}
                        >
                          <Check className={`w-3.5 h-3.5 ${cfg.include_code ? 'text-sky-400' : 'opacity-0'}`} />
                          <span>R / Python Script</span>
                        </button>
                      </div>
                    )}
                  </div>
                );
              })
            )}
          </div>

          {/* Export Format Selector */}
          <div className="space-y-3 pt-2">
            <label className="text-xs font-semibold text-slate-300 uppercase tracking-wider flex items-center gap-1.5">
              <Download className="w-3.5 h-3.5 text-sky-400" />
              <span>Target Compilation Format</span>
            </label>

            <div className="grid grid-cols-2 sm:grid-cols-4 gap-3">
              <button
                type="button"
                onClick={() => setSelectedFormat('pdf')}
                className={`flex flex-col items-start p-3.5 rounded-xl border transition-all text-left ${
                  selectedFormat === 'pdf'
                    ? 'bg-rose-500/15 border-rose-500/50 text-white shadow-lg shadow-rose-500/10'
                    : 'bg-slate-950/80 border-white/10 text-slate-400 hover:border-white/20 hover:text-white'
                }`}
              >
                <FileText className={`w-5 h-5 mb-2 ${selectedFormat === 'pdf' ? 'text-rose-400' : 'text-slate-500'}`} />
                <span className="text-sm font-bold">PDF Report</span>
                <span className="text-[11px] text-slate-400 mt-0.5">Formal multi-page document</span>
              </button>

              <button
                type="button"
                onClick={() => setSelectedFormat('doc')}
                className={`flex flex-col items-start p-3.5 rounded-xl border transition-all text-left ${
                  selectedFormat === 'doc'
                    ? 'bg-sky-500/15 border-sky-500/50 text-white shadow-lg shadow-sky-500/10'
                    : 'bg-slate-950/80 border-white/10 text-slate-400 hover:border-white/20 hover:text-white'
                }`}
              >
                <FileSpreadsheet className={`w-5 h-5 mb-2 ${selectedFormat === 'doc' ? 'text-sky-400' : 'text-slate-500'}`} />
                <span className="text-sm font-bold">MS Word Document</span>
                <span className="text-[11px] text-slate-400 mt-0.5">Editable .doc / .docx format</span>
              </button>

              <button
                type="button"
                onClick={() => setSelectedFormat('html')}
                className={`flex flex-col items-start p-3.5 rounded-xl border transition-all text-left ${
                  selectedFormat === 'html'
                    ? 'bg-emerald-500/15 border-emerald-500/50 text-white shadow-lg shadow-emerald-500/10'
                    : 'bg-slate-950/80 border-white/10 text-slate-400 hover:border-white/20 hover:text-white'
                }`}
              >
                <Globe className={`w-5 h-5 mb-2 ${selectedFormat === 'html' ? 'text-emerald-400' : 'text-slate-500'}`} />
                <span className="text-sm font-bold">Interactive HTML</span>
                <span className="text-[11px] text-slate-400 mt-0.5">Standalone browser file</span>
              </button>

              <button
                type="button"
                onClick={() => setSelectedFormat('rmarkdown')}
                className={`flex flex-col items-start p-3.5 rounded-xl border transition-all text-left ${
                  selectedFormat === 'rmarkdown'
                    ? 'bg-indigo-500/15 border-indigo-500/50 text-white shadow-lg shadow-indigo-500/10'
                    : 'bg-slate-950/80 border-white/10 text-slate-400 hover:border-white/20 hover:text-white'
                }`}
              >
                <Code2 className={`w-5 h-5 mb-2 ${selectedFormat === 'rmarkdown' ? 'text-indigo-400' : 'text-slate-500'}`} />
                <span className="text-sm font-bold">RMarkdown (.Rmd)</span>
                <span className="text-[11px] text-slate-400 mt-0.5">Literate RStudio script</span>
              </button>
            </div>
          </div>

          {/* Error Message */}
          {errorMessage && (
            <div className="p-4 rounded-xl bg-rose-500/15 border border-rose-500/30 text-rose-300 text-xs flex items-center gap-2">
              <AlertCircle className="w-4 h-4 flex-shrink-0 text-rose-400" />
              <span>{errorMessage}</span>
            </div>
          )}
        </div>

        {/* Modal Footer */}
        <div className="flex items-center justify-between px-6 py-4 border-t border-white/10 bg-slate-900/80 rounded-b-2xl">
          <div className="flex items-center gap-2 text-xs text-slate-400">
            <ShieldCheck className="w-4 h-4 text-emerald-400" />
            <span>Type I Error controlled across all compiled runs</span>
          </div>

          <div className="flex items-center gap-3">
            <button
              type="button"
              onClick={onClose}
              className="px-4 py-2 rounded-xl border border-white/10 text-slate-300 hover:bg-white/5 transition-all text-xs font-semibold"
            >
              Cancel
            </button>
            <button
              type="button"
              onClick={handleCompileAndDownload}
              disabled={isExporting || countSelected === 0}
              className={`px-6 py-2.5 rounded-xl font-bold text-xs flex items-center gap-2 shadow-lg transition-all ${
                exportSuccess
                  ? 'bg-emerald-500 text-white shadow-emerald-500/20'
                  : isExporting || countSelected === 0
                  ? 'bg-slate-800 text-slate-500 cursor-not-allowed'
                  : 'btn-primary shadow-sky-500/25 hover:scale-105'
              }`}
            >
              {exportSuccess ? (
                <>
                  <CheckCircle2 className="w-4 h-4 text-white" />
                  <span>Portfolio Downloaded!</span>
                </>
              ) : isExporting ? (
                <>
                  <div className="w-4 h-4 border-2 border-white/30 border-t-white rounded-full animate-spin" />
                  <span>Compiling Portfolio ({selectedFormat.toUpperCase()})...</span>
                </>
              ) : (
                <>
                  <Download className="w-4 h-4" />
                  <span>Compile & Download Portfolio ({countSelected} Runs)</span>
                </>
              )}
            </button>
          </div>
        </div>
      </div>
    </div>
  );
};
