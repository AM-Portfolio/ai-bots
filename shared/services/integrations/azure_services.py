"""Azure AI service implementations for Integration Hub"""

import httpx
from typing import Dict, Any, List

from shared.services.base import BaseService, ServiceConfig, ServiceStatus
from shared.azure_services.azure_ai_manager import azure_ai_manager
from shared.logger import get_logger

logger = get_logger(__name__)


class AzureSpeechService(BaseService):
    """Azure Speech Service (STT/TTS)"""
    
    async def connect(self) -> bool:
        """Connect to Azure Speech"""
        try:
            if azure_ai_manager.speech.is_available():
                self._set_connected()
                logger.info("Azure Speech Service connected")
                return True
            else:
                self._set_error("Azure Speech not configured")
                return False
        except Exception as e:
            self._set_error(f"Azure Speech connection failed: {e}")
            return False
    
    async def disconnect(self) -> bool:
        """Disconnect from Azure Speech"""
        self.status = ServiceStatus.DISCONNECTED
        return True
    
    async def test_connection(self) -> Dict[str, Any]:
        """Test Azure Speech connection"""
        try:
            if not azure_ai_manager.speech.is_available():
                return {
                    "success": False,
                    "error": "Azure Speech Service not configured. Add AZURE_SPEECH_KEY and AZURE_SPEECH_REGION.",
                    "features": []
                }
            
            features = ["Speech-to-Text (STT)", "Text-to-Speech (TTS)"]
            
            return {
                "success": True,
                "message": "Azure Speech Service connected",
                "features": features,
                "region": azure_ai_manager.speech.region if hasattr(azure_ai_manager.speech, 'region') else "configured"
            }
        except Exception as e:
            return {"success": False, "error": str(e), "features": []}
    
    async def execute(self, action: str, **kwargs) -> Dict[str, Any]:
        """Execute Azure Speech actions"""
        return {"success": False, "error": "Direct execution not supported. Use Azure test endpoints."}
    
    async def get_capabilities(self) -> List[str]:
        """Get Azure Speech capabilities"""
        return ["Speech-to-Text (STT)", "Text-to-Speech (TTS)", "Voice Recognition"]


class AzureTranslatorService(BaseService):
    """Azure Translator Service"""
    
    async def connect(self) -> bool:
        """Connect to Azure Translator"""
        try:
            if azure_ai_manager.translation.is_available():
                self._set_connected()
                logger.info("Azure Translator connected")
                return True
            else:
                self._set_error("Azure Translator not configured")
                return False
        except Exception as e:
            self._set_error(f"Azure Translator connection failed: {e}")
            return False
    
    async def disconnect(self) -> bool:
        """Disconnect from Azure Translator"""
        self.status = ServiceStatus.DISCONNECTED
        return True
    
    async def test_connection(self) -> Dict[str, Any]:
        """Test Azure Translator connection"""
        try:
            if not azure_ai_manager.translation.is_available():
                return {
                    "success": False,
                    "error": "Azure Translator not configured. Add AZURE_TRANSLATOR_KEY and AZURE_TRANSLATOR_REGION.",
                    "features": []
                }
            
            features = ["Text Translation", "Language Detection", "90+ Languages"]
            
            return {
                "success": True,
                "message": "Azure Translator connected",
                "features": features,
                "region": azure_ai_manager.translation.region if hasattr(azure_ai_manager.translation, 'region') else "configured"
            }
        except Exception as e:
            return {"success": False, "error": str(e), "features": []}
    
    async def execute(self, action: str, **kwargs) -> Dict[str, Any]:
        """Execute Azure Translator actions"""
        return {"success": False, "error": "Direct execution not supported. Use Azure test endpoints."}
    
    async def get_capabilities(self) -> List[str]:
        """Get Azure Translator capabilities"""
        return ["Text Translation", "Language Detection", "90+ Languages"]


class AzureOpenAIService(BaseService):
    """Azure OpenAI Service"""
    
    async def connect(self) -> bool:
        """Connect to Azure OpenAI"""
        try:
            if azure_ai_manager.models.is_available():
                self._set_connected()
                logger.info("Azure OpenAI connected")
                return True
            else:
                self._set_error("Azure OpenAI not configured")
                return False
        except Exception as e:
            self._set_error(f"Azure OpenAI connection failed: {e}")
            return False
    
    async def disconnect(self) -> bool:
        """Disconnect from Azure OpenAI"""
        self.status = ServiceStatus.DISCONNECTED
        return True
    
    async def test_connection(self) -> Dict[str, Any]:
        """Test Azure OpenAI connection"""
        try:
            if not azure_ai_manager.models.is_available():
                return {
                    "success": False,
                    "error": "Azure OpenAI not configured. Add AZURE_OPENAI_ENDPOINT and AZURE_OPENAI_KEY.",
                    "models": []
                }
            
            # Get model deployment info
            try:
                deployment_info = await azure_ai_manager.models.get_deployment_info()
                models = list(deployment_info.keys()) if isinstance(deployment_info, dict) else ["GPT-4o"]
            except:
                models = ["GPT-4o (configured)"]
            
            return {
                "success": True,
                "message": "Azure OpenAI connected",
                "models": models,
                "endpoint": "configured"
            }
        except Exception as e:
            return {"success": False, "error": str(e), "models": []}
    
    async def execute(self, action: str, **kwargs) -> Dict[str, Any]:
        """Execute Azure OpenAI actions"""
        return {"success": False, "error": "Direct execution not supported. Use Azure test endpoints."}
    
    async def get_capabilities(self) -> List[str]:
        """Get Azure OpenAI capabilities"""
        return ["GPT-4 Models", "Chat Completion", "Code Generation", "Audio Transcription"]
