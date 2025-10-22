"""
Provider Registry

Registers all cloud provider implementations with the factory.
Import this module to ensure all providers are registered.
"""

from .factory import ProviderFactory
from .implementations.azure_provider import AzureProvider
from .implementations.together_provider import TogetherProvider
from .implementations.openai_provider import OpenAIProvider
from shared.logger import logger


def register_all_providers():
    """Register all available cloud providers"""
    logger.info("📋 Registering cloud providers...")
    
    ProviderFactory.register_provider("azure", AzureProvider)
    ProviderFactory.register_provider("together", TogetherProvider)
    ProviderFactory.register_provider("openai", OpenAIProvider)
    
    logger.info("✅ All cloud providers registered")


register_all_providers()
