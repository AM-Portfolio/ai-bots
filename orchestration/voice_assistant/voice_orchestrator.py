"""
Voice Orchestrator - Main coordination for voice assistant

Handles the complete voice interaction flow:
1. Speech-to-Text (STT)
2. Intent Classification
3. Orchestration Routing
4. Response Formatting
5. Text-to-Speech (TTS)
"""

import logging
import io
import base64
from typing import Dict, Optional, Tuple
from pydantic import BaseModel

from shared.config import settings
from shared.llm_providers.resilient_orchestrator import ResilientLLMOrchestrator
from orchestration.summary_layer.beautifier import ResponseBeautifier
from .session_manager import SessionManager
from .intent_classifier import IntentClassifier
from .response_formatter import VoiceResponseFormatter

logger = logging.getLogger(__name__)


class VoiceRequest(BaseModel):
    """Voice request from frontend"""
    session_id: str
    audio_data: str  # Base64 encoded audio
    audio_format: str = "webm"  # webm, mp3, wav


class VoiceResponse(BaseModel):
    """Voice response to frontend"""
    session_id: str
    transcript: str
    intent: str
    confidence: float
    response_text: str
    response_audio: Optional[str] = None  # Base64 encoded audio
    orchestration_used: str
    thinking: Optional[Dict] = None


