import { useState, useRef, useEffect } from 'react';
import { Send, Loader2, Mic, MicOff, Volume2, Sparkles } from 'lucide-react';
import { apiClient } from '../../services/api';
import type { Provider, ThinkingProcessData } from '../../types/api';
import ThinkingProcess from '../Shared/ThinkingProcess';
import BackendActivityStream from '../Shared/BackendActivityStream';
import { logger } from '../../utils/logger';

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
      logger.llm.info(`Calling ${provider} provider`);
      
      const result = await apiClient.testLLM(messageText, provider, showBackendDetails);
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
    <div className="h-full flex flex-col">
      <div className="flex-1 card overflow-y-auto mb-4 p-6">
        {messages.length === 0 && (
          <div className="text-center py-20">
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

        <div className="space-y-4">
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

      {/* Compact Input Area with Settings */}
      <div className="card p-4">
        <div className="flex space-x-3 mb-3">
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
              placeholder={isListening ? "Listening..." : "Message AI Assistant..."}
              className={`w-full px-4 py-3 pr-12 border border-gray-300 rounded-lg focus:ring-2 focus:ring-primary-500 focus:border-transparent resize-none ${isListening ? 'ring-2 ring-red-500' : ''}`}
              rows={2}
              disabled={isListening}
            />
            <button
              onClick={toggleVoiceInput}
              disabled={isLoading}
              className={`absolute right-2 top-2 p-2 rounded-lg transition-colors ${
                isListening 
                  ? 'bg-red-500 text-white hover:bg-red-600' 
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
            className="btn-primary px-6 flex items-center space-x-2 self-end"
          >
            {isLoading ? (
              <Loader2 className="w-5 h-5 animate-spin" />
            ) : (
              <Send className="w-5 h-5" />
            )}
          </button>
        </div>

        {/* Compact Settings Bar */}
        <div className="flex items-center justify-between pt-3 border-t border-gray-200">
          <div className="flex items-center space-x-4">
            <div className="flex items-center space-x-2">
              <select
                value={provider}
                onChange={(e) => setProvider(e.target.value as Provider)}
                className="text-sm border border-gray-300 rounded-lg px-3 py-1.5 focus:ring-2 focus:ring-primary-500 focus:border-transparent bg-white"
              >
                <option value="together">Llama-3.3-70B</option>
                <option value="azure">GPT-4</option>
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
