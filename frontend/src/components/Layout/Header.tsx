import { Activity, HelpCircle } from 'lucide-react';
import type { Tab } from '../../App';

interface HeaderProps {
  activeTab: Tab;
}

const titles: Record<Tab, string> = {
  voice: 'AI Voice Assistant',
  llm: 'LLM Provider Testing',
  github: 'GitHub Integration',
  integrations: 'Integration Testing',
  docs: 'Documentation Orchestrator',
  analysis: 'Full Issue Analysis',
};

const descriptions: Record<Tab, string> = {
  voice: 'Hands-free AI conversation with auto-greeting, continuous listening, and voice responses',
  llm: 'Test Together AI and Azure OpenAI language models with real-time responses',
  github: 'Test GitHub integration and repository access',
  integrations: 'Test Jira, Confluence, and Grafana integrations',
  docs: 'AI-powered documentation workflow: analyze → generate → commit → publish',
  analysis: 'Complete end-to-end issue analysis with context enrichment and fix generation',
};

const Header = ({ activeTab }: HeaderProps) => {
  return (
    <header className="bg-white border-b border-gray-200 px-6 py-4">
      <div className="flex items-center justify-between">
        <div>
          <h2 className="text-2xl font-bold text-gray-900">{titles[activeTab]}</h2>
          <p className="text-sm text-gray-600 mt-1">{descriptions[activeTab]}</p>
        </div>
        
        <div className="flex items-center space-x-3">
          <button className="p-2 text-gray-400 hover:text-gray-600 hover:bg-gray-100 rounded-lg transition-colors">
            <Activity className="w-5 h-5" />
          </button>
          <button className="p-2 text-gray-400 hover:text-gray-600 hover:bg-gray-100 rounded-lg transition-colors">
            <HelpCircle className="w-5 h-5" />
          </button>
        </div>
      </div>
    </header>
  );
};

export default Header;
