"""
Azure Model Deployment Service

Integrates with Azure OpenAI Model Deployments for advanced AI capabilities:
- gpt-4o-transcribe-diarize: Enhanced transcription with speaker diarization
- model-router: Intelligent routing to different GPT models
- gpt-audio-mini: Lightweight audio processing

This complements Service Endpoints (Speech, Translation) for a complete Azure AI solution.
"""

import logging
from typing import Optional, Dict, Any, List
from openai import AsyncAzureOpenAI
from shared.config import settings

logger = logging.getLogger(__name__)


class AzureModelDeploymentService:
    """
    Service for Azure OpenAI Model Deployments
    
    Provides access to:
    - GPT-4o Transcribe with Diarization
    - Model Router for intelligent model selection
    - GPT Audio Mini for lightweight audio tasks
    """
    
    def __init__(self):
        # Get configuration from .env via settings
        self.endpoint = settings.azure_openai_endpoint
        self.api_key = settings.azure_openai_api_key or settings.azure_openai_key
        self.api_version = settings.azure_openai_api_version or '2024-10-21'
        
        # Chat completion configuration (common for all chat models)
        self.chat_model = settings.azure_chat_model or settings.azure_openai_deployment_name or 'gpt-4.1-mini'
        self.chat_api_version = settings.azure_chat_api_version or '2025-01-01-preview'
        
        # Deployment names from .env configuration with fallbacks
        self.gpt4o_transcribe_deployment = (
            settings.azure_gpt4o_transcribe_deployment or
            'gpt-4o-transcribe-diarize'
        )
        self.model_router_deployment = (
            settings.azure_model_router_deployment or
            'model-router'
        )
        self.gpt_audio_mini_deployment = (
            settings.azure_gpt_audio_mini_deployment or
            'gpt-audio-mini'
        )
        
        # Initialize client if credentials available
        self.client: Optional[AsyncAzureOpenAI] = None
        if self.endpoint and self.api_key:
            try:
                self.client = AsyncAzureOpenAI(
                    azure_endpoint=self.endpoint,
                    api_key=self.api_key,
                    api_version=self.api_version
                )
                logger.info("✅ Azure Model Deployment Service initialized")
                logger.info(f"   • Endpoint: {self.endpoint}")
                logger.info(f"   • Chat Model: {self.chat_model} (API: {self.chat_api_version})")
                logger.info(f"   • GPT-4o Transcribe: {self.gpt4o_transcribe_deployment}")
                logger.info(f"   • Model Router: {self.model_router_deployment}")
                logger.info(f"   • GPT Audio Mini: {self.gpt_audio_mini_deployment}")
            except Exception as e:
                logger.warning(f"⚠️  Azure Model Deployment initialization failed: {e}")
        else:
            logger.warning("⚠️  Azure Model Deployment credentials not configured in .env")
            logger.warning("   Required: AZURE_OPENAI_ENDPOINT, AZURE_OPENAI_API_KEY")
    
    def is_available(self) -> bool:
        """Check if Azure Model Deployment service is available"""
        return self.client is not None
    
    async def transcribe_with_diarization(
        self,
        audio_file_path: str,
        language: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Transcribe audio with speaker diarization using GPT-4o
        
        Args:
            audio_file_path: Path to audio file
            language: Optional language hint (auto-detected if not provided)
            
        Returns:
            Dict with transcription, speakers, and timestamps
        """
        if not self.is_available():
            raise ValueError("Azure Model Deployment service not available")
        
        try:
            logger.info(f"🎙️  Transcribing with diarization: {audio_file_path}")
            
            with open(audio_file_path, 'rb') as audio_file:
                response = await self.client.audio.transcriptions.create(
                    model=self.gpt4o_transcribe_deployment,
                    file=audio_file,
                    language=language,
                    response_format="verbose_json",
                    timestamp_granularities=["word", "segment"]
                )
            
            # Extract diarization info
            result = {
                "text": response.text,
                "language": response.language,
                "duration": response.duration,
                "segments": [],
                "speakers": []
            }
            
            # Process segments with speaker information
            if hasattr(response, 'segments'):
                for segment in response.segments:
                    result["segments"].append({
                        "id": segment.id,
                        "start": segment.start,
                        "end": segment.end,
                        "text": segment.text,
                        "speaker": getattr(segment, 'speaker', 'unknown')
                    })
                    
                    # Track unique speakers
                    speaker = getattr(segment, 'speaker', 'unknown')
                    if speaker not in result["speakers"]:
                        result["speakers"].append(speaker)
            
            logger.info(f"✅ Transcription complete")
            logger.info(f"   • Duration: {result['duration']}s")
            logger.info(f"   • Language: {result['language']}")
            logger.info(f"   • Speakers: {len(result['speakers'])}")
            logger.info(f"   • Segments: {len(result['segments'])}")
            
            return result
            
        except Exception as e:
            logger.error(f"❌ Transcription error: {e}")
            raise
    
    async def chat_completion(
        self,
        messages: List[Dict[str, str]],
        temperature: float = 0.7,
        max_tokens: Optional[int] = None,
        model: Optional[str] = None
    ) -> str:
        """
        Common chat completion method for all Azure chat models
        
        Args:
            messages: Chat messages in OpenAI format
            temperature: Sampling temperature (0-2)
            max_tokens: Maximum tokens to generate
            model: Optional model override (uses self.chat_model if not provided)
            
        Returns:
            Assistant's response text
        """
        if not self.is_available():
            raise ValueError("Azure Model Deployment service not available")
        
        # Use provided model or default chat model
        deployment = model or self.chat_model
        
        try:
            # Log request details
            logger.info(f"💬 Azure Chat Completion")
            logger.info(f"   • Model: {deployment}")
            logger.info(f"   • Messages: {len(messages)}")
            logger.info(f"   • Temperature: {temperature}")
            if max_tokens:
                logger.info(f"   • Max tokens: {max_tokens}")
            
            # Log message details at debug level
            for i, msg in enumerate(messages):
                role = msg.get('role', 'unknown')
                content = msg.get('content', '')
                content_preview = content[:100] + '...' if len(content) > 100 else content
                logger.info(f"   • Message {i+1} [{role}]: {content_preview}")
            
            response = await self.client.chat.completions.create(
                model=deployment,
                messages=messages,
                temperature=temperature,
                max_tokens=max_tokens
            )
            
            result = response.choices[0].message.content
            model_used = response.model
            
            logger.info(f"✅ Chat complete")
            logger.info(f"   • Model used: {model_used}")
            logger.info(f"   • Response length: {len(result)} chars")
            if result:
                logger.info(f"   • Response preview: {result[:150]}...")
            
            return result
            
        except Exception as e:
            logger.error(f"❌ Chat error: {e}")
            raise
    
    async def chat_with_model_router(
        self,
        messages: List[Dict[str, str]],
        temperature: float = 0.7,
        max_tokens: Optional[int] = None
    ) -> str:
        """
        Chat using model-router deployment (intelligent routing)
        
        Legacy method - routes to model-router deployment.
        For standard chat, use chat_completion() instead.
        
        Args:
            messages: Chat messages in OpenAI format
            temperature: Sampling temperature (0-2)
            max_tokens: Maximum tokens to generate
            
        Returns:
            Assistant's response text
        """
        return await self.chat_completion(
            messages=messages,
            temperature=temperature,
            max_tokens=max_tokens,
            model=self.model_router_deployment
        )
    
    async def process_audio_mini(
        self,
        audio_file_path: str,
        task: str = "transcribe"
    ) -> str:
        """
        Process audio using lightweight GPT Audio Mini
        
        Args:
            audio_file_path: Path to audio file
            task: Task type (transcribe, translate, etc.)
            
        Returns:
            Processed text result
        """
        if not self.is_available():
            raise ValueError("Azure Model Deployment service not available")
        
        try:
            logger.info(f"🎵 Processing audio (mini): {audio_file_path}")
            logger.info(f"   • Task: {task}")
            
            with open(audio_file_path, 'rb') as audio_file:
                if task == "transcribe":
                    response = await self.client.audio.transcriptions.create(
                        model=self.gpt_audio_mini_deployment,
                        file=audio_file
                    )
                elif task == "translate":
                    response = await self.client.audio.translations.create(
                        model=self.gpt_audio_mini_deployment,
                        file=audio_file
                    )
                else:
                    raise ValueError(f"Unknown task: {task}")
            
            result = response.text
            
            logger.info(f"✅ Audio processing complete")
            logger.info(f"   • Result length: {len(result)} chars")
            
            return result
            
        except Exception as e:
            logger.error(f"❌ Audio processing error: {e}")
            raise
    
    async def get_deployment_info(self) -> Dict[str, Any]:
        """Get information about available deployments"""
        return {
            "available": self.is_available(),
            "endpoint": self.endpoint,
            "api_version": self.api_version,
            "deployments": {
                "chat_model": {
                    "name": self.chat_model,
                    "api_version": self.chat_api_version,
                    "capabilities": ["chat_completion", "multi_turn", "function_calling"],
                    "url": f"{self.endpoint}/openai/deployments/{self.chat_model}/chat/completions?api-version={self.chat_api_version}"
                },
                "gpt4o_transcribe": {
                    "name": self.gpt4o_transcribe_deployment,
                    "capabilities": ["transcription", "diarization", "timestamps"]
                },
                "model_router": {
                    "name": self.model_router_deployment,
                    "capabilities": ["chat", "intelligent_routing", "multi_model"]
                },
                "gpt_audio_mini": {
                    "name": self.gpt_audio_mini_deployment,
                    "capabilities": ["transcription", "translation", "lightweight"]
                }
            }
        }


# Global instance
azure_model_deployment = AzureModelDeploymentService()
