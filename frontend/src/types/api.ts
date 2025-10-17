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

export interface LLMTestResponse {
  success: boolean;
  response?: string;
  error?: string;
  provider_used?: string;
  fallback_used?: boolean;
  tokens?: number;
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
  github_analysis?: any;
  documentation?: any;
  commit?: any;
  confluence_page?: any;
  jira_ticket?: any;
  error?: string;
}

export type Provider = 'together' | 'azure';
export type Source = 'github' | 'jira' | 'grafana';
