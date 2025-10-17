from fastapi import FastAPI, HTTPException, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Dict, Any, Optional
import logging

from features.context_resolver import resolve_context
from features.context_resolver.dto import ContextResolverInput
from features.issue_analyzer import analyze_issue
from features.code_generator import generate_code_fix
from features.test_orchestrator import orchestrate_tests
from features.doc_publisher import publish_documentation
from shared.models import SourceType, EnrichedContext

logger = logging.getLogger(__name__)

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


@app.get("/")
async def root():
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


@app.get("/health")
async def health_check():
    return {"status": "healthy"}


@app.post("/api/test/llm")
async def test_llm(prompt: str, provider: str = "together"):
    """Test LLM provider with a simple prompt"""
    from shared.llm import llm_client
    
    logger.info(f"Testing LLM with provider: {provider}, prompt: {prompt[:50]}...")
    
    try:
        response = await llm_client.chat_completion(
            messages=[{"role": "user", "content": prompt}],
            temperature=0.7
        )
        
        result = {
            "success": True,
            "provider": provider,
            "response": response
        }
        
        logger.info(f"LLM test successful: {result}")
        return result
        
    except Exception as e:
        logger.error(f"LLM test failed: {e}")
        return {"success": False, "error": str(e)}


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
async def test_confluence(space_key: str):
    """Test Confluence integration"""
    from shared.clients.confluence_client import confluence_client
    
    try:
        pages = confluence_client.search_pages(space_key, limit=5)
        return {
            "success": True,
            "pages_count": len(pages),
            "pages": [{"id": p.get("id"), "title": p.get("title")} for p in pages]
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
            "error": result.error_message
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
