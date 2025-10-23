import { useState, useEffect, useRef } from 'react';
import { Mic, MicOff, Volume2, Send, Settings, MessageCircle, X } from 'lucide-react';
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
  const [liveTranscript, setLiveTranscript] = useState<string>('');
  const [audioLevel, setAudioLevel] = useState<number>(0);
  const [showSettings, setShowSettings] = useState(false);
  
  const mediaRecorderRef = useRef<MediaRecorder | null>(null);
  const audioChunksRef = useRef<Blob[]>([]);
  const currentAudioRef = useRef<HTMLAudioElement | null>(null);
  const silenceTimerRef = useRef<number | null>(null);
  const audioContextRef = useRef<AudioContext | null>(null);
  const analyserRef = useRef<AnalyserNode | null>(null);
  const messagesEndRef = useRef<HTMLDivElement>(null);

  // Auto-scroll to bottom
  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages, liveTranscript]);

  // Initialize session on mount
  useEffect(() => {
    initializeSession();
  }, []);

  // Auto-greeting
  useEffect(() => {
    if (!hasGreeted && sessionId) {
      const greetingMessage = "Hi! I'm here to help. What can I do for you?";
      
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
          }, 2000);
        }
      }, 500);
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
      const stream = await navigator.mediaDevices.getUserMedia({ 
        audio: {
          echoCancellation: true,
          noiseSuppression: true,
          autoGainControl: true
        } 
      });
      
      // Setup audio context for level monitoring
      audioContextRef.current = new AudioContext();
      const source = audioContextRef.current.createMediaStreamSource(stream);
      analyserRef.current = audioContextRef.current.createAnalyser();
      analyserRef.current.fftSize = 256;
      source.connect(analyserRef.current);
      
      // Start level monitoring
      monitorAudioLevel();
      
      // Use webm for compatibility
      const mediaRecorder = new MediaRecorder(stream, {
        mimeType: 'audio/webm;codecs=opus'
      });
      
      audioChunksRef.current = [];
      setLiveTranscript('Listening...');
      
      mediaRecorder.ondataavailable = (event) => {
        if (event.data.size > 0) {
          audioChunksRef.current.push(event.data);
        }
      };
      
      mediaRecorder.onstop = async () => {
        // Stop all tracks
        stream.getTracks().forEach(track => track.stop());
        
        // Stop audio context
        if (audioContextRef.current) {
          audioContextRef.current.close();
          audioContextRef.current = null;
        }
        
        // Process the recorded audio
        await processRecordedAudio();
      };
      
      mediaRecorderRef.current = mediaRecorder;
      mediaRecorder.start();
      setVoiceState('recording');
      setError(null);
      
      console.log('🎤 Started recording...');
      
      // Auto-stop after 2 seconds of silence
      resetSilenceDetection();
      
    } catch (err: any) {
      console.error('❌ Failed to start recording:', err);
      setError('Microphone access denied');
      setVoiceState('idle');
      setLiveTranscript('');
    }
  };

  const monitorAudioLevel = () => {
    if (!analyserRef.current) return;
    
    const dataArray = new Uint8Array(analyserRef.current.frequencyBinCount);
    
    const checkLevel = () => {
      if (!analyserRef.current || voiceState !== 'recording') return;
      
      analyserRef.current.getByteFrequencyData(dataArray);
      const average = dataArray.reduce((a, b) => a + b) / dataArray.length;
      const normalizedLevel = Math.min(100, (average / 255) * 200);
      
      setAudioLevel(normalizedLevel);
      
      // Voice activity detection
      if (normalizedLevel > 15) {
        // Reset silence timer when voice detected
        resetSilenceDetection();
      }
      
      requestAnimationFrame(checkLevel);
    };
    
    checkLevel();
  };

  const resetSilenceDetection = () => {
    if (silenceTimerRef.current) {
      clearTimeout(silenceTimerRef.current);
    }
    
    // Auto-send after 2 seconds of silence
    silenceTimerRef.current = window.setTimeout(() => {
      console.log('🔕 Silence detected - auto-sending');
      stopRecording();
    }, 2000);
  };

  const stopRecording = () => {
    if (mediaRecorderRef.current && voiceState === 'recording') {
      mediaRecorderRef.current.stop();
      if (silenceTimerRef.current) {
        clearTimeout(silenceTimerRef.current);
        silenceTimerRef.current = null;
      }
      setAudioLevel(0);
      console.log('⏹️ Stopped recording');
    }
  };

  const processRecordedAudio = async () => {
    if (audioChunksRef.current.length === 0) {
      console.warn('No audio chunks to process');
      setVoiceState('idle');
      setLiveTranscript('');
      return;
    }

    setVoiceState('processing');
    setLiveTranscript('Processing...');
    
    try {
      // Create audio blob
      const audioBlob = new Blob(audioChunksRef.current, { type: 'audio/webm' });
      
      console.log(`📤 Sending ${audioBlob.size} bytes to backend...`);
      
      if (audioBlob.size < 1000) {
        console.warn('⚠️ Audio too small, likely no speech detected');
        setVoiceState('idle');
        setLiveTranscript('');
        if (autoListen) {
          setTimeout(() => startRecording(), 500);
        }
        return;
      }
      
      // Convert to base64
      const reader = new FileReader();
      reader.readAsDataURL(audioBlob);
      
      reader.onloadend = async () => {
        const base64Audio = (reader.result as string).split(',')[1];
        
        // Send to backend
        const response = await axios.post('/api/voice/process', {
          session_id: sessionId,
          audio_data: base64Audio,
          audio_format: 'webm'
        });
        
        const { transcript, response_text, response_audio, intent, confidence } = response.data;
        
        console.log(`📝 Transcript: "${transcript}"`);
        console.log(`🎯 Intent: ${intent} (${(confidence * 100).toFixed(1)}%)`);
        
        setLiveTranscript('');
        
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
      setLiveTranscript('');
      
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

  const toggleVoice = () => {
    if (voiceState === 'recording') {
      stopRecording();
      setAutoListen(false);
    } else if (voiceState === 'speaking') {
      if (currentAudioRef.current) {
        currentAudioRef.current.pause();
        currentAudioRef.current = null;
      }
      window.speechSynthesis.cancel();
      setVoiceState('idle');
    } else {
      setAutoListen(true);
      startRecording();
    }
  };

  const formatTime = (date: Date) => {
    return date.toLocaleTimeString('en-US', { hour: '2-digit', minute: '2-digit' });
  };

  const getStatusBadge = () => {
    switch (voiceState) {
      case 'recording':
        return (
          <div className="flex items-center space-x-2 px-4 py-2 bg-green-500/20 border border-green-500 rounded-full">
            <div className="w-2 h-2 bg-green-500 rounded-full animate-pulse" />
            <span className="text-sm font-medium text-green-700">Listening</span>
          </div>
        );
      case 'processing':
        return (
          <div className="flex items-center space-x-2 px-4 py-2 bg-blue-500/20 border border-blue-500 rounded-full">
            <div className="w-2 h-2 bg-blue-500 rounded-full animate-pulse" />
            <span className="text-sm font-medium text-blue-700">Processing</span>
          </div>
        );
      case 'speaking':
        return (
          <div className="flex items-center space-x-2 px-4 py-2 bg-purple-500/20 border border-purple-500 rounded-full">
            <div className="w-2 h-2 bg-purple-500 rounded-full animate-pulse" />
            <span className="text-sm font-medium text-purple-700">Speaking</span>
          </div>
        );
      default:
        return (
          <div className="flex items-center space-x-2 px-4 py-2 bg-gray-500/20 border border-gray-400 rounded-full">
            <div className="w-2 h-2 bg-gray-500 rounded-full" />
            <span className="text-sm font-medium text-gray-700">Ready</span>
          </div>
        );
    }
  };

  return (
    <div className="h-full flex flex-col bg-gradient-to-br from-slate-50 to-slate-100">
      {/* Header */}
      <div className="bg-white border-b border-gray-200 px-6 py-4">
        <div className="flex items-center justify-between">
          <div className="flex items-center space-x-3">
            <div className="w-10 h-10 bg-gradient-to-br from-blue-500 to-indigo-600 rounded-full flex items-center justify-center">
              <MessageCircle className="w-6 h-6 text-white" />
            </div>
            <div>
              <h1 className="text-xl font-bold text-gray-900">AI Voice Assistant</h1>
              <p className="text-sm text-gray-500">Powered by Azure AI</p>
            </div>
          </div>
          
          <div className="flex items-center space-x-3">
            {getStatusBadge()}
            <button
              onClick={() => setShowSettings(!showSettings)}
              className="p-2 hover:bg-gray-100 rounded-lg transition-colors"
            >
              <Settings className="w-5 h-5 text-gray-600" />
            </button>
          </div>
        </div>
      </div>

      {/* Conversation Area */}
      <div className="flex-1 overflow-y-auto px-6 py-4 space-y-4">
        {messages.length === 0 ? (
          <div className="flex items-center justify-center h-full">
            <div className="text-center">
              <div className="w-16 h-16 bg-gradient-to-br from-blue-500 to-indigo-600 rounded-full flex items-center justify-center mx-auto mb-4">
                <Mic className="w-8 h-8 text-white" />
              </div>
              <h3 className="text-lg font-semibold text-gray-700 mb-2">Ready to listen</h3>
              <p className="text-gray-500">Click the microphone to start talking</p>
            </div>
          </div>
        ) : (
          <>
            {messages.map((message, index) => (
              <div key={index} className={`flex ${message.role === 'user' ? 'justify-end' : 'justify-start'}`}>
                <div className={`max-w-[70%] ${message.role === 'user' ? 'order-2' : 'order-1'}`}>
                  <div className="flex items-end space-x-2">
                    {message.role === 'assistant' && (
                      <div className="w-8 h-8 bg-gradient-to-br from-blue-500 to-indigo-600 rounded-full flex items-center justify-center flex-shrink-0">
                        <MessageCircle className="w-5 h-5 text-white" />
                      </div>
                    )}
                    <div
                      className={`px-4 py-3 rounded-2xl shadow-sm ${
                        message.role === 'user'
                          ? 'bg-blue-600 text-white rounded-br-none'
                          : 'bg-white text-gray-900 rounded-bl-none border border-gray-200'
                      }`}
                    >
                      <p className="text-sm leading-relaxed whitespace-pre-wrap">{message.content}</p>
                      <div className="flex items-center justify-between mt-2 text-xs opacity-70">
                        <span>{formatTime(message.timestamp)}</span>
                        {message.intent && (
                          <span className="ml-3">
                            {message.intent} {message.confidence && `• ${(message.confidence * 100).toFixed(0)}%`}
                          </span>
                        )}
                      </div>
                    </div>
                  </div>
                </div>
              </div>
            ))}
            
            {/* Live Transcription */}
            {liveTranscript && (
              <div className="flex justify-start">
                <div className="max-w-[70%]">
                  <div className="flex items-end space-x-2">
                    <div className="w-8 h-8 bg-gray-400 rounded-full flex items-center justify-center flex-shrink-0 animate-pulse">
                      <Mic className="w-5 h-5 text-white" />
                    </div>
                    <div className="px-4 py-3 rounded-2xl rounded-bl-none bg-gray-200 text-gray-700 border border-gray-300">
                      <p className="text-sm italic">{liveTranscript}</p>
                    </div>
                  </div>
                </div>
              </div>
            )}
            
            <div ref={messagesEndRef} />
          </>
        )}
      </div>

      {/* Controls Footer */}
      <div className="bg-white border-t border-gray-200 px-6 py-4">
        {error && (
          <div className="mb-3 px-4 py-2 bg-red-50 border border-red-200 rounded-lg flex items-center justify-between">
            <p className="text-sm text-red-600">⚠️ {error}</p>
            <button onClick={() => setError(null)} className="text-red-500 hover:text-red-700">
              <X className="w-4 h-4" />
            </button>
          </div>
        )}
        
        <div className="flex items-center space-x-4">
          {/* Audio Level Indicator */}
          {voiceState === 'recording' && (
            <div className="flex-1 h-2 bg-gray-200 rounded-full overflow-hidden">
              <div 
                className="h-full bg-gradient-to-r from-green-400 to-blue-500 transition-all duration-100"
                style={{ width: `${audioLevel}%` }}
              />
            </div>
          )}
          
          {voiceState !== 'recording' && (
            <div className="flex-1">
              <p className="text-sm text-gray-500">
                {autoListen ? '🎤 Continuous mode active' : '⏸️ Press mic to talk'}
              </p>
            </div>
          )}
          
          {/* Main Control Button */}
          <button
            onClick={toggleVoice}
            disabled={voiceState === 'processing'}
            className={`relative p-4 rounded-full transition-all shadow-lg ${
              voiceState === 'recording'
                ? 'bg-red-500 hover:bg-red-600 text-white scale-110'
                : voiceState === 'speaking'
                ? 'bg-purple-500 hover:bg-purple-600 text-white'
                : voiceState === 'processing'
                ? 'bg-blue-500 text-white cursor-not-allowed'
                : 'bg-gradient-to-br from-blue-500 to-indigo-600 hover:from-blue-600 hover:to-indigo-700 text-white'
            } ${voiceState === 'processing' ? 'animate-pulse' : ''}`}
          >
            {voiceState === 'recording' ? (
              <MicOff className="w-6 h-6" />
            ) : voiceState === 'speaking' ? (
              <Volume2 className="w-6 h-6" />
            ) : (
              <Mic className="w-6 h-6" />
            )}
          </button>
          
          {/* Send Button (Manual Mode) */}
          {!autoListen && voiceState === 'recording' && (
            <button
              onClick={stopRecording}
              className="p-4 bg-green-500 hover:bg-green-600 text-white rounded-full transition-all shadow-lg"
            >
              <Send className="w-6 h-6" />
            </button>
          )}
        </div>
        
        <div className="mt-3 flex items-center justify-center space-x-2">
          <label className="flex items-center space-x-2 cursor-pointer">
            <input
              type="checkbox"
              checked={autoListen}
              onChange={(e) => setAutoListen(e.target.checked)}
              className="rounded text-blue-600 focus:ring-2 focus:ring-blue-500"
            />
            <span className="text-sm text-gray-600">Auto-send when I stop speaking</span>
          </label>
        </div>
      </div>
    </div>
  );
};

export default VoiceAssistantPanel;
