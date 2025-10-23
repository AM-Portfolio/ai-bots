"""
Azure Translation Service

Provides text translation with automatic language detection
using Azure Cognitive Services Translator API.
"""

import logging
import requests
import uuid
from typing import Optional, Tuple, List

from ..config import settings

logger = logging.getLogger(__name__)


class AzureTranslationService:
    """
    Azure Translation service with automatic language detection
    
    Features:
    - Automatic language detection
    - Translation to English (or any target language)
    - Support for 100+ languages
    - Batch translation support
    """
    
    def __init__(self):
        # Use new variable names with fallback to legacy names
        self.translation_key = (
            settings.azure_translation_key or 
            settings.azure_translator_key
        )
        self.translation_region = (
            settings.azure_translation_region or 
            settings.azure_translator_region
        )
        self.translation_endpoint = (
            settings.azure_translation_endpoint or 
            settings.azure_translator_endpoint or
            "https://api.cognitive.microsofttranslator.com"
        )
        self._headers = None
        self._initialize()
    
    def _initialize(self):
        """Initialize Azure Translation service"""
        if not self.translation_key:
            logger.warning("⚠️  Azure Translation credentials not configured")
            return
        
        try:
            # Set up headers for API calls
            self._headers = {
                'Ocp-Apim-Subscription-Key': self.translation_key,
                'Ocp-Apim-Subscription-Region': self.translation_region or 'eastus2',
                'Content-type': 'application/json',
                'X-ClientTraceId': str(uuid.uuid4())
            }
            
            logger.info("✅ Azure Translation Service initialized")
            logger.info(f"   • Endpoint: {self.translation_endpoint}")
            logger.info(f"   • Region: {self.translation_region or 'eastus2'}")
            
        except Exception as e:
            logger.error(f"❌ Failed to initialize Azure Translation Service: {e}")
            self._headers = None
    
    async def detect_language(self, text: str) -> Tuple[str, float]:
        """
        Detect the language of the input text
        
        Args:
            text: Input text to detect language
            
        Returns:
            Tuple of (language_code, confidence_score)
        """
        if not self._headers:
            raise ValueError("Azure Translation Service not configured")
        
        try:
            path = '/detect'
            url = self.translation_endpoint + path
            
            params = {
                'api-version': '3.0'
            }
            
            body = [{
                'text': text
            }]
            
            response = requests.post(url, params=params, headers=self._headers, json=body)
            response.raise_for_status()
            
            result = response.json()
            if result and len(result) > 0:
                language = result[0]['language']
                score = result[0]['score']
                
                logger.info(f"🌐 Detected language: {language} (confidence: {score:.2f})")
                return language, score
            
            return "en", 0.0
            
        except Exception as e:
            logger.error(f"❌ Language detection error: {e}")
            return "en", 0.0
    
    async def translate_to_english(
        self,
        text: str,
        source_language: Optional[str] = None
    ) -> Tuple[str, str]:
        """
        Translate text to English with automatic language detection
        
        Args:
            text: Text to translate
            source_language: Source language code (optional, auto-detect if None)
            
        Returns:
            Tuple of (translated_text, detected_source_language)
        """
        if not self._headers:
            raise ValueError("Azure Translation Service not configured")
        
        try:
            path = '/translate'
            url = self.translation_endpoint + path
            
            params = {
                'api-version': '3.0',
                'to': 'en'
            }
            
            # Add source language if provided
            if source_language and source_language != 'auto':
                params['from'] = source_language
            
            body = [{
                'text': text
            }]
            
            logger.info(f"🔄 Translating text to English...")
            logger.info(f"   • Source: {source_language or 'auto-detect'}")
            logger.info(f"   • Text length: {len(text)} chars")
            
            response = requests.post(url, params=params, headers=self._headers, json=body)
            response.raise_for_status()
            
            result = response.json()
            if result and len(result) > 0:
                translated = result[0]['translations'][0]['text']
                detected_lang = result[0].get('detectedLanguage', {}).get('language', source_language or 'unknown')
                
                logger.info(f"✅ Translation complete")
                logger.info(f"   • Detected language: {detected_lang}")
                logger.info(f"   • Translated text: {translated[:100]}...")
                
                return translated, detected_lang
            
            return text, source_language or "unknown"
            
        except Exception as e:
            logger.error(f"❌ Translation error: {e}")
            # Return original text if translation fails
            return text, source_language or "unknown"
    
    async def translate(
        self,
        text: str,
        target_language: str,
        source_language: Optional[str] = None
    ) -> Tuple[str, str]:
        """
        Translate text to any target language
        
        Args:
            text: Text to translate
            target_language: Target language code (e.g., 'en', 'hi', 'es')
            source_language: Source language code (optional, auto-detect if None)
            
        Returns:
            Tuple of (translated_text, detected_source_language)
        """
        if not self._headers:
            raise ValueError("Azure Translation Service not configured")
        
        try:
            path = '/translate'
            url = self.translation_endpoint + path
            
            params = {
                'api-version': '3.0',
                'to': target_language
            }
            
            if source_language and source_language != 'auto':
                params['from'] = source_language
            
            body = [{
                'text': text
            }]
            
            response = requests.post(url, params=params, headers=self._headers, json=body)
            response.raise_for_status()
            
            result = response.json()
            if result and len(result) > 0:
                translated = result[0]['translations'][0]['text']
                detected_lang = result[0].get('detectedLanguage', {}).get('language', source_language or 'unknown')
                
                return translated, detected_lang
            
            return text, source_language or "unknown"
            
        except Exception as e:
            logger.error(f"❌ Translation error: {e}")
            return text, source_language or "unknown"
    
    def is_available(self) -> bool:
        """Check if Azure Translation Service is available"""
        return self._headers is not None


# Global instance
azure_translation_service = AzureTranslationService()
