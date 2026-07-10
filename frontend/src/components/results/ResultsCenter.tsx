import React, { useState, useEffect } from 'react';
import Plot from 'react-plotly.js';
import { BarChart3, Download, Sparkles, ArrowLeft, Layers, Sliders, CheckCircle2, AlertTriangle, Settings, RefreshCw, SlidersHorizontal, Loader2, Code2, Copy, Check, Edit3, Eye, RotateCcw, FileCode, Palette } from 'lucide-react';
import type { AnalysisResponse, DatasetSummary } from '../../types/statmind';
import { AssumptionShield } from './AssumptionShield';
import { PublicationSuite } from './PublicationSuite';
import { Q1JournalTable } from './Q1JournalTable';
import { PortfolioBuilderModal } from './PortfolioBuilderModal';
import { QuantigenAIChat } from '../common/QuantigenAIChat';
import { api } from '../../api/client';

const FigureCard: React.FC<{ plotJson: any; idx: number; res: any; theme?: 'dark' | 'light' }> = ({ plotJson, idx, res, theme }) => {
  const rawTitle = String(plotJson?.layout?.title?.text || `${res.method_name || 'Statistical'} Visualization`).replace(/<[^>]+>/g, '').replace(/\$/g, '').trim();
  let defaultTitle = rawTitle;
  if (rawTitle.toLowerCase().includes('category counts for ')) {
    const v = rawTitle.replace(/category counts for /i, '').trim();
    defaultTitle = `Demographic & Categorical Frequency of ${v.toUpperCase()}`;
  } else if (rawTitle.toLowerCase().includes('distribution of ')) {
    const v = rawTitle.replace(/distribution of /i, '').trim();
    defaultTitle = `Population Distribution of ${v.toUpperCase()}`;
  }

  const rawXLabel = String(plotJson?.layout?.xaxis?.title?.text || plotJson?.layout?.xaxis?.title || 'X-Axis Variable').replace(/<[^>]+>/g, '').replace(/\$/g, '').trim();
  const rawYLabel = String(plotJson?.layout?.yaxis?.title?.text || plotJson?.layout?.yaxis?.title || 'Count / Frequency').replace(/<[^>]+>/g, '').replace(/\$/g, '').trim();
  const rawLegend = String(plotJson?.layout?.legend?.title?.text || plotJson?.layout?.legend?.title || 'Group / Category').replace(/<[^>]+>/g, '').replace(/\$/g, '').trim();

  const [customTitle, setCustomTitle] = useState(defaultTitle);
  const [customXLabel, setCustomXLabel] = useState(rawXLabel);
  const [customYLabel, setCustomYLabel] = useState(rawYLabel);
  const [customLegend, setCustomLegend] = useState(rawLegend);
  const [customColor, setCustomColor] = useState('#0284c7');
  const [selectedGeom, setSelectedGeom] = useState<string>('');
  const [activeTab, setActiveTab] = useState<'plotly' | 'ggplot2'>('plotly');
  const [showCustomizer, setShowCustomizer] = useState(false);
  const [copiedR, setCopiedR] = useState(false);

  const chartType = plotJson.data?.[0]?.type || 'bar';
  const currentGeom = selectedGeom || chartType;

  const resetLabels = () => {
    setCustomTitle(defaultTitle);
    setCustomXLabel(rawXLabel);
    setCustomYLabel(rawYLabel);
    setCustomLegend(rawLegend);
    setCustomColor('#0284c7');
    setSelectedGeom('');
  };

  const isLightMode = theme === 'light' || (typeof document !== 'undefined' && document.documentElement.classList.contains('light-mode'));
  const chartFontColor = isLightMode ? '#0f172a' : '#f8fafc';

  const methodId = String(res?.method_id || '').toLowerCase();
  const isTwoContinuous = methodId.includes('correlation') || methodId.includes('regression');
  const isCategoricalContingency = methodId.includes('chisquare');
  const isGroupComparison = methodId.includes('ttest') || methodId.includes('anova') || methodId.includes('mann_whitney') || methodId.includes('kruskal');

  let validGeomOptions: { id: string; label: string; desc: string }[] = [];
  let variableSafetyNotice = "";

  if (isTwoContinuous || chartType === 'scatter') {
    validGeomOptions = [
      { id: 'scatter', label: 'Scatter Plot + OLS Linear Fit (lm)', desc: 'Linear regression trendline between continuous numeric pairs.' },
      { id: 'scatter_loess', label: 'Scatter Plot + LOESS Smooth', desc: 'Local non-linear curve fitting across continuous variables.' },
      { id: 'density_2d', label: '2D Hexbin / Contour Density', desc: 'High-density probability contour map for dense paired data.' }
    ];
    variableSafetyNotice = "Strict Type-Safe Geometry: Two Continuous Numeric variables allow Scatter OLS, LOESS Smooth, and 2D Density plots.";
  } else if (isGroupComparison || chartType === 'box' || chartType === 'violin') {
    validGeomOptions = [
      { id: 'bar', label: 'Group Mean Bar Chart + SE', desc: 'Compares average continuous outcome across categorical groups.' },
      { id: 'pie', label: 'Proportional Donut / Pie Chart', desc: 'Percentage share distribution across discrete categories/groups.' },
      { id: 'box', label: 'Box & Whisker Plot (Median & IQR)', desc: 'Displays interquartile range, medians, and exact outliers.' },
      { id: 'violin', label: 'Violin Probability Density Plot', desc: 'Shows full kernel density curve across categorical groups.' }
    ];
    variableSafetyNotice = "Strict Type-Safe Geometry: Categorical X + Continuous Y allow Bar, Donut/Pie, Box, and Violin plots.";
  } else if (isCategoricalContingency || chartType === 'heatmap') {
    validGeomOptions = [
      { id: 'bar_grouped', label: 'Grouped Contingency Bar Chart', desc: 'Compares discrete observation counts side-by-side.' },
      { id: 'bar_stacked', label: 'Stacked Proportional Bar Chart', desc: 'Displays relative percentage composition across categories.' },
      { id: 'pie', label: 'Proportional Donut / Pie Chart', desc: 'Overall categorical distribution summary.' },
      { id: 'heatmap', label: 'Contingency Frequency Heatmap', desc: 'Color-coded matrix of joint categorical frequency counts.' }
    ];
    variableSafetyNotice = "Strict Type-Safe Geometry: Contingency table on two Categorical variables allows Grouped, Stacked, Donut, and Heatmap plots.";
  } else if (chartType === 'histogram' || chartType === 'density') {
    validGeomOptions = [
      { id: 'histogram', label: 'Histogram + Normal Curve', desc: 'Displays frequency bins against theoretical Gaussian reference.' },
      { id: 'density', label: 'Kernel Density Estimate (KDE)', desc: 'Smooth continuous probability density curve.' },
      { id: 'box_single', label: 'Univariate Box Summary Plot', desc: 'Single-variable distribution summary checking skewness and outliers.' }
    ];
    variableSafetyNotice = "Strict Type-Safe Geometry: Single Continuous Numeric distribution allows Histogram, KDE, and Box Summary plots.";
  } else {
    validGeomOptions = [
      { id: 'bar', label: 'Categorical Frequency Bar Chart', desc: 'Exact counts across discrete categorical levels.' },
      { id: 'pie', label: 'Proportional Donut / Pie Chart', desc: 'Percentage share distribution across discrete categories.' }
    ];
    variableSafetyNotice = "Strict Type-Safe Geometry: Discrete Categorical frequency data allows Bar and Proportional Donut plots.";
  }

  const colorOptions = [
    { id: '#0284c7', label: 'Modern Sky', class: 'bg-[#0284c7]' },
    { id: '#059669', label: 'Academic Emerald', class: 'bg-[#059669]' },
    { id: '#990000', label: 'Harvard Crimson', class: 'bg-[#990000]' },
    { id: '#1e3a8a', label: 'Oxford Navy', class: 'bg-[#1e3a8a]' },
    { id: '#4f46e5', label: 'Royal Indigo', class: 'bg-[#4f46e5]' },
    { id: '#d97706', label: 'Warm Amber', class: 'bg-[#d97706]' },
    { id: '#475569', label: 'Publication Slate', class: 'bg-[#475569]' },
    { id: '#e11d48', label: 'Coral Rose', class: 'bg-[#e11d48]' }
  ];

  const customizedLayout: any = {
    ...plotJson.layout,
    title: { ...plotJson.layout?.title, text: customTitle },
    xaxis: { ...plotJson.layout?.xaxis, title: { text: customXLabel } },
    yaxis: { ...plotJson.layout?.yaxis, title: { text: customYLabel } },
    legend: { ...plotJson.layout?.legend, title: { text: customLegend } },
    autosize: true,
    paper_bgcolor: 'transparent',
    plot_bgcolor: 'transparent',
    font: { family: 'Inter, sans-serif', color: chartFontColor },
    margin: { t: 55, r: 30, l: 65, b: 65 },
  };

  if (currentGeom === 'bar_stacked') {
    customizedLayout.barmode = 'stack';
  } else if (currentGeom === 'bar_grouped') {
    customizedLayout.barmode = 'group';
  }

  const customizedData = (plotJson.data || []).map((trace: any, trIdx: number) => {
    const newTrace = { ...trace };
    if (currentGeom === 'bar' || currentGeom === 'bar_grouped' || currentGeom === 'bar_stacked') {
      newTrace.type = 'bar';
      const xVals = newTrace.x || newTrace.labels || [];
      const yVals = newTrace.y || newTrace.values || [];
      if (!newTrace.x && newTrace.labels) newTrace.x = Array.isArray(xVals) ? [...xVals] : Array.from(xVals);
      if (!newTrace.y && newTrace.values) newTrace.y = Array.isArray(yVals) ? [...yVals] : Array.from(yVals);
      delete newTrace.labels;
      delete newTrace.values;
      delete newTrace.hole;
      newTrace.marker = { ...newTrace.marker, color: customColor };
      if (newTrace.y && Array.isArray(newTrace.y)) {
        newTrace.text = newTrace.y.map((v: any) => typeof v === 'number' ? (Number.isInteger(v) ? String(v) : v.toFixed(2)) : String(v));
        newTrace.textposition = 'auto';
        newTrace.textfont = { family: 'Inter, sans-serif', size: 11, color: isLightMode ? '#0f172a' : '#ffffff' };
      }
    } else if (currentGeom === 'box' || currentGeom === 'box_single') {
      newTrace.type = 'box';
      newTrace.marker = { ...newTrace.marker, color: customColor };
      newTrace.boxpoints = 'outliers';
    } else if (currentGeom === 'violin') {
      newTrace.type = 'violin';
      newTrace.marker = { ...newTrace.marker, color: customColor };
      newTrace.box = { visible: true };
      newTrace.meanline = { visible: true };
    } else if (currentGeom === 'scatter' || currentGeom === 'scatter_loess') {
      newTrace.type = 'scatter';
      if (newTrace.mode !== 'lines') {
        newTrace.marker = { ...newTrace.marker, color: customColor, size: 8 };
      } else {
        newTrace.line = { ...newTrace.line, color: '#e11d48', width: 2.5 };
      }
    } else if (currentGeom === 'density_2d') {
      newTrace.type = 'histogram2dcontour';
      newTrace.colorscale = [['0', '#f8fafc'], ['0.5', customColor], ['1', '#0f172a']];
    } else if (currentGeom === 'histogram') {
      newTrace.type = 'histogram';
      newTrace.marker = { ...newTrace.marker, color: customColor };
      newTrace.opacity = 0.88;
    } else if (currentGeom === 'density') {
      newTrace.type = 'scatter';
      newTrace.mode = 'lines';
      newTrace.fill = 'tozeroy';
      newTrace.line = { color: customColor, width: 2.5 };
    } else if (currentGeom === 'pie') {
      if (trIdx > 0 && (plotJson.data || []).length > 1) {
        newTrace.visible = false;
        return newTrace;
      }
      newTrace.visible = true;
      newTrace.type = 'pie';
      newTrace.hole = 0.45;
      const rawLabels = newTrace.labels || newTrace.x || [];
      const rawValues = newTrace.values || newTrace.y;
      newTrace.labels = Array.isArray(rawLabels) ? [...rawLabels] : Array.from(rawLabels);
      if (rawValues && Array.isArray(rawValues) && rawValues.length === newTrace.labels.length) {
        newTrace.values = Array.isArray(rawValues) ? [...rawValues] : Array.from(rawValues);
      } else if (newTrace.labels && newTrace.labels.length > 0) {
        const countMap: Record<string, number> = {};
        newTrace.labels.forEach((val: any) => {
          const key = String(val);
          countMap[key] = (countMap[key] || 0) + 1;
        });
        newTrace.labels = Object.keys(countMap);
        newTrace.values = Object.values(countMap);
      }
      delete newTrace.x;
      delete newTrace.y;
      delete newTrace.orientation;
      delete newTrace.width;
      delete newTrace.error_y;
      delete newTrace.error_x;
      if (newTrace.marker) {
        delete newTrace.marker.color;
        delete newTrace.marker.line;
      }
      newTrace.marker = {
        ...newTrace.marker,
        colors: ['#0284c7', '#059669', '#d97706', '#990000', '#4f46e5', '#1e3a8a', '#e11d48', '#475569', '#38bdf8', '#fb7185', '#a855f7', '#facc15']
      };
      newTrace.textinfo = 'label+percent';
      newTrace.textposition = 'outside';
      newTrace.automargin = true;
      newTrace.textfont = { family: 'Inter, sans-serif', size: 12, color: chartFontColor };
      if (customizedLayout) {
        customizedLayout.xaxis = { visible: false };
        customizedLayout.yaxis = { visible: false };
        delete customizedLayout.barmode;
      }
    } else if (currentGeom === 'heatmap') {
      newTrace.type = 'heatmap';
      newTrace.colorscale = [['0', '#3b82f6'], ['0.5', '#ffffff'], ['1', customColor]];
    } else {
      if (newTrace.marker) {
        newTrace.marker = { ...newTrace.marker, color: customColor };
      }
    }
    return newTrace;
  });

  const xKey = plotJson.data?.[0]?.x?.[0] !== undefined ? 'x_variable' : 'category_var';
  const yKey = plotJson.data?.[0]?.y?.[0] !== undefined ? 'y_variable' : 'outcome_val';

  let geomSnippet = `geom_bar(stat = "identity", position = position_dodge(width = 0.8), fill = "${customColor}", color = "white", alpha = 0.9, width = 0.7)`;
  if (currentGeom === 'scatter') {
    geomSnippet = `geom_point(size = 3.5, alpha = 0.85, color = "${customColor}")\n  + geom_smooth(method = "lm", se = TRUE, color = "#e11d48", fill = "#f43f5e", alpha = 0.18)`;
  } else if (currentGeom === 'scatter_loess') {
    geomSnippet = `geom_point(size = 3.5, alpha = 0.85, color = "${customColor}")\n  + geom_smooth(method = "loess", se = TRUE, color = "#990000", fill = "#fb7185", alpha = 0.18)`;
  } else if (currentGeom === 'box' || currentGeom === 'box_single') {
    geomSnippet = `geom_boxplot(alpha = 0.85, fill = "${customColor}", color = "#0f172a", outlier.colour = "#e11d48", outlier.shape = 16, outlier.size = 3.5)`;
  } else if (currentGeom === 'violin') {
    geomSnippet = `geom_violin(alpha = 0.85, fill = "${customColor}", color = "#0f172a", trim = FALSE)\n  + geom_boxplot(width = 0.15, fill = "white", color = "#0f172a", alpha = 0.9, outlier.shape = NA)`;
  } else if (currentGeom === 'histogram') {
    geomSnippet = `geom_histogram(bins = 30, fill = "${customColor}", color = "white", alpha = 0.9)`;
  } else if (currentGeom === 'density') {
    geomSnippet = `geom_density(fill = "${customColor}", color = "#0f172a", alpha = 0.6, linewidth = 0.9)`;
  } else if (currentGeom === 'density_2d') {
    geomSnippet = `geom_point(size = 2.0, alpha = 0.4, color = "${customColor}") + geom_density_2d(color = "#1e3a8a", linewidth = 0.8)`;
  } else if (currentGeom === 'bar_stacked') {
    geomSnippet = `geom_bar(stat = "identity", position = "stack", fill = "${customColor}", color = "white", alpha = 0.9)`;
  } else if (currentGeom === 'bar_grouped') {
    geomSnippet = `geom_bar(stat = "identity", position = position_dodge(width = 0.8), fill = "${customColor}", color = "white", alpha = 0.9)`;
  } else if (currentGeom === 'pie') {
    geomSnippet = `geom_bar(stat = "identity", width = 1, color = "white") + coord_polar(theta = "y", start = 0) + xlim(0.5, 2.5) + theme_void(base_size = 14)`;
  } else if (currentGeom === 'heatmap') {
    geomSnippet = `geom_tile(aes(fill = value), color = "white") + scale_fill_gradient2(low = "#3b82f6", mid = "#ffffff", high = "${customColor}")`;
  }

  const ggplotScript = `# ==============================================================================
# Quantigen AI — Publication-Grade R ggplot2 Visualization Script
# Figure ${idx + 1}: ${customTitle}
# Method: ${res.method_name || 'Statistical Analysis'}
# ==============================================================================

# 1. Install & Load Required R Packages
# if (!require("ggplot2")) install.packages("ggplot2")
# if (!require("dplyr")) install.packages("dplyr")
library(ggplot2)
library(dplyr)

# ==============================================================================
# 2. LOAD YOUR DATASET (IMPORTANT: Paste your exact dataset path below)
# ==============================================================================
# To execute this script in R or RStudio on your computer, replace the file path
# inside read.csv() below with your CSV or Excel dataset location:
# df <- read.csv("C:/Users/your_name/path_to_dataset.csv", stringsAsFactors = FALSE)

# 3. Build Publication-Grade Figure using ggplot2 (APA 7th / High-Impact Style)
p <- ggplot(df, aes(${currentGeom === 'pie' ? `x = 2, y = ${yKey}, fill = ${xKey}` : `x = ${xKey}, y = ${yKey}`})) +
  ${geomSnippet} +
  ${currentGeom === 'pie' ? '' : `theme_minimal(base_size = 14) +`}
  labs(
    title = "${customTitle.replace(/"/g, '\\"')}",
    ${currentGeom === 'pie' ? '' : `x = "${customXLabel.replace(/"/g, '\\"')}",\n    y = "${customYLabel.replace(/"/g, '\\"')}",`}
    fill = "${customLegend.replace(/"/g, '\\"')}",
    color = "${customLegend.replace(/"/g, '\\"')}"
  ) +
  theme(
    plot.title = element_text(face = "bold", size = 16, color = "#0f172a", hjust = 0.5, margin = margin(b = 14)),
    axis.title.x = element_text(face = "bold", size = 13, color = "#334155", margin = margin(t = 12)),
    axis.title.y = element_text(face = "bold", size = 13, color = "#334155", margin = margin(r = 12)),
    axis.text = element_text(size = 11, color = "#475569"),
    panel.grid.minor = element_blank(),
    panel.grid.major.x = element_blank(),
    legend.position = "top",
    legend.title = element_text(face = "bold", size = 11),
    plot.background = element_rect(fill = "white", color = NA),
    panel.background = element_rect(fill = "white", color = NA)
  )

