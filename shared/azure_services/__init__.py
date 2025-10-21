"""
Azure AI Services Integration

Provides unified access to Azure AI Services:
- Service Endpoints: Speech, Translation, Language
- Model Deployments: GPT-4o Transcribe, Model Router, GPT Audio Mini
- Unified Manager: Coordinate workflows across services
"""

from .speech_service import AzureSpeechService
from .translation_service import AzureTranslationService
from .model_deployment_service import AzureModelDeploymentService
from .azure_ai_manager import AzureAIManager, AIWorkflowType

__all__ = [
    "AzureSpeechService",
    "AzureTranslationService",
    "AzureModelDeploymentService",
    "AzureAIManager",
    "AIWorkflowType",
]
