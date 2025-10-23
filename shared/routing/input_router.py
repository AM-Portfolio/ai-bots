"""
Input Router

Routes user input (voice or text) to appropriate processing pipeline
"""

from typing import Dict, Any, Optional
import logging
from enum import Enum

logger = logging.getLogger(__name__)


class InputType(Enum):
    """Input type enumeration"""
    TEXT = "text"
    VOICE = "voice"
    UNKNOWN = "unknown"


class InputRouter:
    """Routes user input (voice or text) to appropriate processing pipeline"""
    
    def __init__(self, speech_service=None):
        """
        Initialize input router
        
        Args:
            speech_service: Optional Azure Speech Service instance
        """
        self.speech_service = speech_service
    
    async def route(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Route input to appropriate processing pipeline
        
        Args:
            input_data: {
                "type": "text" or "voice",
                "content": text content or audio data,
                "metadata": optional metadata
            }
            
        Returns:
            {
                "input_type": InputType,
                "text": processed text,
                "original": original input,
                "language": detected language (for voice),
                "error": error message if failed
            }
        """
        input_type = self._detect_input_type(input_data)
        
        if input_type == InputType.VOICE:
            # Transcribe voice to text using Azure Speech-to-Text
            return await self._process_voice_input(input_data)
        
        elif input_type == InputType.TEXT:
            # Direct text input
            return await self._process_text_input(input_data)
        
        else:
            logger.error("Unknown input type")
            return {
                "input_type": InputType.UNKNOWN,
                "text": None,
                "original": input_data,
                "error": "Unknown input type"
            }
    
    async def _process_voice_input(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """Process voice input through Azure Speech-to-Text"""
        if not self.speech_service:
            logger.error("Speech service not configured")
            return {
                "input_type": InputType.VOICE,
                "text": None,
                "original": input_data,
                "error": "Speech service not configured"
            }
        
        try:
            audio_data = input_data.get("content")
            audio_format = input_data.get("format", "webm")
            
            # Transcribe using Azure Speech Service
            text, language = await self.speech_service.transcribe_audio(
                audio_data=audio_data,
                audio_format=audio_format
            )
            
            if not text:
                logger.error("Failed to transcribe voice input")
                return {
                    "input_type": InputType.VOICE,
                    "text": None,
                    "original": input_data,
                    "error": "Transcription failed"
                }
            
            logger.info(f"✅ Voice input transcribed: {text[:100]}...")
            if language:
                logger.info(f"   • Detected language: {language}")
            
            return {
                "input_type": InputType.VOICE,
                "text": text,
                "language": language,
                "original": input_data
            }
            
        except Exception as e:
            logger.error(f"❌ Voice processing failed: {e}")
            return {
                "input_type": InputType.VOICE,
                "text": None,
                "original": input_data,
                "error": str(e)
            }
    
    async def _process_text_input(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """Process direct text input"""
        try:
            text = input_data.get("content")
            
            if not text:
                logger.error("Empty text input")
                return {
                    "input_type": InputType.TEXT,
                    "text": None,
                    "original": input_data,
                    "error": "Empty text input"
                }
            
            logger.info(f"✅ Text input received: {text[:100]}...")
            
            return {
                "input_type": InputType.TEXT,
                "text": text,
                "original": input_data
            }
            
        except Exception as e:
            logger.error(f"❌ Text processing failed: {e}")
            return {
                "input_type": InputType.TEXT,
                "text": None,
                "original": input_data,
                "error": str(e)
            }
    
    def _detect_input_type(self, input_data: Dict[str, Any]) -> InputType:
        """Detect input type from input data"""
        input_type_str = input_data.get("type", "").lower()
        
        if input_type_str == "voice":
            return InputType.VOICE
        elif input_type_str == "text":
            return InputType.TEXT
        else:
            # Try to auto-detect
            if "audio" in input_type_str or input_data.get("format"):
                return InputType.VOICE
            elif isinstance(input_data.get("content"), str):
                return InputType.TEXT
            else:
                return InputType.UNKNOWN
