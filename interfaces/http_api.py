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
