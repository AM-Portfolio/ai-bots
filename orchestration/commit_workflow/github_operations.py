"""
GitHub Operations using PyGithub
Handles commits, pull requests, and repository management
Uses centralized GitHub wrapper for authentication
"""

import logging
import re
from datetime import datetime
from typing import Dict, Any, Optional, List
from github import Github, GithubException

logger = logging.getLogger(__name__)


def generate_branch_name(commit_message: str, prefix: str = "feature") -> str:
    """
    Generate meaningful branch name from commit message
    
    Args:
        commit_message: Commit message to extract branch name from
        prefix: Branch prefix (feature, fix, docs, etc.)
    
    Returns:
        Sanitized branch name
    
    Example:
        "Add authentication service" -> "feature/add-authentication-service"
        "Fix login bug" -> "fix/login-bug"
    """
    clean_message = commit_message.lower()
    clean_message = re.sub(r'[^a-z0-9\s-]', '', clean_message)
    clean_message = re.sub(r'\s+', '-', clean_message.strip())
    clean_message = clean_message[:50]
    
    timestamp = datetime.now().strftime("%Y%m%d")
    
    return f"{prefix}/{clean_message}-{timestamp}"


class GitHubOperations:
    """
    GitHub operations using PyGithub library
    Provides methods for commits, PRs, and repository management
    Uses centralized GitHub client from GitHubWrapper
    """
    
    def __init__(self, github_client: Optional[Github] = None):
        """
        Initialize GitHub operations with existing client
        
        Args:
            github_client: Existing PyGithub client instance from GitHubWrapper
        """
        self.client = github_client
        if not self.client:
            logger.warning("⚠️ No GitHub client provided - operations will be limited")
        else:
            logger.info("✅ GitHub operations initialized with centralized client")
    
    def _create_branch(
        self,
        repo,
        branch_name: str,
        base_branch: str = "main"
    ) -> bool:
        """
        Create a new branch from base branch
        
        Args:
            repo: PyGithub repository object
            branch_name: Name for new branch
            base_branch: Base branch to branch from (default: main)
        
        Returns:
            True if successful, False otherwise
        """
        try:
            base_ref = repo.get_branch(base_branch)
            repo.create_git_ref(
                ref=f"refs/heads/{branch_name}",
                sha=base_ref.commit.sha
            )
            logger.info(f"✅ Created branch: {branch_name} from {base_branch}")
            return True
        except GithubException as e:
            if e.status == 422:
                logger.info(f"ℹ️ Branch {branch_name} already exists")
                return True
            logger.error(f"Failed to create branch: {e}")
            return False
    
    async def commit_files(
        self,
        repository: str,
        branch: str,
        files: Dict[str, str],
        commit_message: str,
        commit_description: Optional[str] = None,
        create_branch: bool = True,
        base_branch: str = "main"
    ) -> Dict[str, Any]:
        """
        Commit files to GitHub repository
        
        Args:
            repository: Repository name (owner/repo)
            branch: Branch name (will be created if create_branch=True)
            files: Dictionary of {file_path: content}
            commit_message: Commit message
            commit_description: Optional extended description
            create_branch: Whether to create the branch first (default: True)
            base_branch: Base branch to create from (default: main)
        
        Returns:
            Result dictionary with success status and commit info
        """
        if not self.client:
            return {"success": False, "error": "GitHub client not initialized"}
        
        logger.info(f"📝 Committing {len(files)} files to {repository}:{branch}")
        
        try:
            repo = self.client.get_repo(repository)
            
            if create_branch and branch != base_branch:
                if not self._create_branch(repo, branch, base_branch):
                    return {"success": False, "error": f"Failed to create branch {branch}"}
            
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
            branch_url = f"https://github.com/{repository}/tree/{branch}"
            
            logger.info(f"✅ Commit successful: {commit_url}")
            logger.info(f"📌 Branch URL: {branch_url}")
            
            return {
                "success": True,
                "commit_sha": latest_commit.sha,
                "commit_url": commit_url,
                "branch_url": branch_url,
                "files_committed": list(files.keys()),
                "repository": repository,
                "branch": branch,
                "base_branch": base_branch
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
