import { Brain, Github, Plug, FileText, BarChart3, Mic } from 'lucide-react';
import type { Tab } from '../../App';

interface SidebarProps {
  activeTab: Tab;
  onTabChange: (tab: Tab) => void;
}

const Sidebar = ({ activeTab, onTabChange }: SidebarProps) => {
  const menuItems = [
    { id: 'voice' as Tab, label: 'Voice Assistant', icon: Mic },
    { id: 'llm' as Tab, label: 'LLM Testing', icon: Brain },
    { id: 'github' as Tab, label: 'GitHub', icon: Github },
    { id: 'integrations' as Tab, label: 'Integrations', icon: Plug },
    { id: 'docs' as Tab, label: 'Doc Orchestrator', icon: FileText },
    { id: 'analysis' as Tab, label: 'Full Analysis', icon: BarChart3 },
  ];

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

      <nav className="flex-1 p-4 space-y-1">
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
