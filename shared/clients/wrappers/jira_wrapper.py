from typing import Optional, Dict, Any, List
import logging
from shared.config import settings

logger = logging.getLogger(__name__)


class JiraWrapper:
    """
    Unified Jira client wrapper that uses ENV config by default,
    falls back to Replit connector if ENV vars are missing.
    
    This wrapper makes it easy to:
    1. Use traditional ENV-based authentication (JIRA_URL, JIRA_EMAIL, JIRA_API_TOKEN)
    2. Fall back to Replit's Jira integration automatically (if available)
    3. Switch between providers without changing business logic
    4. Remove/replace integrations easily
    
    Usage:
        wrapper = JiraWrapper()
        issue = await wrapper.get_issue("PROJ-123")
    """
    
    def __init__(self):
        self._env_client = None
        # Replit client removed - using regular client only
        self._active_provider = None
        self._initialize()
    
    def _initialize(self):
        """Initialize clients based on available configuration"""
        if all([settings.jira_url, settings.jira_email, settings.jira_api_token]):
            try:
                from shared.clients.jira_client import JiraClient
                self._env_client = JiraClient()
                self._active_provider = "env"
                logger.info("✅ Jira wrapper using ENV config (JIRA_URL, JIRA_EMAIL, JIRA_API_TOKEN)")
            except Exception as e:
                logger.warning(f"Failed to initialize ENV-based Jira client: {e}")
        
        if not self._env_client:
            logger.info("🔄 Jira wrapper: No ENV config, Replit connector not yet implemented")
            self._active_provider = None
    
    @property
    def is_configured(self) -> bool:
        """Check if any provider is configured"""
        return self._env_client is not None
    
    @property
    def provider(self) -> Optional[str]:
        """Get active provider name"""
        return self._active_provider
    
    async def get_issue(self, issue_key: str) -> Optional[Dict[str, Any]]:
        """Get Jira issue (works with both ENV and Replit providers)"""
        if self._env_client:
            return self._env_client.get_issue(issue_key)
        # Replit client removed - using regular client only
        else:
            logger.error("No Jira provider configured")
            return None
    
    async def search_issues(self, jql: str, max_results: int = 50) -> List[Dict[str, Any]]:
        """Search Jira issues using JQL"""
        if self._env_client:
            return self._env_client.search_issues(jql, max_results)
        # Replit client removed - using regular client only
        else:
            logger.error("No Jira provider configured")
            return []
    
    async def create_issue(
        self,
        project_key: str,
        summary: str,
        description: str,
        issue_type: str = "Task",
        labels: Optional[List[str]] = None
    ) -> Optional[str]:
        """Create Jira issue"""
        if self._env_client:
            return self._env_client.create_issue(
                project_key, summary, description, issue_type, labels
            )
        else:
            logger.error("No Jira provider configured")
            return None
    
    async def add_comment(self, issue_key: str, comment: str) -> bool:
        """Add comment to Jira issue"""
        if self._env_client:
            return self._env_client.add_comment(issue_key, comment)
        # Replit client removed - using regular client only
        else:
            logger.error("No Jira provider configured")
            return False
    
    async def transition_issue(self, issue_key: str, transition_name: str) -> bool:
        """Transition Jira issue to new status"""
        if self._env_client:
            return self._env_client.transition_issue(issue_key, transition_name)
        else:
            logger.error("No Jira provider configured")
            return False


jira_wrapper = JiraWrapper()
