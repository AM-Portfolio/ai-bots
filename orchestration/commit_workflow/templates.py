"""
Commit Workflow Templates
Pre-filled templates for GitHub, Confluence, and Jira operations
"""

import logging
from typing import Dict, Any, Optional
from dataclasses import dataclass
from enum import Enum

logger = logging.getLogger(__name__)


class TemplatePlatform(str, Enum):
    """Supported platforms for commit workflows"""
    GITHUB = "github"
    CONFLUENCE = "confluence"
    JIRA = "jira"


@dataclass
class CommitTemplate:
    """
    Template for commit/publish operations
    Contains pre-filled fields that user can customize before executing
    """
    platform: TemplatePlatform
    title: str
    description: str
    fields: Dict[str, Any]
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization"""
        return {
            "platform": self.platform.value,
            "title": self.title,
            "description": self.description,
            "fields": self.fields
        }


class CommitTemplateFactory:
    """
    Factory for creating commit workflow templates
    Generates pre-filled templates based on detected intent
    """
    
    @staticmethod
    def create_github_commit_template(
        repository: Optional[str] = None,
        branch: str = "main",
        files: Optional[Dict[str, str]] = None,
        commit_message: Optional[str] = None,
        commit_description: Optional[str] = None
    ) -> CommitTemplate:
        """
        Create template for GitHub commit
        
        Args:
            repository: Repository name (owner/repo)
            branch: Branch name
            files: Dictionary of file paths and contents
            commit_message: Commit message
            commit_description: Extended commit description
        
        Returns:
            CommitTemplate for GitHub commit
        """
        return CommitTemplate(
            platform=TemplatePlatform.GITHUB,
            title="Commit to GitHub",
            description="Commit files to a GitHub repository",
            fields={
                "repository": repository or "",
                "branch": branch,
                "files": files or {},
                "commit_message": commit_message or "",
                "commit_description": commit_description or ""
            }
        )
    
    @staticmethod
    def create_github_pr_template(
        repository: Optional[str] = None,
        source_branch: str = "main",
        target_branch: str = "main",
        pr_title: Optional[str] = None,
        pr_description: Optional[str] = None,
        reviewers: Optional[list] = None,
        assignees: Optional[list] = None,
        labels: Optional[list] = None,
        draft: bool = False
    ) -> CommitTemplate:
        """
        Create template for GitHub pull request
        
        Args:
            repository: Repository name (owner/repo)
            source_branch: Source branch for PR
            target_branch: Target branch for PR
            pr_title: PR title
            pr_description: PR description
            reviewers: List of reviewer usernames
            assignees: List of assignee usernames
            labels: List of label names
            draft: Whether to create as draft PR
        
        Returns:
            CommitTemplate for GitHub PR
        """
        return CommitTemplate(
            platform=TemplatePlatform.GITHUB,
            title="Create Pull Request",
            description="Create a pull request on GitHub",
            fields={
                "repository": repository or "",
                "source_branch": source_branch,
                "target_branch": target_branch,
                "pr_title": pr_title or "",
                "pr_description": pr_description or "",
                "reviewers": reviewers or [],
                "assignees": assignees or [],
                "labels": labels or [],
                "draft": draft
            }
        )
    
    @staticmethod
    def create_github_commit_and_pr_template(
        repository: Optional[str] = None,
        branch: str = "main",
        target_branch: str = "main",
        files: Optional[Dict[str, str]] = None,
        commit_message: Optional[str] = None,
        commit_description: Optional[str] = None,
        pr_title: Optional[str] = None,
        pr_description: Optional[str] = None,
        reviewers: Optional[list] = None,
        assignees: Optional[list] = None,
        labels: Optional[list] = None,
        draft: bool = False
    ) -> CommitTemplate:
        """
        Create template for GitHub commit + PR workflow
        
        Combines commit and PR creation into single workflow
        
        Returns:
            CommitTemplate for combined workflow
        """
        return CommitTemplate(
            platform=TemplatePlatform.GITHUB,
            title="Commit and Create Pull Request",
            description="Commit files and create a pull request in one workflow",
            fields={
                "repository": repository or "",
                "branch": branch,
                "target_branch": target_branch,
                "files": files or {},
                "commit_message": commit_message or "",
                "commit_description": commit_description or "",
                "pr_title": pr_title or commit_message or "",
                "pr_description": pr_description or "",
                "reviewers": reviewers or [],
                "assignees": assignees or [],
                "labels": labels or [],
                "draft": draft
            }
        )
    
    @staticmethod
    def create_confluence_template(
        space_key: Optional[str] = None,
        page_title: Optional[str] = None,
        content: Optional[str] = None,
        parent_page_id: Optional[str] = None,
        version_comment: Optional[str] = None
    ) -> CommitTemplate:
        """
        Create template for Confluence page publishing
        
        Args:
            space_key: Confluence space key
            page_title: Page title
            content: Page content (HTML or wiki markup)
            parent_page_id: Optional parent page ID
            version_comment: Version comment
        
        Returns:
            CommitTemplate for Confluence
        """
        return CommitTemplate(
            platform=TemplatePlatform.CONFLUENCE,
            title="Publish to Confluence",
            description="Publish or update a Confluence page",
            fields={
                "space_key": space_key or "",
                "page_title": page_title or "",
                "content": content or "",
                "parent_page_id": parent_page_id or "",
                "version_comment": version_comment or "Updated via AI Dev Agent"
            }
        )
    
    @staticmethod
    def create_jira_template(
        project_key: Optional[str] = None,
        issue_type: str = "Task",
        summary: Optional[str] = None,
        description: Optional[str] = None,
        priority: str = "Medium",
        assignee: Optional[str] = None,
        labels: Optional[list] = None,
        components: Optional[list] = None,
        epic_link: Optional[str] = None
    ) -> CommitTemplate:
        """
        Create template for Jira ticket creation
        
        Args:
            project_key: Jira project key
            issue_type: Issue type (Task, Bug, Story, etc.)
            summary: Issue summary
            description: Issue description
            priority: Priority (Highest, High, Medium, Low, Lowest)
            assignee: Assignee username
            labels: List of labels
            components: List of component names
            epic_link: Epic key to link to
        
        Returns:
            CommitTemplate for Jira
        """
        return CommitTemplate(
            platform=TemplatePlatform.JIRA,
            title="Create Jira Ticket",
            description="Create a new Jira ticket",
            fields={
                "project_key": project_key or "",
                "issue_type": issue_type,
                "summary": summary or "",
                "description": description or "",
                "priority": priority,
                "assignee": assignee or "",
                "labels": labels or [],
                "components": components or [],
                "epic_link": epic_link or ""
            }
        )
