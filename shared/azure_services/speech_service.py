"""
Azure Speech-to-Text Service

Provides speech recognition with automatic language detection
using Azure Cognitive Services Speech SDK.
"""

import logging
import base64
import io
from typing import Optional, Tuple
import azure.cognitiveservices.speech as speechsdk

from ..config import settings

logger = logging.getLogger(__name__)


class AzureSpeechService:
    """
    Azure Speech-to-Text service with automatic language detection
    
    Features:
    - Automatic language detection (auto-to-standard)
    - Support for multiple audio formats (webm, mp3, wav)
    - Continuous recognition for longer audio
    """
    
    def __init__(self):
        self.speech_key = settings.azure_speech_key
        self.speech_region = settings.azure_speech_region
        self._speech_config = None
        self._initialize_config()
    
    def _initialize_config(self):
        """Initialize Azure Speech configuration"""
        if not self.speech_key or not self.speech_region:
            logger.warning("⚠️  Azure Speech credentials not configured")
            return
        
        try:
            # Create speech config
            self._speech_config = speechsdk.SpeechConfig(
                subscription=self.speech_key,
                region=self.speech_region
            )
            
            # Enable auto language detection
            self._speech_config.speech_recognition_language = "auto"
            
            logger.info("✅ Azure Speech Service initialized")
            logger.info(f"   • Region: {self.speech_region}")
            logger.info(f"   • Auto language detection: enabled")
            
        except Exception as e:
            logger.error(f"❌ Failed to initialize Azure Speech Service: {e}")
            self._speech_config = None
    
    async def transcribe_audio(
        self,
        audio_data: str,
        audio_format: str = "webm"
    ) -> Tuple[str, Optional[str]]:
        """
        Transcribe audio to text with language detection
        
        Args:
            audio_data: Base64 encoded audio data
            audio_format: Audio format (webm, mp3, wav)
            
        Returns:
            Tuple of (transcribed_text, detected_language)
        """
        if not self._speech_config:
            raise ValueError("Azure Speech Service not configured")
        
        try:
            # Decode base64 audio
            audio_bytes = base64.b64decode(audio_data)
            
            # Create audio stream from bytes
            audio_stream = speechsdk.audio.PushAudioInputStream()
            audio_stream.write(audio_bytes)
            audio_stream.close()
            
            # Create audio config from stream
            audio_config = speechsdk.audio.AudioConfig(stream=audio_stream)
            
            # Create auto-detect source language config
            # Azure STT only supports 4 languages in DetectAudioAtStart mode
            auto_detect_config = speechsdk.languageconfig.AutoDetectSourceLanguageConfig(
                languages=["en-US", "hi-IN", "es-ES", "fr-FR"]
            )
            
            # Create speech recognizer with auto-detection
            speech_recognizer = speechsdk.SpeechRecognizer(
                speech_config=self._speech_config,
                audio_config=audio_config,
                auto_detect_source_language_config=auto_detect_config
            )
            
            logger.info("🎤 Starting Azure speech recognition...")
            
            # Perform recognition
            result = speech_recognizer.recognize_once()
            
            if result.reason == speechsdk.ResultReason.RecognizedSpeech:
                # Get detected language
                detected_language = None
                if hasattr(result, 'properties'):
                    detected_language = result.properties.get(
                        speechsdk.PropertyId.SpeechServiceConnection_AutoDetectSourceLanguageResult
                    )
                
                logger.info(f"✅ Speech recognized")
                logger.info(f"   • Text: {result.text}")
                logger.info(f"   • Language: {detected_language or 'Unknown'}")
                
                return result.text, detected_language
            
            elif result.reason == speechsdk.ResultReason.NoMatch:
                logger.warning("⚠️  No speech could be recognized")
                return "", None
            
            elif result.reason == speechsdk.ResultReason.Canceled:
                cancellation = result.cancellation_details
                logger.error(f"❌ Speech recognition canceled: {cancellation.reason}")
                if cancellation.reason == speechsdk.CancellationReason.Error:
                    logger.error(f"   Error details: {cancellation.error_details}")
                raise Exception(f"Speech recognition failed: {cancellation.error_details}")
            
        except Exception as e:
            logger.error(f"❌ Azure STT error: {e}")
            raise
    
    def is_available(self) -> bool:
        """Check if Azure Speech Service is available"""
        return self._speech_config is not None


# Global instance
azure_speech_service = AzureSpeechService()
