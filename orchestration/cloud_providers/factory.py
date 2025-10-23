"""
Cloud Provider Factory

Factory pattern for creating cloud provider instances based on configuration.
Supports multiple providers (Azure, Together AI, OpenAI) with automatic fallback.
"""

from typing import Optional, Dict, Any, List
from .templates.base import (
    CloudProvider,
    STTProvider,
    TTSProvider,
    TranslationProvider,
    LLMProvider,
    ProviderConfig,
    ProviderCapability
)
from shared.config import settings
from shared.logger import get_logger

logger = get_logger(__name__)


class ProviderFactory:
    """Factory for creating cloud provider instances"""
    
    _provider_registry: Dict[str, type] = {}
    _instances: Dict[str, Any] = {}
    
    @classmethod
    def register_provider(cls, provider_name: str, provider_class: type):
        """
        Register a provider implementation
        
        Args:
            provider_name: Name identifier for the provider (e.g., 'azure', 'together', 'openai')
            provider_class: Provider class to instantiate
        """
        cls._provider_registry[provider_name.lower()] = provider_class
        logger.info(f"✅ Registered cloud provider: {provider_name}")
    
    @classmethod
    def create_provider(
        cls,
        provider_name: str,
        capability: ProviderCapability,
        config: Optional[ProviderConfig] = None
    ) -> Any:
        """
        Create a provider instance for a specific capability
        
        Args:
            provider_name: Name of the provider ('azure', 'together', 'openai')
            capability: Required capability (STT, TTS, Translation, LLM, etc.)
            config: Optional provider configuration (auto-detected from ENV if not provided)
            
        Returns:
            Provider instance implementing the required capability
            
        Raises:
            ValueError: If provider not registered or doesn't support capability
        """
        provider_name = provider_name.lower()
        
        if provider_name not in cls._provider_registry:
            raise ValueError(f"Provider '{provider_name}' not registered")
        
        provider_class = cls._provider_registry[provider_name]
        
        if config is None:
            config = cls._auto_detect_config(provider_name)
        
        cache_key = f"{provider_name}:{capability.value}"
        
        if cache_key in cls._instances:
            logger.debug(f"Using cached provider instance: {cache_key}")
            return cls._instances[cache_key]
        
        instance = provider_class(config=config, capability=capability)
        
        cls._instances[cache_key] = instance
        logger.info(f"✅ Created provider instance: {provider_name} ({capability.value})")
        
        return instance
    
    @classmethod
    def _auto_detect_config(cls, provider_name: str) -> ProviderConfig:
        """
        Auto-detect provider configuration from environment variables
        
        Args:
            provider_name: Name of the provider
            
        Returns:
            ProviderConfig with auto-detected settings
        """
        if provider_name == "azure":
            return ProviderConfig(
                provider_name="azure",
                api_key=settings.azure_openai_api_key or settings.azure_openai_key,
                endpoint=settings.azure_openai_endpoint,
                region=settings.azure_speech_region,
                api_version=settings.azure_openai_api_version,
                additional_config={
                    "speech_key": settings.azure_speech_key,
                    "speech_region": settings.azure_speech_region,
                    "translation_key": settings.azure_translation_key,
                    "translation_region": settings.azure_translation_region,
                    "translation_endpoint": settings.azure_translation_endpoint,
                    "chat_model": settings.azure_chat_model,
                    "gpt4o_transcribe_deployment": settings.azure_gpt4o_transcribe_deployment,
                    "model_router_deployment": settings.azure_model_router_deployment,
                    "gpt_audio_mini_deployment": settings.azure_gpt_audio_mini_deployment,
                }
            )
        
        elif provider_name == "together":
            return ProviderConfig(
                provider_name="together",
                api_key=settings.together_api_key,
                model=settings.together_model or "meta-llama/Llama-3.3-70B-Instruct-Turbo",
            )
        
        elif provider_name == "openai":
            return ProviderConfig(
                provider_name="openai",
                api_key=settings.openai_api_key,
                model=settings.openai_whisper_model or "whisper-1",
                additional_config={
                    "tts_model": settings.openai_tts_model or "tts-1",
                    "tts_voice": settings.openai_tts_voice or "alloy",
                }
            )
        
        else:
            return ProviderConfig(provider_name=provider_name)
    
    @classmethod
    def get_available_providers(cls, capability: ProviderCapability, check_only_preferred: bool = True) -> List[str]:
        """
        Get list of available providers for a capability
        
        Args:
            capability: Required capability
            check_only_preferred: If True, only check preferred provider + azure fallback (default: True)
            
        Returns:
            List of provider names that support the capability and are configured
        """
        available = []
        
        # Determine which providers to check
        if check_only_preferred:
            # Only check preferred provider and Azure (as fallback)
            providers_to_check = []
            preference = get_provider_preference(capability)
            
            if preference != "auto" and preference in cls._provider_registry:
                providers_to_check.append(preference)
            
            # Always include Azure as fallback if not already included
            if "azure" not in providers_to_check and "azure" in cls._provider_registry:
                providers_to_check.append("azure")
        else:
            # Check all registered providers (legacy behavior)
            providers_to_check = list(cls._provider_registry.keys())
        
        for provider_name in providers_to_check:
            try:
                config = cls._auto_detect_config(provider_name)
                provider_class = cls._provider_registry[provider_name]
                
                instance = provider_class(config=config, capability=capability)
                
                if instance.is_available():
                    available.append(provider_name)
            except Exception as e:
                logger.debug(f"Provider '{provider_name}' not available for {capability.value}: {e}")
                continue
        
        return available
    
    @classmethod
    def clear_cache(cls):
        """Clear provider instance cache"""
        cls._instances.clear()
        logger.info("🧹 Cleared provider instance cache")


