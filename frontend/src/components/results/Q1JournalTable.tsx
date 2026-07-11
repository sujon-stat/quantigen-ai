import React, { useState } from 'react';
import { Copy, Check, Award, Zap, AlertTriangle } from 'lucide-react';
import type { MethodResult } from '../../types/statmind';

interface TableProps {
  result: MethodResult;
}

export const Table: React.FC<TableProps> = ({ result }) => {
  const [copiedHtml, setCopiedHtml] = useState(false);

  if (!result) return null;

  const methodId = String(result.method_id || '').toLowerCase();
  const sampleSize = result.sample_size || 0;
  const main = result.main_results || {};
  const effect = result.effect_sizes || {};

  // Helper to format any number to at most 4 decimal values
  const formatNum = (val: any, maxDecimals: number = 4): string => {
    if (val === undefined || val === null || val === '—' || val === '') return '—';
    const num = Number(val);
    if (isNaN(num)) return String(val);
    if (Number.isInteger(num)) return String(num);
    const fixed = num.toFixed(maxDecimals);
    return parseFloat(fixed).toString();
  };

  // Helper to format APA p-values (at most 4 decimals)
  const formatPValue = (p: any): string => {
    if (p === undefined || p === null) return 'N/A';
    const num = Number(p);
    if (isNaN(num)) return String(p);
    if (num < 0.001) return '< .001';
    const str = formatNum(num, 4);
    return str.startsWith('0.') ? `.${str.substring(2)}` : str;
  };

  // Helper to extract test statistic string
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

  const testStat = getTestStat();
  const pValStr = formatPValue(main.p_value ?? main.likelihood_ratio_p_value);

  // Extract primary effect size string formatted as cohens d=0.01 [-0.45, 0.46]
  const getEffectSizeStr = (): string => {
    const entries = Object.entries(effect).filter(([_, v]) => typeof v === 'number');
    if (entries.length === 0) return '—';

    let mainLabel = '';
    let mainVal: number | undefined;
    let lowerVal: number | undefined;
    let upperVal: number | undefined;

    const remaining: string[] = [];

    for (const [k, v] of entries) {
      const lk = k.toLowerCase();
      if (lk.includes('ci_lower') || lk.includes('ci lower') || (lk.includes('lower') && !lk.includes('bound_test'))) {
        lowerVal = v as number;
      } else if (lk.includes('ci_upper') || lk.includes('ci upper') || (lk.includes('upper') && !lk.includes('bound_test'))) {
        upperVal = v as number;
      } else if (lk.includes('cohen') || lk === 'cohens_d' || lk === 'cohens d' || lk === 'd') {
        mainLabel = 'cohens d';
        mainVal = v as number;
      } else if (lk.includes('eta') || lk === 'eta_squared') {
        mainLabel = 'eta squared';
        mainVal = v as number;
      } else if (lk === 'r_squared' || lk === 'r2') {
        mainLabel = 'R²';
        mainVal = v as number;
      } else if (lk === 'cramers_v' || lk === 'v') {
        mainLabel = 'Cramers V';
        mainVal = v as number;
      } else if (lk === 'odds_ratio' || lk === 'or') {
        mainLabel = 'Odds Ratio';
        mainVal = v as number;
      } else if (lk === 'hedges_g' || lk === 'g') {
        mainLabel = 'hedges g';
        mainVal = v as number;
      } else {
        remaining.push(`${k.replace(/_/g, ' ')} = ${formatNum(v)}`);
      }
    }

    if (mainVal === undefined) {
      for (const [k, v] of entries) {
        const lk = k.toLowerCase();
        if (!lk.includes('lower') && !lk.includes('upper')) {
          mainLabel = k.replace(/_/g, ' ');
          const idx = remaining.findIndex(s => s.startsWith(mainLabel));
          if (idx !== -1) remaining.splice(idx, 1);
          mainVal = v as number;
          break;
        }
      }
    }

    if (mainVal !== undefined) {
      const mainStr = `${mainLabel}=${formatNum(mainVal)}`;
      if (lowerVal !== undefined && upperVal !== undefined) {
        return `${mainStr} [${formatNum(lowerVal)}, ${formatNum(upperVal)}]`;
      }
      return remaining.length > 0 ? `${mainStr}; ${remaining.join('; ')}` : mainStr;
    }

    if (lowerVal !== undefined && upperVal !== undefined) {
      return `95% CI [${formatNum(lowerVal)}, ${formatNum(upperVal)}]`;
    }

    return entries.map(([k, v]) => `${k.replace(/_/g, ' ')} = ${formatNum(v as number)}`).join('; ');
  };

  const effectStr = getEffectSizeStr();

  // Generate table rows depending on method
  // Extract exact variable and category names for table display
  const depVar = result.variables_used?.dependent || result.variables_used?.target || result.variables_used?.variable_1 || main.dependent_variable || main.variable || 'Primary Outcome';
  const indepVar = result.variables_used?.independent || result.variables_used?.group || result.variables_used?.factor || result.variables_used?.variable_2 || main.group_variable || 'Grouping Factor';
  const allUsed = Object.entries(result.variables_used || {}).map(([_, v]) => `${v}`).join(', ') || 'Analyzed Variables';

  // Generate table rows depending on method
  interface TableRow {
    variable: string;
    category: string;
    sampleSizeStr: string;
    summaryMetric: string;
    statValue: string;
    dfStr: string;
    pValueStr: string;
    effectStr: string;
  }

  const rows: TableRow[] = [];
  const autoCorrections: string[] = Array.isArray(main.auto_corrections) ? main.auto_corrections : [];
  const isBatch = Boolean(main.is_batch);

  if (Array.isArray(main.multi_variable_table)) {
    main.multi_variable_table.forEach((item: any) => {
      // Support BOTH old field names and new batch_engine field names
      const depName = item.dependent_var ?? item.variable ?? 'Outcome';
      const grpName = item.grouping_var ?? item.grouping_column ?? 'Group';
      const n = item.n_total ?? 0;

      // Build summary metric string from group_summaries embedded in each row
      let summaryMetricStr = '—';
      const rowSummaries = Array.isArray(item.group_summaries) ? item.group_summaries : [];
      const legacySummaries = Array.isArray(main.group_summaries)
        ? main.group_summaries.filter((gs: any) => gs.variable === depName && gs.grouping_column === grpName)
        : [];
      const summaries = rowSummaries.length > 0 ? rowSummaries : legacySummaries;
      if (summaries.length > 0) {
        summaryMetricStr = summaries.slice(0, 4).map((gs: any) => {
          const meanStr = gs.mean !== undefined ? formatNum(gs.mean, 2) : '';
          const sdStr = gs.sd !== undefined ? '±' + formatNum(gs.sd, 2) : '';
          return `${gs.group}: ${meanStr}${sdStr}`;
        }).join(' | ');
        if (summaries.length > 4) summaryMetricStr += ` +${summaries.length - 4} more`;
      } else if (item.mean_difference !== undefined) {
        summaryMetricStr = `Δ = ${formatNum(item.mean_difference)}`;
      }

      // Test statistic — support new field name `test_statistic` and old per-method names
      const rawStat = item.test_statistic ?? item.f_statistic ?? item.t_statistic ??
                      item.u_statistic ?? item.h_statistic ?? item.chi2_statistic;
      const usedMethod = item.method_used ?? methodId;
      let statLabel = 'Stat';
      if (usedMethod.includes('ttest')) statLabel = 't';
      else if (usedMethod.includes('anova')) statLabel = 'F';
      else if (usedMethod.includes('mann')) statLabel = 'U';
      else if (usedMethod.includes('kruskal')) statLabel = 'H';
      else if (usedMethod.includes('chi')) statLabel = 'χ²';
      const statValStr = rawStat !== undefined ? `${statLabel} = ${formatNum(rawStat)}` : '—';

      // df
      const dfStr = item.degrees_of_freedom !== undefined
        ? String(Math.round(item.degrees_of_freedom * 100) / 100)
        : item.degrees_of_freedom_between !== undefined
        ? `${item.degrees_of_freedom_between}, ${item.degrees_of_freedom_within}`
        : '—';

      // Effect size — support new field `effect_size` + `effect_size_label` and old per-method names
      let effStr = '—';
      if (item.effect_size !== undefined && item.effect_size_label) {
        effStr = `${item.effect_size_label.split('(')[0].trim()} = ${formatNum(item.effect_size)}`;
      } else if (item.eta_squared !== undefined) {
        effStr = `η² = ${formatNum(item.eta_squared)}`;
      } else if (item.cohens_d !== undefined) {
        effStr = `d = ${formatNum(item.cohens_d)}`;
      } else if (item.rank_biserial_r !== undefined) {
        effStr = `r = ${formatNum(item.rank_biserial_r)}`;
      } else if (item.epsilon_squared !== undefined) {
        effStr = `ε² = ${formatNum(item.epsilon_squared)}`;
      }

      // Auto-corrected flag
      const corrected = Boolean(item.auto_corrected);

      rows.push({
        variable: depName + (corrected ? ' ⚡' : ''),
        category: grpName,
        sampleSizeStr: n > 0 ? String(n) : String(sampleSize),
        summaryMetric: summaryMetricStr,
        statValue: item.status === 'error' ? `⚠ ${item.error_message?.slice(0, 40) ?? 'Error'}` : statValStr,
        dfStr,
        pValueStr: item.status === 'error' ? '—' : formatPValue(item.p_value),
        effectStr: item.status === 'error' ? '—' : effStr,
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
        variable: allUsed,
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
    const groups = main.group_statistics || main.group_means || main.groups || {};
    Object.entries(groups).forEach(([gName, gVal]: [string, any], index: number) => {
      const mean = typeof gVal === 'object' && gVal.mean !== undefined ? formatNum(gVal.mean) : (typeof gVal === 'number' ? formatNum(gVal) : '—');
      const sd = typeof gVal === 'object' && gVal ? (gVal.std !== undefined ? formatNum(gVal.std) : (gVal.sd !== undefined ? formatNum(gVal.sd) : '—')) : '—';
      const nStr = typeof gVal === 'object' && gVal.n !== undefined ? String(gVal.n) : (main.group_sizes && main.group_sizes[gName] !== undefined ? String(main.group_sizes[gName]) : `${Math.round(sampleSize / 2)}`);
      rows.push({
        variable: depVar !== 'Primary Outcome' ? depVar : allUsed,
        category: String(gName),
        sampleSizeStr: nStr,
        summaryMetric: mean !== '—' && sd !== '—' ? `${mean} ± ${sd}` : (mean !== '—' ? `Mean = ${mean}` : '—'),
        statValue: index === 0 ? `${testStat.label} = ${testStat.value}` : '—',
        dfStr: index === 0 ? testStat.df : '—',
        pValueStr: index === 0 ? pValStr : '—',
        effectStr: index === 0 ? effectStr : '—'
      });
    });
  } else if (main.group_1_name || main.group_2_name || main.group_1_stats || main.mean_1 !== undefined) {
    const g1Name = main.group_1_name || 'Group 1';
    const g2Name = main.group_2_name || 'Group 2';
    const n1 = main.n_1 || main.group_1_stats?.n || Math.round(sampleSize / 2);
    const n2 = main.n_2 || main.group_2_stats?.n || (sampleSize - n1);
    const m1 = main.mean_1 !== undefined ? formatNum(main.mean_1) : (main.group_1_stats?.mean !== undefined ? formatNum(main.group_1_stats.mean) : '—');
    const s1 = main.std_1 !== undefined ? formatNum(main.std_1) : (main.group_1_stats?.std !== undefined ? formatNum(main.group_1_stats.std) : (main.group_1_stats?.sd !== undefined ? formatNum(main.group_1_stats.sd) : '—'));
    const m2 = main.mean_2 !== undefined ? formatNum(main.mean_2) : (main.group_2_stats?.mean !== undefined ? formatNum(main.group_2_stats.mean) : '—');
    const s2 = main.std_2 !== undefined ? formatNum(main.std_2) : (main.group_2_stats?.std !== undefined ? formatNum(main.group_2_stats.std) : (main.group_2_stats?.sd !== undefined ? formatNum(main.group_2_stats.sd) : '—'));
    rows.push({
      variable: depVar !== 'Primary Outcome' ? depVar : allUsed,
      category: String(g1Name),
      sampleSizeStr: String(n1),
      summaryMetric: m1 !== '—' && s1 !== '—' ? `${m1} ± ${s1}` : (m1 !== '—' ? `Mean = ${m1}` : '—'),
      statValue: `${testStat.label} = ${testStat.value}`,
      dfStr: testStat.df,
      pValueStr: pValStr,
      effectStr: effectStr
    });
    rows.push({
      variable: depVar !== 'Primary Outcome' ? depVar : allUsed,
      category: String(g2Name),
      sampleSizeStr: String(n2),
      summaryMetric: m2 !== '—' && s2 !== '—' ? `${m2} ± ${s2}` : (m2 !== '—' ? `Mean = ${m2}` : '—'),
      statValue: '—',
      dfStr: '—',
      pValueStr: '—',
      effectStr: '—'
    });
  } else if (main.coefficients || main.model_summary || main.predictors) {
    const preds = main.coefficients || main.predictors || {};
    if (Object.keys(preds).length > 0) {
      Object.entries(preds).forEach(([predName, predVal]: [string, any], index: number) => {
        rows.push({
          variable: depVar !== 'Primary Outcome' ? depVar : allUsed,
          category: predName,
          sampleSizeStr: index === 0 ? String(sampleSize) : '—',
          summaryMetric: typeof predVal === 'object' && predVal.coef !== undefined ? `Coef: ${formatNum(predVal.coef)}` : '—',
          statValue: typeof predVal === 'object' && predVal.t !== undefined ? `t = ${formatNum(predVal.t)}` : (typeof predVal === 'object' && predVal.z !== undefined ? `Z = ${formatNum(predVal.z)}` : (index === 0 ? `${testStat.label} = ${testStat.value}` : '—')),
          dfStr: index === 0 ? testStat.df : '—',
          pValueStr: typeof predVal === 'object' && (predVal.p_value !== undefined || predVal.p !== undefined) ? formatPValue(predVal.p_value ?? predVal.p) : (index === 0 ? pValStr : '—'),
          effectStr: index === 0 ? effectStr : '—'
        });
      });
    } else {
      rows.push({
        variable: depVar !== 'Primary Outcome' ? depVar : allUsed,
        category: indepVar !== 'Grouping Factor' && indepVar !== depVar ? indepVar : 'Overall',
        sampleSizeStr: String(sampleSize),
        summaryMetric: main.mean_difference !== undefined ? `Diff: ${formatNum(main.mean_difference)}` : (main.model_fit || 'Primary Outcome'),
        statValue: `${testStat.label} = ${testStat.value}`,
        dfStr: testStat.df,
        pValueStr: pValStr,
        effectStr: effectStr
      });
    }
  } else {
    rows.push({
      variable: depVar !== 'Primary Outcome' ? depVar : allUsed,
      category: indepVar !== 'Grouping Factor' && indepVar !== depVar ? indepVar : 'Overall',
      sampleSizeStr: String(sampleSize),
      summaryMetric: main.mean_difference !== undefined ? `Diff: ${formatNum(main.mean_difference)}` : (main.model_fit || 'Primary Analysis Outcome'),
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
        <th style="padding: 6pt 8pt; text-align: left; font-weight: bold;">Category / Level</th>
        <th style="padding: 6pt 8pt; text-align: center; font-weight: bold;">n</th>
        <th style="padding: 6pt 8pt; text-align: center; font-weight: bold;">Mean ± SD / Summary</th>
        <th style="padding: 6pt 8pt; text-align: center; font-weight: bold;">Test Stat</th>
        <th style="padding: 6pt 8pt; text-align: center; font-weight: bold;">df</th>
        <th style="padding: 6pt 8pt; text-align: center; font-weight: bold;">p</th>
        <th style="padding: 6pt 8pt; text-align: left; font-weight: bold;">Effect Size (95% CI)</th>
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
    return html;
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

  return (
    <div className="glass-panel p-6 space-y-4 border-l-4 border-l-sky-500 animate-fade-in">
      <div className="flex flex-col sm:flex-row items-start sm:items-center justify-between gap-3 border-b border-white/10 pb-4">
        <div>
          <div className="flex items-center gap-2">
            <Award className="w-5 h-5 text-sky-400" />
            <h3 className="text-md font-bold text-white">Table (APA 7th / JAMA)</h3>
          </div>
        </div>

        <div className="flex items-center gap-2 flex-wrap">
          <button
            onClick={handleCopyWord}
            className="btn-primary bg-gradient-to-r from-sky-600 to-blue-600 hover:from-sky-500 hover:to-blue-500 text-xs px-3.5 py-1.5 flex items-center gap-1.5 shadow-md shadow-sky-500/20"
          >
            {copiedHtml ? <Check className="w-3.5 h-3.5 text-emerald-300" /> : <Copy className="w-3.5 h-3.5" />}
            <span>{copiedHtml ? 'Copied with Borders!' : '📋 Copy Table for Word / Excel'}</span>
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

      {/* Batch info badge */}
      {isBatch && (
        <div className="flex items-center gap-2 text-[11px] text-sky-300 bg-sky-500/10 border border-sky-400/20 rounded-lg px-3 py-2">
          <AlertTriangle className="w-3.5 h-3.5" />
          <span><strong>{main.n_comparisons ?? rows.length}</strong> comparisons executed in batch. ⚡ marks auto-corrected method per variable.</span>
        </div>
      )}

      {/* On-Screen Table Preview */}
      <div className="overflow-x-auto bg-slate-950/80 p-5 rounded-xl border border-white/10 shadow-inner">
        <table className="w-full text-left font-serif text-sm text-slate-200 border-collapse">
          <thead>
            <tr className="border-t-2 border-b border-slate-300 dark:border-slate-400 text-slate-100 dark:text-white">
              <th className="py-3 px-4 font-bold tracking-wider">Variable / Group</th>
              <th className="py-3 px-4 font-bold tracking-wider">Category / Level</th>
              <th className="py-3 px-4 font-bold text-center">n</th>
              <th className="py-3 px-4 font-bold text-center">Mean ± SD / Summary</th>
              <th className="py-3 px-4 font-bold text-center">Test Stat</th>
              <th className="py-3 px-4 font-bold text-center">df</th>
              <th className="py-3 px-4 font-bold text-center">p</th>
              <th className="py-3 px-4 font-bold text-left">Effect Size (95% CI)</th>
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
                  <td className="py-2.5 px-4 font-normal text-slate-200">{row.variable}</td>
                  <td className="py-2.5 px-4 font-normal text-slate-200">{row.category}</td>
                  <td className="py-2.5 px-4 text-center font-normal text-slate-200">{row.sampleSizeStr}</td>
                  <td className="py-2.5 px-4 text-center font-normal text-slate-200">{row.summaryMetric}</td>
                  <td className="py-2.5 px-4 text-center font-normal text-slate-200">{row.statValue}</td>
                  <td className="py-2.5 px-4 text-center font-normal text-slate-200">{row.dfStr}</td>
                  <td className="py-2.5 px-4 text-center font-normal text-emerald-300">{row.pValueStr}</td>
                  <td className="py-2.5 px-4 text-left font-normal text-sky-300">{row.effectStr}</td>
                </tr>
              );
            })}
          </tbody>
        </table>
        <div className="mt-3 text-[11px] font-serif italic text-slate-400 flex items-center justify-between">
        </div>
      </div>
    </div>
  );
};
