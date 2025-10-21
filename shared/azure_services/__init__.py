"""
Azure AI Services Integration

Provides unified access to Azure AI Services:
- Speech-to-Text (STT)
- Text Translation
- Azure OpenAI (via existing integration)
"""

from .speech_service import AzureSpeechService
from .translation_service import AzureTranslationService

__all__ = [
    "AzureSpeechService",
    "AzureTranslationService",
]
