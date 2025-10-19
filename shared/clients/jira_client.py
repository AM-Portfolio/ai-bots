from jira import JIRA, JIRAError
from typing import List, Dict, Any, Optional
import logging

from ..config import settings

logger = logging.getLogger(__name__)


class JiraClient:
    def __init__(self):
        self.client: Optional[JIRA] = None
        self._initialize_client()
    
    def _initialize_client(self):
        if not all([settings.jira_url, settings.jira_email, settings.jira_api_token]):
            logger.warning("Jira credentials not configured")
            return
        
        try:
            self.client = JIRA(
                server=settings.jira_url,
                basic_auth=(settings.jira_email, settings.jira_api_token)
            )
            logger.info("Jira client initialized successfully")
        except Exception as e:
            logger.error(f"Failed to initialize Jira client: {e}")
            self.client = None
    
    def get_issue(self, issue_key: str) -> Optional[Dict[str, Any]]:
        if not self.client:
            return None
        
        try:
            issue = self.client.issue(issue_key)
            
            return {
                "key": issue.key,
                "summary": issue.fields.summary,
                "description": issue.fields.description or "",
                "status": issue.fields.status.name,
                "priority": issue.fields.priority.name if issue.fields.priority else "None",
                "assignee": issue.fields.assignee.displayName if issue.fields.assignee else "Unassigned",
                "created": issue.fields.created,
                "updated": issue.fields.updated,
                "labels": issue.fields.labels,
                "issue_type": issue.fields.issuetype.name
            }
        except JIRAError as e:
            logger.error(f"Failed to get Jira issue {issue_key}: {e}")
            return None
    
    def search_issues(
        self,
        jql: str,
        max_results: int = 50
    ) -> List[Dict[str, Any]]:
        if not self.client:
            return []
        
        try:
            issues = self.client.search_issues(jql, maxResults=max_results)
            return [
                {
                    "key": issue.key,
                    "summary": issue.fields.summary,
                    "status": issue.fields.status.name
                }
                for issue in issues
            ]
        except JIRAError as e:
            logger.error(f"Failed to search Jira issues: {e}")
            return []
    
    def create_issue(
        self,
        project_key: str,
        summary: str,
        description: str,
        issue_type: str = "Task",
        labels: Optional[List[str]] = None
    ) -> Optional[Dict[str, Any]]:
        if not self.client:
            return None
        
        try:
            issue_dict = {
                'project': {'key': project_key},
                'summary': summary,
                'description': description,
                'issuetype': {'name': issue_type}
            }
            
            if labels:
                issue_dict['labels'] = labels
            
            new_issue = self.client.create_issue(fields=issue_dict)
            logger.info(f"Created Jira issue {new_issue.key}")
            
            return {
                "key": new_issue.key,
                "url": f"{settings.jira_url}/browse/{new_issue.key}",
                "summary": summary,
                "issue_type": issue_type
            }
        except JIRAError as e:
            logger.error(f"Failed to create Jira issue: {e}")
            return None
    
    def create_documentation_ticket(
        self,
        project_key: str,
        repository: str,
        doc_type: str,
        github_commit_url: Optional[str] = None,
        confluence_url: Optional[str] = None
    ) -> Optional[Dict[str, Any]]:
        """Create a Jira ticket for AI-generated documentation"""
        if not self.client:
            logger.warning("Jira client not configured")
            return None
        
        summary = f"[AI-Generated] {doc_type.title()} Documentation for {repository}"
        
        description_parts = [
            f"AI-generated {doc_type} documentation has been created for repository: *{repository}*",
            "",
            "h3. Documentation Links:"
        ]
        
        if github_commit_url:
            description_parts.append(f"* GitHub Commit: {github_commit_url}")
        
        if confluence_url:
            description_parts.append(f"* Confluence Page: {confluence_url}")
        
        if not github_commit_url and not confluence_url:
            description_parts.append("* _No links available_")
        
        description_parts.extend([
            "",
            "h3. Next Steps:",
            "* Review the generated documentation for accuracy",
            "* Add any missing context or details",
            "* Share with the team for feedback",
            "",
            "_This ticket was automatically created by the AI Development Agent._"
        ])
        
        description = "\n".join(description_parts)
        
        return self.create_issue(
            project_key=project_key,
            summary=summary,
            description=description,
            issue_type="Task",
            labels=["ai-generated", "documentation", "auto-created"]
        )
    
    def add_comment(self, issue_key: str, comment: str) -> bool:
        if not self.client:
            return False
        
        try:
            self.client.add_comment(issue_key, comment)
            logger.info(f"Added comment to {issue_key}")
            return True
        except JIRAError as e:
            logger.error(f"Failed to add comment to {issue_key}: {e}")
            return False
    
    def transition_issue(self, issue_key: str, transition_name: str) -> bool:
        if not self.client:
            return False
        
        try:
            transitions = self.client.transitions(issue_key)
            transition_id = None
            
            for t in transitions:
                if t['name'].lower() == transition_name.lower():
                    transition_id = t['id']
                    break
            
            if transition_id:
                self.client.transition_issue(issue_key, transition_id)
                logger.info(f"Transitioned {issue_key} to {transition_name}")
                return True
            else:
                logger.warning(f"Transition '{transition_name}' not found for {issue_key}")
                return False
        except JIRAError as e:
            logger.error(f"Failed to transition {issue_key}: {e}")
            return False


jira_client = JiraClient()
