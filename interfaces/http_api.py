from fastapi import FastAPI, HTTPException, BackgroundTasks, Request, Depends, Body
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse, StreamingResponse
from pydantic import BaseModel
from typing import Dict, Any, Optional, List
import os
import time
from pathlib import Path
from datetime import datetime
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session

from features.context_resolver import resolve_context
from features.context_resolver.dto import ContextResolverInput
from features.issue_analyzer import analyze_issue
from features.code_generator import generate_code_fix
from features.test_orchestrator import orchestrate_tests
from features.doc_publisher import publish_documentation
from shared.models import SourceType, EnrichedContext
from shared.logger import get_logger, set_request_context, clear_request_context
from shared.config import settings
from db import ChatRepository, ChatConversation, ChatMessage
from interfaces.services_api import router as services_router
from interfaces.vector_db_api import router as vector_db_router, initialize_vector_db

logger = get_logger(__name__)

# Database session dependency
engine = create_engine(settings.database_url, echo=False)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

app = FastAPI(
    title="AI Dev Agent API",
    description="AI-powered development agent for automated bug fixing and analysis",
    version="1.0.0"
)

# Startup event to initialize Vector DB
@app.on_event("startup")
async def startup_vector_db():
    """Initialize Vector DB system on startup"""
    try:
        logger.info("🚀 Application startup - initializing Vector DB...")
        success = await initialize_vector_db()
        if success:
            logger.info("✅ Vector DB initialization complete")
        else:
            logger.error("❌ Vector DB initialization failed")
    except Exception as e:
        logger.error(f"❌ Vector DB startup error: {e}", exc_info=True)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# Request logging middleware
@app.middleware("http")
async def log_requests(request: Request, call_next):
    """Log all HTTP requests with timing and context"""
    # Set request context for logging
    set_request_context()
    
    start_time = time.time()
    method = request.method
    path = request.url.path
    
    logger.info(
        f"→ Incoming {method} {path}",
        method=method,
        path=path,
        client_host=request.client.host if request.client else "unknown"
    )
    
    try:
        response = await call_next(request)
        duration_ms = (time.time() - start_time) * 1000
        
        logger.log_api_request(
            method=method,
            path=path,
            status_code=response.status_code,
            duration_ms=duration_ms
        )
        
        return response
    except Exception as e:
        duration_ms = (time.time() - start_time) * 1000
        logger.error(
            f"← Request {method} {path} failed",
            method=method,
            path=path,
            error=str(e),
            duration_ms=duration_ms
        )
        raise
    finally:
        clear_request_context()

# Include service management API router
app.include_router(services_router)

# Include Vector DB API router
app.include_router(vector_db_router)

# Serve React frontend static files in production
frontend_dist = Path(__file__).parent.parent / "frontend" / "dist"
if frontend_dist.exists() and frontend_dist.is_dir():
    logger.info(f"Mounting static files from {frontend_dist}")
    app.mount("/assets", StaticFiles(directory=str(frontend_dist / "assets")), name="static-assets")
else:
    logger.warning(f"Frontend dist directory not found at {frontend_dist}")


class WebhookPayload(BaseModel):
    source: str
    event_type: str
    data: Dict[str, Any]


class IssueAnalysisRequest(BaseModel):
    issue_id: str
    source: SourceType
    repository: str = ""
    create_pr: bool = False
    publish_docs: bool = False
    confluence_space: Optional[str] = None


@app.get("/api")
async def api_root():
    return {
        "service": "AI Dev Agent",
        "version": "1.0.0",
        "status": "running",
        "endpoints": {
            "health": "/health",
            "analyze": "/api/analyze",
            "webhook": "/api/webhook"
        }
    }

@app.get("/")
async def serve_frontend():
    """Serve the React frontend or API info"""
    frontend_dist = Path(__file__).parent.parent / "frontend" / "dist"
    index_file = frontend_dist / "index.html"
    
    if index_file.exists():
        return FileResponse(str(index_file))
    else:
        return {
            "service": "AI Dev Agent",
            "version": "1.0.0",
            "status": "running",
            "note": "Frontend not built. Run 'cd frontend && npm run build' to build the frontend.",
            "endpoints": {
                "health": "/health",
                "analyze": "/api/analyze",
                "webhook": "/api/webhook",
                "docs": "/docs"
            }
        }



@app.get("/health")
async def health_check():
    return {"status": "healthy"}


class LLMTestRequest(BaseModel):
    """Request model for LLM testing with conversation context"""
    prompt: Optional[str] = None
    provider: Optional[str] = None
    model: Optional[str] = None
    show_thinking: Optional[bool] = None
    conversation_history: Optional[List[Dict[str, Any]]] = None


