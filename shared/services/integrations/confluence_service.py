"""Confluence service implementation using base architecture"""

import os
from typing import Dict, Any, List, Optional

from shared.services.base import BaseService, ServiceConfig, ServiceStatus
from shared.logger import get_logger

logger = get_logger(__name__)


class ConfluenceService(BaseService):
    """Confluence integration with LLM wrapper support"""
    
    async def connect(self) -> bool:
        """Connect to Confluence"""
        try:
            from atlassian import Confluence
            from shared.config.settings import settings
            
            if not all([settings.confluence_url, settings.confluence_email, settings.confluence_api_token]):
                self._set_error("Missing Confluence configuration")
                return False
            
            self._client = Confluence(
                url=settings.confluence_url,
                username=settings.confluence_email,
                password=settings.confluence_api_token,
                cloud=True
            )
            
            # Test connection
            spaces = self._client.get_all_spaces(limit=1)
            logger.info(f"Connected to Confluence at {settings.confluence_url}")
            
            self._set_connected()
            return True
            
        except Exception as e:
            self._set_error(str(e))
            return False
    
    async def disconnect(self) -> bool:
        """Disconnect from Confluence"""
        self._client = None
        self.status = ServiceStatus.DISCONNECTED
        return True
    
    async def test_connection(self) -> Dict[str, Any]:
        """Test Confluence connection"""
        try:
            if not self._client:
                return {"success": False, "error": "Not connected"}
            
            spaces = self._client.get_all_spaces(limit=5)
            return {
                "success": True,
                "spaces_count": len(spaces.get('results', [])),
                "connected": True
            }
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    async def execute(self, action: str, **kwargs) -> Dict[str, Any]:
        """Execute Confluence actions"""
        actions = {
            "create_page": self._create_page,
            "update_page": self._update_page,
            "get_page": self._get_page,
            "list_spaces": self._list_spaces,
            "search": self._search
        }
        
        handler = actions.get(action)
        if not handler:
            return {"success": False, "error": f"Unknown action: {action}"}
        
        return await handler(**kwargs)
    
    async def get_capabilities(self) -> List[str]:
        """Get Confluence service capabilities"""
        return [
            "Page Management",
            "Space Management",
            "Content Search",
            "Comments",
            "Attachments"
        ]
    
    # Action handlers
    async def _create_page(
        self,
        space_key: str,
        title: str,
        content: str,
        parent_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """Create a Confluence page"""
        try:
            page = self._client.create_page(
                space=space_key,
                title=title,
                body=content,
                parent_id=parent_id,
                type='page',
                representation='storage'
            )
            
            return {
                "success": True,
                "page_id": page['id'],
                "url": page['_links']['webui']
            }
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    async def _update_page(
        self,
        page_id: str,
        title: str,
        content: str
    ) -> Dict[str, Any]:
        """Update a Confluence page"""
        try:
            page = self._client.update_page(
                page_id=page_id,
                title=title,
                body=content
            )
            
            return {
                "success": True,
                "page_id": page['id'],
                "version": page['version']['number']
            }
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    async def _get_page(self, page_id: str) -> Dict[str, Any]:
        """Get a Confluence page"""
        try:
            page = self._client.get_page_by_id(page_id, expand='body.storage,version')
            return {
                "success": True,
                "title": page['title'],
                "content": page['body']['storage']['value'],
                "version": page['version']['number']
            }
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    async def _list_spaces(self, limit: int = 10) -> Dict[str, Any]:
        """List Confluence spaces"""
        try:
            spaces = self._client.get_all_spaces(limit=limit)
            return {
                "success": True,
                "spaces": [
                    {"key": s['key'], "name": s['name']}
                    for s in spaces.get('results', [])
                ]
            }
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    async def _search(self, query: str, limit: int = 10) -> Dict[str, Any]:
        """Search Confluence"""
        try:
            results = self._client.cql(f'text ~ "{query}"', limit=limit)
            return {
                "success": True,
                "results": [
                    {"id": r['id'], "title": r['title']}
                    for r in results.get('results', [])
                ]
            }
        except Exception as e:
            return {"success": False, "error": str(e)}