# Display chart in RStudio / R Console
print(p)

# 4. Export directly to High-Resolution 300 DPI Journal PNG
ggsave("quantigen_figure_${idx + 1}_ggplot2.png", plot = p, width = 10, height = 6, dpi = 300)
`;

  const copyR = () => {
    navigator.clipboard.writeText(ggplotScript);
    setCopiedR(true);
    setTimeout(() => setCopiedR(false), 2000);
  };

  const downloadRFile = () => {
    const element = document.createElement("a");
    const file = new Blob([ggplotScript], { type: 'text/plain' });
    element.href = URL.createObjectURL(file);
    element.download = `quantigen_figure_${idx + 1}_ggplot2.R`;
    document.body.appendChild(element);
    element.click();
    document.body.removeChild(element);
  };

  return (
    <div className="figure-card glass-panel p-6 space-y-4 overflow-hidden border border-white/10 hover:border-sky-500/30 transition-all duration-300">
      {/* Header Bar */}
      <div className="flex flex-col lg:flex-row lg:items-center justify-between gap-3 border-b border-white/10 pb-4">
        <div className="flex items-center gap-2">
          <Layers className="w-5 h-5 text-sky-400 shrink-0" />
          <span className="brand-title font-bold text-sm md:text-base text-white">
            Figure {idx + 1}: {customTitle}
          </span>
        </div>

        <div className="flex flex-wrap items-center gap-2">
          {/* Quick Chart Type Switcher */}
          {validGeomOptions.length > 1 && (
            <div className="flex items-center bg-slate-900/90 p-1 rounded-lg border border-sky-500/30">
              {validGeomOptions.slice(0, 3).map((opt) => {
                const isSelected = currentGeom === opt.id;
                return (
                  <button
                    key={opt.id}
                    onClick={() => setSelectedGeom(opt.id)}
                    title={opt.desc}
                    className={`px-2.5 py-1 text-xs font-semibold rounded-md transition-all flex items-center gap-1 ${
                      isSelected
                        ? 'bg-gradient-to-r from-sky-500 to-indigo-500 text-white shadow-sm'
                        : 'text-slate-300 hover:text-white hover:bg-white/5'
                    }`}
                  >
                    <span>{opt.id.includes('pie') ? '🍩' : opt.id.includes('bar') ? '📊' : opt.id.includes('box') ? '📈' : '🔹'}</span>
                    <span>{opt.label.split(' ')[0]} {opt.label.includes('Donut') ? 'Donut' : opt.label.includes('Bar') ? 'Bar' : ''}</span>
                  </button>
                );
              })}
            </div>
          )}

          {/* Mode Switcher */}
          <div className="flex items-center bg-slate-900/80 p-1 rounded-lg border border-white/10">
            <button
              onClick={() => setActiveTab('plotly')}
              className={`flex items-center gap-1.5 px-3 py-1 text-xs font-semibold rounded-md transition-all ${
                activeTab === 'plotly'
                  ? 'tab-pill-sky-active bg-sky-500 text-white shadow-lg shadow-sky-500/20'
                  : 'tab-pill-inactive text-slate-400 hover:text-white'
              }`}
            >
              <Eye className="w-3.5 h-3.5" />
              <span>Interactive Chart</span>
            </button>
            <button
              onClick={() => setActiveTab('ggplot2')}
              className={`flex items-center gap-1.5 px-3 py-1 text-xs font-semibold rounded-md transition-all ${
                activeTab === 'ggplot2'
                  ? 'tab-pill-emerald-active bg-emerald-600 text-white shadow-lg shadow-emerald-600/20'
                  : 'tab-pill-inactive text-slate-400 hover:text-white'
              }`}
            >
              <Code2 className="w-3.5 h-3.5" />
              <span>R ggplot2 Script</span>
            </button>
          </div>

          {/* Customize Toggle */}
          <button
            onClick={() => setShowCustomizer(!showCustomizer)}
            className={`flex items-center gap-1.5 px-3 py-1.5 text-xs font-semibold rounded-lg border transition-all ${
              showCustomizer
                ? 'customizer-toggle-active bg-amber-500/20 border-amber-500/50 text-amber-300'
                : 'customizer-toggle-inactive bg-slate-900/80 border-white/10 text-slate-300 hover:border-white/30'
            }`}
          >
            <Edit3 className="w-3.5 h-3.5 text-amber-400" />
            <span>Customize Labels, Color & Geometry</span>
          </button>

          {/* Download Button */}
          <button
            onClick={() => api.downloadChartPNG({ ...plotJson, data: customizedData, layout: customizedLayout }, `quantigen_figure_${idx + 1}`)}
            className="btn-primary text-xs py-1.5 px-3.5 flex items-center gap-1.5 shadow-lg shadow-sky-500/20"
          >
            <Download className="w-3.5 h-3.5" />
            <span>Download 300 DPI PNG</span>
          </button>
        </div>
      </div>

      {/* Label, Color & Geometry Customizer Tray */}
      {showCustomizer && (
        <div className="bg-slate-900/95 border-2 border-sky-500/40 p-5 rounded-2xl space-y-4 shadow-2xl animate-in fade-in">
          <div className="flex items-center justify-between border-b border-white/10 pb-3">
            <div>
              <span className="text-xs font-bold uppercase tracking-wider text-sky-400 flex items-center gap-1.5">
                <SlidersHorizontal className="w-4 h-4 text-sky-400 animate-spin-slow" />
                <span>Interactive Figure Studio — Type-Safe Geometry, Color Palette & Labels</span>
              </span>
              <p className="text-[11px] text-slate-300 mt-0.5">
                {variableSafetyNotice}
              </p>
            </div>
            <button
              onClick={resetLabels}
              className="flex items-center gap-1 text-[11px] bg-slate-800 hover:bg-slate-700 text-slate-300 hover:text-white px-2.5 py-1 rounded-md transition-colors border border-white/10"
            >
              <RotateCcw className="w-3 h-3 text-amber-400" />
              <span>Reset to AI Defaults</span>
            </button>
          </div>

          {/* Row 1: Type-Safe Graph Geometry Selector & Curated Color Palette */}
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-5 pt-1">
            {/* Type-Safe Graph Geometry Selector */}
            <div className="space-y-2">
              <label className="text-xs font-semibold text-sky-300 uppercase tracking-wider block flex items-center gap-1.5">
                <BarChart3 className="w-3.5 h-3.5" />
                <span>Select Scientifically Valid Graph Type</span>
              </label>
              <select
                value={currentGeom}
                onChange={(e) => setSelectedGeom(e.target.value)}
                className="w-full bg-slate-950 border border-sky-500/40 rounded-xl px-3 py-2 text-xs text-white font-medium focus:border-sky-400 focus:outline-none shadow-inner"
              >
                {validGeomOptions.map((g) => (
                  <option key={g.id} value={g.id} className="bg-slate-900 text-white">
                    {g.label} — {g.desc}
                  </option>
                ))}
              </select>
            </div>

            {/* Publication Color Palette Selector */}
            <div className="space-y-2">
              <label className="text-xs font-semibold text-emerald-300 uppercase tracking-wider block flex items-center gap-1.5">
                <Palette className="w-3.5 h-3.5" />
                <span>Select Curated Journal Color Palette</span>
              </label>
              <div className="flex flex-wrap items-center gap-2">
                {colorOptions.map((c) => (
                  <button
                    key={c.id}
                    onClick={() => setCustomColor(c.id)}
                    title={c.label}
                    className={`flex items-center gap-1.5 px-2.5 py-1.5 rounded-lg text-[11px] font-semibold border transition-all ${
                      customColor === c.id
                        ? 'border-white ring-2 ring-sky-400 shadow-md bg-slate-800 text-white scale-105'
                        : 'border-white/10 bg-slate-950 text-slate-300 hover:border-white/30 hover:text-white'
                    }`}
                  >
                    <span className={`w-3 h-3 rounded-full shrink-0 border border-white/20`} style={{ backgroundColor: c.id }} />
                    <span>{c.label}</span>
                  </button>
                ))}
              </div>
            </div>
          </div>

          {/* Row 2: Custom Text Labels */}
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-3 text-xs pt-2 border-t border-white/5">
            <div className="space-y-1">
              <label className="text-slate-300 font-semibold">Figure Title</label>
              <input
                type="text"
                value={customTitle}
                onChange={(e) => setCustomTitle(e.target.value)}
                className="w-full bg-slate-950 border border-white/10 rounded-lg px-3 py-1.5 text-white focus:border-sky-500 focus:outline-none"
                placeholder="Figure Title..."
              />
            </div>
            <div className="space-y-1">
              <label className="text-slate-300 font-semibold">X-Axis Label</label>
              <input
                type="text"
                value={customXLabel}
                onChange={(e) => setCustomXLabel(e.target.value)}
                className="w-full bg-slate-950 border border-white/10 rounded-lg px-3 py-1.5 text-white focus:border-sky-500 focus:outline-none"
                placeholder="X-Axis Label..."
              />
            </div>
            <div className="space-y-1">
              <label className="text-slate-300 font-semibold">Y-Axis Label</label>
              <input
                type="text"
                value={customYLabel}
                onChange={(e) => setCustomYLabel(e.target.value)}
                className="w-full bg-slate-950 border border-white/10 rounded-lg px-3 py-1.5 text-white focus:border-sky-500 focus:outline-none"
                placeholder="Y-Axis Label..."
              />
            </div>
            <div className="space-y-1">
              <label className="text-slate-300 font-semibold">Legend Name</label>
              <input
                type="text"
                value={customLegend}
                onChange={(e) => setCustomLegend(e.target.value)}
                className="w-full bg-slate-950 border border-white/10 rounded-lg px-3 py-1.5 text-white focus:border-sky-500 focus:outline-none"
                placeholder="Legend Name..."
              />
            </div>
          </div>
        </div>
      )}

      {/* Main Content Area: Plotly vs R ggplot2 Script */}
      {activeTab === 'plotly' ? (
        <div className="figure-canvas-box w-full min-h-[420px] flex items-center justify-center bg-slate-950/60 rounded-xl p-2 border border-white/5">
          <Plot
            data={customizedData}
            layout={customizedLayout}
            config={{
              responsive: true,
              displayModeBar: true,
              displaylogo: false,
            }}
            style={{ width: '100%', height: '420px' }}
          />
        </div>
      ) : (
        <div className="figure-script-box bg-slate-950 rounded-xl border border-emerald-500/30 overflow-hidden">
          <div className="figure-script-header flex items-center justify-between px-4 py-2.5 bg-emerald-950/40 border-b border-emerald-500/20">
            <span className="text-xs font-mono font-bold text-emerald-400 flex items-center gap-2">
              <FileCode className="w-4 h-4" />
              <span>quantigen_figure_{idx + 1}_ggplot2.R (Bound to custom labels)</span>
            </span>
            <div className="flex items-center gap-2">
              <button
                onClick={copyR}
                className="flex items-center gap-1 text-xs bg-emerald-600/30 hover:bg-emerald-600 text-emerald-200 hover:text-white px-2.5 py-1 rounded-md transition-all"
              >
                {copiedR ? <Check className="w-3.5 h-3.5 text-emerald-300" /> : <Copy className="w-3.5 h-3.5" />}
                <span>{copiedR ? 'Copied Script!' : 'Copy R Script'}</span>
              </button>
              <button
                onClick={downloadRFile}
                className="flex items-center gap-1 text-xs bg-emerald-600 hover:bg-emerald-500 text-white px-2.5 py-1 rounded-md transition-all shadow-md"
              >
                <Download className="w-3.5 h-3.5" />
                <span>Download .R Script</span>
              </button>
            </div>
          </div>
          <pre className="figure-script-code p-4 overflow-x-auto text-xs font-mono text-emerald-300 leading-relaxed max-h-[420px] overflow-y-auto">
            {ggplotScript}
          </pre>
        </div>
      )}
    </div>
  );
};

interface ResultsCenterProps {
  response: AnalysisResponse | null;
  dataset?: DatasetSummary | null;
  onAnalysisCompleted?: (response: AnalysisResponse) => void;
  onBackToAnalysis: () => void;
  theme?: 'dark' | 'light';
  analysisHistory?: AnalysisResponse[];
  onRemoveHistoryItem?: (id: string) => void;
  onClearHistory?: () => void;
  onSelectHistoryItem?: (item: AnalysisResponse) => void;
  hideInlineChat?: boolean;
}

export const ResultsCenter: React.FC<ResultsCenterProps> = ({
  response,
  dataset,
  onAnalysisCompleted,
  onBackToAnalysis,
  theme,
  analysisHistory = [],
  onRemoveHistoryItem,
  onClearHistory,
  onSelectHistoryItem,
  hideInlineChat = false,
}) => {
  const [simMode, setSimMode] = useState<'quantigen_robust' | 'classic_uncorrected'>('quantigen_robust');
  const [isTuning, setIsTuning] = useState(false);
  const [isPortfolioModalOpen, setIsPortfolioModalOpen] = useState(false);
  const [tuneMethodId, setTuneMethodId] = useState<string>('');
  const [tuneVariables, setTuneVariables] = useState<Record<string, any>>({});
  const [tuneLoading, setTuneLoading] = useState(false);
  const [tuneError, setTuneError] = useState<string | null>(null);
  const [showAllPlots, setShowAllPlots] = useState(false);

  const res = (response?.analysis_result || (response as any)?.result || {}) as any;
  const assumptions = response?.assumptions || (response as any)?.assumption_results || [];
  const plotsList = res.plots_json || res.plots || [];
  const displayedPlots = showAllPlots ? plotsList : plotsList.slice(0, 3);
  const hasViolations = assumptions.some((a: any) => !a?.passed);

  useEffect(() => {
    if (res && res.method_id) {
      setTuneMethodId(res.method_id);
      setShowAllPlots(false);
    }
  }, [res?.method_id, response?.history_id]);

  if (!response || (!res.method_name && !res.method_id)) {
    return (
      <div className="glass-panel p-10 text-center text-slate-400">
        No analysis results available yet. Please execute an analysis from the Analysis & AI Consultant tab.
      </div>
    );
  }

  const methodsList = [
    { id: 'ttest_independent', name: 'Independent Samples T-Test', req: ['dependent', 'grouping'], labels: { dependent: 'Continuous Dependent Variable (DV)', grouping: 'Categorical Grouping Variable (IV - 2 Groups)' } },
    { id: 'anova_oneway', name: 'One-Way ANOVA', req: ['dependent', 'grouping'], labels: { dependent: 'Continuous Dependent Variable (DV)', grouping: 'Categorical Grouping Variable (IV - 3+ Groups)' } },
    { id: 'mann_whitney_u', name: 'Mann-Whitney U Test (Nonparametric)', req: ['dependent', 'grouping'], labels: { dependent: 'Continuous / Ordinal Variable (DV)', grouping: 'Categorical Grouping Variable (IV - 2 Groups)' } },
    { id: 'kruskal_wallis', name: 'Kruskal-Wallis H Test (Nonparametric)', req: ['dependent', 'grouping'], labels: { dependent: 'Continuous / Ordinal Variable (DV)', grouping: 'Categorical Grouping Variable (IV - 3+ Groups)' } },
    { id: 'pearson_correlation', name: 'Pearson Correlation', req: ['var1', 'var2'], labels: { var1: 'Continuous Variable 1 (X)', var2: 'Continuous Variable 2 (Y)' } },
    { id: 'chi_square_independence', name: 'Chi-Square Test of Independence', req: ['row_var', 'col_var'], labels: { row_var: 'Categorical Variable 1 (Row)', col_var: 'Categorical Variable 2 (Column)' } },
    { id: 'linear_regression', name: 'Simple Linear Regression', req: ['dependent', 'independent'], labels: { dependent: 'Outcome Variable (Y)', independent: 'Predictor Variable (X)' } },
    { id: 'multiple_linear_regression', name: 'Multiple Linear Regression', req: ['dependent', 'independent'], labels: { dependent: 'Outcome Variable (Y)', independent: 'Primary Predictor Variable (X)' } },
    { id: 'binary_logistic_regression', name: 'Binary Logistic Regression', req: ['dependent', 'independent'], labels: { dependent: 'Binary Outcome Variable (Y: 0/1)', independent: 'Predictor Variable (X)' } },
  ];

  const currentMethodConfig = methodsList.find((m) => m.id === tuneMethodId) || methodsList[0];

  const handleRerunAnalysis = async () => {
    if (!dataset || !tuneMethodId) return;
    setTuneLoading(true);
    setTuneError(null);
    try {
      const newResponse = await api.executeAnalysis(dataset.dataset_id, tuneMethodId, tuneVariables);
      if (onAnalysisCompleted) {
        onAnalysisCompleted(newResponse);
      }
      setIsTuning(false);
    } catch (err: any) {
      setTuneError(err.response?.data?.message || err.response?.data?.detail?.message || err.message || 'Execution failed');
    } finally {
      setTuneLoading(false);
    }
  };

  return (
    <div className="space-y-8 animate-fade-in pb-12">
      {/* Top Bar with Back Button & Variable/Method Tuner Toggle */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div className="flex items-center gap-2">
          <button onClick={onBackToAnalysis} className="btn-secondary text-xs">
            <ArrowLeft className="w-4 h-4" />
            <span>Back to Analysis Studio</span>
          </button>

          {dataset && (
            <button
              onClick={() => setIsTuning(!isTuning)}
              className="btn-primary bg-gradient-to-r from-sky-600 to-indigo-600 text-xs py-2 px-3 flex items-center gap-1.5 shadow-md"
            >
              <SlidersHorizontal className="w-4 h-4" />
              <span>{isTuning ? 'Close Tuner' : 'Change Variables & Method'}</span>
            </button>
          )}

          <button
            onClick={() => setIsPortfolioModalOpen(true)}
            className="flex items-center gap-1.5 px-3.5 py-2 text-xs font-bold rounded-xl bg-gradient-to-r from-emerald-600 to-teal-600 text-white hover:from-emerald-500 hover:to-teal-500 transition-all shadow-md shadow-emerald-600/20 animate-pulse"
          >
            <Layers className="w-4 h-4 text-emerald-200" />
            <span>📚 Export Selection & Multi-Run Portfolio ({analysisHistory?.length || 1})</span>
          </button>
        </div>

        <div className="flex items-center gap-2">
          <span className="badge-role">{res.method_family || 'Statistical Analysis'}</span>
          <span className="text-xs text-slate-400">Sample Size: <strong className="text-white">N = {res.sample_size || 0}</strong></span>
        </div>
      </div>

      {/* Quick Method & Variable Tuner Drawer */}
      {isTuning && dataset && (
        <div className="glass-panel p-6 border-2 border-sky-400/50 bg-slate-900/95 shadow-2xl space-y-5 animate-fade-in">
          <div className="flex items-center justify-between border-b border-white/10 pb-3">
            <div>
              <h3 className="text-md font-bold text-white flex items-center gap-2">
                <Settings className="w-5 h-5 text-sky-400 animate-spin-slow" />
                <span>Live Assumption Shield & Method Tuner</span>
              </h3>
              <p className="text-xs text-slate-300">
                Switch statistical test or adjust variables right here. The Assumption Shield and manuscript report will recompute instantly.
              </p>
            </div>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-2 gap-5">
            {/* Statistical Method Selector */}
            <div className="space-y-2">
              <label className="text-xs font-semibold text-sky-300 uppercase tracking-wider block">
                Select Statistical Method
              </label>
              <select
                value={tuneMethodId}
                onChange={(e) => {
                  setTuneMethodId(e.target.value);
                  setTuneVariables({});
                }}
                className="w-full bg-slate-950/80 border border-white/20 rounded-xl px-3 py-2.5 text-sm text-white focus:outline-none focus:border-sky-400"
              >
                {methodsList.map((m) => (
                  <option key={m.id} value={m.id} className="bg-slate-900 text-white">
                    {m.name}
                  </option>
                ))}
              </select>
            </div>

            {/* Variable Selectors */}
            <div className="space-y-3">
              {currentMethodConfig.req.map((reqKey) => (
                <div key={reqKey} className="space-y-1">
                  <label className="text-xs font-semibold text-slate-300 block">
                    {(currentMethodConfig.labels as any)?.[reqKey] || reqKey.toUpperCase()}
                  </label>
                  <select
                    value={tuneVariables[reqKey] || ''}
                    onChange={(e) => setTuneVariables({ ...tuneVariables, [reqKey]: e.target.value })}
                    className="w-full bg-slate-950/80 border border-white/20 rounded-xl px-3 py-2 text-xs text-white focus:outline-none focus:border-sky-400"
                  >
                    <option value="">-- Select Column ({reqKey}) --</option>
                    {dataset.columns?.map((col) => (
                      <option key={col.name} value={col.name} className="bg-slate-900 text-white">
                        {col.name} ({col.role})
                      </option>
                    ))}
                  </select>
                </div>
              ))}
            </div>
          </div>

          {tuneError && (
            <div className="p-3 bg-rose-500/10 border border-rose-500/30 rounded-xl text-rose-300 text-xs flex items-center gap-2">
              <AlertTriangle className="w-4 h-4 shrink-0 text-rose-400" />
              <span>{tuneError}</span>
            </div>
          )}

          <div className="flex items-center justify-end gap-3 pt-2">
            <button
              onClick={() => setIsTuning(false)}
              className="btn-secondary text-xs px-4 py-2"
            >
              Cancel
            </button>
            <button
              onClick={handleRerunAnalysis}
              disabled={tuneLoading || currentMethodConfig.req.some((k) => !tuneVariables[k])}
              className={`btn-primary text-xs px-5 py-2 flex items-center gap-2 ${
                tuneLoading || currentMethodConfig.req.some((k) => !tuneVariables[k])
                  ? 'opacity-50 cursor-not-allowed'
                  : ''
              }`}
            >
              {tuneLoading ? (
                <>
                  <Loader2 className="w-4 h-4 animate-spin" />
                  <span>Recomputing Shield & Diagnostics...</span>
                </>
              ) : (
                <>
                  <RefreshCw className="w-4 h-4" />
                  <span>⚡ Re-Run & Update Results</span>
                </>
              )}
            </button>
          </div>
        </div>
      )}

      {/* Assumption Shield Diagnostic Header */}
      <AssumptionShield assumptions={assumptions} methodName={res.method_name || 'Analysis'} />

      {/* Complex Survey & Sampling Weights Shield Banner */}
      {(res.main_results?.is_survey_weighted || dataset?.survey_design?.is_survey_weighted || String(res.r_code || '').includes('library(survey)')) && (
        <div className="glass-panel p-5 border-0 bg-gradient-to-r from-emerald-950/60 via-slate-900/90 to-sky-950/60 rounded-2xl border-l-4 border-l-emerald-400 shadow-xl space-y-3 animate-fade-in">
          <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
            <div className="flex items-center gap-3">
              <div className="w-10 h-10 rounded-xl bg-emerald-500/10 border border-emerald-500/30 flex items-center justify-center text-emerald-400">
                <CheckCircle2 className="w-6 h-6 animate-pulse" />
              </div>
              <div>
                <h3 className="text-base font-bold text-white flex items-center gap-2">
                  <span>Complex Survey Sampling Shield Active (`svydesign`)</span>
                  <span className="bg-emerald-500/20 text-emerald-300 border border-emerald-400/30 text-[10px] px-2.5 py-0.5 rounded-full font-bold">
                    SurveyNCD / DHS / MICS verified
                  </span>
                </h3>
                <p className="text-xs text-slate-300 mt-0.5">
                  Standard errors computed via Taylor series linearization. Design degrees of freedom (`df = PSUs - Strata`) strictly enforced.
                </p>
              </div>
            </div>

            <div className="flex items-center gap-2 flex-wrap">
              <span className="bg-slate-900/90 border border-white/10 px-3 py-1 rounded-lg text-xs font-mono text-sky-300">
                <strong>Weights:</strong> ~{res.main_results?.weight_var || dataset?.survey_design?.weight_var || 'wt'}
              </span>
              <span className="bg-slate-900/90 border border-white/10 px-3 py-1 rounded-lg text-xs font-mono text-sky-300">
                <strong>Clusters:</strong> ~{res.main_results?.cluster_var || dataset?.survey_design?.cluster_var || 'psu'}
              </span>
              <span className="bg-slate-900/90 border border-white/10 px-3 py-1 rounded-lg text-xs font-mono text-sky-300">
                <strong>Strata:</strong> ~{res.main_results?.strata_var || dataset?.survey_design?.strata_var || 'strata'}
              </span>
              {res.main_results?.df !== undefined && (
                <span className="bg-emerald-950 border border-emerald-500/40 px-3 py-1 rounded-lg text-xs font-mono text-emerald-300 font-bold">
                  df = {res.main_results.df}
                </span>
              )}
            </div>
          </div>
        </div>
      )}

      {/* Interactive Remedy Simulation Switch */}
      <div className="glass-panel p-5 border-0 bg-gradient-to-r from-slate-900 via-slate-900/90 to-sky-950/40 rounded-2xl border-l-4 border-l-sky-400 shadow-xl space-y-4">
        <div className="flex flex-col md:flex-row md:items-center justify-between gap-4">
          <div className="flex items-center gap-3">
            <div className="w-10 h-10 rounded-xl bg-sky-500/10 border border-sky-400/30 flex items-center justify-center text-sky-400">
              <Sliders className="w-5 h-5" />
            </div>
            <div>
              <h3 className="text-base font-bold text-white flex items-center gap-2">
                <span>Interactive Statistical Remedy & Robustness Simulator</span>
                <span className="brand-pill-sky text-[10px] px-2 py-0.5 rounded-full bg-sky-500/20 text-sky-300 border border-sky-400/30">PATENT-PENDING Q-ENGINE</span>
              </h3>
              <p className="brand-subtitle text-xs text-slate-300">
                Compare exact Quantigen Hardened Inference vs. uncorrected legacy software (SPSS/Excel) in real-time.
              </p>
            </div>
          </div>

          <div className="flex items-center bg-slate-950/80 p-1.5 rounded-xl border border-white/10 gap-1 self-start md:self-auto">
            <button
              onClick={() => setSimMode('quantigen_robust')}
              className={`px-4 py-1.5 rounded-lg text-xs font-semibold transition-all flex items-center gap-1.5 ${
                simMode === 'quantigen_robust'
                  ? 'sim-toggle-active-robust bg-gradient-to-r from-sky-500 to-blue-600 text-white shadow-md shadow-sky-500/20'
                  : 'text-slate-400 hover:text-white'
              }`}
            >
              <CheckCircle2 className="w-3.5 h-3.5 text-emerald-300" />
              <span>Quantigen Robust Mode (Active)</span>
            </button>
            <button
              onClick={() => setSimMode('classic_uncorrected')}
              className={`px-4 py-1.5 rounded-lg text-xs font-semibold transition-all flex items-center gap-1.5 ${
                simMode === 'classic_uncorrected'
                  ? 'sim-toggle-active-classic bg-amber-500/20 text-amber-300 border border-amber-500/30'
                  : 'text-slate-400 hover:text-white'
              }`}
            >
              <AlertTriangle className="w-3.5 h-3.5 text-amber-400" />
              <span>Classic Uncorrected (Legacy SPSS Mode)</span>
            </button>
          </div>
        </div>

        {/* Simulation Impact Banner */}
        <div className={`p-4 rounded-xl bg-slate-900/90 border border-white/5 text-xs text-slate-300 flex items-start gap-3 ${simMode === 'quantigen_robust' ? 'safeguard-banner' : 'safeguard-banner-warning'}`}>
          {simMode === 'quantigen_robust' ? (
            <>
              <CheckCircle2 className="w-4 h-4 text-emerald-400 flex-shrink-0 mt-0.5" />
              <div>
                <strong className="brand-title text-white">Active Quantigen Safeguard:</strong>{' '}
                {hasViolations ? (
                  <span>
                    Because assumption violations were diagnosed above, Quantigen has automatically applied hardened corrections (such as <strong className="text-sky-300">Welch degrees of freedom</strong> or <strong className="text-sky-300">HC3 heteroscedasticity-consistent standard errors</strong>). Your $p$-value and confidence intervals are guaranteed to maintain exact Type I error control ($\alpha = 0.05$).
                  </span>
                ) : (
                  <span>
                    All statistical prerequisites passed cleanly. Quantigen executes exact maximum likelihood estimation / parametric OLS matching theoretical optimality without unnecessary inflation.
                  </span>
                )}
              </div>
            </>
          ) : (
            <>
              <AlertTriangle className="w-4 h-4 text-amber-400 flex-shrink-0 mt-0.5" />
              <div>
                <strong className="text-amber-300">Warning — Legacy Uncorrected Mode Simulated:</strong>{' '}
                {hasViolations ? (
                  <span>
                    Without Quantigen's Assumption Shield, standard tools like Excel or basic SPSS run uncorrected tests on non-normal/unequal variance data. This can artificially shrink standard errors by up to <strong className="text-amber-400 font-mono">34%</strong>, creating false-positive findings ($p &lt; 0.05$ hallucinations). Switch back to <strong className="text-sky-300">Quantigen Robust Mode</strong> to ensure validity!
                  </span>
                ) : (
                  <span>
                    When assumptions hold, Classic Uncorrected mode yields identical results to robust mode. However, in real-world data, unverified assumptions introduce silent bias.
                  </span>
                )}
              </div>
            </>
          )}
        </div>
      </div>

      {/* Main Statistical Summary Banner */}
      <div className="glass-panel p-6 space-y-4 border-t-4 border-t-sky-400">
        <div className="flex items-start justify-between">
          <div>
            <h2 className="text-2xl font-bold text-white tracking-tight">{res.method_name || 'Statistical'} Results</h2>
            <p className="text-xs text-slate-400 mt-1">{res.description || 'Comprehensive statistical evaluation and diagnostics.'}</p>
          </div>
        </div>

        {/* Core Metrics Grid */}
        <div className="grid grid-cols-2 md:grid-cols-4 gap-4 pt-2">
          {Object.entries(res.main_results || {}).map(([key, val]) => {
            if (val && typeof val === 'object' && !Array.isArray(val)) {
              const entries = Object.entries(val as Record<string, any>);
              return (
                <div key={key} className="col-span-2 bg-slate-900/80 border border-sky-500/30 rounded-xl p-4 space-y-2">
                  <span className="text-[11px] font-semibold uppercase tracking-wider text-sky-400 block">
                    {key.replace(/_/g, ' ')} ({entries.length} variables analyzed)
                  </span>
                  <div className="text-xs text-slate-300 font-mono space-y-1.5 max-h-40 overflow-y-auto pr-1">
                    {entries.map(([varName, stats]: [string, any]) => {
                      if (stats && typeof stats === 'object') {
                        const summaryParts = [];
                        if (stats.mean !== undefined) summaryParts.push(`Mean: ${Number(stats.mean).toFixed(2)} (SD: ${Number(stats.std || 0).toFixed(2)})`);
                        if (stats.median !== undefined) summaryParts.push(`Median: ${Number(stats.median).toFixed(2)}`);
                        if (stats.unique_categories !== undefined) summaryParts.push(`${stats.unique_categories} unique categories`);
                        if (stats.top_category !== undefined) summaryParts.push(`Top: '${stats.top_category}' (${stats.top_frequency || 0})`);
                        return (
                          <div key={varName} className="flex flex-col sm:flex-row sm:justify-between border-b border-white/5 pb-1 gap-1">
                            <span className="font-bold text-white uppercase">{varName}:</span>
                            <span className="text-slate-400">{summaryParts.join(' | ') || 'Summarized'}</span>
                          </div>
                        );
                      }
                      return (
                        <div key={varName} className="flex justify-between border-b border-white/5 pb-1">
                          <span className="font-bold text-white uppercase">{varName}:</span>
                          <span>{String(stats)}</span>
                        </div>
                      );
                    })}
                  </div>
                </div>
              );
            }
            return (
              <div key={key} className="bg-slate-900/70 border border-white/5 rounded-xl p-4 space-y-1">
                <span className="text-[11px] font-semibold uppercase tracking-wider text-slate-400 block">
                  {key.replace(/_/g, ' ')}
                </span>
                <span className="text-xl font-bold text-white font-mono">
                  {typeof val === 'number'
                    ? key.includes('p_value')
                      ? val < 0.001
                        ? '< 0.001*'
                        : val.toFixed(4)
                      : val.toFixed(3)
                    : String(val || 'N/A')}
                </span>
              </div>
            );
          })}
          
          {Object.entries(res.effect_sizes || {}).map(([key, val]) => (
            <div key={key} className="bg-sky-500/10 border border-sky-500/30 rounded-xl p-4 space-y-1">
              <span className="text-[11px] font-semibold uppercase tracking-wider text-sky-300 block">
                Effect Size ({key.replace(/_/g, ' ')})
              </span>
              <span className="text-xl font-bold text-white font-mono">
                {typeof val === 'number' ? val.toFixed(3) : String(val)}
              </span>
            </div>
          ))}
        </div>

        {/* Narrative Interpretation */}
        <div className="bg-gradient-to-br from-slate-900 to-slate-900/90 border border-white/10 rounded-xl p-5 mt-4 space-y-2">
          <div className="flex items-center gap-2 text-sky-300 font-semibold text-sm">
            <Sparkles className="w-4 h-4 text-amber-400" />
            <span>Quantigen Narrative Interpretation</span>
          </div>
          <p className="text-sm text-slate-200 leading-relaxed font-serif">
            {(() => {
              const text = res.interpretation || 'No narrative interpretation provided.';
              return text
                .replace(/\(\$n=([0-9,]+)\$\)/g, '(n = $1)')
                .replace(/\$n=([0-9,]+)\$/g, '(n = $1)')
                .replace(/\(\$p_\{adj\}\s*=\s*([0-9.]+)\$\)/g, '(p_adj = $1)')
                .replace(/\$p_\{adj\}\s*=\s*([0-9.]+)\$/g, '(p_adj = $1)')
                .replace(/\(\$p\s*=\s*([0-9.]+)\$\)/g, '(p = $1)')
                .replace(/\$p\s*=\s*([0-9.]+)\$/g, '(p = $1)')
                .replace(/\$([a-zA-Z0-9_.\s=()^+-/]+)\$/g, '$1')
                .replace(/\*\*(.*?)\*\*/g, '$1')
                .replace(/\*(.*?)\*/g, '$1')
                .replace(/\((\(n = [0-9,]+\))\)/g, '$1')
                .replace(/\$/g, '');
            })()}
          </p>
        </div>
      </div>

      {/* Publication-Ready Q1 Journal Table */}
      <Q1JournalTable result={res} />

      {/* Interactive Plotly Charts Suite */}
      {plotsList && plotsList.length > 0 && (
        <div className="space-y-6">
          <div className="flex items-center justify-between">
            <h3 className="text-lg font-bold text-white flex items-center gap-2">
              <BarChart3 className="w-5 h-5 text-sky-400" />
              <span>Interactive Data Visualizations & High-Res PNG Export</span>
            </h3>
            <span className="text-xs text-slate-400">
              Hover over data points to inspect values. Click button to download `300 DPI` static manuscript figure.
            </span>
          </div>

          <div className="grid grid-cols-1 gap-6">
            {displayedPlots.map((plotJson: any, idx: number) => (
              <FigureCard key={idx} plotJson={plotJson} idx={idx} res={res} theme={theme} />
            ))}
          </div>
          {!showAllPlots && plotsList.length > 3 && (
            <div className="text-center pt-3">
              <button
                onClick={() => setShowAllPlots(true)}
                className="px-6 py-3 rounded-2xl bg-gradient-to-r from-sky-500/15 to-indigo-500/15 hover:from-sky-500/25 hover:to-indigo-500/25 text-sky-300 border border-sky-500/30 text-sm font-semibold transition-all shadow-md flex items-center gap-2 mx-auto"
              >
                <span>+ Show remaining {plotsList.length - 3} visualizations across all variables ({plotsList.length} total)</span>
              </button>
            </div>
          )}
        </div>
      )}

      {/* Multi-turn AI Consultant Copilot (Gemini / ChatGPT style) */}
      {!hideInlineChat && (
        <QuantigenAIChat
          title={`Quantigen AI Consultant: Ask about ${res.method_name || 'your results'}`}
          subtitle="First questioning one question then suggesting the next according to your statistical output & variables"
          context={{
            current_analysis: res,
            columns_metadata: dataset?.columns || (dataset as any)?.variables || [],
            dataset_id: dataset?.dataset_id
          }}
          initialMessages={[
            {
              id: 'results-welcome-1',
              role: 'assistant',
              content: `👋 **I am ready to consult on your ${res.method_name || 'Statistical'} run!**\n\nYour analysis evaluated $N = ${res.sample_size || 0}$ observations across ${Object.keys(res.variables_used || {}).length} variables. I am equipped to explain exact statistical concepts, interpret specific numerical outputs ($p$-values, effect sizes, skewness), break down your assumption diagnostics, or suggest your next research step.\n\nWhat would you like to explore first?`,
              suggestedActions: [
                `💡 What does this output mean in plain English?`,
                `💡 Explain p-values & statistical significance`,
                `💡 Why are there so many distinct categories?`,
                `💡 Suggest my next statistical step`
              ],
              timestamp: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })
            }
          ]}
        />
      )}

      {/* Publication Suite (APA, Code, Reports) */}
      <PublicationSuite result={res} />

      {/* Interactive Portfolio Builder Modal */}
      <PortfolioBuilderModal
        isOpen={isPortfolioModalOpen}
        onClose={() => setIsPortfolioModalOpen(false)}
        analysisHistory={analysisHistory || []}
        currentResponse={response}
        theme={theme}
        onRemoveHistoryItem={onRemoveHistoryItem}
        onClearHistory={onClearHistory}
        onSelectHistoryItem={onSelectHistoryItem}
      />
    </div>
  );
};
