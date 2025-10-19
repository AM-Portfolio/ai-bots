import { useState, useRef, useEffect } from 'react';
import { Send, Loader2, Mic, MicOff, Volume2, Sparkles } from 'lucide-react';
import ReactMarkdown from 'react-markdown';
import remarkGfm from 'remark-gfm';
import rehypeHighlight from 'rehype-highlight';
import { apiClient } from '../../services/api';
import type { Provider, ThinkingProcessData } from '../../types/api';
import ThinkingProcess from '../Shared/ThinkingProcess';
import BackendActivityStream from '../Shared/BackendActivityStream';
import { logger } from '../../utils/logger';
import 'highlight.js/styles/github-dark.css';

interface Message {
  role: 'user' | 'assistant';
  content: string;
  provider?: string;
  duration?: number;
}

const LLMTestPanel = () => {
  const [messages, setMessages] = useState<Message[]>([]);
  const [input, setInput] = useState('');
  const [provider, setProvider] = useState<Provider>('together');
  const [model, setModel] = useState('meta-llama/Llama-3.3-70B-Instruct-Turbo');
  const [isLoading, setIsLoading] = useState(false);
  const [showBackendDetails, setShowBackendDetails] = useState(false);
  const [thinkingData, setThinkingData] = useState<ThinkingProcessData | null>(null);
  const [currentConversationId, setCurrentConversationId] = useState<number | null>(null);
  const [streamingMessage, setStreamingMessage] = useState<string | null>(null);
  const [useStreaming, setUseStreaming] = useState(false);
  
  // Voice features
  const [isListening, setIsListening] = useState(false);
  const [voiceEnabled, setVoiceEnabled] = useState(false);
  const recognitionRef = useRef<any>(null);
  const audioRef = useRef<HTMLAudioElement | null>(null);

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
      setThinkingData(null);
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
        duration: msg.duration
      })));
      setCurrentConversationId(conversationId);
      
      logger.chat.info(`Loaded conversation ${conversationId} with ${msgs.length} messages`);
      
      // Get conversation to set provider
      const convResponse = await fetch('/api/chat/conversations');
      const conversations = await convResponse.json();
      const conv = conversations.find((c: any) => c.id === conversationId);
      if (conv) {
        setProvider(conv.provider as Provider);
        logger.chat.debug(`Provider set to ${conv.provider}`);
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
          messages
        })
      });
      
      const result = await response.json();
      if (result.success) {
        setCurrentConversationId(result.conversation_id);
        // Trigger sidebar refresh
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
      logger.voice.info('Stopping voice recognition');
      recognitionRef.current?.stop();
      setIsListening(false);
    } else {
      logger.voice.info('Starting voice recognition');
      recognitionRef.current?.start();
      setIsListening(true);
    }
  };

  const playVoiceResponse = async (text: string) => {
    if (!voiceEnabled) return;
    
    try {
      if (audioRef.current) {
        audioRef.current.pause();
        audioRef.current = null;
      }

      const utterance = new SpeechSynthesisUtterance(text);
      utterance.rate = 1.0;
      utterance.pitch = 1.0;
      utterance.volume = 1.0;
      
      const voices = window.speechSynthesis.getVoices();
      const englishVoice = voices.find(voice => voice.lang.startsWith('en-')) || voices[0];
      if (englishVoice) {
        utterance.voice = englishVoice;
      }
      
      window.speechSynthesis.speak(utterance);
    } catch (error) {
      console.error('Voice playback error:', error);
    }
  };

  const handleSend = async () => {
    if (!input.trim() || isLoading) return;

    const userMessage: Message = { role: 'user', content: input };
    setMessages((prev) => [...prev, userMessage]);
    const messageText = input;
    setInput('');
    setIsLoading(true);
    setThinkingData(null);

    logger.chat.info(`Sending message to ${provider}`, { 
      messageLength: messageText.length, 
      streaming: useStreaming,
      backendDetails: showBackendDetails
    });

    // Use streaming if enabled - set message to trigger BackendActivityStream
    if (useStreaming) {
      logger.chat.debug('Using streaming mode');
      setStreamingMessage(messageText);
      // Don't return - let the component handle the stream
    }

    // Skip normal API call if streaming is active - let BackendActivityStream handle it
    if (useStreaming) {
      // Loading state will be managed by stream callbacks
      return;
    }

    try {
      const startTime = performance.now();
      logger.llm.info(`Calling ${provider} provider with model ${model}`);
      
      // Build conversation history from previous messages (excluding the current user message)
      const conversationHistory = messages.map(msg => ({
        role: msg.role,
        content: msg.content
      }));
      
      logger.chat.debug(`Sending ${conversationHistory.length} previous messages as context`);
      
      const result = await apiClient.testLLM(messageText, provider, showBackendDetails, model, conversationHistory);
      const duration = (performance.now() - startTime) / 1000;
      
      logger.llm.success(`Response received from ${provider}`, { 
        duration: `${duration.toFixed(2)}s`,
        responseLength: result.response?.length || 0
      });
      
      if (result.thinking) {
        setThinkingData(result.thinking);
        logger.chat.debug('Backend thinking data received', { 
          steps: result.thinking.steps?.length || 0 
        });
      }

      if (result.success && result.response) {
        const assistantMessage: Message = {
          role: 'assistant',
          content: result.response,
          provider: result.provider_used || provider,
          duration,
        };
        setMessages((prev) => [...prev, assistantMessage]);
        
        logger.chat.success(`Message completed in ${duration.toFixed(2)}s`);
        setTimeout(() => saveConversation(), 500);
        
        if (voiceEnabled) {
          logger.voice.info('Playing voice response');
          playVoiceResponse(result.response);
        }
      } else {
        logger.chat.error('LLM returned error', { error: result.error });
        const errorMessage: Message = {
          role: 'assistant',
          content: `Error: ${result.error || 'Unknown error occurred'}`,
        };
        setMessages((prev) => [...prev, errorMessage]);
      }
    } catch (error) {
      logger.chat.error('Failed to send message', { 
        error: error instanceof Error ? error.message : String(error) 
      });
      const errorMessage: Message = {
        role: 'assistant',
        content: `Error: ${error instanceof Error ? error.message : 'Failed to connect to API'}`,
      };
      setMessages((prev) => [...prev, errorMessage]);
    } finally {
      setIsLoading(false);
    }
  };

  const handleStreamComplete = (result: any) => {
    setIsLoading(false);
    setStreamingMessage(null);
    
    // Create a summary response based on the pipeline result
    const assistantMessage: Message = {
      role: 'assistant',
      content: `Pipeline completed successfully!\n\n✓ Found ${result.parsed_message?.references_count || 0} references\n✓ Fetched ${result.enriched_context?.context_items || 0} context items\n✓ Executed ${result.tasks?.executed || 0} tasks (${result.tasks?.successful || 0} successful)`,
      provider: provider,
      duration: 0
    };
    setMessages((prev) => [...prev, assistantMessage]);
    setTimeout(() => saveConversation(), 500);
  };

  const handleStreamError = (error: string) => {
    setIsLoading(false);
    setStreamingMessage(null);
    
    const errorMessage: Message = {
      role: 'assistant',
      content: `Error: ${error}`,
    };
    setMessages((prev) => [...prev, errorMessage]);
  };

  return (
    <div className="h-full flex flex-col bg-gradient-to-br from-gray-50 to-blue-50/30">
      <div className="flex-1 overflow-y-auto mb-4 p-6">
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

        <div className="space-y-6 max-w-5xl mx-auto">
          {messages.map((message, index) => (
            <div
              key={index}
              className={`flex ${message.role === 'user' ? 'justify-end' : 'justify-start'}`}
            >
              <div
                className={`max-w-[85%] ${
                  message.role === 'user' 
                    ? 'bg-gradient-to-br from-blue-600 to-blue-700 text-white rounded-2xl rounded-tr-sm shadow-md' 
                    : 'bg-white border border-gray-200 rounded-2xl rounded-tl-sm shadow-sm'
                } p-5 transition-all hover:shadow-lg`}
              >
                {message.role === 'assistant' && (
                  <div className="flex items-center gap-2 mb-3 pb-3 border-b border-gray-100">
                    <div className="w-8 h-8 bg-gradient-to-br from-blue-500 to-purple-600 rounded-lg flex items-center justify-center">
                      <Sparkles className="w-4 h-4 text-white" />
                    </div>
                    <span className="font-semibold text-gray-700">
                      AI Assistant
                    </span>
                    {message.provider && (
                      <span className="text-xs px-2 py-0.5 bg-blue-100 text-blue-700 rounded-full">
                        {message.provider}
                      </span>
                    )}
                    {message.duration && (
                      <span className="text-xs text-gray-400 ml-auto">
                        {message.duration.toFixed(2)}s
                      </span>
                    )}
                  </div>
                )}
                <div className={`prose prose-sm max-w-none ${
                  message.role === 'user' 
                    ? 'prose-invert' 
                    : 'prose-headings:text-gray-900 prose-p:text-gray-700 prose-strong:text-gray-900 prose-code:text-blue-600 prose-code:bg-blue-50 prose-code:px-1 prose-code:py-0.5 prose-code:rounded prose-pre:bg-gray-900 prose-pre:text-gray-100'
                }`}>
                  {message.role === 'assistant' ? (
                    <ReactMarkdown 
                      remarkPlugins={[remarkGfm]}
                      rehypePlugins={[rehypeHighlight as any]}
                    >
                      {message.content}
                    </ReactMarkdown>
                  ) : (
                    <div className="whitespace-pre-wrap">{message.content}</div>
                  )}
                </div>
              </div>
            </div>
          ))}

          {/* Streaming backend activity */}
          {streamingMessage && useStreaming && (
            <BackendActivityStream
              message={streamingMessage}
              templateName="default"
              executeTasks={true}
              onComplete={handleStreamComplete}
              onError={handleStreamError}
            />
          )}

          {/* Traditional thinking process display */}
          {showBackendDetails && !useStreaming && thinkingData && (
            <ThinkingProcess data={thinkingData} title="Backend Processing Steps" />
          )}

          {isLoading && !streamingMessage && (
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
      </div>

      {/* Modern Input Area */}
      <div className="bg-white border-t border-gray-200 shadow-lg p-4">
        <div className="flex space-x-3 mb-3 max-w-5xl mx-auto">
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
              placeholder={isListening ? "🎤 Listening..." : "Ask me anything about your code..."}
              className={`w-full px-4 py-3 pr-12 border-2 rounded-xl focus:ring-2 focus:ring-blue-500 focus:border-blue-500 resize-none transition-all ${
                isListening 
                  ? 'border-red-400 ring-2 ring-red-400/20 bg-red-50' 
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
                  ? 'bg-red-500 text-white hover:bg-red-600 shadow-md' 
                  : 'bg-gray-100 text-gray-600 hover:bg-gray-200'
              }`}
              title={isListening ? "Stop listening" : "Start voice input"}
            >
              {isListening ? (
                <MicOff className="w-4 h-4" />
              ) : (
                <Mic className="w-4 h-4" />
              )}
            </button>
          </div>
          <button
            onClick={handleSend}
            disabled={isLoading || !input.trim()}
            className="bg-gradient-to-br from-blue-600 to-purple-600 text-white px-8 py-3 rounded-xl hover:from-blue-700 hover:to-purple-700 disabled:opacity-50 disabled:cursor-not-allowed flex items-center space-x-2 self-end shadow-md hover:shadow-lg transition-all"
          >
            {isLoading ? (
              <Loader2 className="w-5 h-5 animate-spin" />
            ) : (
              <Send className="w-5 h-5" />
            )}
          </button>
        </div>

        {/* Modern Settings Bar */}
        <div className="flex items-center justify-between pt-3 border-t border-gray-100 max-w-5xl mx-auto">
          <div className="flex items-center space-x-4">
            <div className="flex items-center space-x-2">
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
                className="text-sm border-2 border-gray-200 rounded-lg px-3 py-1.5 focus:ring-2 focus:ring-blue-500 focus:border-blue-500 bg-white hover:border-gray-300 transition-colors"
              >
                <option value="meta-llama/Llama-3.3-70B-Instruct-Turbo">🦙 Llama-3.3-70B</option>
                <option value="deepseek-ai/DeepSeek-R1">🧠 DeepSeek-R1</option>
                <option value="Qwen/Qwen3-Coder-480B-A35B-Instruct-FP8">💻 Qwen3-Coder</option>
                <option value="azure">☁️ GPT-4 (Azure)</option>
              </select>
            </div>

            <label className="flex items-center space-x-2 cursor-pointer">
              <input
                type="checkbox"
                checked={voiceEnabled}
                onChange={(e) => setVoiceEnabled(e.target.checked)}
                className="w-4 h-4 text-primary-600 rounded focus:ring-primary-500"
              />
              <Volume2 className="w-4 h-4 text-gray-600" />
              <span className="text-sm text-gray-700">Voice</span>
            </label>

            <label className="flex items-center space-x-2 cursor-pointer">
              <input
                type="checkbox"
                checked={showBackendDetails}
                onChange={(e) => setShowBackendDetails(e.target.checked)}
                className="w-4 h-4 text-primary-600 rounded focus:ring-primary-500"
              />
              <Sparkles className="w-4 h-4 text-gray-600" />
              <span className="text-sm text-gray-700">Details</span>
            </label>

            {showBackendDetails && (
              <label className="flex items-center space-x-2 cursor-pointer">
                <input
                  type="checkbox"
                  checked={useStreaming}
                  onChange={(e) => setUseStreaming(e.target.checked)}
                  className="w-4 h-4 text-primary-600 rounded focus:ring-primary-500"
                />
                <Loader2 className="w-4 h-4 text-gray-600" />
                <span className="text-sm text-gray-700">Stream</span>
              </label>
            )}
          </div>

          <div className="text-xs text-gray-500">
            {isListening && (
              <span className="flex items-center space-x-1 text-red-600">
                <span className="animate-pulse">🎤</span>
                <span>Listening...</span>
              </span>
            )}
            {voiceEnabled && !isListening && (
              <span className="flex items-center space-x-1 text-blue-600">
                <Volume2 className="w-3 h-3" />
                <span>Voice enabled</span>
              </span>
            )}
          </div>
        </div>
      </div>
    </div>
  );
};

export default LLMTestPanel;
