export type VariableRole = 'continuous' | 'categorical' | 'ordinal' | 'binary' | 'count' | 'datetime' | 'id';

export interface VariableMetadata {
  name: string;
  role: VariableRole;
  data_type: string;
  missing_count: number;
  unique_values: number;
  summary_stats?: {
    mean?: number;
    std?: number;
    min?: number;
    max?: number;
    categories?: Record<string, number>;
  };
}

export interface SurveyDesignSpec {
  is_survey_weighted: boolean;
  design_type?: string;
  weight_var?: string | null;
  cluster_var?: string | null;
  strata_var?: string | null;
  nest?: boolean;
}

export interface DatasetSummary {
  dataset_id: string;
  filename: string;
  total_rows: number;
  total_columns: number;
  columns: VariableMetadata[];
  preview_data: Record<string, any>[];
  missing_values_total: number;
  survey_design?: SurveyDesignSpec;
}

export interface AssumptionResult {
  assumption_name: string;
  test_name: string;
  p_value?: number | null;
  statistic?: number | null;
  passed: boolean;
  explanation: string;
}

export interface MethodResult {
  method_id: string;
  method_name: string;
  method_family: string;
  description: string;
  variables_used: Record<string, any>;
  sample_size: number;
  main_results: Record<string, any>;
  effect_sizes: Record<string, any>;
  plots_json: Record<string, any>[];
  assumption_summary: string;
  python_code: string;
  r_code: string;
  interpretation: string;
}

export interface AnalysisResponse {
  history_id?: string;
  timestamp?: string;
  analysis_result: MethodResult;
  assumptions: AssumptionResult[];
  recommendation?: {
    status: 'PASSED' | 'WARNING' | 'VIOLATED';
    message: string;
    suggested_method?: string;
  };
}

export interface IntentRecommendation {
  method_id: string;
  method_name: string;
  method_family: string;
  rationale: string;
  suggested_variables: Record<string, any>;
  mapped_variables?: Record<string, any>;
  assumptions_to_check: string[];
  requires_confirmation: boolean;
}

export interface ChatMessage {
  id: string;
  sender: 'user' | 'assistant';
  text: string;
  recommendation?: IntentRecommendation;
  timestamp: string;
}

export interface PortfolioItemConfig {
  history_id: string;
  include_table: boolean;
  include_graph: boolean;
  include_narrative: boolean;
  include_code: boolean;
  preferred_graph_type: 'pie' | 'bar' | 'box' | 'default';
}

export interface PortfolioItemRequest {
  history_id: string;
  method_name: string;
  description: string;
  sample_size: number;
  interpretation: string;
  r_code: string;
  python_code: string;
  apa_citation?: string;
  assumption_summary?: string;
  plots_json?: Record<string, any>[];
  main_results?: Record<string, any>;
  effect_sizes?: Record<string, any>;
  config: PortfolioItemConfig;
}

export interface PortfolioExportPayload {
  title: string;
  items: PortfolioItemRequest[];
  format: 'pdf' | 'doc' | 'html' | 'rmarkdown';
}
