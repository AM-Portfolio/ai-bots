import { useState } from 'react';
import { Send, Loader2, ChevronDown, ChevronRight, Settings } from 'lucide-react';
import { apiClient } from '../../services/api';
import type { Provider } from '../../types/api';

interface Message {
  role: 'user' | 'assistant';
  content: string;
  provider?: string;
  duration?: number;
}

interface ThinkingStep {
  title: string;
  details: string[];
}

const LLMTestPanel = () => {
  const [messages, setMessages] = useState<Message[]>([]);
  const [input, setInput] = useState('What are some best practices for writing clean Python code?');
  const [provider, setProvider] = useState<Provider>('together');
  const [isLoading, setIsLoading] = useState(false);
  const [showBackendDetails, setShowBackendDetails] = useState(false);
  const [thinkingSteps, setThinkingSteps] = useState<ThinkingStep[]>([]);
  const [expandedSteps, setExpandedSteps] = useState<Set<number>>(new Set());

  const handleSend = async () => {
    if (!input.trim() || isLoading) return;

    const userMessage: Message = { role: 'user', content: input };
    setMessages((prev) => [...prev, userMessage]);
    setInput('');
    setIsLoading(true);
    setThinkingSteps([]);

    if (showBackendDetails) {
      setThinkingSteps([
        {
          title: '🔍 Step 1: Provider Selection',
          details: [
            `Selected Provider: ${provider}`,
            provider === 'together' ? 'Model: Llama-3.3-70B-Instruct-Turbo' : 'Model: GPT-4',
            `Fallback: ${provider === 'together' ? 'Azure OpenAI' : 'Together AI'} (if configured)`,
          ],
        },
        {
          title: '📤 Step 2: Sending API Request',
          details: [
            `Provider: ${provider}`,
            `Prompt Length: ${input.length} characters`,
            'Endpoint: /api/test/llm',
            'Method: POST',
          ],
        },
      ]);
    }

    try {
      const startTime = performance.now();
      const result = await apiClient.testLLM(input, provider);
      const duration = (performance.now() - startTime) / 1000;

      if (showBackendDetails) {
        setThinkingSteps((prev) => [
          ...prev,
          {
            title: '📥 Step 3: API Response Received',
            details: [
              `Response Time: ${duration.toFixed(2)}s`,
              `Success: ${result.success}`,
              result.response ? `Response Length: ${result.response.length} characters` : '',
              result.provider_used ? `Provider Used: ${result.provider_used}` : '',
              result.fallback_used ? '⚠️ Fallback was used' : '',
              result.tokens ? `Token Usage: ${result.tokens} tokens` : '',
            ].filter(Boolean),
          },
        ]);
      }

      if (result.success && result.response) {
        const assistantMessage: Message = {
          role: 'assistant',
          content: result.response,
          provider: result.provider_used || provider,
          duration,
        };
        setMessages((prev) => [...prev, assistantMessage]);
      } else {
        const errorMessage: Message = {
          role: 'assistant',
          content: `Error: ${result.error || 'Unknown error occurred'}`,
        };
        setMessages((prev) => [...prev, errorMessage]);
      }
    } catch (error) {
      const errorMessage: Message = {
        role: 'assistant',
        content: `Error: ${error instanceof Error ? error.message : 'Failed to connect to API'}`,
      };
      setMessages((prev) => [...prev, errorMessage]);
    } finally {
      setIsLoading(false);
    }
  };

  const toggleStep = (index: number) => {
    setExpandedSteps((prev) => {
      const newSet = new Set(prev);
      if (newSet.has(index)) {
        newSet.delete(index);
      } else {
        newSet.add(index);
      }
      return newSet;
    });
  };

  return (
    <div className="space-y-6">
      <div className="card">
        <div className="flex items-center justify-between mb-4">
          <div className="flex items-center space-x-3">
            <Settings className="w-5 h-5 text-gray-600" />
            <h3 className="text-lg font-semibold text-gray-900">Settings</h3>
          </div>
          <label className="flex items-center space-x-2 cursor-pointer">
            <input
              type="checkbox"
              checked={showBackendDetails}
              onChange={(e) => setShowBackendDetails(e.target.checked)}
              className="w-4 h-4 text-primary-600 rounded focus:ring-primary-500"
            />
            <span className="text-sm text-gray-700">Show Backend Details</span>
          </label>
        </div>

        <div className="flex items-center space-x-4">
          <div className="flex-1">
            <label className="block text-sm font-medium text-gray-700 mb-2">
              Provider
            </label>
            <select
              value={provider}
              onChange={(e) => setProvider(e.target.value as Provider)}
              className="input-field"
            >
              <option value="together">Together AI (Llama-3.3-70B)</option>
              <option value="azure">Azure OpenAI (GPT-4)</option>
            </select>
          </div>
        </div>
      </div>

      <div className="card min-h-[500px] flex flex-col">
        <div className="flex-1 overflow-y-auto mb-4 space-y-4">
          {messages.length === 0 && (
            <div className="text-center py-12">
              <div className="w-16 h-16 bg-primary-100 rounded-full mx-auto mb-4 flex items-center justify-center">
                <Send className="w-8 h-8 text-primary-600" />
              </div>
              <h3 className="text-lg font-semibold text-gray-900 mb-2">
                Ready to chat!
              </h3>
              <p className="text-gray-600">
                Send a message to start testing the LLM
              </p>
            </div>
          )}

          {messages.map((message, index) => (
            <div
              key={index}
              className={`flex ${message.role === 'user' ? 'justify-end' : 'justify-start'}`}
            >
              <div
                className={`message-bubble ${
                  message.role === 'user' ? 'message-user' : 'message-assistant'
                }`}
              >
                <div className="flex items-center justify-between mb-1">
                  <span className="font-semibold text-sm">
                    {message.role === 'user' ? 'You' : `🤖 AI Assistant${message.provider ? ` (${message.provider})` : ''}`}
                  </span>
                  {message.duration && (
                    <span className="text-xs text-gray-500 ml-4">
                      {message.duration.toFixed(2)}s
                    </span>
                  )}
                </div>
                <div className="whitespace-pre-wrap">{message.content}</div>
              </div>
            </div>
          ))}

          {isLoading && showBackendDetails && thinkingSteps.length > 0 && (
            <div className="bg-gray-50 rounded-lg p-4 space-y-2">
              <div className="flex items-center space-x-2 text-sm font-medium text-gray-700 mb-3">
                <Loader2 className="w-4 h-4 animate-spin" />
                <span>Processing...</span>
              </div>
              {thinkingSteps.map((step, index) => (
                <div key={index} className="border border-gray-200 rounded-lg overflow-hidden">
                  <button
                    onClick={() => toggleStep(index)}
                    className="w-full flex items-center justify-between p-3 bg-white hover:bg-gray-50 transition-colors"
                  >
                    <span className="text-sm font-medium text-gray-700">{step.title}</span>
                    {expandedSteps.has(index) ? (
                      <ChevronDown className="w-4 h-4 text-gray-500" />
                    ) : (
                      <ChevronRight className="w-4 h-4 text-gray-500" />
                    )}
                  </button>
                  {expandedSteps.has(index) && (
                    <div className="px-3 pb-3 bg-white space-y-1">
                      {step.details.map((detail, detailIndex) => (
                        <p key={detailIndex} className="text-sm text-gray-600">
                          {detail}
                        </p>
                      ))}
                    </div>
                  )}
                </div>
              ))}
            </div>
          )}

          {isLoading && !showBackendDetails && (
            <div className="flex justify-start">
              <div className="message-bubble message-assistant">
                <div className="flex items-center space-x-2">
                  <Loader2 className="w-4 h-4 animate-spin" />
                  <span>Thinking...</span>
                </div>
              </div>
            </div>
          )}
        </div>

        <div className="border-t border-gray-200 pt-4">
          <div className="flex space-x-3">
            <textarea
              value={input}
              onChange={(e) => setInput(e.target.value)}
              onKeyDown={(e) => {
                if (e.key === 'Enter' && !e.shiftKey) {
                  e.preventDefault();
                  handleSend();
                }
              }}
              placeholder="Type your message... (Shift+Enter for new line)"
              className="textarea-field"
              rows={3}
            />
            <button
              onClick={handleSend}
              disabled={isLoading || !input.trim()}
              className="btn-primary flex items-center space-x-2 self-end"
            >
              {isLoading ? (
                <Loader2 className="w-5 h-5 animate-spin" />
              ) : (
                <Send className="w-5 h-5" />
              )}
              <span>Send</span>
            </button>
          </div>
        </div>
      </div>
    </div>
  );
};

export default LLMTestPanel;
