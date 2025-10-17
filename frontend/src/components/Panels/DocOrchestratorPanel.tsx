import { useState } from 'react';
import { FileText, Loader2, CheckCircle, AlertCircle } from 'lucide-react';
import { apiClient } from '../../services/api';

interface Step {
  name: string;
  status: 'pending' | 'running' | 'complete' | 'error';
  message?: string;
}

const DocOrchestratorPanel = () => {
  const [prompt, setPrompt] = useState('Document the authentication module in the project');
  const [repository, setRepository] = useState('owner/repo');
  const [confluenceSpace, setConfluenceSpace] = useState('');
  const [jiraProject, setJiraProject] = useState('');
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
        confluence_space: confluenceSpace || undefined,
        jira_project: jiraProject || undefined,
      });

      const updateStep = (index: number, status: 'complete' | 'error', message?: string) => {
        setSteps((prev) =>
          prev.map((step, i) =>
            i === index ? { ...step, status, message } : step
          )
        );
      };

      if (response.github_analysis) {
        updateStep(0, 'complete', 'Repository analyzed successfully');
        updateStep(1, 'running');
      }

      if (response.documentation) {
        updateStep(1, 'complete', 'Documentation generated');
        updateStep(2, 'running');
      }

      if (response.commit) {
        updateStep(2, 'complete', `Committed: ${response.commit.sha?.substring(0, 7)}`);
        updateStep(3, 'running');
      }

      if (response.confluence_page) {
        updateStep(3, 'complete', `Page: ${response.confluence_page.title}`);
        updateStep(4, 'running');
      }

      if (response.jira_ticket) {
        updateStep(4, 'complete', `Ticket: ${response.jira_ticket.key}`);
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

          <div className="grid grid-cols-2 gap-4">
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">
                Confluence Space (optional)
              </label>
              <input
                type="text"
                value={confluenceSpace}
                onChange={(e) => setConfluenceSpace(e.target.value)}
                placeholder="SPACE-KEY"
                className="input-field"
              />
            </div>

            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">
                Jira Project (optional)
              </label>
              <input
                type="text"
                value={jiraProject}
                onChange={(e) => setJiraProject(e.target.value)}
                placeholder="PROJECT-KEY"
                className="input-field"
              />
            </div>
          </div>

          <button
            onClick={handleOrchestrate}
            disabled={isRunning || !prompt.trim() || !repository.trim()}
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
          <div className="flex items-center space-x-3 mb-3">
            <CheckCircle className="w-6 h-6 text-green-600" />
            <h3 className="text-lg font-semibold text-green-900">
              Documentation Workflow Complete!
            </h3>
          </div>
          <p className="text-green-800">
            All steps completed successfully. Documentation has been generated, committed, and
            published.
          </p>
        </div>
      )}
    </div>
  );
};

export default DocOrchestratorPanel;
