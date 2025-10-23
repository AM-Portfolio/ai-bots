"""
LLM Testing API endpoints

Handles LLM provider testing, orchestration, and streaming.
"""

import uuid
import re
import sys
from pathlib import Path
from typing import Dict, Any, Optional, List
from datetime import datetime
from fastapi import APIRouter, HTTPException, Body
from fastapi.responses import StreamingResponse
from pydantic import BaseModel

from shared.logger import get_logger

logger = get_logger(__name__)

router = APIRouter(prefix="/api", tags=["llm"])


class LLMTestRequest(BaseModel):
    """Request model for LLM testing with conversation context"""
    prompt: Optional[str] = None
    provider: Optional[str] = None
    model: Optional[str] = None
    show_thinking: Optional[bool] = None
    conversation_history: Optional[List[Dict[str, Any]]] = None


class StreamOrchestrationRequest(BaseModel):
    message: str
    template_name: str = "default"
    execute_tasks: bool = True


@router.post("/test/llm")
async def test_llm(
    # Support both query params (old frontend) and body (new frontend)
    request: LLMTestRequest = Body(LLMTestRequest()),
    prompt: Optional[str] = None,
    provider: Optional[str] = None,
    model: Optional[str] = None,
    show_thinking: Optional[bool] = None
):
    """Test LLM provider - uses GitHub-LLM orchestration for GitHub-related queries with conversation context"""
    from shared.llm import llm_client
    from shared.thinking_process import create_llm_thinking_process
    from shared.utils.github_query_detector import is_github_query, get_github_context
    from orchestration.github_llm.models import QueryRequest, QueryType
    from orchestration.context_manager import ConversationContextManager
    
    # Extract parameters - prefer body, fall back to query params for backwards compatibility
    prompt = request.prompt or prompt
    provider = request.provider or provider or "together"
    model = request.model or model or "meta-llama/Llama-3.3-70B-Instruct-Turbo"
    show_thinking = request.show_thinking if request.show_thinking is not None else (show_thinking or False)
    conversation_history = request.conversation_history
    
    if not prompt:
        raise HTTPException(status_code=400, detail="Prompt is required")
    
    logger.info(f"🧪 Testing LLM with provider: {provider}, model: {model}, prompt: {prompt[:50]}...")
    
    # STEP 0: Apply conversation context if history provided
    original_prompt = prompt
    conversation_context = None
    
    if conversation_history and len(conversation_history) > 0:
        logger.info(f"🧠 Applying conversation context from {len(conversation_history)} previous messages")
        context_manager = ConversationContextManager()
        prompt, conversation_context = context_manager.augment_query_with_context(
            query=prompt,
            conversation_history=conversation_history
        )
        
        if prompt != original_prompt:
            logger.info(f"✨ Query augmented: '{original_prompt}' → '{prompt}'")
    
    # STEP 1: Detect if this is a GitHub-related query
    is_github = is_github_query(prompt)
    github_context = get_github_context(prompt) if is_github else None
    
    logger.info(f"📊 Query Analysis: github_related={is_github}, context={github_context}")
    
    # STEP 2: Route to GitHub-LLM Orchestrator if GitHub-related
    if is_github:
        return await _handle_github_orchestration(prompt, github_context, show_thinking)
    
    logger.info("🔄 Using standard orchestration pipeline...")
    
    # Use full orchestration pipeline
    return await _handle_orchestration_pipeline(prompt, provider, show_thinking)


