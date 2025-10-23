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
            <div className="flex items-center justify-center h-full p-8">
              <div className="text-center max-w-2xl">
                <div className="w-24 h-24 mx-auto mb-6 bg-gradient-to-br from-blue-500 to-purple-600 rounded-full flex items-center justify-center">
                  <svg className="w-12 h-12 text-white" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 11a7 7 0 01-7 7m0 0a7 7 0 01-7-7m7 7v4m0 0H8m4 0h4m-4-8a3 3 0 01-3-3V5a3 3 0 116 0v6a3 3 0 01-3 3z" />
                  </svg>
                </div>
                <h2 className="text-3xl font-bold text-gray-900 mb-4">Voice Assistant</h2>
                <p className="text-lg text-gray-600 mb-8">
                  Your AI voice assistant is active in the floating panel at the bottom-right corner.
                  Just start speaking and the AI will automatically respond!
                </p>
                <div className="bg-blue-50 border border-blue-200 rounded-xl p-6 text-left">
                  <h3 className="font-semibold text-blue-900 mb-3">How it works:</h3>
                  <ul className="space-y-2 text-blue-800">
                    <li className="flex items-start">
                      <svg className="w-5 h-5 mr-2 mt-0.5 flex-shrink-0" fill="currentColor" viewBox="0 0 20 20">
                        <path fillRule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zm3.707-9.293a1 1 0 00-1.414-1.414L9 10.586 7.707 9.293a1 1 0 00-1.414 1.414l2 2a1 1 0 001.414 0l4-4z" clipRule="evenodd" />
                      </svg>
                      <span><strong>Auto-listening:</strong> Continuously listens for your voice</span>
                    </li>
                    <li className="flex items-start">
                      <svg className="w-5 h-5 mr-2 mt-0.5 flex-shrink-0" fill="currentColor" viewBox="0 0 20 20">
                        <path fillRule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zm3.707-9.293a1 1 0 00-1.414-1.414L9 10.586 7.707 9.293a1 1 0 00-1.414 1.414l2 2a1 1 0 001.414 0l4-4z" clipRule="evenodd" />
                      </svg>
                      <span><strong>Auto-send:</strong> Sends after 3 seconds of silence</span>
                    </li>
                    <li className="flex items-start">
                      <svg className="w-5 h-5 mr-2 mt-0.5 flex-shrink-0" fill="currentColor" viewBox="0 0 20 20">
                        <path fillRule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zm3.707-9.293a1 1 0 00-1.414-1.414L9 10.586 7.707 9.293a1 1 0 00-1.414 1.414l2 2a1 1 0 001.414 0l4-4z" clipRule="evenodd" />
                      </svg>
                      <span><strong>Continuous mode:</strong> Keeps listening after each response</span>
                    </li>
                    <li className="flex items-start">
                      <svg className="w-5 h-5 mr-2 mt-0.5 flex-shrink-0" fill="currentColor" viewBox="0 0 20 20">
                        <path fillRule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zm3.707-9.293a1 1 0 00-1.414-1.414L9 10.586 7.707 9.293a1 1 0 00-1.414 1.414l2 2a1 1 0 001.414 0l4-4z" clipRule="evenodd" />
                      </svg>
                      <span><strong>Visual feedback:</strong> See audio levels and status in real-time</span>
                    </li>
                  </ul>
                </div>
                <p className="text-sm text-gray-500 mt-6">
                  💡 <strong>Tip:</strong> You can minimize, mute, or close the floating panel anytime. Look for it in the bottom-right corner!
                </p>
              </div>
            </div>
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
      
      {/* Floating Voice Assistant - Always available from any tab */}
      <VoiceAssistantPanel />
    </div>
  )
}

export default App