@app.post("/api/test/llm")
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
    from interfaces.vector_db_api import github_llm_orchestrator
    from orchestration.github_llm.models import QueryRequest, QueryType
    from orchestration.context_manager import ConversationContextManager
    import uuid
    
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
    
    # STEP 2: Route to GitHub-LLM Orchestrator if GitHub-related AND orchestrator is initialized
    if is_github and github_llm_orchestrator is not None:
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
    elif is_github and github_llm_orchestrator is None:
        logger.warning("⚠️  GitHub query detected but orchestrator not initialized yet. Using standard pipeline.")
    
    logger.info(f"🔄 Using standard orchestration pipeline...")
    
    # ALWAYS use full orchestration pipeline
    if True:  # Always use orchestration
        from orchestration.facade import OrchestrationFacade
        from shared.services.manager import ServiceManager
        
        try:
            logger.info(f"🔄 Starting orchestration pipeline for message: {prompt[:100]}...")
            
            # Use connection factory to get service manager with integrations
            from orchestration.shared.connection_factory import get_service_manager
            service_manager = await get_service_manager()
            orchestration = OrchestrationFacade(service_manager)
            
            logger.info("📋 Orchestration facade initialized with integrations, processing message...")
            
            # Try primary orchestration pipeline with resilient fallback
            orchestration_error = None
            try:
                # Process message through full pipeline: parser → enricher → prompt builder → agent
                result = await orchestration.process_message(
                    message=prompt,
                    template_name="default",
                    execute_tasks=True
                )
                
                logger.info(f"✅ Orchestration completed successfully. Result keys: {list(result.keys())}")
            except Exception as e:
                orchestration_error = e
                logger.warning(f"⚠️  Orchestration pipeline error: {str(e)[:200]}")
                logger.info(f"🔄 Attempting resilient fallback with direct LLM providers...")
                
                # Build error thinking data
                error_thinking = {
                    "steps": [{
                        "id": "orchestration_pipeline",
                        "title": "🚀 Orchestration Pipeline",
                        "description": "Primary pipeline failed, trying fallback providers",
                        "status": "failed",
                        "start_time": datetime.now().isoformat(),
                        "end_time": datetime.now().isoformat(),
                        "duration_ms": 0,
                        "error": str(e)[:200],
                        "metadata": {"error_type": type(e).__name__}
                    }],
                    "workflow_id": str(uuid.uuid4()),
                    "workflow_type": "resilient_fallback",
                    "start_time": datetime.now().isoformat(),
                    "end_time": None,
                    "total_duration_ms": None,
                    "status": "in_progress"
                }
                
                # Try resilient fallback with multiple providers
                from shared.llm_providers.resilient_orchestrator import get_resilient_orchestrator
                
                orchestrator = get_resilient_orchestrator()
                
                try:
                    fallback_start = datetime.now()
                    response_text, metadata = await orchestrator.chat_completion_with_fallback(
                        messages=[{"role": "user", "content": prompt}],
                        temperature=0.7,
                        preferred_provider=provider,
                        model=model
                    )
                    
                    fallback_duration = (datetime.now() - fallback_start).total_seconds() * 1000
                    
                    logger.info(f"✅ Resilient fallback succeeded with {metadata.get('provider_used')}")
                    
                    # Add successful fallback step
                    error_thinking["steps"].append({
                        "id": "resilient_fallback",
                        "title": f"🔄 Resilient Fallback → {metadata.get('provider_used', 'unknown').upper()}",
                        "description": f"Successfully got response from {metadata.get('provider_used')} provider (attempt {metadata.get('attempt_number', 1)})",
                        "status": "completed",
                        "start_time": fallback_start.isoformat(),
                        "end_time": datetime.now().isoformat(),
                        "duration_ms": fallback_duration,
                        "error": None,
                        "metadata": metadata
                    })
                    error_thinking["status"] = "completed"
                    error_thinking["end_time"] = datetime.now().isoformat()
                    
                    return {
                        "success": True,
                        "provider": metadata.get('provider_used', provider),
                        "response": response_text,
                        "fallback_used": True,
                        "fallback_metadata": metadata,
                        "thinking": error_thinking if show_thinking else None
                    }
                except Exception as fallback_error:
                    logger.error(f"❌ All fallback attempts failed: {fallback_error}")
                    
                    # Add failed fallback step
                    error_thinking["steps"].append({
                        "id": "resilient_fallback",
                        "title": "🔄 Resilient Fallback",
                        "description": "All fallback providers failed",
                        "status": "failed",
                        "start_time": datetime.now().isoformat(),
                        "end_time": datetime.now().isoformat(),
                        "duration_ms": 0,
                        "error": str(fallback_error)[:200],
                        "metadata": {"error_type": type(fallback_error).__name__}
                    })
                    error_thinking["status"] = "failed"
                    error_thinking["end_time"] = datetime.now().isoformat()
                    
                    return {
                        "success": False,
                        "error": f"All providers failed. Pipeline: {str(orchestration_error)[:100]}. Fallback: {str(fallback_error)[:100]}",
                        "thinking": error_thinking if show_thinking else None
                    }
            
            # If we got here, orchestration succeeded
            
            # Convert orchestration result to LLM test format with timeline
            workflow_start = datetime.now()
            
            # Step 1: Create task plan showing what we WILL do
            task_plan = []
            
            # Always plan these steps
            task_plan.append({
                "id": "parse_message",
                "title": "📝 Parse Message",
                "description": "Analyzing user message to extract references and context",
                "status": "pending"
            })
            
            task_plan.append({
                "id": "enrich_context",
                "title": "🔍 Enrich Context",
                "description": "Gathering additional information from integrations",
                "status": "pending"
            })
            
            task_plan.append({
                "id": "build_prompt",
                "title": "🏗️  Build Prompt",
                "description": "Creating optimized prompt for AI model",
                "status": "pending"
            })
            
            task_plan.append({
                "id": "execute_tasks",
                "title": "⚡ Execute Tasks",
                "description": "Running AI analysis and generating response",
                "status": "pending"
            })
            
            # Step 2: Build thinking data showing execution progress
            thinking_data = {
                "steps": [],
                "workflow_id": str(uuid.uuid4()),
                "workflow_type": "orchestration",
                "start_time": workflow_start.isoformat(),
                "end_time": None,
                "total_duration_ms": None,
                "status": "in_progress"
            }
            
            # Step 3: Execute and update each step
            step_start = datetime.now()
            
            # Parse Message
            if result.get("parsed_message"):
                refs = result["parsed_message"].references
                github_refs = [r.normalized_value for r in refs if r.type.value.startswith('github')]
                jira_refs = [r.normalized_value for r in refs if r.type.value.startswith('jira')]
                confluence_refs = [r.normalized_value for r in refs if r.type.value.startswith('confluence')]
                
                description = f"Found {len(refs)} reference{'s' if len(refs) != 1 else ''}"
                if github_refs:
                    description += f" • {len(github_refs)} GitHub"
                if jira_refs:
                    description += f" • {len(jira_refs)} Jira"
                if confluence_refs:
                    description += f" • {len(confluence_refs)} Confluence"
                
                step_end = datetime.now()
                thinking_data["steps"].append({
                    "id": "parse_message",
                    "title": "📝 Parse Message",
                    "description": description,
                    "status": "completed",
                    "start_time": step_start.isoformat(),
                    "end_time": step_end.isoformat(),
                    "duration_ms": int((step_end - step_start).total_seconds() * 1000),
                    "error": None,
                    "metadata": {
                        "references_found": len(refs),
                        "github_refs": github_refs,
                        "jira_refs": jira_refs,
                        "confluence_refs": confluence_refs
                    }
                })
            
            # Enrich Context
            step_start = datetime.now()
            if result.get("enriched_context"):
                ctx = result["enriched_context"]
                cache_hits = len([item for item in ctx.context_items if item.cache_hit])
                
                description = f"Gathered {len(ctx.context_items)} context item{'s' if len(ctx.context_items) != 1 else ''}"
                if cache_hits > 0:
                    description += f" • {cache_hits} from cache ⚡"
                
                step_end = datetime.now()
                thinking_data["steps"].append({
                    "id": "enrich_context",
                    "title": "🔍 Enrich Context",
                    "description": description,
                    "status": "completed",
                    "start_time": step_start.isoformat(),
                    "end_time": step_end.isoformat(),
                    "duration_ms": int((step_end - step_start).total_seconds() * 1000),
                    "error": None,
                    "metadata": {
                        "context_items": len(ctx.context_items),
                        "cache_hits": cache_hits
                    }
                })
            
            # Build Prompt
            step_start = datetime.now()
            if result.get("formatted_prompt"):
                prompt_len = len(result["formatted_prompt"].system_prompt) + len(result["formatted_prompt"].user_prompt)
                description = f"Created {prompt_len:,} character prompt for AI model"
                
                step_end = datetime.now()
                thinking_data["steps"].append({
                    "id": "build_prompt",
                    "title": "🏗️  Build Prompt",
                    "description": description,
                    "status": "completed",
                    "start_time": step_start.isoformat(),
                    "end_time": step_end.isoformat(),
                    "duration_ms": int((step_end - step_start).total_seconds() * 1000),
                    "error": None,
                    "metadata": {
                        "prompt_length": prompt_len,
                        "system_prompt_length": len(result["formatted_prompt"].system_prompt),
                        "user_prompt_length": len(result["formatted_prompt"].user_prompt)
                    }
                })
            
            # Execute Tasks
            step_start = datetime.now()
            if result.get("task_results"):
                tasks = result["task_results"]
                successful = len([t for t in tasks if t.status == "completed"])
                
                description = f"Executed {len(tasks)} task{'s' if len(tasks) != 1 else ''} • {successful} successful"
                
                step_end = datetime.now()
                thinking_data["steps"].append({
                    "id": "execute_tasks",
                    "title": "⚡ Execute Tasks",
                    "description": description,
                    "status": "completed",
                    "start_time": step_start.isoformat(),
                    "end_time": step_end.isoformat(),
                    "duration_ms": int((step_end - step_start).total_seconds() * 1000),
                    "error": None,
                    "metadata": {
                        "tasks_executed": len(tasks),
                        "tasks_successful": successful,
                        "task_types": [t.task_type for t in tasks]
                    }
                })
            
            # Mark any remaining planned steps as skipped
            completed_ids = [step["id"] for step in thinking_data["steps"]]
            for planned_step in task_plan:
                if planned_step["id"] not in completed_ids:
                    thinking_data["steps"].append({
                        "id": planned_step["id"],
                        "title": planned_step["title"],
                        "description": "Step was skipped",
                        "status": "skipped",
                        "start_time": None,
                        "end_time": None,
                        "duration_ms": None,
                        "error": None,
                        "metadata": {}
                    })
            
            # Finalize workflow
            workflow_end = datetime.now()
            thinking_data["end_time"] = workflow_end.isoformat()
            thinking_data["total_duration_ms"] = int((workflow_end - workflow_start).total_seconds() * 1000)
            thinking_data["status"] = "completed"
            
            # Extract the LLM response from task results
            response = "Pipeline executed successfully."
            if result.get("task_results") and len(result["task_results"]) > 0:
                # Get the last task result as the response
                last_result = result["task_results"][-1]
                if hasattr(last_result, 'result') and isinstance(last_result.result, dict):
                    if "response" in last_result.result:
                        response = last_result.result["response"]
                    elif "analysis" in last_result.result:
                        response = last_result.result["analysis"]
                    elif "diagnosis" in last_result.result:
                        response = last_result.result["diagnosis"]
            
            # Extract GitHub context from enriched_context object
            github_context = None
            if result.get("enriched_context"):
                enriched = result["enriched_context"]
                github_items = [
                    item for item in enriched.context_items 
                    if item.source_type.value.startswith('GITHUB')
                ]
                if github_items:
                    github_context = {
                        "items": [
                            {
                                "type": item.source_type.value,
                                "id": item.source_id,
                                "data_preview": str(item.data)[:200] if item.data else None
                            }
                            for item in github_items
                        ]
                    }
            
            return {
                "success": True,
                "provider": provider,
                "response": response,
                "github_context": github_context,
                "thinking": thinking_data if show_thinking else None,
                "orchestration_result": result
            }
            
        except Exception as e:
            logger.error(f"❌ Orchestration pipeline failed: {e}", exc_info=True)
            return {
                "success": False,
                "error": f"Orchestration failed: {str(e)}",
                "thinking": None
            }
    
    # Simple mode without orchestration (backward compatibility)
    workflow_id = str(uuid.uuid4())
    thinking = create_llm_thinking_process(workflow_id)
    
    try:
        # Step 1: Validate input
        thinking.start_step("validate_input")
        if not prompt or len(prompt.strip()) == 0:
            thinking.fail_step("validate_input", "Empty prompt provided")
            return {"success": False, "error": "Empty prompt", "thinking": thinking.to_dict() if show_thinking else None}
        thinking.complete_step("validate_input", {"prompt_length": len(prompt)})
        
        # Step 2: Check GitHub context
        thinking.start_step("check_github")
        github_context = None
        if "repo" in prompt.lower() or "repository" in prompt.lower() or "github" in prompt.lower():
            # Extract potential repo mentions
            import re
            repo_pattern = r'([a-zA-Z0-9_-]+/[a-zA-Z0-9_-]+)'
            repos = re.findall(repo_pattern, prompt)
            if repos:
                github_context = {"mentioned_repos": repos}
                thinking.complete_step("check_github", {"repos_found": repos})
            else:
                thinking.skip_step("check_github", "No specific repo format found")
        else:
            thinking.skip_step("check_github", "No GitHub keywords detected")
        
        # Step 3: Select provider
        thinking.start_step("select_provider")
        thinking.complete_step("select_provider", {"provider": provider})
        
        # Step 4: Prepare prompt
        thinking.start_step("prepare_prompt")
        messages = [{"role": "user", "content": prompt}]
        if github_context:
            messages[0]["content"] = f"[GitHub Context: {github_context}]\n\n{prompt}"
        thinking.complete_step("prepare_prompt", {"message_count": len(messages)})
        
        # Step 5: Call LLM
        thinking.start_step("call_llm")
        response = await llm_client.chat_completion(
            messages=messages,
            temperature=0.7
        )
        thinking.complete_step("call_llm", {"response_length": len(response) if response else 0})
        
        # Step 6: Process response
        thinking.start_step("process_response")
        thinking.complete_step("process_response", {"final_response_length": len(response) if response else 0})
        
        thinking.end_time = datetime.now()
        
        result = {
            "success": True,
            "provider": provider,
            "response": response,
            "github_context": github_context,
            "thinking": thinking.to_dict() if show_thinking else None
        }
        
        logger.info(f"LLM test successful with thinking process")
        return result
        
    except Exception as e:
        logger.error(f"LLM test failed: {e}")
        if thinking.steps:
            current_step = [s for s in thinking.steps if s.status.value == "in_progress"]
            if current_step:
                thinking.fail_step(current_step[0].id, str(e))
        return {"success": False, "error": str(e), "thinking": thinking.to_dict() if show_thinking else None}


