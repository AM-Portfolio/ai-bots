"""
LangGraph-based Intelligent Commit Workflow Router
Uses LLM to parse user intent and route to appropriate workflow
"""

import logging
import json
from typing import Dict, Any, Optional
from dataclasses import dataclass
from enum import Enum

from orchestration.commit_workflow.templates import (
    CommitTemplateFactory,
    CommitTemplate,
    TemplatePlatform
)

logger = logging.getLogger(__name__)


class WorkflowAction(str, Enum):
    """Actions that can be performed"""
    COMMIT = "commit"
    CREATE_PR = "create_pr"
    COMMIT_AND_PR = "commit_and_pr"
    PUBLISH = "publish"
    CREATE_TICKET = "create_ticket"
    UNKNOWN = "unknown"


@dataclass
class CommitIntent:
    """
    Parsed intent from user message
    Contains platform, action, and extracted parameters
    """
    platform: TemplatePlatform
    action: WorkflowAction
    confidence: float
    parameters: Dict[str, Any]
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary"""
        return {
            "platform": self.platform.value,
            "action": self.action.value,
            "confidence": self.confidence,
            "parameters": self.parameters
        }


class CommitWorkflowRouter:
    """
    Intelligent router for commit workflows
    Uses LLM to understand user intent and generate appropriate templates
    """
    
    def __init__(self, llm_orchestrator):
        """
        Initialize router with LLM orchestrator
        
        Args:
            llm_orchestrator: ResilientLLMOrchestrator instance
        """
        self.llm = llm_orchestrator
        logger.info("✅ Commit Workflow Router initialized")
    
    async def parse_user_intent(
        self,
        message: str,
        context: Optional[Dict[str, Any]] = None
    ) -> CommitIntent:
        """
        Parse user message to detect commit/publish intent
        
        Uses LLM to understand natural language and extract parameters
        
        Args:
            message: User's natural language message
            context: Optional context (current repo, branch, etc.)
        
        Returns:
            CommitIntent with parsed platform, action, and parameters
        """
        logger.info(f"🧠 Parsing commit intent from: {message[:100]}...")
        
        prompt = self._build_intent_parsing_prompt(message, context)
        
        try:
            response = await self.llm.generate_completion(
                prompt=prompt,
                temperature=0.1,
                max_tokens=500
            )
            
            intent_data = self._extract_json_from_response(response)
            
            intent = CommitIntent(
                platform=TemplatePlatform(intent_data.get("platform", "github")),
                action=WorkflowAction(intent_data.get("action", "commit")),
                confidence=intent_data.get("confidence", 0.8),
                parameters=intent_data.get("parameters", {})
            )
            
            logger.info(f"✅ Detected intent: {intent.platform.value} / {intent.action.value} (confidence: {intent.confidence})")
            
            return intent
            
        except Exception as e:
            logger.warning(f"LLM intent parsing failed, using fallback: {e}")
            return self._fallback_intent_detection(message, context)
    
    def _build_intent_parsing_prompt(self, message: str, context: Optional[Dict[str, Any]]) -> str:
        """Build prompt for LLM intent parsing"""
        context_str = json.dumps(context, indent=2) if context else "{}"
        
        return f"""Analyze this user message and extract the commit/publish intent.
Generate a meaningful commit message and branch name from the user's intent.

User Message: "{message}"

Context: {context_str}

Detect:
1. Platform: github, confluence, or jira
2. Action: commit, create_pr, commit_and_pr, publish, or create_ticket
3. Parameters: Extract repository, commit_message, branch_name, etc.
4. Confidence: 0.0 to 1.0

IMPORTANT:
- ALWAYS generate a meaningful commit_message based on what the user wants to commit
- ALWAYS generate a branch_name (NEVER use "main" - create a feature/fix/docs branch)
- Branch names should follow pattern: feature/description or fix/description or docs/description
- Commit messages should be clear, concise, and descriptive

Return JSON only:
{{
  "platform": "github",
  "action": "commit",
  "confidence": 0.95,
  "parameters": {{
    "repository": "owner/repo",
    "commit_message": "Add authentication service",
    "branch_name": "feature/add-authentication-service",
    "branch_prefix": "feature"
  }}
}}

Examples:
- "commit authentication docs to repo ai-bots" → {{"platform": "github", "action": "commit", "parameters": {{"repository": "ai-bots", "commit_message": "Add authentication documentation", "branch_name": "docs/add-authentication-docs", "branch_prefix": "docs"}}, "confidence": 0.95}}
- "commit and create PR for bug fix" → {{"platform": "github", "action": "commit_and_pr", "parameters": {{"commit_message": "Fix critical bug", "branch_name": "fix/critical-bug", "branch_prefix": "fix"}}, "confidence": 0.95}}
- "publish to Confluence" → {{"platform": "confluence", "action": "publish", "confidence": 0.9}}

