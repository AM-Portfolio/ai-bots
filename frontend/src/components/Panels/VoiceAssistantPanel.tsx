import { useState, useEffect, useRef } from 'react';
import { Mic, X, Minimize2, Maximize2, Volume2, VolumeX } from 'lucide-react';
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
  
  // Keep ref in sync with state for use in closures
  useEffect(() => {
    voiceStateRef.current = voiceState;
  }, [voiceState]);
  const [hasGreeted, setHasGreeted] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [audioLevel, setAudioLevel] = useState<number>(0);
  const [isMinimized, setIsMinimized] = useState(true);
  const [isMuted, setIsMuted] = useState(false);
  const [isVisible, setIsVisible] = useState(true);
  
  const mediaRecorderRef = useRef<MediaRecorder | null>(null);
  const audioChunksRef = useRef<Blob[]>([]);
  const currentAudioRef = useRef<HTMLAudioElement | null>(null);
  const silenceTimerRef = useRef<number | null>(null);
  const audioContextRef = useRef<AudioContext | null>(null);
  const analyserRef = useRef<AnalyserNode | null>(null);
  const messagesEndRef = useRef<HTMLDivElement>(null);
  const animationFrameRef = useRef<number | null>(null);
  const streamRef = useRef<MediaStream | null>(null);
  const lastAudioWhileMutedRef = useRef<Blob | null>(null);
  const voiceStateRef = useRef<VoiceState>('idle');

  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages]);

  useEffect(() => {
    if (isVisible && !sessionId) {
      initializeSession();
    }
  }, [isVisible]);
  
  // Process stored audio when unmuted
  useEffect(() => {
    const processStoredAudio = async () => {
      if (!isMuted && lastAudioWhileMutedRef.current && sessionId) {
        console.log('[Voice] 🔊 Unmuted - processing last command');
        const audioBlob = lastAudioWhileMutedRef.current;
        lastAudioWhileMutedRef.current = null;
        
        setVoiceState('processing');
        
        try {
          const reader = new FileReader();
          reader.readAsDataURL(audioBlob);
          
          reader.onloadend = async () => {
            const base64Audio = (reader.result as string).split(',')[1];
            
            console.log('[Voice] 📤 Sending stored audio to backend...');
            console.log('[Voice] Audio size (base64):', base64Audio.length, 'chars');
            
            const response = await axios.post('/api/voice/process', {
              session_id: sessionId,
              audio_data: base64Audio,
              audio_format: 'webm'
            });
            
            const { transcript, response_text, response_audio, intent, confidence } = response.data;
            
            console.log('[Voice] Transcript:', transcript);
            console.log('[Voice] Intent:', intent, `(${(confidence * 100).toFixed(1)}%)`);
            
            const userMessage: Message = {
              role: 'user',
              content: transcript || '(no speech detected)',
              timestamp: new Date()
            };
            setMessages(prev => [...prev, userMessage]);
            
            const aiMessage: Message = {
              role: 'assistant',
              content: response_text,
              timestamp: new Date(),
              intent,
              confidence
            };
            setMessages(prev => [...prev, aiMessage]);
            
            if (response_audio) {
              await playAudioResponse(response_audio);
            } else {
              speakText(response_text);
            }
            
            setVoiceState('idle');
            setTimeout(() => startRecording(), 1000);
          };
        } catch (err: any) {
          console.error('[Voice] Failed to process stored audio:', err);
          setError(err.response?.data?.detail || 'Failed to process voice');
          setVoiceState('idle');
          setTimeout(() => startRecording(), 2000);
        }
      }
    };
    
    processStoredAudio();
  }, [isMuted, sessionId]);

  useEffect(() => {
    if (!hasGreeted && sessionId) {
      const greetingMessage = "Hi! I'm ready to help. Just start speaking.";
      
      setTimeout(() => {
        const aiMessage: Message = {
          role: 'assistant',
          content: greetingMessage,
          timestamp: new Date()
        };
        setMessages([aiMessage]);
        if (!isMuted) {
          speakText(greetingMessage);
        }
        setHasGreeted(true);
        
        setTimeout(() => {
          startRecording();
        }, 1500);
      }, 500);
    }
  }, [hasGreeted, sessionId]);

  const initializeSession = async () => {
    try {
      const response = await axios.post<VoiceSession>('/api/voice/session', {
        user_id: 'web-user'
      });
      
      setSessionId(response.data.session_id);
      console.log('[Voice] Session initialized:', response.data.session_id);
    } catch (err: any) {
      console.error('[Voice] Failed to initialize session:', err);
      setError('Failed to initialize voice session');
    }
  };

  const startRecording = async () => {
    if (!sessionId || voiceState === 'recording') {
      return;
    }

    try {
      const stream = await navigator.mediaDevices.getUserMedia({ 
        audio: {
          echoCancellation: false,  // Disabled - was removing voice
          noiseSuppression: false,   // Disabled - was removing voice
          autoGainControl: true,     // Keep this for volume boost
          sampleRate: 48000
        } 
      });
      
      streamRef.current = stream;
      
      audioContextRef.current = new AudioContext();
      const source = audioContextRef.current.createMediaStreamSource(stream);
      analyserRef.current = audioContextRef.current.createAnalyser();
      analyserRef.current.fftSize = 2048;
      analyserRef.current.smoothingTimeConstant = 0.8;
      source.connect(analyserRef.current);
      
      monitorAudioLevel();
      
      let mimeType = 'audio/webm;codecs=opus';
      if (!MediaRecorder.isTypeSupported(mimeType)) {
        mimeType = 'audio/webm';
      }
      
      const mediaRecorder = new MediaRecorder(stream, {
        mimeType,
        audioBitsPerSecond: 128000
      });
      
      audioChunksRef.current = [];
      
      mediaRecorder.ondataavailable = (event) => {
        if (event.data.size > 0) {
          audioChunksRef.current.push(event.data);
          console.log('[Voice] Audio chunk:', event.data.size, 'bytes');
        }
      };
      
      mediaRecorder.onstop = async () => {
        console.log('[Voice] Recording stopped, processing...');
        await processRecordedAudio();
      };
      
      mediaRecorderRef.current = mediaRecorder;
      mediaRecorder.start(100);
      setVoiceState('recording');
      setError(null);
      
      console.log('[Voice] Recording started with', mimeType);
      
      startSilenceDetection();
      
    } catch (err: any) {
      console.error('[Voice] Failed to start recording:', err);
      setError('Microphone access denied. Please allow microphone access.');
      setVoiceState('idle');
    }
  };

  const monitorAudioLevel = () => {
    if (!analyserRef.current) return;
    
    const dataArray = new Uint8Array(analyserRef.current.frequencyBinCount);
    
    const checkLevel = () => {
      if (!analyserRef.current) return;
      
      analyserRef.current.getByteFrequencyData(dataArray);
      const average = dataArray.reduce((a, b) => a + b) / dataArray.length;
      const normalizedLevel = Math.min(100, (average / 255) * 300);
      
      setAudioLevel(normalizedLevel);
      
      // Use ref to avoid stale closure
      // Only reset timer if we detect significant audio (above background noise)
      if (voiceStateRef.current === 'recording' && normalizedLevel > 15) {
        console.log('[Voice] Audio detected, level:', normalizedLevel.toFixed(1));
        resetSilenceTimer();
      }
      
      animationFrameRef.current = requestAnimationFrame(checkLevel);
    };
    
    checkLevel();
  };

  const startSilenceDetection = () => {
    resetSilenceTimer();
  };

  const resetSilenceTimer = () => {
    if (silenceTimerRef.current) {
      clearTimeout(silenceTimerRef.current);
    }
    
    silenceTimerRef.current = window.setTimeout(() => {
      // Use ref to avoid stale closure
      if (voiceStateRef.current === 'recording' && audioChunksRef.current.length > 0) {
        console.log('[Voice] Silence detected after speech - auto-sending');
        stopRecording();
      }
    }, 3000);
  };

  const stopRecording = () => {
    if (mediaRecorderRef.current && voiceStateRef.current === 'recording') {
      if (silenceTimerRef.current) {
        clearTimeout(silenceTimerRef.current);
        silenceTimerRef.current = null;
      }
      
      if (animationFrameRef.current) {
        cancelAnimationFrame(animationFrameRef.current);
        animationFrameRef.current = null;
      }
      
      mediaRecorderRef.current.stop();
      
      if (streamRef.current) {
        streamRef.current.getTracks().forEach(track => {
          track.stop();
          console.log('[Voice] Stopped track:', track.kind);
        });
        streamRef.current = null;
      }
      
      if (audioContextRef.current) {
        audioContextRef.current.close();
        audioContextRef.current = null;
      }
      
      setAudioLevel(0);
      console.log('[Voice] Recording stopped');
    }
  };

  const processRecordedAudio = async () => {
    console.log('[Voice] Processing', audioChunksRef.current.length, 'audio chunks');
    
    if (audioChunksRef.current.length === 0) {
      console.warn('[Voice] No audio chunks to process');
      setVoiceState('idle');
      setTimeout(() => startRecording(), 1000);
      return;
    }

    const audioBlob = new Blob(audioChunksRef.current, { type: 'audio/webm' });
    console.log('[Voice] Audio blob size:', audioBlob.size, 'bytes');
    
    if (audioBlob.size < 5000) {
      console.warn('[Voice] Audio too small, likely no speech');
      setVoiceState('idle');
      setTimeout(() => startRecording(), 1000);
      return;
    }
    
    // If muted, store the audio and restart recording
    if (isMuted) {
      console.log('[Voice] 🔇 Muted - storing last command');
      lastAudioWhileMutedRef.current = audioBlob;
      setVoiceState('idle');
      setTimeout(() => startRecording(), 1000);
      return;
    }

    setVoiceState('processing');
    
    try {
      const reader = new FileReader();
      reader.readAsDataURL(audioBlob);
      
      reader.onloadend = async () => {
        const base64Audio = (reader.result as string).split(',')[1];
        
        console.log('[Voice] 📤 Sending audio to backend...');
        console.log('[Voice] Session ID:', sessionId);
        console.log('[Voice] Audio size (base64):', base64Audio.length, 'chars');
        
        const response = await axios.post('/api/voice/process', {
          session_id: sessionId,
          audio_data: base64Audio,
          audio_format: 'webm'
        });
        
        const { transcript, response_text, response_audio, intent, confidence } = response.data;
        
        console.log('[Voice] Transcript:', transcript);
        console.log('[Voice] Intent:', intent, `(${(confidence * 100).toFixed(1)}%)`);
        
        const userMessage: Message = {
          role: 'user',
          content: transcript || '(no speech detected)',
          timestamp: new Date()
        };
        setMessages(prev => [...prev, userMessage]);
        
        const aiMessage: Message = {
          role: 'assistant',
          content: response_text,
          timestamp: new Date(),
          intent,
          confidence
        };
        setMessages(prev => [...prev, aiMessage]);
        
        if (!isMuted) {
          if (response_audio) {
            await playAudioResponse(response_audio);
          } else {
            speakText(response_text);
          }
        }
        
        setTimeout(() => {
          startRecording();
        }, 1000);
      };
      
    } catch (err: any) {
      console.error('[Voice] Failed to process audio:', err);
      setError(err.response?.data?.detail || 'Failed to process voice');
      setVoiceState('idle');
      
      setTimeout(() => {
        setError(null);
        startRecording();
      }, 2000);
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
          console.log('[Voice] Playing AI response');
        };
        
        audio.onended = () => {
          setVoiceState('idle');
          URL.revokeObjectURL(url);
          console.log('[Voice] Playback complete');
          resolve();
        };
        
        audio.onerror = (err) => {
          console.error('[Voice] Playback error:', err);
          setVoiceState('idle');
          URL.revokeObjectURL(url);
          reject(err);
        };
        
        audio.play();
        
      } catch (err) {
        console.error('[Voice] Failed to decode audio:', err);
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

  const formatTime = (date: Date) => {
    return date.toLocaleTimeString('en-US', { hour: '2-digit', minute: '2-digit' });
  };

  if (!isVisible) {
    return null;
  }

  return (
    <div className="fixed bottom-6 right-6 z-50 flex flex-col">
      {/* Floating Voice Assistant */}
      <div 
        className={`bg-white rounded-2xl shadow-2xl border-2 transition-all duration-300 ${
          isMinimized ? 'w-20 h-20' : 'w-96 h-[600px]'
        } ${
          voiceState === 'recording' ? 'border-green-500' :
          voiceState === 'processing' ? 'border-blue-500' :
          voiceState === 'speaking' ? 'border-purple-500' :
          'border-gray-300'
        }`}
      >
        {/* Header */}
        <div className={`flex items-center justify-between p-4 border-b ${
          voiceState === 'recording' ? 'bg-green-50' :
          voiceState === 'processing' ? 'bg-blue-50' :
          voiceState === 'speaking' ? 'bg-purple-50' :
          'bg-gray-50'
        } rounded-t-2xl`}>
          {!isMinimized && (
            <>
              <div className="flex items-center space-x-3">
                <div className={`w-10 h-10 rounded-full flex items-center justify-center ${
                  voiceState === 'recording' ? 'bg-green-500' :
                  voiceState === 'processing' ? 'bg-blue-500' :
                  voiceState === 'speaking' ? 'bg-purple-500' :
                  'bg-gray-400'
                }`}>
                  <Mic className="w-5 h-5 text-white" />
                </div>
                <div>
                  <h3 className="font-semibold text-gray-900">Voice Assistant</h3>
                  <p className="text-xs text-gray-600">
                    {voiceState === 'recording' && 'Listening...'}
                    {voiceState === 'processing' && 'Processing...'}
                    {voiceState === 'speaking' && 'Speaking...'}
                    {voiceState === 'idle' && 'Ready'}
                  </p>
                </div>
              </div>
              <div className="flex items-center space-x-2">
                <button
                  onClick={() => setIsMuted(!isMuted)}
                  className={`relative p-2 hover:bg-gray-200 rounded-lg transition-colors ${
                    isMuted && lastAudioWhileMutedRef.current ? 'bg-orange-100' : ''
                  }`}
                  title={isMuted ? (lastAudioWhileMutedRef.current ? 'Unmute to send command' : 'Unmute') : 'Mute'}
                >
                  {isMuted ? (
                    <VolumeX className={`w-4 h-4 ${lastAudioWhileMutedRef.current ? 'text-orange-600' : 'text-gray-600'}`} />
                  ) : (
                    <Volume2 className="w-4 h-4 text-gray-600" />
                  )}
                  {isMuted && lastAudioWhileMutedRef.current && (
                    <span className="absolute -top-1 -right-1 w-3 h-3 bg-orange-500 rounded-full animate-pulse"></span>
                  )}
                </button>
                <button
                  onClick={() => setIsMinimized(!isMinimized)}
                  className="p-2 hover:bg-gray-200 rounded-lg transition-colors"
                >
                  {isMinimized ? (
                    <Maximize2 className="w-4 h-4 text-gray-600" />
                  ) : (
                    <Minimize2 className="w-4 h-4 text-gray-600" />
                  )}
                </button>
                <button
                  onClick={() => {
                    stopRecording();
                    setIsVisible(false);
                  }}
                  className="p-2 hover:bg-gray-200 rounded-lg transition-colors"
                >
                  <X className="w-4 h-4 text-gray-600" />
                </button>
              </div>
            </>
          )}
          {isMinimized && (
            <button
              onClick={() => setIsMinimized(false)}
              className="w-full h-full flex items-center justify-center"
            >
              <Mic className={`w-8 h-8 ${
                voiceState === 'recording' ? 'text-green-500 animate-pulse' :
                voiceState === 'processing' ? 'text-blue-500 animate-pulse' :
                voiceState === 'speaking' ? 'text-purple-500 animate-pulse' :
                'text-gray-400'
              }`} />
            </button>
          )}
        </div>

        {!isMinimized && (
          <>
            {/* Messages */}
            <div className="flex-1 overflow-y-auto p-4 space-y-3 bg-gradient-to-b from-gray-50 to-white">
              {messages.length === 0 && (
                <div className="text-center text-gray-400 text-sm mt-20">
                  Start speaking to begin conversation...
                </div>
              )}
              {messages.map((msg, idx) => (
                <div
                  key={idx}
                  className={`flex ${msg.role === 'user' ? 'justify-end' : 'justify-start'} items-start space-x-2`}
                >
                  {msg.role === 'assistant' && (
                    <div className="w-8 h-8 rounded-full bg-gradient-to-br from-blue-500 to-purple-600 flex items-center justify-center flex-shrink-0">
                      <Mic className="w-4 h-4 text-white" />
                    </div>
                  )}
                  <div
                    className={`max-w-[75%] rounded-2xl px-4 py-2 ${
                      msg.role === 'user'
                        ? 'bg-blue-500 text-white'
                        : 'bg-white border border-gray-200 text-gray-900'
                    }`}
                  >
                    <p className="text-sm">{msg.content}</p>
                    <div className="flex items-center justify-between mt-1 text-xs opacity-70">
                      <span>{formatTime(msg.timestamp)}</span>
                      {msg.intent && (
                        <span className="ml-2">
                          {msg.intent} • {((msg.confidence || 0) * 100).toFixed(0)}%
                        </span>
                      )}
                    </div>
                  </div>
                </div>
              ))}
              <div ref={messagesEndRef} />
            </div>

            {/* Voice Activity Indicator */}
            <div className="p-4 border-t bg-white rounded-b-2xl">
              {/* Audio Level Visualizer */}
              {voiceState === 'recording' && (
                <div className="mb-3">
                  <div className="flex items-center justify-center space-x-1 h-12">
                    {[...Array(20)].map((_, i) => {
                      const height = Math.max(10, audioLevel * (Math.random() * 0.5 + 0.75));
                      return (
                        <div
                          key={i}
                          className="w-1 bg-gradient-to-t from-green-500 to-green-400 rounded-full transition-all duration-100"
                          style={{
                            height: `${height}%`,
                            opacity: audioLevel > 5 ? 0.8 : 0.3
                          }}
                        />
                      );
                    })}
                  </div>
                  <p className="text-xs text-center text-gray-600 mt-2">
                    Speak now • Auto-sends after 3s silence
                  </p>
                </div>
              )}

              {/* Status Indicator */}
              <div className="flex items-center justify-center">
                <div className={`px-4 py-2 rounded-full text-sm font-medium ${
                  voiceState === 'recording' ? 'bg-green-100 text-green-700' :
                  voiceState === 'processing' ? 'bg-blue-100 text-blue-700' :
                  voiceState === 'speaking' ? 'bg-purple-100 text-purple-700' :
                  'bg-gray-100 text-gray-700'
                }`}>
                  {voiceState === 'recording' && '🎤 Listening for your voice...'}
                  {voiceState === 'processing' && '⚡ Processing your request...'}
                  {voiceState === 'speaking' && '🔊 AI is responding...'}
                  {voiceState === 'idle' && '✨ Continuous conversation mode'}
                </div>
              </div>

              {/* Error Display */}
              {error && (
                <div className="mt-3 p-3 bg-red-50 border border-red-200 rounded-lg flex items-center justify-between">
                  <p className="text-xs text-red-700">{error}</p>
                  <button
                    onClick={() => setError(null)}
                    className="text-red-500 hover:text-red-700"
                  >
                    <X className="w-4 h-4" />
                  </button>
                </div>
              )}
            </div>
          </>
        )}
      </div>
    </div>
  );
};

export default VoiceAssistantPanel;
