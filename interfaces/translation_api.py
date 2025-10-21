"""
Translation API Endpoints

Provides REST API for text translation using Azure Translation Service.
Supports multilingual chat in LLM Testing page.
"""

import logging
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import Optional

from shared.azure_services import AzureTranslationService

logger = logging.getLogger(__name__)

# Create router
router = APIRouter(prefix="/api/translation", tags=["translation"])

# Initialize translation service
translation_service = AzureTranslationService()


class TranslationRequest(BaseModel):
    """Request model for translation"""
    text: str
    target_language: str = "en"
    source_language: Optional[str] = None


class TranslationResponse(BaseModel):
    """Response model for translation"""
    original_text: str
    translated_text: str
    source_language: str
    target_language: str
    success: bool
    message: Optional[str] = None


class LanguageDetectionRequest(BaseModel):
    """Request model for language detection"""
    text: str


class LanguageDetectionResponse(BaseModel):
    """Response model for language detection"""
    text: str
    detected_language: str
    confidence: float
    success: bool


@router.post("/translate", response_model=TranslationResponse)
async def translate_text(request: TranslationRequest):
    """
    Translate text to target language
    
    Auto-detects source language if not provided.
    Default target is English (en).
    """
    try:
        if not translation_service.is_available():
            raise HTTPException(
                status_code=503,
                detail="Azure Translation Service not configured"
            )
        
        logger.info(f"🌐 Translation request: {request.text[:50]}...")
        logger.info(f"   • Target: {request.target_language}")
        logger.info(f"   • Source: {request.source_language or 'auto-detect'}")
        
        # Translate
        translated_text, detected_lang = await translation_service.translate(
            text=request.text,
            target_language=request.target_language,
            source_language=request.source_language
        )
        
        return TranslationResponse(
            original_text=request.text,
            translated_text=translated_text,
            source_language=detected_lang,
            target_language=request.target_language,
            success=True,
            message=f"Translated from {detected_lang} to {request.target_language}"
        )
        
    except Exception as e:
        logger.error(f"❌ Translation error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/translate-to-english", response_model=TranslationResponse)
async def translate_to_english(text: str):
    """
    Translate text to English with auto language detection
    
    Convenient endpoint for chat/voice that always translates to English.
    """
    try:
        if not translation_service.is_available():
            raise HTTPException(
                status_code=503,
                detail="Azure Translation Service not configured"
            )
        
        logger.info(f"🌐 Translating to English: {text[:50]}...")
        
        # Translate to English
        translated_text, detected_lang = await translation_service.translate_to_english(text)
        
        return TranslationResponse(
            original_text=text,
            translated_text=translated_text,
            source_language=detected_lang,
            target_language="en",
            success=True,
            message=f"Translated from {detected_lang} to English"
        )
        
    except Exception as e:
        logger.error(f"❌ Translation error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/detect-language", response_model=LanguageDetectionResponse)
async def detect_language(request: LanguageDetectionRequest):
    """
    Detect the language of input text
    
    Returns language code and confidence score.
    """
    try:
        if not translation_service.is_available():
            raise HTTPException(
                status_code=503,
                detail="Azure Translation Service not configured"
            )
        
        logger.info(f"🔍 Detecting language: {request.text[:50]}...")
        
        # Detect language
        language, confidence = await translation_service.detect_language(request.text)
        
        return LanguageDetectionResponse(
            text=request.text,
            detected_language=language,
            confidence=confidence,
            success=True
        )
        
    except Exception as e:
        logger.error(f"❌ Language detection error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/health")
async def translation_health():
    """Check if translation service is available"""
    return {
        "service": "Azure Translation",
        "available": translation_service.is_available(),
        "endpoint": translation_service.translation_endpoint
    }
