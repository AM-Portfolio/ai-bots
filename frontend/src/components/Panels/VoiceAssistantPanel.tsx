import { useState, useEffect, useRef } from 'react';
import { Mic, MicOff, Volume2, VolumeX, Sparkles, Loader2 } from 'lucide-react';
import axios from 'axios';

interface Message {
  role: 'user' | 'assistant';
  content: string;
  timestamp: Date;
  intent?: string;
  confidence?: number;
}

type VoiceState = 'idle' | 'recording' | 'processing' | 'speaking';

interface VoiceSession {
  session_id: string;
  created_at: string;
  turn_count: number;
  status: string;
}

const VoiceAssistantPanel = () => {
  const [messages, setMessages] = useState<Message[]>([]);
  const [voiceState, setVoiceState] = useState<VoiceState>('idle');
  const [sessionId, setSessionId] = useState<string | null>(null);
  const [autoListen, setAutoListen] = useState(true);
  const [hasGreeted, setHasGreeted] = useState(false);
  const [error, setError] = useState<string | null>(null);
  
  const mediaRecorderRef = useRef<MediaRecorder | null>(null);
  const audioChunksRef = useRef<Blob[]>([]);
  const canvasRef = useRef<HTMLCanvasElement>(null);
  const animationRef = useRef<number>(0);
  const currentAudioRef = useRef<HTMLAudioElement | null>(null);
  const pauseDetectionTimerRef = useRef<number | null>(null);

  // Initialize session on mount
  useEffect(() => {
    initializeSession();
  }, []);

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

      const isActive = voiceState === 'recording' || voiceState === 'speaking';
      
      // Draw animated circles
      const numCircles = 3;
      for (let i = 0; i < numCircles; i++) {
        const radius = 80 + i * 30;
        const alpha = isActive ? 0.6 - i * 0.15 : 0.2 - i * 0.05;
        
        ctx.beginPath();
        ctx.arc(centerX, centerY, radius + Math.sin(angle + i) * 10, 0, Math.PI * 2);
        ctx.strokeStyle = `rgba(59, 130, 246, ${alpha})`;
        ctx.lineWidth = 2;
        ctx.stroke();
      }

      // Draw dots around the circle
      if (isActive) {
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
  }, [voiceState]);

  // Auto-greeting
  useEffect(() => {
    if (!hasGreeted && sessionId) {
      const greetingMessage = "Hi! I'm your AI assistant. I can help you with code questions, commit workflows, and general conversations. How can I help you today?";
      
      setTimeout(() => {
        const aiMessage: Message = {
          role: 'assistant',
          content: greetingMessage,
          timestamp: new Date()
        };
        setMessages([aiMessage]);
        speakText(greetingMessage);
        setHasGreeted(true);
        
        // Start listening after greeting
        if (autoListen) {
          setTimeout(() => {
            startRecording();
          }, 4000);
        }
      }, 1000);
    }
  }, [hasGreeted, sessionId]);

  const initializeSession = async () => {
    try {
      const response = await axios.post<VoiceSession>('/api/voice/session', {
        user_id: 'web-user'
      });
      
      setSessionId(response.data.session_id);
      console.log('✅ Voice session initialized:', response.data.session_id);
    } catch (err: any) {
      console.error('❌ Failed to initialize voice session:', err);
      setError('Failed to initialize voice session');
    }
  };

  const startRecording = async () => {
    if (!sessionId) {
      console.warn('No session ID, cannot start recording');
      return;
    }

    try {
      const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
      
      // Use webm for compatibility
      const mediaRecorder = new MediaRecorder(stream, {
        mimeType: 'audio/webm;codecs=opus'
      });
      
      audioChunksRef.current = [];
      
      mediaRecorder.ondataavailable = (event) => {
        if (event.data.size > 0) {
          audioChunksRef.current.push(event.data);
        }
      };
      
      mediaRecorder.onstop = async () => {
        // Stop all tracks
        stream.getTracks().forEach(track => track.stop());
        
        // Process the recorded audio
        await processRecordedAudio();
      };
      
      mediaRecorderRef.current = mediaRecorder;
      mediaRecorder.start();
      setVoiceState('recording');
      setError(null);
      
      console.log('🎤 Started recording...');
      
      // Auto-stop after 1.5 seconds of silence (pause detection)
      resetPauseDetection();
      
    } catch (err: any) {
      console.error('❌ Failed to start recording:', err);
      setError('Microphone access denied');
      setVoiceState('idle');
    }
  };

  const stopRecording = () => {
    if (mediaRecorderRef.current && voiceState === 'recording') {
      mediaRecorderRef.current.stop();
      clearPauseDetection();
      console.log('⏹️ Stopped recording');
    }
  };

  const resetPauseDetection = () => {
    clearPauseDetection();
    pauseDetectionTimerRef.current = window.setTimeout(() => {
      console.log('🔕 Pause detected - stopping recording');
      stopRecording();
    }, 1500); // 1.5 second pause detection
  };

  const clearPauseDetection = () => {
    if (pauseDetectionTimerRef.current) {
      window.clearTimeout(pauseDetectionTimerRef.current);
      pauseDetectionTimerRef.current = null;
    }
  };

  const processRecordedAudio = async () => {
    if (audioChunksRef.current.length === 0) {
      console.warn('No audio chunks to process');
      setVoiceState('idle');
      return;
    }

    setVoiceState('processing');
    
    try {
      // Create audio blob
      const audioBlob = new Blob(audioChunksRef.current, { type: 'audio/webm' });
      
      // Convert to base64
      const reader = new FileReader();
      reader.readAsDataURL(audioBlob);
      
      reader.onloadend = async () => {
        const base64Audio = (reader.result as string).split(',')[1];
        
        console.log(`📤 Sending ${audioBlob.size} bytes to backend...`);
        
        // Send to backend
        const response = await axios.post('/api/voice/process', {
          session_id: sessionId,
          audio_data: base64Audio,
          audio_format: 'webm'
        });
        
        const { transcript, response_text, response_audio, intent, confidence } = response.data;
        
        console.log(`📝 Transcript: "${transcript}"`);
        console.log(`🎯 Intent: ${intent} (${(confidence * 100).toFixed(1)}%)`);
        
        // Add user message
        const userMessage: Message = {
          role: 'user',
          content: transcript,
          timestamp: new Date()
        };
        setMessages(prev => [...prev, userMessage]);
        
        // Add AI message
        const aiMessage: Message = {
          role: 'assistant',
          content: response_text,
          timestamp: new Date(),
          intent,
          confidence
        };
        setMessages(prev => [...prev, aiMessage]);
        
        // Play response audio if available
        if (response_audio) {
          await playAudioResponse(response_audio);
        } else {
          // Fallback to browser TTS
          speakText(response_text);
        }
        
        // Continue listening if auto-listen is on
        if (autoListen) {
          setTimeout(() => {
            startRecording();
          }, 500);
        } else {
          setVoiceState('idle');
        }
        
      };
      
    } catch (err: any) {
      console.error('❌ Failed to process audio:', err);
      setError(err.response?.data?.detail || 'Failed to process voice');
      setVoiceState('idle');
      
      // Retry if auto-listen is on
      if (autoListen) {
        setTimeout(() => {
          startRecording();
        }, 2000);
      }
    }
  };

  const playAudioResponse = async (base64Audio: string): Promise<void> => {
    return new Promise((resolve, reject) => {
      try {
        // Convert base64 to audio
        const audioData = atob(base64Audio);
        const arrayBuffer = new ArrayBuffer(audioData.length);
        const view = new Uint8Array(arrayBuffer);
        
        for (let i = 0; i < audioData.length; i++) {
          view[i] = audioData.charCodeAt(i);
        }
        
        const blob = new Blob([arrayBuffer], { type: 'audio/mpeg' });
        const url = URL.createObjectURL(blob);
        
        const audio = new Audio(url);
        currentAudioRef.current = audio;
        
        audio.onplay = () => {
          setVoiceState('speaking');
          console.log('🔊 Playing AI response...');
        };
        
        audio.onended = () => {
          setVoiceState('idle');
          URL.revokeObjectURL(url);
          console.log('✅ Audio playback complete');
          resolve();
        };
        
        audio.onerror = (err) => {
          console.error('❌ Audio playback error:', err);
          setVoiceState('idle');
          URL.revokeObjectURL(url);
          reject(err);
        };
        
        audio.play();
        
      } catch (err) {
        console.error('❌ Failed to decode audio:', err);
        setVoiceState('idle');
        reject(err);
      }
    });
  };

  const speakText = (text: string) => {
    // Fallback to browser TTS
    window.speechSynthesis.cancel();
    
    const utterance = new SpeechSynthesisUtterance(text);
    utterance.rate = 1.0;
    utterance.pitch = 1.0;
    utterance.volume = 1.0;
    
    const voices = window.speechSynthesis.getVoices();
    const preferredVoice = voices.find(voice => 
      voice.lang.startsWith('en-') && voice.name.includes('Female')
    ) || voices.find(voice => voice.lang.startsWith('en-')) || voices[0];
    
    if (preferredVoice) {
      utterance.voice = preferredVoice;
    }
    
    utterance.onstart = () => setVoiceState('speaking');
    utterance.onend = () => setVoiceState('idle');
    
    window.speechSynthesis.speak(utterance);
  };

  const toggleAutoListen = () => {
    if (autoListen) {
      setAutoListen(false);
      stopRecording();
      clearPauseDetection();
      setVoiceState('idle');
    } else {
      setAutoListen(true);
      startRecording();
    }
  };

  const stopSpeaking = () => {
    if (currentAudioRef.current) {
      currentAudioRef.current.pause();
      currentAudioRef.current = null;
    }
    window.speechSynthesis.cancel();
    setVoiceState('idle');
  };

  const getStateIcon = () => {
    switch (voiceState) {
      case 'recording':
        return <Mic className="w-16 h-16 text-white animate-pulse" />;
      case 'processing':
        return <Loader2 className="w-16 h-16 text-white animate-spin" />;
      case 'speaking':
        return <Volume2 className="w-16 h-16 text-white animate-pulse" />;
      default:
        return <Sparkles className="w-16 h-16 text-white" />;
    }
  };

  const getStateColor = () => {
    switch (voiceState) {
      case 'recording':
        return 'bg-blue-500 shadow-2xl shadow-blue-500/50';
      case 'processing':
        return 'bg-purple-500 shadow-2xl shadow-purple-500/50';
      case 'speaking':
        return 'bg-indigo-500 shadow-2xl shadow-indigo-500/50';
      default:
        return 'bg-gray-300';
    }
  };

  const getStateText = () => {
    switch (voiceState) {
      case 'recording':
        return { title: 'Listening...', subtitle: '🎤 Speak now, I\'m listening' };
      case 'processing':
        return { title: 'Processing...', subtitle: '🤔 Understanding your request' };
      case 'speaking':
        return { title: 'Speaking...', subtitle: '🔊 AI is responding' };
      default:
        return { 
          title: 'AI Voice Assistant', 
          subtitle: autoListen ? '✨ Ready for continuous conversation' : '⏸️ Voice paused' 
        };
    }
  };

  const stateText = getStateText();

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
              <div className={`w-32 h-32 rounded-full flex items-center justify-center transition-all duration-300 ${getStateColor()}`}>
                {getStateIcon()}
              </div>
            </div>
          </div>
        </div>

        {/* Status Text */}
        <div className="text-center mb-6">
          <h2 className="text-3xl font-bold text-gray-900 mb-2">
            {stateText.title}
          </h2>
          <p className="text-gray-600">
            {stateText.subtitle}
          </p>
          {error && (
            <p className="text-red-500 text-sm mt-2">⚠️ {error}</p>
          )}
        </div>

        {/* Controls */}
        <div className="flex justify-center space-x-4 mb-8">
          <button
            onClick={toggleAutoListen}
            disabled={voiceState === 'processing'}
            className={`px-6 py-3 rounded-full font-semibold transition-all flex items-center space-x-2 ${
              autoListen 
                ? 'bg-blue-500 text-white hover:bg-blue-600 shadow-lg' 
                : 'bg-gray-300 text-gray-700 hover:bg-gray-400'
            } ${voiceState === 'processing' ? 'opacity-50 cursor-not-allowed' : ''}`}
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
            onClick={stopSpeaking}
            disabled={voiceState !== 'speaking'}
            className={`px-6 py-3 rounded-full font-semibold transition-all flex items-center space-x-2 ${
              voiceState === 'speaking'
                ? 'bg-indigo-500 text-white hover:bg-indigo-600 shadow-lg'
                : 'bg-gray-200 text-gray-400 cursor-not-allowed'
            }`}
          >
            {voiceState === 'speaking' ? (
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
            <p className="text-gray-400 text-center py-8">
              {sessionId ? 'Say something to get started...' : 'Initializing AI assistant...'}
            </p>
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
                      {message.intent && (
                        <span className="ml-2 text-xs opacity-70">
                          • {message.intent}
                          {message.confidence && ` (${(message.confidence * 100).toFixed(0)}%)`}
                        </span>
                      )}
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
          <p>💡 Powered by OpenAI Whisper (STT) and GPT (LLM) with intelligent routing</p>
          <p className="mt-1">🔄 Continuous conversation mode is {autoListen ? 'ON' : 'OFF'}</p>
          <p className="mt-1 text-xs">
            🎯 Auto-detects: Code questions → GitHub | Commits → Workflow | Other → Assistant
          </p>
        </div>
      </div>
    </div>
  );
};

export default VoiceAssistantPanel;
