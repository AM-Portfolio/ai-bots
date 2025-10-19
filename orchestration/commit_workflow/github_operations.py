"""
GitHub Operations using PyGithub
Handles commits, pull requests, and repository management
"""

import logging
import os
from typing import Dict, Any, Optional, List
from github import Github, GithubException

logger = logging.getLogger(__name__)


class GitHubOperations:
    """
    GitHub operations using PyGithub library
    Provides methods for commits, PRs, and repository management
    """
    
    def __init__(self, token: Optional[str] = None):
        """
        Initialize GitHub client
        
        Args:
            token: GitHub personal access token (defaults to env var)
        """
        self.token = token or os.getenv("GITHUB_TOKEN")
        if not self.token:
            logger.warning("No GitHub token found - operations will be limited")
            self.client = None
        else:
            self.client = Github(self.token)
            logger.info("✅ GitHub client initialized with PyGithub")
    
    async def commit_files(
        self,
        repository: str,
        branch: str,
        files: Dict[str, str],
        commit_message: str,
        commit_description: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Commit files to GitHub repository
        
        Args:
            repository: Repository name (owner/repo)
            branch: Branch name
            files: Dictionary of {file_path: content}
            commit_message: Commit message
            commit_description: Optional extended description
        
        Returns:
            Result dictionary with success status and commit info
        """
        if not self.client:
            return {"success": False, "error": "GitHub client not initialized"}
        
        logger.info(f"📝 Committing {len(files)} files to {repository}:{branch}")
        
        try:
            repo = self.client.get_repo(repository)
            
            full_message = commit_message
            if commit_description:
                full_message = f"{commit_message}\n\n{commit_description}"
            
            for file_path, content in files.items():
                try:
                    contents = repo.get_contents(file_path, ref=branch)
                    repo.update_file(
                        path=file_path,
                        message=full_message,
                        content=content,
                        sha=contents.sha,
                        branch=branch
                    )
                    logger.info(f"✅ Updated: {file_path}")
                
                except GithubException as e:
                    if e.status == 404:
                        repo.create_file(
                            path=file_path,
                            message=full_message,
                            content=content,
                            branch=branch
                        )
                        logger.info(f"✅ Created: {file_path}")
                    else:
                        raise
            
            latest_commit = repo.get_branch(branch).commit
            commit_url = latest_commit.html_url
            
            logger.info(f"✅ Commit successful: {commit_url}")
            
            return {
                "success": True,
                "commit_sha": latest_commit.sha,
                "commit_url": commit_url,
                "files_committed": list(files.keys()),
                "repository": repository,
                "branch": branch
            }
            
        except Exception as e:
            logger.error(f"Failed to commit files: {e}")
            return {
                "success": False,
                "error": str(e)
            }
    
    async def create_pull_request(
        self,
        repository: str,
        source_branch: str,
        target_branch: str,
        title: str,
        description: Optional[str] = None,
        reviewers: Optional[List[str]] = None,
        assignees: Optional[List[str]] = None,
        labels: Optional[List[str]] = None,
        draft: bool = False
    ) -> Dict[str, Any]:
        """
        Create pull request on GitHub
        
        Args:
            repository: Repository name (owner/repo)
            source_branch: Source branch for PR
            target_branch: Target branch for PR
            title: PR title
            description: PR description
            reviewers: List of reviewer usernames
            assignees: List of assignee usernames
            labels: List of label names
            draft: Whether to create as draft PR
        
        Returns:
            Result dictionary with success status and PR info
        """
        if not self.client:
            return {"success": False, "error": "GitHub client not initialized"}
        
        logger.info(f"🔀 Creating PR: {source_branch} → {target_branch} in {repository}")
        
        try:
            repo = self.client.get_repo(repository)
            
            pr = repo.create_pull(
                title=title,
                body=description or "",
                head=source_branch,
                base=target_branch,
                draft=draft
            )
            
            if reviewers:
                pr.create_review_request(reviewers=reviewers)
            
            if assignees:
                pr.add_to_assignees(*assignees)
            
            if labels:
                pr.add_to_labels(*labels)
            
            logger.info(f"✅ PR created: {pr.html_url}")
            
            return {
                "success": True,
                "pr_number": pr.number,
                "pr_url": pr.html_url,
                "pr_state": pr.state,
                "repository": repository,
                "source_branch": source_branch,
                "target_branch": target_branch
            }
            
        except Exception as e:
            logger.error(f"Failed to create PR: {e}")
            return {
                "success": False,
                "error": str(e)
            }
    
    async def commit_and_create_pr(
        self,
        repository: str,
        branch: str,
        files: Dict[str, str],
        commit_message: str,
        pr_title: str,
        pr_description: Optional[str] = None,
        target_branch: str = "main",
        reviewers: Optional[List[str]] = None,
        assignees: Optional[List[str]] = None,
        labels: Optional[List[str]] = None,
        draft: bool = False
    ) -> Dict[str, Any]:
        """
        Commit files and create PR in one operation
        
        Combines commit_files and create_pull_request
        
        Returns:
            Result dictionary with both commit and PR info
        """
        logger.info(f"🚀 Commit + PR workflow for {repository}")
        
        commit_result = await self.commit_files(
            repository=repository,
            branch=branch,
            files=files,
            commit_message=commit_message
        )
        
        if not commit_result["success"]:
            return commit_result
        
        pr_result = await self.create_pull_request(
            repository=repository,
            source_branch=branch,
            target_branch=target_branch,
            title=pr_title,
            description=pr_description,
            reviewers=reviewers,
            assignees=assignees,
            labels=labels,
            draft=draft
        )
        
        if not pr_result["success"]:
            return {
                **commit_result,
                "pr_created": False,
                "pr_error": pr_result["error"]
            }
        
        return {
            "success": True,
            "commit_sha": commit_result["commit_sha"],
            "commit_url": commit_result["commit_url"],
            "pr_number": pr_result["pr_number"],
            "pr_url": pr_result["pr_url"],
            "repository": repository,
            "branch": branch
        }
