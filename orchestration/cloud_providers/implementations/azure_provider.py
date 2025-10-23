"""
Azure Cloud Provider Implementation

Wraps existing Azure AI services (Speech, Translation, Model Deployments)
to implement cloud-agnostic provider templates.
"""

from typing import Optional, Dict, Any, List
import base64
from ..templates.base import (
    CloudProvider,
    STTProvider,
    TTSProvider,
    TranslationProvider,
    LLMProvider,
    ProviderConfig,
    ProviderCapability,
    STTResult,
    TTSResult,
    TranslationResult,
    LLMResult
)
from shared.azure_services.speech_service import AzureSpeechService
from shared.azure_services.translation_service import AzureTranslationService
from shared.azure_services.model_deployment_service import AzureModelDeploymentService
from shared.logger import get_logger

logger = get_logger(__name__)


class AzureProvider(CloudProvider, STTProvider, TTSProvider, TranslationProvider, LLMProvider):
    """
    Azure Cloud Provider
    
    Unified provider implementing all Azure AI capabilities:
    - Speech-to-Text (Azure Speech Service)
    - Text-to-Speech (Azure Speech Service)
    - Translation (Azure Translator)
    - LLM Chat (Azure OpenAI)
    - Embeddings (Azure OpenAI)
    """
    
    def __init__(self, config: ProviderConfig, capability: ProviderCapability):
        super().__init__(config)
        self.capability = capability
        
        self.speech_service = AzureSpeechService()
        self.translation_service = AzureTranslationService()
        self.model_service = AzureModelDeploymentService()
        
        self._capabilities = [
            ProviderCapability.SPEECH_TO_TEXT,
            ProviderCapability.TEXT_TO_SPEECH,
            ProviderCapability.TRANSLATION,
            ProviderCapability.LLM_CHAT,
            ProviderCapability.LLM_EMBEDDING,
            ProviderCapability.AUDIO_TRANSCRIPTION,
            ProviderCapability.DIARIZATION,
        ]
        
        logger.info(f"🔷 Azure Provider initialized for {capability.value}")
    
    def is_available(self) -> bool:
        """Check if Azure services are available for the requested capability"""
        if self.capability == ProviderCapability.SPEECH_TO_TEXT:
            return self.speech_service.is_available()
        
        elif self.capability == ProviderCapability.TEXT_TO_SPEECH:
            return self.speech_service.is_available()
        
        elif self.capability == ProviderCapability.TRANSLATION:
            return self.translation_service.is_available()
        
        elif self.capability in [ProviderCapability.LLM_CHAT, ProviderCapability.LLM_EMBEDDING]:
            return self.model_service.is_available()
        
        return False
    
    def get_capabilities(self) -> List[ProviderCapability]:
        """Get supported capabilities"""
        return self._capabilities
    
    async def health_check(self) -> Dict[str, Any]:
        """Perform health check on Azure services"""
        return {
            "provider": "azure",
            "speech": {
                "available": self.speech_service.is_available(),
                "region": self.speech_service.speech_region if self.speech_service.is_available() else None
            },
            "translation": {
                "available": self.translation_service.is_available(),
                "endpoint": self.translation_service.translation_endpoint if self.translation_service.is_available() else None
            },
            "models": {
                "available": self.model_service.is_available(),
                "endpoint": self.model_service.endpoint if self.model_service.is_available() else None
            }
        }
    
    async def transcribe(
        self,
        audio_data: bytes,
        audio_format: str = "wav",
        language: Optional[str] = None,
        enable_auto_detection: bool = True
    ) -> STTResult:
        """Transcribe audio using Azure Speech Service"""
        audio_base64 = base64.b64encode(audio_data).decode('utf-8')
        
        text, detected_lang = await self.speech_service.transcribe_audio(
            audio_data=audio_base64,
            audio_format=audio_format
        )
        
        return STTResult(
            text=text,
            detected_language=detected_lang,
            confidence=None,
            method="azure_speech",
            metadata={"provider": "azure", "format": audio_format}
        )
    
    async def synthesize(
        self,
        text: str,
        language: Optional[str] = None,
        voice: Optional[str] = None,
        audio_format: str = "mp3"
    ) -> TTSResult:
        """Convert text to speech using Azure Speech Service"""
        raise NotImplementedError("Azure TTS not yet implemented in base service")
    
    async def translate(
        self,
        text: str,
        target_language: str,
        source_language: Optional[str] = None,
        detect_language: bool = True
    ) -> TranslationResult:
        """Translate text using Azure Translator"""
        translated_text, detected_lang = await self.translation_service.translate(
            text=text,
            target_language=target_language,
            source_language=source_language
        )
        
        return TranslationResult(
            translated_text=translated_text,
            source_language=detected_lang,
            target_language=target_language,
            confidence=None,
            metadata={"provider": "azure"}
        )
    
    async def detect_language(self, text: str) -> Dict[str, Any]:
        """Detect language using Azure Translator"""
        detected_lang, confidence = await self.translation_service.detect_language(text)
        return {
            "language": detected_lang,
            "confidence": confidence
        }
    
    async def chat_completion(
        self,
        messages: List[Dict[str, str]],
        temperature: float = 0.7,
        max_tokens: int = 2000,
        stream: bool = False
    ) -> LLMResult:
        """Generate chat completion using Azure OpenAI"""
        result = await self.model_service.chat_completion(
            messages=messages,
            temperature=temperature,
            max_tokens=max_tokens
        )
        
        if isinstance(result, dict):
            content = result.get("content", "")
            model = result.get("model", self.config.additional_config.get("chat_model", "gpt-4.1-mini"))
            usage = result.get("usage")
            metadata = result
        else:
            content = str(result)
            model = self.config.additional_config.get("chat_model", "gpt-4.1-mini") if self.config.additional_config else "gpt-4.1-mini"
            usage = None
            metadata = {"provider": "azure"}
        
        return LLMResult(
            content=content,
            model=model,
            usage=usage,
            metadata=metadata
        )
    
    async def generate_embedding(
        self,
        text: str,
        model: Optional[str] = None
    ) -> List[float]:
        """Generate embedding using Azure OpenAI"""
        raise NotImplementedError("Azure embeddings not yet implemented in model deployment service")
    
    @property
    def model_name(self) -> str:
        """Get current model name"""
        if self.config.additional_config:
            return self.config.additional_config.get("chat_model", "gpt-4.1-mini")
        return "gpt-4.1-mini"
