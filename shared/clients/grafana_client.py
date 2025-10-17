import aiohttp
from typing import Dict, Any, Optional, List
import logging

from ..config import settings

logger = logging.getLogger(__name__)


class GrafanaClient:
    def __init__(self):
        self.base_url = settings.grafana_url
        self.api_key = settings.grafana_api_key
        self.headers = {}
        
        if self.api_key:
            self.headers['Authorization'] = f'Bearer {self.api_key}'
            logger.info("Grafana client initialized successfully")
        else:
            logger.warning("Grafana API key not configured")
    
    async def query_metrics(
        self,
        query: str,
        start_time: str,
        end_time: str
    ) -> Optional[Dict[str, Any]]:
        if not self.api_key:
            return None
        
        url = f"{self.base_url}/api/datasources/proxy/1/api/v1/query_range"
        
        params = {
            'query': query,
            'start': start_time,
            'end': end_time,
            'step': '15s'
        }
        
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(url, headers=self.headers, params=params) as response:
                    if response.status == 200:
                        data = await response.json()
                        logger.info(f"Successfully queried metrics: {query}")
                        return data
                    else:
                        logger.error(f"Grafana query failed with status {response.status}")
                        return None
        except Exception as e:
            logger.error(f"Failed to query Grafana metrics: {e}")
            return None
    
    async def get_alerts(self, state: str = "all") -> List[Dict[str, Any]]:
        if not self.api_key:
            return []
        
        url = f"{self.base_url}/api/alerts"
        params = {"state": state}
        
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(url, headers=self.headers, params=params) as response:
                    if response.status == 200:
                        alerts = await response.json()
                        logger.info(f"Retrieved {len(alerts)} alerts from Grafana")
                        return alerts
                    else:
                        logger.error(f"Failed to get alerts with status {response.status}")
                        return []
        except Exception as e:
            logger.error(f"Failed to get Grafana alerts: {e}")
            return []
    
    async def get_dashboard(self, uid: str) -> Optional[Dict[str, Any]]:
        if not self.api_key:
            return None
        
        url = f"{self.base_url}/api/dashboards/uid/{uid}"
        
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(url, headers=self.headers) as response:
                    if response.status == 200:
                        dashboard = await response.json()
                        logger.info(f"Retrieved dashboard {uid}")
                        return dashboard
                    else:
                        logger.error(f"Failed to get dashboard with status {response.status}")
                        return None
        except Exception as e:
            logger.error(f"Failed to get Grafana dashboard: {e}")
            return None
    
    async def create_annotation(
        self,
        text: str,
        tags: List[str],
        time: Optional[int] = None
    ) -> bool:
        if not self.api_key:
            return False
        
        url = f"{self.base_url}/api/annotations"
        
        import time as time_module
        annotation = {
            'text': text,
            'tags': tags,
            'time': time or int(time_module.time() * 1000)
        }
        
        try:
            async with aiohttp.ClientSession() as session:
                async with session.post(url, headers=self.headers, json=annotation) as response:
                    if response.status == 200:
                        logger.info(f"Created annotation: {text}")
                        return True
                    else:
                        logger.error(f"Failed to create annotation with status {response.status}")
                        return False
        except Exception as e:
            logger.error(f"Failed to create Grafana annotation: {e}")
            return False


grafana_client = GrafanaClient()
