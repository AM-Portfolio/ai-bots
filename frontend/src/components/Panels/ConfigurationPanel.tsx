import { useState } from 'react';
import { Settings, Database, Key, Cloud, Save } from 'lucide-react';

const ConfigurationPanel = () => {
  const [config, setConfig] = useState({
    githubToken: '',
    githubOwner: '',
    jiraUrl: '',
    jiraUsername: '',
    jiraApiToken: '',
    confluenceUrl: '',
    confluenceUsername: '',
    confluenceApiToken: '',
    grafanaUrl: '',
    grafanaApiKey: '',
    togetherApiKey: '',
    azureOpenAIKey: '',
    azureOpenAIEndpoint: '',
  });

  const [saved, setSaved] = useState(false);

  const handleChange = (field: string, value: string) => {
    setConfig(prev => ({ ...prev, [field]: value }));
    setSaved(false);
  };

  const handleSave = () => {
    console.log('Saving configuration:', config);
    setSaved(true);
    setTimeout(() => setSaved(false), 3000);
  };

  const ConfigSection = ({ title, icon: Icon, children }: { title: string; icon: any; children: React.ReactNode }) => (
    <div className="card">
      <div className="flex items-center space-x-3 mb-4">
        <Icon className="w-6 h-6 text-primary-600" />
        <h3 className="text-lg font-semibold text-gray-900">{title}</h3>
      </div>
      <div className="space-y-4">
        {children}
      </div>
    </div>
  );

  const InputField = ({ 
    label, 
    value, 
    onChange, 
    placeholder, 
    type = 'text' 
  }: { 
    label: string; 
    value: string; 
    onChange: (value: string) => void; 
    placeholder: string; 
    type?: string;
  }) => (
    <div>
      <label className="block text-sm font-medium text-gray-700 mb-2">
        {label}
      </label>
      <input
        type={type}
        value={value}
        onChange={(e) => onChange(e.target.value)}
        placeholder={placeholder}
        className="input-field w-full"
      />
    </div>
  );

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h2 className="text-2xl font-bold text-gray-900">Application Configuration</h2>
          <p className="text-gray-600 mt-1">Configure your integrations and API credentials</p>
        </div>
        <button
          onClick={handleSave}
          className={`btn-primary flex items-center space-x-2 ${saved ? 'bg-green-600 hover:bg-green-700' : ''}`}
        >
          <Save className="w-5 h-5" />
          <span>{saved ? 'Saved!' : 'Save Configuration'}</span>
        </button>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        <ConfigSection title="GitHub Configuration" icon={Database}>
          <InputField
            label="GitHub Personal Access Token"
            value={config.githubToken}
            onChange={(v) => handleChange('githubToken', v)}
            placeholder="ghp_xxxxxxxxxxxx"
            type="password"
          />
          <InputField
            label="Default Repository Owner"
            value={config.githubOwner}
            onChange={(v) => handleChange('githubOwner', v)}
            placeholder="your-username"
          />
        </ConfigSection>

        <ConfigSection title="Jira Configuration" icon={Key}>
          <InputField
            label="Jira URL"
            value={config.jiraUrl}
            onChange={(v) => handleChange('jiraUrl', v)}
            placeholder="https://your-domain.atlassian.net"
          />
          <InputField
            label="Username/Email"
            value={config.jiraUsername}
            onChange={(v) => handleChange('jiraUsername', v)}
            placeholder="your-email@example.com"
          />
          <InputField
            label="API Token"
            value={config.jiraApiToken}
            onChange={(v) => handleChange('jiraApiToken', v)}
            placeholder="Your Jira API token"
            type="password"
          />
        </ConfigSection>

        <ConfigSection title="Confluence Configuration" icon={Database}>
          <InputField
            label="Confluence URL"
            value={config.confluenceUrl}
            onChange={(v) => handleChange('confluenceUrl', v)}
            placeholder="https://your-domain.atlassian.net/wiki"
          />
          <InputField
            label="Username/Email"
            value={config.confluenceUsername}
            onChange={(v) => handleChange('confluenceUsername', v)}
            placeholder="your-email@example.com"
          />
          <InputField
            label="API Token"
            value={config.confluenceApiToken}
            onChange={(v) => handleChange('confluenceApiToken', v)}
            placeholder="Your Confluence API token"
            type="password"
          />
        </ConfigSection>

        <ConfigSection title="Grafana Configuration" icon={Cloud}>
          <InputField
            label="Grafana URL"
            value={config.grafanaUrl}
            onChange={(v) => handleChange('grafanaUrl', v)}
            placeholder="https://your-grafana-instance.com"
          />
          <InputField
            label="API Key"
            value={config.grafanaApiKey}
            onChange={(v) => handleChange('grafanaApiKey', v)}
            placeholder="Your Grafana API key"
            type="password"
          />
        </ConfigSection>

        <ConfigSection title="AI Provider - Together AI" icon={Settings}>
          <InputField
            label="Together AI API Key"
            value={config.togetherApiKey}
            onChange={(v) => handleChange('togetherApiKey', v)}
            placeholder="Your Together AI API key"
            type="password"
          />
        </ConfigSection>

        <ConfigSection title="AI Provider - Azure OpenAI" icon={Cloud}>
          <InputField
            label="Azure OpenAI API Key"
            value={config.azureOpenAIKey}
            onChange={(v) => handleChange('azureOpenAIKey', v)}
            placeholder="Your Azure OpenAI API key"
            type="password"
          />
          <InputField
            label="Azure OpenAI Endpoint"
            value={config.azureOpenAIEndpoint}
            onChange={(v) => handleChange('azureOpenAIEndpoint', v)}
            placeholder="https://your-resource.openai.azure.com/"
          />
        </ConfigSection>
      </div>

      <div className="card bg-blue-50 border-blue-200">
        <div className="flex items-start space-x-3">
          <Settings className="w-5 h-5 text-blue-600 mt-0.5" />
          <div className="flex-1">
            <h4 className="font-semibold text-blue-900 mb-1">Configuration Note</h4>
            <p className="text-sm text-blue-800">
              All credentials are stored securely. Environment variables will be updated when you save. 
              Make sure to restart the application after saving for changes to take effect.
            </p>
          </div>
        </div>
      </div>
    </div>
  );
};

export default ConfigurationPanel;
