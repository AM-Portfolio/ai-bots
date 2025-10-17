import { useState, useEffect, useRef } from 'react';
import { Mic, MicOff, Volume2, VolumeX, Sparkles } from 'lucide-react';
import { apiClient } from '../../services/api';
import type { Provider } from '../../types/api';

interface Message {
  role: 'user' | 'assistant';
  content: string;
  timestamp: Date;
}

const VoiceAssistantPanel = () => {
  const [messages, setMessages] = useState<Message[]>([]);
  const [isListening, setIsListening] = useState(false);
  const [isSpeaking, setIsSpeaking] = useState(false);
  const [autoListen, setAutoListen] = useState(true);
  const [hasGreeted, setHasGreeted] = useState(false);
  const [provider] = useState<Provider>('together');
  
  const recognitionRef = useRef<any>(null);
  const synthRef = useRef<SpeechSynthesisUtterance | null>(null);
  const canvasRef = useRef<HTMLCanvasElement>(null);
  const animationRef = useRef<number>(0);

  // Animated voice visualization
  useEffect(() => {
    const canvas = canvasRef.current;
    if (!canvas) return;

    const ctx = canvas.getContext('2d');
    if (!ctx) return;

    const centerX = canvas.width / 2;
    const centerY = canvas.height / 2;
    let angle = 0;

    const animate = () => {
      ctx.clearRect(0, 0, canvas.width, canvas.height);

      // Draw animated circles
      const numCircles = 3;
      for (let i = 0; i < numCircles; i++) {
        const radius = 80 + i * 30;
        const alpha = (isListening || isSpeaking) ? 0.6 - i * 0.15 : 0.2 - i * 0.05;
        
        ctx.beginPath();
        ctx.arc(centerX, centerY, radius + Math.sin(angle + i) * 10, 0, Math.PI * 2);
        ctx.strokeStyle = `rgba(59, 130, 246, ${alpha})`;
        ctx.lineWidth = 2;
        ctx.stroke();
      }

      // Draw dots around the circle
      if (isListening || isSpeaking) {
        const numDots = 24;
        for (let i = 0; i < numDots; i++) {
          const dotAngle = (i / numDots) * Math.PI * 2 + angle;
          const dotRadius = 120;
          const x = centerX + Math.cos(dotAngle) * dotRadius;
          const y = centerY + Math.sin(dotAngle) * dotRadius;
          
          ctx.beginPath();
          ctx.arc(x, y, 2, 0, Math.PI * 2);
          ctx.fillStyle = `rgba(59, 130, 246, ${0.4 + Math.sin(angle + i * 0.5) * 0.3})`;
          ctx.fill();
        }
      }

      angle += 0.03;
      animationRef.current = requestAnimationFrame(animate);
    };

    animate();

    return () => {
      if (animationRef.current) {
        cancelAnimationFrame(animationRef.current);
      }
    };
  }, [isListening, isSpeaking]);

  // Initialize speech recognition
  useEffect(() => {
    if (typeof window !== 'undefined' && ('webkitSpeechRecognition' in window || 'SpeechRecognition' in window)) {
      const SpeechRecognition = (window as any).webkitSpeechRecognition || (window as any).SpeechRecognition;
      recognitionRef.current = new SpeechRecognition();
      recognitionRef.current.continuous = true;
      recognitionRef.current.interimResults = false;
      recognitionRef.current.lang = 'en-US';

      recognitionRef.current.onresult = async (event: any) => {
        const transcript = event.results[event.results.length - 1][0].transcript;
        
        // Add user message
        const userMessage: Message = {
          role: 'user',
          content: transcript,
          timestamp: new Date()
        };
        setMessages((prev) => [...prev, userMessage]);

        // Get AI response
        await handleAIResponse(transcript);
      };

      recognitionRef.current.onerror = (event: any) => {
        console.error('Speech recognition error:', event.error);
        if (autoListen && event.error !== 'aborted') {
          setTimeout(() => {
            try {
              recognitionRef.current?.start();
              setIsListening(true);
            } catch (e) {
              console.error('Failed to restart recognition:', e);
            }
          }, 1000);
        }
      };

      recognitionRef.current.onend = () => {
        setIsListening(false);
        if (autoListen) {
          setTimeout(() => {
            try {
              recognitionRef.current?.start();
              setIsListening(true);
            } catch (e) {
              console.error('Failed to restart recognition:', e);
            }
          }, 500);
        }
      };
    }
  }, [autoListen]);

  // Auto-greeting on load
  useEffect(() => {
    if (!hasGreeted) {
      const greetingMessage = "Hi! I'm your AI assistant. How can I help you today?";
      
      setTimeout(() => {
        const aiMessage: Message = {
          role: 'assistant',
          content: greetingMessage,
          timestamp: new Date()
        };
        setMessages([aiMessage]);
        speak(greetingMessage);
        setHasGreeted(true);
        
        // Start listening after greeting
        if (autoListen) {
          setTimeout(() => {
            startListening();
          }, 3000);
        }
      }, 1000);
    }
  }, [hasGreeted]);

  const speak = (text: string) => {
    // Stop any ongoing speech
    window.speechSynthesis.cancel();
    
    const utterance = new SpeechSynthesisUtterance(text);
    utterance.rate = 1.0;
    utterance.pitch = 1.0;
    utterance.volume = 1.0;
    
    // Get available voices
    const voices = window.speechSynthesis.getVoices();
    const preferredVoice = voices.find(voice => 
      voice.lang.startsWith('en-') && voice.name.includes('Female')
    ) || voices.find(voice => voice.lang.startsWith('en-')) || voices[0];
    
    if (preferredVoice) {
      utterance.voice = preferredVoice;
    }
    
    utterance.onstart = () => setIsSpeaking(true);
    utterance.onend = () => setIsSpeaking(false);
    
    synthRef.current = utterance;
    window.speechSynthesis.speak(utterance);
  };

  const handleAIResponse = async (userInput: string) => {
    try {
      const result = await apiClient.testLLM(userInput, provider);
      
      if (result.success && result.response) {
        const aiMessage: Message = {
          role: 'assistant',
          content: result.response,
          timestamp: new Date()
        };
        setMessages((prev) => [...prev, aiMessage]);
        
        // Speak the response
        speak(result.response);
      }
    } catch (error) {
      console.error('AI response error:', error);
    }
  };

  const startListening = () => {
    try {
      recognitionRef.current?.start();
      setIsListening(true);
    } catch (e) {
      console.error('Failed to start listening:', e);
    }
  };

  const stopListening = () => {
    try {
      recognitionRef.current?.stop();
      setIsListening(false);
    } catch (e) {
      console.error('Failed to stop listening:', e);
    }
  };

  const toggleAutoListen = () => {
    if (autoListen) {
      setAutoListen(false);
      stopListening();
    } else {
      setAutoListen(true);
      startListening();
    }
  };

  const toggleMute = () => {
    if (isSpeaking) {
      window.speechSynthesis.cancel();
      setIsSpeaking(false);
    }
  };

  return (
    <div className="h-full flex items-center justify-center bg-gradient-to-br from-blue-50 to-indigo-50">
      <div className="max-w-4xl w-full px-8">
        {/* Animated Voice Visualization */}
        <div className="flex justify-center mb-8">
          <div className="relative">
            <canvas
              ref={canvasRef}
              width={400}
              height={400}
              className="max-w-full"
            />
            <div className="absolute inset-0 flex items-center justify-center">
              <div className={`w-32 h-32 rounded-full flex items-center justify-center transition-all duration-300 ${
                isListening ? 'bg-blue-500 shadow-2xl shadow-blue-500/50' : 
                isSpeaking ? 'bg-indigo-500 shadow-2xl shadow-indigo-500/50' : 
                'bg-gray-300'
              }`}>
                {isListening ? (
                  <Mic className="w-16 h-16 text-white animate-pulse" />
                ) : isSpeaking ? (
                  <Volume2 className="w-16 h-16 text-white animate-pulse" />
                ) : (
                  <Sparkles className="w-16 h-16 text-white" />
                )}
              </div>
            </div>
          </div>
        </div>

        {/* Status Text */}
        <div className="text-center mb-6">
          <h2 className="text-3xl font-bold text-gray-900 mb-2">
            {isListening ? 'Listening...' : isSpeaking ? 'Speaking...' : 'AI Voice Assistant'}
          </h2>
          <p className="text-gray-600">
            {isListening ? '🎤 Speak now, I\'m listening' : 
             isSpeaking ? '🔊 AI is speaking' : 
             autoListen ? '✨ Ready for continuous conversation' : '⏸️ Voice paused'}
          </p>
        </div>

        {/* Controls */}
        <div className="flex justify-center space-x-4 mb-8">
          <button
            onClick={toggleAutoListen}
            className={`px-6 py-3 rounded-full font-semibold transition-all flex items-center space-x-2 ${
              autoListen 
                ? 'bg-blue-500 text-white hover:bg-blue-600 shadow-lg' 
                : 'bg-gray-300 text-gray-700 hover:bg-gray-400'
            }`}
          >
            {autoListen ? (
              <>
                <Mic className="w-5 h-5" />
                <span>Voice Active</span>
              </>
            ) : (
              <>
                <MicOff className="w-5 h-5" />
                <span>Voice Paused</span>
              </>
            )}
          </button>

          <button
            onClick={toggleMute}
            disabled={!isSpeaking}
            className={`px-6 py-3 rounded-full font-semibold transition-all flex items-center space-x-2 ${
              isSpeaking
                ? 'bg-indigo-500 text-white hover:bg-indigo-600 shadow-lg'
                : 'bg-gray-200 text-gray-400 cursor-not-allowed'
            }`}
          >
            {isSpeaking ? (
              <>
                <VolumeX className="w-5 h-5" />
                <span>Stop Speaking</span>
              </>
            ) : (
              <>
                <Volume2 className="w-5 h-5" />
                <span>Not Speaking</span>
              </>
            )}
          </button>
        </div>

        {/* Conversation History */}
        <div className="bg-white rounded-2xl shadow-xl p-6 max-h-96 overflow-y-auto">
          <h3 className="text-lg font-semibold text-gray-800 mb-4">Conversation</h3>
          {messages.length === 0 ? (
            <p className="text-gray-400 text-center py-8">Initializing AI assistant...</p>
          ) : (
            <div className="space-y-3">
              {messages.map((message, index) => (
                <div
                  key={index}
                  className={`flex ${message.role === 'user' ? 'justify-end' : 'justify-start'}`}
                >
                  <div
                    className={`max-w-[80%] px-4 py-2 rounded-2xl ${
                      message.role === 'user'
                        ? 'bg-blue-500 text-white'
                        : 'bg-gray-100 text-gray-900'
                    }`}
                  >
                    <p className="text-sm font-medium mb-1">
                      {message.role === 'user' ? 'You' : '🤖 AI Assistant'}
                    </p>
                    <p className="whitespace-pre-wrap">{message.content}</p>
                  </div>
                </div>
              ))}
            </div>
          )}
        </div>

        {/* Helper Text */}
        <div className="mt-6 text-center text-sm text-gray-500">
          <p>💡 Just speak naturally - I'll listen and respond automatically</p>
          <p className="mt-1">🔄 Continuous conversation mode is {autoListen ? 'ON' : 'OFF'}</p>
        </div>
      </div>
    </div>
  );
};

export default VoiceAssistantPanel;
