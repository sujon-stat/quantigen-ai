import React, { useState } from 'react';
import { Copy, Check, Award, Zap, AlertTriangle } from 'lucide-react';
import type { MethodResult } from '../../types/statmind';

interface Q1JournalTableProps {
  result: MethodResult;
  sampleSize?: number;
}

// Helper functions
const formatNum = (num: any, decimals = 4): string => {
  if (num === null || num === undefined || num === '—' || num === '' || isNaN(Number(num))) return '—';
  const val = Number(num);
  if (Number.isInteger(val)) return String(val);
  return parseFloat(val.toFixed(decimals)).toString();
};

const formatPValue = (p: any): string => {
  if (p === null || p === undefined || p === '—' || isNaN(Number(p))) return '—';
  const num = Number(p);
  if (num < 0.001) return '< .001***';
  if (num < 0.01) return `${num.toFixed(3)}**`;
  if (num < 0.05) return `${num.toFixed(3)}*`;
  const str = formatNum(num, 3);
  return str.startsWith('0.') ? `.${str.substring(2)}` : str;
};

export const Q1JournalTable: React.FC<Q1JournalTableProps> = ({ result, sampleSize: propSampleSize }) => {
  const [copiedCsv, setCopiedCsv] = useState(false);
  const [copiedHtml, setCopiedHtml] = useState(false);

  if (!result) return null;

  const methodId = String(result.method_id || '').toLowerCase();
  const methodName = result.method_name || 'Statistical Analysis';
  const sampleSize = propSampleSize ?? result.sample_size ?? 0;
  const main = result.main_results || {};
  const effect = result.effect_sizes || {};

  const rows: any[] = [];
  const autoCorrections: string[] = Array.isArray(main.auto_corrections) ? main.auto_corrections : [];
  const isBatch = Boolean(main.is_batch);

  // Helper to extract non-batch test statistic string
  const getTestStat = (): { label: string; value: string; df: string } => {
    if (main.t_statistic !== undefined) {
      return { label: 't', value: formatNum(main.t_statistic), df: main.degrees_of_freedom !== undefined ? formatNum(main.degrees_of_freedom) : '—' };
    }
    if (main.f_statistic !== undefined) {
      const dfb = main.df_between !== undefined ? formatNum(main.df_between) : (main.df_num !== undefined ? formatNum(main.df_num) : '—');
      const dfw = main.df_within !== undefined ? formatNum(main.df_within) : (main.df_denom !== undefined ? formatNum(main.df_denom) : '—');
      return { label: 'F', value: formatNum(main.f_statistic), df: `${dfb}, ${dfw}` };
    }
    if (main.chi2_statistic !== undefined || main.chi2 !== undefined || main.likelihood_ratio_chi2 !== undefined) {
      const val = main.chi2_statistic ?? main.chi2 ?? main.likelihood_ratio_chi2;
      return { label: 'χ²', value: formatNum(val), df: main.degrees_of_freedom !== undefined ? formatNum(main.degrees_of_freedom) : (main.dof_model !== undefined ? formatNum(main.dof_model) : '1') };
    }
    if (main.z_statistic !== undefined || main.z !== undefined) {
      return { label: 'Z', value: formatNum(main.z_statistic ?? main.z), df: '—' };
    }
    if (main.u_statistic !== undefined || main.mann_whitney_u !== undefined) {
      return { label: 'U', value: formatNum(main.u_statistic ?? main.mann_whitney_u), df: '—' };
    }
    if (main.correlation_coefficient !== undefined || main.r !== undefined || main.spearman_rho !== undefined) {
      const val = main.correlation_coefficient ?? main.r ?? main.spearman_rho;
      return { label: methodId.includes('spearman') ? 'ρ' : 'r', value: formatNum(val), df: main.degrees_of_freedom !== undefined ? formatNum(main.degrees_of_freedom) : `n=${sampleSize}` };
    }
    return { label: 'Statistic', value: '—', df: '—' };
  };

  // Map the batch_engine output to table rows
  if (Array.isArray(main.multi_variable_table)) {
    main.multi_variable_table.forEach((item: any) => {
      if (item.status === 'error') {
        rows.push({
          variable: item.dependent_var || '—',
          category: item.grouping_var || '—',
          sampleSizeStr: '—',
          summaryMetric: '—',
          statValue: `⚠️ ${item.error_message || 'Execution Error'}`,
          dfStr: '—',
          pValueStr: '—',
          effectStr: '—',
        });
        return;
      }

      // 1. Summary Metrics (Mean ± SD per group)
      let summaryMetricStr = '—';
      const summaries = Array.isArray(item.group_summaries) ? item.group_summaries : [];
      if (summaries.length > 0) {
        summaryMetricStr = summaries.slice(0, 4).map((gs: any) => {
          const meanStr = gs.mean !== undefined ? formatNum(gs.mean, 2) : '';
          const sdStr = gs.sd !== undefined ? ` ±${formatNum(gs.sd, 2)}` : '';
          return `${gs.group}: ${meanStr}${sdStr}`;
        }).join(' | ');
        if (summaries.length > 4) summaryMetricStr += ` +${summaries.length - 4} more`;
      } else if (item.mean_difference !== undefined) {
        summaryMetricStr = `Δ = ${formatNum(item.mean_difference)}`;
      }

      // 2. Test Statistic (Using unified field names from batch_engine)
      const rawStat = item.test_statistic;
      let statLabel = 'Stat';
      const usedMethod = item.method_used || methodId;
      if (usedMethod.includes('ttest')) statLabel = 't';
      else if (usedMethod.includes('anova')) statLabel = 'F';
      else if (usedMethod.includes('mann')) statLabel = 'U';
      else if (usedMethod.includes('kruskal')) statLabel = 'H';
      else if (usedMethod.includes('chi')) statLabel = 'χ²';
      
      const statValStr = rawStat !== undefined ? `${statLabel} = ${formatNum(rawStat)}` : '—';

      // 3. Degrees of Freedom
      let dfStr = '—';
      if (item.degrees_of_freedom !== undefined) {
        dfStr = String(Math.round(item.degrees_of_freedom * 100) / 100);
      } else if (item.degrees_of_freedom_between !== undefined) {
        dfStr = `${item.degrees_of_freedom_between}, ${item.degrees_of_freedom_within}`;
      }

      // 4. Effect Size (Using unified field names from batch_engine)
      let effStr = '—';
      if (item.effect_size !== undefined && item.effect_size_label) {
        const label = item.effect_size_label.split('(')[0].trim();
        effStr = `${label} = ${formatNum(item.effect_size)}`;
      }

      // 5. Variable Names (Add ⚡ if auto-corrected)
      const corrected = Boolean(item.auto_corrected);
      const depName = item.dependent_var ?? 'Outcome';
      const grpName = item.grouping_var ?? 'Group';

      rows.push({
        variable: depName + (corrected ? ' ⚡' : ''),
        category: grpName,
        sampleSizeStr: String(item.n_total || 0),
        summaryMetric: summaryMetricStr,
        statValue: statValStr,
        dfStr: dfStr,
        pValueStr: formatPValue(item.p_value),
        effectStr: effStr,
      });
    });
  } else if (methodId.includes('descriptive')) {
    const vars = main.variables || main.columns || {};
    if (Object.keys(vars).length > 0) {
      Object.entries(vars).forEach(([vName, vData]: [string, any]) => {
        const mean = vData.mean !== undefined ? formatNum(vData.mean) : '—';
        const sd = vData.std !== undefined ? formatNum(vData.std) : (vData.sd !== undefined ? formatNum(vData.sd) : '—');
        const median = vData.median !== undefined ? formatNum(vData.median) : '—';
        const metricStr = mean !== '—' && sd !== '—' ? `${mean} ± ${sd}` : (median !== '—' ? `Median = ${median}` : 'Categorical');
        rows.push({
          variable: vName,
          category: 'Overall',
          sampleSizeStr: vData.n !== undefined ? String(vData.n) : String(sampleSize),
          summaryMetric: metricStr,
          statValue: vData.skewness !== undefined ? `Skew: ${formatNum(vData.skewness)}` : '—',
          dfStr: vData.kurtosis !== undefined ? `Kurt: ${formatNum(vData.kurtosis)}` : '—',
          pValueStr: '—',
          effectStr: '—'
        });
      });
    } else {
      const mean = main.mean !== undefined ? formatNum(main.mean) : '—';
      const sd = main.std !== undefined ? formatNum(main.std) : (main.sd !== undefined ? formatNum(main.sd) : '—');
      rows.push({
        variable: 'Analyzed Variable',
        category: 'Overall',
        sampleSizeStr: String(sampleSize),
        summaryMetric: mean !== '—' && sd !== '—' ? `${mean} ± ${sd}` : 'See Summary Chart',
        statValue: main.skewness !== undefined ? `Skew: ${formatNum(main.skewness)}` : '—',
        dfStr: main.kurtosis !== undefined ? `Kurt: ${formatNum(main.kurtosis)}` : '—',
        pValueStr: '—',
        effectStr: '—'
      });
    }
  } else if (main.group_statistics || main.group_means || (main.groups && typeof main.groups === 'object')) {
    const testStat = getTestStat();
    const pValStr = formatPValue(main.p_value ?? main.likelihood_ratio_p_value);
    const groups = main.group_statistics || main.group_means || main.groups || {};
    const depVarName = String(main.dependent_variable || main.dependent || 'Outcome');
    Object.entries(groups).forEach(([gName, gVal]: [string, any], index: number) => {
      const mean = typeof gVal === 'object' && gVal.mean !== undefined ? formatNum(gVal.mean) : (typeof gVal === 'number' ? formatNum(gVal) : '—');
      const sd = typeof gVal === 'object' && gVal ? (gVal.std !== undefined ? formatNum(gVal.std) : (gVal.sd !== undefined ? formatNum(gVal.sd) : '—')) : '—';
      const nStr = typeof gVal === 'object' && gVal.n !== undefined ? String(gVal.n) : (main.group_sizes && main.group_sizes[gName] !== undefined ? String(main.group_sizes[gName]) : `${Math.round(sampleSize / 2)}`);
      rows.push({
        variable: depVarName,
        category: String(gName),
        sampleSizeStr: nStr,
        summaryMetric: mean !== '—' && sd !== '—' ? `${mean} ± ${sd}` : (mean !== '—' ? `Mean = ${mean}` : '—'),
        statValue: index === 0 ? `${testStat.label} = ${testStat.value}` : '—',
        dfStr: index === 0 ? testStat.df : '—',
        pValueStr: index === 0 ? pValStr : '—',
        effectStr: index === 0 ? (effect.cohens_d !== undefined ? `d = ${formatNum(effect.cohens_d)}` : (effect.eta_squared !== undefined ? `η² = ${formatNum(effect.eta_squared)}` : '—')) : '—'
      });
    });
  } else {
    const testStat = getTestStat();
    const pValStr = formatPValue(main.p_value ?? main.likelihood_ratio_p_value);
    const depVarName = String(main.dependent_variable || main.dependent || 'Analyzed Variable');
    const grpVarName = String(main.independent_variable || main.grouping || 'Overall');
    rows.push({
      variable: depVarName,
      category: grpVarName,
      sampleSizeStr: String(sampleSize),
      summaryMetric: main.mean_difference !== undefined ? `Diff: ${formatNum(main.mean_difference)}` : (main.model_fit || 'Primary Analysis Outcome'),
      statValue: `${testStat.label} = ${testStat.value}`,
      dfStr: testStat.df,
      pValueStr: pValStr,
      effectStr: effect.cohens_d !== undefined ? `d = ${formatNum(effect.cohens_d)}` : (effect.eta_squared !== undefined ? `η² = ${formatNum(effect.eta_squared)}` : '—')
    });
  }

  const handleCopyCsv = () => {
    const headers = "Variable, Group, N, Summary, Statistic, df, p-value, Effect Size";
    const csvRows = rows.map(r => 
      `"${r.variable}", "${r.category}", "${r.sampleSizeStr}", "${r.summaryMetric}", "${r.statValue}", "${r.dfStr}", "${r.pValueStr}", "${r.effectStr}"`
    ).join('\n');
    navigator.clipboard.writeText(headers + '\n' + csvRows);
    setCopiedCsv(true);
    setTimeout(() => setCopiedCsv(false), 2000);
  };

  const handleCopyWord = async () => {
    let html = `<table style="width:100%; border-collapse:collapse; font-family:'Times New Roman', serif; font-size:11pt; color:#000000;">
    <thead>
      <tr style="border-top: 2pt solid #000000; border-bottom: 1pt solid #000000;">
        <th style="padding: 6pt 8pt; text-align: left; font-weight: bold;">Outcome Variable</th>
        <th style="padding: 6pt 8pt; text-align: left; font-weight: bold;">Grouping Variable</th>
        <th style="padding: 6pt 8pt; text-align: center; font-weight: bold;">N</th>
        <th style="padding: 6pt 8pt; text-align: center; font-weight: bold;">Summary (Mean ± SD)</th>
        <th style="padding: 6pt 8pt; text-align: center; font-weight: bold;">Statistic</th>
        <th style="padding: 6pt 8pt; text-align: center; font-weight: bold;">df</th>
        <th style="padding: 6pt 8pt; text-align: center; font-weight: bold;">p-value</th>
        <th style="padding: 6pt 8pt; text-align: left; font-weight: bold;">Effect Size</th>
      </tr>
    </thead>
    <tbody>`;
    rows.forEach((row, i) => {
      const isLast = i === rows.length - 1;
      const borderStyle = isLast ? 'border-bottom: 2pt solid #000000;' : 'border-bottom: none;';
      html += `
      <tr style="${borderStyle}">
        <td style="padding: 5pt 8pt; text-align: left; font-weight: normal;">${row.variable}</td>
        <td style="padding: 5pt 8pt; text-align: left; font-weight: normal;">${row.category}</td>
        <td style="padding: 5pt 8pt; text-align: center; font-weight: normal;">${row.sampleSizeStr}</td>
        <td style="padding: 5pt 8pt; text-align: center; font-weight: normal;">${row.summaryMetric}</td>
        <td style="padding: 5pt 8pt; text-align: center; font-weight: normal;">${row.statValue}</td>
        <td style="padding: 5pt 8pt; text-align: center; font-weight: normal;">${row.dfStr}</td>
        <td style="padding: 5pt 8pt; text-align: center; font-weight: normal;">${row.pValueStr}</td>
        <td style="padding: 5pt 8pt; text-align: left; font-weight: normal;">${row.effectStr}</td>
      </tr>`;
    });
    html += `</tbody></table><p style="font-family:'Times New Roman', serif; font-size:9.5pt; font-style:italic; margin-top:4pt;">Note. Test applied: ${methodName}. Table formatted to Q1 journal publication standards (APA 7th Edition). p < .05 considered statistically significant.</p>`;
    try {
      const blobHtml = new Blob([html], { type: 'text/html' });
      const blobText = new Blob([html.replace(/<[^>]+>/g, '')], { type: 'text/plain' });
      await navigator.clipboard.write([
        new ClipboardItem({
          'text/html': blobHtml,
          'text/plain': blobText
        })
      ]);
    } catch {
      navigator.clipboard.writeText(html);
    }
    setCopiedHtml(true);
    setTimeout(() => setCopiedHtml(false), 2000);
  };

  if (rows.length === 0) {
    return <p className="text-slate-400 text-sm p-4">No comparison table data available.</p>;
  }

  return (
    <div className="glass-panel p-6 space-y-4 border-l-4 border-l-sky-500 animate-fade-in">
      {/* Header */}
      <div className="flex flex-col sm:flex-row items-start sm:items-center justify-between gap-3 border-b border-white/10 pb-4">
        <div className="flex items-center gap-3">
          <Award className="w-5 h-5 text-amber-400" />
          <h3 className="text-md font-bold text-white font-serif">
            {result.method_name || "Table (APA 7th / JAMA)"}
          </h3>
        </div>

        <div className="flex items-center gap-2 flex-wrap">
          <button
            onClick={handleCopyCsv}
            className="flex items-center gap-1.5 px-3 py-1.5 text-xs bg-slate-800 border border-white/10 rounded-lg hover:bg-slate-700 transition font-medium text-slate-200"
          >
            {copiedCsv ? <Check className="w-3.5 h-3.5 text-emerald-400" /> : <Copy className="w-3.5 h-3.5" />}
            <span>{copiedCsv ? 'Copied CSV!' : 'Copy Table (CSV)'}</span>
          </button>
          <button
            onClick={handleCopyWord}
            className="btn-primary bg-gradient-to-r from-sky-600 to-blue-600 hover:from-sky-500 hover:to-blue-500 text-xs px-3.5 py-1.5 flex items-center gap-1.5 shadow-md shadow-sky-500/20"
          >
            {copiedHtml ? <Check className="w-3.5 h-3.5 text-emerald-300" /> : <Copy className="w-3.5 h-3.5" />}
            <span>{copiedHtml ? 'Copied with Borders!' : '📋 Copy for Word / Excel'}</span>
          </button>
        </div>
      </div>

      {/* Agentic Shield Auto-Correction Banners */}
      {autoCorrections.length > 0 && (
        <div className="space-y-2">
          {autoCorrections.map((note, i) => (
            <div key={i} className="flex items-start gap-2.5 bg-amber-500/10 border border-amber-400/40 rounded-xl px-4 py-3">
              <Zap className="w-4 h-4 text-amber-400 flex-shrink-0 mt-0.5" />
              <p className="text-xs text-amber-200 font-medium leading-relaxed">{note}</p>
            </div>
          ))}
        </div>
      )}

      {/* Batch Info Badge */}
      {isBatch && (
        <div className="flex items-center gap-2 text-[11px] text-sky-300 bg-sky-500/10 border border-sky-400/20 rounded-lg px-3 py-2">
          <AlertTriangle className="w-3.5 h-3.5 shrink-0" />
          <span><strong>{main.n_comparisons ?? rows.length}</strong> comparisons executed in batch. The ⚡ symbol indicates an auto-corrected method.</span>
        </div>
      )}

      {/* The Academic Table */}
      <div className="overflow-x-auto bg-slate-950/80 p-5 rounded-xl border border-white/10 shadow-inner">
        <table className="w-full text-left font-serif text-sm text-slate-200 border-collapse">
          <thead>
            <tr className="border-t-2 border-b border-slate-300 dark:border-slate-400 text-slate-100 dark:text-white">
              <th className="py-3 px-4 font-bold tracking-wider">Outcome Variable</th>
              <th className="py-3 px-4 font-bold tracking-wider">Grouping Variable</th>
              <th className="py-3 px-4 font-bold text-center">N</th>
              <th className="py-3 px-4 font-bold text-center">Summary (Mean ± SD)</th>
              <th className="py-3 px-4 font-bold text-center">Statistic</th>
              <th className="py-3 px-4 font-bold text-center">df</th>
              <th className="py-3 px-4 font-bold text-center">p-value</th>
              <th className="py-3 px-4 font-bold text-left">Effect Size</th>
            </tr>
          </thead>
          <tbody>
            {rows.map((row, idx) => {
              const isLast = idx === rows.length - 1;
              return (
                <tr
                  key={idx}
                  className={`transition-colors hover:bg-slate-800/40 ${
                    isLast ? 'border-b-2 border-slate-300 dark:border-slate-400' : 'border-b border-white/5'
                  }`}
                >
                  <td className="py-2.5 px-4 font-medium text-white whitespace-nowrap">{row.variable}</td>
                  <td className="py-2.5 px-4 text-slate-300 whitespace-nowrap">{row.category}</td>
                  <td className="py-2.5 px-4 text-center text-slate-400">{row.sampleSizeStr}</td>
                  <td className="py-2.5 px-4 text-xs text-slate-300 max-w-[250px]">{row.summaryMetric}</td>
                  <td className="py-2.5 px-4 text-center font-mono text-xs">{row.statValue}</td>
                  <td className="py-2.5 px-4 text-center font-mono text-xs text-slate-400">{row.dfStr}</td>
                  <td className="py-2.5 px-4 text-center font-mono text-xs font-bold text-emerald-300">{row.pValueStr}</td>
                  <td className="py-2.5 px-4 text-left font-mono text-xs text-sky-300">{row.effectStr}</td>
                </tr>
              );
            })}
          </tbody>
        </table>
        <div className="mt-3 text-[11px] font-serif italic text-slate-400 flex items-center justify-between">
          <span>Note. Test applied: {methodName}. Table formatted to Q1 journal publication standards (APA 7th Edition). * p &lt; .05, ** p &lt; .01, *** p &lt; .001.</span>
          <span className="text-slate-500 font-sans not-italic">Quantigen AI Precision Engine</span>
        </div>
      </div>
    </div>
  );
};
