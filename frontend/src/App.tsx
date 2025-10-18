import { useState, useEffect } from 'react'
import Sidebar from './components/Layout/Sidebar'
import Header from './components/Layout/Header'
import LLMTestPanel from './components/Panels/LLMTestPanel'
import IntegrationsHub from './components/Panels/IntegrationsHub'
import DocOrchestratorPanel from './components/Panels/DocOrchestratorPanel'
import VoiceAssistantPanel from './components/Panels/VoiceAssistantPanel'
import LogViewer from './components/Shared/LogViewer'
import { logger } from './utils/logger'

export type Tab = 'voice' | 'llm' | 'integrations' | 'docs';

function App() {
  const [activeTab, setActiveTab] = useState<Tab>('llm');

  useEffect(() => {
    logger.ui.info('Application started');
  }, []);

  const handleTabChange = (tab: Tab) => {
    logger.ui.info(`Switched to ${tab} tab`);
    setActiveTab(tab);
  };

  return (
    <div className="flex h-screen bg-gray-50">
      <Sidebar activeTab={activeTab} onTabChange={handleTabChange} />
      
      <div className="flex-1 flex flex-col overflow-hidden">
        <Header activeTab={activeTab} />
        
        <main className="flex-1 overflow-hidden">
          {activeTab === 'voice' ? (
            <VoiceAssistantPanel />
          ) : activeTab === 'integrations' ? (
            <IntegrationsHub />
          ) : (
            <div className="max-w-7xl mx-auto px-6 py-8 h-full overflow-y-auto">
              {activeTab === 'llm' && <LLMTestPanel />}
              {activeTab === 'docs' && <DocOrchestratorPanel />}
            </div>
          )}
        </main>
      </div>
      
      <LogViewer />
    </div>
  )
}

export default App
