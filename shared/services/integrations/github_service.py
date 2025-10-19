"""GitHub service implementation using base architecture"""

import os
from typing import Dict, Any, List, Optional
from datetime import datetime

from shared.services.base import BaseService, ServiceConfig, ServiceStatus
from shared.logger import get_logger

logger = get_logger(__name__)


class GitHubService(BaseService):
    """GitHub integration with LLM wrapper support"""
    
    async def connect(self) -> bool:
        """Connect to GitHub using Replit connector"""
        try:
            from shared.clients.github_replit_client import get_github_access_token
            from github import Github
            
            token = await get_github_access_token()
            if not token:
                self._set_error("Failed to get GitHub access token")
                return False
            
            self._client = Github(token)
            
            # Test connection
            user = self._client.get_user()
            logger.info(f"Connected to GitHub as: {user.login}")
            
            self._set_connected()
            return True
            
        except Exception as e:
            self._set_error(str(e))
            return False
    
    async def disconnect(self) -> bool:
        """Disconnect from GitHub"""
        if self._client:
            self._client.close()
            self._client = None
        self.status = ServiceStatus.DISCONNECTED
        return True
    
    async def test_connection(self) -> Dict[str, Any]:
        """Test GitHub connection"""
        try:
            if not self._client:
                return {"success": False, "error": "Not connected"}
            
            user = self._client.get_user()
            return {
                "success": True,
                "user": user.login,
                "name": user.name,
                "repos": user.public_repos
            }
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    async def execute(self, action: str, **kwargs) -> Dict[str, Any]:
        """Execute GitHub actions"""
        actions = {
            "get_repo": self._get_repo,
            "list_repos": self._list_repos,
            "create_issue": self._create_issue,
            "create_pr": self._create_pr,
            "get_file": self._get_file,
            "commit_file": self._commit_file
        }
        
        handler = actions.get(action)
        if not handler:
            return {"success": False, "error": f"Unknown action: {action}"}
        
        return await handler(**kwargs)
    
    async def get_capabilities(self) -> List[str]:
        """Get GitHub service capabilities"""
        return [
            "Repository Management",
            "Issue Tracking",
            "Pull Requests",
            "File Operations",
            "Branch Management",
            "Webhooks"
        ]
    
    # Action handlers
    async def _get_repo(self, repo_name: str) -> Dict[str, Any]:
        """Get repository information"""
        try:
            repo = self._client.get_repo(repo_name)
            return {
                "success": True,
                "name": repo.name,
                "full_name": repo.full_name,
                "description": repo.description,
                "stars": repo.stargazers_count
            }
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    async def _list_repos(self, user: Optional[str] = None) -> Dict[str, Any]:
        """List repositories"""
        try:
            if user:
                repos = self._client.get_user(user).get_repos()
            else:
                repos = self._client.get_user().get_repos()
            
            return {
                "success": True,
                "repos": [{"name": r.name, "full_name": r.full_name} for r in repos[:20]]
            }
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    async def _create_issue(
        self, 
        repo_name: str, 
        title: str, 
        body: str
    ) -> Dict[str, Any]:
        """Create an issue"""
        try:
            repo = self._client.get_repo(repo_name)
            issue = repo.create_issue(title=title, body=body)
            return {
                "success": True,
                "issue_number": issue.number,
                "url": issue.html_url
            }
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    async def _create_pr(
        self,
        repo_name: str,
        title: str,
        body: str,
        head: str,
        base: str = "main"
    ) -> Dict[str, Any]:
        """Create a pull request"""
        try:
            repo = self._client.get_repo(repo_name)
            pr = repo.create_pull(title=title, body=body, head=head, base=base)
            return {
                "success": True,
                "pr_number": pr.number,
                "url": pr.html_url
            }
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    async def _get_file(
        self, 
        repo_name: str, 
        file_path: str, 
        ref: str = "main"
    ) -> Dict[str, Any]:
        """Get file content"""
        try:
            repo = self._client.get_repo(repo_name)
            content = repo.get_contents(file_path, ref=ref)
            return {
                "success": True,
                "content": content.decoded_content.decode('utf-8'),
                "sha": content.sha
            }
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    async def _commit_file(
        self,
        repo_name: str,
        file_path: str,
        content: str,
        message: str,
        branch: str = "main"
    ) -> Dict[str, Any]:
        """Commit a file"""
        try:
            repo = self._client.get_repo(repo_name)
            
            # Try to get existing file
            try:
                existing = repo.get_contents(file_path, ref=branch)
                result = repo.update_file(
                    file_path,
                    message,
                    content,
                    existing.sha,
                    branch=branch
                )
                action = "updated"
            except:
                result = repo.create_file(
                    file_path,
                    message,
                    content,
                    branch=branch
                )
                action = "created"
            
            return {
                "success": True,
                "action": action,
                "commit_sha": result['commit'].sha,
                "commit_url": result['commit'].html_url
            }
        except Exception as e:
            return {"success": False, "error": str(e)}
