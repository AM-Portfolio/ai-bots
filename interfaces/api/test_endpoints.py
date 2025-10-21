"""
Integration testing API endpoints

Handles testing of various integrations like GitHub, Jira, Confluence, etc.
"""

from typing import Optional
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from shared.logger import get_logger

logger = get_logger(__name__)

router = APIRouter(prefix="/api/test", tags=["testing"])


@router.post("/github")
async def test_github(repository: str):
    """Test GitHub integration"""
    from shared.clients.github_client import GitHubClient
    
    try:
        client = GitHubClient()
        if not client.client:
            return {"success": False, "error": "GitHub client not initialized - please set up GitHub integration"}
        
        issues = await client.get_issues(repository, limit=5)
        if issues is None:
            return {"success": False, "error": "Failed to fetch issues"}
        
        return {
            "success": True,
            "issues_count": len(issues),
            "issues": [{"number": i["number"], "title": i["title"]} for i in issues]
        }
    except Exception as e:
        return {"success": False, "error": str(e)}


@router.post("/jira")
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


@router.post("/confluence")
async def test_confluence():
    """Test Confluence integration"""
    from shared.clients.confluence_client import ConfluenceClient
    
    try:
        confluence_client = ConfluenceClient()
        if not confluence_client.client:
            return {"success": False, "error": "Confluence credentials not configured"}
        
        is_connected = await confluence_client.test_connection()
        if not is_connected:
            return {"success": False, "error": "Failed to connect to Confluence"}
        
        spaces = await confluence_client.get_spaces()
        if spaces is None:
            return {"success": False, "error": "Failed to retrieve spaces"}
        
        return {
            "success": True,
            "spaces": [{"key": s.get("key"), "name": s.get("name")} for s in spaces[:5]]
        }
    except Exception as e:
        return {"success": False, "error": str(e)}


@router.post("/grafana")
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


@router.post("/context-resolver")
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


@router.post("/code-analysis")
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


@router.post("/generate-tests")
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