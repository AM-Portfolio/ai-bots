"""Documentation Orchestrator - Complete workflow for AI-driven documentation"""
import logging
from typing import Optional, Dict, Any
from pydantic import BaseModel

from features.doc_generator import generate_documentation
from shared.clients.confluence_replit_client import confluence_replit_client
from shared.clients.jira_client import jira_client

logger = logging.getLogger(__name__)


class DocOrchestrationRequest(BaseModel):
    """Request for complete documentation workflow"""
    prompt: str
    repository: Optional[str] = None
    max_files: int = 10
    
    # GitHub options
    commit_to_github: bool = True
    commit_path: str = "docs/AI_GENERATED_DOCS.md"
    commit_message: Optional[str] = None
    
    # Confluence options
    publish_to_confluence: bool = False
    confluence_space_key: Optional[str] = None
    confluence_parent_id: Optional[str] = None
    
    # Jira options
    create_jira_ticket: bool = False
    jira_project_key: Optional[str] = None


class DocOrchestrationResult(BaseModel):
    """Result of complete documentation workflow"""
    success: bool
    documentation: Optional[str] = None
    files_analyzed: list = []
    repository: Optional[str] = None
    
    github_commit: Optional[Dict[str, Any]] = None
    confluence_page: Optional[Dict[str, Any]] = None
    jira_ticket: Optional[Dict[str, Any]] = None
    
    error_message: Optional[str] = None
    workflow_summary: Dict[str, str] = {}


class DocOrchestrator:
    """Orchestrates the complete documentation workflow"""
    
    async def orchestrate(self, request: DocOrchestrationRequest) -> DocOrchestrationResult:
        """
        Execute complete documentation workflow:
        1. Generate documentation from prompt
        2. Commit to GitHub (optional)
        3. Publish to Confluence (optional)
        4. Create Jira ticket (optional)
        """
        workflow_summary = {}
        
        try:
            # Step 1: Generate documentation
            logger.info(f"Starting documentation workflow for prompt: {request.prompt[:100]}...")
            workflow_summary["step_1_generate"] = "started"
            
            doc_result = await generate_documentation(
                prompt=request.prompt,
                repository=request.repository,
                max_files=request.max_files,
                commit_to_github=request.commit_to_github,
                commit_path=request.commit_path,
                commit_message=request.commit_message
            )
            
            if not doc_result.success:
                workflow_summary["step_1_generate"] = f"failed: {doc_result.error_message}"
                return DocOrchestrationResult(
                    success=False,
                    error_message=doc_result.error_message,
                    workflow_summary=workflow_summary
                )
            
            workflow_summary["step_1_generate"] = "completed"
            workflow_summary["files_analyzed"] = f"{len(doc_result.files_analyzed)} files"
            
            # Step 2: GitHub commit (already done if requested)
            github_commit = doc_result.github_commit
            if github_commit:
                workflow_summary["step_2_github"] = f"committed: {github_commit.get('commit_url', 'N/A')}"
            else:
                workflow_summary["step_2_github"] = "skipped"
            
            # Step 3: Publish to Confluence (optional)
            confluence_page = None
            if request.publish_to_confluence and request.confluence_space_key:
                logger.info("Publishing documentation to Confluence...")
                workflow_summary["step_3_confluence"] = "started"
                
                confluence_page = await confluence_replit_client.create_page(
                    space_key=request.confluence_space_key,
                    title=f"AI Documentation: {doc_result.repository or 'Generated'}",
                    content=doc_result.documentation or "",
                    parent_id=request.confluence_parent_id
                )
                
                if confluence_page:
                    workflow_summary["step_3_confluence"] = f"published: {confluence_page.get('url', 'N/A')}"
                    logger.info(f"Published to Confluence: {confluence_page.get('url')}")
                else:
                    workflow_summary["step_3_confluence"] = "failed: Could not publish"
            else:
                workflow_summary["step_3_confluence"] = "skipped"
            
            # Step 4: Create Jira ticket (optional)
            jira_ticket = None
            if request.create_jira_ticket and request.jira_project_key:
                logger.info("Creating Jira ticket...")
                workflow_summary["step_4_jira"] = "started"
                
                jira_ticket = jira_client.create_documentation_ticket(
                    project_key=request.jira_project_key,
                    repository=doc_result.repository or "Unknown",
                    doc_type=doc_result.metadata.get("task_type", "general"),
                    github_commit_url=github_commit.get("commit_url") if github_commit else None,
                    confluence_url=confluence_page.get("url") if confluence_page else None
                )
                
                if jira_ticket:
                    workflow_summary["step_4_jira"] = f"created: {jira_ticket.get('url', 'N/A')}"
                    logger.info(f"Created Jira ticket: {jira_ticket.get('key')}")
                else:
                    workflow_summary["step_4_jira"] = "failed: Could not create ticket"
            else:
                workflow_summary["step_4_jira"] = "skipped"
            
            # Success!
            logger.info(f"Documentation workflow completed successfully!")
            
            return DocOrchestrationResult(
                success=True,
                documentation=doc_result.documentation,
                files_analyzed=doc_result.files_analyzed,
                repository=doc_result.repository,
                github_commit=github_commit,
                confluence_page=confluence_page,
                jira_ticket=jira_ticket,
                workflow_summary=workflow_summary
            )
            
        except Exception as e:
            logger.error(f"Documentation orchestration failed: {e}")
            workflow_summary["error"] = str(e)
            return DocOrchestrationResult(
                success=False,
                error_message=str(e),
                workflow_summary=workflow_summary
            )


async def orchestrate_documentation(
    prompt: str,
    repository: Optional[str] = None,
    max_files: int = 10,
    commit_to_github: bool = True,
    commit_path: str = "docs/AI_GENERATED_DOCS.md",
    commit_message: Optional[str] = None,
    publish_to_confluence: bool = False,
    confluence_space_key: Optional[str] = None,
    confluence_parent_id: Optional[str] = None,
    create_jira_ticket: bool = False,
    jira_project_key: Optional[str] = None
) -> DocOrchestrationResult:
    """
    Orchestrate complete documentation workflow
    
    Args:
        prompt: Natural language description of what to document
        repository: Repository name (owner/repo)
        max_files: Maximum files to analyze
        commit_to_github: Whether to commit docs to GitHub
        commit_path: Path where to save docs in repo
        commit_message: Custom commit message
        publish_to_confluence: Whether to publish to Confluence
        confluence_space_key: Confluence space key
        confluence_parent_id: Parent page ID in Confluence
        create_jira_ticket: Whether to create Jira ticket
        jira_project_key: Jira project key
    
    Returns:
        DocOrchestrationResult with complete workflow results
    """
    orchestrator = DocOrchestrator()
    
    request = DocOrchestrationRequest(
        prompt=prompt,
        repository=repository,
        max_files=max_files,
        commit_to_github=commit_to_github,
        commit_path=commit_path,
        commit_message=commit_message,
        publish_to_confluence=publish_to_confluence,
        confluence_space_key=confluence_space_key,
        confluence_parent_id=confluence_parent_id,
        create_jira_ticket=create_jira_ticket,
        jira_project_key=jira_project_key
    )
    
    result = await orchestrator.orchestrate(request)
    return result
