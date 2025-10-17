import { useState } from 'react'
import Sidebar from './components/Layout/Sidebar'
import Header from './components/Layout/Header'
import LLMTestPanel from './components/Panels/LLMTestPanel'
import GitHubTestPanel from './components/Panels/GitHubTestPanel'
import IntegrationsPanel from './components/Panels/IntegrationsPanel'
import DocOrchestratorPanel from './components/Panels/DocOrchestratorPanel'
import FullAnalysisPanel from './components/Panels/FullAnalysisPanel'
import VoiceAssistantPanel from './components/Panels/VoiceAssistantPanel'

export type Tab = 'llm' | 'github' | 'integrations' | 'docs' | 'analysis' | 'voice';

function App() {
  const [activeTab, setActiveTab] = useState<Tab>('llm');

  return (
    <div className="flex h-screen bg-gray-50">
      <Sidebar activeTab={activeTab} onTabChange={setActiveTab} />
      
      <div className="flex-1 flex flex-col overflow-hidden">
        <Header activeTab={activeTab} />
        
        <main className="flex-1 overflow-y-auto">
          {activeTab === 'voice' ? (
            <VoiceAssistantPanel />
          ) : (
            <div className="max-w-7xl mx-auto px-6 py-8">
              {activeTab === 'llm' && <LLMTestPanel />}
              {activeTab === 'github' && <GitHubTestPanel />}
              {activeTab === 'integrations' && <IntegrationsPanel />}
              {activeTab === 'docs' && <DocOrchestratorPanel />}
              {activeTab === 'analysis' && <FullAnalysisPanel />}
            </div>
          )}
        </main>
      </div>
    </div>
  )
}

export default App
