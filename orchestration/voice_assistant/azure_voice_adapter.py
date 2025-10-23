"""
Azure Voice Adapter

Handles Speech-to-Text and Translation integration for Voice Assistant
using Azure AI Services.

Flow:
1. Speech-to-Text (Azure STT with auto language detection)
2. Text Translation (Auto-to-English using Azure Translation)
3. Return translated text for orchestration
"""

import logging
from typing import Tuple, Optional

from shared.azure_services import AzureSpeechService, AzureTranslationService
from shared.config import settings

logger = logging.getLogger(__name__)


class AzureVoiceAdapter:
    """
    Adapter for Azure Speech and Translation services in Voice Assistant
    
    Provides unified interface for:
    - Speech-to-Text with auto language detection
    - Text translation to English
    - Fallback to original text if services unavailable
    """
    
    def __init__(self):
        self.speech_service = AzureSpeechService()
        self.translation_service = AzureTranslationService()
        self.enable_translation = settings.enable_auto_translation
        
        logger.info("🎙️  Azure Voice Adapter initialized")
        logger.info(f"   • STT available: {self.speech_service.is_available()}")
        logger.info(f"   • Translation available: {self.translation_service.is_available()}")
        logger.info(f"   • Auto-translation: {'enabled' if self.enable_translation else 'disabled'}")
    
    async def process_audio(
        self,
        audio_data: str,
        audio_format: str = "webm"
    ) -> Tuple[str, str, Optional[str], Optional[str]]:
        """
        Process audio through STT and Translation pipeline
        
        Args:
            audio_data: Base64 encoded audio
            audio_format: Audio format (webm, mp3, wav)
            
        Returns:
            Tuple of (
                original_transcript,
                translated_text,
                detected_language,
                confidence_note
            )
        """
        logger.info("🔄 Processing audio through Azure pipeline...")
        
        original_text = ""
        translated_text = ""
        detected_language = None
        confidence_note = None
        
        try:
            # Step 1: Speech-to-Text with language detection
            if self.speech_service.is_available():
                logger.info("📝 Step 1: Azure STT (Auto language detection)")
                original_text, detected_language = await self.speech_service.transcribe_audio(
                    audio_data,
                    audio_format
                )
                logger.info(f"✅ Transcribed: '{original_text}' (lang: {detected_language})")
            else:
                logger.warning("⚠️  Azure STT not available, skipping transcription")
                raise ValueError("Azure Speech Service not configured")
            
            # Step 2: Translation to English (if enabled and needed)
            if self.enable_translation and self.translation_service.is_available():
                # Check if translation is needed
                if detected_language and not detected_language.startswith('en'):
                    logger.info("🌐 Step 2: Translating to English...")
                    translated_text, confirmed_lang = await self.translation_service.translate_to_english(
                        original_text,
                        detected_language
                    )
                    confidence_note = f"Detected {confirmed_lang}, translated to English"
                    logger.info(f"✅ Translated: '{translated_text}'")
                else:
                    # Already in English, no translation needed
                    translated_text = original_text
                    confidence_note = f"Detected {detected_language or 'English'}, no translation needed"
                    logger.info(f"✅ Already in English, using original text")
            else:
                # Translation disabled or not available
                translated_text = original_text
                confidence_note = "Translation disabled"
                logger.info("ℹ️  Translation skipped (disabled or unavailable)")
            
            logger.info("✅ Azure voice processing complete")
            logger.info(f"   • Original: {original_text}")
            logger.info(f"   • Translated: {translated_text}")
            logger.info(f"   • Language: {detected_language}")
            
            return original_text, translated_text, detected_language, confidence_note
            
        except Exception as e:
            logger.error(f"❌ Azure voice processing error: {e}")
            raise
    
    def is_available(self) -> bool:
        """Check if Azure voice services are available"""
        return self.speech_service.is_available()
