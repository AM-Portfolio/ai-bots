"""
Unified AI API

Cloud-agnostic API endpoints that use the orchestration layer.
Replaces provider-specific routes with unified interfaces.
"""

from fastapi import APIRouter, HTTPException, File, UploadFile, Form
from pydantic import BaseModel
from typing import Optional, List, Dict, Any
import base64

from orchestration.cloud_providers.registry import register_all_providers
from orchestration.cloud_providers.orchestrator import orchestrator
from shared.logger import get_logger

logger = get_logger(__name__)


router = APIRouter(prefix="/api/ai", tags=["Unified AI"])


class ChatRequest(BaseModel):
    """Request model for chat completion"""
    messages: List[Dict[str, str]]
    temperature: Optional[float] = 0.7
    max_tokens: Optional[int] = 2000
    provider: Optional[str] = None


class TranscriptionRequest(BaseModel):
    """Request model for speech-to-text"""
    audio_base64: str
    audio_format: str = "wav"
    language: Optional[str] = None
    provider: Optional[str] = None


class TranslationRequest(BaseModel):
    """Request model for translation"""
    text: str
    target_language: str
    source_language: Optional[str] = None
    provider: Optional[str] = None


class TTSRequest(BaseModel):
    """Request model for text-to-speech"""
    text: str
    language: Optional[str] = None
    voice: Optional[str] = None
    audio_format: str = "mp3"
    provider: Optional[str] = None


@router.post("/chat")
async def chat_completion(request: ChatRequest):
    """
    Generate chat completion using orchestrated LLM providers
    
    Automatically routes to best available provider:
    - Primary: User-configured provider
    - Fallback: Automatic fallback chain (Azure → Together AI → OpenAI)
    """
    try:
        logger.info(f"💬 Chat request received")
        logger.info(f"   • Provider preference: {request.provider or 'auto'}")
        logger.info(f"   • Messages: {len(request.messages)}")
        
        result = await orchestrator.chat_completion(
            messages=request.messages,
            temperature=request.temperature,
            max_tokens=request.max_tokens,
            preferred_provider=request.provider
        )
        
        return {
            "content": result.content,
            "model": result.model,
            "provider": result.metadata.get("provider"),
            "usage": result.usage,
            "duration_ms": result.duration_ms
        }
    
    except Exception as e:
        logger.error(f"❌ Chat completion failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/transcribe")
async def transcribe_audio(request: TranscriptionRequest):
    """
    Transcribe audio to text using orchestrated STT providers
    
    Automatically routes to best available provider:
    - Primary: User-configured provider
    - Fallback: Azure → OpenAI
    """
    try:
        logger.info(f"🎙️  Transcription request received")
        logger.info(f"   • Provider preference: {request.provider or 'auto'}")
        logger.info(f"   • Format: {request.audio_format}")
        
        audio_data = base64.b64decode(request.audio_base64)
        
        result = await orchestrator.speech_to_text(
            audio_data=audio_data,
            audio_format=request.audio_format,
            language=request.language,
            preferred_provider=request.provider
        )
        
        return {
            "text": result.text,
            "detected_language": result.detected_language,
            "confidence": result.confidence,
            "method": result.method,
            "provider": result.metadata.get("provider"),
            "duration_ms": result.duration_ms
        }
    
    except Exception as e:
        logger.error(f"❌ Transcription failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/translate")
async def translate_text(request: TranslationRequest):
    """
    Translate text using orchestrated translation providers
    
    Currently uses Azure Translator (primary provider for translation)
    """
    try:
        logger.info(f"🌐 Translation request received")
        logger.info(f"   • Target language: {request.target_language}")
        logger.info(f"   • Provider preference: {request.provider or 'auto'}")
        
        result = await orchestrator.translate_text(
            text=request.text,
            target_language=request.target_language,
            source_language=request.source_language,
            preferred_provider=request.provider
        )
        
        return {
            "translated_text": result.translated_text,
            "source_language": result.source_language,
            "target_language": result.target_language,
            "confidence": result.confidence,
            "provider": result.metadata.get("provider"),
            "duration_ms": result.duration_ms
        }
    
    except Exception as e:
        logger.error(f"❌ Translation failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/speak")
async def text_to_speech(request: TTSRequest):
    """
    Convert text to speech using orchestrated TTS providers
    
    Automatically routes to best available provider:
    - Primary: OpenAI TTS
    - Fallback: Azure Speech Service
    """
    try:
        logger.info(f"🔊 TTS request received")
        logger.info(f"   • Text length: {len(request.text)} chars")
        logger.info(f"   • Provider preference: {request.provider or 'auto'}")
        
        result = await orchestrator.text_to_speech(
            text=request.text,
            language=request.language,
            voice=request.voice,
            audio_format=request.audio_format,
            preferred_provider=request.provider
        )
        
        audio_base64 = base64.b64encode(result.audio_data).decode('utf-8')
        
        return {
            "audio_base64": audio_base64,
            "audio_format": result.audio_format,
            "provider": result.metadata.get("provider"),
            "duration_ms": result.duration_ms
        }
    
    except Exception as e:
        logger.error(f"❌ TTS failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/status")
async def get_orchestrator_status():
    """
    Get status of all cloud providers and capabilities
    
    Returns configuration, available providers, and fallback chains
    """
    try:
        logger.info("📊 Orchestrator status request")
        
        status = await orchestrator.get_orchestrator_status()
        
        return status
    
    except Exception as e:
        logger.error(f"❌ Status check failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/providers")
async def list_providers():
    """
    List all registered cloud providers and their capabilities
    """
    try:
        from orchestration.cloud_providers.templates.base import ProviderCapability
        
        providers = {}
        
        for provider_name in ["azure", "together", "openai"]:
            capabilities = []
            for capability in ProviderCapability:
                try:
                    from orchestration.cloud_providers.factory import ProviderFactory
                    available = ProviderFactory.get_available_providers(capability)
                    if provider_name in available:
                        capabilities.append(capability.value)
                except:
                    continue
            
            providers[provider_name] = {
                "capabilities": capabilities,
                "configured": len(capabilities) > 0
            }
        
        return {"providers": providers}
    
    except Exception as e:
        logger.error(f"❌ Provider listing failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))
