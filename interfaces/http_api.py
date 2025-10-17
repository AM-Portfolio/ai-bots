from fastapi import FastAPI, HTTPException, BackgroundTasks, Request, Depends
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
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

@app.get("/", response_class=FileResponse)
async def serve_frontend():
    """Serve the React frontend"""
    frontend_dist = Path(__file__).parent.parent / "frontend" / "dist"
    index_file = frontend_dist / "index.html"
    
    if index_file.exists():
        return FileResponse(str(index_file))
    else:
        return {
            "service": "AI Dev Agent",
            "version": "1.0.0",
            "status": "running",
            "note": "Frontend not built. Run 'cd frontend && npm run build' to build the frontend."
        }



@app.get("/health")
async def health_check():
    return {"status": "healthy"}


@app.post("/api/test/llm")
async def test_llm(prompt: str, provider: str = "together", show_thinking: bool = False):
    """Test LLM provider with a simple prompt"""
    from shared.llm import llm_client
    from shared.thinking_process import create_llm_thinking_process
    import uuid
    
    logger.info(f"Testing LLM with provider: {provider}, prompt: {prompt[:50]}...")
    
    # Create thinking process
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


@app.get("/{full_path:path}", response_class=FileResponse)
async def serve_spa_routes(full_path: str):
    """Catch-all route to serve React SPA for client-side routing"""
    frontend_dist = Path(__file__).parent.parent / "frontend" / "dist"
    index_file = frontend_dist / "index.html"
    
    if index_file.exists():
        return FileResponse(str(index_file))
    else:
        raise HTTPException(status_code=404, detail="Not found")
