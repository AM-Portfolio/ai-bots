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


confluence_client = ConfluenceClient()