class VoiceOrchestrator:
    """
    Main orchestrator for voice assistant
    
    Coordinates:
    - Session management
    - Speech recognition
    - Intent classification  
    - Orchestration routing
    - Response generation
    - Speech synthesis
    """
    
    def __init__(self):
        logger.info("🚀 Initializing Voice Orchestrator...")
        
        # Initialize components
        self.session_manager = SessionManager()
        
        # Initialize LLM for intent and formatting
        self.llm = ResilientLLMOrchestrator()
        
        # Initialize beautifier for response cleanup
        self.beautifier = ResponseBeautifier(llm_provider=settings.llm_provider)
        
        # Initialize intent classifier
        self.intent_classifier = IntentClassifier(self.llm)
        
        # Initialize response formatter
        self.response_formatter = VoiceResponseFormatter(
            llm_orchestrator=self.llm,
            beautifier=self.beautifier,
            max_length=settings.voice_response_max_length
        )
        
        # STT/TTS clients (initialized lazily)
        self._stt_client = None
        self._tts_client = None
        
        logger.info("✅ Voice Orchestrator ready")
    
    async def process_voice_request(self, request: VoiceRequest) -> VoiceResponse:
        """
        Process a voice request end-to-end
        
        Flow:
        1. Get/create session
        2. Transcribe audio to text (STT)
        3. Classify intent
        4. Route to appropriate orchestration
        5. Format response for voice
        6. Synthesize speech (TTS)
        7. Return response
        """
        logger.info(f"🎤 Processing voice request for session: {request.session_id}")
        
        # Step 1: Get session
        session = self.session_manager.get_or_create_session(request.session_id)
        
        # Step 2: Transcribe audio
        transcript = await self._transcribe_audio(request.audio_data, request.audio_format)
        logger.info(f"📝 Transcript: {transcript}")
        
        # Add user turn to session
        self.session_manager.add_turn(request.session_id, "user", transcript)
        
        # Step 3: Classify intent
        conversation_history = self.session_manager.get_conversation_history(request.session_id)
        intent = await self.intent_classifier.classify(transcript, conversation_history)
        
        # Step 4: Route to orchestration
        response_text, thinking = await self._route_to_orchestration(
            transcript,
            intent,
            request.session_id
        )
        
        # Step 5: Format for voice
        voice_friendly_response = await self.response_formatter.format_for_voice(
            response_text,
            intent.type
        )
        
        # Add assistant turn to session
        self.session_manager.add_turn(
            request.session_id,
            "assistant",
            voice_friendly_response,
            intent=intent.type,
            orchestration=intent.orchestration
        )
        
        # Step 6: Synthesize speech
        audio_data = await self._synthesize_speech(voice_friendly_response)
        
        # Step 7: Return response
        return VoiceResponse(
            session_id=request.session_id,
            transcript=transcript,
            intent=intent.type,
            confidence=intent.confidence,
            response_text=voice_friendly_response,
            response_audio=audio_data,
            orchestration_used=intent.orchestration,
            thinking=thinking
        )
    
    async def _transcribe_audio(self, audio_base64: str, audio_format: str) -> str:
        """Transcribe audio to text using configured STT provider"""
        logger.info(f"🎧 Transcribing audio (format: {audio_format})...")
        
        try:
            if settings.voice_stt_provider == "openai":
                return await self._transcribe_openai(audio_base64, audio_format)
            elif settings.voice_stt_provider == "azure":
                return await self._transcribe_azure(audio_base64, audio_format)
            else:
                logger.warning(f"Unknown STT provider: {settings.voice_stt_provider}, using fallback")
                return "[Transcription unavailable - configure STT provider]"
        except Exception as e:
            logger.error(f"❌ STT failed: {e}")
            return f"[Transcription error: {str(e)}]"
    
    async def _transcribe_openai(self, audio_base64: str, audio_format: str) -> str:
        """Transcribe using OpenAI Whisper"""
        if not settings.openai_api_key:
            raise ValueError("OpenAI API key not configured")
        
        try:
            import openai
            
            if not self._stt_client:
                self._stt_client = openai.OpenAI(api_key=settings.openai_api_key)
            
            # Decode base64 audio
            audio_bytes = base64.b64decode(audio_base64)
            
            # Create audio file object
            audio_file = io.BytesIO(audio_bytes)
            audio_file.name = f"audio.{audio_format}"
            
            # Transcribe
            response = self._stt_client.audio.transcriptions.create(
                model=settings.openai_whisper_model,
                file=audio_file,
                language="en"
            )
            
            return response.text
            
        except ImportError:
            logger.error("❌ OpenAI library not installed. Run: pip install openai")
            return "[OpenAI library not installed]"
        except Exception as e:
            logger.error(f"❌ OpenAI Whisper error: {e}")
            raise
    
    async def _transcribe_azure(self, audio_base64: str, audio_format: str) -> str:
        """Transcribe using Azure Speech Services"""
        if not settings.azure_speech_key:
            raise ValueError("Azure Speech key not configured")
        
        # TODO: Implement Azure Speech SDK transcription when needed
        logger.warning("Azure Speech transcription not yet implemented")
        return "[Azure Speech STT not yet implemented]"
    
    async def _route_to_orchestration(self, transcript: str, intent, session_id: str) -> Tuple[str, Optional[Dict]]:
        """Route to appropriate orchestration based on intent"""
        logger.info(f"🔀 Routing to orchestration: {intent.orchestration}")
        
        thinking = {"steps": []}
        
        try:
            if intent.orchestration == "commit_workflow":
                response = await self._handle_commit_intent(transcript, intent, session_id)
                thinking["steps"].append({"step": "commit_workflow", "status": "completed"})
            
            elif intent.orchestration == "github_llm":
                response = await self._handle_github_query(transcript, intent, session_id)
                thinking["steps"].append({"step": "github_llm_query", "status": "completed"})
            
            else:  # general_llm
                response = await self._handle_general_query(transcript, intent, session_id)
                thinking["steps"].append({"step": "general_llm", "status": "completed"})
            
            return response, thinking
            
        except Exception as e:
            logger.error(f"❌ Orchestration failed: {e}")
            return f"Sorry, I encountered an error: {str(e)}", thinking
    
    async def _handle_commit_intent(self, transcript: str, intent, session_id: str) -> str:
        """Handle commit workflow"""
        # TODO: Integrate with existing commit workflow
        repo = intent.entities.get("repository", "unknown")
        return f"I understand you want to commit code to {repo}. The commit workflow integration is coming soon!"
    
    async def _handle_github_query(self, transcript: str, intent, session_id: str) -> str:
        """Handle GitHub/code queries"""
        # TODO: Integrate with existing GitHub-LLM orchestrator
        return "Let me search the codebase for you. GitHub query integration is coming soon!"
    
    async def _handle_general_query(self, transcript: str, intent, session_id: str) -> str:
        """Handle general queries"""
        conversation_history = self.session_manager.get_conversation_history(session_id)
        
        # Build messages with context
        messages = self._build_general_messages(transcript, conversation_history)
        
        # Generate response using resilient LLM
        response, metadata = await self.llm.chat_completion_with_fallback(
            messages=messages,
            temperature=0.7
        )
        
        return response
    
    def _build_general_messages(self, user_input: str, history: list) -> list:
        """Build messages for general conversation with language detection"""
        from shared.utils.language_detector import detect_language_with_confidence, get_language_instruction
        
        # Detect language from user input
        detected_lang, confidence = detect_language_with_confidence(user_input)
        lang_instruction = get_language_instruction(detected_lang)
        
        logger.info(f"🌐 Detected language: {detected_lang} (confidence: {confidence:.2f})")
        
        messages = [
            {
                "role": "system",
                "content": f"You are a helpful AI development assistant. Respond naturally and conversationally. Keep responses concise for voice interaction. {lang_instruction}"
            }
        ]
        
        # Add recent conversation history
        if history:
            for turn in history[-5:]:
                messages.append({
                    "role": turn['role'],
                    "content": turn['content']
                })
        
        # Add current user input
        messages.append({
            "role": "user",
            "content": user_input
        })
        
        return messages
    
    async def _synthesize_speech(self, text: str) -> Optional[str]:
        """Synthesize speech from text using configured TTS provider"""
        logger.info(f"🔊 Synthesizing speech (length: {len(text)})")
        
        try:
            if settings.voice_tts_provider == "openai":
                return await self._synthesize_openai(text)
            elif settings.voice_tts_provider == "azure":
                return await self._synthesize_azure(text)
            else:
                logger.warning(f"Unknown TTS provider: {settings.voice_tts_provider}")
                return None
        except Exception as e:
            logger.error(f"❌ TTS failed: {e}")
            return None
    
    async def _synthesize_openai(self, text: str) -> str:
        """Synthesize speech using OpenAI TTS"""
        if not settings.openai_api_key:
            raise ValueError("OpenAI API key not configured")
        
        try:
            import openai
            
            if not self._tts_client:
                self._tts_client = openai.OpenAI(api_key=settings.openai_api_key)
            
            # Generate speech
            response = self._tts_client.audio.speech.create(
                model=settings.openai_tts_model,
                voice=settings.openai_tts_voice,  # type: ignore
                input=text
            )
            
            # Convert to base64
            audio_bytes = response.content
            audio_base64 = base64.b64encode(audio_bytes).decode('utf-8')
            
            return audio_base64
            
        except ImportError:
            logger.error("❌ OpenAI library not installed. Run: pip install openai")
            return None
        except Exception as e:
            logger.error(f"❌ OpenAI TTS error: {e}")
            raise
    
    async def _synthesize_azure(self, text: str) -> Optional[str]:
        """Synthesize speech using Azure TTS"""
        if not settings.azure_speech_key:
            raise ValueError("Azure Speech key not configured")
        
        # TODO: Implement Azure TTS when needed
        logger.warning("Azure TTS not yet implemented")
        return None
