import React, { useState } from 'react';
import { 
  Table as TableIcon, 
  LayoutGrid, 
  CheckCircle2, 
  AlertTriangle, 
  XCircle, 
  BarChart2, 
  Sparkles, 
  Search 
} from 'lucide-react';
import type { DatasetSummary } from '../../types/statmind';

interface DatasetViewSwitcherProps {
  dataset: DatasetSummary;
  onSelectVariable?: (varName: string) => void;
}

export const DatasetViewSwitcher: React.FC<DatasetViewSwitcherProps> = ({
  dataset,
  onSelectVariable
}) => {
  const [viewMode, setViewMode] = useState<'spreadsheet' | 'cards'>('spreadsheet');
  const [searchQuery, setSearchQuery] = useState('');
  const [filterRole, setFilterRole] = useState<string>('all');

  const variables = (dataset.columns || (dataset as any).variables || []).map((col: any) => {
    const name = col.name || col.id || col;
    const type = col.type || col.inferred_type || col.data_type || 'continuous';
    const missing = col.missing_count || col.missing || 0;
    const total = dataset.total_rows || (dataset as any).n_rows || 100;
    const missingPct = Math.round((missing / total) * 100);
    const outliers = col.outliers_count || col.outliers || (missing > 0 ? 1 : 0);
    
    const dist = col.skewness && Math.abs(col.skewness) > 1 ? 'Skewed' : col.is_normal === false ? 'Non-Normal' : 'Approximately Normal';
    const rec = type === 'continuous' || type === 'numeric' ? 'Mean ± SD' : 'n (%) frequencies';

    return {
      name,
      type,
      missing,
      missingPct,
      outliers,
      dist,
      rec,
      mean: col.mean,
      std: col.std || col.std_dev,
      unique: col.unique_count || col.unique_values
    };
  });

  const filteredVariables = variables.filter((v) => {
    const matchesSearch = v.name.toLowerCase().includes(searchQuery.toLowerCase());
    const matchesRole = filterRole === 'all' ? true : v.type.toLowerCase() === filterRole;
    return matchesSearch && matchesRole;
  });

  return (
    <div className="space-y-6 animate-fade-in">
      {/* Control Bar: View Toggle, Search & Filters */}
      <div className="flex flex-col sm:flex-row items-stretch sm:items-center justify-between gap-4 bg-slate-900/90 p-4 rounded-2xl border border-white/10 shadow-lg">
        <div className="flex items-center gap-3">
          <div className="flex items-center p-1 rounded-xl bg-slate-950 border border-white/10 text-xs font-bold">
            <button
              onClick={() => setViewMode('spreadsheet')}
              className={`flex items-center gap-1.5 px-3 py-1.5 rounded-lg transition-all ${
                viewMode === 'spreadsheet'
                  ? 'bg-sky-500 text-white shadow-sm'
                  : 'text-slate-400 hover:text-white'
              }`}
            >
              <TableIcon className="w-4 h-4" />
              <span>Spreadsheet Grid (SPSS + Sheets)</span>
            </button>
            <button
              onClick={() => setViewMode('cards')}
              className={`flex items-center gap-1.5 px-3 py-1.5 rounded-lg transition-all ${
                viewMode === 'cards'
                  ? 'bg-sky-500 text-white shadow-sm'
                  : 'text-slate-400 hover:text-white'
              }`}
            >
              <LayoutGrid className="w-4 h-4" />
              <span>Variable Cards ({variables.length})</span>
            </button>
          </div>
        </div>

        <div className="flex items-center gap-3">
          <div className="relative flex-1 sm:w-64">
            <Search className="w-4 h-4 text-slate-400 absolute left-3 top-1/2 -translate-y-1/2" />
            <input
              type="text"
              placeholder="Search variable name..."
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              className="w-full pl-9 pr-3 py-1.5 rounded-xl bg-slate-950 border border-white/10 text-xs text-white placeholder-slate-500 focus:outline-none focus:border-sky-400"
            />
          </div>

          <select
            value={filterRole}
            onChange={(e) => setFilterRole(e.target.value)}
            className="px-3 py-1.5 rounded-xl bg-slate-950 border border-white/10 text-xs text-slate-200 focus:outline-none focus:border-sky-400"
          >
            <option value="all">All Roles</option>
            <option value="continuous">Continuous / Numeric</option>
            <option value="binary">Binary</option>
            <option value="categorical">Categorical / Nominal</option>
          </select>
        </div>
      </div>

      {/* Spreadsheet Grid View (Google Sheets + SPSS hybrid) */}
      {viewMode === 'spreadsheet' && (
        <div className="overflow-x-auto rounded-2xl border border-white/10 bg-slate-950 shadow-xl custom-scrollbar">
          <table className="w-full text-left border-collapse text-xs">
            <thead>
              <tr className="bg-slate-900 border-b border-white/10 text-slate-300 font-bold uppercase tracking-wider">
                <th className="py-3 px-4 w-12 text-center bg-slate-900/90 border-r border-white/10">#</th>
                <th className="py-3 px-4">Variable Name</th>
                <th className="py-3 px-4">Role & Badge</th>
                <th className="py-3 px-4 text-center">Missing</th>
                <th className="py-3 px-4 text-center">Outliers</th>
                <th className="py-3 px-4">Distribution Profile</th>
                <th className="py-3 px-4">Recommended Summary</th>
                <th className="py-3 px-4 text-right">Actions</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-white/5">
              {filteredVariables.map((v, idx) => {
                const isNumeric = v.type === 'continuous' || v.type === 'numeric';
                const isBinary = v.type === 'binary' || v.unique === 2;
                
                return (
                  <tr 
                    key={v.name}
                    onClick={() => onSelectVariable && onSelectVariable(v.name)}
                    className="hover:bg-sky-500/10 transition-colors cursor-pointer group"
                  >
                    <td className="py-3 px-4 text-center font-mono text-slate-500 bg-slate-900/40 border-r border-white/10">
                      {idx + 1}
                    </td>
                    <td className="py-3 px-4 font-bold text-white group-hover:text-sky-300">
                      <div className="flex items-center gap-2">
                        <BarChart2 className="w-4 h-4 text-sky-400 flex-shrink-0" />
                        <span>{v.name}</span>
                      </div>
                    </td>
                    <td className="py-3 px-4">
                      {isNumeric ? (
                        <span className="inline-flex items-center gap-1 px-2 py-0.5 rounded-full bg-emerald-500/20 text-emerald-300 font-bold border border-emerald-500/40 text-[10px]">
                          <CheckCircle2 className="w-3 h-3" />
                          <span>✔ Numeric / Continuous [Green]</span>
                        </span>
                      ) : isBinary ? (
                        <span className="inline-flex items-center gap-1 px-2 py-0.5 rounded-full bg-emerald-500/20 text-emerald-300 font-bold border border-emerald-500/40 text-[10px]">
                          <CheckCircle2 className="w-3 h-3" />
                          <span>✔ Binary [Green]</span>
                        </span>
                      ) : (
                        <span className="inline-flex items-center gap-1 px-2 py-0.5 rounded-full bg-sky-500/20 text-sky-300 font-bold border border-sky-400/40 text-[10px]">
                          <span>Categorical ({v.unique || 'N/A'} levels)</span>
                        </span>
                      )}
                    </td>
                    <td className="py-3 px-4 text-center">
                      {v.missing === 0 ? (
                        <span className="text-emerald-400 font-mono">0 (0%)</span>
                      ) : (
                        <span className="inline-flex items-center gap-1 px-2 py-0.5 rounded-full bg-amber-500/20 text-amber-300 font-bold border border-amber-500/40 text-[10px]">
                          <AlertTriangle className="w-3 h-3" />
                          <span>⚠ {v.missing} ({v.missingPct}%) [Amber]</span>
                        </span>
                      )}
                    </td>
                    <td className="py-3 px-4 text-center">
                      {v.outliers === 0 ? (
                        <span className="text-slate-400 font-mono">0</span>
                      ) : (
                        <span className="inline-flex items-center gap-1 px-2 py-0.5 rounded-full bg-rose-500/20 text-rose-300 font-bold border border-rose-500/40 text-[10px]">
                          <XCircle className="w-3 h-3" />
                          <span>❌ {v.outliers} Outliers [Red]</span>
                        </span>
                      )}
                    </td>
                    <td className="py-3 px-4 text-slate-300">
                      <span className="font-medium">{v.dist}</span>
                    </td>
                    <td className="py-3 px-4 font-mono text-sky-300">
                      {v.rec}
                    </td>
                    <td className="py-3 px-4 text-right">
                      <button
                        onClick={(e) => {
                          e.stopPropagation();
                          onSelectVariable && onSelectVariable(v.name);
                        }}
                        className="px-2.5 py-1 rounded bg-slate-800 hover:bg-sky-500 text-slate-300 hover:text-white transition-all text-[11px] font-bold"
                      >
                        Explore
                      </button>
                    </td>
                  </tr>
                );
              })}
            </tbody>
          </table>
        </div>
      )}

      {/* Variable Cards View */}
      {viewMode === 'cards' && (
        <div className="grid grid-cols-1 sm:grid-cols-2 md:grid-cols-3 lg:grid-cols-4 gap-4">
          {filteredVariables.map((v) => {
            const isNumeric = v.type === 'continuous' || v.type === 'numeric';
            const isBinary = v.type === 'binary' || v.unique === 2;

            return (
              <div
                key={v.name}
                onClick={() => onSelectVariable && onSelectVariable(v.name)}
                className="group relative rounded-2xl bg-slate-900/90 border border-white/10 hover:border-sky-400/60 p-4 shadow-lg hover:shadow-sky-500/10 transition-all duration-300 cursor-pointer flex flex-col justify-between space-y-3"
              >
                <div className="space-y-2">
                  <div className="flex items-start justify-between gap-2">
                    <h4 className="font-bold text-white text-sm group-hover:text-sky-300 transition-colors truncate">
                      {v.name}
                    </h4>
                    {isNumeric || isBinary ? (
                      <span className="px-2 py-0.5 rounded-full bg-emerald-500/20 text-emerald-300 text-[9px] font-bold border border-emerald-500/40 flex items-center gap-1 flex-shrink-0">
                        <CheckCircle2 className="w-2.5 h-2.5" />
                        <span>{isNumeric ? 'Continuous' : 'Binary'}</span>
                      </span>
                    ) : (
                      <span className="px-2 py-0.5 rounded-full bg-sky-500/20 text-sky-300 text-[9px] font-bold border border-sky-400/40 flex-shrink-0">
                        Categorical
                      </span>
                    )}
                  </div>

                  <div className="grid grid-cols-2 gap-2 pt-2 border-t border-white/10 text-xs">
                    <div className="bg-slate-950/60 p-2 rounded-lg border border-white/5">
                      <span className="text-[10px] text-slate-400 block font-mono uppercase">Missing</span>
                      <span className={`font-bold ${v.missing > 0 ? 'text-amber-300' : 'text-emerald-400'}`}>
                        {v.missing > 0 ? `⚠ ${v.missing} (${v.missingPct}%)` : '0 (0%)'}
                      </span>
                    </div>

                    <div className="bg-slate-950/60 p-2 rounded-lg border border-white/5">
                      <span className="text-[10px] text-slate-400 block font-mono uppercase">Outliers</span>
                      <span className={`font-bold ${v.outliers > 0 ? 'text-rose-300' : 'text-slate-300'}`}>
                        {v.outliers > 0 ? `❌ ${v.outliers}` : '0 checked'}
                      </span>
                    </div>
                  </div>

                  <div className="bg-slate-950/40 p-2 rounded-lg text-xs space-y-1">
                    <div className="flex items-center justify-between text-slate-400 text-[11px]">
                      <span>Distribution:</span>
                      <span className="text-slate-200 font-medium">{v.dist}</span>
                    </div>
                    <div className="flex items-center justify-between text-slate-400 text-[11px]">
                      <span>Recommended:</span>
                      <span className="text-sky-300 font-mono">{v.rec}</span>
                    </div>
                  </div>
                </div>

                <div className="pt-2 border-t border-white/10 flex items-center justify-between text-[11px] font-bold text-sky-400 group-hover:text-sky-300">
                  <span className="flex items-center gap-1">
                    <Sparkles className="w-3 h-3 text-amber-300" />
                    Inspect Card
                  </span>
                  <span>Explore →</span>
                </div>
              </div>
            );
          })}
        </div>
      )}
    </div>
  );
};
