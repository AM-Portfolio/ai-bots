"""
Azure AI Test API Endpoints

Provides test endpoints for Azure AI workflows:
- Voice Assistant Flow (STT → Translation → Chat)
- Meeting Transcription Flow (Diarization → Summarization)
- Multilingual Chat Flow (Translation → Chat → Translation)
- Service Health Checks

Follows proper separation of concerns: API → Service → Business Logic
"""

import logging
from fastapi import APIRouter, HTTPException, UploadFile, File
from pydantic import BaseModel
from typing import Optional, Dict, Any, List

from shared.azure_services.azure_ai_manager import azure_ai_manager, AIWorkflowType

logger = logging.getLogger(__name__)

# Create router
router = APIRouter(prefix="/api/azure", tags=["azure-ai"])


# ============================================================================
# REQUEST/RESPONSE MODELS
# ============================================================================

class VoiceAssistantRequest(BaseModel):
    """Request model for voice assistant flow"""
    audio_base64: str
    audio_format: str = "webm"
    use_enhanced_transcription: bool = False


class VoiceAssistantResponse(BaseModel):
    """Response model for voice assistant flow"""
    original_text: str
    translated_text: str
    detected_language: str
    needs_translation: bool
    transcription_method: str


class MultilingualChatRequest(BaseModel):
    """Request model for multilingual chat"""
    message: str
    source_language: Optional[str] = None
    target_language: str = "en"


class MultilingualChatResponse(BaseModel):
    """Response model for multilingual chat"""
    original_message: str
    english_message: str
    detected_language: str
    english_response: str
    translated_response: str
    response_language: str


class ServiceStatusResponse(BaseModel):
    """Response model for service status"""
    service_endpoints: Dict[str, Any]
    model_deployments: Dict[str, Any]


# ============================================================================
# VOICE ASSISTANT ENDPOINTS
# ============================================================================