class StreamOrchestrationRequest(BaseModel):
    message: str
    template_name: str = "default"
    execute_tasks: bool = True


@app.post("/api/orchestration/stream")
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


@app.post("/api/test/github")
async def test_github(repository: str):
    """Test GitHub integration"""
    from shared.clients.github_replit_client import github_replit_client
    
    try:
        client = await github_replit_client._get_client()
        if not client:
            return {"success": False, "error": "GitHub client not initialized - please set up GitHub integration"}
        
        repo = client.get_repo(repository)
        issues = list(repo.get_issues(state="open")[:5])
        return {
            "success": True,
            "issues_count": len(issues),
            "issues": [{"number": i.number, "title": i.title} for i in issues]
        }
    except Exception as e:
        return {"success": False, "error": str(e)}


@app.post("/api/test/jira")
async def test_jira(project_key: str):
    """Test Jira integration"""
    from shared.clients.jira_client import jira_client
    
    try:
        issues = jira_client.search_issues(f"project = {project_key} AND status = Open", max_results=5)
        return {
            "success": True,
            "issues_count": len(issues),
            "issues": [{"key": i.get("key"), "summary": i.get("summary")} for i in issues]
        }
    except Exception as e:
        return {"success": False, "error": str(e)}


@app.post("/api/test/confluence")
async def test_confluence():
    """Test Confluence integration"""
    from shared.clients.confluence_replit_client import confluence_replit_client
    
    try:
        if not confluence_replit_client.is_configured():
            return {"success": False, "error": "Confluence credentials not configured"}
        
        is_connected = await confluence_replit_client.test_connection()
        if not is_connected:
            return {"success": False, "error": "Failed to connect to Confluence"}
        
        spaces = await confluence_replit_client.get_spaces()
        if spaces is None:
            return {"success": False, "error": "Failed to retrieve spaces"}
        
        return {
            "success": True,
            "spaces": [{"key": s.get("key"), "name": s.get("name")} for s in spaces[:5]]
        }
    except Exception as e:
        return {"success": False, "error": str(e)}


