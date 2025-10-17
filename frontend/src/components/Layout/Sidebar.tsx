import { Brain, Plug, FileText, Mic, Settings, MessageSquarePlus, Clock, Trash2, ChevronDown, ChevronRight } from 'lucide-react';
import { useState, useEffect } from 'react';
import type { Tab } from '../../App';

interface SidebarProps {
  activeTab: Tab;
  onTabChange: (tab: Tab) => void;
}

interface Conversation {
  id: number;
  title: string;
  provider: string;
  created_at: string;
  updated_at: string;
  message_count: number;
}

const Sidebar = ({ activeTab, onTabChange }: SidebarProps) => {
  const [conversations, setConversations] = useState<Conversation[]>([]);
  const [showHistory, setShowHistory] = useState(false);
  const [currentConversationId, setCurrentConversationId] = useState<number | null>(null);

  const menuItems = [
    { id: 'voice' as Tab, label: 'Voice Assistant', icon: Mic },
    { id: 'llm' as Tab, label: 'LLM Testing', icon: Brain },
    { id: 'integrations' as Tab, label: 'Integrations', icon: Plug },
    { id: 'config' as Tab, label: 'Configuration', icon: Settings },
    { id: 'docs' as Tab, label: 'Doc Orchestrator', icon: FileText },
  ];

  useEffect(() => {
    if (activeTab === 'llm') {
      loadConversations();
    }
  }, [activeTab]);

  const loadConversations = async () => {
    try {
      const response = await fetch('/api/chat/conversations');
      const data = await response.json();
      setConversations(data);
    } catch (error) {
      console.error('Failed to load conversations:', error);
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
        setCurrentConversationId(null);
        window.dispatchEvent(new CustomEvent('clearChat'));
      }
      
      await loadConversations();
    } catch (error) {
      console.error('Failed to delete conversation:', error);
    }
  };

  const loadConversation = (conversationId: number) => {
    setCurrentConversationId(conversationId);
    window.dispatchEvent(new CustomEvent('loadConversation', { 
      detail: { conversationId } 
    }));
  };

  const startNewChat = () => {
    setCurrentConversationId(null);
    window.dispatchEvent(new CustomEvent('clearChat'));
  };

  return (
    <aside className="w-64 bg-white border-r border-gray-200 flex flex-col">
      <div className="p-6 border-b border-gray-200">
        <div className="flex items-center space-x-3">
          <div className="w-10 h-10 bg-gradient-to-br from-primary-500 to-primary-700 rounded-xl flex items-center justify-center">
            <Brain className="w-6 h-6 text-white" />
          </div>
          <div>
            <h1 className="text-lg font-bold text-gray-900">AI Dev Agent</h1>
            <p className="text-xs text-gray-500">v1.0.0</p>
          </div>
        </div>
      </div>

      <nav className="flex-1 p-4 space-y-1 overflow-y-auto">
        {menuItems.map((item) => {
          const Icon = item.icon;
          const isActive = activeTab === item.id;
          
          return (
            <button
              key={item.id}
              onClick={() => onTabChange(item.id)}
              className={`
                w-full flex items-center space-x-3 px-4 py-3 rounded-lg transition-all duration-200
                ${isActive
                  ? 'bg-primary-50 text-primary-700 font-medium'
                  : 'text-gray-600 hover:bg-gray-100 hover:text-gray-900'
                }
              `}
            >
              <Icon className={`w-5 h-5 ${isActive ? 'text-primary-600' : 'text-gray-400'}`} />
              <span>{item.label}</span>
            </button>
          );
        })}

        {/* Chat History Section - Only show when LLM Testing is active */}
        {activeTab === 'llm' && (
          <div className="pt-4 mt-4 border-t border-gray-200">
            <button
              onClick={startNewChat}
              className="w-full btn-primary flex items-center justify-center space-x-2 mb-3"
            >
              <MessageSquarePlus className="w-4 h-4" />
              <span>New Chat</span>
            </button>

            <button
              onClick={() => setShowHistory(!showHistory)}
              className="w-full flex items-center justify-between px-2 py-2 text-sm font-semibold text-gray-700 hover:bg-gray-50 rounded-lg transition-colors"
            >
              <span>Recent Conversations</span>
              {showHistory ? (
                <ChevronDown className="w-4 h-4" />
              ) : (
                <ChevronRight className="w-4 h-4" />
              )}
            </button>

            {showHistory && (
              <div className="mt-2 space-y-1 max-h-96 overflow-y-auto">
                {conversations.map((conv) => (
                  <div
                    key={conv.id}
                    onClick={() => loadConversation(conv.id)}
                    className={`p-2 rounded-lg cursor-pointer transition-colors group ${
                      currentConversationId === conv.id
                        ? 'bg-primary-50 border border-primary-200'
                        : 'hover:bg-gray-50'
                    }`}
                  >
                    <div className="flex items-start justify-between">
                      <div className="flex-1 min-w-0">
                        <p className="text-xs font-medium text-gray-900 truncate">
                          {conv.title}
                        </p>
                        <div className="flex items-center space-x-1 mt-1">
                          <Clock className="w-3 h-3 text-gray-400" />
                          <p className="text-xs text-gray-500">
                            {new Date(conv.updated_at).toLocaleDateString()}
                          </p>
                        </div>
                      </div>
                      <button
                        onClick={(e) => deleteConversation(conv.id, e)}
                        className="opacity-0 group-hover:opacity-100 ml-1 p-1 text-red-500 hover:bg-red-50 rounded transition-opacity"
                      >
                        <Trash2 className="w-3 h-3" />
                      </button>
                    </div>
                  </div>
                ))}
                
                {conversations.length === 0 && (
                  <p className="text-xs text-gray-500 text-center py-3">
                    No conversations yet
                  </p>
                )}
              </div>
            )}
          </div>
        )}
      </nav>

      <div className="p-4 border-t border-gray-200">
        <div className="text-xs text-gray-500 space-y-1">
          <p className="font-medium">Status: <span className="text-green-600">● Running</span></p>
          <p>Together AI + Azure OpenAI</p>
        </div>
      </div>
    </aside>
  );
};

export default Sidebar;