@router.post("/voice-assistant", response_model=VoiceAssistantResponse)
async def test_voice_assistant_flow(request: VoiceAssistantRequest):
    """
    Test complete voice assistant flow:
    1. Speech-to-Text (Azure Speech or GPT-4o)
    2. Translation to English (Azure Translator)
    3. Returns both original and translated text
    
    Use this to test the voice input pipeline before backend orchestration.
    """
    try:
        logger.info("🎯 Testing Voice Assistant Flow")
        logger.info(f"   • Audio format: {request.audio_format}")
        logger.info(f"   • Enhanced transcription: {request.use_enhanced_transcription}")
        
        result = await azure_ai_manager.voice_assistant_flow(
            audio_base64=request.audio_base64,
            audio_format=request.audio_format,
            use_enhanced_transcription=request.use_enhanced_transcription
        )
        
        return VoiceAssistantResponse(**result)
        
    except Exception as e:
        logger.error(f"❌ Voice Assistant Flow test failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# ============================================================================
# MEETING TRANSCRIPTION ENDPOINTS
# ============================================================================

@router.post("/meeting-transcription")
async def test_meeting_transcription_flow(audio_file: UploadFile = File(...)):
    """
    Test meeting transcription with speaker diarization:
    1. GPT-4o transcription with diarization
    2. Speaker identification
    3. Segment timestamps
    
    Requires Azure Model Deployments (GPT-4o-transcribe-diarize).
    """
    try:
        logger.info(f"🎯 Testing Meeting Transcription: {audio_file.filename}")
        
        # Save uploaded file temporarily
        import tempfile
        import os
        
        with tempfile.NamedTemporaryFile(delete=False, suffix=os.path.splitext(audio_file.filename)[1]) as tmp_file:
            content = await audio_file.read()
            tmp_file.write(content)
            tmp_file_path = tmp_file.name
        
        try:
            result = await azure_ai_manager.meeting_transcription_flow(tmp_file_path)
            return result
        finally:
            # Clean up temp file
            if os.path.exists(tmp_file_path):
                os.remove(tmp_file_path)
        
    except Exception as e:
        logger.error(f"❌ Meeting Transcription test failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# ============================================================================
# MULTILINGUAL CHAT ENDPOINTS
# ============================================================================

@router.post("/multilingual-chat", response_model=MultilingualChatResponse)
async def test_multilingual_chat_flow(request: MultilingualChatRequest):
    """
    Test multilingual chat flow:
    1. Detect/translate user message to English
    2. Process with Model Router (GPT)
    3. Translate response back to user's language
    
    Requires Azure Translation + Model Deployments.
    """
    try:
        logger.info("🎯 Testing Multilingual Chat Flow")
        logger.info(f"   • Message: {request.message[:50]}...")
        logger.info(f"   • Target language: {request.target_language}")
        
        result = await azure_ai_manager.multilingual_chat_flow(
            user_message=request.message,
            source_language=request.source_language,
            target_language=request.target_language
        )
        
        return MultilingualChatResponse(**result)
        
    except Exception as e:
        logger.error(f"❌ Multilingual Chat test failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# ============================================================================
# SERVICE HEALTH & STATUS ENDPOINTS
# ============================================================================

@router.get("/status", response_model=ServiceStatusResponse)
async def get_azure_service_status():
    """
    Get status of all Azure AI services
    
    Returns availability and configuration of:
    - Service Endpoints (Speech, Translation)
    - Model Deployments (GPT-4o, Model Router, GPT Audio Mini)
    """
    try:
        logger.info("📊 Getting Azure AI service status")
        
        status = azure_ai_manager.get_service_status()
        
        return ServiceStatusResponse(**status)
        
    except Exception as e:
        logger.error(f"❌ Status check failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/test-all")
async def test_all_azure_services():
    """
    Test all Azure AI services and workflows
    
    Returns comprehensive health check and available workflows.
    """
    try:
        logger.info("🧪 Testing all Azure AI services")
        
        results = await azure_ai_manager.test_all_services()
        
        return {
            "status": "success",
            "services": results,
            "message": f"Available workflows: {', '.join(results.get('workflows_available', []))}"
        }
        
    except Exception as e:
        logger.error(f"❌ Full service test failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/workflows")
async def get_available_workflows():
    """
    Get list of available Azure AI workflows
    
    Returns which workflows can be used based on configured services.
    """
    try:
        workflows = []
        
        # Check voice assistant
        if azure_ai_manager.speech.is_available() and azure_ai_manager.translation.is_available():
            workflows.append({
                "name": "voice_assistant",
                "description": "STT → Translation → Chat workflow",
                "endpoint": "/api/azure/voice-assistant",
                "method": "POST"
            })
        
        # Check meeting transcription
        if azure_ai_manager.models.is_available():
            workflows.append({
                "name": "meeting_transcription",
                "description": "Diarized transcription with speaker identification",
                "endpoint": "/api/azure/meeting-transcription",
                "method": "POST"
            })
            
            workflows.append({
                "name": "multilingual_chat",
                "description": "Translation → Chat → Translation workflow",
                "endpoint": "/api/azure/multilingual-chat",
                "method": "POST"
            })
        
        return {
            "workflows": workflows,
            "count": len(workflows)
        }
        
    except Exception as e:
        logger.error(f"❌ Workflow check failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# ============================================================================
# CONFIGURATION ENDPOINTS
# ============================================================================

@router.get("/deployments")
async def get_model_deployments():
    """
    Get information about Azure Model Deployments
    
    Returns deployment names and capabilities.
    """
    try:
        if not azure_ai_manager.models.is_available():
            raise HTTPException(
                status_code=503,
                detail="Azure Model Deployments not configured"
            )
        
        info = await azure_ai_manager.models.get_deployment_info()
        
        return {
            "status": "available",
            "deployments": info
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Deployment info failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))
