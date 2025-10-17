import { useState } from 'react';
import { Github, Loader2, CheckCircle, XCircle } from 'lucide-react';
import { apiClient } from '../../services/api';

const GitHubTestPanel = () => {
  const [repository, setRepository] = useState('octocat/Hello-World');
  const [isLoading, setIsLoading] = useState(false);
  const [result, setResult] = useState<any>(null);

  const handleTest = async () => {
    setIsLoading(true);
    setResult(null);

    try {
      const response = await apiClient.testGitHub(repository);
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
          <Github className="w-6 h-6 text-gray-700" />
          <h3 className="text-xl font-semibold text-gray-900">GitHub Repository Test</h3>
        </div>

        <div className="space-y-4">
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">
              Repository (owner/repo)
            </label>
            <input
              type="text"
              value={repository}
              onChange={(e) => setRepository(e.target.value)}
              placeholder="octocat/Hello-World"
              className="input-field"
            />
          </div>

          <button
            onClick={handleTest}
            disabled={isLoading || !repository.trim()}
            className="btn-primary w-full flex items-center justify-center space-x-2"
          >
            {isLoading ? (
              <>
                <Loader2 className="w-5 h-5 animate-spin" />
                <span>Testing...</span>
              </>
            ) : (
              <>
                <Github className="w-5 h-5" />
                <span>Test GitHub Integration</span>
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
              {result.success ? 'Success!' : 'Error'}
            </h3>
          </div>

          {result.success ? (
            <div className="space-y-4">
              <div>
                <p className="text-sm font-medium text-gray-700 mb-1">Repository</p>
                <p className="text-gray-900">{result.repository}</p>
              </div>
              
              {result.default_branch && (
                <div>
                  <p className="text-sm font-medium text-gray-700 mb-1">Default Branch</p>
                  <p className="text-gray-900">{result.default_branch}</p>
                </div>
              )}
              
              {result.issues && result.issues.length > 0 && (
                <div>
                  <p className="text-sm font-medium text-gray-700 mb-2">
                    Recent Issues ({result.issues.length})
                  </p>
                  <div className="space-y-2">
                    {result.issues.slice(0, 5).map((issue: any, index: number) => (
                      <div key={index} className="bg-gray-50 rounded-lg p-3">
                        <p className="font-medium text-gray-900">#{issue.number}: {issue.title}</p>
                        <p className="text-sm text-gray-600 mt-1">{issue.state}</p>
                      </div>
                    ))}
                  </div>
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

export default GitHubTestPanel;
