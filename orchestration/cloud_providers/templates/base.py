"""
Cloud Provider Base Templates

Abstract base classes defining interfaces for cloud AI services.
All provider implementations must implement these interfaces for orchestration compatibility.
"""

from abc import ABC, abstractmethod
from typing import Optional, Dict, Any, List
from enum import Enum
from dataclasses import dataclass


class ProviderCapability(Enum):
    """Capabilities that a cloud provider can support"""
    SPEECH_TO_TEXT = "stt"
    TEXT_TO_SPEECH = "tts"
    TRANSLATION = "translation"
    LLM_CHAT = "llm_chat"
    LLM_EMBEDDING = "llm_embedding"
    AUDIO_TRANSCRIPTION = "audio_transcription"
    DIARIZATION = "diarization"
    VISION = "vision"


@dataclass
class ProviderConfig:
    """Configuration for a cloud provider"""
    provider_name: str
    api_key: Optional[str] = None
    endpoint: Optional[str] = None
    region: Optional[str] = None
    model: Optional[str] = None
    deployment_name: Optional[str] = None
    api_version: Optional[str] = None
    additional_config: Optional[Dict[str, Any]] = None


@dataclass
class STTResult:
    """Result from Speech-to-Text operation"""
    text: str
    detected_language: Optional[str] = None
    confidence: Optional[float] = None
    duration_ms: Optional[float] = None
    method: Optional[str] = None
    metadata: Optional[Dict[str, Any]] = None


@dataclass
class TTSResult:
    """Result from Text-to-Speech operation"""
    audio_data: bytes
    audio_format: str
    duration_ms: Optional[float] = None
    metadata: Optional[Dict[str, Any]] = None


@dataclass
class TranslationResult:
    """Result from translation operation"""
    translated_text: str
    source_language: str
    target_language: str
    confidence: Optional[float] = None
    duration_ms: Optional[float] = None
    metadata: Optional[Dict[str, Any]] = None


@dataclass
class LLMResult:
    """Result from LLM operation"""
    content: str
    model: str
    usage: Optional[Dict[str, int]] = None
    duration_ms: Optional[float] = None
    metadata: Optional[Dict[str, Any]] = None


class CloudProvider(ABC):
    """Base class for all cloud providers"""
    
    def __init__(self, config: ProviderConfig):
        self.config = config
        self._capabilities: List[ProviderCapability] = []
    
    @property
    def provider_name(self) -> str:
        """Get provider name"""
        return self.config.provider_name
    
    @abstractmethod
    def is_available(self) -> bool:
        """Check if provider is configured and available"""
        pass
    
    @abstractmethod
    def get_capabilities(self) -> List[ProviderCapability]:
        """Get list of supported capabilities"""
        pass
    
    def supports_capability(self, capability: ProviderCapability) -> bool:
        """Check if provider supports a specific capability"""
        return capability in self.get_capabilities()
    
    @abstractmethod
    async def health_check(self) -> Dict[str, Any]:
        """Perform health check on provider services"""
        pass


class STTProvider(ABC):
    """Abstract base class for Speech-to-Text providers"""
    
    @abstractmethod
    async def transcribe(
        self,
        audio_data: bytes,
        audio_format: str = "wav",
        language: Optional[str] = None,
        enable_auto_detection: bool = True
    ) -> STTResult:
        """
        Transcribe audio to text
        
        Args:
            audio_data: Audio data in bytes
            audio_format: Audio format (wav, mp3, etc.)
            language: Language code (e.g., 'en', 'hi') or None for auto-detection
            enable_auto_detection: Enable automatic language detection
            
        Returns:
            STTResult with transcription and metadata
        """
        pass
    
    @abstractmethod
    def is_available(self) -> bool:
        """Check if STT service is available"""
        pass


class TTSProvider(ABC):
    """Abstract base class for Text-to-Speech providers"""
    
    @abstractmethod
    async def synthesize(
        self,
        text: str,
        language: Optional[str] = None,
        voice: Optional[str] = None,
        audio_format: str = "mp3"
    ) -> TTSResult:
        """
        Convert text to speech
        
        Args:
            text: Text to synthesize
            language: Target language code
            voice: Voice ID or name
            audio_format: Output audio format
            
        Returns:
            TTSResult with audio data and metadata
        """
        pass
    
    @abstractmethod
    def is_available(self) -> bool:
        """Check if TTS service is available"""
        pass


class TranslationProvider(ABC):
    """Abstract base class for Translation providers"""
    
    @abstractmethod
    async def translate(
        self,
        text: str,
        target_language: str,
        source_language: Optional[str] = None,
        detect_language: bool = True
    ) -> TranslationResult:
        """
        Translate text to target language
        
        Args:
            text: Text to translate
            target_language: Target language code
            source_language: Source language code (None for auto-detection)
            detect_language: Enable automatic language detection
            
        Returns:
            TranslationResult with translated text and metadata
        """
        pass
    
    @abstractmethod
    async def detect_language(self, text: str) -> Dict[str, Any]:
        """
        Detect language of text
        
        Args:
            text: Text to analyze
            
        Returns:
            Dictionary with detected language and confidence
        """
        pass
    
    @abstractmethod
    def is_available(self) -> bool:
        """Check if translation service is available"""
        pass


class LLMProvider(ABC):
    """Abstract base class for LLM providers"""
    
    @abstractmethod
    async def chat_completion(
        self,
        messages: List[Dict[str, str]],
        temperature: float = 0.7,
        max_tokens: int = 2000,
        stream: bool = False
    ) -> LLMResult:
        """
        Generate chat completion
        
        Args:
            messages: List of message dicts with 'role' and 'content'
            temperature: Sampling temperature
            max_tokens: Maximum tokens in response
            stream: Enable streaming response
            
        Returns:
            LLMResult with generated content and metadata
        """
        pass
    
    @abstractmethod
    async def generate_embedding(
        self,
        text: str,
        model: Optional[str] = None
    ) -> List[float]:
        """
        Generate text embedding
        
        Args:
            text: Text to embed
            model: Embedding model name
            
        Returns:
            List of embedding values
        """
        pass
    
    @abstractmethod
    def is_available(self) -> bool:
        """Check if LLM service is available"""
        pass
    
    @property
    @abstractmethod
    def model_name(self) -> str:
        """Get current model name"""
        pass