async def _handle_github_orchestration(prompt: str, github_context: Dict, show_thinking: bool):
    """Handle GitHub-specific orchestration"""
    from orchestration.github_llm.models import QueryRequest, QueryType
    from orchestration.github_llm.query_orchestrator import GitHubLLMOrchestrator
    
    logger.info("🚀 Routing to GitHub-LLM Orchestrator for intelligent processing...")

    try:
        # Convert string query_type to QueryType enum
        query_type_str = github_context.get('query_type', 'semantic_search')
        query_type_map = {
            'code_search': QueryType.CODE_SEARCH,
            'file_explanation': QueryType.FILE_EXPLANATION,
            'semantic_search': QueryType.SEMANTIC_SEARCH,
            'documentation': QueryType.DOCUMENTATION,
            'repo_summary': QueryType.REPO_SUMMARY
        }
        query_type_enum = query_type_map.get(query_type_str, QueryType.SEMANTIC_SEARCH)
        
        # Create query request
        query_request = QueryRequest(
            query=prompt,
            query_type=query_type_enum,
            repository=github_context.get('repository'),
            max_results=5,
            include_vector_search=True,
            include_github_direct=True
        )
        
        logger.info(f"📋 GitHub-LLM Request: type={query_request.query_type}, repo={query_request.repository}")
        
        # Instantiate GitHub-LLM orchestrator with config
        from orchestration.github_llm.config import GitHubLLMConfig
        from orchestration.github_llm.query_orchestrator import GitHubLLMOrchestrator
        
        config = GitHubLLMConfig.from_settings()
        github_llm_orchestrator = GitHubLLMOrchestrator(config=config)
        
        # Process through GitHub-LLM orchestrator
        start_time = datetime.now()
        response = await github_llm_orchestrator.process_query(query_request)
        processing_time = (datetime.now() - start_time).total_seconds() * 1000
        
        logger.info(f"✅ GitHub-LLM completed in {processing_time:.2f}ms, confidence={response.confidence_score:.2f}")
        
        # Build thinking process for UI
        thinking_data = {
            "steps": [
                {
                    "id": "github_detection",
                    "title": "🎯 GitHub Query Detection",
                    "description": f"Detected as {github_context['query_type']} query",
                    "status": "completed",
                    "start_time": start_time.isoformat(),
                    "end_time": start_time.isoformat(),
                    "duration_ms": 1,
                    "metadata": github_context
                },
                {
                    "id": "github_llm_orchestration",
                    "title": "🤖 GitHub-LLM Orchestration",
                    "description": f"Queried {len(response.sources)} sources with {response.confidence_score:.0%} confidence",
                    "status": "completed",
                    "start_time": start_time.isoformat(),
                    "end_time": datetime.now().isoformat(),
                    "duration_ms": processing_time,
                    "metadata": {
                        "sources_count": len(response.sources),
                        "confidence": response.confidence_score,
                        "query_type": response.query_type.value
                    }
                }
            ],
            "workflow_id": str(uuid.uuid4()),
            "workflow_type": "github_llm",
            "start_time": start_time.isoformat(),
            "end_time": datetime.now().isoformat(),
            "total_duration_ms": processing_time,
            "status": "completed"
        }
        
        return {
            "success": True,
            "provider": "github_llm",
            "response": response.beautified_response or response.summary,
            "github_orchestration_used": True,
            "github_context": github_context,
            "metadata": {
                "query_type": response.query_type.value,
                "sources_count": len(response.sources),
                "confidence_score": response.confidence_score,
                "processing_time_ms": response.processing_time_ms
            },
            "thinking": thinking_data if show_thinking else None
        }
        
    except Exception as e:
        logger.error(f"❌ GitHub-LLM orchestration failed: {e}", exc_info=True)
        logger.info("🔄 Falling back to standard LLM pipeline...")
        # Fall through to standard pipeline
        raise


