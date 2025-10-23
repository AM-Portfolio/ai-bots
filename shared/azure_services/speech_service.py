"""
Azure Speech-to-Text Service

Provides speech recognition with automatic language detection
using Azure Cognitive Services Speech SDK.
"""

import logging
import base64
import io
import tempfile
import subprocess
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
    
    def _convert_webm_to_wav(self, audio_bytes: bytes) -> bytes:
        """
        Convert WebM audio to WAV format using ffmpeg
        
        Args:
            audio_bytes: Raw WebM audio bytes
            
        Returns:
            WAV audio bytes
        """
        import os
        try:
            # Create temporary input file and write WebM data
            with tempfile.NamedTemporaryFile(suffix='.webm', delete=False) as webm_file:
                webm_file.write(audio_bytes)
                webm_file.flush()  # Ensure data is written to disk
                webm_path = webm_file.name
            
            # Create temporary output file path (empty file for FFmpeg to write to)
            wav_fd, wav_path = tempfile.mkstemp(suffix='.wav')
            os.close(wav_fd)  # Close the file descriptor, FFmpeg will write to it
            
            # Convert using ffmpeg: WebM -> WAV (16kHz mono PCM)
            result = subprocess.run([
                'ffmpeg',
                '-y',            # Overwrite output file without asking
                '-i', webm_path,
                '-ar', '16000',  # 16kHz sample rate
                '-ac', '1',      # Mono
                '-f', 'wav',     # WAV format
                wav_path
            ], capture_output=True, text=True, timeout=10)
            
            if result.returncode != 0:
                logger.error(f"❌ FFmpeg conversion failed: {result.stderr}")
                raise Exception(f"Audio conversion failed: {result.stderr}")
            
            # Read converted WAV file
            with open(wav_path, 'rb') as f:
                wav_bytes = f.read()
            
            # Cleanup temporary files
            os.unlink(webm_path)
            os.unlink(wav_path)
            
            logger.info(f"✅ Converted WebM ({len(audio_bytes)} bytes) to WAV ({len(wav_bytes)} bytes)")
            return wav_bytes
            
        except Exception as e:
            logger.error(f"❌ Audio conversion error: {e}")
            raise
    
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
            logger.info(f"📥 Received audio: {len(audio_bytes)} bytes, format: {audio_format}")
            
            # Convert WebM to WAV if needed
            if audio_format.lower() in ['webm', 'audio/webm']:
                logger.info("🔄 Converting WebM to WAV for Azure STT...")
                audio_bytes = self._convert_webm_to_wav(audio_bytes)
            
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
            
            # If we get here, return empty result
            return "", None
            
        except Exception as e:
            logger.error(f"❌ Azure STT error: {e}")
            raise
    
    def is_available(self) -> bool:
        """Check if Azure Speech Service is available"""
        return self._speech_config is not None


# Global instance
azure_speech_service = AzureSpeechService()
