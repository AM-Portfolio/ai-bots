from typing import Optional, List, Dict, Any
import logging

from .base import BaseLLMProvider
from .together_provider import TogetherAIProvider
from .azure_provider import AzureOpenAIProvider

logger = logging.getLogger(__name__)


class ProviderConfig:
    """Configuration for a single LLM provider"""
    
    def __init__(self, name: str, is_configured: bool, provider: Optional[BaseLLMProvider] = None):
        self.name = name
        self.is_configured = is_configured
        self.provider = provider
        self.is_available = provider.is_available() if provider else False


class LLMFactory:
    """Factory for creating LLM provider instances with intelligent fallback"""
    
    @staticmethod
    def detect_configured_providers(
        azure_endpoint: Optional[str] = None,
        azure_api_key: Optional[str] = None,
        together_api_key: Optional[str] = None
    ) -> Dict[str, bool]:
        """
        Detect which providers are configured based on credentials.
        
        Returns:
            Dict with provider names and configuration status
        """
        return {
            "azure": bool(azure_endpoint and azure_api_key),
            "together": bool(together_api_key)
        }
    
    @staticmethod
    def create_provider(
        provider_type: str = "together",
        together_api_key: Optional[str] = None,
        together_model: str = "meta-llama/Llama-3.3-70B-Instruct-Turbo",
        azure_endpoint: Optional[str] = None,
        azure_api_key: Optional[str] = None,
        azure_deployment: str = "gpt-4",
        azure_api_version: str = "2024-02-15-preview"
    ) -> BaseLLMProvider:
        """
        Create an LLM provider instance based on the specified type.
        
        Args:
            provider_type: Type of provider ("together" or "azure")
            together_api_key: Together AI API key
            together_model: Together AI model name
            azure_endpoint: Azure OpenAI endpoint
            azure_api_key: Azure OpenAI API key
            azure_deployment: Azure OpenAI deployment name
            azure_api_version: Azure OpenAI API version
        
        Returns:
            BaseLLMProvider instance
        """
        provider_type = provider_type.lower()
        
        if provider_type == "together":
            logger.info("Creating Together AI provider")
            return TogetherAIProvider(
                api_key=together_api_key,
                model=together_model
            )
        elif provider_type == "azure":
            logger.info("Creating Azure OpenAI provider")
            return AzureOpenAIProvider(
                endpoint=azure_endpoint,
                api_key=azure_api_key,
                deployment_name=azure_deployment,
                api_version=azure_api_version
            )
        else:
            raise ValueError(f"Unknown provider type: {provider_type}. Use 'together' or 'azure'")


def get_llm_client(
    provider_type: str = "auto",
    azure_endpoint: Optional[str] = None,
    azure_api_key: Optional[str] = None,
    azure_deployment: str = "gpt-4.1-mini",
    azure_api_version: str = "2025-01-01-preview",
    together_api_key: Optional[str] = None,
    together_model: str = "meta-llama/Llama-3.3-70B-Instruct-Turbo"
) -> BaseLLMProvider:
    """
    Intelligent LLM client creation with automatic provider detection and fallback.
    
    Behavior:
    - provider_type="auto": Auto-detect based on configured credentials
    - provider_type="azure": Use Azure, fallback to Together if both configured
    - provider_type="together": Use Together, fallback to Azure if both configured
    
    Fallback logic:
    - If BOTH providers configured: Enable fallback
    - If ONLY ONE provider configured: Use it exclusively, no fallback
    - If NONE configured: Raise error
    
    Args:
        provider_type: "auto", "azure", or "together"
        azure_endpoint: Azure OpenAI endpoint
        azure_api_key: Azure OpenAI API key
        azure_deployment: Azure deployment name
        azure_api_version: Azure API version
        together_api_key: Together AI API key
        together_model: Together AI model name
        
    Returns:
        BaseLLMProvider instance
        
    Raises:
        ValueError: If no providers are configured
    """
    
    # Detect configured providers
    configured = LLMFactory.detect_configured_providers(
        azure_endpoint=azure_endpoint,
        azure_api_key=azure_api_key,
        together_api_key=together_api_key
    )
    
    azure_configured = configured["azure"]
    together_configured = configured["together"]
    
    # Count configured providers
    num_configured = sum(configured.values())
    
    # Case 1: No providers configured - ERROR
    if num_configured == 0:
        error_msg = (
            "❌ No LLM providers configured. Please set one of:\n"
            "   • Azure: AZURE_OPENAI_ENDPOINT + AZURE_OPENAI_API_KEY\n"
            "   • Together AI: TOGETHER_API_KEY"
        )
        logger.error(error_msg)
        raise ValueError(error_msg)
    
    # Case 2: Only one provider configured - Use it exclusively
    if num_configured == 1:
        if azure_configured:
            logger.info("✅ Only Azure configured - using Azure exclusively (no fallback)")
            provider = AzureOpenAIProvider(
                endpoint=azure_endpoint,
                api_key=azure_api_key,
                deployment_name=azure_deployment,
                api_version=azure_api_version
            )
            if not provider.is_available():
                raise ValueError("❌ Azure OpenAI configured but not available. Check credentials.")
            return provider
        
        else:  # together_configured
            logger.info("✅ Only Together AI configured - using Together exclusively (no fallback)")
            provider = TogetherAIProvider(
                api_key=together_api_key,
                model=together_model
            )
            if not provider.is_available():
                raise ValueError("❌ Together AI configured but not available. Check credentials.")
            return provider
    
    # Case 3: Both providers configured - Enable smart fallback
    logger.info("✅ Both Azure and Together AI configured - fallback enabled")
    
    # Determine primary provider
    if provider_type == "auto":
        # Auto-detect: Prefer Azure if configured
        primary_type = "azure" if azure_configured else "together"
        logger.info(f"   • Auto-detection: Using {primary_type} as primary")
    else:
        primary_type = provider_type.lower()
    
    # Create primary provider only (lazy fallback initialization)
    if primary_type == "azure":
        primary = AzureOpenAIProvider(
            endpoint=azure_endpoint,
            api_key=azure_api_key,
            deployment_name=azure_deployment,
            api_version=azure_api_version
        )
        primary_name = "Azure OpenAI"
        fallback_name = "Together AI"
    else:  # together
        primary = TogetherAIProvider(
            api_key=together_api_key,
            model=together_model
        )
        primary_name = "Together AI"
        fallback_name = "Azure OpenAI"
    
    # Try primary provider
    if primary.is_available():
        logger.info(f"   • ✅ {primary_name} is available (primary)")
        logger.info(f"   • 🔄 {fallback_name} ready as fallback (will load on-demand if needed)")
        return primary
    
    # Primary failed, create and try fallback
    logger.warning(f"   • ⚠️  {primary_name} not available, trying fallback...")
    
    # Lazy initialize fallback only when needed
    if primary_type == "azure":
        fallback = TogetherAIProvider(
            api_key=together_api_key,
            model=together_model
        )
    else:
        fallback = AzureOpenAIProvider(
            endpoint=azure_endpoint,
            api_key=azure_api_key,
            deployment_name=azure_deployment,
            api_version=azure_api_version
        )
    
    if fallback.is_available():
        logger.info(f"   • ✅ {fallback_name} is available (fallback activated)")
        return fallback
    
    # Both failed
    error_msg = f"❌ Both {primary_name} and {fallback_name} failed to initialize"
    logger.error(error_msg)
    raise ValueError(error_msg)
