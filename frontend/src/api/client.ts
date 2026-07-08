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
    // Otherwise (when hosted by FastAPI or on public domain like https://statmind.app), use same origin
    return `${window.location.origin}/api/v1`;
  }
  return 'http://localhost:8000/api/v1';
};

const API_BASE_URL = resolveApiUrl();

const apiClient = axios.create({
  baseURL: API_BASE_URL,
  headers: {
    'Content-Type': 'application/json',
  },
});

export const api = {
  async healthCheck(): Promise<{ status: string }> {
    const res = await apiClient.get('/health');
    return res.data;
  },

  async uploadDataset(file: File): Promise<DatasetSummary> {
    const formData = new FormData();
    formData.append('file', file);
    const res = await apiClient.post('/datasets/upload', formData, {
      headers: { 'Content-Type': 'multipart/form-data' },
    });
    return res.data;
  },

  async updateVariableRole(datasetId: string, varName: string, role: string): Promise<DatasetSummary> {
    const res = await apiClient.patch(`/datasets/${datasetId}/variables/${varName}`, null, {
      params: { role },
    });
    return res.data;
  },

  async executeAnalysis(datasetId: string, methodId: string, variables: Record<string, any>): Promise<AnalysisResponse> {
    const res = await apiClient.post('/analysis/execute', {
      dataset_id: datasetId,
      method_id: methodId,
      variables,
    });
    return res.data;
  },

  async recommendMethod(query: string, columnsMetadata: any[]): Promise<{ recommendation: IntentRecommendation; message: string }> {
    const res = await apiClient.post('/chat/recommend', {
      query,
      columns_metadata: columnsMetadata,
    });
    return {
      recommendation: res.data.recommendation,
      message: res.data.message,
    };
  },

  async consultFollowup(message: string, history: any[], context: any): Promise<{ response: string }> {
    const res = await apiClient.post('/chat/consult', {
      message,
      history,
      context,
    });
    return res.data;
  },

  async downloadScript(code: string, language: 'r' | 'python', filename?: string) {
    const res = await apiClient.post('/export/script', { code, language, filename }, { responseType: 'blob' });
    const url = window.URL.createObjectURL(new Blob([res.data]));
    const link = document.createElement('a');
    link.href = url;
    link.setAttribute('download', `${filename || 'statmind_script'}.${language === 'r' ? 'R' : 'py'}`);
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
      filename: filename || 'statmind_chart',
    }, { responseType: 'blob' });
    
    const url = window.URL.createObjectURL(new Blob([res.data], { type: 'image/png' }));
    const link = document.createElement('a');
    link.href = url;
    link.setAttribute('download', `${filename || 'statmind_chart'}.png`);
    document.body.appendChild(link);
    link.click();
    link.remove();
  },

  async downloadReport(result: MethodResult, format: 'markdown' | 'html' | 'html_manuscript' = 'html_manuscript', apaCitation?: string) {
    const payload = {
      method_name: result.method_name,
      description: result.description,
      sample_size: result.sample_size,
      interpretation: result.interpretation,
      r_code: result.r_code,
      python_code: result.python_code,
      apa_citation: apaCitation,
      assumption_summary: result.assumption_summary,
      plots_json: result.plots_json,
      format,
    };
    
    const res = await apiClient.post('/export/report', payload, { responseType: 'blob' });
    const ext = format === 'markdown' ? 'md' : 'html';
    const url = window.URL.createObjectURL(new Blob([res.data]));
    const link = document.createElement('a');
    link.href = url;
    link.setAttribute('download', `statmind_${result.method_id}_report.${ext}`);
    document.body.appendChild(link);
    link.click();
    link.remove();
  },
};
