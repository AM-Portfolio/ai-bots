import { useState, useRef, useEffect } from 'react';
import { Send, Loader2, Mic, MicOff, ChevronDown, ChevronUp, Sparkles, ExternalLink, GitBranch, GitPullRequest } from 'lucide-react';
import ReactMarkdown from 'react-markdown';
import remarkGfm from 'remark-gfm';
import rehypeHighlight from 'rehype-highlight';
import { apiClient } from '../../services/api';
import type { Provider, ThinkingProcessData } from '../../types/api';
import { logger } from '../../utils/logger';
import ThinkingProcess from '../Shared/ThinkingProcess';
import ApprovalDialog from '../Shared/ApprovalDialog';
import 'highlight.js/styles/github-dark.css';

interface Message {
  role: 'user' | 'assistant';
  content: string;
  provider?: string;
  duration?: number;
  thinking?: ThinkingProcessData;
  isExpanded?: boolean;
  approvalRequest?: any;
  workflow?: string;
  intent?: any;
  repoContent?: string;
  nextActions?: Array<{
    action: string;
    label: string;
    url?: string;
    repository?: string;
    source_branch?: string;
    target_branch?: string;
  }>;
}

const LLMTestPanel = () => {
  const [messages, setMessages] = useState<Message[]>([]);
  const [input, setInput] = useState('');
  const [provider, setProvider] = useState<Provider>('together');
  const [model, setModel] = useState('meta-llama/Llama-3.3-70B-Instruct-Turbo');
  const [isLoading, setIsLoading] = useState(false);
  const [showBackendDetails, setShowBackendDetails] = useState(false);
  const [currentConversationId, setCurrentConversationId] = useState<number | null>(null);
  const [isApprovingCommit, setIsApprovingCommit] = useState(false);
  
  // Voice features
  const [isListening, setIsListening] = useState(false);
  const [voiceEnabled, setVoiceEnabled] = useState(false);
  const recognitionRef = useRef<any>(null);
  const messagesEndRef = useRef<HTMLDivElement>(null);

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  };

  useEffect(() => {
    scrollToBottom();
  }, [messages]);

  // Listen for sidebar events
  useEffect(() => {
    const handleLoadConversation = async (e: Event) => {
      const customEvent = e as CustomEvent;
      const conversationId = customEvent.detail.conversationId;
      await loadConversation(conversationId);
    };

    const handleClearChat = () => {
      setMessages([]);
      setCurrentConversationId(null);
      setInput('');
    };

    window.addEventListener('loadConversation', handleLoadConversation);
    window.addEventListener('clearChat', handleClearChat);

    return () => {
      window.removeEventListener('loadConversation', handleLoadConversation);
      window.removeEventListener('clearChat', handleClearChat);
    };
  }, []);

  const loadConversation = async (conversationId: number) => {
    await logger.chat.track('Load conversation', async () => {
      const response = await fetch(`/api/chat/conversations/${conversationId}/messages`);
      const msgs = await response.json();
      
      setMessages(msgs.map((msg: any) => ({
        role: msg.role,
        content: msg.content,
        duration: msg.duration,
        isExpanded: false
      })));
      setCurrentConversationId(conversationId);
      
      const convResponse = await fetch('/api/chat/conversations');
      const conversations = await convResponse.json();
      const conv = conversations.find((c: any) => c.id === conversationId);
      if (conv) {
        setProvider(conv.provider as Provider);
      }
    });
  };

  const saveConversation = async () => {
    if (messages.length === 0) return;
    
    try {
      const firstUserMsg = messages.find(m => m.role === 'user');
      const title = firstUserMsg 
        ? firstUserMsg.content.slice(0, 50) + (firstUserMsg.content.length > 50 ? '...' : '')
        : 'New Conversation';
      
      const response = await fetch('/api/chat/conversations', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          conversation_id: currentConversationId,
          title,
          provider,
          messages: messages.map(m => ({ role: m.role, content: m.content, duration: m.duration }))
        })
      });
      
      const result = await response.json();
      if (result.success) {
        setCurrentConversationId(result.conversation_id);
        window.dispatchEvent(new CustomEvent('conversationSaved'));
      }
    } catch (error) {
      console.error('Failed to save conversation:', error);
    }
  };

  // Initialize speech recognition
  useEffect(() => {
    if (typeof window !== 'undefined' && ('webkitSpeechRecognition' in window || 'SpeechRecognition' in window)) {
      const SpeechRecognition = (window as any).webkitSpeechRecognition || (window as any).SpeechRecognition;
      recognitionRef.current = new SpeechRecognition();
      recognitionRef.current.continuous = false;
      recognitionRef.current.interimResults = false;
      recognitionRef.current.lang = 'en-US';

      recognitionRef.current.onresult = (event: any) => {
        const transcript = event.results[0][0].transcript;
        setInput(transcript);
        setIsListening(false);
      };

      recognitionRef.current.onerror = () => {
        setIsListening(false);
      };

      recognitionRef.current.onend = () => {
        setIsListening(false);
      };
    }
  }, []);

  const toggleVoiceInput = () => {
    if (isListening) {
      recognitionRef.current?.stop();
      setIsListening(false);
    } else {
      recognitionRef.current?.start();
      setIsListening(true);
    }
  };

  const playVoiceResponse = async (text: string) => {
    if (!voiceEnabled) return;
    
    const utterance = new SpeechSynthesisUtterance(text);
    const voices = window.speechSynthesis.getVoices();
    const englishVoice = voices.find(voice => voice.lang.startsWith('en-')) || voices[0];
    if (englishVoice) {
      utterance.voice = englishVoice;
    }
    window.speechSynthesis.speak(utterance);
  };

  const extractOverview = (content: string): string => {
    // Extract first paragraph or first 200 characters as overview
    const lines = content.split('\n').filter(line => line.trim());
    const firstParagraph = lines.slice(0, 3).join('\n');
    return firstParagraph.length > 250 ? firstParagraph.substring(0, 247) + '...' : firstParagraph;
  };

  const toggleMessageExpansion = (index: number) => {
    setMessages(prev => prev.map((msg, i) => 
      i === index ? { ...msg, isExpanded: !msg.isExpanded } : msg
    ));
  };

  const detectCommitIntent = (message: string): boolean => {
    const lowerMessage = message.toLowerCase();
    const commitKeywords = ['commit', 'push', 'create pr', 'pull request', 'merge', 'branch'];
    return commitKeywords.some(keyword => lowerMessage.includes(keyword));
  };

  const extractRepository = (message: string): string | undefined => {
    const repoPatterns = [
      /repo(?:sitory)?\s+([a-zA-Z0-9_-]+\/[a-zA-Z0-9_-]+)/i,
      /in\s+([a-zA-Z0-9_-]+\/[a-zA-Z0-9_-]+)/i,
      /to\s+([a-zA-Z0-9_-]+\/[a-zA-Z0-9_-]+)/i,
    ];
    for (const pattern of repoPatterns) {
      const match = message.match(pattern);
      if (match) return match[1];
    }
    return undefined;
  };

  const handleApprove = async (messageIndex: number) => {
    const message = messages[messageIndex];
    if (!message.approvalRequest) return;

    setIsApprovingCommit(true);
    try {
      const result = await apiClient.approveCommit(message.approvalRequest.id, true);
      
      if (result.success && result.operation_result) {
        const opResult = result.operation_result;
        let responseMessage = `## ✅ Operation Completed Successfully!\n\n`;
        
        if (opResult.repository) {
          responseMessage += `**Repository**: \`${opResult.repository}\`\n`;
        }
        if (opResult.branch) {
          responseMessage += `**Branch**: \`${opResult.branch}\`\n`;
        }
        if (opResult.commit_sha) {
          responseMessage += `**Commit**: \`${opResult.commit_sha.substring(0, 7)}\`\n`;
        }
        
        const assistantMessage: Message = {
          role: 'assistant',
          content: responseMessage,
          isExpanded: true,
          nextActions: opResult.next_actions || []
        };
        setMessages((prev) => [...prev, assistantMessage]);
      } else {
        throw new Error(result.operation_result?.error || 'Operation failed');
      }
    } catch (error) {
      const errorMessage: Message = {
        role: 'assistant',
        content: `❌ Operation failed: ${error instanceof Error ? error.message : 'Unknown error'}`,
        isExpanded: true
      };
      setMessages((prev) => [...prev, errorMessage]);
    } finally {
      setIsApprovingCommit(false);
    }
  };

  const handleReject = async (messageIndex: number) => {
    const message = messages[messageIndex];
    if (!message.approvalRequest) return;

    setIsApprovingCommit(true);
    try {
      await apiClient.approveCommit(message.approvalRequest.id, false, undefined, 'User rejected');
      const assistantMessage: Message = {
        role: 'assistant',
        content: '❌ Operation rejected by user.',
        isExpanded: true
      };
      setMessages((prev) => [...prev, assistantMessage]);
    } catch (error) {
      const errorMessage: Message = {
        role: 'assistant',
        content: `Error rejecting operation: ${error instanceof Error ? error.message : 'Unknown error'}`,
        isExpanded: true
      };
      setMessages((prev) => [...prev, errorMessage]);
    } finally {
      setIsApprovingCommit(false);
    }
  };

  const handleCommitWorkflow = async (userMessage: string) => {
    try {
      const repository = extractRepository(userMessage);
      
      // Step 1: Fetch GitHub content first using orchestrator
      const fetchMessage: Message = {
        role: 'assistant',
        content: '🔍 Fetching repository content...',
        isExpanded: true
      };
      setMessages((prev) => [...prev, fetchMessage]);
      
      const repoQuery = repository 
        ? `Get content from repository ${repository}` 
        : userMessage;
      const contentResult = await apiClient.testLLM(repoQuery, provider, false, model);
      
      if (!contentResult.success || !contentResult.response) {
        throw new Error('Failed to fetch repository content');
      }
      
      // Step 2: Parse commit intent with fetched content
      const result = await apiClient.parseCommitIntent(
        userMessage, 
        repository, 
        undefined, 
        { repo_content: contentResult.response }
      );
      
      if (result.success && result.approval_request) {
        const assistantMessage: Message = {
          role: 'assistant',
          content: '',
          approvalRequest: result.approval_request,
          workflow: result.workflow,
          intent: result.intent,
          repoContent: contentResult.response,
          isExpanded: true
        };
        setMessages((prev) => [...prev, assistantMessage]);
      } else {
        throw new Error('Failed to parse commit intent');
      }
    } catch (error) {
      const errorMessage: Message = {
        role: 'assistant',
        content: `Error processing commit request: ${error instanceof Error ? error.message : 'Unknown error'}`,
        isExpanded: true
      };
      setMessages((prev) => [...prev, errorMessage]);
    }
  };

  const handleSend = async () => {
    if (!input.trim() || isLoading) return;

    const userMessage: Message = { role: 'user', content: input.trim(), isExpanded: true };
    setMessages((prev) => [...prev, userMessage]);
    const currentInput = input.trim();
    setInput('');
    setIsLoading(true);

    await logger.llm.track('LLM query', async () => {
      try {
        // Check if this is a commit/PR intent
        if (detectCommitIntent(currentInput)) {
          await handleCommitWorkflow(currentInput);
          setIsLoading(false);
          return;
        }

        // Regular LLM query
        const result = await apiClient.testLLM(currentInput, provider, showBackendDetails, model);
        
        if (result.success && result.response) {
          const assistantMessage: Message = {
            role: 'assistant',
            content: result.response,
            provider: result.provider_used,
            thinking: result.thinking,
            isExpanded: false
          };
          setMessages((prev) => [...prev, assistantMessage]);
          await saveConversation();
          await playVoiceResponse(result.response);
        } else {
          const errorMessage: Message = {
            role: 'assistant',
            content: `Error: ${result.error || 'Unknown error occurred'}`,
            isExpanded: true
          };
          setMessages((prev) => [...prev, errorMessage]);
        }
      } catch (error) {
        const errorMessage: Message = {
          role: 'assistant',
          content: `Error: ${error instanceof Error ? error.message : 'Failed to connect to API'}`,
          isExpanded: true
        };
        setMessages((prev) => [...prev, errorMessage]);
      } finally {
        setIsLoading(false);
      }
    });
  };

  return (
    <div className="h-full flex flex-col bg-gradient-to-br from-slate-50 via-white to-blue-50/30">
      {/* Messages Area */}
      <div className="flex-1 overflow-y-auto px-6 py-6">
        {messages.length === 0 && (
          <div className="text-center py-20">
            <div className="w-20 h-20 bg-gradient-to-br from-blue-500 to-purple-600 rounded-2xl mx-auto mb-6 flex items-center justify-center shadow-lg">
              <Sparkles className="w-10 h-10 text-white" />
            </div>
            <h3 className="text-2xl font-bold bg-gradient-to-r from-blue-600 to-purple-600 bg-clip-text text-transparent mb-3">
              AI Development Assistant
            </h3>
            <p className="text-gray-600 text-lg">
              Ask me anything about your codebase
            </p>
          </div>
        )}

        <div className="space-y-4 max-w-4xl mx-auto">
          {messages.map((message, index) => (
            <div key={index} className={`flex ${message.role === 'user' ? 'justify-end' : 'justify-start'}`}>
              {message.role === 'user' ? (
                <div className="bg-gradient-to-br from-blue-600 to-blue-700 text-white rounded-2xl rounded-tr-md px-4 py-3 max-w-[80%] shadow-sm">
                  <div className="prose prose-sm prose-invert max-w-none">
                    {message.content}
                  </div>
                </div>
              ) : (
                <div className="bg-white rounded-2xl rounded-tl-md shadow-sm border border-gray-100 max-w-[85%] overflow-hidden">
                  {/* AI Response Header */}
                  <div className="px-4 py-3 border-b border-gray-100 flex items-center justify-between bg-gradient-to-r from-blue-50 to-purple-50">
                    <div className="flex items-center gap-2">
                      <div className="w-7 h-7 bg-gradient-to-br from-blue-500 to-purple-600 rounded-lg flex items-center justify-center">
                        <Sparkles className="w-4 h-4 text-white" />
                      </div>
                      <span className="font-semibold text-sm text-gray-800">AI Assistant</span>
                      {message.provider && (
                        <span className="text-xs px-2 py-0.5 bg-white border border-blue-200 text-blue-700 rounded-full">
                          {message.provider}
                        </span>
                      )}
                    </div>
                    <div className="flex items-center gap-2">
                      {message.duration && (
                        <span className="text-xs text-gray-500">{message.duration.toFixed(2)}s</span>
                      )}
                      <button
                        onClick={() => toggleMessageExpansion(index)}
                        className="p-1 hover:bg-white rounded-lg transition-colors"
                        title={message.isExpanded ? 'Show overview' : 'Show full response'}
                      >
                        {message.isExpanded ? (
                          <ChevronUp className="w-4 h-4 text-gray-600" />
                        ) : (
                          <ChevronDown className="w-4 h-4 text-gray-600" />
                        )}
                      </button>
                    </div>
                  </div>

                  {/* Response Content */}
                  <div className="px-4 py-4">
                    {message.approvalRequest ? (
                      <ApprovalDialog
                        approvalRequest={message.approvalRequest}
                        workflow={message.workflow || 'unknown'}
                        intent={message.intent || {}}
                        onApprove={() => handleApprove(index)}
                        onReject={() => handleReject(index)}
                        isLoading={isApprovingCommit}
                      />
                    ) : (
                      <div className="prose prose-sm max-w-none prose-headings:text-gray-900 prose-p:text-gray-700 prose-strong:text-gray-900 prose-code:text-blue-600 prose-code:bg-blue-50 prose-code:px-1.5 prose-code:py-0.5 prose-code:rounded prose-pre:bg-gray-900 prose-pre:text-gray-100 prose-a:text-blue-600">
                        <ReactMarkdown 
                          remarkPlugins={[remarkGfm]}
                          rehypePlugins={[rehypeHighlight as any]}
                        >
                          {message.isExpanded ? message.content : extractOverview(message.content)}
                        </ReactMarkdown>
                        {!message.isExpanded && message.content && (
                          <button
                            onClick={() => toggleMessageExpansion(index)}
                            className="mt-2 text-sm text-blue-600 hover:text-blue-700 font-medium"
                          >
                            Read full response →
                          </button>
                        )}
                        
                        {/* Next Actions Buttons */}
                        {message.nextActions && message.nextActions.length > 0 && (
                          <div className="mt-4 pt-4 border-t border-gray-200">
                            <p className="text-sm font-semibold text-gray-700 mb-2">🎯 Next Actions:</p>
                            <div className="flex flex-wrap gap-2">
                              {message.nextActions.map((action, idx) => {
                                const Icon = action.action === 'view_commit' ? ExternalLink : action.action === 'view_branch' ? GitBranch : GitPullRequest;
                                return (
                                  <a
                                    key={idx}
                                    href={action.url}
                                    target="_blank"
                                    rel="noopener noreferrer"
                                    className="inline-flex items-center gap-2 px-4 py-2 bg-gradient-to-r from-blue-500 to-blue-600 text-white text-sm font-medium rounded-lg hover:from-blue-600 hover:to-blue-700 transition-all shadow-sm hover:shadow-md"
                                  >
                                    <Icon className="w-4 h-4" />
                                    {action.label}
                                  </a>
                                );
                              })}
                            </div>
                          </div>
                        )}
                      </div>
                    )}
                  </div>

                  {/* Backend Execution Steps / Thinking Process */}
                  {message.thinking && showBackendDetails && (
                    <div className="px-4 pb-4">
                      <ThinkingProcess 
                        data={message.thinking} 
                        title="Backend Execution Steps"
                      />
                    </div>
                  )}
                </div>
              )}
            </div>
          ))}

          {/* Loading indicator */}
          {isLoading && (
            <div className="flex justify-start">
              <div className="bg-white rounded-2xl rounded-tl-md shadow-sm border border-gray-100 px-4 py-3 min-w-[200px]">
                <div className="flex items-center gap-3">
                  <div className="flex gap-1">
                    <div className="w-2 h-2 bg-blue-500 rounded-full animate-bounce"></div>
                    <div className="w-2 h-2 bg-blue-500 rounded-full animate-bounce" style={{ animationDelay: '0.1s' }}></div>
                    <div className="w-2 h-2 bg-blue-500 rounded-full animate-bounce" style={{ animationDelay: '0.2s' }}></div>
                  </div>
                  <span className="text-sm text-gray-600">Thinking...</span>
                </div>
              </div>
            </div>
          )}
          
          <div ref={messagesEndRef} />
        </div>
      </div>

      {/* Compact Input Area with Inline Settings */}
      <div className="bg-white border-t border-gray-200 shadow-lg px-6 py-4">
        <div className="max-w-4xl mx-auto space-y-3">
          {/* Settings Row */}
          <div className="flex items-center gap-4 px-1">
            <div className="flex items-center gap-2 text-sm text-gray-600">
              <Sparkles className="w-4 h-4 text-blue-600" />
              <span className="font-medium">Model:</span>
            </div>
            
            <select
              value={provider === 'together' ? model : provider}
              onChange={(e) => {
                const value = e.target.value;
                if (value === 'azure') {
                  setProvider('azure');
                } else {
                  setProvider('together');
                  setModel(value);
                }
              }}
              className="text-xs px-2 py-1 border border-gray-300 rounded-md bg-white hover:border-gray-400 transition-colors focus:outline-none focus:ring-2 focus:ring-blue-500"
            >
              <option value="meta-llama/Llama-3.3-70B-Instruct-Turbo">🦙 Llama 3.3 70B</option>
              <option value="deepseek-ai/DeepSeek-R1">🧠 DeepSeek-R1</option>
              <option value="Qwen/Qwen3-Coder-480B-A35B-Instruct-FP8">💻 Qwen3 Coder</option>
              <option value="azure">☁️ GPT-4</option>
            </select>

            <label className="flex items-center gap-1.5 cursor-pointer text-xs text-gray-700">
              <input
                type="checkbox"
                checked={showBackendDetails}
                onChange={(e) => setShowBackendDetails(e.target.checked)}
                className="w-3.5 h-3.5 rounded"
              />
              Show Thinking
            </label>

            <label className="flex items-center gap-1.5 cursor-pointer text-xs text-gray-700">
              <input
                type="checkbox"
                checked={voiceEnabled}
                onChange={(e) => setVoiceEnabled(e.target.checked)}
                className="w-3.5 h-3.5 rounded"
              />
              Voice
            </label>
          </div>

          {/* Input Row */}
          <div className="flex gap-3">
            <div className="flex-1 relative">
              <textarea
                value={input}
                onChange={(e) => setInput(e.target.value)}
                onKeyDown={(e) => {
                  if (e.key === 'Enter' && !e.shiftKey) {
                    e.preventDefault();
                    handleSend();
                  }
                }}
                placeholder={isListening ? "🎤 Listening..." : "Ask me anything..."}
                className={`w-full px-4 py-3 pr-12 border-2 rounded-xl resize-none transition-all focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-blue-500 ${
                  isListening 
                    ? 'border-red-400 bg-red-50' 
                    : 'border-gray-200 hover:border-gray-300'
                }`}
                rows={2}
                disabled={isListening}
              />
              <button
                onClick={toggleVoiceInput}
                disabled={isLoading}
                className={`absolute right-2 top-2 p-2 rounded-lg transition-all ${
                  isListening 
                    ? 'bg-red-500 text-white' 
                    : 'bg-gray-100 text-gray-600 hover:bg-gray-200'
                }`}
              >
                {isListening ? <MicOff className="w-4 h-4" /> : <Mic className="w-4 h-4" />}
              </button>
            </div>
            <button
              onClick={handleSend}
              disabled={isLoading || !input.trim()}
              className="bg-gradient-to-br from-blue-600 to-purple-600 text-white px-8 py-3 rounded-xl hover:from-blue-700 hover:to-purple-700 disabled:opacity-50 disabled:cursor-not-allowed shadow-md hover:shadow-lg transition-all flex items-center gap-2"
            >
              {isLoading ? <Loader2 className="w-5 h-5 animate-spin" /> : <Send className="w-5 h-5" />}
            </button>
          </div>
        </div>
      </div>
    </div>
  );
};

export default LLMTestPanel;
