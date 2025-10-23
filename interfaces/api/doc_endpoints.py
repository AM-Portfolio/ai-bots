"""
Documentation generation and orchestration API endpoints

Handles documentation generation, publishing, and workflow orchestration.
"""

from typing import Optional, Dict, Any
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from shared.logger import get_logger

logger = get_logger(__name__)

router = APIRouter(prefix="/api", tags=["documentation"])


class DocGenerationRequest(BaseModel):
    """Request model for documentation generation"""
    prompt: str
    repository: Optional[str] = None
    max_files: int = 10
    format: str = "markdown"


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


@router.post("/generate-docs")
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


@router.post("/docs/orchestrate")
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