import { useState, useEffect } from 'react';
import { Settings, Save, Cloud, Mic, MessageSquare, CheckCircle, XCircle } from 'lucide-react';
import { logger } from '../../utils/logger';

interface ProviderStatus {
  provider: string;
  available: boolean;
  capabilities: string[];
}

interface ProviderConfig {
  stt_provider: string;
  chat_provider: string;
  tts_provider: string;
}

const ProviderSettings = () => {
  const [isOpen, setIsOpen] = useState(false);
  const [config, setConfig] = useState<ProviderConfig>({
    stt_provider: 'azure',
    chat_provider: 'together',
    tts_provider: 'openai'
  });
  const [providers, setProviders] = useState<ProviderStatus[]>([]);
  const [isSaving, setIsSaving] = useState(false);
  const [saveStatus, setSaveStatus] = useState<'idle' | 'success' | 'error'>('idle');
  const [errorMessage, setErrorMessage] = useState<string>('');

  useEffect(() => {
    fetchProviders();
    fetchConfig();
  }, []);

  const fetchProviders = async () => {
    try {
      const response = await fetch('/api/ai/providers');
      const data = await response.json();
      setProviders(data.providers || []);
      logger.settings.info('Fetched available providers', data);
    } catch (error) {
      logger.settings.error('Failed to fetch providers', { error });
    }
  };

  const fetchConfig = async () => {
    try {
      const response = await fetch('/api/ai/config');
      if (response.ok) {
        const data = await response.json();
        setConfig(data);
        logger.settings.info('Fetched provider config', data);
      }
    } catch (error) {
      logger.settings.warn('Failed to fetch config, using defaults', { error });
    }
  };

  const handleSave = async () => {
    setIsSaving(true);
    setSaveStatus('idle');
    setErrorMessage('');
    
    try {
      const response = await fetch('/api/ai/config', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(config)
      });

      if (response.ok) {
        setSaveStatus('success');
        logger.settings.info('Saved provider configuration', config);
        setTimeout(() => setSaveStatus('idle'), 3000);
      } else {
        const errorData = await response.json();
        const errorMsg = errorData.detail?.details?.join(', ') || errorData.detail?.error || 'Failed to save configuration';
        setErrorMessage(errorMsg);
        setSaveStatus('error');
        logger.settings.error('Failed to save configuration', { error: errorMsg });
      }
    } catch (error) {
      setSaveStatus('error');
      setErrorMessage('Network error: Could not connect to server');
      logger.settings.error('Failed to save configuration', { error });
    } finally {
      setIsSaving(false);
    }
  };

  const getProviderOptions = (capability: 'stt' | 'chat' | 'tts') => {
    const capabilityMap = {
      stt: 'speech_to_text',
      chat: 'llm_chat',
      tts: 'text_to_speech'
    };
    
    return providers
      .filter(p => p.capabilities.includes(capabilityMap[capability]))
      .map(p => p.provider);
  };

  const ProviderSelect = ({ 
    label, 
    icon: Icon, 
    value, 
    onChange, 
    capability 
  }: { 
    label: string; 
    icon: any; 
    value: string; 
    onChange: (value: string) => void;
    capability: 'stt' | 'chat' | 'tts';
  }) => {
    const options = getProviderOptions(capability);
    
    return (
      <div className="flex items-center space-x-3">
        <Icon className="w-5 h-5 text-gray-500 flex-shrink-0" />
        <div className="flex-1">
          <label className="block text-sm font-medium text-gray-700 mb-1">
            {label}
          </label>
          <select
            value={value}
            onChange={(e) => onChange(e.target.value)}
            className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500 text-sm"
          >
            {options.length === 0 && (
              <option value="">No providers available</option>
            )}
            {options.map(provider => (
              <option key={provider} value={provider}>
                {provider.charAt(0).toUpperCase() + provider.slice(1)}
              </option>
            ))}
          </select>
        </div>
      </div>
    );
  };

  if (!isOpen) {
    return (
      <button
        onClick={() => setIsOpen(true)}
        className="inline-flex items-center space-x-2 px-3 py-2 text-sm font-medium text-gray-700 bg-white border border-gray-300 rounded-lg hover:bg-gray-50 transition-colors"
      >
        <Settings className="w-4 h-4" />
        <span>Provider Settings</span>
      </button>
    );
  }

  return (
    <div className="bg-white border border-gray-200 rounded-lg p-4 shadow-sm">
      <div className="flex items-center justify-between mb-4">
        <div className="flex items-center space-x-2">
          <Cloud className="w-5 h-5 text-blue-600" />
          <h3 className="text-sm font-semibold text-gray-900">Backend Provider Configuration</h3>
        </div>
        <button
          onClick={() => setIsOpen(false)}
          className="text-gray-400 hover:text-gray-600"
        >
          ×
        </button>
      </div>

      <div className="space-y-3 mb-4">
        <ProviderSelect
          label="Speech-to-Text Provider"
          icon={Mic}
          value={config.stt_provider}
          onChange={(v) => setConfig({ ...config, stt_provider: v })}
          capability="stt"
        />
        
        <ProviderSelect
          label="Chat Completion Provider"
          icon={MessageSquare}
          value={config.chat_provider}
          onChange={(v) => setConfig({ ...config, chat_provider: v })}
          capability="chat"
        />
        
        <ProviderSelect
          label="Text-to-Speech Provider"
          icon={Mic}
          value={config.tts_provider}
          onChange={(v) => setConfig({ ...config, tts_provider: v })}
          capability="tts"
        />
      </div>

      <div className="flex items-center justify-between pt-3 border-t border-gray-200">
        <div className="text-xs text-gray-500">
          {providers.length} providers available
        </div>
        
        <div className="flex items-center space-x-2">
          {saveStatus === 'success' && (
            <span className="flex items-center space-x-1 text-xs text-green-600">
              <CheckCircle className="w-4 h-4" />
              <span>Saved!</span>
            </span>
          )}
          {saveStatus === 'error' && (
            <span className="flex items-center space-x-1 text-xs text-red-600">
              <XCircle className="w-4 h-4" />
              <span>Failed</span>
            </span>
          )}
          
          <button
            onClick={handleSave}
            disabled={isSaving}
            className="inline-flex items-center space-x-2 px-3 py-1.5 text-sm font-medium text-white bg-blue-600 rounded-lg hover:bg-blue-700 disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
          >
            {isSaving ? (
              <>
                <div className="w-4 h-4 border-2 border-white border-t-transparent rounded-full animate-spin" />
                <span>Saving...</span>
              </>
            ) : (
              <>
                <Save className="w-4 h-4" />
                <span>Save</span>
              </>
            )}
          </button>
        </div>
      </div>

      {errorMessage && (
        <div className="mt-3 p-2 bg-red-50 border border-red-200 rounded text-xs text-red-800">
          <strong>Error:</strong> {errorMessage}
        </div>
      )}

      <div className="mt-3 p-2 bg-blue-50 border border-blue-200 rounded text-xs text-blue-800">
        <strong>Note:</strong> Backend will use these providers for all AI requests. Changes take effect immediately.
      </div>
    </div>
  );
};

export default ProviderSettings;
