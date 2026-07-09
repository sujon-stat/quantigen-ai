import React, { useState } from 'react';
import { Copy, Check, FileText, Award } from 'lucide-react';
import type { MethodResult } from '../../types/statmind';

interface Q1JournalTableProps {
  result: MethodResult;
}

export const Q1JournalTable: React.FC<Q1JournalTableProps> = ({ result }) => {
  const [copiedHtml, setCopiedHtml] = useState(false);
  const [copiedLatex, setCopiedLatex] = useState(false);

  if (!result) return null;

  const methodId = String(result.method_id || '').toLowerCase();
  const methodName = result.method_name || 'Statistical Analysis';
  const sampleSize = result.sample_size || 0;
  const main = result.main_results || {};
  const effect = result.effect_sizes || {};

  // Helper to format APA p-values
  const formatPValue = (p: any): string => {
    if (p === undefined || p === null) return 'N/A';
    const num = Number(p);
    if (isNaN(num)) return String(p);
    if (num < 0.001) return '< .001';
    const rounded = Math.round(num * 1000) / 1000;
    const str = rounded.toFixed(3);
    return str.startsWith('0.') ? `.${str.substring(2)}` : str;
  };

  // Helper to extract test statistic string
  const getTestStat = (): { label: string; value: string; df: string } => {
    if (main.t_statistic !== undefined) {
      return { label: 't', value: Number(main.t_statistic).toFixed(2), df: main.degrees_of_freedom !== undefined ? Number(main.degrees_of_freedom).toFixed(1) : '—' };
    }
    if (main.f_statistic !== undefined) {
      const dfb = main.df_between !== undefined ? main.df_between : (main.df_num !== undefined ? main.df_num : '—');
      const dfw = main.df_within !== undefined ? main.df_within : (main.df_denom !== undefined ? main.df_denom : '—');
      return { label: 'F', value: Number(main.f_statistic).toFixed(2), df: `${dfb}, ${dfw}` };
    }
    if (main.chi2_statistic !== undefined || main.chi2 !== undefined || main.likelihood_ratio_chi2 !== undefined) {
      const val = main.chi2_statistic ?? main.chi2 ?? main.likelihood_ratio_chi2;
      return { label: 'χ²', value: Number(val).toFixed(2), df: main.degrees_of_freedom !== undefined ? String(main.degrees_of_freedom) : (main.dof_model !== undefined ? String(main.dof_model) : '1') };
    }
    if (main.z_statistic !== undefined || main.z !== undefined) {
      return { label: 'Z', value: Number(main.z_statistic ?? main.z).toFixed(2), df: '—' };
    }
    if (main.u_statistic !== undefined || main.mann_whitney_u !== undefined) {
      return { label: 'U', value: Number(main.u_statistic ?? main.mann_whitney_u).toFixed(1), df: '—' };
    }
    if (main.correlation_coefficient !== undefined || main.r !== undefined || main.spearman_rho !== undefined) {
      const val = main.correlation_coefficient ?? main.r ?? main.spearman_rho;
      return { label: methodId.includes('spearman') ? 'ρ' : 'r', value: Number(val).toFixed(3), df: main.degrees_of_freedom !== undefined ? String(main.degrees_of_freedom) : `n=${sampleSize}` };
    }
    return { label: 'Statistic', value: '—', df: '—' };
  };

  const testStat = getTestStat();
  const pValStr = formatPValue(main.p_value ?? main.likelihood_ratio_p_value);

  // Extract primary effect size string
  const getEffectSizeStr = (): string => {
    const entries = Object.entries(effect).filter(([_, v]) => typeof v === 'number');
    if (entries.length === 0) return '—';
    return entries.map(([k, v]) => `${k.replace('_', ' ')} = ${(v as number).toFixed(2)}`).join('; ');
  };

  const effectStr = getEffectSizeStr();

  // Generate table rows depending on method
  interface TableRow {
    variable: string;
    sampleSizeStr: string;
    summaryMetric: string;
    statValue: string;
    dfStr: string;
    pValueStr: string;
    effectStr: string;
  }

  const rows: TableRow[] = [];

  if (methodId.includes('descriptive')) {
    // Check if we have descriptive statistics rows or variable summaries
    const vars = main.variables || main.columns || {};
    if (Object.keys(vars).length > 0) {
      Object.entries(vars).forEach(([vName, vData]: [string, any]) => {
        const mean = vData.mean !== undefined ? Number(vData.mean).toFixed(2) : '—';
        const sd = vData.std !== undefined ? Number(vData.std).toFixed(2) : (vData.sd !== undefined ? Number(vData.sd).toFixed(2) : '—');
        const median = vData.median !== undefined ? Number(vData.median).toFixed(2) : '—';
        const metricStr = mean !== '—' && sd !== '—' ? `${mean} ± ${sd}` : (median !== '—' ? `Median = ${median}` : 'Categorical');
        rows.push({
          variable: vName,
          sampleSizeStr: vData.n !== undefined ? String(vData.n) : String(sampleSize),
          summaryMetric: metricStr,
          statValue: vData.skewness !== undefined ? `Skew: ${Number(vData.skewness).toFixed(2)}` : '—',
          dfStr: vData.kurtosis !== undefined ? `Kurt: ${Number(vData.kurtosis).toFixed(2)}` : '—',
          pValueStr: '—',
          effectStr: '—'
        });
      });
    } else {
      const mean = main.mean !== undefined ? Number(main.mean).toFixed(2) : '—';
      const sd = main.std !== undefined ? Number(main.std).toFixed(2) : (main.sd !== undefined ? Number(main.sd).toFixed(2) : '—');
      rows.push({
        variable: 'Analyzed Variables (Composite)',
        sampleSizeStr: String(sampleSize),
        summaryMetric: mean !== '—' && sd !== '—' ? `${mean} ± ${sd}` : 'See Summary Chart',
        statValue: main.skewness !== undefined ? `Skew: ${Number(main.skewness).toFixed(2)}` : '—',
        dfStr: main.kurtosis !== undefined ? `Kurt: ${Number(main.kurtosis).toFixed(2)}` : '—',
        pValueStr: '—',
        effectStr: '—'
      });
    }
  } else if (main.group_statistics || main.group_means) {
    const groups = main.group_statistics || main.group_means || {};
    Object.entries(groups).forEach(([gName, gVal]: [string, any], index: number) => {
      const mean = typeof gVal === 'object' && gVal.mean !== undefined ? Number(gVal.mean).toFixed(2) : (typeof gVal === 'number' ? gVal.toFixed(2) : '—');
      const sd = typeof gVal === 'object' && gVal ? (gVal.std !== undefined ? Number(gVal.std).toFixed(2) : (gVal.sd !== undefined ? Number(gVal.sd).toFixed(2) : '—')) : '—';
      const nStr = typeof gVal === 'object' && gVal.n !== undefined ? String(gVal.n) : (main.group_sizes && main.group_sizes[gName] !== undefined ? String(main.group_sizes[gName]) : `${Math.round(sampleSize / 2)}`);
      rows.push({
        variable: `Group: ${gName}`,
        sampleSizeStr: nStr,
        summaryMetric: mean !== '—' && sd !== '—' ? `${mean} ± ${sd}` : (mean !== '—' ? `Mean = ${mean}` : '—'),
        statValue: index === 0 ? `${testStat.label} = ${testStat.value}` : '—',
        dfStr: index === 0 ? testStat.df : '—',
        pValueStr: index === 0 ? pValStr : '—',
        effectStr: index === 0 ? effectStr : '—'
      });
    });
  } else {
    rows.push({
      variable: methodName,
      sampleSizeStr: String(sampleSize),
      summaryMetric: main.mean_difference !== undefined ? `Diff: ${Number(main.mean_difference).toFixed(2)}` : (main.model_fit || 'Primary Analysis Outcome'),
      statValue: `${testStat.label} = ${testStat.value}`,
      dfStr: testStat.df,
      pValueStr: pValStr,
      effectStr: effectStr
    });
  }

  // Construct pure HTML markup for Word/Excel clipboard
  const getHtmlMarkup = (): string => {
    let html = `<table style="width:100%; border-collapse:collapse; font-family:'Times New Roman', serif; font-size:11pt; color:#000000;">
    <thead>
      <tr style="border-top: 2pt solid #000000; border-bottom: 1pt solid #000000;">
        <th style="padding: 6pt 8pt; text-align: left; font-weight: bold;">Variable / Group</th>
        <th style="padding: 6pt 8pt; text-align: center; font-weight: bold;">n</th>
        <th style="padding: 6pt 8pt; text-align: center; font-weight: bold;">Mean ± SD / Summary</th>
        <th style="padding: 6pt 8pt; text-align: center; font-weight: bold;">Test Stat</th>
        <th style="padding: 6pt 8pt; text-align: center; font-weight: bold;">df</th>
        <th style="padding: 6pt 8pt; text-align: center; font-weight: bold;">p</th>
        <th style="padding: 6pt 8pt; text-align: left; font-weight: bold;">Effect Size</th>
      </tr>
    </thead>
    <tbody>`;
    rows.forEach((row, i) => {
      const isLast = i === rows.length - 1;
      const borderStyle = isLast ? 'border-bottom: 2pt solid #000000;' : 'border-bottom: none;';
      html += `
      <tr style="${borderStyle}">
        <td style="padding: 5pt 8pt; text-align: left;">${row.variable}</td>
        <td style="padding: 5pt 8pt; text-align: center;">${row.sampleSizeStr}</td>
        <td style="padding: 5pt 8pt; text-align: center;">${row.summaryMetric}</td>
        <td style="padding: 5pt 8pt; text-align: center;">${row.statValue}</td>
        <td style="padding: 5pt 8pt; text-align: center;">${row.dfStr}</td>
        <td style="padding: 5pt 8pt; text-align: center;">${row.pValueStr}</td>
        <td style="padding: 5pt 8pt; text-align: left;">${row.effectStr}</td>
      </tr>`;
    });
    html += `
    </tbody>
  </table>
  <p style="font-family:'Times New Roman', serif; font-size:9.5pt; font-style:italic; margin-top:4pt;">Note. Table formatted to Q1 journal publication standards (APA 7th Edition). p < .05 considered statistically significant.</p>`;
    return html;
  };

  const getLatexMarkup = (): string => {
    let latex = `\\begin{table}[htbp]
\\centering
\\caption{${methodName} Results and Summary Statistics}
\\begin{tabular}{l c c c c c l}
\\toprule
\\textbf{Variable / Group} & \\textbf{n} & \\textbf{Mean $\\pm$ SD / Summary} & \\textbf{Test Stat} & \\textbf{df} & \\textbf{\\textit{p}} & \\textbf{Effect Size} \\\\
\\midrule\n`;
    rows.forEach((row) => {
      const cleanVar = row.variable.replace(/_/g, '\\_').replace(/%/g, '\\%');
      latex += `${cleanVar} & ${row.sampleSizeStr} & ${row.summaryMetric} & ${row.statValue} & ${row.dfStr} & ${row.pValueStr} & ${row.effectStr} \\\\\n`;
    });
    latex += `\\bottomrule
\\end{tabular}
\\vspace{1ex}
\\raggedright \\small \\textit{Note.} Table formatted to APA 7th / Q1 journal publication standards.
\\end{table}`;
    return latex;
  };

  const handleCopyWord = async () => {
    try {
      const html = getHtmlMarkup();
      const blobHtml = new Blob([html], { type: 'text/html' });
      const blobText = new Blob([html.replace(/<[^>]+>/g, '')], { type: 'text/plain' });
      await navigator.clipboard.write([
        new ClipboardItem({
          'text/html': blobHtml,
          'text/plain': blobText
        })
      ]);
      setCopiedHtml(true);
      setTimeout(() => setCopiedHtml(false), 2500);
    } catch {
      // Fallback
      navigator.clipboard.writeText(getHtmlMarkup());
      setCopiedHtml(true);
      setTimeout(() => setCopiedHtml(false), 2500);
    }
  };

  const handleCopyLatex = () => {
    navigator.clipboard.writeText(getLatexMarkup());
    setCopiedLatex(true);
    setTimeout(() => setCopiedLatex(false), 2500);
  };

  return (
    <div className="glass-panel p-6 space-y-4 border-l-4 border-l-sky-500 animate-fade-in">
      <div className="flex flex-col sm:flex-row items-start sm:items-center justify-between gap-3 border-b border-white/10 pb-4">
        <div>
          <div className="flex items-center gap-2">
            <Award className="w-5 h-5 text-sky-400" />
            <h3 className="text-md font-bold text-white">Q1 Journal Publication-Ready Table (APA 7th / JAMA)</h3>
          </div>
          <p className="text-xs text-slate-400 mt-0.5">
            Formatted with top/bottom horizontal rules, zero vertical gridlines, and exact APA 7th \(p\)-value precision.
          </p>
        </div>

        <div className="flex items-center gap-2 flex-wrap">
          <button
            onClick={handleCopyWord}
            className="btn-primary bg-gradient-to-r from-sky-600 to-blue-600 hover:from-sky-500 hover:to-blue-500 text-xs px-3.5 py-1.5 flex items-center gap-1.5 shadow-md shadow-sky-500/20"
          >
            {copiedHtml ? <Check className="w-3.5 h-3.5 text-emerald-300" /> : <Copy className="w-3.5 h-3.5" />}
            <span>{copiedHtml ? 'Copied with Borders!' : '📋 Copy Table for Word / Excel'}</span>
          </button>

          <button
            onClick={handleCopyLatex}
            className="btn-secondary text-xs px-3 py-1.5 flex items-center gap-1.5 border-white/20 hover:border-white/40"
          >
            {copiedLatex ? <Check className="w-3.5 h-3.5 text-emerald-400" /> : <FileText className="w-3.5 h-3.5 text-slate-300" />}
            <span>{copiedLatex ? 'Copied LaTeX!' : '📋 Copy LaTeX Table'}</span>
          </button>
        </div>
      </div>

      {/* On-Screen Table Preview */}
      <div className="overflow-x-auto bg-slate-950/80 p-5 rounded-xl border border-white/10 shadow-inner">
        <table className="w-full text-left font-serif text-sm text-slate-200 border-collapse">
          <thead>
            <tr className="border-t-2 border-b border-slate-300 dark:border-slate-400 text-slate-100 dark:text-white">
              <th className="py-3 px-4 font-bold tracking-wider">Variable / Group</th>
              <th className="py-3 px-4 font-bold text-center">n</th>
              <th className="py-3 px-4 font-bold text-center">Mean ± SD / Summary</th>
              <th className="py-3 px-4 font-bold text-center">Test Stat</th>
              <th className="py-3 px-4 font-bold text-center">df</th>
              <th className="py-3 px-4 font-bold text-center">p</th>
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
                    isLast ? 'border-b-2 border-slate-300 dark:border-slate-400 font-semibold text-white' : 'border-b border-white/5'
                  }`}
                >
                  <td className="py-2.5 px-4 font-medium">{row.variable}</td>
                  <td className="py-2.5 px-4 text-center">{row.sampleSizeStr}</td>
                  <td className="py-2.5 px-4 text-center">{row.summaryMetric}</td>
                  <td className="py-2.5 px-4 text-center">{row.statValue}</td>
                  <td className="py-2.5 px-4 text-center">{row.dfStr}</td>
                  <td className="py-2.5 px-4 text-center text-emerald-300 font-mono">{row.pValueStr}</td>
                  <td className="py-2.5 px-4 text-left text-sky-300">{row.effectStr}</td>
                </tr>
              );
            })}
          </tbody>
        </table>
        <div className="mt-3 text-[11px] font-serif italic text-slate-400 flex items-center justify-between">
          <span>Note. Table formatted to Q1 journal publication standards (APA 7th Edition). p &lt; .05 considered statistically significant.</span>
          <span className="text-slate-500 font-sans not-italic">Quantigen AI Precision Engine</span>
        </div>
      </div>
    </div>
  );
};
