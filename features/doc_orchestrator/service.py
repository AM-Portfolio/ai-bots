"""Documentation Orchestrator - Complete workflow for AI-driven documentation"""
import logging
from typing import Optional, Dict, Any
from pydantic import BaseModel
from datetime import datetime
import uuid

from features.doc_generator import generate_documentation
from shared.clients.confluence_replit_client import confluence_replit_client
from shared.clients.jira_client import jira_client
from shared.thinking_process import create_doc_orchestrator_thinking_process

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
    thinking: Optional[Dict[str, Any]] = None


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
        
        # Initialize thinking process
        thinking = create_doc_orchestrator_thinking_process(str(uuid.uuid4()))
        
        try:
            # Step 1: Validate repository
            thinking.start_step("validate_repo")
            if request.repository:
                thinking.complete_step("validate_repo", {"repository": request.repository})
            else:
                thinking.skip_step("validate_repo", "No repository specified")
            
            # Step 2: Analyze code & Generate documentation
            logger.info(f"Starting documentation workflow for prompt: {request.prompt[:100]}...")
            workflow_summary["step_1_generate"] = "started"
            thinking.start_step("analyze_code")
            thinking.start_step("generate_docs")
            
            doc_result = await generate_documentation(
                prompt=request.prompt,
                repository=request.repository,
                max_files=request.max_files,
                commit_to_github=request.commit_to_github,
                commit_path=request.commit_path,
                commit_message=request.commit_message
            )
            
            if not doc_result.success:
                error_msg = doc_result.error_message or "Documentation generation failed"
                workflow_summary["step_1_generate"] = f"failed: {error_msg}"
                thinking.fail_step("generate_docs", error_msg)
                thinking.end_time = datetime.now()
                return DocOrchestrationResult(
                    success=False,
                    error_message=error_msg,
                    workflow_summary=workflow_summary,
                    thinking=thinking.to_dict()
                )
            
            workflow_summary["step_1_generate"] = "completed"
            workflow_summary["files_analyzed"] = f"{len(doc_result.files_analyzed)} files"
            thinking.complete_step("analyze_code", {"files_count": len(doc_result.files_analyzed)})
            thinking.complete_step("generate_docs", {
                "files_count": len(doc_result.files_analyzed),
                "doc_length": len(doc_result.documentation) if doc_result.documentation else 0
            })
            
            # Step 3 & 4: GitHub commit (create_commit & push_to_github)
            thinking.start_step("create_commit")
            thinking.start_step("push_to_github")
            github_commit = doc_result.github_commit
            if github_commit:
                workflow_summary["step_2_github"] = f"committed: {github_commit.get('commit_url', 'N/A')}"
                thinking.complete_step("create_commit", {"file_path": request.commit_path})
                thinking.complete_step("push_to_github", {
                    "commit_sha": github_commit.get('commit_sha'),
                    "commit_url": github_commit.get('commit_url'),
                    "action": github_commit.get('action')
                })
            else:
                if request.commit_to_github:
                    workflow_summary["step_2_github"] = "failed: No commit result"
                    thinking.fail_step("create_commit", "Commit preparation failed")
                    thinking.fail_step("push_to_github", "Commit was requested but no result received")
                else:
                    workflow_summary["step_2_github"] = "skipped"
                    thinking.skip_step("create_commit", "Commit not requested")
                    thinking.skip_step("push_to_github", "Commit not requested")
            
            # Step 3: Publish to Confluence (optional)
            confluence_page = None
            if request.publish_to_confluence and request.confluence_space_key:
                logger.info("Publishing documentation to Confluence...")
                workflow_summary["step_3_confluence"] = "started"
                thinking.start_step("publish_confluence")
                
                confluence_page = await confluence_replit_client.create_page(
                    space_key=request.confluence_space_key,
                    title=f"AI Documentation: {doc_result.repository or 'Generated'}",
                    content=doc_result.documentation or "",
                    parent_id=request.confluence_parent_id
                )
                
                if confluence_page:
                    workflow_summary["step_3_confluence"] = f"published: {confluence_page.get('url', 'N/A')}"
                    thinking.complete_step("publish_confluence", {"page_url": confluence_page.get('url')})
                    logger.info(f"Published to Confluence: {confluence_page.get('url')}")
                else:
                    workflow_summary["step_3_confluence"] = "failed: Could not publish"
                    thinking.fail_step("publish_confluence", "Could not publish to Confluence")
            else:
                workflow_summary["step_3_confluence"] = "skipped"
                if not thinking._find_step("publish_confluence"):
                    thinking.add_step("publish_confluence", "Publish to Confluence", "Publishing to Confluence (optional)")
                thinking.skip_step("publish_confluence", "Confluence publishing not requested")
            
            # Step 5: Create Jira ticket (optional)
            jira_ticket = None
            if request.create_jira_ticket and request.jira_project_key:
                logger.info("Creating Jira ticket...")
                workflow_summary["step_4_jira"] = "started"
                if not thinking._find_step("create_jira"):
                    thinking.add_step("create_jira", "Create Jira Ticket", "Creating documentation ticket in Jira")
                thinking.start_step("create_jira")
                
                jira_ticket = jira_client.create_documentation_ticket(
                    project_key=request.jira_project_key,
                    repository=doc_result.repository or "Unknown",
                    doc_type=doc_result.metadata.get("task_type", "general"),
                    github_commit_url=github_commit.get("commit_url") if github_commit else None,
                    confluence_url=confluence_page.get("url") if confluence_page else None
                )
                
                if jira_ticket:
                    workflow_summary["step_4_jira"] = f"created: {jira_ticket.get('url', 'N/A')}"
                    thinking.complete_step("create_jira", {"ticket_key": jira_ticket.get('key')})
                    logger.info(f"Created Jira ticket: {jira_ticket.get('key')}")
                else:
                    workflow_summary["step_4_jira"] = "failed: Could not create ticket"
                    thinking.fail_step("create_jira", "Could not create Jira ticket")
            else:
                workflow_summary["step_4_jira"] = "skipped"
                if not thinking._find_step("create_jira"):
                    thinking.add_step("create_jira", "Create Jira Ticket", "Creating documentation ticket in Jira")
                thinking.skip_step("create_jira", "Jira ticket creation not requested")
            
            # Success!
            logger.info(f"Documentation workflow completed successfully!")
            thinking.end_time = datetime.now()
            
            return DocOrchestrationResult(
                success=True,
                documentation=doc_result.documentation,
                files_analyzed=doc_result.files_analyzed,
                repository=doc_result.repository,
                github_commit=github_commit,
                confluence_page=confluence_page,
                jira_ticket=jira_ticket,
                workflow_summary=workflow_summary,
                thinking=thinking.to_dict()
            )
            
        except Exception as e:
            logger.error(f"Documentation orchestration failed: {e}")
            workflow_summary["error"] = str(e)
            thinking.end_time = datetime.now()
            return DocOrchestrationResult(
                success=False,
                error_message=str(e),
                workflow_summary=workflow_summary,
                thinking=thinking.to_dict()
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
