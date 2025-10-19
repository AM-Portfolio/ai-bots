from typing import Optional, Dict, Any, List
import logging
from shared.config import settings

logger = logging.getLogger(__name__)


class ConfluenceWrapper:
    """
    Unified Confluence client wrapper that uses ENV config by default,
    falls back to Replit connector if ENV vars are missing.
    
    This wrapper makes it easy to:
    1. Use traditional ENV-based authentication (CONFLUENCE_URL, CONFLUENCE_EMAIL, CONFLUENCE_API_TOKEN)
    2. Fall back to Replit's Confluence integration automatically
    3. Switch between providers without changing business logic
    4. Remove/replace integrations easily
    
    Usage:
        wrapper = ConfluenceWrapper()
        page = await wrapper.get_page("123456")
    """
    
    def __init__(self):
        self._env_client = None
        self._replit_client = None
        self._active_provider = None
        self._initialize()
    
    def _initialize(self):
        """Initialize clients based on available configuration"""
        if all([settings.confluence_url, settings.confluence_email, settings.confluence_api_token]):
            try:
                from shared.clients.confluence_client import ConfluenceClient
                self._env_client = ConfluenceClient()
                self._active_provider = "env"
                logger.info("✅ Confluence wrapper using ENV config (CONFLUENCE_URL, CONFLUENCE_EMAIL, CONFLUENCE_API_TOKEN)")
            except Exception as e:
                logger.warning(f"Failed to initialize ENV-based Confluence client: {e}")
        
        if not self._env_client:
            try:
                from shared.clients.confluence_replit_client import ConfluenceReplitClient
                self._replit_client = ConfluenceReplitClient()
                if self._replit_client.is_configured():
                    self._active_provider = "replit"
                    logger.info("🔄 Confluence wrapper using Replit connector (fallback)")
                else:
                    self._replit_client = None
                    logger.info("⚠️  Confluence wrapper: No ENV config or Replit connector available")
            except Exception as e:
                logger.error(f"Failed to initialize Replit Confluence client: {e}")
    
    @property
    def is_configured(self) -> bool:
        """Check if any provider is configured"""
        return self._env_client is not None or self._replit_client is not None
    
    @property
    def provider(self) -> Optional[str]:
        """Get active provider name"""
        return self._active_provider
    
    async def get_page(self, page_id: str) -> Optional[Dict[str, Any]]:
        """Get Confluence page (works with both ENV and Replit providers)"""
        if self._env_client:
            return self._env_client.get_page(page_id)
        elif self._replit_client:
            return await self._replit_client.get_page(page_id)
        else:
            logger.error("No Confluence provider configured")
            return None
    
    async def create_page(
        self,
        space_key: str,
        title: str,
        content: str,
        parent_id: Optional[str] = None
    ) -> Optional[str]:
        """Create Confluence page"""
        if self._env_client:
            return self._env_client.create_page(space_key, title, content, parent_id)
        elif self._replit_client:
            return await self._replit_client.create_page(space_key, title, content, parent_id)
        else:
            logger.error("No Confluence provider configured")
            return None
    
    async def update_page(
        self,
        page_id: str,
        title: str,
        content: str
    ) -> bool:
        """Update Confluence page"""
        if self._env_client:
            return self._env_client.update_page(page_id, title, content)
        elif self._replit_client:
            return await self._replit_client.update_page(page_id, title, content)
        else:
            logger.error("No Confluence provider configured")
            return False
    
    async def search_pages(self, cql: str, limit: int = 25) -> List[Dict[str, Any]]:
        """Search Confluence pages using CQL"""
        if self._env_client:
            return self._env_client.search_pages(cql, limit)
        elif self._replit_client:
            return await self._replit_client.search_pages(cql, limit)
        else:
            logger.error("No Confluence provider configured")
            return []
    
    async def add_labels(self, page_id: str, labels: List[str]) -> bool:
        """Add labels to Confluence page"""
        if self._env_client:
            return self._env_client.add_labels(page_id, labels)
        elif self._replit_client:
            return await self._replit_client.add_labels(page_id, labels)
        else:
            logger.error("No Confluence provider configured")
            return False
    
    async def test_connection(self) -> bool:
        """Test Confluence connection"""
        if self._env_client:
            return True
        elif self._replit_client:
            return await self._replit_client.test_connection()
        else:
            return False
    
    async def get_spaces(self) -> Optional[list]:
        """Get all Confluence spaces"""
        if self._env_client:
            logger.warning("get_spaces not implemented for ENV client")
            return None
        elif self._replit_client:
            return await self._replit_client.get_spaces()
        else:
            return None


confluence_wrapper = ConfluenceWrapper()