def get_provider_preference(capability: ProviderCapability) -> str:
    """
    Get user's preferred provider for a capability from configuration
    
    Args:
        capability: Required capability
        
    Returns:
        Provider name ('azure', 'together', 'openai', or 'auto')
    """
    if capability == ProviderCapability.LLM_CHAT:
        return settings.chat_provider or settings.llm_provider or "auto"
    
    elif capability == ProviderCapability.LLM_EMBEDDING:
        return settings.embedding_provider or settings.llm_provider or "auto"
    
    elif capability == ProviderCapability.SPEECH_TO_TEXT:
        return settings.voice_stt_provider or "auto"
    
    elif capability == ProviderCapability.TEXT_TO_SPEECH:
        return settings.voice_tts_provider or "auto"
    
    elif capability == ProviderCapability.TRANSLATION:
        return "azure"
    
    else:
        return "auto"


def get_fallback_chain(capability: ProviderCapability) -> List[str]:
    """
    Get fallback chain for a capability
    
    Args:
        capability: Required capability
        
    Returns:
        Ordered list of providers to try (primary first, then fallbacks)
    """
    preference = get_provider_preference(capability)
    
    if capability in [ProviderCapability.LLM_CHAT, ProviderCapability.LLM_EMBEDDING]:
        if preference == "auto":
            return ["azure", "together", "openai"]
        elif preference == "azure":
            return ["azure", "together", "openai"]
        elif preference == "together":
            return ["together", "azure", "openai"]
        elif preference == "openai":
            return ["openai", "azure", "together"]
    
    elif capability == ProviderCapability.SPEECH_TO_TEXT:
        if preference == "auto" or preference == "azure":
            return ["azure", "openai"]
        elif preference == "openai":
            return ["openai", "azure"]
    
    elif capability == ProviderCapability.TEXT_TO_SPEECH:
        if preference == "auto" or preference == "openai":
            return ["openai", "azure"]
        elif preference == "azure":
            return ["azure", "openai"]
    
    elif capability == ProviderCapability.TRANSLATION:
        return ["azure"]
    
    return ["azure", "together", "openai"]