@app.post("/api/test/grafana")
async def test_grafana():
    """Test Grafana integration"""
    from shared.clients.grafana_client import grafana_client
    
    try:
        alerts = await grafana_client.get_alerts()
        return {
            "success": True,
            "alerts_count": len(alerts),
            "alerts": [{"id": a.get("id"), "name": a.get("name")} for a in alerts[:5]]
        }
    except Exception as e:
        return {"success": False, "error": str(e)}


@app.post("/api/test/context-resolver")
async def test_context_resolver(issue_id: str, source: str, repository: str = ""):
    """Test context resolver"""
    from features.context_resolver import resolve_context
    from features.context_resolver.dto import ContextResolverInput
    from shared.models import SourceType
    
    try:
        context_input = ContextResolverInput(
            issue_id=issue_id,
            source=SourceType(source),
            repository=repository,
            include_logs=True,
            include_metrics=True,
            include_related_issues=True
        )
        
        result = await resolve_context(context_input)
        
        return {
            "success": result.success,
            "data": result.enriched_data if result.success else None,
            "error": result.error_message
        }
    except Exception as e:
        return {"success": False, "error": str(e)}


@app.post("/api/test/code-analysis")
async def test_code_analysis(code: str, context: str):
    """Test LLM code analysis"""
    from shared.llm import llm_client
    
    try:
        analysis = await llm_client.analyze_code(code, context, task="analyze")
        return {
            "success": True,
            "analysis": analysis
        }
    except Exception as e:
        return {"success": False, "error": str(e)}


