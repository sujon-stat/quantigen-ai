import React, { useState } from 'react';
import { Upload, FileText, CheckCircle2, AlertCircle, RefreshCw, Table, Hash, Tag, Layers } from 'lucide-react';
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
      ) : (
        /* Dataset Loaded View */
        <div className="space-y-6">
          {/* Summary Banner */}
          <div className="glass-panel p-6 flex flex-col md:flex-row md:items-center justify-between gap-4 border-l-4 border-l-emerald-400">
            <div className="flex items-center gap-4">
              <div className="w-12 h-12 rounded-xl bg-emerald-500/10 border border-emerald-500/30 flex items-center justify-center">
                <CheckCircle2 className="w-6 h-6 text-emerald-400" />
              </div>
              <div>
                <div className="flex items-center gap-2">
                  <h3 className="text-lg font-bold text-white">{dataset.filename}</h3>
                  <span className="badge-pass">Verified & Parsed</span>
                </div>
                <p className="text-xs text-slate-300 mt-1">
                  <strong>{dataset.total_rows}</strong> observations • <strong>{dataset.total_columns}</strong> variables •{' '}
                  <strong>{dataset.missing_values_total}</strong> missing data points
                </p>
              </div>
            </div>
            <div className="flex items-center gap-3">
              <label htmlFor="dataset-change" className="btn-secondary text-xs cursor-pointer">
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
              <button onClick={onProceedToAnalysis} className="btn-primary text-xs">
                <span>Proceed to Analysis Studio</span>
                <CheckCircle2 className="w-4 h-4" />
              </button>
            </div>
          </div>

          {/* Variable Registry & Role Binding */}
          <div className="glass-panel p-6 space-y-4">
            <div className="flex items-center justify-between">
              <div>
                <h4 className="text-md font-bold text-white flex items-center gap-2">
                  <Tag className="w-4 h-4 text-sky-400" />
                  <span>Variable Registry & Statistical Role Assignment</span>
                </h4>
                <p className="text-xs text-slate-400 mt-0.5">
                  Click a variable's role badge below if you need to override StatMind's automated type inference (`Continuous`, `Categorical`, or `Binary`).
                </p>
              </div>
            </div>

            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              {dataset.columns.map((col) => (
                <div
                  key={col.name}
                  className="p-4 rounded-xl bg-slate-900/60 border border-white/5 flex flex-col justify-between gap-3 hover:border-white/15 transition-all"
                >
                  <div className="flex items-start justify-between gap-2">
                    <div className="flex items-center gap-2.5">
                      <div
                        className={`w-8 h-8 rounded-lg flex items-center justify-center text-xs font-bold ${
                          col.role === 'continuous'
                            ? 'bg-sky-500/20 text-sky-300 border border-sky-500/30'
                            : col.role === 'categorical'
                            ? 'bg-indigo-500/20 text-indigo-300 border border-indigo-500/30'
                            : 'bg-emerald-500/20 text-emerald-300 border border-emerald-500/30'
                        }`}
                      >
                        {col.role === 'continuous' ? <Hash className="w-4 h-4" /> : <Layers className="w-4 h-4" />}
                      </div>
                      <div>
                        <span className="font-semibold text-white text-sm">{col.name}</span>
                        <div className="text-[11px] text-slate-400">
                          Type: <code className="text-slate-300">{col.data_type}</code> • Unique: {col.unique_values} • Missing: {col.missing_count}
                        </div>
                      </div>
                    </div>

                    {/* Role Selector */}
                    <div className="flex items-center gap-1">
                      {(['continuous', 'categorical', 'binary'] as VariableRole[]).map((role) => (
                        <button
                          key={role}
                          onClick={() => handleRoleChange(col.name, role)}
                          disabled={updatingVar === col.name || col.role === role}
                          className={`px-2.5 py-1 rounded text-[11px] font-medium transition-all ${
                            col.role === role
                              ? 'bg-sky-500 text-white shadow-sm'
                              : 'bg-white/5 text-slate-400 hover:text-white hover:bg-white/10'
                          }`}
                        >
                          {role === 'continuous' ? 'Cont' : role === 'categorical' ? 'Cat' : 'Bin'}
                        </button>
                      ))}
                    </div>
                  </div>

                  {/* Summary Stats Pill */}
                  {col.summary_stats && (
                    <div className="mt-1 pt-2 border-t border-white/5 flex items-center justify-between text-[11px] text-slate-400">
                      {col.summary_stats.mean !== undefined ? (
                        <span>
                          Mean: <strong className="text-slate-200">{col.summary_stats.mean.toFixed(2)}</strong> (SD: {col.summary_stats.std?.toFixed(2)}) • Range: [{col.summary_stats.min?.toFixed(1)}, {col.summary_stats.max?.toFixed(1)}]
                        </span>
                      ) : col.summary_stats.categories ? (
                        <span>
                          Categories: <strong className="text-slate-200">{Object.keys(col.summary_stats.categories).slice(0, 4).join(', ')}</strong>
                        </span>
                      ) : null}
                    </div>
                  )}
                </div>
              ))}
            </div>
          </div>

          {/* Data Preview Table */}
          <div className="glass-panel p-6 space-y-4">
            <h4 className="text-md font-bold text-white flex items-center gap-2">
              <Table className="w-4 h-4 text-sky-400" />
              <span>Dataset Observation Preview (First 5 Rows)</span>
            </h4>
            <div className="overflow-x-auto rounded-xl border border-white/5">
              <table className="w-full text-left border-collapse text-xs">
                <thead>
                  <tr className="bg-slate-900/80 border-b border-white/10 text-slate-300">
                    {dataset.columns.map((col) => (
                      <th key={col.name} className="p-3 font-semibold">
                        {col.name}{' '}
                        <span className="text-[10px] text-sky-400/80 font-normal">({col.role})</span>
                      </th>
                    ))}
                  </tr>
                </thead>
                <tbody className="divide-y divide-white/5 bg-slate-900/40">
                  {dataset.preview_data.slice(0, 5).map((row, idx) => (
                    <tr key={idx} className="hover:bg-white/5 transition-colors">
                      {dataset.columns.map((col) => (
                        <td key={col.name} className="p-3 text-slate-300 font-mono">
                          {row[col.name] !== null && row[col.name] !== undefined ? String(row[col.name]) : <span className="text-slate-600 italic">null</span>}
                        </td>
                      ))}
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};
