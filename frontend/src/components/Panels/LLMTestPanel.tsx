import { useState, useRef, useEffect } from 'react';
import { Send, Loader2, Settings, Mic, MicOff, Volume2, Sparkles, MessageSquarePlus, Trash2, Clock } from 'lucide-react';
import { apiClient } from '../../services/api';
import type { Provider, ThinkingProcessData } from '../../types/api';
import ThinkingProcess from '../Shared/ThinkingProcess';

interface Message {
  role: 'user' | 'assistant';
  content: string;
  provider?: string;
  duration?: number;
}

interface Conversation {
  id: number;
  title: string;
  provider: string;
  created_at: string;
  updated_at: string;
  message_count: number;
}

const LLMTestPanel = () => {
  const [messages, setMessages] = useState<Message[]>([]);
  const [input, setInput] = useState('What are some best practices for writing clean Python code?');
  const [provider, setProvider] = useState<Provider>('together');
  const [isLoading, setIsLoading] = useState(false);
  const [showBackendDetails, setShowBackendDetails] = useState(true);
  const [thinkingData, setThinkingData] = useState<ThinkingProcessData | null>(null);
  
  // Chat history state
  const [conversations, setConversations] = useState<Conversation[]>([]);
  const [currentConversationId, setCurrentConversationId] = useState<number | null>(null);
  const [showHistory, setShowHistory] = useState(true);
  
  // Voice features
  const [isListening, setIsListening] = useState(false);
  const [voiceEnabled, setVoiceEnabled] = useState(false);
  const [thinkingMode, setThinkingMode] = useState(false);
  const recognitionRef = useRef<any>(null);
  const audioRef = useRef<HTMLAudioElement | null>(null);

  // Load conversations on mount
  useEffect(() => {
    loadConversations();
  }, []);

  const loadConversations = async () => {
    try {
      const response = await fetch('/api/chat/conversations');
      const data = await response.json();
      setConversations(data);
    } catch (error) {
      console.error('Failed to load conversations:', error);
    }
  };

  const loadConversation = async (conversationId: number) => {
    try {
      const response = await fetch(`/api/chat/conversations/${conversationId}/messages`);
      const msgs = await response.json();
      
      setMessages(msgs.map((msg: any) => ({
        role: msg.role,
        content: msg.content,
        duration: msg.duration
      })));
      setCurrentConversationId(conversationId);
      
      // Set provider from conversation
      const conv = conversations.find(c => c.id === conversationId);
      if (conv) {
        setProvider(conv.provider as Provider);
      }
    } catch (error) {
      console.error('Failed to load conversation:', error);
    }
  };

  const saveConversation = async () => {
    if (messages.length === 0) return;
    
    try {
      // Generate title from first user message
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
        await loadConversations();
      }
    } catch (error) {
      console.error('Failed to save conversation:', error);
    }
  };

  const deleteConversation = async (conversationId: number, e: React.MouseEvent) => {
    e.stopPropagation();
    
    if (!confirm('Are you sure you want to delete this conversation?')) return;
    
    try {
      await fetch(`/api/chat/conversations/${conversationId}`, {
        method: 'DELETE'
      });
      
      if (currentConversationId === conversationId) {
        setMessages([]);
        setCurrentConversationId(null);
      }
      
      await loadConversations();
    } catch (error) {
      console.error('Failed to delete conversation:', error);
    }
  };

  const startNewChat = () => {
    setMessages([]);
    setCurrentConversationId(null);
    setThinkingData(null);
    setInput('');
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
    const newMessages = [...messages, userMessage];
    setMessages(newMessages);
    const messageText = input;
    setInput('');
    setIsLoading(true);
    setThinkingData(null);

    try {
      const startTime = performance.now();
      const result = await apiClient.testLLM(messageText, provider, showBackendDetails);
      const duration = (performance.now() - startTime) / 1000;
      
      if (result.thinking) {
        setThinkingData(result.thinking);
      }

      if (result.success && result.response) {
        const assistantMessage: Message = {
          role: 'assistant',
          content: result.response,
          provider: result.provider_used || provider,
          duration,
        };
        setMessages((prev) => [...prev, assistantMessage]);
        
        // Auto-save after assistant response
        setTimeout(() => saveConversation(), 500);
        
        if (voiceEnabled) {
          playVoiceResponse(result.response);
        }
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

  return (
    <div className="flex h-full gap-4">
      {/* Chat History Sidebar */}
      {showHistory && (
        <div className="w-64 flex-shrink-0 card p-4 overflow-y-auto">
          <button
            onClick={startNewChat}
            className="w-full btn-primary flex items-center justify-center space-x-2 mb-4"
          >
            <MessageSquarePlus className="w-5 h-5" />
            <span>New Chat</span>
          </button>
          
          <h3 className="text-sm font-semibold text-gray-700 mb-3">Recent Conversations</h3>
          
          <div className="space-y-2">
            {conversations.map((conv) => (
              <div
                key={conv.id}
                onClick={() => loadConversation(conv.id)}
                className={`p-3 rounded-lg cursor-pointer transition-colors group ${
                  currentConversationId === conv.id
                    ? 'bg-primary-50 border-2 border-primary-200'
                    : 'bg-gray-50 hover:bg-gray-100 border-2 border-transparent'
                }`}
              >
                <div className="flex items-start justify-between">
                  <div className="flex-1 min-w-0">
                    <p className="text-sm font-medium text-gray-900 truncate">
                      {conv.title}
                    </p>
                    <div className="flex items-center space-x-2 mt-1">
                      <Clock className="w-3 h-3 text-gray-400" />
                      <p className="text-xs text-gray-500">
                        {new Date(conv.updated_at).toLocaleDateString()}
                      </p>
                    </div>
                    <p className="text-xs text-gray-400 mt-1">
                      {conv.message_count} messages
                    </p>
                  </div>
                  <button
                    onClick={(e) => deleteConversation(conv.id, e)}
                    className="opacity-0 group-hover:opacity-100 ml-2 p-1 text-red-500 hover:bg-red-50 rounded transition-opacity"
                  >
                    <Trash2 className="w-4 h-4" />
                  </button>
                </div>
              </div>
            ))}
            
            {conversations.length === 0 && (
              <p className="text-sm text-gray-500 text-center py-4">
                No conversations yet
              </p>
            )}
          </div>
        </div>
      )}

      {/* Main Chat Area */}
      <div className="flex-1 space-y-6">
        <div className="card">
          <div className="flex items-center justify-between mb-4">
            <div className="flex items-center space-x-3">
              <Settings className="w-5 h-5 text-gray-600" />
              <h3 className="text-lg font-semibold text-gray-900">Settings</h3>
            </div>
            <div className="flex items-center space-x-4">
              <label className="flex items-center space-x-2 cursor-pointer">
                <input
                  type="checkbox"
                  checked={voiceEnabled}
                  onChange={(e) => setVoiceEnabled(e.target.checked)}
                  className="w-4 h-4 text-primary-600 rounded focus:ring-primary-500"
                />
                <Volume2 className="w-4 h-4 text-gray-600" />
                <span className="text-sm text-gray-700">Voice Response</span>
              </label>
              <label className="flex items-center space-x-2 cursor-pointer">
                <input
                  type="checkbox"
                  checked={thinkingMode}
                  onChange={(e) => setThinkingMode(e.target.checked)}
                  className="w-4 h-4 text-primary-600 rounded focus:ring-primary-500"
                />
                <Sparkles className="w-4 h-4 text-gray-600" />
                <span className="text-sm text-gray-700">Thinking Mode</span>
              </label>
              <label className="flex items-center space-x-2 cursor-pointer">
                <input
                  type="checkbox"
                  checked={showBackendDetails}
                  onChange={(e) => setShowBackendDetails(e.target.checked)}
                  className="w-4 h-4 text-primary-600 rounded focus:ring-primary-500"
                />
                <span className="text-sm text-gray-700">Backend Details</span>
              </label>
            </div>
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

            {showBackendDetails && thinkingData && (
              <ThinkingProcess data={thinkingData} title="Backend Processing Steps" />
            )}

            {isLoading && (!showBackendDetails || thinkingMode) && (
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
                  placeholder={isListening ? "Listening..." : "Type your message... (Shift+Enter for new line)"}
                  className={`textarea-field pr-12 ${isListening ? 'ring-2 ring-red-500' : ''}`}
                  rows={3}
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
                    <MicOff className="w-5 h-5" />
                  ) : (
                    <Mic className="w-5 h-5" />
                  )}
                </button>
              </div>
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
            {isListening && (
              <p className="text-sm text-red-600 mt-2 flex items-center space-x-2">
                <span className="animate-pulse">🎤</span>
                <span>Listening... Speak now</span>
              </p>
            )}
            {voiceEnabled && (
              <p className="text-sm text-blue-600 mt-2 flex items-center space-x-2">
                <Volume2 className="w-4 h-4" />
                <span>Voice responses enabled</span>
              </p>
            )}
          </div>
        </div>
      </div>
    </div>
  );
};

export default LLMTestPanel;
