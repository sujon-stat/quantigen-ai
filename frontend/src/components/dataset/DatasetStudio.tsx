import React, { useState } from 'react';
import { Upload, FileText, CheckCircle2, AlertCircle, RefreshCw, Table, Hash, Tag, Layers, Search, X, List, LayoutGrid, ChevronLeft, ChevronRight } from 'lucide-react';
import type { DatasetSummary, VariableRole } from '../../types/statmind';
import { api } from '../../api/client';

interface DatasetStudioProps {
  dataset: DatasetSummary | null;
  onDatasetLoaded: (summary: DatasetSummary) => void;
  onProceedToAnalysis: () => void;
}

export const DatasetStudio: React.FC<DatasetStudioProps> = ({
  dataset,
  onDatasetLoaded,
  onProceedToAnalysis,
}) => {
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [updatingVar, setUpdatingVar] = useState<string | null>(null);
  const [searchQuery, setSearchQuery] = useState('');
  const [roleFilter, setRoleFilter] = useState<'all' | 'continuous' | 'categorical' | 'ordinal' | 'count' | 'binary'>('all');
  const [viewMode, setViewMode] = useState<'table' | 'grid'>('table');
  const [currentPage, setCurrentPage] = useState(1);
  const pageSize = 15;

  const handleFileUpload = async (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (!file) return;

    setLoading(true);
    setError(null);
    try {
      const summary = await api.uploadDataset(file);
      onDatasetLoaded(summary);
    } catch (err: any) {
      const serverMsg = err.response?.data?.message || (typeof err.response?.data?.detail === 'string' ? err.response?.data?.detail : err.response?.data?.detail?.message);
      setError(serverMsg || err.message || 'Error uploading dataset');
    } finally {
      setLoading(false);
    }
  };

  const handleRoleChange = async (varName: string, newRole: VariableRole) => {
    if (!dataset) return;
    setUpdatingVar(varName);
    try {
      const updated = await api.updateVariableRole(dataset.dataset_id, varName, newRole);
      onDatasetLoaded(updated);
    } catch (err: any) {
      setError(err.response?.data?.detail?.message || 'Error updating variable role');
    } finally {
      setUpdatingVar(null);
    }
  };

  return (
    <div className="space-y-6 animate-fade-in">
      {/* Upload Box */}
      {!dataset ? (
        <div className="glass-panel p-10 text-center border-2 border-dashed border-sky-500/30 hover:border-sky-400/60 transition-all">
          <input
            type="file"
            id="dataset-upload"
            accept=".csv,.xlsx,.xls"
            onChange={handleFileUpload}
            className="hidden"
          />
          <label
            htmlFor="dataset-upload"
            className="cursor-pointer flex flex-col items-center justify-center space-y-4"
          >
            <div className="w-16 h-16 rounded-2xl bg-sky-500/10 border border-sky-400/30 flex items-center justify-center shadow-lg">
              {loading ? (
                <RefreshCw className="w-8 h-8 text-sky-400 animate-spin" />
              ) : (
                <Upload className="w-8 h-8 text-sky-400" />
              )}
            </div>
            <div>
              <h3 className="text-xl font-bold text-white mb-1">
                {loading ? 'Analyzing Dataset Structure...' : 'Upload Your Dataset (.csv or .xlsx)'}
              </h3>
              <p className="text-sm text-slate-400 max-w-md mx-auto">
                Upload your research data. StatMind AI will automatically infer variable types, check for missing data, and calculate diagnostic summary statistics.
              </p>
            </div>
            <div className="btn-primary mt-2">
              <FileText className="w-4 h-4" />
              <span>Select File from Computer</span>
            </div>
          </label>
          {error && (
            <div className="mt-6 p-4 rounded-xl bg-rose-500/10 border border-rose-500/30 text-rose-300 text-sm flex items-center justify-center gap-2 max-w-lg mx-auto">
              <AlertCircle className="w-5 h-5 flex-shrink-0" />
              <span>{error}</span>
            </div>
          )}
        </div>
      ) : (() => {
        /* Dataset Loaded View */
        const cols = dataset.columns || (dataset as any).variables || [];
        const previewRows = dataset.preview_data || (dataset as any).preview_rows || [];
        const filename = dataset.filename || (dataset as any).name || 'Dataset.csv';
        const totalRows = dataset.total_rows ?? (dataset as any).n_rows ?? 0;
        const totalCols = dataset.total_columns ?? (dataset as any).n_columns ?? cols.length;
        const missingTotal = dataset.missing_values_total ?? cols.reduce((acc: number, c: any) => acc + (c.missing_count || 0), 0);

        const getScale = (col: any) => col.role || col.data_type || col.detected_type || 'categorical';
        const contCount = cols.filter((c: any) => getScale(c) === 'continuous').length;
        const catCount = cols.filter((c: any) => getScale(c) === 'categorical').length;
        const ordCount = cols.filter((c: any) => getScale(c) === 'ordinal').length;
        const cntCount = cols.filter((c: any) => getScale(c) === 'count').length;
        const binCount = cols.filter((c: any) => getScale(c) === 'binary').length;

        const filteredCols = cols.filter((col: any) => {
          const matchesSearch = col.name.toLowerCase().includes(searchQuery.toLowerCase());
          const matchesRole = roleFilter === 'all' || getScale(col) === roleFilter;
          return matchesSearch && matchesRole;
        });

        const totalPages = Math.max(1, Math.ceil(filteredCols.length / pageSize));
        const safePage = Math.min(currentPage, totalPages);
        const paginatedCols = filteredCols.slice((safePage - 1) * pageSize, safePage * pageSize);

        return (
          <div className="space-y-6">
            {/* Summary Banner */}
            <div className="glass-panel p-6 flex flex-col md:flex-row md:items-center justify-between gap-4 border-l-4 border-l-emerald-400 shadow-xl shadow-emerald-500/5">
              <div className="flex items-center gap-4">
                <div className="w-12 h-12 rounded-xl bg-emerald-500/10 border border-emerald-500/30 flex items-center justify-center">
                  <CheckCircle2 className="w-6 h-6 text-emerald-400" />
                </div>
                <div>
                  <div className="flex items-center gap-2">
                    <h3 className="text-lg font-bold text-white">{filename}</h3>
                    <span className="badge-pass">Verified & Parsed</span>
                  </div>
                  <p className="text-xs text-slate-300 mt-1 flex items-center gap-2 flex-wrap">
                    <span className="bg-slate-900/80 px-2.5 py-1 rounded-md border border-white/5 font-mono">
                      <strong className="text-sky-300">{totalRows.toLocaleString()}</strong> rows
                    </span>
                    <span className="bg-slate-900/80 px-2.5 py-1 rounded-md border border-white/5 font-mono">
                      <strong className="text-sky-300">{totalCols}</strong> variables
                    </span>
                    <span className="bg-slate-900/80 px-2.5 py-1 rounded-md border border-white/5 font-mono">
                      <strong className={missingTotal > 0 ? "text-amber-400" : "text-emerald-400"}>{missingTotal}</strong> missing data points
                    </span>
                  </p>
                </div>
              </div>
              <div className="flex items-center gap-3">
                <label htmlFor="dataset-change" className="btn-secondary text-xs cursor-pointer shadow-md">
                  <Upload className="w-3.5 h-3.5" />
                  <span>Upload Different File</span>
                  <input
                    type="file"
                    id="dataset-change"
                    accept=".csv,.xlsx,.xls"
                    onChange={handleFileUpload}
                    className="hidden"
                  />
                </label>
                <button onClick={onProceedToAnalysis} className="btn-primary text-xs shadow-lg shadow-sky-500/20">
                  <span>Proceed to Analysis Studio</span>
                  <CheckCircle2 className="w-4 h-4" />
                </button>
              </div>
            </div>

            {/* Variable Registry & Role Binding */}
            <div className="glass-panel p-6 space-y-5">
              <div className="flex flex-col lg:flex-row lg:items-center justify-between gap-4 border-b border-white/10 pb-4">
                <div>
                  <h4 className="text-md font-bold text-white flex items-center gap-2">
                    <Tag className="w-4 h-4 text-sky-400" />
                    <span>Measurement Scale Assignment & Variable Registry</span>
                  </h4>
                  <p className="text-xs text-slate-400 mt-0.5">
                    Explore distributions and override formal statistical Measurement Scales (`Continuous`, `Categorical`, `Ordinal`, `Count`, or `Binary`).
                  </p>
                </div>

                {/* View Mode Toggle */}
                <div className="flex items-center gap-2 bg-slate-900/80 p-1 rounded-lg border border-white/10 self-start lg:self-auto">
                  <button
                    onClick={() => setViewMode('table')}
                    className={`flex items-center gap-1.5 px-3 py-1.5 rounded-md text-xs font-medium transition-all ${
                      viewMode === 'table'
                        ? 'bg-sky-500 text-white shadow-sm'
                        : 'text-slate-400 hover:text-white hover:bg-white/5'
                    }`}
                  >
                    <List className="w-3.5 h-3.5" />
                    <span>Compact Table</span>
                  </button>
                  <button
                    onClick={() => setViewMode('grid')}
                    className={`flex items-center gap-1.5 px-3 py-1.5 rounded-md text-xs font-medium transition-all ${
                      viewMode === 'grid'
                        ? 'bg-sky-500 text-white shadow-sm'
                        : 'text-slate-400 hover:text-white hover:bg-white/5'
                    }`}
                  >
                    <LayoutGrid className="w-3.5 h-3.5" />
                    <span>Cards Grid</span>
                  </button>
                </div>
              </div>

              {/* Search & Filter Bar */}
              <div className="flex flex-col md:flex-row md:items-center justify-between gap-4">
                {/* Search Box */}
                <div className="relative w-full md:w-72">
                  <Search className="w-4 h-4 absolute left-3 top-1/2 -translate-y-1/2 text-slate-400" />
                  <input
                    type="text"
                    value={searchQuery}
                    onChange={(e) => {
                      setSearchQuery(e.target.value);
                      setCurrentPage(1);
                    }}
                    placeholder={`Search ${cols.length} variables...`}
                    className="w-full bg-slate-900/90 border border-white/10 rounded-xl pl-9 pr-8 py-2 text-xs text-white placeholder:text-slate-500 focus:outline-none focus:border-sky-400 transition-all"
                  />
                  {searchQuery && (
                    <button
                      onClick={() => {
                        setSearchQuery('');
                        setCurrentPage(1);
                      }}
                      className="absolute right-2.5 top-1/2 -translate-y-1/2 text-slate-400 hover:text-white p-0.5"
                    >
                      <X className="w-3.5 h-3.5" />
                    </button>
                  )}
                </div>

                {/* Role Filters */}
                <div className="flex items-center gap-1.5 overflow-x-auto pb-1 md:pb-0 custom-scrollbar">
                  {[
                    { id: 'all', label: `All (${cols.length})` },
                    { id: 'continuous', label: `Continuous (${contCount})` },
                    { id: 'categorical', label: `Categorical (${catCount})` },
                    { id: 'ordinal', label: `Ordinal (${ordCount})` },
                    { id: 'count', label: `Count (${cntCount})` },
                    { id: 'binary', label: `Binary (${binCount})` },
                  ].map((tab) => (
                    <button
                      key={tab.id}
                      onClick={() => {
                        setRoleFilter(tab.id as any);
                        setCurrentPage(1);
                      }}
                      className={`px-3 py-1.5 rounded-lg text-xs font-medium whitespace-nowrap transition-all ${
                        roleFilter === tab.id
                          ? 'bg-white/15 text-white border border-white/20 shadow-sm'
                          : 'bg-slate-900/50 text-slate-400 hover:text-white hover:bg-white/5 border border-transparent'
                      }`}
                    >
                      {tab.label}
                    </button>
                  ))}
                </div>
              </div>

              {/* Variables Display: Compact Table vs Grid */}
              {filteredCols.length === 0 ? (
                <div className="p-8 text-center bg-slate-900/40 rounded-xl border border-white/5">
                  <AlertCircle className="w-8 h-8 text-slate-500 mx-auto mb-2" />
                  <p className="text-sm font-semibold text-slate-300">No variables found matching "{searchQuery}"</p>
                  <button
                    onClick={() => { setSearchQuery(''); setRoleFilter('all'); }}
                    className="mt-3 btn-secondary text-xs"
                  >
                    Reset Filters
                  </button>
                </div>
              ) : viewMode === 'table' ? (
                /* Compact Table View */
                <div className="overflow-x-auto rounded-xl border border-white/10 bg-slate-900/40 shadow-inner">
                  <table className="w-full text-left border-collapse text-xs">
                    <thead>
                      <tr className="bg-slate-900/90 border-b border-white/10 text-slate-300 font-semibold uppercase tracking-wider text-[11px]">
                        <th className="p-3.5">Variable Name</th>
                        <th className="p-3.5">Detected Type</th>
                        <th className="p-3.5">Data Quality</th>
                        <th className="p-3.5">Distribution Summary</th>
                        <th className="p-3.5 text-right">Measurement Scale (Level)</th>
                      </tr>
                    </thead>
                    <tbody className="divide-y divide-white/5">
                      {paginatedCols.map((col: any) => {
                        const role = getScale(col);
                        const dataType = col.data_type || col.detected_type || 'categorical';
                        return (
                          <tr key={col.name} className="hover:bg-white/[0.04] transition-colors group">
                            <td className="p-3.5 font-medium text-white">
                              <div className="flex items-center gap-2.5">
                                <div
                                  className={`w-7 h-7 rounded-lg flex items-center justify-center text-xs font-bold shrink-0 ${
                                    role === 'continuous'
                                      ? 'bg-sky-500/20 text-sky-300 border border-sky-500/30'
                                      : role === 'categorical'
                                      ? 'bg-indigo-500/20 text-indigo-300 border border-indigo-500/30'
                                      : role === 'ordinal'
                                      ? 'bg-purple-500/20 text-purple-300 border border-purple-500/30'
                                      : role === 'count'
                                      ? 'bg-amber-500/20 text-amber-300 border border-amber-500/30'
                                      : 'bg-emerald-500/20 text-emerald-300 border border-emerald-500/30'
                                  }`}
                                >
                                  {role === 'continuous' || role === 'count' ? <Hash className="w-3.5 h-3.5" /> : <Layers className="w-3.5 h-3.5" />}
                                </div>
                                <span className="font-semibold text-white text-sm group-hover:text-sky-300 transition-colors">{col.name}</span>
                              </div>
                            </td>
                            <td className="p-3.5">
                              <span className="px-2 py-0.5 rounded bg-white/5 border border-white/10 font-mono text-[11px] text-slate-300">
                                {dataType}
                              </span>
                            </td>
                            <td className="p-3.5 text-slate-400">
                              <span>
                                Unique: <strong className="text-slate-200">{col.unique_values ?? 0}</strong> • Missing:{' '}
                                <strong className={col.missing_count > 0 ? "text-amber-400" : "text-emerald-400"}>{col.missing_count ?? 0}</strong>
                              </span>
                            </td>
                            <td className="p-3.5 text-slate-400 font-mono text-[11px]">
                              {col.summary_stats && col.summary_stats.mean !== undefined && col.summary_stats.mean !== null ? (
                                <span className="text-slate-300">
                                  Mean: <strong className="text-white">{Number(col.summary_stats.mean).toFixed(2)}</strong> {col.summary_stats.std !== undefined && col.summary_stats.std !== null ? `(SD: ${Number(col.summary_stats.std).toFixed(2)})` : ''} • Range [{col.summary_stats.min !== undefined && col.summary_stats.min !== null ? Number(col.summary_stats.min).toFixed(1) : '?'}, {col.summary_stats.max !== undefined && col.summary_stats.max !== null ? Number(col.summary_stats.max).toFixed(1) : '?'}]
                                </span>
                              ) : col.summary_stats && col.summary_stats.categories ? (
                                <span className="text-slate-300">
                                  Categories: <strong className="text-white">{Object.keys(col.summary_stats.categories).slice(0, 4).join(', ')}</strong>
                                </span>
                              ) : (
                                <span className="text-slate-500 italic">—</span>
                              )}
                            </td>
                            <td className="p-3.5 text-right">
                              <div className="inline-flex items-center gap-1 bg-slate-900/90 p-1 rounded-lg border border-white/10">
                                {(['continuous', 'categorical', 'ordinal', 'count', 'binary'] as VariableRole[]).map((r) => (
                                  <button
                                    key={r}
                                    title={r === 'continuous' ? 'Continuous (Interval/Ratio)' : r === 'categorical' ? 'Categorical (Nominal)' : r === 'ordinal' ? 'Ordinal (Ranked categories)' : r === 'count' ? 'Count (Discrete integers)' : 'Binary (Dichotomous)'}
                                    onClick={() => handleRoleChange(col.name, r)}
                                    disabled={updatingVar === col.name || role === r}
                                    className={`px-2 py-1 rounded text-[11px] font-medium transition-all ${
                                      role === r
                                        ? r === 'ordinal'
                                          ? 'bg-purple-500 text-white shadow-sm font-bold'
                                          : r === 'count'
                                          ? 'bg-amber-600 text-white shadow-sm font-bold'
                                          : r === 'categorical'
                                          ? 'bg-indigo-500 text-white shadow-sm font-bold'
                                          : r === 'binary'
                                          ? 'bg-emerald-500 text-white shadow-sm font-bold'
                                          : 'bg-sky-500 text-white shadow-sm font-bold'
                                        : 'bg-transparent text-slate-400 hover:text-white hover:bg-white/10'
                                    }`}
                                  >
                                    {r === 'continuous' ? 'Cont' : r === 'categorical' ? 'Cat' : r === 'ordinal' ? 'Ord' : r === 'count' ? 'Cnt' : 'Bin'}
                                  </button>
                                ))}
                              </div>
                            </td>
                          </tr>
                        );
                      })}
                    </tbody>
                  </table>
                </div>
              ) : (
                /* Card Grid View */
                <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
                  {paginatedCols.map((col: any) => {
                    const role = getScale(col);
                    const dataType = col.data_type || col.detected_type || 'categorical';
                    return (
                      <div
                        key={col.name}
                        className="p-4 rounded-xl bg-slate-900/60 border border-white/5 flex flex-col justify-between gap-3 hover:border-white/15 transition-all shadow-md group"
                      >
                        <div className="flex items-start justify-between gap-2">
                          <div className="flex items-center gap-2.5">
                            <div
                              className={`w-8 h-8 rounded-lg flex items-center justify-center text-xs font-bold shrink-0 ${
                                role === 'continuous'
                                  ? 'bg-sky-500/20 text-sky-300 border border-sky-500/30'
                                  : role === 'categorical'
                                  ? 'bg-indigo-500/20 text-indigo-300 border border-indigo-500/30'
                                  : role === 'ordinal'
                                  ? 'bg-purple-500/20 text-purple-300 border border-purple-500/30'
                                  : role === 'count'
                                  ? 'bg-amber-500/20 text-amber-300 border border-amber-500/30'
                                  : 'bg-emerald-500/20 text-emerald-300 border border-emerald-500/30'
                              }`}
                            >
                              {role === 'continuous' || role === 'count' ? <Hash className="w-4 h-4" /> : <Layers className="w-4 h-4" />}
                            </div>
                            <div>
                              <span className="font-semibold text-white text-sm group-hover:text-sky-300 transition-colors">{col.name}</span>
                              <div className="text-[11px] text-slate-400 mt-0.5">
                                Type: <code className="text-slate-300 font-mono">{dataType}</code>
                              </div>
                            </div>
                          </div>

                          {/* Role Selector */}
                          <div className="flex items-center gap-0.5 bg-slate-950 p-1 rounded-lg border border-white/10 shrink-0 flex-wrap">
                            {(['continuous', 'categorical', 'ordinal', 'count', 'binary'] as VariableRole[]).map((r) => (
                              <button
                                key={r}
                                title={r === 'continuous' ? 'Continuous (Interval/Ratio)' : r === 'categorical' ? 'Categorical (Nominal)' : r === 'ordinal' ? 'Ordinal (Ranked categories)' : r === 'count' ? 'Count (Discrete integers)' : 'Binary (Dichotomous)'}
                                onClick={() => handleRoleChange(col.name, r)}
                                disabled={updatingVar === col.name || role === r}
                                className={`px-1.5 py-0.5 rounded text-[10px] font-medium transition-all ${
                                  role === r
                                    ? r === 'ordinal'
                                      ? 'bg-purple-500 text-white shadow-sm font-bold'
                                      : r === 'count'
                                      ? 'bg-amber-600 text-white shadow-sm font-bold'
                                      : r === 'categorical'
                                      ? 'bg-indigo-500 text-white shadow-sm font-bold'
                                      : r === 'binary'
                                      ? 'bg-emerald-500 text-white shadow-sm font-bold'
                                      : 'bg-sky-500 text-white shadow-sm font-bold'
                                    : 'text-slate-400 hover:text-white hover:bg-white/10'
                                }`}
                              >
                                {r === 'continuous' ? 'Cont' : r === 'categorical' ? 'Cat' : r === 'ordinal' ? 'Ord' : r === 'count' ? 'Cnt' : 'Bin'}
                              </button>
                            ))}
                          </div>
                        </div>

                        <div className="text-[11px] text-slate-400 flex items-center justify-between border-t border-white/5 pt-2.5">
                          <span>Unique: <strong className="text-slate-200">{col.unique_values ?? 0}</strong></span>
                          <span>Missing: <strong className={col.missing_count > 0 ? "text-amber-400" : "text-emerald-400"}>{col.missing_count ?? 0}</strong></span>
                        </div>

                        {/* Summary Stats Pill */}
                        {col.summary_stats && (
                          <div className="bg-slate-950/60 p-2 rounded-lg border border-white/5 text-[11px] text-slate-400 font-mono">
                            {col.summary_stats.mean !== undefined && col.summary_stats.mean !== null ? (
                              <div className="space-y-0.5">
                                <div className="text-slate-300">Mean: <strong className="text-white">{Number(col.summary_stats.mean).toFixed(2)}</strong> {col.summary_stats.std !== undefined && col.summary_stats.std !== null ? `(SD: ${Number(col.summary_stats.std).toFixed(2)})` : ''}</div>
                                <div className="text-[10px] text-slate-400">Range: [{col.summary_stats.min !== undefined && col.summary_stats.min !== null ? Number(col.summary_stats.min).toFixed(1) : '?'}, {col.summary_stats.max !== undefined && col.summary_stats.max !== null ? Number(col.summary_stats.max).toFixed(1) : '?'}]</div>
                              </div>
                            ) : col.summary_stats.categories ? (
                              <div>
                                <span className="text-slate-400">Top: </span>
                                <strong className="text-slate-200">{Object.keys(col.summary_stats.categories).slice(0, 3).join(', ')}</strong>
                              </div>
                            ) : null}
                          </div>
                        )}
                      </div>
                    );
                  })}
                </div>
              )}

              {/* Pagination Controls */}
              {totalPages > 1 && (
                <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3 pt-3 border-t border-white/10 text-xs text-slate-400">
                  <div>
                    Showing <strong className="text-white">{(safePage - 1) * pageSize + 1}</strong> to{' '}
                    <strong className="text-white">{Math.min(safePage * pageSize, filteredCols.length)}</strong> of{' '}
                    <strong className="text-white">{filteredCols.length}</strong> variables
                  </div>
                  <div className="flex items-center gap-2">
                    <button
                      onClick={() => setCurrentPage(1)}
                      disabled={safePage === 1}
                      className="px-2.5 py-1.5 rounded-lg bg-slate-900 border border-white/10 text-slate-300 disabled:opacity-40 disabled:cursor-not-allowed hover:bg-white/5"
                    >
                      First
                    </button>
                    <button
                      onClick={() => setCurrentPage((p) => Math.max(1, p - 1))}
                      disabled={safePage === 1}
                      className="p-1.5 rounded-lg bg-slate-900 border border-white/10 text-slate-300 disabled:opacity-40 disabled:cursor-not-allowed hover:bg-white/5"
                    >
                      <ChevronLeft className="w-4 h-4" />
                    </button>
                    <span className="px-3 py-1 font-mono text-slate-200 bg-white/5 rounded-lg">
                      Page {safePage} of {totalPages}
                    </span>
                    <button
                      onClick={() => setCurrentPage((p) => Math.min(totalPages, p + 1))}
                      disabled={safePage === totalPages}
                      className="p-1.5 rounded-lg bg-slate-900 border border-white/10 text-slate-300 disabled:opacity-40 disabled:cursor-not-allowed hover:bg-white/5"
                    >
                      <ChevronRight className="w-4 h-4" />
                    </button>
                    <button
                      onClick={() => setCurrentPage(totalPages)}
                      disabled={safePage === totalPages}
                      className="px-2.5 py-1.5 rounded-lg bg-slate-900 border border-white/10 text-slate-300 disabled:opacity-40 disabled:cursor-not-allowed hover:bg-white/5"
                    >
                      Last
                    </button>
                  </div>
                </div>
              )}
            </div>

            {/* Data Preview Table */}
            <div className="glass-panel p-6 space-y-4">
              <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-2 border-b border-white/10 pb-4">
                <div>
                  <h4 className="text-md font-bold text-white flex items-center gap-2">
                    <Table className="w-4 h-4 text-sky-400" />
                    <span>Dataset Observation Preview (First 5 Rows)</span>
                  </h4>
                  <p className="text-xs text-slate-400 mt-0.5">
                    Showing first 5 observations across all {cols.length} variables. Scroll horizontally to inspect columns.
                  </p>
                </div>
                <span className="text-xs font-mono bg-sky-500/10 text-sky-300 border border-sky-500/30 px-3 py-1 rounded-full shrink-0">
                  {cols.length} Total Columns
                </span>
              </div>
              <div className="overflow-x-auto rounded-xl border border-white/10 bg-slate-900/60 shadow-inner max-h-[380px] custom-scrollbar relative">
                <table className="w-full text-left border-collapse text-xs">
                  <thead>
                    <tr className="bg-slate-950 border-b border-white/10 text-slate-300 uppercase font-semibold text-[11px] tracking-wider sticky top-0 z-20">
                      {cols.map((col: any, colIdx: number) => {
                        const role = getScale(col);
                        return (
                          <th
                            key={col.name}
                            className={`p-3.5 whitespace-nowrap border-r border-white/5 ${
                              colIdx === 0
                                ? 'sticky left-0 bg-slate-950 shadow-md z-30 text-sky-300'
                                : ''
                            }`}
                          >
                            <div className="flex items-center gap-1.5">
                              <span>{col.name}</span>
                              <span className="text-[10px] text-slate-400 font-normal font-mono">({role})</span>
                            </div>
                          </th>
                        );
                      })}
                    </tr>
                  </thead>
                  <tbody className="divide-y divide-white/5">
                    {previewRows.slice(0, 5).map((row: any, idx: number) => (
                      <tr key={idx} className="hover:bg-white/[0.04] transition-colors">
                        {cols.map((col: any, colIdx: number) => (
                          <td
                            key={col.name}
                            className={`p-3.5 font-mono text-slate-300 whitespace-nowrap border-r border-white/5 ${
                              colIdx === 0
                                ? 'sticky left-0 bg-slate-950/95 font-semibold text-white shadow-md z-10'
                                : ''
                            }`}
                          >
                            {row && row[col.name] !== null && row[col.name] !== undefined ? (
                              String(row[col.name])
                            ) : (
                              <span className="text-slate-600 italic">null</span>
                            )}
                          </td>
                        ))}
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            </div>
          </div>
        );
      })()}
    </div>
  );
};
