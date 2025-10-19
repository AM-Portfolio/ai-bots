"""Confluence client using Basic Auth with API token"""
import logging
from typing import Optional, Dict, Any
import base64
from shared.config import settings

logger = logging.getLogger(__name__)


class ConfluenceReplitClient:
    """Confluence client that uses Basic Auth with API token"""
    
    def __init__(self):
        self.site_url = (settings.confluence_url or '').rstrip('/wiki').rstrip('/')
        self.email = settings.confluence_email or ''
        self.api_token = settings.confluence_api_token or ''
        
        if self.site_url and self.email and self.api_token:
            # Create Basic Auth header
            auth_string = f"{self.email}:{self.api_token}"
            auth_bytes = auth_string.encode('ascii')
            base64_bytes = base64.b64encode(auth_bytes)
            self.auth_header = base64_bytes.decode('ascii')
            logger.info(f"Confluence client initialized for site: {self.site_url}")
        else:
            self.auth_header = None
            logger.warning("Confluence credentials not configured")
    
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
    
    async def test_connection(self) -> bool:
        """Test Confluence connection"""
        if not self.is_configured():
            logger.error("Confluence credentials not configured")
            return False
        
        try:
            import aiohttp
            
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
    
    async def get_spaces(self) -> Optional[list]:
        """Get all Confluence spaces"""
        if not self.is_configured():
            return None
        
        try:
            import aiohttp
            
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
    
    async def create_page(
        self,
        space_key: str,
        title: str,
        content: str,
        parent_id: Optional[str] = None
    ) -> Optional[Dict[str, Any]]:
        """Create a new Confluence page using REST API v1"""
        if not self.is_configured():
            logger.error("Confluence credentials not available")
            return None
        
        try:
            import aiohttp
            
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
    
    async def update_page(
        self,
        page_id: str,
        title: str,
        content: str,
        version_number: int
    ) -> Optional[Dict[str, Any]]:
        """Update an existing Confluence page"""
        if not self.is_configured():
            return None
        
        try:
            import aiohttp
            
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
    
    async def get_page(self, page_id: str) -> Optional[Dict[str, Any]]:
        """Get a Confluence page by ID"""
        if not self.is_configured():
            return None
        
        try:
            import aiohttp
            
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
    
    def _markdown_to_storage(self, markdown: str) -> str:
        """Convert markdown to Confluence storage format"""
        import re
        
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


confluence_replit_client = ConfluenceReplitClient()
