import axios, { AxiosInstance } from 'axios';
import type {
  ServiceInfo,
  LLMTestResponse,
  GitHubTestResponse,
  JiraTestResponse,
  ConfluenceTestResponse,
  GrafanaTestResponse,
  AnalyzeRequest,
  AnalyzeResponse,
  DocOrchestrationRequest,
  DocOrchestrationResponse,
  Provider,
} from '../types/api';

class ApiClient {
  private client: AxiosInstance;

  constructor() {
    const baseURL = import.meta.env.DEV
      ? 'http://localhost:8000'
      : window.location.origin;

    this.client = axios.create({
      baseURL,
      headers: {
        'Content-Type': 'application/json',
      },
    });
  }

  async getServiceInfo(): Promise<ServiceInfo> {
    const { data } = await this.client.get<ServiceInfo>('/');
    return data;
  }

  async checkHealth(): Promise<{ status: string }> {
    const { data } = await this.client.get<{ status: string }>('/health');
    return data;
  }

  async testLLM(prompt: string, provider: Provider = 'together'): Promise<LLMTestResponse> {
    const { data } = await this.client.post<LLMTestResponse>(
      `/api/test/llm?prompt=${encodeURIComponent(prompt)}&provider=${provider}`
    );
    return data;
  }

  async testGitHub(repository: string): Promise<GitHubTestResponse> {
    const { data } = await this.client.post<GitHubTestResponse>(
      `/api/test/github?repository=${encodeURIComponent(repository)}`
    );
    return data;
  }

  async testJira(): Promise<JiraTestResponse> {
    const { data } = await this.client.post<JiraTestResponse>('/api/test/jira');
    return data;
  }

  async testConfluence(): Promise<ConfluenceTestResponse> {
    const { data } = await this.client.post<ConfluenceTestResponse>('/api/test/confluence');
    return data;
  }

  async testGrafana(): Promise<GrafanaTestResponse> {
    const { data } = await this.client.post<GrafanaTestResponse>('/api/test/grafana');
    return data;
  }

  async analyze(request: AnalyzeRequest): Promise<AnalyzeResponse> {
    const { data } = await this.client.post<AnalyzeResponse>('/api/analyze', request);
    return data;
  }

  async orchestrateDocumentation(request: DocOrchestrationRequest): Promise<DocOrchestrationResponse> {
    const { data } = await this.client.post<DocOrchestrationResponse>(
      '/api/docs/orchestrate',
      request
    );
    return data;
  }
}

export const apiClient = new ApiClient();
