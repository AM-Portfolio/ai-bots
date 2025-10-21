from atlassian import Confluence
from typing import Dict, Any, Optional, List
import logging

from ..config import settings

logger = logging.getLogger(__name__)


class ConfluenceClient:
    def __init__(self):
        self.client: Optional[Confluence] = None
        self._initialize_client()
    
    def _initialize_client(self):
        if not all([settings.confluence_url, settings.confluence_email, settings.confluence_api_token]):
            logger.warning("Confluence credentials not configured")
            return
        
        try:
            self.client = Confluence(
                url=settings.confluence_url,
                username=settings.confluence_email,
                password=settings.confluence_api_token,
                cloud=True
            )
            logger.info("Confluence client initialized successfully")
        except Exception as e:
            logger.error(f"Failed to initialize Confluence client: {e}")
            self.client = None
    
    def get_page(self, page_id: str) -> Optional[Dict[str, Any]]:
        if not self.client:
            return None
        
        try:
            page = self.client.get_page_by_id(
                page_id,
                expand='body.storage,version'
            )
            
            return {
                "id": page['id'],
                "title": page['title'],
                "content": page['body']['storage']['value'],
                "version": page['version']['number'],
                "url": f"{settings.confluence_url}/wiki/spaces/{page['space']['key']}/pages/{page['id']}"
            }
        except Exception as e:
            logger.error(f"Failed to get Confluence page {page_id}: {e}")
            return None
    
    def create_page(
        self,
        space_key: str,
        title: str,
        content: str,
        parent_id: Optional[str] = None
    ) -> Optional[str]:
        if not self.client:
            return None
        
        try:
            page = self.client.create_page(
                space=space_key,
                title=title,
                body=content,
                parent_id=parent_id
            )
            
            page_id = page['id']
            logger.info(f"Created Confluence page: {title} (ID: {page_id})")
            return page_id
        except Exception as e:
            logger.error(f"Failed to create Confluence page '{title}': {e}")
            return None
    
    def update_page(
        self,
        page_id: str,
        title: str,
        content: str
    ) -> bool:
        if not self.client:
            return False
        
        try:
            page = self.client.get_page_by_id(page_id, expand='version')
            version = page['version']['number']
            
            self.client.update_page(
                page_id=page_id,
                title=title,
                body=content,
                version_number=version + 1
            )
            
            logger.info(f"Updated Confluence page {page_id}")
            return True
        except Exception as e:
            logger.error(f"Failed to update Confluence page {page_id}: {e}")
            return False
    
    def search_pages(
        self,
        cql: str,
        limit: int = 25
    ) -> List[Dict[str, Any]]:
        if not self.client:
            return []
        
        try:
            results = self.client.cql(cql, limit=limit)
            
            pages = []
            for result in results.get('results', []):
                pages.append({
                    "id": result['content']['id'],
                    "title": result['content']['title'],
                    "space": result['content']['space']['key']
                })
            
            return pages
        except Exception as e:
            logger.error(f"Failed to search Confluence pages: {e}")
            return []
    
    def add_labels(self, page_id: str, labels: List[str]) -> bool:
        if not self.client:
            return False
        
        try:
            for label in labels:
                self.client.set_page_label(page_id, label)
            
            logger.info(f"Added labels to page {page_id}: {labels}")
            return True
        except Exception as e:
            logger.error(f"Failed to add labels to page {page_id}: {e}")
            return False
    
    def get_spaces(self) -> List[Dict[str, Any]]:
        """Get all accessible spaces"""
        if not self.client:
            return []
        
        try:
            spaces = self.client.get_all_spaces()
            return [{
                "key": space["key"],
                "name": space["name"],
                "type": space.get("type", "unknown")
            } for space in spaces.get("results", [])]
        except Exception as e:
            logger.error(f"Failed to get spaces: {e}")
            return []
    
    def get_space_info(self, space_key: str) -> Optional[Dict[str, Any]]:
        """Get space information"""
        if not self.client:
            return None
        
        try:
            space = self.client.get_space(space_key)
            return {
                "key": space["key"],
                "name": space["name"],
                "type": space.get("type", "unknown")
            }
        except Exception as e:
            logger.error(f"Failed to get space info for {space_key}: {e}")
            return None
    
    def get_pages_in_space(self, space_key: str, limit: int = 50) -> List[Dict[str, Any]]:
        """Get pages in a space"""
        if not self.client:
            return []
        
        try:
            pages = self.client.get_all_pages_from_space(space_key, limit=limit)
            return [{
                "id": page["id"],
                "title": page["title"]
            } for page in pages]
        except Exception as e:
            logger.error(f"Failed to get pages from space {space_key}: {e}")
            return []
    
    def delete_page(self, page_id: str) -> bool:
        """Delete a page"""
        if not self.client:
            return False
        
        try:
            self.client.remove_page(page_id)
            logger.info(f"Deleted page {page_id}")
            return True
        except Exception as e:
            logger.error(f"Failed to delete page {page_id}: {e}")
            return False
    
    def test_connection(self) -> bool:
        """Test connection to Confluence"""
        if not self.client:
            return False
        
        try:
            # Try to get user info as a test
            self.client.get_current_user()
            return True
        except Exception as e:
            logger.error(f"Connection test failed: {e}")
            return False


confluence_client = ConfluenceClient()