Return JSON now:"""
    
    def _extract_json_from_response(self, response: str) -> Dict[str, Any]:
        """Extract JSON from LLM response"""
        try:
            response = response.strip()
            
            if "```json" in response:
                response = response.split("```json")[1].split("```")[0]
            elif "```" in response:
                response = response.split("```")[1].split("```")[0]
            
            response = response.strip()
            
            return json.loads(response)
            
        except Exception as e:
            logger.warning(f"Failed to parse JSON: {e}")
            return {}
    
    def _fallback_intent_detection(
        self,
        message: str,
        context: Optional[Dict[str, Any]]
    ) -> CommitIntent:
        """
        Fallback rule-based intent detection
        Used when LLM parsing fails
        """
        message_lower = message.lower()
        
        if "confluence" in message_lower or "publish" in message_lower:
            return CommitIntent(
                platform=TemplatePlatform.CONFLUENCE,
                action=WorkflowAction.PUBLISH,
                confidence=0.7,
                parameters={}
            )
        
        elif "jira" in message_lower or "ticket" in message_lower:
            return CommitIntent(
                platform=TemplatePlatform.JIRA,
                action=WorkflowAction.CREATE_TICKET,
                confidence=0.7,
                parameters={}
            )
        
        elif "pull request" in message_lower or "pr" in message_lower:
            if "commit" in message_lower:
                action = WorkflowAction.COMMIT_AND_PR
            else:
                action = WorkflowAction.CREATE_PR
            
            return CommitIntent(
                platform=TemplatePlatform.GITHUB,
                action=action,
                confidence=0.7,
                parameters={}
            )
        
        else:
            return CommitIntent(
                platform=TemplatePlatform.GITHUB,
                action=WorkflowAction.COMMIT,
                confidence=0.6,
                parameters={}
            )
    
    async def route_to_workflow(
        self,
        intent: CommitIntent,
        additional_params: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Route intent to appropriate workflow and generate template
        
        Args:
            intent: Parsed CommitIntent
            additional_params: Additional parameters to merge
        
        Returns:
            Dictionary with workflow name and template
        """
        params = {**intent.parameters, **(additional_params or {})}
        
        logger.info(f"🔀 Routing to workflow: {intent.platform.value} / {intent.action.value}")
        
        if intent.platform == TemplatePlatform.GITHUB:
            from orchestration.commit_workflow.github_operations import generate_branch_name
            
            commit_msg = params.get("commit_message", "Update files")
            branch_prefix = params.get("branch_prefix", "feature")
            branch_name = params.get("branch_name") or generate_branch_name(commit_msg, branch_prefix)
            
            if intent.action == WorkflowAction.COMMIT:
                template = CommitTemplateFactory.create_github_commit_template(
                    repository=params.get("repository"),
                    branch=branch_name,
                    files=params.get("files", {}),
                    commit_message=commit_msg
                )
                workflow = "github_commit"
            
            elif intent.action == WorkflowAction.CREATE_PR:
                template = CommitTemplateFactory.create_github_pr_template(
                    repository=params.get("repository"),
                    source_branch=branch_name,
                    target_branch=params.get("target_branch", "main"),
                    pr_title=params.get("pr_title") or commit_msg
                )
                workflow = "github_pr"
            
            elif intent.action == WorkflowAction.COMMIT_AND_PR:
                template = CommitTemplateFactory.create_github_commit_and_pr_template(
                    repository=params.get("repository"),
                    branch=branch_name,
                    target_branch=params.get("target_branch", "main"),
                    commit_message=commit_msg,
                    pr_title=params.get("pr_title") or commit_msg
                )
                workflow = "github_commit_and_pr"
            
            else:
                template = CommitTemplateFactory.create_github_commit_template()
                workflow = "github_commit"
        
        elif intent.platform == TemplatePlatform.CONFLUENCE:
            template = CommitTemplateFactory.create_confluence_template(
                space_key=params.get("space_key"),
                page_title=params.get("page_title"),
                content=params.get("content")
            )
            workflow = "confluence_publish"
        
        elif intent.platform == TemplatePlatform.JIRA:
            template = CommitTemplateFactory.create_jira_template(
                project_key=params.get("project_key"),
                summary=params.get("summary"),
                description=params.get("description")
            )
            workflow = "jira_ticket"
        
        else:
            template = CommitTemplateFactory.create_github_commit_template()
            workflow = "github_commit"
        
        logger.info(f"✅ Generated template for workflow: {workflow}")
        
        return {
            "workflow": workflow,
            "template": template,
            "intent": intent.to_dict(),
            "requires_approval": True
        }
