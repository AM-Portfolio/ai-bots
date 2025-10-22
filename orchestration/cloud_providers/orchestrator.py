"""
Cloud Orchestration Manager

Central orchestrator for routing AI workflows to appropriate cloud providers.
Implements automatic fallback, health tracking, and provider-agnostic workflow execution.
"""

from typing import Optional, Dict, Any, List
import time
from .factory import ProviderFactory, get_fallback_chain, get_provider_preference
from .templates.base import (
    STTProvider,
    TTSProvider,
    TranslationProvider,
    LLMProvider,
    ProviderCapability,
    STTResult,
    TTSResult,
    TranslationResult,
    LLMResult
)
from shared.logger import logger


class CloudOrchestrator:
    """
    Central orchestrator for cloud-agnostic AI workflows
    
    Routes requests to appropriate providers based on configuration,
    implements automatic fallback chains, and tracks provider health.
    """
    
    def __init__(self):
        self.factory = ProviderFactory
        self._health_status: Dict[str, Dict[str, Any]] = {}
    
    async def speech_to_text(
        self,
        audio_data: bytes,
        audio_format: str = "wav",
        language: Optional[str] = None,
        enable_auto_detection: bool = True,
        preferred_provider: Optional[str] = None
    ) -> STTResult:
        """
        Transcribe audio to text using best available provider
        
        Args:
            audio_data: Audio data in bytes
            audio_format: Audio format (wav, mp3, etc.)
            language: Language code or None for auto-detection
            enable_auto_detection: Enable automatic language detection
            preferred_provider: Force specific provider (overrides config)
            
        Returns:
            STTResult with transcription and metadata
            
        Raises:
            RuntimeError: If all providers fail
        """
        capability = ProviderCapability.SPEECH_TO_TEXT
        
        if preferred_provider:
            chain = [preferred_provider]
        else:
            chain = get_fallback_chain(capability)
        
        logger.info(f"🎙️  STT Request - Provider chain: {chain}")
        
        errors = []
        
        for provider_name in chain:
            try:
                logger.info(f"   Trying provider: {provider_name}")
                
                provider: STTProvider = self.factory.create_provider(
                    provider_name=provider_name,
                    capability=capability
                )
                
                if not provider.is_available():
                    logger.warning(f"   ⚠️  {provider_name} not available")
                    continue
                
                start_time = time.time()
                
                result = await provider.transcribe(
                    audio_data=audio_data,
                    audio_format=audio_format,
                    language=language,
                    enable_auto_detection=enable_auto_detection
                )
                
                duration_ms = (time.time() - start_time) * 1000
                result.duration_ms = duration_ms
                
                if not result.metadata:
                    result.metadata = {}
                result.metadata['provider'] = provider_name
                
                logger.info(f"   ✅ STT successful with {provider_name} ({duration_ms:.0f}ms)")
                
                return result
                
            except Exception as e:
                error_msg = f"{provider_name}: {str(e)}"
                errors.append(error_msg)
                logger.warning(f"   ❌ {provider_name} failed: {e}")
                continue
        
        error_summary = "; ".join(errors)
        raise RuntimeError(f"All STT providers failed: {error_summary}")
    
    async def text_to_speech(
        self,
        text: str,
        language: Optional[str] = None,
        voice: Optional[str] = None,
        audio_format: str = "mp3",
        preferred_provider: Optional[str] = None
    ) -> TTSResult:
        """
        Convert text to speech using best available provider
        
        Args:
            text: Text to synthesize
            language: Target language code
            voice: Voice ID or name
            audio_format: Output audio format
            preferred_provider: Force specific provider (overrides config)
            
        Returns:
            TTSResult with audio data and metadata
            
        Raises:
            RuntimeError: If all providers fail
        """
        capability = ProviderCapability.TEXT_TO_SPEECH
        
        if preferred_provider:
            chain = [preferred_provider]
        else:
            chain = get_fallback_chain(capability)
        
        logger.info(f"🔊 TTS Request - Provider chain: {chain}")
        
        errors = []
        
        for provider_name in chain:
            try:
                logger.info(f"   Trying provider: {provider_name}")
                
                provider: TTSProvider = self.factory.create_provider(
                    provider_name=provider_name,
                    capability=capability
                )
                
                if not provider.is_available():
                    logger.warning(f"   ⚠️  {provider_name} not available")
                    continue
                
                start_time = time.time()
                
                result = await provider.synthesize(
                    text=text,
                    language=language,
                    voice=voice,
                    audio_format=audio_format
                )
                
                duration_ms = (time.time() - start_time) * 1000
                result.duration_ms = duration_ms
                
                if not result.metadata:
                    result.metadata = {}
                result.metadata['provider'] = provider_name
                
                logger.info(f"   ✅ TTS successful with {provider_name} ({duration_ms:.0f}ms)")
                
                return result
                
            except Exception as e:
                error_msg = f"{provider_name}: {str(e)}"
                errors.append(error_msg)
                logger.warning(f"   ❌ {provider_name} failed: {e}")
                continue
        
        error_summary = "; ".join(errors)
        raise RuntimeError(f"All TTS providers failed: {error_summary}")
    
    async def translate_text(
        self,
        text: str,
        target_language: str,
        source_language: Optional[str] = None,
        detect_language: bool = True,
        preferred_provider: Optional[str] = None
    ) -> TranslationResult:
        """
        Translate text using best available provider
        
        Args:
            text: Text to translate
            target_language: Target language code
            source_language: Source language code (None for auto-detection)
            detect_language: Enable automatic language detection
            preferred_provider: Force specific provider (overrides config)
            
        Returns:
            TranslationResult with translated text and metadata
            
        Raises:
            RuntimeError: If all providers fail
        """
        capability = ProviderCapability.TRANSLATION
        
        if preferred_provider:
            chain = [preferred_provider]
        else:
            chain = get_fallback_chain(capability)
        
        logger.info(f"🌐 Translation Request - Provider chain: {chain}")
        
        errors = []
        
        for provider_name in chain:
            try:
                logger.info(f"   Trying provider: {provider_name}")
                
                provider: TranslationProvider = self.factory.create_provider(
                    provider_name=provider_name,
                    capability=capability
                )
                
                if not provider.is_available():
                    logger.warning(f"   ⚠️  {provider_name} not available")
                    continue
                
                start_time = time.time()
                
                result = await provider.translate(
                    text=text,
                    target_language=target_language,
                    source_language=source_language,
                    detect_language=detect_language
                )
                
                duration_ms = (time.time() - start_time) * 1000
                result.duration_ms = duration_ms
                
                if not result.metadata:
                    result.metadata = {}
                result.metadata['provider'] = provider_name
                
                logger.info(f"   ✅ Translation successful with {provider_name} ({duration_ms:.0f}ms)")
                
                return result
                
            except Exception as e:
                error_msg = f"{provider_name}: {str(e)}"
                errors.append(error_msg)
                logger.warning(f"   ❌ {provider_name} failed: {e}")
                continue
        
        error_summary = "; ".join(errors)
        raise RuntimeError(f"All translation providers failed: {error_summary}")
    
    async def chat_completion(
        self,
        messages: List[Dict[str, str]],
        temperature: float = 0.7,
        max_tokens: int = 2000,
        stream: bool = False,
        preferred_provider: Optional[str] = None
    ) -> LLMResult:
        """
        Generate chat completion using best available LLM provider
        
        Args:
            messages: List of message dicts with 'role' and 'content'
            temperature: Sampling temperature
            max_tokens: Maximum tokens in response
            stream: Enable streaming response
            preferred_provider: Force specific provider (overrides config)
            
        Returns:
            LLMResult with generated content and metadata
            
        Raises:
            RuntimeError: If all providers fail
        """
        capability = ProviderCapability.LLM_CHAT
        
        if preferred_provider:
            chain = [preferred_provider]
        else:
            chain = get_fallback_chain(capability)
        
        logger.info(f"💬 Chat Request - Provider chain: {chain}")
        
        errors = []
        
        for provider_name in chain:
            try:
                logger.info(f"   Trying provider: {provider_name}")
                
                provider: LLMProvider = self.factory.create_provider(
                    provider_name=provider_name,
                    capability=capability
                )
                
                if not provider.is_available():
                    logger.warning(f"   ⚠️  {provider_name} not available")
                    continue
                
                start_time = time.time()
                
                result = await provider.chat_completion(
                    messages=messages,
                    temperature=temperature,
                    max_tokens=max_tokens,
                    stream=stream
                )
                
                duration_ms = (time.time() - start_time) * 1000
                result.duration_ms = duration_ms
                
                if not result.metadata:
                    result.metadata = {}
                result.metadata['provider'] = provider_name
                
                logger.info(f"   ✅ Chat completion successful with {provider_name} ({duration_ms:.0f}ms)")
                
                return result
                
            except Exception as e:
                error_msg = f"{provider_name}: {str(e)}"
                errors.append(error_msg)
                logger.warning(f"   ❌ {provider_name} failed: {e}")
                continue
        
        error_summary = "; ".join(errors)
        raise RuntimeError(f"All LLM providers failed: {error_summary}")
    
    async def get_orchestrator_status(self) -> Dict[str, Any]:
        """
        Get status of all providers and capabilities
        
        Returns:
            Dictionary with provider availability and health status
        """
        status = {
            "providers": {},
            "capabilities": {},
            "config": {
                "stt_provider": get_provider_preference(ProviderCapability.SPEECH_TO_TEXT),
                "tts_provider": get_provider_preference(ProviderCapability.TEXT_TO_SPEECH),
                "translation_provider": get_provider_preference(ProviderCapability.TRANSLATION),
                "llm_chat_provider": get_provider_preference(ProviderCapability.LLM_CHAT),
                "llm_embedding_provider": get_provider_preference(ProviderCapability.LLM_EMBEDDING),
            }
        }
        
        for capability in ProviderCapability:
            available_providers = self.factory.get_available_providers(capability)
            fallback_chain = get_fallback_chain(capability)
            
            status["capabilities"][capability.value] = {
                "available_providers": available_providers,
                "fallback_chain": fallback_chain,
                "count": len(available_providers)
            }
        
        provider_names = ["azure", "together", "openai"]
        
        for provider_name in provider_names:
            try:
                config = self.factory._auto_detect_config(provider_name)
                status["providers"][provider_name] = {
                    "configured": bool(config.api_key or config.endpoint),
                    "capabilities": []
                }
                
                for capability in ProviderCapability:
                    if provider_name in self.factory.get_available_providers(capability):
                        status["providers"][provider_name]["capabilities"].append(capability.value)
                
            except Exception as e:
                status["providers"][provider_name] = {
                    "configured": False,
                    "error": str(e)
                }
        
        return status


orchestrator = CloudOrchestrator()
