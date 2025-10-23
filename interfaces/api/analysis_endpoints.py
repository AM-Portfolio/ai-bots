"""
Issue analysis and workflow API endpoints

Handles issue analysis, code fixes, and automated workflows.
"""

from typing import Dict, Any, Optional
from fastapi import APIRouter, HTTPException, BackgroundTasks
from pydantic import BaseModel

from shared.models import SourceType, EnrichedContext
from shared.logger import get_logger

logger = get_logger(__name__)

router = APIRouter(prefix="/api", tags=["analysis"])


class IssueAnalysisRequest(BaseModel):
    issue_id: str
    source: SourceType
    repository: str = ""
    create_pr: bool = False
    publish_docs: bool = False
    confluence_space: Optional[str] = None


class WebhookPayload(BaseModel):
    source: str
    event_type: str
    data: Dict[str, Any]


@router.post("/analyze")
async def analyze_issue_endpoint(
    request: IssueAnalysisRequest,
    background_tasks: BackgroundTasks
):
    """Analyze an issue and optionally create fixes, PRs, and documentation"""
    from features.context_resolver import resolve_context
    from features.context_resolver.dto import ContextResolverInput
    from features.issue_analyzer import analyze_issue
    from features.code_generator import generate_code_fix
    from features.test_orchestrator import orchestrate_tests
    from features.doc_publisher import publish_documentation
    
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


@router.post("/webhook/{source}")
async def webhook_handler(
    source: str,
    payload: WebhookPayload,
    background_tasks: BackgroundTasks
):
    """Handle incoming webhooks from various sources"""
    logger.info(f"Received webhook from {source}: {payload.event_type}")
    
    if source == "github":
        if payload.event_type == "issues":
            action = payload.data.get("action")
            if action in ["opened", "labeled"]:
                # Add background task to process issue
                pass
    
    elif source == "grafana":
        if payload.event_type == "alert":
            logger.info("Processing Grafana alert")
    
    elif source == "jira":
        if payload.event_type == "issue_created":
            logger.info("Processing Jira issue")
    
    return {"status": "received"}


async def process_github_issue(issue_number: int, repository: str):
    """Background task to process GitHub issue"""
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