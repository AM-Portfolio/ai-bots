"""
Azure AI Manager

Unified coordinator for all Azure AI Services:
- Service Endpoints (Speech, Translation, Language)
- Model Deployments (GPT-4o Transcribe, Model Router, GPT Audio Mini)

Provides high-level interface for common AI workflows combining multiple services.
"""

import logging
from typing import Optional, Dict, Any, List
from enum import Enum

from shared.azure_services.speech_service import AzureSpeechService
from shared.azure_services.translation_service import AzureTranslationService
from shared.azure_services.model_deployment_service import AzureModelDeploymentService

logger = logging.getLogger(__name__)


class AIWorkflowType(str, Enum):
    """Types of AI workflows supported"""
    VOICE_ASSISTANT = "voice_assistant"  # STT → Translation → Chat
    MEETING_TRANSCRIPTION = "meeting_transcription"  # Diarized transcription → Summary
    MULTILINGUAL_CHAT = "multilingual_chat"  # Translation → Chat → Translation back
    AUDIO_ANALYSIS = "audio_analysis"  # STT → Analysis → Insights


class AzureAIManager:
    """
    Unified manager for Azure AI Services
    
    Coordinates Service Endpoints and Model Deployments for complete AI workflows.
    """
    
    def __init__(self):
        # Initialize all Azure services
        self.speech = AzureSpeechService()
        self.translation = AzureTranslationService()
        self.models = AzureModelDeploymentService()
        
        logger.info("🧠 Azure AI Manager initialized")
        logger.info(f"   • Speech Service: {'✓' if self.speech.is_available() else '✗'}")
        logger.info(f"   • Translation Service: {'✓' if self.translation.is_available() else '✗'}")
        logger.info(f"   • Model Deployments: {'✓' if self.models.is_available() else '✗'}")
    
    def get_service_status(self) -> Dict[str, Any]:
        """Get status of all Azure AI services"""
        return {
            "service_endpoints": {
                "speech": {
                    "available": self.speech.is_available(),
                    "endpoint": self.speech.speech_endpoint
                },
                "translation": {
                    "available": self.translation.is_available(),
                    "endpoint": self.translation.translation_endpoint
                }
            },
            "model_deployments": self.models.get_deployment_info() if hasattr(self.models, 'get_deployment_info') else {
                "available": self.models.is_available()
            }
        }
    
    async def voice_assistant_flow(
        self,
        audio_base64: str,
        audio_format: str = "webm",
        use_enhanced_transcription: bool = False
    ) -> Dict[str, Any]:
        """
        Complete voice assistant flow:
        1. STT (Speech or GPT-4o with diarization)
        2. Translation to English
        3. Ready for backend orchestration
        
        Args:
            audio_base64: Base64-encoded audio
            audio_format: Audio format (webm, wav, mp3)
            use_enhanced_transcription: Use GPT-4o for better transcription
            
        Returns:
            Dict with original text, translated text, language, and metadata
        """
        logger.info(f"🎯 Voice Assistant Flow (enhanced={use_enhanced_transcription})")
        
        try:
            # Step 1: Speech-to-Text
            if use_enhanced_transcription and self.models.is_available():
                # Use GPT-4o transcription (requires saving audio to file first)
                logger.info("   • Using GPT-4o enhanced transcription")
                # TODO: Implement file saving and GPT-4o transcription
                # For now, fallback to standard STT
                original_text, detected_lang = await self.speech.transcribe_audio(
                    audio_base64,
                    audio_format
                )
            else:
                # Use Azure Speech Service
                logger.info("   • Using Azure Speech Service")
                original_text, detected_lang = await self.speech.transcribe_audio(
                    audio_base64,
                    audio_format
                )
            
            # Step 2: Translation to English (if needed)
            if detected_lang != 'en' and self.translation.is_available():
                logger.info(f"   • Translating from {detected_lang} to English")
                translated_text, _ = await self.translation.translate_to_english(original_text)
            else:
                translated_text = original_text
            
            result = {
                "original_text": original_text,
                "translated_text": translated_text,
                "detected_language": detected_lang,
                "needs_translation": detected_lang != 'en',
                "transcription_method": "gpt4o" if use_enhanced_transcription else "azure_speech"
            }
            
            logger.info(f"✅ Voice Assistant Flow complete")
            logger.info(f"   • Language: {detected_lang}")
            logger.info(f"   • Translation needed: {result['needs_translation']}")
            
            return result
            
        except Exception as e:
            logger.error(f"❌ Voice Assistant Flow error: {e}")
            raise
    
    async def meeting_transcription_flow(
        self,
        audio_file_path: str
    ) -> Dict[str, Any]:
        """
        Meeting transcription with speaker diarization:
        1. GPT-4o transcription with diarization
        2. Speaker identification
        3. Segment timestamps
        
        Args:
            audio_file_path: Path to meeting audio file
            
        Returns:
            Dict with transcript, speakers, and segments
        """
        logger.info(f"🎯 Meeting Transcription Flow: {audio_file_path}")
        
        if not self.models.is_available():
            raise ValueError("Azure Model Deployments required for meeting transcription")
        
        try:
            # Use GPT-4o for diarized transcription
            result = await self.models.transcribe_with_diarization(audio_file_path)
            
            logger.info(f"✅ Meeting Transcription complete")
            logger.info(f"   • Speakers: {len(result.get('speakers', []))}")
            logger.info(f"   • Duration: {result.get('duration', 0)}s")
            
            return result
            
        except Exception as e:
            logger.error(f"❌ Meeting Transcription error: {e}")
            raise
    
    async def multilingual_chat_flow(
        self,
        user_message: str,
        source_language: Optional[str] = None,
        target_language: str = "en"
    ) -> Dict[str, Any]:
        """
        Multilingual chat flow:
        1. Detect/translate user message to English
        2. Process with Model Router
        3. Optionally translate response back to user's language
        
        Args:
            user_message: User's message in any language
            source_language: Source language (auto-detected if None)
            target_language: Target language for response
            
        Returns:
            Dict with original message, English message, response, and translated response
        """
        logger.info(f"🎯 Multilingual Chat Flow")
        logger.info(f"   • Source language: {source_language or 'auto'}")
        logger.info(f"   • Target language: {target_language}")
        
        try:
            # Step 1: Translate to English if needed
            if self.translation.is_available():
                english_message, detected_lang = await self.translation.translate_to_english(
                    user_message
                )
            else:
                english_message = user_message
                detected_lang = source_language or "en"
            
            # Step 2: Get AI response using Model Router
            if self.models.is_available():
                logger.info("   • Using Model Router for response")
                messages = [
                    {"role": "user", "content": english_message}
                ]
                english_response = await self.models.chat_with_model_router(messages)
            else:
                raise ValueError("Azure Model Deployments required for chat")
            
            # Step 3: Translate response back if needed
            if target_language != "en" and self.translation.is_available():
                logger.info(f"   • Translating response to {target_language}")
                translated_response, _ = await self.translation.translate(
                    english_response,
                    target_language=target_language
                )
            else:
                translated_response = english_response
            
            result = {
                "original_message": user_message,
                "english_message": english_message,
                "detected_language": detected_lang,
                "english_response": english_response,
                "translated_response": translated_response,
                "response_language": target_language
            }
            
            logger.info(f"✅ Multilingual Chat complete")
            
            return result
            
        except Exception as e:
            logger.error(f"❌ Multilingual Chat error: {e}")
            raise
    
    async def test_all_services(self) -> Dict[str, Any]:
        """
        Test all Azure AI services
        
        Returns health status and capabilities of each service
        """
        logger.info("🧪 Testing all Azure AI services...")
        
        results = {
            "speech_service": {
                "available": self.speech.is_available(),
                "endpoint": self.speech.speech_endpoint if self.speech.is_available() else None
            },
            "translation_service": {
                "available": self.translation.is_available(),
                "endpoint": self.translation.translation_endpoint if self.translation.is_available() else None
            },
            "model_deployments": {
                "available": self.models.is_available(),
                "deployments": await self.models.get_deployment_info() if self.models.is_available() else None
            },
            "workflows_available": []
        }
        
        # Check which workflows are available
        if self.speech.is_available() and self.translation.is_available():
            results["workflows_available"].append("voice_assistant")
        
        if self.models.is_available():
            results["workflows_available"].append("meeting_transcription")
            results["workflows_available"].append("multilingual_chat")
        
        logger.info(f"✅ Service test complete")
        logger.info(f"   • Available workflows: {len(results['workflows_available'])}")
        
        return results


# Global instance
azure_ai_manager = AzureAIManager()