async def _handle_orchestration_pipeline(prompt: str, provider: str, show_thinking: bool):
    """Handle full orchestration pipeline"""
    from orchestration.facade import OrchestrationFacade
    from orchestration.shared.connection_factory import get_service_manager
    
    try:
        logger.info(f"🔄 Starting orchestration pipeline for message: {prompt[:100]}...")
        
        # Use connection factory to get service manager with integrations
        service_manager = await get_service_manager()
        orchestration = OrchestrationFacade(service_manager)
        
        logger.info("📋 Orchestration facade initialized with integrations, processing message...")
        
        # Process message through full pipeline: parser → enricher → prompt builder → agent
        result = await orchestration.process_message(
            message=prompt,
            template_name="default",
            execute_tasks=True
        )
        
        logger.info(f"✅ Orchestration completed successfully. Result keys: {list(result.keys())}")
        
        # Build comprehensive thinking data
        thinking_data = await _build_orchestration_thinking(result, show_thinking)
        
        # Extract the LLM response from task results
        response = "Pipeline executed successfully."
        if result.get("task_results") and len(result["task_results"]) > 0:
            last_task = result["task_results"][-1]
            # AgentTask is a dataclass, access result attribute
            if last_task.result and isinstance(last_task.result, dict) and "response" in last_task.result:
                response = last_task.result["response"]
        
        # Extract GitHub context from enriched_context object
        github_context = None
        if result.get("enriched_context"):
            github_context = _extract_github_context(result["enriched_context"])
        
        return {
            "success": True,
            "provider": provider,
            "response": response,
            "github_context": github_context,
            "thinking": thinking_data,
            "orchestration_result": result
        }
        
    except Exception as e:
        logger.error(f"❌ Orchestration pipeline failed: {e}", exc_info=True)
        return {
            "success": False,
            "error": f"Orchestration failed: {str(e)}",
            "thinking": None
        }


async def _build_orchestration_thinking(result: Dict, show_thinking: bool) -> Optional[Dict]:
    """Build thinking process data from orchestration result"""
    if not show_thinking:
        return None
    
    workflow_start = datetime.now()
    thinking_data = {
        "steps": [],
        "workflow_id": str(uuid.uuid4()),
        "workflow_type": "orchestration",
        "start_time": workflow_start.isoformat(),
        "end_time": None,
        "total_duration_ms": None,
        "status": "in_progress"
    }
    
    # Add steps based on orchestration result
    if result.get("parsed_message"):
        refs = result["parsed_message"].references
        thinking_data["steps"].append({
            "id": "parse_message",
            "title": "📝 Parse Message",
            "description": f"Found {len(refs)} reference{'s' if len(refs) != 1 else ''}",
            "status": "completed",
            "metadata": {"references_found": len(refs)}
        })
    
    if result.get("enriched_context"):
        ctx = result["enriched_context"]
        thinking_data["steps"].append({
            "id": "enrich_context",
            "title": "🔍 Enrich Context",
            "description": f"Gathered {len(ctx.context_items)} context items",
            "status": "completed",
            "metadata": {"context_items": len(ctx.context_items)}
        })
    
    # Finalize workflow
    workflow_end = datetime.now()
    thinking_data["end_time"] = workflow_end.isoformat()
    thinking_data["total_duration_ms"] = int((workflow_end - workflow_start).total_seconds() * 1000)
    thinking_data["status"] = "completed"
    
    return thinking_data


def _extract_github_context(enriched_context) -> Optional[Dict]:
    """Extract GitHub context from enriched context"""
    github_context = None
    
    if hasattr(enriched_context, 'context_items'):
        github_items = [
            item for item in enriched_context.context_items 
            if hasattr(item, 'source_type') and 'github' in item.source_type.lower()
        ]
        
        if github_items:
            github_context = {
                "items_found": len(github_items),
                "repositories": list(set([
                    item.metadata.get("repository", "unknown") 
                    for item in github_items 
                    if hasattr(item, 'metadata') and item.metadata
                ]))
            }
    
    return github_context


@router.post("/orchestration/stream")
async def stream_orchestration(request: StreamOrchestrationRequest):
    """
    Stream orchestration pipeline activity in real-time
    
    Returns Server-Sent Events showing backend processing steps
    """
    from orchestration.streaming_wrapper import StreamingOrchestrationWrapper
    from shared.services.manager import ServiceManager
    
    logger.info(f"Starting streaming orchestration for message: {request.message[:50]}...")
    
    service_manager = ServiceManager()
    wrapper = StreamingOrchestrationWrapper(service_manager)
    
    return StreamingResponse(
        wrapper.stream_process_message(
            message=request.message,
            template_name=request.template_name,
            execute_tasks=request.execute_tasks
        ),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no"
        }
    )