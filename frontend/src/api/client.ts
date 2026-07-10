import axios from 'axios';
import type { DatasetSummary, AnalysisResponse, IntentRecommendation, MethodResult } from '../types/statmind';

const resolveApiUrl = () => {
  if (import.meta.env.VITE_API_BASE_URL) {
    return import.meta.env.VITE_API_BASE_URL;
  }
  if (typeof window !== 'undefined' && window.location.origin) {
    // When running in local development server (Vite port 5173), point to backend port 8000
    if (window.location.port === '5173' || window.location.port === '3000') {
      return `${window.location.protocol}//${window.location.hostname}:8000/api/v1`;
    }
    // Otherwise (when hosted by FastAPI or on public domain like https://quantigen.ai), use same origin
    return `${window.location.origin}/api/v1`;
  }
  return 'http://localhost:8000/api/v1';
};

const API_BASE_URL = resolveApiUrl();

const apiClient = axios.create({
  baseURL: API_BASE_URL,
});

export const normalizeDatasetSummary = (data: any): DatasetSummary => {
  if (!data) return data;
  const rawCols = data.columns || data.variables || [];
  const normalizedCols = rawCols.map((c: any) => {
    const dt = c.data_type || c.detected_type || 'categorical';
    const role = c.role || dt || 'categorical';
    return {
      name: c.name || 'Unnamed',
      role: role as any,
      data_type: dt,
      missing_count: c.missing_count ?? 0,
      unique_values: c.unique_values ?? 0,
      summary_stats: {
        ...(c.summary_stats || {}),
        categories: c.summary_stats?.categories || c.summary_stats?.top_categories || {},
      },
    };
  });

  return {
    ...data,
    dataset_id: data.dataset_id || '',
    filename: data.filename || data.name || 'dataset.csv',
    total_rows: data.total_rows ?? data.n_rows ?? 0,
    total_columns: data.total_columns ?? data.n_columns ?? normalizedCols.length,
    columns: normalizedCols,
    preview_data: data.preview_data || data.preview_rows || [],
    missing_values_total: data.missing_values_total ?? normalizedCols.reduce((acc: number, c: any) => acc + (c.missing_count || 0), 0),
  };
};

