import { useState } from 'react';
import { Loader2, CheckCircle, XCircle } from 'lucide-react';
import { apiClient } from '../../services/api';

interface TestResult {
  success: boolean;
  data?: any;
  error?: string;
}

const IntegrationsPanel = () => {
  const [githubRepo, setGithubRepo] = useState('octocat/Hello-World');
  const [githubResult, setGithubResult] = useState<TestResult | null>(null);
  const [jiraResult, setJiraResult] = useState<TestResult | null>(null);
  const [confluenceResult, setConfluenceResult] = useState<TestResult | null>(null);
  const [grafanaResult, setGrafanaResult] = useState<TestResult | null>(null);
  const [loadingStates, setLoadingStates] = useState({
    github: false,
    jira: false,
    confluence: false,
    grafana: false,
  });

  const testGitHub = async () => {
    setLoadingStates((prev) => ({ ...prev, github: true }));
    setGithubResult(null);
    try {
      const response = await apiClient.testGitHub(githubRepo);
      setGithubResult({ success: response.success, data: response, error: response.error });
    } catch (error) {
      setGithubResult({
        success: false,
        error: error instanceof Error ? error.message : 'Failed to connect',
      });
    } finally {
      setLoadingStates((prev) => ({ ...prev, github: false }));
    }
  };

  const testJira = async () => {
    setLoadingStates((prev) => ({ ...prev, jira: true }));
    setJiraResult(null);
    try {
      const response = await apiClient.testJira();
      setJiraResult({ success: response.success, data: response.projects, error: response.error });
    } catch (error) {
      setJiraResult({
        success: false,
        error: error instanceof Error ? error.message : 'Failed to connect',
      });
    } finally {
      setLoadingStates((prev) => ({ ...prev, jira: false }));
    }
  };

  const testConfluence = async () => {
    setLoadingStates((prev) => ({ ...prev, confluence: true }));
    setConfluenceResult(null);
    try {
      const response = await apiClient.testConfluence();
      setConfluenceResult({
        success: response.success,
        data: response.spaces,
        error: response.error,
      });
    } catch (error) {
      setConfluenceResult({
        success: false,
        error: error instanceof Error ? error.message : 'Failed to connect',
      });
    } finally {
      setLoadingStates((prev) => ({ ...prev, confluence: false }));
    }
  };

  const testGrafana = async () => {
    setLoadingStates((prev) => ({ ...prev, grafana: true }));
    setGrafanaResult(null);
    try {
      const response = await apiClient.testGrafana();
      setGrafanaResult({
        success: response.success,
        data: response.datasources,
        error: response.error,
      });
    } catch (error) {
      setGrafanaResult({
        success: false,
        error: error instanceof Error ? error.message : 'Failed to connect',
      });
    } finally {
      setLoadingStates((prev) => ({ ...prev, grafana: false }));
    }
  };

  const IntegrationCard = ({
    title,
    description,
    icon,
    onTest,
    isLoading,
    result,
    hasInput = false,
    inputValue = '',
    onInputChange,
    inputPlaceholder = '',
  }: {
    title: string;
    description: string;
    icon: string;
    onTest: () => void;
    isLoading: boolean;
    result: TestResult | null;
    hasInput?: boolean;
    inputValue?: string;
    onInputChange?: (value: string) => void;
    inputPlaceholder?: string;
  }) => (
    <div className="card">
      <div className="flex items-center space-x-3 mb-4">
        <div className="w-12 h-12 bg-gradient-to-br from-primary-500 to-primary-700 rounded-lg flex items-center justify-center text-2xl">
          {icon}
        </div>
        <div>
          <h3 className="text-lg font-semibold text-gray-900">{title}</h3>
          <p className="text-sm text-gray-600">{description}</p>
        </div>
      </div>

      {hasInput && onInputChange && (
        <div className="mb-4">
          <input
            type="text"
            value={inputValue}
            onChange={(e) => onInputChange(e.target.value)}
            placeholder={inputPlaceholder}
            className="input-field w-full"
          />
        </div>
      )}

      <button
        onClick={onTest}
        disabled={isLoading}
        className="btn-primary w-full flex items-center justify-center space-x-2"
      >
        {isLoading ? (
          <>
            <Loader2 className="w-5 h-5 animate-spin" />
            <span>Testing...</span>
          </>
        ) : (
          <span>Test Integration</span>
        )}
      </button>

      {result && (
        <div className="mt-4">
          <div className="flex items-center space-x-2 mb-2">
            {result.success ? (
              <CheckCircle className="w-5 h-5 text-green-600" />
            ) : (
              <XCircle className="w-5 h-5 text-red-600" />
            )}
            <span className="font-medium text-gray-900">
              {result.success ? 'Connected!' : 'Connection Failed'}
            </span>
          </div>

          {result.success && result.data && (
            <div className="bg-green-50 border border-green-200 rounded-lg p-3">
              {Array.isArray(result.data) ? (
                <p className="text-sm text-green-800">
                  Found {result.data.length} item(s)
                </p>
              ) : result.data.repository ? (
                <div className="text-sm text-green-800">
                  <p>Repository: {result.data.repository}</p>
                  {result.data.default_branch && <p>Branch: {result.data.default_branch}</p>}
                  {result.data.issues && <p>Issues: {result.data.issues.length}</p>}
                </div>
              ) : (
                <p className="text-sm text-green-800">Connected successfully!</p>
              )}
            </div>
          )}

          {!result.success && result.error && (
            <div className="bg-red-50 border border-red-200 rounded-lg p-3">
              <p className="text-sm text-red-800">{result.error}</p>
            </div>
          )}
        </div>
      )}
    </div>
  );

  return (
    <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
      <IntegrationCard
        title="GitHub"
        description="Test GitHub API connection"
        icon="🐙"
        onTest={testGitHub}
        isLoading={loadingStates.github}
        result={githubResult}
        hasInput={true}
        inputValue={githubRepo}
        onInputChange={setGithubRepo}
        inputPlaceholder="owner/repo"
      />
      
      <IntegrationCard
        title="Jira"
        description="Test Jira API connection"
        icon="📋"
        onTest={testJira}
        isLoading={loadingStates.jira}
        result={jiraResult}
      />
      
      <IntegrationCard
        title="Confluence"
        description="Test Confluence API connection"
        icon="📚"
        onTest={testConfluence}
        isLoading={loadingStates.confluence}
        result={confluenceResult}
      />
      
      <IntegrationCard
        title="Grafana"
        description="Test Grafana API connection"
        icon="📊"
        onTest={testGrafana}
        isLoading={loadingStates.grafana}
        result={grafanaResult}
      />
    </div>
  );
};

export default IntegrationsPanel;
