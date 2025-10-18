from typing import Optional, Dict, Any, List
import logging
from shared.config import settings

logger = logging.getLogger(__name__)


class GitHubWrapper:
    """
    Unified GitHub client wrapper that uses ENV config by default,
    falls back to Replit connector if ENV vars are missing.
    
    This wrapper makes it easy to:
    1. Use traditional ENV-based authentication (GITHUB_TOKEN)
    2. Fall back to Replit's GitHub integration automatically
    3. Switch between providers without changing business logic
    4. Remove/replace integrations easily
    
    Usage:
        wrapper = GitHubWrapper()
        issue = await wrapper.get_issue("owner/repo", 123)
    """
    
    def __init__(self):
        self._env_client = None
        self._replit_client = None
        self._active_provider = None
        self._initialize()
    
    def _initialize(self):
        """Initialize clients based on available configuration"""
        if settings.github_token:
            try:
                from shared.clients.github_client import GitHubClient
                self._env_client = GitHubClient()
                self._active_provider = "env"
                logger.info("✅ GitHub wrapper using ENV config (GITHUB_TOKEN)")
            except Exception as e:
                logger.warning(f"Failed to initialize ENV-based GitHub client: {e}")
        
        if not self._env_client:
            try:
                from shared.clients.github_replit_client import GitHubReplitClient
                self._replit_client = GitHubReplitClient()
                self._active_provider = "replit"
                logger.info("🔄 GitHub wrapper using Replit connector (fallback)")
            except Exception as e:
                logger.error(f"Failed to initialize Replit GitHub client: {e}")
    
    @property
    def is_configured(self) -> bool:
        """Check if any provider is configured"""
        return self._env_client is not None or self._replit_client is not None
    
    @property
    def provider(self) -> Optional[str]:
        """Get active provider name"""
        return self._active_provider
    
    async def get_issue(self, repo_name: str, issue_number: int) -> Optional[Dict[str, Any]]:
        """Get GitHub issue (works with both ENV and Replit providers)"""
        if self._env_client:
            return self._env_client.get_issue(repo_name, issue_number)
        elif self._replit_client:
            return await self._replit_client.get_issue(repo_name, issue_number)
        else:
            logger.error("No GitHub provider configured")
            return None
    
    async def get_pull_request(self, repo_name: str, pr_number: int) -> Optional[Dict[str, Any]]:
        """Get GitHub pull request"""
        if self._env_client:
            return self._env_client.get_pull_request(repo_name, pr_number)
        elif self._replit_client:
            return await self._replit_client.get_pull_request(repo_name, pr_number)
        else:
            logger.error("No GitHub provider configured")
            return None
    
    async def create_pull_request(
        self,
        repo_name: str,
        title: str,
        body: str,
        head: str,
        base: str = "main"
    ) -> Optional[str]:
        """Create GitHub pull request"""
        if self._env_client:
            return self._env_client.create_pull_request(repo_name, title, body, head, base)
        elif self._replit_client:
            return await self._replit_client.create_pull_request(repo_name, title, body, head, base)
        else:
            logger.error("No GitHub provider configured")
            return None
    
    async def get_file_content(
        self,
        repo_name: str,
        file_path: str,
        branch: str = "main"
    ) -> Optional[str]:
        """Get file content from repository"""
        if self._env_client:
            return self._env_client.get_file_content(repo_name, file_path, branch)
        elif self._replit_client:
            return await self._replit_client.get_file_content(repo_name, file_path, branch)
        else:
            logger.error("No GitHub provider configured")
            return None
    
    async def create_or_update_file(
        self,
        repo_name: str,
        file_path: str,
        content: str,
        commit_message: str,
        branch: str = "main"
    ) -> bool:
        """Create or update file in repository"""
        if self._env_client:
            return self._env_client.create_or_update_file(
                repo_name, file_path, content, commit_message, branch
            )
        elif self._replit_client:
            return await self._replit_client.create_or_update_file(
                repo_name, file_path, content, commit_message, branch
            )
        else:
            logger.error("No GitHub provider configured")
            return False
    
    async def create_branch(self, repo_name: str, branch_name: str, base_branch: str = "main") -> bool:
        """Create a new branch (only available for Replit connector)"""
        if self._replit_client:
            return await self._replit_client.create_branch(repo_name, branch_name, base_branch)
        else:
            logger.warning("create_branch only available with Replit connector")
            return False
    
    async def commit_documentation(
        self,
        repo_name: str,
        file_path: str,
        content: str,
        commit_message: str,
        branch_name: Optional[str] = None
    ) -> Optional[Dict[str, Any]]:
        """Commit documentation to repository (primarily for Replit connector)"""
        if self._replit_client:
            return await self._replit_client.commit_documentation(
                repo_name, file_path, content, commit_message, branch_name
            )
        elif self._env_client:
            logger.warning("commit_documentation not fully supported for ENV client, using create_or_update_file")
            success = self._env_client.create_or_update_file(
                repo_name, file_path, content, commit_message, branch_name if branch_name else "main"
            )
            return {"success": success} if success else None
        else:
            logger.error("No GitHub provider configured")
            return None


github_wrapper = GitHubWrapper()
