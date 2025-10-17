"""Confluence client using Replit's Confluence integration"""
import os
import logging
from typing import Optional, Dict, Any
from datetime import datetime

logger = logging.getLogger(__name__)


async def get_confluence_access_token() -> Optional[Dict[str, str]]:
    """Get Confluence access token and site URL from Replit connector"""
    try:
        import aiohttp
        
        hostname = os.environ.get('REPLIT_CONNECTORS_HOSTNAME')
        x_replit_token = None
        
        if os.environ.get('REPL_IDENTITY'):
            x_replit_token = 'repl ' + os.environ.get('REPL_IDENTITY')
        elif os.environ.get('WEB_REPL_RENEWAL'):
            x_replit_token = 'depl ' + os.environ.get('WEB_REPL_RENEWAL')
        
        if not x_replit_token or not hostname:
            logger.warning("Replit connector not available")
            return None
        
        url = f'https://{hostname}/api/v2/connection?include_secrets=true&connector_names=confluence'
        headers = {
            'Accept': 'application/json',
            'X_REPLIT_TOKEN': x_replit_token
        }
        
        async with aiohttp.ClientSession() as session:
            async with session.get(url, headers=headers) as response:
                if response.status != 200:
                    logger.error(f"Failed to get Confluence credentials: {response.status}")
                    return None
                
                data = await response.json()
                items = data.get('items', [])
                
                if not items:
                    logger.warning("No Confluence connection found")
                    return None
                
                connection_settings = items[0]
                access_token = (
                    connection_settings.get('settings', {}).get('access_token') or
                    connection_settings.get('settings', {}).get('oauth', {}).get('credentials', {}).get('access_token')
                )
                site_url = connection_settings.get('settings', {}).get('site_url', '')
                
                if not access_token or not site_url:
                    logger.error("Confluence access token or site URL not found in connection")
                    return None
                
                return {
                    'access_token': access_token,
                    'site_url': site_url
                }
                
    except Exception as e:
        logger.error(f"Error getting Confluence credentials: {e}")
        return None


class ConfluenceReplitClient:
    """Confluence client that uses Replit's Confluence integration"""
    
    def __init__(self):
        self._credentials: Optional[Dict[str, str]] = None
    
    async def _get_credentials(self) -> Optional[Dict[str, str]]:
        """Get or refresh Confluence credentials"""
        try:
            credentials = await get_confluence_access_token()
            if not credentials:
                return None
            
            self._credentials = credentials
            logger.info(f"Confluence client initialized for site: {credentials['site_url']}")
            return self._credentials
            
        except Exception as e:
            logger.error(f"Failed to get Confluence credentials: {e}")
            return None
    
    async def create_page(
        self,
        space_key: str,
        title: str,
        content: str,
        parent_id: Optional[str] = None
    ) -> Optional[Dict[str, Any]]:
        """Create a new Confluence page"""
        credentials = await self._get_credentials()
        if not credentials:
            logger.error("Confluence credentials not available")
            return None
        
        try:
            import aiohttp
            
            # Confluence REST API v2
            api_url = f"{credentials['site_url']}/wiki/api/v2/pages"
            
            headers = {
                'Authorization': f"Bearer {credentials['access_token']}",
                'Accept': 'application/json',
                'Content-Type': 'application/json'
            }
            
            # Convert markdown to Confluence storage format (basic conversion)
            storage_content = self._markdown_to_storage(content)
            
            payload = {
                "spaceId": space_key,
                "status": "current",
                "title": title,
                "body": {
                    "representation": "storage",
                    "value": storage_content
                }
            }
            
            if parent_id:
                payload["parentId"] = parent_id
            
            async with aiohttp.ClientSession() as session:
                async with session.post(api_url, headers=headers, json=payload) as response:
                    if response.status in [200, 201]:
                        data = await response.json()
                        page_url = f"{credentials['site_url']}/wiki{data.get('_links', {}).get('webui', '')}"
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
        credentials = await self._get_credentials()
        if not credentials:
            return None
        
        try:
            import aiohttp
            
            api_url = f"{credentials['site_url']}/wiki/api/v2/pages/{page_id}"
            
            headers = {
                'Authorization': f"Bearer {credentials['access_token']}",
                'Accept': 'application/json',
                'Content-Type': 'application/json'
            }
            
            storage_content = self._markdown_to_storage(content)
            
            payload = {
                "id": page_id,
                "status": "current",
                "title": title,
                "body": {
                    "representation": "storage",
                    "value": storage_content
                },
                "version": {
                    "number": version_number + 1
                }
            }
            
            async with aiohttp.ClientSession() as session:
                async with session.put(api_url, headers=headers, json=payload) as response:
                    if response.status == 200:
                        data = await response.json()
                        page_url = f"{credentials['site_url']}/wiki{data.get('_links', {}).get('webui', '')}"
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
        credentials = await self._get_credentials()
        if not credentials:
            return None
        
        try:
            import aiohttp
            
            api_url = f"{credentials['site_url']}/wiki/api/v2/pages/{page_id}"
            
            headers = {
                'Authorization': f"Bearer {credentials['access_token']}",
                'Accept': 'application/json'
            }
            
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
        """Convert markdown to Confluence storage format (basic conversion)"""
        # Basic markdown to HTML-like Confluence storage format
        # This is a simple conversion - for production, use a proper markdown parser
        
        storage = markdown
        
        # Convert headers
        storage = storage.replace('# ', '<h1>').replace('\n', '</h1>\n', 1)
        storage = storage.replace('## ', '<h2>').replace('\n', '</h2>\n', 1)
        storage = storage.replace('### ', '<h3>').replace('\n', '</h3>\n', 1)
        storage = storage.replace('#### ', '<h4>').replace('\n', '</h4>\n', 1)
        
        # Convert code blocks
        import re
        storage = re.sub(r'```(\w+)?\n(.*?)\n```', r'<ac:structured-macro ac:name="code"><ac:parameter ac:name="language">\1</ac:parameter><ac:plain-text-body><![CDATA[\2]]></ac:plain-text-body></ac:structured-macro>', storage, flags=re.DOTALL)
        
        # Convert bold and italic
        storage = re.sub(r'\*\*(.+?)\*\*', r'<strong>\1</strong>', storage)
        storage = re.sub(r'\*(.+?)\*', r'<em>\1</em>', storage)
        
        # Convert line breaks
        storage = storage.replace('\n\n', '<p></p>')
        
        return f"<p>{storage}</p>"


confluence_replit_client = ConfluenceReplitClient()
