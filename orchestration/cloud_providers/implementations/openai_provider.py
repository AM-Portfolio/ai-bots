"""
OpenAI Provider Implementation

Implements cloud-agnostic templates for OpenAI services (Whisper STT, TTS, Chat).
"""

from typing import Optional, Dict, Any, List
import base64
from ..templates.base import (
    CloudProvider,
    STTProvider,
    TTSProvider,
    LLMProvider,
    ProviderConfig,
    ProviderCapability,
    STTResult,
    TTSResult,
    LLMResult
)
from shared.logger import get_logger

logger = get_logger(__name__)


class OpenAIProvider(CloudProvider, STTProvider, TTSProvider, LLMProvider):
    """
    OpenAI Provider
    
    Implements OpenAI capabilities:
    - Speech-to-Text (Whisper)
    - Text-to-Speech (TTS)
    - Chat Completion (GPT models)
    """
    
    def __init__(self, config: ProviderConfig, capability: ProviderCapability):
        super().__init__(config)
        self.capability = capability
        
        self._capabilities = [
            ProviderCapability.SPEECH_TO_TEXT,
            ProviderCapability.TEXT_TO_SPEECH,
            ProviderCapability.LLM_CHAT,
        ]
        
        logger.info(f"🟦 OpenAI Provider initialized for {capability.value}")
    
    def is_available(self) -> bool:
        """Check if OpenAI is configured"""
        return bool(self.config.api_key)
    
    def get_capabilities(self) -> List[ProviderCapability]:
        """Get supported capabilities"""
        return self._capabilities
    
    async def health_check(self) -> Dict[str, Any]:
        """Perform health check on OpenAI"""
        return {
            "provider": "openai",
            "available": self.is_available(),
            "model": self.config.model,
        }
    
    async def transcribe(
        self,
        audio_data: bytes,
        audio_format: str = "wav",
        language: Optional[str] = None,
        enable_auto_detection: bool = True
    ) -> STTResult:
        """Transcribe audio using OpenAI Whisper"""
        try:
            from openai import AsyncOpenAI
            
            client = AsyncOpenAI(api_key=self.config.api_key)
            
            import io
            audio_file = io.BytesIO(audio_data)
            audio_file.name = f"audio.{audio_format}"
            
            response = await client.audio.transcriptions.create(
                model=self.config.model or "whisper-1",
                file=audio_file,
                language=language if language else None
            )
            
            return STTResult(
                text=response.text,
                detected_language=language,
                confidence=None,
                method="openai_whisper",
                metadata={"provider": "openai"}
            )
        
        except Exception as e:
            logger.error(f"OpenAI Whisper transcription failed: {e}")
            raise
    
    async def synthesize(
        self,
        text: str,
        language: Optional[str] = None,
        voice: Optional[str] = None,
        audio_format: str = "mp3"
    ) -> TTSResult:
        """Convert text to speech using OpenAI TTS"""
        try:
            from openai import AsyncOpenAI
            
            client = AsyncOpenAI(api_key=self.config.api_key)
            
            tts_config = self.config.additional_config or {}
            tts_model = tts_config.get("tts_model", "tts-1")
            tts_voice = voice or tts_config.get("tts_voice", "alloy")
            
            response = await client.audio.speech.create(
                model=tts_model,
                voice=tts_voice,
                input=text
            )
            
            audio_data = response.content
            
            return TTSResult(
                audio_data=audio_data,
                audio_format=audio_format,
                metadata={"provider": "openai", "voice": tts_voice, "model": tts_model}
            )
        
        except Exception as e:
            logger.error(f"OpenAI TTS synthesis failed: {e}")
            raise
    
    async def chat_completion(
        self,
        messages: List[Dict[str, str]],
        temperature: float = 0.7,
        max_tokens: int = 2000,
        stream: bool = False
    ) -> LLMResult:
        """Generate chat completion using OpenAI"""
        try:
            from openai import AsyncOpenAI
            
            client = AsyncOpenAI(api_key=self.config.api_key)
            
            response = await client.chat.completions.create(
                model=self.config.model or "gpt-4.1-mini",
                messages=messages,
                temperature=temperature,
                max_tokens=max_tokens,
                stream=stream
            )
            
            if stream:
                return response
            
            content = response.choices[0].message.content
            
            return LLMResult(
                content=content,
                model=response.model,
                usage={
                    "prompt_tokens": response.usage.prompt_tokens,
                    "completion_tokens": response.usage.completion_tokens,
                    "total_tokens": response.usage.total_tokens
                } if response.usage else None,
                metadata={"provider": "openai"}
            )
        
        except Exception as e:
            logger.error(f"OpenAI chat completion failed: {e}")
            raise
    
    async def generate_embedding(
        self,
        text: str,
        model: Optional[str] = None
    ) -> List[float]:
        """Generate embedding using OpenAI"""
        try:
            from openai import AsyncOpenAI
            
            client = AsyncOpenAI(api_key=self.config.api_key)
            
            response = await client.embeddings.create(
                model=model or "text-embedding-3-small",
                input=text
            )
            
            return response.data[0].embedding
        
        except Exception as e:
            logger.error(f"OpenAI embedding generation failed: {e}")
            raise
    
    @property
    def model_name(self) -> str:
        """Get current model name"""
        return self.config.model or "gpt-4.1-mini"
