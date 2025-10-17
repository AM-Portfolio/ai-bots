import { useState } from 'react';
import { BarChart3, Loader2, CheckCircle, XCircle } from 'lucide-react';
import { apiClient } from '../../services/api';
import type { Source } from '../../types/api';

const FullAnalysisPanel = () => {
  const [issueId, setIssueId] = useState('');
  const [source, setSource] = useState<Source>('github');
  const [repository, setRepository] = useState('owner/repo');
  const [isLoading, setIsLoading] = useState(false);
  const [result, setResult] = useState<any>(null);

  const handleAnalyze = async () => {
    setIsLoading(true);
    setResult(null);

    try {
      const response = await apiClient.analyze({
        issue_id: issueId,
        source,
        repository: source === 'github' ? repository : undefined,
      });
      setResult(response);
    } catch (error) {
      setResult({
        success: false,
        error: error instanceof Error ? error.message : 'Failed to connect to API',
      });
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <div className="space-y-6">
      <div className="card">
        <div className="flex items-center space-x-3 mb-6">
          <BarChart3 className="w-6 h-6 text-gray-700" />
          <h3 className="text-xl font-semibold text-gray-900">Full Issue Analysis</h3>
        </div>

        <div className="space-y-4">
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">
              Source
            </label>
            <select
              value={source}
              onChange={(e) => setSource(e.target.value as Source)}
              className="input-field"
            >
              <option value="github">GitHub</option>
              <option value="jira">Jira</option>
              <option value="grafana">Grafana</option>
            </select>
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">
              Issue ID
            </label>
            <input
              type="text"
              value={issueId}
              onChange={(e) => setIssueId(e.target.value)}
              placeholder="123"
              className="input-field"
            />
          </div>

          {source === 'github' && (
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">
                Repository (owner/repo)
              </label>
              <input
                type="text"
                value={repository}
                onChange={(e) => setRepository(e.target.value)}
                placeholder="owner/repo"
                className="input-field"
              />
            </div>
          )}

          <button
            onClick={handleAnalyze}
            disabled={isLoading || !issueId.trim()}
            className="btn-primary w-full flex items-center justify-center space-x-2"
          >
            {isLoading ? (
              <>
                <Loader2 className="w-5 h-5 animate-spin" />
                <span>Analyzing...</span>
              </>
            ) : (
              <>
                <BarChart3 className="w-5 h-5" />
                <span>Analyze Issue</span>
              </>
            )}
          </button>
        </div>
      </div>

      {result && (
        <div className="card">
          <div className="flex items-center space-x-3 mb-4">
            {result.success ? (
              <CheckCircle className="w-6 h-6 text-green-600" />
            ) : (
              <XCircle className="w-6 h-6 text-red-600" />
            )}
            <h3 className="text-lg font-semibold text-gray-900">
              {result.success ? 'Analysis Complete' : 'Analysis Failed'}
            </h3>
          </div>

          {result.success ? (
            <div className="space-y-4">
              <div className="bg-blue-50 border border-blue-200 rounded-lg p-4">
                <p className="text-blue-900">
                  Analysis completed successfully! The AI has processed the issue, enriched context,
                  and generated a comprehensive fix with tests.
                </p>
              </div>

              {result.analysis && (
                <div>
                  <pre className="bg-gray-50 rounded-lg p-4 overflow-x-auto text-sm">
                    {JSON.stringify(result.analysis, null, 2)}
                  </pre>
                </div>
              )}
            </div>
          ) : (
            <div className="bg-red-50 border border-red-200 rounded-lg p-4">
              <p className="text-red-800">{result.error}</p>
            </div>
          )}
        </div>
      )}
    </div>
  );
};

export default FullAnalysisPanel;
