"""
Commit workflow API endpoints

Handles commit/publish workflow operations including GitHub operations and approval management.
"""

import uuid
from typing import Dict, Any, Optional
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from shared.logger import get_logger

logger = get_logger(__name__)

router = APIRouter(prefix="/api/commit", tags=["commit"])


class CommitWorkflowRequest(BaseModel):
    """Request to initiate commit/publish workflow"""
    message: str
    repository: Optional[str] = None
    branch: Optional[str] = None
    files: Optional[Dict[str, str]] = None
    context: Optional[Dict[str, Any]] = None


class ApprovalResponse(BaseModel):
    """User's response to approval request"""
    approval_id: str
    approved: bool
    updated_template: Optional[Dict[str, Any]] = None
    rejection_reason: Optional[str] = None


@router.post("/parse-intent")
async def parse_commit_intent(request: CommitWorkflowRequest):
    """
    Parse user message to detect commit/publish intent
    Returns approval template for user confirmation
    
    IMPORTANT: Requires repo_content in context to prevent commits without GitHub data
    """
    from shared.llm_providers.resilient_orchestrator import get_resilient_orchestrator
    from orchestration.commit_workflow import CommitWorkflowRouter
    from orchestration.commit_workflow.approval_system import get_approval_manager
    
    logger.info(f"🧠 Parsing commit intent: {request.message[:100]}...")
    
    try:
        # Validate that GitHub content was fetched
        if not request.files or 'repo_content' not in request.files:
            logger.error("❌ GitHub content not provided - commit workflow requires repository content")
            raise HTTPException(
                status_code=400,
                detail="GitHub content must be fetched before creating commit. Please ensure repository content is loaded first."
            )
        
        logger.info(f"✅ GitHub content validated (length: {len(request.files.get('repo_content', ''))} chars)")
        
        llm_orchestrator = get_resilient_orchestrator()
        router_instance = CommitWorkflowRouter(llm_orchestrator)
        
        intent = await router_instance.parse_user_intent(request.message, request.context)
        
        workflow_result = await router_instance.route_to_workflow(
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


@router.post("/approve")
async def approve_commit(response: ApprovalResponse):
    """
    User approves/rejects commit operation
    If approved, executes the operation
    """
    from orchestration.commit_workflow.approval_system import get_approval_manager
    
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


@router.get("/pending-approvals")
async def list_pending_approvals():
    """List all pending approval requests"""
    from orchestration.commit_workflow.approval_system import get_approval_manager
    
    approval_manager = get_approval_manager()
    pending = approval_manager.list_pending_requests()
    
    return {
        "pending_approvals": [req.to_dict() for req in pending],
        "count": len(pending)
    }


async def execute_commit_operation(operation_type: str, template_data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Execute approved commit/publish operation
    Returns result with links for next actions
    Uses centralized GitHub client from wrapper
    """
    from orchestration.commit_workflow import GitHubOperations
    from shared.clients.wrappers.github_wrapper import GitHubWrapper
    
    logger.info(f"⚡ Executing operation: {operation_type}")
    
    # Get GitHub client from centralized wrapper
    github_wrapper = GitHubWrapper()
    
    # Extract PyGithub client from wrapper
    github_client = None
    if github_wrapper._env_client and hasattr(github_wrapper._env_client, 'client'):
        github_client = github_wrapper._env_client.client
        logger.info("✅ Using centralized GitHub client from ENV wrapper")
    elif github_wrapper._replit_client:
        logger.warning("⚠️ Replit connector detected, but PyGithub operations require ENV-based client")
    
    github_ops = GitHubOperations(github_client)
    
    if operation_type == "github_commit":
        result = await github_ops.commit_files(
            repository=template_data["repository"],
            branch=template_data["branch"],
            files=template_data.get("files", {}),
            commit_message=template_data["commit_message"],
            commit_description=template_data.get("commit_description")
        )
        
        if result["success"]:
            pr_url = f"https://github.com/{template_data['repository']}/compare/{result.get('base_branch', 'main')}...{result['branch']}?expand=1"
            
            return {
                **result,
                "next_actions": [
                    {
                        "action": "view_commit",
                        "label": "View Commit",
                        "url": result["commit_url"]
                    },
                    {
                        "action": "view_branch",
                        "label": "View Branch",
                        "url": result.get("branch_url", result["commit_url"])
                    },
                    {
                        "action": "create_pr",
                        "label": "Create Pull Request",
                        "url": pr_url,
                        "repository": template_data["repository"],
                        "source_branch": result["branch"],
                        "target_branch": result.get("base_branch", "main")
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