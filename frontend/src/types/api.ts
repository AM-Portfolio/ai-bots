export interface ServiceInfo {
  service: string;
  version: string;
  status: string;
  endpoints: {
    health: string;
    analyze: string;
    webhook: string;
  };
}

export interface ThinkingStep {
  id: string;
  title: string;
  description: string;
  status: 'pending' | 'in_progress' | 'completed' | 'failed' | 'skipped';
  start_time: string | null;
  end_time: string | null;
  metadata: Record<string, any>;
  error: string | null;
  duration_ms: number | null;
}

export interface ThinkingProcessData {
  workflow_id: string;
  workflow_type: string;
  steps: ThinkingStep[];
  start_time: string;
  end_time: string | null;
  total_duration_ms: number | null;
  status: string;
}

export interface LLMTestResponse {
  success: boolean;
  response?: string;
  error?: string;
  provider_used?: string;
  fallback_used?: boolean;
  tokens?: number;
  github_context?: any;
  thinking?: ThinkingProcessData;
}

export interface GitHubTestResponse {
  success: boolean;
  repository?: string;
  default_branch?: string;
  issues?: any[];
  error?: string;
}

export interface JiraTestResponse {
  success: boolean;
  projects?: any[];
  error?: string;
}

export interface ConfluenceTestResponse {
  success: boolean;
  spaces?: any[];
  error?: string;
}

export interface GrafanaTestResponse {
  success: boolean;
  datasources?: any[];
  error?: string;
}

export interface AnalyzeRequest {
  issue_id: string;
  source: string;
  repository?: string;
}

export interface AnalyzeResponse {
  success: boolean;
  analysis?: any;
  error?: string;
}

export interface DocOrchestrationRequest {
  prompt: string;
  repository: string;
  confluence_space?: string;
  jira_project?: string;
}

export interface DocOrchestrationResponse {
  success: boolean;
  documentation?: string;
  files_analyzed?: string[];
  repository?: string;
  github_commit?: {
    action?: string;
    file_path?: string;
    branch?: string;
    commit_url?: string;
    commit_sha?: string;
    file_url?: string;
  };
  confluence_page?: {
    id?: string;
    title?: string;
    url?: string;
    space_key?: string;
  };
  jira_ticket?: {
    key?: string;
    url?: string;
    id?: string;
  };
  error?: string;
  workflow_summary?: Record<string, string>;
  thinking?: ThinkingProcessData;
}

export type Provider = 'together' | 'azure';
export type Source = 'github' | 'jira' | 'grafana';
