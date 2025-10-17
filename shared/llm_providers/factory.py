from typing import Optional
import logging

from .base import BaseLLMProvider
from .together_provider import TogetherAIProvider
from .azure_provider import AzureOpenAIProvider

logger = logging.getLogger(__name__)


class LLMFactory:
    """Factory for creating LLM provider instances"""
    
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
    provider_type: str = "together",
    together_api_key: Optional[str] = None,
    together_model: str = "meta-llama/Llama-3.3-70B-Instruct-Turbo",
    azure_endpoint: Optional[str] = None,
    azure_api_key: Optional[str] = None,
    azure_deployment: str = "gpt-4",
    azure_api_version: str = "2024-02-15-preview"
) -> BaseLLMProvider:
    """
    Convenience function to get an LLM client instance.
    
    Defaults to Together AI as the primary provider.
    Falls back to Azure OpenAI if Together AI is not available.
    """
    try:
        client = LLMFactory.create_provider(
            provider_type=provider_type,
            together_api_key=together_api_key,
            together_model=together_model,
            azure_endpoint=azure_endpoint,
            azure_api_key=azure_api_key,
            azure_deployment=azure_deployment,
            azure_api_version=azure_api_version
        )
        
        if client.is_available():
            return client
        
        logger.warning(f"{provider_type.capitalize()} provider not available, trying fallback")
        
        if provider_type == "together" and azure_endpoint and azure_api_key:
            logger.info("Falling back to Azure OpenAI")
            fallback_client = AzureOpenAIProvider(
                endpoint=azure_endpoint,
                api_key=azure_api_key,
                deployment_name=azure_deployment,
                api_version=azure_api_version
            )
            if fallback_client.is_available():
                return fallback_client
        
        logger.warning("No LLM provider available")
        return client
        
    except Exception as e:
        logger.error(f"Error creating LLM provider: {e}")
        raise
