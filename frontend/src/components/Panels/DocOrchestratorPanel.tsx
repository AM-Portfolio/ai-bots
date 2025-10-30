import { useState } from 'react';
import { FileText, Loader2, CheckCircle, AlertCircle, Github, FileCode, BookOpen } from 'lucide-react';
import { apiClient } from '../../services/api';

interface Step {
  name: string;
  status: 'pending' | 'running' | 'complete' | 'error';
  message?: string;
}

const DocOrchestratorPanel = () => {
  const [prompt, setPrompt] = useState('Document the authentication module in the project');
  const [repository, setRepository] = useState('AM-Portfolio/am-portfolio');
  
  const [enableGithub, setEnableGithub] = useState(true);
  const [enableConfluence, setEnableConfluence] = useState(true);
  const [enableJira, setEnableJira] = useState(true);
  
  const [confluenceSpace, setConfluenceSpace] = useState('~712020d4f71b3abac74895ba25e7e54d4cfc10');
  const [jiraProject, setJiraProject] = useState('KAN');
  
  const [isRunning, setIsRunning] = useState(false);
  const [steps, setSteps] = useState<Step[]>([]);
  const [result, setResult] = useState<any>(null);

  const handleOrchestrate = async () => {
    setIsRunning(true);
    setResult(null);
    setSteps([
      { name: 'Analyzing GitHub Repository', status: 'running' },
      { name: 'Generating Documentation', status: 'pending' },
      { name: 'Committing to GitHub', status: 'pending' },
      { name: 'Publishing to Confluence', status: 'pending' },
      { name: 'Creating Jira Ticket', status: 'pending' },
    ]);

    try {
      const response = await apiClient.orchestrateDocumentation({
        prompt,
        repository,
        commit_to_github: enableGithub,
        publish_to_confluence: enableConfluence,
        confluence_space_key: enableConfluence ? confluenceSpace : undefined,
        create_jira_ticket: enableJira,
        jira_project_key: enableJira ? jiraProject : undefined,
      });

      const updateStep = (index: number, status: Step['status'], message?: string) => {
        setSteps((prev) =>
          prev.map((step, i) =>
            i === index ? { ...step, status, message } : step
          )
        );
      };

      if (response.files_analyzed && response.files_analyzed.length > 0) {
        updateStep(0, 'complete', `Analyzed ${response.files_analyzed.length} files`);
        updateStep(1, 'running');
      } else {
        updateStep(0, 'complete', 'Repository analyzed');
        updateStep(1, 'running');
      }

      if (response.documentation) {
        updateStep(1, 'complete', `Generated ${Math.round(response.documentation.length / 100)} KB of docs`);
        updateStep(2, 'running');
      }

      if (response.github_commit) {
        const commitMsg = response.github_commit.branch 
          ? `${response.github_commit.action} on ${response.github_commit.branch}`
          : `Committed: ${response.github_commit.commit_sha?.substring(0, 7)}`;
        updateStep(2, 'complete', commitMsg);
        
        if (enableConfluence) {
          updateStep(3, 'running');
        } else {
          updateStep(3, 'complete', 'Skipped (not enabled)');
        }
      } else if (!enableGithub) {
        updateStep(2, 'complete', 'Skipped (not enabled)');
        if (enableConfluence) {
          updateStep(3, 'running');
        } else {
          updateStep(3, 'complete', 'Skipped (not enabled)');
        }
      }

      if (response.confluence_page) {
        updateStep(3, 'complete', `Page: ${response.confluence_page.title}`);
        
        if (enableJira) {
          updateStep(4, 'running');
        } else {
          updateStep(4, 'complete', 'Skipped (not enabled)');
        }
      } else if (!enableConfluence) {
        updateStep(3, 'complete', 'Skipped (not enabled)');
        
        if (enableJira) {
          updateStep(4, 'running');
        } else {
          updateStep(4, 'complete', 'Skipped (not enabled)');
        }
      }

      if (response.jira_ticket) {
        updateStep(4, 'complete', `Ticket: ${response.jira_ticket.key}`);
      } else if (!enableJira) {
        updateStep(4, 'complete', 'Skipped (not enabled)');
      }

      setResult(response);
    } catch (error) {
      const errorMessage = error instanceof Error ? error.message : 'Failed to orchestrate';
      setSteps((prev) =>
        prev.map((step) =>
          step.status === 'running' ? { ...step, status: 'error', message: errorMessage } : step
        )
      );
      setResult({ success: false, error: errorMessage });
    } finally {
      setIsRunning(false);
    }
  };

  return (
    <div className="space-y-6">
      <div className="card">
        <div className="flex items-center space-x-3 mb-6">
          <FileText className="w-6 h-6 text-gray-700" />
          <h3 className="text-xl font-semibold text-gray-900">
            AI-Powered Documentation Workflow
          </h3>
        </div>

        <div className="space-y-4">
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">
              Documentation Prompt
            </label>
            <textarea
              value={prompt}
              onChange={(e) => setPrompt(e.target.value)}
              placeholder="Describe what you want to document..."
              className="textarea-field"
              rows={3}
            />
          </div>

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

          <div className="border-t border-gray-200 pt-4">
            <label className="block text-sm font-medium text-gray-700 mb-3">
              Select Publishing Destinations
            </label>
            
            <div className="space-y-4">
              <label className="flex items-start space-x-3 p-4 border rounded-lg cursor-pointer hover:bg-gray-50 transition-colors">
                <input
                  type="checkbox"
                  checked={enableGithub}
                  onChange={(e) => setEnableGithub(e.target.checked)}
                  className="mt-1 h-4 w-4 text-primary-600 border-gray-300 rounded focus:ring-primary-500"
                />
                <div className="flex-1">
                  <div className="flex items-center space-x-2">
                    <Github className="w-5 h-5 text-gray-600" />
                    <span className="font-medium text-gray-900">Commit to GitHub</span>
                    <span className="text-xs bg-green-100 text-green-700 px-2 py-0.5 rounded">Recommended</span>
                  </div>
                  <p className="text-sm text-gray-600 mt-1">
                    Create a new branch and commit documentation to your repository
                  </p>
                </div>
              </label>

              <label className="flex items-start space-x-3 p-4 border rounded-lg cursor-pointer hover:bg-gray-50 transition-colors">
                <input
                  type="checkbox"
                  checked={enableConfluence}
                  onChange={(e) => setEnableConfluence(e.target.checked)}
                  className="mt-1 h-4 w-4 text-primary-600 border-gray-300 rounded focus:ring-primary-500"
                />
                <div className="flex-1">
                  <div className="flex items-center space-x-2">
                    <BookOpen className="w-5 h-5 text-gray-600" />
                    <span className="font-medium text-gray-900">Publish to Confluence</span>
                  </div>
                  <p className="text-sm text-gray-600 mt-1">
                    Create a documentation page in your Confluence space
                  </p>
                  
                  {enableConfluence && (
                    <div className="mt-3">
                      <input
                        type="text"
                        value={confluenceSpace}
                        onChange={(e) => setConfluenceSpace(e.target.value)}
                        placeholder="Space Key (e.g., AlgoTradin)"
                        className="input-field text-sm"
                      />
                      <p className="text-xs text-gray-500 mt-1">
                        💡 Available: AlgoTradin, 380b0d2c6e0d44cea72e7ec2f0fac338
                      </p>
                    </div>
                  )}
                </div>
              </label>

              <label className="flex items-start space-x-3 p-4 border rounded-lg cursor-pointer hover:bg-gray-50 transition-colors">
                <input
                  type="checkbox"
                  checked={enableJira}
                  onChange={(e) => setEnableJira(e.target.checked)}
                  className="mt-1 h-4 w-4 text-primary-600 border-gray-300 rounded focus:ring-primary-500"
                />
                <div className="flex-1">
                  <div className="flex items-center space-x-2">
                    <FileCode className="w-5 h-5 text-gray-600" />
                    <span className="font-medium text-gray-900">Create Jira Ticket</span>
                  </div>
                  <p className="text-sm text-gray-600 mt-1">
                    Create a documentation tracking ticket in Jira
                  </p>
                  
                  {enableJira && (
                    <div className="mt-3">
                      <input
                        type="text"
                        value={jiraProject}
                        onChange={(e) => setJiraProject(e.target.value)}
                        placeholder="Project Key (e.g., PROJ)"
                        className="input-field text-sm"
                      />
                      <p className="text-xs text-gray-500 mt-1">
                        💡 Test Jira integration to see available projects
                      </p>
                    </div>
                  )}
                </div>
              </label>
            </div>
          </div>

          <button
            onClick={handleOrchestrate}
            disabled={isRunning || !prompt.trim() || !repository.trim() || (!enableGithub && !enableConfluence && !enableJira)}
            className="btn-primary w-full flex items-center justify-center space-x-2"
          >
            {isRunning ? (
              <>
                <Loader2 className="w-5 h-5 animate-spin" />
                <span>Orchestrating...</span>
              </>
            ) : (
              <>
                <FileText className="w-5 h-5" />
                <span>Start Documentation Workflow</span>
              </>
            )}
          </button>
          
          {!enableGithub && !enableConfluence && !enableJira && (
            <p className="text-sm text-amber-600 text-center">
              ⚠️ Please select at least one destination
            </p>
          )}
        </div>
      </div>

      {steps.length > 0 && (
        <div className="card">
          <h3 className="text-lg font-semibold text-gray-900 mb-4">Workflow Progress</h3>
          <div className="space-y-3">
            {steps.map((step, index) => (
              <div
                key={index}
                className="flex items-center space-x-3 p-3 bg-gray-50 rounded-lg"
              >
                {step.status === 'pending' && (
                  <div className="w-6 h-6 rounded-full border-2 border-gray-300" />
                )}
                {step.status === 'running' && (
                  <Loader2 className="w-6 h-6 text-primary-600 animate-spin" />
                )}
                {step.status === 'complete' && (
                  <CheckCircle className="w-6 h-6 text-green-600" />
                )}
                {step.status === 'error' && (
                  <AlertCircle className="w-6 h-6 text-red-600" />
                )}

                <div className="flex-1">
                  <p className="font-medium text-gray-900">{step.name}</p>
                  {step.message && (
                    <p className="text-sm text-gray-600 mt-1">{step.message}</p>
                  )}
                </div>
              </div>
            ))}
          </div>
        </div>
      )}

      {result && result.success && (
        <div className="card bg-green-50 border-green-200">
          <div className="flex items-center space-x-2 mb-4">
            <CheckCircle className="w-5 h-5 text-green-600" />
            <h3 className="text-lg font-semibold text-green-900">
              Documentation Workflow Complete!
            </h3>
          </div>
          <p className="text-sm text-green-700 mb-4">
            All steps completed successfully. Documentation has been generated, committed, and published.
          </p>

          <div className="bg-white rounded-lg p-4 space-y-3">
            <h4 className="text-sm font-semibold text-gray-700 mb-2">📎 Quick Links:</h4>
            
            {result.github_commit && (
              <>
                <div className="flex items-start space-x-2">
                  <Github className="w-4 h-4 text-gray-500 mt-0.5" />
                  <div className="flex-1 min-w-0">
                    <p className="text-sm font-medium text-gray-700">GitHub File:</p>
                    <a
                      href={result.github_commit.file_url}
                      target="_blank"
                      rel="noopener noreferrer"
                      className="text-sm text-primary-600 hover:text-primary-700 hover:underline break-all"
                    >
                      {result.github_commit.file_path} (branch: {result.github_commit.branch})
                    </a>
                  </div>
                </div>

                <div className="flex items-start space-x-2">
                  <FileCode className="w-4 h-4 text-gray-500 mt-0.5" />
                  <div className="flex-1 min-w-0">
                    <p className="text-sm font-medium text-gray-700">Commit:</p>
                    <a
                      href={result.github_commit.commit_url}
                      target="_blank"
                      rel="noopener noreferrer"
                      className="text-sm text-primary-600 hover:text-primary-700 hover:underline break-all"
                    >
                      {result.github_commit.commit_sha?.substring(0, 7)}
                    </a>
                  </div>
                </div>
              </>
            )}

            {result.confluence_page && (
              <div className="flex items-start space-x-2">
                <BookOpen className="w-4 h-4 text-gray-500 mt-0.5" />
                <div className="flex-1 min-w-0">
                  <p className="text-sm font-medium text-gray-700">Confluence Page:</p>
                  <a
                    href={result.confluence_page.url}
                    target="_blank"
                    rel="noopener noreferrer"
                    className="text-sm text-primary-600 hover:text-primary-700 hover:underline break-all"
                  >
                    {result.confluence_page.title}
                  </a>
                </div>
              </div>
            )}

            {result.jira_ticket && (
              <div className="flex items-start space-x-2">
                <FileText className="w-4 h-4 text-gray-500 mt-0.5" />
                <div className="flex-1 min-w-0">
                  <p className="text-sm font-medium text-gray-700">Jira Ticket:</p>
                  <a
                    href={result.jira_ticket.url}
                    target="_blank"
                    rel="noopener noreferrer"
                    className="text-sm text-primary-600 hover:text-primary-700 hover:underline"
                  >
                    {result.jira_ticket.key}
                  </a>
                </div>
              </div>
            )}
          </div>
        </div>
      )}

      {result && !result.success && (
        <div className="card bg-red-50 border-red-200">
          <div className="flex items-center space-x-2">
            <AlertCircle className="w-5 h-5 text-red-600" />
            <h3 className="text-lg font-semibold text-red-900">Workflow Failed</h3>
          </div>
          <p className="text-sm text-red-700 mt-2">{result.error}</p>
        </div>
      )}
    </div>
  );
};

export default DocOrchestratorPanel;