@app.post("/api/test/generate-tests")
async def test_generate_tests(code: str, language: str = "python"):
    """Test test generation"""
    from shared.llm import llm_client
    
    try:
        tests = await llm_client.generate_tests(code, language)
        return {
            "success": True,
            "tests": tests
        }
    except Exception as e:
        return {"success": False, "error": str(e)}


class DocGenerationRequest(BaseModel):
    """Request model for documentation generation"""
    prompt: str
    repository: Optional[str] = None
    max_files: int = 10
    format: str = "markdown"


@app.post("/api/generate-docs")
async def generate_docs_endpoint(request: DocGenerationRequest):
    """
    Generate documentation from natural language prompt
    
    Example prompts:
    - "Generate API documentation for owner/repo focusing on authentication"
    - "Document the user service in myorg/myapp"
    - "Create architecture docs for owner/repo"
    """
    from features.doc_generator import generate_documentation
    
    logger.info(f"Generating documentation from prompt: {request.prompt[:100]}...")
    
    try:
        result = await generate_documentation(
            prompt=request.prompt,
            repository=request.repository,
            max_files=request.max_files,
            format=request.format
        )
        
        return {
            "success": result.success,
            "documentation": result.documentation,
            "files_analyzed": result.files_analyzed,
            "repository": result.repository,
            "github_commit": result.github_commit,
            "metadata": result.metadata,
            "error": result.error_message
        }
        
    except Exception as e:
        logger.error(f"Documentation generation failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


class DocOrchestrationRequest(BaseModel):
    """Request model for complete documentation workflow"""
    prompt: str
    repository: Optional[str] = None
    max_files: int = 10
    
    commit_to_github: bool = True
    commit_path: str = "docs/AI_GENERATED_DOCS.md"
    commit_message: Optional[str] = None
    
    publish_to_confluence: bool = False
    confluence_space_key: Optional[str] = None
    confluence_parent_id: Optional[str] = None
    
    create_jira_ticket: bool = False
    jira_project_key: Optional[str] = None


@app.post("/api/docs/orchestrate")
async def orchestrate_docs_endpoint(request: DocOrchestrationRequest):
    """
    Complete documentation workflow: analyze → generate → commit → publish → ticket
    
    Example:
    ```json
    {
      "prompt": "Document the API for owner/repo",
      "repository": "owner/repo",
      "commit_to_github": true,
      "publish_to_confluence": true,
      "confluence_space_key": "DOCS",
      "create_jira_ticket": true,
      "jira_project_key": "PROJ"
    }
    ```
    """
    from features.doc_orchestrator import orchestrate_documentation
    
    logger.info(f"Orchestrating documentation workflow for: {request.prompt[:100]}...")
    
    try:
        result = await orchestrate_documentation(
            prompt=request.prompt,
            repository=request.repository,
            max_files=request.max_files,
            commit_to_github=request.commit_to_github,
            commit_path=request.commit_path,
            commit_message=request.commit_message,
            publish_to_confluence=request.publish_to_confluence,
            confluence_space_key=request.confluence_space_key,
            confluence_parent_id=request.confluence_parent_id,
            create_jira_ticket=request.create_jira_ticket,
            jira_project_key=request.jira_project_key
        )
        
        return {
            "success": result.success,
            "documentation": result.documentation,
            "files_analyzed": result.files_analyzed,
            "repository": result.repository,
            "github_commit": result.github_commit,
            "confluence_page": result.confluence_page,
            "jira_ticket": result.jira_ticket,
            "workflow_summary": result.workflow_summary,
            "error": result.error_message,
            "thinking": result.thinking
        }
        
    except Exception as e:
        logger.error(f"Documentation orchestration failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/analyze")
async def analyze_issue_endpoint(
    request: IssueAnalysisRequest,
    background_tasks: BackgroundTasks
):
    logger.info(f"Analyzing issue: {request.issue_id} from {request.source}")
    
    try:
        context_input = ContextResolverInput(
            issue_id=request.issue_id,
            source=request.source,
            repository=request.repository,
            include_logs=True,
            include_metrics=True,
            include_related_issues=True
        )
        
        context_result = await resolve_context(context_input)
        
        if not context_result.success:
            raise HTTPException(status_code=400, detail=context_result.error_message)
        
        enriched_context = EnrichedContext(**context_result.enriched_data)
        
        analysis = await analyze_issue(enriched_context)
        
        fixes = await generate_code_fix(analysis)
        
        response = {
            "issue_id": request.issue_id,
            "analysis": analysis.model_dump(),
            "fixes_count": len(fixes),
            "pr_url": None,
            "documentation_page": None
        }
        
        if request.create_pr and fixes:
            pr_url = await orchestrate_tests(
                fixes=fixes,
                repository=request.repository
            )
            response["pr_url"] = pr_url
        
        if request.publish_docs and request.confluence_space:
            page_id = await publish_documentation(
                analysis=analysis,
                space_key=request.confluence_space
            )
            response["documentation_page"] = page_id
        
        return response
    
    except Exception as e:
        logger.error(f"Analysis failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# Chat History Endpoints
class ChatMessageModel(BaseModel):
    role: str
    content: str
    duration: Optional[float] = None

class SaveConversationRequest(BaseModel):
    conversation_id: Optional[int] = None
    title: str
    provider: str
    messages: List[ChatMessageModel]

class ConversationResponse(BaseModel):
    id: int
    title: str
    provider: str
    created_at: datetime
    updated_at: datetime
    message_count: int = 0

class MessageResponse(BaseModel):
    id: int
    role: str
    content: str
    duration: Optional[float]
    created_at: datetime

@app.post("/api/chat/conversations")
async def save_conversation(request: SaveConversationRequest, db: Session = Depends(get_db)):
    """Save or update a chat conversation"""
    try:
        chat_repo = ChatRepository(db)
        
        if request.conversation_id:
            # Update existing conversation
            conversation = chat_repo.get_conversation(request.conversation_id)
            if not conversation:
                raise HTTPException(status_code=404, detail="Conversation not found")
        else:
            # Create new conversation
            conversation = chat_repo.create_conversation(
                title=request.title,
                provider=request.provider
            )
        
        # Add messages
        for msg in request.messages:
            chat_repo.add_message(
                conversation_id=conversation.id,
                role=msg.role,
                content=msg.content,
                duration=msg.duration
            )
        
        return {"success": True, "conversation_id": conversation.id}
    except Exception as e:
        logger.error(f"Failed to save conversation: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/chat/conversations", response_model=List[ConversationResponse])
async def list_conversations(db: Session = Depends(get_db)):
    """List all chat conversations"""
    try:
        chat_repo = ChatRepository(db)
        conversations = chat_repo.list_conversations(limit=50)
        
        result = []
        for conv in conversations:
            result.append(ConversationResponse(
                id=conv.id,
                title=conv.title,
                provider=conv.provider,
                created_at=conv.created_at,
                updated_at=conv.updated_at,
                message_count=len(conv.messages) if conv.messages else 0
            ))
        
        return result
    except Exception as e:
        logger.error(f"Failed to list conversations: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/chat/conversations/{conversation_id}/messages", response_model=List[MessageResponse])
async def get_conversation_messages(conversation_id: int, db: Session = Depends(get_db)):
    """Get all messages for a conversation"""
    try:
        chat_repo = ChatRepository(db)
        messages = chat_repo.get_messages(conversation_id)
        
        return [
            MessageResponse(
                id=msg.id,
                role=msg.role,
                content=msg.content,
                duration=msg.duration,
                created_at=msg.created_at
            )
            for msg in messages
        ]
    except Exception as e:
        logger.error(f"Failed to get messages: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.delete("/api/chat/conversations/{conversation_id}")
async def delete_conversation(conversation_id: int, db: Session = Depends(get_db)):
    """Delete a chat conversation"""
    try:
        chat_repo = ChatRepository(db)
        success = chat_repo.delete_conversation(conversation_id)
        
        if not success:
            raise HTTPException(status_code=404, detail="Conversation not found")
        
        return {"success": True}
    except Exception as e:
        logger.error(f"Failed to delete conversation: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/webhook/{source}")
async def webhook_handler(
    source: str,
    payload: WebhookPayload,
    background_tasks: BackgroundTasks
):
    logger.info(f"Received webhook from {source}: {payload.event_type}")
    
    if source == "github":
        if payload.event_type == "issues":
            action = payload.data.get("action")
            if action in ["opened", "labeled"]:
                issue = payload.data.get("issue", {})
                labels = [label.get("name") for label in issue.get("labels", [])]
                
                if "bug" in labels or "ai-fix" in labels:
                    background_tasks.add_task(
                        process_github_issue,
                        issue.get("number"),
                        payload.data.get("repository", {}).get("full_name")
                    )
    
    elif source == "grafana":
        if payload.event_type == "alert":
            logger.info("Processing Grafana alert")
    
    elif source == "jira":
        if payload.event_type == "issue_created":
            logger.info("Processing Jira issue")
    
    return {"status": "received"}


async def process_github_issue(issue_number: int, repository: str):
    logger.info(f"Processing GitHub issue {repository}#{issue_number}")
    
    try:
        request = IssueAnalysisRequest(
            issue_id=str(issue_number),
            source=SourceType.GITHUB,
            repository=repository,
            create_pr=True,
            publish_docs=False
        )
        
        await analyze_issue_endpoint(request, BackgroundTasks())
    except Exception as e:
        logger.error(f"Failed to process issue: {e}")


# ==================== COMMIT WORKFLOW API ====================

from orchestration.commit_workflow import CommitWorkflowRouter, GitHubOperations
from orchestration.commit_workflow.approval_system import get_approval_manager

class CommitWorkflowRequest(BaseModel):
    """Request to initiate commit/publish workflow"""
    message: str
    repository: Optional[str] = None
    branch: Optional[str] = None
    files: Optional[Dict[str, str]] = None
    context: Optional[Dict[str, Any]] = None


@app.post("/api/commit/parse-intent")
async def parse_commit_intent(request: CommitWorkflowRequest):
    """
    Parse user message to detect commit/publish intent
    Returns approval template for user confirmation
    """
    from shared.llm_providers.resilient_orchestrator import get_llm_orchestrator
    
    logger.info(f"🧠 Parsing commit intent: {request.message[:100]}...")
    
    try:
        llm_orchestrator = get_llm_orchestrator()
        router = CommitWorkflowRouter(llm_orchestrator)
        
        intent = await router.parse_user_intent(request.message, request.context)
        
        workflow_result = await router.route_to_workflow(
            intent,
            {
                "repository": request.repository,
                "branch": request.branch or "main",
                "files": request.files or {},
                "context": request.context or {}
            }
        )
        
        approval_manager = get_approval_manager()
        approval_request = approval_manager.create_approval_request(
            operation_type=workflow_result["workflow"],
            title=workflow_result["template"].title,
            description=workflow_result["template"].description,
            template_data=workflow_result["template"].fields
        )
        
        return {
            "success": True,
            "intent": {
                "platform": intent.platform,
                "action": intent.action,
                "confidence": intent.confidence
            },
            "workflow": workflow_result["workflow"],
            "template": workflow_result["template"].fields,
            "approval_request": approval_request.to_dict(),
            "requires_approval": workflow_result.get("requires_approval", True)
        }
        
    except Exception as e:
        logger.error(f"Failed to parse commit intent: {e}")
        raise HTTPException(status_code=500, detail=str(e))


class ApprovalResponse(BaseModel):
    """User's response to approval request"""
    approval_id: str
    approved: bool
    updated_template: Optional[Dict[str, Any]] = None
    rejection_reason: Optional[str] = None


@app.post("/api/commit/approve")
async def approve_commit(response: ApprovalResponse):
    """
    User approves/rejects commit operation
    If approved, executes the operation
    """
    approval_manager = get_approval_manager()
    
    logger.info(f"📋 Processing approval: {response.approval_id}, approved={response.approved}")
    
    try:
        if not response.approved:
            approval_manager.reject_request(response.approval_id, response.rejection_reason)
            return {
                "success": True,
                "status": "rejected",
                "message": "Operation cancelled by user"
            }
        
        approval_request = approval_manager.approve_request(
            response.approval_id,
            response.updated_template
        )
        
        if not approval_request:
            raise HTTPException(status_code=404, detail="Approval request not found or expired")
        
        result = await execute_commit_operation(
            operation_type=approval_request.operation_type,
            template_data=approval_request.template_data
        )
        
        return {
            "success": True,
            "status": "approved",
            "operation_result": result
        }
        
    except Exception as e:
        logger.error(f"Failed to process approval: {e}")
        raise HTTPException(status_code=500, detail=str(e))


async def execute_commit_operation(operation_type: str, template_data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Execute approved commit/publish operation
    Returns result with links for next actions
    """
    logger.info(f"⚡ Executing operation: {operation_type}")
    
    github_ops = GitHubOperations()
    
    if operation_type == "github_commit":
        result = await github_ops.commit_files(
            repository=template_data["repository"],
            branch=template_data["branch"],
            files=template_data.get("files", {}),
            commit_message=template_data["commit_message"],
            commit_description=template_data.get("commit_description")
        )
        
        if result["success"]:
            return {
                **result,
                "next_actions": [
                    {
                        "action": "view_commit",
                        "label": "View Commit",
                        "url": result["commit_url"]
                    },
                    {
                        "action": "create_pr",
                        "label": "Create Pull Request",
                        "prompt": "Would you like to create a pull request for this commit?"
                    }
                ]
            }
        return result
    
    elif operation_type == "github_pr":
        result = await github_ops.create_pull_request(
            repository=template_data["repository"],
            source_branch=template_data.get("source_branch", "main"),
            target_branch=template_data.get("target_branch", "main"),
            title=template_data.get("pr_title", ""),
            description=template_data.get("pr_description"),
            reviewers=template_data.get("reviewers"),
            assignees=template_data.get("assignees"),
            labels=template_data.get("labels"),
            draft=template_data.get("draft", False)
        )
        
        if result["success"]:
            return {
                **result,
                "next_actions": [
                    {
                        "action": "view_pr",
                        "label": "View Pull Request",
                        "url": result["pr_url"]
                    }
                ]
            }
        return result
    
    elif operation_type == "github_commit_and_pr":
        result = await github_ops.commit_and_create_pr(
            repository=template_data["repository"],
            branch=template_data.get("branch", "main"),
            files=template_data.get("files", {}),
            commit_message=template_data["commit_message"],
            pr_title=template_data.get("pr_title", template_data["commit_message"]),
            pr_description=template_data.get("pr_description", ""),
            target_branch=template_data.get("target_branch", "main")
        )
        
        if result["success"]:
            return {
                **result,
                "next_actions": [
                    {
                        "action": "view_commit",
                        "label": "View Commit",
                        "url": result["commit_url"]
                    },
                    {
                        "action": "view_pr",
                        "label": "View Pull Request",
                        "url": result["pr_url"]
                    }
                ]
            }
        return result
    
    else:
        logger.warning(f"Unknown operation type: {operation_type}")
        return {"success": False, "error": "Unknown operation type"}


@app.get("/api/commit/pending-approvals")
async def list_pending_approvals():
    """List all pending approval requests"""
    approval_manager = get_approval_manager()
    pending = approval_manager.list_pending_requests()
    
    return {
        "pending_approvals": [req.to_dict() for req in pending],
        "count": len(pending)
    }


@app.get("/{full_path:path}", response_class=FileResponse)
async def serve_spa_routes(full_path: str):
    """Catch-all route to serve React SPA for client-side routing"""
    frontend_dist = Path(__file__).parent.parent / "frontend" / "dist"
    index_file = frontend_dist / "index.html"
    
    if index_file.exists():
        return FileResponse(str(index_file))
    else:
        raise HTTPException(status_code=404, detail="Not found")
