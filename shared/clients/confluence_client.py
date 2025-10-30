from atlassian import Confluence
from typing import Dict, Any, Optional, List
import logging
import re
import base64
import aiohttp
import asyncio

from ..config import settings

logger = logging.getLogger(__name__)


class ConfluenceClient:
    def __init__(self):
        self.client: Optional[Confluence] = None
        self.site_url = None
        self.email = None
        self.api_token = None
        self.auth_header = None
        self._initialize_client()
    
    def _initialize_client(self):
        if not all([settings.confluence_url, settings.confluence_email, settings.confluence_api_token]):
            logger.warning("Confluence credentials not configured")
            return
        
        # Store credentials for both atlassian-python-api and direct API calls
        self.site_url = settings.confluence_url.rstrip('/wiki').rstrip('/')
        self.email = settings.confluence_email
        self.api_token = settings.confluence_api_token
        
        # Create Basic Auth header for direct API calls
        auth_string = f"{self.email}:{self.api_token}"
        auth_bytes = auth_string.encode('ascii')
        base64_bytes = base64.b64encode(auth_bytes)
        self.auth_header = base64_bytes.decode('ascii')
        
        try:
            # Initialize atlassian-python-api client
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
    
    def _get_headers(self) -> Dict[str, str]:
        """Get request headers with Basic Auth"""
        if not self.auth_header:
            return {}
        
        return {
            'Authorization': f'Basic {self.auth_header}',
            'Accept': 'application/json',
            'Content-Type': 'application/json'
        }
    
    def is_configured(self) -> bool:
        """Check if Confluence is configured"""
        return bool(self.auth_header)
    
    async def get_page(self, page_id: str) -> Optional[Dict[str, Any]]:
        if not self.client:
            return None
        
        try:
            page = self.client.get_page_by_id(
                page_id,
                expand='body.storage,version,space'
            )
            
            # Safely get space key with fallback
            space_key = page.get('space', {}).get('key', settings.confluence_space_key or 'unknown')
            
            return {
                "id": page['id'],
                "title": page['title'],
                "content": page['body']['storage']['value'],
                "version": page['version']['number'],
                "space_key": space_key,
                "url": f"{settings.confluence_url}/wiki/spaces/{space_key}/pages/{page['id']}"
            }
        except Exception as e:
            logger.error(f"Failed to get Confluence page {page_id}: {e}")
            return None
    
    async def create_page(
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
    
    # Enhanced async methods from Replit client
    async def test_connection_async(self) -> bool:
        """Test Confluence connection asynchronously"""
        if not self.is_configured():
            logger.error("Confluence credentials not configured")
            return False
        
        try:
            # Test with spaces endpoint
            api_url = f"{self.site_url}/wiki/rest/api/space"
            headers = self._get_headers()
            
            async with aiohttp.ClientSession() as session:
                async with session.get(api_url, headers=headers) as response:
                    if response.status == 200:
                        logger.info("Confluence connection test successful")
                        return True
                    else:
                        error_text = await response.text()
                        logger.error(f"Confluence connection test failed: {response.status} - {error_text}")
                        return False
        
        except Exception as e:
            logger.error(f"Error testing Confluence connection: {e}")
            return False
    
    async def get_spaces_async(self) -> Optional[list]:
        """Get all Confluence spaces asynchronously"""
        if not self.is_configured():
            return None
        
        try:
            api_url = f"{self.site_url}/wiki/rest/api/space"
            headers = self._get_headers()
            
            async with aiohttp.ClientSession() as session:
                async with session.get(api_url, headers=headers) as response:
                    if response.status == 200:
                        data = await response.json()
                        return data.get('results', [])
                    else:
                        error_text = await response.text()
                        logger.error(f"Failed to get spaces: {response.status} - {error_text}")
                        return None
        
        except Exception as e:
            logger.error(f"Error getting spaces: {e}")
            return None
    
    def _markdown_to_storage(self, markdown: str) -> str:
        """Convert markdown to Confluence storage format"""
        storage = markdown
        
        # Convert headers
        storage = re.sub(r'^# (.+)$', r'<h1>\1</h1>', storage, flags=re.MULTILINE)
        storage = re.sub(r'^## (.+)$', r'<h2>\1</h2>', storage, flags=re.MULTILINE)
        storage = re.sub(r'^### (.+)$', r'<h3>\1</h3>', storage, flags=re.MULTILINE)
        storage = re.sub(r'^#### (.+)$', r'<h4>\1</h4>', storage, flags=re.MULTILINE)
        
        # Convert code blocks
        def replace_code_block(match):
            lang = match.group(1) or 'none'
            code = match.group(2)
            return f'<ac:structured-macro ac:name="code"><ac:parameter ac:name="language">{lang}</ac:parameter><ac:plain-text-body><![CDATA[{code}]]></ac:plain-text-body></ac:structured-macro>'
        
        storage = re.sub(r'```(\w+)?\n(.*?)\n```', replace_code_block, storage, flags=re.DOTALL)
        
        # Convert bold and italic
        storage = re.sub(r'\*\*(.+?)\*\*', r'<strong>\1</strong>', storage)
        storage = re.sub(r'\*(.+?)\*', r'<em>\1</em>', storage)
        
        # Convert bullet lists
        storage = re.sub(r'^\* (.+)$', r'<ul><li>\1</li></ul>', storage, flags=re.MULTILINE)
        storage = re.sub(r'</ul>\n<ul>', '\n', storage)  # Merge adjacent lists
        
        # Convert line breaks to paragraphs
        storage = re.sub(r'\n\n+', '</p><p>', storage)
        
        return f"<p>{storage}</p>"
    
    async def create_page_async(
        self,
        space_key: str,
        title: str,
        content: str,
        parent_id: Optional[str] = None
    ) -> Optional[Dict[str, Any]]:
        """Create a new Confluence page using REST API v1 asynchronously"""
        if not self.is_configured():
            logger.error("Confluence credentials not available")
            return None
        
        try:
            # Use REST API v1 for better compatibility
            api_url = f"{self.site_url}/wiki/rest/api/content"
            headers = self._get_headers()
            
            # Convert markdown to Confluence storage format
            storage_content = self._markdown_to_storage(content)
            
            payload = {
                "type": "page",
                "title": title,
                "space": {
                    "key": space_key
                },
                "body": {
                    "storage": {
                        "value": storage_content,
                        "representation": "storage"
                    }
                }
            }
            
            if parent_id:
                payload["ancestors"] = [{"id": parent_id}]
            
            async with aiohttp.ClientSession() as session:
                async with session.post(api_url, headers=headers, json=payload) as response:
                    if response.status in [200, 201]:
                        data = await response.json()
                        page_url = f"{self.site_url}/wiki{data.get('_links', {}).get('webui', '')}"
                        result = {
                            "id": data.get("id"),
                            "title": data.get("title"),
                            "url": page_url,
                            "space_key": space_key
                        }
                        logger.info(f"Created Confluence page: {title} ({result['id']})")
                        return result
                    else:
                        error_text = await response.text()
                        logger.error(f"Failed to create Confluence page: {response.status} - {error_text}")
                        return None
        
        except Exception as e:
            logger.error(f"Error creating Confluence page: {e}")
            return None
    
    async def update_page_async(
        self,
        page_id: str,
        title: str,
        content: str,
        version_number: int
    ) -> Optional[Dict[str, Any]]:
        """Update an existing Confluence page asynchronously"""
        if not self.is_configured():
            return None
        
        try:
            api_url = f"{self.site_url}/wiki/rest/api/content/{page_id}"
            headers = self._get_headers()
            
            storage_content = self._markdown_to_storage(content)
            
            payload = {
                "type": "page",
                "title": title,
                "body": {
                    "storage": {
                        "value": storage_content,
                        "representation": "storage"
                    }
                },
                "version": {
                    "number": version_number + 1
                }
            }
            
            async with aiohttp.ClientSession() as session:
                async with session.put(api_url, headers=headers, json=payload) as response:
                    if response.status == 200:
                        data = await response.json()
                        page_url = f"{self.site_url}/wiki{data.get('_links', {}).get('webui', '')}"
                        result = {
                            "id": data.get("id"),
                            "title": data.get("title"),
                            "url": page_url,
                            "version": version_number + 1
                        }
                        logger.info(f"Updated Confluence page: {title}")
                        return result
                    else:
                        error_text = await response.text()
                        logger.error(f"Failed to update Confluence page: {response.status} - {error_text}")
                        return None
        
        except Exception as e:
            logger.error(f"Error updating Confluence page: {e}")
            return None
    
    async def get_page_async(self, page_id: str) -> Optional[Dict[str, Any]]:
        """Get a Confluence page by ID asynchronously"""
        if not self.is_configured():
            return None
        
        try:
            api_url = f"{self.site_url}/wiki/rest/api/content/{page_id}"
            headers = self._get_headers()
            
            async with aiohttp.ClientSession() as session:
                async with session.get(api_url, headers=headers) as response:
                    if response.status == 200:
                        data = await response.json()
                        return {
                            "id": data.get("id"),
                            "title": data.get("title"),
                            "version": data.get("version", {}).get("number", 1)
                        }
                    else:
                        logger.error(f"Failed to get Confluence page: {response.status}")
                        return None
        
        except Exception as e:
            logger.error(f"Error getting Confluence page: {e}")
            return None


confluence_client = ConfluenceClient()