export const api = {
  async healthCheck(): Promise<{ status: string }> {
    const res = await apiClient.get('/health');
    return res.data;
  },

  async uploadDataset(file: File): Promise<DatasetSummary> {
    const formData = new FormData();
    formData.append('file', file);
    const res = await apiClient.post('/datasets/upload', formData);
    return normalizeDatasetSummary(res.data);
  },

  async updateVariableRole(datasetId: string, varName: string, role: string): Promise<DatasetSummary> {
    const res = await apiClient.patch(`/datasets/${datasetId}/variables/${varName}`, {
      detected_type: role,
    });
    return normalizeDatasetSummary(res.data);
  },

  async updateSurveyDesign(datasetId: string, surveyDesign: Record<string, any>): Promise<DatasetSummary> {
    const res = await apiClient.patch(`/datasets/${datasetId}/survey_design`, surveyDesign);
    return normalizeDatasetSummary(res.data);
  },

  async executeAnalysis(datasetId: string, methodId: string, variables: Record<string, any>): Promise<AnalysisResponse> {
    const res = await apiClient.post('/analysis/execute', {
      dataset_id: datasetId,
      method_id: methodId,
      variables,
    });
    const data = res.data || {};
    const methodResult = data.result || data.analysis_result || {};
    if (methodResult.plots && !methodResult.plots_json) {
      methodResult.plots_json = methodResult.plots;
    } else if (methodResult.plots_json && !methodResult.plots) {
      methodResult.plots = methodResult.plots_json;
    }
    methodResult.main_results = methodResult.main_results || {};
    methodResult.effect_sizes = methodResult.effect_sizes || {};
    methodResult.plots_json = methodResult.plots_json || [];
    methodResult.method_id = methodResult.method_id || methodId || '';
    methodResult.method_name = methodResult.method_name || 'Statistical Analysis';
    methodResult.method_family = methodResult.method_family || 'Analysis';
    methodResult.description = methodResult.description || '';
    methodResult.interpretation = methodResult.interpretation || '';

    const assumptionsList = data.assumption_results || data.assumptions || [];
    return {
      ...data,
      analysis_result: methodResult,
      result: methodResult,
      assumptions: assumptionsList,
      assumption_results: assumptionsList,
    } as any;
  },

  async recommendMethod(query: string, columnsMetadata: any[], datasetId?: string): Promise<{ recommendation: IntentRecommendation; message: string }> {
    const res = await apiClient.post('/chat/recommend', {
      query,
      dataset_id: datasetId || '',
      columns_metadata: columnsMetadata,
    });
    const rec = res.data.recommendation || res.data;
    return {
      recommendation: rec,
      message: res.data.message || `Recommended ${rec?.method_name || 'statistical method'}.`,
    };
  },

  async consultFollowup(message: string, history: any[], context: any): Promise<any> {
    const res = await apiClient.post('/chat/consult', {
      message,
      history,
      context,
    });
    return res.data;
  },

  async downloadScript(code: string, language: string, filename?: string) {
    const res = await apiClient.post('/export/script', { code, language, filename }, { responseType: 'blob' });
    const url = window.URL.createObjectURL(new Blob([res.data]));
    const link = document.createElement('a');
    link.href = url;
    const ext = language.toLowerCase() === 'rmd' ? 'Rmd' : language.toLowerCase() === 'r' ? 'R' : 'py';
    link.setAttribute('download', `${filename || 'quantigen_script'}.${ext}`);
    document.body.appendChild(link);
    link.click();
    link.remove();
  },

  async downloadChartPNG(plotJson: any, filename?: string) {
    const res = await apiClient.post('/export/chart', {
      plot_json: plotJson,
      width: 1000,
      height: 600,
      scale: 3.0,
      filename: filename || 'quantigen_chart',
    }, { responseType: 'blob' });
    
    const url = window.URL.createObjectURL(new Blob([res.data], { type: 'image/png' }));
    const link = document.createElement('a');
    link.href = url;
    link.setAttribute('download', `${filename || 'quantigen_chart'}.png`);
    document.body.appendChild(link);
    link.click();
    link.remove();
  },

  async downloadReport(result: MethodResult, format: 'markdown' | 'html' | 'html_manuscript' | 'doc' | 'pdf' = 'html_manuscript', apaCitation?: string) {
    const payload = {
      method_name: result.method_name,
      description: result.description,
      sample_size: result.sample_size,
      interpretation: result.interpretation,
      r_code: result.r_code,
      python_code: result.python_code,
      apa_citation: apaCitation,
      assumption_summary: result.assumption_summary,
      plots_json: (result as any).plots || (result as any).plots_json || [],
      format,
    };
    
    const res = await apiClient.post('/export/report', payload, { responseType: 'blob' });
    const extMap: Record<string, string> = {
      markdown: 'md',
      doc: 'doc',
      pdf: 'pdf', // True standalone binary manuscript PDF
      html: 'html',
      html_manuscript: 'html'
    };
    const mimeMap: Record<string, string> = {
      markdown: 'text/markdown;charset=utf-8',
      doc: 'application/msword',
      pdf: 'application/pdf',
      html: 'text/html;charset=utf-8',
      html_manuscript: 'text/html;charset=utf-8'
    };
    const ext = extMap[format] || 'html';
    const rawHeader = res.headers?.['content-type'];
    const headerStr = typeof rawHeader === 'string' ? rawHeader : 'application/octet-stream';
    const mimeType = mimeMap[format] || headerStr;
    const safeName = (result.method_id || result.method_name || 'analysis').toString().toLowerCase().replace(/[^a-z0-9_]/g, '_');
    const blob = new Blob([res.data], { type: mimeType });
    const url = window.URL.createObjectURL(blob);
    const link = document.createElement('a');
    link.href = url;
    link.setAttribute('download', `quantigen_${safeName}_${format === 'doc' ? 'manuscript' : 'report'}.${ext}`);
    document.body.appendChild(link);
    link.click();
    setTimeout(() => window.URL.revokeObjectURL(url), 100);
    link.remove();
  },

  async downloadPortfolio(payload: import('../types/statmind').PortfolioExportPayload) {
    const res = await apiClient.post('/export/portfolio', payload, { responseType: 'blob' });
    const extMap: Record<string, string> = {
      pdf: 'pdf',
      doc: 'doc',
      html: 'html',
      rmarkdown: 'Rmd',
    };
    const ext = extMap[payload.format] || 'pdf';
    const rawHeader = res.headers?.['content-type'];
    const mimeType = typeof rawHeader === 'string' ? rawHeader : 'application/octet-stream';
    const safeTitle = (payload.title || 'quantigen_portfolio').toString().toLowerCase().replace(/[^a-z0-9_]/g, '_');
    const blob = new Blob([res.data], { type: mimeType });
    const url = window.URL.createObjectURL(blob);
    const link = document.createElement('a');
    link.href = url;
    link.setAttribute('download', `${safeTitle}.${ext}`);
    document.body.appendChild(link);
    link.click();
    setTimeout(() => window.URL.revokeObjectURL(url), 100);
    link.remove();
  },

  async executeAnalysisStream(
    datasetId: string,
    methodId: string,
    variables: Record<string, any>,
    onStep: (stepEvent: { step_id?: string; status?: string; label?: string; detail?: string; type?: string; data?: any }) => void,
    options: Record<string, any> = {}
  ): Promise<AnalysisResponse> {
    const response = await fetch(`${API_BASE_URL}/analysis/agent/run`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        dataset_id: datasetId,
        method_id: methodId,
        variables,
        options,
        override_assumptions: true,
      }),
    });

    if (!response.ok || !response.body) {
      throw new Error(`Failed to initiate agent stream: ${response.statusText}`);
    }

    const reader = response.body.getReader();
    const decoder = new TextDecoder('utf-8');
    let buffer = '';
    let finalResult: AnalysisResponse | null = null;

    while (true) {
      const { done, value } = await reader.read();
      if (done) break;
      buffer += decoder.decode(value, { stream: true });
      const lines = buffer.split('\n\n');
      buffer = lines.pop() || '';

      for (const line of lines) {
        if (line.startsWith('data: ')) {
          try {
            const jsonStr = line.replace('data: ', '').trim();
            if (!jsonStr) continue;
            const payload = JSON.parse(jsonStr);
            onStep(payload);
            if (payload.type === 'final_result') {
              finalResult = payload.data;
            } else if (payload.type === 'error') {
              throw new Error(payload.detail || 'Error in agent execution stream');
            }
          } catch (e: any) {
            console.error('Error parsing SSE payload:', e);
          }
        }
      }
    }

    if (!finalResult) {
      return this.executeAnalysis(datasetId, methodId, variables);
    }
    return finalResult;
  },
};
